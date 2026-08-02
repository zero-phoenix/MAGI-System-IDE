import asyncio
import json
import logging
from typing import Callable, Awaitable, Any

logger = logging.getLogger(__name__)

class MockWebSocketServer:
    """
    Servidor RPC / WebSocket simulado para pruebas de integración (Área 10).
    En producción usaría el módulo 'websockets' sobre 127.0.0.1.
    """
    def __init__(self, port: int = 8080):
        self.port = port
        self.handlers = {}
        self.connected = False
        
    def register_handler(self, method: str, handler: Callable[[Any], Awaitable[Any]]):
        self.handlers[method] = handler
        
    async def start(self):
        logger.info(f"Servidor RPC iniciando en ws://127.0.0.1:{self.port}")
        self.connected = True
        
    async def simulate_message_from_gui(self, message: str) -> str:
        """Simula recibir un JSON de Tauri/React y procesarlo"""
        try:
            data = json.loads(message)
            method = data.get("method")
            payload = data.get("payload", {})
            req_id = data.get("request_id", "0")
            
            if method in self.handlers:
                result = await self.handlers[method](payload)
                return json.dumps({"request_id": req_id, "ok": True, "result": result})
            else:
                return json.dumps({"request_id": req_id, "ok": False, "error": {"message": "Method not found"}})
                
        except json.JSONDecodeError:
             return json.dumps({"ok": False, "error": {"message": "Invalid JSON"}})
