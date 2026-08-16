"""
Telemetría, auditoría firmada y parentesco de ramas.

Las tres salen de mirar cómo lo hacen Zcode Desktop y Claude Code, y las tres
cubren un hueco concreto de MAGI:

* No se podía contestar «¿por qué tarda?»: solo había una latencia media.
* NAOKO escribe en el repositorio del usuario y no dejaba traza verificable.
* Las variantes paralelas publicaban sin nada que las distinguiera.
"""
from __future__ import annotations

import asyncio
import copy
import json
import time

import pytest

from magi.core.auditoria import Auditoria
from magi.core.store import telemetria as tl
from magi.core.store.state import TaskStore


@pytest.fixture()
def store(tmp_path):
    return TaskStore(path=tmp_path / "t.db")


@pytest.fixture()
def tel(store):
    return tl.Telemetria(store)


# ------------------------------------------------------------- telemetría

def test_un_turno_registra_el_tiempo_desglosado(tel, store):
    with tel.turno("t1", "MELCHIOR", familia="gpt") as t:
        time.sleep(0.02)
        t.primer_token()
        time.sleep(0.02)
        t.tokens(entrada=100, salida=50)

    with store._conn() as c:
        f = c.execute("SELECT * FROM turno").fetchone()
    assert f["estado"] == "completado"
    assert f["ms_primer_token"] > 0
    assert f["ms_total"] >= f["ms_primer_token"], "el total incluye el TTFT"
    assert f["tokens_in"] == 100 and f["tokens_out"] == 50


def test_un_turno_que_revienta_no_se_queda_en_curso(tel, store):
    """
    La misma clase de fallo que las tareas zombis. Algo que figura en curso sin
    estarlo envenena todo lo que lo lea, y ya nos costó un bloqueo permanente.
    """
    with pytest.raises(RuntimeError):
        with tel.turno("t1", "CASPER") as t:
            raise RuntimeError("el proveedor se cayó")

    with store._conn() as c:
        f = c.execute("SELECT * FROM turno").fetchone()
    assert f["estado"] == "error"
    assert f["fin"] is not None
    assert f["detalle_error"]


def test_una_cancelacion_no_se_cuenta_como_error(tel, store):
    with pytest.raises(asyncio.CancelledError):
        with tel.turno("t1", "CASPER"):
            raise asyncio.CancelledError()
    with store._conn() as c:
        f = c.execute("SELECT * FROM turno").fetchone()
    assert f["estado"] == "cancelado"
    assert f["cancelado_por_usuario"] == 1


@pytest.mark.parametrize("mensaje,tipo,rotar", [
    ("This model's maximum context length is 8192 tokens", "contexto", False),
    ("429 Too Many Requests", "cuota", True),
    ("Read timed out after 150s", "timeout", True),
    ("MissingRequirementsError: browser_cookie3", "credenciales", True),
    ("BrowserBlocked: MAGI no abre navegadores", "navegador_bloqueado", True),
])
def test_los_fallos_tienen_nombre_y_dicen_si_rotar_sirve(mensaje, tipo, rotar):
    """
    `contexto` es el que importa: si el prompt no cabe, cambiar de proveedor no
    arregla nada — el siguiente falla por lo mismo. MAGI lo leía como
    «proveedor roto» y recorría la familia entera para declararla agotada.
    """
    assert tl.clasifica_error(mensaje) == (tipo, rotar)


def test_el_contexto_excedido_queda_marcado_aparte(tel, store):
    with pytest.raises(RuntimeError):
        with tel.turno("t1", "MELCHIOR"):
            raise RuntimeError("maximum context length exceeded")
    with store._conn() as c:
        f = c.execute("SELECT * FROM turno").fetchone()
    assert f["contexto_excedido"] == 1
    assert f["tipo_error"] == "contexto"


def test_las_herramientas_de_solo_lectura_se_distinguen(tel, store):
    """
    En las 4.641 filas de Zcode, este registro destapa que las de solo lectura
    fallan el 63 % y las de escritura el 5 %. MAGI ya clasificaba bien
    (Tool.access, Tool.dangerous); lo que faltaba era guardar la llamada.
    """
    for i in range(6):
        uid = tel.herramienta("read_file", task_id="t1", solo_lectura=True)
        tel.herramienta_fin(uid, ok=(i == 0), inicio=time.time(),
                            error=None if i == 0 else "no existe")
    for _ in range(6):
        uid = tel.herramienta("edit_file", task_id="t1", solo_lectura=False,
                              peligrosa=True)
        tel.herramienta_fin(uid, ok=True, inicio=time.time())

    peor = tl.herramientas_que_fallan(store, minimo=5)[0]
    assert peor["herramienta"] == "read_file"
    assert peor["solo_lectura"] is True
    assert peor["tasa"] > 0.8


def test_una_salida_cortada_queda_marcada(tel, store):
    uid = tel.herramienta("grep", task_id="t1", solo_lectura=True)
    tel.herramienta_fin(uid, ok=True, inicio=time.time(), salida="x" * 100,
                        truncada=True)
    assert tl.resumen(store)["truncados"] == 1


def test_el_hedging_por_fin_se_puede_medir(tel, store):
    """
    HEDGE_AFTER_S=4 estaba puesto a ojo porque no había forma de saber si el
    segundo candidato llegaba a ganar alguna vez.
    """
    for i, gano_el_segundo in enumerate([True, False, False, False]):
        pid = f"pet_{i}"
        a = tel.llamada(pid, 0, task_id="t1")
        b = tel.llamada(pid, 1, task_id="t1")
        tel.llamada_fin(a, ok=True, inicio=time.time(),
                        gano=not gano_el_segundo)
        tel.llamada_fin(b, ok=True, inicio=time.time(), gano=gano_el_segundo)

    h = tl.sirve_el_hedging(store)
    assert h["peticiones"] == 4
    assert h["coberturas"] == 4
    assert h["gano_la_cobertura"] == 1
    assert h["utilidad"] == 0.25


def test_medir_no_puede_romper_lo_medido(store, monkeypatch):
    """
    La regla de oro. Un sistema que se cae porque no pudo escribir una métrica
    es peor que uno sin métricas.
    """
    t = tl.Telemetria(store)

    def revienta(*a, **k):
        raise RuntimeError("disco lleno")

    monkeypatch.setattr(store, "_conn", revienta)
    with t.turno("t1", "MELCHIOR") as turno:      # no debe lanzar
        turno.primer_token()
    assert t.herramienta("x") .startswith("uso_")
    assert t.llamada("p", 0).startswith("lla_")


# -------------------------------------------------------------- auditoría

def test_cada_accion_queda_firmada(tmp_path):
    a = Auditoria(raiz=tmp_path)
    a.registrar("git.commit", detalle="arreglo el bus", ficheros=3)
    a.registrar("git.publicado", detalle="v5.1.6")
    v = a.verificar()
    assert v["ok"] and v["intacta"]
    assert v["entradas"] == 2


def test_editar_una_linea_se_detecta(tmp_path):
    a = Auditoria(raiz=tmp_path)
    a.registrar("git.commit", detalle="toca 3 ficheros", ficheros=3)
    a.registrar("git.publicado", detalle="v5.1.6")

    lineas = a.diario.read_text(encoding="utf-8").splitlines()
    d = json.loads(lineas[0])
    d["ficheros"] = 1                       # alguien maquilla lo que tocó
    lineas[0] = json.dumps(d, ensure_ascii=False)
    a.diario.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    v = a.verificar()
    assert not v["ok"]
    assert v["rota_en_linea"] == 1


def test_borrar_una_linea_tambien_se_detecta(tmp_path):
    """
    Esto es lo que aporta ENCADENAR. Firmar cada línea suelta detecta que una
    cambió; encadenar detecta además que una desapareció, que es la forma
    cómoda de esconder algo.
    """
    a = Auditoria(raiz=tmp_path)
    for i in range(4):
        a.registrar("git.orden", detalle=f"orden {i}")

    lineas = a.diario.read_text(encoding="utf-8").splitlines()
    del lineas[1]                                  # se borra la del medio
    a.diario.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    v = a.verificar()
    assert not v["ok"]
    assert v["rota_en_linea"] == 2


def test_auditar_nunca_puede_tumbar_la_accion_auditada(tmp_path, monkeypatch):
    a = Auditoria(raiz=tmp_path)
    monkeypatch.setattr(a, "_ultima_firma",
                        lambda: (_ for _ in ()).throw(OSError("disco lleno")))
    a.registrar("git.push", detalle="algo")        # no debe lanzar


def test_el_diario_sin_estrenar_esta_intacto(tmp_path):
    assert Auditoria(raiz=tmp_path).verificar()["ok"] is True


def test_naoko_audita_antes_de_tocar_tu_repositorio():
    """Guard: si alguien quita la llamada, esto se entera."""
    import inspect

    from magi.modules.infrastructure import naoko
    fuente = inspect.getsource(naoko.NaokoAgent._git_push)
    assert "auditoria" in fuente
    assert "git.commit" in fuente and "git.publicado" in fuente


# ---------------------------------------------------- parentesco de ramas

class AgenteFalso:
    """Lo mínimo que `generate_variants` necesita tocar."""
    family = "gpt"
    role_name = "MELCHIOR"

    def __init__(self):
        self.seed = 0
        self.rama = None
        self.rama_rol = ""
        self.rama_profundidad = 0
        self.vistos: list[tuple] = []

    async def generate_proposal(self, task_id, command, round_num, *a, **k):
        # Cede el control a propósito: así se reproduce el entrelazado real de
        # `asyncio.gather`, que es donde estaba el fallo.
        await asyncio.sleep(0.01)
        self.vistos.append((self.seed, self.rama))
        return {"content": f"propuesta con semilla {self.seed}"}


def test_cada_variante_conserva_su_semilla_pese_a_ir_en_paralelo():
    """
    FALLO PREEXISTENTE, encontrado al añadir el parentesco.

    El código hacía `agent.seed = ...` sobre el agente COMPARTIDO y lo
    restauraba en un `finally`. En secuencial funciona; con `asyncio.gather`
    no: la primera variante pone su semilla, cede en el primer `await`, la
    segunda la pisa... y las tres acaban llamando con la misma. Las «variantes
    con semillas distintas» eran la misma petición repetida N veces, que es
    justo lo contrario de lo que se buscaba.
    """
    from magi.modules.swarm.parallel import generate_variants

    a = AgenteFalso()
    asyncio.run(generate_variants(a, task_id="t1", command="haz algo",
                                  round_num=1, n=3))
    semillas = [s for s, _ in a.vistos]
    assert len(set(semillas)) == 3, f"semillas colisionadas: {semillas}"


def test_cada_variante_tiene_su_propia_rama():
    """
    Sin esto, las N variantes publican con el mismo task_id y la interfaz las
    apila como si fueran una conversación, cuando son N intentos paralelos.
    """
    from magi.modules.swarm.parallel import generate_variants

    a = AgenteFalso()
    asyncio.run(generate_variants(a, task_id="t1", command="x", round_num=2,
                                  n=3))
    ramas = [r for _, r in a.vistos]
    assert len(set(ramas)) == 3
    assert all(r.startswith("t1/r2/melchior/v") for r in ramas)


def test_el_agente_original_no_queda_manchado():
    """La copia es por variante; el agente compartido no cambia."""
    from magi.modules.swarm.parallel import generate_variants

    a = AgenteFalso()
    asyncio.run(generate_variants(a, task_id="t1", command="x", round_num=1,
                                  n=2))
    assert a.rama is None
    assert a.seed == 0


def test_la_rama_viaja_en_el_payload_de_los_eventos():
    from magi.core.blackboard import Blackboard
    from magi.modules.swarm.agents import SwarmAgentBase

    class Bus:
        def subscribe(self, *a, **k): pass

    ag = SwarmAgentBase(Blackboard(), Bus())
    assert ag._rama() == {}, "sin rama no se ensucia el payload"

    ag.rama = "t1/r1/melchior/v0"
    ag.rama_rol = "enfoque A"
    ag.rama_profundidad = 1
    p = ag._rama()
    assert p["rama"] == "t1/r1/melchior/v0"
    assert p["rama_rol"] == "enfoque A"
    assert p["profundidad"] == 1
