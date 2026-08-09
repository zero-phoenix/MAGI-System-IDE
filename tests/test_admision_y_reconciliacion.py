"""
Lo que impide que el sistema vuelva a bloquearse.

El fallo que estos tests protegen tenía dos mitades que por separado parecen
inocentes:

1. `_rehydrate()` devolvía las tareas `in_progress` a memoria sin relanzar su
   bucle. Zombis: figuran trabajando, no las ejecuta nadie.
2. `submit_task` hacía `return` mudo si la tarea estaba `in_progress`.

Juntas dejaron esta instalación bloqueada de forma PERMANENTE: la fila con id
`default` —el que manda siempre la interfaz— llevaba `in_progress` desde el 8
de agosto a las 22:38, y cada mensaje del usuario chocaba contra ella y se
descartaba sin dejar rastro. En cada arranque, para siempre.
"""
from __future__ import annotations

import asyncio
import sqlite3

import pytest

from magi.core.store.state import (TaskStore, TaskState, INTERRUMPIDA,
                                   EN_CURSO, ESPERANDO_USUARIO)
from magi.core.store.admision import (LibroDeAdmision, ADMITIDA, PROMOVIDA,
                                      DESCARTADA, AHORA, ENCOLAR)


@pytest.fixture()
def store(tmp_path):
    return TaskStore(path=tmp_path / "t.db")


# --------------------------------------------------------------- migraciones

def test_la_base_queda_al_dia(store):
    inf = store.estado_migraciones()
    assert inf["al_dia"], inf
    assert inf["pendientes"] == []
    assert inf["discrepantes"] == []


def test_migrar_es_idempotente(tmp_path):
    p = tmp_path / "t.db"
    TaskStore(path=p)
    TaskStore(path=p)
    TaskStore(path=p)
    c = sqlite3.connect(p)
    n = c.execute("select count(*) from migracion_esquema").fetchone()[0]
    c.close()
    from magi.core.store.migraciones import MIGRACIONES
    assert n == len(MIGRACIONES), "una migración se aplicó dos veces"


def test_una_migracion_editada_se_detecta(store):
    """Publicada y luego editada: se avisa y NO se reaplica."""
    from magi.core.store import migraciones
    with store._conn() as c:
        c.execute("update migracion_esquema set checksum='cambiado' "
                  "where id='0004_libro_de_admision'")
    with store._conn() as c:
        inf = migraciones.informe(c)
    assert "0004_libro_de_admision" in inf["discrepantes"]


# ------------------------------------------------------------ reconciliación

def test_una_tarea_en_curso_al_arrancar_no_puede_seguir_en_curso(store):
    """
    EL INVARIANTE DE LA FASE 0.

    Nada más arrancar no hay ni un bucle vivo. Cualquier cosa que figure
    `in_progress` es un zombi por definición.
    """
    store.save(TaskState(task_id="default", command="algo", status=EN_CURSO))
    assert store.reconciliar() == ["default"]
    assert store.load("default").status == INTERRUMPIDA


def test_reconciliar_no_toca_las_que_esperan_al_usuario(store):
    store.save(TaskState(task_id="t1", command="x", status=ESPERANDO_USUARIO))
    assert store.reconciliar() == []
    assert store.load("t1").status == ESPERANDO_USUARIO


def test_reconciliar_escribe_por_que(store):
    store.save(TaskState(task_id="t1", command="x", status=EN_CURSO))
    store.reconciliar()
    assert store.load("t1").motivo_cierre


def test_una_interrumpida_sigue_siendo_reanudable(store):
    store.save(TaskState(task_id="t1", command="x", status=EN_CURSO))
    store.reconciliar()
    assert [t.task_id for t in store.resumable()] == ["t1"]


def test_reconciliar_vivas_respeta_los_bucles_que_si_corren(store):
    store.save(TaskState(task_id="viva", command="x", status=EN_CURSO))
    store.save(TaskState(task_id="zombi", command="x", status=EN_CURSO))
    rec = store.reconciliar_vivas(lambda t: t == "viva")
    assert rec == ["zombi"]
    assert store.load("viva").status == EN_CURSO
    assert store.load("zombi").status == INTERRUMPIDA


# --------------------------------------------------------- ciclo de vida

def test_lo_archivado_deja_de_rehidratarse(store):
    """La causa de que se acumularan 7 tareas desde el 7 de agosto."""
    store.save(TaskState(task_id="vieja", command="x",
                         status=ESPERANDO_USUARIO))
    assert len(store.resumable()) == 1
    store.archivar("vieja", "cerrada por el usuario")
    assert store.resumable() == []
    assert store.load("vieja") is not None, "archivar no es borrar"


def test_una_tarea_sin_orden_tiene_nombre(store):
    """En la base real hay dos filas con `command` vacío."""
    store.save(TaskState(task_id="t_vacia", command=""))
    assert store.load("t_vacia").nombre


def test_bifurcar_hereda_contexto_sin_contaminar_el_origen(store):
    store.save(TaskState(task_id="madre", command="original",
                         status=ESPERANDO_USUARIO, engine="deep",
                         last_proposal={"content": "P"}))
    hija = store.bifurcar("madre", "hija", "pregunta nueva")
    assert hija is not None
    assert hija.bifurcada_de == "madre"
    assert hija.engine == "deep"
    assert hija.last_proposal == {"content": "P"}
    assert store.load("madre").command == "original"
    assert store.load("madre").status == ESPERANDO_USUARIO


# ------------------------------------------------------- libro de admisión

def test_admitir_deja_constancia_antes_de_decidir(store):
    lib = LibroDeAdmision(store)
    e = lib.admitir("crea un tetris", "default")
    assert e.estado == ADMITIDA
    assert e.secuencia_admitida >= 1
    assert lib.recientes()[0].texto == "crea un tetris"


def test_no_se_puede_descartar_sin_motivo(store):
    """
    El invariante con dientes.

    Descartar sin escribir por qué es EXACTAMENTE el fallo original. Aquí
    revienta en Python; y si alguien esquiva el módulo y escribe SQL a pelo,
    revienta la restricción CHECK de la migración 0004.
    """
    lib = LibroDeAdmision(store)
    e = lib.admitir("hola")
    with pytest.raises(ValueError):
        lib.descartar(e.id, "")
    with pytest.raises(ValueError):
        lib.descartar(e.id, "   ")


def test_la_base_tambien_lo_impide_por_su_cuenta(store):
    lib = LibroDeAdmision(store)
    e = lib.admitir("hola")
    with pytest.raises(sqlite3.IntegrityError):
        with store._conn() as c:
            c.execute("update entrada_usuario set estado='descartada' "
                      "where id=?", (e.id,))


def test_descartar_con_motivo_lo_guarda(store):
    lib = LibroDeAdmision(store)
    e = lib.admitir("hola")
    lib.descartar(e.id, "el enjambre no estaba conectado")
    guardada = lib.recientes()[0]
    assert guardada.estado == DESCARTADA
    assert "no estaba conectado" in guardada.motivo
    assert "descartada" in guardada.resumen()


def test_la_cola_respeta_el_orden_de_llegada(store):
    lib = LibroDeAdmision(store)
    for t in ("primera", "segunda", "tercera"):
        lib.admitir(t, "t1", entrega=ENCOLAR)
    assert [e.texto for e in lib.en_cola("t1")] == ["primera", "segunda",
                                                    "tercera"]
    assert lib.siguiente_en_cola("t1").texto == "primera"


def test_promover_saca_de_la_cola(store):
    lib = LibroDeAdmision(store)
    e = lib.admitir("x", "t1", entrega=ENCOLAR)
    lib.promover(e.id, "t1")
    assert lib.en_cola("t1") == []


def test_perdidas_detecta_ciclos_sin_cerrar(store):
    """
    Una entrada `admitida` con entrega `ahora` que nadie resolvió es un camino
    del código que no cierra el ciclo. Antes eso era invisible; ahora se ve.
    """
    lib = LibroDeAdmision(store)
    e = lib.admitir("huerfana", "t1")
    assert [x.id for x in lib.perdidas()] == [e.id]
    lib.promover(e.id, "t1")
    assert lib.perdidas() == []


# ------------------------------------------- el escenario real, de extremo a
#                                              extremo

class BusEspia:
    """Bus que solo apunta lo que se publica."""
    def __init__(self):
        self.eventos = []

    async def publish(self, event):
        self.eventos.append((event.topic, event.payload))

    def subscribe(self, *a, **k):
        pass

    def textos(self) -> str:
        return " ".join(
            str(p.get("content", p)) if isinstance(p, dict) else str(p)
            for _, p in self.eventos)


def _orquestador(store, bus):
    from magi.core.blackboard import Blackboard
    from magi.modules.swarm.orchestrator import SwarmOrchestrator
    return SwarmOrchestrator(Blackboard(), bus, store=store)


def test_el_bloqueo_permanente_ya_no_ocurre(store, monkeypatch):
    """
    REPRODUCE EL FALLO EXACTO DE ESTA MÁQUINA.

    Estado de partida idéntico al de la base real del usuario: la tarea
    `default` figura `in_progress` desde una sesión anterior, sin bucle vivo.

    Antes: `submit_task` hacía `return` mudo y el mensaje desaparecía. Para
    siempre, porque la fila nunca cambiaba.
    """
    store.save(TaskState(
        task_id="default", status=EN_CURSO,
        command="por que la filosofia es la madre de todas las ciencias"))

    bus = BusEspia()
    orq = _orquestador(store, bus)

    # Al construirse ya debe haber reconciliado: nada figura en curso.
    assert store.load("default").status == INTERRUMPIDA
    assert orq.active_tasks["default"]["status"] == INTERRUMPIDA

    lanzados = []
    monkeypatch.setattr(orq, "_spawn_loop", lambda tid: lanzados.append(tid))

    asyncio.run(orq.submit_task(
        "default", "crea un juego de tetris en un ejecutable portable"))

    # 1. Se retoma de verdad, no se ignora.
    assert lanzados == ["default"]
    assert orq.active_tasks["default"]["command"].startswith("crea un juego")
    # 2. El usuario se entera.
    assert bus.eventos, "el silencio ERA el fallo"
    assert "tetris" in orq.active_tasks["default"]["command"]
    # 3. Queda escrito en el libro.
    lib = LibroDeAdmision(store)
    assert lib.recientes()[0].estado == PROMOVIDA
    assert lib.perdidas() == []


def test_si_de_verdad_esta_trabajando_se_encola_y_se_avisa(store, monkeypatch):
    """
    El caso 2: la tarea SÍ tiene un bucle vivo.

    Aquí es donde Zcode pone `delivery='queue'` y Claude Code `queued`. No se
    tira el mensaje: espera turno y se dice en voz alta.
    """
    store.save(TaskState(task_id="t1", command="algo", status=EN_CURSO))
    bus = BusEspia()
    orq = _orquestador(store, bus)

    # Simula que t1 tiene bucle vivo, y devuélvela a en curso.
    orq.active_tasks["t1"]["status"] = EN_CURSO
    from magi.core import cancel
    monkeypatch.setattr(cancel.supervisor(), "is_running",
                        lambda tid: tid == "t1")
    monkeypatch.setattr(orq, "_spawn_loop",
                        lambda tid: pytest.fail("no debe relanzar una viva"))

    asyncio.run(orq.submit_task("t1", "una cosa mas"))

    lib = LibroDeAdmision(store)
    cola = lib.en_cola("t1")
    assert [e.texto for e in cola] == ["una cosa mas"]
    assert "COLA" in bus.textos() or "cola" in bus.textos()
    assert any(t == "swarm.entrada_encolada" for t, _ in bus.eventos)


def test_lo_encolado_se_atiende_al_cerrar_la_ronda(store):
    store.save(TaskState(task_id="t1", command="algo", status=EN_CURSO))
    bus = BusEspia()
    orq = _orquestador(store, bus)
    orq.active_tasks["t1"]["status"] = EN_CURSO

    lib = LibroDeAdmision(store)
    lib.admitir("lo siguiente", "t1", entrega=ENCOLAR)

    assert asyncio.run(orq._vaciar_cola("t1")) is True
    assert orq.active_tasks["t1"]["command"] == "lo siguiente"
    assert lib.en_cola("t1") == []
    assert asyncio.run(orq._vaciar_cola("t1")) is False


def test_ninguna_entrada_se_pierde_pase_lo_que_pase(store, monkeypatch):
    """
    EL INVARIANTE GENERAL. Si `_despachar` revienta, la entrada queda como
    `fallida` con el motivo — nunca desaparecida.
    """
    bus = BusEspia()
    orq = _orquestador(store, bus)

    async def revienta(*a, **k):
        raise RuntimeError("el clasificador se cayó")

    monkeypatch.setattr(orq, "_despachar", revienta)
    with pytest.raises(RuntimeError):
        asyncio.run(orq.submit_task("t1", "una pregunta importante"))

    lib = LibroDeAdmision(store)
    reg = lib.recientes()[0]
    assert reg.texto == "una pregunta importante"
    assert reg.estado == "fallida"
    assert "clasificador" in reg.motivo
