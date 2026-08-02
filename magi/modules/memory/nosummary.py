import logging
import unicodedata
from magi.modules.memory.record import MemoryRecord

logger = logging.getLogger(__name__)

class NoSummary:
    """
    Prohibición de Resumen (P18.b).
    Valida mecánicamente que todo contexto recuperado sea idéntico al original.
    """
    def __init__(self, record: MemoryRecord):
        self.record = record
        
    def _normalize(self, text: str) -> str:
        # P18.4: Normalización NFKC, minúsculas, colapso de espacios
        text = unicodedata.normalize("NFKC", text).lower()
        return " ".join(text.split())

    def assert_verbatim(self, fragment: str, source_id: str) -> bool:
        """
        Asegura que `fragment` sea una subcadena exacta (post-normalización) del ítem original.
        Cero tolerancia a paráfrasis.
        """
        original = self.record.get_text(source_id)
        if not original:
            raise ValueError(f"SummaryDetected: source_id '{source_id}' no encontrado.")
            
        norm_frag = self._normalize(fragment)
        norm_orig = self._normalize(original)
        
        if norm_frag not in norm_orig:
            logger.critical(f"SummaryDetected: El nodo intentó inyectar un resumen. Fragmento: '{fragment}'")
            raise ValueError("SummaryDetected: Tolerancia 0. El fragmento no existe literalmente.")
            
        return True
