"""
Identificación de binarios y perfiles de consola (Plan MAGI 9.0 §5.3).

Antes de desensamblar nada hay que saber QUÉ es: arquitectura, endianness,
modo (ARM/Thumb), y dónde empieza el código. Equivocarse en cualquiera de esas
cuatro cosas produce desensamblado que parece válido y no lo es — el modo de
fallo más traicionero de la ingeniería inversa.

Los perfiles de consola están para eso: un dump de PSP es MIPS32 little-endian
con base 0x08800000, y saberlo de antemano evita adivinar.
"""
from __future__ import annotations

import logging
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConsoleProfile:
    """Datos duros de una consola. Lo que hace falta para emular o portar."""
    id: str
    name: str
    cpu: str
    arch: str                    # capstone: "mips" | "arm" | "arm64" | "x86"
    bits: int
    endian: str                  # "little" | "big"
    extra_cpus: list[str] = field(default_factory=list)
    ram_mb: float = 0.0
    gpu: str = ""
    gpu_programmable: bool = False   # ¿shaders o pipeline fijo?
    load_base: int = 0
    formats: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


# Perfiles de las consolas que más te interesan, más las vecinas útiles para
# comparar. Los datos son los que condicionan un port real.
CONSOLES: dict[str, ConsoleProfile] = {
    "psp": ConsoleProfile(
        "psp", "PlayStation Portable", "Allegrex (MIPS32 R4000)", "mips", 32,
        "little", ["Media Engine (MIPS32)"], 32.0,
        "Graphics Engine (pipeline fijo)", False, 0x08804000,
        ["ELF", "PBP", "ISO", "CSO", "PRX"],
        "VFPU de 128 bits propio: no tiene equivalente directo en ARM y suele "
        "ser el mayor coste de un port."),
    "nds": ConsoleProfile(
        "nds", "Nintendo DS", "ARM946E-S (ARMv5TE)", "arm", 32, "little",
        ["ARM7TDMI (ARMv4T)"], 4.0,
        "2D engine x2 + 3D pipeline fijo", False, 0x02000000,
        ["NDS", "SRL"],
        "DOS CPUs con memoria compartida y arbitraje: la sincronización entre "
        "ARM9 y ARM7 es el problema central, no la emulación de cada una."),
    "vita": ConsoleProfile(
        "vita", "PlayStation Vita", "ARM Cortex-A9 (ARMv7-A, NEON)", "arm", 32,
        "little", ["Cortex-A9 x4"], 512.0,
        "PowerVR SGX543MP4+ (shaders programables)", True, 0x81000000,
        ["SELF", "VPK", "SUPRX"],
        "MMU real y shaders programables: casi nada del backend gráfico de una "
        "consola de pipeline fijo se reutiliza."),
    "gba": ConsoleProfile(
        "gba", "Game Boy Advance", "ARM7TDMI (ARMv4T)", "arm", 32, "little",
        [], 0.25, "2D por hardware", False, 0x08000000, ["GBA", "AGB"],
        "ARM y Thumb entremezclados; detectar el modo por sección es esencial."),
    "psx": ConsoleProfile(
        "psx", "PlayStation", "MIPS R3000A", "mips", 32, "little", [], 2.0,
        "GPU + GTE (pipeline fijo)", False, 0x80010000, ["BIN", "EXE", "PSF"],
        "Sin FPU: la GTE hace la geometría en enteros."),
    "n64": ConsoleProfile(
        "n64", "Nintendo 64", "MIPS R4300i", "mips", 64, "big", ["RSP"], 4.0,
        "RCP (RSP + RDP), microcódigo", False, 0x80000000, ["Z64", "N64", "V64"],
        "BIG-ENDIAN: casi todos los demás objetivos son little-endian y eso "
        "cambia cada acceso a memoria."),
    "3ds": ConsoleProfile(
        "3ds", "Nintendo 3DS", "ARM11 MPCore (ARMv6K)", "arm", 32, "little",
        ["ARM9 (ARMv5TE)"], 128.0, "PICA200 (shaders programables)", True,
        0x00100000, ["3DS", "CIA", "CXI"],
        "Puente natural entre NDS y Vita: comparte familia ARM con ambas."),
}


@dataclass
class BinaryInfo:
    path: str
    size: int
    format: str = "raw"          # ELF | PE | Mach-O | NDS | raw
    arch: str = "unknown"
    bits: int = 32
    endian: str = "little"
    entry: int = 0
    console: str | None = None
    confidence: float = 0.0
    sections: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [f"{Path(self.path).name} — {self.size:,} bytes",
                 f"formato: {self.format} · arquitectura: {self.arch} "
                 f"{self.bits} bits {self.endian}-endian"]
        if self.entry:
            lines.append(f"punto de entrada: 0x{self.entry:08x}")
        if self.console:
            p = CONSOLES[self.console]
            lines.append(f"consola probable: {p.name} "
                         f"(confianza {self.confidence:.0%})")
            lines.append(f"  CPU: {p.cpu}" +
                         (f" + {', '.join(p.extra_cpus)}" if p.extra_cpus else ""))
            if p.notes:
                lines.append(f"  a tener en cuenta: {p.notes}")
        if self.sections:
            lines.append(f"secciones ({len(self.sections)}): " +
                         ", ".join(s["name"] for s in self.sections[:10]))
        lines += [f"  {n}" for n in self.notes]
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        d = dict(self.__dict__)
        if self.console:
            d["console_profile"] = CONSOLES[self.console].to_dict()
        return d


_EM_TO_ARCH = {
    0x02: ("sparc", 32), 0x03: ("x86", 32), 0x08: ("mips", 32),
    0x14: ("ppc", 32), 0x15: ("ppc", 64), 0x28: ("arm", 32),
    0x3E: ("x86", 64), 0xB7: ("arm64", 64), 0xF3: ("riscv", 64),
}


ELF_MIN_HEADER = 52          # tamaño mínimo de una cabecera ELF32 válida


def _parse_elf(data: bytes, info: BinaryInfo) -> None:
    info.format = "ELF"
    # Un dump parcial o una descarga a medias tiene la firma \x7fELF y nada
    # más. Sin esta guarda, struct.unpack_from lanzaba struct.error y tumbaba
    # la herramienta en vez de informar del truncamiento.
    if len(data) < ELF_MIN_HEADER:
        info.notes.append(
            f"cabecera ELF truncada: {len(data)} bytes de {ELF_MIN_HEADER} "
            f"mínimos. ¿Descarga incompleta o volcado parcial?")
        if len(data) > 5:
            info.bits = 64 if data[4] == 2 else 32
            info.endian = "big" if data[5] == 2 else "little"
        return
    info.bits = 64 if data[4] == 2 else 32
    info.endian = "big" if data[5] == 2 else "little"
    fmt = ">" if info.endian == "big" else "<"
    e_machine = struct.unpack_from(fmt + "H", data, 18)[0]
    arch, bits = _EM_TO_ARCH.get(e_machine, ("unknown", info.bits))
    info.arch = arch
    if info.bits == 64:
        info.entry = struct.unpack_from(fmt + "Q", data, 24)[0]
    else:
        info.entry = struct.unpack_from(fmt + "I", data, 24)[0]

    # Tabla de secciones (nombres): útil para localizar .text
    try:
        off = 32 if info.bits == 32 else 40
        e_shoff = struct.unpack_from(fmt + ("I" if info.bits == 32 else "Q"),
                                     data, off)[0]
        base = 46 if info.bits == 32 else 58
        e_shentsize, e_shnum, e_shstrndx = struct.unpack_from(
            fmt + "HHH", data, base)
        if e_shoff and e_shnum and e_shoff < len(data):
            str_off = e_shoff + e_shstrndx * e_shentsize
            strtab_off = struct.unpack_from(
                fmt + ("I" if info.bits == 32 else "Q"), data,
                str_off + (16 if info.bits == 32 else 24))[0]
            for i in range(min(e_shnum, 60)):
                sh = e_shoff + i * e_shentsize
                if sh + e_shentsize > len(data):
                    break
                name_off = struct.unpack_from(fmt + "I", data, sh)[0]
                end = data.find(b"\0", strtab_off + name_off)
                name = data[strtab_off + name_off:end].decode(
                    "ascii", errors="replace")
                addr = struct.unpack_from(
                    fmt + ("I" if info.bits == 32 else "Q"), data,
                    sh + (12 if info.bits == 32 else 16))[0]
                size = struct.unpack_from(
                    fmt + ("I" if info.bits == 32 else "Q"), data,
                    sh + (20 if info.bits == 32 else 32))[0]
                if name:
                    info.sections.append(
                        {"name": name, "addr": addr, "size": size})
    except Exception as e:
        info.notes.append(f"tabla de secciones ilegible: {e}")


def _guess_console(info: BinaryInfo, data: bytes) -> None:
    """Heurística por arquitectura, endianness y firmas conocidas."""
    scores: dict[str, float] = {}

    # Firma de cabecera NDS: el logo de Nintendo está en 0xC0
    if len(data) > 0x200 and data[0xC0:0xC4] == b"\x24\xff\xae\x51":
        info.format, info.arch = "NDS", "arm"
        scores["nds"] = 0.95

    if b"PSP" in data[:0x400] or b"~PSP" in data[:16]:
        scores["psp"] = scores.get("psp", 0) + 0.6
    if b"SCE" in data[:16] or b"\x00PSF" in data[:8]:
        scores["vita"] = scores.get("vita", 0) + 0.4

    for cid, p in CONSOLES.items():
        if p.arch != info.arch or p.endian != info.endian:
            continue
        s = scores.get(cid, 0.0) + 0.3
        if info.entry and abs(info.entry - p.load_base) < 0x1000000:
            s += 0.35
            info.notes.append(
                f"punto de entrada cerca de la base de carga de {p.name}")
        scores[cid] = s

    if scores:
        best = max(scores, key=scores.get)
        info.console = best
        info.confidence = min(scores[best], 0.99)


def identify(path: str | Path) -> BinaryInfo:
    """
    Identifica un binario. No requiere Ghidra ni radare2.

    Tolera ficheros truncados y corruptos: informa de lo que puede y dice qué
    le falta, en vez de lanzar una excepción. Un firmware a medio descargar es
    un caso normal, no un error del programa.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    data = p.read_bytes()
    info = BinaryInfo(path=str(p), size=len(data))
    if len(data) < 16:
        info.notes.append("fichero demasiado pequeño para identificar")
        return info

    if data[:4] == b"\x7fELF":
        _parse_elf(data, info)
    elif data[:2] == b"MZ":
        info.format = "PE"
        try:
            pe = struct.unpack_from("<I", data, 0x3C)[0]
            if pe + 6 > len(data):
                raise ValueError("cabecera PE fuera del fichero")
            machine = struct.unpack_from("<H", data, pe + 4)[0]
            info.arch, info.bits = {
                0x014c: ("x86", 32), 0x8664: ("x86", 64),
                0x01c0: ("arm", 32), 0xaa64: ("arm64", 64),
            }.get(machine, ("unknown", 32))
        except Exception as e:
            info.notes.append(f"cabecera PE ilegible: {e}")
    elif data[:4] in (b"\xfe\xed\xfa\xce", b"\xcf\xfa\xed\xfe"):
        info.format = "Mach-O"
    elif len(data) > 0x200 and data[0xC0:0xC4] == b"\x24\xff\xae\x51":
        info.format, info.arch = "NDS", "arm"
    else:
        info.notes.append(
            "formato sin cabecera reconocible: probablemente un dump crudo. "
            "Indica la consola con `console=` para fijar arquitectura y base.")

    _guess_console(info, data)
    return info


def profile(console_id: str) -> ConsoleProfile | None:
    return CONSOLES.get(console_id.lower())


def list_consoles() -> list[str]:
    return sorted(CONSOLES)
