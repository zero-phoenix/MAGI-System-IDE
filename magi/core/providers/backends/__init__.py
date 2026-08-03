"""
Backends de inferencia.

RESTRICCIÓN DEL PROYECTO (confirmada por el usuario, y ya presente en §I.3 del
documento de arquitectura): **solo IA de nube gratuita, sin claves de API y sin
modelos locales**. No hay backend de Ollama, ni de OpenRouter con clave, ni de
CLIs de suscripción. Todo pasa por g4f.

La diversidad del enjambre —que en v5.0.28 no existía— se consigue fijando el
proveedor g4f por familia, no dejando el auto-router. Ver g4f_backend.py.
"""
from .echo import EchoProvider
from .g4f_backend import (
    G4FProvider, FAMILY_SPECS, DEFAULT_SWARM_FAMILIES, build_swarm_providers,
)

__all__ = [
    "EchoProvider", "G4FProvider", "FAMILY_SPECS", "DEFAULT_SWARM_FAMILIES",
    "build_swarm_providers", "build_default_registry",
]

# Orden de preferencia entre familias. Las primeras son las que mejor
# rendimiento han dado para razonamiento y código.
_PRIORITY = {
    "deepseek": 10, "claude": 15, "qwen": 20, "gemini": 30,
    "gpt": 40, "command": 50, "glm": 55, "llama": 60,
    "perplexity": 70, "auto": 99,
}


async def build_default_registry(*, probe: bool = True, families=None):
    """
    Registra una familia por backend para que ProviderRegistry pueda repartir
    familias distintas entre Melchior, Balthasar y Casper.

    `auto` (el auto-router de g4f, que es lo único que usaba v5.0.28) queda
    registrado en última posición: sigue siendo la red de seguridad, pero deja
    de ser el camino principal.
    """
    from ..registry import ProviderRegistry

    reg = ProviderRegistry()
    for family in (families or FAMILY_SPECS.keys()):
        reg.register(G4FProvider(family=family), priority=_PRIORITY.get(family, 80))
    if probe:
        await reg.probe_all()
    return reg
