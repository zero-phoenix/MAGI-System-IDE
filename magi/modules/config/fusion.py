import hashlib
import json
import logging
from typing import Any

from .schema import ConfigDeclarationRegister

logger = logging.getLogger(__name__)

class ConfigFusionEngine:
    """
    A17-1: Fusión por capas con trazabilidad de origen y validación cruzada.
    Capas: 1 (Fábrica) -> 2 (Máquina) -> 3 (Usuario) -> 4 (Proyecto) -> 5 (Turno)
    """

    LAYERS = ["factory", "machine", "user", "project", "turn"]

    def __init__(self, register: ConfigDeclarationRegister):
        self.register = register
        self.effective_config: dict[str, Any] = {}
        # path -> (valor, capa_origen, capa_sobreescrita)
        self.traceability: dict[str, tuple[Any, str, str | None]] = {}
        self.current_hash: str = ""

    def fuse_layers(self, layer_data: dict[str, dict[str, Any]]) -> bool:
        """
        Fusiona las capas y valida cruzadamente.
        Si la validación falla, NO se aplica nada.
        """
        temp_config = {}
        temp_trace = {}

        for layer_name in self.LAYERS:
            data = layer_data.get(layer_name, {})
            for path, value in data.items():
                field_def = self.register.get_field(path)
                if not field_def:
                    logger.warning(f"Campo desconocido o huérfano ignorado durante fusión: {path}")
                    continue

                # Trazabilidad
                overwritten = temp_trace.get(path, (None, None, None))[1]
                temp_trace[path] = (value, layer_name, overwritten)
                temp_config[path] = value

        # 4. Validar el resultado COMPLETO (restricciones cruzadas A17-1.4)
        if not self._cross_validate(temp_config):
            return False

        self.effective_config = temp_config
        self.traceability = temp_trace
        self.current_hash = self._compute_hash(temp_config)
        logger.info(f"Fusión completada. Hash efectivo: {self.current_hash}")
        return True

    def _cross_validate(self, config: dict[str, Any]) -> bool:
        """
        Validación cruzada obligatoria A17-1.4
        """
        issues = []

        # 4.1 Pesos de rúbrica deben sumar 100
        acc = config.get("debate.rubric.weight.accuracy", 40)
        spd = config.get("debate.rubric.weight.speed", 30)
        sft = config.get("debate.rubric.weight.safety", 30)

        total_weight = acc + spd + sft
        if total_weight != 100:
            issues.append(f"Los pesos de la rúbrica suman {total_weight}, pero deben sumar 100 exactamente.")

        # 4.2 rounds.min <= rounds.max y rounds.min >= 3
        r_min = config.get("debate.rounds.min", 3)
        r_max = config.get("debate.rounds.max", 7)
        if r_min < 3:
            issues.append(f"debate.rounds.min no puede ser inferior a 3. Valor propuesto: {r_min}")
        if r_min > r_max:
            issues.append(f"debate.rounds.min ({r_min}) no puede superar a debate.rounds.max ({r_max}).")

        # 4.3 Límites físicos (Área 9) no pueden superar los de fábrica
        factory_temp = self.register.get_field("security.max_temp").maximum
        req_temp = config.get("security.max_temp", 240.0)
        if req_temp > factory_temp:
            issues.append(f"La temperatura máxima ({req_temp}) supera el tope físico de fábrica ({factory_temp}).")

        if issues:
            for issue in issues:
                logger.error(f"Validación cruzada fallida: {issue}")
            return False

        return True

    def _compute_hash(self, config: dict[str, Any]) -> str:
        # A17-1.6 Hash de procedencia
        # Ordenamos las claves para garantizar determinismo
        serialized = json.dumps(config, sort_keys=True)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    def get_effective_value(self, path: str) -> Any:
        return self.effective_config.get(path)

    def get_traceability(self, path: str) -> tuple[Any, str, str | None]:
        return self.traceability.get(path, (None, None, None))
