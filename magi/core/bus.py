import asyncio
import logging
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)

class BusEvent(BaseModel):
    topic: str
    payload: Any
    critical: bool = False


#: Temas que se pueden perder sin que el usuario se quede sin saber nada.
#:
#: `TERMINAL_OUT` es el volcado del registro: útil para depurar, prescindible
#: cuando hay que elegir. Una tarea con cobertura x3 genera cientos de líneas
#: en segundos, y son justo las que llenaban la cola de la interfaz.
#:
#: Todo lo demás —lo que dicen Naoko y Ritsuko, lo que aportan los tres nodos,
#: el estado del enjambre, los errores— se considera irrenunciable. Ante la
#: duda, un tema NUEVO no entra aquí: es mejor perder una línea de log de más
#: que perder en silencio algo que la persona estaba esperando.
_TEMAS_PRESCINDIBLES = ("TERMINAL_OUT", "obs.metric", "sonda.actualizada")


def _es_prescindible(topic: str) -> bool:
    return topic in _TEMAS_PRESCINDIBLES

class MagiBus:
    """
    Bus de eventos en memoria (Pub/Sub).
    At-most-once en memoria. At-least-once en disco si critical=True.
    Maneja backpressure y descarta telemetría vieja si la cola se llena.
    """
    def __init__(self):
        self.subscribers: dict[str, list[asyncio.Queue]] = {}
        self.handlers: dict[asyncio.Queue, Callable[[BusEvent], Any]] = {}
        self.dropped_counts: dict[str, int] = {}
        # Workers cuya creación quedó pendiente por no haber bucle de eventos.
        self._pending_workers: list[asyncio.Queue] = []
        self._worker_tasks: list[asyncio.Task] = []
        # Persistencia opcional de eventos críticos. El Kernel engancha aquí
        # su MagiDatabase al arrancar. Sin esto, un crash pierde los eventos
        # críticos (system.started, error.critical, obs.alert...) que justo
        # son los que hacen falta para diagnosticar por qué se cayó.
        self._critical_sink: Callable[[BusEvent], Any] | None = None
        # Tareas de persistencia en vuelo. Guardar la referencia NO es
        # decorativo: el bucle de eventos solo mantiene una referencia DÉBIL a
        # las tareas, así que una tarea sin dueño puede ser recolectada por el
        # GC a mitad de ejecución. El evento crítico desaparecería en silencio
        # — justo el fallo que esta persistencia venía a evitar, y de los que
        # no se reproducen a voluntad. El done_callback la descarta al acabar,
        # así que el conjunto no crece.
        self._sink_tasks: set[asyncio.Task] = set()

    def attach_critical_sink(self, sink: Callable[["BusEvent"], Any]) -> None:
        """Engancha un receptor para eventos críticos (lo llama el Kernel).

        El sink recibe el evento y decide qué hacer (típicamente: insertarlo en
        task_event). Se invoca de forma no bloqueante: el bus nunca espera al
        sink, y un fallo del sink nunca impide el broadcast.
        """
        self._critical_sink = sink

    def subscribe(self, topic_glob: str, handler: Callable[[BusEvent], Any], maxsize: int = 1024) -> str:
        queue = asyncio.Queue(maxsize=maxsize)
        if topic_glob not in self.subscribers:
            self.subscribers[topic_glob] = []
        self.subscribers[topic_glob].append(queue)
        self.handlers[queue] = handler

        # subscribe() se llama desde constructores SÍNCRONOS (Kernel, Naoko,
        # WSServer, MetricsCollector...). Si no hay bucle todavía,
        # asyncio.create_task revienta con "no running event loop" y el kernel
        # ni siquiera se construye. El worker queda pendiente y arranca en
        # cuanto haya bucle.
        self._spawn_worker(queue)
        return str(id(queue))

    def _spawn_worker(self, queue: asyncio.Queue) -> bool:
        # Comprobar el bucle ANTES de crear la corrutina: si se crea y luego
        # falla create_task, queda un objeto sin await y Python avisa con
        # RuntimeWarning en cada suscripción.
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            if queue not in self._pending_workers:
                self._pending_workers.append(queue)
            return False
        self._worker_tasks.append(asyncio.create_task(self._worker(queue)))
        return True

    def start_pending_workers(self) -> int:
        """Arranca los workers que quedaron en cola. Idempotente."""
        started = 0
        for queue in list(self._pending_workers):
            if self._spawn_worker(queue):
                self._pending_workers.remove(queue)
                started += 1
        if started:
            logger.debug("[bus] %d worker(s) arrancados de forma diferida", started)
        return started

    async def shutdown(self) -> None:
        """Cancela los workers. Sin esto quedaban vivos toda la sesión."""
        for t in self._worker_tasks:
            t.cancel()
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

    async def publish(self, event: BusEvent) -> None:
        if self._pending_workers:
            self.start_pending_workers()
        if event.critical and self._critical_sink is not None:
            # Persistencia de eventos críticos (system.started, error.critical,
            # obs.alert...). Fire-and-forget: el bus NUNCA espera al sink ni
            # deja de hacer broadcast si el sink falla. Un crash pierde los
            # eventos en RAM; con esto quedan en task_event para diagnóstico.
            #
            # El principio del bus (§backpressure) se respeta: la persistencia
            # no bloquea al productor. Si el sink va lento, su task se acumula,
            # pero el evento ya se ha entregado a los suscriptores.
            tarea = asyncio.create_task(self._persist_critical(event))
            self._sink_tasks.add(tarea)
            tarea.add_done_callback(self._sink_tasks.discard)

        # EL BROADCAST. Va aquí, en publish, y no puede ir en ningún otro
        # sitio: es lo único que hace que el bus sea un bus.
        #
        # Al introducir la persistencia, este bucle acabó dentro del método
        # nuevo (_persist_critical) en vez de quedarse en publish. El efecto
        # era total y silencioso: publish() dejaba de entregar a los
        # suscriptores, y el broadcast solo ocurría de rebote, para eventos
        # critical y únicamente si había un sink enganchado. Sin sink —el caso
        # de los tests y de cualquier arranque antes de Kernel.start()— el
        # sistema entero se quedaba mudo: ni interfaz, ni Naoko, ni telemetría,
        # ni enjambre. Una indentación.
        #
        # Es la clase de fallo contra la que el proyecto ya tiene un principio
        # escrito: no basta con que el código nuevo funcione, hay que mirar qué
        # le pasó al que ya estaba.
        for glob, queues in self.subscribers.items():
            if self._match_topic(glob, event.topic):
                for q in queues:
                    try:
                        q.put_nowait(event)
                    except asyncio.QueueFull:
                        self._descartar_el_mas_viejo(q, event)

    async def _persist_critical(self, event: "BusEvent") -> None:
        """Invoca el sink de persistencia. Aislada para que un fallo no propague."""
        try:
            await self._critical_sink(event)  # type: ignore[misc]
        except Exception as e:
            logger.debug("[bus] sink crítico falló para %s: %s", event.topic, e)

    def _descartar_el_mas_viejo(self, q: asyncio.Queue, event: "BusEvent") -> None:
        """
        Cola llena: se tira el evento MÁS ANTIGUO y entra el nuevo. Nunca se
        bloquea al productor.

        EL BLOQUEO QUE ESTO ELIMINA
        ===========================
        La versión anterior, para todo lo que no fuera telemetría, hacía:

            logger.warning("Cola llena ... Productor bloqueado esperando espacio")
            await q.put(event)          # <-- pausa la corrutina productora

        Y con eso un fallo tonto congeló el sistema entero. La secuencia real,
        del registro del usuario:

          1. `sys.config` lanzaba ImportError en cada llamada (un nombre sin
             exportar).
          2. ws_server lo registraba con nivel ERROR.
          3. BusLogHandler convierte todo ERROR en un evento `error.critical`.
          4. Naoko está suscrita a `error.critical` y DIAGNOSTICA cada uno
             llamando al enjambre: segundos por evento.
          5. Su cola se llenó.
          6. `await q.put(...)` bloqueó al productor... que era el propio
             sistema de logging. Todo se paró.
          7. Y el `logger.warning` de esta misma función generaba OTRO evento
             por el mismo camino: el remedio alimentaba la enfermedad. De ahí
             los cientos de líneas idénticas.

        El usuario escribió "crea un documento de word en mi escritorio" y no
        pasó nada, porque ya no quedaba nadie libre para atenderle.

        LA REGLA
        ========
        Un bus de eventos de diagnóstico JAMÁS bloquea a quien produce. Si el
        consumidor no da abasto, el que sobra es el evento, no el sistema.
        Perder una línea de log es un inconveniente; congelar la aplicación
        del usuario no lo es. Y se lleva la cuenta de lo descartado para
        poder decirlo, en vez de perderlo en silencio.
        """
        # QUÉ SE TIRA CUANDO NO CABE TODO (v5.9.0 §G2)
        #
        # «El más viejo» era una política ciega, y la ceguera se paga con lo
        # que más duele. La cola de la interfaz —ws_server se suscribe a `"*"`,
        # así que TODO pasa por ella— se llena de `TERMINAL_OUT`: cada línea de
        # log de cada proveedor. Durante una tarea con cobertura x3 son cientos
        # en segundos. Y al llenarse, lo primero que salía por la puerta era lo
        # más antiguo, que podía ser perfectamente la respuesta de Naoko
        # esperando su turno detrás de trescientas líneas de registro.
        #
        # Ahora, cuando no cabe: si lo que ENTRA es prescindible, se queda
        # fuera lo que entra. Solo se desaloja a un veterano cuando lo nuevo
        # es algo que el usuario necesita ver.
        #
        # Perder una línea de terminal es un inconveniente. Perder la respuesta
        # que la persona está esperando delante de la pantalla no lo es.
        if _es_prescindible(event.topic):
            self._contar_descarte(event.topic)
            return
        try:
            q.get_nowait()                  # fuera el más viejo
            q.put_nowait(event)
        except (asyncio.QueueEmpty, asyncio.QueueFull):
            pass                            # otra corrutina se nos adelantó
        self._contar_descarte(event.topic)

    def _contar_descarte(self, topic: str) -> None:
        n = self.dropped_counts.get(topic, 0) + 1
        self.dropped_counts[topic] = n
        # Se avisa en progresión geométrica (1, 10, 100, 1000...). Registrar
        # cada descarte volvería a generar un evento por descarte, que es
        # justo el bucle que se está cerrando aquí. Y `logger.debug` no pasa
        # por BusLogHandler en el nivel por defecto.
        if n == 1 or (n % 100 == 0):
            logger.debug("[bus] cola llena en '%s': %d evento(s) descartado(s)",
                         topic, n)

    def dropped_report(self) -> dict[str, int]:
        """Qué se ha descartado y cuánto. Lo enseña el panel de sistema."""
        return dict(self.dropped_counts)

    def _match_topic(self, glob: str, topic: str) -> bool:
        if glob == "*":
            return True
        if glob.endswith("*"):
            return topic.startswith(glob[:-1])
        return glob == topic

    async def _worker(self, queue: asyncio.Queue):
        handler = self.handlers[queue]
        while True:
            event = await queue.get()
            try:
                res = handler(event)
                if asyncio.iscoroutine(res) or hasattr(res, '__await__'):
                    await res
            except Exception as e:
                logger.error(f"Error en handler para evento {event.topic}: {e}")
            finally:
                queue.task_done()
