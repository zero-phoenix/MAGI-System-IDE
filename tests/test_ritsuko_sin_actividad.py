"""
Un auditor que grita en vacío enseña a no hacerle caso.

LO QUE PASÓ, EL 2026-08-20
==========================
Binario recién compilado, arrancado hacía cuarenta segundos, sin una sola
tarea lanzada. Se le preguntó a Ritsuko por el estado del sistema y contestó:

    **Veredicto:** EMPEORA

    **Hallazgos:**
    1. **Todos los nodos están mudos**: MELCHIOR, BALTHASAR y CASPER están en
       la lista de nodos mudos…

Los tres estaban perfectamente. Nadie les había pedido nada.

La causa era aritmética, no de redacción: `evidencia()["nodos"]["mudos"]`
listaba a los tres siempre que `AGENT_POST` valiera cero, y cero es el valor
normal de un sistema recién arrancado. El auditor recibía «los tres callados»
como hecho y concluía lo único razonable con ese hecho delante.

Es el mismo error que ya se corrigió en el canario de deriva de Naoko (C13):
0 de N no significa «falla el 100 %», significa «no hay medición». Aquí, cero
aportaciones no significa «tres nodos rotos», significa «nada que auditar».

Importa más de lo que parece. Una alarma falsa sobre un sistema sano entrena
al usuario a ignorar al auditor — y entonces deja de servir justo el día que
tenga razón.
"""
from __future__ import annotations

import pathlib

import pytest

from magi.modules.infrastructure.ritsuko import RitsukoAgent


def _auditora(eventos: list[dict]) -> RitsukoAgent:
    """Ritsuko con una ventana de eventos puesta a mano, sin bus ni modelos."""
    r = RitsukoAgent.__new__(RitsukoAgent)
    r._eventos = eventos
    r.metrics = None
    r.store = None
    r.swarm = None
    return r


def _post(quien: str) -> dict:
    return {"tema": "AGENT_POST", "quien": quien, "texto": "algo"}


def test_sin_actividad_no_se_acusa_a_nadie():
    ev = _auditora([]).evidencia()

    assert ev["nodos"]["total"] == 0
    assert ev["nodos"]["sin_actividad"] is True
    assert ev["nodos"]["mudos"] == [], (
        "con cero aportaciones los tres nodos salen 'mudos' por aritmética, "
        "no por avería: eso es la alarma falsa que hay que evitar")


def test_con_actividad_el_nodo_callado_si_se_señala():
    """
    La mitad que no se puede perder.

    Callar la alarma cuando no hay datos está bien; callarla cuando SÍ los hay
    convertiría el arreglo en una regresión: «el sistema sigue funcionando con
    dos de tres» es exactamente lo que Ritsuko existe para ver.
    """
    ev = _auditora([_post("MELCHIOR"), _post("BALTHASAR"),
                    _post("MELCHIOR")]).evidencia()

    assert ev["nodos"]["sin_actividad"] is False
    assert ev["nodos"]["mudos"] == ["CASPER"]
    assert ev["nodos"]["aportaciones"] == {"MELCHIOR": 2, "BALTHASAR": 1}


def test_los_tres_hablando_no_deja_a_nadie_mudo():
    ev = _auditora([_post("MELCHIOR"), _post("BALTHASAR"),
                    _post("CASPER")]).evidencia()

    assert ev["nodos"]["mudos"] == []
    assert ev["nodos"]["sin_actividad"] is False


def test_la_regla_esta_escrita_en_el_prompt():
    """
    La evidencia limpia no basta por sí sola: el modelo redacta el veredicto y
    hay que decirle explícitamente qué significa «sin actividad». Sin la regla,
    nada le impide volver a firmar EMPEORA sobre un sistema intacto.
    """
    fuente = (pathlib.Path(__file__).resolve().parents[1] / "magi" / "modules"
              / "infrastructure" / "ritsuko.py").read_text(encoding="utf-8")
    assert "SIN ACTIVIDAD NO HAY AVERIA" in fuente
    assert "sin_actividad" in fuente


@pytest.mark.parametrize("quien", ["MELCHIOR", "BALTHASAR", "CASPER"])
def test_un_solo_nodo_hablando_deja_mudos_a_los_otros_dos(quien):
    ev = _auditora([_post(quien)]).evidencia()
    otros = {"MELCHIOR", "BALTHASAR", "CASPER"} - {quien}
    assert set(ev["nodos"]["mudos"]) == otros
