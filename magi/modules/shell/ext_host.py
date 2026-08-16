import json
import logging
import os
import struct
import sys

logger = logging.getLogger(__name__)

class NativeMessagingHost:
    """
    Protocolo de Mensajería Nativa (Native Messaging) de Chrome/Edge/Firefox.
    Lee de stdin y escribe en stdout usando prefijos de longitud de 32 bits (Little Endian).
    (P21.b.2 y A21-2)
    """
    def __init__(self):
        # Asegurarse de que stdin/stdout sean binarios en Windows
        if sys.platform == "win32":
            import msvcrt
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

    def read_message(self) -> dict:
        """Lee un mensaje desde la extensión."""
        raw_length = sys.stdin.buffer.read(4)
        if not raw_length:
            return None

        msg_length = struct.unpack('@I', raw_length)[0]
        # P21.b.2: Tamaño máximo 8 MB
        if msg_length > 8 * 1024 * 1024:
            raise ValueError("Mensaje demasiado grande")

        message = sys.stdin.buffer.read(msg_length).decode('utf-8')
        return json.loads(message)

    def send_message(self, message: dict):
        """Envía una respuesta a la extensión."""
        encoded = json.dumps(message).encode('utf-8')
        sys.stdout.buffer.write(struct.pack('@I', len(encoded)))
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()

    def run(self):
        logger.info("Iniciando Native Messaging Host...")
        while True:
            try:
                msg = self.read_message()
                if not msg:
                    break

                # A21-2: Aquí se validaría el emparejamiento (ext_pairing)
                # y se pasaría al Área 15 (Ingesta) a través del bus.
                logger.info(f"Mensaje recibido: {msg.get('action')}")

                # Respuesta base (sólo acuse de recibo y estado del IDE)
                response = {
                    "status": "ok",
                    "ide_state": "ready"
                }
                self.send_message(response)

            except Exception as e:
                logger.error(f"Error procesando mensaje: {e}")
                break
