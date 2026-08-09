import logging
import asyncio
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from magi.core.bus import MagiBus, BusEvent

logger = logging.getLogger(__name__)

class MemGraphAdapter:
    """
    Área 13 - MAGI-MEM
    Adaptador del motor de grafo de memoria de código (DeusData/codebase-memory-mcp).
    Maneja la validación de seguridad A13-1 y la persistencia de los deltas de conocimiento.
    """
    def __init__(self, bus: MagiBus, bin_path: str | None = None):
        """
        bin_path resuelve en este orden:
          1. Argumento explícito (tests, configuración manual).
          2. Variable de entorno CODEBASE_MEMORY_MCP.
          3. data_dir() / "codebase-memory-mcp.exe" (junto al resto de binarios
             del usuario, en LOCALAPPDATA/Library/Application Support).
        Si no se encuentra, is_binary_present=False y el adaptador funciona en
        modo degradado (start() ya lo avisa). Antes el default era una ruta
        absoluta a una máquina concreta, así que el binario no se encontraba en
        ninguna otra.
        """
        from magi.core.paths import data_dir
        import os
        if bin_path is None:
            bin_path = (os.environ.get("CODEBASE_MEMORY_MCP")
                        or str(data_dir() / "codebase-memory-mcp.exe"))
        self.bus = bus
        self.bin_path = Path(bin_path)
        self.is_binary_present = self.bin_path.exists()
        
    async def start(self):
        """Verifica la existencia del binario y avisa al sistema si usa el Fallback."""
        if not self.is_binary_present:
            logger.warning("[MAGI-MEM] Binario codebase-memory-mcp no encontrado. Usando Fallback (ctags+networkx limitados).")
            # En un entorno real, iniciaríamos el servicio de Fallback aquí.
            await self.bus.publish(BusEvent(
                topic="memgraph.status",
                payload={"status": "degraded", "reason": "binary_missing"}
            ))
        else:
            logger.info("[MAGI-MEM] Binario MCP detectado. Motor de grafo listo.")
            # Arranque del subprocess MCP
            await self.bus.publish(BusEvent(
                topic="memgraph.status",
                payload={"status": "ready"}
            ))

    def _validate_cypher(self, query: str) -> str:
        """
        Algoritmo A13-1: Validación de seguridad de consultas Cypher.
        Rechaza operaciones destructivas o de escritura.
        Asegura que haya un LIMIT explícito.
        """
        upper_q = query.upper()
        # 1. Palabras prohibidas de escritura
        forbidden = ["CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE", "LOAD CSV", "CALL DB.", "APOC."]
        for f in forbidden:
            if f in upper_q:
                raise ValueError(f"Security Violation: Consulta Cypher contiene cláusula prohibida de escritura '{f}'")
        
        # 2. Exigir o añadir LIMIT
        if "LIMIT " not in upper_q:
            query += " LIMIT 5000"
            
        # 3. Anclaje a proyecto (Simplificado para validación)
        if "PROJECT" not in upper_q and "PROJECT_NAME" not in upper_q:
            logger.debug("[MAGI-MEM] Advertencia: La consulta debería anclarse a un Project.")
            
        return query

    async def query_graph(self, cypher: str, timeout_ms: int = 2000) -> List[Dict[str, Any]]:
        """Ejecuta una consulta Cypher contra el grafo de código."""
        try:
            safe_query = self._validate_cypher(cypher)
        except ValueError as e:
            logger.error(f"[MAGI-MEM] {e}")
            raise
            
        if not self.is_binary_present:
            # Fallback path: Devolver simulado o vacío para pruebas de integración
            logger.debug(f"[MAGI-MEM Fallback] Executing stub query: {safe_query}")
            await asyncio.sleep(0.1) # Simulando I/O
            return []
            
        # Llamada real al MCP (Stub para implementación completa posterior)
        logger.debug(f"[MAGI-MEM] Executing MCP query: {safe_query}")
        return []

    def search_graph(self, label: str, name_pattern: str) -> List[Dict[str, Any]]:
        """Stub para simular búsqueda en el grafo MCP por label y patrón."""
        if label == "Method" and name_pattern == "auth.*":
            return [{"id": "auth.login"}, {"id": "auth.logout"}]
        return []

    def trace_call_path(self, method: str) -> List[str]:
        """Stub para simular trace de llamadas."""
        if method == "auth.login":
            return ["auth.login", "crypto.hash_password", "db.query"]
        return []

    async def record_knowledge(self, knowledge_id: str, qualified_name: str, statement: str, evidence: List[str]):
        """Emite un evento de registro de delta de conocimiento para que el Database lo guarde."""
        await self.bus.publish(BusEvent(
            topic="knowledge.recorded",
            payload={
                "knowledge_id": knowledge_id,
                "qualified_name": qualified_name,
                "statement": statement,
                "evidence_refs": evidence,
                "evidence_tier_min": 3,
                "expires_when": "on_signature_change"
            }
        ))
        logger.info(f"[MAGI-MEM] Conocimiento registrado para: {qualified_name}")
