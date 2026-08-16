

class CitationValidator:
    """
    Validador de Citas (P2.c).
    Filtra alucinaciones del LLM exigiendo anclajes reales.
    """
    def __init__(self, corpus_index):
        # Mantenemos una lista de locators válidos en memoria para validación
        self.valid_locators = {doc["locator"] for doc in corpus_index.documents}

    def validate(self, citations: list[dict[str, str]]) -> list[dict[str, str]]:
        """
        Descarta citas donde el 'locator' (referencia) no existe en el corpus real.
        """
        valid_citations = []
        for cite in citations:
            loc = cite.get("locator")
            if loc in self.valid_locators:
                valid_citations.append(cite)
        return valid_citations
