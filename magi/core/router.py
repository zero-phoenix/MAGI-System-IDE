"""
Enrutamiento adaptativo (Plan MAGI 9.0 §2.3).

EL PROBLEMA
===========
v5.0.28, orchestrator.py:174:  `if is_asking_approval or current_round >= 3:`

TODA petición pasaba por el debate popperiano completo: Melchior propone,
Balthasar critica, Casper arbitra, tres rondas. Preguntar "¿qué hora es?"
costaba 9 llamadas a la nube y 60-90 segundos.

El debate es valioso para decisiones de arquitectura. Es absurdo para un saludo.

LA SOLUCIÓN
===========
Un clasificador barato al entrar que elige la ruta. Heurístico primero (0 ms,
0 tokens); solo cae al modelo cuando el heurístico duda.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Route(str, Enum):
    CHAT = "chat"        # 1 agente, sin debate            objetivo < 3 s
    LOOKUP = "lookup"    # 1 agente + web                  objetivo < 8 s
    TASK = "task"        # Melchior con herramientas + Balthasar verifica  < 60 s
    BUILD = "build"      # debate completo + ejecución iterada             minutos


@dataclass
class RoutingDecision:
    route: Route
    confidence: float
    reason: str
    max_rounds: int
    use_tools: bool

    def to_dict(self) -> dict:
        return {"route": self.route.value, "confidence": round(self.confidence, 2),
                "reason": self.reason, "max_rounds": self.max_rounds,
                "use_tools": self.use_tools}


_CHAT = re.compile(
    r"^\s*(hola|buenas|hey|qué tal|que tal|gracias|ok|vale|adiós|adios|"
    r"sí|si|no|entendido|perfecto|genial|prueba|test|ping)\b[\s!?.]*$", re.I)

_CHAT_ABOUT_SELF = re.compile(
    r"\b(quién eres|quien eres|qué eres|que eres|cómo estás|como estas|"
    r"qué puedes hacer|que puedes hacer|ayuda|help)\b", re.I)

_LOOKUP = re.compile(
    r"\b(qué es|que es|quién es|quien es|cuándo|cuando|dónde|donde|"
    r"cuál es|cual es|cuánto|cuanto|define|significa|precio de|"
    r"cotización|noticias|últimas|ultimas|actualidad|hoy en)\b", re.I)

# Verbos de construcción.
_BUILD_VERB = re.compile(
    r"\b(crea|construye|desarrolla|implementa|programa|diseña|"
    r"refactoriza|migra|porta|portea|adapta|investiga)\b", re.I)

# Sustantivos de artefacto: si aparece uno, el alcance es de proyecto aunque la
# frase sea corta ("haz un emulador de NES" son 5 palabras y es un BUILD).
_ARTIFACT = re.compile(
    r"\b(juego|videojuego|emulador|aplicación|aplicacion|app|sistema|"
    r"proyecto|arquitectura|manga|cómic|comic|vídeo|video|dashboard|"
    r"compilador|intérprete|interprete|dynarec|motor|librería|libreria|"
    r"framework|api|servidor|bot|plugin|extensión|extension)\b", re.I)

_BUILD = re.compile(_BUILD_VERB.pattern + "|" + _ARTIFACT.pattern, re.I)

_TASK = re.compile(
    r"\b(arregla|corrige|repara|revisa|lee|abre|busca|encuentra|lista|"
    r"muestra|ejecuta|corre|instala|renombra|mueve|copia|borra|elimina|"
    r"añade|agrega|quita|actualiza|comprueba|verifica|test)\b", re.I)

_COMPLEX = re.compile(
    r"\b(y luego|después|despues|además|ademas|también|tambien|"
    r"por otro lado|asimismo|paso a paso|en detalle|exhaustiv)\b", re.I)


def classify_heuristic(command: str) -> RoutingDecision | None:
    """Clasificación sin coste. None = no está seguro, que decida el modelo."""
    text = (command or "").strip()
    if not text:
        return RoutingDecision(Route.CHAT, 1.0, "vacío", 1, False)

    words = len(text.split())

    if _CHAT.match(text) or (words <= 4 and _CHAT_ABOUT_SELF.search(text)):
        return RoutingDecision(Route.CHAT, 0.95, "saludo o confirmación", 1, False)

    build_verb = bool(_BUILD_VERB.search(text))
    artifact = bool(_ARTIFACT.search(text))
    # (Había aquí un `build_hit = build_verb or artifact` que no usaba nadie:
    # las reglas de abajo combinan las dos señales por separado y con pesos
    # distintos. Una variable calculada y nunca leída deja la duda de si falta
    # aplicarla o sobra; sobraba.)
    task_hit = bool(_TASK.search(text))
    lookup_hit = bool(_LOOKUP.search(text))
    complex_hit = bool(_COMPLEX.search(text))

    # Un sustantivo de artefacto implica alcance de proyecto por sí solo.
    if artifact and (build_verb or words > 5):
        return RoutingDecision(Route.BUILD, 0.85,
                               "artefacto de proyecto solicitado", 1, True)
    if build_verb and (words > 8 or complex_hit):
        return RoutingDecision(Route.BUILD, 0.8,
                               "verbo de construcción + alcance amplio", 1, True)
    if build_verb:
        return RoutingDecision(Route.TASK, 0.7, "verbo de construcción acotado", 1, True)
    if task_hit:
        return RoutingDecision(Route.TASK, 0.8, "acción concreta sobre el sistema", 1, True)
    if lookup_hit and words <= 20:
        return RoutingDecision(Route.LOOKUP, 0.8, "pregunta factual", 1, True)
    if words <= 6:
        return RoutingDecision(Route.CHAT, 0.6, "enunciado muy corto", 1, False)
    return None


CLASSIFIER_PROMPT = """Clasifica la petición del usuario en UNA categoría.

chat   — saludo, charla, pregunta sobre el propio asistente. No requiere trabajo.
lookup — pregunta factual que se responde buscando información.
task    — acción concreta y acotada sobre ficheros, código o el sistema.
build   — construir algo sustancial: proyecto, aplicación, juego, análisis profundo,
          investigación con varias partes.

Responde SOLO con la palabra de la categoría, en minúsculas, sin nada más."""


async def classify(command: str, registry=None, *,
                   allow_model: bool = True) -> RoutingDecision:
    """Heurístico primero; el modelo solo cuando hay duda real."""
    decision = classify_heuristic(command)
    if decision is not None:
        logger.debug("[router] heurístico -> %s (%s)", decision.route.value,
                     decision.reason)
        return decision

    if not allow_model or registry is None:
        return RoutingDecision(Route.TASK, 0.5, "por defecto (sin clasificador)", 1, True)

    try:
        from .providers.base import CompletionRequest, Message
        resp = await registry.complete(
            CompletionRequest(
                messages=[Message("system", CLASSIFIER_PROMPT),
                          Message("user", command[:1500])],
                temperature=0.0, max_tokens=8, timeout_s=25.0),
            use_cache=True)
        label = (resp.content or "").strip().lower()
        for route in Route:
            if route.value in label:
                cfg = {
                    Route.CHAT: (1, False), Route.LOOKUP: (1, True),
                    Route.TASK: (1, True), Route.BUILD: (1, True),
                }[route]
                return RoutingDecision(route, 0.75, f"clasificador ({resp.family})",
                                       cfg[0], cfg[1])
    except Exception as e:
        logger.warning("[router] clasificador falló (%s); uso TASK", e)

    return RoutingDecision(Route.TASK, 0.5, "por defecto tras fallo", 1, True)
