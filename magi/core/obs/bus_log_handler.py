import logging
import asyncio
from typing import Any
from magi.core.bus import MagiBus, BusEvent  # type: ignore

class BusLogHandler(logging.Handler):
    """
    Handler de logging que intercepta mensajes y los envía al MagiBus (y de ahí al WebSocket).
    Permite que la GUI renderice la terminal del servidor en tiempo real.
    """
    def __init__(self, bus: MagiBus):
        super().__init__()
        self.bus = bus
        self.loop = None
        self.setFormatter(logging.Formatter('[%(levelname)s] %(name)s: %(message)s'))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            
            if self.loop is None:
                try:
                    self.loop = asyncio.get_running_loop()
                except RuntimeError:
                    # Si no hay loop, no podemos enviarlo al bus asíncrono
                    return
            
            # Crear tarea para publicar en el bus sin bloquear
            asyncio.create_task(
                self.bus.publish(BusEvent(
                    topic="TERMINAL_OUT",
                    payload={"message": msg}
                ))
            )
            
            if record.levelno >= logging.ERROR and "NAOKO" not in record.name and "NAOKO" not in msg:
                asyncio.create_task(
                    self.bus.publish(BusEvent(
                        topic="error.critical",
                        payload={"message": msg}
                    ))
                )
        except Exception:
            self.handleError(record)
