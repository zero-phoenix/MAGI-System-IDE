import re


class SecretsBlockedError(Exception):
    pass

class SecretsSweeper:
    """
    Barrido de Secretos (CTL-9).
    """
    def __init__(self):
        # Patrones básicos de secretos para el MVP
        self.patterns = [
            re.compile(r"AKIA[0-9A-Z]{16}"), # AWS Access Key ID
            re.compile(r"-----BEGIN PRIVATE KEY-----") # PKCS8
        ]

    def sweep(self, file_content: str, filename: str) -> None:
        """
        Rechaza el contenido si parece un secreto.
        """
        for p in self.patterns:
            if p.search(file_content):
                raise SecretsBlockedError(f"Secreto detectado en '{filename}'. Bloqueando sincronización remota (CTL-9). Rota la clave de inmediato.")
