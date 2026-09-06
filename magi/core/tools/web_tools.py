"""
Herramientas de percepción web sin navegador (F1).

Registra web_search y web_read con presupuesto y citas URL+fecha.
"""
from __future__ import annotations

from .builtin import ToolContext, ToolResult


def registrar(reg) -> None:
    @reg.tool(
        "web_search",
        "Búsqueda web sin navegador (HTML): devuelve títulos, URLs y extractos "
        "con fecha de consulta obligatoria. Presupuesto limitado por ronda.",
        {
            "type": "object",
            "properties": {
                "consulta": {
                    "type": "string",
                    "description": "término o frase de búsqueda",
                },
                "limite": {
                    "type": "integer",
                    "description": "número máximo de resultados (defecto: 5)",
                },
            },
            "required": ["consulta"],
        },
        access={"net"},
    )
    def web_search_tool(consulta: str, ctx: ToolContext, limite: int = 5):
        from ...modules.percepcion.web import web_search
        ok, msg, _ = web_search(consulta, limite=limite, task_id=ctx.task_id or "")
        return ToolResult(ok, msg if ok else "", error="" if ok else msg)

    @reg.tool(
        "web_read",
        "Lectura web sin navegador: extrae texto legible con límite de tamaño "
        "(máx 1 redirección HTTP) y cita obligatoria con URL y fecha.",
        {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL http:// o https:// a leer",
                },
                "max_chars": {
                    "type": "integer",
                    "description": "máximo de caracteres de texto a retornar (defecto: 4000)",
                },
            },
            "required": ["url"],
        },
        access={"net"},
    )
    def web_read_tool(url: str, ctx: ToolContext, max_chars: int = 4000):
        from ...modules.percepcion.web import web_read
        ok, msg, _ = web_read(url, max_chars=max_chars, task_id=ctx.task_id or "")
        return ToolResult(ok, msg if ok else "", error="" if ok else msg)
