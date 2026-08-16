from typing import Any

from pydantic import BaseModel, Field


class ConfigField(BaseModel):
    path: str
    type_name: str
    default: Any
    minimum: Any | None = None
    maximum: Any | None = None
    label: str
    effect: str
    consequence_if_lower: str | None = None
    cost_hint: str | None = None
    gate: str
    restart_required: bool = False
    scope_allowed: list[str] = Field(default_factory=lambda: ["global", "project", "turn"])

class ConfigDeclarationRegister:
    """
    Registro global de esquemas. Genera la pantalla y valida tipos.
    """
    def __init__(self):
        self.fields: dict[str, ConfigField] = {}
        self._bootstrap_core_schema()

    def register_field(self, field: ConfigField):
        self.fields[field.path] = field

    def get_field(self, path: str) -> ConfigField | None:
        return self.fields.get(path)

    def _bootstrap_core_schema(self):
        # Debate
        self.register_field(ConfigField(
            path="debate.rounds.min",
            type_name="int",
            default=3,
            minimum=3,
            maximum=12,
            label="Rondas mínimas de deliberación",
            effect="Ninguna deliberación terminará antes de este número de rondas, aunque haya acuerdo.",
            consequence_if_lower="No se puede bajar de 3: una sola pasada no es deliberación.",
            cost_hint="Cada ronda adicional cuesta ~23 000 tokens.",
            gate="PV-3.b.4"
        ))
        self.register_field(ConfigField(
            path="debate.rounds.max",
            type_name="int",
            default=7,
            minimum=3,
            maximum=20,
            label="Rondas máximas de deliberación",
            effect="Fuerza un consenso o cierre del debate tras este número de rondas.",
            gate="PV-3.b.4"
        ))
        # Rúbrica
        self.register_field(ConfigField(
            path="debate.rubric.weight.accuracy", type_name="int", default=40, minimum=0, maximum=100, label="Peso de precisión", effect="Afecta puntuación del juez.", gate="PV-3"
        ))
        self.register_field(ConfigField(
            path="debate.rubric.weight.speed", type_name="int", default=30, minimum=0, maximum=100, label="Peso de velocidad", effect="Afecta puntuación del juez.", gate="PV-3"
        ))
        self.register_field(ConfigField(
            path="debate.rubric.weight.safety", type_name="int", default=30, minimum=0, maximum=100, label="Peso de seguridad", effect="Afecta puntuación del juez.", gate="PV-3"
        ))
        # Seguridad física
        self.register_field(ConfigField(
            path="security.max_temp",
            type_name="float",
            default=240.0,
            maximum=260.0,
            label="Temperatura máxima del extrusor",
            effect="Límite duro de firmware para evitar incendios.",
            gate="PV-9.a",
            restart_required=True
        ))
        # Red/Portables
        self.register_field(ConfigField(
            path="os_portable.network",
            type_name="str",
            default="none",
            label="Red por defecto en VM",
            effect="Permitir salida de red a la máquina virtual.",
            gate="CTL-4"
        ))
