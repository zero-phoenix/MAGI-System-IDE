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
        
    async def generate_proposal(self, task_id: str, command: str, round_num: int) -> dict:
        logger.info(f"[MELCHIOR] Analizando comando con {self.provider}...")
        
        sys_prompt = "Eres MELCHIOR, un arquitecto de software avanzado. Debes proponer una solución técnica estructurada al requerimiento del usuario. Sé directo, técnico y conciso. Si esto es una revisión, mejora la propuesta anterior basándote en las críticas."
        
        loader = self.blackboard.read("global.skills_loader")
        if loader:
            skills = loader.search(command)
            sys_prompt += f"\n\nCATÁLOGO DE SKILLS RELEVANTES:\n{skills}\nPuedes sugerir el uso de estas skills para resolver la tarea."
            
        user_prompt = f"Ronda {round_num}. Requerimiento/Crítica: {command}. Genera la propuesta."
        
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
        
        sys_prompt = "Eres BALTHASAR, un ingeniero de seguridad y analista estático implacable. Tu trabajo es encontrar defectos, problemas de concurrencia, vulnerabilidades o ineficiencias en la propuesta arquitectónica de Melchior. Sé incisivo pero constructivo."
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
        
        sys_prompt = "Eres CASPER, el árbitro final del sistema MAGI. Tienes la propuesta de Melchior y la crítica de Balthasar. Debes evaluar si la propuesta es lo suficientemente sólida para ser aprobada o si Melchior debe hacer otra ronda de mejoras. Debes responder estrictamente en formato JSON: {\"decision\": \"APPROVED\" o \"REJECTED_NEEDS_WORK\", \"feedback\": \"Tu síntesis y orden hacia Melchior\"}"
        user_prompt = f"Ronda {round_num}.\nPropuesta:\n{proposal['content']}\n\nCrítica:\n{critique['content']}\n\nGenera el JSON final de arbitraje."
        
        content, actual_provider = await self.llm.generate(sys_prompt, user_prompt, model=self.provider)
        
        decision = "APPROVED"
        feedback = content
        
        # Parseo simple para robustez ante salidas sucias del LLM
        if "REJECTED" in content.upper() and round_num < 2:
            decision = "REJECTED_NEEDS_WORK"
        elif "APPROVED" in content.upper() or round_num >= 2:
            decision = "APPROVED"
            
        await self.bus.publish(BusEvent(
            topic="AGENT_POST",
            payload={
                "type": "AGENT_POST",
                "task_id": task_id,
                "agent": "CASPER",
                "role": "arbitro",
                "provider": f"{actual_provider} ({self.provider})",
                "content": feedback,
                "changes": 0,
                "stats": "N/A"
            }
        ))
        
        return {"decision": decision, "feedback": feedback}
