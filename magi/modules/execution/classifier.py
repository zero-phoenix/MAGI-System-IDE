from typing import Any


class ErrorClassifier:
    """
    Clasificador de Errores (P8.3).
    Traduce stderr/exit_codes a Clases de Error Refutables.
    """
    def __init__(self):
        pass

    def classify(self, execution_record: dict[str, Any]) -> str:
        code = execution_record.get("exit_code", 0)
        stderr = execution_record.get("stderr", "")

        if code == 0:
            return "ok"

        if "SyntaxError" in stderr or "Parse error" in stderr:
            return "sintaxis"

        if code == 139 or "Segmentation fault" in stderr:
            return "runtime"

        return "logico"
