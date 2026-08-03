"""
Matriz de contraste entre consolas y análisis de portabilidad (§5.3).

PARA QUÉ
========
Lo que pediste: "saber cómo modificar un emulador de una consola y adaptarlo
para otra usando análisis y comparación".

Ese trabajo tiene una parte que es criterio y otra que es contabilidad. La
segunda es la que se puede automatizar: qué subsistemas se reutilizan tal cual,
cuáles hay que reemplazar, y cuáles son irreducibles y por qué.

La respuesta honesta suele ser incómoda — portar PPSSPP a Vita no es "cambiar
el dynarec", es reescribir el backend gráfico entero porque un pipeline fijo no
se traduce a shaders programables. Mejor saberlo antes de empezar que después.

(Sustituye a PortabilityMatrix, que devolvía un diccionario con dos módulos
inventados —"core_fpu", "gui_menu"— y no se llamaba desde ningún sitio.)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .identify import CONSOLES, ConsoleProfile


class Reuse(str, Enum):
    DIRECT = "reutilizable"        # sirve tal cual
    ADAPT = "adaptable"            # misma idea, hay que tocarlo
    REPLACE = "reemplazar"         # hay que escribirlo de nuevo
    HARD = "irreducible"           # no hay equivalencia; rediseño


SUBSYSTEMS = [
    "carga_de_rom", "cpu_interprete", "dynarec", "mmu", "planificador",
    "gpu", "audio", "entrada", "hle_sistema", "savestates", "frontend",
]

_EFFORT = {Reuse.DIRECT: 0, Reuse.ADAPT: 2, Reuse.REPLACE: 5, Reuse.HARD: 9}


@dataclass
class PortItem:
    subsystem: str
    verdict: Reuse
    reason: str

    @property
    def effort(self) -> int:
        return _EFFORT[self.verdict]


@dataclass
class PortAnalysis:
    source: ConsoleProfile
    target: ConsoleProfile
    items: list[PortItem] = field(default_factory=list)

    @property
    def effort(self) -> int:
        return sum(i.effort for i in self.items)

    @property
    def max_effort(self) -> int:
        return len(self.items) * _EFFORT[Reuse.HARD]

    @property
    def reuse_ratio(self) -> float:
        return 1.0 - (self.effort / self.max_effort) if self.max_effort else 0.0

    def by_verdict(self, v: Reuse) -> list[PortItem]:
        return [i for i in self.items if i.verdict is v]

    def render(self) -> str:
        lines = [
            f"PORTAR: {self.source.name} -> {self.target.name}",
            "",
            f"{'subsistema':<16s} {'veredicto':<14s} motivo",
            "-" * 92,
        ]
        for i in sorted(self.items, key=lambda x: -x.effort):
            lines.append(f"{i.subsystem:<16s} {i.verdict.value:<14s} {i.reason}")
        lines += [
            "-" * 92,
            f"reutilización estimada: {self.reuse_ratio:.0%}  "
            f"(esfuerzo {self.effort}/{self.max_effort})",
        ]
        hard = self.by_verdict(Reuse.HARD)
        if hard:
            lines.append("")
            lines.append("IRREDUCIBLE — empieza por aquí o descarta el port:")
            lines += [f"  · {i.subsystem}: {i.reason}" for i in hard]
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source.id, "target": self.target.id,
            "reuse_ratio": round(self.reuse_ratio, 3),
            "effort": self.effort,
            "items": [{"subsystem": i.subsystem, "verdict": i.verdict.value,
                       "reason": i.reason} for i in self.items],
        }


def analyze_port(source_id: str, target_id: str) -> PortAnalysis:
    """
    Análisis de portabilidad entre dos consolas, subsistema a subsistema.

    Las reglas salen de las diferencias que de verdad condicionan el trabajo:
    familia de ISA, endianness, número de CPUs, y si la GPU es de pipeline fijo
    o programable.
    """
    src, tgt = CONSOLES.get(source_id.lower()), CONSOLES.get(target_id.lower())
    if src is None or tgt is None:
        raise ValueError(f"consola desconocida: {source_id} o {target_id}")

    same_isa = src.arch == tgt.arch
    same_endian = src.endian == tgt.endian
    src_multi, tgt_multi = bool(src.extra_cpus), bool(tgt.extra_cpus)
    items: list[PortItem] = []

    items.append(PortItem(
        "carga_de_rom", Reuse.REPLACE,
        f"formatos distintos: {'/'.join(src.formats[:3])} frente a "
        f"{'/'.join(tgt.formats[:3])}"))

    if same_isa:
        items.append(PortItem(
            "cpu_interprete", Reuse.ADAPT,
            f"misma familia ({src.arch}): cambian extensiones y modos, no la "
            f"estructura del intérprete"))
        items.append(PortItem(
            "dynarec", Reuse.ADAPT,
            "el backend de emisión se conserva; cambia el frontend de decodificación"))
    else:
        items.append(PortItem(
            "cpu_interprete", Reuse.REPLACE,
            f"{src.cpu} -> {tgt.cpu}: decodificador y semántica nuevos"))
        items.append(PortItem(
            "dynarec", Reuse.REPLACE,
            f"frontend de {src.arch} y emisión para {tgt.arch}: la IR intermedia "
            f"y la asignación de registros sí suelen reutilizarse"))

    if not same_endian:
        items.append(PortItem(
            "mmu", Reuse.HARD,
            f"{src.endian}-endian -> {tgt.endian}-endian: afecta a CADA acceso "
            f"a memoria, no es un adaptador que se ponga en un sitio"))
    elif src.ram_mb and tgt.ram_mb and tgt.ram_mb / max(src.ram_mb, 0.1) > 8:
        items.append(PortItem(
            "mmu", Reuse.REPLACE,
            f"salto de {src.ram_mb:g} MB a {tgt.ram_mb:g} MB: el mapa de memoria "
            f"plano deja de servir"))
    else:
        items.append(PortItem("mmu", Reuse.ADAPT,
                              "mismo endianness; cambia el mapa de memoria"))

    if src_multi != tgt_multi:
        items.append(PortItem(
            "planificador", Reuse.HARD,
            "una consola tiene varias CPUs y la otra no: el modelo de "
            "sincronización cambia de raíz, no se adapta"))
    elif src_multi:
        items.append(PortItem("planificador", Reuse.ADAPT,
                              "ambas multi-CPU: cambian relojes y arbitraje"))
    else:
        items.append(PortItem("planificador", Reuse.DIRECT,
                              "CPU única en ambas: el bucle de ciclos se conserva"))

    if src.gpu_programmable and tgt.gpu_programmable:
        items.append(PortItem("gpu", Reuse.ADAPT,
                              "ambas con shaders: cambia el traductor de shaders"))
    elif not src.gpu_programmable and tgt.gpu_programmable:
        items.append(PortItem(
            "gpu", Reuse.HARD,
            f"pipeline fijo ({src.gpu}) -> programable ({tgt.gpu}): el backend "
            f"gráfico se reescribe entero, no se adapta"))
    elif src.gpu_programmable:
        items.append(PortItem(
            "gpu", Reuse.HARD,
            "shaders -> pipeline fijo: hay que emular estados fijos con lo que "
            "el hardware destino no expone"))
    else:
        items.append(PortItem("gpu", Reuse.REPLACE,
                              "ambas de pipeline fijo, pero con registros distintos"))

    items.append(PortItem("audio", Reuse.REPLACE,
                          "el DSP y el formato de muestras son propios de cada consola"))
    items.append(PortItem("entrada", Reuse.ADAPT,
                          "mapeo de botones y sensores; estructura reutilizable"))
    items.append(PortItem(
        "hle_sistema", Reuse.REPLACE,
        "las llamadas de sistema son específicas; es donde más tiempo se va "
        "una vez la CPU funciona"))
    items.append(PortItem(
        "savestates", Reuse.ADAPT,
        "el mecanismo de serialización se conserva; cambia qué estado se guarda"))
    items.append(PortItem(
        "frontend", Reuse.DIRECT,
        "interfaz, configuración, entrada y grabación: reutilizable tal cual"))

    return PortAnalysis(src, tgt, items)


def compare_consoles(console_ids: list[str]) -> str:
    """Tabla de contraste. La vista de conjunto antes de elegir objetivo."""
    profiles = [CONSOLES[c.lower()] for c in console_ids if c.lower() in CONSOLES]
    if not profiles:
        return "ninguna consola reconocida"

    rows = [
        ("CPU", lambda p: p.cpu),
        ("ISA", lambda p: f"{p.arch} {p.bits}b {p.endian}"),
        ("CPUs extra", lambda p: ", ".join(p.extra_cpus) or "—"),
        ("RAM", lambda p: f"{p.ram_mb:g} MB"),
        ("GPU", lambda p: p.gpu),
        ("Shaders", lambda p: "sí" if p.gpu_programmable else "pipeline fijo"),
        ("Base carga", lambda p: f"0x{p.load_base:08x}"),
        ("Formatos", lambda p: "/".join(p.formats[:3])),
    ]
    w = max(28, max(len(p.name) for p in profiles) + 2)
    out = ["".ljust(12) + "".join(p.name.ljust(w) for p in profiles),
           "-" * (12 + w * len(profiles))]
    for label, fn in rows:
        out.append(label.ljust(12)
                   + "".join(str(fn(p))[:w - 2].ljust(w) for p in profiles))
    out.append("")
    for p in profiles:
        if p.notes:
            out.append(f"{p.name}: {p.notes}")
    return "\n".join(out)


def suggest_port_path(target_id: str) -> str:
    """
    Qué emulador conviene tomar como base para una consola destino.

    Ordena por reutilización real, no por popularidad del proyecto.
    """
    tgt = CONSOLES.get(target_id.lower())
    if tgt is None:
        return f"consola desconocida: {target_id}"

    scored = []
    for cid in CONSOLES:
        if cid == target_id.lower():
            continue
        a = analyze_port(cid, target_id)
        scored.append((a.reuse_ratio, cid, a))
    scored.sort(key=lambda t: -t[0])

    lines = [f"Bases candidatas para un emulador de {tgt.name}:", ""]
    for ratio, cid, a in scored[:4]:
        hard = a.by_verdict(Reuse.HARD)
        lines.append(f"  {CONSOLES[cid].name:<24s} reutilización {ratio:.0%}"
                     + (f"  · irreducible: "
                        f"{', '.join(i.subsystem for i in hard)}" if hard else ""))
    lines += ["", "El porcentaje mide subsistemas, no líneas de código: el "
              "frontend es grande y se reutiliza entero, mientras que un "
              "dynarec nuevo es pequeño en líneas y enorme en trabajo."]
    return "\n".join(lines)
