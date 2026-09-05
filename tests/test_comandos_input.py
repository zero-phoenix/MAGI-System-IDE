"""
Las órdenes escritas en el input se ejecutan, no se debaten.

El caso que lo motiva (5-sep-2026): «task.cancel task_x» tecleado arrancó
una tarea que propuso desregistrar una tarea programada de Windows. B1.
"""
from magi.core.comandos import clasificar


def test_task_cancel_con_objetivo():
    assert clasificar("task.cancel task_or2r73jm") == ("cancel", "task_or2r73jm")


def test_task_cancel_sin_objetivo_delega_en_el_llamador():
    assert clasificar("task.cancel") == ("cancel", "")


def test_variantes_de_parar_todo():
    assert clasificar("parar todo")[0] == "estop"
    assert clasificar("EMERGENCY_STOP")[0] == "estop"
    assert clasificar("emergencia")[0] == "estop"


def test_un_encargo_normal_no_es_orden():
    assert clasificar("crea un juego de tetris en un exe") == ("", "")
    assert clasificar("cancela el ruido de fondo del audio") == ("", "")


def test_vacio_y_no_texto():
    assert clasificar("") == ("", "")
    assert clasificar(None) == ("", "")
