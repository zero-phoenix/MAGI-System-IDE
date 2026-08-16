import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

class HierarchicalMemory:
    """
    Pilar 5: Memoria Jerárquica Autosintetizada.
    Observa el tamaño del contexto. Si supera el umbral, comprime
    la información antigua invocando a un modelo local o gratuito,
    destilando el conocimiento para evitar olvidar el hilo a largo plazo.
    """
    def __init__(self, provider, max_tokens: int = 8000):
        self.provider = provider
        self.max_tokens = max_tokens

    async def compress_if_needed(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Comprime el historial si este excede la capacidad."""
        current_len = sum(len(str(item)) for item in history) // 4 # Aproximación burda a tokens

        if current_len < self.max_tokens:
            return history

        logger.warning(f"[MEMORY] Contexto en riesgo ({current_len} tokens). Iniciando auto-síntesis...")

        # Simulamos la extracción de la primera mitad del historial
        half_idx = len(history) // 2
        old_context = history[:half_idx]
        recent_context = history[half_idx:]

        # En el sistema real, aquí llamaríamos a self.provider.generate()
        # pasándole el old_context para que devuelva un resumen jerárquico.
        await asyncio.sleep(0.5)
        summary = "[SÍNTESIS COMPRIMIDA] " + " ".join([str(x)[:10] for x in old_context])

        logger.info("[MEMORY] Compresión exitosa. Reintegrando nodo de memoria densa.")

        new_history = [{"role": "system", "content": summary}] + recent_context
        return new_history
