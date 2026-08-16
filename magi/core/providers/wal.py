import hashlib
import sqlite3
from typing import Any


class ResumableWAL:
    """
    Write-Ahead Log transaccional para unidades de trabajo largo.
    Garantiza idempotencia (UPSERT) y que el progreso sobreviva a fallos.
    """
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self._init_schema()

    def _init_schema(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS job_unit (
                    job_id TEXT,
                    unit_id TEXT,
                    state TEXT, -- PENDING, DONE, STALE
                    output_ref TEXT,
                    provider_id TEXT,
                    input_hash TEXT,
                    PRIMARY KEY(job_id, unit_id)
                )
            ''')

    def compute_unit_id(self, job_kind: str, input_normalized: str, index: int) -> str:
        """
        unit_id ESTABLE y determinista (A6-1).
        Nunca un contador temporal.
        """
        raw = f"{job_kind}:{input_normalized}:{index}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def open_work(self, job_id: str, units: list[dict[str, Any]]):
        """
        Guarda las unidades como PENDING al inicio.
        units = [{'unit_id': 'hash', 'input_hash': 'h2'}, ...]
        """
        with self.conn:
            for u in units:
                self.conn.execute('''
                    INSERT OR IGNORE INTO job_unit (job_id, unit_id, state, input_hash)
                    VALUES (?, ?, 'PENDING', ?)
                ''', (job_id, u['unit_id'], u.get('input_hash', '')))

    def commit_unit(self, job_id: str, unit_id: str, output_ref: str, provider_id: str):
        """
        UPSERT idempotente. Si reejecutas no duplicas efectos.
        """
        with self.conn:
            self.conn.execute('''
                UPDATE job_unit
                SET state = 'DONE', output_ref = ?, provider_id = ?
                WHERE job_id = ? AND unit_id = ?
            ''', (output_ref, provider_id, job_id, unit_id))

    def get_pending_units(self, job_id: str) -> list[str]:
        cur = self.conn.execute("SELECT unit_id FROM job_unit WHERE job_id = ? AND state != 'DONE'", (job_id,))
        return [r[0] for r in cur.fetchall()]

    def close(self):
        self.conn.close()
