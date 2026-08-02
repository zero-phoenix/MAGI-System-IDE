from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Param(BaseModel):
    name: str
    value: float
    unit: str
    range: List[float]
    sensitivity: str

class Principle(BaseModel):
    summary: str
    physical_domain: List[str]
    governing_equations: List[str]
    key_phenomena: List[str]

class Invention(BaseModel):
    """
    Esquema paramétrico formal de la Invención (P11.a).
    """
    invention_id: str
    version: int
    title: str
    domain: str
    operating_principle: Principle
    parameter_vector: List[Param]
    trl: int
    killer_hypothesis: str
    
    def validate_schema(self) -> bool:
        """Validación extra más allá de Pydantic si es necesario."""
        if not self.killer_hypothesis:
            raise ValueError("Killer hypothesis is empty")
        return True
