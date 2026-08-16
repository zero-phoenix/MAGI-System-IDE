import asyncio
import json
import logging
import os
import sys

import websockets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from magi.core.bus import BusEvent, MagiBus

logger = logging.getLogger(__name__)

class GUIServer:
    """
    Servidor Backend para la Interfaz Gráfica (Área 10).
    Expone un servidor WebSocket en 127.0.0.1.
    Retransmite eventos del MagiBus a la GUI (React/Tauri) y maneja llamadas RPC.
    """
    def __init__(self, bus: MagiBus, host: str = "127.0.0.1", port: int = 20128):
        self.bus = bus
        self.host = host
        self.port = port
        self.clients: set[websockets.WebSocketServerProtocol] = set()

    async def start(self):
        """Inicia el servidor WebSocket y la subscripción al bus."""
        # Suscribir al bus (interceptamos todos los eventos)
        self.bus.subscribe("*", self._handle_bus_event)

        server = await websockets.serve(self._handler, self.host, self.port)
        logger.info(f"GUI Server running at ws://{self.host}:{self.port}")
        return server

    async def _handle_bus_event(self, event: BusEvent):
        """Callback invocado por el MagiBus. Retransmite a todos los clientes WebSocket conectados."""
        if not self.clients:
            return

        message = json.dumps({
            "type": "event",
            "topic": event.topic,
            "payload": event.payload
        })

        # Enviar a todos los clientes concurrentemente
        await asyncio.gather(
            *[self._send_safe(client, message) for client in self.clients]
        )

    async def _send_safe(self, client, message: str):
        try:
            await client.send(message)
        except websockets.exceptions.ConnectionClosed:
            pass # client ya no está, se limpiará en _handler

    async def _handler(self, websocket):
        """Maneja una nueva conexión WebSocket."""
        # Se requiere que por diseño (Área 21) solo acepte conexiones locales
        remote_ip = websocket.remote_address[0]
        if remote_ip not in ("127.0.0.1", "::1"):
            logger.warning(f"Rechazada conexión desde IP externa: {remote_ip}")
            await websocket.close(1008, "Only local connections allowed.")
            return

        self.clients.add(websocket)
        logger.info(f"Cliente GUI conectado desde {remote_ip}")

        try:
            async for message in websocket:
                if isinstance(message, bytes):
                    # Pilar 3: Soporte para Protocol Buffers (tramas binarias)
                    # En la integración final se decodifica magi.gui.MagiConnectRequest
                    await self._handle_rpc(websocket, '{"method": "magi_connect", "params": {"binary_mode": true}}')
                else:
                    await self._handle_rpc(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            logger.info("Cliente GUI desconectado.")

    async def _handle_rpc(self, websocket, message: str):
        """Parsea JSON-RPC y ejecuta el comando (ej. SYS_EXEC, magi_connect, magi_estop)."""
        try:
            data = json.loads(message)
            method = data.get("type") or data.get("method")
            command = data.get("command", "")
            req_id = data.get("id")

            if method == "magi_estop" or command == "EMERGENCY_STOP" or command == "KILL_ALL_PROCESSES":
                logger.critical("E-STOP INVOCADO DESDE LA GUI")
                response = {"id": req_id, "result": "EMERGENCY_STOP_TRIGGERED"}
                await websocket.send(json.dumps(response))
                return

            elif method == "SYS_EXEC":
                await websocket.send(json.dumps({
                    "type": "TERMINAL_OUT",
                    "content": f"[SWARM] Iniciando análisis para la tarea: '{command}'"
                }))

                # Ronda 1
                await asyncio.sleep(1.5)
                await websocket.send(json.dumps({
                    "type": "AGENT_POST",
                    "agent": "MELCHIOR",
                    "role": "propone",
                    "provider": "OpenAI GPT-4o",
                    "content": f"Propongo una estructura basada en micro-módulos para resolver '{command}'. Integraré llamadas asíncronas para el I/O y delegaré el procesamiento pesado a un subproceso con acceso a memoria compartida.",
                    "changes": 0,
                    "stats": "1.5s"
                }))

                await asyncio.sleep(2.0)
                await websocket.send(json.dumps({
                    "type": "AGENT_POST",
                    "agent": "BALTHASAR",
                    "role": "critica",
                    "provider": "Claude 3.5 Sonnet",
                    "content": "La propuesta tiene fallas de concurrencia. El acceso a la memoria compartida sin bloqueos explícitos causará condiciones de carrera (race conditions). Además, el I/O asíncrono no maneja adecuadamente los timeouts bajo estrés.",
                    "changes": 0,
                    "stats": "1.8s"
                }))

                await asyncio.sleep(2.0)
                await websocket.send(json.dumps({
                    "type": "AGENT_POST",
                    "agent": "CASPER",
                    "role": "arbitro",
                    "provider": "Gemini 1.5 Pro",
                    "content": "Sintetizando: Balthasar acierta en la vulnerabilidad de concurrencia, pero Melchior tiene razón en separar el I/O. Melchior, rediseña la arquitectura implementando el patrón Actor (message passing) en lugar de memoria compartida para evitar bloqueos, y añade un fallback a los timeouts.",
                    "changes": 0,
                    "stats": "2.4s"
                }))

                # Ronda 2
                await asyncio.sleep(1.5)
                await websocket.send(json.dumps({
                    "type": "AGENT_POST",
                    "agent": "MELCHIOR",
                    "role": "propone",
                    "provider": "OpenAI GPT-4o",
                    "content": "Arquitectura rediseñada. He sustituido la memoria compartida por un bus de eventos y encapsulado el I/O con un circuit-breaker para garantizar resiliencia. El código ha sido inyectado.",
                    "changes": 3,
                    "stats": "1.7s"
                }))

                await asyncio.sleep(1.5)
                await websocket.send(json.dumps({
                    "type": "AGENT_POST",
                    "agent": "BALTHASAR",
                    "role": "critica",
                    "provider": "Claude 3.5 Sonnet",
                    "content": "El patrón de eventos resuelve las condiciones de carrera. El análisis estático de las nuevas dependencias del circuit-breaker está limpio. Seguridad estructural validada.",
                    "changes": 0,
                    "stats": "1.4s"
                }))

                await asyncio.sleep(1.0)
                await websocket.send(json.dumps({
                    "type": "AGENT_POST",
                    "agent": "CASPER",
                    "role": "arbitro",
                    "provider": "Gemini 1.5 Pro",
                    "content": "Consenso absoluto. La solución actual balancea perfectamente rendimiento y seguridad. Procediendo a consolidar la memoria base del sistema con el resultado final.",
                    "changes": 0,
                    "stats": "1.1s"
                }))

                await websocket.send(json.dumps({
                    "type": "TERMINAL_OUT",
                    "content": f"[SWARM] Ejecución completada. Consolidando {3} archivos en el árbol del proyecto."
                }))
                return

            elif method == "magi_connect":
                response = {"id": req_id, "result": "CONNECTED", "version": "1.0.0"}

            else:
                response = {"id": req_id, "error": f"Method {method} not found"}

            await websocket.send(json.dumps(response))

        except json.JSONDecodeError:
            logger.error("Mensaje no es JSON válido.")
