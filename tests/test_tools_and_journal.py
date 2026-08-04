"""
Tests de herramientas, journal y bucle de agente.

El journal es lo que hace utilizable el acceso sin restricciones a la máquina:
si toda mutación se puede deshacer, se puede dejar al agente actuar sin pedir
permiso. Estos tests verifican que el deshacer funciona de verdad.
"""
import pytest

from magi.core.tools import (
    ToolContext, WriteJournal, build_registry, registry_for_role,
    parse_tool_calls, strip_tool_calls, format_results,
)
from magi.core.tools.registry import ToolResult


@pytest.fixture
def ctx(tmp_path):
    return ToolContext(task_id="t1", cwd=tmp_path,
                       journal=WriteJournal(task_id="t1", root=tmp_path / ".j"))


# ------------------------------------------------------------------- protocolo

def test_parse_fenced_tool_call():
    text = 'Voy a mirarlo.\n```tool\n{"tool":"read_file","args":{"path":"a.py"}}\n```'
    calls = parse_tool_calls(text)
    assert len(calls) == 1
    assert calls[0].name == "read_file"
    assert calls[0].args["path"] == "a.py"


def test_parse_multiple_calls_in_one_turn():
    text = ('```tool\n{"tool":"read_file","args":{"path":"a"}}\n```\n'
            '```tool\n{"tool":"list_dir","args":{"path":"."}}\n```')
    assert [c.name for c in parse_tool_calls(text)] == ["read_file", "list_dir"]


def test_parse_tolerates_alternate_shapes():
    """Los modelos gratuitos formatean de formas variadas; el parser aguanta."""
    assert parse_tool_calls('<tool>{"name":"grep","arguments":{"pattern":"x"}}</tool>')
    assert parse_tool_calls('```tool_call\n{"tool":"glob","args":{"pattern":"*.py"}}\n```')


def test_no_tool_call_means_agent_finished():
    assert parse_tool_calls("Conclusión: ya está.") == []


def test_strip_removes_plumbing_from_user_view():
    text = 'Analizando.\n```tool\n{"tool":"read_file","args":{}}\n```\nListo.'
    out = strip_tool_calls(text)
    assert "tool" not in out and "Analizando" in out and "Listo" in out


def test_format_results_marks_errors():
    out = format_results([ToolResult(False, "", "run_tests", error="rc=1")])
    assert 'status="ERROR"' in out and "rc=1" in out


# ------------------------------------------------------------------- ficheros

@pytest.mark.asyncio
async def test_write_then_read(ctx):
    reg = build_registry()
    r = await reg.execute("write_file", {"path": "x.txt", "content": "hola"}, ctx)
    assert r.ok
    r = await reg.execute("read_file", {"path": "x.txt"}, ctx)
    assert r.ok and "hola" in r.content


@pytest.mark.asyncio
async def test_edit_requires_unique_match(ctx):
    reg = build_registry()
    await reg.execute("write_file", {"path": "d.txt", "content": "a\na\n"}, ctx)
    r = await reg.execute("edit_file", {"path": "d.txt", "old": "a", "new": "b"}, ctx)
    assert not r.ok and "veces" in (r.error or "")
    r = await reg.execute("edit_file",
                          {"path": "d.txt", "old": "a", "new": "b", "all": True}, ctx)
    assert r.ok


@pytest.mark.asyncio
async def test_grep_finds_and_reports_line(ctx):
    reg = build_registry()
    await reg.execute("write_file", {"path": "s.py", "content": "x=1\nSECRETO=2\n"}, ctx)
    r = await reg.execute("grep", {"pattern": "SECRETO", "path": "."}, ctx)
    assert r.ok and "SECRETO" in r.content and ":2:" in r.content


@pytest.mark.asyncio
async def test_unknown_tool_is_a_helpful_error(ctx):
    r = await build_registry().execute("no_existe", {}, ctx)
    assert not r.ok and "Disponibles" in (r.error or "")


@pytest.mark.asyncio
async def test_hallucinated_args_are_dropped(ctx):
    """Los modelos gratuitos inventan parámetros. No debe reventar."""
    reg = build_registry()
    r = await reg.execute("write_file",
                          {"path": "h.txt", "content": "ok", "inventado": 42}, ctx)
    assert r.ok


# ---------------------------------------------------------- deshacer (§4.2)

@pytest.mark.asyncio
async def test_undo_restores_previous_content(ctx):
    reg = build_registry()
    await reg.execute("write_file", {"path": "v.txt", "content": "original"}, ctx)
    await reg.execute("write_file", {"path": "v.txt", "content": "MODIFICADO"}, ctx)
    assert (ctx.cwd / "v.txt").read_text() == "MODIFICADO"

    assert ctx.journal.undo_last() is not None
    assert (ctx.cwd / "v.txt").read_text() == "original"


@pytest.mark.asyncio
async def test_undo_of_creation_removes_file(ctx):
    reg = build_registry()
    await reg.execute("write_file", {"path": "nuevo.txt", "content": "x"}, ctx)
    assert (ctx.cwd / "nuevo.txt").exists()
    ctx.journal.undo_last()
    assert not (ctx.cwd / "nuevo.txt").exists()


@pytest.mark.asyncio
async def test_undo_restores_deleted_file(ctx):
    reg = build_registry()
    await reg.execute("write_file", {"path": "b.txt", "content": "importante"}, ctx)
    await reg.execute("delete_path", {"path": "b.txt"}, ctx)
    assert not (ctx.cwd / "b.txt").exists()
    ctx.journal.undo_last()
    assert (ctx.cwd / "b.txt").read_text() == "importante"


@pytest.mark.asyncio
async def test_undo_whole_task(ctx):
    """El caso real: 'deshaz todo lo que acabas de hacer'."""
    reg = build_registry()
    for i in range(4):
        await reg.execute("write_file", {"path": f"f{i}.txt", "content": "x"}, ctx)
    assert ctx.journal.undo_task("t1") == 4
    assert not any((ctx.cwd / f"f{i}.txt").exists() for i in range(4))


@pytest.mark.asyncio
async def test_dry_run_mutates_nothing(ctx):
    ctx.dry_run = True
    reg = build_registry()
    r = await reg.execute("write_file", {"path": "no.txt", "content": "x"}, ctx)
    assert r.ok and "dry-run" in r.content
    assert not (ctx.cwd / "no.txt").exists()


# -------------------------------------------------------------- ejecución

@pytest.mark.asyncio
async def test_run_command_captures_output(ctx):
    r = await build_registry().execute(
        "run_command", {"command": "echo hola-magi"}, ctx)
    assert r.ok and "hola-magi" in r.content


@pytest.mark.asyncio
async def test_run_command_reports_failure(ctx):
    r = await build_registry().execute("run_command", {"command": "exit 3"}, ctx)
    assert not r.ok and r.meta["rc"] == 3


@pytest.mark.asyncio
async def test_python_exec(ctx):
    r = await build_registry().execute(
        "python_exec", {"code": "print(6*7)"}, ctx)
    assert r.ok and "42" in r.content


# ------------------------------------------------------------ perfiles de rol

def test_balthasar_cannot_write_but_can_execute():
    """No es una restricción de seguridad: es lo que le da autoridad. Puede
    ejecutar el código de Melchior y aportar evidencia, no reescribirlo."""
    b = registry_for_role("BALTHASAR")
    assert "write_file" not in b.names()
    assert "edit_file" not in b.names()
    assert "run_tests" in b.names()
    assert "read_file" in b.names()


def test_melchior_has_full_access():
    m = registry_for_role("MELCHIOR")
    assert {"write_file", "edit_file", "run_command"} <= set(m.names())


def test_casper_is_read_and_verify_only():
    c = registry_for_role("CASPER")
    assert "write_file" not in c.names() and "run_tests" in c.names()


def test_catalog_lines_stay_cheap():
    """Ninguna línea del catálogo puede dispararse: entra en cada prompt."""
    cat = build_registry().catalog()
    assert "read_file(" in cat
    assert max(len(l) for l in cat.splitlines()) < 200


def test_catalog_is_scoped_to_the_task_domain():
    """
    Lo que va al prompt NO es el catálogo completo, sino el del rol acotado por
    el enunciado. Con 30 herramientas el catálogo entero pasó de 3200
    caracteres; compactar el texto ya no daba más de sí y la respuesta correcta
    fue no ofrecer el toolchain de emuladores a quien escribe un informe.
    """
    full = len(build_registry().catalog())
    code_task = registry_for_role("MELCHIOR", "arregla el bug del scroll en App.tsx")
    emu_task = registry_for_role("MELCHIOR", "analiza el dynarec de PPSSPP")

    assert len(code_task.catalog()) < 1500, "una tarea de código no necesita 30 herramientas"
    assert len(code_task.catalog()) < full / 2
    assert "disassemble" not in code_task.names()
    assert "compose_manga_page" not in code_task.names()
    assert "disassemble" in emu_task.names()


def test_scoping_never_removes_the_core_tools():
    """Acotar por dominio no puede dejar a un agente sin poder leer ni escribir."""
    for hint in ("dibuja un manga", "analiza este binario", "escribe un informe",
                 "", "algo totalmente ambiguo"):
        names = set(registry_for_role("MELCHIOR", hint).names())
        assert {"read_file", "write_file", "run_command"} <= names, hint


def test_no_hint_offers_everything():
    """Ante la duda, catálogo completo: mejor grande que insuficiente."""
    assert len(registry_for_role("MELCHIOR", "").names()) == \
           len(build_registry().names())


# ------------------------------------------------------------ paralelismo

@pytest.mark.asyncio
async def test_tools_execute_in_parallel(ctx):
    reg = build_registry()
    await reg.execute("write_file", {"path": "p.txt", "content": "z"}, ctx)
    results = await reg.execute_many(
        [("read_file", {"path": "p.txt"}), ("list_dir", {"path": "."})], ctx)
    assert len(results) == 2 and all(r.ok for r in results)
