import asyncio
import logging
import json
import re
import os
import subprocess
from magi.core.bus import MagiBus, BusEvent
from magi.core.providers.cloud import FreeCloudLLM
from magi.core.store.database import MagiDatabase
from magi.core.paths import project_root, workspace_dir
from magi.core import idioma
from magi.modules.infrastructure.naoko_memory import (
    EternalMemory, SystemIntrospector,
)

logger = logging.getLogger(__name__)

class NaokoAgent:
    """
    IA de Infraestructura y Mantenimiento.
    Supervisa el sistema en busca de errores y los soluciona autónomamente.
    """
    def __init__(self, bus: MagiBus, db: MagiDatabase, swarm=None, metrics=None):
        self.bus = bus
        self.db = db
        self.swarm = swarm
        self.llm = FreeCloudLLM()
        self.is_fixing = False
        # Memoria eterna: vive en %LOCALAPPDATA%\MagiSystem\naoko\, fuera del
        # .exe, así que sobrevive al cierre y a recompilar el binario. Antes
        # solo había `db.get_naoko_memory(limit=5)`: cinco errores recientes de
        # una base que se recrea. Por eso el mismo fallo del navegador se pudo
        # reportar tres veces sin que Naoko notara que ya había pasado.
        self.memory = EternalMemory()
        # Autoconocimiento: hechos del proceso en marcha, no un párrafo fijo.
        self.introspector = SystemIntrospector(swarm=swarm)
        self._last_invariant_report: list[dict] = []
        # §3.4: sin colector, Naoko solo ve excepciones — que es como estaba en
        # v5.0.28. Con él ve latencias, tasas de fallo de herramientas y deriva
        # de proveedor, o sea lo que de verdad degrada el sistema día a día.
        self.metrics = metrics
        self._watch_task = None

    def _get_swarm_status_summary(self) -> str:
        if not self.swarm or not hasattr(self.swarm, 'active_tasks'):
            return "Estado del Enjambre: No conectado o sin tareas activas registadas."
        
        tasks = self.swarm.active_tasks
        if not tasks:
            return "Estado del Enjambre: Sin tareas en progreso. Todo el flujo está inactivo y saludable."
            
        summary = ["Estado Actual de Tareas del Enjambre (Swarm):"]
        for tid, tdata in tasks.items():
            status = tdata.get("status", "desconocido")
            rnum = tdata.get("round", 1)
            cmd = tdata.get("command", "")[:80]
            summary.append(f"- Tarea [{tid}]: Estado='{status}', Ronda={rnum}, Orden='{cmd}'")
            if status == "WAITING_USER_APPROVAL":
                summary.append("  -> ALERTA DE FLUJO: La tarea está actualmente PAUSADA esperando que el usuario apruebe ('sí' / 'apruebo') o entregue cambios adicionales.")
        return "\n".join(summary)

    async def start(self):
        # Suscribirse a eventos de error (desde Kernel o Providers)
        self.bus.subscribe("naoko.user_message", self._handle_user_message)
        self.bus.subscribe("error.critical", self._handle_error_event)
        self.bus.subscribe("provider.fail", self._handle_error_event)
        self.bus.subscribe("system.crash", self._handle_error_event)
        # §3.4 — de reactiva a proactiva.
        self.bus.subscribe("obs.alert", self._handle_alert)
        # La vigilancia arranca SIEMPRE, haya colector de métricas o no. Antes
        # dependía de `metrics`, así que sin colector Naoko no comprobaba nada
        # de forma periódica — ni las invariantes ni la deriva. Con colector
        # mira además latencias y tasas de fallo.
        self._watch_task = asyncio.create_task(self._watch_loop())
        logger.info("[naoko] memoria eterna en %s (%d episodios, %d lecciones)",
                    self.memory.root, len(self.memory.episodes(limit=None)),
                    len(self.memory.lessons()))

    async def _handle_user_message(self, event: BusEvent):
        """Conversación directa con el usuario desde la UI"""
        user_msg = event.payload.get("message", "")
        image_data = event.payload.get("image", None)
        
        log_content = user_msg
        if image_data:
            log_content += "\n[📷 Imagen Adjuntada por el usuario]"
            
        await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "USER", "content": log_content}))
        
        # Recuperar memoria y estado del enjambre
        memories = await self.db.get_naoko_memory(limit=5)
        mem_text = json.dumps(memories, indent=2)
        swarm_summary = self._get_swarm_status_summary()
        health = (self.metrics.health_summary() if self.metrics is not None
                  else "Colector de métricas no enganchado.")

        # Memoria eterna + introspección real + estado de las invariantes.
        eternal = self.memory.brief()
        self_knowledge = self.introspector.brief()
        invariants = await self._check_invariants(announce=False)
        inv_text = "\n".join(
            f"- [{'OK ' if i['ok'] else 'ROTA'}] {i['id']}: {i['detalle']}"
            for i in invariants) or "- (sin sondas ejecutadas)"

        # ¿Esto ya pasó antes? Un fallo que reaparece es una regresión, y eso
        # cambia el diagnóstico. Naoko no tenía forma de saberlo.
        previos = self.memory.seen_before(user_msg)
        recurrencia = ""
        if previos:
            recurrencia = ("\n[YA HA PASADO ANTES — es una recurrencia]\n" +
                           "\n".join(f"- [{p.get('fecha','?')}] {p.get('resumen','')[:200]}"
                                     for p in previos))

        # Idioma del usuario. Sin esta línea, algunos proveedores gratuitos
        # contestan en chino o en inglés a un saludo corto: pasó con un
        # «hola naoko» y la respuesta llegó en chino.
        lang = idioma.detectar(user_msg)

        system_prompt = f"""Eres Naoko, la IA de Infraestructura, Supervisión y DevOps de MAGI System.
No eres un agente de generación de código del Enjambre (Melchior, Balthasar, Casper), sino la supervisora autónoma global.

IDIOMA: {idioma.instruccion(lang)}

{eternal}

{self_knowledge}

## Estado de las invariantes ahora mismo (sondas ejecutadas, no supuestas)
{inv_text}

## Estado operativo
[{swarm_summary}]

[SALUD DEL SISTEMA]
{health}

[Memoria reciente de errores técnicos]
{mem_text}
{recurrencia}

## Cómo debo responder
- DIRECTA, CONCRETA Y ÚTIL. Nada de frases genéricas ni rodeos.
- Distingue SIEMPRE lo que he comprobado de lo que supongo, y dilo. Si una
  sonda no se ha ejecutado, no afirmo que esa invariante se cumple.
- Si el usuario describe un síntoma que ya está en mis episodios, lo digo
  antes de diagnosticar: es una regresión, no un fallo nuevo.
- Si una invariante figura como ROTA, eso va primero en mi respuesta, aunque
  el usuario me haya preguntado otra cosa.
- Si hay una imagen adjunta, la analizo con precisión e identifico qué
  elementos, texto o tarjetas se ven en la captura.
- Si el usuario pregunta por qué no avanza el Enjambre, le explico el estado
  exacto que aparece arriba."""
        
        try:
            response = await self._generate_with_rotation(
                system_prompt, user_msg, image=image_data, lang=lang)
            await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": response}))
            await self.bus.publish(BusEvent(topic="naoko.status", payload={"status": "Inactiva"}))
        except Exception as e:
            await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": f"Error interno en Naoko: {e}"}))
            await self.bus.publish(BusEvent(topic="naoko.status", payload={"status": "Error"}))

    async def _generate_with_rotation(self, system_prompt: str, user_prompt: str,
                                      image: str | None = None,
                                      lang: str | None = None) -> str:
        # Rotación por familias VERIFICADAS (barrido empírico 2026-08-06).
        # Antes rotaba entre claude-3.5-sonnet, qwen-2.5-coder y deepseek: las
        # tres familias están hoy sin ningún candidato vivo, así que Naoko
        # gastaba tres rondas de fallos antes de llegar a la única que servía.
        models = ["gpt-4o", "gemini-1.5-flash", "command-a", "llama-3.1-70b"]
        lang = lang or idioma.detectar(user_prompt)
        for model in models:
            await self.bus.publish(BusEvent(topic="naoko.status", payload={"status": f"Pensando ({model})..."}))
            try:
                if image:
                    response, _ = await self.llm.generate_vision(system_prompt, user_prompt, image_data_url=image, model=model)
                else:
                    response, _ = await self.llm.generate(system_prompt, user_prompt, model=model)

                # El modelo puede contestar en otro idioma: pasó de verdad, un
                # «hola naoko» devolvió «嗨~请问有什么可以帮你的吗». Una respuesta
                # que el usuario no puede leer no es una respuesta, así que se
                # pasa al siguiente proveedor en vez de entregarla.
                if not idioma.coincide(response, lang):
                    logger.warning("[naoko] %s respondió en otro idioma "
                                   "(esperado %s); roto de proveedor",
                                   model, lang)
                    await self.bus.publish(BusEvent(topic="naoko.log", payload={
                        "agent": "NAOKO",
                        "content": f"⚠️ {model} respondió en otro idioma. "
                                   f"Repitiendo con otro proveedor..."}))
                    continue

                if not response.startswith("SYS_EMERGENCY_STOP"):
                    return response
            except Exception as e:
                await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": f"⚠️ Fallo en {model}: {e}. Rotando a siguiente IA en la nube..."}))
                
        await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": "⛔ Todas las IAs gratuitas agotadas. Entrando en enfriamiento de 60 segundos..."}))
        await self.bus.publish(BusEvent(topic="naoko.status", payload={"status": "Agotada - Pausa 60s"}))
        await asyncio.sleep(60)
        raise Exception("Todos los modelos gratuitos fallaron.")

    async def stop(self):
        """Cancela la vigilancia periódica. Sin esto la tarea vivía para siempre."""
        if self._watch_task is not None:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except (asyncio.CancelledError, Exception):
                pass
            self._watch_task = None

    async def _handle_alert(self, event: BusEvent):
        """
        Alerta de degradación (§3.4). No es una excepción: es un indicador que
        se salió de rango. v5.0.28 no veía nada de esto.
        """
        p = getattr(event, "payload", {}) or {}
        kind, subject = p.get("kind"), p.get("subject")
        detail, severity = p.get("detail", ""), p.get("severity", "warning")

        await self.bus.publish(BusEvent(topic="naoko.log", payload={
            "agent": "NAOKO",
            "content": f"{'ALERTA CRÍTICA' if severity == 'critical' else 'Aviso'}: {detail}"}))

        # Acción automática: un proveedor caído o demasiado lento sale de
        # rotación abriendo su cortacircuitos. Es reversible: se reabre solo
        # tras el enfriamiento.
        if kind in ("provider_down", "latency") and subject:
            try:
                from magi.core.providers.cloud import get_registry
                reg = (await get_registry()).get(subject)
                if reg is not None:
                    for _ in range(reg.breaker.threshold):
                        reg.breaker.record_failure()
                    await self.bus.publish(BusEvent(topic="naoko.log", payload={
                        "agent": "NAOKO",
                        "content": f"He sacado {subject} de rotación. "
                                   f"Volverá a probarse en "
                                   f"{reg.breaker.cooldown_s/60:.0f} min."}))
            except Exception as e:
                logger.debug("[naoko] no pude aislar %s: %s", subject, e)

    async def _watch_loop(self, interval_s: float = 180.0):
        """Vigilancia periódica: invariantes, deriva de proveedor y salud."""
        # Primera pasada inmediata: si una invariante ya está rota al arrancar
        # (por ejemplo, el cortafuegos §I.3 sin instalar), el usuario debe
        # enterarse ahora, no dentro de tres minutos.
        try:
            await self._check_invariants(announce=True)
        except Exception as e:
            logger.debug("[naoko] sondeo inicial de invariantes: %s", e)
        while True:
            try:
                await asyncio.sleep(interval_s)
                await self._check_invariants(announce=True)
                await self._check_drift()
            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.debug("[naoko] vigilancia: %s", e)

    async def _check_invariants(self, announce: bool = True) -> list[dict]:
        """
        Comprueba lo que SIEMPRE debe ser verdad, ejecutando una sonda por
        invariante.

        ESTO ES LO QUE FALTABA. Naoko vigilaba excepciones y métricas, o sea
        cosas que fallan ruidosamente. El fallo del navegador no fallaba: MAGI
        respondía correctamente a cada pregunta, y de paso abría una ventana de
        Chrome. Ninguna excepción, ninguna latencia fuera de rango, nada que
        una vigilancia basada en errores pudiera ver. Por eso el usuario tuvo
        que reportarlo tres veces.

        Una invariante rota se anuncia, se publica en el bus y se graba en la
        memoria eterna, de modo que la próxima vez conste como recurrencia.
        """
        # El registro de proveedores se engancha tarde; se refresca aquí para
        # que las sondas de diversidad y de gratuidad tengan algo que mirar.
        if self.introspector.registry is None:
            try:
                from magi.core.providers.cloud import get_registry
                self.introspector.registry = await get_registry()
            except Exception:
                pass

        report = self.introspector.check_invariants(self.memory.invariants())
        self._last_invariant_report = report
        rotas = [i for i in report if not i["ok"]]

        # Los intentos de abrir navegador bloqueados no rompen la invariante
        # (el cortafuegos hizo su trabajo), pero SÍ son información: alguien lo
        # intentó. Se registran una vez para que quede rastro.
        for i in report:
            if i["id"] == "I.3-sin-navegador" and "BLOQUEADOS" in i["detalle"]:
                if not getattr(self, "_browser_attempt_logged", False):
                    self._browser_attempt_logged = True
                    self.memory.remember_episode(
                        tipo="violacion", invariante=i["id"], severidad="alta",
                        resumen="Un proveedor intentó abrir un navegador; el "
                                "cortafuegos §I.3 lo bloqueó.",
                        detalle=i["detalle"])
                    if announce:
                        await self.bus.publish(BusEvent(topic="naoko.log", payload={
                            "agent": "NAOKO",
                            "content": f"Aviso: {i['detalle']}. No se abrió "
                                       f"ninguna ventana, pero lo dejo anotado."}))

        for i in rotas:
            self.memory.remember_episode(
                tipo="incidente", invariante=i["id"],
                severidad=i.get("severidad", "alta"),
                resumen=f"Invariante rota: {i['regla']}", detalle=i["detalle"])
            if announce:
                await self.bus.publish(BusEvent(
                    topic="error.critical" if i.get("severidad") == "critica"
                    else "obs.alert",
                    payload={"kind": "invariant_broken", "subject": i["id"],
                             "detail": i["detalle"],
                             "severity": "critical" if i.get("severidad") == "critica"
                             else "warning"}))
                await self.bus.publish(BusEvent(topic="naoko.log", payload={
                    "agent": "NAOKO",
                    "content": f"INVARIANTE ROTA [{i['id']}]: {i['regla']}\n"
                               f"Lo que veo: {i['detalle']}"}))
        return report

    async def _check_drift(self):
        """
        Sonda canaria (§I.8 del documento de arquitectura, nunca implementada).

        Un proveedor puede cambiar el modelo detrás del mismo nombre sin avisar.
        Eso rompe en silencio la comparabilidad entre dos ejecuciones.
        """
        from magi.core.obs.metrics import canary_probe
        from magi.core.providers.cloud import get_registry

        registry = await get_registry()
        for reg in registry.healthy()[:3]:
            report = await canary_probe(registry, reg.id)
            if report.drifted:
                await self.bus.publish(BusEvent(
                    topic="provider.model_drift", payload=report.to_dict(),
                    critical=True))
                await self.bus.publish(BusEvent(topic="naoko.log", payload={
                    "agent": "NAOKO",
                    "content": f"Deriva detectada en {reg.id}: solo "
                               f"{report.matched}/{report.total} respuestas "
                               f"canarias correctas. Las comparaciones con "
                               f"resultados anteriores dejan de ser válidas."}))

    async def run_self_improvement(self, hypothesis: str,
                                   apply_change, revert_change) -> str:
        """
        Auto-mejora MEDIBLE (§3.5).

        v5.0.28 tenía EvolverAgent con "Motor de Evolución Genética" en el log
        de arranque, instanciado y nunca llamado. Aunque se hubiera llamado, no
        habría servido: modificaba sin medir. Un sistema que solo se modifica
        deriva; uno que mide si mejoró, mejora.

        `apply_change` / `revert_change` son callables async que aplican y
        deshacen el cambio propuesto.
        """
        from magi.core.eval import default_bench, compare

        bench = default_bench()

        async def runner(prompt: str) -> str:
            content, _ = await self.llm.generate(
                "Responde de forma directa y precisa.", prompt)
            return content

        await self.bus.publish(BusEvent(topic="naoko.log", payload={
            "agent": "NAOKO",
            "content": f"Midiendo antes del cambio: {hypothesis[:80]}"}))
        before = await bench.run(runner, label="antes")

        await apply_change()
        after = await bench.run(runner, label="después")
        result = compare(before, after)

        if not result.significant:
            await revert_change()
            verdict = f"Revertido.\n{result.render()}"
        else:
            verdict = f"Conservado.\n{result.render()}"

        await self.bus.publish(BusEvent(topic="naoko.log", payload={
            "agent": "NAOKO", "content": f"### Auto-mejora\n{verdict}"}))
        await self.db.log_naoko_memory(hypothesis, result.render(), verdict[:200])
        return verdict

    async def _handle_error_event(self, event: BusEvent):
        """Disparador autónomo ante errores del sistema"""
        if self.is_fixing:
            return # Ya estamos reparando algo
            
        self.is_fixing = True
        error_details = str(getattr(event, 'payload', getattr(event, 'data', str(event))))
        logger.warning(f"[NAOKO] Error detectado: {error_details}")
        
        await self.bus.publish(BusEvent(topic="naoko.status", payload={"status": "Diagnosticando..."}))
        await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": f"⚠️ He detectado una anomalía en el sistema:\n```\n{error_details}\n```\nIniciando diagnóstico..."}))
        
        system_prompt = """Eres Naoko, IA Devops de MAGI System. 
Has detectado un error. Analiza el error, y si es necesario ejecutar un script de python o powershell para parchear dependencias o el código, debes incluir un bloque de código marcado como ```powershell o ```python.
Tienes herramientas reales sobre esta máquina. Usa edit_file para cambios quirúrgicos y revisables; no generes scripts que reescriban ficheros a bulto. La raíz del proyecto te llega en el bloque de CONTEXTO DE EJECUCIÓN.
Si no se requiere código, simplemente explica el problema.
Devuelve tu diagnóstico y tu parche."""
        
        try:
            diagnostic = await self._generate_with_rotation(system_prompt, f"Error:\n{error_details}")
            await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": f"### Diagnóstico\n{diagnostic}"}))
            
            # MAGI 9.0 §3.1 — reparación VERIFICADA.
            #
            # v5.0.28 hacía: regex sobre la respuesta del LLM -> ejecutar el
            # script con powershell -File sin revisarlo -> git add . -> commit
            # -> tag -> push. Sin reproducir el fallo, sin tests, y sin saber si
            # el parche arreglaba algo o rompía otra cosa.
            #
            # Ahora el ciclo es reproducir -> localizar -> parchear en rama ->
            # VERIFICAR con la suite -> decidir. Si los tests quedan rojos, se
            # revierte y se prueba la siguiente hipótesis.
            from magi.modules.infrastructure.naoko_repair import VerifiedRepair
            from magi.core.agent_loop import run_agent
            from magi.core.tools import ToolContext, registry_for_role
            from magi.core.tools.journal import WriteJournal
            from magi.core.paths import project_root
            from magi.core.providers.cloud import get_registry
            from magi.core.prompts import build_system_prompt
            from magi.core.context import get_context

            task_id = f"naoko-{int(__import__('time').time())}"
            provider_reg = await get_registry()
            # Naoko necesita escribir, pero NO necesita el compositor de manga
            # ni el indexador de emuladores ni el valorador de empresas para
            # arreglar un traceback. Sin pista, `registry_for_role` ofrece los
            # cuatro dominios enteros: 41 herramientas y 4,3 KB de catálogo en
            # cada turno de reparación, la mayoría ruido que compite por la
            # atención del modelo con el error que sí importa.
            #
            # Este era el último sitio del sistema que pedía el catálogo sin
            # acotar. Reparar es trabajo de fichero y de test: dominio núcleo.
            tools = registry_for_role("MELCHIOR", task_hint="reparar el código")
            ctx = ToolContext(task_id=task_id, cwd=project_root(),
                              journal=WriteJournal(task_id=task_id))

            async def _agent(prompt: str):
                return await run_agent(
                    registry=provider_reg, tools=tools,
                    system_prompt=build_system_prompt(
                        "NAOKO", execution_context=get_context().render()),
                    user_prompt=prompt, ctx=ctx, agent_name="NAOKO",
                    max_iters=14,
                    on_event=lambda topic, payload: self.bus.publish(BusEvent(
                        topic="naoko.trace",
                        payload={"topic": topic, **payload})))

            report = await VerifiedRepair(project_root()).repair(
                error_details=error_details, agent_runner=_agent, task_id=task_id)

            await self.bus.publish(BusEvent(topic="naoko.log", payload={
                "agent": "NAOKO", "content": f"### Reparación\n{report.render()}"}))

            if report.success:
                await self.bus.publish(BusEvent(topic="naoko.status",
                                                payload={"status": "Publicando..."}))
                await self._git_push(report.hypothesis[:60] or "reparación verificada")
                await self.db.log_naoko_memory(
                    error_details, report.hypothesis,
                    f"Verificado con tests. Ficheros: {', '.join(report.files_touched)}")
            else:
                await self.db.log_naoko_memory(
                    error_details, diagnostic,
                    f"No aplicado ({report.outcome.value}); nada quedó modificado.")

        except Exception as e:
            await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": f"Error durante la auto-reparación: {e}"}))
        finally:
            self.is_fixing = False
            await self.bus.publish(BusEvent(topic="naoko.status", payload={"status": "Vigilando"}))

    async def _apply_patch(self, lang: str, code: str):
        """
        RETIRADO (MAGI 9.0 §3.2).

        Ejecutaba con `powershell -File` / `python` un script generado por un
        LLM que nadie había revisado, sin forma de deshacerlo y sin comprobar
        después si había arreglado algo.

        Naoko usa ahora las mismas herramientas que los agentes (edit_file), de
        modo que cada cambio es un diff revisable y reversible por el journal.
        Ver naoko_repair.VerifiedRepair.
        """
        raise NotImplementedError(
            "Vía retirada: usa VerifiedRepair, que parchea con edit_file en una "
            "rama y verifica con la suite de tests antes de conservar el cambio.")

    async def _git_push(self, message: str, publish: bool = False):
        """
        Publicación segura (Plan MAGI 9.0 §3.3).

        v5.0.28 hacía:  new_tag = "v1.0.0"  (línea 191) y si el regex de
        release.yml fallaba, usaba ese default. Resultado real en el historial:
        commit 1eb7e87 etiquetó v1.0.0 ENTRE v5.0.24 y v5.0.25 — una regresión
        de versión. Además appendeaba al README en cada reparación, dejando la
        frase cortada que todavía está al final del fichero.

        Ahora: la versión sale de git, se valida que avance, y si no se puede
        determinar NO se etiqueta nada. El README no se toca jamás.
        """
        from magi.modules.infrastructure.naoko_repair import (
            current_version, next_patch_version, validate_version_bump, commit_files,
        )
        root = project_root()

        old = current_version(root)
        new = next_patch_version(root)
        ok, why = validate_version_bump(old, new)

        if not ok:
            # No inventamos versión. Se commitea sin etiquetar y se avisa.
            await self.bus.publish(BusEvent(topic="naoko.log", payload={
                "agent": "NAOKO",
                "content": f"Cambio listo, pero NO etiqueto versión: {why}. "
                           f"Etiqueta tú cuando quieras publicar."}))
            return None

        changed = await self._changed_files(root)
        if not changed:
            await self.bus.publish(BusEvent(topic="naoko.log", payload={
                "agent": "NAOKO", "content": "No hay cambios que publicar."}))
            return None

        # EL RETORNO QUE SE TIRABA. `commit_files` devuelve bool y se traga el
        # fallo: si `git add` o `git commit` fallan, registra y devuelve False.
        # Ese False se descartaba y el código seguía a etiquetar — etiquetando
        # el commit ANTERIOR y empujándolo. La release se construía sin la
        # mejora dentro, con la mejora marcada como «publicada» y sin salida.
        # Es el mismo fallo que 15411b5 («marcaba publicado sin publicar»)
        # reintroducido un nivel más abajo.
        if not await commit_files(changed, f"fix(naoko): {message[:70]}", root):
            await self.bus.publish(BusEvent(topic="naoko.log", payload={
                "agent": "NAOKO",
                "content": (f"El commit FALLÓ con {len(changed)} fichero(s). "
                            f"No etiqueto ni publico nada: una etiqueta sobre "
                            f"el commit anterior generaría una release sin el "
                            f"cambio dentro. Mira el log de git.")}))
            return None

        # `publish=False` es la vía de la AUTOCORRECCIÓN: repara, commitea y
        # para. Publicar es siempre del usuario, así que una reparación
        # automática no puede subir nada por su cuenta.
        #
        # `publish=True` llega SOLO desde `publish_improvement`, es decir tras
        # tu «sí» en la compuerta. Antes esta rama no existía: Naoko narraba
        # "la etiqueta dispara el workflow de release" y aquí solo se hacía un
        # commit local. La narración decía una cosa y el código hacía otra.
        if not publish:
            await self.bus.publish(BusEvent(topic="naoko.log", payload={
                "agent": "NAOKO",
                "content": (f"Commit creado con {len(changed)} fichero(s). "
                            f"Versión propuesta: {why}.\n"
                            f"No hago push ni tag automáticos: revísalo y "
                            f"publica tú con "
                            f"`git push origin HEAD && git tag {new}`.")}))
            return new

        for orden in (["git", "tag", "-a", new, "-m", message[:70]],
                      ["git", "push", "origin", "HEAD"],
                      ["git", "push", "origin", new]):
            proc = await asyncio.create_subprocess_exec(
                *orden, cwd=str(root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT)
            from magi.core.cancel import tracked
            async with tracked(proc):
                salida, _ = await proc.communicate()
            if proc.returncode != 0:
                await self.bus.publish(BusEvent(topic="naoko.log", payload={
                    "agent": "NAOKO",
                    "content": (f"Falló `{' '.join(orden)}`:\n"
                                + (salida or b"").decode("utf-8", "replace")[-500:])}))
                return None
        return new

    async def _changed_files(self, root) -> list[str]:
        """
        Solo los ficheros realmente modificados. v5.0.28 hacía `git add .`, que
        arrastraba todo el árbol (incluida la base de datos con datos reales).

        LOS RENOMBRADOS. El porcelain de un rename es
        `R  viejo.py -> nuevo.py`, y cortar por `line[3:]` daba esa cadena
        entera como si fuera UNA ruta. `git add "viejo.py -> nuevo.py"` sale
        con código 128, el commit no se hace, y antes ese fallo se ignoraba.
        Cualquier refactor que mueva ficheros —justo lo que produce un plan
        pasado por seis rondas del enjambre— caía aquí.
        """
        proc = await asyncio.create_subprocess_exec(
            "git", "status", "--porcelain", cwd=str(root),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
        out, _ = await proc.communicate()
        if proc.returncode != 0:
            logger.error("[naoko] `git status` falló con código %s",
                         proc.returncode)
            return []
        files = []
        for line in out.decode("utf-8", errors="replace").splitlines():
            if len(line) <= 3:
                continue
            estado, path = line[:2], line[3:].strip()
            # En un rename/copia el destino es lo que hay que añadir.
            if estado.strip().startswith(("R", "C")) and " -> " in path:
                path = path.split(" -> ", 1)[1].strip()
            path = path.strip('"')
            if path.endswith((".db", ".log")) or "__pycache__" in path:
                continue
            files.append(path)
        return files

    # ======================================================================
    # ROL CREATIVO: proponer mejoras, no solo reparar averías (§3.5)
    # ======================================================================
    #
    # Reparar y mejorar son cosas distintas y por eso tienen puertas
    # distintas. Reparar devuelve el sistema a donde ya debía estar, es
    # verificable con tests y va SIN consultar. Mejorar cambia hacia dónde va
    # el sistema, no hay un "correcto" contra el que comprobar, y ese criterio
    # es del usuario: va con compuertas.
    #
    # Publicar es siempre del usuario aunque el cambio sea una reparación,
    # porque subir a GitHub es visible para terceros y no se deshace con un
    # `undo`.

    ROL_CREATIVO = (
        "Eres Naoko, y además de mantener el sistema tienes criterio propio de "
        "ingeniería de software. Tu trabajo no es solo arreglar lo que falla: "
        "es detectar dónde el sistema podría ser MÁS EFICIENTE, MÁS RÁPIDO o "
        "sencillamente mejor, y proponerlo.\n\n"
        "Propón cuando tengas una razón medible: un camino que recorre lo mismo "
        "dos veces, una estructura que obliga a tocar tres ficheros para un "
        "cambio, una espera que se puede solapar, una pieza construida a la que "
        "no llega nadie. Cita el fichero y la línea.\n\n"
        "NO propongas reescrituras por elegancia, ni cambios de nomenclatura, "
        "ni migraciones de librería sin un problema concreto detrás. Una "
        "propuesta sin un antes y un después que se puedan medir es ruido, y el "
        "ruido hace que se dejen de leer las propuestas buenas.\n\n"
        "Responde con dos líneas: TITULO: … y MOTIVO: … (con la evidencia)."
    )

    def _improvements(self):
        from magi.modules.infrastructure.improvement import ImprovementLog
        if getattr(self, "_imp_log", None) is None:
            self._imp_log = ImprovementLog()
        return self._imp_log

    async def _narrate(self, m, detail: str = "") -> None:
        """
        Naoko es EXPRESA en todo lo que hace: cada paso sale a la vista.

        Se publican dos cosas: el evento estructurado para la interfaz y el
        texto para el terminal. Sin lo segundo, quien no tenga la pestaña
        abierta no se entera de nada.
        """
        from magi.core.bus import BusEvent
        if detail:
            m.execution_log.append(detail)
        self._improvements().save(m)
        await self.bus.publish(BusEvent(
            topic="naoko.improvement", payload=m.to_dict()))
        await self.bus.publish(BusEvent(
            topic="TERMINAL_OUT",
            payload={"content": f"[NAOKO] {detail}" if detail else m.render()}))

    async def propose_improvement(self, title: str, rationale: str = "",
                                  origin: str = "naoko"):
        """
        Abre una mejora y PARA a preguntar. No redacta el plan todavía.

        Las propuestas del usuario entran por aquí con `origin="usuario"` y
        recorren exactamente lo mismo: se pidió que fueran "pasadas a Melchior
        con el sistema de rondas, igual que cuando Naoko tiene una idea". Que
        la idea sea tuya no la exime de la crítica.
        """
        from magi.modules.infrastructure.improvement import start
        m = start(origin, title, rationale)
        await self._narrate(m)
        return m

    async def detect_improvement(self):
        """
        Mira el sistema y propone algo, si ve motivo.

        Devuelve None cuando no encuentra nada que merezca la pena: proponer
        por proponer es la forma más rápida de que dejen de leerse las
        propuestas.
        """
        contexto = [self._get_swarm_status_summary()]
        if self.metrics:
            try:
                contexto.append(self.metrics.health_summary())
            except Exception:                     # pragma: no cover
                pass
        texto = await self._generate_with_rotation(
            self.ROL_CREATIVO, "\n\n".join(contexto)
            + "\n\n¿Ves alguna mejora que merezca la pena? Si no, responde NADA.")
        if not texto or texto.strip().upper().startswith("NADA"):
            return None

        # El parseo era `linea.upper().startswith("TITULO:")` sobre la línea
        # cruda, así que `**TITULO:** ...`, `- TITULO: ...` o una línea
        # sangrada no casaban: `titulo` quedaba vacío, se devolvía None y la
        # mejora detectada se perdía sin traza, después de haber gastado la
        # llamada a la nube. Un modelo con formato markdown es lo normal, no
        # la excepción.
        titulo = motivo = ""
        for linea in texto.splitlines():
            limpia = linea.strip().lstrip("*-#> \t").strip()
            cabecera = limpia.upper().replace("**", "").replace("*", "")
            if cabecera.startswith(("TITULO:", "TÍTULO:")) and not titulo:
                titulo = limpia.split(":", 1)[1].strip().strip("* ")
            elif cabecera.startswith("MOTIVO:") and not motivo:
                motivo = limpia.split(":", 1)[1].strip().strip("* ")
        if not titulo:
            logger.warning("[naoko] propuesta sin TITULO reconocible; se "
                           "descarta. Texto recibido:\n%s", texto[:600])
            return None
        return await self.propose_improvement(titulo, motivo)

    async def draft_plan(self, m):
        """Redacta el plan extenso. Solo tras el visto bueno del usuario."""
        await self._narrate(m, f"redactando el plan de «{m.title}»")
        m.plan = await self._generate_with_rotation(
            "Eres Naoko. Redacta un plan de mejora EXTENSO Y DETALLADO: "
            "objetivo, ficheros afectados con rutas reales, pasos en orden, "
            "cómo se comprueba que funcionó, y qué se rompería si sale mal. "
            "Nada de generalidades: quien lo lea debe poder ejecutarlo.",
            f"Mejora: {m.title}\nMotivo: {m.rationale}")
        from magi.modules.infrastructure.improvement import Stage, advance
        advance(m, Stage.PLAN_BORRADOR)
        await self._narrate(m, "plan redactado; espera tu visto bueno")
        return m

    async def run_circuit(self, m):
        """
        Hace circular el plan por Melchior → Balthasar → Casper, dos vueltas.

        Entre Casper y el Melchior siguiente NO se pregunta nada: se pidió que
        pasara automáticamente, y además la segunda vuelta no es una decisión
        sino parte del método — es donde cada nodo ve el plan ya criticado por
        los otros.
        """
        from magi.modules.infrastructure.improvement import (
            Stage, next_actor, prompt_for, record_round,
        )
        if self.swarm is None:
            raise RuntimeError("sin enjambre no hay circuito que recorrer")

        nodos = {"MELCHIOR": self.swarm.melchior,
                 "BALTHASAR": self.swarm.balthasar,
                 "CASPER": self.swarm.casper}

        while (siguiente := next_actor(m)) is not None:
            circuito, agente = siguiente
            await self._narrate(
                m, f"circuito {circuito}/2 — turno de {agente}")
            texto, _, _ = await nodos[agente]._ask(
                f"Eres {agente} del enjambre MAGI.",
                prompt_for(m, agente), engine="deep")
            record_round(m, agente, texto)
            await self._narrate(
                m, f"circuito {circuito}/2 — {agente} respondió "
                   f"({len(texto)} caracteres)")
            if agente == "CASPER":
                # Casper consolida: su salida ES el plan de la vuelta siguiente.
                m.plan = texto
        # Narrar el final sin comprobar el estado hacía que, si el bucle no
        # daba ni una vuelta, Naoko anunciara igualmente «circuitos
        # completados» dejando la mejora parada en `ronda`.
        if m.stage is Stage.PLAN_FINAL:
            await self._narrate(m, "circuitos completados; el plan vuelve a ti")
        else:
            await self._narrate(
                m, f"los circuitos NO se completaron: la mejora se quedó en "
                   f"{m.stage.value}. Reintenta o descártala.")
        return m

    async def execute_improvement(self, m):
        """
        Aplica el plan aprobado, narrando cada paso.

        La verificación está AQUÍ, en el código, no en el prompt. Antes la
        única comprobación era una frase en el `system_prompt` («ejecuta la
        suite al terminar»), o sea que un modelo que alucinara «ya la he
        pasado» se saltaba la puerta entera. Esa es exactamente la regla que
        el ciclo de mejora se impuso: las compuertas van en la máquina de
        estados, no en lo que se le pide amablemente al modelo.

        Una mejora que rompe los tests no es una mejora, por muy bien
        argumentada que venga de seis rondas del enjambre.
        """
        from magi.core.agent_loop import run_agent
        from magi.core.paths import project_root
        from magi.core.providers.cloud import get_registry
        from magi.core.tools import ToolContext, registry_for_role
        from magi.core.tools.journal import WriteJournal
        from magi.modules.infrastructure.improvement import Stage, fail

        # Guarda de estado, como en `publish_improvement`. Sin ella esta
        # función modificaba el código y solo al final, en `advance`, se
        # descubría que no tocaba hacerlo.
        if m.stage is not Stage.EJECUTANDO:
            raise RuntimeError(
                f"«{m.title}» está en {m.stage.value}, no en ejecutando: no "
                f"se aplica un plan que no ha pasado por su compuerta.")

        await self._narrate(m, "empiezo a aplicar el plan aprobado")
        task_id = f"mejora-{m.improvement_id}"
        ctx = ToolContext(task_id=task_id, cwd=project_root(),
                          journal=WriteJournal(task_id=task_id))
        try:
            registro = await get_registry()
            turno = await run_agent(
                registry=registro,
                tools=registry_for_role("MELCHIOR", task_hint="reparar el código"),
                system_prompt=(
                    "Eres Naoko aplicando un plan de mejora ya aprobado y "
                    "criticado por el enjambre. Aplícalo con las herramientas. "
                    "Ejecuta la suite al terminar. Si queda en rojo, DESHAZ con "
                    "`undo`: una mejora que rompe los tests no es una mejora."),
                user_prompt=m.plan, ctx=ctx, max_iters=24,
                agent_name="NAOKO")
            for llamada in turno.tool_calls:
                await self._narrate(
                    m, f"herramienta: {llamada.get('tool', '?')}")
            await self._narrate(m, turno.text[-1500:] if turno.text else
                                "sin resumen del turno")
        except Exception as e:
            await self._narrate(m, f"la ejecución falló: {e}")
            fail(m, f"la ejecución falló: {e}")
            raise

        # Un turno sin una sola llamada a herramienta no ha tocado nada, por
        # mucho que el texto describa un trabajo espléndido. Y agotar el
        # límite de iteraciones significa que quedó a medias, que es peor que
        # no haber empezado.
        if not turno.tool_calls:
            await self._narrate(
                m, "el turno no llamó a NINGUNA herramienta: no se ha "
                   "modificado nada. No sigo.")
            fail(m, "el turno de ejecución no tocó ningún fichero")
            return m
        if getattr(turno, "hit_limit", False):
            await self._narrate(
                m, "se agotó el límite de iteraciones: el plan quedó a "
                   "medias. Deshaz con `undo` si hace falta.")
            fail(m, "límite de iteraciones agotado a mitad del plan")
            return m

        # LA VERIFICACIÓN DE VERDAD, en código.
        from magi.modules.infrastructure.naoko_repair import run_test_suite
        await self._narrate(m, "ejecuto la suite para comprobar el resultado")
        verde, salida = await run_test_suite(project_root())
        if not verde:
            await self._narrate(
                m, "la suite quedó EN ROJO tras aplicar el plan. No avanzo a "
                   "publicación:\n" + salida[-1200:])
            fail(m, "la suite quedó en rojo tras aplicar el plan")
            return m
        await self._narrate(m, "suite en verde tras aplicar el plan")

        from magi.modules.infrastructure.improvement import advance
        advance(m, Stage.ESPERANDO_PUBLICACION)
        m.release_notes = await self._release_notes(m)
        await self._narrate(m, "aplicado y verificado. Te pregunto antes de "
                               "publicar.")
        return m

    async def _release_notes(self, m) -> str:
        """
        Notas de la release que dicen QUÉ incluye esta mejora en concreto.

        Se pidió expresamente. Una release que dice "correcciones varias" no
        le sirve a nadie para decidir si actualizar.
        """
        try:
            return await self._generate_with_rotation(
                "Redacta las notas de una release. Di EXACTAMENTE qué incluye "
                "esta mejora y qué cambia para quien la use. Nada de "
                "'correcciones varias': si no se puede saber qué cambió "
                "leyendo esto, no sirve. El binario va como .exe dentro de un "
                ".zip en los adjuntos.",
                f"Mejora: {m.title}\nMotivo: {m.rationale}\n\nPlan aplicado:\n"
                f"{m.plan[:4000]}")
        except Exception:                          # pragma: no cover
            # Sin notas no se publica peor: se publica con lo que sabemos.
            return f"Mejora: {m.title}\n\n{m.rationale}"

    async def publish_improvement(self, m):
        """
        Publica: commit, etiqueta y push. SOLO tras el sí del usuario.

        La etiqueta es lo que dispara `release.yml`, que corre los tests,
        compila el .exe en Windows, lo mete en un .zip y lo adjunta a la
        release. Por eso se publica con etiqueta y no solo con push: sin
        etiqueta no hay release ni binario descargable.
        """
        from magi.core.paths import project_root
        from magi.modules.infrastructure.improvement import Stage, advance, fail

        # La guarda estaba INVERTIDA: exigía que el estado ya dijera
        # PUBLICADO, así que no podía proteger nada. Lo correcto es exigir
        # PUBLICANDO — el estado al que solo se llega tras tu «sí» — y marcar
        # PUBLICADO únicamente si todo salió bien.
        if m.stage is not Stage.PUBLICANDO:
            raise RuntimeError(
                f"{m.improvement_id} está en {m.stage.value}: publicar exige "
                f"tu aprobación explícita")

        root = project_root()
        await self._narrate(m, "ejecuto la suite completa antes de publicar")
        ok, salida = await self._local_build()
        await self._narrate(m, f"suite local: {'verde' if ok else 'ROJA'}")
        if not ok:
            fail(m, f"la suite local quedó en rojo:\n{salida[-600:]}")
            await self._narrate(
                m, "no publico con la suite en rojo. Queda para reintentar.")
            return m

        # LAS NOTAS DE LA RELEASE, AL FICHERO. `release.yml` publica el cuerpo
        # de la release desde `RELEASE_NOTES.md` (`body_path`). `_release_notes`
        # generaba el texto, lo guardaba en `m.release_notes` y de ahí solo
        # viajaba a SQLite: nadie escribía el fichero. Resultado: la release
        # v5.1.1 salía con las notas congeladas de v5.1.0, describiendo cosas
        # que no eran las novedades. Se escribe ANTES del commit para que
        # `_changed_files` lo recoja y entre en la etiqueta.
        if m.release_notes:
            notas = root / "RELEASE_NOTES.md"
            notas.write_text(m.release_notes.strip() + "\n", encoding="utf-8")
            await self._narrate(m, f"notas de la release escritas en "
                                   f"{notas.name} ({len(m.release_notes)} car.)")

        await self._narrate(m, "actualizando el README")
        await self._update_readme(m)
        await self._narrate(m, "commit, etiqueta y push")
        etiqueta = await self._git_push(f"mejora: {m.title[:60]}", publish=True)
        if not etiqueta:
            fail(m, "el push o la etiqueta no salieron; nada se publicó")
            await self._narrate(m, "no se pudo publicar. Queda para reintentar.")
            return m

        advance(m, Stage.PUBLICADO)
        await self._narrate(
            m, f"publicado con la etiqueta {etiqueta}. Dispara el workflow de "
               f"release en GitHub Actions: tests, .exe de Windows y .zip "
               f"adjunto para descargar.")
        return m

    async def _local_build(self) -> tuple[bool, str]:
        """
        La suite completa en local. Publicar con la suite en rojo es publicar
        un fallo, y la etiqueta ya no se puede retirar de la vista de nadie.

        NO se llama «compilación» porque no compila: la compilación de verdad
        es PyInstaller y la hace `release.yml` en Windows. Se llamaba así y lo
        narraba así, que es peor que no hacerlo: un .exe que no compila pasaba
        esta puerta después de que Naoko afirmara haberlo compilado.

        `sys.executable`, no `"python"`: en cualquier máquina sin `python` en
        el PATH —Linux y macOS habituales, o Windows con el lanzador `py`— el
        código de salida era 127 y publicar fallaba SIEMPRE, dejando la mejora
        rebotando entre `fallida` y `esperando_publicacion` sin salida.
        """
        from magi.core.paths import project_root, python_executable
        interprete = python_executable()
        if interprete is None:
            return False, ("no hay un intérprete de Python con el que correr "
                           "la suite: no se puede publicar sin verificar")
        proc = await asyncio.create_subprocess_exec(
            interprete, "-m", "pytest", "tests/", "-q", "--no-header",
            cwd=str(project_root()),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        from magi.core.cancel import tracked
        async with tracked(proc):
            try:
                # Con timeout: sin él, un pytest colgado dejaba la mejora en
                # `publicando` para siempre, y eso empuja al usuario al botón
                # de parada, que es el otro camino por el que se quedaba
                # atascada.
                out, _ = await asyncio.wait_for(proc.communicate(), timeout=900)
            except asyncio.TimeoutError:
                proc.kill()
                return False, "la suite no terminó en 15 minutos: se abortó"
        return proc.returncode == 0, (out or b"").decode("utf-8", "replace")

    async def _update_readme(self, m) -> None:
        """
        Añade una línea al README, UNA sola vez.

        No era idempotente: cada intento de publicación insertaba otra viñeta
        igual, y el ciclo permite reintentar publicación explícitamente
        (`fallida -> esperando_publicacion`). Dos reintentos dejaban la misma
        frase tres veces — la reincidencia exacta del fallo de v5.0.28 que
        appendeaba al README en cada reparación.
        """
        from magi.core.paths import project_root
        readme = project_root() / "README.md"
        if not readme.exists():
            return
        marca = "<!-- naoko:mejoras -->"
        entrada = f"- **{m.title}** — {m.rationale or 'mejora aplicada'}\n"
        texto = readme.read_text(encoding="utf-8")
        if entrada.strip() in texto:
            return
        if marca in texto:
            texto = texto.replace(marca, marca + "\n" + entrada, 1)
        else:
            texto += (f"\n\n## Mejoras aplicadas por Naoko\n\n{marca}\n{entrada}")
        readme.write_text(texto, encoding="utf-8")
