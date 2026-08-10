"""
Tests de timeout y degradado en magi/core/agent_loop.py
"""
import asyncio
from unittest.mock import AsyncMock

import pytest

from magi.core.agent_loop import run_agent
from magi.core.providers.base import CompletionResponse, Usage
from magi.core.providers.registry import ProviderRegistry
from magi.core.tools.builtin import ToolContext
from magi.core.tools.registry import ToolRegistry


class _FakeProvider:
    id = "g4f-fake"
    family = "fake"
    is_local = True
    supports_tools = False
    supports_vision = False
    supports_stream = False

    def __init__(self, delay: float = 0.0):
        self.delay = delay

    async def complete(self, req):
        if self.delay:
            await asyncio.sleep(self.delay)
        return CompletionResponse(
            provider_id=self.id,
            model="fake-model",
            family=self.family,
            content="ok",
            usage=Usage(prompt_tokens=1, completion_tokens=1),
        )


@pytest.fixture
def ctx(tmp_path):
    return ToolContext(task_id="test_timeout", cwd=tmp_path)


@pytest.fixture
def registry_no_tools():
    reg = ProviderRegistry()
    # Registramos un provider que nunca debería llamarse en estos tests
    return reg


@pytest.fixture
def tools():
    t = ToolRegistry()
    return t


@pytest.mark.asyncio
async def test_agent_returns_degraded_on_timeout(tools, ctx):
    """Si registry.complete no responde, run_agent devuelve turno degradado."""
    reg = ProviderRegistry()
    # proveedor que duerme más que el timeout
    reg.register(_FakeProvider(delay=10.0))

    events = []

    async def on_event(topic, payload):
        events.append((topic, payload))

    turn = await run_agent(
        registry=reg,
        tools=tools,
        system_prompt="sys",
        user_prompt="user",
        ctx=ctx,
        agent_name="TEST",
        iteration_timeout_s=0.1,
        on_event=on_event,
    )

    assert turn.degraded is not None
    assert turn.provider_id == "TIMEOUT"
    assert "excedió" in turn.text or "agotado" in turn.text
    assert any(topic == "agent.timeout" for topic, _ in events)


@pytest.mark.asyncio
async def test_agent_emits_slow_iteration(tools, ctx):
    """Si una iteración supera soft_timeout_s, se emite agent.slow_iteration."""
    reg = ProviderRegistry()
    reg.register(_FakeProvider(delay=0.2))

    events = []

    async def on_event(topic, payload):
        events.append((topic, payload))

    await run_agent(
        registry=reg,
        tools=tools,
        system_prompt="sys",
        user_prompt="user",
        ctx=ctx,
        agent_name="TEST",
        soft_timeout_s=0.05,
        iteration_timeout_s=2.0,
        on_event=on_event,
    )

    assert any(topic == "agent.slow_iteration" for topic, _ in events)
