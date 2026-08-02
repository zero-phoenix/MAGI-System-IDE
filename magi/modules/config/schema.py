class ConfigSchema:
    """
    Esquemas de Configuración (P17.a).
    Define los campos disponibles.
    """
    def __init__(self):
        self.fields = {
            "debate.rounds.min": {
                "type": int,
                "default": 3,
                "minimum": 3,
                "maximum": 12,
                "gate": "PV-3.b.4"
            },
            "security.max_temp": {
                "type": float,
                "default": 240.0,
                "maximum": 260.0, # Tope físico de fábrica
                "gate": "PV-9.a"
            }
        }
        
    def get_field(self, path: str) -> dict:
        return self.fields.get(path)
