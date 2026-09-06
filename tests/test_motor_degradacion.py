"""
Pruebas para D2: Degradación de motor deep -> fast por salud de proveedores.

MEDIDO EN LA MISIÓN TETRIS (5-sep-2026):
El sistema pasó más de 45 minutos intentando turnos en modo `deep` mientras los
proveedores gratuitos estaban moribundos. `deep` concede 40 llamadas y 480s de
pared; sobre proveedores caídos, esto multiplica exponencialmente los timeouts.

D2 introduce la compuerta de salud: si la tasa de respuestas inservibles supera
el umbral (>= 50%) en la sonda periódica o en la telemetría en vivo, el motor
deep se degrada automáticamente a fast, reduciendo el presupuesto a 18 llamadas
y 150s, y notificando la causa con su evidencia medida.
"""
from __future__ import annotations

import time

import pytest

from magi.core.obs.metrics import MetricsCollector
from magi.core.providers import sonda
from magi.core.store.state import TaskStore
from magi.modules.infrastructure.motor import (
    estilo_y_motor,
    salud_proveedores_degradada,
)


@pytest.fixture()
def store(tmp_path):
    return TaskStore(path=tmp_path / "test_sonda_d2.db")


def _registrar_sonda(store, ok: bool, n: int = 1, ts: float | None = None):
    ts = ts or time.time()
    for _ in range(n):
        sonda.registrar(
            store,
            sonda.Medicion(
                familia="gpt",
                proveedor="TestProvider",
                modelo="test-model",
                ok=ok,
                ms=500.0 if ok else None,
                ts=ts,
            ),
        )


# =================================================================== Pruebas

@pytest.mark.asyncio
async def test_control_proveedores_sanos_conserva_deep(store, monkeypatch):
    """Control: si los proveedores están sanos (10% fallos), deep se conserva."""
    async def falso_estilo(cmd, llm=None):
        return "tecnico"
    monkeypatch.setattr("magi.modules.infrastructure.naoko.estilo_para", falso_estilo)

    # 9 éxitos, 1 fallo = 10% fallos (< 50%)
    _registrar_sonda(store, ok=True, n=9)
    _registrar_sonda(store, ok=False, n=1)

    estilo, motor, origen = await estilo_y_motor(
        "analiza la arquitectura del sistema y diseña una refactorización",
        motor_gui="deep",
        store=store,
    )
    assert motor == "deep"
    assert origen == "naoko"


@pytest.mark.asyncio
async def test_d2_degrada_deep_a_fast_con_sonda_caida(store, monkeypatch):
    """D2: si la sonda reporta >= 50% de fallos, deep se degrada a fast."""
    async def falso_estilo(cmd, llm=None):
        return "tecnico"
    monkeypatch.setattr("magi.modules.infrastructure.naoko.estilo_para", falso_estilo)

    # 2 éxitos, 8 fallos = 80% fallos (>= 50%)
    _registrar_sonda(store, ok=True, n=2)
    _registrar_sonda(store, ok=False, n=8)

    estilo, motor, origen = await estilo_y_motor(
        "analiza la arquitectura del sistema y diseña una refactorización",
        motor_gui="deep",
        store=store,
    )
    assert motor == "fast"
    assert "salud-degradada:sonda" in origen
    assert "80.0%" in origen


@pytest.mark.asyncio
async def test_d2_degrada_deep_a_fast_con_telemetria_en_vivo_caida(monkeypatch):
    """D2: telemetría en vivo con >= 50% fallos también dispara la degradación."""
    async def falso_estilo(cmd, llm=None):
        return "divulgativo"
    monkeypatch.setattr("magi.modules.infrastructure.naoko.estilo_para", falso_estilo)

    metrics = MetricsCollector()
    # 3 éxitos, 7 fallos = 70% fallos
    for _ in range(3):
        metrics.record_provider("p1", 1000.0, ok=True)
    for _ in range(7):
        metrics.record_provider("p1", 0.0, ok=False)

    estilo, motor, origen = await estilo_y_motor(
        "investiga el rendimiento del compilador",
        motor_gui="deep",
        metrics=metrics,
    )
    assert motor == "fast"
    assert "salud-degradada:telemetria" in origen
    assert "70.0%" in origen


@pytest.mark.asyncio
async def test_regla_de_oro_nunca_se_sube_a_quien_pidio_fast(store, monkeypatch):
    """Regla de oro: si el usuario pidió fast, se queda en fast siempre."""
    async def falso_estilo(cmd, llm=None):
        return "tecnico"
    monkeypatch.setattr("magi.modules.infrastructure.naoko.estilo_para", falso_estilo)

    _registrar_sonda(store, ok=False, n=10)

    estilo, motor, origen = await estilo_y_motor(
        "analiza a fondo la seguridad",
        motor_gui="fast",
        store=store,
    )
    assert motor == "fast"


@pytest.mark.asyncio
async def test_encargo_trivial_no_gasta_evaluacion_de_salud(store, monkeypatch):
    """Encargos triviales van directos por el atajo sin evaluar sonda."""
    estilo, motor, origen = await estilo_y_motor(
        "crea holamundo.py",
        motor_gui="deep",
        store=store,
    )
    assert (estilo, motor, origen) == ("tecnico", "fast", "heuristica-trivial")


def test_sin_datos_suficientes_no_se_inventa_degradacion(store):
    """Sin evidencia mínima (< 4 muestras), la regla de oro no degrada."""
    # Solo 2 muestras fallidas: insuficiente para afirmar caída general
    _registrar_sonda(store, ok=False, n=2)

    degradada, tasa, motivo = salud_proveedores_degradada(store=store)
    assert not degradada
    assert tasa is None
    assert motivo == "sin-datos-suficientes"


def test_presupuesto_frugal_en_fast_vs_deep():
    """Verifica que el motor fast reduce el presupuesto de pared y llamadas."""
    from magi.core.presupuesto import para

    p_deep = para("deep")
    p_fast = para("fast")

    assert p_deep.llamadas == 40
    assert p_deep.pared_s == 480.0
    assert p_fast.llamadas == 18
    assert p_fast.pared_s == 150.0
    assert p_fast.llamadas < p_deep.llamadas
    assert p_fast.pared_s < p_deep.pared_s
