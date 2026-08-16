"""
Desensamblado con Capstone (Plan MAGI 9.0 §5.3).

Sin dependencias externas: Capstone es un paquete pip y cubre MIPS (PSP, PSX,
N64) y ARM (NDS, GBA, Vita, 3DS), que es todo tu abanico.

Ghidra y radare2 se detectan si están instalados y se usan para lo que
Capstone no hace —decompilación a C, xrefs globales—, pero el análisis básico
no depende de ellos.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_ARCH_MAP = {
    "mips": "CS_ARCH_MIPS", "arm": "CS_ARCH_ARM", "arm64": "CS_ARCH_ARM64",
    "x86": "CS_ARCH_X86", "ppc": "CS_ARCH_PPC", "sparc": "CS_ARCH_SPARC",
    "riscv": "CS_ARCH_RISCV",
}


@dataclass
class Instruction:
    addr: int
    mnemonic: str
    op_str: str
    size: int
    bytes_hex: str = ""

    def render(self) -> str:
        return f"0x{self.addr:08x}  {self.mnemonic:<10s} {self.op_str}"


@dataclass
class Disassembly:
    instructions: list[Instruction] = field(default_factory=list)
    arch: str = ""
    mode: str = ""
    truncated: bool = False
    error: str | None = None

    def render(self, limit: int = 200) -> str:
        if self.error:
            return f"ERROR: {self.error}"
        head = f"{len(self.instructions)} instrucciones ({self.arch} {self.mode})"
        body = "\n".join(i.render() for i in self.instructions[:limit])
        tail = "\n…" if len(self.instructions) > limit else ""
        return f"{head}\n{body}{tail}"

    def mnemonics(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for i in self.instructions:
            out[i.mnemonic] = out.get(i.mnemonic, 0) + 1
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    def branch_targets(self) -> list[int]:
        """Destinos de salto: la base para reconstruir bloques básicos."""
        out = []
        for i in self.instructions:
            if i.mnemonic.startswith(("b", "j", "call")):
                for tok in i.op_str.replace(",", " ").split():
                    if tok.startswith("0x"):
                        try:
                            out.append(int(tok, 16))
                        except ValueError:
                            pass
        return sorted(set(out))


def _capstone(arch: str, bits: int, endian: str, thumb: bool = False):
    try:
        import capstone
    except ImportError as e:
        raise RuntimeError("capstone no instalado: pip install capstone") from e

    cs_arch = getattr(capstone, _ARCH_MAP.get(arch, ""), None)
    if cs_arch is None:
        raise ValueError(f"arquitectura no soportada: {arch}")

    mode = 0
    if arch == "mips":
        mode |= capstone.CS_MODE_MIPS64 if bits == 64 else capstone.CS_MODE_MIPS32
    elif arch == "arm":
        # ARM y Thumb se entremezclan en GBA y NDS: elegir mal produce
        # desensamblado que parece válido y no lo es.
        mode |= capstone.CS_MODE_THUMB if thumb else capstone.CS_MODE_ARM
    elif arch == "arm64":
        mode |= capstone.CS_MODE_ARM
    elif arch == "x86":
        mode |= capstone.CS_MODE_64 if bits == 64 else capstone.CS_MODE_32

    mode |= (capstone.CS_MODE_BIG_ENDIAN if endian == "big"
             else capstone.CS_MODE_LITTLE_ENDIAN)

    md = capstone.Cs(cs_arch, mode)
    md.detail = False
    return md


def disassemble(data: bytes, *, arch: str = "mips", bits: int = 32,
                endian: str = "little", base: int = 0, thumb: bool = False,
                max_insns: int = 4000) -> Disassembly:
    result = Disassembly(arch=arch,
                         mode=("thumb" if thumb else "arm") if arch == "arm"
                         else f"{bits}")
    try:
        md = _capstone(arch, bits, endian, thumb)
    except Exception as e:
        result.error = str(e)
        return result

    for n, insn in enumerate(md.disasm(data, base)):
        if n >= max_insns:
            result.truncated = True
            break
        result.instructions.append(Instruction(
            insn.address, insn.mnemonic, insn.op_str, insn.size,
            insn.bytes.hex()))
    return result


def disassemble_file(path: str | Path, *, offset: int = 0, length: int = 4096,
                     console: str | None = None, **kw) -> Disassembly:
    """Desensambla un trozo de fichero, con perfil de consola si se indica."""
    from .identify import identify, profile

    p = Path(path)
    data = p.read_bytes()[offset:offset + length]

    if console:
        prof = profile(console)
        if prof:
            kw.setdefault("arch", prof.arch)
            kw.setdefault("bits", prof.bits)
            kw.setdefault("endian", prof.endian)
            kw.setdefault("base", prof.load_base + offset)
    else:
        info = identify(p)
        kw.setdefault("arch", info.arch if info.arch != "unknown" else "mips")
        kw.setdefault("bits", info.bits)
        kw.setdefault("endian", info.endian)
    return disassemble(data, **kw)


def extract_strings(data: bytes, min_len: int = 5,
                    limit: int = 500) -> list[tuple[int, str]]:
    """Cadenas ASCII. Suele ser lo primero que orienta en un firmware."""
    out, cur, start = [], [], 0
    for i, b in enumerate(data):
        if 0x20 <= b < 0x7F:
            if not cur:
                start = i
            cur.append(chr(b))
        else:
            if len(cur) >= min_len:
                out.append((start, "".join(cur)))
                if len(out) >= limit:
                    return out
            cur = []
    if len(cur) >= min_len:
        out.append((start, "".join(cur)))
    return out


# ------------------------------------------------------- externos opcionales

def available_tools() -> dict[str, bool]:
    """Qué hay instalado. El análisis básico no depende de nada de esto."""
    return {
        "capstone": _module_present("capstone"),
        "unicorn": _module_present("unicorn"),
        "ghidra": bool(shutil.which("analyzeHeadless")
                       or shutil.which("ghidraRun")),
        "radare2": bool(shutil.which("r2") or shutil.which("radare2")),
        "rizin": bool(shutil.which("rizin")),
        "objdump": bool(shutil.which("objdump")),
        "readelf": bool(shutil.which("readelf")),
    }


def _module_present(name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(name) is not None


def ghidra_decompile(path: str | Path, *, timeout: int = 900,
                     project_dir: str | Path | None = None) -> str:
    """
    Decompilación a C con Ghidra headless, si está instalado.

    No es un requisito: si falta, el resto del toolchain sigue funcionando y
    esta función lo dice en vez de fallar en silencio.
    """
    exe = shutil.which("analyzeHeadless")
    if not exe:
        return ("Ghidra no está instalado o analyzeHeadless no está en el PATH. "
                "El desensamblado con Capstone sigue disponible; para "
                "decompilación a C hace falta Ghidra (https://ghidra-sre.org).")

    import tempfile
    proj = Path(project_dir) if project_dir else Path(tempfile.mkdtemp(
        prefix="magi-ghidra-"))
    proj.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            [exe, str(proj), "magi_tmp", "-import", str(path),
             "-analysisTimeoutPerFile", str(timeout // 2), "-deleteProject"],
            capture_output=True, text=True, timeout=timeout)
        out = proc.stdout or proc.stderr
        return out[-20000:] if out else "Ghidra terminó sin salida."
    except subprocess.TimeoutExpired:
        return f"Ghidra excedió {timeout}s. Prueba con un binario más pequeño."
    except Exception as e:
        return f"Ghidra falló: {e}"


def r2_analyze(path: str | Path, commands: list[str] | None = None,
               timeout: int = 300) -> str:
    """Análisis con radare2/rizin si están instalados."""
    exe = shutil.which("r2") or shutil.which("radare2") or shutil.which("rizin")
    if not exe:
        return ("radare2/rizin no instalado. Capstone cubre el desensamblado; "
                "r2 aporta xrefs globales y análisis de funciones.")
    cmds = commands or ["aaa", "afl", "iI"]
    try:
        proc = subprocess.run(
            [exe, "-q", "-c", "; ".join(cmds), str(path)],
            capture_output=True, text=True, timeout=timeout)
        return proc.stdout or proc.stderr
    except subprocess.TimeoutExpired:
        return f"r2 excedió {timeout}s"
    except Exception as e:
        return f"r2 falló: {e}"
