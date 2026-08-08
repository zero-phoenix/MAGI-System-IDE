"""Sistema de herramientas de MAGI 9.0."""
from .journal import WriteJournal, JournalEntry
from .registry import Tool, ToolRegistry, ToolResult
from .protocol import (
    parse_tool_calls, strip_tool_calls, format_results, build_system_suffix,
)
from .builtin import (
    ToolContext, build_registry, registry_for_role,
    # Estos cuatro se reexportan porque el resto del sistema los necesita y
    # los estaba importando de aquí. `ALL_DOMAINS` faltaba, y el kernel hacía
    # `from magi.core.tools import ALL_DOMAINS`: el handler `sys.config`
    # lanzaba ImportError en CADA llamada, la interfaz lo reintentaba, y el
    # error acabó congelando el sistema entero (ver magi/core/bus.py).
    #
    # Un módulo que se importa desde fuera tiene que decir explícitamente qué
    # ofrece. Aquí faltaba un nombre y no había forma de enterarse hasta que
    # alguien pulsaba una pestaña.
    ALL_DOMAINS, CORE_TOOLS, DEVOPS_TOOLS, domains_for,
)

__all__ = [
    "WriteJournal", "JournalEntry",
    "Tool", "ToolRegistry", "ToolResult",
    "parse_tool_calls", "strip_tool_calls", "format_results", "build_system_suffix",
    "ToolContext", "build_registry", "registry_for_role",
    "ALL_DOMAINS", "CORE_TOOLS", "DEVOPS_TOOLS", "domains_for",
]
