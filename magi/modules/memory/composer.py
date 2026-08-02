import logging
from magi.modules.memory.record import MemoryRecord
from magi.modules.memory.nosummary import NoSummary

logger = logging.getLogger(__name__)

class Composer:
    """
    Compositor de Contexto (P18.c).
    Prepara la ventana de contexto. Si excede, direcciona mediante índice completo literal, pero NO resume.
    """
    def __init__(self, record: MemoryRecord):
        self.record = record
        self.validator = NoSummary(record)
        
    def compose(self, budget_tokens: int, items_to_include: list) -> dict:
        """
        Ensambla el contexto.
        A18-2: Si no cabe, compone un índice (Bloque 2) con 160 chars literales e instrucción de fetch.
        """
        # Calcular tokens de todos los ítems completos (aprox. 4 chars por token)
        total_chars = sum(len(self.record.get_text(i)) for i in items_to_include)
        
        if (total_chars / 4) > budget_tokens:
            logger.info(f"memory.overflow: El registro excede {budget_tokens} tokens. Activando modo direccionado.")
            # Montar bloque 2 (Índice Literal)
            index_lines = []
            for i in items_to_include:
                full_text = self.record.get_text(i)
                # Validar que no perdemos texto original
                self.validator.assert_verbatim(full_text, i)
                
                # Extraemos hasta 160 chars LITERAMENTE
                snippet = full_text[:160] + "..." if len(full_text) > 160 else full_text
                index_lines.append(f"[{i}]: {snippet}")
            
            warning_msg = f"Hay {len(items_to_include)} elementos relacionados con este turno que no están cargados íntegramente. Recupéralos con memory.fetch antes de pronunciarte sobre ellos."
            
            context_body = "\n".join(index_lines) + "\n\n" + warning_msg
            return {"context": context_body, "mode": "directed"}
            
        # Si cabe completo: Bloque 3 (Cuerpo literal)
        full_blocks = []
        for i in items_to_include:
            text = self.record.get_text(i)
            self.validator.assert_verbatim(text, i)
            full_blocks.append(f"[{i}]:\n{text}")
            
        return {"context": "\n\n".join(full_blocks), "mode": "full"}
