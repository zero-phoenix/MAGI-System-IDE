"""
Puente entre el logging de Python y el bus de eventos.

Permite que la GUI pinte la terminal del servidor en tiempo real, y que Naoko
se entere de los errores. Las dos cosas son útiles y las dos son peligrosas:
un handler de logging que publica eventos puede realimentarse a sí mismo.

EL BUCLE QUE ESTO CIERRA
========================
Del registro del usuario, cientos de líneas idénticas:

    [ERROR] ... el handler 'sys.config' falló ... ImportError ...
    [WARNING] magi.core.bus: Cola llena para error.critical. Productor bloqueado.
    [WARNING] magi.core.bus: Cola llena para error.critical. Productor bloqueado.
    ... (x200)

La secuencia:

  1. Un handler RPC falla y se registra con nivel ERROR.
  2. Esta clase convierte el ERROR en un evento `error.critical`.
  3. Naoko está suscrita y DIAGNOSTICA cada uno con inferencia real.
  4. Su cola se llena.
  5. El bus registraba un WARNING por cada evento que no cabía...
  6. ...y ese WARNING volvía a pasar por AQUÍ, generando otro evento.

El sistema se ahogaba con sus propios mensajes de que se estaba ahogando.

LAS TRES DEFENSAS
=================
1. NO REENTRAR. Mientras se está publicando un evento de log, cualquier log
   que se genere por debajo se ignora. Corta el bucle de raíz.
2. NO REPETIR. El mismo mensaje repetido se cuenta, no se reenvía. Doscientas
   copias del mismo ImportError no informan más que una.
3. NO ESCALAR LO QUE NO ES CRÍTICO. Que falle un panel de la interfaz no es
   una emergencia del sistema. Solo se despierta a Naoko para lo que de
   verdad lo merece.
"""
import asyncio
import logging
import threading
import time

from magi.core.bus import BusEvent, MagiBus  # type: ignore

#: Módulos cuyos errores NO despiertan a Naoko.
#:
#: Que un panel de consulta no cargue es un fallo real y hay que verlo en la
#: terminal, pero no es una avería del sistema que merezca gastar inferencia
#: en diagnosticarla. Antes, cada uno de estos lanzaba un diagnóstico completo
#: del enjambre.
_NO_CRITICOS = (
    "magi.core.rpc",          # un handler RPC que falla degrada un panel
    "magi.core.obs",          # la propia observabilidad
    "magi.core.bus",          # el bus quejándose de sí mismo
    "websockets",             # la librería del transporte
    "asyncio",                # avisos del bucle de eventos
)

#: Ventana de supresión de mensajes idénticos.
_VENTANA_REPETIDOS_S = 30.0

#: Cuántos mensajes distintos se recuerdan para deduplicar.
_MAX_RECORDADOS = 256


class BusLogHandler(logging.Handler):
    """Publica los registros en el bus, sin poder ahogarse a sí mismo."""

    def __init__(self, bus: MagiBus):
        super().__init__()
        self.bus = bus
        self.loop = None
        self.setFormatter(logging.Formatter('[%(levelname)s] %(name)s: %(message)s'))
        # Reentrada por hilo: `emit` puede dispararse desde cualquiera.
        self._local = threading.local()
        self._vistos: dict[str, tuple[float, int]] = {}
        self.suprimidos = 0

    # ------------------------------------------------------------ ayudas

    def _repetido(self, clave: str) -> bool:
        """True si este mismo mensaje ya salió hace poco."""
        ahora = time.monotonic()
        anterior = self._vistos.get(clave)
        if anterior and ahora - anterior[0] < _VENTANA_REPETIDOS_S:
            self._vistos[clave] = (anterior[0], anterior[1] + 1)
            self.suprimidos += 1
            return True
        if len(self._vistos) > _MAX_RECORDADOS:
            # Se limpia lo caducado antes de crecer sin límite.
            self._vistos = {k: v for k, v in self._vistos.items()
                            if ahora - v[0] < _VENTANA_REPETIDOS_S}
        self._vistos[clave] = (ahora, 1)
        return False

    def _publicar(self, topic: str, payload: dict) -> None:
        # EL ORDEN IMPORTA: primero se comprueba que HAY bucle, y solo entonces
        # se construye la corrutina.
        #
        # Antes era `asyncio.create_task(self.bus.publish(...))` dentro de un
        # try/except RuntimeError. Python evalúa los argumentos primero, así
        # que `self.bus.publish(...)` ya había creado la corrutina cuando
        # `create_task` fallaba por no haber bucle: el except se la tragaba sin
        # awaitarla y el intérprete lo cantaba en cada arranque con
        # «RuntimeWarning: coroutine 'MagiBus.publish' was never awaited».
        # Aviso feo, sí, pero lo caro es lo otro: ese registro se perdía en
        # silencio, y son justo los de antes de levantar el bucle —los del
        # arranque— los que hacen falta cuando algo no arranca.
        try:
            bucle = asyncio.get_running_loop()
        except RuntimeError:
            return        # sin bucle todavía: no hay a quién avisar
        bucle.create_task(self.bus.publish(BusEvent(topic=topic,
                                                    payload=payload)))

    # -------------------------------------------------------------- emit

    def emit(self, record: logging.LogRecord) -> None:
        # DEFENSA 1: no reentrar. Si publicar este registro genera más
        # registros (y los genera: el bus avisa cuando descarta), esos se
        # ignoran en vez de realimentar la cola.
        if getattr(self._local, "dentro", False):
            return
        self._local.dentro = True
        try:
            msg = self.format(record)

            if self.loop is None:
                try:
                    self.loop = asyncio.get_running_loop()
                except RuntimeError:
                    return

            # DEFENSA 2: no repetir. Doscientas copias del mismo ImportError
            # no informan más que una, y sí llenan la cola.
            clave = f"{record.name}:{record.levelno}:{record.getMessage()[:200]}"
            if self._repetido(clave):
                return

            self._publicar("TERMINAL_OUT", {"message": msg})

            # DEFENSA 3: solo lo que de verdad es crítico despierta a Naoko.
            if record.levelno < logging.ERROR:
                return
            if record.name.startswith(_NO_CRITICOS):
                return
            if "NAOKO" in record.name or "NAOKO" in msg:
                return          # que no se diagnostique a sí misma
            self._publicar("error.critical", {"message": msg,
                                              "logger": record.name})
        except Exception:
            self.handleError(record)
        finally:
            self._local.dentro = False
