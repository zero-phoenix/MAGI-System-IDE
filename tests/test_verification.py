"""
Tests de la verificación ejecutable de propuestas (Plan MAGI 9.0 §2.5).

El caso central que motivó este fichero: un Tetris (o cualquier juego pygame)
LLEGABA a la verificación, se ejecutaba, arrancaba bien… y se marcaba como
FALLA-timeout porque su mainloop nunca termina. El orquestador lo devolvía a
Melchior una y otra vez sin gastar ronda (log del usuario: "Ronda 5"
repitiéndose). Código correcto rechazado en bucle.

La detección de bloques GUI y el guardián headless lo corrigen: un juego que
arranca da `run-headless` y OK; un bucle infinito sin bucle de eventos sigue
dando FALLA por timeout (no se enmascara).
"""
from __future__ import annotations

import pytest

from magi.core.verification import (
    ProposalVerifier,
    VerificationReport,
    _es_bloque_gui,
    extract_blocks,
)

pytest.importorskip("pygame", reason="la verificación headless de GUI requiere pygame")


# =========================================================== detección GUI

def test_detecta_los_frameworks_de_gui():
    """Un bloque que abre ventana o bucle de eventos debe detectarse como GUI."""
    assert _es_bloque_gui("import pygame\npygame.init()")
    assert _es_bloque_gui("from pygame.locals import *\n")
    assert _es_bloque_gui("import tkinter\nroot = tkinter.Tk()\nroot.mainloop()")
    assert _es_bloque_gui("import turtle\nturtle.forward(100)\nturtle.done()")
    assert _es_bloque_gui("root.after(100, tick)")


def test_no_marca_como_gui_un_bucle_infinito_sin_eventos():
    """
    Un `while True` puro es un BUG, no una GUI: debe seguir dando FALLA por
    timeout. Si lo marcáramos como GUI, enmascararíamos el error.
    """
    assert not _es_bloque_gui("while True:\n    pass")
    assert not _es_bloque_gui("print('hola')")
    assert not _es_bloque_gui("def f():\n    return 42")


def test_extrae_bloques_por_lenguaje():
    bloques = extract_blocks("```python\nprint(1)\n```\n```json\n{}\n```")
    assert len(bloques) == 2
    assert bloques[0] == ("python", "print(1)\n")
    assert bloques[1] == ("json", "{}\n")


# =========================================================== ejecución

@pytest.mark.asyncio
async def test_un_juego_pygame_arranca_y_no_cuelga():
    """
    La regresión del log: un Tetris correcto debe dar OK, no FALLA-timeout.
    Antes colgaba 45s y salía como 'no arranca'; ahora termina headless.
    """
    tetris = (
        "import pygame\n"
        "pygame.init()\n"
        "pantalla = pygame.display.set_mode((100, 100))\n"
        "reloj = pygame.time.Clock()\n"
        "corriendo = True\n"
        "while corriendo:\n"
        "    for e in pygame.event.get():\n"
        "        if e.type == pygame.QUIT:\n"
        "            corriendo = False\n"
        "    pantalla.fill((10, 10, 10))\n"
        "    pygame.display.flip()\n"
        "    reloj.tick(60)\n"
        "pygame.quit()\n"
    )
    v = ProposalVerifier(timeout_s=6.0)
    report = await v.verify(f"```python\n{tetris}```")
    assert report.ok, f"El juego arrancó pero se marcó como fallo:\n{report.render()}"
    assert report.blocks[0].stage == "run-headless"


@pytest.mark.asyncio
async def test_un_bucle_infinito_puro_sigue_dando_falla():
    """El guardián GUI no debe enmascarar un bug real de bucle infinito."""
    v = ProposalVerifier(timeout_s=3.0)
    report = await v.verify("```python\nwhile True:\n    pass\n```")
    assert not report.ok
    assert report.blocks[0].stage == "run"


@pytest.mark.asyncio
async def test_un_pygame_con_error_real_da_falla_con_el_traceback():
    """Un GUI que revienta debe reportar el error, no aprobarse."""
    roto = (
        "import pygame\n"
        "pygame.init()\n"
        "x = no_existe\n"
    )
    v = ProposalVerifier(timeout_s=6.0)
    report = await v.verify(f"```python\n{roto}```")
    assert not report.ok
    assert "NameError" in report.blocks[0].detail or "no_existe" in report.blocks[0].detail


@pytest.mark.asyncio
async def test_tkinter_no_cuelga():
    """tkinter también abre ventana; el guardián debe cancelar su mainloop."""
    app = (
        "import tkinter\n"
        "root = tkinter.Tk()\n"
        "root.after(10, root.destroy)\n"
        "root.mainloop()\n"
    )
    v = ProposalVerifier(timeout_s=6.0)
    report = await v.verify(f"```python\n{app}```")
    assert report.ok, f"tkinter arrancó pero se marcó como fallo:\n{report.render()}"


# =========================================================== informe

def test_el_informe_sin_codigo_lo_dice():
    report = VerificationReport(blocks=[], had_code=False)
    assert "Sin bloques" in report.render()


def test_feedback_para_el_autor_cita_los_fallos():
    from magi.core.verification import BlockResult
    report = VerificationReport(had_code=True)
    report.blocks = [BlockResult("python", 0, False, "run", "NameError: x")]
    fb = report.feedback_for_author()
    assert "NO pasa" in fb
    assert "NameError" in fb
