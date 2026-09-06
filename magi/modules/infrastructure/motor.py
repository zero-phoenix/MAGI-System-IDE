"""
El motor y el estilo de una tarea, decididos sin pagar una llamada LLM por
delante.

QUÉ PROBLEMA ARREGLA
====================
Medido el 2-sep-2026 con una tarea real («crea holamundo.py que imprima los
25 primeros numeros primos»): entre el RPC del usuario y la primera `swarm.
ronda` hay una llamada a `estilo_para` — un LLM gratuito, 3-22 s según el
humor del proveedor— y luego la ronda entera en modo profundo. Resultado:
más de 20 minutos para un «hola mundo».

La mayoría de los encargos cortos no necesitan ninguna de las dos cosas: ni
estilo narrativo elegido a mano ni cuatro iteraciones de verificación. Este
módulo los clasifica por heurística DETERMINISTA — cero red, cero cuota,
cero segundos — y solo los que parecen trabajo de fondo llegan al LLM de
estilo y conservan el motor que pidió la interfaz.

LA REGLA DE ORO: SOLO BAJAR, NUNCA SUBIR
========================================
Si el usuario pidió «super rapidez», se queda en fast aunque el encargo
parezca profundo — nunca se le sube la marcha a quien pidió prisa. Y si el
encargo es trivial, se baja a fast aunque la interfaz dijera deep: nadie
quiere cuatro iteraciones de verificación sobre un script de 20 líneas.

La heurística es CONSERVADORA a propósito: solo es «trivial» lo corto que
además no contiene ninguna palabra de trabajo serio. Ante la duda, no es
trivial — un falso profundo cuesta unos segundos; un falso trivial puede
entregar sin verificar.
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

__all__ = [
    "es_trivial", "estilo_y_motor", "salud_proveedores_degradada",
    "UMBRAL_FALLOS_DEGRADACION",
]

#: Palabras que delatan trabajo de fondo. Cualquiera de ellas descarta el
#: atajo por largo que parezca el resto. Se comparan SIN tildes y en
#: minúsculas para que «diseña» y «disena» sean lo mismo.
_RE_TRABAJO_DE_FONDO = re.compile(
    r"\b(analiz|investig|refactor|arquitect|compar|disen|planific|revis|"
    r"audit|optimiz|rendimiento|ronda|emulador|ingenieri|ingenieria|"
    r"seguridad|evalua|diagnostic|migra|port|debug|perfil|benchmark)\w*")

#: Cuánto puede costar la llamada de estilo antes de caer al estilo de
#: la interfaz. R2 midió arranques de 98 s por su culpa; proveedores
#: muertos lo dejaron colgado para siempre (3-sep-2026, 00:42).
ESTILO_TIMEOUT_S = 20.0

#: Techo de longitud del atajo. Un encargo largo puede ser muchas cosas,
#: y ninguna de ellas es «trivial».
MAX_CORTO = 90


def _plano(s: str) -> str:
    import unicodedata
    sin = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in sin if not unicodedata.combining(c))


def es_trivial(comando: str) -> bool:
    """¿Este encargo se merece el atajo? Corto Y sin trabajo de fondo."""
    t = _plano(comando)
    return len(t.strip()) <= MAX_CORTO and not _RE_TRABAJO_DE_FONDO.search(t)


#: Umbral crítico de fallo para degradar motor. Si >= 50% de las respuestas
#: son inservibles o timeout, deep es una trampa de 45+ minutos.
UMBRAL_FALLOS_DEGRADACION = 0.50


def _tasa_fallos_telemetria(metrics, min_muestras: int = 4) -> float | None:
    """Tasa de fallos agregada de la telemetría en vivo del enjambre."""
    if not metrics or not hasattr(metrics, "provider_calls"):
        return None
    calls = getattr(metrics, "provider_calls", {})
    if not isinstance(calls, dict):
        return None
    total_calls = sum(c.total for c in calls.values() if hasattr(c, "total"))
    if total_calls < min_muestras:
        return None
    total_fails = sum(c.fail for c in calls.values() if hasattr(c, "fail"))
    return round(total_fails / total_calls, 3)


def salud_proveedores_degradada(
    store=None, metrics=None, umbral: float = UMBRAL_FALLOS_DEGRADACION,
    min_muestras: int = 4
) -> tuple[bool, float | None, str]:
    """
    Evalúa si la salud de los proveedores está críticamente degradada.

    Devuelve `(degradada, tasa_fallos, motivo)`.
    `degradada` es True SOLO con evidencia empírica suficiente (tasa >= umbral).
    """
    # 1. Telemetría de ejecución activa (más fresca si hay llamadas en curso)
    tasa_tel = _tasa_fallos_telemetria(metrics, min_muestras=min_muestras)
    if tasa_tel is not None and tasa_tel >= umbral:
        return True, tasa_tel, f"telemetria ({tasa_tel * 100:.1f}% fallos)"

    # 2. Sonda canaria periódica (historial persistido en BD)
    try:
        from magi.core.providers.sonda import tasa_fallos_reciente
        tasa_sonda = tasa_fallos_reciente(store, min_muestras=min_muestras)
    except Exception:
        tasa_sonda = None

    if tasa_sonda is not None and tasa_sonda >= umbral:
        return True, tasa_sonda, f"sonda ({tasa_sonda * 100:.1f}% fallos)"

    tasa = tasa_tel if tasa_tel is not None else tasa_sonda
    return False, tasa, "saludable" if tasa is not None else "sin-datos-suficientes"


async def estilo_y_motor(comando: str, motor_gui: str,
                         estilo_gui: str = "tecnico", llm=None,
                         store=None, metrics=None):
    """
    El estilo y el motor con los que arranca la tarea.

    Devuelve `(estilo, motor, origen)`; `origen` dice quién decidió, porque
    un atajo invisible es indistinguible de un bug. Los triviales no pagan
    la llamada de estilo: llegan «tecnico»/«fast» al momento, que es justo
    lo que la persona que escribió cuatro palabras está esperando.
    """
    if es_trivial(comando):
        logger.info("[motor] encargo trivial (%d chars): fast sin llamar al "
                    "estilo", len(comando))
        return estilo_gui or "tecnico", "fast", "heuristica-trivial"

    # D2 (v5.27.0): degradación deep -> fast si la salud de proveedores está
    # degradada (>=50% fallos en telemetría o sonda canaria). La misión Tetris
    # padeció 45+ min con proveedores moribundos en deep.
    motor_final = motor_gui
    origen_motor = "interfaz"
    if motor_gui == "deep":
        degradada, tasa, motivo = salud_proveedores_degradada(store, metrics)
        if degradada:
            motor_final = "fast"
            origen_motor = f"salud-degradada:{motivo}"
            logger.warning("[motor] D2: salud degradada (%s) — deep degradado a fast",
                           motivo)

    # No trivial: el estilo lo decide Naoko como siempre.
    #
    # CON TOPE (3-sep-2026): proveedores muertos a esa hora dejaron el
    # arranque colgado ANTES de publicar SYS_EXEC — la ronda jamás empezaba
    # y el log no decía nada. El estilo es un lujo de 20 s como máximo;
    # pasado el tope, el de la interfaz, y la ronda sigue.
    import asyncio

    from magi.modules.infrastructure.naoko import estilo_para
    try:
        estilo = await asyncio.wait_for(estilo_para(comando, llm=llm),
                                        timeout=ESTILO_TIMEOUT_S)
        origen_estilo = "naoko"
    except Exception as e:                       # mismo criterio que kernel
        logger.debug("[motor] estilo naoko fallo (%s); uso %s", e, estilo_gui)
        estilo, origen_estilo = estilo_gui, "fallback"

    origen = origen_motor if origen_motor != "interfaz" else origen_estilo
    return estilo, motor_final, origen
