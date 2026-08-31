"""
Una corrida del emulador solo existe si se VE (R9).

LA CORRIDA QUE OBLIGÓ A ESCRIBIR ESTO
=====================================
30 de agosto de 2026, ronda 1 de YabauseVita. El log decía:

    FPS: 59.9   (estable, ventana tras ventana)
    GPU: drawn=296 presented=296 dropped=0

Y la pantalla era negra. Negra de verdad — 93,6 % de los píxeles, con la
BIOS de la Saturn sin haber encendido la salida de vídeo (TVMD.DISP=0) y
un intérprete SH2 roto que ejecutaba el 2 % del trabajo. El contador de
FPS cuenta llamadas al lazo de emulación: un core que no ejecuta
instrucciones también «hace 60 FPS».

La captura continua de la ventana lo enseñó en segundos; el log llevaba
media hora mintiendo con números perfectos. Nadie mira la pantalla por
defecto — ni el enjambre, ni quien lee el informe — así que la corrida
tiene que traer sus propios ojos.

QUÉ HACE
========
Cuando el encargo es una corrida o medición del emulador, inyecta ARRIBA
del prompt el protocolo de verificación:

  - capturas continuas de la ventana DEL JUEGO — Vita3K abre dos ventanas
    (GUI y juego 960x544); por título se captura la equivocada
  - veredicto de imagen (% de píxel casi negro) y de movimiento (% de
    píxeles que cambian entre capturas): sin ambos, la corrida NO EXISTE
  - la ruta del harness que ya sabe hacer todo esto (vita3k_ctl.py; se
    localiza solo buscando tools/vita3k_ctl.py hacia arriba)
  - los DOS contadores de FPS que existen y no se pueden mezclar: el del
    título de la ventana mide la APP Vita; el show_fps dibujado sobre el
    juego mide el ROM Saturn (regla R11 de la bitácora). Un informe que
    cite «60 FPS» sin decir cuál de los dos es, no describe nada.
  - el formato de veredicto exigido: imagen + movimiento + ambos FPS +
    errores del log.

QUÉ NO HACE
===========
No ejecuta el harness ni valida las capturas: eso es del agente con sus
herramientas (python_exec). Señala el protocolo y deja constancia de que
señaló, para que «corrí el bench y traje FPS» sin imagen vuelva a ser
visible.
"""
from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path

__all__ = ["pertinente", "para_el_prompt", "harness", "HARNESS_NOMBRE"]

HARNESS_NOMBRE = "vita3k_ctl.py"

#: Un encargo es una corrida del emulador si habla de medir/correr Y de
#: emulador/juego. Las dos condiciones: «optimiza el emulador» (sin corrida)
#: no necesita este protocolo, y «mide la latencia del GUI» (sin emulador)
#: tampoco.
_RE_CORRIDA = re.compile(
    r"\b(corrida|correr|ejecutar|medir|medicion|medicion de|benchmark|bench|"
    r"ronda|captura|fps|probar|prueba|verificar)\w*\b")
_RE_EMULADOR = re.compile(
    r"\b(yabause|yabausevita|saturn|vita3k|vita|emulador|emulacion|"
    r"sonic|panzer|nights)\w*\b")


def _plano(s: str) -> str:
    sin = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in sin if not unicodedata.combining(c))


def pertinente(encargo: str) -> bool:
    """¿Este encargo exige una corrida con ojos?"""
    t = _plano(encargo)
    return bool(_RE_CORRIDA.search(t) and _RE_EMULADOR.search(t))


def harness(inicio: str | os.PathLike | None = None) -> Path | None:
    """Dónde está vita3k_ctl.py: se busca hacia arriba, como la bitácora.

    La variable de entorno gana por la misma razón que en bitácora.localizar:
    es la única forma de que una prueba apunte a un sitio de mentira.
    """
    env = os.environ.get("MAGI_HARNESS_VITA3K")
    if env and Path(env).is_file():
        return Path(env)

    base = Path(inicio or os.getcwd()).resolve()
    for carpeta in (base, *base.parents):
        cand = carpeta / "tools" / HARNESS_NOMBRE
        if cand.is_file():
            return cand
    return None


def para_el_prompt(encargo: str, inicio: str | os.PathLike | None = None) -> str:
    """El protocolo de verificación, inyectado arriba. Vacío si no aplica."""
    if not pertinente(encargo):
        return ""

    ruta = harness(inicio)
    donde = f"`{ruta}`" if ruta else (
        "`tools/vita3k_ctl.py` del repositorio del emulador "
        "(no se localizó desde aquí; búscalo antes de correr nada)")

    return (

        "\n\n---\n**PROTOCOLO DE CORRIDA VERIFICADA (R9 — la bitácora):**\n"
        "Una corrida sin verificación de imagen y movimiento NO es evidencia: "
        "el 30-ago-2026 el emulador reportó 59,9 FPS estables durante media "
        "hora con la pantalla negra. Antes de traer cualquier número:\n"
        f"1. Ejecuta la corrida con el harness {donde}, que lanza Vita3K sin "
        "elevar, arranca el emulador por sí solo (autostart) y toma capturas "
        "continuas de la ventana DEL JUEGO — Vita3K abre dos ventanas y la "
        "del juego es la de cliente 960x544.\n"
        "2. Exige los cuatro: `has_image` (negro < 90 %), `has_motion` "
        "(diff > 0,5 %), los DOS contadores de FPS y los errores del log. "
        "El FPS del título de Vita3K mide la app; el `show_fps` dibujado "
        "sobre el juego mide el ROM. Cítalos por separado o no cites ninguno.\n"
        "3. Sin imagen en movimiento, el resultado se reporta como "
        "«corrida inválida: sin ojos», aunque el log traiga números "
        "perfectos.\n"
        "3b. **Y el sonido (R16).** Llama a `listen_audio` mientras el juego "
        "corre y trae `has_sound` y `choppy`. El log no ve el audio: en "
        "YabauseVita `scsp_th` quema los mismos 1,1-1,4 s por ventana tanto "
        "si el sonido sale limpio como si sale a trompicones. Si "
        "`audio_available` dice que no hay oídos en esta máquina, el "
        "veredicto de audio es **SIN COMPROBAR**, que no es «no suena»: "
        "declararlo así es obligatorio, inventarlo es peor que omitirlo.\n"
        "4. Las propuestas de optimización llegan por las tres filosofías "
        "ortogonales de la bitácora (§2: hacer menos → composite, mover "
        "menos → upload, repartir mejor → dropped), cada una con su "
        "predicción falsable. La corrida verificada es la que adjudica: "
        "sin sus cuatro campos, ninguna propuesta gana ni pierde.\n"
    )
