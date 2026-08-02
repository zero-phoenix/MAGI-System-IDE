from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ProviderCircuitState:
    state: str = "closed" # closed, open, half_open
    failures: int = 0
    opened_at: Optional[float] = None

@dataclass
class ProviderStats:
    latency_ms_ewma: float = 1000.0
    error_rate_ewma: float = 0.0

@dataclass
class ProviderCapabilities:
    max_context: int
    vision: bool
    tools: bool
    structured_output: str

@dataclass
class ProviderDef:
    id: str
    kind: str # local, oficial-gratuito
    endpoint: Optional[str]
    models: List[str]
    capabilities: ProviderCapabilities
    cost: float
    circuit: ProviderCircuitState
    stats: ProviderStats
    
class ProviderRegistry:
    """
    Gestor de proveedores y estado en memoria.
    """
    def __init__(self):
        self.providers: Dict[str, ProviderDef] = {}
        # Hardcode default providers for MVP
        self._register_default_providers()
        
    def _register_default_providers(self):
        self.providers["local-text"] = ProviderDef(
            id="local-text",
            kind="local",
            endpoint="http://127.0.0.1:8081/v1",
            models=["qwen2.5-coder-7b-q5km"],
            capabilities=ProviderCapabilities(32768, False, False, "gbnf"),
            cost=0.0,
            circuit=ProviderCircuitState(),
            stats=ProviderStats()
        )
        self.providers["local-vlm"] = ProviderDef(
            id="local-vlm",
            kind="local",
            endpoint="http://127.0.0.1:8082/v1",
            models=["qwen2-vl-7b-q4km"],
            capabilities=ProviderCapabilities(32768, True, False, "gbnf"),
            cost=0.0,
            circuit=ProviderCircuitState(),
            stats=ProviderStats()
        )
        self.providers["claude-code-cli"] = ProviderDef(
            id="claude-code-cli",
            kind="nube",
            endpoint=None,
            models=["claude-3-5-sonnet"],
            capabilities=ProviderCapabilities(200000, True, True, "schema+retry"),
            cost=0.0,
            circuit=ProviderCircuitState(),
            stats=ProviderStats()
        )
        self.providers["openai-gpt4o"] = ProviderDef(
            id="openai-gpt4o",
            kind="nube",
            endpoint="api.openai.com",
            models=["gpt-4o"],
            capabilities=ProviderCapabilities(128000, True, True, "schema+retry"),
            cost=0.0,
            circuit=ProviderCircuitState(),
            stats=ProviderStats()
        )
        self.providers["google-gemini-1.5"] = ProviderDef(
            id="google-gemini-1.5",
            kind="nube",
            endpoint="generativelanguage.googleapis.com",
            models=["gemini-1.5-pro", "gemini-1.5-flash"],
            capabilities=ProviderCapabilities(1000000, True, True, "schema+retry"),
            cost=0.0,
            circuit=ProviderCircuitState(),
            stats=ProviderStats()
        )
        self.providers["anthropic-claude-3-opus"] = ProviderDef(
            id="anthropic-claude-3-opus",
            kind="nube",
            endpoint="api.anthropic.com",
            models=["claude-3-opus-20240229"],
            capabilities=ProviderCapabilities(200000, True, True, "schema+retry"),
            cost=0.0,
            circuit=ProviderCircuitState(),
            stats=ProviderStats()
        )
        self.providers["mistral-large"] = ProviderDef(
            id="mistral-large",
            kind="nube",
            endpoint="api.mistral.ai",
            models=["mistral-large-latest"],
            capabilities=ProviderCapabilities(32000, False, True, "schema+retry"),
            cost=0.0,
            circuit=ProviderCircuitState(),
            stats=ProviderStats()
        )
        self.providers["deepseek-chat"] = ProviderDef(
            id="deepseek-chat",
            kind="nube",
            endpoint="api.deepseek.com",
            models=["deepseek-chat"],
            capabilities=ProviderCapabilities(64000, False, True, "schema+retry"),
            cost=0.0,
            circuit=ProviderCircuitState(),
            stats=ProviderStats()
        )
        self.providers["openrouter-fallback"] = ProviderDef(
            id="openrouter-fallback",
            kind="nube",
            endpoint="openrouter.ai/api",
            models=["auto"],
            capabilities=ProviderCapabilities(64000, True, True, "schema+retry"),
            cost=0.0,
            circuit=ProviderCircuitState(),
            stats=ProviderStats()
        )
        
    def get_provider(self, provider_id: str) -> Optional[ProviderDef]:
        return self.providers.get(provider_id)
        
    def update_stats(self, provider_id: str, latency: float, error: bool):
        p = self.get_provider(provider_id)
        if p:
            alpha = 0.1
            p.stats.latency_ms_ewma = (alpha * latency) + ((1 - alpha) * p.stats.latency_ms_ewma)
            err_val = 1.0 if error else 0.0
            p.stats.error_rate_ewma = (alpha * err_val) + ((1 - alpha) * p.stats.error_rate_ewma)
