import sqlite3
import asyncio
import logging
import json
import uuid
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class MagiDatabase:
    """
    Motor de persistencia SQLite de MAGI.
    Maneja el almacenamiento inmutable de tareas y debates del enjambre.
    """
    def __init__(self, db_path: str = "magi_brain.db"):
        import os
        if db_path == "magi_brain.db":
            home_dir = os.path.expanduser("~")
            magi_dir = os.path.join(home_dir, ".magi")
            os.makedirs(magi_dir, exist_ok=True)
            self.db_path = os.path.join(magi_dir, "magi_brain.db")
        else:
            self.db_path = db_path
        self._init_db()        
    def _get_connection(self):
        # check_same_thread=False para poder operar asíncronamente con to_thread
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        """Crea el esquema de la base de datos si no existe."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Tabla de Misiones / Tareas
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id TEXT PRIMARY KEY,
                        command TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabla de Debates (Memoria de los Agentes)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS debates (
                        id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        round_num INTEGER NOT NULL,
                        agent_name TEXT NOT NULL,
                        role TEXT NOT NULL,
                        provider TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(task_id) REFERENCES tasks(id)
                    )
                """)
                
                # --- ÁREA 13: MAGI-MEM ---
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS mem_project (
                        project TEXT PRIMARY KEY,
                        last_indexed TIMESTAMP,
                        nodes INTEGER,
                        edges INTEGER,
                        languages TEXT
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS mem_query_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        duration_ms INTEGER NOT NULL,
                        rows INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS mem_knowledge (
                        knowledge_id TEXT PRIMARY KEY,
                        qualified_name TEXT NOT NULL,
                        statement TEXT NOT NULL,
                        evidence_refs TEXT NOT NULL,
                        evidence_tier_min INTEGER,
                        expires_when TEXT,
                        invalidated_by TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS mem_coverage (
                        project TEXT NOT NULL,
                        language TEXT NOT NULL,
                        files_indexed INTEGER NOT NULL,
                        PRIMARY KEY(project, language)
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS provider_telemetry (
                        provider TEXT PRIMARY KEY,
                        success_count INTEGER DEFAULT 0,
                        failure_count INTEGER DEFAULT 0,
                        avg_latency_ms REAL DEFAULT 0.0,
                        avg_word_count REAL DEFAULT 0.0,
                        code_density_ratio REAL DEFAULT 0.0,
                        specialization TEXT
                    )
                """)
                
                conn.commit()
                logger.info(f"[DB] Esquema de persistencia inicializado en {self.db_path}")
        except Exception as e:
            logger.error(f"[DB] Error inicializando base de datos: {e}")

    async def save_task(self, task_id: str, command: str, status: str = "STARTED"):
        """Guarda una tarea de forma asíncrona."""
        def _save():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tasks (id, command, status) VALUES (?, ?, ?)",
                    (task_id, command, status)
                )
                conn.commit()
        try:
            await asyncio.to_thread(_save)
        except Exception as e:
            logger.error(f"[DB] Error guardando tarea {task_id}: {e}")

    async def save_debate_entry(self, task_id: str, round_num: int, agent_name: str, role: str, provider: str, content: str):
        """Guarda una intervención de un agente de forma asíncrona."""
        entry_id = str(uuid.uuid4())
        def _save():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO debates 
                       (id, task_id, round_num, agent_name, role, provider, content) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (entry_id, task_id, round_num, agent_name, role, provider, content)
                )
                conn.commit()
        try:
            await asyncio.to_thread(_save)
        except Exception as e:
            logger.error(f"[DB] Error guardando debate de {agent_name}: {e}")

    async def save_knowledge_delta(self, knowledge_id: str, qualified_name: str, statement: str, evidence_refs: list, evidence_tier_min: int, expires_when: str):
        """Guarda un delta de conocimiento (MemGraph) de forma asíncrona."""
        evidence_json = json.dumps(evidence_refs)
        def _save():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO mem_knowledge 
                       (knowledge_id, qualified_name, statement, evidence_refs, evidence_tier_min, expires_when) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (knowledge_id, qualified_name, statement, evidence_json, evidence_tier_min, expires_when)
                )
                conn.commit()
        try:
            await asyncio.to_thread(_save)
        except Exception as e:
            logger.error(f"[DB] Error guardando knowledge delta para {qualified_name}: {e}")

    async def get_knowledge_for(self, qualified_name: str) -> List[Dict[str, Any]]:
        """Recupera los deltas de conocimiento vigentes para un nodo."""
        def _get():
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM mem_knowledge WHERE qualified_name = ? AND invalidated_by IS NULL",
                    (qualified_name,)
                )
                return [dict(row) for row in cursor.fetchall()]
        try:
            return await asyncio.to_thread(_get)
        except Exception as e:
            logger.error(f"[DB] Error leyendo knowledge para {qualified_name}: {e}")
            return []

    async def log_provider_success(self, provider: str, latency_ms: float, has_code: bool, word_count: int, role: str):
        """Actualiza las métricas de éxito y calcula la inteligencia empírica."""
        def _save():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM provider_telemetry WHERE provider = ?", (provider,))
                row = cursor.fetchone()
                if row:
                    s_count = row[1] + 1
                    # Calcular promedios iterativos
                    avg_lat = row[3] + (latency_ms - row[3]) / s_count
                    avg_wc = row[4] + (word_count - row[4]) / s_count
                    code_ratio = row[5] + ((1.0 if has_code else 0.0) - row[5]) / s_count
                    
                    cursor.execute("""
                        UPDATE provider_telemetry 
                        SET success_count = ?, avg_latency_ms = ?, avg_word_count = ?, code_density_ratio = ?, specialization = ? 
                        WHERE provider = ?
                    """, (s_count, avg_lat, avg_wc, code_ratio, role, provider))
                else:
                    cursor.execute("""
                        INSERT INTO provider_telemetry 
                        (provider, success_count, failure_count, avg_latency_ms, avg_word_count, code_density_ratio, specialization) 
                        VALUES (?, 1, 0, ?, ?, ?, ?)
                    """, (provider, latency_ms, word_count, 1.0 if has_code else 0.0, role))
                conn.commit()
        try:
            await asyncio.to_thread(_save)
        except Exception as e:
            logger.error(f"[DB] Error guardando éxito para {provider}: {e}")

    async def log_provider_failure(self, provider: str):
        """Registra un fallo en las métricas."""
        def _save():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM provider_telemetry WHERE provider = ?", (provider,))
                row = cursor.fetchone()
                if row:
                    cursor.execute("UPDATE provider_telemetry SET failure_count = failure_count + 1 WHERE provider = ?", (provider,))
                else:
                    cursor.execute("""
                        INSERT INTO provider_telemetry 
                        (provider, success_count, failure_count, avg_latency_ms, avg_word_count, code_density_ratio, specialization) 
                        VALUES (?, 0, 1, 0.0, 0.0, 0.0, 'None')
                    """, (provider,))
                conn.commit()
        try:
            await asyncio.to_thread(_save)
        except Exception as e:
            logger.error(f"[DB] Error guardando fallo para {provider}: {e}")

    async def get_telemetry(self) -> List[Dict[str, Any]]:
        """Devuelve todas las métricas de los proveedores para el Dashboard."""
        def _get():
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM provider_telemetry ORDER BY success_count DESC, avg_latency_ms ASC")
                return [dict(row) for row in cursor.fetchall()]
        try:
            return await asyncio.to_thread(_get)
        except Exception as e:
            logger.error(f"[DB] Error leyendo telemetría: {e}")
            return []

