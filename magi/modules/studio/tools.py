"""
Herramientas de la fábrica de artefactos (Plan MAGI 9.0 §5).

Sin este registro, artifacts.py sería andamiaje. Con él, Melchior construye un
juego y Balthasar lo ARRANCA y mira la captura antes de opinar.
"""
from __future__ import annotations

from pathlib import Path

from ...core.tools.registry import ToolRegistry, ToolResult


def register_studio_tools(reg: ToolRegistry) -> ToolRegistry:

    @reg.tool("observe_artifact",
              "Inspecciona un artefacto ya generado: arranca un programa, "
              "renderiza un juego y captura un fotograma, mide un documento o "
              "analiza una imagen. Devuelve lo que SE VE, no lo que se supone.",
              {"type": "object", "properties": {
                  "path": {"type": "string"},
                  "kind": {"type": "string",
                           "enum": ["programa", "juego", "imagen",
                                    "documento", "video", "datos"]},
                  "entry": {"type": "string",
                            "description": "punto de entrada del juego, p.ej. main.py"}},
               "required": ["path"]}, access={"exec"})
    async def observe_artifact(path: str, ctx=None, kind: str = "",
                               entry: str = ""):
        from .artifacts import observe
        p = ctx.resolve(path) if ctx else Path(path)
        kw = {}
        if entry:
            kw["entry"] = entry
        obs = await observe(p, kind or None, **kw)
        return ToolResult(obs.ok, obs.render(),
                          error=None if obs.ok else "; ".join(obs.problems),
                          meta={"screenshot": obs.screenshot,
                                "kind": obs.kind.value})

    @reg.tool("inspect_image",
              "Analiza una imagen sin gastar cuota de visión: tamaño, número "
              "de colores y color dominante. Detecta pantallas en negro.",
              {"type": "object", "properties": {"path": {"type": "string"}},
               "required": ["path"]}, access={"read"})
    async def inspect_image(path: str, ctx=None):
        from .artifacts import observe_image
        p = ctx.resolve(path) if ctx else Path(path)
        obs = await observe_image(p)
        return ToolResult(obs.ok, obs.render(),
                          error=None if obs.ok else "; ".join(obs.problems))

    @reg.tool("compose_manga_page",
              "Compone una página de manga: rejilla de viñetas, orden de "
              "lectura derecha-a-izquierda, globos y rotulación. Valida la "
              "composición ANTES de generar dibujos.",
              {"type": "object", "properties": {
                  "out_path": {"type": "string"},
                  "rows": {"type": "integer"},
                  "cols": {"type": "integer"},
                  "prompts": {"type": "array", "items": {"type": "string"},
                              "description": "descripción de cada viñeta"},
                  "layout": {"type": "string", "enum": ["grid", "dramatic"]},
                  "order": {"type": "string",
                            "enum": ["rtl", "ltr"],
                            "description": "rtl = manga (por defecto)"}},
               "required": ["out_path"]}, access={"write"}, dangerous=True)
    async def compose_manga_page(out_path: str, ctx=None, rows: int = 2,
                                 cols: int = 2, prompts: list | None = None,
                                 layout: str = "grid", order: str = "rtl"):
        from .manga import (ReadingOrder, compose_page, dramatic_page,
                            grid_page)
        ro = ReadingOrder.RTL if order == "rtl" else ReadingOrder.LTR
        prompts = prompts or []
        spec = (dramatic_page(prompts, order=ro) if layout == "dramatic"
                else grid_page(rows, cols, prompts, order=ro))
        problems = spec.validate()
        if problems:
            return ToolResult(False, "", error="; ".join(problems))
        out = ctx.resolve(out_path) if ctx else Path(out_path)
        if ctx is not None:
            ctx.get_journal().record(out, "create", tool="compose_manga_page")
        report = await compose_page(spec, out)
        lines = [f"página: {report.get('path')}",
                 f"viñetas: {report.get('panels')} · "
                 f"generadas: {report.get('generated')} · "
                 f"lectura: {report.get('reading_order')}"]
        if report.get("problems"):
            lines.append("problemas: " + "; ".join(report["problems"]))
        return ToolResult(report.get("ok", False), "\n".join(lines),
                          error=None if report.get("ok")
                          else "; ".join(report.get("problems", [])))

    @reg.tool("validate_manga_layout",
              "Comprueba una composición (solapes, huecos, viñetas fuera de "
              "página) SIN generar dibujos. Barato: evita gastar cuota en una "
              "página mal montada.",
              {"type": "object", "properties": {
                  "rows": {"type": "integer"}, "cols": {"type": "integer"},
                  "layout": {"type": "string", "enum": ["grid", "dramatic"]}},
               "required": ["rows", "cols"]}, access={"read"})
    def validate_manga_layout(rows: int, cols: int, layout: str = "grid"):
        from .manga import dramatic_page, grid_page
        spec = dramatic_page() if layout == "dramatic" else grid_page(rows, cols)
        problems = spec.validate()
        seq = [f"({p.row},{p.col})" for p in spec.reading_sequence()]
        body = (f"{len(spec.panels)} viñetas, lectura {spec.order.value}\n"
                f"orden: {' -> '.join(seq)}")
        if problems:
            return ToolResult(False, body, error="; ".join(problems))
        return ToolResult(True, body + "\ncomposición válida")

    @reg.tool("studio_backends",
              "Qué se puede generar y observar en esta máquina.",
              {"type": "object", "properties": {}}, access={"read"})
    def studio_backends():
        from .artifacts import backends_report
        return ToolResult(True, backends_report())

    return reg
