"""
El atajo de los encargos triviales: sin red, sin cuota, sin esperar.

Medido el 2-sep-2026: 20+ minutos para un «holamundo» porque TODO encargo
pagaba la llamada de estilo (3-22 s) y corría en motor profundo. El atajo
es determinista y conservador: ante la duda, no es trivial.
"""
import pytest

from magi.modules.infrastructure.motor import es_trivial, estilo_y_motor


def test_cortos_sencillos_son_triviales():
    assert es_trivial("crea holamundo.py que imprima hola")
    assert es_trivial("que numero es primo 17")


def test_trabajo_de_fondo_nunca_es_trivial():
    assert not es_trivial("optimiza el emulador")            # corto pero serio
    assert not es_trivial("analiza este log")
    assert not es_trivial("diseña una API REST para el inventario")
    assert not es_trivial("x" * 200)                          # largo


async def test_lo_trivial_no_llama_al_llm(monkeypatch):
    async def estallaria(*a, **kw):
        raise AssertionError("un encargo trivial no debe pagar la llamada de estilo")
    monkeypatch.setattr("magi.modules.infrastructure.naoko.estilo_para", estallaria)
    estilo, motor, origen = await estilo_y_motor(
        "crea holamundo.py que imprima hola", motor_gui="deep")
    assert (estilo, motor, origen) == ("tecnico", "fast", "heuristica-trivial")


async def test_lo_serio_sigue_preguntando_a_naoko(monkeypatch):
    async def falso_estilo(cmd, llm=None):
        return "divulgativo"
    monkeypatch.setattr("magi.modules.infrastructure.naoko.estilo_para", falso_estilo)
    estilo, motor, origen = await estilo_y_motor(
        "analiza el rendimiento del emulador yabausevita", motor_gui="deep")
    assert (estilo, motor, origen) == ("divulgativo", "deep", "naoko")


async def test_nunca_se_sube_la_marcha(monkeypatch):
    """Pidió fast: se queda en fast aunque el encargo parezca profundo."""
    async def falso_estilo(cmd, llm=None):
        return "tecnico"
    monkeypatch.setattr("magi.modules.infrastructure.naoko.estilo_para", falso_estilo)
    _, motor, _ = await estilo_y_motor(
        "analiza a fondo el rendimiento", motor_gui="fast")
    assert motor == "fast"
