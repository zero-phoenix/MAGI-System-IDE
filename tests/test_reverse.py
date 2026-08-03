"""
Toolchain de ingeniería inversa y emuladores (§5.3).

Todo funciona con capstone + unicorn (paquetes pip). Ghidra y radare2 se usan
si están, y si no, el resto sigue funcionando y lo dice.
"""
import pytest

from magi.core.tools import build_registry, registry_for_role
from magi.modules.reverse.disasm import (
    available_tools, disassemble, extract_strings,
)
from magi.modules.reverse.emulate import differential_test, emulate
from magi.modules.reverse.identify import CONSOLES, identify, profile
from magi.modules.reverse.matrix import (
    Reuse, analyze_port, compare_consoles, suggest_port_path,
)

def _mips_le(*words: int) -> bytes:
    """
    Codifica palabras MIPS en little-endian.

    La primera versión de este fichero las escribía a mano en hex y me equivoqué
    de orden de bytes en una: `lui $v0,0` es 0x3C020000, o sea 00 00 02 3c, y yo
    puse 00 00 3c 02. Capstone lo rechazó (correcto) pero Unicorn ejecutó la
    basura sin quejarse y el test de emulación pasaba igual. Construirlas desde
    la palabra evita el error entero.
    """
    return b"".join(w.to_bytes(4, "little") for w in words)


# Fragmentos MIPS reales (little-endian, como PSP/PSX)
MIPS_PROLOGUE = _mips_le(0x27BDFFE0,       # addiu $sp, $sp, -32
                         0xAFBF001C)       # sw    $ra, 28($sp)
MIPS_LOAD_ADD = _mips_le(0x3C020000,       # lui   $v0, 0
                         0x34421234,       # ori   $v0, $v0, 0x1234
                         0x24420001)       # addiu $v0, $v0, 1


# ------------------------------------------------------------ desensamblado

def test_disassembles_mips():
    d = disassemble(MIPS_PROLOGUE, arch="mips", base=0x08804000)
    assert d.error is None
    assert len(d.instructions) == 2
    assert d.instructions[0].mnemonic == "addiu"
    assert d.instructions[0].addr == 0x08804000


def test_disassembles_arm_and_thumb_differently():
    """
    En GBA y NDS ARM y Thumb se entremezclan. Elegir mal el modo produce
    desensamblado que PARECE válido y no lo es — el fallo más traicionero.
    """
    code = bytes.fromhex("0400a0e1")
    arm = disassemble(code, arch="arm", thumb=False)
    thumb = disassemble(code, arch="arm", thumb=True)
    assert arm.mode == "arm" and thumb.mode == "thumb"
    assert [i.mnemonic for i in arm.instructions] != \
           [i.mnemonic for i in thumb.instructions]


def test_endianness_changes_the_decoding():
    """N64 es big-endian y casi todo lo demás little: no es un detalle."""
    le = disassemble(MIPS_PROLOGUE, arch="mips", endian="little")
    be = disassemble(MIPS_PROLOGUE, arch="mips", endian="big")
    assert [i.mnemonic for i in le.instructions] != \
           [i.mnemonic for i in be.instructions]


def test_unsupported_arch_reports_instead_of_crashing():
    d = disassemble(b"\x00" * 8, arch="inventada")
    assert d.error and "no soportada" in d.error


def test_mnemonic_histogram():
    d = disassemble(MIPS_LOAD_ADD, arch="mips")
    assert set(d.mnemonics()) >= {"lui", "ori", "addiu"}


def test_extract_strings():
    data = b"\x00\x01PPSSPP v1.17\x00\xff\xfeGraphics Engine\x00"
    found = extract_strings(data, min_len=5)
    assert any("PPSSPP" in s for _, s in found)
    assert any("Graphics" in s for _, s in found)


def test_toolchain_status_is_honest_about_what_is_missing():
    tools = available_tools()
    assert tools["capstone"] and tools["unicorn"]
    assert "ghidra" in tools and "radare2" in tools


# ------------------------------------------------------------ identificación

def test_identifies_an_elf(tmp_path):
    elf = bytearray(64)
    elf[0:4] = b"\x7fELF"
    elf[4] = 1          # 32 bits
    elf[5] = 1          # little-endian
    elf[16:18] = (2).to_bytes(2, "little")
    elf[18:20] = (8).to_bytes(2, "little")     # EM_MIPS
    elf[24:28] = (0x08804000).to_bytes(4, "little")
    p = tmp_path / "test.elf"
    p.write_bytes(bytes(elf))

    info = identify(p)
    assert info.format == "ELF" and info.arch == "mips"
    assert info.entry == 0x08804000
    assert info.console == "psp", "la base de carga debería delatar la PSP"


def test_identifies_an_nds_header(tmp_path):
    data = bytearray(0x400)
    data[0xC0:0xC4] = b"\x24\xff\xae\x51"      # logo de Nintendo
    p = tmp_path / "juego.nds"
    p.write_bytes(bytes(data))

    info = identify(p)
    assert info.format == "NDS" and info.console == "nds"
    assert info.confidence > 0.9


def test_raw_dump_says_what_it_needs(tmp_path):
    p = tmp_path / "dump.bin"
    p.write_bytes(bytes(range(256)) * 4)
    info = identify(p)
    assert any("consola" in n for n in info.notes)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        identify("/no/existe.bin")


def test_console_profiles_have_the_data_a_port_needs():
    for cid, p in CONSOLES.items():
        assert p.arch and p.endian in ("little", "big")
        assert p.bits in (32, 64)
        assert p.formats, f"{cid} sin formatos declarados"


def test_psp_profile_is_accurate():
    p = profile("psp")
    assert "MIPS" in p.cpu and p.arch == "mips" and p.endian == "little"
    assert not p.gpu_programmable
    assert "VFPU" in p.notes


def test_n64_is_big_endian():
    assert profile("n64").endian == "big"


# ------------------------------------------------------------ emulación

def test_fixtures_decode_to_the_intended_instructions():
    """
    Guarda sobre los propios fixtures. Si los bytes están mal codificados,
    Unicorn puede ejecutarlos igual y dar un resultado que parece correcto —
    me pasó al escribir este fichero.
    """
    d = disassemble(MIPS_LOAD_ADD, arch="mips", base=0x1000)
    assert [i.mnemonic for i in d.instructions] == ["lui", "ori", "addiu"]
    d = disassemble(MIPS_PROLOGUE, arch="mips")
    assert [i.mnemonic for i in d.instructions] == ["addiu", "sw"]


def test_emulates_mips_and_reads_registers():
    r = emulate(MIPS_LOAD_ADD, arch="mips", base=0x1000, max_instructions=20)
    assert r.ok, r.error
    assert r.instructions_run == 3
    assert r.registers["V0"] == 0x1235, "lui+ori+addiu debe dejar 0x1235 en $v0"


def test_registers_are_read_from_the_right_module():
    """
    Las constantes de unicorn viven en submódulos (unicorn.mips_const), no en
    el paquete raíz. Buscarlas en `unicorn` devolvía None y el volcado salía
    vacío sin que nada fallara: un fallo silencioso.
    """
    r = emulate(MIPS_LOAD_ADD, arch="mips")
    assert r.registers, "los registros no pueden salir vacíos"
    assert "PC" in r.registers and "SP" in r.registers


def test_differential_test_locates_the_divergence():
    """El caso real: tu dynarec da un valor y el hardware otro."""
    out = differential_test(MIPS_LOAD_ADD, {"V0": 0x1234}, arch="mips")
    assert "DIVERGENCIA" in out and "0x00001235" in out


def test_differential_test_confirms_a_match():
    out = differential_test(MIPS_LOAD_ADD, {"V0": 0x1235}, arch="mips")
    assert "Coincide" in out


def test_bad_arch_does_not_crash():
    r = emulate(b"\x00\x00\x00\x00", arch="inventada")
    assert not r.ok and "no soportada" in r.error


# ------------------------------------------------------- portabilidad

def test_psp_to_vita_flags_the_gpu_as_irreducible():
    """
    Lo que de verdad cuesta ese port no es el dynarec: es que un pipeline fijo
    no se traduce a shaders programables.
    """
    a = analyze_port("psp", "vita")
    gpu = next(i for i in a.items if i.subsystem == "gpu")
    assert gpu.verdict is Reuse.HARD
    assert "pipeline fijo" in gpu.reason


def test_same_isa_makes_the_dynarec_adaptable():
    a = analyze_port("nds", "vita")     # ARM -> ARM
    dyn = next(i for i in a.items if i.subsystem == "dynarec")
    assert dyn.verdict is Reuse.ADAPT


def test_different_isa_forces_a_new_dynarec():
    a = analyze_port("psp", "nds")      # MIPS -> ARM
    dyn = next(i for i in a.items if i.subsystem == "dynarec")
    assert dyn.verdict is Reuse.REPLACE


def test_endian_change_is_irreducible():
    """N64 (big) a cualquier otra: afecta a cada acceso a memoria."""
    a = analyze_port("n64", "psp")
    mmu = next(i for i in a.items if i.subsystem == "mmu")
    assert mmu.verdict is Reuse.HARD
    assert "endian" in mmu.reason


def test_cpu_count_mismatch_is_irreducible():
    a = analyze_port("nds", "gba")      # dos CPUs -> una
    sched = next(i for i in a.items if i.subsystem == "planificador")
    assert sched.verdict is Reuse.HARD


def test_frontend_is_always_reusable():
    a = analyze_port("psp", "vita")
    fe = next(i for i in a.items if i.subsystem == "frontend")
    assert fe.verdict is Reuse.DIRECT


def test_reuse_ratio_is_bounded():
    for src in ("psp", "nds", "n64"):
        for tgt in ("vita", "3ds"):
            a = analyze_port(src, tgt)
            assert 0.0 <= a.reuse_ratio <= 1.0


def test_unknown_console_raises():
    with pytest.raises(ValueError):
        analyze_port("psp", "dreamcast")


def test_suggested_base_prefers_architectural_proximity():
    """
    Para Vita (ARMv7 + shaders) la mejor base es 3DS (ARMv6K + shaders), no
    PSP (MIPS + pipeline fijo), aunque PSP sea el emulador más conocido.
    """
    out = suggest_port_path("vita")
    lines = [l for l in out.splitlines() if "reutilización" in l]
    assert lines and "3DS" in lines[0]


def test_comparison_table_has_the_decisive_rows():
    out = compare_consoles(["psp", "nds", "vita"])
    for row in ("CPU", "ISA", "RAM", "GPU", "Shaders", "Base carga"):
        assert row in out
    assert "VFPU" in out


# ------------------------------------------------------------ cableado

def test_reverse_tools_are_in_the_swarm_catalog():
    """
    Sin este enganche, todo magi/modules/reverse/ sería código correcto que
    ningún agente puede invocar — el error que ya cometí tres veces.
    """
    names = set(build_registry().names())
    for t in ("binary_identify", "disassemble", "emulate_code",
              "analyze_port", "compare_consoles", "suggest_port_base",
              "differential_test", "binary_strings", "console_profile"):
        assert t in names, f"{t} no está en el catálogo del enjambre"


def test_role_profiles_include_reverse_tools():
    m = set(registry_for_role("MELCHIOR").names())
    b = set(registry_for_role("BALTHASAR").names())
    c = set(registry_for_role("CASPER").names())

    assert "disassemble" in m and "emulate_code" in m
    assert "emulate_code" in b, "Balthasar debe poder ejecutar para refutar"
    assert "analyze_port" in c, "el árbitro debe poder comprobar arquitecturas"
    assert "write_file" not in b


def test_catalog_stays_within_a_free_provider_window():
    """El catálogo entra en cada prompt: no puede dispararse."""
    assert len(build_registry().catalog()) < 4000


@pytest.mark.asyncio
async def test_tools_execute_through_the_registry(tmp_path):
    from magi.core.tools import ToolContext, WriteJournal
    ctx = ToolContext(task_id="t", cwd=tmp_path,
                      journal=WriteJournal("t", tmp_path / ".j"))
    reg = build_registry()

    r = await reg.execute("console_profile", {"console": "psp"}, ctx)
    assert r.ok and "MIPS" in r.content

    r = await reg.execute("analyze_port", {"source": "psp", "target": "vita"}, ctx)
    assert r.ok and "irreducible" in r.content.lower()

    r = await reg.execute("emulate_code",
                          {"hex_code": MIPS_LOAD_ADD.hex(), "arch": "mips"}, ctx)
    assert r.ok and "V0=0x00001235" in r.content

    r = await reg.execute("console_profile", {"console": "dreamcast"}, ctx)
    assert not r.ok and "Disponibles" in r.error
