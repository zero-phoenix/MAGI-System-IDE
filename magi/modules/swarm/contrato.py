"""
El encargo como CONTRATO: qué prometí y cómo se comprueba (D1, D5).

POR QUÉ EXISTE
==============
«Un ping pong de 32 bits a todo color en un exe portable» no es un tema sobre
el que escribir: son cuatro compromisos separables, y cada uno se puede
comprobar. Cuando el sistema lo trata como un tema, escribe *sobre* el juego en
vez de entregar *el* juego — que es exactamente lo que midieron las pruebas del
16 al 20 de agosto.

Y hay un segundo fallo, más silencioso: **partes del enunciado que se pierden**.
La prueba D pedía explícitamente «el orden de trabajo que minimiza el riesgo de
abandono»; la respuesta, buena en lo demás, no mencionó el abandono ni una vez.
Nadie lo notó porque nadie llevaba la lista.

Esto lleva la lista.

QUÉ NO ES
=========
No es un analizador de lenguaje natural ni pretende serlo. Es una lista de
señales frecuentes y comprobables, con un objetivo modesto y medible: que
ninguna promesa explícita del enunciado salga de la conversación sin que
alguien la haya mirado. Cuando no está seguro, no inventa: no añade el
compromiso.
"""
from __future__ import annotations

import unicodedata

__all__ = ["compromisos", "sin_cubrir", "render"]


def _plano(s: str) -> str:
    sin = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in sin if not unicodedata.combining(c))


#: Señales -> (nombre del compromiso, cómo se comprueba). El texto de la
#: derecha se le enseña al usuario y viaja al prompt: un compromiso que no dice
#: cómo se comprueba es un deseo.
SENALES: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (("exe", ".exe", "ejecutable", "binario"),
     "entregar un ejecutable",
     "existe el fichero y su hash consta en el informe"),
    (("portable", "sin dependencias", "sin instalacion", "standalone"),
     "que sea portable",
     "no requiere instalar nada: se justifica la dependencia elegida"),
    (("unico", "un solo", "un unico", "onefile", "single"),
     "un único fichero",
     "un solo artefacto, no una carpeta"),
    (("16 bits", "32 bits", "24 bits", "8 bits", "rgb565", "rgba", "a todo color"),
     "el formato de color pedido",
     "el artefacto lo verifica solo (modo --formato o equivalente)"),
    (("juego", "jugable", "game"),
     "que sea jugable",
     "autoprueba que avanza la partida y sale con codigo 0"),
    (("test", "pruebas", "pytest", "unitarios"),
     "traer pruebas",
     "los tests se ejecutan y pasan"),
    (("riesgo", "abandono", "fracaso"),
     "hablar de los riesgos",
     "la respuesta los nombra explicitamente"),
    (("orden", "faseado", "fases", "roadmap", "plan de trabajo"),
     "dar un orden de trabajo",
     "la respuesta lista las fases en secuencia"),
    (("valida", "validar", "verificar", "comprobar", "diferencial"),
     "decir como se valida",
     "la respuesta describe el oraculo de cada etapa"),
    (("justifica", "por que", "razona", "explica por que"),
     "justificar las decisiones",
     "cada eleccion viene con su motivo"),
)


def compromisos(texto: str) -> list[dict]:
    """
    Los compromisos comprobables que contiene el encargo.

    Se devuelven en el orden en que aparecen las señales, que suele ser el
    orden en que el usuario los tiene en la cabeza.
    """
    t = _plano(texto)
    if not t.strip():
        return []
    fuera: list[dict] = []
    for claves, nombre, comprobacion in SENALES:
        pos = min((t.find(k) for k in claves if k in t), default=-1)
        if pos >= 0:
            fuera.append({"que": nombre, "como": comprobacion, "pos": pos})
    fuera.sort(key=lambda c: c["pos"])
    for c in fuera:
        c.pop("pos", None)
    return fuera


#: Palabras que delatan que un compromiso se ha tocado en la respuesta. Se
#: buscan sobre el texto entregado, no sobre el debate interno: lo que no llega
#: al usuario no cuenta como contestado.
_HUELLAS = {
    "entregar un ejecutable": ("exe", "ejecutable", "binario", "artefacto"),
    "que sea portable": ("portable", "dependencia", "standalone", "sin instalar"),
    "un único fichero": ("onefile", "un solo fichero", "unico fichero", "un fichero"),
    "el formato de color pedido": ("bits", "rgb", "rgba", "color", "paleta"),
    "que sea jugable": ("jugab", "partida", "controles", "autoprueba", "fps"),
    "traer pruebas": ("test", "prueba", "pytest", "verifica"),
    "hablar de los riesgos": ("riesgo", "abandono", "fracas", "peligro"),
    "dar un orden de trabajo": ("fase", "orden", "paso", "etapa", "roadmap"),
    "decir como se valida": ("valida", "verifica", "oracul", "diferencial", "test"),
    "justificar las decisiones": ("porque", "por que", "motivo", "razon", "justific"),
}


def sin_cubrir(respuesta: str, lista: list[dict]) -> list[str]:
    """
    Qué compromisos NO aparecen en lo entregado.

    Deliberadamente tolerante: basta una huella para darlo por tocado. El
    objetivo no es puntuar la respuesta, es que no se pierda una promesa
    entera sin que nadie lo note — que es lo que pasó con «minimiza el riesgo
    de abandono».
    """
    t = _plano(respuesta)
    faltan = []
    for c in lista:
        huellas = _HUELLAS.get(c["que"], ())
        if huellas and not any(h in t for h in huellas):
            faltan.append(c["que"])
    return faltan


def render(lista: list[dict]) -> str:
    """Una línea por compromiso, para enseñárselo al usuario al empezar."""
    if not lista:
        return ""
    filas = "\n".join(f"  · {c['que']} — se comprueba: {c['como']}"
                      for c in lista)
    return ("[CONTRATO] Así he entendido lo que pides, y así lo voy a "
            f"comprobar:\n{filas}")


def para_el_prompt(lista: list[dict]) -> str:
    """El contrato, redactado para que el agente no pueda decir que no lo vio."""
    if not lista:
        return ""
    filas = "\n".join(f"- {c['que']} (comprobación: {c['como']})" for c in lista)
    return ("\n\nCONTRATO DEL ENCARGO — cada punto es una promesa que hay que "
            f"cumplir y que se va a comprobar:\n{filas}\n"
            "Si alguno no se puede cumplir, dilo explícitamente en la "
            "respuesta en vez de omitirlo.")

# Excepción a la regla de no re-exportar: `para_el_prompt` viaja al agente y
# `render` al usuario. Son dos públicos distintos y por eso son dos funciones.
__all__.append("para_el_prompt")
