"""
Tests de estado persistente (§1.4) y streaming (§1.2).

Los dos huecos de la Fase 1 que quedaban:
  - orchestrator.py:17 guardaba active_tasks en un dict de RAM: cerrar la
    ventana perdía la conversación, la ronda y la propuesta pendiente — con una
    base de datos SQLite ya presente y sin usar para esto.
  - cloud.py llamaba a create() sin stream=True: 30-90 s de pantalla quieta.
"""
import asyncio

import pytest

from magi.core.blackboard import Blackboard
from magi.core.bus import MagiBus, BusEvent
from magi.core.providers.cloud import FreeCloudLLM, set_registry
from magi.core.providers.registry import ProviderRegistry
from magi.core.providers.backends.echo import EchoProvider
from magi.core.store.state import TaskState, TaskStore
from magi.modules.swarm.orchestrator import SwarmOrchestrator


@pytest.fixture
def store(tmp_path):
    return TaskStore(tmp_path / "test.db")


# ------------------------------------------------------- estado persistente

def test_task_survives_a_restart(store, tmp_path):
    """El caso real: cerrar la app no debe perder la conversación."""
    store.save(TaskState(task_id="t1", command="analiza el dynarec",
                         status="WAITING_USER_APPROVAL", round=2,
                         engine="deep", narrative_style="analitico",
                         last_proposal={"content": "propuesta v2"}))

    # Nueva instancia = proceso reiniciado
    reopened = TaskStore(tmp_path / "test.db")
    got = reopened.load("t1")
    assert got is not None
    assert got.command == "analiza el dynarec"
    assert got.status == "WAITING_USER_APPROVAL"
    assert got.round == 2
    assert got.engine == "deep"
    assert got.narrative_style == "analitico"
    assert got.last_proposal["content"] == "propuesta v2"


def test_only_resumable_tasks_come_back(store):
    store.save(TaskState("a", "cmd", status="in_progress"))
    store.save(TaskState("b", "cmd", status="WAITING_USER_APPROVAL"))
    store.save(TaskState("c", "cmd", status="completed"))
    store.save(TaskState("d", "cmd", status="failed"))

    ids = {t.task_id for t in store.resumable()}
    assert ids == {"a", "b"}


def test_save_is_idempotent(store):
    store.save(TaskState("t", "v1", round=1))
    store.save(TaskState("t", "v2", round=5))
    got = store.load("t")
    assert got.command == "v2" and got.round == 5
    assert len(store.recent()) == 1


def test_event_log_is_ordered(store):
    for i in range(5):
        store.append_event("t", "AGENT_POST", {"i": i})
    evs = store.events("t")
    assert [e["payload"]["i"] for e in evs] == [0, 1, 2, 3, 4]


def test_token_accounting(store):
    """Contabilidad de tokens: no existía en v5.0.28."""
    store.record_usage(task_id="t", agent="MELCHIOR", provider="g4f-deepseek",
                       family="deepseek", tokens_in=100, tokens_out=250,
                       latency_ms=1200)
    store.record_usage(task_id="t", agent="BALTHASAR", provider="g4f-claude",
                       family="claude", tokens_in=300, tokens_out=180,
                       latency_ms=2000)
    u = store.usage_for("t")
    assert u["calls"] == 2
    assert u["total_tokens"] == 830
    assert u["avg_latency_ms"] == 1600.0
    assert {a["family"] for a in u["by_agent"]} == {"deepseek", "claude"}


def test_missing_task_returns_none(store):
    assert store.load("no-existe") is None


# --------------------------------------------- orquestador + persistencia

@pytest.fixture
async def wired(tmp_path):
    reg = ProviderRegistry()
    for fam in ("deepseek", "claude", "qwen"):
        reg.register(EchoProvider(f"g4f-{fam}", fam, canned="ok. ### CONCLUSIÓN"))
    await reg.probe_all()
    set_registry(reg)
    yield TaskStore(tmp_path / "orch.db")
    set_registry(None)


@pytest.mark.asyncio
async def test_orchestrator_persists_on_submit(wired):
    swarm = SwarmOrchestrator(Blackboard(), MagiBus(), store=wired)
    await swarm.submit_task("t-p", "haz algo", engine="deep",
                            narrative_style="creativo")
    await asyncio.sleep(0.2)

    saved = wired.load("t-p")
    assert saved is not None
    assert saved.command == "haz algo"
    assert saved.engine == "deep"
    assert saved.narrative_style == "creativo"


@pytest.mark.asyncio
async def test_orchestrator_rehydrates_after_restart(wired):
    """Un orquestador nuevo sobre la misma BD recupera lo pendiente."""
    wired.save(TaskState(task_id="t-old", command="tarea previa",
                         status="WAITING_USER_APPROVAL", round=3,
                         engine="deep", narrative_style="sintetico",
                         last_proposal={"content": "propuesta guardada"}))

    swarm = SwarmOrchestrator(Blackboard(), MagiBus(), store=wired)
    assert "t-old" in swarm.active_tasks
    st = swarm.active_tasks["t-old"]
    assert st["status"] == "WAITING_USER_APPROVAL"
    assert st["round"] == 3
    assert st["narrative_style"] == "sintetico"
    assert st["last_proposal"]["content"] == "propuesta guardada"


@pytest.mark.asyncio
async def test_completed_tasks_are_not_rehydrated(wired):
    wired.save(TaskState("done", "cmd", status="completed"))
    swarm = SwarmOrchestrator(Blackboard(), MagiBus(), store=wired)
    assert "done" not in swarm.active_tasks


# ------------------------------------------------------------- streaming

@pytest.mark.asyncio
async def test_agent_emits_deltas_before_the_full_answer(tmp_path):
    """
    Lo que el usuario nota: texto apareciendo, no una pantalla quieta.
    Se comprueba que llegan varios deltas y un cierre.
    """
    reg = ProviderRegistry()
    reg.register(EchoProvider("g4f-deepseek", "deepseek",
                              canned="uno dos tres cuatro cinco"))
    await reg.probe_all()
    set_registry(reg)
    try:
        bus = MagiBus()
        deltas, ends = [], []

        async def on_delta(e: BusEvent):
            deltas.append(e.payload)

        async def on_end(e: BusEvent):
            ends.append(e.payload)

        bus.subscribe("agent.delta", on_delta)
        bus.subscribe("agent.delta_end", on_end)

        from magi.modules.swarm.agents import MelchiorAgent
        agent = MelchiorAgent(Blackboard(), bus)
        agent.llm = FreeCloudLLM(reg)
        await agent.generate_proposal("t-stream", "algo", 1)
        await asyncio.sleep(0.1)

        assert len(deltas) > 2, "debe llegar más de un fragmento"
        assert all(d["agent"] == "MELCHIOR" for d in deltas)
        assert all(d["task_id"] == "t-stream" for d in deltas)
        assert deltas[0]["family"] == "deepseek"
        assert ends, "debe emitirse agent.delta_end al terminar"
        assert "".join(d["text"] for d in deltas).strip() == "uno dos tres cuatro cinco"
    finally:
        set_registry(None)


@pytest.mark.asyncio
async def test_streaming_falls_back_when_provider_breaks():
    """Si el stream revienta antes del primer token, se cae a no-streaming
    en vez de dejar al usuario sin respuesta."""
    class BrokenStream(EchoProvider):
        async def stream(self, req):
            raise RuntimeError("stream no soportado")
            yield  # pragma: no cover

    reg = ProviderRegistry()
    reg.register(BrokenStream("g4f-deepseek", "deepseek", canned="respuesta completa"))
    await reg.probe_all()
    set_registry(reg)
    try:
        bus = MagiBus()
        posts = []

        async def on_post(e: BusEvent):
            posts.append(e.payload)

        bus.subscribe("AGENT_POST", on_post)

        from magi.modules.swarm.agents import MelchiorAgent
        agent = MelchiorAgent(Blackboard(), bus)
        agent.llm = FreeCloudLLM(reg)
        result = await agent.generate_proposal("t-fb", "algo", 1)
        await asyncio.sleep(0.1)

        assert "respuesta completa" in result["content"]
        assert posts, "debe publicarse el AGENT_POST igualmente"
    finally:
        set_registry(None)


@pytest.mark.asyncio
async def test_deltas_reassemble_into_the_final_text():
    """El texto acumulado por la GUI debe coincidir con el AGENT_POST final."""
    reg = ProviderRegistry()
    reg.register(EchoProvider("g4f-qwen", "qwen", canned="alfa beta gamma delta"))
    await reg.probe_all()
    set_registry(reg)
    try:
        bus = MagiBus()
        chunks, final = [], []

        async def on_delta(e: BusEvent):
            chunks.append(e.payload["text"])

        async def on_post(e: BusEvent):
            final.append(e.payload["content"])

        bus.subscribe("agent.delta", on_delta)
        bus.subscribe("AGENT_POST", on_post)

        from magi.modules.swarm.agents import CasperAgent
        agent = CasperAgent(Blackboard(), bus)
        agent.llm = FreeCloudLLM(reg)
        await agent.arbitrate("t-r", {"content": "p"}, {"content": "c"}, 1)
        await asyncio.sleep(0.1)

        assert final, "debe llegar el mensaje final"
        assert "".join(chunks).strip() in final[0]
    finally:
        set_registry(None)
