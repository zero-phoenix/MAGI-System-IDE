"""
Composición de páginas de manga (§5.4).

Se verifica la COMPOSICIÓN —rejilla, orden de lectura, globos, validación—, que
es geometría determinista. La generación de dibujos necesita ComfyUI y queda
detrás de un backend enchufable: no se puede verificar sin él, y fingir que sí
sería exactamente lo que este proyecto lleva diez commits corrigiendo.
"""
import pytest

from magi.core.tools import ToolContext, WriteJournal, build_registry, registry_for_role
from magi.modules.studio.manga import (
    ComfyUIBackend,
    PageSpec,
    Panel,
    PlaceholderBackend,
    ReadingOrder,
    compose_page,
    dramatic_page,
    grid_page,
)

pytest.importorskip("PIL", reason="Pillow no instalado")


# ------------------------------------------------------- orden de lectura

def test_manga_reads_right_to_left():
    """
    Componer con orden occidental produce viñetas correctas y una página
    ilegible — un fallo que no se ve mirando cada dibujo por separado.
    """
    spec = grid_page(2, 2, order=ReadingOrder.RTL)
    seq = [(p.row, p.col) for p in spec.reading_sequence()]
    assert seq == [(0, 1), (0, 0), (1, 1), (1, 0)]


def test_western_order_is_left_to_right():
    spec = grid_page(2, 2, order=ReadingOrder.LTR)
    seq = [(p.row, p.col) for p in spec.reading_sequence()]
    assert seq == [(0, 0), (0, 1), (1, 0), (1, 1)]


def test_wide_panel_orders_by_its_right_edge():
    spec = dramatic_page(order=ReadingOrder.RTL)
    seq = [(p.row, p.col) for p in spec.reading_sequence()]
    assert seq[0] == (0, 0), "la panorámica de arriba va primero"
    assert seq[1] == (1, 1), "en manga, la derecha antes que la izquierda"


# ------------------------------------------------------------- validación

def test_valid_grid_has_no_problems():
    assert grid_page(3, 2).validate() == []


def test_overlapping_panels_are_detected():
    spec = PageSpec([Panel(0, 0, col_span=2), Panel(0, 1)], rows=1, cols=2)
    problems = spec.validate()
    assert any("solapan" in p for p in problems)


def test_panel_outside_the_page_is_detected():
    spec = PageSpec([Panel(0, 0, col_span=5)], rows=1, cols=2)
    assert any("se sale por la derecha" in p for p in spec.validate())

    spec = PageSpec([Panel(0, 0, row_span=4)], rows=2, cols=1)
    assert any("se sale por abajo" in p for p in spec.validate())


def test_empty_cells_are_reported():
    spec = PageSpec([Panel(0, 0)], rows=2, cols=2)
    assert any("celdas vacías" in p for p in spec.validate())


def test_empty_page_is_invalid():
    assert any("sin viñetas" in p for p in PageSpec([], 1, 1).validate())


# --------------------------------------------------------------- geometría

def test_panels_do_not_overlap_in_pixels():
    spec = grid_page(2, 2)
    rects = [spec.panel_rect(p) for p in spec.panels]
    for i, (ax0, ay0, ax1, ay1) in enumerate(rects):
        assert ax1 > ax0 and ay1 > ay0, "rectángulo degenerado"
        for j, (bx0, by0, bx1, by1) in enumerate(rects):
            if i >= j:
                continue
            solapa = not (ax1 <= bx0 or bx1 <= ax0 or ay1 <= by0 or by1 <= ay0)
            assert not solapa, f"viñetas {i} y {j} se pisan en píxeles"


def test_panels_stay_inside_the_margins():
    spec = grid_page(3, 2)
    for p in spec.panels:
        x0, y0, x1, y1 = spec.panel_rect(p)
        assert x0 >= spec.margin and y0 >= spec.margin
        assert x1 <= spec.width - spec.margin + 1
        assert y1 <= spec.height - spec.margin + 1


def test_spanning_panel_is_wider():
    spec = dramatic_page()
    wide = next(p for p in spec.panels if p.col_span == 2)
    narrow = next(p for p in spec.panels if p.col_span == 1)
    wx0, _, wx1, _ = spec.panel_rect(wide)
    nx0, _, nx1, _ = spec.panel_rect(narrow)
    assert (wx1 - wx0) > (nx1 - nx0) * 1.8


# --------------------------------------------------------------- composición

@pytest.mark.asyncio
async def test_composes_a_page_with_placeholders(tmp_path):
    spec = grid_page(2, 2, ["un gato en un tejado", "primer plano del gato",
                            "el gato salta", "el gato aterriza"])
    out = tmp_path / "pagina.png"
    report = await compose_page(spec, out)
    assert report["ok"], report.get("problems")
    assert out.exists()
    assert report["panels"] == 4 and report["generated"] == 4


@pytest.mark.asyncio
async def test_composed_page_is_not_blank(tmp_path):
    """Se apoya en el mismo detector del bucle de observación (§5)."""
    from magi.modules.studio.artifacts import observe_image
    spec = grid_page(2, 2, ["a", "b", "c", "d"])
    out = tmp_path / "p.png"
    await compose_page(spec, out)
    obs = await observe_image(out)
    assert obs.ok, "la página compuesta no puede ser de un solo color"


@pytest.mark.asyncio
async def test_invalid_layout_generates_nothing(tmp_path):
    """No gastar cuota en una página que ya se sabe mal montada."""
    spec = PageSpec([Panel(0, 0, col_span=2), Panel(0, 1)], rows=1, cols=2)
    out = tmp_path / "mala.png"
    report = await compose_page(spec, out)
    assert not report["ok"]
    assert not out.exists(), "no debe escribir nada si la composición es inválida"


@pytest.mark.asyncio
async def test_dialogue_and_captions_do_not_crash(tmp_path):
    spec = PageSpec(
        [Panel(0, 0, prompt="escena", dialogue=["¡Cuidado!", "¿Qué pasa?"],
               caption="Tres días después...")],
        rows=1, cols=1)
    out = tmp_path / "d.png"
    assert (await compose_page(spec, out))["ok"]


@pytest.mark.asyncio
async def test_failing_backend_is_reported_not_hidden(tmp_path):
    class Broken:
        async def generate(self, prompt, w, h, out):
            return False

    spec = grid_page(1, 2, ["a", "b"])
    report = await compose_page(spec, tmp_path / "x.png", backend=Broken())
    assert not report["ok"]
    assert any("sin dibujo generado" in p for p in report["problems"])


# ------------------------------------------------------------- ComfyUI

def test_comfyui_workflow_is_well_formed():
    """El grafo se puede comprobar sin ComfyUI corriendo."""
    wf = ComfyUIBackend()._workflow("un gato", 512, 768, seed=42)
    assert wf["5"]["inputs"]["width"] == 512
    assert wf["6"]["inputs"]["text"] == "un gato"
    assert wf["3"]["inputs"]["seed"] == 42
    for node in wf.values():
        assert "class_type" in node and "inputs" in node


@pytest.mark.asyncio
async def test_comfyui_absent_fails_explicitly(tmp_path):
    """No debe fingir que generó algo."""
    b = ComfyUIBackend(host="http://127.0.0.1:1")
    assert not b.reachable()
    assert await b.generate("x", 64, 64, tmp_path / "n.png") is False


def test_backends_report_says_what_is_missing():
    from magi.modules.studio.artifacts import backends_report
    out = backends_report()
    assert "comfyui_local" in out
    if "no   comfyui_local" in out:
        assert "marcadores de posición" in out


# ---------------------------------------------------------------- cableado

def test_manga_tools_are_in_the_catalog():
    names = set(build_registry().names())
    assert "compose_manga_page" in names and "validate_manga_layout" in names


def test_manga_tools_appear_for_a_manga_task():
    names = set(registry_for_role("MELCHIOR", "dibuja una página de manga").names())
    assert "compose_manga_page" in names


@pytest.mark.asyncio
async def test_layout_validation_tool(tmp_path):
    ctx = ToolContext(task_id="t", cwd=tmp_path,
                      journal=WriteJournal("t", tmp_path / ".j"))
    reg = build_registry()
    r = await reg.execute("validate_manga_layout",
                          {"rows": 2, "cols": 2, "layout": "grid"}, ctx)
    assert r.ok and "derecha-a-izquierda" in r.content

    r = await reg.execute("compose_manga_page",
                          {"out_path": "pag.png", "rows": 2, "cols": 2,
                           "prompts": ["a", "b", "c", "d"]}, ctx)
    assert r.ok and (tmp_path / "pag.png").exists()
