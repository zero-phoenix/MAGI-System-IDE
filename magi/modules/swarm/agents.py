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
    #: cuántas familias distintas se prueban si la respuesta llega en otro
    #: idioma. Acotado a propósito: ver _reintentar_idioma().
    MAX_REINTENTOS_IDIOMA: int = 2
    #: y en el camino CON herramientas, uno solo. Ahí cada reintento reejecuta
    #: el bucle de herramientas entero —entre 50 y 74 s por pasada en el caso
    #: real—, así que el mismo tope de 2 convertiría un turno de un minuto en
    #: uno de tres. Una respuesta en otro idioma se puede volver a pedir; tres
    #: minutos de espera no se devuelven.
    MAX_REINTENTOS_TOOLS: int = 1

    def __init__(self, blackboard: Blackboard, bus: MagiBus):
        self.blackboard = blackboard
        self.bus = bus
        self.llm = FreeCloudLLM()
        # Rama en la que trabaja este agente ahora mismo. La pone el
        # orquestador antes de lanzar cada variante o cada eje.
        self.rama: str | None = None
        self.rama_rol: str = ""
        self.rama_profundidad: int = 0

    def _telemetria(self):
        """
        Escritor de telemetría, o None si no hay tienda a mano.

        Devolver None y seguir es deliberado: los tests construyen agentes
        sueltos, sin orquestador ni base de datos, y medir NUNCA puede ser un
        requisito para funcionar.
        """
        try:
            store = self.blackboard.get("global.task_store")
        except Exception:
            store = None
        if store is None:
            return None
        try:
            from magi.core.store.telemetria import Telemetria
            return Telemetria(store)
        except Exception:                                # pragma: no cover
            return None

    def _rama(self) -> dict:
        """
        Identidad de la rama, para pegarla a cada evento.

        MAGI lanza 2-3 variantes de Melchior EN PARALELO y 4 ejes de crítica de
        Balthasar EN PARALELO. Todos publicaban con el mismo `task_id` y sin
        nada que los distinguiera, así que la interfaz no podía separar de
        quién era cada salida y las apilaba como si fueran una conversación
        lineal. Zcode resuelve esto con `session_task_link(role, depth, path)`
        y Claude Code con `parent_tool_use_id` / `logical_parent_uuid`.
        """
        if not self.rama:
            return {}
        return {"rama": self.rama, "rama_rol": self.rama_rol,
                "profundidad": self.rama_profundidad}

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
        from magi.core import idioma

        # El idioma sale del enunciado del usuario. Sin esta línea un
        # proveedor gratuito puede contestar en otro: se vio a Naoko responder
        # en chino a un «hola», y los tres nodos comparten el mismo catálogo
        # de proveedores, así que están igual de expuestos.
        lang = idioma.detectar(user_prompt)
        full_sys = "\n\n".join([
            sys_prompt,
            f"IDIOMA: {idioma.instruccion(lang)}",
            style_fragment(narrative_style),
            get_context().render(),
        ])
        temp = temperature if engine == "fast" else max(0.1, temperature - 0.2)

        # GUARDA DE IDIOMA. La instrucción del prompt no basta con los
        # proveedores gratuitos: CASPER llegó a entregar su aprobación en
        # chino (三个方案...) porque nadie miraba la respuesta. Si la familia
        # propia del nodo responde en otro alfabeto, se reintenta con otra
        # familia del registry antes de devolver. El usuario no ve nada: solo
        # recibe la respuesta en su idioma, o la mejor que se pudo conseguir.
        content, provider_id = await self.llm.generate(
            full_sys, user_prompt,
            family=self.family, temperature=temp, seed=self.seed)
        if idioma.coincide(content, lang):
            return content, provider_id, self._family_of(provider_id)

        # La familia propia respondió en otro idioma: reintento acotado.
        logger.debug("[%s] familia %s respondió en otro idioma (esperado %s); "
                     "reintentando", self.role_name, self.family, lang)
        content, provider_id = await self._reintentar_idioma(
            full_sys, user_prompt, temp=temp, lang=lang,
            previo=(content, provider_id))
        return content, provider_id, self._family_of(provider_id)

    async def _reintentar_idioma(self, full_sys: str, user_prompt: str, *,
                                 temp: float, lang: str,
                                 previo: tuple[str, str]) -> tuple[str, str]:
        """
        Reintenta en otras familias hasta acertar el idioma, con tope.

        Devuelve la primera respuesta que coincide, o la última obtenida si
        ninguna acierta: entregar algo ilegible es mejor que no entregar nada,
        y es un fallo visible y reversible (el usuario puede volver a pedirlo).

        EL TOPE NO ES PRUDENCIA DECORATIVA. `coincide()` es un detector
        heurístico y es tolerante a propósito, pero puede dar un falso negativo
        —un bloque de código, una respuesta corta llena de tecnicismos—. Sin
        tope, ese único falso negativo dispara una llamada por cada familia
        verificada del catálogo: hasta diez, por agente, por ronda, y son tres
        agentes. Treinta llamadas de red para un turno que debería costar tres.
        El daño de no acertar el idioma es una respuesta ilegible; el de
        reintentar sin freno es un sistema que no responde. Dos intentos cubren
        el caso real (una familia con sesgo de idioma) sin abrir esa puerta.
        """
        from magi.core import idioma
        content, provider_id = previo
        candidatas = self._otras_familias_del_registry()[:self.MAX_REINTENTOS_IDIOMA]
        for familia in candidatas:
            try:
                alt, alt_pid = await self.llm.generate(
                    full_sys, user_prompt,
                    family=familia, temperature=temp, seed=self.seed)
            except Exception as e:
                logger.debug("[%s] reintento en %s falló: %s",
                             self.role_name, familia, e)
                continue
            if idioma.coincide(alt, lang):
                return alt, alt_pid
            content, provider_id = alt, alt_pid  # quedarse con la última
        return content, provider_id

    def _otras_familias_del_registry(self) -> list[str]:
        """Familias distintas a la propia, para rotar si la propia falla de idioma.

        Lee del catálogo de familias verificadas de g4f. El registry es async
        y aquí no podemos esperarlo, pero las familias verificadas son las que
        el registry registraría. Si el catálogo no está cargado, no hay
        rotación y se devuelve lo que haya.
        """
        try:
            from magi.core.providers.backends.g4f_backend import VERIFIED_FAMILIES
            return [f for f in VERIFIED_FAMILIES if f != self.family]
        except Exception:
            return []

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
        from magi.core import idioma

        full_sys = "\n\n".join([
            sys_prompt,
            f"IDIOMA: {idioma.instruccion(idioma.detectar(user_prompt))}",
            style_fragment(narrative_style), get_context().render()])

        ctx = ToolContext(task_id=task_id,
                          cwd=workspace_dir(),
                          journal=WriteJournal(task_id=task_id))

        async def on_event(topic: str, payload: dict) -> None:
            await self.bus.publish(BusEvent(
                topic=topic, payload={"task_id": task_id, **payload}))
            # UX: convertir eventos de timeout/lentitud en mensajes visibles
            # en la terminal sin depender de que el frontend los reconozca.
            if topic == "agent.timeout":
                await self.bus.publish(BusEvent(
                    topic="TERMINAL_OUT",
                    payload={"content":
                             f"[AVISO] {self.role_name} no respondió en "
                             f"{payload.get('timeout_s', '?')}s "
                             f"(proveedor: {payload.get('provider', '?')}). "
                             "Se devuelve respuesta degradada."}))
            elif topic == "agent.slow_iteration":
                await self.bus.publish(BusEvent(
                    topic="TERMINAL_OUT",
                    payload={"content":
                             f"[AVISO] {self.role_name} iteración "
                             f"{payload.get('iteration', '?')} lenta "
                             f"({payload.get('elapsed_s', 0):.1f}s con "
                             f"{payload.get('provider', '?')})."}))

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

        # GUARDA DE IDIOMA (mismo principio que en _ask), CON RED DEBAJO.
        #
        # LA RED NO ES OPCIONAL, Y ESTE ES EL MOTIVO
        # ==========================================
        # Esta guarda existe para mejorar la respuesta: si el proveedor se
        # despista y contesta en otro idioma, se reintenta. Nada más. Y aun así
        # llegó a tumbar el sistema entero.
        #
        # El método al que llamaba se había renombrado y aquí quedó el nombre
        # viejo. Como el `for` estaba FUERA del try, el AttributeError subía
        # hasta arriba:
        #
        #   [parallel] variante 0 falló: 'MelchiorAgent' object has no
        #              attribute '_familias_disponibles'   (x3)
        #   [SWARM] Error catastrófico: ninguna variante de propuesta se
        #           completó
        #
        # Tres variantes muertas, la orquestación caída y el usuario esperando
        # tres minutos para no recibir nada — y todo tras haber generado ya
        # respuestas perfectamente válidas, que se tiraron a la basura.
        #
        # La lección no es «cuidado al renombrar». Es que **una mejora de
        # calidad no puede tener autoridad para matar lo que mejora**. Si el
        # reintento falla, por el motivo que sea, se entrega lo que ya había:
        # una respuesta en otro idioma es un problema; ninguna respuesta es
        # otro mucho peor. Por eso todo el bloque va dentro de un try.
        #
        # Y el tope importa aquí más que en _ask: cada reintento reejecuta el
        # bucle de herramientas ENTERO. En el caso real, cada pasada costó
        # entre 50 y 74 segundos. Sin tope, un falso negativo del detector
        # convertía un turno de un minuto en uno de diez.
        try:
            lang = idioma.detectar(user_prompt)
            if turn.text and not idioma.coincide(turn.text, lang):
                logger.debug("[%s] turno con herramientas en otro idioma "
                             "(esperado %s); reintentando con otra familia",
                             self.role_name, lang)
                for familia in self._otras_familias_del_registry()[
                        :self.MAX_REINTENTOS_TOOLS]:
                    try:
                        alt = await run_agent(
                            registry=registry,
                            tools=registry_for_role(self.tool_role,
                                                    task_hint=user_prompt),
                            system_prompt=full_sys, user_prompt=user_prompt,
                            ctx=ctx,
                            prefer_provider=f"g4f-{familia}",
                            max_iters=max_iters,
                            temperature=0.4 if engine == "fast" else 0.2,
                            seed=self.seed, on_event=on_event,
                            agent_name=self.role_name)
                    except Exception as e:
                        logger.debug("[%s] reintento en %s falló: %s",
                                     self.role_name, familia, e)
                        continue
                    # Solo se ADOPTA el reintento si acierta el idioma. Antes
                    # se sobrescribía `turn` con cada intento, así que un
                    # reintento peor que el original lo sustituía igualmente.
                    if alt.text and idioma.coincide(alt.text, lang):
                        logger.info("[%s] reintento en %s acertó el idioma",
                                    self.role_name, familia)
                        turn = alt
                        break
        except Exception as e:                            # pragma: no cover
            logger.warning("[%s] la guarda de idioma falló (%s); entrego la "
                           "respuesta original", self.role_name, e)

        # §3.4 — CONTABILIDAD DE TOKENS.
        #
        # Estaba construida entera menos el cable del medio: `agent_loop` ya
        # sumaba tokens_in/tokens_out de cada respuesta, `AgentTurn` los
        # traía, y `TaskStore.record_usage()` sabía escribirlos en la tabla
        # `token_ledger`... a la que no llamaba NADIE. La cuenta acababa aquí,
        # metida en una cadena de log por `turn.summary()`, y la tabla llevaba
        # vacía desde que se creó.
        #
        # Es la misma clase de fallo que las piezas sin conectar, pero en los
        # datos: el esquema existe, los métodos existen, y el panel de coste
        # no tiene nada que enseñar porque nadie escribió jamás una fila.
        await self._record_usage(task_id, turn)
        return turn.text, turn.provider_id, self._family_of(turn.provider_id)

    async def _record_usage(self, task_id: str, turn) -> None:
        """Vuelca el gasto del turno al ledger y lo publica para la interfaz."""
        familia = self._family_of(turn.provider_id)
        try:
            from magi.core.store.state import TaskStore
            TaskStore().record_usage(
                task_id=task_id, agent=self.role_name,
                provider=turn.provider_id, family=familia,
                tokens_in=turn.tokens_in, tokens_out=turn.tokens_out,
                latency_ms=turn.elapsed_s * 1000.0)
        except Exception as e:                    # pragma: no cover
            # Contabilizar nunca puede tumbar el turno que contabiliza.
            logger.warning("[%s] no se pudo registrar el gasto: %s",
                           self.role_name, e)
        try:
            await self.bus.publish(BusEvent(topic="task.usage", payload={
                "task_id": task_id, "agent": self.role_name,
                "provider": turn.provider_id, "family": familia,
                "tokens_in": turn.tokens_in, "tokens_out": turn.tokens_out,
                "elapsed_s": round(turn.elapsed_s, 2),
                "iterations": turn.iterations,
                "tool_calls": len(turn.tool_calls),
            }))
        except Exception as e:                    # pragma: no cover
            logger.debug("[%s] no se pudo publicar el gasto: %s",
                         self.role_name, e)

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
        from magi.core import idioma

        # La instrucción de idioma faltaba aquí (estaba en _ask pero no en
        # _ask_stream). Como _ask_stream es el camino principal del enjambre,
        # las tres IA respondían sin que se les dijera en qué idioma hablar.
        lang = idioma.detectar(user_prompt)
        full_sys = "\n\n".join([
            sys_prompt,
            f"IDIOMA: {idioma.instruccion(lang)}",
            style_fragment(narrative_style), get_context().render()])
        temp = temperature if engine == "fast" else max(0.1, temperature - 0.2)

        reg = await self.llm._reg()
        req = CompletionRequest(
            messages=[Message("system", full_sys), Message("user", user_prompt)],
            temperature=temp, seed=self.seed, timeout_s=150.0, stream=True)

        chunks: list[str] = []
        provider_id = f"g4f-{self.family}"
        # Turno medido. Hasta ahora solo se guardaba una latencia media por
        # proveedor: un número que no distingue «tarda en arrancar» de «tarda
        # en generar». Con TTFT y tiempo total separados, la pregunta «¿por
        # qué tarda?» tiene respuesta. Ver core/store/telemetria.py.
        tel = self._telemetria()
        ctx = tel.turno(task_id, self.role_name, familia=self.family,
                        ronda=getattr(self, "_ronda", None)) if tel else None
        turno = ctx.__enter__() if ctx else None
        try:
            if turno:
                turno.intento()
            async for delta in reg.stream(req, prefer=f"g4f-{self.family}"):
                if delta.provider_id:
                    provider_id = delta.provider_id
                if delta.text:
                    if turno:
                        # Solo la primera marca cuenta: es el TTFT.
                        turno.primer_token()
                    chunks.append(delta.text)
                    await self.bus.publish(BusEvent(
                        topic="agent.delta",
                        payload={"task_id": task_id, "agent": self.role_name,
                                 "family": self._family_of(provider_id),
                                 "provider": provider_id,
                                 "text": delta.text, "seq": delta.seq,
                                 **self._rama()}))
                if delta.done:
                    await self.bus.publish(BusEvent(
                        topic="agent.delta_end",
                        payload={"task_id": task_id, "agent": self.role_name,
                                 **self._rama()}))
            if turno:
                turno.proveedor = provider_id
                turno.familia = self._family_of(provider_id)
                turno.tokens(entrada=len(full_sys) + len(user_prompt),
                             salida=len("".join(chunks)))

            # GUARDA DE IDIOMA EN EL CAMINO DE STREAMING.
            #
            # Esta era la mitad que faltaba. La INSTRUCCIÓN de idioma se había
            # añadido aquí, pero la COMPROBACIÓN solo existía en _ask. Y como
            # _ask_stream es el camino real del enjambre —_ask solo se usa como
            # red cuando el flujo falla—, una respuesta en chino seguía
            # llegando entera al usuario. Es exactamente lo de la captura: los
            # tres nodos hablando en otro idioma con la guarda ya «arreglada».
            #
            # El texto ya se ha visto pasar en vivo; no se puede des-enviar.
            # Lo que sí se puede es no dejarlo como respuesta final: se cierra
            # el flujo con el mismo `aborted` que ya usa el fallback de error
            # (el front borra el buffer parcial al recibirlo) y se reintenta
            # sin streaming. El usuario ve el texto raro desaparecer y llegar
            # la respuesta buena, que es el comportamiento menos malo posible
            # cuando el proveedor ya ha hablado.
            texto = "".join(chunks)
            if texto and not idioma.coincide(texto, lang):
                logger.debug("[%s] el flujo llegó en otro idioma (esperado %s); "
                             "reintento sin streaming", self.role_name, lang)
                await self.bus.publish(BusEvent(
                    topic="agent.delta_end",
                    payload={"task_id": task_id, "agent": self.role_name,
                             "aborted": True, **self._rama()}))
                alt, alt_pid = await self._reintentar_idioma(
                    full_sys, user_prompt, temp=temp, lang=lang,
                    previo=(texto, provider_id))
                return alt, alt_pid, self._family_of(alt_pid)
        except Exception as e:
            if turno:
                turno.fallo(e)
            # Si YA hay texto, no se tira. Antes cualquier excepción a mitad
            # del flujo mandaba a pedir la respuesta entera otra vez, y la
            # excepción más frecuente no era del proveedor: era escribir un
            # acento en la consola cp1252 de Windows. Se perdían diez segundos
            # de respuesta ya generada por un problema de codificación del log.
            #
            # La causa se cierra en magi/core/consola.py; esto es la red: una
            # respuesta parcial y utilizable vale más que repetir la llamada.
            if chunks:
                logger.warning("[%s] el flujo se cortó (%s), pero ya había "
                               "%d fragmentos: me quedo con lo recibido",
                               self.role_name, e, len(chunks))
                await self.bus.publish(BusEvent(
                    topic="agent.delta_end",
                    payload={"task_id": task_id, "agent": self.role_name}))
                return ("".join(chunks), provider_id,
                        self._family_of(provider_id))

            logger.warning("[%s] streaming falló (%s); caigo a no-streaming",
                           self.role_name, e)
            await self.bus.publish(BusEvent(
                topic="agent.delta_end",
                payload={"task_id": task_id, "agent": self.role_name,
                         "aborted": True}))
            return await self._ask(sys_prompt, user_prompt, engine=engine,
                                   narrative_style=narrative_style,
                                   temperature=temperature)  # ya devuelve 3-tupla
        finally:
            # Cerrar SIEMPRE. Un turno abierto para siempre es la misma clase
            # de fallo que las tareas zombis, y ya la cometimos una vez: algo
            # que figura en curso sin estarlo envenena todo lo que lo lea.
            if ctx is not None:
                try:
                    ctx.__exit__(None, None, None)
                except Exception:
                    pass

        return "".join(chunks), provider_id, self._family_of(provider_id)

def _familia_por_defecto(rol: str) -> str:
    """
    Familia asignada a un rol, tomada del ÚNICO sitio donde se decide.

    Los tres nodos tenían su familia escrita a fuego en la clase
    (`family = "deepseek"`, `"claude"`, `"qwen"`). Cuando el catálogo se
    reverificó y esas tres familias resultaron no tener ni un candidato vivo,
    se actualizó `DEFAULT_SWARM_FAMILIES`... y a los agentes no les llegó,
    porque leían su propio atributo. El resultado está en el registro del
    usuario:

        [MELCHIOR] Analizando comando con deepseek...
        [registry] g4f-deepseek falló: familia 'deepseek' agotada (4 candidatos)
        [registry] g4f-claude falló: familia 'claude' agotada (2 candidatos)
        [registry] g4f-claude falló: ... (x4)

    Cada ronda gastaba seis intentos contra proveedores que no pueden
    responder —dos de ellos intentando abrir Chrome, bloqueados— antes de
    caer a los que sí. Eso es la demora que se notaba.

    Derivarlo elimina la clase de fallo entera: no puede haber dos verdades
    sobre qué familia usa cada nodo si solo hay una escrita.
    """
    from magi.core.providers.backends.g4f_backend import DEFAULT_SWARM_FAMILIES
    return DEFAULT_SWARM_FAMILIES.get(rol.upper(), "auto")


class MelchiorAgent(SwarmAgentBase):
    """Melchior - El Arquitecto (Propone soluciones)"""
    role_name = "MELCHIOR"
    tool_role = "MELCHIOR"
    seed = 11

    def __init__(self, blackboard: Blackboard, bus: MagiBus):
        super().__init__(blackboard, bus)
        self.family = _familia_por_defecto("MELCHIOR")
        self.provider = self.family
        
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
- Si el usuario pide un ejecutable .exe portable, primero crea el proyecto Python en workspace/ y luego invoca la herramienta `build_project_exe(path=<directorio>, name=<nombre>, output=<ruta del .exe>)`. El bundle de MAGI incluye un intérprete Python embebido, así que NO dependas de que el usuario tenga Python instalado.
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
    role_name = "BALTHASAR"
    tool_role = "BALTHASAR"
    seed = 22

    def __init__(self, blackboard: Blackboard, bus: MagiBus):
        super().__init__(blackboard, bus)
        self.family = _familia_por_defecto("BALTHASAR")
        self.provider = self.family
        
    async def generate_critique(self, task_id: str, proposal: dict, round_num: int,
                                engine: str = "fast",
                                narrative_style: str = "tecnico",
                                use_tools: bool = False) -> dict:
        logger.info(f"[BALTHASAR] Criticando propuesta con {self.provider}...")
        
        sys_prompt = """Eres BALTHASAR, un ingeniero de seguridad y analista estático implacable. Tu trabajo es encontrar defectos, problemas de concurrencia, vulnerabilidades o ineficiencias en la propuesta arquitectónica de Melchior.
- Sé implacable pero constructivo. No apruebes propuestas sin cuestionar su robustez.
- NUNCA le hagas preguntas al usuario. Tu única función es criticar a Melchior.
- Si la propuesta genera un juego, una GUI, un vídeo, una imagen o cualquier artefacto ejecutable, DEBES usar `observe_artifact` (o `record_program` para vídeo) sobre el resultado y citar lo que SE VE en tu crítica. No critiques solo el código si puedes mirar el artefacto.
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
    role_name = "CASPER"
    tool_role = "CASPER"
    seed = 33

    def __init__(self, blackboard: Blackboard, bus: MagiBus):
        super().__init__(blackboard, bus)
        self.family = _familia_por_defecto("CASPER")
        self.provider = self.family
        
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
- Si la propuesta genera un ejecutable (.exe), un juego o un artefacto visual, exige que Balthasar lo haya observado y cita el resultado de la observación en tu veredicto. No apruebes a ciegas.
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


# Se fija también en la CLASE, no solo en la instancia.
#
# Al mover la familia a `__init__` para que la leyera de DEFAULT_SWARM_FAMILIES,
# `MelchiorAgent.family` quedó valiendo "auto" —el defecto de la clase base— y
# eso lo cazó `test_each_agent_declares_a_distinct_family`, que comprueba la
# diversidad del enjambre (§1.1) sin instanciar nada. Tenía razón el test: si
# el atributo de clase miente, cualquiera que lo lea sin instanciar se lleva un
# dato falso.
#
# Va aquí abajo, después de las tres clases, porque `_familia_por_defecto`
# importa el backend de proveedores y hacerlo en la cabecera crearía un ciclo.
for _cls, _rol in ((MelchiorAgent, "MELCHIOR"),
                   (BalthasarAgent, "BALTHASAR"),
                   (CasperAgent, "CASPER")):
    _cls.family = _familia_por_defecto(_rol)
del _cls, _rol
