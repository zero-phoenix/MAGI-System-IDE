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
              "Compone una página de manga con viñetas y lectura RTL, "
              "validando la composición antes de dibujar nada.",
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

    # ------------------------------------------------------------------ §5.5

    # Presets en lugar de ancho/alto/fps sueltos. Tres motivos: la línea del
    # catálogo baja de 224 a ~130 caracteres, elegir "vertical" es más fácil
    # de acertar que recordar que el manga va en 1080x1920, y no hay forma de
    # pedir dimensiones impares, que H.264 rechaza.
    FORMATOS = {
        "horizontal": (1920, 1080, 30),   # informes, demos, tutoriales
        "vertical":   (1080, 1920, 30),   # manga y móvil
        "cuadrado":   (1080, 1080, 30),
        "rapido":     (640, 360, 24),     # pruebas: renderiza en segundos
    }

    @reg.tool("render_animatic",
              "Monta imágenes en vídeo con zoom Ken Burns y transiciones, y "
              "lo inspecciona. Para manga, informes y demos.",
              {"type": "object", "properties": {
                  "images": {"type": "array", "items": {"type": "string"}},
                  "out_path": {"type": "string"},
                  "seconds_each": {"type": "number"},
                  "format": {"type": "string",
                             "enum": sorted(FORMATOS)},
                  "audio": {"type": "string"}},
               "required": ["images", "out_path"]}, access={"write"})
    async def render_animatic(images: list, out_path: str, ctx=None,
                              seconds_each: float = 3.0,
                              format: str = "horizontal", audio: str = "",
                              crossfade: float = 0.5, ken_burns: bool = True):
        from .video import Slide, VideoSpec, render_slideshow
        if format not in FORMATOS:
            return ToolResult(
                False, "", error=f"formato '{format}' desconocido. "
                f"Disponibles: {', '.join(sorted(FORMATOS))}")
        ancho, alto, fps = FORMATOS[format]
        rutas = [str(ctx.resolve(i)) if ctx else str(i) for i in images]
        spec = VideoSpec(
            slides=[Slide(r, float(seconds_each)) for r in rutas],
            width=ancho, height=alto, fps=fps,
            crossfade=float(crossfade), ken_burns=bool(ken_burns),
            audio=str(ctx.resolve(audio)) if (audio and ctx) else audio)
        destino = ctx.resolve(out_path) if ctx else Path(out_path)
        if ctx and getattr(ctx, "journal", None):
            ctx.journal.record(destino, "create", tool="render_animatic")
        obs = await render_slideshow(spec, destino)
        return ToolResult(obs.ok, obs.render(),
                          error=None if obs.ok else "; ".join(obs.problems),
                          meta={"path": str(destino), "screenshot": obs.screenshot})

    @reg.tool("record_program",
              "Graba en vídeo un programa gráfico en ejecución y lo revisa. "
              "Ver treinta fotogramas dice si se mueve o se congela.",
              {"type": "object", "properties": {
                  "path": {"type": "string"},
                  "out_path": {"type": "string"},
                  "seconds": {"type": "number"},
                  "fps": {"type": "integer"},
                  "entry": {"type": "string"}},
               "required": ["path", "out_path"]}, access={"exec", "write"})
    async def record_program(path: str, out_path: str, ctx=None,
                             seconds: float = 6.0, fps: int = 20,
                             entry: str = "main.py"):
        from .video import capture_program
        origen = ctx.resolve(path) if ctx else Path(path)
        destino = ctx.resolve(out_path) if ctx else Path(out_path)
        if ctx and getattr(ctx, "journal", None):
            ctx.journal.record(destino, "create", tool="record_program")
        obs = await capture_program(origen, destino, seconds=float(seconds),
                                    fps=int(fps), entry=entry)
        return ToolResult(obs.ok, obs.render(),
                          error=None if obs.ok else "; ".join(obs.problems),
                          meta={"path": str(destino)})

    return reg
