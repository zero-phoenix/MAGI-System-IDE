import time


class KnowledgeStore:
    """
    Capa Epistemológica de MAGI-MEM (P13.b).
    Base de datos de deltas de conocimiento (KnowledgeDelta) anclados a identificadores del código.
    """
    def __init__(self):
        self.store = {}

    def record_knowledge(self, qualified_name: str, delta_statement: str) -> str:
        """
        Registra una deducción firme sobre una función o clase.
        """
        if qualified_name not in self.store:
            self.store[qualified_name] = []

        record = {
            "knowledge_id": f"kn_{int(time.time()*1000)}",
            "qualified_name": qualified_name,
            "statement": delta_statement,
            "established_by": "MELCHIOR"
        }
        self.store[qualified_name].append(record)
        return record["knowledge_id"]

    def knowledge_for(self, qualified_name: str) -> list:
        """
        Recupera los deltas de conocimiento asociados a un nodo de código.
        """
        return self.store.get(qualified_name, [])
