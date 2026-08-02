import yaml
import logging
from typing import Dict, Any, Tuple
from pathlib import Path
from .schema import ConfigDeclarationRegister

logger = logging.getLogger(__name__)

class ConfigImporter:
    """
    A17-3: Importación segura de configuración compartida.
    """
    
    # Parámetros estrictamente protegidos que nunca se pueden importar de un tercero
    FORBIDDEN_IMPORTS = [
        "safety.quarantine.disable",
        "safety.r3.automatic",
        "route.privacy.disable_classes",
        "hardware.limits.override"
    ]

    def import_yaml(self, filepath: str, current_config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], list]:
        """
        Lee un YAML y lo valida. Rechaza cambios hostiles de seguridad.
        Retorna (exito, config_aceptada, mensajes_rechazo).
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error leyendo YAML de configuración: {e}")
            return False, {}, ["Archivo inválido"]
            
        accepted_changes = {}
        rejected_messages = []
        
        # 1. Validar contra esquemas
        for k, v in imported.items():
            schema = ConfigDeclarationRegister.get_schema(k)
            if not schema:
                rejected_messages.append(f"Rechazado: '{k}' es desconocido.")
                continue
                
            # 3. RECHAZAR sin excepción cambios hostiles
            if self._is_forbidden_change(k, v, current_config):
                rejected_messages.append(f"Rechazado (Seguridad): '{k}' violaría límites de seguridad.")
                continue
                
            accepted_changes[k] = v
            
        return True, accepted_changes, rejected_messages

    def _is_forbidden_change(self, path: str, new_value: Any, current_config: Dict[str, Any]) -> bool:
        """
        Detecta si un cambio vulnera la seguridad física o desactiva protecciones.
        """
        if path in self.FORBIDDEN_IMPORTS:
            return True
            
        # Ejemplo: reducir la lista negra por debajo del mínimo no se permite
        if path == "security.blacklist.paths":
            current_list = current_config.get(path, [])
            if len(new_value) < len(current_list): # Simplificación
                return True
                
        return False
