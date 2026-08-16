import os
from typing import Any


class PolicyManager:
    """
    Gestor de Políticas (P10.c).
    Fuerza el modelo de capacidades (Sandbox Lógico).
    """
    def __init__(self):
        self.hard_black_list = [
            "C:\\Windows",
            "C:\\Program Files",
            "/boot", "/etc", "/usr", "/bin", "/sbin", "/lib",
            "~/.ssh", "~/.gnupg"
        ]
        # Política default
        self.policy = {
            "fs.write": {"allow": ["${PROJECT}/workspace/**", "${PROJECT}/artifacts/**"]}
        }

    def _is_in_blacklist(self, path: str) -> bool:
        normalized = os.path.normpath(path)
        for black_item in self.hard_black_list:
            if normalized.startswith(os.path.normpath(black_item)):
                return True
        return False

    def check_permission(self, capability: str, params: dict[str, Any]) -> dict:
        """
        Evalúa si la acción está permitida, denegada por política, o bloqueada por lista negra dura.
        """
        if capability == "fs.write":
            path = params.get("path", "")

            if self._is_in_blacklist(path):
                return {"status": "denied", "reason": "HARD_BLACKLIST: Ruta de sistema protegida"}

            # Evaluacion simplificada de la política
            if "${PROJECT}/workspace" in path:
                return {"status": "allowed"}
            return {"status": "denied", "reason": "Not explicitly allowed in policy.yaml"}

        elif capability == "proc.spawn":
            binary = params.get("binary", "")
            if binary in ["yosys", "prusa-slicer", "ghidra"]:
                return {"status": "allowed"}
            return {"status": "denied", "reason": "Binary not in allow_binaries catalog"}

        return {"status": "denied", "reason": "Unknown capability"}
