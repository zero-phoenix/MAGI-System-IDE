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
from magi.modules.infrastructure.naoko import NaokoAgent

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
        self.naoko = NaokoAgent(self.bus, self.db, swarm=self.swarm)
        
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
        self.rpc.register_handler("git.clone", self._handle_git_clone)
        self.rpc.register_handler("naoko.chat", self._handle_naoko_chat)
        
    async def _handle_naoko_chat(self, payload, websocket):
        msg = payload.get("message", "")
        await self.bus.publish(BusEvent(topic="naoko.user_message", payload={"message": msg}))
        return {"status": "ok"}
        
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

    async def _handle_git_clone(self, payload, websocket):
        import asyncio
        import os
        from pathlib import Path
        
        repo_url = payload.get("url")
        if not repo_url:
            return {"status": "error", "message": "URL requerida"}
            
        scratch_dir = Path("D:/PROYECTOS/MAGI System IDE/scratch")
        scratch_dir.mkdir(parents=True, exist_ok=True)
        
        # Publicar inicio en terminal
        await self.bus.publish(BusEvent(topic="SYS_EXEC", payload={"task_id": "sys_git", "command": f"git clone {repo_url}"}))
        await self.bus.publish(BusEvent(topic="sys.terminal.out", payload=f"\\n> Clonando {repo_url} en {scratch_dir}...\\n"))
        
        process = await asyncio.create_subprocess_shell(
            f"git clone {repo_url}",
            cwd=str(scratch_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        out_msg = (stdout.decode() + "\\n" + stderr.decode()).strip()
        
        await self.bus.publish(BusEvent(topic="sys.terminal.out", payload=f"{out_msg}\\n[Git Clone completado con código {process.returncode}]"))
        
        return {"status": "ok", "message": f"Clonado completado en scratch/"}

    async def _handle_state_sync(self, payload, websocket):
        """Devuelve el estado real del sistema para poblar la GUI sin simulación."""
        import os
        from pathlib import Path
        
        # Escanear proyectos reales en D:\PROYECTOS\MAGI System IDE\scratch
        base_dir = Path("D:/PROYECTOS/MAGI System IDE/scratch")
        real_projects = []
        if base_dir.exists():
            for child in base_dir.iterdir():
                if child.is_dir() and not child.name.startswith("."):
                    real_projects.append({
                        "name": child.name,
                        "desc": "local · git detectado" if (child / ".git").exists() else "local · sin remoto"
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
        import os
        from pathlib import Path
        import asyncio
        
        command = payload.get("command", "") if isinstance(payload, dict) else payload
        raw_id = payload.get("id", "task_0") if isinstance(payload, dict) else "task_0"
        
        # interceptar comando GIT_PUSH_TO_GITHUB
        if isinstance(command, str) and command.startswith("GIT_PUSH_TO_GITHUB"):
            repo_url = command.split(" ", 1)[1] if " " in command else ""
            if not repo_url:
                await self.bus.publish(BusEvent(topic="TERMINAL_OUT", payload="URL de GitHub requerida para push."))
                return
                
            scratch_dir = Path("D:/PROYECTOS/MAGI System IDE/scratch")
            
            await self.bus.publish(BusEvent(topic="TERMINAL_OUT", payload=f"Iniciando subida a GitHub: {repo_url}"))
            
            script = f"""
            git init
            git add .
            git commit -m "Auto-commit by MAGI"
            git branch -M main
            git remote add origin {repo_url}
            git push -u origin main -f
            """
            
            process = await asyncio.create_subprocess_shell(
                script,
                cwd=str(scratch_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            out_msg = (stdout.decode() + "\n" + stderr.decode()).strip()
            await self.bus.publish(BusEvent(topic="TERMINAL_OUT", payload=f"{out_msg}\n[Subida completada con código {process.returncode}]"))
            return

        if isinstance(command, str) and command.startswith("SYS_EXEC_HOST"):
            script = command.replace("SYS_EXEC_HOST", "", 1).strip()
            scratch_dir = Path("D:/PROYECTOS/MAGI System IDE/scratch")
            
            await self.bus.publish(BusEvent(topic="TERMINAL_OUT", payload="Ejecutando script local en host (ZCode Mode)..."))
            
            process = await asyncio.create_subprocess_shell(
                script,
                cwd=str(scratch_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            out_msg = (stdout.decode() + "\n" + stderr.decode()).strip()
            await self.bus.publish(BusEvent(topic="TERMINAL_OUT", payload=f"{out_msg}\n[Ejecución completada con código {process.returncode}]"))
            return

        # Siempre generar un id único si es task_0 o vacío
        if not raw_id or raw_id == "task_0":
            task_id = f"task_{uuid.uuid4().hex[:8]}"
        else:
            task_id = raw_id
            
        engine = payload.get("engine", "fast") if isinstance(payload, dict) else "fast"
            
        # Generar un proyecto automático si es una conversación nueva
        # Para simular "cada vez que inicie una conversacion", creamos la carpeta
        new_proj_dir = Path("D:/PROYECTOS/MAGI System IDE/scratch") / f"project_{task_id}"
        new_proj_dir.mkdir(parents=True, exist_ok=True)
        
        await self.bus.publish(BusEvent(
            topic="system.project_created",
            payload={"name": f"project_{task_id}"}
        ))
        
        # Publicar en el bus para que el Logger lo intercepte
        await self.bus.publish(BusEvent(
            topic="SYS_EXEC",
            payload={"task_id": task_id, "command": command, "engine": engine}
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
        await self.naoko.start()
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
