"""
Los oídos, enchufados al enjambre.

Sin este registro, `magi/modules/percepcion/` sería andamiaje: código correcto
que ningún agente puede invocar. Es el fallo número 1 de este repositorio y ya
se pagó tres veces —`bitacora.py`, `controles.json`, y las herramientas de
ingeniería inversa antes que ellos—, así que el enganche va con el módulo, no
después.

Quién las necesita: **Balthasar**. Su trabajo es refutar con evidencia, y
«el audio no sale» es una refutación que no se puede hacer leyendo el log.
"""
from __future__ import annotations

import logging

from ...core.tools.registry import ToolRegistry, ToolResult

logger = logging.getLogger(__name__)

#: Tope duro. Escuchar es bloqueante; un agente que pida 10 minutos de captura
#: cuelga el turno del enjambre entero.
MAX_SEGUNDOS = 120


def register_percepcion_tools(reg: ToolRegistry) -> ToolRegistry:
    """Añade los oídos a un registro existente."""

    @reg.tool("listen_audio",
              "Escucha lo que suena en el sistema durante N segundos y "
              "dictamina si HAY sonido y si sale ENTERO o entrecortado. "
              "Úsala mientras un juego o artefacto corre: el log de CPU no "
              "distingue audio limpio de audio con cortes.",
              {"type": "object",
               "properties": {
                   "seconds": {"type": "number",
                               "description": "cuánto escuchar (1-120)"}},
               "required": ["seconds"]},
              access={"read"})
    def listen_audio(seconds: float, ctx=None):
        from .oidos import disponible, escuchar, motivo_no_disponible

        try:
            segs = float(seconds)
        except (TypeError, ValueError):
            return ToolResult(False, "", error="`seconds` no es un número")
        if not 1 <= segs <= MAX_SEGUNDOS:
            return ToolResult(
                False, "", error=f"`seconds` fuera de rango (1-{MAX_SEGUNDOS})")

        if not disponible():
            # No es un fallo del agente ni de la corrida: es una capacidad que
            # no está en esta máquina. Se dice, no se finge un veredicto.
            return ToolResult(
                False, "",
                error=(f"oídos no disponibles en este sistema "
                       f"({motivo_no_disponible()}). El veredicto de audio "
                       f"queda SIN COMPROBAR — que no es lo mismo que "
                       f"«no suena»."))

        v = escuchar(segs)
        if v.get("error"):
            return ToolResult(False, "", error=v["error"])

        estado = ("SIN SONIDO" if not v["has_sound"]
                  else "ENTRECORTADO" if v["choppy"] else "SONIDO CONTINUO")
        cuerpo = (
            "%s — sonando el %.1f%% del tiempo, %d corte(s) a silencio, "
            "RMS mediana %.5f sobre %d tramos de 100 ms."
            % (estado, v["sonando_pct"], v["cortes"], v["rms_mediana"],
               v["tramos"]))
        if v["choppy"]:
            cuerpo += (" Hay señal pero con caídas repetidas: mira underruns "
                       "del backend de audio antes que el mezclador.")
        return ToolResult(True, cuerpo, meta=v)

    @reg.tool("classify_screen",
              "Lee una captura de pantalla de un juego y dice QUÉ es: negro, "
              "carga, licencia, menú, título o partida; en qué idioma habla y "
              "qué botón está pidiendo. Úsala para saber dónde se quedó "
              "atascado un juego en vez de describir la captura a mano.",
              {"type": "object",
               "properties": {
                   "path": {"type": "string",
                            "description": "ruta de la imagen"},
                   "black_pct": {"type": "number",
                                 "description": "% de píxeles negros, del harness"},
                   "motion_pct": {"type": "number",
                                  "description": "% de cambio respecto a la anterior"},
                   "console": {"type": "string",
                               "description": "clave de consola en la memoria "
                                              "de mandos, p.ej. sega_saturn"}},
               "required": ["path"]},
              access={"read"})
    def classify_screen(path: str, black_pct: float = 0.0,
                        motion_pct: float = 0.0, console: str = "",
                        ctx=None):
        from pathlib import Path

        from .vista import clasificar, disponible, leer_texto

        p = ctx.resolve(path) if ctx else Path(path)
        if not p.is_file():
            return ToolResult(False, "", error=f"no existe: {p}")

        texto = ""
        if disponible():
            try:
                from PIL import Image
                with Image.open(p) as img:
                    texto = leer_texto(img)
            except Exception as e:      # pragma: no cover
                return ToolResult(False, "", error=f"no se pudo leer: {e}")

        botones = None
        if console:
            try:
                from ..swarm.memoria_persistente import cargar_controles
                ficha = (cargar_controles().get("consolas") or {}).get(console)
                botones = (ficha or {}).get("botones")
            except Exception:           # pragma: no cover
                botones = None

        pant = clasificar(black_pct, motion_pct, texto, botones)
        cuerpo = f"PANTALLA: {pant.clase} — {pant.razon}."
        if pant.idioma:
            cuerpo += f" Idioma: {pant.idioma} (confianza {pant.confianza_idioma:.2f})."
        if pant.botones:
            cuerpo += f" Pide: {', '.join(pant.botones)}."
        if not disponible():
            cuerpo += (" AVISO: sin OCR en esta máquina, así que idioma y "
                       "botones quedan SIN COMPROBAR — no es que no los haya.")
        return ToolResult(True, cuerpo,
                          meta={"clase": pant.clase, "razon": pant.razon,
                                "idioma": pant.idioma,
                                "confianza_idioma": pant.confianza_idioma,
                                "botones": pant.botones,
                                "texto": pant.texto[:400],
                                "ocr_disponible": disponible()})

    @reg.tool("audio_available",
              "Dice si esta máquina puede escuchar la salida de audio. "
              "Compruébalo ANTES de prometer un veredicto de sonido.",
              {"type": "object", "properties": {}}, access={"read"})
    def audio_available(ctx=None):
        from .oidos import disponible, motivo_no_disponible
        if disponible():
            return ToolResult(True, "Oídos disponibles (loopback WASAPI).",
                              meta={"available": True})
        return ToolResult(True,
                          f"Oídos NO disponibles: {motivo_no_disponible()}",
                          meta={"available": False})

    return reg
