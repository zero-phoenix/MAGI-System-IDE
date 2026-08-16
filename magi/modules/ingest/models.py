from typing import Any

from pydantic import BaseModel, Field


class FormatProfile(BaseModel):
    family: str = Field(..., description="e.g. 'wordprocessor', 'spreadsheet'")
    name: str = Field(..., description="e.g. 'WordPerfect 5.1'")
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    era: str | None = None
    endianness: str | None = None

class IngestAttempt(BaseModel):
    level: int
    tool: str
    ok: bool
    reason: str | None = None
    duration_ms: int | None = None

class EncodingGuess(BaseModel):
    detected: str
    confidence: float
    method: str
    line_endings: str

class IngestContent(BaseModel):
    text_ref: str
    layout_ref: str
    images: list[dict[str, Any]] = Field(default_factory=list)
    tables: int = 0
    pages: int = 1

class Fidelity(BaseModel):
    text: str = Field("completo", description="completo, aproximado, perdido")
    formato: str = Field("completo", description="completo, aproximado, perdido")
    imagenes: str = Field("completo", description="completo, aproximado, perdido")
    perdido: list[str] = Field(default_factory=list)

class Custody(BaseModel):
    original_inmutable: bool = True
    transformaciones: list[str] = Field(default_factory=list)

class IngestResult(BaseModel):
    """
    Documento Canónico (§15.3). Salida unificada de la cascada de ingesta.
    """
    ingest_id: str
    source: dict[str, Any]
    format: FormatProfile
    resolved_at_level: int
    attempts: list[IngestAttempt]
    encoding: EncodingGuess | None = None
    content: IngestContent | None = None
    fidelity: Fidelity
    status: str = Field(..., description="leido_completo, leido_parcial, abierto_en_entorno_de_epoca, no_legible")
    custody: Custody
