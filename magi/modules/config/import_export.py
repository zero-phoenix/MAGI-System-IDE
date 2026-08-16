import logging
from typing import Any

from ruamel.yaml import YAML

from .schema import ConfigDeclarationRegister

logger = logging.getLogger(__name__)

class ConfigImporter:
    """
    A17-3: Importación segura de configuración compartida.
    """

    def __init__(self, register: ConfigDeclarationRegister):
        self.register = register
        self.yaml = YAML()
        self.yaml.preserve_quotes = True

    # Parámetros estrictamente protegidos que nunca se pueden importar de un tercero
    FORBIDDEN_IMPORTS = [
        "safety.quarantine.disable",
        "safety.r3.automatic",
        "route.privacy.disable_classes",
        "hardware.limits.override",
        "debate.rounds.min"  # A17-3: Protegido contra reducción hostil
    ]

    def import_yaml(self, filepath: str, current_config: dict[str, Any]) -> tuple[bool, dict[str, Any], list]:
        """
        Lee un YAML y lo valida. Rechaza cambios hostiles de seguridad.
        Retorna (exito, config_aceptada, mensajes_rechazo).
        """
        try:
            with open(filepath, encoding='utf-8') as f:
                imported = self.yaml.load(f) or {}
        except Exception as e:
            logger.error(f"Error leyendo YAML de configuración: {e}")
            return False, {}, ["Archivo inválido"]

        accepted_changes = {}
        rejected_messages = []

        # 1. Validar contra esquemas
        for k, v in imported.items():
            schema = self.register.get_field(k)
            if not schema:
                rejected_messages.append(f"Rechazado: '{k}' es desconocido (no se ignora en silencio).")
                continue

            # 3. RECHAZAR sin excepción cambios hostiles
            if self._is_forbidden_change(k, v, current_config, schema):
                rejected_messages.append(f"Rechazado (Seguridad): Cambio a '{k}' violaría políticas duras.")
                continue

            accepted_changes[k] = v

        return True, accepted_changes, rejected_messages

    def _is_forbidden_change(self, path: str, new_value: Any, current_config: dict[str, Any], schema) -> bool:
        """
        Detecta si un cambio vulnera la seguridad física o desactiva protecciones.
        """
        # Regla dura: rounds.min no puede bajar de 3
        if path == "debate.rounds.min" and int(new_value) < 3:
            return True

        if path in self.FORBIDDEN_IMPORTS:
            return True

        # Intentar superar el límite físico del esquema
        if schema.maximum is not None and isinstance(new_value, (int, float)):
            if new_value > schema.maximum:
                return True

        return False
