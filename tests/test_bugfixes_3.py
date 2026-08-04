"""
Regresiones de la cuarta pasada de verificación.

Técnicas nuevas: fuzzing de los parsers con entrada arbitraria, concurrencia
real, y crecimiento de memoria en sesión larga. Los tres bugs que salieron
tenían el mismo perfil — el sistema funcionaba en el caso normal y fallaba en
silencio fuera de él.
"""
import asyncio
import random
import string
import tempfile
from pathlib import Path

import pytest

from magi.core.blackboard import Blackboard
from magi.core.bus import MagiBus
from magi.core.providers.backends.echo import EchoProvider
from magi.core.providers.cloud import set_registry
from magi.core.providers.registry import ProviderRegistry
from magi.core.router import classify_heuristic
from magi.core.store.state import TaskStore
from magi.core.tools.protocol import parse_tool_calls, strip_tool_calls
from magi.modules.memory.episodic import MAX_ATTEMPTS_RETAINED, EpisodicMemory
from magi.modules.reverse.disasm import disassemble
from magi.modules.reverse.identify import identify
from magi.modules.swarm.orchestrator import SwarmOrchestrator


# ---- BUG 1: 24 de 25 tareas concurrentes se perdían en silencio ----

@pytest.fixture
async def swarm(tmp_path):
    reg = ProviderRegistry()
    for fam in ("deepseek", "claude", "qwen"):
        reg.register(EchoProvider(f"g4f-{fam}", fam,
                                  canned='{"decision":"APPROVED","feedback":"ok"}'))
    await reg.probe_all()
    set_registry(reg)
    yield SwarmOrchestrator(Blackboard(), MagiBus(),
                            store=TaskStore(tmp_path / "s.db"))
    set_registry(None)


@pytest.mark.asyncio
async def test_concurrent_tasks_are_not_merged(swarm):
    """
    v5.0.28 reescribía el task_id entrante por el de la tarea previa siempre
    que estuviera en WAITING_USER_APPROVAL *o* in_progress. Medido: de 25
    peticiones simultáneas sobrevivía UNA.
    """
    await asyncio.gather(*[
        swarm.submit_task(f"t{i}", f"tarea {i}", route="task",
                          max_rounds=1, use_tools=False)
        for i in range(12)])
    assert len(swarm.active_tasks) == 12, (
        f"se fundieron: quedan {len(swarm.active_tasks)} de 12")


@pytest.mark.asyncio
async def test_new_request_while_thinking_is_not_swallowed(swarm):
    """
    El caso de uso real: preguntas algo nuevo mientras el enjambre piensa. Antes
    tu petición se convertía sin avisar en "comentario a la propuesta anterior".
    """
    await swarm.submit_task("primera", "analiza el dynarec", use_tools=False)
    swarm.active_tasks["primera"]["status"] = "in_progress"

    await swarm.submit_task("segunda", "¿qué hora es?", use_tools=False)
    assert "segunda" in swarm.active_tasks
    assert swarm.active_tasks["segunda"]["command"] == "¿qué hora es?"


@pytest.mark.asyncio
async def test_reply_to_a_pending_approval_is_still_absorbed(swarm):
    """La absorción SÍ es correcta cuando la tarea previa espera respuesta."""
    await swarm.submit_task("original", "haz algo", use_tools=False)
    await asyncio.sleep(0.2)
    swarm.active_tasks["original"]["status"] = "WAITING_USER_APPROVAL"
    swarm.latest_task_id = "original"

    await swarm.submit_task("id-distinto", "sí, apruebo", use_tools=False)
    assert "id-distinto" not in swarm.active_tasks, (
        "una respuesta a una aprobación pendiente debe ir a la tarea original")


@pytest.mark.asyncio
async def test_every_concurrent_task_is_persisted(swarm, tmp_path):
    await asyncio.gather(*[
        swarm.submit_task(f"p{i}", f"cmd {i}", route="task",
                          max_rounds=1, use_tools=False) for i in range(10)])
    assert len(swarm.store.recent(limit=50)) == 10


# ---- BUG 2: identify reventaba con binarios truncados ----

def test_truncated_elf_reports_instead_of_crashing(tmp_path):
    """
    Un firmware a medio descargar tiene la firma \\x7fELF y nada más.
    struct.unpack_from lanzaba struct.error y tumbaba la herramienta.
    """
    p = tmp_path / "trunc.elf"
    p.write_bytes(b"\x7fELF" + bytes(15))
    info = identify(p)
    assert info.format == "ELF"
    assert any("truncada" in n for n in info.notes)


def test_pe_header_outside_the_file(tmp_path):
    p = tmp_path / "malo.exe"
    p.write_bytes(b"MZ" + b"\x00" * 0x3A + (0xFFFFFF).to_bytes(4, "little"))
    info = identify(p)
    assert info.format == "PE"
    assert any("ilegible" in n or "fuera" in n for n in info.notes)


def test_identify_survives_fuzzing(tmp_path):
    """600 binarios corruptos: cero excepciones."""
    rnd = random.Random(1234)
    for i in range(300):
        p = tmp_path / f"f{i}.bin"
        k = rnd.random()
        if k < 0.35:
            data = b"\x7fELF" + bytes(rnd.randrange(256)
                                      for _ in range(rnd.randrange(90)))
        elif k < 0.6:
            data = b"MZ" + bytes(rnd.randrange(256)
                                 for _ in range(rnd.randrange(90)))
        else:
            data = bytes(rnd.randrange(256) for _ in range(rnd.randrange(200)))
        p.write_bytes(data)
        identify(p)     # no debe lanzar


def test_tool_protocol_survives_fuzzing():
    rnd = random.Random(99)
    for _ in range(1500):
        s = "".join(rnd.choice(string.printable)
                    for _ in range(rnd.randrange(200)))
        if rnd.random() < 0.4:
            s = f"```tool\n{s}\n```"
        parse_tool_calls(s)
        strip_tool_calls(s)


def test_router_survives_fuzzing():
    rnd = random.Random(7)
    for _ in range(800):
        s = "".join(rnd.choice(string.printable + "áéíóúñ¿¡")
                    for _ in range(rnd.randrange(120)))
        classify_heuristic(s)


def test_disassembler_survives_random_bytes():
    rnd = random.Random(3)
    for arch in ("mips", "arm", "arm64", "x86"):
        for _ in range(60):
            data = bytes(rnd.randrange(256) for _ in range(rnd.randrange(64)))
            disassemble(data, arch=arch,
                        endian=rnd.choice(("little", "big")))


# ---- BUG 3: la memoria episódica crecía toda la sesión ----

def test_episodic_memory_is_capped():
    """
    El bloque del prompt ya estaba acotado, pero _attempts crecía sin límite y
    _load() reproducía TODO el histórico al rehidratar.
    """
    mem = EpisodicMemory("t")
    for i in range(3000):
        mem.record(round_num=i, approach="e" * 300, outcome="refutado",
                   reason="r" * 300)
    assert len(mem.attempts) <= MAX_ATTEMPTS_RETAINED
    assert len(mem.render_for_prompt()) < 2500


def test_capped_memory_keeps_the_most_recent():
    mem = EpisodicMemory("t")
    for i in range(200):
        mem.record(round_num=i, approach=f"enfoque numero {i} con texto largo",
                   outcome="refutado")
    assert "199" in mem.attempts[-1].approach
    assert len(mem.attempts) == MAX_ATTEMPTS_RETAINED


def test_old_schema_entries_do_not_break_loading(tmp_path):
    """Una entrada con campos de otra versión no debe tumbar la carga entera."""
    store = TaskStore(tmp_path / "m.db")
    store.append_event("t", "memory.attempt",
                       {"round_num": 1, "approach": "válida",
                        "outcome": "refutado", "reason": "", "ts": 1.0})
    store.append_event("t", "memory.attempt",
                       {"campo_inventado": 1, "otro": "x"})
    store.append_event("t", "memory.attempt",
                       {"round_num": 2, "approach": "también válida",
                        "outcome": "refutado", "reason": "", "ts": 2.0})

    mem = EpisodicMemory("t", store=store)
    assert len(mem.attempts) == 2, "las válidas deben sobrevivir"


def test_metrics_series_stay_bounded():
    from magi.core.obs.metrics import MetricsCollector
    m = MetricsCollector()
    for i in range(5000):
        m.record_provider("p", 1000.0 + i, ok=True)
        m.record_tool("t", ok=True)
    assert m.provider_latency["p"].n <= 200
    assert len(m.alerts) <= 100
