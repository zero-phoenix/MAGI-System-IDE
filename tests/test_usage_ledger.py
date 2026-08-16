"""
Contabilidad de tokens (§3.4) y panel de coste (§7.3).

Estaba construida ENTERA menos el cable del medio, y por eso no saltó nunca:

  · `agent_loop.py` sumaba tokens_in/tokens_out de cada respuesta.
  · `AgentTurn` los traía hasta el enjambre.
  · `TaskStore.record_usage()` sabía escribirlos en `token_ledger`.
  · Nadie llamaba a `record_usage`.

Los números llegaban a `agents.py`, se metían en una cadena de log con
`turn.summary()` y se tiraban. La tabla llevaba vacía desde que se creó, así
que un panel de coste habría enseñado cero con toda naturalidad.

Es la misma clase de fallo que una pieza sin conectar, pero en los datos — y
más difícil de ver, porque no hay ningún import que falte.
"""
import json
import re
from pathlib import Path

import pytest
from source_helpers import code_of

from magi.core.store.state import TaskStore

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def store(tmp_path):
    return TaskStore(tmp_path / "brain.db")


def test_registra_y_agrega(store):
    store.record_usage(task_id="t1", agent="MELCHIOR", provider="g4f-deepseek",
                       family="deepseek", tokens_in=100, tokens_out=200,
                       latency_ms=1500)
    store.record_usage(task_id="t1", agent="CASPER", provider="g4f-qwen",
                       family="qwen", tokens_in=50, tokens_out=25,
                       latency_ms=800)
    u = store.usage_for("t1")
    assert u["calls"] == 2
    assert u["total_tokens"] == 375
    assert {a["agent"] for a in u["by_agent"]} == {"MELCHIOR", "CASPER"}


def test_no_mezcla_tareas(store):
    store.record_usage(task_id="t1", agent="A", provider="p", family="f",
                       tokens_in=10, tokens_out=10)
    store.record_usage(task_id="t2", agent="A", provider="p", family="f",
                       tokens_in=99, tokens_out=99)
    assert store.usage_for("t1")["total_tokens"] == 20


def test_una_tarea_sin_gasto_devuelve_ceros_no_error(store):
    u = store.usage_for("inexistente")
    assert u["calls"] == 0 and u["total_tokens"] == 0


# ------------------------------------------------------------- el cable

def test_el_enjambre_llama_a_record_usage():
    """
    EL FALLO. Sin esta llamada todo lo demás es decorado: el esquema existe,
    los métodos existen, y la tabla no recibe una fila en su vida.
    """
    src = (ROOT / "magi/modules/swarm/agents.py").read_text(encoding="utf-8")
    assert "record_usage(" in src, \
        "el enjambre no registra el gasto: token_ledger seguirá vacía"
    assert "task.usage" in src, \
        "el gasto no se publica al bus: la interfaz no puede enseñarlo"


def test_los_tokens_del_turno_no_se_quedan_en_el_log():
    """
    Regresión concreta: `turn.tokens_in` y `turn.tokens_out` solo aparecían
    dentro de `turn.summary()`, que es una cadena para el log. Un dato que
    solo existe formateado no es un dato.
    """
    src = (ROOT / "magi/modules/swarm/agents.py").read_text(encoding="utf-8")
    assert "turn.tokens_in" in src and "turn.tokens_out" in src


def test_contabilizar_no_puede_tumbar_el_turno():
    """
    Un fallo escribiendo la contabilidad no puede perder la respuesta que el
    usuario estaba esperando. Se registra en el log y se sigue.
    """
    import inspect

    from magi.modules.swarm.agents import SwarmAgentBase
    src = inspect.getsource(SwarmAgentBase._record_usage)
    assert src.count("except Exception") >= 2, \
        "registrar y publicar el gasto deben ir protegidos por separado"


@pytest.mark.asyncio
async def test_el_gasto_llega_al_bus():
    """De extremo a extremo sin red: se publica lo que la interfaz necesita."""
    from magi.core.bus import BusEvent, MagiBus
    from magi.modules.swarm.agents import SwarmAgentBase

    class TurnoFalso:
        provider_id, tokens_in, tokens_out = "g4f-deepseek", 120, 340
        elapsed_s, iterations, tool_calls = 2.5, 3, []

    recibidos = []

    class BusEspia(MagiBus):
        async def publish(self, ev: BusEvent):
            recibidos.append(ev)

    agente = SwarmAgentBase.__new__(SwarmAgentBase)
    agente.bus = BusEspia()
    agente.role_name = "MELCHIOR"
    await agente._record_usage("t42", TurnoFalso())

    ev = next(e for e in recibidos if e.topic == "task.usage")
    assert ev.payload["tokens_in"] == 120
    assert ev.payload["tokens_out"] == 340
    assert ev.payload["family"] == "deepseek"
    assert ev.payload["task_id"] == "t42"
    json.dumps(ev.payload)          # tiene que viajar por el websocket


# ------------------------------------------------------ el lado de la interfaz

def test_la_interfaz_escucha_el_gasto():
    socket = (ROOT / "magi-gui/src/useMagiSocket.ts").read_text(encoding="utf-8")
    assert "task.usage" in socket, \
        "el backend publica el gasto y la interfaz no lo escucha"


def test_el_panel_de_coste_esta_conectado():
    app = (ROOT / "magi-gui/src/App.tsx").read_text(encoding="utf-8")
    codigo = re.sub(r"/\*.*?\*/|//[^\n]*", "", app, flags=re.S)
    assert "CostPanel" in codigo
    assert '"Coste"' in codigo, "la pestaña no aparece en la barra"


def test_el_payload_trae_lo_que_el_panel_agrega():
    """
    Contrato: si el backend deja de mandar un campo, el panel no da error —
    muestra NaN o cero, que es peor.
    """
    agents = (ROOT / "magi/modules/swarm/agents.py").read_text(encoding="utf-8")
    cost = (ROOT / "magi-gui/src/lib/cost.ts").read_text(encoding="utf-8")
    campos = re.search(r"interface UsageEntry \{(.*?)\n\}", cost, re.S).group(1)
    for campo in re.findall(r"^\s*(\w+):", campos, re.M):
        if campo == "id":          # lo pone el store al recibir
            continue
        assert f'"{campo}"' in agents, \
            f"el panel espera '{campo}' y el backend no lo publica"


# --------------------------------------------------- §7.3 historiales acotados

def test_el_terminal_no_crece_sin_limite():
    """
    Medido antes: 4000 anexiones daban 4,9 MB de cadena, y App.tsx la recorría
    ENTERA dos veces por repintado buscando una frase — 2,7 ms por repintado,
    con un useEffect que se dispara en cada línea nueva. La salida de un solo
    `grep` son cientos de líneas seguidas.
    """
    store = code_of(ROOT / "magi-gui/src/store.ts")
    assert "appendBounded" in store, "el terminal vuelve a crecer sin límite"
    assert "state.terminalOutput + text" not in store


def test_la_aprobacion_no_se_detecta_escaneando_el_terminal():
    """
    Se buscaba la frase dentro de todo el historial en cada repintado. Ahora
    la bandera se pone cuando llega el texto, una sola vez.
    """
    codigo = code_of(ROOT / "magi-gui/src/App.tsx")
    assert 'terminalOutput.includes(' not in codigo, \
        "vuelve a escanearse el terminal entero en cada repintado"
    assert "awaitingApproval" in codigo


def test_la_lista_de_mensajes_esta_acotada():
    """
    Lo caro no era el `.map` (3 ms por 50 repintados de 800 mensajes) sino
    montar un ReactMarkdown por mensaje. Se arregla no montándolos.
    """
    codigo = code_of(ROOT / "magi-gui/src/App.tsx")
    assert "tail(messages)" in codigo
    assert "{messages.map(" not in codigo, "se vuelven a pintar todos"
