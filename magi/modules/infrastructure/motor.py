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

__all__ = ["es_trivial", "estilo_y_motor"]

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


async def estilo_y_motor(comando: str, motor_gui: str,
                         estilo_gui: str = "tecnico", llm=None):
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

    # No trivial: el estilo lo decide Naoko como siempre, y el motor es el
    # de la interfaz — aquí no se sube ni se baja nada.
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
        origen = "naoko"
    except Exception as e:                       # mismo criterio que kernel
        logger.debug("[motor] estilo naoko fallo (%s); uso %s", e, estilo_gui)
        estilo, origen = estilo_gui, "fallback"
    return estilo, motor_gui, origen
