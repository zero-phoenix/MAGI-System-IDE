import asyncio
import logging
from magi.core.blackboard import Blackboard # type: ignore
from magi.core.bus import MagiBus, BusEvent # type: ignore
from magi.core.providers.cloud import FreeCloudLLM # type: ignore

logger = logging.getLogger(__name__)

class SwarmAgentBase:
    def __init__(self, blackboard: Blackboard, bus: MagiBus):
        self.blackboard = blackboard
        self.bus = bus
        self.llm = FreeCloudLLM()

class MelchiorAgent(SwarmAgentBase):
    """Melchior - El Arquitecto (Propone soluciones)"""
    def __init__(self, blackboard: Blackboard, bus: MagiBus):
        super().__init__(blackboard, bus)
        self.provider = "deepseek" # DeepSeek-Coder (China)
        
    async def generate_proposal(self, task_id: str, command: str, round_num: int, last_proposal: dict | None = None, last_critique: dict | None = None) -> dict:
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
        
        content, actual_provider = await self.llm.generate(sys_prompt, user_prompt, model=self.provider)
        
        await self.bus.publish(BusEvent(
            topic="AGENT_POST",
            payload={
                "type": "AGENT_POST",
                "task_id": task_id,
                "agent": "MELCHIOR",
                "role": "propone",
                "provider": f"{actual_provider} ({self.provider})",
                "content": content,
                "changes": 1 if round_num > 1 else 0,
                "stats": "N/A"
            }
        ))
        
        return {"content": content, "changes": 1 if round_num > 1 else 0}

class BalthasarAgent(SwarmAgentBase):
    """Balthasar - El Crítico (Busca fallas en la propuesta)"""
    def __init__(self, blackboard: Blackboard, bus: MagiBus):
        super().__init__(blackboard, bus)
        self.provider = "claude-3.5-sonnet" # Anthropic Claude (USA)
        
    async def generate_critique(self, task_id: str, proposal: dict, round_num: int) -> dict:
        logger.info(f"[BALTHASAR] Criticando propuesta con {self.provider}...")
        
        sys_prompt = """Eres BALTHASAR, un ingeniero de seguridad y analista estático implacable. Tu trabajo es encontrar defectos, problemas de concurrencia, vulnerabilidades o ineficiencias en la propuesta arquitectónica de Melchior.
- Sé implacable pero constructivo. No apruebes propuestas sin cuestionar su robustez.
- NUNCA le hagas preguntas al usuario. Tu única función es criticar a Melchior.
- Explica tus puntos de manera extremadamente clara, didáctica y fácil de entender (usa analogías simples de la vida real si ayuda).
- Sin embargo, es fundamental que NO elimines ni simplifiques ningún detalle técnico, arquitectónico o científico importante.
- OBLIGATORIO: Finaliza tu respuesta con un encabezado `### CONCLUSIÓN` que resuma tu crítica."""
        user_prompt = f"Ronda {round_num}. Propuesta a evaluar:\n{proposal['content']}\n\nGenera tu crítica concisa."
        
        content, actual_provider = await self.llm.generate(sys_prompt, user_prompt, model=self.provider)
            
        await self.bus.publish(BusEvent(
            topic="AGENT_POST",
            payload={
                "type": "AGENT_POST",
                "task_id": task_id,
                "agent": "BALTHASAR",
                "role": "critica",
                "provider": f"{actual_provider} ({self.provider})",
                "content": content,
                "changes": 0,
                "stats": "N/A"
            }
        ))
        
        return {"content": content, "status": "CRITIQUE_GENERATED"}


class CasperAgent(SwarmAgentBase):
    """Casper - El Árbitro (Toma la decisión final o fuerza otra ronda)"""
    def __init__(self, blackboard: Blackboard, bus: MagiBus):
        super().__init__(blackboard, bus)
        self.provider = "qwen-2.5" # Qwen Alibaba (China)
        
    async def arbitrate(self, task_id: str, proposal: dict, critique: dict, round_num: int) -> dict:
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
        
        content, actual_provider = await self.llm.generate(sys_prompt, user_prompt, model=self.provider)
        
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
                "provider": f"{actual_provider} ({self.provider})",
                "content": formatted_content,
                "changes": 0,
                "stats": f"Decisión: {decision}"
            }
        ))
        
        return {"decision": decision, "feedback": feedback}
