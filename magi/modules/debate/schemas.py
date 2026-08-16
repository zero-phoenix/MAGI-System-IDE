
from pydantic import BaseModel, Field


class Tesis(BaseModel):
    """
    Hipótesis inicial generada por Melchior.
    """
    afirmacion: str = Field(..., description="La afirmación principal deducida del documento")
    evidencia_id: str = Field(..., description="ID de la unidad (Area 1 o Area 2) que soporta esto")
    confianza: float = Field(..., ge=0.0, le=1.0)

class Refutacion(BaseModel):
    """
    Argumento hostil generado por Balthasar.
    """
    valido: bool = Field(..., description="¿Es válida la Tesis?")
    mecanismo: str = Field(..., description="Mecanismo lógico o empírico de la refutación")
    evidencia_contra_id: str | None = Field(None, description="ID de la unidad que contradice la tesis")

class Acta(BaseModel):
    """
    Veredicto final de Casper.
    """
    tesis_id: str
    veredicto: str = Field(..., description="aprobado, rechazado, o undecided")
    score: float = Field(..., description="Puntuación matemática de la rúbrica")
    justificacion: str
