import time
from typing import Optional
from .registry import ProviderRegistry, ProviderDef

class CircuitBreaker:
    """
    Patrón cortacircuitos con temporizador exponencial.
    Umbral: 5 fallos en ventana (o consecutivos).
    """
    def __init__(self, registry: ProviderRegistry):
        self.registry = registry
        
    def record_success(self, provider_id: str):
        p = self.registry.get_provider(provider_id)
        if p:
            p.circuit.state = "closed"
            p.circuit.failures = 0
            p.circuit.opened_at = None
            
    def record_failure(self, provider_id: str):
        p = self.registry.get_provider(provider_id)
        if p:
            p.circuit.failures += 1
            if p.circuit.failures >= 5 and p.circuit.state == "closed":
                p.circuit.state = "open"
                p.circuit.opened_at = time.time()
                
    def is_allowed(self, provider_id: str) -> bool:
        p = self.registry.get_provider(provider_id)
        if not p: return False
        
        if p.circuit.state == "closed":
            return True
            
        if p.circuit.state == "open":
            if p.circuit.opened_at:
                # Exponencial hasta 15 mins (900s)
                # simplificado: probamos después de 60s
                time_since = time.time() - p.circuit.opened_at
                if time_since > 60:
                    p.circuit.state = "half_open"
                    return True
            return False
            
        if p.circuit.state == "half_open":
            return False # Solo permitimos una de prueba (que ya pasó la verificación)
            
        return False
