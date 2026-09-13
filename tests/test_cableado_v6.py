"""
Las fases v6 existían y no se ejecutaban: esto mira el ORQUESTADOR.

QUÉ PASÓ
========
La v5.27.0 publicó F2-F5 y las notas las dieron por «consolidadas». Los
módulos están escritos y `tests/test_fases_v6.py` pasa en verde. Pero ese
fichero prueba las UNIDADES con las dependencias inyectadas a mano, y
ninguna de sus pruebas toca el orquestador. Medido contra el código el
12-sep-2026, ninguna de las cuatro fases operaba:

  F2  la única llamada a subagentes vive bajo `elif False:`   (orchestrator:1137)
  F3  el plan nace en `pendiente` y nadie lo actualiza ni lo inyecta
  F4  el retorno de `evaluar_cierre_entrega` se descarta       (orchestrator:1455)
  F5  a Casper no se le ofrece el cuarto veredicto, y si lo emitiera
      caería en la rama `else` de «tarea fallida»              (orchestrator:1475)

Cuatro módulos con sus pruebas en verde y cero comportamiento. Es el caso
exacto de «verde sin comprobar es peor que rojo»: los tests medían que el
código existe, no que se llama.

QUÉ MIDE ESTE FICHERO
=====================
Cada prueba arranca una ronda real del orquestador con proveedores de guion
y comprueba el EFECTO. Ninguna inyecta la pieza que quiere probar: si el
cableado desaparece, la prueba se pone roja.
"""

from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

import pytest
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
from magi.modules.swarm.orchestrator import SwarmOrchestrator


@pytest.fixture
async def captura():
    """Bus con los tres canales que estas pruebas necesitan leer."""
    bus = MagiBus()
    posts: list[dict] = []
    terminal: list[str] = []

    async def on_post(event: BusEvent):
        if isinstance(event.payload, dict):
            posts.append(event.payload)

    async def on_terminal(event: BusEvent):
        if isinstance(event.payload, dict):
            terminal.append(str(event.payload.get("content", "")))

    bus.subscribe("AGENT_POST", on_post)
    bus.subscribe("TERMINAL_OUT", on_terminal)
    yield bus, posts, terminal
    set_registry(None)


async def _ronda_con_veredicto(captura, veredicto: str, *, max_rounds: int = 3):
    """Una ronda real donde Casper cierra con el veredicto que se le pida."""
    bus, posts, terminal = captura
    melchior = GuionProvider(
        f"g4f-{FAM_MELCHIOR}", FAM_MELCHIOR, por_defecto=("propuesta sin codigo", 0.0)
    )
    balthasar = GuionProvider(
        f"g4f-{FAM_BALTHASAR}",
        FAM_BALTHASAR,
        por_defecto=("un defecto en el eje. OBJECIONES: 0", 0.0),
    )
    casper = GuionProvider(f"g4f-{FAM_CASPER}", FAM_CASPER, por_defecto=(veredicto, 0.0))
    reg = _montar(melchior, balthasar, casper)
    await reg.probe_all()
    set_registry(reg)

    db = Path(tempfile.mkdtemp(prefix="magi-cableado-")) / "t.db"
    swarm = SwarmOrchestrator(Blackboard(), bus, store=TaskStore(db))
    await swarm.submit_task("t-v6", ENCARGO, use_tools=False, max_rounds=max_rounds)

    # Se espera al ESTADO, no a un reloj: un sleep fijo mide el runner.
    for _ in range(int(40.0 / 0.05)):
        await asyncio.sleep(0.05)
        estado = (swarm.active_tasks.get("t-v6") or {}).get("status")
        if estado in ("completed", "failed", "WAITING_USER_APPROVAL"):
            break
    await asyncio.sleep(0.3)
    return swarm, posts, terminal, (melchior, balthasar, casper)


# =========================================================================
# F5 — el cuarto veredicto
# =========================================================================


@pytest.mark.asyncio
async def test_f5_el_desvio_de_foco_no_es_una_tarea_fallida(captura, monkeypatch, tmp_path):
    """
    «La pregunta era otra» es un cierre, no un fracaso.

    Hoy cae en el `else` del bucle de veredictos, que marca `failed` y
    publica «Tarea fallida tras N rondas». Y como ese `else` no corta el
    bucle, el debate ENTERO se repite hasta agotar las rondas: tres
    arbitrajes pagados para acabar entregando igual. El usuario pierde el
    hallazgo —que su pregunta apuntaba al sitio equivocado— y paga tres
    veces por perderlo.
    """
    mem = tmp_path / "memoria"
    mem.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MAGI_MEMORIA", str(mem))

    swarm, _posts, terminal, (_mel, _bal, casper) = await _ronda_con_veredicto(
        captura,
        "El cuello de botella esta en el bus del SH2 esclavo, no en el "
        "shader que discuten las tres propuestas.\n\n"
        "DECISIÓN: LA PREGUNTA ERA OTRA",
    )

    estado = (swarm.active_tasks.get("t-v6") or {}).get("status")
    assert estado != "failed", f"un desvio de foco quedo como tarea fallida (status={estado})"

    fallidas = [t for t in terminal if "Tarea fallida" in t]
    assert not fallidas, f"se publico como fallo: {fallidas}"

    assert casper._calls == 1, (
        f"el desvio no corto el bucle: Casper arbitro {casper._calls} veces " "el mismo debate"
    )

    aviso = [t for t in terminal if "pregunta era otra" in t.lower()]
    assert aviso, "el usuario no se entera del desvio; TERMINAL_OUT solo " f"trae: {terminal}"


@pytest.mark.asyncio
async def test_f5_el_desvio_queda_en_descartes_para_no_repetirlo(captura, monkeypatch, tmp_path):
    """
    El invariante de F5 es la memoria, no el mensaje.

    `registrar_descarte_pregunta_otra()` existe desde la v5.27.0 y no tiene
    ningun llamador en `magi/`: lo que el desvio enseño se pierde al cerrar
    la tarea, y la ronda siguiente puede repetirlo entero.
    """
    mem = tmp_path / "memoria"
    mem.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MAGI_MEMORIA", str(mem))

    await _ronda_con_veredicto(
        captura,
        "Las tres propuestas atacan el 1.2% del tiempo de frame.\n\n"
        "DECISIÓN: LA PREGUNTA ERA OTRA",
    )

    fichero = mem / "descartes.jsonl"
    assert fichero.exists(), (
        f"no se escribio descartes.jsonl; en {mem} hay " f"{[p.name for p in mem.iterdir()]}"
    )

    filas = [json.loads(l) for l in fichero.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert filas, "descartes.jsonl quedo vacio"
    assert any(
        "pregunta era otra" in (f.get("filosofia") or "").lower() for f in filas
    ), f"ninguna fila marca el desvio: {filas}"


@pytest.mark.asyncio
async def test_f5_una_aprobacion_normal_sigue_entrando_por_su_puerta(captura):
    """
    Control de la pareja anterior, en la misma corrida.

    Sin esto, las dos pruebas de arriba pasarian igual si el cableado
    mandase TODO por la rama del desvio. Un veredicto normal tiene que
    seguir parando en la aprobacion del usuario.
    """
    swarm, _posts, terminal, _provs = await _ronda_con_veredicto(
        captura, "Todo correcto.\n\nDECISIÓN: APROBADA"
    )

    estado = (swarm.active_tasks.get("t-v6") or {}).get("status")
    assert estado in (
        "WAITING_USER_APPROVAL",
        "completed",
    ), f"una aprobacion normal acabo en {estado}"
    assert not any(
        "pregunta era otra" in t.lower() for t in terminal
    ), "una aprobacion normal se conto como desvio de foco"
