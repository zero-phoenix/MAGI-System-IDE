from .base import BaseProvider
from .claude_cli import ClaudeCodeCLIProvider
from .cloud_api import CloudAPIProvider


def get_provider(name: str) -> BaseProvider:
    """Factory para instanciar el proveedor adecuado."""
    if name == "claude-code-cli":
        return ClaudeCodeCLIProvider()
    elif name.startswith("cloud-"):
        return CloudAPIProvider(name)
    else:
        raise ValueError(f"Proveedor desconocido: {name}")
