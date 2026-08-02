import asyncio
import logging
import json
from .bus import MagiBus, BusEvent
from .policy.engine import PolicyEngine, Capability
from .rpc.ws_server import MockWebSocketServer

logger = logging.getLogger(__name__)

class Kernel:
    """
    Núcleo (Área 0). Único dueño del estado y bucle principal.
    Amalgama el Bus, el servidor RPC, y las áreas de dominio.
    """
    def __init__(self):
        self.bus = MagiBus()
        self.policy = PolicyEngine()
        self.rpc = MockWebSocketServer()
        self._setup_rpc()
        
    def _setup_rpc(self):
        # Registrar manejadores RPC base
        self.rpc.register_handler("rpc.hello", self._handle_hello)
        self.rpc.register_handler("rpc.policy.check", self._handle_policy_check)
        
    async def _handle_hello(self, payload):
        return {"status": "MAGI Kernel Online", "version": "1.0"}
        
    async def _handle_policy_check(self, payload):
        cap = Capability(name=payload.get("name"), resource=payload.get("resource"))
        res = self.policy.request_capability("rpc_client", cap)
        return {"granted": res.granted, "reason": res.reason}

    async def start(self):
        logger.info("Iniciando MAGI Kernel...")
        await self.rpc.start()
        
        # Test de emisión en bus
        await self.bus.publish(BusEvent(
            topic="system.started",
            payload={"status": "online"},
            critical=True
        ))
        
        logger.info("Kernel listo.")
        
    async def shutdown(self):
        logger.info("Apagando Kernel...")
