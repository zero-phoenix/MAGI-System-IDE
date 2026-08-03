"""
Fase 3: observabilidad proactiva (§3.4) y auto-mejora medible (§3.5).
"""
import asyncio

import pytest

from magi.core.bus import BusEvent, MagiBus
from magi.core.eval.bench import (
    BenchResult, EvalBench, EvalTask, TaskOutcome, compare, default_bench,
)
from magi.core.obs.metrics import (
    Alert, Counter, MetricsCollector, Series, canary_probe,
)
from magi.core.providers.backends.echo import EchoProvider
from magi.core.providers.registry import ProviderRegistry


# ------------------------------------------------- §3.4 series y contadores

def test_series_percentiles():
    s = Series()
    for v in range(1, 101):
        s.add(float(v))
    assert s.n == 100
    assert 45 <= s.p50 <= 55
    assert s.p95 >= 90
    assert s.p99 >= s.p95


def test_series_is_a_sliding_window():
    """Sin ventana, la memoria crece toda la sesión."""
    s = Series()
    for v in range(1000):
        s.add(float(v))
    assert s.n <= 200


def test_counter_failure_rate():
    c = Counter()
    for _ in range(7):
        c.record(True)
    for _ in range(3):
        c.record(False)
    assert c.total == 10 and c.failure_rate == 0.3


# --------------------------------------------------------- §3.4 alertas

def test_slow_provider_raises_an_alert():
    """
    Lo que v5.0.28 no veía: un proveedor que responde en 25 s no lanza ninguna
    excepción y arruina la experiencia igual.
    """
    m = MetricsCollector(latency_p95_warn_ms=10_000, min_samples=5)
    alerts = []
    for _ in range(10):
        alerts += m.record_provider("g4f-lento", 25_000.0, ok=True)
    assert alerts and alerts[0].kind == "latency"
    assert "rotación" in alerts[0].detail


def test_healthy_provider_raises_nothing():
    m = MetricsCollector(latency_p95_warn_ms=10_000, min_samples=5)
    alerts = []
    for _ in range(10):
        alerts += m.record_provider("g4f-rapido", 1_200.0, ok=True)
    assert not alerts


def test_failing_provider_is_critical():
    m = MetricsCollector(min_samples=4)
    alerts = []
    for _ in range(10):
        alerts += m.record_provider("g4f-caido", 0.0, ok=False)
    assert any(a.kind == "provider_down" and a.severity == "critical"
               for a in alerts)


def test_broken_tool_raises_an_alert():
    m = MetricsCollector(tool_failure_warn=0.3, min_samples=5)
    alerts = []
    for i in range(10):
        alerts += m.record_tool("edit_file", ok=(i % 2 == 0))
    assert alerts and alerts[0].kind == "tool_failures"
    assert "prompt confuso" in alerts[0].detail


def test_alerts_have_a_cooldown():
    """Una alerta que salta cada dos minutos deja de leerse."""
    m = MetricsCollector(latency_p95_warn_ms=1_000, min_samples=3)
    first = []
    for _ in range(20):
        first += m.record_provider("p", 9_000.0, ok=True)
    assert len(first) == 1, "no debe repetir la misma alerta"


def test_snapshot_shape():
    m = MetricsCollector()
    m.record_provider("g4f-qwen", 900.0, ok=True)
    m.record_tool("read_file", ok=True)
    m.record_agent("MELCHIOR", 4_500.0)
    snap = m.snapshot()
    assert "g4f-qwen" in snap["providers"]
    assert "read_file" in snap["tools"]
    assert "MELCHIOR" in snap["agents"]


def test_health_summary_is_prompt_sized():
    """Va dentro del prompt de Naoko: no puede ser un volcado gigante."""
    m = MetricsCollector()
    for i in range(50):
        m.record_provider(f"g4f-{i % 5}", 1_000.0 + i, ok=True)
    out = m.health_summary()
    assert len(out) < 1500 and "p95" in out


# --------------------------------------------------- §3.4 bus y deriva

@pytest.mark.asyncio
async def test_collector_reads_tool_results_from_the_bus():
    m = MetricsCollector()
    bus = MagiBus()
    m.attach(bus)
    await bus.publish(BusEvent(topic="agent.tool_result", payload={
        "agent": "MELCHIOR",
        "results": [{"tool": "read_file", "ok": True},
                    {"tool": "run_command", "ok": False, "error": "rc=1"}]}))
    await asyncio.sleep(0.05)
    assert m.tool_calls["read_file"].ok == 1
    assert m.tool_calls["run_command"].fail == 1


@pytest.mark.asyncio
async def test_canary_detects_a_drifted_provider():
    """
    Sonda canaria (§I.8 del documento de arquitectura). Estaba especificada
    desde la primera versión del plan y nunca se implementó.
    """
    reg = ProviderRegistry()
    reg.register(EchoProvider("g4f-raro", "raro", canned="respuesta sin sentido"))
    await reg.probe_all()
    report = await canary_probe(reg, "g4f-raro")
    assert report.drifted and report.matched == 0


@pytest.mark.asyncio
async def test_canary_passes_a_correct_provider():
    class Correct(EchoProvider):
        def _render(self, req):
            q = str(req.messages[-1].content).lower()
            if "17" in q:
                return "51"
            if "francia" in q:
                return "Paris"
            return "OK"

    reg = ProviderRegistry()
    reg.register(Correct("g4f-bueno", "bueno"))
    await reg.probe_all()
    report = await canary_probe(reg, "g4f-bueno")
    assert not report.drifted and report.matched == 3


@pytest.mark.asyncio
async def test_registry_feeds_the_collector():
    """El registro debe alimentar las métricas, no solo su propio breaker."""
    from magi.core.providers.base import CompletionRequest, Message

    m = MetricsCollector()
    reg = ProviderRegistry(metrics=m)
    reg.register(EchoProvider("g4f-x", "x"))
    await reg.probe_all()
    await reg.complete(CompletionRequest(messages=[Message("user", "hola")]))
    assert m.provider_calls["g4f-x"].ok == 1


# ------------------------------------------------------- §3.5 banco

def test_bench_tasks_are_graded_by_code_not_opinion():
    bench = default_bench()
    assert len(bench.tasks) >= 8
    assert all(callable(t.grader) for t in bench.tasks)
    arith = next(t for t in bench.tasks if t.id == "arith_1")
    assert arith.grade("El resultado es 1081.")
    assert not arith.grade("El resultado es 1000.")


def test_bench_grades_python_syntax():
    bench = default_bench()
    code = next(t for t in bench.tasks if t.id == "code_1")
    assert code.grade("```python\ndef es_par(n):\n    return n % 2 == 0\n```")
    assert not code.grade("```python\ndef es_par(n:\n```")


def test_bench_checks_honesty():
    """Una tarea cuya respuesta correcta es admitir que no se puede saber."""
    bench = default_bench()
    t = next(t for t in bench.tasks if t.id == "honesty_1")
    assert t.grade("No tengo forma de saber eso.")
    assert not t.grade("El número de serie es XKJ-4471-A.")


def test_grader_exceptions_count_as_failure():
    def explosive(_):
        raise RuntimeError("grader roto")
    assert not EvalTask("t", "p", explosive).grade("respuesta")


@pytest.mark.asyncio
async def test_bench_runs_and_scores():
    tasks = [EvalTask("a", "di hola", lambda x: "hola" in x.lower()),
             EvalTask("b", "di adios", lambda x: "adios" in x.lower())]

    async def runner(prompt):
        return "hola"

    result = await EvalBench(tasks).run(runner, label="prueba")
    assert result.total == 2 and result.passed == 1 and result.score == 0.5


@pytest.mark.asyncio
async def test_bench_survives_a_broken_runner():
    async def broken(prompt):
        raise RuntimeError("proveedor caído")

    r = await EvalBench([EvalTask("a", "p", lambda x: True)]).run(broken)
    assert r.score == 0.0 and r.outcomes[0].error


@pytest.mark.asyncio
async def test_bench_enforces_a_timeout():
    async def slow(prompt):
        await asyncio.sleep(5)
        return "tarde"

    r = await EvalBench([EvalTask("a", "p", lambda x: True)],
                        timeout_s=0.3).run(slow)
    assert not r.outcomes[0].passed and "timeout" in r.outcomes[0].error


# ------------------------------------------------- §3.5 decisión A/B

def _result(label, passed_ids, all_ids):
    return BenchResult(
        [TaskOutcome(i, i in passed_ids, 1.0) for i in all_ids], label=label)


def test_improvement_without_regressions_is_accepted():
    ids = [f"t{i}" for i in range(10)]
    c = compare(_result("antes", {"t0", "t1"}, ids),
                _result("después", {"t0", "t1", "t2", "t3"}, ids))
    assert c.significant and "ACEPTADO" in c.verdict
    assert c.fixed == ["t2", "t3"] and not c.broken


def test_any_regression_is_rejected():
    """Romper algo que funcionaba pesa más que arreglar algo que no."""
    ids = [f"t{i}" for i in range(10)]
    c = compare(_result("antes", {"t0", "t1", "t2"}, ids),
                _result("después", {"t0", "t3", "t4", "t5"}, ids))
    assert not c.significant
    assert "RECHAZADO" in c.verdict and c.broken == ["t1", "t2"]


def test_tiny_improvement_is_not_conclusive():
    ids = [f"t{i}" for i in range(10)]
    c = compare(_result("antes", {"t0"}, ids), _result("después", {"t0", "t1"}, ids))
    assert not c.significant and "NO CONCLUYENTE" in c.verdict


def test_no_change_is_rejected():
    ids = [f"t{i}" for i in range(5)]
    c = compare(_result("antes", {"t0"}, ids), _result("después", {"t0"}, ids))
    assert not c.significant and "RECHAZADO" in c.verdict


@pytest.mark.asyncio
async def test_ab_test_end_to_end():
    tasks = [EvalTask(f"t{i}", "p", lambda x: "bien" in x) for i in range(5)]

    async def bad(p):
        return "mal"

    async def good(p):
        return "bien"

    c = await EvalBench(tasks).ab_test(bad, good)
    assert c.before.score == 0.0 and c.after.score == 1.0
    assert c.significant


def test_history_is_persisted(tmp_path):
    bench = EvalBench([])
    path = tmp_path / "hist.json"
    bench.save(_result("r1", {"a"}, ["a", "b"]), path)
    bench.save(_result("r2", {"a", "b"}, ["a", "b"]), path)
    import json
    hist = json.loads(path.read_text(encoding="utf-8"))
    assert len(hist) == 2 and hist[1]["score"] == 1.0


# --------------------------------------------------------- cableado

def test_phase3_is_wired():
    """La comprobación que me ha faltado tres veces."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    kernel = (root / "magi/core/kernel.py").read_text(encoding="utf-8")
    naoko = (root / "magi/modules/infrastructure/naoko.py").read_text(encoding="utf-8")
    registry = (root / "magi/core/providers/registry.py").read_text(encoding="utf-8")

    assert "MetricsCollector()" in kernel, "§3.4 colector sin crear"
    assert "metrics.attach(" in kernel, "§3.4 colector sin enganchar al bus"
    assert "metrics=self.metrics" in kernel, "Naoko no recibe el colector"
    assert "self.metrics.record_provider" in registry, "el registro no mide"
    assert "obs.alert" in naoko, "§3.4 Naoko no escucha alertas"
    assert "canary_probe" in naoko, "§3.4 sonda canaria sin conectar"
    assert "default_bench" in naoko, "§3.5 banco sin conectar"
    assert "naoko.self_improve" in kernel, "§3.5 auto-mejora no invocable"
