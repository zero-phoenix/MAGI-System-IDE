import logging
import math
from typing import Any

logger = logging.getLogger(__name__)

class SemanticRAG:
    """
    Pilar 2: Base de Datos Vectorial (RAG Semántico Avanzado).
    Permite búsquedas por similitud semántica (Embeddings) en lugar de coincidencias exactas.
    Ideal para el Área 2 y Área 13 (Grafo de código desensamblado).
    """
    def __init__(self):
        # Mocks a SQLite-VSS o ChromaDB collection
        self._vector_store: list[dict[str, Any]] = []

    def _mock_embed(self, text: str) -> list[float]:
        """Simula la generación de un embedding (ej. a través de modelo local MTEB)."""
        text_lower = text.lower()
        # Mock determinista basado en presencia de subcadenas
        score1 = 1.0 if "desensamblad" in text_lower else 0.0
        score2 = 1.0 if "manzana" in text_lower else 0.0
        return [score1, score2]

    def _cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        """Calcula similitud del coseno."""
        dot = sum(a * b for a, b in zip(v1, v2, strict=True))
        norm_a = math.sqrt(sum(a * a for a in v1))
        norm_b = math.sqrt(sum(b * b for b in v2))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def add_document(self, doc_id: str, content: str, metadata: dict = None):
        """Añade un documento a la base de datos vectorial."""
        vector = self._mock_embed(content)
        self._vector_store.append({
            "id": doc_id,
            "vector": vector,
            "content": content,
            "metadata": metadata or {}
        })
        logger.debug(f"[RAG] Documento '{doc_id}' indexado semánticamente.")

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Busca el top-k de documentos más similares semánticamente."""
        query_vector = self._mock_embed(query)

        scored = []
        for doc in self._vector_store:
            sim = self._cosine_similarity(query_vector, doc["vector"])
            scored.append((sim, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]
