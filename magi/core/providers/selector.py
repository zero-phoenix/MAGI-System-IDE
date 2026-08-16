from .circuit import CircuitBreaker
from .registry import ProviderDef, ProviderRegistry


class ProviderSelector:
    """
    Algoritmo de puntuación y selección.
    """
    def __init__(self, registry: ProviderRegistry, circuit: CircuitBreaker):
        self.registry = registry
        self.circuit = circuit

    def select_provider(self, req_vision: bool, est_tokens: int) -> ProviderDef | None:
        scored = []
        for pid, p in self.registry.providers.items():
            if not self.circuit.is_allowed(pid):
                continue

            # Filtro duro
            if req_vision and not p.capabilities.vision:
                continue

            # Score (simplified quota headroom to 1 for this MVP mock)
            cap_fit = 1.0
            health = max(0.0, 1.0 - p.stats.error_rate_ewma)
            quota_headroom = 1.0
            speed = 1.0 / (1.0 + p.stats.latency_ms_ewma / 10000.0)

            score = (0.40 * cap_fit) + (0.25 * health) + (0.20 * quota_headroom) + (0.15 * speed)

            # Preferimos nube sobre local según la corrección del usuario
            if p.kind == "nube" or p.kind == "oficial-gratuito":
                score += 1.0 # Fuerte bonificación a nube

            scored.append((score, p))

        if not scored:
            # Fallback forzado a suelo si todo falla. El invocador DEBE pausar tras la unidad.
            fallback = self.registry.get_provider("local-text")
            # Inyectamos una bandera en tiempo de ejecución para indicar que es un fallback extremo
            fallback.requires_pause_after_unit = True
            return fallback

        scored.sort(key=lambda x: x[0], reverse=True)
        chosen = scored[0][1]
        chosen.requires_pause_after_unit = False

        # Si se eligió local porque no quedaban nubes sanas, marcamos la pausa
        if chosen.kind == "local":
            chosen.requires_pause_after_unit = True

        return chosen
