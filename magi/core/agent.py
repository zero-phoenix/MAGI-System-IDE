import asyncio
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

class SwarmAgent:
    """
    Agente Autónomo del Enjambre.
    Reacciona pasivamente a estímulos en la Pizarra (Blackboard).
    """
    def __init__(self, name: str, interest_keys: list[str], process_func: Callable):
        self.name = name
        self.interest_keys = interest_keys
        self.process_func = process_func

    async def observe(self, key: str, value: Any):
        """Callback invocado por el Blackboard."""
        if key in self.interest_keys:
            logger.info(f"[SWARM:{self.name}] Observó cambio en '{key}'. Iniciando inferencia...")
            await asyncio.sleep(0.1) # Simulando pensamiento
            result = self.process_func(value)
            if result:
                logger.info(f"[SWARM:{self.name}] Aportación generada: {result}")
                return result
