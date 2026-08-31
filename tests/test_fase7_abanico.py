"""
Fase 7 — el abanico paralelo, con su compuerta medida.

POR QUÉ ESTE FICHERO MIDEN TIEMPOS Y NO SOLO ESTADOS
====================================================
La compuerta de la fase 7 no es «funciona»: es «la ronda tarda MENOS con
la misma calidad medida». Un test que solo comprueba que el dossier llega
no puede retirar el mecanismo si no sirve — y esta fase exige poder
retirarlo. Así que aquí se corre la ronda REAL (orquestador, agentes,
bus) contra proveedores con GUION y RETARDO, dos veces: con el abanico
encendido y con `MAGI_ABANICO=0` (el flujo serial de antes). Mismos
guiones, mismos retrasos; solo cambia el orden.

La calidad se mide como lo que es aquí: misma estructura (mismos posts,
misma decisión de Casper, mismas variantes verificadas). La calidad
«literaria» de un proveedor de guion no existe — lo que no se mide con
proveedores reales se declara SIN COMPROBAR en la bitácora, no se
simula en un test.
"""
import asyncio
import time
from pathlib import Path

import pytest

# La infraestructura de guion vive en `swarm_helpers`, no aqui: un test
# que importa a otro test declara una dependencia que requirements.txt
# no puede satisfacer, y el runner del release se cae al importarla.
from swarm_helpers import (  # noqa: E402
    CODIGO_CORTO,
    CODIGO_LENTO,
    ENCARGO,
    FAM_BALTHASAR,
    FAM_CASPER,
    FAM_MELCHIOR,
    EscalonadoProvider,
    GuionProvider,
)
from swarm_helpers import (
    montar_registro as _montar,
)

from magi.core.blackboard import Blackboard
from magi.core.bus import BusEvent, MagiBus
from magi.core.providers.cloud import set_registry
from magi.modules.swarm.orchestrator import SwarmOrchestrator


async def _correr_ronda(captura, task_id, use_tools=True):
    """
    Arranca una tarea y espera a que hablen los tres nodos.

    El TaskStore se apunta a un directorio temporal POR RONDA: el de la
    máquina es compartido y una tarea rehidratada de una corrida anterior
    interfirió con estas carreras (reproducido: la tarea vieja se quedaba
    `in_progress` y la nueva no llegaba a correr). Un test de tiempos no
    puede heredar el estado de lo que pasó fuera de él.
    """
    import tempfile

    from magi.core.store.state import TaskStore

    bus, posts, fases = captura
    db = Path(tempfile.mkdtemp(prefix="magi-fase7-")) / "t.db"
    swarm = SwarmOrchestrator(Blackboard(), bus, store=TaskStore(db))
    t0 = time.monotonic()
    await swarm.submit_task(task_id, ENCARGO, use_tools=use_tools,
                            max_rounds=1)
    for _ in range(int(30.0 / 0.05)):
        await asyncio.sleep(0.05)
        if {"MELCHIOR", "BALTHASAR", "CASPER"} <= {
                p.get("agent") for p in posts}:
            break
    await asyncio.sleep(0.3)     # margen para asentar el veredicto
    return swarm, time.monotonic() - t0


@pytest.fixture
async def captura():
    bus = MagiBus()
    posts: list[dict] = []
    fases: list[dict] = []

    async def on_post(event: BusEvent):
        if isinstance(event.payload, dict):
            posts.append(event.payload)

    async def on_fases(event: BusEvent):
        if isinstance(event.payload, dict):
            fases.append(event.payload)

    bus.subscribe("AGENT_POST", on_post)
    bus.subscribe("swarm.fases", on_fases)
    yield bus, posts, fases
    set_registry(None)


# ------------------------------------------------ LA COMPUERTA DE LA FASE 7

@pytest.mark.asyncio
async def test_la_cascada_acorta_la_pared_de_melchior(captura, monkeypatch):
    """
    LA COMPUERTA: la fase de generar+verificar tarda MENOS con el abanico.

    Montaje: dos variantes — la primera termina pronto pero su código tarda
    1,5 s en verificarse; la segunda tarda en generarse y verifica al
    instante. En serie: la generación entera (1,2 s) y LUEGO la
    verificación larga (~2,9 s). En cascada: la verificación larga corre
    durante la generación de la lenta (~1,9 s). Con la misma estructura.
    """
    async def una_carrera(abanico_on: bool):
        bus, posts, fases = captura
        posts.clear()
        fases.clear()
        monkeypatch.setenv("MAGI_ABANICO", "0" if not abanico_on else "1")
        melchior = EscalonadoProvider(
            f"g4f-{FAM_MELCHIOR}", FAM_MELCHIOR,
            primera=(CODIGO_LENTO, 0.35), siguientes=(CODIGO_CORTO, 1.2))
        balthasar = GuionProvider(
            f"g4f-{FAM_BALTHASAR}", FAM_BALTHASAR,
            por_defecto=("sin defectos en este eje. OBJECIONES: 0", 0.0))
        casper = GuionProvider(
            f"g4f-{FAM_CASPER}", FAM_CASPER,
            por_defecto=("veredicto. DECISIÓN: APROBADA", 0.0))
        reg = _montar(melchior, balthasar, casper)
        await reg.probe_all()
        set_registry(reg)
        swarm, _ = await _correr_ronda(captura, "t-carrera", use_tools=False)
        assert fases, "la ronda no publicó swarm.fases"
        return {
            "t_melchior": fases[-1]["t_melchior_ms"] / 1000.0,
            "posts": [(p["agent"], p["role"]) for p in posts],
            "estado": swarm.active_tasks["t-carrera"].get("status"),
        }

    serial = await una_carrera(False)
    abanico = await una_carrera(True)

    # MISMA CALIDAD: mismos intervinientes, un mensaje por agente, el
    # mismo estado final de la tarea.
    assert {"MELCHIOR", "BALTHASAR", "CASPER"} <= {
        a for a, _ in abanico["posts"]}
    assert abanico["posts"].count(("MELCHIOR", "propone")) == 1
    assert abanico["estado"] == serial["estado"]

    # Y MENOS PARED: la verificación larga dejó de esperar a la generación
    # lenta. El margen (0,4 s) es menor que la ganancia esperada (~0,9 s)
    # para absorber el arranque del intérprete del verificador.
    assert abanico["t_melchior"] < serial["t_melchior"] - 0.4, (
        f"la cascada no acortó la pared: serial {serial['t_melchior']:.2f}s "
        f"vs abanico {abanico['t_melchior']:.2f}s — si esto se repite, la "
        f"compuerta pide retirar el mecanismo")


# --------------------------------------------------- EL RECON, EN PARALELO

@pytest.mark.asyncio
async def test_el_recon_cabe_en_la_ventana_de_melchior(captura, monkeypatch):
    """El recon corre DURANTE Melchior: llega a los ejes y no alarga la
    fase de Melchior."""
    monkeypatch.setenv("MAGI_ABANICO", "1")
    bus, posts, fases = captura
    melchior = GuionProvider(
        f"g4f-{FAM_MELCHIOR}", FAM_MELCHIOR,
        por_defecto=("propuesta sin código", 0.6))
    balthasar = GuionProvider(
        f"g4f-{FAM_BALTHASAR}", FAM_BALTHASAR,
        reglas=[("RECONOCIMIENTO",
                 "DOSIER: la memoria registra un intento previo de parser "
                 "que falló por codificación.", 0.3)],
        por_defecto=("sin defectos en este eje. OBJECIONES: 0", 0.0))
    casper = GuionProvider(
        f"g4f-{FAM_CASPER}", FAM_CASPER,
        por_defecto=("veredicto. DECISIÓN: APROBADA", 0.0))
    reg = _montar(melchior, balthasar, casper)
    await reg.probe_all()
    set_registry(reg)
    await _correr_ronda(captura, "t-recon", use_tools=True)

    recon = [v for v in balthasar.vistos if "RECONOCIMIENTO" in v]
    ejes = [v for v in balthasar.vistos if "RECONOCIMIENTO" not in v]
    assert recon, "el recon no se disparó"
    assert any("DOSIER" in v for v in ejes), (
        "el dossier del recon no llegó a los ejes de crítica")
    assert fases and fases[-1].get("recon") is True
    # La fase de Melchior NO creció por el recon: 0,6 s de guion; en serie
    # habría sido 0,6 + 0,3 del recon.
    assert fases[-1]["t_melchior_ms"] < 900, (
        f"la fase de Melchior absorbió al recon: "
        f"{fases[-1]['t_melchior_ms']} ms")


@pytest.mark.asyncio
async def test_el_recon_tardio_se_cancela_y_no_alarga_la_ronda(captura,
                                                               monkeypatch):
    """Un recon más lento que Melchior no tiene derecho a alargar la
    ronda: se cancela, los ejes siguen sin dossier y la pared no cambia."""
    async def una_carrera(abanico_on: bool):
        monkeypatch.setenv("MAGI_ABANICO", "0" if not abanico_on else "1")
        bus, posts, fases = captura
        posts.clear()
        fases.clear()
        melchior = GuionProvider(
            f"g4f-{FAM_MELCHIOR}", FAM_MELCHIOR,
            por_defecto=("propuesta sin código", 0.4))
        balthasar = GuionProvider(
            f"g4f-{FAM_BALTHASAR}", FAM_BALTHASAR,
            reglas=[("RECONOCIMIENTO", "DOSIER: tardísimo.", 5.0)],
            por_defecto=("sin defectos en este eje. OBJECIONES: 0", 0.0))
        casper = GuionProvider(
            f"g4f-{FAM_CASPER}", FAM_CASPER,
            por_defecto=("veredicto. DECISIÓN: APROBADA", 0.0))
        reg = _montar(melchior, balthasar, casper)
        await reg.probe_all()
        set_registry(reg)
        _, pared = await _correr_ronda(captura, "t-recon-lento",
                                       use_tools=True)
        return pared, fases[-1]

    pared_con, fases_con = await una_carrera(True)
    pared_sin, _ = await una_carrera(False)
    assert fases_con.get("recon") is False
    assert pared_con < 3.0, (f"la ronda esperó al recon tardío: "
                             f"{pared_con:.2f}s")
    assert pared_con < pared_sin + 1.0
