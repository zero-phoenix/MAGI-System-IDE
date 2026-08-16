from magi.modules.config.schema import ConfigDeclarationRegister


class ConfigValidator:
    """
    Validador Cruzado Estricto (P17.c).
    Garantiza que no se puedan inyectar configuraciones peligrosas.
    """
    def __init__(self):
        self.schema = ConfigDeclarationRegister()

    def validate_import(self, incoming_config: dict) -> dict:
        """
        Rechaza configuraciones inválidas o peligrosas (ej: rounds.min < 3).
        """
        for key, value in incoming_config.items():
            field_def = self.schema.get_field(key)
            if not field_def:
                continue

            # Regla: debate.rounds.min nunca puede ser menor que 3
            if key == "debate.rounds.min":
                if value < field_def.minimum:
                    return {"success": False, "reason": f"Value {value} for {key} is below absolute minimum of {field_def.minimum}"}

            # Regla: topes de seguridad
            if key == "security.max_temp":
                if value > field_def.maximum:
                    return {"success": False, "reason": f"Value {value} for {key} exceeds factory maximum of {field_def.maximum}"}

        return {"success": True, "validated_config": incoming_config}
