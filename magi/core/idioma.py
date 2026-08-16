"""
Idioma de la respuesta: el del usuario, siempre.

EL FALLO
========
El usuario escribió «hola naoko» y Naoko respondió:

    ¡Hola! 嗨~请问有什么可以帮你的吗😊

Los proveedores gratuitos de g4f son puertas a modelos con sesgos de idioma
distintos; algunos contestan en chino o en inglés a un saludo corto, porque el
prompt no les dice en qué idioma tienen que hablar y un «hola» da poca señal.

No es un detalle cosmético: una respuesta que el usuario no puede leer es una
respuesta que no existe. Y con proveedores gratuitos pasa lo bastante a menudo
como para que haya que defenderse por diseño en vez de confiar en el modelo.

LA DEFENSA
==========
Dos capas, como con el navegador:

1. INSTRUCCIÓN — se le dice al modelo, en su propio idioma, en qué idioma debe
   contestar. Barato y funciona casi siempre.
2. COMPROBACIÓN — se mira la respuesta. Si vino en otro alfabeto o en otro
   idioma, se pide de nuevo. Es la capa que convierte «casi siempre» en «se
   nota cuando falla».

La detección es deliberadamente simple: alfabetos y palabras vacías muy
frecuentes. No hace falta acertar el idioma exacto de un texto arbitrario,
solo responder a «¿esto está en el mismo idioma que la pregunta?», que es una
pregunta mucho más fácil.
"""
from __future__ import annotations

import re
import unicodedata
from collections import OrderedDict

__all__ = ["detectar", "nombre_de", "instruccion", "coincide", "NOMBRES",
           "ADMITIDOS", "PROHIBIDOS", "IDIOMA_FINAL", "admisible",
           "necesita_traduccion", "instruccion_de_traduccion"]

#: EN QUÉ IDIOMAS SE ACEPTA QUE CONTESTE UN PROVEEDOR.
#:
#: No es lo mismo que en qué idioma lo lee el usuario (ver `IDIOMA_FINAL`).
#: Estos cuatro se aceptan porque son legibles, porque se traducen bien y —lo
#: que de verdad importa— porque **rechazarlos sale caro**: hasta hoy, una
#: respuesta en inglés disparaba una regeneración completa en otra familia, con
#: su latencia y su riesgo de fallar otra vez. Traducirla cuesta una llamada
#: corta a un proveedor rápido y no puede devolver algo peor.
ADMITIDOS: tuple[str, ...] = ("es", "en", "pt", "it")

#: LO QUE NO SE ACEPTA NUNCA, PASE LO QUE PASE.
#:
#: El chino va nombrado y no por manía: es el caso MEDIDO. `Yqcloud` —durante
#: un tiempo el único candidato vivo de la familia `gpt`, la de MELCHIOR—
#: responde en chino a un prompt en español:
#:
#:     'di: funciona'  ->  '看起来你输入的内容里「funciona」是西班牙语…'
#:
#: Esa fue la causa raíz de que el enjambre entregara conclusiones ilegibles.
#: Aquí no hay traducción que valga: se descarta la respuesta y se reintenta.
#: Lo demás (japonés, coreano, ruso, árabe, francés, alemán…) tampoco está en
#: ADMITIDOS, así que también se reintenta; el chino además se registra por su
#: nombre para que el motivo salga en el log y no haya que deducirlo.
PROHIBIDOS: tuple[str, ...] = ("zh", "ja", "ko", "ru", "ar")

#: EL IDIOMA EN EL QUE EL USUARIO LEE. SIEMPRE. SIN EXCEPCIÓN.
#:
#: Los tres agentes pueden contestar en cualquiera de ADMITIDOS, pero lo que
#: llega a la interfaz —conclusiones del enjambre y TODO lo de Naoko— va en
#: español. Un sistema que a veces habla en otro idioma obliga al usuario a
#: traducir; y si tiene que traducir, la respuesta no está terminada.
IDIOMA_FINAL = "es"

NOMBRES = {
    "es": "español", "en": "English", "pt": "português", "fr": "français",
    "it": "italiano", "de": "Deutsch", "zh": "中文", "ja": "日本語",
    "ko": "한국어", "ru": "русский", "ar": "العربية",
}

# Palabras vacías muy frecuentes. Cortas a propósito: se buscan como palabra
# entera, así que no hay falsos positivos por subcadena.
_PISTAS = {
    "es": {"el", "la", "los", "las", "de", "que", "por", "para", "como",
           "con", "una", "un", "es", "está", "esto", "pero", "porque",
           "hola", "qué", "cómo", "cuándo", "dónde", "gracias", "sí", "no"},
    "en": {"the", "of", "and", "to", "is", "are", "this", "that", "with",
           "for", "how", "what", "why", "hello", "hi", "thanks", "please",
           # Pronombres y auxiliares. Sin ellos, una frase corta en inglés
           # ("I will build it now") no deja NINGUNA palabra vacía reconocida
           # y `detectar` caía al por defecto (español): la respuesta pasaba
           # por válida y la guarda de idioma no rotaba nunca. Estas palabras
           # no aparecen en las listas de las otras lenguas latinas, así que
           # añadirlas no crea falsos positivos en francés/italiano/etc.
           #
           # `i` se excluye a propósito: es LA variable de bucle por defecto
           # en Python (`for i in range(...)`) y aparece en casi todo snippet.
           # Como pronombre inglés va en mayúscula ("I") y la distinción se
           # pierde al normalizar a minúscula; su valor discriminante no
           # compensa los falsos positivos sobre código. `will`, `you`, `it`,
           # `would`, etc. sí son distintivos y no colisionan con reservadas.
           "you", "it", "we", "they", "my", "your", "will", "do",
           "does", "can", "could", "would", "should", "was", "were", "has",
           "have", "had", "did"},
    "pt": {"o", "a", "os", "as", "de", "que", "para", "com", "uma", "não",
           "está", "olá", "obrigado", "porque", "como"},
    "fr": {"le", "la", "les", "de", "que", "pour", "avec", "une", "est",
           "bonjour", "merci", "pourquoi", "comment"},
    "it": {"il", "lo", "la", "di", "che", "per", "con", "una", "è", "ciao",
           "grazie", "perché", "come"},
    "de": {"der", "die", "das", "und", "ist", "nicht", "mit", "für", "wie",
           "hallo", "danke", "warum"},
}

# Caché de traducciones. La traducción es determinista para un texto dado
# (temperature=0, prompt fijo), así que repetirla solo gasta cuota gratuita
# y añade latencia. Vida del proceso, LRU acotado: lo que se repite en una
# sesión (reintentos, resíntesis con el mismo contenido) sale al instante.
_CACHE_TRADUCCIONES: OrderedDict[str, str] = OrderedDict()
_CACHE_TRADUCCIONES_MAX = 512


def traduccion_cacheada(texto: str) -> str | None:
    """La traducción registrada para este texto, o None."""
    t = _CACHE_TRADUCCIONES.get(texto)
    if t is not None:
        _CACHE_TRADUCCIONES.move_to_end(texto)
    return t


def recordar_traduccion(texto: str, traducido: str) -> None:
    """Anota una traducción válida para no repetir la llamada."""
    _CACHE_TRADUCCIONES[texto] = traducido
    _CACHE_TRADUCCIONES.move_to_end(texto)
    while len(_CACHE_TRADUCCIONES) > _CACHE_TRADUCCIONES_MAX:
        _CACHE_TRADUCCIONES.popitem(last=False)

# Rangos de alfabeto que identifican el idioma por sí solos.
_ALFABETOS = (
    ("zh", r"[一-鿿]"),
    ("ja", r"[぀-ヿ]"),
    ("ko", r"[가-힯]"),
    ("ru", r"[Ѐ-ӿ]"),
    ("ar", r"[؀-ۿ]"),
)

_PALABRA = re.compile(r"[^\W\d_]+", re.UNICODE)


def _normaliza(palabra: str) -> str:
    return palabra.lower()


def detectar(texto: str, por_defecto: str = "es") -> str:
    """
    Código de idioma del texto. `por_defecto` cuando no hay señal suficiente.

    Un «hola» suelto SÍ decide: es justo el caso en el que el modelo se
    despista, así que las pistas incluyen saludos.
    """
    if not texto or not texto.strip():
        return por_defecto

    # Un alfabeto no latino manda: no hay ambigüedad posible.
    for codigo, patron in _ALFABETOS:
        if len(re.findall(patron, texto)) >= 2:
            return codigo

    palabras = {_normaliza(p) for p in _PALABRA.findall(texto)}
    if not palabras:
        return por_defecto

    puntos = {c: len(palabras & pistas) for c, pistas in _PISTAS.items()}
    mejor = max(puntos, key=lambda c: puntos[c])
    if puntos[mejor] == 0:
        # Sin palabras vacías reconocidas: los acentos y la ñ siguen siendo
        # una señal débil pero real de lengua romance.
        if any(unicodedata.combining(c) for c in unicodedata.normalize("NFD", texto)):
            return por_defecto
        return por_defecto
    return mejor


def nombre_de(codigo: str) -> str:
    return NOMBRES.get(codigo, codigo)


def instruccion(codigo: str) -> str:
    """Línea que se añade al prompt del sistema. Va en el idioma pedido."""
    nombre = nombre_de(codigo)
    plantillas = {
        "es": f"Responde SIEMPRE en {nombre}, en todo el mensaje, sin mezclar "
              f"otros idiomas.",
        "en": f"Always answer in {nombre}, for the entire message, without "
              f"mixing other languages.",
        "pt": f"Responde SEMPRE em {nombre}, na mensagem inteira.",
        "fr": f"Réponds TOUJOURS en {nombre}, dans tout le message.",
        "it": f"Rispondi SEMPRE in {nombre}, in tutto il messaggio.",
        "de": f"Antworte IMMER auf {nombre}, in der gesamten Nachricht.",
    }
    return plantillas.get(codigo,
                          f"Always answer in {nombre}, for the entire message.")


def admisible(respuesta: str) -> tuple[bool, str]:
    """
    ¿Vale esta respuesta tal cual, o hay que volver a pedirla?

    Devuelve `(vale, código detectado)`. Vale si está en uno de `ADMITIDOS`.

    POR QUÉ ESTO SUSTITUYE A `coincide()` EN LA GUARDA
    ==================================================
    `coincide(respuesta, esperado)` preguntaba «¿está en EL idioma del
    usuario?». Con esa pregunta, una respuesta perfecta en inglés era un fallo
    y costaba una regeneración entera en otra familia — que además podía volver
    a fallar, o tardar 24 s, o no existir porque la familia estaba caída.

    La pregunta correcta es otra: «¿puedo *usar* esto?». Si está en español,
    inglés, portugués o italiano, sí: se traduce y listo. Si está en chino, no
    hay nada que hacer con ello y hay que volver a pedirlo.

    Un texto sin señal de idioma —un bloque de código, una URL, un número—
    devuelve el por defecto (`es`) y se acepta. Rechazarlo sería reintentar por
    no haber encontrado palabras vacías en un `for i in range(10)`.
    """
    if not respuesta or not respuesta.strip():
        return True, IDIOMA_FINAL
    codigo = detectar(respuesta, por_defecto=IDIOMA_FINAL)
    return codigo in ADMITIDOS, codigo


def necesita_traduccion(codigo: str) -> bool:
    """¿Hay que traducir esto antes de enseñárselo al usuario?"""
    return codigo != IDIOMA_FINAL


def instruccion_de_traduccion() -> str:
    """
    Prompt de sistema para traducir al español conservando el contenido.

    Las tres prohibiciones no son adorno: sin ellas, un modelo pequeño
    «mejora» el texto, resume las conclusiones y reformatea el código. Lo que
    se pide es un traductor, no un editor — si el enjambre concluyó algo, el
    usuario tiene que leer ESO, no una versión abreviada.
    """
    return (
        "Eres un traductor técnico. Traduce al español el mensaje del usuario.\n"
        "\n"
        "REGLAS:\n"
        "- Traduce TODO el texto, sin resumir, sin añadir y sin comentar.\n"
        "- NO traduzcas el contenido de los bloques de código, ni los nombres "
        "de variables, funciones, ficheros ni rutas.\n"
        "- Conserva exactamente el formato: saltos de línea, listas, tablas, "
        "marcadores y bloques ```.\n"
        "- Si ya está en español, devuélvelo tal cual, sin cambiar nada.\n"
        "- Responde ÚNICAMENTE con la traducción. Sin prefacio, sin "
        "«Aquí tienes la traducción», sin comillas alrededor."
    )


def coincide(respuesta: str, esperado: str) -> bool:
    """
    ¿Está la respuesta en el idioma esperado?

    Tolerante a propósito con las lenguas de alfabeto latino —un tecnicismo en
    inglés dentro de un texto en español no es un fallo—, e intransigente con
    el cambio de alfabeto, que es el caso que se vio y el que deja la respuesta
    ilegible.
    """
    if not respuesta or not respuesta.strip():
        return True

    esperado_es_latino = esperado not in {"zh", "ja", "ko", "ru", "ar"}
    for codigo, patron in _ALFABETOS:
        if codigo == esperado:
            continue
        # Unos pocos caracteres pueden ser una cita o un emoji descompuesto;
        # una frase entera en otro alfabeto no.
        if len(re.findall(patron, respuesta)) >= 4 and esperado_es_latino:
            return False

    if not esperado_es_latino:
        patron = dict(_ALFABETOS).get(esperado)
        if patron and len(re.findall(patron, respuesta)) < 2:
            return False
        return True

    detectado = detectar(respuesta, por_defecto=esperado)
    if detectado == esperado:
        return True

    # Entre lenguas latinas: una respuesta en otro idioma NO vale, por corta
    # que sea.
    #
    # La línea anterior era `return len(respuesta.split()) < 12`: una respuesta
    # corta se daba por buena SÍ O SÍ. Eso era justo el agujero por el que se
    # colaba el bug de la captura — "Sure! I will create a Tetris game for
    # you." (9 palabras) pasaba por español válido, así que la guarda de los
    # tres agentes y de Naoko nunca rotaba y el usuario veía "las 3 ia no me
    # hablan en español". El log mentía con "reintento en gemini acertó el
    # idioma" porque esa rama solo se activa cuando la respuesta ES larga.
    #
    # La excepción legítima es la respuesta SIN señal de ningún idioma: un
    # bloque de código, un número, una URL. Ahí `detectar` cae al por defecto
    # (que es el idioma del usuario) y no hay motivo para rechazar. Pero si la
    # detección encontró palabras vacías de OTRA lengua romance, la respuesta
    # está en ese idioma, no en el esperado, por corta que sea.
    palabras = {_normaliza(p) for p in _PALABRA.findall(respuesta)}
    if not palabras:
        return True  # sin texto evaluable: no es un fallo de idioma
    otras = {c: len(palabras & pistas) for c, pistas in _PISTAS.items()
             if c != esperado}
    # Una sola coincidencia aislada puede ser ruido: `for` e `in` son
    # reservadas de Python, `code` aparece en cualquier snippet. Una frase
    # de verdad en otro idioma deja dos o más palabras vacías, y eso sí es
    # señal inequívoca. Es el mismo principio que el `detectar` de alfabetos
    # (>= 2 caracteres): una ocurrencia suelta no decide.
    return max(otras.values()) < 2
