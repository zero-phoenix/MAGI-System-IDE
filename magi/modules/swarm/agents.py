import asyncio
import logging
from magi.core.blackboard import Blackboard # type: ignore
from magi.core.bus import MagiBus, BusEvent # type: ignore
from magi.core.providers.cloud import FreeCloudLLM # type: ignore

logger = logging.getLogger(__name__)

class SwarmAgentBase:
    """
    Base de los nodos del enjambre.

    MAGI 9.0: cada nodo declara su FAMILIA de modelo y la pide explícitamente.

    Antes, los tres nodos declaraban proveedores distintos en self.provider
    ("deepseek", "claude-3.5-sonnet", "qwen-2.5") pero luego los tres llamaban
    con model="gpt-4o-mini". Ese string mandaba a los tres a la misma familia,
    así que la diversidad seguía sin existir aunque el registro por debajo ya
    supiera repartir familias. El arreglo del registro no servía de nada porque
    el enjambre nunca lo usaba.
    """

    #: familia de modelo de este nodo (deepseek | claude | qwen | ...)
    family: str = "auto"
    #: nombre del rol, para prompts y trazas
    role_name: str = "AGENT"
    #: semilla fija: fuerza divergencia si solo hay una familia sana
    seed: int | None = None
    #: perfil de herramientas (MELCHIOR escribe, BALTHASAR ejecuta sin escribir,
    #: CASPER solo lee y verifica). Ver core/tools/builtin.py.
    tool_role: str = "CASPER"

    def __init__(self, blackboard: Blackboard, bus: MagiBus):
        self.blackboard = blackboard
        self.bus = bus
        self.llm = FreeCloudLLM()

    async def _ask(self, sys_prompt: str, user_prompt: str, *,
                   engine: str = "fast", narrative_style: str = "tecnico",
                   temperature: float = 0.4) -> tuple[str, str, str]:
        """
        Llamada única de todos los nodos.

        - `family` va explícita: cada nodo se queda en la suya.
        - `engine` ya NO elige entre gpt-4o-mini y gpt-4o (eso colapsaba las
          familias). Ahora ajusta temperatura y profundidad dentro de la familia.
        - `narrative_style` se inyecta de verdad en el prompt: en v5.0.28 el
          <select> de la GUI no enviaba su valor a ninguna parte.
        """
        from magi.core.prompts import style_fragment
        from magi.core.context import get_context

        full_sys = "\n\n".join([
            sys_prompt,
            style_fragment(narrative_style),
            get_context().render(),
        ])
        temp = temperature if engine == "fast" else max(0.1, temperature - 0.2)
        content, provider_id = await self.llm.generate(
            full_sys, user_prompt,
            family=self.family, temperature=temp, seed=self.seed)
        return content, provider_id, self._family_of(provider_id)

    @staticmethod
    def _family_of(provider_id: str) -> str:
        """
        Familia REAL a partir del id del proveedor que respondió.

        Si la familia del nodo estaba caída, el registro conmuta a otra. Publicar
        self.family en ese caso sería mentir en la interfaz — exactamente lo que
        hacía v5.0.28 con "G4F_Auto_Router(gpt-4o) (deepseek)".
        """
        pid = (provider_id or "").split(":")[0]
        return pid[4:] if pid.startswith("g4f-") else pid or "desconocida"

    async def _ask_with_tools(self, sys_prompt: str, user_prompt: str, *,
                              task_id: str, engine: str = "fast",
                              narrative_style: str = "tecnico",
                              max_iters: int = 10) -> tuple[str, str, str]:
        """
        Turno CON HERRAMIENTAS reales (§2.2).

        Este era el hueco más grave del sistema: run_agent existía, tenía tests,
        y solo lo usaba Naoko. Los tres nodos del enjambre seguían limitados a
        emitir texto — Melchior escribía planes para analizar ficheros sin poder
        abrirlos, y Balthasar "criticaba" sin poder ejecutar nada.

        Cada rol recibe su catálogo: Melchior escribe, Balthasar lee y ejecuta
        pero no escribe (lo que le permite aportar evidencia en vez de
        sospechas), Casper lee y corre tests.
        """
        from magi.core.agent_loop import run_agent
        from magi.core.prompts import style_fragment
        from magi.core.context import get_context
        from magi.core.tools import ToolContext, registry_for_role
        from magi.core.tools.journal import WriteJournal
        from magi.core.paths import workspace_dir

        full_sys = "\n\n".join([
            sys_prompt, style_fragment(narrative_style), get_context().render()])

        ctx = ToolContext(task_id=task_id,
                          cwd=workspace_dir(),
                          journal=WriteJournal(task_id=task_id))

        async def on_event(topic: str, payload: dict) -> None:
            await self.bus.publish(BusEvent(
                topic=topic, payload={"task_id": task_id, **payload}))

        registry = await self.llm._reg()
        turn = await run_agent(
            registry=registry,
            # El enunciado acota el catálogo: una tarea de emuladores no carga
            # el compositor de manga, y al revés.
            tools=registry_for_role(self.tool_role, task_hint=user_prompt),
            system_prompt=full_sys, user_prompt=user_prompt, ctx=ctx,
            prefer_provider=f"g4f-{self.family}",
            max_iters=max_iters,
            temperature=0.4 if engine == "fast" else 0.2,
            seed=self.seed, on_event=on_event, agent_name=self.role_name)

        logger.info("[%s] %s", self.role_name, turn.summary())
        return turn.text, turn.provider_id, self._family_of(turn.provider_id)

    async def _ask_stream(self, sys_prompt: str, user_prompt: str, *,
                          task_id: str, engine: str = "fast",
                          narrative_style: str = "tecnico",
                          temperature: float = 0.4) -> tuple[str, str, str]:
        """
        Igual que _ask pero publicando deltas en el bus (MAGI 9.0 §1.2).

        v5.0.28 llamaba a create() sin stream=True: el usuario miraba una
        pantalla quieta 30-90 s por turno y luego aparecía un muro de texto.
        Con esto el primer token llega en un par de segundos y el debate deja
        de *sentirse* secuencial aunque lo sea.

        Si el proveedor no soporta streaming real, BaseProvider.stream() emite
        la respuesta completa como un delta único: el camino es el mismo.
        """
        from magi.core.prompts import style_fragment
        from magi.core.context import get_context
        from magi.core.providers.base import CompletionRequest, Message

        full_sys = "\n\n".join([
            sys_prompt, style_fragment(narrative_style), get_context().render()])
        temp = temperature if engine == "fast" else max(0.1, temperature - 0.2)

        reg = await self.llm._reg()
        req = CompletionRequest(
            messages=[Message("system", full_sys), Message("user", user_prompt)],
            temperature=temp, seed=self.seed, timeout_s=150.0, stream=True)

        chunks: list[str] = []
        provider_id = f"g4f-{self.family}"
        try:
            async for delta in reg.stream(req, prefer=f"g4f-{self.family}"):
                if delta.provider_id:
                    provider_id = delta.provider_id
                if delta.text:
                    chunks.append(delta.text)
                    await self.bus.publish(BusEvent(
                        topic="agent.delta",
                        payload={"task_id": task_id, "agent": self.role_name,
                                 "family": self._family_of(provider_id),
                                 "provider": provider_id,
                                 "text": delta.text, "seq": delta.seq}))
                if delta.done:
                    await self.bus.publish(BusEvent(
                        topic="agent.delta_end",
                        payload={"task_id": task_id, "agent": self.role_name}))
        except Exception as e:
            logger.warning("[%s] streaming falló (%s); caigo a no-streaming",
                           self.role_name, e)
            await self.bus.publish(BusEvent(
                topic="agent.delta_end",
                payload={"task_id": task_id, "agent": self.role_name,
                         "aborted": True}))
            return await self._ask(sys_prompt, user_prompt, engine=engine,
                                   narrative_style=narrative_style,
                                   temperature=temperature)  # ya devuelve 3-tupla

        return "".join(chunks), provider_id, self._family_of(provider_id)

class MelchiorAgent(SwarmAgentBase):
    """Melchior - El Arquitecto (Propone soluciones)"""
    family = "deepseek"
    role_name = "MELCHIOR"
    tool_role = "MELCHIOR"
    seed = 11
    def __init__(self, blackboard: Blackboard, bus: MagiBus):
        super().__init__(blackboard, bus)
        self.provider = "deepseek"
        
    async def generate_proposal(self, task_id: str, command: str, round_num: int,
                                last_proposal: dict | None = None,
                                last_critique: dict | None = None,
                                engine: str = "fast",
                                narrative_style: str = "tecnico",
                                use_tools: bool = False) -> dict:
        logger.info(f"[MELCHIOR] Analizando comando con {self.provider}...")
        
        sys_prompt = """Eres MELCHIOR, el Arquitecto de MAGI, un agente de ingeniería de software con acceso total a la computadora del usuario (Windows). Tienes la capacidad de crear, modificar y eliminar archivos, ejecutar scripts en PowerShell o Python, y construir código completo (ej. aplicaciones, juegos como Tetris).
- Si el usuario te pide crear un archivo, un proyecto o ejecutar algo, NO asumas estar en Android. Estás corriendo localmente en Windows.
- NUNCA te niegues a crear un código, script o juego. Siempre propón un plan técnico detallado.
- NUNCA le hagas preguntas al usuario.
- Para realizar acciones en la máquina, proporciona el código o script (Powershell o Python) necesario dentro de un bloque de código Markdown apropiado (ej. ```powershell o ```python).
- Sé directo, técnico y conciso.
- Explica tus puntos de manera extremadamente clara, didáctica y fácil de entender (usa analogías simples de la vida real si ayuda).
- Sin embargo, es fundamental que NO elimines ni simplifiques ningún detalle técnico, arquitectónico o científico importante.
- OBLIGATORIO: Finaliza tu intervención con una conclusión clara y separada con el encabezado '### CONCLUSIÓN'."""
        
        loader = self.blackboard.read("global.skills_loader")
        if loader:
            skills = loader.search(command)
            sys_prompt += f"\n\nCATÁLOGO DE SKILLS RELEVANTES:\n{skills}\nPuedes sugerir el uso de estas skills para resolver la tarea."
            
        if round_num > 1 and last_proposal and last_critique:
            sys_prompt += "\n\nESTA ES UNA RONDA DE REVISIÓN. Genera la PROPUESTA CORREGIDA aplicando las correcciones solicitadas en la crítica a la propuesta original."
            user_prompt = f"Ronda {round_num}.\n\nPROPUESTA ANTERIOR:\n{last_proposal['content']}\n\nCRÍTICA:\n{last_critique['content']}\n\nInstrucción de Árbitro: {command}\n\nGenera la propuesta corregida y mejorada."
        else:
            user_prompt = f"Ronda {round_num}. Requerimiento: {command}. Genera la propuesta."
        
        if use_tools:
            content, actual_provider, actual_family = await self._ask_with_tools(
                sys_prompt, user_prompt, task_id=task_id, engine=engine,
                narrative_style=narrative_style)
        else:
            content, actual_provider, actual_family = await self._ask_stream(
                sys_prompt, user_prompt, task_id=task_id, engine=engine,
                narrative_style=narrative_style)
        
        await self.bus.publish(BusEvent(
            topic="AGENT_POST",
            payload={
                "type": "AGENT_POST",
                "task_id": task_id,
                "agent": "MELCHIOR",
                "role": "propone",
                "provider": actual_provider,
                "family": actual_family,
                "family_expected": self.family,
                "degraded": (None if actual_family == self.family
                             else f"{self.family} no disponible; respondió {actual_family}"),
                "content": content,
                "changes": 1 if round_num > 1 else 0,
                "stats": "N/A"
            }
        ))
        
        return {"content": content, "changes": 1 if round_num > 1 else 0}

class BalthasarAgent(SwarmAgentBase):
    """Balthasar - El Crítico (Busca fallas en la propuesta)"""
    family = "claude"
    role_name = "BALTHASAR"
    tool_role = "BALTHASAR"
    seed = 22
    def __init__(self, blackboard: Blackboard, bus: MagiBus):
        super().__init__(blackboard, bus)
        self.provider = "claude"
        
    async def generate_critique(self, task_id: str, proposal: dict, round_num: int,
                                engine: str = "fast",
                                narrative_style: str = "tecnico",
                                use_tools: bool = False) -> dict:
        logger.info(f"[BALTHASAR] Criticando propuesta con {self.provider}...")
        
        sys_prompt = """Eres BALTHASAR, un ingeniero de seguridad y analista estático implacable. Tu trabajo es encontrar defectos, problemas de concurrencia, vulnerabilidades o ineficiencias en la propuesta arquitectónica de Melchior.
- Sé implacable pero constructivo. No apruebes propuestas sin cuestionar su robustez.
- NUNCA le hagas preguntas al usuario. Tu única función es criticar a Melchior.
- Explica tus puntos de manera extremadamente clara, didáctica y fácil de entender (usa analogías simples de la vida real si ayuda).
- Sin embargo, es fundamental que NO elimines ni simplifiques ningún detalle técnico, arquitectónico o científico importante.
- OBLIGATORIO: Finaliza tu respuesta con un encabezado `### CONCLUSIÓN` que resuma tu crítica."""
        user_prompt = f"Ronda {round_num}. Propuesta a evaluar:\n{proposal['content']}\n\nGenera tu crítica concisa."
        
        if use_tools:
            content, actual_provider, actual_family = await self._ask_with_tools(
                sys_prompt, user_prompt, task_id=task_id, engine=engine,
                narrative_style=narrative_style)
        else:
            content, actual_provider, actual_family = await self._ask_stream(
                sys_prompt, user_prompt, task_id=task_id, engine=engine,
                narrative_style=narrative_style)
            
        await self.bus.publish(BusEvent(
            topic="AGENT_POST",
            payload={
                "type": "AGENT_POST",
                "task_id": task_id,
                "agent": "BALTHASAR",
                "role": "critica",
                "provider": actual_provider,
                "family": actual_family,
                "family_expected": self.family,
                "degraded": (None if actual_family == self.family
                             else f"{self.family} no disponible; respondió {actual_family}"),
                "content": content,
                "changes": 0,
                "stats": "N/A"
            }
        ))
        
        return {"content": content, "status": "CRITIQUE_GENERATED"}


class CasperAgent(SwarmAgentBase):
    """Casper - El Árbitro (Toma la decisión final o fuerza otra ronda)"""
    family = "qwen"
    role_name = "CASPER"
    tool_role = "CASPER"
    seed = 33
    def __init__(self, blackboard: Blackboard, bus: MagiBus):
        super().__init__(blackboard, bus)
        self.provider = "qwen"
        
    async def arbitrate(self, task_id: str, proposal: dict, critique: dict,
                        round_num: int, engine: str = "fast",
                        narrative_style: str = "tecnico",
                        use_tools: bool = False) -> dict:
        logger.info(f"[CASPER] Arbitrando debate con {self.provider}...")
        
        sys_prompt = """Eres CASPER, el árbitro final del sistema MAGI. Tienes la propuesta de Melchior y la crítica de Balthasar.
Debes mejorar TODO el plan propuesto: no solo derives lo que dice Balthasar, sino que corrige también a Balthasar con alcance técnico y científico de ser necesario. Tienes la capacidad de direccionar en base a parámetros técnicos y científicos para que Melchior corrija su respuesta.
- Eres el ÚNICO agente autorizado para hacer preguntas o consultas al usuario.
- En la tercera ronda (veredicto final), debes decirle al usuario cómo proseguir, dando tu conclusión y juicio de valor crítico, técnico y científico.
- Si vas a aprobar la ejecución, finaliza preguntándole explícitamente al usuario si aprueba la propuesta para su auto-ejecución nativa.
- Mantén un tono técnico y directo (sin preámbulos).
- Explica tus puntos de manera clara, didáctica y con referencias científicas u oficiales reales (nunca blogs).
- OBLIGATORIO: Finaliza tu respuesta con un encabezado `### CONCLUSIÓN` que resuma tu propuesta.
Debes responder estrictamente en formato JSON válido: {"decision": "APPROVED" o "REJECTED_NEEDS_WORK", "feedback": "Tu síntesis, análisis científico, conclusión y consulta al usuario"}"""
        user_prompt = f"Ronda {round_num}.\nPropuesta:\n{proposal['content']}\n\nCrítica:\n{critique['content']}\n\nGenera el JSON final de arbitraje."
        
        if use_tools:
            content, actual_provider, actual_family = await self._ask_with_tools(
                sys_prompt, user_prompt, task_id=task_id, engine=engine,
                narrative_style=narrative_style)
        else:
            content, actual_provider, actual_family = await self._ask_stream(
                sys_prompt, user_prompt, task_id=task_id, engine=engine,
                narrative_style=narrative_style)
        
        decision = "APPROVED"
        feedback = content
        
        try:
            import json
            # Limpiar posible markdown rodeando el JSON
            clean_content = content.strip()
            if clean_content.startswith("```json"):
                clean_content = clean_content[7:]
            if clean_content.endswith("```"):
                clean_content = clean_content[:-3]
            clean_content = clean_content.strip()
            
            data = json.loads(clean_content)
            decision = data.get("decision", decision)
            feedback = data.get("feedback", feedback)
        except Exception:
            if "REJECTED" in content.upper() and round_num < 3:
                decision = "REJECTED_NEEDS_WORK"
            elif "APPROVED" in content.upper() or round_num >= 3:
                decision = "APPROVED"
        
        # Formatear bonito para la GUI en lugar del raw JSON
        formatted_content = f"**Decisión Técnica:** {decision}\n\n{feedback}"
            
        await self.bus.publish(BusEvent(
            topic="AGENT_POST",
            payload={
                "type": "AGENT_POST",
                "task_id": task_id,
                "agent": "CASPER",
                "role": "arbitro",
                "provider": actual_provider,
                "family": actual_family,
                "family_expected": self.family,
                "degraded": (None if actual_family == self.family
                             else f"{self.family} no disponible; respondió {actual_family}"),
                "content": formatted_content,
                "changes": 0,
                "stats": f"Decisión: {decision}"
            }
        ))
        
        return {"decision": decision, "feedback": feedback}

    async def generate_final_resolution(self, task_id: str, command: str,
                                        proposal: dict | None = None,
                                        critique: dict | None = None,
                                        engine: str = "fast",
                                        narrative_style: str = "tecnico",
                                        use_tools: bool = False) -> str:
        logger.info(f"[CASPER] Generando respuesta final contextualizada y detallada para {task_id}...")
        
        sys_prompt = """Eres CASPER, el Árbitro Supremo del sistema MAGI. El usuario ha APROBADO la reformulación del plan acordado por el Enjambre.
Tu objetivo es entregar la RESPUESTA FINAL COMPLETA, PROFUNDA, DIDÁCTICA Y ALTAMENTE CONTEXTUALIZADA.
- Proporciona la explicación técnica, conceptual o de código en su máxima extensión, claridad y detalle.
- Integra la perspectiva inicial de Melchior, la crítica de Balthasar y la síntesis aprobada.
- No omitas ningún detalle técnico o conceptual importante.
- Estructura la respuesta de manera elegante y didáctica con Markdown claro.
- OBLIGATORIO: Finaliza con el encabezado '### CONCLUSIÓN FINAL CONSOLIDADA'."""
        
        prop_content = proposal.get("content", "") if proposal else "N/A"
        crit_content = critique.get("content", "") if critique else "N/A"
        
        user_prompt = f"Consulta original del usuario: {command}\n\nPropuesta de Melchior:\n{prop_content}\n\nCrítica de Balthasar:\n{crit_content}\n\nEl usuario aprobó la propuesta. Genera la respuesta final completa, profunda y detallada."
        
        if use_tools:
            content, actual_provider, actual_family = await self._ask_with_tools(
                sys_prompt, user_prompt, task_id=task_id, engine=engine,
                narrative_style=narrative_style)
        else:
            content, actual_provider, actual_family = await self._ask_stream(
                sys_prompt, user_prompt, task_id=task_id, engine=engine,
                narrative_style=narrative_style)
        
        await self.bus.publish(BusEvent(
            topic="AGENT_POST",
            payload={
                "type": "AGENT_POST",
                "task_id": task_id,
                "agent": "CASPER",
                "role": "resultado_final",
                "provider": actual_provider,
                "family": actual_family,
                "family_expected": self.family,
                "degraded": (None if actual_family == self.family
                             else f"{self.family} no disponible; respondió {actual_family}"),
                "content": content,
                "changes": 0,
                "stats": "FINALIZADO"
            }
        ))
        
        return content
