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

# Índices de corpus ya construidos, por ruta. Indexar PPSSPP entero tarda
# segundos; hacerlo en cada turno del debate sería absurdo.
_CORPUS_CACHE: dict[str, object] = {}


def register_reverse_tools(reg: ToolRegistry) -> ToolRegistry:
    """Añade el toolchain de RE a un registro existente."""

    # ------------------------------------------------------------ identificar

    @reg.tool("binary_identify",
              "Identifica un binario: formato, arquitectura, endianness, punto "
              "de entrada y consola probable. SIEMPRE antes de desensamblar.",
              {"type": "object", "properties": {"path": {"type": "string"}},
               "required": ["path"]}, access={"read"})
    def binary_identify(path: str, ctx=None):
        from .entropy import analyze_file, reading
        from .identify import identify
        p = ctx.resolve(path) if ctx else Path(path)
        try:
            cuerpo = identify(p).render()
        except FileNotFoundError:
            return ToolResult(False, "", error=f"no existe: {p}")

        # La entropía se añade AQUÍ, y no solo como herramienta aparte, porque
        # el momento en que evita perder horas es justo este: antes de
        # desensamblar. Un EBOOT.BIN cifrado se ve igual que código roto, y la
        # conclusión natural al ver salir basura de Capstone es que falla el
        # decodificador. Si el agente tiene que acordarse de pedir la entropía
        # por su cuenta, no se acordará.
        try:
            informe = analyze_file(p)
            cuerpo += (f"\nentropía: {informe.overall:.2f}/8.00 — "
                       f"{reading(informe.overall)}")
            zonas = informe.hot_regions()
            if zonas and not informe.encrypted:
                cuerpo += (f"\n  {len(zonas)} zona(s) de alta entropía que la "
                           f"media global esconde; usa binary_entropy")
            return ToolResult(True, cuerpo,
                              meta={"entropy": round(informe.overall, 3),
                                    "encrypted": informe.encrypted})
        except (OSError, ValueError):
            return ToolResult(True, cuerpo)

    @reg.tool("binary_entropy",
              "Entropía de un binario y zonas cifradas o comprimidas.",
              {"type": "object", "properties": {"path": {"type": "string"}},
               "required": ["path"]}, access={"read"})
    def binary_entropy(path: str, ctx=None):
        from .entropy import analyze_file
        p = ctx.resolve(path) if ctx else Path(path)
        try:
            informe = analyze_file(p)
        except (FileNotFoundError, IsADirectoryError) as e:
            return ToolResult(False, "", error=str(e))
        return ToolResult(True, informe.render(), meta=informe.to_dict())

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

    # ------------------------------------------------------- corpus real

    @reg.tool("index_emulator",
              "Indexa el código fuente de un emulador y clasifica cada fichero "
              "en subsistemas (dynarec, gpu, mmu, hle...). El resultado queda "
              "cacheado para las comparaciones posteriores.",
              {"type": "object", "properties": {
                  "path": {"type": "string"},
                  "name": {"type": "string",
                           "description": "etiqueta, p.ej. PPSSPP"}},
               "required": ["path"]}, access={"read"})
    def index_emulator(path: str, ctx=None, name: str = ""):
        from .corpus import index_source_tree
        p = ctx.resolve(path) if ctx else Path(path)
        try:
            idx = index_source_tree(p, name=name)
        except NotADirectoryError:
            return ToolResult(False, "", error=f"no es un directorio: {p}")
        if idx.total_files == 0:
            return ToolResult(False, "", error=(
                f"no se encontró código fuente en {p}. ¿Es la raíz del "
                f"repositorio del emulador?"))
        _CORPUS_CACHE[str(p)] = idx
        if name:
            _CORPUS_CACHE[name.lower()] = idx
        return ToolResult(True, idx.render(),
                          meta={"files": idx.total_files,
                                "lines": idx.total_lines})

    @reg.tool("locate_subsystem",
              "Dónde vive un subsistema en un emulador ya indexado, con "
              "ficheros y número de líneas reales.",
              {"type": "object", "properties": {
                  "emulator": {"type": "string",
                               "description": "nombre o ruta usados al indexar"},
                  "subsystem": {"type": "string",
                                "description": "dynarec, gpu, mmu, hle_sistema..."}},
               "required": ["emulator", "subsystem"]}, access={"read"})
    def locate_subsystem_tool(emulator: str, subsystem: str):
        from .corpus import locate_subsystem, subsystem_names
        idx = _CORPUS_CACHE.get(emulator) or _CORPUS_CACHE.get(emulator.lower())
        if idx is None:
            return ToolResult(False, "", error=(
                f"'{emulator}' no está indexado. Usa index_emulator primero. "
                f"Indexados: {', '.join(sorted(k for k in _CORPUS_CACHE)) or 'ninguno'}"))
        if subsystem not in subsystem_names():
            return ToolResult(False, "", error=(
                f"subsistema desconocido. Disponibles: "
                f"{', '.join(subsystem_names())}"))
        return ToolResult(True, locate_subsystem(idx, subsystem))

    @reg.tool("compare_emulators",
              "Contrasta dos emuladores ya indexados subsistema a subsistema, "
              "con líneas de código reales y lectura de dónde está el trabajo.",
              {"type": "object", "properties": {
                  "a": {"type": "string"}, "b": {"type": "string"}},
               "required": ["a", "b"]}, access={"read"})
    def compare_emulators(a: str, b: str):
        from .corpus import compare_corpora
        ia = _CORPUS_CACHE.get(a) or _CORPUS_CACHE.get(a.lower())
        ib = _CORPUS_CACHE.get(b) or _CORPUS_CACHE.get(b.lower())
        missing = [n for n, i in ((a, ia), (b, ib)) if i is None]
        if missing:
            return ToolResult(False, "", error=(
                f"sin indexar: {', '.join(missing)}. Usa index_emulator antes."))
        return ToolResult(True, compare_corpora(ia, ib).render())

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
