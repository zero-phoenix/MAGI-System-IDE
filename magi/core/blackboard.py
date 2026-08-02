import asyncio
import logging
from typing import Dict, Any, List, Callable

logger = logging.getLogger(__name__)

class Blackboard:
    """
    Pizarra Central (Blackboard) para la Mente de Enjambre.
    Agentes autónomos leen de la pizarra y postean soluciones sin 
    coordinación central.
    """
    def __init__(self):
        self.knowledge_base: Dict[str, Any] = {}
        self.subscribers: List[Callable] = []
        
    def post(self, key: str, value: Any):
        """Escribe una hipótesis o resultado en la pizarra y notifica al enjambre."""
        logger.debug(f"[BLACKBOARD] Nuevo post en '{key}': {value}")
        self.knowledge_base[key] = value
        for sub in self.subscribers:
            # Notifica asíncronamente a los agentes del enjambre
            asyncio.create_task(sub(key, value))
            
    def subscribe(self, callback: Callable):
        """Un agente se suscribe para vigilar la pizarra."""
        self.subscribers.append(callback)
        
    def read(self, key: str) -> Any:
        return self.knowledge_base.get(key)
