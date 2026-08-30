"""
La secuencia de inyecciones tiene su propia casa (y su porqué).

Nació cuando la cuarta inyección inline (ronda_verificada) hizo saltar el
trinquete del orchestrator. Estos tests fijan el contrato de `acumuladas`:
que llame a las cuatro, en el orden documentado, y que no edite lo que cada
una escribió.
"""
from __future__ import annotations

import pytest

from magi.modules.swarm import inyecciones


@pytest.fixture
def encargo_de_emulador() -> str:
    return "ronda 2: corre y mide el emulador yabausevita (sonic r)"


def test_concatena_a_las_cuatro(monkeypatch, encargo_de_emulador):
    """Cada módulo aporta su trozo; ninguno se queda sin llamar."""
    llamadas = []
    import magi.modules.swarm.aceptacion as acept
    import magi.modules.swarm.bitacora as bit
    import magi.modules.swarm.caja_de_herramientas as caja
    import magi.modules.swarm.ronda_verificada as ronda

    def espiar(nombre, original):
        def espia(encargo, *a, **kw):
            llamadas.append(nombre)
            return original(encargo, *a, **kw) if original else ""
        return espia

    monkeypatch.setattr(acept, "criterios", lambda e: e)
    monkeypatch.setattr(acept, "para_el_prompt",
                        espiar("aceptacion", lambda e: "[A]"))
    monkeypatch.setattr(caja, "para_el_prompt",
                        espiar("caja", lambda e: "[C]"))
    monkeypatch.setattr(bit, "para_el_prompt",
                        espiar("bitacora", lambda e: "[B]"))
    monkeypatch.setattr(ronda, "para_el_prompt",
                        espiar("ronda", lambda e: "[R]"))

    fuera = inyecciones.acumuladas(encargo_de_emulador)

    assert llamadas == ["aceptacion", "caja", "bitacora", "ronda"]
    assert fuera == "[A][C][B][R]"


def test_encargo_ajeno_queda_casi_vacio(monkeypatch, tmp_path):
    """Sin bitácora ni harness alrededor, un encargo que no es del ciclo no
    recibe ni bitácora ni protocolo de corrida — las inyecciones filtran."""
    monkeypatch.delenv("MAGI_BITACORA", raising=False)
    monkeypatch.delenv("MAGI_HARNESS_VITA3K", raising=False)
    monkeypatch.chdir(tmp_path)
    fuera = inyecciones.acumuladas("escribe un poema sobre el mar")
    assert "PROTOCOLO DE CORRIDA" not in fuera
    assert "BITÁCORA" not in fuera.upper() or "bitácora" not in fuera
