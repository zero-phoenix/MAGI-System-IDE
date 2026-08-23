"""
Con tres canarios no se distingue deriva de ruido (§G3).

C13 ya cubría el caso `0 de N`: un canario que no contesta no dice nada del
modelo. Lo que quedaba fuera era el caso intermedio, y ahí es donde apareció:

2026-08-23, sistema del usuario PARADO, sin ninguna tarea, 200 s de sonda:

    Deriva detectada en g4f-gpt:    solo 1/3 respuestas canarias correctas
    Deriva detectada en g4f-gemini: solo 1/3 respuestas canarias correctas

Dos alarmas críticas sobre proveedores intactos. Ese mismo día, Perplexity
devolvió «tud.» —cuatro caracteres— tres veces seguidas: con proveedores
gratuitos, acertar 1 de 3 es ruido normal, no una señal.

Deriva significa que el proveedor responde BIEN y DISTINTO. Si la mayoría no
llega a responder bien, lo que se mide es la salud del proveedor, no la
identidad del modelo. Y el veredicto se publica como crítico e invalida las
comparaciones del sistema: equivocarse ahí sale caro.
"""
from __future__ import annotations

import pytest

from magi.modules.infrastructure.naoko import deriva_es_concluyente


@pytest.mark.parametrize("acertados,total", [(0, 3), (1, 3), (1, 2), (2, 5)])
def test_sin_mayoria_no_hay_veredicto(acertados, total):
    assert not deriva_es_concluyente(acertados, total)


@pytest.mark.parametrize("acertados,total", [(2, 3), (3, 3), (3, 5), (5, 5)])
def test_con_mayoria_si_se_puede_juzgar(acertados, total):
    """
    La mitad que hace falta para que el guardián no sea un silenciador.

    Si esto devolviera siempre `False`, MAGI dejaría de detectar deriva real
    —un proveedor que cambia de modelo por debajo sin avisar—, que es
    exactamente el problema que la detección venía a resolver.
    """
    assert deriva_es_concluyente(acertados, total)


def test_sin_canarios_no_se_afirma_nada():
    """Cero de cero no es «todo bien»: es que no se midió."""
    assert not deriva_es_concluyente(0, 0)


def test_el_caso_exacto_del_23_de_agosto():
    """El que apareció en la sonda, nombrado para que no vuelva en silencio."""
    assert not deriva_es_concluyente(1, 3)
