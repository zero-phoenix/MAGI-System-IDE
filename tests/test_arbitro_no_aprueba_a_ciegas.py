"""
El árbitro no firma lo que no ha leído (C1, C2, C11, C12).

Estos cuatro tests fijan el fallo más caro que ha tenido este sistema, medido
tres veces el 2026-08-20: el usuario recibía

    **Decisión Técnica:** APPROVED
    [Tiempo de espera agotado tras 150s en iteración 1. Proveedor: g4f-gpt...]

Casper no había recibido NADA. El texto no traía marcador de decisión, y el
respaldo de `_leer_decision` aprobaba por defecto. Aprobar sin haber leído no
es imprecisión: es afirmar algo que nadie ha comprobado.
"""
from __future__ import annotations

import pytest

from magi.core.providers.base import es_degradada
from magi.modules.swarm.agents import _leer_decision


@pytest.mark.parametrize("texto,proveedor", [
    ("[Tiempo de espera agotado tras 150s en iteracion 1. Proveedor: g4f-gpt]", "TIMEOUT"),
    ("[Inferencia no disponible: todos los proveedores fallaron]", "SYSTEM_ERROR"),
    ("", "g4f-gpt"),
])
def test_una_respuesta_degradada_nunca_produce_aprobacion(texto, proveedor):
    assert es_degradada(texto, proveedor)
    decision, _ = _leer_decision(texto, round_num=1, degradada=True)
    assert decision == "SIN_ARBITRAJE"
    assert decision != "APPROVED"


def test_el_texto_solo_tambien_delata_el_fallo():
    """
    Sin `provider_id` a mano, el texto basta.

    Importa porque hay caminos —tareas rehidratadas, respuestas que pasan por
    el bus— donde solo queda la cadena.
    """
    decision, _ = _leer_decision(
        "[Tiempo de espera agotado tras 150s en iteracion 1]", round_num=1)
    assert decision == "SIN_ARBITRAJE"


def test_una_respuesta_de_verdad_sigue_aprobando():
    """La guarda no puede volverse un freno: lo normal tiene que pasar."""
    decision, _ = _leer_decision(
        "He revisado ambas propuestas y la B es correcta.\n\nDECISIÓN: APROBADA",
        round_num=1)
    assert decision == "APPROVED"


def test_declarar_una_compilacion_que_no_consta_sale_avisado():
    """
    C12 — «Se compiló exitosamente el binario» con el registro vacío.

    Es el caso real de la prueba del ping pong: cero bloques de código, cero
    artefactos, y el informe hablando de un `.exe` en pasado.
    """
    from magi.core.blackboard import Blackboard
    from magi.core.bus import MagiBus
    from magi.modules.swarm.orchestrator import SwarmOrchestrator

    swarm = SwarmOrchestrator(Blackboard(), MagiBus())
    aviso = swarm._contraste_con_el_registro(
        state={},
        verdict={"decision": "APPROVED",
                 "feedback": "Empaquetado final: se compiló exitosamente el "
                             "binario ejecutable único portable (onefile)."})
    assert aviso is not None and "no hay fichero que buscar" in aviso

    # Y con artefacto de verdad, no molesta.
    assert swarm._contraste_con_el_registro(
        state={"artefactos": ["C:/x/juego.exe"]},
        verdict={"feedback": "se compiló exitosamente el binario"}) is None
