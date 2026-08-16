import re
from dataclasses import dataclass


@dataclass
class Capability:
    id: str
    name: str
    content: str
    areas: list[str]

class CapabilitySelector:
    """
    Motor de selección de capacidades (Área 12).
    Selecciona máximo 4 bloques con base en relevancia para evitar desbordar el contexto.
    """
    def __init__(self, capabilities: list[Capability]):
        self.capabilities = capabilities
        self.history_success: dict[str, dict[str, float]] = {} # cap_id -> {task_kind: freq}

    def _compute_semantic_sim(self, text1: str, text2: str) -> float:
        """
        MVP: Similitud semántica básica usando solapamiento de tokens Jaccard.
        Para el producto final, esto usa nomic-embed-text (Área 13).
        """
        def tokenize(t):
            return set(re.findall(r'\b\w+\b', t.lower()))

        t1 = tokenize(text1)
        t2 = tokenize(text2)
        if not t1 or not t2:
            return 0.0
        intersection = len(t1.intersection(t2))
        union = len(t1.union(t2))
        return intersection / union if union > 0 else 0.0

    def select(self, task_area: str, task_topic: str, task_kind: str, max_blocks: int = 4) -> list[Capability]:
        """
        Calcula la relevancia:
        0.5 * area_match + 0.3 * semantic_sim + 0.2 * success_freq
        """
        scored = []
        for cap in self.capabilities:
            area_match = 1.0 if task_area in cap.areas else 0.0
            sem_sim = self._compute_semantic_sim(cap.name + "\n" + cap.content, task_topic)
            succ_freq = self.history_success.get(cap.id, {}).get(task_kind, 0.0)

            relevance = (0.5 * area_match) + (0.3 * sem_sim) + (0.2 * succ_freq)
            scored.append((relevance, cap))

        # Ordenar por relevancia descendente
        scored.sort(key=lambda x: x[0], reverse=True)

        # Seleccionar top N y deduplicar por similitud (umbral > 0.8)
        selected = []
        for rel, cap in scored:
            if rel <= 0.01: # Ignorar capacidades irrelevantes
                continue

            # Evitar duplicados (ej: 2 capacidades de matemáticas muy similares)
            is_dup = False
            for s in selected:
                if self._compute_semantic_sim(cap.content, s.content) > 0.8:
                    is_dup = True
                    break

            if not is_dup:
                selected.append(cap)

            if len(selected) >= max_blocks:
                break

        return selected
