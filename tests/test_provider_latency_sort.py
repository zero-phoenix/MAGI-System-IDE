"""
Tests para la ordenación de proveedores por latencia p95 en ProviderRegistry.
"""
import pytest

from magi.core.providers.base import BaseProvider, CompletionRequest, CompletionResponse, Usage
from magi.core.providers.registry import ProviderRegistry


class _SlowProvider(BaseProvider):
    id = "g4f-slow"
    family = "slow"
    is_local = True
    supports_tools = False
    supports_vision = False
    supports_stream = False

    async def complete(self, req: CompletionRequest):
        return CompletionResponse(
            provider_id=self.id, model="m", family=self.family,
            content="ok", usage=Usage(1, 1))


class _FastProvider(BaseProvider):
    id = "g4f-fast"
    family = "fast"
    is_local = True
    supports_tools = False
    supports_vision = False
    supports_stream = False

    async def complete(self, req: CompletionRequest):
        return CompletionResponse(
            provider_id=self.id, model="m", family=self.family,
            content="ok", usage=Usage(1, 1))


def test_candidates_sorted_by_latency():
    reg = ProviderRegistry()
    reg.register(_SlowProvider(), priority=50)
    reg.register(_FastProvider(), priority=100)

    # Simular latencias observadas
    slow = reg.get("g4f-slow")
    fast = reg.get("g4f-fast")
    for _ in range(10):
        slow.breaker.record_success(5000.0)   # 5 s
        fast.breaker.record_success(200.0)      # 200 ms

    cands = reg._candidates(prefer=None, need_tools=False, need_vision=False)
    ids = [r.id for r in cands]
    assert ids[0] == "g4f-fast"
    assert ids[1] == "g4f-slow"


def test_prefer_overrides_latency():
    reg = ProviderRegistry()
    reg.register(_SlowProvider(), priority=50)
    reg.register(_FastProvider(), priority=100)

    slow = reg.get("g4f-slow")
    fast = reg.get("g4f-fast")
    for _ in range(10):
        slow.breaker.record_success(5000.0)
        fast.breaker.record_success(200.0)

    cands = reg._candidates(
        prefer="g4f-slow", need_tools=False, need_vision=False)
    ids = [r.id for r in cands]
    assert ids[0] == "g4f-slow"
