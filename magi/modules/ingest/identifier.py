class Identifier:
    """
    Identificador Multiseñal (P15.a). Nivel 0.
    """
    def identify(self, path: str, magic_bytes: str, ext: str) -> dict:
        """
        Determina el formato priorizando magic_bytes sobre la extensión.
        """
        # Regla: La extensión nunca decide sola si el magic dice otra cosa
        if magic_bytes == "PDF_MAGIC":
            return {"format": "PDF", "confidence": 0.9}
        elif magic_bytes == "WORDPERFECT_MAGIC":
            return {"format": "WordPerfect 1.0", "confidence": 0.8}

        # Si magic contradice extensión agresivamente
        if ext == ".pdf" and magic_bytes == "EXE_MAGIC":
             return {"format": "UNSAFE_EXECUTABLE", "confidence": 0.95}

        return {"format": "UNKNOWN", "confidence": 0.0}
