from magi.modules.memory.record import MemoryRecord

class Composer:
    """
    Compositor de Contexto (P18.c).
    Prepara la ventana de contexto. Si se excede, direcciona pero NO resume.
    """
    def __init__(self, record: MemoryRecord):
        self.record = record
        
    def compose(self, budget_tokens: int, items_to_include: list) -> dict:
        """
        Simula el ensamblado. Si el presupuesto es muy bajo, omite el cuerpo
        y deja sólo referencias explícitas (truncado indexado).
        """
        total_len = sum(len(self.record.get_text(i)) for i in items_to_include)
        # Asumiendo 1 token = 4 chars
        if (total_len / 4) > budget_tokens:
            return {
                "context": f"Hay elementos no cargados: {items_to_include}. Recupéralos con memory.fetch antes de pronunciarte sobre ellos."
            }
            
        # Cabe bien
        full_text = " ".join([self.record.get_text(i) for i in items_to_include])
        return {"context": full_text}
