class MemoryRecord:
    """
    Registro Íntegro (P18.a).
    Almacena los ítems de manera literal e inmutable (simulado).
    """
    def __init__(self):
        self.items = []
        
    def append(self, item_id: str, text: str) -> None:
        """
        Guarda el texto íntegramente. No hay operación de borrado o edición.
        """
        self.items.append({"id": item_id, "text": text})
        
    def get_text(self, item_id: str) -> str:
        for item in self.items:
            if item["id"] == item_id:
                return item["text"]
        return ""
