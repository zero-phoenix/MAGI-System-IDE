"""
Herramientas de ingeniería inversa para el enjambre (Plan MAGI 9.0 §5.3).

Sin esto, todo el módulo `reverse/` sería andamiaje: código correcto que ningún
agente puede invocar. Es el error que ya cometí tres veces en esta
reconstrucción, así que aquí el registro va primero.

Con estas herramientas, Melchior puede DESENSAMBLAR un firmware en vez de
proponer un plan para desensamblarlo, y Balthasar puede EJECUTAR un fragmento
para comprobar si la afirmación de Melchior sobre él es cierta.
"""
from __future__ import annotations

import logging
from pathlib import Path

from ...core.tools.registry import ToolRegistry, ToolResult

logger = logging.getLogger(__name__)

MAX_SLICE = 256 * 1024


def register_reverse_tools(reg: ToolRegistry) -> ToolRegistry:
    """Añade el toolchain de RE a un registro existente."""

    # ------------------------------------------------------------ identificar

    @reg.tool("binary_identify",
              "Identifica un binario: formato, arquitectura, endianness, punto "
              "de entrada y consola probable. SIEMPRE antes de desensamblar.",
              {"type": "object", "properties": {"path": {"type": "string"}},
               "required": ["path"]}, access={"read"})
    def binary_identify(path: str, ctx=None):
        from .identify import identify
        p = ctx.resolve(path) if ctx else Path(path)
        try:
            return ToolResult(True, identify(p).render())
        except FileNotFoundError:
            return ToolResult(False, "", error=f"no existe: {p}")

    @reg.tool("console_profile",
              "Datos duros de una consola: CPU, ISA, RAM, GPU, base de carga.",
              {"type": "object", "properties": {
                  "console": {"type": "string",
                              "description": "psp, nds, vita, gba, psx, n64, 3ds"}},
               "required": ["console"]}, access={"read"})
    def console_profile(console: str):
        from .identify import list_consoles, profile
        p = profile(console)
        if p is None:
            return ToolResult(False, "", error=f"consola desconocida. "
                              f"Disponibles: {', '.join(list_consoles())}")
        lines = [f"{p.name}", f"  CPU: {p.cpu}"]
        if p.extra_cpus:
            lines.append(f"  CPUs adicionales: {', '.join(p.extra_cpus)}")
        lines += [f"  ISA: {p.arch} {p.bits} bits {p.endian}-endian",
                  f"  RAM: {p.ram_mb:g} MB",
                  f"  GPU: {p.gpu} ({'shaders' if p.gpu_programmable else 'pipeline fijo'})",
                  f"  base de carga: 0x{p.load_base:08x}",
                  f"  formatos: {', '.join(p.formats)}"]
        if p.notes:
            lines.append(f"  a tener en cuenta: {p.notes}")
        return ToolResult(True, "\n".join(lines))

    # ------------------------------------------------------------ desensamblar

    @reg.tool("disassemble",
              "Desensambla un binario con Capstone. Indica `console` para fijar "
              "arquitectura y base automáticamente.",
              {"type": "object", "properties": {
                  "path": {"type": "string"},
                  "offset": {"type": "integer"},
                  "length": {"type": "integer"},
                  "console": {"type": "string"},
                  "arch": {"type": "string", "description": "mips, arm, arm64, x86"},
                  "thumb": {"type": "boolean", "description": "modo Thumb en ARM"}},
               "required": ["path"]}, access={"read"})
    def disassemble_tool(path: str, ctx=None, offset: int = 0,
                         length: int = 2048, console: str = "",
                         arch: str = "", thumb: bool = False):
        from .disasm import disassemble_file
        p = ctx.resolve(path) if ctx else Path(path)
        if not Path(p).exists():
            return ToolResult(False, "", error=f"no existe: {p}")
        kw = {"thumb": thumb}
        if arch:
            kw["arch"] = arch
        d = disassemble_file(p, offset=offset,
                             length=min(length, MAX_SLICE),
                             console=console or None, **kw)
        if d.error:
            return ToolResult(False, "", error=d.error)
        body = d.render(limit=150)
        top = d.mnemonics()
        extra = ("\n\nmnemónicos más frecuentes: "
                 + ", ".join(f"{k}×{v}" for k, v in list(top.items())[:8]))
        return ToolResult(True, body + extra,
                          meta={"count": len(d.instructions)})

    @reg.tool("binary_strings",
              "Extrae cadenas ASCII de un binario. Suele ser lo primero que "
              "orienta en un firmware desconocido.",
              {"type": "object", "properties": {
                  "path": {"type": "string"}, "min_len": {"type": "integer"}},
               "required": ["path"]}, access={"read"})
    def binary_strings(path: str, ctx=None, min_len: int = 6):
        from .disasm import extract_strings
        p = ctx.resolve(path) if ctx else Path(path)
        if not Path(p).exists():
            return ToolResult(False, "", error=f"no existe: {p}")
        found = extract_strings(Path(p).read_bytes(), min_len=min_len, limit=300)
        if not found:
            return ToolResult(True, "(sin cadenas legibles)")
        return ToolResult(True, "\n".join(f"0x{o:08x}  {s}" for o, s in found),
                          meta={"count": len(found)})

    # --------------------------------------------------------------- emular

    @reg.tool("emulate_code",
              "Ejecuta un fragmento de código máquina (hex) con Unicorn y "
              "devuelve los registros. Para comprobar qué hace de verdad.",
              {"type": "object", "properties": {
                  "hex_code": {"type": "string",
                               "description": "bytes en hexadecimal, sin espacios"},
                  "arch": {"type": "string"},
                  "endian": {"type": "string"},
                  "base": {"type": "integer"}},
               "required": ["hex_code"]}, access={"exec"})
    def emulate_code(hex_code: str, arch: str = "mips",
                     endian: str = "little", base: int = 0x1000):
        from .emulate import emulate
        try:
            code = bytes.fromhex(hex_code.replace(" ", "").replace("\n", ""))
        except ValueError as e:
            return ToolResult(False, "", error=f"hex inválido: {e}")
        if not code:
            return ToolResult(False, "", error="fragmento vacío")
        r = emulate(code, arch=arch, endian=endian, base=base)
        return ToolResult(r.ok, r.render(), error=r.error)

    @reg.tool("differential_test",
              "Compara el estado de registros de TU emulador contra Unicorn "
              "como referencia. Localiza la instrucción exacta que diverge.",
              {"type": "object", "properties": {
                  "hex_code": {"type": "string"},
                  "expected": {"type": "object",
                               "description": 'p.ej. {"V0": 4660, "SP": 1234}'},
                  "arch": {"type": "string"}},
               "required": ["hex_code", "expected"]}, access={"exec"})
    def differential(hex_code: str, expected: dict, arch: str = "mips"):
        from .emulate import differential_test
        try:
            code = bytes.fromhex(hex_code.replace(" ", ""))
        except ValueError as e:
            return ToolResult(False, "", error=f"hex inválido: {e}")
        regs = {k: int(v, 16) if isinstance(v, str) else int(v)
                for k, v in (expected or {}).items()}
        return ToolResult(True, differential_test(code, regs, arch=arch))

    # ------------------------------------------------------------ portabilidad

    @reg.tool("compare_consoles",
              "Tabla de contraste entre consolas: CPU, ISA, RAM, GPU, formatos.",
              {"type": "object", "properties": {
                  "consoles": {"type": "array", "items": {"type": "string"}}},
               "required": ["consoles"]}, access={"read"})
    def compare_tool(consoles: list):
        from .matrix import compare_consoles
        if isinstance(consoles, str):
            consoles = [c.strip() for c in consoles.split(",")]
        return ToolResult(True, compare_consoles(consoles))

    @reg.tool("analyze_port",
              "Analiza qué cuesta portar un emulador de una consola a otra, "
              "subsistema a subsistema, con veredicto y motivo.",
              {"type": "object", "properties": {
                  "source": {"type": "string"}, "target": {"type": "string"}},
               "required": ["source", "target"]}, access={"read"})
    def analyze_port_tool(source: str, target: str):
        from .matrix import analyze_port
        try:
            return ToolResult(True, analyze_port(source, target).render())
        except ValueError as e:
            return ToolResult(False, "", error=str(e))

    @reg.tool("suggest_port_base",
              "Qué emulador conviene tomar como base para una consola destino, "
              "ordenado por reutilización real.",
              {"type": "object", "properties": {"target": {"type": "string"}},
               "required": ["target"]}, access={"read"})
    def suggest_tool(target: str):
        from .matrix import suggest_port_path
        return ToolResult(True, suggest_port_path(target))

    @reg.tool("re_toolchain_status",
              "Qué herramientas de ingeniería inversa hay instaladas.",
              {"type": "object", "properties": {}}, access={"read"})
    def toolchain_status():
        from .disasm import available_tools
        tools = available_tools()
        lines = [f"  {'sí' if v else 'no':<4s} {k}" for k, v in tools.items()]
        note = ("\nCapstone y Unicorn bastan para desensamblar y emular. "
                "Ghidra y radare2 añaden decompilación a C y xrefs globales, "
                "pero no son necesarios.")
        return ToolResult(True, "\n".join(lines) + note)

    return reg
