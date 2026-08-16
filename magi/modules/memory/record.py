import hashlib
import logging
import unicodedata
from typing import Any

logger = logging.getLogger(__name__)

class MemoryRecord:
    """
    Registro Íntegro (P18.a).
    Almacena los ítems de manera literal e inmutable con hash en cadena.
    """
    def __init__(self, record_id: str):
        self.record_id = record_id
        self._items: list[dict[str, Any]] = []
        self._chain_head = "0" * 64  # Hash semilla

    def _canonical(self, text: str) -> str:
        # Normalización NFKC (Area 18 - 18.4)
        return unicodedata.normalize("NFKC", text)

    def append(self, item_id: str, kind: str, text: str) -> str:
        """
        Guarda el texto íntegramente. Calcula sha256(prev_hash || canonical(item)).
        No hay operación de borrado o edición.
        """
        canonical_text = self._canonical(text)
        payload = f"{self._chain_head}||{item_id}||{kind}||{canonical_text}"
        new_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()

        item = {
            "id": item_id,
            "kind": kind,
            "text": text,  # Texto inalterado
            "canonical": canonical_text,
            "prev_hash": self._chain_head,
            "hash": new_hash
        }

        self._items.append(item)
        self._chain_head = new_hash
        return new_hash

    def get_text(self, item_id: str) -> str:
        """Devuelve el texto literal, usado por composer y nosummary."""
        for item in self._items:
            if item["id"] == item_id:
                return item["text"]
        return ""

    def get_items(self) -> list[dict[str, Any]]:
        # Devuelve copia para no mutar accidentalmente
        return list(self._items)

    def get_chain_head(self) -> str:
        return self._chain_head

    def verify_chain(self) -> bool:
        """
        P18.a.1 Recorre el registro recalculando la cadena para detectar corrupción (A18-3).
        """
        current_head = "0" * 64
        for item in self._items:
            if item["prev_hash"] != current_head:
                logger.critical(f"memory.chain_broken: prev_hash discrepante en {item['id']}")
                return False

            # Verificar que el texto no ha sido alterado (re-canonicar)
            if item["canonical"] != self._canonical(item["text"]):
                logger.critical(f"memory.chain_broken: Texto literal alterado en {item['id']}")
                return False

            payload = f"{current_head}||{item['id']}||{item['kind']}||{item['canonical']}"
            expected_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()

            if item["hash"] != expected_hash:
                logger.critical(f"memory.chain_broken: Corrupción de datos detectada en {item['id']}")
                return False

            current_head = expected_hash

        return True
