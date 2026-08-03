"""
Tests de rutas, enrutamiento adaptativo, prompts, contexto y bucle de agente.
"""
import os
from pathlib import Path

import pytest

from magi.core import paths
from magi.core.router import Route, classify, classify_heuristic
from magi.core.prompts import build_system_prompt, style_fragment, NARRATIVE_STYLES
from magi.core.context import ExecutionContext, HostInfo, GitInfo
from magi.core.agent_loop import run_agent, _trim
from magi.core.providers.base import Message
from magi.core.providers.registry import ProviderRegistry
from magi.core.providers.backends.echo import EchoProvider
from magi.core.tools import ToolContext, WriteJournal, build_registry


# ----------------------------------------------------------------- rutas §1.3

def test_paths_are_not_hardcoded_to_one_machine():
    """v5.0.28 tenía 'D:/PROYECTOS/MAGI System IDE' en 8 sitios: el .exe de
    Releases no arrancaba en ninguna otra máquina."""
    assert paths.data_dir().exists()
    assert paths.workspace_dir().exists()
    assert "PROYECTOS" not in str(paths.data_dir())


def test_db_lives_outside_the_repo():
    """magi_brain.db acabó commiteado con datos reales dentro."""
    assert paths.db_path().parent == paths.data_dir()
    assert paths.db_path().name == "magi_brain.db"


def test_no_absolute_windows_paths_left_in_source():
    root = Path(__file__).resolve().parents[1]
    offenders = []
    for py in (root / "magi").rglob("*.py"):
        if py.name in {"paths.py", "naoko_repair.py"}:
            continue          # solo los mencionan en documentación del bug
        text = py.read_text(encoding="utf-8", errors="replace")
        if "D:/PROYECTOS" in text or "d:/PROYECTOS" in text:
            offenders.append(str(py.relative_to(root)))
    assert not offenders, f"rutas absolutas restantes: {offenders}"


# ------------------------------------------------------- enrutamiento §2.3

@pytest.mark.parametrize("text,expected", [
    ("hola", Route.CHAT),
    ("gracias", Route.CHAT),
    ("ok", Route.CHAT),
    ("¿qué es un dynarec?", Route.LOOKUP),
    ("lee el fichero kernel.py", Route.TASK),
    ("arregla el bug del scroll", Route.TASK),
    ("crea un emulador de Game Boy en Rust con soporte de audio y guardado",
     Route.BUILD),
])
def test_heuristic_routing(text, expected):
    d = classify_heuristic(text)
    assert d is not None and d.route is expected


def test_chat_does_not_trigger_full_debate():
    """El coste real de v5.0.28: 'hola' disparaba 3 rondas = 9 llamadas."""
    d = classify_heuristic("hola")
    assert d.max_rounds == 1 and d.use_tools is False


def test_build_gets_more_rounds_and_tools():
    d = classify_heuristic("desarrolla un videojuego completo con sprites y niveles")
    assert d.route is Route.BUILD and d.max_rounds >= 3 and d.use_tools


@pytest.mark.asyncio
async def test_classifier_falls_back_without_registry():
    d = await classify("algo muy ambiguo que no encaja en ningún patrón claro",
                       registry=None)
    assert d.route in set(Route)


# ------------------------------------------------------------- prompts §2.7

def test_four_narrative_styles_exist():
    assert set(NARRATIVE_STYLES) == {"tecnico", "sintetico", "creativo", "analitico"}


def test_style_is_injected_into_the_prompt():
    """v5.0.28: el <select> existía en App.tsx:307 y su valor no salía nunca
    del navegador. Aquí el estilo llega de verdad al prompt."""
    p = build_system_prompt("MELCHIOR", narrative_style="sintetico")
    assert "SINTÉTICO" in p and "máximo 5 líneas" in p


def test_unknown_style_falls_back_to_technical():
    assert style_fragment("inventado") == NARRATIVE_STYLES["tecnico"]
    assert style_fragment(None) == NARRATIVE_STYLES["tecnico"]


def test_roles_have_distinct_prompts():
    m = build_system_prompt("MELCHIOR")
    b = build_system_prompt("BALTHASAR")
    c = build_system_prompt("CASPER")
    assert m != b != c
    assert "REFUTAR" in b
    assert "ÁRBITRO" in c


def test_balthasar_is_told_to_bring_evidence():
    b = build_system_prompt("BALTHASAR")
    assert "HABIENDO EJECUTADO" in b


# ------------------------------------------------------------ contexto §4.3

def test_context_block_states_time_host_and_os():
    """Los agentes no sabían qué día era ni en qué máquina corrían: Melchior
    proponía apt-get en Windows."""
    ctx = ExecutionContext(host=HostInfo.probe(), git=GitInfo())
    block = ctx.render()
    assert "CONTEXTO DE EJECUCIÓN" in block
    assert "Ahora:" in block and "Host:" in block
    assert str(os.getpid()) in block


def test_context_warns_about_knowledge_cutoff():
    block = ExecutionContext().render()
    assert "fecha de corte" in block and "web_fetch" in block


def test_context_states_free_cloud_only_constraint():
    """La restricción del proyecto debe estar en el prompt: sin ella el agente
    propone instalar modelos locales o pedir claves de API."""
    block = ExecutionContext().render()
    assert "gratuita" in block and "sin claves" in block


def test_context_goes_into_the_system_prompt():
    p = build_system_prompt("MELCHIOR",
                            execution_context=ExecutionContext().render())
    assert "CONTEXTO DE EJECUCIÓN" in p


# ------------------------------------------------------- bucle de agente §2.2

@pytest.mark.asyncio
async def test_agent_without_tool_calls_finishes_in_one_iteration(tmp_path):
    reg = ProviderRegistry()
    reg.register(EchoProvider("e", "a", canned="Conclusión: ya está."))
    await reg.probe_all()

    turn = await run_agent(
        registry=reg, tools=build_registry(),
        system_prompt="sys", user_prompt="haz algo",
        ctx=ToolContext(task_id="t", cwd=tmp_path,
                        journal=WriteJournal("t", tmp_path / ".j")))
    assert turn.iterations == 1 and not turn.tool_calls


@pytest.mark.asyncio
async def test_agent_executes_a_tool_then_concludes(tmp_path):
    """El salto de capacidad: el agente LEE el fichero en vez de imaginarlo."""
    (tmp_path / "dato.txt").write_text("valor-secreto-42", encoding="utf-8")

    class Scripted(EchoProvider):
        def __init__(self):
            super().__init__("scripted", "a")
            self.n = 0

        def _render(self, req):
            self.n += 1
            if self.n == 1:
                return ('Voy a leerlo.\n```tool\n'
                        '{"tool":"read_file","args":{"path":"dato.txt"}}\n```')
            return "El fichero contiene valor-secreto-42. ### CONCLUSIÓN"

    reg = ProviderRegistry()
    reg.register(Scripted())
    await reg.probe_all()

    turn = await run_agent(
        registry=reg, tools=build_registry(),
        system_prompt="sys", user_prompt="¿qué hay en dato.txt?",
        ctx=ToolContext(task_id="t", cwd=tmp_path,
                        journal=WriteJournal("t", tmp_path / ".j")))
    assert turn.iterations == 2
    assert turn.tool_calls[0]["tool"] == "read_file"
    assert turn.tool_calls[0]["ok"]
    assert "valor-secreto-42" in turn.text


@pytest.mark.asyncio
async def test_agent_stops_at_iteration_limit(tmp_path):
    """Un modelo que se atasca pidiendo herramientas no debe bucear infinito."""
    class Looping(EchoProvider):
        def _render(self, req):
            return '```tool\n{"tool":"list_dir","args":{"path":"."}}\n```'

    reg = ProviderRegistry()
    reg.register(Looping("loop", "a"))
    await reg.probe_all()

    turn = await run_agent(
        registry=reg, tools=build_registry(),
        system_prompt="s", user_prompt="u", max_iters=3,
        ctx=ToolContext(task_id="t", cwd=tmp_path,
                        journal=WriteJournal("t", tmp_path / ".j")))
    assert turn.hit_limit and turn.iterations == 3


@pytest.mark.asyncio
async def test_agent_emits_events_for_the_gui(tmp_path):
    """La traza de herramientas convierte una caja negra en un colaborador."""
    events = []

    class Once(EchoProvider):
        def __init__(self):
            super().__init__("o", "a")
            self.n = 0

        def _render(self, req):
            self.n += 1
            return ('```tool\n{"tool":"list_dir","args":{"path":"."}}\n```'
                    if self.n == 1 else "listo")

    reg = ProviderRegistry()
    reg.register(Once())
    await reg.probe_all()

    async def on_event(topic, payload):
        events.append(topic)

    await run_agent(registry=reg, tools=build_registry(),
                    system_prompt="s", user_prompt="u", on_event=on_event,
                    ctx=ToolContext(task_id="t", cwd=tmp_path,
                                    journal=WriteJournal("t", tmp_path / ".j")))
    assert "agent.tool_use" in events
    assert "agent.tool_result" in events
    assert "agent.done" in events


def test_context_trimming_keeps_system_and_original_request():
    msgs = [Message("system", "S"), Message("user", "PETICIÓN")] + \
           [Message("assistant", "x" * 5000) for _ in range(30)]
    out = _trim(msgs, keep_recent=6, max_chars=20_000)
    assert out[0].content == "S"
    assert out[1].content == "PETICIÓN"
    assert len(out) < len(msgs)
