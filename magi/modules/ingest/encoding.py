import chardet

from .models import EncodingGuess


class EncodingDetector:
    """
    A15-2: Detección de codificación con heurísticas de época + chardet.
    """
    def detect(self, data: bytes) -> EncodingGuess:
        if not data:
            return EncodingGuess(detected="UTF-8", confidence=1.0, method="empty", line_endings="LF")

        # 1. BOM Check
        if data.startswith(b'\xef\xbb\xbf'):
            return EncodingGuess(detected="UTF-8-SIG", confidence=1.0, method="BOM", line_endings=self._guess_lines(data))
        if data.startswith(b'\xff\xfe') or data.startswith(b'\xfe\xff'):
            return EncodingGuess(detected="UTF-16", confidence=1.0, method="BOM", line_endings=self._guess_lines(data))

        # 2. Heurísticas propias de época (A15-2.3)
        # 3.1 CP437/CP850: densidad de caracteres de dibujo de caja de DOS
        box_drawing = sum(1 for b in data if b in (0xB0, 0xB1, 0xB2, 0xDF, 0xDC, 0xDD, 0xDE))
        if len(data) > 0 and box_drawing / len(data) > 0.05:
            return EncodingGuess(
                detected="CP437",
                confidence=0.85,
                method="densidad dibujo de caja MS-DOS",
                line_endings=self._guess_lines(data)
            )

        # 3.2 EBCDIC: Ausencia total de 0x20 como espacio y presencia de 0x40 (espacio en EBCDIC)
        if b'\x40' in data and b'\x20' not in data:
            return EncodingGuess(
                detected="EBCDIC",
                confidence=0.90,
                method="ausencia 0x20 + presencia 0x40",
                line_endings=self._guess_lines(data)
            )

        # 3.3 Mac Roman: Acentos comunes en español en distribución Mac (e.g., 0x8E=é, 0x8F=è, 0xA5=•)
        # 3.4 Fin de línea CR refuerza Mac Roman
        mac_accents = sum(1 for b in data if b in (0x8E, 0x8F, 0xA5, 0xCC, 0xCD))
        line_ends = self._guess_lines(data)
        if line_ends == "CR" and mac_accents > 2:
            return EncodingGuess(
                detected="MacRoman",
                confidence=0.80,
                method="acentos Mac + fin de línea CR",
                line_endings="CR"
            )

        # 3. Chardet estadístico general
        res = chardet.detect(data)
        encoding = res['encoding'] or "UTF-8"
        confidence = res['confidence'] or 0.0

        return EncodingGuess(
            detected=encoding,
            confidence=confidence,
            method="chardet estadístico",
            line_endings=line_ends
        )

    def _guess_lines(self, data: bytes) -> str:
        has_cr = b'\r' in data
        has_lf = b'\n' in data
        if has_cr and has_lf:
            if b'\r\n' in data:
                return "CRLF"
            return "Mixed"
        if has_cr:
            return "CR"
        return "LF"
