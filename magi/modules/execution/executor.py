import time
from typing import Any


class IsolatedExecutor:
    """
    Ejecutor de Procesos (P8.2).
    Captura stdio, estado de salida y gestiona Snapshots.
    """
    def __init__(self):
        pass

    def _create_snapshot(self) -> str:
        """Simula crear un commit de pygit2 para reversibilidad."""
        return "snap_12345"

    def execute(self, action: dict[str, Any]) -> dict[str, Any]:
        """Simula la ejecución controlada de una herramienta."""
        snapshot = None
        if action.get("radius") in ["R1", "R2"]:
            snapshot = self._create_snapshot()

        # Simular ejecución
        time.sleep(0.1)

        # Simulación de éxito/fallo inyectada
        if "fail_syntax" in action.get("params", {}):
            return {"exit_code": 1, "stderr": "SyntaxError: invalid syntax at line 4", "snapshot": snapshot}
        if "fail_logic" in action.get("params", {}):
            return {"exit_code": 139, "stderr": "Segmentation fault (core dumped)", "snapshot": snapshot}

        return {"exit_code": 0, "stdout": "Success", "snapshot": snapshot}
