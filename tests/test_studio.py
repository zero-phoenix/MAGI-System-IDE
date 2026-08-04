"""
Fábrica de artefactos con bucle de observación (§5).

La idea que se comprueba aquí: un sistema que genera un juego y te lo entrega
sin arrancarlo ha generado *código de juego*; uno que lo arranca, captura un
fotograma y lo mira, ha hecho *un juego*.
"""
import asyncio

import pytest

from magi.core.tools import ToolContext, WriteJournal, build_registry
from magi.modules.studio.artifacts import (
    ArtifactKind, Observation, available_backends, observe, observe_document,
    observe_game, observe_image, observe_program,
)

pygame = pytest.importorskip("pygame", reason="pygame no instalado")


GAME_VISIBLE = """
import pygame
pygame.init()
s = pygame.display.set_mode((320, 240))
c = pygame.time.Clock()
for _ in range(1000):
    s.fill((20, 20, 30))
    pygame.draw.rect(s, (240, 200, 60), (150, 110, 40, 40))
    pygame.draw.circle(s, (200, 60, 60), (80, 60), 18)
    pygame.display.flip()
    c.tick(60)
"""

GAME_INVISIBLE = """
import pygame
pygame.init()
s = pygame.display.set_mode((320, 240))
c = pygame.time.Clock()
for _ in range(1000):
    s.fill((20, 20, 30))
    pygame.draw.rect(s, (20, 20, 30), (150, 110, 20, 20))
    pygame.display.flip()
    c.tick(60)
"""

GAME_CRASHES = "import pygame\npygame.init()\nraise RuntimeError('boom')\n"


# ------------------------------------------------------------------ juegos

@pytest.mark.asyncio
async def test_playable_game_is_observed_ok(tmp_path):
    (tmp_path / "main.py").write_text(GAME_VISIBLE, encoding="utf-8")
    obs = await observe_game(tmp_path, frames=20)
    assert obs.ok, obs.render()
    assert obs.screenshot and obs.kind is ArtifactKind.GAME


@pytest.mark.asyncio
async def test_blank_screen_is_caught_without_a_vision_model(tmp_path):
    """
    EL caso que justifica todo el bucle: el juego arranca, dibuja fotogramas y
    no se ve nada porque el jugador es del color del fondo. Leyendo el código
    no se detecta; mirando la captura, sí — y sin gastar cuota de visión.
    """
    (tmp_path / "main.py").write_text(GAME_INVISIBLE, encoding="utf-8")
    obs = await observe_game(tmp_path, frames=20)
    assert not obs.ok, "una pantalla de un solo color no puede dar OK"
    assert any("un solo color" in p for p in obs.problems)
    assert "color del fondo" in obs.feedback()


@pytest.mark.asyncio
async def test_crashing_game_reports_the_traceback(tmp_path):
    (tmp_path / "roto.py").write_text(GAME_CRASHES, encoding="utf-8")
    obs = await observe_game(tmp_path, entry="roto.py", frames=10)
    assert not obs.ok
    assert any("ni un fotograma" in p for p in obs.problems)
    assert "boom" in obs.feedback()


@pytest.mark.asyncio
async def test_stale_screenshot_is_not_reported(tmp_path):
    """
    Bug encontrado en la demo: tras una ejecución correcta, una posterior que
    revienta seguía informando de la captura ANTERIOR. El informe describía la
    ejecución equivocada.
    """
    (tmp_path / "main.py").write_text(GAME_VISIBLE, encoding="utf-8")
    ok = await observe_game(tmp_path, frames=20)
    assert ok.screenshot

    (tmp_path / "roto.py").write_text(GAME_CRASHES, encoding="utf-8")
    bad = await observe_game(tmp_path, entry="roto.py", frames=10)
    assert bad.screenshot is None, "no debe heredar la captura de otra ejecución"


@pytest.mark.asyncio
async def test_missing_entry_point(tmp_path):
    obs = await observe_game(tmp_path, entry="no_existe.py")
    assert not obs.ok and "no existe" in obs.problems[0]


@pytest.mark.asyncio
async def test_harness_is_cleaned_up(tmp_path):
    (tmp_path / "main.py").write_text(GAME_VISIBLE, encoding="utf-8")
    await observe_game(tmp_path, frames=15)
    assert not (tmp_path / "_magi_harness.py").exists()


# --------------------------------------------------------------- programas

@pytest.mark.asyncio
async def test_program_that_runs(tmp_path):
    p = tmp_path / "ok.py"
    p.write_text("print('todo bien')\n", encoding="utf-8")
    obs = await observe_program(p)
    assert obs.ok and "todo bien" in obs.evidence[0]


@pytest.mark.asyncio
async def test_program_that_fails(tmp_path):
    p = tmp_path / "mal.py"
    p.write_text("raise ValueError('estalla')\n", encoding="utf-8")
    obs = await observe_program(p)
    assert not obs.ok
    assert "estalla" in obs.feedback()


# ----------------------------------------------------------------- imagen

@pytest.mark.asyncio
async def test_solid_colour_image_is_flagged(tmp_path):
    from PIL import Image
    p = tmp_path / "vacia.png"
    Image.new("RGB", (64, 64), (10, 10, 10)).save(p)
    obs = await observe_image(p)
    assert not obs.ok and "un solo color" in obs.problems[0]


@pytest.mark.asyncio
async def test_image_with_content_passes(tmp_path):
    from PIL import Image, ImageDraw
    p = tmp_path / "con_contenido.png"
    im = Image.new("RGB", (64, 64), (10, 10, 10))
    ImageDraw.Draw(im).rectangle([10, 10, 50, 50], fill=(240, 200, 60))
    im.save(p)
    obs = await observe_image(p)
    assert obs.ok


@pytest.mark.asyncio
async def test_missing_image(tmp_path):
    obs = await observe_image(tmp_path / "no.png")
    assert not obs.ok


# -------------------------------------------------------------- documentos

@pytest.mark.asyncio
async def test_empty_document_is_flagged(tmp_path):
    p = tmp_path / "vacio.md"
    p.write_text("# Título\n", encoding="utf-8")
    obs = await observe_document(p)
    assert not obs.ok and "vacío" in obs.problems[0]


@pytest.mark.asyncio
async def test_document_with_content(tmp_path):
    p = tmp_path / "informe.md"
    p.write_text("# Informe\n\n" + "palabra " * 200, encoding="utf-8")
    obs = await observe_document(p)
    assert obs.ok
    # 202: las 200 repeticiones más las dos palabras del título.
    assert "202 palabras" in " ".join(obs.evidence)


@pytest.mark.asyncio
async def test_zero_byte_file(tmp_path):
    p = tmp_path / "cero.txt"
    p.write_bytes(b"")
    obs = await observe_document(p)
    assert not obs.ok and any("0 bytes" in x for x in obs.problems)


@pytest.mark.asyncio
async def test_docx_is_measured(tmp_path):
    docx = pytest.importorskip("docx")
    p = tmp_path / "doc.docx"
    d = docx.Document()
    d.add_paragraph("palabra " * 60)
    d.save(p)
    obs = await observe_document(p)
    assert obs.ok and "párrafos" in obs.evidence[1]


# ---------------------------------------------------------------- despacho

@pytest.mark.asyncio
async def test_kind_is_inferred_from_the_extension(tmp_path):
    from PIL import Image
    img = tmp_path / "x.png"
    Image.new("RGB", (8, 8), (1, 2, 3)).save(img)
    assert (await observe(img)).kind is ArtifactKind.IMAGE

    doc = tmp_path / "y.md"
    doc.write_text("hola " * 50, encoding="utf-8")
    assert (await observe(doc)).kind is ArtifactKind.DOCUMENT


def test_backends_report_what_is_available():
    b = available_backends()
    assert "pygame" in b and "pillow" in b and "comfyui_local" in b


# ---------------------------------------------------------------- cableado

def test_studio_tools_are_in_the_swarm_catalog():
    names = set(build_registry().names())
    for t in ("observe_artifact", "inspect_image", "studio_backends"):
        assert t in names, f"{t} no está conectado al enjambre"


def test_critic_and_judge_can_observe():
    """
    Balthasar debe poder ARRANCAR el juego para criticarlo, y Casper mirar el
    artefacto en vez de fiarse del acta.
    """
    from magi.core.tools import registry_for_role
    assert "observe_artifact" in registry_for_role("BALTHASAR").names()
    assert "observe_artifact" in registry_for_role("CASPER").names()


@pytest.mark.asyncio
async def test_observe_artifact_tool_end_to_end(tmp_path):
    (tmp_path / "main.py").write_text(GAME_INVISIBLE, encoding="utf-8")
    ctx = ToolContext(task_id="t", cwd=tmp_path,
                      journal=WriteJournal("t", tmp_path / ".j"))
    r = await build_registry().execute(
        "observe_artifact", {"path": ".", "kind": "juego"}, ctx)
    assert not r.ok
    assert "un solo color" in (r.error or "")
