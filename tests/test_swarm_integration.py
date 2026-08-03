"""
Tests de integración del enjambre: kernel -> orquestador -> agentes -> proveedor.

POR QUÉ EXISTE ESTE FICHERO
===========================
El primer intento de arreglar la diversidad tocó ProviderRegistry y se verificó
con tests unitarios sobre `select_for_swarm()`. Pasaban todos. Pero el enjambre
NUNCA llamaba a `select_for_swarm()`: iba por agents.py, que pedía
`model="gpt-4o-mini"` en los tres nodos, y ese alias mandaba a los tres a la
familia "gpt". El bug seguía vivo, una capa por encima de donde se arregló.

La lección: un test que verifica una pieza aislada no demuestra que el sistema
la use. Estos tests recorren el camino completo.
"""
import asyncio

import pytest

from magi.core.blackboard import Blackboard
from magi.core.bus import MagiBus, BusEvent
from magi.core.providers.cloud import FreeCloudLLM, set_registry
from magi.core.providers.registry import ProviderRegistry
from magi.core.providers.backends.echo import EchoProvider
from magi.modules.swarm.orchestrator import SwarmOrchestrator


class FamilyEcho(EchoProvider):
    """Devuelve su familia en el cuerpo para poder rastrear quién respondió."""

    def _render(self, req):
        return f"[familia={self.family}] propuesta técnica. ### CONCLUSIÓN"


@pytest.fixture
async def swarm_registry():
    reg = ProviderRegistry()
    for fam in ("deepseek", "claude", "qwen", "gpt", "gemini"):
        reg.register(FamilyEcho(f"g4f-{fam}", fam), priority=10)
    await reg.probe_all()
    set_registry(reg)
    yield reg
    set_registry(None)


@pytest.fixture
async def bus_capture():
    """Async porque MagiBus.subscribe() arranca un worker con create_task."""
    bus = MagiBus()
    posts: list[dict] = []

    async def on_post(event: BusEvent):
        if isinstance(event.payload, dict):
            posts.append(event.payload)

    bus.subscribe("AGENT_POST", on_post)
    yield bus, posts


# ---------------------------------------------------- EL test que faltaba

@pytest.mark.asyncio
async def test_three_agents_hit_three_distinct_families(swarm_registry, bus_capture):
    """
    Recorre orquestador -> agentes -> proveedor y comprueba que cada nodo
    aterriza en una familia DISTINTA.

    Con el código de v5.0.28 (y con el primer intento de arreglo) los tres
    caían en 'gpt' y este test fallaría.
    """
    bus, posts = bus_capture
    swarm = SwarmOrchestrator(Blackboard(), bus)

    await swarm.submit_task("t-div", "diseña un parser de ROM", engine="fast")
    for _ in range(60):
        await asyncio.sleep(0.05)
        if len({p.get("agent") for p in posts}) >= 3:
            break

    by_agent = {p["agent"]: p for p in posts}
    assert {"MELCHIOR", "BALTHASAR", "CASPER"} <= set(by_agent)

    families = {a: by_agent[a]["family"] for a in ("MELCHIOR", "BALTHASAR", "CASPER")}
    assert len(set(families.values())) == 3, (
        f"los tres nodos deben usar familias distintas, pero fueron: {families}")
    assert families["MELCHIOR"] == "deepseek"
    assert families["BALTHASAR"] == "claude"
    assert families["CASPER"] == "qwen"


@pytest.mark.asyncio
async def test_provider_reported_is_the_one_that_answered(swarm_registry, bus_capture):
    """
    v5.0.28 publicaba provider="G4F_Auto_Router(gpt-4o) (deepseek)", donde el
    paréntesis final era lo que el agente CREÍA usar. La GUI mentía.
    """
    bus, posts = bus_capture
    swarm = SwarmOrchestrator(Blackboard(), bus)

    await swarm.submit_task("t-prov", "analiza esto", engine="fast")
    for _ in range(60):
        await asyncio.sleep(0.05)
        if posts:
            break

    p = posts[0]
    assert p["provider"].startswith("g4f-")
    assert p["family"] in p["provider"], "el proveedor reportado debe ser el real"


# ------------------------------------------------- estilo narrativo real

@pytest.mark.asyncio
async def test_narrative_style_reaches_the_prompt(swarm_registry):
    """
    El <select> de v5.0.28 no enviaba su valor a ninguna parte. Después de la
    primera corrección llegaba al estado de la tarea... y se quedaba ahí, sin
    llegar nunca al prompt. Esto comprueba el último tramo.
    """
    seen: list[str] = []

    class Capturing(EchoProvider):
        def _render(self, req):
            seen.append(str(req.messages[0].content))
            return "ok. ### CONCLUSIÓN"

    reg = ProviderRegistry()
    reg.register(Capturing("g4f-deepseek", "deepseek"))
    await reg.probe_all()
    set_registry(reg)
    try:
        llm = FreeCloudLLM(reg)
        from magi.modules.swarm.agents import MelchiorAgent
        agent = MelchiorAgent(Blackboard(), MagiBus())
        agent.llm = llm
        await agent.generate_proposal("t", "haz algo", 1,
                                      narrative_style="sintetico")
        assert seen, "el agente no llegó a llamar al proveedor"
        assert "SINTÉTICO" in seen[0]
        assert "máximo 5 líneas" in seen[0]
    finally:
        set_registry(None)


@pytest.mark.asyncio
async def test_execution_context_reaches_the_prompt(swarm_registry):
    """Los agentes deben saber en qué SO y en qué fecha corren."""
    seen: list[str] = []

    class Capturing(EchoProvider):
        def _render(self, req):
            seen.append(str(req.messages[0].content))
            return "ok"

    reg = ProviderRegistry()
    reg.register(Capturing("g4f-claude", "claude"))
    await reg.probe_all()
    set_registry(reg)
    try:
        from magi.modules.swarm.agents import BalthasarAgent
        agent = BalthasarAgent(Blackboard(), MagiBus())
        agent.llm = FreeCloudLLM(reg)
        await agent.generate_critique("t", {"content": "propuesta"}, 1)
        assert "CONTEXTO DE EJECUCIÓN" in seen[0]
    finally:
        set_registry(None)


# --------------------------------------------------- engine y reanudación

@pytest.mark.asyncio
async def test_engine_reaches_the_task_state(swarm_registry, bus_capture):
    """kernel.py:216 llamaba a submit_task(task_id, command) sin pasar engine."""
    bus, _ = bus_capture
    swarm = SwarmOrchestrator(Blackboard(), bus)
    await swarm.submit_task("t-eng", "algo", engine="deep",
                            narrative_style="analitico")
    await asyncio.sleep(0.2)
    state = swarm.active_tasks["t-eng"]
    assert state["engine"] == "deep"
    assert state["narrative_style"] == "analitico"


@pytest.mark.asyncio
async def test_changing_selectors_mid_conversation_takes_effect(swarm_registry,
                                                                bus_capture):
    """
    Cambiar motor o estilo a mitad de conversación no tenía efecto: se guardaban
    al crear la tarea y las llamadas posteriores reutilizaban el estado viejo.
    """
    bus, _ = bus_capture
    swarm = SwarmOrchestrator(Blackboard(), bus)

    await swarm.submit_task("t-mid", "primera orden", engine="fast",
                            narrative_style="tecnico")
    await asyncio.sleep(0.3)
    swarm.active_tasks["t-mid"]["status"] = "WAITING_USER_APPROVAL"

    await swarm.submit_task("t-mid", "cambia el enfoque", engine="deep",
                            narrative_style="creativo")
    await asyncio.sleep(0.1)

    state = swarm.active_tasks["t-mid"]
    assert state["engine"] == "deep"
    assert state["narrative_style"] == "creativo"


# ------------------------------------------------------- no hay regresión

def test_agents_never_pin_a_gpt_model():
    """
    Guarda sobre el CÓDIGO de agents.py (sin docstrings, que citan el bug para
    explicarlo). Si alguien vuelve a fijar un modelo gpt-* en los tres nodos,
    colapsan otra vez a la misma familia y la diversidad desaparece sin ruido.
    """
    import ast
    from pathlib import Path

    tree = ast.parse((Path(__file__).resolve().parents[1]
                      / "magi/modules/swarm/agents.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                node.body.pop(0)
    code = ast.unparse(tree)

    assert "target_model" not in code
    assert "gpt-4o" not in code, "ningún nodo debe fijar un modelo gpt-*"


def test_each_agent_declares_a_distinct_family():
    from magi.modules.swarm.agents import (
        MelchiorAgent, BalthasarAgent, CasperAgent)
    fams = [MelchiorAgent.family, BalthasarAgent.family, CasperAgent.family]
    assert len(set(fams)) == 3, f"familias repetidas: {fams}"
    assert "auto" not in fams, "ningún nodo debe quedar en el auto-router"


def test_each_agent_has_a_distinct_seed():
    """Si solo hay una familia sana, la divergencia se fuerza por semilla."""
    from magi.modules.swarm.agents import (
        MelchiorAgent, BalthasarAgent, CasperAgent)
    seeds = [MelchiorAgent.seed, BalthasarAgent.seed, CasperAgent.seed]
    assert len(set(seeds)) == 3 and None not in seeds
