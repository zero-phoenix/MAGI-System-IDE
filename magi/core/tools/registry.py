"""
Registro de herramientas (Plan MAGI 9.0 §2.2).

EL TECHO QUE ESTO ROMPE
=======================
En v5.0.28 los tres agentes solo podían emitir texto. Melchior escribía un plan
para analizar un firmware sin haber abierto el firmware. Balthasar criticaba ese
plan sin poder verificar nada. La única "acción" del sistema era un regex sobre
la respuesta aprobada (orchestrator.py:45) que extraía bloques ``` y los
ejecutaba a ciegas.

Era un sistema que HABLABA SOBRE trabajo en vez de HACER trabajo.

Aquí cada agente recibe un catálogo y un bucle que lo ejecuta hasta terminar.
"""
from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

logger = logging.getLogger(__name__)

Access = Literal["read", "write", "exec", "net"]


@dataclass
class ToolResult:
    ok: bool
    content: str
    tool: str = ""
    error: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def render(self, max_len: int = 8000) -> str:
        """Texto que vuelve al modelo. Truncado para no reventar el contexto."""
        body = self.content if self.ok else f"ERROR: {self.error or self.content}"
        if len(body) > max_len:
            head, tail = body[: max_len // 2], body[-max_len // 4:]
            body = f"{head}\n\n… [recortado {len(body) - len(head) - len(tail)} chars] …\n\n{tail}"
        return body


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]          # JSON Schema
    handler: Callable[..., Any]
    access: set[Access] = field(default_factory=set)
    dangerous: bool = False             # muta el sistema; se registra en journal

    #: tope de la descripción en el catálogo. El catálogo entra ENTERO en cada
    #: prompt de cada agente: si crece sin control, se come la ventana de un
    #: proveedor gratuito y el bucle de herramientas revienta a la 3ª iteración.
    MAX_DESC = 90

    #: nombres de tipo abreviados. El significado es el mismo y una firma de
    #: seis parámetros baja de 200 caracteres a 180.
    _TYPE_ABBR = {"string": "str", "integer": "int", "boolean": "bool",
                  "number": "num", "array": "list", "object": "obj"}

    def signature(self) -> str:
        """Línea compacta para el prompt."""
        props = self.parameters.get("properties", {})
        required = set(self.parameters.get("required", []))
        args = ", ".join(
            f"{k}{'' if k in required else '?'}:"
            f"{self._TYPE_ABBR.get(v.get('type', 'any'), v.get('type', 'any'))}"
            for k, v in props.items()
        )
        # Primera frase, y recortada: la descripción larga sirve para el
        # esquema JSON, no para el listado que ve el modelo en cada turno.
        desc = self.description.split(". ")[0].strip().rstrip(".")
        if len(desc) > self.MAX_DESC:
            desc = desc[:self.MAX_DESC].rsplit(" ", 1)[0] + "…"
        return f"{self.name}({args}) — {desc}"

    def to_openai_schema(self) -> dict[str, Any]:
        return {"type": "function", "function": {
            "name": self.name, "description": self.description,
            "parameters": self.parameters}}


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def tool(self, name: str, description: str, parameters: dict[str, Any],
             access: set[Access] | None = None, dangerous: bool = False):
        """Decorador de registro."""
        def deco(fn):
            self.register(Tool(name, description, parameters, fn,
                               access or set(), dangerous))
            return fn
        return deco

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return sorted(self._tools)

    def subset(self, allowed: set[str] | None = None,
               deny_access: set[Access] | None = None) -> ToolRegistry:
        """
        Vista filtrada. Se usa para dar a Balthasar lectura y ejecución pero no
        escritura — que no es una restricción de seguridad, es lo que le da
        AUTORIDAD: una crítica que dice "esto falla con entrada vacía" habiendo
        ejecutado el caso vale mucho más que una que lo sospecha.
        """
        out = ToolRegistry()
        for name, t in self._tools.items():
            if allowed is not None and name not in allowed:
                continue
            if deny_access and (t.access & deny_access):
                continue
            out.register(t)
        return out

    def catalog(self) -> str:
        return "\n".join(f"- {t.signature()}" for t in
                         sorted(self._tools.values(), key=lambda t: t.name))

    def to_openai_schemas(self) -> list[dict[str, Any]]:
        return [t.to_openai_schema() for t in self._tools.values()]

    async def execute(self, name: str, args: dict[str, Any],
                      ctx: Any = None) -> ToolResult:
        tool = self.get(name)
        if tool is None:
            return ToolResult(False, "", name,
                              f"herramienta desconocida '{name}'. "
                              f"Disponibles: {', '.join(self.names())}")
        try:
            sig = inspect.signature(tool.handler)
            call_args = dict(args)
            if "ctx" in sig.parameters:
                call_args["ctx"] = ctx
            # descarta argumentos que el handler no acepta (los modelos
            # gratuitos alucinan parámetros con frecuencia)
            if not any(p.kind is inspect.Parameter.VAR_KEYWORD
                       for p in sig.parameters.values()):
                call_args = {k: v for k, v in call_args.items()
                             if k in sig.parameters}
            result = tool.handler(**call_args)
            if inspect.isawaitable(result):
                result = await result
            if isinstance(result, ToolResult):
                result.tool = name
                return result
            return ToolResult(True, str(result), name)
        except TypeError as e:
            return ToolResult(False, "", name, f"argumentos inválidos: {e}")
        except Exception as e:
            logger.exception("[tools] %s falló", name)
            return ToolResult(False, "", name, f"{type(e).__name__}: {e}")

    async def execute_many(self, calls: list[tuple[str, dict]],
                           ctx: Any = None) -> list[ToolResult]:
        """Ejecuta en paralelo cuando el modelo pide varias a la vez."""
        return list(await asyncio.gather(
            *(self.execute(n, a, ctx) for n, a in calls)))
