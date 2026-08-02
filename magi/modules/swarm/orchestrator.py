import asyncio
import logging
from magi.core.blackboard import Blackboard
from magi.core.bus import MagiBus, BusEvent
from .agents import MelchiorAgent, BalthasarAgent, CasperAgent

logger = logging.getLogger(__name__)

class SwarmOrchestrator:
    """
    Controla el ciclo de vida de un debate Popperiano en el Enjambre (Área 16).
    Evita que los agentes hablen al mismo tiempo, manejando el turn-taking.
    """
    def __init__(self, blackboard: Blackboard, bus: MagiBus):
        self.blackboard = blackboard
        self.bus = bus
        self.active_tasks = {}
        
        # Inicializar agentes
        self.melchior = MelchiorAgent(self.blackboard, self.bus)
        self.balthasar = BalthasarAgent(self.blackboard, self.bus)
        self.casper = CasperAgent(self.blackboard, self.bus)

    async def submit_task(self, task_id: str, command: str):
        """Inicia un nuevo flujo de trabajo en el enjambre."""
        logger.info(f"[SWARM] Iniciando tarea {task_id}: {command}")
        self.active_tasks[task_id] = {
            "command": command,
            "round": 1,
            "status": "in_progress"
        }
        
        await self.bus.publish(BusEvent(
            topic="TERMINAL_OUT",
            payload={"content": f"[SWARM] Iniciando análisis para la tarea: '{command}'"}
        ))
        
        # Arrancar el bucle de la conversación asíncronamente
        asyncio.create_task(self._orchestrate_loop(task_id))
        
    async def _orchestrate_loop(self, task_id: str):
        state = self.active_tasks[task_id]
        
        while state["status"] == "in_progress":
            current_round = state["round"]
            logger.info(f"[SWARM] Iniciando Ronda {current_round} para {task_id}")
            
            # 1. Melchior Propone
            last_proposal = state.get("last_proposal")
            last_critique = state.get("last_critique")
            proposal = await self.melchior.generate_proposal(task_id, state["command"], current_round, last_proposal, last_critique)
            self.blackboard.post(f"{task_id}.proposal", proposal)
            
            # 2. Balthasar Critica
            critique = await self.balthasar.generate_critique(task_id, proposal, current_round)
            self.blackboard.post(f"{task_id}.critique", critique)
            
            # 3. Casper Arbitra
            verdict = await self.casper.arbitrate(task_id, proposal, critique, current_round)
            self.blackboard.post(f"{task_id}.verdict", verdict)
            
            if verdict["decision"] == "APPROVED":
                state["status"] = "completed"
                await self.bus.publish(BusEvent(
                    topic="TERMINAL_OUT",
                    payload={"content": f"[SWARM] Ejecución completada en Ronda {current_round}. Consolidando cambios en el árbol del proyecto."}
                ))
            elif verdict["decision"] == "REJECTED_NEEDS_WORK":
                state["round"] += 1
                state["last_proposal"] = proposal
                state["last_critique"] = critique
                state["command"] = f"Revisar propuesta considerando crítica: {verdict['feedback']}"
                # Pequeña pausa antes de la siguiente ronda
                await asyncio.sleep(1.0)
            else:
                state["status"] = "failed"
                await self.bus.publish(BusEvent(
                    topic="TERMINAL_OUT",
                    payload={"content": f"[SWARM] Tarea fallida tras {current_round} rondas."}
                ))
