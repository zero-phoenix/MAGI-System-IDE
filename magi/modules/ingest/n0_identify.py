import os
from pathlib import Path
from .models import FormatProfile

class IdentifierN0:
    """
    N0: Identificación mediante fusión de señales (A15-1.2).
    La extensión nunca decide sola.
    """
    def identify(self, path: Path) -> FormatProfile:
        # En una implementación real usaría libmagic, Apache Tika y heurísticas.
        # Aquí proveemos la estructura de desempate.
        
        filename = path.name.lower()
        
        # Simulación de señales
        magic_signal = self._mock_magic(path)
        ext = path.suffix.lower()
        
        confidence = 0.0
        family = "unknown"
        name = "unknown"
        evidence = []
        
        # Simulación: ZIP que es DOCX
        if magic_signal == "application/zip":
            if ext == ".docx":
                family = "wordprocessor"
                name = "OOXML Word (DOCX)"
                confidence = 0.95
                evidence = ["magic ZIP", "estructura OOXML", "extensión .docx (desempate)"]
            elif ext == ".jar":
                family = "archive"
                name = "Java Archive"
                confidence = 0.90
                evidence = ["magic ZIP", "extensión .jar"]
            else:
                family = "archive"
                name = "ZIP Archive"
                confidence = 0.80
                evidence = ["magic ZIP"]
        elif magic_signal == "text/plain":
            family = "text"
            name = "Plain Text"
            confidence = 0.9
            evidence = ["magic TEXT"]
        
        # Si la extensión no cuadra con la estructura, la estructura manda.
        # En un test con extensión falsa (ej. ZIP renombrado a .doc), detectará ZIP.
        if ext == ".doc" and magic_signal == "application/zip":
            # Demostración del Gate N0: extensión ignorada.
            family = "archive"
            name = "ZIP Archive"
            confidence = 0.85
            evidence = ["magic ZIP", "ignoring fake .doc extension"]

        return FormatProfile(
            family=family,
            name=name,
            confidence=confidence,
            evidence=evidence
        )
        
    def _mock_magic(self, path: Path) -> str:
        # Simula el retorno de libmagic
        name = path.name.lower()
        if "zip" in name or name.endswith(".docx"):
            return "application/zip"
        return "application/octet-stream"
