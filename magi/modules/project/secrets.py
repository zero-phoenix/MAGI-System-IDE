import logging
import math
import re

logger = logging.getLogger(__name__)

# CTL-9: Barrido de secretos
class SecretScanner:
    """
    Implementa CTL-9: Barrido de secretos por patrón y entropía.
    Garantiza que no se suban credenciales en los repositorios locales/remotos (P21.c.2).
    """

    # Patrones comunes de tokens y claves
    PATTERNS = [
        re.compile(r'(?i)(api[_-]?key|secret|token|password)[\s:=]+["\']?[a-zA-Z0-9\-_]{16,}["\']?'),
        re.compile(r'gh[po]_[a-zA-Z0-9]{36}'),          # GitHub Tokens
        re.compile(r'AKIA[0-9A-Z]{16}'),               # AWS Key
        re.compile(r'-----BEGIN (RSA|OPENSSH|PRIVATE) KEY-----') # Claves privadas completas
    ]

    @staticmethod
    def shannon_entropy(data: str) -> float:
        """Calcula la entropía de Shannon para detectar cadenas pseudoaleatorias (ej. tokens base64)."""
        if not data:
            return 0.0
        entropy = 0
        for x in set(data):
            p_x = float(data.count(x)) / len(data)
            entropy -= p_x * math.log(p_x, 2)
        return entropy

    def scan_content(self, content: str) -> list[str]:
        """Escanea el contenido en memoria y retorna los hallazgos."""
        findings = []
        for pattern in self.PATTERNS:
            if pattern.search(content):
                findings.append(f"Match de patrón sospechoso: {pattern.pattern[:15]}...")

        # Opcional: Escaneo por entropía en palabras muy largas
        for word in re.findall(r'[a-zA-Z0-9\-_+]{32,}', content):
            if self.shannon_entropy(word) > 4.5:
                findings.append("Cadena de alta entropía detectada (posible llave base64/hex).")

        return findings

    def scan_file(self, filepath: str) -> list[str]:
        """Escanea un fichero en el disco."""
        try:
            with open(filepath, encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return self.scan_content(content)
        except Exception as e:
            logger.error(f"No se pudo escanear el archivo {filepath}: {e}")
            return []
