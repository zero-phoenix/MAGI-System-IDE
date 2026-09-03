"""
El perro guardián de la ronda dormida — el juicio sin el reloj.

Nacido de una tarea real: 20+ minutos en «in_progress» con el bus mudo
(2-sep-2026). Ningún watchdog miraba el PROGRESO de una ronda viva.
"""
from magi.modules.infrastructure.guardian import deberia_alertar


def test_silencio_largo_con_tareas_vivas_alerta():
    r = deberia_alertar({"t1": "in_progress"}, 1500.0)
    assert r and r["vivas"] == ["t1"] and r["silencio_s"] == 1500


def test_bus_vivo_no_alerta_aunque_haya_tareas():
    assert deberia_alertar({"t1": "in_progress"}, 30.0) is None


def test_sin_tareas_vivas_el_silencio_no_es_ronda_dormida():
    assert deberia_alertar({"t1": "completed", "t2": "WAITING_USER_APPROVAL"},
                           99999.0) is None
