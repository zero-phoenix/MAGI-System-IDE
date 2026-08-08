import asyncio
import logging
from pydantic import BaseModel, Field
from typing import Callable, Awaitable, Dict, List, Any

logger = logging.getLogger(__name__)

class BusEvent(BaseModel):
    topic: str
    payload: Any
    critical: bool = False

class MagiBus:
    """
    Bus de eventos en memoria (Pub/Sub).
    At-most-once en memoria. At-least-once en disco si critical=True.
    Maneja backpressure y descarta telemetría vieja si la cola se llena.
    """
    def __init__(self):
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
        self.handlers: Dict[asyncio.Queue, Callable[[BusEvent], Any]] = {}
        self.dropped_counts: Dict[str, int] = {}
        # Workers cuya creación quedó pendiente por no haber bucle de eventos.
        self._pending_workers: List[asyncio.Queue] = []
        self._worker_tasks: List[asyncio.Task] = []
        
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
        if event.critical:
            # TODO: persist in event_log before broadcasting (SQLite)
            logger.debug(f"Event {event.topic} is critical. Should persist to WAL.")
            
        for glob, queues in self.subscribers.items():
            if self._match_topic(glob, event.topic):
                for q in queues:
                    try:
                        q.put_nowait(event)
                    except asyncio.QueueFull:
                        self._descartar_el_mas_viejo(q, event)

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
        try:
            q.get_nowait()                  # fuera el más viejo
            q.put_nowait(event)
        except (asyncio.QueueEmpty, asyncio.QueueFull):
            pass                            # otra corrutina se nos adelantó
        n = self.dropped_counts.get(event.topic, 0) + 1
        self.dropped_counts[event.topic] = n
        # Se avisa en progresión geométrica (1, 10, 100, 1000...). Registrar
        # cada descarte volvería a generar un evento por descarte, que es
        # justo el bucle que se está cerrando aquí. Y `logger.debug` no pasa
        # por BusLogHandler en el nivel por defecto.
        if n == 1 or (n % 100 == 0):
            logger.debug("[bus] cola llena en '%s': %d evento(s) descartado(s)",
                         event.topic, n)

    def dropped_report(self) -> dict[str, int]:
        """Qué se ha descartado y cuánto. Lo enseña el panel de sistema."""
        return dict(self.dropped_counts)

    def _match_topic(self, glob: str, topic: str) -> bool:
        if glob == "*": return True
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
