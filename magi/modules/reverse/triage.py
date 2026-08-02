import math
from typing import Dict, Any

class BinaryTriage:
    """
    Triaje de binarios (P5.1).
    Calcula entropía de Shannon para detectar si un binario está cifrado/comprimido.
    """
    def __init__(self):
        pass
        
    def _calculate_entropy(self, data: bytes) -> float:
        if not data:
            return 0.0
        entropy = 0
        for x in range(256):
            p_x = float(data.count(x)) / len(data)
            if p_x > 0:
                entropy += - p_x * math.log2(p_x)
        return entropy

    def analyze(self, binary_data: bytes) -> Dict[str, Any]:
        """
        Calcula magic bytes y entropía.
        Si la entropía supera 7.5, se asume comprimido o cifrado.
        """
        ent = self._calculate_entropy(binary_data)
        
        # Extracción simple de Magic Bytes
        magic = binary_data[:4].hex() if len(binary_data) >= 4 else "unknown"
        
        return {
            "entropy": ent,
            "is_encrypted_or_compressed": ent > 7.5,
            "magic_bytes": magic
        }
