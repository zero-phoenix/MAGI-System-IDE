from .models import EncodingGuess

class EncodingDetector:
    """
    A15-2: Detección de codificación con heurísticas de época.
    """
    def detect(self, data: bytes) -> EncodingGuess:
        # Heurísticas de época simuladas
        if b'\xb0' in data and b'\xdf' in data: # Dibujo de caja (marco)
            return EncodingGuess(
                detected="CP437",
                confidence=0.85,
                method="densidad dibujo de caja MS-DOS",
                line_endings="CRLF"
            )
        elif b'\x40' in data and b'\x20' not in data:
            return EncodingGuess(
                detected="EBCDIC",
                confidence=0.90,
                method="ausencia 0x20 + presencia 0x40",
                line_endings="LF"
            )
            
        return EncodingGuess(
            detected="UTF-8",
            confidence=0.99,
            method="uchardet fallback",
            line_endings="LF"
        )
