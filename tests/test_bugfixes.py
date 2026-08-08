"""
Regresiones de la pasada de verificación.

Cuatro bugs encontrados sondeando el código propio, no leyéndolo. Tres eran de
la misma familia: el sistema afirmaba algo que no comprobaba.
"""
import asyncio
import pathlib
import tempfile

import pytest

from magi.core.agent_loop import _trim
from magi.core.blackboard import Blackboard
from magi.core.bus import MagiBus, BusEvent
from magi.core.providers.base import Message
from magi.core.providers.cloud import FreeCloudLLM, set_registry
from magi.core.providers.registry import ProviderRegistry
from magi.core.providers.backends.echo import EchoProvider
from magi.core.tools import ToolContext, WriteJournal, build_registry
from magi.modules.swarm.agents import MelchiorAgent


# ------- BUG 1: la interfaz declaraba la familia PEDIDA, no la que respondió

@pytest.mark.asyncio
async def test_reports_actual_family_when_its_own_is_down():
    """
    Si la familia del nodo está caída, el registro conmuta a otra. Publicar
    self.family en ese caso es mentir en la interfaz — la misma clase de engaño
    que "G4F_Auto_Router(gpt-4o) (deepseek)" en v5.0.28.

    La familia propia se DERIVA, no se escribe. Antes este test fijaba
    "deepseek" a mano y se puso rojo al cambiar el reparto del enjambre — el
    mismo fallo que tenían los agentes: dos verdades sobre qué familia usa
    cada nodo.
    """
    propia = MelchiorAgent.family
    reg = ProviderRegistry()
    reg.register(EchoProvider(f"g4f-{propia}", propia, fail_times=99))
    reg.register(EchoProvider("g4f-suplente", "suplente",
                              canned="respuesta del suplente"))
    await reg.probe_all()
    set_registry(reg)
    try:
        bus, posts = MagiBus(), []

        async def cap(e: BusEvent):
            if isinstance(e.payload, dict) and e.payload.get("agent"):
                posts.append(e.payload)

        bus.subscribe("AGENT_POST", cap)

        agent = MelchiorAgent(Blackboard(), bus)
        agent.llm = FreeCloudLLM(reg)
        await agent.generate_proposal("t", "algo", 1)
        await asyncio.sleep(0.15)

        p = posts[0]
        assert p["family"] == "suplente", "debe publicarse la familia que respondió"
        assert p["family_expected"] == propia
        assert p["degraded"] and "no disponible" in p["degraded"]
    finally:
        set_registry(None)


@pytest.mark.asyncio
async def test_no_degradation_flag_when_family_is_healthy():
    propia = MelchiorAgent.family
    reg = ProviderRegistry()
    reg.register(EchoProvider(f"g4f-{propia}", propia, canned="ok"))
    await reg.probe_all()
    set_registry(reg)
    try:
        bus, posts = MagiBus(), []

        async def cap(e: BusEvent):
            if isinstance(e.payload, dict) and e.payload.get("agent"):
                posts.append(e.payload)

        bus.subscribe("AGENT_POST", cap)
        agent = MelchiorAgent(Blackboard(), bus)
        agent.llm = FreeCloudLLM(reg)
        await agent.generate_proposal("t", "algo", 1)
        await asyncio.sleep(0.15)

        assert posts[0]["family"] == propia
        assert posts[0]["degraded"] is None
    finally:
        set_registry(None)


def test_family_extraction_from_provider_id():
    from magi.modules.swarm.agents import SwarmAgentBase
    f = SwarmAgentBase._family_of
    assert f("g4f-deepseek:PhindAi/deepseek-v3") == "deepseek"
    assert f("g4f-claude") == "claude"
    assert f("") == "desconocida"


# ------------------------- BUG 2: procesos zombi al vencer el timeout

@pytest.mark.asyncio
async def test_timeout_reaps_the_process():
    """
    kill() sin wait() dejaba el transporte sin limpiar: proceso zombi y
    "RuntimeError: Event loop is closed" al recolectarlo.

    El comando que se cuelga es un Python, no `sleep`. `sleep` no existe en
    Windows: el proceso moría al instante con rc=1 y el test comprobaba el
    manejo de un comando inexistente en vez del de un timeout. En el runner de
    CI pasaba por accidente, porque Git for Windows deja un `sleep.exe` en el
    PATH; en un Windows limpio daba rojo. Un test que mide otra cosa según la
    máquina no mide nada.
    """
    import sys as _sys
    tmp = pathlib.Path(tempfile.mkdtemp())
    ctx = ToolContext(task_id="t", cwd=tmp, journal=WriteJournal("t", tmp / ".j"))
    colgado = f'"{_sys.executable}" -c "import time; time.sleep(5)"'
    r = await build_registry().execute(
        "run_command", {"command": colgado, "timeout": 1}, ctx)
    assert not r.ok and "timeout" in r.error
    await asyncio.sleep(0.05)   # si quedara sin recolectar, saltaría aquí


# ----------------------------- BUG 3: _trim no acotaba el contexto

def test_trim_bounds_context_even_with_huge_messages():
    """
    La salida de un run_tests puede ocupar 40 000 caracteres ella sola. El
    bucle antiguo solo descartaba mensajes y no podía bajar de 4, así que con
    mensajes grandes devolvía 160 000 caracteres con un tope de 30 000.
    """
    msgs = ([Message("system", "S"), Message("user", "P")]
            + [Message("assistant", "x" * 40_000) for _ in range(20)])
    out = _trim(msgs, keep_recent=6, max_chars=30_000)
    total = sum(len(str(m.content)) for m in out)

    assert total <= 33_000, f"contexto sin acotar: {total} caracteres"
    assert out[0].content == "S", "el system nunca se descarta"
    assert out[1].content == "P", "la petición original nunca se descarta"


def test_trim_leaves_small_conversations_untouched():
    msgs = [Message("system", "S"), Message("user", "P"),
            Message("assistant", "corto")]
    assert _trim(msgs) == msgs


def test_trim_marks_where_it_pruned():
    msgs = ([Message("system", "S"), Message("user", "P")]
            + [Message("assistant", "y" * 1000) for _ in range(30)])
    out = _trim(msgs, keep_recent=4, max_chars=10_000)
    assert any("podado" in str(m.content) for m in out)


# --------------- BUG 4: el ciclo seguro de Naoko no estaba conectado

def test_naoko_uses_verified_repair():
    """
    Escribí VerifiedRepair con sus tests y NO lo enchufé: naoko.py seguía
    ejecutando el script generado por el LLM a ciegas. Mi propia regla
    "conecta o borra", incumplida.
    """
    import inspect
    from magi.modules.infrastructure.naoko import NaokoAgent
    src = inspect.getsource(NaokoAgent._handle_error_event)
    assert "VerifiedRepair" in src
    assert "_apply_patch" not in src


@pytest.mark.asyncio
async def test_blind_patch_path_is_gone():
    """La vía peligrosa debe fallar explícitamente si alguien la reintroduce."""
    from magi.modules.infrastructure.naoko import NaokoAgent
    from magi.core.store.database import MagiDatabase

    naoko = NaokoAgent(MagiBus(), MagiDatabase())
    with pytest.raises(NotImplementedError):
        await naoko._apply_patch("python", "import os; os.remove('/')")
