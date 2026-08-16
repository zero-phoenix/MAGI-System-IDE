from typing import Any, Literal

from pydantic import BaseModel, Field


class RouteDirective(BaseModel):
    role: Literal["MELCHIOR", "BALTHASAR", "CASPER", "VLM", "EMBED", "RERANK"]
    pin_model: str | None = None
    allow_remote: bool = False
    required_caps: dict[str, Any] = Field(default_factory=dict)
    strategy: Literal["priority", "lkgp", "cost-optimized", "round-robin"]
    forbid_providers: list[str] = Field(default_factory=list)
    max_tokens_in: int = 12000
    unit_id: str
    privacy_class: Literal["local_only", "consented_remote"] = "local_only"

class InferenceRequest(BaseModel):
    prompt: str
    system: str | None = None
    temperature: float = 0.7
    seed: int | None = None

class CostTelemetry(BaseModel):
    provider: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    cache_hit: bool

class ModelResponse(BaseModel):
    text: str
    telemetry: CostTelemetry
