from typing import Any


class PreflightChecker:
    """
    Comprobaciones Previas de Seguridad (P8.1).
    Valida Radio de Impacto e intercepta acciones destructivas sin confirmación.
    """
    def __init__(self):
        pass

    def run_preflight(self, action: dict[str, Any]) -> dict[str, Any]:
        radius = action.get("radius", "R0")

        # Validación de Radio (Anti-Disfraz)
        # Si la acción dice ser R1 (Inerte) pero invoca "fs.format" o "mcu.erase", rechazar.
        kind = action.get("kind", "")
        if "erase" in kind or "format" in kind:
            if radius != "R3":
                return {"status": "rejected", "reason": "radio_infravalorado: Acción destructiva declarada como no destructiva."}

        # Validación R3 Humana
        if radius == "R3" and not action.get("human_confirmed", False):
            return {"status": "awaiting_human", "reason": "La acción R3 requiere confirmación humana explícita."}

        return {"status": "ok"}
