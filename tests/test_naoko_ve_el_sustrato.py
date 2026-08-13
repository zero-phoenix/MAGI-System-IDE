"""
Naoko supervisaba el enjambre sin ver el suelo que pisa.

EL HUECO
========
Podía decir «MELCHIOR va lento». No podía decir «MELCHIOR va lento porque su
familia se quedó con un solo candidato y ese responde en chino». La primera
frase es una observación; la segunda, un diagnóstico. Solo la segunda se puede
accionar.

Y no es un ejemplo inventado: el 2026-08-13 la familia de MELCHIOR tenía
exactamente un candidato vivo, `Yqcloud`, que contesta en chino. Naoko no tenía
forma de saberlo ni de contarlo, así que el fallo se descubrió midiendo a mano.
"""
from __future__ import annotations

import pytest

from magi.core.providers import sonda
from magi.core.store.state import TaskStore


class _SwarmDePega:
    def __init__(self, store):
        self.store = store
        self.active_tasks = {}


def _naoko_con(store):
    """Naoko sin `__init__`: aquí solo se prueba una función de lectura."""
    from magi.modules.infrastructure.naoko import NaokoAgent

    n = NaokoAgent.__new__(NaokoAgent)
    n.swarm = _SwarmDePega(store)
    return n


@pytest.fixture()
def store(tmp_path):
    return TaskStore(path=tmp_path / "n.db")


def test_dice_cuantos_candidatos_VIVOS_tiene_cada_familia(store):
    """
    La latencia sola no avisa de nada: una familia con 1 de 4 candidatos vivos
    funciona hoy perfectamente y se queda sin nadie mañana. Ese ratio es la
    parte que permite anticiparse.
    """
    sonda.registrar(store, sonda.Medicion("claude", "Perplexity",
                                          "claude45sonnet", ok=True, ms=3723.0))
    sonda.registrar(store, sonda.Medicion("claude", "Perplexity",
                                          "claude40opus", ok=True, ms=2832.0))

    texto = _naoko_con(store)._resumen_del_sustrato()
    assert "claude" in texto
    assert "vivos" in texto
    assert "ms" in texto, "sin latencia no se sabe si va lento"


def test_AVISA_de_la_familia_que_vive_de_un_solo_candidato(store):
    """
    El caso real: la familia de MELCHIOR con un único superviviente. Un aviso
    aquí es la diferencia entre arreglarlo el martes o descubrirlo el viernes
    con el enjambre parado.
    """
    sonda.registrar(store, sonda.Medicion("gpt", "Yqcloud", "gpt-4",
                                          ok=True, ms=11795.0))

    texto = _naoko_con(store)._resumen_del_sustrato()
    assert "AVISO" in texto
    assert "gpt" in texto
    assert "un solo" in texto


def test_sin_mediciones_lo_dice_en_vez_de_callar(store):
    """
    Callar se lee como «todo bien». «Aún no he medido» y «todo va bien» son
    afirmaciones distintas, y confundirlas es cómo un panel acaba mintiendo
    sin que nadie escriba una mentira.
    """
    texto = _naoko_con(store)._resumen_del_sustrato()
    assert "no ha medido" in texto or "sin medir" in texto


def test_si_no_puede_leer_la_sonda_NO_revienta(store, monkeypatch):
    """
    Perder al supervisor porque no pudo leer una tabla es cambiar un problema
    pequeño por uno grande. Naoko habla justo cuando algo va mal.
    """
    monkeypatch.setattr(sonda, "resumen_para_panel",
                        lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("la base está bloqueada")))

    texto = _naoko_con(store)._resumen_del_sustrato()
    assert isinstance(texto, str) and texto
    assert "no he podido" in texto
    assert "bloqueada" in texto, "hay que decir POR QUÉ no se pudo"


def test_sin_almacen_tampoco_revienta():
    from magi.modules.infrastructure.naoko import NaokoAgent

    n = NaokoAgent.__new__(NaokoAgent)
    n.swarm = None
    assert isinstance(n._resumen_del_sustrato(), str)


def test_el_sustrato_entra_en_el_prompt_de_naoko():
    """
    Que el resumen exista no sirve de nada si no llega al prompt. Se lee el
    fuente porque construir el prompt entero exige media Naoko en pie, y esto
    es una comprobación de cableado, no de comportamiento.
    """
    import inspect

    from magi.modules.infrastructure import naoko as mod

    fuente = inspect.getsource(mod)
    assert "sustrato = self._resumen_del_sustrato()" in fuente
    assert "{sustrato}" in fuente, (
        "el resumen se calcula y no se usa: el peor de los dos mundos, "
        "porque cuesta lo mismo y no informa de nada")
