"""
Vista: leer la pantalla como la lee una persona (R17).

QUÉ FALTABA
===========
R9 dio ojos: `has_image` y `has_motion` responden «¿hay algo y se mueve?».
R16 dio oídos. Pero ninguno de los dos sabe **qué** está pasando:

  - «NiGHTS no llega al título» hubo que averiguarlo mirando una captura a
    mano y describiéndola. Eso no se repite ni escala.
  - «va lento» sin decir *dónde* no sirve: Panzer corre a 59,8 FPS y NiGHTS a
    40, pero el número que importa es por PANTALLA — el menú a 60 y la
    partida a 17 es un diagnóstico; la media de ambos, 38, no es nada.
  - un agente que quiera **jugar** necesita saber qué botón le pide la
    pantalla, y en qué idioma se lo pide.

QUÉ HACE
========
Cuatro cosas, todas sobre una imagen ya capturada:

  `leer_texto`      OCR de la pantalla (Tesseract).
  `idioma`          en qué idioma habla el juego, con confianza.
  `botones_pedidos` qué botón pide la pantalla ("PRESS START" → `start`),
                    validado contra la memoria de mandos de esa consola.
  `clasificar`      en qué clase de pantalla estamos: negro, carga, licencia,
                    menú, título o partida.

Y un libro mayor, `Zonas`, que acumula FPS por clase de pantalla. Eso es
«juzgar en qué zonas va lento» con un número por zona, no una impresión.

QUÉ NO HACE
===========
No captura: recibe imágenes. Igual que el veredicto de los oídos vive
separado de la tarjeta de sonido, esto vive separado de la ventana — así se
prueba con imágenes sintéticas, sin emulador y sin Windows.

No juega solo. Decir qué botón pide la pantalla y saber cuál es en el mando
es la mitad; pulsarlo en el momento correcto y entender si eso *avanzó* el
juego es la otra, y esa necesita un lazo de decisión que aquí no está.
"""
from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

__all__ = ["disponible", "leer_texto", "idioma", "botones_pedidos",
           "clasificar", "Zonas", "Pantalla"]


def _ocr():
    """Backend a demanda: media CI corre en Linux sin Tesseract."""
    try:
        import pytesseract
        from PIL import Image  # noqa: F401
        return pytesseract, ""
    except Exception as e:      # pragma: no cover - depende del sistema
        return None, str(e)


def disponible() -> bool:
    t, _ = _ocr()
    if t is None:
        return False
    try:
        t.get_tesseract_version()
        return True
    except Exception:           # pragma: no cover
        return False


def leer_texto(imagen) -> str:
    """OCR. Cadena vacía si no hay backend: «no pude leer» se distingue de
    «no había texto» por `disponible()`, no inventando un resultado."""
    t, _ = _ocr()
    if t is None:
        return ""
    try:
        return t.image_to_string(imagen, lang="eng+spa")
    except Exception:           # pragma: no cover
        return ""


# --------------------------------------------------------------- idioma

#: Palabras función: las que aparecen en cualquier frase del idioma y casi
#: nunca en otro. Se usan estas y no un modelo porque el texto de un juego
#: son cuatro palabras en mayúsculas con OCR sucio — un clasificador
#: entrenado con prosa se equivoca más aquí que una lista corta.
_FUNCION = {
    "es": ("el", "la", "los", "las", "de", "que", "para", "con", "pulsa",
           "juego", "opciones", "salir", "continuar", "empezar", "nuevo"),
    "en": ("the", "of", "and", "to", "press", "start", "game", "options",
           "exit", "continue", "new", "select"),
    "fr": ("le", "la", "les", "des", "pour", "appuyez", "jeu", "quitter"),
    "de": ("der", "die", "das", "und", "drücken", "spiel", "beenden"),
    "it": ("il", "lo", "gli", "per", "premi", "gioco", "esci"),
    "pt": ("o", "os", "para", "com", "pressione", "jogo", "sair"),
}

#: Rangos de escritura japonesa. El japonés no se detecta por palabras: se
#: detecta porque hay kana. Un solo carácter basta y no hay falso positivo
#: posible desde un alfabeto latino.
_KANA = (("぀", "ゟ"), ("゠", "ヿ"))
_KANJI = (("一", "鿿"),)


def _en_rango(c: str, rangos) -> bool:
    return any(a <= c <= b for a, b in rangos)


def _plano(s: str) -> str:
    sin = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in sin if not unicodedata.combining(c))


def idioma(texto: str) -> tuple[str, float]:
    """
    Devuelve `(codigo, confianza)`. Confianza 0 significa «no sé», y hay que
    decirlo: adivinar el idioma de tres letras de OCR sucio y presentarlo
    como dato es exactamente lo que R9 prohíbe del lado de la imagen.
    """
    if not texto or not texto.strip():
        return ("", 0.0)

    kana = sum(1 for c in texto if _en_rango(c, _KANA))
    if kana:
        return ("ja", min(1.0, 0.6 + kana / 20))
    kanji = sum(1 for c in texto if _en_rango(c, _KANJI))
    if kanji >= 2:
        return ("ja", min(1.0, 0.5 + kanji / 20))

    palabras = re.findall(r"[a-záéíóúüñ]+", _plano(texto))
    if not palabras:
        return ("", 0.0)
    conjunto = set(palabras)
    puntos = {k: len(conjunto & set(v)) for k, v in _FUNCION.items()}
    mejor = max(puntos, key=lambda k: puntos[k])
    if puntos[mejor] == 0:
        return ("", 0.0)
    segundo = sorted(puntos.values())[-2] if len(puntos) > 1 else 0
    # La confianza mide la DISTANCIA al segundo candidato, no los aciertos:
    # "START" acierta en inglés y en nada más, pero un empate a uno entre dos
    # idiomas no es una detección, es una moneda al aire.
    ventaja = puntos[mejor] - segundo
    return (mejor, min(1.0, 0.35 + 0.2 * ventaja + 0.05 * puntos[mejor]))


# -------------------------------------------------------------- botones

_VERBOS = ("press", "push", "hit", "pulsa", "presiona", "aprieta",
           "appuyez", "premi", "drucke", "drücke")

#: Cómo pide un juego que pulses algo. Dos patrones y no uno porque el OCR
#: real pega las palabras: «PULSA START PARA JUGAR» se leyó literalmente
#: `PULSASTARTPARA JUGAR` en la primera prueba con Tesseract. Un patrón con
#: `\b` detrás del verbo no encuentra nada ahí, y ese es el caso normal, no
#: el raro.
_PIDE = re.compile(
    r"\b(?:" + "|".join(_VERBOS) + r")\b[\s:]*([A-Za-z0-9]{1,6})",
    re.IGNORECASE)
_PIDE_PEGADO = re.compile(
    r"(?:" + "|".join(_VERBOS) + r")([A-Za-z0-9]{1,10})",
    re.IGNORECASE)

#: Sinónimos de pantalla → nombre canónico del botón en la memoria de mandos.
_ALIAS = {
    "start": "start", "run": "start", "enter": "start",
    "select": "select",
    "a": "A", "b": "B", "c": "C", "x": "X", "y": "Y", "z": "Z",
    "l": "L", "r": "R",
    "any": "start",         # «press any button» → el más seguro
    "button": "start",
}


def botones_pedidos(texto: str, botones_consola: list[str] | None = None
                    ) -> list[str]:
    """
    Qué botón pide la pantalla, validado contra el mando de ESA consola.

    La validación importa: si la pantalla dice «PRESS X» y la consola no
    tiene X (el Saturn no lo tiene en la fila de abajo), es OCR sucio o es
    otra consola, y devolverlo sin comprobar mandaría al agente a pulsar una
    tecla que no existe.
    """
    fuera: list[str] = []

    def anotar(canon: str | None) -> None:
        if canon is None:
            return
        if botones_consola and canon not in botones_consola:
            return
        if canon not in fuera:
            fuera.append(canon)

    t = texto or ""
    for bruto in _PIDE.findall(t):
        anotar(_ALIAS.get(bruto.lower()))

    # Segunda pasada para el texto pegado. Del bloque que sigue al verbo se
    # prueba el prefijo más largo que sea un alias conocido: en
    # `PULSASTARTPARA`, "startpara" no es nada pero "start" sí.
    for bloque in _PIDE_PEGADO.findall(t):
        b = bloque.lower()
        for largo in range(min(len(b), 6), 0, -1):
            canon = _ALIAS.get(b[:largo])
            if canon is not None:
                anotar(canon)
                break
    return fuera


# ------------------------------------------------------------- pantalla

@dataclass
class Pantalla:
    clase: str                    # negro|carga|licencia|menu|titulo|partida
    razon: str                    # por qué se clasificó así
    texto: str = ""
    idioma: str = ""
    confianza_idioma: float = 0.0
    botones: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.clase} ({self.razon})"


_LEGAL = ("licensed", "licencia", "trademark", "all rights", "reservados",
          "sega enterprises", "produced by", "under license")
_CARGA = ("loading", "cargando", "now loading", "please wait", "espere")


def clasificar(negro_pct: float, movimiento_pct: float, texto: str = "",
               botones_consola: list[str] | None = None) -> Pantalla:
    """
    En qué clase de pantalla estamos.

    El orden de las reglas es el diagnóstico: se descarta primero lo que hace
    inútil a todo lo demás. Una pantalla negra no tiene idioma ni botones que
    leer, y preguntárselo produce ruido con pinta de dato.
    """
    lang, conf = idioma(texto)
    bot = botones_pedidos(texto, botones_consola)
    plano = _plano(texto)

    if negro_pct >= 97.0:
        return Pantalla("negro", f"{negro_pct:.1f}% de pixeles negros")
    if any(p in plano for p in _CARGA):
        return Pantalla("carga", "texto de carga en pantalla", texto, lang,
                        conf, bot)
    if any(p in plano for p in _LEGAL):
        return Pantalla("licencia", "aviso legal en pantalla", texto, lang,
                        conf, bot)
    if bot and movimiento_pct < 3.0:
        return Pantalla("titulo", f"pide {bot[0]} y apenas se mueve", texto,
                        lang, conf, bot)
    if movimiento_pct >= 3.0:
        return Pantalla("partida", f"{movimiento_pct:.1f}% de movimiento",
                        texto, lang, conf, bot)
    if len(plano.split()) >= 6:
        return Pantalla("menu", "mucho texto y poco movimiento", texto, lang,
                        conf, bot)
    return Pantalla("desconocida", "ni texto ni movimiento suficientes", texto,
                    lang, conf, bot)


# ----------------------------------------------------------------- zonas

class Zonas:
    """
    FPS por clase de pantalla. «Va lento» sin decir dónde no es diagnóstico.

    La media global miente por construcción: un juego que va a 60 en el menú
    y a 17 en la partida tiene una media de 38, y 38 no ocurre nunca.
    """

    def __init__(self):
        self._m: dict[str, list[float]] = defaultdict(list)

    def registrar(self, clase: str, fps: float) -> None:
        if fps is not None and fps > 0:
            self._m[clase].append(float(fps))

    @property
    def clases(self) -> list[str]:
        return sorted(self._m)

    def mediana(self, clase: str) -> float | None:
        v = sorted(self._m.get(clase, []))
        return v[len(v) // 2] if v else None

    def informe(self) -> dict[str, Any]:
        por_clase = {c: {"muestras": len(self._m[c]),
                         "fps_mediana": self.mediana(c),
                         "fps_min": min(self._m[c]),
                         "fps_max": max(self._m[c])}
                     for c in self.clases}
        jugables = {c: d for c, d in por_clase.items()
                    if c in ("partida", "titulo", "menu")}
        peor = min(jugables, key=lambda c: jugables[c]["fps_mediana"],
                   default=None)
        return {
            "por_clase": por_clase,
            "zona_mas_lenta": peor,
            "fps_zona_mas_lenta": jugables[peor]["fps_mediana"] if peor else None,
            # Se declara explícitamente para que nadie lo cite como si fuera
            # un rendimiento real observable.
            "aviso": ("la media entre clases no describe ninguna pantalla; "
                      "compara siempre la misma clase entre corridas"),
        }
