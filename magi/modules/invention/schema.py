
from pydantic import BaseModel


class Param(BaseModel):
    name: str
    value: float
    unit: str
    range: list[float]
    sensitivity: str

class Principle(BaseModel):
    summary: str
    physical_domain: list[str]
    governing_equations: list[str]
    key_phenomena: list[str]

class Invention(BaseModel):
    """
    Esquema paramétrico formal de la Invención (P11.a).
    """
    invention_id: str
    version: int
    title: str
    domain: str
    operating_principle: Principle
    parameter_vector: list[Param]
    trl: int
    killer_hypothesis: str

    def validate_schema(self) -> bool:
        """Validación extra más allá de Pydantic si es necesario."""
        if not self.killer_hypothesis:
            raise ValueError("Killer hypothesis is empty")
        return True
