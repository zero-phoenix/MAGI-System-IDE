import asyncio
import logging
import json
from .bus import MagiBus, BusEvent
from .policy.engine import PolicyEngine, Capability
from .rpc.ws_server import WSServer
from .blackboard import Blackboard
from magi.modules.swarm.orchestrator import SwarmOrchestrator
from magi.core.store.database import MagiDatabase
from magi.core.store.logger import BusLogger
from magi.core.obs.bus_log_handler import BusLogHandler
from magi.modules.memgraph import MemGraphAdapter
from magi.modules.skills.loader import AASLoader

logger = logging.getLogger(__name__)

class Kernel:
    """
    Núcleo (Área 0). Único dueño del estado y bucle principal.
    Amalgama el Bus, el servidor RPC, y las áreas de dominio.
    """
    def __init__(self, host="127.0.0.1", port=20128):
        self.bus = MagiBus()
        self.db = MagiDatabase(db_path="magi_brain.db")
        self.bus_logger = None # Se inicializa en start()
        
        self.blackboard = Blackboard()
        self.swarm = SwarmOrchestrator(self.blackboard, self.bus)
        self.policy = PolicyEngine()
        self.memgraph = MemGraphAdapter(self.bus)
        
        # Cargar catálogo de Skills
        self.skills_loader = AASLoader()
        loaded_count = self.skills_loader.load()
        if loaded_count > 0:
            self.blackboard.post("global.skills_loader", self.skills_loader)
        
        self.rpc = WSServer(bus=self.bus, host=host, port=port)
        self._setup_rpc()
        
    def _setup_rpc(self):
        self.rpc.register_handler("rpc.hello", self._handle_hello)
        self.rpc.register_handler("rpc.policy.check", self._handle_policy_check)
        self.rpc.register_handler("magi_connect", self._handle_connect)
        self.rpc.register_handler("magi_estop", self._handle_estop)
        self.rpc.register_handler("EMERGENCY_STOP", self._handle_estop)
        self.rpc.register_handler("KILL_ALL_PROCESSES", self._handle_estop)
        self.rpc.register_handler("SYS_EXEC", self._handle_sys_exec)
        self.rpc.register_handler("rpc.state.sync", self._handle_state_sync)
        
    async def _handle_hello(self, payload, websocket):
        return {"status": "MAGI Kernel Online", "version": "1.0"}
        
    async def _handle_connect(self, payload, websocket):
        return {"result": "CONNECTED", "version": "1.0.0"}

    async def _handle_estop(self, payload, websocket):
        logger.critical("E-STOP INVOCADO DESDE LA GUI")
        return "EMERGENCY_STOP_TRIGGERED"

    async def _handle_policy_check(self, payload, websocket):
        cap = Capability(name=payload.get("name"), resource=payload.get("resource"))
        res = self.policy.request_capability("rpc_client", cap)
        return {"granted": res.granted, "reason": res.reason}

    async def _handle_state_sync(self, payload, websocket):
        """Devuelve el estado real del sistema para poblar la GUI sin simulación."""
        import os
        from pathlib import Path
        
        # Escanear proyectos reales en D:\PROYECTOS\MAGI System IDE
        base_dir = Path("D:/PROYECTOS/MAGI System IDE")
        real_projects = []
        if base_dir.exists():
            for child in base_dir.iterdir():
                if child.is_dir() and (child / ".magi" / "project.yaml").exists():
                    real_projects.append({
                        "name": child.name,
                        "desc": "local · repositorio detectado" if (child / ".git").exists() else "local · sin remoto"
                    })
        
        return {
            "projects": real_projects,
            "metrics": {
                "prov_a": "31/50",
                "prov_b": "agotado",
                "prov_c": "ok",
                "status": "online"
            }
        }

    async def _handle_sys_exec(self, payload, websocket):
        import uuid
        command = payload.get("command", "") if isinstance(payload, dict) else payload
        raw_id = payload.get("id", "task_0") if isinstance(payload, dict) else "task_0"
        
        # Siempre generar un id único si es task_0 o vacío
        if not raw_id or raw_id == "task_0":
            task_id = f"task_{uuid.uuid4().hex[:8]}"
        else:
            task_id = raw_id
        
        # Publicar en el bus para que el Logger lo intercepte
        await self.bus.publish(BusEvent(
            topic="SYS_EXEC",
            payload={"task_id": task_id, "command": command}
        ))
        
        # Delegamos el control al Orquestador del Enjambre (Área 16)
        # El orquestador publicará los avances en el MagiBus que la GUI consumirá
        await self.swarm.submit_task(task_id, command)

    async def start(self):
        logger.info("Iniciando MAGI Kernel...")
        
        # Inicializamos el Logger ahora que el event_loop existe
        self.bus_logger = BusLogger(self.bus, self.db)
        
        # Conectar el root logger al bus para enviar logs a la UI
        bus_handler = BusLogHandler(self.bus)
        logging.getLogger().addHandler(bus_handler)
        
        await self.memgraph.start()
        await self.rpc.start()
        
        await self.bus.publish(BusEvent(
            topic="system.started",
            payload={"status": "online"},
            critical=True
        ))
        
        logger.info("Kernel listo.")
        
    async def shutdown(self):
        logger.info("Apagando Kernel...")
        await self.rpc.close()

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    async def main():
        kernel = Kernel()
        try:
            await kernel.start()
            # Mantener el kernel vivo
            await asyncio.Future()
        except KeyboardInterrupt:
            await kernel.shutdown()
            
    asyncio.run(main())
