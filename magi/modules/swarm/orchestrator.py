import asyncio
import logging
from magi.core.blackboard import Blackboard
from magi.core.bus import MagiBus, BusEvent
from .agents import MelchiorAgent, BalthasarAgent, CasperAgent
from magi.core.paths import project_root, workspace_dir

logger = logging.getLogger(__name__)

class SwarmOrchestrator:
    """
    Controla el ciclo de vida de un debate Popperiano en el Enjambre (Área 16).
    Evita que los agentes hablen al mismo tiempo, manejando el turn-taking.
    """
    def __init__(self, blackboard: Blackboard, bus: MagiBus, store=None):
        self.blackboard = blackboard
        self.bus = bus
        # MAGI 9.0 §1.4: el estado deja de vivir solo en RAM. active_tasks se
        # mantiene como caché caliente, pero se persiste en cada transición.
        # Antes, cerrar la ventana perdía la conversación entera.
        from magi.core.store.state import TaskStore
        self.store = store if store is not None else TaskStore()
        self.active_tasks = {}
        self.latest_task_id = None
        self._rehydrate()
        
        # Inicializar agentes
        self.melchior = MelchiorAgent(self.blackboard, self.bus)
        self.balthasar = BalthasarAgent(self.blackboard, self.bus)
        self.casper = CasperAgent(self.blackboard, self.bus)

    def _rehydrate(self) -> None:
        """Recupera las tareas reanudables al arrancar."""
        try:
            for st in self.store.resumable():
                self.active_tasks[st.task_id] = {
                    "command": st.command, "round": st.round, "status": st.status,
                    "engine": st.engine, "narrative_style": st.narrative_style,
                    "last_proposal": st.last_proposal,
                    "last_critique": st.last_critique,
                }
                self.latest_task_id = st.task_id
            if self.active_tasks:
                logger.info("[SWARM] %d tarea(s) recuperadas tras reinicio: %s",
                            len(self.active_tasks), ", ".join(self.active_tasks))
        except Exception as e:
            logger.warning("[SWARM] no se pudo rehidratar el estado: %s", e)

    def _persist(self, task_id: str) -> None:
        """Vuelca el estado en curso. Llamar tras cada transición."""
        state = self.active_tasks.get(task_id)
        if not state:
            return
        try:
            from magi.core.store.state import TaskState
            existing = self.store.load(task_id)
            self.store.save(TaskState(
                task_id=task_id,
                command=state.get("command", ""),
                status=state.get("status", "in_progress"),
                round=state.get("round", 1),
                engine=state.get("engine", "fast"),
                narrative_style=state.get("narrative_style", "tecnico"),
                last_proposal=state.get("last_proposal"),
                last_critique=state.get("last_critique"),
                created_at=existing.created_at if existing else __import__("time").time(),
            ))
        except Exception as e:
            logger.warning("[SWARM] no se pudo persistir %s: %s", task_id, e)

    async def submit_task(self, task_id: str, command: str, engine: str = "fast",
                          narrative_style: str = "tecnico"):
        """Inicia un nuevo flujo de trabajo en el enjambre o resume uno pausado."""
        # Reutilizar la tarea activa si existe una pendiente de aprobación o en progreso
        if task_id not in self.active_tasks and self.latest_task_id and self.latest_task_id in self.active_tasks:
            prev_state = self.active_tasks[self.latest_task_id]
            if prev_state["status"] in ["WAITING_USER_APPROVAL", "in_progress"]:
                task_id = self.latest_task_id

        if task_id in self.active_tasks:
            state = self.active_tasks[task_id]
            # El usuario puede cambiar motor o estilo a mitad de conversación:
            # antes se guardaban solo al crear la tarea y los cambios posteriores
            # se perdían en silencio.
            state["engine"] = engine
            state["narrative_style"] = narrative_style
            self._persist(task_id)
            if state["status"] == "WAITING_USER_APPROVAL":
                if any(word in command.lower().strip() for word in ["si", "sí", "apruebo", "ok", "adelante", "ejecuta", "yes", "claro"]):
                    state["status"] = "completed"
                    self._persist(task_id)
                    await self.bus.publish(BusEvent(
                        topic="TERMINAL_OUT",
                        payload={"content": f"[SWARM] Aprobación recibida. Tarea {task_id} finalizada exitosamente."}
                    ))
                    
                    import re
                    content = state.get("last_proposal", {}).get("content", "")
                    blocks = re.findall(r'```(\w+)?\n(.*?)```', content, re.IGNORECASE | re.DOTALL)
                    
                    if blocks:
                        from pathlib import Path
                        import os
                        
                        async def _auto_exec():
                            # MAGI 9.0 §4.2: la ejecución sigue siendo sin
                            # restricciones, pero pasa por el journal para poder
                            # deshacerla. Antes no había forma de revertir nada.
                            from magi.core.tools.journal import WriteJournal
                            journal = WriteJournal(task_id=task_id)
                            scratch_dir = workspace_dir()
                            os.makedirs(scratch_dir, exist_ok=True)
                            
                            for i, (lang, code) in enumerate(blocks):
                                lang = lang.lower().strip() if lang else ""
                                await self.bus.publish(BusEvent(
                                    topic="TERMINAL_OUT", 
                                    payload={"content": f"[AUTO-EXEC] Ejecutando bloque {i+1} ({lang or 'shell'})..."}
                                ))
                                
                                if lang in ["python", "py"]:
                                    temp_file = scratch_dir / f"auto_script_{i}.py"
                                    journal.record(temp_file, "create", tool="auto_exec")
                                    temp_file.write_text(code, encoding="utf-8")
                                    cmd = f"python {temp_file.name}"
                                else:
                                    temp_file = scratch_dir / f"auto_script_{i}.ps1"
                                    journal.record(temp_file, "create", tool="auto_exec")
                                    temp_file.write_text(code, encoding="utf-8")
                                    cmd = f"powershell -ExecutionPolicy Bypass -File {temp_file.name}"
                                    
                                process = await asyncio.create_subprocess_shell(
                                    cmd,
                                    cwd=str(scratch_dir),
                                    stdout=asyncio.subprocess.PIPE,
                                    stderr=asyncio.subprocess.PIPE
                                )
                                stdout, stderr = await process.communicate()
                                out_msg = (stdout.decode() + "\n" + stderr.decode()).strip()
                                await self.bus.publish(BusEvent(
                                    topic="TERMINAL_OUT", 
                                    payload={"content": f"Salida del bloque {i+1}:\n{out_msg}\n[Finalizado con código {process.returncode}]"}
                                ))
                                
                        asyncio.create_task(_auto_exec())
                    else:
                        await self.bus.publish(BusEvent(
                            topic="TERMINAL_OUT",
                            payload={"content": "[SWARM] Propuesta aprobada por el usuario. Generando resolución final estructurada y contextualizada..."}
                        ))
                        asyncio.create_task(
                            self.casper.generate_final_resolution(
                                task_id,
                                state["command"],
                                state.get("last_proposal"),
                                state.get("last_critique"),
                                engine=state.get("engine", "fast"),
                                narrative_style=state.get("narrative_style", "tecnico"),
                            )
                        )
                else:
                    state["status"] = "in_progress"
                    state["command"] = f"Ajustar la propuesta según las nuevas instrucciones del usuario: {command}"
                    state["round"] += 1
                    await self.bus.publish(BusEvent(
                        topic="TERMINAL_OUT",
                        payload={"content": f"[SWARM] Feedback del usuario recibido. Reanudando debate (Ronda {state['round']})."}
                    ))
                    asyncio.create_task(self._orchestrate_loop(task_id))
                return
            elif state["status"] == "in_progress":
                return # Ignorar comandos extra mientras piensa
                
        logger.info(f"[SWARM] Iniciando tarea {task_id}: {command}")
        self.latest_task_id = task_id
        self.active_tasks[task_id] = {
            "command": command,
            "round": 1,
            "status": "in_progress",
            "engine": engine,
            "narrative_style": narrative_style,
        }
        self._persist(task_id)
        
        await self.bus.publish(BusEvent(
            topic="TERMINAL_OUT",
            payload={"content": f"[SWARM] Iniciando análisis para la tarea: '{command}'"}
        ))
        
        # Arrancar el bucle de la conversación asíncronamente
        asyncio.create_task(self._orchestrate_loop(task_id))
        
    async def _orchestrate_loop(self, task_id: str):
        state = self.active_tasks[task_id]
        
        while state["status"] == "in_progress":
            try:
                current_round = state["round"]
                logger.info(f"[SWARM] Iniciando Ronda {current_round} para {task_id}")
                
                engine = state.get("engine", "fast")
                style = state.get("narrative_style", "tecnico")
                
                # 1. Melchior Propone
                last_proposal = state.get("last_proposal")
                last_critique = state.get("last_critique")
                proposal = await self.melchior.generate_proposal(
                    task_id, state["command"], current_round,
                    last_proposal, last_critique, engine, style)
                self.blackboard.post(f"{task_id}.proposal", proposal)
                state["last_proposal"] = proposal
                self._persist(task_id)
                if "SYS_EMERGENCY_STOP" in proposal["content"]:
                    await self._trigger_emergency_stop(task_id, state)
                    break
                
                # 2. Balthasar Critica
                critique = await self.balthasar.generate_critique(
                    task_id, proposal, current_round, engine, style)
                self.blackboard.post(f"{task_id}.critique", critique)
                state["last_critique"] = critique
                self._persist(task_id)
                if "SYS_EMERGENCY_STOP" in critique["content"]:
                    await self._trigger_emergency_stop(task_id, state)
                    break
                
                # 3. Casper Arbitra
                verdict = await self.casper.arbitrate(
                    task_id, proposal, critique, current_round, engine, style)
                self.blackboard.post(f"{task_id}.verdict", verdict)
                if "SYS_EMERGENCY_STOP" in verdict.get("feedback", ""):
                    await self._trigger_emergency_stop(task_id, state)
                    break
            except Exception as e:
                logger.error(f"[SWARM] Error catastrófico durante orquestación: {e}")
                error_msg = f"[SISTEMA] Error crítico en el Enjambre: {str(e)}. Las IAs podrían estar inoperativas."
                await self.bus.publish(BusEvent(topic="TERMINAL_OUT", payload={"agent": "SYSTEM", "content": error_msg}))
                state["status"] = "WAITING_USER_APPROVAL"
                await self.bus.publish(BusEvent(topic="swarm.task_completed", payload={"task_id": task_id, "result": error_msg}))
                break
            
            feedback_text = verdict.get("feedback", "").upper()
            is_asking_approval = "¿APRUEBAS" in feedback_text or "APRUEBAS" in feedback_text or verdict["decision"] == "APPROVED"
            
            if is_asking_approval or current_round >= 3:
                state["status"] = "WAITING_USER_APPROVAL"
                self._persist(task_id)
                await self.bus.publish(BusEvent(
                    topic="TERMINAL_OUT",
                    payload={"content": f"[SWARM] Esperando aprobación interactiva del usuario para ejecutar o finalizar la propuesta final."}
                ))
                break # Pausar el bucle hasta recibir input del usuario
            elif verdict["decision"] == "REJECTED_NEEDS_WORK":
                state["round"] += 1
                state["command"] = f"Revisar propuesta considerando crítica: {verdict['feedback']}"
                await asyncio.sleep(1.0)
            else:
                state["status"] = "failed"
                await self.bus.publish(BusEvent(
                    topic="TERMINAL_OUT",
                    payload={"content": f"[SWARM] Tarea fallida tras {current_round} rondas."}
                ))

    async def _trigger_emergency_stop(self, task_id: str, state: dict):
        logger.critical(f"[SWARM] EMERGENCY STOP TRIGGERED FOR TASK {task_id}")
        state["status"] = "failed"
        await self.bus.publish(BusEvent(
            topic="TERMINAL_OUT",
            payload={"content": f"\n[!!!] CONTINGENCIA DE SEGURIDAD ACTIVADA [!!!]\nEl motor cognitivo superior fue censurado y el motor de fallback confirmó riesgo operativo.\nAbortando operaciones del Enjambre inmediatamente y aplicando kill-switch local automatizado.\n"}
        ))
        await self.bus.publish(BusEvent(topic="EMERGENCY_STOP", payload={}))
