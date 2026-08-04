import asyncio
import logging
from magi.core.blackboard import Blackboard
from magi.core.bus import MagiBus, BusEvent
from .agents import MelchiorAgent, BalthasarAgent, CasperAgent
from .parallel import (
    critique_multi_axis, format_variants_for_critic, generate_variants,
)
from magi.core.verification import ProposalVerifier
from magi.modules.memory.episodic import EpisodicMemory
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
        self._memory: dict[str, EpisodicMemory] = {}

        # Agentes ANTES de rehidratar: _rehydrate puede reanudar una tarea.
        self.melchior = MelchiorAgent(self.blackboard, self.bus)
        self.balthasar = BalthasarAgent(self.blackboard, self.bus)
        self.casper = CasperAgent(self.blackboard, self.bus)

        self._rehydrate()

    def memory_for(self, task_id: str) -> EpisodicMemory:
        """Memoria episódica de la tarea (§2.6). Persistida en task_event."""
        if task_id not in self._memory:
            self._memory[task_id] = EpisodicMemory(task_id, store=self.store)
        return self._memory[task_id]

    def _rehydrate(self) -> None:
        """Recupera las tareas reanudables al arrancar."""
        try:
            for st in self.store.resumable():
                self.active_tasks[st.task_id] = {
                    "command": st.command, "round": st.round, "status": st.status,
                    "engine": st.engine, "narrative_style": st.narrative_style,
                    "route": st.route, "max_rounds": st.max_rounds,
                    "use_tools": st.use_tools,
                    "last_proposal": st.last_proposal,
                    "last_critique": st.last_critique,
                }
                self.latest_task_id = st.task_id
            if self.active_tasks:
                logger.info("[SWARM] %d tarea(s) recuperadas tras reinicio: %s",
                            len(self.active_tasks), ", ".join(self.active_tasks))
        except Exception as e:
            logger.warning("[SWARM] no se pudo rehidratar el estado: %s", e)

    async def _publish_approval(self, task_id: str, state: dict,
                                verdict: dict) -> None:
        """
        Publica `swarm.approval_required` con TODO lo necesario para decidir
        (§7.4): qué ficheros toca, su contenido antes y después, y si los
        tests pasaron.

        Nunca deja caer una excepción hacia arriba. Si reunir el contexto
        falla, la aprobación se pide igual con menos información: una tarea
        que se queda colgada porque el panel de revisión reventó es peor que
        una revisión incompleta.
        """
        try:
            from magi.core.approval import build_approval_request
            from magi.core.tools.journal import WriteJournal

            verificacion = state.get("verification") or {}
            peticion = build_approval_request(
                task_id,
                journal=WriteJournal(task_id=task_id),
                summary=(verdict.get("feedback")
                         or state.get("last_proposal", {}).get("content", "")),
                commands=list(state.get("pending_commands") or []),
                tests_ran=bool(verificacion.get("ran")),
                tests_passed=bool(verificacion.get("passed")),
                tests_detail=str(verificacion.get("detail", "")),
            )
            await self.bus.publish(BusEvent(
                topic="swarm.approval_required", payload=peticion.to_payload()))
            await self.bus.publish(BusEvent(
                topic="TERMINAL_OUT", payload={"content": peticion.render()}))
        except Exception as e:                    # pragma: no cover
            logger.warning(
                "[SWARM] no se pudo reunir el contexto de aprobación: %s", e)

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
                route=state.get("route", "task"),
                max_rounds=state.get("max_rounds", 3),
                use_tools=state.get("use_tools", True),
                last_proposal=state.get("last_proposal"),
                last_critique=state.get("last_critique"),
                created_at=existing.created_at if existing else __import__("time").time(),
            ))
        except Exception as e:
            logger.warning("[SWARM] no se pudo persistir %s: %s", task_id, e)

    async def submit_task(self, task_id: str, command: str, engine: str = "fast",
                          narrative_style: str = "tecnico",
                          route: str = "task", max_rounds: int = 3,
                          use_tools: bool = True):
        """Inicia un nuevo flujo de trabajo en el enjambre o resume uno pausado."""
        # Absorción de la petición en la tarea anterior.
        #
        # v5.0.28 reescribía el task_id entrante por el de la tarea previa
        # siempre que esa estuviera en WAITING_USER_APPROVAL *o* in_progress.
        # Consecuencia medida: de 25 peticiones concurrentes, 24 se perdían en
        # silencio — todas se fundían en una sola tarea. Y en uso normal, si
        # preguntabas algo nuevo mientras el enjambre pensaba, tu petición se
        # convertía sin avisar en "comentario a la propuesta anterior".
        #
        # La absorción SOLO tiene sentido cuando la tarea previa está esperando
        # respuesta del usuario: ahí sí, lo que escribes es la respuesta.
        # Nunca cuando está en progreso.
        if (task_id not in self.active_tasks and self.latest_task_id
                and self.latest_task_id in self.active_tasks):
            prev = self.active_tasks[self.latest_task_id]
            if prev["status"] == "WAITING_USER_APPROVAL":
                logger.info("[SWARM] %s se trata como respuesta a %s (pendiente "
                            "de aprobación)", task_id, self.latest_task_id)
                task_id = self.latest_task_id
            else:
                logger.info("[SWARM] %s arranca en paralelo (la anterior sigue "
                            "en progreso)", task_id)

        if task_id in self.active_tasks:
            state = self.active_tasks[task_id]
            # El usuario puede cambiar motor o estilo a mitad de conversación:
            # antes se guardaban solo al crear la tarea y los cambios posteriores
            # se perdían en silencio.
            state["engine"] = engine
            state["narrative_style"] = narrative_style
            state["route"] = route
            state["max_rounds"] = max_rounds
            state["use_tools"] = use_tools
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
                                # §7.3 — este es EL proceso que más urge poder
                                # parar: un script generado por un LLM
                                # ejecutándose en la máquina del usuario, en
                                # PowerShell con la política saltada. Sin
                                # inscribirlo, la parada de emergencia lo
                                # ignoraba por completo.
                                from magi.core.cancel import supervisor
                                supervisor().register_process(task_id, process)
                                try:
                                    stdout, stderr = await process.communicate()
                                finally:
                                    supervisor().forget_process(task_id, process)
                                out_msg = (stdout.decode() + "\n" + stderr.decode()).strip()
                                await self.bus.publish(BusEvent(
                                    topic="TERMINAL_OUT", 
                                    payload={"content": f"Salida del bloque {i+1}:\n{out_msg}\n[Finalizado con código {process.returncode}]"}
                                ))
                                
                        self._spawn_tracked(task_id, _auto_exec())
                    else:
                        await self.bus.publish(BusEvent(
                            topic="TERMINAL_OUT",
                            payload={"content": "[SWARM] Propuesta aprobada por el usuario. Generando resolución final estructurada y contextualizada..."}
                        ))
                        self._spawn_tracked(
                            task_id,
                            self.casper.generate_final_resolution(
                                task_id,
                                state["command"],
                                state.get("last_proposal"),
                                state.get("last_critique"),
                                engine=state.get("engine", "fast"),
                                narrative_style=state.get("narrative_style", "tecnico"),
                                use_tools=state.get("use_tools", False),
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
                    self._spawn_loop(task_id)
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
            "route": route,
            "max_rounds": max_rounds,
            "use_tools": use_tools,
        }
        self._persist(task_id)
        
        await self.bus.publish(BusEvent(
            topic="TERMINAL_OUT",
            payload={"content": f"[SWARM] Iniciando análisis para la tarea: '{command}'"}
        ))
        
        # Arrancar el bucle de la conversación asíncronamente
        self._spawn_loop(task_id)
        
    async def _orchestrate_loop(self, task_id: str):
        state = self.active_tasks[task_id]
        
        while state["status"] == "in_progress":
            try:
                current_round = state["round"]
                logger.info(f"[SWARM] Iniciando Ronda {current_round} para {task_id}")
                
                engine = state.get("engine", "fast")
                style = state.get("narrative_style", "tecnico")
                # Explorar cuesta cuota: solo la ruta build genera 3 enfoques.
                n_variants = {"build": 3, "task": 2}.get(
                    state.get("route", "task"), 1)
                use_tools = state.get("use_tools", True)
                
                last_proposal = state.get("last_proposal")
                last_critique = state.get("last_critique")

                # ---- 1. MELCHIOR: N enfoques EN PARALELO (§2.4) -------------
                # Antes: una sola propuesta secuencial. Ahora varias variantes
                # con semillas distintas; el tiempo de pared es el de una.
                memory = self.memory_for(task_id)
                history = memory.render_for_prompt()
                command_with_memory = (
                    f"{state['command']}\n\n{history}" if history else state["command"])

                variants = await generate_variants(
                    self.melchior, task_id=task_id, command=command_with_memory,
                    round_num=current_round, n=n_variants, engine=engine,
                    narrative_style=style, last_proposal=last_proposal,
                    last_critique=last_critique, use_tools=use_tools)

                # ---- 2. VERIFICACIÓN EJECUTABLE (§2.5) ----------------------
                # Ninguna propuesta con código llega al crítico sin ejecutarse.
                # Elimina la clase de fallo más cara: tres rondas debatiendo
                # elegantemente sobre código que no compila.
                verifier = ProposalVerifier()
                reports = await asyncio.gather(
                    *(verifier.verify(v.content) for v in variants))
                for v, rep in zip(variants, reports):
                    v.verified = rep.ok
                    v.verification = rep.render()

                good = [v for v in variants if v.verified]
                if not good and any(r.had_code for r in reports):
                    # Todas fallan: vuelve a Melchior con el traceback SIN
                    # gastar una ronda de debate.
                    worst = reports[0]
                    await self.bus.publish(BusEvent(
                        topic="TERMINAL_OUT",
                        payload={"content": "[VERIFICACIÓN] El código propuesto no "
                                            "arranca. Devuelto a Melchior sin gastar ronda."}))
                    await self.bus.publish(BusEvent(
                        topic="swarm.verification_failed",
                        payload={"task_id": task_id, "round": current_round,
                                 "detail": worst.render()[:2000]}))
                    for v, rep in zip(variants, reports):
                        memory.record(round_num=current_round, approach=v.content,
                                      outcome="no_verifica",
                                      reason=(rep.failures[0].detail
                                              if rep.failures else "no arranca"))
                    state["command"] = (f"{state['command']}\n\n"
                                        f"{worst.feedback_for_author()}")
                    await asyncio.sleep(0.5)
                    continue

                chosen = good or variants
                proposal = {"content": format_variants_for_critic(chosen),
                            "changes": 1 if current_round > 1 else 0,
                            "variants": len(chosen)}
                self.blackboard.post(f"{task_id}.proposal", proposal)
                state["last_proposal"] = proposal
                self._persist(task_id)
                if "SYS_EMERGENCY_STOP" in proposal["content"]:
                    await self._trigger_emergency_stop(task_id, state)
                    break

                evidence = "\n\n".join(
                    f"[{v.label}] {v.verification}" for v in chosen if v.verification)

                # ---- 3. BALTHASAR: crítica multi-eje EN PARALELO (§2.4) -----
                multi = await critique_multi_axis(
                    self.balthasar, task_id=task_id,
                    proposal_text=proposal["content"], round_num=current_round,
                    engine=engine, narrative_style=style, use_tools=use_tools,
                    evidence=("\n\n--- EVIDENCIA DE EJECUCIÓN ---\n" + evidence)
                    if evidence else "")
                critique = {"content": multi.render(), "status": "CRITIQUE_GENERATED",
                            "axes": multi.axes_ok}
                await self.bus.publish(BusEvent(topic="AGENT_POST", payload={
                    "type": "AGENT_POST", "task_id": task_id, "agent": "BALTHASAR",
                    "role": "critica", "provider": self.balthasar.family,
                    "family": self.balthasar.family,
                    "content": critique["content"], "changes": 0,
                    "stats": f"{multi.axes_ok} ejes"}))
                self.blackboard.post(f"{task_id}.critique", critique)
                state["last_critique"] = critique
                self._persist(task_id)
                if "SYS_EMERGENCY_STOP" in critique["content"]:
                    await self._trigger_emergency_stop(task_id, state)
                    break
                
                # 3. Casper Arbitra
                verdict = await self.casper.arbitrate(
                    task_id, proposal, critique, current_round, engine, style,
                    use_tools=use_tools)
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
            
            if is_asking_approval or current_round >= state.get("max_rounds", 3):
                state["status"] = "WAITING_USER_APPROVAL"
                self._persist(task_id)

                # §7.4 — aprobación CON CONTEXTO. Antes solo salía esta frase,
                # y la interfaz deducía el estado de aprobación buscándola
                # dentro del terminal (App.tsx:167). Al no haber evento con
                # datos, `DiffViewer` recibía originalCode="" y pintaba todo
                # como añadido: no era un diff, era el texto nuevo en verde.
                # Aprobar sobre eso es aprobar a ciegas con la APARIENCIA de
                # haber revisado, que es lo peor de las dos cosas.
                await self._publish_approval(task_id, state, verdict)

                await self.bus.publish(BusEvent(
                    topic="TERMINAL_OUT",
                    payload={"content": f"[SWARM] Esperando aprobación interactiva del usuario para ejecutar o finalizar la propuesta final."}
                ))
                break # Pausar el bucle hasta recibir input del usuario
            elif verdict["decision"] == "REJECTED_NEEDS_WORK":
                self.memory_for(task_id).record(
                    round_num=current_round,
                    approach=state.get("last_proposal", {}).get("content", ""),
                    outcome="refutado",
                    reason=verdict.get("feedback", ""))
                state["round"] += 1
                state["command"] = f"Revisar propuesta considerando crítica: {verdict['feedback']}"
                await asyncio.sleep(1.0)
            else:
                state["status"] = "failed"
                await self.bus.publish(BusEvent(
                    topic="TERMINAL_OUT",
                    payload={"content": f"[SWARM] Tarea fallida tras {current_round} rondas."}
                ))

    def _spawn_tracked(self, task_id: str, coro) -> None:
        """
        Lanza una corrutina de fondo GUARDANDO su handle.

        Lo encontró un test que comprueba con AST que ningún `create_task`
        aparezca como sentencia suelta. Buscar la cadena no habría servido:
        `handle = create_task(...)` la contiene y es lo correcto; lo que hay
        que prohibir es tirar el resultado.

        Y los dos que quedaban eran los peores posibles — la auto-ejecución
        de un script generado por el modelo, y la resolución final tras
        aprobar. Justo lo que uno quiere poder parar.
        """
        from magi.core.cancel import supervisor
        supervisor().register_loop(task_id, asyncio.create_task(coro))

    def _spawn_loop(self, task_id: str) -> None:
        """
        Lanza el bucle de orquestación GUARDANDO su handle.

        Antes era `asyncio.create_task(self._orchestrate_loop(task_id))` a
        secas, dos veces. El handle se tiraba, así que no existía ningún
        objeto al que pedirle que parase — y por eso el botón de parada de
        emergencia no tenía nada que cancelar aunque hubiera querido.
        """
        self._spawn_tracked(task_id, self._orchestrate_loop(task_id))

    async def _trigger_emergency_stop(self, task_id: str, state: dict):
        logger.critical(f"[SWARM] EMERGENCY STOP TRIGGERED FOR TASK {task_id}")
        state["status"] = "failed"
        # Sin persistir, la fila de task_state se quedaba en `in_progress`, que
        # está en RESUMABLE: al reiniciar, `_rehydrate` devolvía a la vida la
        # tarea que se acababa de abortar por riesgo operativo.
        self._persist(task_id)

        # El mensaje anterior afirmaba estar "aplicando kill-switch local
        # automatizado" y no se aplicaba ninguno: el bucle hacía `break` y
        # cualquier subproceso lanzado seguía vivo. Ahora se para de verdad y
        # se informa de lo que se paró, no de lo que se pretendía parar.
        from magi.core.cancel import supervisor
        informe = await supervisor().stop_processes(task_id)
        muertos, fallidos = informe
        mensaje = (
            f"\n[!!!] CONTINGENCIA DE SEGURIDAD ACTIVADA [!!!]\n"
            f"Riesgo operativo confirmado; se aborta la tarea {task_id}.\n"
            f"Procesos terminados: {muertos}."
            + (f"\nAVISO: {fallidos} proceso(s) NO murieron; compruébalos a mano.\n"
               if fallidos else "\n"))
        await self.bus.publish(BusEvent(
            topic="TERMINAL_OUT",
            payload={"content": mensaje}
        ))
        await self.bus.publish(BusEvent(topic="EMERGENCY_STOP", payload={}))
