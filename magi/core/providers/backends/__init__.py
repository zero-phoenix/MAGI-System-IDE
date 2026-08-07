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

# Orden de preferencia entre familias.
#
# El orden anterior (deepseek 10, claude 15, qwen 20, ...) reflejaba qué
# familias razonan mejor EN TEORÍA. El problema es que `select_for_swarm`
# reparte los tres nodos por este orden, así que Melchior, Balthasar y Casper
# acababan en deepseek, claude y qwen: las tres familias que en la verificación
# empírica del 2026-08-06 no tienen ni un solo candidato vivo. El registro
# anunciaba "diversidad=full" con tres proveedores que no responden.
#
# Ahora manda lo verificado. Delante van las familias con al menos un candidato
# que contestó de verdad, ordenadas por latencia medida; detrás, las que hoy
# están agotadas —siguen registradas, porque pueden revivir, pero no se llevan
# los puestos del enjambre.
_PRIORITY = {
    # verificadas: responden por HTTP, sin navegador (ms medidos)
    "gpt": 10,          # Yqcloud 2000ms · WeWordle 2389ms · CopilotApp 1156ms
    "gemini": 15,       # Gemini/gemini-3.5-flash 3421ms
    "command": 20,      # CohereForAI command-a-03-2025 1078ms
    "llama": 25,        # Groq 922ms
    "hf": 30,           # HuggingSpace 890ms
    "perplexity": 35,   # Perplexity/auto 7921ms (respuesta pobre)
    # sin candidato vivo hoy: se registran, pero al final
    "deepseek": 60, "claude": 65, "qwen": 70, "glm": 75,
    # red de seguridad
    "auto": 99,
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
