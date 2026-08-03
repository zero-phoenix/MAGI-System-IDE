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

RESUMABLE = ("in_progress", "WAITING_USER_APPROVAL")


@dataclass
class TaskState:
    task_id: str
    command: str
    status: str = "in_progress"
    round: int = 1
    engine: str = "fast"
    narrative_style: str = "tecnico"
    route: str = "task"
    last_proposal: dict | None = None
    last_critique: dict | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def resumable(self) -> bool:
        return self.status in RESUMABLE

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "TaskState":
        return cls(
            task_id=row["task_id"], command=row["command"], status=row["status"],
            round=row["round_num"], engine=row["engine"],
            narrative_style=row["narrative_style"], route=row["route"],
            last_proposal=json.loads(row["last_proposal"]) if row["last_proposal"] else None,
            last_critique=json.loads(row["last_critique"]) if row["last_critique"] else None,
            created_at=row["created_at"], updated_at=row["updated_at"],
        )


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
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS task_state (
                    task_id         TEXT PRIMARY KEY,
                    command         TEXT NOT NULL,
                    status          TEXT NOT NULL,
                    round_num       INTEGER NOT NULL DEFAULT 1,
                    engine          TEXT NOT NULL DEFAULT 'fast',
                    narrative_style TEXT NOT NULL DEFAULT 'tecnico',
                    route           TEXT NOT NULL DEFAULT 'task',
                    last_proposal   TEXT,
                    last_critique   TEXT,
                    created_at      REAL NOT NULL,
                    updated_at      REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_task_state_status
                    ON task_state(status, updated_at DESC);

                CREATE TABLE IF NOT EXISTS task_event (
                    seq      INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id  TEXT NOT NULL,
                    topic    TEXT NOT NULL,
                    payload  TEXT,
                    ts       REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_task_event_task
                    ON task_event(task_id, seq);

                CREATE TABLE IF NOT EXISTS token_ledger (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id    TEXT,
                    agent      TEXT,
                    provider   TEXT,
                    family     TEXT,
                    tokens_in  INTEGER DEFAULT 0,
                    tokens_out INTEGER DEFAULT 0,
                    latency_ms REAL DEFAULT 0,
                    ts         REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_token_ledger_task
                    ON token_ledger(task_id, ts);
            """)

    # ---------------------------------------------------------------- tareas

    def save(self, state: TaskState) -> None:
        state.updated_at = time.time()
        with self._conn() as c:
            c.execute("""
                INSERT INTO task_state (task_id, command, status, round_num, engine,
                    narrative_style, route, last_proposal, last_critique,
                    created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(task_id) DO UPDATE SET
                    command=excluded.command, status=excluded.status,
                    round_num=excluded.round_num, engine=excluded.engine,
                    narrative_style=excluded.narrative_style, route=excluded.route,
                    last_proposal=excluded.last_proposal,
                    last_critique=excluded.last_critique,
                    updated_at=excluded.updated_at
            """, (
                state.task_id, state.command, state.status, state.round,
                state.engine, state.narrative_style, state.route,
                json.dumps(state.last_proposal, ensure_ascii=False) if state.last_proposal else None,
                json.dumps(state.last_critique, ensure_ascii=False) if state.last_critique else None,
                state.created_at, state.updated_at,
            ))

    def load(self, task_id: str) -> TaskState | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM task_state WHERE task_id=?",
                            (task_id,)).fetchone()
        return TaskState.from_row(row) if row else None

    def resumable(self) -> list[TaskState]:
        """Lo que el kernel rehidrata al arrancar."""
        q = ",".join("?" * len(RESUMABLE))
        with self._conn() as c:
            rows = c.execute(
                f"SELECT * FROM task_state WHERE status IN ({q}) "
                f"ORDER BY updated_at DESC", RESUMABLE).fetchall()
        return [TaskState.from_row(r) for r in rows]

    def recent(self, limit: int = 20) -> list[TaskState]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM task_state ORDER BY updated_at DESC "
                             "LIMIT ?", (limit,)).fetchall()
        return [TaskState.from_row(r) for r in rows]

    def delete(self, task_id: str) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM task_state WHERE task_id=?", (task_id,))
            c.execute("DELETE FROM task_event WHERE task_id=?", (task_id,))

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
