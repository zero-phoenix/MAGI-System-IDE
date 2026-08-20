"""
Estado persistente de tareas (Plan MAGI 9.0 §1.4).

EL PROBLEMA
===========
orchestrator.py:17 — `self.active_tasks = {}`

Un diccionario en RAM. Cerrar la ventana, un crash de PyWebView o un reinicio
perdían todo: la conversación, la ronda en curso, la propuesta pendiente de
aprobación. Y esto con una base de datos SQLite ya presente en el proyecto, con
tablas `tasks` y `debates` que el orquestador nunca tocaba.

LA SOLUCIÓN
===========
Estado en SQLite + registro de eventos. Al arrancar, el kernel rehidrata las
tareas en `in_progress` o `WAITING_USER_APPROVAL` y puede reanudarlas.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..paths import db_path

logger = logging.getLogger(__name__)

# `interrumpida`: estaba en curso cuando el proceso murió. Es reanudable, pero
# NO está corriendo. Antes no existía este estado, y por eso una tarea que
# quedó a medias volvía como `in_progress` para siempre: figuraba trabajando
# sin que nadie la ejecutara, y `submit_task` descartaba en silencio todo lo
# que el usuario escribiera después. Ver `reconciliar()`.
INTERRUMPIDA = "interrumpida"
EN_CURSO = "in_progress"
ESPERANDO_USUARIO = "WAITING_USER_APPROVAL"

RESUMABLE = (EN_CURSO, ESPERANDO_USUARIO, INTERRUMPIDA)


@dataclass
class TaskState:
    task_id: str
    command: str
    status: str = "in_progress"
    round: int = 1
    engine: str = "fast"
    narrative_style: str = "tecnico"
    route: str = "task"
    max_rounds: int = 3
    use_tools: bool = True
    last_proposal: dict | None = None
    last_critique: dict | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    # Ciclo de vida (migración 0003). `titulo` va aparte de `command` porque en
    # la base real de este equipo hay dos tareas con `command` vacío: se
    # crearon sin orden y nadie pudo nombrarlas después.
    titulo: str = ""
    archivada: bool = False
    borrada: bool = False
    sin_leer_en: float | None = None
    bifurcada_de: str | None = None
    motivo_cierre: str | None = None
    # Presupuesto (v6.0 §A1): techo de llamadas y de regeneraciones. Solo lo
    # incrementa el presupuesto; el resto del sistema lo lee.
    calls_used: int = 0
    rebuilds: int = 0

    @property
    def resumable(self) -> bool:
        return (self.status in RESUMABLE
                and not self.archivada and not self.borrada)

    @property
    def agotado(self) -> bool:
        from ..presupuesto import para as _para
        p = _para(self.engine)
        return self.calls_used >= p.llamadas

    @property
    def nombre(self) -> str:
        """Cómo se enseña en una lista. Nunca vacío."""
        if self.titulo:
            return self.titulo
        t = (self.command or "").strip().splitlines()[0] if self.command else ""
        return (t[:60] + "…") if len(t) > 60 else (t or f"(sin orden) {self.task_id}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> TaskState:
        return cls(
            task_id=row["task_id"], command=row["command"], status=row["status"],
            round=row["round_num"], engine=row["engine"],
            narrative_style=row["narrative_style"], route=row["route"],
            max_rounds=row["max_rounds"], use_tools=bool(row["use_tools"]),
            last_proposal=json.loads(row["last_proposal"]) if row["last_proposal"] else None,
            last_critique=json.loads(row["last_critique"]) if row["last_critique"] else None,
            created_at=row["created_at"], updated_at=row["updated_at"],
            **cls._ciclo_de_vida(row),
        )

    @staticmethod
    def _ciclo_de_vida(row: sqlite3.Row) -> dict:
        """
        Lee las columnas de la migración 0003 si están.

        Se comprueba en vez de darlas por hechas porque un test puede crear la
        tabla a mano y porque una base a la que le falte la migración debe
        seguir cargando, no reventar.
        """
        try:
            k = set(row.keys())
        except Exception:
            return {}
        return {
            "titulo": (row["titulo"] or "") if "titulo" in k else "",
            "archivada": bool(row["archivada"]) if "archivada" in k else False,
            "borrada": bool(row["borrada"]) if "borrada" in k else False,
            "sin_leer_en": row["sin_leer_en"] if "sin_leer_en" in k else None,
            "bifurcada_de": row["bifurcada_de"] if "bifurcada_de" in k else None,
            "motivo_cierre": row["motivo_cierre"] if "motivo_cierre" in k else None,
            "calls_used": int(row["calls_used"]) if "calls_used" in k else 0,
            "rebuilds": int(row["rebuilds"]) if "rebuilds" in k else 0,
        }


class TaskStore:
    """Persistencia de tareas + registro de eventos (event sourcing real)."""

    def __init__(self, path: str | Path | None = None):
        self.path = str(path or db_path())
        self._init()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path, check_same_thread=False)
        c.row_factory = sqlite3.Row
        return c

    def _init(self) -> None:
        """
        El esquema ya no se crea aquí: lo llevan las migraciones.

        Antes esto era un `CREATE TABLE IF NOT EXISTS` gigante más un
        `_migrate()` que añadía dos columnas a mano. Funcionaba mientras el
        esquema no cambiara, pero `IF NOT EXISTS` no añade columnas a una tabla
        que ya existe: cualquier columna nueva simplemente no llegaba a las
        máquinas que ya habían abierto MAGI una vez. Ver `migraciones.py`.
        """
        from .migraciones import ejecutar
        with self._conn() as c:
            ejecutar(c)

    def estado_migraciones(self) -> dict:
        """Para la pestaña Configuración: si esta base está al día."""
        from .migraciones import informe
        with self._conn() as c:
            return informe(c)

    # ---------------------------------------------------------------- tareas

    def save(self, state: TaskState) -> None:
        state.updated_at = time.time()
        with self._conn() as c:
            c.execute("""
                INSERT INTO task_state (task_id, command, status, round_num, engine,
                    narrative_style, route, max_rounds, use_tools,
                    last_proposal, last_critique, created_at, updated_at,
                    titulo, archivada, borrada, sin_leer_en, bifurcada_de,
                    motivo_cierre, calls_used, rebuilds)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(task_id) DO UPDATE SET
                    command=excluded.command, status=excluded.status,
                    round_num=excluded.round_num, engine=excluded.engine,
                    narrative_style=excluded.narrative_style, route=excluded.route,
                    max_rounds=excluded.max_rounds, use_tools=excluded.use_tools,
                    last_proposal=excluded.last_proposal,
                    last_critique=excluded.last_critique,
                    updated_at=excluded.updated_at,
                    titulo=excluded.titulo, archivada=excluded.archivada,
                    borrada=excluded.borrada, sin_leer_en=excluded.sin_leer_en,
                    bifurcada_de=excluded.bifurcada_de,
                    motivo_cierre=excluded.motivo_cierre,
                    calls_used=excluded.calls_used, rebuilds=excluded.rebuilds
            """, (
                state.task_id, state.command, state.status, state.round,
                state.engine, state.narrative_style, state.route,
                state.max_rounds, int(state.use_tools),
                json.dumps(state.last_proposal, ensure_ascii=False) if state.last_proposal else None,
                json.dumps(state.last_critique, ensure_ascii=False) if state.last_critique else None,
                state.created_at, state.updated_at,
                state.titulo, int(state.archivada), int(state.borrada),
                state.sin_leer_en, state.bifurcada_de, state.motivo_cierre,
                int(state.calls_used), int(state.rebuilds),
            ))

    def load(self, task_id: str) -> TaskState | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM task_state WHERE task_id=?",
                            (task_id,)).fetchone()
        return TaskState.from_row(row) if row else None

    def resumable(self) -> list[TaskState]:
        """
        Lo que el kernel rehidrata al arrancar.

        Excluye archivadas y borradas. Antes no lo hacía —no existían esas
        columnas— así que devolvía TODO lo que alguna vez estuvo abierto: en
        esta máquina, 7 tareas desde el 7 de agosto, 4 de ellas "en curso".
        """
        q = ",".join("?" * len(RESUMABLE))
        with self._conn() as c:
            rows = c.execute(
                f"SELECT * FROM task_state WHERE status IN ({q}) "
                f"AND archivada=0 AND borrada=0 "
                f"ORDER BY updated_at DESC", RESUMABLE).fetchall()
        return [TaskState.from_row(r) for r in rows]

    def recent(self, limit: int = 20) -> list[TaskState]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM task_state ORDER BY updated_at DESC "
                             "LIMIT ?", (limit,)).fetchall()
        return [TaskState.from_row(r) for r in rows]

    def visibles(self, limit: int = 100) -> list[TaskState]:
        """
        Tareas para la columna izquierda de la GUI: ni archivadas ni borradas.

        `recent` devuelve todo (incluido lo archivado, útil para auditoría);
        la lista de conversaciones que ve el usuario solo debe mostrar lo
        activo. Si las columnas de la migración 0003 no existen, cae a
        `recent` sin filtrar — la base sigue siendo legible.
        """
        try:
            with self._conn() as c:
                k = c.execute("PRAGMA table_info(task_state)").fetchall()
                if not any(r[1] == "borrada" for r in k):
                    return self.recent(limit)
                rows = c.execute(
                    "SELECT * FROM task_state WHERE borrada=0 "
                    "ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
            return [TaskState.from_row(r) for r in rows]
        except Exception:
            return self.recent(limit)

    def renombrar(self, task_id: str, titulo: str) -> None:
        """
        Fija el título con el que la tarea se muestra en la lista.

        El título lo genera una IA a partir del comando del usuario (5-8
        palabras), para que la columna izquierda diga «Juego Tetris portable»
        en vez de `task_a3f9c2b1`. `TaskState.nombre()` ya lo devuelve si está.
        """
        with self._conn() as c:
            k = c.execute("PRAGMA table_info(task_state)").fetchall()
            if any(r[1] == "titulo" for r in k):
                c.execute(
                    "UPDATE task_state SET titulo=?, updated_at=? WHERE task_id=?",
                    (titulo[:80], time.time(), task_id))

    def reconciliar(self) -> list[str]:
        """
        FASE 0. Toda tarea `in_progress` al arrancar estaba corriendo cuando el
        proceso murió: pasa a `interrumpida`.

        Se llama ANTES de rehidratar, cuando todavía no hay ningún bucle vivo,
        así que no hace falta preguntar cuáles corren — la respuesta es
        ninguna. Para el caso general (reconciliar con el proceso ya en
        marcha) está `reconciliar_vivas()`.

        POR QUÉ ESTO DESBLOQUEA LA APLICACIÓN
        =====================================
        `_rehydrate()` devolvía esas tareas a `active_tasks` como `in_progress`
        sin volver a lanzar su bucle: zombis. Y `submit_task` tenía

            elif state["status"] == "in_progress":
                return   # sin evento, sin fila, sin motivo

        Encadenado: la fila `default` de esta máquina llevaba `in_progress`
        desde el 8 de agosto a las 22:38, así que TODO lo que el usuario
        escribiera —que siempre va con id `default`— chocaba contra ella y se
        descartaba en silencio. En cada arranque, para siempre, porque la fila
        nunca cambiaba.

        Devuelve los ids reconciliados.
        """
        with self._conn() as c:
            ids = [r["task_id"] for r in c.execute(
                "SELECT task_id FROM task_state "
                "WHERE status=? AND archivada=0 AND borrada=0", (EN_CURSO,))]
            if ids:
                c.execute(
                    "UPDATE task_state SET status=?, motivo_cierre=?, "
                    "updated_at=? WHERE status=? AND archivada=0 AND borrada=0",
                    (INTERRUMPIDA,
                     "el proceso se cerró mientras estaba en curso",
                     time.time(), EN_CURSO))
        if ids:
            logger.warning(
                "[store] %d tarea(s) quedaron a medias y pasan a interrumpida: "
                "%s. Son reanudables; NO estaban corriendo.",
                len(ids), ", ".join(ids))
        return ids

    def reconciliar_vivas(self, esta_viva) -> list[str]:
        """
        Igual, pero preguntando por cada tarea si su bucle sigue vivo.

        `esta_viva` es normalmente `supervisor().is_running`, que ya existía en
        `core/cancel.py:163` y era la ÚNICA fuente que sabía de verdad si algo
        se estaba ejecutando. Nadie la consultaba salvo el botón de parada.
        """
        rec: list[str] = []
        with self._conn() as c:
            ids = [r["task_id"] for r in c.execute(
                "SELECT task_id FROM task_state "
                "WHERE status=? AND archivada=0 AND borrada=0", (EN_CURSO,))]
            for tid in ids:
                try:
                    if esta_viva(tid):
                        continue
                except Exception:
                    pass
                c.execute("UPDATE task_state SET status=?, motivo_cierre=?, "
                          "updated_at=? WHERE task_id=?",
                          (INTERRUMPIDA, "sin bucle de ejecución vivo",
                           time.time(), tid))
                rec.append(tid)
        if rec:
            logger.warning("[store] zombis reconciliados: %s", ", ".join(rec))
        return rec

    def archivar(self, task_id: str, motivo: str = "") -> None:
        """
        Sale de la vista sin perderse. Es lo que faltaba para que las tareas
        cerradas no se acumularan indefinidamente.
        """
        with self._conn() as c:
            c.execute("UPDATE task_state SET archivada=1, motivo_cierre=?, "
                      "updated_at=? WHERE task_id=?",
                      (motivo or None, time.time(), task_id))

    def bifurcar(self, origen: str, nuevo_id: str, command: str,
                 titulo: str = "") -> TaskState | None:
        """
        Nueva tarea que HEREDA el contexto de otra sin contaminarla.

        Es la respuesta correcta a escribir algo nuevo mientras otra tarea
        espera aprobación. Hasta ahora había que elegir entre absorberlo —y
        perder la pregunta, que es lo que pasó con «dime por que la soledad
        duele»— o abrir una tarea suelta que no sabe nada de lo anterior.
        """
        base = self.load(origen)
        if base is None:
            return None
        hija = TaskState(
            task_id=nuevo_id, command=command, status=EN_CURSO, round=1,
            engine=base.engine, narrative_style=base.narrative_style,
            route=base.route, max_rounds=base.max_rounds,
            use_tools=base.use_tools,
            last_proposal=base.last_proposal, last_critique=base.last_critique,
            titulo=titulo, bifurcada_de=origen)
        self.save(hija)
        logger.info("[store] %s bifurcada de %s", nuevo_id, origen)
        return hija

    def delete(self, task_id: str) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM task_state WHERE task_id=?", (task_id,))
            c.execute("DELETE FROM task_event WHERE task_id=?", (task_id,))

    #: Lo que crean los arneses de medida, no el usuario. `auditar_sistema.py`
    #: abre una tarea `auditoria-<epoch>` por pasada; el banco de evaluación,
    #: una `eval-<epoch>`. Ver `purgar_sinteticas`.
    PREFIJOS_SINTETICOS = ("auditoria", "eval-", "t-techo", "bench-")

    def purgar_sinteticas(self, prefijos: tuple[str, ...] | None = None) -> list[str]:
        """
        Borra las tareas que creó una herramienta de medida, no una persona.

        POR QUÉ HACE FALTA
        ==================
        Estado real de la base el 2026-08-20, tras una tarde de auditorías:

            total: 23   WAITING_USER_APPROVAL: 14   interrumpida: 7

        De esas 23, **trece** eran `auditoria-<epoch>`: una por cada pasada de
        `scripts/auditar_sistema.py`. El arnés abre la tarea, mide, y se va sin
        recogerla. Cada una queda esperando una aprobación que nadie va a dar,
        el kernel la rehidrata en cada arranque y la interfaz la lista como una
        conversación pendiente del usuario. La herramienta que existe para
        diagnosticar el sistema estaba ensuciando lo que mide.

        Se borra en vez de archivar a propósito: archivar la deja fuera de la
        vista pero dentro de la tabla, y estas filas no tienen ningún valor
        histórico — la medición vive en `artifacts/auditoria.json`, que es
        donde debe vivir.

        Nunca toca una tarea con `bifurcada_de`: si alguien ramificó trabajo
        real desde una auditoría, ese trabajo es del usuario.
        """
        prefijos = prefijos or self.PREFIJOS_SINTETICOS
        with self._conn() as c:
            filas = c.execute(
                "SELECT task_id FROM task_state WHERE bifurcada_de IS NULL"
            ).fetchall()
        ids = [r[0] for r in filas
               if any(str(r[0]).startswith(p) for p in prefijos)]
        for tid in ids:
            self.delete(tid)
        if ids:
            logger.info("[store] purgadas %d tarea(s) de instrumentación: %s",
                        len(ids), ", ".join(ids))
        return ids

    # --------------------------------------------------------------- eventos

    def append_event(self, task_id: str, topic: str, payload: Any = None) -> None:
        with self._conn() as c:
            c.execute("INSERT INTO task_event (task_id, topic, payload, ts) "
                      "VALUES (?,?,?,?)",
                      (task_id, topic,
                       json.dumps(payload, ensure_ascii=False, default=str)
                       if payload is not None else None,
                       time.time()))

    def events(self, task_id: str, limit: int = 500) -> list[dict]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM task_event WHERE task_id=? "
                             "ORDER BY seq LIMIT ?", (task_id, limit)).fetchall()
        return [{"seq": r["seq"], "topic": r["topic"], "ts": r["ts"],
                 "payload": json.loads(r["payload"]) if r["payload"] else None}
                for r in rows]

    # ---------------------------------------------------------------- tokens

    def record_usage(self, *, task_id: str, agent: str, provider: str,
                     family: str, tokens_in: int = 0, tokens_out: int = 0,
                     latency_ms: float = 0.0) -> None:
        """Contabilidad de tokens: no existía en v5.0.28."""
        with self._conn() as c:
            c.execute("INSERT INTO token_ledger (task_id, agent, provider, family,"
                      " tokens_in, tokens_out, latency_ms, ts) VALUES (?,?,?,?,?,?,?,?)",
                      (task_id, agent, provider, family, tokens_in, tokens_out,
                       latency_ms, time.time()))

    def usage_for(self, task_id: str) -> dict[str, Any]:
        with self._conn() as c:
            row = c.execute(
                "SELECT COUNT(*) n, COALESCE(SUM(tokens_in),0) ti, "
                "COALESCE(SUM(tokens_out),0) to_, COALESCE(AVG(latency_ms),0) lat "
                "FROM token_ledger WHERE task_id=?", (task_id,)).fetchone()
            by_agent = c.execute(
                "SELECT agent, family, COALESCE(SUM(tokens_in+tokens_out),0) t "
                "FROM token_ledger WHERE task_id=? GROUP BY agent, family",
                (task_id,)).fetchall()
        return {
            "calls": row["n"], "tokens_in": row["ti"], "tokens_out": row["to_"],
            "total_tokens": row["ti"] + row["to_"],
            "avg_latency_ms": round(row["lat"], 1),
            "by_agent": [{"agent": r["agent"], "family": r["family"],
                          "tokens": r["t"]} for r in by_agent],
        }
