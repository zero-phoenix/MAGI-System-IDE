"""
Catálogo de diagnóstico de NAOKO: síntoma → causa → arreglo.

POR QUÉ ESTE MÓDULO EXISTE
==========================
El usuario preguntó «pedi al sistema crear un juego de tris pero no responde».
NAOKO tenía el estado del enjambre delante, contó bien las tareas… y contestó
con la excusa genérica que su propio prompt le prohibía («es común que se
produzcan fallos temporales…») y a continuación **se inventó una partida de
tres en raya**, con reglas y tablero.

El diagnóstico fácil es «mala redacción». Es falso. Pasaron dos cosas:

1. **Le dimos una premisa falsa.** `_get_swarm_status_summary()` decía
   literalmente «EN CURSO: task_6c0c00a9… Si se queja de demora, ESTO es la
   demora». Esas tareas llevaban muertas desde el día anterior. Con una
   premisa falsa, la explicación coherente también es falsa.
2. **No tenía nada verdadero que decir, y rellenó.** Un modelo al que se le
   pide diagnosticar sin darle con qué diagnosticar produce texto plausible.
   El tres en raya no fue un despiste: fue rellenar un hueco.

Ya intentamos arreglarlo con reglas en el prompt («REGLA DURA: los datos antes
que la empatía»). No bastó, y no podía bastar: el problema no era la
instrucción, era el material.

DE DÓNDE SALE LA FORMA
======================
Zcode Desktop trae cinco habilidades `diagnosing-*` (skills, mcp, hooks,
plugins, commands). La de skills tiene esta estructura:

  1. Orden de descubrimiento explícito, con precedencias
  2. Modelo de fallo en dos niveles: «no carga» vs «carga pero no se dispara»
  3. Doce fallos típicos, cada uno síntoma → causa → arreglo
  4. Flujo de localización ORDENADO, con instrucción de parar al encontrarlo

Y una frase que resume el principio entero:

  «Que una habilidad cargue y que se dispare son dos cosas distintas —
   distínguelas primero.»

LA REGLA
========
NAOKO **no contesta una pregunta operativa sin haber consultado este
catálogo**. Si un caso encaja, la respuesta se construye con datos del libro de
tareas y el modelo solo la redacta. Si ninguno encaja, dice que no lo sabe y
enseña lo que ve. Nunca inventa.
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Callable

logger = logging.getLogger(__name__)

VERSION = 1


@dataclass
class Situacion:
    """
    Lo que se sabe de verdad cuando alguien se queja.

    Todo son HECHOS leídos del sistema. Ni una sola opinión: si un campo no se
    pudo averiguar, va a None y el diagnóstico lo tiene en cuenta en vez de
    rellenarlo.
    """
    tareas: dict = field(default_factory=dict)
    vivas: set = field(default_factory=set)
    esperando_usuario: list = field(default_factory=list)
    interrumpidas: list = field(default_factory=list)
    en_curso_de_verdad: list = field(default_factory=list)
    zombis: list = field(default_factory=list)
    en_cola: int = 0
    entradas_perdidas: int = 0
    ultimas_entradas: list = field(default_factory=list)
    latencias: dict = field(default_factory=dict)
    familias_agotadas: list = field(default_factory=list)
    truncados: int = 0
    reintentos: int = 0

    @property
    def hay_alguna_tarea(self) -> bool:
        return bool(self.tareas)


@dataclass
class Caso:
    """Una entrada del catálogo."""
    id: str
    sintoma: str
    cuando: Callable[[str, Situacion], bool]
    causa: str
    arreglo: Callable[[Situacion], str]

    def aplica(self, pregunta: str, s: Situacion) -> bool:
        try:
            return bool(self.cuando(pregunta, s))
        except Exception:                              # pragma: no cover
            return False


# --------------------------------------------------- reconocer la queja
#
# Sin acentos y en minúsculas: el usuario escribe «demora», «demorá», «por que»
# y «porqué» indistintamente, y una respuesta correcta no puede depender de eso.

def _limpia(t: str) -> str:
    t = (t or "").lower()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"),
                 ("ñ", "n")):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t)


_NO_RESPONDE = ("no responde", "no contesta", "no me responde", "sin respuesta",
                "no pasa nada", "no hace nada", "no funciona", "no salio nada",
                "no aparece nada", "se quedo", "esta parado", "no me contesta")

_TARDA = ("tarda", "demora", "lento", "lenta", "se demora", "cuanto falta",
          "sigue pensando", "esta tardando")

_INCOHERENTE = ("no tiene sentido", "incoherente", "raro", "se corto",
                "esta cortado", "no entiendo la respuesta", "a medias")


def es_operativa(pregunta: str) -> bool:
    """
    ¿Es una pregunta sobre el propio sistema?

    Solo estas se contestan de forma determinista. Si el usuario pregunta de
    filosofía, NAOKO responde normal — este catálogo no se mete.
    """
    p = _limpia(pregunta)
    return any(f in p for f in _NO_RESPONDE + _TARDA + _INCOHERENTE)


def _quiere(claves):
    return lambda pregunta, s: any(f in _limpia(pregunta) for f in claves)


def _y(*fns):
    return lambda p, s: all(f(p, s) for f in fns)


def _lista(ids, n=3):
    ids = list(ids)
    return ", ".join(ids[:n]) + ("…" if len(ids) > n else "")


CATALOGO: tuple[Caso, ...] = (

    # 1. El caso que bloqueó esta instalación durante días.
    Caso(
        id="zombi",
        sintoma="«pregunté y no responde», y hay tareas que FIGURAN en curso "
                "sin bucle de ejecución vivo",
        cuando=_y(_quiere(_NO_RESPONDE), lambda p, s: bool(s.zombis)),
        causa="Una o más tareas quedaron a medias en una sesión anterior y "
              "volvieron a cargarse como «en curso» sin que nadie las "
              "ejecutara. Mientras figuren así, lo que escribes choca contra "
              "ellas.",
        arreglo=lambda s: (
            f"Tareas afectadas: {_lista(s.zombis)}. Se marcan como "
            f"interrumpidas y se retoman con tu último mensaje. No hace falta "
            f"que hagas nada."),
    ),

    # 2. No es un fallo: te toca a ti.
    Caso(
        id="espera_al_usuario",
        sintoma="«no responde», y hay tareas esperando tu visto bueno",
        cuando=_y(_quiere(_NO_RESPONDE),
                  lambda p, s: bool(s.esperando_usuario) and not s.zombis),
        causa="El enjambre YA terminó su trabajo y está esperando tu "
              "aprobación. No está atascado ni caído.",
        arreglo=lambda s: (
            f"Tareas en espera: {_lista(s.esperando_usuario)}. Escribe «sí» o "
            f"«apruebo» para cerrarlas, o pide un cambio concreto. Cualquier "
            f"otra cosa se toma como pregunta nueva."),
    ),

    # 3. Nunca llegó. Aquí es donde el sistema mentía antes.
    Caso(
        id="no_llego",
        sintoma="«pregunté y no responde», y NO hay ninguna tarea registrada",
        cuando=_y(_quiere(_NO_RESPONDE), lambda p, s: not s.hay_alguna_tarea),
        causa="Tu petición no llegó al enjambre. No es que vaya lenta: no "
              "existe.",
        arreglo=lambda s: (
            "Hay que mirar el libro de admisión, que registra toda entrada y "
            "por qué se descartó. Si tampoco aparece ahí, el fallo está entre "
            "la interfaz y el núcleo, no en los proveedores."),
    ),
)

CATALOGO = CATALOGO + (

    # 4. Se perdió por el camino: un ciclo del código que no cierra.
    Caso(
        id="entrada_perdida",
        sintoma="«no responde», y hay entradas admitidas que nadie resolvió",
        cuando=_y(_quiere(_NO_RESPONDE),
                  lambda p, s: s.entradas_perdidas > 0),
        causa="Tu mensaje se registró al entrar pero ningún camino del código "
              "lo cerró. Es un fallo del sistema, no de los proveedores.",
        arreglo=lambda s: (
            f"{s.entradas_perdidas} entrada(s) sin resolver. Se pueden "
            f"reenviar sin reescribirlas: están guardadas con su texto."),
    ),

    # 5. Está en cola, que ahora es un estado que existe.
    Caso(
        id="en_cola",
        sintoma="«no responde», y lo que escribiste está esperando turno",
        cuando=_y(_quiere(_NO_RESPONDE + _TARDA),
                  lambda p, s: s.en_cola > 0),
        causa="El enjambre estaba ocupado cuando escribiste, así que tu "
              "mensaje quedó en cola. Antes se descartaba en silencio; ahora "
              "espera turno.",
        arreglo=lambda s: (
            f"{s.en_cola} mensaje(s) en cola. Se atienden al cerrar la ronda "
            f"actual, en orden de llegada. No hay que reescribir nada."),
    ),

    # 6. Tarda de verdad, y se puede decir DÓNDE.
    Caso(
        id="demora_real",
        sintoma="«tarda mucho», y hay tareas realmente en ejecución",
        cuando=_y(_quiere(_TARDA), lambda p, s: bool(s.en_curso_de_verdad)),
        causa="Hay trabajo en curso de verdad (bucle vivo comprobado).",
        arreglo=lambda s: (
            f"En ejecución: {_lista(s.en_curso_de_verdad)}. "
            + (f"Latencias medidas por familia: "
               + ", ".join(f"{k} {v:.1f}s" for k, v in
                           sorted(s.latencias.items())[:4]) + ". "
               if s.latencias else "")
            + (f"Familias agotadas ahora mismo: "
               f"{', '.join(s.familias_agotadas)}. " if s.familias_agotadas
               else "")
            + "Se puede parar solo esta tarea sin tocar las demás."),
    ),
)

CATALOGO = CATALOGO + (

    # 7. Reintentos: la demora está en rotar proveedores, no en pensar.
    Caso(
        id="demora_por_reintentos",
        sintoma="«tarda mucho», y el número de reintentos es alto",
        cuando=_y(_quiere(_TARDA), lambda p, s: s.reintentos >= 3),
        causa="El tiempo se está yendo en reintentos contra proveedores que "
              "no contestan, no en generar la respuesta.",
        arreglo=lambda s: (
            f"{s.reintentos} reintentos en este turno. Los proveedores "
            f"condenados están listados con su motivo en Configuración; si "
            f"alguno ya funciona, se quita del catálogo sin recompilar."),
    ),

    # 8. Salida cortada: se le achacaba al modelo.
    Caso(
        id="truncado",
        sintoma="«la respuesta no tiene sentido» o «está a medias», y hay "
                "salidas marcadas como cortadas",
        cuando=_y(_quiere(_INCOHERENTE), lambda p, s: s.truncados > 0),
        causa="La salida se cortó por longitud. La incoherencia no es del "
              "modelo: le falta el final.",
        arreglo=lambda s: (
            f"{s.truncados} salida(s) truncada(s). Conviene reducir el "
            f"contexto o partir la petición. El tope está en Configuración."),
    ),
)


# Comprobación de integridad del catálogo: dos casos con el mismo id serían un
# fallo silencioso al buscar por id.
assert len({c.id for c in CATALOGO}) == len(CATALOGO), "ids duplicados"


@dataclass
class Diagnostico:
    caso: Caso | None
    texto: str
    seguro: bool

    def to_dict(self) -> dict:
        return {"caso": self.caso.id if self.caso else None,
                "texto": self.texto, "seguro": self.seguro,
                "version_catalogo": VERSION}


def _no_lo_se(s: Situacion) -> Diagnostico:
    """
    Cuando ningún caso encaja.

    Esto ES la respuesta correcta, no un fallo. Decir «no lo sé, esto es lo que
    veo» y enseñar los datos vale infinitamente más que un párrafo plausible.
    Un sistema de diagnóstico que improvisa sobre su propio estado da confianza
    falsa, que es peor que no tener diagnóstico.
    """
    partes = ["No sé decirte la causa con lo que veo. Esto es lo que hay:"]
    if s.en_curso_de_verdad:
        partes.append(f"- En ejecución ahora: {_lista(s.en_curso_de_verdad)}")
    if s.zombis:
        partes.append(f"- Figuran en curso pero sin bucle vivo: "
                      f"{_lista(s.zombis)}")
    if s.esperando_usuario:
        partes.append(f"- Esperando tu aprobación: "
                      f"{_lista(s.esperando_usuario)}")
    if s.interrumpidas:
        partes.append(f"- Interrumpidas (reanudables): "
                      f"{_lista(s.interrumpidas)}")
    if s.en_cola:
        partes.append(f"- En cola: {s.en_cola}")
    if not s.hay_alguna_tarea:
        partes.append("- Ninguna tarea registrada.")
    partes.append("Dime qué escribiste y a qué hora y lo busco en el libro "
                  "de admisión.")
    return Diagnostico(None, "\n".join(partes), seguro=False)


def diagnosticar(pregunta: str, s: Situacion) -> Diagnostico | None:
    """
    Devuelve una respuesta CONSTRUIDA CON DATOS, o None si la pregunta no es
    operativa.

    El orden del catálogo importa y se para en el primero que encaja — igual
    que el flujo de localización de Zcode, que dice explícitamente «para cuando
    encuentres la causa». Buscar más allá no aporta y multiplica las
    explicaciones, que es como se acaba diciendo tres cosas a la vez.
    """
    if not es_operativa(pregunta):
        return None

    for caso in CATALOGO:
        if caso.aplica(pregunta, s):
            texto = (f"{caso.causa}\n\n{caso.arreglo(s)}")
            logger.info("[diagnostico] caso=%s", caso.id)
            return Diagnostico(caso, texto, seguro=True)

    return _no_lo_se(s)


def catalogo_legible() -> str:
    """El catálogo para enseñarlo en Configuración. Es contenido, no magia."""
    filas = [f"Catálogo de diagnóstico v{VERSION} — {len(CATALOGO)} casos", ""]
    for c in CATALOGO:
        filas.append(f"[{c.id}]")
        filas.append(f"  síntoma: {c.sintoma}")
        filas.append(f"  causa:   {c.causa}")
    return "\n".join(filas)
