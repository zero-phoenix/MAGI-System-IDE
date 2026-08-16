class SpecError(Exception):
    pass

class MediaSpec:
    """
    Especificación Medible (P20.a).
    Toda solicitud debe tener criterios medibles duros ('hard').
    """
    def __init__(self, request: str, acceptance_criteria: list):
        self.request = request
        self.acceptance_criteria = acceptance_criteria
        self._validate()

    def _validate(self):
        has_hard_criteria = any(c.get('hard', False) for c in self.acceptance_criteria)
        if not has_hard_criteria:
             raise SpecError("Se requieren criterios de aceptación duros (hard=True) para generar la obra.")

    def get_hard_criteria(self) -> list:
        return [c for c in self.acceptance_criteria if c.get('hard', False)]
