from typing import Any

from .classifier import ErrorClassifier
from .estop import EmergencyStop
from .executor import IsolatedExecutor
from .preflight import PreflightChecker


class ExecutionEngine:
    """
    Motor Central de Ejecución (P8.5).
    """
    def __init__(self):
        self.preflight = PreflightChecker()
        self.executor = IsolatedExecutor()
        self.classifier = ErrorClassifier()
        self.estop = EmergencyStop()

    def step(self, action: dict[str, Any]) -> dict[str, Any]:
        """
        Paso completo de Ejecución.
        """
        # 1. E-STOP Check
        self.estop.check()

        # 2. Preflight
        pre_res = self.preflight.run_preflight(action)
        if pre_res["status"] != "ok":
            return {"status": pre_res["status"], "reason": pre_res.get("reason", "Unknown preflight error")}

        # 3. Ejecutar
        exec_record = self.executor.execute(action)

        # 4. Clasificar
        err_class = self.classifier.classify(exec_record)

        if err_class != "ok":
            return {
                "status": "failed",
                "error_class": err_class,
                "snapshot": exec_record.get("snapshot"),
                "detail": exec_record.get("stderr", "")
            }

        return {"status": "success", "snapshot": exec_record.get("snapshot")}
