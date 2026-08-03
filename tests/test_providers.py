"""
Tests de la capa de proveedores — la regresión que más importa evitar.

El bug central de v5.0.28 (los tres agentes colapsando al mismo modelo) habría
sido detectado por test_swarm_gets_distinct_families en cuanto se escribió.
"""
import asyncio

import pytest

from magi.core.providers.base import (
    CompletionRequest, Message, ProviderError, ProviderState,
)
from magi.core.providers.cache import TTLCache, make_key
from magi.core.providers.circuit import CircuitBreaker
from magi.core.providers.registry import ProviderRegistry
from magi.core.providers.backends.echo import EchoProvider


def _req(text="hola"):
    return CompletionRequest(messages=[Message("user", text)])


# ------------------------------------------------------------------ diversidad

@pytest.mark.asyncio
async def test_swarm_gets_distinct_families():
    """EL test. Con tres familias sanas, cada nodo recibe una distinta.

    En v5.0.28 esto era imposible: cloud.py:122-123 reescribía deepseek,
    claude-3.5-sonnet y qwen-2.5 a gpt-4o antes de salir.
    """
    reg = ProviderRegistry()
    reg.register(EchoProvider("g4f-deepseek", "deepseek"), priority=10)
    reg.register(EchoProvider("g4f-claude", "claude"), priority=20)
    reg.register(EchoProvider("g4f-qwen", "qwen"), priority=30)
    await reg.probe_all()

    a = reg.select_for_swarm()
    assert a.diversity == "full"
    assert len(set(a.families.values())) == 3
    assert a.by_role["MELCHIOR"] != a.by_role["BALTHASAR"] != a.by_role["CASPER"]
    assert a.degraded_reason_for("BALTHASAR") is None


@pytest.mark.asyncio
async def test_two_families_isolates_the_judge():
    reg = ProviderRegistry()
    reg.register(EchoProvider("p1", "deepseek"), priority=10)
    reg.register(EchoProvider("p2", "claude"), priority=20)
    await reg.probe_all()

    a = reg.select_for_swarm()
    assert a.diversity == "partial"
    # CASPER (el juez) se queda solo en su familia
    assert a.families["CASPER"] != a.families["MELCHIOR"]
    assert a.families["MELCHIOR"] == a.families["BALTHASAR"]
    assert "misma familia" in a.degraded_reason_for("MELCHIOR")


@pytest.mark.asyncio
async def test_single_family_declares_degradation():
    """Una sola familia es aceptable; DISIMULARLO no lo es."""
    reg = ProviderRegistry()
    reg.register(EchoProvider("solo", "gpt"))
    await reg.probe_all()

    a = reg.select_for_swarm()
    assert a.diversity == "degraded"
    assert "una sola familia" in a.note


@pytest.mark.asyncio
async def test_no_providers_is_not_a_crash():
    a = ProviderRegistry().select_for_swarm()
    assert a.diversity == "none"


# -------------------------------------------------------------------- timeouts

@pytest.mark.asyncio
async def test_timeout_is_enforced():
    """v5.0.28 no tenía timeout: un proveedor colgado congelaba el enjambre."""
    reg = ProviderRegistry()
    reg.register(EchoProvider("lento", "a", delay_s=5.0))
    await reg.probe_all()

    req = _req()
    req.timeout_s = 0.2
    with pytest.raises(ProviderError):
        await reg.complete(req, max_attempts=1)
    assert reg.get("lento").breaker.failures == 1


@pytest.mark.asyncio
async def test_failover_to_next_family():
    reg = ProviderRegistry()
    reg.register(EchoProvider("roto", "a", fail_times=99), priority=1)
    reg.register(EchoProvider("sano", "b", canned="respuesta buena"), priority=2)
    await reg.probe_all()

    resp = await reg.complete(_req())
    assert resp.provider_id == "sano"
    assert resp.content == "respuesta buena"


# ------------------------------------------------------------- cortacircuitos

def test_circuit_opens_and_recovers():
    cb = CircuitBreaker(threshold=3, cooldown_s=10.0)
    assert cb.allows()
    for _ in range(3):
        cb.record_failure(now=100.0)
    assert not cb.allows(now=100.0)
    assert cb.state(now=100.0) is ProviderState.OPEN
    # pasado el cooldown deja pasar una sonda
    assert cb.allows(now=111.0)
    assert cb.state(now=111.0) is ProviderState.HALF_OPEN
    cb.record_success(latency_ms=42.0)
    assert cb.state() is ProviderState.CLOSED


def test_halfopen_failure_reopens_immediately():
    cb = CircuitBreaker(threshold=3, cooldown_s=5.0)
    for _ in range(3):
        cb.record_failure(now=0.0)
    cb.allows(now=10.0)                    # -> HALF_OPEN
    cb.record_failure(now=10.0)            # la sonda falla
    assert cb.state(now=10.1) is ProviderState.OPEN


@pytest.mark.asyncio
async def test_open_circuit_excludes_provider():
    reg = ProviderRegistry()
    reg.register(EchoProvider("caido", "a"))
    reg.register(EchoProvider("vivo", "b"))
    await reg.probe_all()
    for _ in range(3):
        reg.get("caido").breaker.record_failure()
    assert [r.id for r in reg.healthy()] == ["vivo"]


# --------------------------------------------------------------------- caché

def test_cache_is_bounded():
    """v5.0.28: self._cache crecía sin límite. Fuga de memoria por sesión."""
    c = TTLCache(maxsize=3)
    for i in range(10):
        c.set(f"k{i}", i)
    assert len(c) == 3
    assert c.get("k0") is None      # expulsado
    assert c.get("k9") == 9


def test_cache_ttl_expires():
    import time
    c = TTLCache(maxsize=10, ttl_s=0.05)
    c.set("k", "v")
    assert c.get("k") == "v"
    time.sleep(0.08)
    assert c.get("k") is None


def test_make_key_is_stable_and_discriminating():
    assert make_key("a", 1) == make_key("a", 1)
    assert make_key("a", 1) != make_key("a", 2)


@pytest.mark.asyncio
async def test_registry_uses_cache():
    reg = ProviderRegistry()
    reg.register(EchoProvider("e", "a"))
    await reg.probe_all()
    await reg.complete(_req("misma pregunta"))
    await reg.complete(_req("misma pregunta"))
    assert reg.cache.hits >= 1


# ------------------------------------------------------------------ streaming

@pytest.mark.asyncio
async def test_streaming_yields_incremental_deltas():
    """Sin esto el usuario mira una pantalla quieta 30-90 s (§1.2)."""
    reg = ProviderRegistry()
    reg.register(EchoProvider("e", "a", canned="uno dos tres cuatro"))
    await reg.probe_all()

    deltas = [d async for d in reg.stream(_req())]
    assert len(deltas) > 2
    assert deltas[-1].done
    assert "".join(d.text for d in deltas).strip() == "uno dos tres cuatro"


# -------------------------------------------------------------- contabilidad

@pytest.mark.asyncio
async def test_tokens_are_accounted():
    reg = ProviderRegistry()
    reg.register(EchoProvider("e", "a"))
    await reg.probe_all()
    await reg.complete(_req("cuenta estos tokens"))
    t = reg.telemetry()["providers"][0]
    assert t["calls"] == 1 and t["tokens_in"] > 0 and t["tokens_out"] > 0
