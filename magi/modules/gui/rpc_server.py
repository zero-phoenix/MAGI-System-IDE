import json


class RPCServer:
    """
    Servidor RPC / WebSocket mock para IPC de GUI (P10.a).
    """
    def __init__(self):
        self.clients = []
        self.handlers = {
            "magi_connect": self._handle_connect,
            "magi_estop": self._handle_estop
        }

    async def _handle_connect(self, payload):
        token = payload.get("token")
        if token == "secret_gui_token":
            return {"status": "ok", "session_id": "sess_1"}
        return {"status": "error", "message": "Invalid token"}

    async def _handle_estop(self, payload):
        # Invocaria el E-STOP del Area 8 real
        return {"status": "ok", "action": "HALTED"}

    async def process_message(self, raw_msg: str) -> str:
        try:
            req = json.loads(raw_msg)
            method = req.get("method")
            if method in self.handlers:
                resp = await self.handlers[method](req.get("params", {}))
                return json.dumps({"id": req.get("id"), "result": resp})
            return json.dumps({"id": req.get("id"), "error": "Method not found"})
        except Exception as e:
            return json.dumps({"error": str(e)})
