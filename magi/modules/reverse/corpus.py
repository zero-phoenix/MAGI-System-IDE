"""
Indexado y comparación de código de emuladores (Plan MAGI 9.0 §5.3).

QUÉ RESUELVE
============
`analyze_port` compara CONSOLAS a partir de sus perfiles de hardware. Útil para
decidir, insuficiente para trabajar: no te dice dónde está el dynarec de PPSSPP
ni cuántas líneas tiene el rasterizador de melonDS.

Esto indexa el árbol de fuentes de un emulador y clasifica cada fichero en
subsistemas, con referencias reales. A partir de ahí la comparación entre dos
emuladores deja de ser una tabla de especificaciones y pasa a ser un contraste
de código: "el dispatch del dynarec vive en Core/MIPS/MIPSCompALU.cpp, 1 240
líneas, y su equivalente en melonDS está en ARMJIT_A64/, 3 100 líneas".

Sin dependencias: recorrido de ficheros y coincidencia de patrones. tree-sitter
daría precisión sintáctica, pero exige compilar gramáticas por lenguaje y aquí
lo que importa es localizar subsistemas, no analizar sintaxis.
"""
from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SOURCE_EXT = {".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx",
              ".rs", ".m", ".mm", ".java", ".cs", ".go"}

SKIP_DIRS = {".git", "node_modules", "build", "cmake-build-debug", "out",
             "third_party", "externals", "ext", "vendor", "deps", "target",
             "__pycache__", ".vs", ".idea", "docs", "assets"}

MAX_FILES = 20_000
MAX_BYTES_SCANNED = 300_000     # por fichero


@dataclass(frozen=True)
class SubsystemRule:
    """Señales para clasificar un fichero. Ruta pesa más que contenido."""
    name: str
    path_patterns: tuple[str, ...]
    content_patterns: tuple[str, ...]
    description: str


# Reglas derivadas de cómo se organizan de verdad los emuladores conocidos.
RULES: tuple[SubsystemRule, ...] = (
    SubsystemRule(
        "dynarec",
        # Los backends de emisión viven bajo un directorio de arquitectura
        # DENTRO del directorio de CPU: Core/MIPS/x86/, src/ARMJIT_A64/.
        # Sin esos patrones, Core/MIPS/x86/CompALU.cpp —que en PPSSPP ES el
        # dynarec— se clasificaba como intérprete por el "core/mips" de la ruta.
        ("jit", "dynarec", "recompil", "compiler/", "ir/", "codegen",
         "/comp", "/x86/", "/x64/", "/arm64/", "/aarch64/", "/riscv/",
         "/backend"),
        (r"\bemit[A-Z_]", r"\bEmit[A-Z]", r"code_?block", r"\bIRBlock\b",
         r"regalloc", r"register_?alloc", r"\bJit\b", r"trampoline"),
        "recompilación dinámica: frontend de decodificación, IR y emisión"),
    SubsystemRule(
        "cpu_interprete",
        ("interp", "cpu/", "core/mips", "core/arm", "arm7", "arm9",
         "allegrec", "r3000", "r4300"),
        (r"case\s+0x[0-9a-fA-F]{2,}", r"opcode", r"\bdecode[A-Z_]",
         r"instruction_?table", r"\bexecute_?instruction"),
        "intérprete de instrucciones: decodificación y semántica"),
    SubsystemRule(
        "mmu",
        ("mmu", "memmap", "memory", "mem/", "bus"),
        (r"\bRead(8|16|32|64)\b", r"\bWrite(8|16|32|64)\b", r"\btlb\b",
         r"translate_?addr", r"page_?table", r"memory_?map"),
        "mapa de memoria, traducción de direcciones y accesos"),
    SubsystemRule(
        "gpu",
        ("gpu", "gfx", "graphics", "render", "video", "vulkan", "opengl",
         "d3d", "rasteriz", "shader"),
        (r"\bglDraw", r"\bvkCmd", r"shader", r"texture", r"\bvertex\b",
         r"rasteriz", r"framebuffer", r"\bblend\b"),
        "rasterizado, texturas, shaders y presentación"),
    SubsystemRule(
        "audio",
        ("audio", "sound", "spu", "dsp", "sas"),
        (r"\bsample_?rate\b", r"\bmixer\b", r"\bADPCM\b", r"\bPCM\b",
         r"audio_?buffer", r"\bvoice\[", r"\bchannel\["),
        "DSP, mezcla y salida de muestras"),
    SubsystemRule(
        "hle_sistema",
        ("hle", "kernel", "syscall", "module", "loader/", "nid"),
        (r"\bsceKernel", r"\bsyscall\b", r"\bHLE_", r"\bnid\b",
         r"import_?func", r"\bsvc[A-Z_]"),
        "emulación de alto nivel del sistema operativo de la consola"),
    SubsystemRule(
        "planificador",
        ("sched", "timing", "cycle", "event"),
        (r"\bcycles?_?(count|left|until)", r"\bScheduleEvent\b",
         r"\btimestamp\b", r"\bdowncount\b", r"\bcoreTiming\b"),
        "reloj, presupuesto de ciclos y cola de eventos"),
    SubsystemRule(
        "savestates",
        ("savestate", "state/", "serializ", "snapshot"),
        (r"\bDoState\b", r"\bserialize\b", r"\bsave_?state\b",
         r"\bChunkFile\b", r"\bDoArray\b"),
        "serialización del estado completo de la máquina"),
    SubsystemRule(
        "entrada",
        ("input", "controller", "pad", "keymap", "touch"),
        (r"\bbutton", r"\banalog\b", r"\bkeymap\b", r"\bgamepad\b",
         r"\btouch(screen)?\b"),
        "mapeo de mandos, botones y sensores"),
    SubsystemRule(
        "carga_de_rom",
        ("loader", "iso", "disc", "cart", "rom", "format"),
        (r"\bELF_?Header\b", r"\bmagic\b", r"\bLoadROM\b", r"\bmount\b",
         r"\bISO9660\b", r"\bcso\b"),
        "lectura y montaje de imágenes de juego"),
    SubsystemRule(
        "frontend",
        ("ui/", "gui", "qt/", "imgui", "frontend", "menu", "config",
         "windows/", "android/", "ios/", "sdl"),
        (r"\bQWidget\b", r"\bImGui::", r"\bwxFrame\b", r"\bsetWindowTitle\b",
         r"\bmenu_?item\b"),
        "interfaz, configuración y empaquetado por plataforma"),
)

_PATH_WEIGHT = 3.0
_CONTENT_WEIGHT = 1.0


@dataclass
class FileEntry:
    path: str
    lines: int
    subsystem: str
    score: float
    signals: list[str] = field(default_factory=list)


@dataclass
class SubsystemStats:
    name: str
    files: int = 0
    lines: int = 0
    examples: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "files": self.files, "lines": self.lines,
                "examples": self.examples[:5]}


@dataclass
class CorpusIndex:
    root: str
    name: str
    total_files: int = 0
    total_lines: int = 0
    scanned: int = 0
    truncated: bool = False
    subsystems: dict[str, SubsystemStats] = field(default_factory=dict)
    entries: list[FileEntry] = field(default_factory=list)

    def top(self, n: int = 12) -> list[SubsystemStats]:
        return sorted(self.subsystems.values(), key=lambda s: -s.lines)[:n]

    def render(self) -> str:
        lines = [f"{self.name} — {self.root}",
                 f"{self.total_files:,} ficheros de código, "
                 f"{self.total_lines:,} líneas"
                 + ("  [truncado]" if self.truncated else ""),
                 "",
                 f"{'subsistema':<16s} {'ficheros':>9s} {'líneas':>10s}  ejemplos",
                 "-" * 92]
        for s in self.top():
            ex = ", ".join(Path(e).name for e in s.examples[:2])
            lines.append(f"{s.name:<16s} {s.files:>9,d} {s.lines:>10,d}  {ex}")
        no_class = self.total_lines - sum(s.lines for s in self.subsystems.values())
        if no_class > 0:
            lines.append(f"{'(sin clasificar)':<16s} {'':>9s} {no_class:>10,d}")
        return "\n".join(lines)

    def files_for(self, subsystem: str, limit: int = 20) -> list[FileEntry]:
        return sorted((e for e in self.entries if e.subsystem == subsystem),
                      key=lambda e: -e.lines)[:limit]

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "root": self.root,
                "total_files": self.total_files, "total_lines": self.total_lines,
                "subsystems": {k: v.to_dict() for k, v in self.subsystems.items()}}


def _classify(rel_path: str, text: str) -> tuple[str, float, list[str]]:
    """
    Clasifica un fichero. La ruta pesa el triple que el contenido: un fichero
    bajo GPU/ es del subsistema gráfico aunque mencione 'cycles' de pasada.
    """
    low_path = rel_path.lower().replace("\\", "/")
    scores: dict[str, float] = defaultdict(float)
    signals: dict[str, list[str]] = defaultdict(list)

    for rule in RULES:
        for pat in rule.path_patterns:
            if pat in low_path:
                scores[rule.name] += _PATH_WEIGHT
                signals[rule.name].append(f"ruta~{pat}")
                break
        hits = 0
        for pat in rule.content_patterns:
            if re.search(pat, text):
                hits += 1
                if hits <= 2:
                    signals[rule.name].append(f"código~{pat}")
        if hits:
            scores[rule.name] += _CONTENT_WEIGHT * min(hits, 4)

    if not scores:
        return "", 0.0, []
    best = max(scores, key=lambda k: scores[k])
    return best, scores[best], signals[best][:3]


def index_source_tree(root: str | Path, *, name: str = "",
                      min_score: float = 2.0,
                      max_files: int = MAX_FILES) -> CorpusIndex:
    """
    Recorre un árbol de fuentes y clasifica cada fichero en un subsistema.

    Pensado para el corpus que te interesa: PPSSPP (PSP), melonDS y DeSmuME
    (NDS), Vita3K (Vita), mGBA (GBA). Funciona con cualquier proyecto C/C++/Rust.
    """
    r = Path(root)
    if not r.is_dir():
        raise NotADirectoryError(r)

    idx = CorpusIndex(root=str(r), name=name or r.name)
    for path in sorted(r.rglob("*")):
        if idx.scanned >= max_files:
            idx.truncated = True
            break
        if not path.is_file() or path.suffix.lower() not in SOURCE_EXT:
            continue
        if any(part.lower() in SKIP_DIRS for part in path.parts):
            continue

        try:
            raw = path.read_bytes()[:MAX_BYTES_SCANNED]
            text = raw.decode("utf-8", errors="replace")
        except OSError:
            continue

        idx.scanned += 1
        n_lines = text.count("\n") + 1
        idx.total_files += 1
        idx.total_lines += n_lines

        # `as_posix()`, no `str()`. `_classify` pesa la RUTA por encima del
        # contenido —un fichero bajo GPU/ es del subsistema gráfico aunque
        # mencione 'cycles' de pasada—, y esas pistas están escritas con '/'.
        # En Windows `str(Path)` da 'GPU\\...', ninguna casaba, y la
        # clasificación se iba con cualquier palabra suelta del contenido: el
        # fallo exacto que ese peso existe para evitar. Analizar el árbol de
        # PPSSPP desde Windows daba subsistemas mal repartidos, en silencio.
        rel = path.relative_to(r).as_posix()
        sub, score, sig = _classify(rel, text)
        if not sub or score < min_score:
            continue

        idx.entries.append(FileEntry(rel, n_lines, sub, score, sig))
        st = idx.subsystems.setdefault(sub, SubsystemStats(sub))
        st.files += 1
        st.lines += n_lines
        if len(st.examples) < 8:
            st.examples.append(rel)

    logger.info("[corpus] %s: %d ficheros, %d líneas, %d subsistemas",
                idx.name, idx.total_files, idx.total_lines, len(idx.subsystems))
    return idx


# ------------------------------------------------------------- comparación

@dataclass
class CorpusComparison:
    a: CorpusIndex
    b: CorpusIndex

    def render(self) -> str:
        subs = sorted(set(self.a.subsystems) | set(self.b.subsystems))
        w = 26
        lines = [
            f"CONTRASTE DE CÓDIGO: {self.a.name} frente a {self.b.name}",
            "",
            f"{'subsistema':<16s} {self.a.name[:w]:>{w}s} {self.b.name[:w]:>{w}s}   razón",
            "-" * (18 + w * 2 + 10),
        ]
        for s in subs:
            la = self.a.subsystems.get(s, SubsystemStats(s)).lines
            lb = self.b.subsystems.get(s, SubsystemStats(s)).lines
            ratio = (f"{la / lb:.1f}x" if la and lb
                     else ("solo A" if la else "solo B"))
            lines.append(f"{s:<16s} {la:>{w},d} {lb:>{w},d}   {ratio}")
        lines += ["", f"total{'':<11s} {self.a.total_lines:>{w},d} "
                      f"{self.b.total_lines:>{w},d}"]
        lines.append("")
        lines.append(self._reading())
        return "\n".join(lines)

    def _reading(self) -> str:
        """La parte que convierte números en una decisión."""
        notes = []
        for s in ("dynarec", "gpu", "hle_sistema"):
            la = self.a.subsystems.get(s, SubsystemStats(s)).lines
            lb = self.b.subsystems.get(s, SubsystemStats(s)).lines
            if la and lb and max(la, lb) / max(min(la, lb), 1) > 2.5:
                bigger = self.a.name if la > lb else self.b.name
                notes.append(
                    f"- {s}: {bigger} dedica {max(la, lb) / max(min(la, lb), 1):.1f}x "
                    f"más código. Si vas a portar en esa dirección, es donde se "
                    f"concentra el trabajo que no se ve en la tabla de consolas.")
            elif la and not lb:
                notes.append(f"- {s}: solo existe en {self.a.name}; "
                             f"{self.b.name} tendría que escribirlo entero.")
            elif lb and not la:
                notes.append(f"- {s}: solo existe en {self.b.name}.")
        return ("Lectura:\n" + "\n".join(notes)) if notes else \
            "Lectura: reparto de código comparable entre ambos."

    def to_dict(self) -> dict[str, Any]:
        return {"a": self.a.to_dict(), "b": self.b.to_dict()}


def compare_corpora(a: CorpusIndex, b: CorpusIndex) -> CorpusComparison:
    return CorpusComparison(a, b)


def locate_subsystem(index: CorpusIndex, subsystem: str,
                     limit: int = 15) -> str:
    """Dónde vive un subsistema, con ficheros y tamaños reales."""
    files = index.files_for(subsystem, limit)
    if not files:
        known = ", ".join(sorted(index.subsystems)) or "ninguno"
        return (f"No se localizó '{subsystem}' en {index.name}. "
                f"Subsistemas detectados: {known}")
    rule = next((r for r in RULES if r.name == subsystem), None)
    head = [f"{subsystem} en {index.name}"]
    if rule:
        head.append(f"  ({rule.description})")
    head.append("")
    for e in files:
        head.append(f"  {e.lines:>6,d} líneas  {e.path}")
        if e.signals:
            head.append(f"{'':>14s}  señales: {', '.join(e.signals)}")
    total = sum(e.lines for e in index.files_for(subsystem, 10_000))
    head.append(f"\n  total del subsistema: {total:,} líneas")
    return "\n".join(head)


def subsystem_names() -> list[str]:
    return [r.name for r in RULES]
