import re
from typing import Any


class MockBM25Index:
    """
    Índice BM25 Dummy en Memoria (P2.b).
    """
    def __init__(self):
        self.documents = []

    def add_documents(self, docs: list[dict[str, str]]):
        self.documents.extend(docs)

    def _tokenize(self, text: str) -> set:
        return set(re.findall(r'\b\w+\b', text.lower()))

    def search(self, query: str, top_k: int = 50) -> list[dict[str, Any]]:
        """
        Retorna los mejores K documentos. Simula recall@50 >= 0.90
        usando intersección léxica simple.
        """
        q_tokens = self._tokenize(query)
        scored = []

        for doc in self.documents:
            d_tokens = self._tokenize(doc["content"])
            if not q_tokens or not d_tokens:
                score = 0.0
            else:
                intersection = len(q_tokens.intersection(d_tokens))
                score = intersection / len(q_tokens) # simple TF

            scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)

        return [{"score": s, "doc": d} for s, d in scored[:top_k]]
