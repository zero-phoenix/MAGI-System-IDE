import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import websockets

from magi.core.bus import BusEvent, MagiBus  # type: ignore
from magi.core.paths import db_path, project_root
from magi.core.store.database import MagiDatabase

logger = logging.getLogger(__name__)

class WSServer:
    """
    Servidor RPC / WebSocket real para MAGI System IDE (Área 10).
    """
    def __init__(self, bus: MagiBus, host: str = "127.0.0.1", port: int = 20128):
        self.bus = bus
        self.host = host
        self.port = port
        self.handlers = {}
        self.clients: set[Any] = set()
        self.server = None
        self.db = MagiDatabase(str(db_path()))

        # Registramos endpoints internos
        self.register_handler("GET_TELEMETRY", self._handle_get_telemetry)
        self.register_handler("GET_FILE_TREE", self._handle_get_file_tree)
        self.register_handler("GET_FILE_CONTENT", self._handle_get_file_content)

    def register_handler(self, method: str, handler: Callable[[Any, Any], Awaitable[Any]]):
        self.handlers[method] = handler

    async def start(self):
        logger.info(f"Servidor RPC iniciando en ws://{self.host}:{self.port}")
        self.bus.subscribe("*", self._handle_bus_event)
        self.server = await websockets.serve(self._handler, self.host, self.port)

    async def close(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def wait_closed(self):
        if self.server:
            await self.server.wait_closed()

    async def _handle_bus_event(self, event: BusEvent):
        if not self.clients:
            return

        message = json.dumps({
            "type": "event",
            "topic": event.topic,
            "payload": event.payload
        })

        await asyncio.gather(
            *[self._send_safe(client, message) for client in self.clients]
        )

    async def _send_safe(self, client, message: str):
        try:
            await client.send(message)
        except websockets.exceptions.ConnectionClosed:
            pass

    async def _handler(self, websocket):
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
                    await self._process_rpc(websocket, '{"method": "magi_connect", "params": {"binary_mode": true}}')
                else:
                    await self._process_rpc(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            logger.info("Cliente GUI desconectado.")

    async def _process_rpc(self, websocket, message: str):
        """
        Atiende una petición RPC. NUNCA deja escapar una excepción.

        DOS FALLOS QUE TENÍA ESTO, LOS DOS REPRODUCIDOS
        ===============================================
        1. Solo capturaba `json.JSONDecodeError`. Cualquier excepción de un
           handler subía hasta el `async for message in websocket` del bucle
           de conexión, que solo captura `ConnectionClosed`, y MATABA LA
           CONEXIÓN ENTERA:

               handler que lanza -> CONEXIÓN CERRADA (1011)
               conexión tras el fallo -> MUERTA

           Una petición mal formada dejaba a la interfaz sin kernel. Y da
           igual lo defensivo que sea cada handler: basta con que uno falle
           una vez.

        2. `if result is not None` no respondía cuando un handler devolvía
           `None`. El cliente se quedaba esperando una respuesta que no
           llegaba nunca — con el helper `rpc()` de la interfaz, la promesa
           colgada hasta el tiempo límite y el panel girando.

        Ahora SIEMPRE se responde y ningún fallo de handler tumba el canal.
        """
        req_id = "0"
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            logger.error("Mensaje no es JSON válido.")
            await self._reply(websocket, req_id, False,
                              error="el mensaje no es JSON válido")
            return

        try:
            method = data.get("type") or data.get("method")
            payload = data.get("payload") or data.get("params") or data
            req_id = data.get("id") or data.get("request_id", "0")

            if method not in self.handlers:
                await self._reply(websocket, req_id, False,
                                  error=f"Method {method} not found")
                return

            result = await self.handlers[method](payload, websocket)
            await self._reply(websocket, req_id, True, result=result)

        except asyncio.CancelledError:
            raise                      # parar el servidor sí debe propagarse
        except websockets.exceptions.ConnectionClosed:
            raise                      # lo gestiona el bucle de conexión
        except Exception as e:
            # El error viaja al cliente en vez de cerrarle el canal: así el
            # usuario ve QUÉ falló en lugar de una desconexión inexplicable.
            logger.exception("[rpc] el handler '%s' falló", data.get("type"))
            await self._reply(websocket, req_id, False,
                              error=f"{type(e).__name__}: {e}")

    async def _reply(self, websocket, req_id, ok: bool, result=None,
                     error: str | None = None) -> None:
        """Responde siempre. Si el envío falla, no se arrastra al bucle."""
        cuerpo = {"id": req_id, "ok": ok}
        if ok:
            cuerpo["result"] = result
        else:
            cuerpo["error"] = error or "error desconocido"
        try:
            await websocket.send(json.dumps(cuerpo, default=str))
        except websockets.exceptions.ConnectionClosed:
            pass                       # el cliente ya se fue; no es un error
        except Exception as e:         # pragma: no cover
            logger.warning("[rpc] no se pudo responder a %s: %s", req_id, e)

    async def _handle_get_telemetry(self, payload: Any, websocket: Any) -> Any:
        return await self.db.get_telemetry()

    async def _handle_get_file_tree(self, payload: Any, websocket: Any) -> Any:
        import os

        base_dir = project_root()

        def build_tree(dir_path):
            tree = []
            try:
                for entry in sorted(os.scandir(dir_path), key=lambda e: (not e.is_dir(), e.name)):
                    if entry.name in ('.git', 'node_modules', '__pycache__', 'dist', 'build', '.gemini'):
                        continue
                    if entry.is_dir():
                        tree.append({"name": entry.name, "type": "folder", "path": entry.path, "children": build_tree(entry.path)})
                    else:
                        tree.append({"name": entry.name, "type": "file", "path": entry.path})
            except PermissionError:
                pass
            return tree

        return build_tree(base_dir)

    async def _handle_get_file_content(self, payload: Any, websocket: Any) -> Any:
        import os
        path = payload.get("path")
        if not path or not os.path.exists(path) or not os.path.isfile(path):
            return {"error": "File not found or invalid path"}
        try:
            with open(path, encoding="utf-8") as f:
                return {"path": path, "content": f.read()}
        except Exception as e:
            return {"error": str(e)}

    async def simulate_message_from_gui(self, message: str) -> str:
        """Helper para pruebas unitarias sin levantar el websocket real."""
        class DummyWebSocket:
            def __init__(self):
                self.responses = []
            async def send(self, data):
                self.responses.append(data)

        ws = DummyWebSocket()
        await self._process_rpc(ws, message)
        return ws.responses[0] if ws.responses else ""
