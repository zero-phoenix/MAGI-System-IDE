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

    @reg.tool("studio_backends",
              "Qué se puede generar y observar en esta máquina.",
              {"type": "object", "properties": {}}, access={"read"})
    def studio_backends():
        from .artifacts import available_backends
        b = available_backends()
        lines = [f"  {'sí' if v else 'no':<4s} {k}" for k, v in b.items()]
        return ToolResult(True, "\n".join(lines))

    return reg
