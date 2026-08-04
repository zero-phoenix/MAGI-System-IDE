"""
Indexado y contraste de código de emuladores (§5.3).

`analyze_port` compara CONSOLAS desde sus perfiles de hardware. Esto compara
EMULADORES desde su código: dónde está el dynarec, cuántas líneas tiene el
rasterizador, qué subsistema concentra el trabajo de verdad.
"""
import pytest

from magi.core.tools import ToolContext, WriteJournal, build_registry
from magi.modules.reverse.corpus import (
    CorpusIndex, compare_corpora, index_source_tree, locate_subsystem,
    subsystem_names,
)


def _make_emulator(root, name, layout):
    """Construye un árbol de fuentes sintético con la forma de un emulador real."""
    for rel, body in layout.items():
        p = root / name / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    return root / name


PSP_LIKE = {
    "Core/MIPS/MIPSInt.cpp": "\n".join(
        ["void Interpret(u32 op) {", "  switch (op >> 26) {"]
        + [f"    case 0x{i:02x}: decodeSpecial(op); break;" for i in range(40)]
        + ["  }", "}"]),
    "Core/MIPS/JitCommon/JitBlockCache.cpp": "\n".join(
        ["struct IRBlock {};", "void EmitMovReg(int a, int b) {}"]
        + ["// regalloc" for _ in range(300)]),
    "Core/MIPS/x86/CompALU.cpp": "\n".join(
        ["void EmitAdd() {}", "// code_block dispatch"] + ["x" for _ in range(200)]),
    "GPU/GLES/GPU_GLES.cpp": "\n".join(
        ["void Draw() { glDrawArrays(); }", "// texture, shader, framebuffer"]
        + ["// rasteriz" for _ in range(500)]),
    "Core/HLE/sceKernelThread.cpp": "\n".join(
        ["int sceKernelCreateThread() { return 0; }"] + ["// nid" for _ in range(400)]),
    "Core/MemMap.cpp": "\n".join(
        ["u32 Read32(u32 addr) { return 0; }", "void Write32(u32 a, u32 v) {}"]
        + ["// memory_map" for _ in range(150)]),
    "Core/CoreTiming.cpp": "\n".join(
        ["void ScheduleEvent(int c) {}", "int downcount;"] + ["y" for _ in range(90)]),
    "Core/SaveState.cpp": "\n".join(
        ["void DoState(PointerWrap &p) {}"] + ["// serialize" for _ in range(120)]),
    "UI/GameSettingsScreen.cpp": "\n".join(
        ["// ImGui::Begin", "// menu_item"] + ["z" for _ in range(600)]),
    "Core/Loaders.cpp": "\n".join(
        ["bool LoadROM() { return true; }", "// ISO9660, magic"] + ["w" for _ in range(80)]),
}

NDS_LIKE = {
    "src/ARMInterpreter.cpp": "\n".join(
        ["void Execute(u32 op) {"] + [f"  case 0x{i:03x}: opcode(op);" for i in range(60)]
        + ["}"]),
    "src/ARMJIT_A64/ARMJIT_Compiler.cpp": "\n".join(
        ["void EmitLoad() {}", "// register_alloc, code_block"]
        + ["a" for _ in range(1500)]),
    "src/GPU3D_Soft.cpp": "\n".join(
        ["// rasteriz, vertex, texture"] + ["b" for _ in range(200)]),
    "src/SPU.cpp": "\n".join(
        ["// ADPCM mixer sample_rate", "int channel[16];"] + ["c" for _ in range(140)]),
    "src/NDSCart.cpp": "\n".join(["// LoadROM magic"] + ["d" for _ in range(70)]),
    "src/Memory.cpp": "\n".join(
        ["u32 Read32(u32 a){return 0;}", "// page_table tlb"] + ["e" for _ in range(300)]),
    "src/Savestate.cpp": "\n".join(["// serialize save_state"] + ["f" for _ in range(60)]),
    "src/frontend/qt_sdl/main.cpp": "\n".join(
        ["// QWidget setWindowTitle"] + ["g" for _ in range(400)]),
}


@pytest.fixture
def corpora(tmp_path):
    a = _make_emulator(tmp_path, "PPSSPP-like", PSP_LIKE)
    b = _make_emulator(tmp_path, "melonDS-like", NDS_LIKE)
    return (index_source_tree(a, name="PPSSPP"),
            index_source_tree(b, name="melonDS"))


# ------------------------------------------------------------- clasificación

def test_indexes_and_counts(corpora):
    psp, _ = corpora
    assert psp.total_files == len(PSP_LIKE)
    assert psp.total_lines > 2000
    assert psp.name == "PPSSPP"


def test_classifies_the_dynarec(corpora):
    psp, _ = corpora
    assert "dynarec" in psp.subsystems
    files = [e.path for e in psp.files_for("dynarec")]
    assert any("Jit" in f or "CompALU" in f for f in files)


def test_path_outweighs_incidental_content(corpora):
    """
    Un fichero bajo GPU/ es del subsistema gráfico aunque mencione 'cycles' de
    pasada. Sin ese peso, la clasificación se va con cualquier palabra suelta.
    """
    psp, _ = corpora
    gpu_files = [e.path for e in psp.files_for("gpu")]
    assert any("GPU/" in f for f in gpu_files)


def test_classifies_hle_and_frontend(corpora):
    psp, _ = corpora
    assert "hle_sistema" in psp.subsystems
    assert "frontend" in psp.subsystems
    assert any("sceKernel" in e.path or "HLE" in e.path
               for e in psp.files_for("hle_sistema"))


def test_every_rule_has_a_name_and_description():
    from magi.modules.reverse.corpus import RULES
    names = subsystem_names()
    assert len(names) == len(set(names)), "subsistemas duplicados"
    assert all(r.description for r in RULES)


def test_skips_vendored_and_build_dirs(tmp_path):
    root = tmp_path / "emu"
    (root / "src").mkdir(parents=True)
    (root / "src" / "cpu.cpp").write_text("case 0x01: opcode(x);", encoding="utf-8")
    for skipped in ("third_party", "build", "node_modules"):
        d = root / skipped
        d.mkdir()
        (d / "enorme.cpp").write_text("x\n" * 5000, encoding="utf-8")

    idx = index_source_tree(root)
    assert idx.total_files == 1, "no debe contar dependencias ni artefactos"


def test_ignores_non_source_files(tmp_path):
    root = tmp_path / "e"
    root.mkdir()
    (root / "a.cpp").write_text("case 0x01:", encoding="utf-8")
    (root / "README.md").write_text("x" * 1000, encoding="utf-8")
    (root / "icono.png").write_bytes(b"\x89PNG" + bytes(500))
    assert index_source_tree(root).total_files == 1


def test_not_a_directory():
    with pytest.raises(NotADirectoryError):
        index_source_tree(__file__)


def test_binary_garbage_does_not_crash(tmp_path):
    root = tmp_path / "e"
    root.mkdir()
    (root / "raro.cpp").write_bytes(bytes(range(256)) * 50)
    idx = index_source_tree(root)
    assert idx.total_files == 1


# --------------------------------------------------------------- localizar

def test_locate_subsystem_cites_real_files(corpora):
    psp, _ = corpora
    out = locate_subsystem(psp, "dynarec")
    assert "líneas" in out
    assert ".cpp" in out
    assert "total del subsistema" in out


def test_locate_reports_signals(corpora):
    psp, _ = corpora
    out = locate_subsystem(psp, "gpu")
    assert "señales:" in out


def test_locate_unknown_subsystem_lists_what_exists(corpora):
    psp, _ = corpora
    out = locate_subsystem(psp, "inventado")
    assert "No se localizó" in out and "Subsistemas detectados" in out


# --------------------------------------------------------------- comparar

def test_comparison_uses_real_line_counts(corpora):
    psp, nds = corpora
    out = compare_corpora(psp, nds).render()
    assert "PPSSPP" in out and "melonDS" in out
    assert "dynarec" in out
    assert "total" in out


def test_comparison_flags_where_the_work_is(corpora):
    """
    El dynarec de melonDS-like tiene ~5x más líneas: la lectura debe decirlo,
    porque es trabajo que la tabla de consolas no muestra.
    """
    psp, nds = corpora
    out = compare_corpora(psp, nds).render()
    assert "Lectura:" in out
    assert "dynarec" in out.split("Lectura:")[1]


def test_comparison_notes_missing_subsystems(tmp_path):
    a = _make_emulator(tmp_path, "con_audio", {
        "src/SPU.cpp": "// ADPCM mixer sample_rate\n" + "x\n" * 100})
    b = _make_emulator(tmp_path, "sin_audio", {
        "src/gpu.cpp": "// rasteriz texture shader\n" + "y\n" * 100})
    out = compare_corpora(index_source_tree(a, name="A"),
                          index_source_tree(b, name="B")).render()
    assert "solo A" in out or "solo B" in out


# ---------------------------------------------------------------- cableado

def test_corpus_tools_are_in_the_catalog():
    names = set(build_registry().names())
    for t in ("index_emulator", "locate_subsystem", "compare_emulators"):
        assert t in names, f"{t} no está conectado al enjambre"


@pytest.mark.asyncio
async def test_tools_end_to_end(tmp_path):
    _make_emulator(tmp_path, "EmuA", PSP_LIKE)
    _make_emulator(tmp_path, "EmuB", NDS_LIKE)
    ctx = ToolContext(task_id="t", cwd=tmp_path,
                      journal=WriteJournal("t", tmp_path / ".j"))
    reg = build_registry()

    r = await reg.execute("index_emulator", {"path": "EmuA", "name": "EmuA"}, ctx)
    assert r.ok and r.meta["files"] == len(PSP_LIKE)

    r = await reg.execute("locate_subsystem",
                          {"emulator": "EmuA", "subsystem": "dynarec"}, ctx)
    assert r.ok and ".cpp" in r.content

    # comparar antes de indexar el segundo debe avisar, no fallar en silencio
    r = await reg.execute("compare_emulators", {"a": "EmuA", "b": "EmuB"}, ctx)
    assert not r.ok and "sin indexar" in r.error

    await reg.execute("index_emulator", {"path": "EmuB", "name": "EmuB"}, ctx)
    r = await reg.execute("compare_emulators", {"a": "EmuA", "b": "EmuB"}, ctx)
    assert r.ok and "Lectura:" in r.content


@pytest.mark.asyncio
async def test_indexing_a_non_repo_says_so(tmp_path):
    (tmp_path / "vacio").mkdir()
    ctx = ToolContext(task_id="t", cwd=tmp_path,
                      journal=WriteJournal("t", tmp_path / ".j"))
    r = await build_registry().execute(
        "index_emulator", {"path": "vacio"}, ctx)
    assert not r.ok and "código fuente" in r.error


def test_arch_backend_dirs_are_dynarec_not_interpreter(corpora):
    """
    Encontrado en la demo: Core/MIPS/x86/CompALU.cpp salía como intérprete
    porque "core/mips" coincidía con el patrón de CPU. En PPSSPP ese fichero ES
    el dynarec — los backends de emisión viven bajo un directorio de
    arquitectura dentro del de CPU.
    """
    psp, _ = corpora
    dynarec = [e.path for e in psp.files_for("dynarec")]
    assert any("CompALU" in f for f in dynarec), (
        f"CompALU.cpp debe ser dynarec, no intérprete. dynarec={dynarec}")
    interp = [e.path for e in psp.files_for("cpu_interprete")]
    assert any("MIPSInt" in f for f in interp), "el intérprete real sigue ahí"
    assert not any("x86" in f for f in interp)
