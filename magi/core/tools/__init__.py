"""Sistema de herramientas de MAGI 9.0."""
from .journal import WriteJournal, JournalEntry
from .registry import Tool, ToolRegistry, ToolResult
from .protocol import (
    parse_tool_calls, strip_tool_calls, format_results, build_system_suffix,
)
from .builtin import ToolContext, build_registry, registry_for_role

__all__ = [
    "WriteJournal", "JournalEntry",
    "Tool", "ToolRegistry", "ToolResult",
    "parse_tool_calls", "strip_tool_calls", "format_results", "build_system_suffix",
    "ToolContext", "build_registry", "registry_for_role",
]
