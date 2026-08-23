"""
«No me dio tiempo a comprobarlo» no es «está bien» (§G5).

EL AGUJERO, REPRODUCIDO
=======================
Un bloque con interfaz gráfica que agotaba el plazo salía como `skipped` con
`ok=True`. La intención era razonable: un juego pygame correcto no termina por
sí solo, y marcarlo como fallo sería injusto.

Pero eso convierte «se acabó el tiempo» en «aprobado», y las dos cosas no se
parecen en nada. Reproducido el 2026-08-23 con tres líneas:

    import pygame
    pygame.init()
    x = no_existe

Con plazo de 20 s: `ok=False`, NameError detectado. Con plazo de 6 s: el
NameError no llega a verse y el bloque **se aprueba**.

Y el plazo era de 8 s, cuando en este mismo equipo `import pygame` +
`pygame.init()` cuestan 1,91 s antes de ejecutar una sola línea del usuario.
En una máquina ocupada, un Tetris roto pasaba la verificación — justo el
encargo que el usuario acababa de hacer.

LA REGLA
========
La prueba de que el código arrancó de verdad es que llegara a pintar. El
guardián imprime una marca en su primer fotograma:

  · con marca -> llegó al bucle de dibujo y no termina solo: `skipped`, ok.
  · sin marca -> no se sabe nada: NO se aprueba.
"""
from __future__ import annotations

import pytest

from magi.core.verification import (
    _GUI_TIMEOUT_S,
    _MARCA_PRIMER_FOTOGRAMA,
    ProposalVerifier,
)

JUEGO_QUE_PINTA = (
    "import pygame\n"
    "pygame.init()\n"
    "p = pygame.display.set_mode((80, 60))\n"
    "while True:\n"
    "    p.fill((0, 0, 0))\n"
    "    pygame.display.flip()\n"
)

CUELGA_ANTES_DE_PINTAR = (
    "import pygame\n"
    "pygame.init()\n"
    "import time\n"
    "time.sleep(3600)\n"
    "pygame.display.set_mode((80, 60))\n"
)


def test_el_plazo_da_para_arrancar_pygame():
    """
    `import pygame` + `init()` cuestan 1,91 s medidos aquí. Un plazo que no
    cubre eso con holgura no verifica: aprueba por agotamiento.
    """
    assert _GUI_TIMEOUT_S >= 20.0, (
        "con un plazo corto, un bloque GUI se aprueba sin haberse comprobado")


@pytest.mark.asyncio
async def test_un_juego_que_pinta_se_da_por_arrancado():
    v = ProposalVerifier(timeout_s=_GUI_TIMEOUT_S)
    r = await v.verify(f"```python\n{JUEGO_QUE_PINTA}```")
    b = r.blocks[0]
    assert b.ok, f"un juego que pinta fotogramas arranca:\n{b.detail}"
    assert b.stage in ("run-headless", "skipped")


@pytest.mark.asyncio
async def test_lo_que_nunca_pinta_no_se_aprueba():
    """
    La mitad que cierra el agujero. Se cuelga ANTES de dibujar: el guardián no
    llega a contar ni un fotograma, así que no hay ninguna prueba de que el
    código funcione. Antes esto salía aprobado.
    """
    v = ProposalVerifier(timeout_s=6.0)
    r = await v.verify(f"```python\n{CUELGA_ANTES_DE_PINTAR}```")
    b = r.blocks[0]
    assert not b.ok, (
        "sin un solo fotograma no hay nada verificado, y no se puede aprobar")
    assert "NO VERIFICADO" in b.detail


def test_el_guardian_imprime_la_marca():
    """
    Si el guardián deja de imprimirla, todo juego correcto pasaría a «NO
    VERIFICADO» y el arreglo se convertiría en un bloqueo. La marca es la
    bisagra: tiene que estar en los dos sitios.
    """
    from magi.core.verification import _GUI_GUARD

    assert _MARCA_PRIMER_FOTOGRAMA in _GUI_GUARD
