"""
Si pediste un fichero, un texto sobre el fichero no es una entrega (C4).

Sale de dos encargos reales del 2026-08-20 —«haz una réplica de Tetris en un
.exe portable» y «crea un ping pong a color de 16 bits en un .exe portable»—
que terminaron con cero bloques de código, cero artefactos, y el árbitro
escribiendo «se compiló exitosamente el binario ejecutable único portable».

Nada lo detectó porque nada sabía que se había pedido un binario.
"""
from __future__ import annotations

import pytest

from magi.core.blackboard import Blackboard
from magi.core.bus import MagiBus
from magi.modules.swarm.intencion import pide_artefacto
from magi.modules.swarm.orchestrator import SwarmOrchestrator


@pytest.mark.parametrize("texto", [
    "Haz una replica del juego Tetris en un ejecutable unico portable en formato exe.",
    "Crea un juego de ping pong a color de 16 bits en un unico ejecutable exe portable.",
    "hazme un script de python que ordene ficheros",
    "compila un binario portable con el juego",
])
def test_reconoce_lo_que_pide_producto(texto):
    assert pide_artefacto(texto) is True


@pytest.mark.parametrize("texto", [
    # Preguntar cómo se hace algo no es pedirlo. Este es el falso positivo que
    # convertiría una explicación en un binario que nadie encargó.
    "Explica como se hace un ejecutable portable con PyInstaller",
    "compara pygame y tkinter para un juego",
    "por que el exe de PPSSPP pesa tanto",
    "que es un binario portable",
    "resume el estado del proyecto",
    "",
])
def test_no_confunde_una_pregunta_con_un_encargo(texto):
    assert pide_artefacto(texto) is False


def _swarm() -> SwarmOrchestrator:
    return SwarmOrchestrator(Blackboard(), MagiBus())


def test_sin_codigo_ni_artefacto_la_entrega_esta_incompleta():
    falta = _swarm()._contrato_de_entregable({
        "command": "crea un ping pong en un exe portable",
        "last_proposal": {"content": "Se implementó una arquitectura basada en "
                                     "Pygame y se empaquetó con PyInstaller."},
    })
    assert falta is not None
    assert "no hay ni un bloque de código" in falta
    assert "no se ha generado ningún artefacto" in falta


def test_con_codigo_verificado_y_artefacto_el_contrato_se_cumple():
    falta = _swarm()._contrato_de_entregable({
        "command": "crea un ping pong en un exe portable",
        "last_proposal": {"content": "```python\nprint('hola')\n```"},
        "verification": {"ran": True, "passed": True},
        "artefactos": ["C:/Users/x/Desktop/pong.exe"],
    })
    assert falta is None


def test_una_pregunta_no_arrastra_contrato():
    """Sin encargo de producto no hay nada que exigir, y no debe estorbar."""
    assert _swarm()._contrato_de_entregable({
        "command": "explica como funciona un dynarec",
        "last_proposal": {"content": "Un dynarec traduce bloques..."},
    }) is None
