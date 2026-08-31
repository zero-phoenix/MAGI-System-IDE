"""
Fase 8 — la réplica: condicional, acotada, una vuelta, con salida.

Estos tests prueban el MECANISMO contra el orquestador real con
proveedores de guion: que la réplica solo exista si Balthasar firma
objeciones, que la concesión cierre antes de Casper, que la defensa
llegue al arbitraje, y que el modo sombra mida el contrafactual que la
compuerta de vida o muerte exige (¿cambia Casper al menos 1 de cada 5?).

Lo que NO puede medir este fichero: si los proveedores reales cambian de
veredicto con la réplica bastante. Eso se mide con `MAGI_REPLICA_SOMBRA=1`
en rondas de verdad y se lee de `magi/data/memoria/replica.jsonl` — aquí
queda declarado SIN COMPROBAR, no simulado.
"""
import asyncio
import json
from pathlib import Path

import pytest

# La infraestructura de guion vive en `swarm_helpers`: importarla del
# otro test declaraba una dependencia que requirements.txt no cubre.
from swarm_helpers import (
    ENCARGO,
    FAM_BALTHASAR,
    FAM_CASPER,
    FAM_MELCHIOR,
    GuionProvider,
)
from swarm_helpers import (
    montar_registro as _montar,
)

from magi.core.blackboard import Blackboard
from magi.core.bus import BusEvent, MagiBus
from magi.core.providers.cloud import set_registry
from magi.core.store.state import TaskStore
from magi.modules.swarm import replica
from magi.modules.swarm.orchestrator import SwarmOrchestrator

# ------------------------------------------------------------ unidad pura

def test_contar_objeciones_solo_cuenta_firmas():
    ejes = {
        "correccion": "falla con vacía. OBJECIONES: 2",
        "seguridad": "sin problemas. OBJECIONES: 0",
        "rendimiento": "no evaluado",          # sin firma: no cuenta
    }
    total, firmas = replica.contar_objeciones(ejes)
    assert (total, firmas) == (2, 2)


def test_extracto_acota_y_excluye_la_firma():
    ejes = {"correccion": "objeción uno. OBJECIONES: 1"}
    extracto = replica.extracto_de_objeciones(ejes)
    assert "objeción uno" in extracto
    assert "OBJECIONES" not in extracto


def test_es_concesion_mira_la_primera_linea():
    assert replica.es_concesion("CONCESIÓN: tienes razón en la línea 12.")
    assert replica.es_concesion("\n\n**CONCESIÓN:** el caso vacío rompe.")
    # Una concesión MENCIONADA a mitad de defensa no es rendición:
    assert not replica.es_concesion(
        "La objeción habla de una concesión hipotética, pero la línea 4 "
        "ya valida la entrada.")


def test_veredicto_por_concesion_entra_por_puerta_de_revision():
    crit = {"content": "la crítica completa"}
    v = replica.veredicto_por_concesion(crit, "CONCESIÓN: el caso vacío rompe.")
    assert v["decision"] == "REJECTED_NEEDS_WORK"
    assert "la crítica completa" in v["feedback"]
    assert "CONCESIÓN" in v["feedback"]


def test_registrar_escribe_jsonl(tmp_path, monkeypatch):
    monkeypatch.setenv("MAGI_MEMORIA", str(tmp_path))
    assert replica.registrar({"task_id": "t", "fired": True})
    linea = json.loads((tmp_path / "replica.jsonl").read_text("utf-8"))
    assert linea["fired"] is True and "ts" in linea


# ------------------------------------------------- el mecanismo en la ronda

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


async def _ronda(captura, *, objeciones, respuesta_replica, sombra=False,
                 memoria=None, monkeypatch=None):
    """Una ronda con guion: Balthasar firma N objeciones y la réplica de
    Melchior dice lo que se le diga. Devuelve providers y swarm."""
    import tempfile

    if monkeypatch is not None:
        monkeypatch.delenv("MAGI_ABANICO", raising=False)
        monkeypatch.setenv("MAGI_REPLICA_SOMBRA", "1" if sombra else "0")
        if memoria is not None:
            monkeypatch.setenv("MAGI_MEMORIA", str(memoria))
    bus, posts, fases = captura
    melchior = GuionProvider(
        f"g4f-{FAM_MELCHIOR}", FAM_MELCHIOR,
        reglas=[("OBJECIONES DE BALTHASAR", respuesta_replica, 0.0)],
        por_defecto=("propuesta sin código", 0.0))
    balthasar = GuionProvider(
        f"g4f-{FAM_BALTHASAR}", FAM_BALTHASAR,
        por_defecto=(f"defecto en el eje. OBJECIONES: {objeciones}", 0.0))
    casper = GuionProvider(
        f"g4f-{FAM_CASPER}", FAM_CASPER,
        reglas=[("RÉPLICA de Melchior", "vi la réplica. DECISIÓN: APROBADA",
                 0.0)],
        por_defecto=("sin réplica a la vista. DECISIÓN: NECESITA REVISIÓN",
                     0.0))
    reg = _montar(melchior, balthasar, casper)
    await reg.probe_all()
    set_registry(reg)
    db = Path(tempfile.mkdtemp(prefix="magi-fase8-")) / "t.db"
    swarm = SwarmOrchestrator(Blackboard(), bus, store=TaskStore(db))
    await swarm.submit_task("t-r", ENCARGO, use_tools=False, max_rounds=1)
    for _ in range(int(30.0 / 0.05)):
        await asyncio.sleep(0.05)
        if {"MELCHIOR", "BALTHASAR", "CASPER"} <= {
                p.get("agent") for p in posts}:
            break
        # la concesión cierra ANTES de Casper: esperar solo a los otros dos
        if {"MELCHIOR", "BALTHASAR"} <= {p.get("agent") for p in posts} and \
                any(p.get("role") == "replica" for p in posts):
            break
    await asyncio.sleep(0.3)
    return swarm, posts, fases, (melchior, balthasar, casper)


@pytest.mark.asyncio
async def test_sin_objeciones_firmadas_no_hay_replica(captura, monkeypatch):
    """La segunda vuelta se gana, no se regala."""
    swarm, posts, fases, (mel, bal, cas) = await _ronda(
        captura, objeciones=0, respuesta_replica="no debería llamarse",
        monkeypatch=monkeypatch)
    assert not any(p.get("role") == "replica" for p in posts), (
        "hubo réplica sin objeciones firmadas")
    assert cas._calls == 1
    assert not any("RÉPLICA de Melchior" in v for v in cas.vistos)
    assert fases and fases[-1]["fired"] is False


@pytest.mark.asyncio
async def test_la_concesion_cierra_antes_de_casper(captura, monkeypatch):
    """Melchior se rinde: no se gasta el arbitraje y el veredicto entra
    por la puerta de revisión."""
    swarm, posts, fases, (mel, bal, cas) = await _ronda(
        captura, objeciones=2,
        respuesta_replica="CONCESIÓN: el caso vacío rompe en la línea 12.",
        monkeypatch=monkeypatch)
    assert any(p.get("role") == "replica" for p in posts)
    assert cas._calls == 0, "la concesión gastó un arbitraje de todos modos"
    assert not any(p.get("agent") == "CASPER" for p in posts)
    veredicto = swarm.blackboard.read("t-r.verdict")
    assert veredicto["decision"] == "REJECTED_NEEDS_WORK"
    assert "CONCESIÓN" in veredicto["feedback"]
    assert fases[-1]["concedio"] is True and fases[-1]["fired"] is True


@pytest.mark.asyncio
async def test_la_defensa_llega_al_arbitraje(captura, monkeypatch):
    """Réplica defendiéndose: Casper arbitra con ella sobre la mesa."""
    swarm, posts, fases, (mel, bal, cas) = await _ronda(
        captura, objeciones=2,
        respuesta_replica="La línea 12 ya valida la entrada vacía; está "
                          "en el bloque de guardas.",
        monkeypatch=monkeypatch)
    assert any(p.get("role") == "replica" for p in posts)
    assert any("RÉPLICA de Melchior" in v for v in cas.vistos), (
        "Casper arbitró sin ver la réplica: sigue siendo juicio en rebeldía")
    assert cas._calls == 1
    veredicto = swarm.blackboard.read("t-r.verdict")
    assert veredicto["decision"] == "APPROVED"    # el guion: con réplica aprueba


@pytest.mark.asyncio
async def test_la_sombra_mide_el_contrafactual(captura, monkeypatch,
                                               tmp_path):
    """
    COMPUERTA de vida o muerte: con el modo sombra, el contrafactual se
    corre y se compara. El guion hace que la réplica VOLTEE el veredicto
    (sin ella: revisión; con ella: aprobada) — el registro tiene que
    dejar constancia de ese cambio, que es exactamente lo que la compuerta
    cuenta en rondas reales.
    """
    (tmp_path / "memoria").mkdir(exist_ok=True)
    swarm, posts, fases, (mel, bal, cas) = await _ronda(
        captura, objeciones=2,
        respuesta_replica="La línea 12 ya valida la entrada vacía.",
        sombra=True, memoria=tmp_path / "memoria", monkeypatch=monkeypatch)
    # Un SOLO Casper público: la sombra no habla.
    assert sum(1 for p in posts if p.get("agent") == "CASPER"
               and p.get("role") == "arbitro") == 1
    assert cas._calls == 2, "la sombra no corrió el contrafactual"
    registro = (tmp_path / "memoria" / "replica.jsonl").read_text("utf-8")
    lineas = [json.loads(x) for x in registro.splitlines() if x.strip()]
    assert lineas and lineas[-1]["sombra"]["cambia"] is True
    assert lineas[-1]["sombra"] == {"sin": "REJECTED_NEEDS_WORK",
                                    "con": "APPROVED", "cambia": True}
