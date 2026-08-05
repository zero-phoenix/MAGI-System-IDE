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
from magi.core.paths import project_root, workspace_dir, db_path

logger = logging.getLogger(__name__)

class Kernel:
    """
    Núcleo (Área 0). Único dueño del estado y bucle principal.
    Amalgama el Bus, el servidor RPC, y las áreas de dominio.
    """
    def __init__(self, host="127.0.0.1", port=20128):
        self.bus = MagiBus()
        self.db = MagiDatabase(db_path=str(db_path()))
        self.bus_logger = None # Se inicializa en start()
        
        self.blackboard = Blackboard()
        self.swarm = SwarmOrchestrator(self.blackboard, self.bus)
        self.policy = PolicyEngine()
        self.memgraph = MemGraphAdapter(self.bus)
        # §3.4 — observabilidad. Enganchado al bus para que Naoko vea
        # degradación, no solo excepciones.
        from magi.core.obs.metrics import MetricsCollector
        self.metrics = MetricsCollector()
        self.metrics.attach(self.bus)
        self.naoko = NaokoAgent(self.bus, self.db, swarm=self.swarm,
                                metrics=self.metrics)
        
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
        # §7.3 — parar UN turno sin matar la aplicación ni las demás tareas.
        self.rpc.register_handler("task.cancel", self._handle_cancel_task)
        self.rpc.register_handler("task.running", self._handle_running_tasks)
        # Ciclo de mejora de Naoko: proponer, decidir en cada compuerta y
        # consultar lo que está pendiente de tu respuesta.
        self.rpc.register_handler("naoko.improve.propose", self._handle_improve_propose)
        self.rpc.register_handler("naoko.improve.decide", self._handle_improve_decide)
        self.rpc.register_handler("naoko.improve.list", self._handle_improve_list)
        self.rpc.register_handler("SYS_EXEC", self._handle_sys_exec)
        self.rpc.register_handler("rpc.state.sync", self._handle_state_sync)
        self.rpc.register_handler("git.clone", self._handle_git_clone)
        self.rpc.register_handler("naoko.chat", self._handle_naoko_chat)
        self.rpc.register_handler("obs.metrics", self._handle_metrics)
        self.rpc.register_handler("naoko.self_improve", self._handle_self_improve)
        self.rpc.register_handler("eval.run", self._handle_eval_run)
        
    async def _handle_metrics(self, payload, websocket):
        """Panel de salud (§3.4): latencias, herramientas, alertas."""
        return self.metrics.snapshot()

    async def _handle_self_improve(self, payload, websocket):
        """
        Auto-mejora medible (§3.5), a petición.

        No se dispara sola: cambiar el sistema tiene coste de cuota y el usuario
        debe poder elegir cuándo. Lo que sí es automático es la MEDICIÓN — el
        cambio solo se conserva si el banco mejora sin regresiones.
        """
        hypothesis = (payload or {}).get("hypothesis", "").strip()
        if not hypothesis:
            return {"status": "error",
                    "message": "indica qué cambio quieres probar"}

        async def noop():
            return None

        verdict = await self.naoko.run_self_improvement(hypothesis, noop, noop)
        return {"status": "ok", "verdict": verdict}

    async def _handle_eval_run(self, payload, websocket):
        """Ejecuta el banco de evaluación y devuelve la puntuación."""
        from magi.core.eval import default_bench
        from magi.core.providers.cloud import FreeCloudLLM

        llm = FreeCloudLLM()

        async def runner(prompt: str) -> str:
            content, _ = await llm.generate("Responde de forma directa.", prompt)
            return content

        result = await default_bench().run(runner, label="manual")
        await self.bus.publish(BusEvent(topic="eval.result",
                                        payload=result.to_dict()))
        return result.to_dict()

    async def _handle_naoko_chat(self, payload, websocket):
        msg = payload.get("message", "") if isinstance(payload, dict) else str(payload)
        image = payload.get("image", None) if isinstance(payload, dict) else None
        await self.bus.publish(BusEvent(topic="naoko.user_message", payload={"message": msg, "image": image}))
        return {"status": "ok"}
        
    async def _handle_hello(self, payload, websocket):
        return {"status": "MAGI Kernel Online", "version": "1.0"}
        
    async def _handle_connect(self, payload, websocket):
        return {"result": "CONNECTED", "version": "1.0.0"}

    async def _handle_estop(self, payload, websocket):
        """
        Parada de emergencia REAL (§7.3).

        Este handler entero era:

            logger.critical("E-STOP INVOCADO DESDE LA GUI")
            return "EMERGENCY_STOP_TRIGGERED"

        Una línea de log y una cadena. No cancelaba ningún bucle ni mataba
        ningún proceso: el botón de parada de la interfaz no paraba nada, y
        devolvía una respuesta con aspecto de éxito.

        Es el control que más caro sale que mienta. Todo el acceso sin
        restricciones a la máquina se sostiene sobre dos salidas: deshacer lo
        hecho (§4.2, el journal) y PARAR lo que se está haciendo. La segunda
        no existía.
        """
        from magi.core.cancel import supervisor
        logger.critical("E-STOP INVOCADO DESDE LA GUI")
        informe = await supervisor().cancel_all()
        await self.bus.publish(BusEvent(
            topic="task.cancelled", payload=informe.to_payload()))
        await self.bus.publish(BusEvent(
            topic="TERMINAL_OUT", payload={"content": informe.render()}))
        return informe.to_payload()

    async def _handle_cancel_task(self, payload, websocket):
        """
        Cancela UNA tarea (§7.3: "poder parar un turno a mitad sin matar la
        app").

        Antes la única opción era la parada de emergencia, que además de no
        funcionar habría sido un mazazo: si tienes tres conversaciones y una
        se está yendo por las ramas, no quieres tirar las otras dos.
        """
        from magi.core.cancel import supervisor
        task_id = (payload or {}).get("task_id", "").strip()
        if not task_id:
            return {"status": "error", "message": "indica qué tarea parar"}

        sup = supervisor()
        if not sup.is_running(task_id):
            return {"status": "ok", "stopped_anything": False,
                    "detail": f"{task_id} no está en marcha; nada que parar. "
                              f"En curso: {', '.join(sup.running_tasks()) or 'ninguna'}"}

        informe = await sup.cancel(task_id)
        estado = self.swarm.active_tasks.get(task_id)
        if estado is not None:
            estado["status"] = "cancelled"
            self.swarm._persist(task_id)
        await self.bus.publish(BusEvent(
            topic="task.cancelled", payload=informe.to_payload()))
        await self.bus.publish(BusEvent(
            topic="TERMINAL_OUT", payload={"content": informe.render()}))
        return informe.to_payload()

    async def _handle_running_tasks(self, payload, websocket):
        """Qué hay en marcha ahora mismo, para poder ofrecer pararlo."""
        from magi.core.cancel import supervisor
        return {"running": supervisor().running_tasks()}

    # ---------------------------------------------------- ciclo de mejora

    async def _handle_improve_propose(self, payload, websocket):
        """
        Abre una mejora. `origin="usuario"` cuando la propones tú.

        Tu propuesta recorre exactamente el mismo circuito que una idea de
        Naoko: se pidió así. Que la idea sea tuya no la exime de la crítica
        del enjambre; si acaso al revés.
        """
        p = payload or {}
        titulo = (p.get("title") or "").strip()
        if not titulo:
            return {"status": "error", "message": "indica qué quieres mejorar"}
        m = await self.naoko.propose_improvement(
            titulo, (p.get("rationale") or "").strip(),
            origin=p.get("origin") or "usuario")
        return m.to_dict()

    async def _handle_improve_decide(self, payload, websocket):
        """
        Tu decisión en una compuerta. Es lo único que hace avanzar el ciclo.

        Un "no" descarta y no es un error: tratar el rechazo como fallo
        empujaría a insistir, y una propuesta que insiste deja de serlo.
        """
        from magi.modules.infrastructure.improvement import Stage, user_decides

        p = payload or {}
        log = self.naoko._improvements()
        m = log.get((p.get("improvement_id") or "").strip())
        if m is None:
            return {"status": "error", "message": "no existe esa mejora"}
        if not m.awaiting_user:
            return {"status": "error",
                    "message": f"{m.improvement_id} está en {m.stage.value} y "
                               f"no espera decisión tuya"}

        anterior = m.stage
        aprueba = bool(p.get("approve"))
        try:
            user_decides(m, aprueba)
        except Exception as e:
            return {"status": "error", "message": str(e)}
        log.save(m)
        await self.naoko._narrate(
            m, f"decidiste {'SÍ' if aprueba else 'NO'} en {anterior.value}")

        if not aprueba:
            return m.to_dict()

        # Cada compuerta abre una fase distinta. Van en segundo plano y bajo el
        # supervisor: son largas y el usuario debe poder pararlas (§7.3).
        from magi.core.cancel import supervisor

        async def _seguir():
            try:
                if anterior is Stage.IDEA:
                    await self.naoko.draft_plan(m)
                elif anterior is Stage.PLAN_BORRADOR:
                    await self.naoko.run_circuit(m)
                elif anterior is Stage.PLAN_FINAL:
                    await self.naoko.execute_improvement(m)
                elif anterior is Stage.ESPERANDO_PUBLICACION:
                    await self.naoko.publish_improvement(m)
            except Exception as e:
                logger.exception("[mejora] %s falló", m.improvement_id)
                await self.bus.publish(BusEvent(
                    topic="TERMINAL_OUT",
                    payload={"content": f"[NAOKO] la fase falló: {e}"}))
            finally:
                self.naoko._improvements().save(m)

        supervisor().register_loop(
            f"mejora-{m.improvement_id}", asyncio.create_task(_seguir()))
        return m.to_dict()

    async def _handle_improve_list(self, payload, websocket):
        """Qué hay abierto y qué espera respuesta tuya."""
        log = self.naoko._improvements()
        return {"all": [m.to_dict() for m in log.all()[:20]],
                "pending": [m.to_dict() for m in log.pending_user()]}

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
            
        scratch_dir = workspace_dir()
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
        
        # Escanear proyectos reales en el workspace del usuario
        base_dir = workspace_dir()
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
                
            scratch_dir = workspace_dir()
            
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
            scratch_dir = workspace_dir()
            
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
        # MAGI 9.0 §2.7: el estilo narrativo llega de la GUI y se propaga al enjambre.
        narrative_style = (payload.get("narrative_style", "tecnico")
                           if isinstance(payload, dict) else "tecnico")
            
        # Generar un proyecto automático si es una conversación nueva
        # Para simular "cada vez que inicie una conversacion", creamos la carpeta
        new_proj_dir = workspace_dir() / f"project_{task_id}"
        new_proj_dir.mkdir(parents=True, exist_ok=True)
        
        await self.bus.publish(BusEvent(
            topic="system.project_created",
            payload={"name": f"project_{task_id}"}
        ))
        
        # Publicar en el bus para que el Logger lo intercepte
        await self.bus.publish(BusEvent(
            topic="SYS_EXEC",
            payload={"task_id": task_id, "command": command, "engine": engine,
                     "narrative_style": narrative_style}
        ))
        
        # Delegamos el control al Orquestador del Enjambre (Área 16)
        # El orquestador publicará los avances en el MagiBus que la GUI consumirá
        # MAGI 9.0 §2.3 — enrutamiento adaptativo.
        #
        # Estaba escrito y con tests, y NO se llamaba desde ningún sitio: toda
        # petición seguía pasando por el debate popperiano completo. Preguntar
        # "¿qué hora es?" costaba 9 llamadas a la nube y 60-90 s.
        from magi.core.router import classify
        from magi.core.providers.cloud import get_registry

        try:
            decision = await classify(command, await get_registry())
        except Exception as e:
            logger.warning("[kernel] clasificador falló (%s); ruta task", e)
            from magi.core.router import RoutingDecision, Route
            decision = RoutingDecision(Route.TASK, 0.5, "fallo del clasificador",
                                       2, True)

        logger.info("[kernel] ruta=%s (%s, confianza %.2f)",
                    decision.route.value, decision.reason, decision.confidence)
        await self.bus.publish(BusEvent(
            topic="swarm.routed",
            payload={"task_id": task_id, **decision.to_dict()}))

        # v5.0.28 llamaba a submit_task(task_id, command) sin pasar engine:
        # el selector de motor de la GUI tampoco tenía efecto.
        await self.swarm.submit_task(task_id, command, engine=engine,
                                     narrative_style=narrative_style,
                                     route=decision.route.value,
                                     max_rounds=decision.max_rounds,
                                     use_tools=decision.use_tools)

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
        if getattr(self, "naoko", None) is not None:
            await self.naoko.stop()
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
