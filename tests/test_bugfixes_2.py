"""
Regresiones de la tercera pasada de verificación.

Esta vez las técnicas fueron distintas: arrancar el sistema de verdad, buscar
fugas de recursos, y comparar el contrato entre backend y frontend. Salieron
bugs que ninguna lectura del código habría encontrado.
"""
import asyncio
import re
from pathlib import Path

import pytest

from magi.core.bus import BusEvent, MagiBus
from magi.core.store.state import TaskState, TaskStore

ROOT = Path(__file__).resolve().parents[1]


# ---- BUG A: el kernel ni siquiera se construía (el peor de todos) ----

def test_bus_subscribe_works_without_an_event_loop():
    """
    subscribe() hacía asyncio.create_task() directamente. Como se llama desde
    constructores SÍNCRONOS (Kernel, Naoko, WSServer, MetricsCollector),
    reventaba con "no running event loop" y la aplicación no arrancaba.

    Lo encontré arrancando el kernel, no leyendo el código.
    """
    bus = MagiBus()

    async def handler(event):
        pass

    bus.subscribe("test.topic", handler)     # sin bucle: no debe lanzar
    assert len(bus._pending_workers) == 1


def test_kernel_constructs_outside_the_loop():
    """main.py construye el Kernel fuera del bucle asyncio."""
    from magi.core.kernel import Kernel
    k = Kernel(host="127.0.0.1", port=20993)
    assert k.metrics is not None
    assert "obs.metrics" in k.rpc.handlers
    assert "naoko.self_improve" in k.rpc.handlers


def _bus_subscribed_outside_the_loop():
    """Simula el caso real: el Kernel se construye ANTES de arrancar asyncio."""
    bus = MagiBus()
    got: list = []

    async def handler(event):
        got.append(event.payload)

    bus.subscribe("x", handler)
    return bus, got


def test_subscription_outside_the_loop_is_deferred():
    bus, _ = _bus_subscribed_outside_the_loop()
    assert len(bus._pending_workers) == 1


@pytest.mark.asyncio
async def test_pending_workers_start_on_first_publish():
    # Construido fuera del bucle, igual que main.py construye el Kernel.
    bus, got = await asyncio.get_running_loop().run_in_executor(
        None, _bus_subscribed_outside_the_loop)
    assert bus._pending_workers, "debe quedar pendiente al no haber bucle"

    await bus.publish(BusEvent(topic="x", payload={"v": 1}))
    await asyncio.sleep(0.05)
    assert not bus._pending_workers, "publish debe arrancar los pendientes"
    assert got == [{"v": 1}], "el evento debe llegar al handler diferido"
    await bus.shutdown()


def test_subscribe_leaves_no_orphan_coroutine():
    """
    La primera versión del arreglo creaba la corrutina ANTES de comprobar el
    bucle, así que al fallar quedaba sin await y Python avisaba en cada
    suscripción.
    """
    import warnings
    bus = MagiBus()

    async def handler(event):
        pass

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        bus.subscribe("a", handler)
        bus.subscribe("b", handler)


@pytest.mark.asyncio
async def test_bus_shutdown_cancels_workers():
    """Los workers vivían toda la sesión aunque el bus ya no se usara."""
    bus = MagiBus()

    async def handler(event):
        pass

    for i in range(3):
        bus.subscribe(f"t{i}", handler)
    await bus.publish(BusEvent(topic="t0", payload=None))
    await asyncio.sleep(0.05)

    before = len(asyncio.all_tasks())
    await bus.shutdown()
    await asyncio.sleep(0.05)
    assert len(asyncio.all_tasks()) < before


# ---- BUG B: la ruta se perdía al reiniciar ----

def test_route_budget_survives_a_restart(tmp_path):
    """
    Una tarea 'build' tiene 4 rondas y herramientas. Al reiniciar volvía a los
    valores por defecto (3 rondas) porque TaskState no guardaba max_rounds ni
    use_tools: el trabajo largo se degradaba en silencio.
    """
    store = TaskStore(tmp_path / "r.db")
    store.save(TaskState(task_id="t", command="crea un emulador",
                         status="WAITING_USER_APPROVAL", route="build",
                         max_rounds=4, use_tools=True))

    revived = TaskStore(tmp_path / "r.db").load("t")
    assert revived.route == "build"
    assert revived.max_rounds == 4
    assert revived.use_tools is True


def test_use_tools_false_survives_too():
    """Un booleano en SQLite es un entero: False no puede volver como True."""
    import tempfile
    store = TaskStore(Path(tempfile.mkdtemp()) / "b.db")
    store.save(TaskState("t", "hola", route="chat", max_rounds=1,
                         use_tools=False))
    assert store.load("t").use_tools is False


def test_schema_migration_adds_missing_columns(tmp_path):
    """Bases creadas antes de estos campos no deben perder datos."""
    import sqlite3
    path = tmp_path / "old.db"
    with sqlite3.connect(path) as c:
        c.executescript("""
            CREATE TABLE task_state (
                task_id TEXT PRIMARY KEY, command TEXT NOT NULL,
                status TEXT NOT NULL, round_num INTEGER NOT NULL DEFAULT 1,
                engine TEXT NOT NULL DEFAULT 'fast',
                narrative_style TEXT NOT NULL DEFAULT 'tecnico',
                route TEXT NOT NULL DEFAULT 'task',
                last_proposal TEXT, last_critique TEXT,
                created_at REAL NOT NULL, updated_at REAL NOT NULL);
        """)
        c.execute("INSERT INTO task_state VALUES "
                  "('viejo','cmd','in_progress',2,'fast','tecnico','task',"
                  "NULL,NULL,1.0,2.0)")

    store = TaskStore(path)                      # dispara la migración
    got = store.load("viejo")
    assert got is not None and got.command == "cmd"
    assert got.max_rounds == 3 and got.use_tools is True


@pytest.mark.asyncio
async def test_orchestrator_restores_the_full_route(tmp_path):
    from magi.core.blackboard import Blackboard
    from magi.modules.swarm.orchestrator import SwarmOrchestrator

    store = TaskStore(tmp_path / "o.db")
    store.save(TaskState("t", "cmd", status="WAITING_USER_APPROVAL",
                         route="build", max_rounds=4, use_tools=True))

    swarm = SwarmOrchestrator(Blackboard(), MagiBus(), store=store)
    st = swarm.active_tasks["t"]
    assert st["route"] == "build"
    assert st["max_rounds"] == 4
    assert st["use_tools"] is True


# ---- BUG C: eventos que la interfaz ignoraba ----

def _emitted_topics() -> set[str]:
    src = "\n".join(f.read_text(encoding="utf-8")
                    for f in (ROOT / "magi").rglob("*.py")
                    if "_attic" not in f.parts)
    # Los topics se emiten de dos formas: BusEvent(topic=...) y el helper
    # emit("...") del bucle de agentes. Contar solo la primera daba un falso
    # negativo sobre agent.tool_use.
    return (set(re.findall(r'topic="([a-zA-Z_.]+)"', src))
            | set(re.findall(r"topic='([a-zA-Z_.]+)'", src))
            | set(re.findall(r'emit\(\s*"([a-zA-Z_.]+)"', src)))


def _handled_topics() -> set[str]:
    ts = (ROOT / "magi-gui/src/useMagiSocket.ts").read_text(encoding="utf-8")
    return set(re.findall(r"topic === '([a-zA-Z_.]+)'", ts))


def test_user_facing_events_reach_the_interface():
    """
    Una alerta que solo va al log del backend es una función invisible: §3.4
    entero era inútil para el usuario porque la GUI no manejaba obs.alert.
    """
    must_be_visible = {
        "obs.alert",                  # §3.4 degradación
        "provider.model_drift",       # §3.4 deriva
        "swarm.verification_failed",  # §2.5 por qué se rechazó una ronda
        "swarm.routed",               # §2.3 por qué ruta fue
        "agent.tool_use",             # §2.2 qué está haciendo
        "agent.delta",                # §1.2 streaming
    }
    emitted, handled = _emitted_topics(), _handled_topics()
    for topic in must_be_visible:
        assert topic in emitted, f"{topic} no se emite en el backend"
        assert topic in handled, f"{topic} se emite pero la GUI lo ignora"


def test_tool_use_payload_matches_the_store_contract():
    """agent_loop emite `calls`; el store espera `calls`."""
    loop_src = (ROOT / "magi/core/agent_loop.py").read_text(encoding="utf-8")
    store_src = (ROOT / "magi-gui/src/store.ts").read_text(encoding="utf-8")
    assert '"calls": [{"tool": c.name' in loop_src
    assert "calls: any[]" in store_src
    assert '"results": [{"tool": r.tool' in loop_src
    assert "results: any[]" in store_src


# ---- No hay fuga de tareas al alertar ----

@pytest.mark.asyncio
async def test_alerting_does_not_leak_tasks():
    from magi.core.obs.metrics import MetricsCollector

    bus = MagiBus()
    m = MetricsCollector(bus=bus, latency_p95_warn_ms=100, min_samples=2)
    base = len(asyncio.all_tasks())
    for _ in range(40):
        m.record_provider("p", 9_999.0, ok=True)
        m.record_tool("t", ok=False)
    await asyncio.sleep(0.15)
    assert len(asyncio.all_tasks()) - base < 10
