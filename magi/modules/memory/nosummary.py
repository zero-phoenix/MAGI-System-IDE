from magi.modules.memory.record import MemoryRecord

class NoSummary:
    """
    Prohibición de Resumen (P18.b).
    Valida que el contenido recuperado exista textualmente en el registro.
    """
    def __init__(self, record: MemoryRecord):
        self.record = record
        
    def assert_verbatim(self, fragment: str, source_id: str) -> bool:
        """
        Asegura que `fragment` sea una subcadena exacta del ítem original.
        Cero tolerancia a paráfrasis.
        """
        original = self.record.get_text(source_id)
        if fragment not in original:
            raise ValueError(f"SummaryDetected: Fragment '{fragment}' not found verbatim in original.")
        return True
