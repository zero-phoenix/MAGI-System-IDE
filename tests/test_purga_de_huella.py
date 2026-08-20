"""
El arnés de medida no puede dejar basura en la base del usuario.

LO QUE PASÓ, MEDIDO
===================
Estado real de `magi_brain.db` el 2026-08-20, tras una tarde de auditorías:

    total: 23   WAITING_USER_APPROVAL: 14   interrumpida: 7

Trece de esas veintitrés eran `auditoria-<epoch>`: una fila por cada pasada de
`scripts/auditar_sistema.py`. Ninguna la había abierto el usuario. Cada una
quedaba esperando una aprobación que nadie iba a dar, el kernel la rehidrataba
en cada arranque y la interfaz la listaba como una conversación pendiente.

El usuario lo vio así: «le escribí a Naoko y no me responde». Entre sus
conversaciones reales había trece falsas, y la lista ya no le decía nada.

Estos tests fijan las dos mitades del arreglo: que la purga borre lo sintético,
y —lo más importante— que NO toque nada del usuario.
"""
from __future__ import annotations

from magi.core.store.state import (
    ESPERANDO_USUARIO,
    TaskState,
    TaskStore,
)


def _store(tmp_path) -> TaskStore:
    return TaskStore(tmp_path / "prueba.db")


def test_purga_las_tareas_del_arnes(tmp_path):
    store = _store(tmp_path)
    for tid in ("auditoria", "auditoria-1787204151", "auditoria-1787215012",
                "eval-99", "t-techo", "bench-3"):
        store.save(TaskState(task_id=tid, command="medir",
                             status=ESPERANDO_USUARIO))

    purgadas = store.purgar_sinteticas()

    assert len(purgadas) == 6, purgadas
    assert store.resumable() == []


def test_no_toca_las_conversaciones_del_usuario(tmp_path):
    """
    La mitad que importa.

    Una purga demasiado ansiosa es infinitamente peor que la basura que
    limpia: borrar sin avisar el trabajo de alguien no tiene arreglo.
    """
    store = _store(tmp_path)
    store.save(TaskState(task_id="task_29ceb5d6",
                         command="por que la filosofia es la madre de todas",
                         status=ESPERANDO_USUARIO))
    store.save(TaskState(task_id="auditoria-1787204151", command="medir",
                         status=ESPERANDO_USUARIO))
    # Nombre que EMPIEZA distinto pero contiene el prefijo: no es sintética.
    store.save(TaskState(task_id="task_auditoria_de_seguridad",
                         command="audita mi repositorio", status=ESPERANDO_USUARIO))

    purgadas = store.purgar_sinteticas()

    assert purgadas == ["auditoria-1787204151"]
    vivas = {t.task_id for t in store.resumable()}
    assert vivas == {"task_29ceb5d6", "task_auditoria_de_seguridad"}


def test_respeta_lo_que_el_usuario_bifurco_desde_una_auditoria(tmp_path):
    """
    Si alguien ramificó trabajo real desde una tarea de medida, ese trabajo es
    suyo aunque el identificador padre fuera sintético.
    """
    store = _store(tmp_path)
    store.save(TaskState(task_id="auditoria-1787204151", command="medir",
                         status=ESPERANDO_USUARIO))
    store.bifurcar("auditoria-1787204151", "auditoria-hija",
                   "sigue con esto, me interesa")

    purgadas = store.purgar_sinteticas()

    assert purgadas == ["auditoria-1787204151"]
    assert store.load("auditoria-hija") is not None


def test_el_arnes_llama_a_la_purga():
    """
    Que el método exista no sirve de nada si `auditar_sistema.py` no lo usa —
    que es exactamente la forma que tuvo este fallo durante trece pasadas.
    """
    import pathlib

    arnes = (pathlib.Path(__file__).resolve().parents[1]
             / "scripts" / "auditar_sistema.py").read_text(encoding="utf-8",
                                                           errors="replace")
    assert "purgar_sinteticas()" in arnes, (
        "el arnés de auditoría debe recoger su propia huella antes de salir")
