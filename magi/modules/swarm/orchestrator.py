import asyncio
import logging

from magi.core.blackboard import Blackboard
from magi.core.bus import BusEvent, MagiBus
from magi.core.paths import workspace_dir
from magi.core.store.admision import AHORA, ENCOLAR
from magi.core.store.state import INTERRUMPIDA
from magi.core.verification import ProposalVerifier
from magi.modules.memory.episodic import EpisodicMemory

from .agents import BalthasarAgent, CasperAgent, MelchiorAgent
from .intencion import aprueba as _aprueba
from .intencion import es_respuesta_a_aprobacion
from .parallel import (
    critique_multi_axis,
    format_variants_for_critic,
    generate_variants,
)

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
        self._reconciliadas: list[str] = []
        # Libro de admisión: toda entrada del usuario queda escrita antes de
        # decidir qué hacer con ella. Ver `core/store/admision.py`.
        from magi.core.store.admision import LibroDeAdmision
        self.admision = LibroDeAdmision(self.store)
        # Los agentes necesitan la tienda para medir sus turnos, y el
        # blackboard es la vía que ya existe para compartir cosas globales.
        # Pasarla por el constructor de cada agente habría cambiado tres
        # firmas públicas para un detalle de instrumentación.
        try:
            self.blackboard.post("global.task_store", self.store)
        except Exception:                                 # pragma: no cover
            pass

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
        """
        Recupera las tareas reanudables al arrancar.

        FASE 0 — antes de leer nada, reconciliar. Todo lo que figure
        `in_progress` en este momento estaba corriendo cuando el proceso murió:
        no hay ni un bucle vivo todavía. Devolverlas como `in_progress` era
        crear zombis, y un zombi con el id `default` bloqueaba la aplicación
        entera de forma permanente.
        """
        try:
            reconciliadas = self.store.reconciliar()
            if reconciliadas:
                self._reconciliadas = reconciliadas
        except Exception as e:
            logger.warning("[SWARM] no se pudo reconciliar el estado: %s", e)

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
                # `or {}` y no `get(..., {})`: el valor por defecto de `get`
                # solo actúa si la clave falta, no si está y vale None — que
                # es el caso de una tarea rehidratada sin propuesta.
                summary=(verdict.get("feedback")
                         or (state.get("last_proposal") or {}).get("content", "")),
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
        # LO PRIMERO: dejarlo escrito. Antes de clasificar, antes de decidir,
        # antes de nada. Si algo revienta más abajo, el mensaje del usuario ya
        # está en el libro y se ve que llegó.
        #
        # Este orden es el que hace que el fallo sea imposible, no una regla
        # que haya que recordar respetar.
        entrada = None
        try:
            entrada = self.admision.admitir(command, task_id, entrega=AHORA)
        except Exception as e:                        # pragma: no cover
            logger.warning("[SWARM] no se pudo registrar la entrada: %s", e)

        # `_despachar` puede REASIGNAR el id: si escribes «sí, apruebo», la
        # petición se absorbe en la tarea que esperaba tu visto bueno. Con el
        # id original, la entrada se archivaba bajo una tarea que no llegó a
        # existir, y el libro perdía la traza de dónde acabó el trabajo.
        # Devolverlo es lo único que lo mantiene honesto.
        destino = task_id
        try:
            destino = await self._despachar(
                task_id, command, engine, narrative_style,
                route, max_rounds, use_tools, entrada) or task_id
        except Exception as e:
            if entrada is not None:
                try:
                    self.admision.fallar(entrada.id, str(e))
                except Exception:
                    pass
            raise
        else:
            # Cierre del ciclo. Cualquier camino de `_despachar` que termine
            # bien deja la entrada promovida, salvo que ya la haya encolado o
            # resuelto él mismo. Así el invariante no depende de acordarse de
            # cerrar el ciclo en cada rama: se cierra aquí, una vez.
            self._cerrar_entrada(entrada, destino)

    def _cerrar_entrada(self, entrada, task_id: str) -> None:
        if entrada is None:
            return
        try:
            with self.store._conn() as c:
                fila = c.execute(
                    "SELECT estado, entrega FROM entrada_usuario WHERE id=?",
                    (entrada.id,)).fetchone()
            if fila and fila["estado"] == "admitida" and fila["entrega"] == AHORA:
                self.admision.promover(entrada.id, task_id)
        except Exception as e:                        # pragma: no cover
            logger.warning("[SWARM] no se pudo cerrar la entrada %s: %s",
                           entrada.id, e)

    async def _despachar(self, task_id: str, command: str, engine: str,
                         narrative_style: str, route: str, max_rounds: int,
                         use_tools: bool, entrada=None):
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
        # Y AUN ASÍ SEGUÍA TRAGÁNDOSE PREGUNTAS. El arreglo anterior acotó la
        # absorción a WAITING_USER_APPROVAL, pero eso no basta: mientras una
        # tarea espera tu visto bueno, CUALQUIER cosa que escribas se convertía
        # en su respuesta. Ocurrió tal cual —el usuario escribió "dime por que
        # la soledad duele", una pregunta nueva y sin relación, y el registro
        # dice:
        #
        #     [SWARM] task_84hkn8xp se trata como respuesta a task_29ceb5d6
        #     [SWARM] Feedback del usuario recibido. Reanudando debate (Ronda 2)
        #
        # Su pregunta no se contestó nunca: se gastó como comentario a otra
        # propuesta. Desde fuera parece que el sistema no responde, y no hay
        # forma de darse cuenta.
        #
        # Ahora se mira QUÉ has escrito, no solo en qué estado está lo
        # anterior. Solo se absorbe si de verdad parece una respuesta a la
        # pregunta pendiente; una pregunta nueva abre su propia tarea y se
        # avisa de que la otra sigue esperando.
        if (task_id not in self.active_tasks and self.latest_task_id
                and self.latest_task_id in self.active_tasks):
            prev = self.active_tasks[self.latest_task_id]
            if prev["status"] == "WAITING_USER_APPROVAL":
                if es_respuesta_a_aprobacion(command):
                    logger.info("[SWARM] %s se trata como respuesta a %s "
                                "(pendiente de aprobación)",
                                task_id, self.latest_task_id)
                    task_id = self.latest_task_id
                else:
                    logger.info("[SWARM] %s es una petición NUEVA, no una "
                                "respuesta a %s: arranca por separado",
                                task_id, self.latest_task_id)
                    await self.bus.publish(BusEvent(
                        topic="TERMINAL_OUT",
                        payload={"content":
                                 f"[SWARM] Lo tomo como pregunta nueva. La tarea "
                                 f"{self.latest_task_id} sigue esperando tu "
                                 f"aprobación; escribe 'sí' o 'apruebo' cuando "
                                 f"quieras cerrarla."}))
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
                # `in` sobre una lista de subcadenas daba aprobaciones falsas:
                # el «si» de «siempre», «análisis» o «sigue así» cerraba la
                # tarea y lanzaba la auto-ejecución de los bloques de código.
                # Ahora se comparan palabras enteras y sin acentos.
                if _aprueba(command):
                    state["status"] = "completed"
                    self._persist(task_id)
                    await self.bus.publish(BusEvent(
                        topic="TERMINAL_OUT",
                        payload={"content": f"[SWARM] Aprobación recibida. Tarea {task_id} finalizada exitosamente."}
                    ))

                    import re
                    # `.get("last_proposal", {})` NO protege de nada aquí: el
                    # segundo argumento solo se usa si la clave FALTA. Si está
                    # presente y vale None —que es justo lo que pasa con una
                    # tarea rehidratada que nunca llegó a producir propuesta—
                    # devuelve None y el `.get("content")` siguiente revienta
                    # con AttributeError.
                    #
                    # Se hizo alcanzable al reanudar tareas interrumpidas: se
                    # rehidratan con last_proposal=None y aprobarlas mataba el
                    # turno. Con el libro de admisión el mensaje ya no se
                    # perdía —quedaba registrado como `fallida`—, pero seguía
                    # sin ejecutarse.
                    prop = state.get("last_proposal") or {}
                    content = prop.get("content") or ""
                    blocks = re.findall(r'```(\w+)?\n(.*?)```', content, re.IGNORECASE | re.DOTALL)

                    if blocks:
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
                    # El usuario NO está de acuerdo con la síntesis de Casper.
                    # La segunda ronda arranca en MELCHIOR (la tesis): se le
                    # pasa la síntesis previa de Casper + las observaciones del
                    # usuario, para que genere una tesis corregida. Después
                    # Balthasar refuta y Casper sintetiza de nuevo.
                    state["status"] = "in_progress"
                    veredicto_previo = self.blackboard.read(f"{task_id}.verdict")
                    sintesis_casper = ""
                    if isinstance(veredicto_previo, dict):
                        sintesis_casper = veredicto_previo.get("feedback", "")
                    state["command"] = (
                        f"El usuario no está de acuerdo con la síntesis de Casper. "
                        f"Estas son SUS OBSERVACIONES (respeta cada punto):\n{command}\n\n"
                        f"Esta fue la SÍNTESIS PREVIA de Casper a refinar:\n{sintesis_casper}\n\n"
                        f"Genera una TESIS corregida que integre las observaciones del usuario.")
                    state["round"] += 1
                    await self.bus.publish(BusEvent(
                        topic="TERMINAL_OUT",
                        payload={"content": f"[SWARM] Feedback del usuario recibido. Reanudando debate (Ronda {state['round']}): Melchior parte de la síntesis previa + tus observaciones."}
                    ))
                    self._spawn_loop(task_id)
                return task_id
            elif state["status"] in ("in_progress", INTERRUMPIDA):
                # AQUÍ ESTABA EL FALLO QUE BLOQUEABA EL SISTEMA
                # ================================================
                # Antes:
                #     elif state["status"] == "in_progress":
                #         return   # Ignorar comandos extra mientras piensa
                #
                # Un `return` mudo: ni evento, ni fila, ni motivo. El mensaje
                # del usuario se evaporaba. Y como `_rehydrate()` resucitaba
                # las tareas `in_progress` sin volver a lanzar su bucle, una
                # tarea muerta de una sesión anterior seguía "en curso" para
                # siempre y se tragaba TODO lo que se escribiera después. La
                # fila `default` de esta máquina llevaba así desde el 8 de
                # agosto a las 22:38.
                #
                # Ahora hay tres salidas, y las tres dejan constancia:
                #
                #   1. interrumpida  -> se reanuda con la orden nueva
                #   2. viva de verdad -> se ENCOLA y se avisa
                #   3. figura viva pero no lo está -> se reconcilia y se reanuda
                #
                # El caso 2 es lo que hacen Zcode (`delivery='queue'`) y Claude
                # Code (`command_lifecycle: queued`): si el agente está
                # ocupado, la entrada espera turno. No se tira.
                await self._entrada_mientras_ocupada(task_id, state, command,
                                                     entrada)
                return task_id


        logger.info(f"[SWARM] Iniciando tarea {task_id}: {command}")
        self.latest_task_id = task_id
        # EL IDIOMA SE DECIDE AQUÍ, UNA VEZ, Y NO SE VUELVE A TOCAR.
        #
        # `command` es lo que escribió el usuario, limpio. En cuanto arranca el
        # debate, el prompt de cada agente lleva pegada la memoria de las
        # rondas anteriores, y deducir el idioma de ahí es lo que producía el
        # bucle: una sola respuesta colada en chino contaminaba el prompt de la
        # ronda siguiente, `detectar()` respondía «zh», y la guarda pasaba a
        # EXIGIR chino a los tres nodos. De protección a causa.
        #
        # Fijándolo en el origen, ninguna ronda posterior puede cambiarlo.
        from magi.core import idioma as _idioma_mod
        lang_usuario = _idioma_mod.detectar(command)
        for agente in (self.melchior, self.balthasar, self.casper):
            agente.lang_usuario = lang_usuario
        logger.info("[SWARM] idioma de la tarea fijado a '%s' desde tu mensaje",
                    lang_usuario)

        self.active_tasks[task_id] = {
            "command": command,
            "lang_usuario": lang_usuario,
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
        return task_id

    async def _entrada_mientras_ocupada(self, task_id: str, state: dict,
                                        command: str, entrada) -> None:
        """
        Qué hacer con lo que escribes mientras la tarea ya está ocupada.

        Sustituye al `return` mudo. Tres caminos, y ninguno pierde el mensaje.
        """
        from magi.core.cancel import supervisor

        try:
            viva = supervisor().is_running(task_id)
        except Exception:
            viva = False

        # 1. Interrumpida, o figura viva pero no lo está. En ambos casos no hay
        #    nadie trabajando: se reanuda con la orden nueva. El segundo caso
        #    es el zombi clásico, y aquí se cura solo en vez de bloquear.
        if state["status"] == INTERRUMPIDA or not viva:
            motivo = ("reanudada tras interrupción"
                      if state["status"] == INTERRUMPIDA
                      else "figuraba en curso pero no había bucle vivo")
            logger.info("[SWARM] %s: %s. Se reanuda con la orden nueva.",
                        task_id, motivo)
            state["status"] = "in_progress"
            state["command"] = command
            state["round"] = max(1, int(state.get("round", 1)))
            self._persist(task_id)
            if entrada is not None:
                self.admision.promover(entrada.id, task_id)
            await self.bus.publish(BusEvent(
                topic="TERMINAL_OUT",
                payload={"content":
                         f"[SWARM] La tarea {task_id} {motivo}. Retomo con lo "
                         f"que acabas de escribir."}))
            self._spawn_loop(task_id)
            return

        # 2. Viva de verdad. Se ENCOLA — que es lo que hacen Zcode
        #    (delivery='queue') y Claude Code (command_lifecycle: queued) — y
        #    se dice en voz alta. El turno en curso la recogerá al terminar.
        if entrada is not None:
            try:
                with self.store._conn() as c:
                    c.execute("UPDATE entrada_usuario SET entrega=? WHERE id=?",
                              (ENCOLAR, entrada.id))
            except Exception as e:                    # pragma: no cover
                logger.warning("[SWARM] no se pudo encolar %s: %s",
                               entrada.id, e)
        pendientes = len(self.admision.en_cola(task_id))
        logger.info("[SWARM] %s ocupada; entrada encolada (%d en cola)",
                    task_id, pendientes)
        await self.bus.publish(BusEvent(
            topic="TERMINAL_OUT",
            payload={"content":
                     f"[SWARM] El enjambre está trabajando en {task_id} "
                     f"(ronda {state.get('round', 1)}). Tu mensaje queda EN "
                     f"COLA y se atiende al terminar la ronda "
                     f"({pendientes} en espera). No se ha perdido."}))
        await self.bus.publish(BusEvent(
            topic="swarm.entrada_encolada",
            payload={"task_id": task_id, "pendientes": pendientes,
                     "texto": command[:200]}))

    async def _vaciar_cola(self, task_id: str) -> bool:
        """
        Recoge lo que se encoló mientras trabajábamos.

        Se llama al cerrar una ronda. Devuelve True si había algo, para que el
        bucle sepa que tiene que seguir en vez de pararse.
        """
        siguiente = self.admision.siguiente_en_cola(task_id)
        if siguiente is None:
            return False
        state = self.active_tasks.get(task_id)
        if state is None:
            return False

        self.admision.promover(siguiente.id, task_id)
        state["status"] = "in_progress"
        state["command"] = siguiente.texto
        state["round"] = int(state.get("round", 1)) + 1
        self._persist(task_id)
        await self.bus.publish(BusEvent(
            topic="TERMINAL_OUT",
            payload={"content":
                     f"[SWARM] Retomo lo que dejaste en cola: "
                     f"«{siguiente.texto[:80]}»"}))
        return True

    async def _orchestrate_loop(self, task_id: str):
        state = self.active_tasks[task_id]

        while state["status"] == "in_progress":
            try:
                current_round = state["round"]
                logger.info(f"[SWARM] Iniciando Ronda {current_round} para {task_id}")

                engine = state.get("engine", "fast")
                style = state.get("narrative_style", "tecnico")
                # Se reafirma en cada ronda: una tarea rehidratada tras un
                # reinicio vuelve del disco con su idioma, y los agentes son
                # objetos compartidos que otra tarea pudo haber cambiado.
                if state.get("lang_usuario"):
                    for _a in (self.melchior, self.balthasar, self.casper):
                        _a.lang_usuario = state["lang_usuario"]
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
                for v, rep in zip(variants, reports, strict=True):
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
                    for v, rep in zip(variants, reports, strict=True):
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

                # ---- LA ÚNICA INTERVENCIÓN DE MELCHIOR EN ESTA RONDA -------
                #
                # Un agente, un turno, un mensaje. Antes cada variante publicaba
                # el suyo: el usuario leía «MELCHIOR propone» tres veces
                # seguidas, con tres análisis parciales, y eso no se lee como
                # una intervención sino como un agente repitiéndose. Las
                # variantes son andamiaje para explorar; lo que se debate es el
                # resultado.
                #
                # Y va con la EVIDENCIA DE EJECUCIÓN pegada, porque Melchior no
                # solo propone: ejecuta en el mismo turno. Separar «lo que digo»
                # de «lo que comprobé» obligaba a leer dos mensajes para saber
                # si la propuesta arranca.
                melchior_msg = proposal["content"]
                if evidence:
                    melchior_msg += ("\n\n---\n**Ejecutado y verificado en este "
                                     "mismo turno:**\n\n" + evidence)
                # El proveedor y la familia son los REALES, los de quien
                # respondió, no los que el nodo tenía asignados. Es el contrato
                # del panel desde que se descubrió que la interfaz enseñaba la
                # familia esperada mientras contestaba otra: si el registro
                # conmuta, se dice. `provider` lleva el id (g4f-…) y `family`
                # la familia; confundirlos deja el panel mintiendo otra vez.
                prov_real = [v.provider for v in chosen if v.provider]
                fam_real = [v.family for v in chosen if v.family]
                await self.bus.publish(BusEvent(topic="AGENT_POST", payload={
                    "type": "AGENT_POST", "task_id": task_id, "agent": "MELCHIOR",
                    "role": "propone",
                    "provider": (", ".join(dict.fromkeys(prov_real))
                                 or f"g4f-{self.melchior.family}"),
                    "family": (fam_real[0] if fam_real else self.melchior.family),
                    "family_expected": self.melchior.family,
                    "degraded": (None if (not fam_real
                                          or fam_real[0] == self.melchior.family)
                                 else f"{self.melchior.family} no disponible; "
                                      f"respondió {fam_real[0]}"),
                    "content": melchior_msg,
                    "changes": 1 if current_round > 1 else 0,
                    "stats": (f"{len(chosen)} enfoque(s) · "
                              f"{sum(1 for v in chosen if v.verified)} verificado(s)"),
                }))

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
                # Antes de pedir aprobación, mirar si escribiste algo mientras
                # trabajábamos. Si lo hay, se atiende AHORA en vez de pedirte
                # el visto bueno a una propuesta que ya has comentado.
                if await self._vaciar_cola(task_id):
                    continue
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
                    payload={"content": "[SWARM] Esperando aprobación interactiva del usuario para ejecutar o finalizar la propuesta final."}
                ))
                break # Pausar el bucle hasta recibir input del usuario
            elif verdict["decision"] == "REJECTED_NEEDS_WORK":
                self.memory_for(task_id).record(
                    round_num=current_round,
                    approach=(state.get("last_proposal") or {}).get("content", ""),
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
