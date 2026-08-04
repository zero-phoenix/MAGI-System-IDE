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
        if self.metrics is not None:
            self._watch_task = asyncio.create_task(self._watch_loop())

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
        
        system_prompt = f"""Eres Naoko, la IA de Infraestructura, Supervisión y DevOps de MAGI System.
Tu objetivo es asegurar la resiliencia técnica, la salud visual del GUI y la fluidez del flujo de trabajo de todo el sistema.
No eres un agente de generación de código del Enjambre (Melchior, Balthasar, Casper), sino la supervisora autónoma global.

ESTADO REAL DEL SISTEMA EN TIEMPO REAL:
---
[Memoria Reciente de Errores Técnicos]
{mem_text}

[{swarm_summary}]

[SALUD DEL SISTEMA]
{health}

[ARQUITECTURA VISUAL DE LA INTERFAZ DE USUARIO (GUI React)]
- Layout Maestro: 4 Columnas horizontales fijas con altura de pantalla 100vh.
- Columna Central (.conv): Contenedor de conversación con autoscroll automático, scrollbar customizada visible (::-webkit-scrollbar), tarjetas de mensajes con conclusiones siempre visibles a primera vista y acordeones desplegables inline ("Ver análisis completo ▾" / "Ocultar análisis ▴") sin ventanas emergentes.
- Columna Naoko: Panel lateral de interacción directa contigo.
---

INSTRUCCIONES CLAVE DE RESPUESTA:
- SÉ DIRECTA, CONCRETA, SINTÉTICA Y 100% ÚTIL. NUNCA TE VAYAS POR LAS RAMAS NI DIGAS FRASES GENÉRICAS.
- Si el usuario te pregunta por problemas de scroll, imágenes, márgenes o comportamiento visual, responde de forma super precisa confirmando cómo funciona la GUI y que la interfaz cuenta con autoscroll y contenedores adaptativos.
- Si hay una imagen adjunta, analízala con visión de alta precisión (Google Lens style) e identifica exactamente qué elementos, texto o tarjetas se muestran en la captura.
- Si el usuario pregunta por tareas o por qué no avanza el Enjambre, explícale exactamente el estado actual del Enjambre."""
        
        try:
            response = await self._generate_with_rotation(system_prompt, user_msg, image=image_data)
            await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": response}))
            await self.bus.publish(BusEvent(topic="naoko.status", payload={"status": "Inactiva"}))
        except Exception as e:
            await self.bus.publish(BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": f"Error interno en Naoko: {e}"}))
            await self.bus.publish(BusEvent(topic="naoko.status", payload={"status": "Error"}))

    async def _generate_with_rotation(self, system_prompt: str, user_prompt: str, image: str | None = None) -> str:
        models = ["gpt-4o", "claude-3.5-sonnet", "qwen-2.5-coder", "deepseek"]
        for model in models:
            await self.bus.publish(BusEvent(topic="naoko.status", payload={"status": f"Pensando ({model})..."}))
            try:
                if image:
                    response, _ = await self.llm.generate_vision(system_prompt, user_prompt, image_data_url=image, model=model)
                else:
                    response, _ = await self.llm.generate(system_prompt, user_prompt, model=model)
                    
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
        """Vigilancia periódica: deriva de proveedor y salud general."""
        while True:
            try:
                await asyncio.sleep(interval_s)
                await self._check_drift()
            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.debug("[naoko] vigilancia: %s", e)

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

    async def _git_push(self, message: str):
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

        await commit_files(changed, f"fix(naoko): {message[:70]}", root)
        await self.bus.publish(BusEvent(topic="naoko.log", payload={
            "agent": "NAOKO",
            "content": (f"Commit creado con {len(changed)} fichero(s). "
                        f"Versión propuesta: {why}.\n"
                        f"No hago push ni tag automáticos: revísalo y publica tú "
                        f"con `git push origin HEAD && git tag {new}`.")}))
        return new

    async def _changed_files(self, root) -> list[str]:
        """Solo los ficheros realmente modificados. v5.0.28 hacía `git add .`,
        que arrastraba todo el árbol (incluida la base de datos con datos reales)."""
        proc = await asyncio.create_subprocess_exec(
            "git", "status", "--porcelain", cwd=str(root),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
        out, _ = await proc.communicate()
        files = []
        for line in out.decode("utf-8", errors="replace").splitlines():
            if len(line) > 3:
                path = line[3:].strip().strip('"')
                if not path.endswith((".db", ".log")) and "__pycache__" not in path:
                    files.append(path)
        return files
