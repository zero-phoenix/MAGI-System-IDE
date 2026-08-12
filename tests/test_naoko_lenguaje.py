"""
Naoko habla de tus conversaciones, no de filas de una base de datos.

LO QUE DECÍA
============
    Hay 2 tareas bloqueadas esperando por ti (WAITING_USER_APPROVAL):
    task_29ceb5d6 (ronda 2), task_c95b7d00 (ronda 2)
    Hay 4 tareas en estado interrumpido (task_50f418e5, task_6c0c00a9, …)

Exacto, y no se puede accionar. `task_29ceb5d6` no le dice nada a nadie —las
conversaciones ya tienen título generado—, `WAITING_USER_APPROVAL` es un nombre
de la máquina de estados, y la lista no dice qué hacer con nada de eso.

Además iba todo mezclado: lo que espera al usuario junto a lo que sigue solo,
cuando solo una de las dos cosas le toca a él.

LO QUE NO CAMBIA
================
El detalle técnico se conserva entero en el contexto de Naoko —identificadores,
estados internos, quién tiene bucle vivo—, porque sin eso no puede
diagnosticar. Lo que cambia es lo que le pone delante al usuario. Se pliega, no
se borra.
"""
from __future__ import annotations

import pytest

from magi.modules.infrastructure.naoko_lenguaje import (
    en_cristiano, nombre_de_tarea, que_te_toca, resumen_humano,
)


# ---------------------------------------------------------------- el nombre

def test_usa_el_titulo_que_ya_existe():
    assert nombre_de_tarea("task_29ceb5d6",
                           {"titulo": "Juego Tetris portable"}) == \
        "Juego Tetris portable"


def test_sin_titulo_usa_el_enunciado_recortado():
    n = nombre_de_tarea("task_1", {"command": "crea un juego de tetris en un "
                                              "solo ejecutable portable exe"})
    assert n.startswith("«crea un juego de tetris")
    assert n.endswith("…»") or n.endswith("»")
    assert len(n) <= 52


def test_el_identificador_es_el_ultimo_recurso_y_no_el_primero():
    """
    Antes era el único. Sigue estando para no quedarse sin nada que decir, pero
    solo cuando de verdad no hay nada mejor.
    """
    assert nombre_de_tarea("task_29ceb5d6", {}) == "task_29ceb5d6"
    assert nombre_de_tarea("task_29ceb5d6", {"titulo": "", "command": ""}) == \
        "task_29ceb5d6"


def test_un_titulo_de_tres_lineas_deja_de_ser_un_titulo():
    n = nombre_de_tarea("t", {"command": "línea uno\nlínea dos\nlínea tres " * 5})
    assert "\n" not in n and len(n) <= 52


# ------------------------------------------------------------- el estado

@pytest.mark.parametrize("interno,esperado", [
    ("WAITING_USER_APPROVAL", "esperando tu visto bueno"),
    ("interrumpida", "a medias, se retoma sola"),
    ("in_progress", "trabajando"),
])
def test_los_estados_se_dicen_en_lo_que_significan(interno, esperado):
    assert en_cristiano(interno) == esperado


def test_un_estado_desconocido_se_dice_tal_cual_y_no_se_inventa():
    """Traducir a ciegas un estado que no se conoce sería inventarse qué pasa."""
    assert en_cristiano("estado_futuro") == "estado_futuro"


def test_cada_estado_trae_lo_que_puedes_hacer():
    assert "sí" in que_te_toca("WAITING_USER_APPROVAL")
    assert que_te_toca("in_progress") == "", (
        "si no le toca al usuario, no se le pide nada: decirlo también informa")


# ------------------------------------------------------------- el resumen

def test_separa_lo_tuyo_de_lo_que_va_solo():
    """
    La mezcla era el fallo de fondo: había que deducir qué parte requería
    acción. Ahora son dos bloques y el primero es el tuyo.
    """
    texto = resumen_humano({
        "t1": {"status": "WAITING_USER_APPROVAL", "round": 2,
               "titulo": "Juego Tetris portable"},
        "t2": {"status": "interrumpida", "titulo": "Análisis del emulador"},
    })
    assert "Te toca a ti:" in texto
    assert "sin que tengas que hacer nada" in texto
    assert texto.index("Te toca a ti") < texto.index("sin que tengas")


def test_no_aparece_ningun_identificador_cuando_hay_titulo():
    """La comprobación que resume todo lo demás."""
    texto = resumen_humano({
        "task_29ceb5d6": {"status": "WAITING_USER_APPROVAL", "round": 2,
                          "titulo": "Juego Tetris portable"},
        "task_50f418e5": {"status": "interrumpida",
                          "titulo": "Portar el dynarec"},
    })
    assert "task_29ceb5d6" not in texto
    assert "task_50f418e5" not in texto
    assert "Juego Tetris portable" in texto
    assert "Portar el dynarec" in texto


def test_no_aparece_ningun_nombre_de_estado_interno():
    texto = resumen_humano({
        "t1": {"status": "WAITING_USER_APPROVAL", "titulo": "A"},
        "t2": {"status": "in_progress", "titulo": "B"},
        "t3": {"status": "interrumpida", "titulo": "C"},
    })
    for interno in ("WAITING_USER_APPROVAL", "in_progress", "interrumpida"):
        assert interno not in texto, f"«{interno}» es de la base de datos"


def test_una_tarea_que_figura_en_curso_sin_estarlo_no_se_declara_trabajando():
    """
    Es el dato que llevó a Naoko a explicarle al usuario una demora que no
    existía. Decir que trabaja algo que no tiene bucle vivo es falso, y el
    usuario espera basándose en esa falsedad.
    """
    tareas = {"t1": {"status": "in_progress", "titulo": "Zombi", "round": 1}}

    viva = resumen_humano(tareas, vivo=lambda _t: True)
    assert "trabajando ahora mismo" in viva

    muerta = resumen_humano(tareas, vivo=lambda _t: False)
    assert "trabajando ahora mismo" not in muerta
    assert "no tiene nada ejecutándose" in muerta


def test_sin_conversaciones_lo_dice_y_no_enseña_una_lista_vacia():
    assert "ninguna conversación abierta" in resumen_humano({})


def test_una_tarea_terminada_no_pide_nada_al_usuario():
    texto = resumen_humano({"t1": {"status": "completed", "titulo": "Hecho"}})
    assert "Te toca a ti" not in texto
