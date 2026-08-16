import tarfile
import zipfile
from pathlib import Path

import magic

from .models import FormatProfile


class IdentifierN0:
    """
    N0: Identificación mediante libmagic (python-magic) y validación estructural.
    La extensión nunca decide sola, solo desempata o apoya.
    """
    def identify(self, path: Path) -> FormatProfile:
        if not path.exists():
            return FormatProfile(family="unknown", name="Not Found", confidence=0.0, evidence=["File not found"])

        ext = path.suffix.lower()
        evidence = []

        # 1. libmagic para inspección profunda (magic bytes)
        try:
            mime_type = magic.from_file(str(path), mime=True)
            magic_desc = magic.from_file(str(path))
            evidence.append(f"libmagic: {mime_type}")
        except Exception as e:
            mime_type = "application/octet-stream"
            magic_desc = "unknown"
            evidence.append(f"libmagic falló: {e}")

        family = "unknown"
        name = "Unknown Format"
        confidence = 0.0

        # 2. Análisis estructural para contenedores
        is_zip = zipfile.is_zipfile(str(path))
        is_tar = tarfile.is_tarfile(str(path))

        if is_zip or is_tar or mime_type in ["application/zip", "application/x-tar", "application/gzip"]:
            family = "archive"
            name = "ZIP/TAR Archive"
            confidence = 0.85
            if is_zip:
                evidence.append("Estructura comprobada: ZIP")
            if is_tar:
                evidence.append("Estructura comprobada: TAR")

            # Subtipos estructurales dentro de ZIP (DOCX, JAR, etc.)
            if is_zip:
                # Comprobar si es DOCX/OOXML
                try:
                    with zipfile.ZipFile(str(path), 'r') as zf:
                        if "word/document.xml" in zf.namelist():
                            family = "wordprocessor"
                            name = "OOXML Word (DOCX)"
                            confidence = 0.95
                            evidence.append("Estructura OOXML (word/document.xml)")
                        elif "META-INF/MANIFEST.MF" in zf.namelist() and ext == ".jar":
                            name = "Java Archive"
                            confidence = 0.90
                            evidence.append("Estructura JAR y extensión .jar")
                except zipfile.BadZipFile:
                    pass

        elif mime_type.startswith("text/"):
            family = "text"
            name = "Plain Text"
            confidence = 0.9
        elif mime_type == "application/pdf":
            family = "document"
            name = "PDF Document"
            confidence = 0.95
        elif mime_type.startswith("image/"):
            family = "image"
            name = magic_desc
            confidence = 0.90

        # 3. La extensión como desempate (Regla de Oro A15-1)
        if ext == ".doc" and family == "archive":
            # Demostración del Gate N0: extensión ignorada si choca frontalmente con la estructura.
            evidence.append(f"Extensión {ext} ignorada, contradice la estructura.")
        elif family == "unknown" and ext != "":
            # Si libmagic falla (e.g. un formato muy crudo), la extensión puede dar una pista débil (Nivel 5)
            evidence.append(f"Única pista: extensión {ext}")
            confidence = 0.3
            name = f"Unknown {ext} file"

        return FormatProfile(
            family=family,
            name=name,
            confidence=confidence,
            evidence=evidence
        )
