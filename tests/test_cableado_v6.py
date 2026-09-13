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


async def _ronda_con_veredicto(captura, veredicto: str, *,
                               max_rounds: int = 3,
                               encargo: str = ENCARGO):
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
    await swarm.submit_task("t-v6", encargo, use_tools=False, max_rounds=max_rounds)

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
# =========================================================================
# F3 - el plan vivo
# =========================================================================

ENCARGO_EN_PARTES = """Prepara la ronda del emulador:
1. instrumenta el contador de ciclos del SH2 esclavo
2. mide una corrida de 60 segundos con ojos y oidos
3. escribe el hallazgo en la bitacora con su control
"""


@pytest.mark.asyncio
async def test_f3_el_plan_viaja_en_el_prompt_del_enjambre(captura):
    """
    El plan existe desde que nace la tarea y el enjambre no lo ve.

    `crear_plan_desde_enunciado` parte el encargo en sus partes y el plan se
    publica a la interfaz (`task.plan`), pero `PlanTarea.para_el_prompt()` no
    tiene ningun llamador: `inyecciones.acumuladas()` inyecta aceptacion, caja,
    bitacora, ronda, memoria y automodelo - el plan no esta.

    Es la mitad que hace util a F3. Un enjambre que no sabe que el encargo
    tenia tres partes no puede echar en falta las dos que no hizo: por eso se
    dejan partes sin hacer sin que nadie lo note, que es justo el fallo que F3
    venia a cerrar.
    """
    _swarm, _posts, _terminal, (melchior, _bal, _cas) = await _ronda_con_veredicto(
        captura, "Hecho. DECISION: APROBADA", encargo=ENCARGO_EN_PARTES)

    prompts = chr(10).join(melchior.vistos)
    assert "ESTADO DEL PLAN DE TRABAJO" in prompts, (
        "el plan no se inyecta en el prompt: el enjambre no sabe en cuantas "
        "partes se dividio el encargo")
    for parte in ("instrumenta el contador", "mide una corrida",
                  "escribe el hallazgo"):
        assert parte in prompts, f"falta la parte «{parte}» en el prompt"


@pytest.mark.asyncio
async def test_f3_un_encargo_sin_partes_no_ensucia_el_prompt(captura):
    """
    Control: sin partes que declarar, no se inyecta nada.

    `crear_plan_desde_enunciado` siempre crea al menos una parte -el encargo
    entero- y repetirla arriba del prompt seria ruido: el enjambre ya tiene el
    encargo delante. Sin este control, la prueba de arriba pasaria igual
    inyectando el plan SIEMPRE.
    """
    _swarm, _posts, _terminal, (melchior, _bal, _cas) = await _ronda_con_veredicto(
        captura, "Hecho. DECISION: APROBADA",
        encargo="arregla el parser de ROM que se cuelga con cabeceras cortas")

    prompts = chr(10).join(melchior.vistos)
    assert "ESTADO DEL PLAN DE TRABAJO" not in prompts, (
        "se inyecto un plan de una sola parte, que es repetir el encargo")
# =========================================================================
# F2 - los subagentes
# =========================================================================


@pytest.mark.asyncio
async def test_f2_sin_ejecutor_el_subagente_no_concluye_nada():
    """
    Un subagente sin quien lo ejecute no puede haber leido nada.

    `despachar_subagente` traia un "fallback determinista" que devolvia
    `Analisis de {mision}: verificado sin hallazgos criticos.` con exito=True.
    Es un «no encontre nada» sin haber mirado: sale al bus como SUBAGENT_TRACE
    y, en cuanto alguien cablee esto al debate, entra como evidencia.

    Este proyecto ya pago ese error dos veces —los 53,3 FPS que Melchior no
    midio y el `vita_gpu.h` que cito sin que existiera— y la regla que salio de
    ahi es que una conclusion fabricada es peor que el silencio, porque el
    critico la defiende y el debate se va detras de ella.
    """
    from magi.modules.swarm.subagentes import GestorSubagentes, despachar_subagente

    res = await despachar_subagente(
        nodo="MELCHIOR", familia="gpt", mision="recon del parser",
        round_num=1, gestor=GestorSubagentes())

    assert not res.exito, f"concluyo sin ejecutor: {res.conclusion!r}"
    assert not res.conclusion, f"fabrico una conclusion: {res.conclusion!r}"
    assert "sin ejecutor" in res.error.lower(), res.error
    assert "sin hallazgos" not in res.conclusion.lower()


def test_f2_ninguna_rama_del_enjambre_esta_apagada_con_un_false_literal():
    """
    El patron que escondio F2 durante una version entera.

    La unica llamada a subagentes vivia bajo `elif False:`. Nada lo cazaba: el
    trinquete de huerfanos busca el NOMBRE en cualquier fichero del repositorio
    y `despachar_subagente` aparecia en sus tests, asi que contaba como usado.
    El README y las notas de la v5.27.0 lo dieron por «consolidado».

    Codigo apagado con una constante no es una funcionalidad desactivada: es
    una funcionalidad que nadie sabe que esta apagada.
    """
    import ast

    raiz = Path(__file__).resolve().parents[1] / "magi"
    apagadas = []
    for fichero in raiz.rglob("*.py"):
        if "_attic" in fichero.parts or "__pycache__" in fichero.parts:
            continue
        try:
            arbol = ast.parse(fichero.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.If):
                continue
            prueba = nodo.test
            if isinstance(prueba, ast.Constant) and prueba.value in (False, 0):
                apagadas.append(f"{fichero.relative_to(raiz.parent)}:{nodo.lineno}")

    assert not apagadas, (
        "hay ramas apagadas con una constante falsa:\n  " + "\n  ".join(apagadas)
        + "\n\nO se conecta, o se borra: dejarla ahi hace creer que la"
          " funcionalidad existe.")
@pytest.mark.asyncio
async def test_f2_encendido_el_subagente_sale_al_bus_con_la_familia_de_su_nodo(
        captura, monkeypatch):
    """
    Con la bandera encendida, la rama existe y se recorre de verdad.

    Antes vivia bajo `elif False:`, asi que esta prueba no podia escribirse:
    no habia camino que recorrer. El invariante 1 —misma familia que su nodo—
    se comprueba en el evento, no en la funcion suelta.
    """
    monkeypatch.setenv("MAGI_SUBAGENTES", "1")
    trazas = []

    bus = captura[0]

    async def on_trace(event):
        trazas.append(event.payload)

    bus.subscribe("SUBAGENT_TRACE", on_trace)

    _swarm, _posts, _terminal, (melchior, _b, _c) = await _ronda_con_veredicto(
        captura, "Hecho. DECISION: APROBADA")

    assert trazas, "la rama de subagentes no se recorrio con la bandera encendida"
    assert trazas[0]["nodo"] == "MELCHIOR"
    assert trazas[0]["familia"] == melchior.family, (
        f"el subagente salio de otra familia: {trazas[0]['familia']} en vez de "
        f"{melchior.family}")
    assert trazas[0]["conclusion"], "salio al bus sin conclusion"


@pytest.mark.asyncio
async def test_f2_apagado_por_defecto_no_gasta_una_llamada(captura):
    """
    Control: sin la bandera no se despacha nada.

    La premisa de F2 —«una ronda con subagentes gasta MENOS contexto por
    nodo»— no esta medida, y cada subagente es una llamada mas a proveedores
    gratuitos que ya se degradan solos. Hasta que se mida contra un control en
    la misma corrida, apagado.
    """
    trazas = []
    bus = captura[0]

    async def on_trace(event):
        trazas.append(event.payload)

    bus.subscribe("SUBAGENT_TRACE", on_trace)

    await _ronda_con_veredicto(captura, "Hecho. DECISION: APROBADA")

    assert not trazas, f"se despacho un subagente sin pedirlo: {trazas}"
