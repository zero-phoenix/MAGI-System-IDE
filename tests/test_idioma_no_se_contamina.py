"""
El idioma lo decide lo que TÚ escribiste. Nada más.

EL BUCLE QUE ESTO ROMPE
=======================
El usuario escribía en español y las tres IA le contestaban en chino. La guarda
de idioma existía, estaba en los dos caminos, tenía tope de reintentos… y el
log decía que funcionaba:

    [MELCHIOR] reintento en gemini acertó el idioma

Acertaba. El idioma equivocado.

El idioma esperado se deducía con `idioma.detectar(user_prompt)`, y
`user_prompt` NO es lo que escribió el usuario: a partir de la ronda 2 lleva
pegada la memoria del debate —lo que dijeron Melchior, Balthasar y Casper
antes—. Así que:

    ronda 1  un proveedor gratuito responde en chino y se cuela
    ronda 2  el prompt contiene ese chino -> detectar() dice «zh»
             -> la guarda EXIGE chino
             -> rota de familia hasta encontrar una que responda en chino
             -> lo registra como éxito

De protección a causa. Y no se sale escribiendo más veces en español, porque
cada ronda hereda la contaminación de la anterior: es un bucle que se
realimenta solo.

Lo instructivo es que **cada pieza por separado era correcta**. La detección
funciona, la comparación funciona, la rotación funciona. Lo que estaba mal era
de dónde salía el dato de entrada — y eso ningún test de las piezas lo ve.
"""
from __future__ import annotations

import pytest

from magi.core import idioma
from magi.modules.swarm.agents import BalthasarAgent, MelchiorAgent

CHINO = "结论：方案 B 最稳固。其代码逻辑简单且无参数矛盾；三种方案均未涉及网络。"
ESPANOL = "La propuesta B es la más sólida porque su lógica no tiene contradicciones."


def _agente(clase=MelchiorAgent):
    a = clase.__new__(clase)          # sin __init__: no queremos red ni bus
    a.lang_usuario = None
    return a


# ------------------------------------------------- la contaminación, aislada

def test_el_prompt_contaminado_engaña_a_la_deteccion():
    """
    Primero: que quede fijado el mecanismo del fallo, no solo el arreglo.

    Un prompt de ronda 2 = petición del usuario en español + memoria del debate
    con chino dentro. Detectar sobre eso da «zh», y esa es toda la avería.
    """
    prompt_ronda_2 = f"Ronda 2. Requerimiento: crea un juego de tetris\n\n{CHINO}"
    assert idioma.detectar("crea un juego de tetris portable") == "es"
    assert idioma.detectar(prompt_ronda_2) != "es", (
        "si esto deja de ser cierto, el detector ha cambiado y este test ya no "
        "reproduce el fallo que motivó el arreglo")


def test_con_el_idioma_fijado_el_prompt_contaminado_da_igual():
    """El arreglo: `lang_usuario` manda sobre cualquier cosa que traiga el prompt."""
    a = _agente()
    a.lang_usuario = "es"
    prompt_ronda_2 = f"Ronda 2. Requerimiento: crea un juego de tetris\n\n{CHINO}"
    assert a._idioma(prompt_ronda_2) == "es", (
        "el idioma del usuario no puede depender de lo que respondieran los "
        "agentes en rondas anteriores")


def test_sin_idioma_fijado_se_deduce_del_prompt():
    """
    El respaldo sigue existiendo para llamadas sueltas (tests, herramientas).

    Se comprueba porque es la diferencia entre «arreglado» y «roto de otra
    forma»: quitar el respaldo dejaría sin idioma a todo lo que no pase por el
    orquestador.
    """
    a = _agente()
    assert a.lang_usuario is None
    assert a._idioma("crea un juego de tetris portable") == "es"


@pytest.mark.parametrize("clase", [MelchiorAgent, BalthasarAgent])
def test_los_tres_nodos_comparten_el_mecanismo(clase):
    a = _agente(clase)
    a.lang_usuario = "es"
    assert a._idioma(CHINO) == "es"


# --------------------------------------------- y la guarda hace su trabajo

def test_una_respuesta_en_chino_no_pasa_por_espanol():
    """
    Con el idioma correcto, `coincide` rechaza el chino. Es la otra mitad: de
    nada sirve saber el idioma si la comparación lo da por bueno.
    """
    assert idioma.coincide(ESPANOL, "es") is True
    assert idioma.coincide(CHINO, "es") is False


def test_una_respuesta_corta_en_ingles_tampoco_pasa():
    """
    El caso concreto de la captura anterior: «Sure! I will create a Tetris game
    for you.» — nueve palabras, y durante una versión entera pasó por español
    válido porque las respuestas cortas se daban por buenas sin mirar.
    """
    assert idioma.coincide("Sure! I will create a Tetris game for you.", "es") is False
