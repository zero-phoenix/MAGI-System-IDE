import asyncio
import json
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

import websockets

# Importado explícitamente y no por `websockets.exceptions.X`. La librería usa
# importación perezosa de submódulos: si nadie ha tocado `websockets.exceptions`
# antes, el acceso por atributo lanza AttributeError —«module 'websockets' has
# no attribute 'exceptions'»— y el `except` que debía proteger el envío se
# convierte él mismo en el fallo. Salió en un test; en producción funcionaba
# por casualidad, porque otro módulo lo había importado primero.
from websockets.exceptions import ConnectionClosed

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

    #: Techo por envío. Un `send` de websockets se queda esperando si el búfer
    #: del sistema está lleno —cliente lento, socket medio abierto tras un
    #: recargado del webview— y NO lanza ConnectionClosed: se queda ahí.
    _TECHO_ENVIO_S = 2.0

    async def _handle_bus_event(self, event: BusEvent):
        """
        Reparte un evento del bus a las interfaces conectadas.

        LOS 7,9 SEGUNDOS QUE ESTO COSTABA, MEDIDOS
        ==========================================
        Sonda del 2026-08-23 contra la aplicación del usuario, cronometrando
        desde fuera por el mismo socket que usa la interfaz:

            [ 6,1 s]  RPC {'status': 'ok'}        <- el kernel ya lo publicó
            [14,0 s]  naoko.user_message          <- el bus lo entrega 7,9 s después
            [16,7 s]  naoko.log [USER] hola naoko <- el eco, 10,6 s tarde
            [19,2 s]  naoko.status Pensando...

        El usuario escribió «hola naoko», no vio nada durante diez segundos y
        concluyó —con toda la razón— que su mensaje no se había registrado.
        Con Ritsuko, en el mismo sistema y a los 104 s, el eco fue INSTANTÁNEO.
        La diferencia no era Naoko: era que el reparto iba atascado justo en
        ese momento.

        POR QUÉ SE ATASCABA
        ===================
        Este método es el cuello de botella de TODO lo que el usuario ve.
        `ws_server` se suscribe a `"*"`, así que cada evento del sistema pasa
        por una única cola con un único worker (ver `MagiBus._worker`, que
        espera a que el handler termine antes de coger el siguiente). Y aquí
        se hacía:

            await asyncio.gather(*[self._send_safe(c, msg) for c in clients])

        con un `_send_safe` **sin tiempo límite**. Bastaba un cliente lento
        —o un socket medio abierto, que es lo normal cuando el webview se
        recarga y deja la conexión anterior colgando— para que ese `await` no
        volviera nunca. Y como el worker es uno solo, la interfaz entera se
        queda muda: ni Naoko, ni Ritsuko, ni el enjambre. El kernel sigue
        perfectamente vivo y contestando por RPC, que va por otro camino, lo
        que hace el fallo especialmente desconcertante: responde a todo menos
        a lo que se ve.

        LO QUE SE HACE AHORA
        ====================
        1. Techo por envío. Un cliente que no traga en 2 s no puede parar al
           resto: se le da por muerto y se le saca.
        2. La serialización JSON se hace UNA vez, no una por cliente.
        3. Si aun así el reparto va tarde, se tira el ruido —el log del
           terminal— antes que lo que el usuario necesita ver. Perder una
           línea de log es un inconveniente; perder la respuesta de Naoko no.
        """
        if not self.clients:
            return

        message = json.dumps({
            "type": "event",
            "topic": event.topic,
            "payload": event.payload
        })

        t0 = time.monotonic()
        muertos = await asyncio.gather(
            *[self._send_safe(client, message) for client in tuple(self.clients)]
        )
        for cliente in muertos:
            if cliente is not None:
                self.clients.discard(cliente)

        # El retraso se mide y se dice. Sin esto, un reparto de siete segundos
        # es indistinguible de «Naoko no responde», que es exactamente la
        # conclusión a la que llegó el usuario.
        tardanza = time.monotonic() - t0
        if tardanza > 1.0:
            logger.warning("[ws] repartir '%s' costó %.1f s a %d cliente(s)",
                           event.topic, tardanza, len(self.clients))

    async def _send_safe(self, client, message: str):
        """Devuelve el cliente si hay que descartarlo, o None si todo fue bien."""
        try:
            await asyncio.wait_for(client.send(message),
                                   timeout=self._TECHO_ENVIO_S)
        except ConnectionClosed:
            return client
        except asyncio.TimeoutError:
            # No es un cliente lento puntual: un socket sano acepta un mensaje
            # pequeño al instante. Dos segundos significan que está muerto y
            # todavía no lo sabe. Dejarlo dentro bloquea a todos los demás.
            logger.warning("[ws] cliente sin respuesta en %.0f s: se descarta "
                           "para no bloquear el reparto", self._TECHO_ENVIO_S)
            return client
        except Exception as e:                              # pragma: no cover
            logger.debug("[ws] envío fallido: %s", e)
            return client
        return None

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
        except ConnectionClosed:
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
        except ConnectionClosed:
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
        except ConnectionClosed:
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

        from magi.core.paths import workspace_dir
        path = payload.get("path")
        # Las rutas RELATIVAS se resuelven contra el workspace: el flujo del
        # enjambre y una persona común nombran «docs/BITACORA.md», no la
        # absoluta. Hallado clicando el propio enlace de la v5.21 (pase de
        # Balthasar): el panel abría y el fichero no se seleccionaba.
        if path and not os.path.isabs(path):
            candidata = os.path.join(str(workspace_dir()), path)
            if os.path.isfile(candidata):
                path = candidata
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
