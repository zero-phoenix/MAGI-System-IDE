"""
FreeCloudLLM — capa de compatibilidad sobre el nuevo ProviderRegistry.

Mantiene la firma que usan agents.py, naoko.py y orchestrator.py, pero por
debajo ya no hay auto-router ciego: hay familias fijadas, cortacircuitos real,
timeout y caché acotada.

QUÉ CAMBIA RESPECTO A v5.0.28
=============================
1. Se ELIMINA el remapeo que destruía la diversidad:
       if model in ["claude-3.5-sonnet","qwen-2.5","deepseek"]: model = "gpt-4o"
   Ahora 'deepseek' va de verdad a un proveedor deepseek.

2. Se ELIMINA código muerto que el README anunciaba y nunca corría:
   provider_swarm, user_agents (rotación de navegadores), proxies,
   _refresh_proxies, _is_alive, _mark_failure. Cero sitios de llamada en v5.0.28.

3. Se AÑADE timeout por llamada. Antes no había ninguno: un proveedor colgado
   congelaba el enjambre para siempre.

4. La caché pasa de dict sin límite (fuga de memoria) a LRU+TTL.

5. La heurística de censura deja de disparar el kill-switch global. En v5.0.28
   bastaba que una respuesta contuviera "no puedo" o "lo siento" —frases
   normales en español técnico— para abortar todo el sistema (cloud.py:136-159
   -> orchestrator.py:145). Ahora solo se reintenta en otra familia.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from .base import CompletionRequest, Message, ProviderError
from .registry import ProviderRegistry

logger = logging.getLogger(__name__)

# Familia por defecto de cada alias que usaban los agentes.
_ALIAS_TO_FAMILY = {
    "deepseek": "deepseek",
    "deepseek-coder": "deepseek",
    "qwen-2.5": "qwen",
    "qwen-2.5-coder": "qwen",
    "claude-3.5-sonnet": "claude",
    "gpt-4o": "gpt",
    "gpt-4o-mini": "gpt",
    "gpt-4": "gpt",
    "gemini-1.5-flash": "gemini",
    "gemini-3.5-flash": "gemini",
    "llama-3.1-70b": "llama",
    "command-a": "command",
    "command-a-03-2025": "command",
    "perplexity": "perplexity",
}

# Frases que indican rechazo del proveedor. Se usan SOLO para reintentar en otra
# familia, nunca para detener el sistema.
_REFUSAL_HINTS = (
    "i cannot fulfill", "i cannot assist", "i can't help with that",
    "violates policy", "against my programming",
)

_registry: ProviderRegistry | None = None
_registry_lock = asyncio.Lock()


async def get_registry() -> ProviderRegistry:
    """Registro compartido, construido una sola vez."""
    global _registry
    async with _registry_lock:
        if _registry is None:
            from .backends import build_default_registry
            _registry = await build_default_registry(probe=True)
    return _registry


def set_registry(reg: ProviderRegistry) -> None:
    """Inyección para tests (evita tocar la red)."""
    global _registry
    _registry = reg


class FreeCloudLLM:
    """
    Inferencia de nube gratuita, sin claves de API y sin modelos locales
    (§I.3 del documento de arquitectura, confirmado por el usuario).
    """

    def __init__(self, registry: ProviderRegistry | None = None):
        self._registry = registry

    async def _reg(self) -> ProviderRegistry:
        return self._registry or await get_registry()

    @staticmethod
    def _family_for(model: str) -> str:
        return _ALIAS_TO_FAMILY.get((model or "").lower(), "auto")

    async def generate(self, system_prompt: str, user_prompt: str,
                       model: str = "gpt-4o",
                       family: str | None = None,
                       temperature: float = 0.4,
                       seed: int | None = None) -> tuple[str, str]:
        """
        Devuelve (contenido, nombre_del_proveedor_que_respondió).

        El segundo elemento es ahora el proveedor REAL. En v5.0.28 la GUI
        mostraba "G4F_Auto_Router(gpt-4o) (deepseek)" donde el paréntesis final
        era lo que el agente CREÍA usar, no lo que se usó.
        """
        reg = await self._reg()
        # `family` explícita gana sobre el alias de modelo. Es lo que permite que
        # cada nodo del enjambre se quede en SU familia: agents.py pedía
        # model="gpt-4o-mini" en los tres, y eso los mandaba a los tres a la
        # familia "gpt" — reproduciendo el bug de v5.0.28 una capa más arriba.
        fam = family or self._family_for(model)
        prefer = f"g4f-{fam}" if fam != "auto" else None

        req = CompletionRequest(
            messages=[Message("system", system_prompt), Message("user", user_prompt)],
            timeout_s=150.0, temperature=temperature, seed=seed,
        )
        try:
            resp = await reg.complete(req, prefer=prefer)
        except ProviderError as e:
            logger.error("[cloud] todas las familias agotadas: %s", e)
            return (f"[Inferencia no disponible: {e}]", "SYSTEM_ERROR")

        content = resp.content or ""
        if any(h in content.lower() for h in _REFUSAL_HINTS):
            logger.info("[cloud] %s rechazó; reintento en otra familia", resp.provider_id)
            try:
                alt = await reg.complete(req, use_cache=False)
                if alt.provider_id != resp.provider_id and alt.content.strip():
                    return (alt.content, f"{alt.provider_id}:{alt.model}")
            except ProviderError:
                pass

        return (content, f"{resp.provider_id}:{resp.model}")

    async def generate_vision(self, system_prompt: str, user_prompt: str,
                              image_data_url: str,
                              model: str = "gpt-4o") -> tuple[str, str]:
        """Multimodal — lo que Naoko usa para leer capturas de pantalla."""
        reg = await self._reg()
        req = CompletionRequest(
            messages=[Message("system", system_prompt), Message("user", user_prompt)],
            timeout_s=180.0)

        for regn in reg.healthy(need_vision=True):
            provider = regn.provider
            fn = getattr(provider, "complete_vision", None)
            if fn is None:
                continue
            try:
                resp = await asyncio.wait_for(fn(req, image_data_url), timeout=180.0)
                if resp.content.strip():
                    regn.breaker.record_success(resp.latency_ms)
                    return (resp.content, f"{resp.provider_id}:vision")
            except Exception as e:
                regn.breaker.record_failure()
                logger.debug("[cloud] visión falló en %s: %s", regn.id, e)

        return ("[No hay proveedor con visión disponible ahora mismo. "
                "Describe la imagen por texto y sigo.]", "SYSTEM_NO_VISION")

    async def telemetry(self) -> dict[str, Any]:
        return (await self._reg()).telemetry()
