from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Any, Dict

class RouteDirective(BaseModel):
    role: Literal["MELCHIOR", "BALTHASAR", "CASPER", "VLM", "EMBED", "RERANK"]
    pin_model: Optional[str] = None
    allow_remote: bool = False
    required_caps: Dict[str, Any] = Field(default_factory=dict)
    strategy: Literal["priority", "lkgp", "cost-optimized", "round-robin"]
    forbid_providers: List[str] = Field(default_factory=list)
    max_tokens_in: int = 12000
    unit_id: str
    privacy_class: Literal["local_only", "consented_remote"] = "local_only"

class InferenceRequest(BaseModel):
    prompt: str
    system: Optional[str] = None
    temperature: float = 0.7
    seed: Optional[int] = None

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
