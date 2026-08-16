import logging

logger = logging.getLogger(__name__)

class WebBlockedError(Exception):
    pass

class WebPolicy:
    """
    Puerta de Política (CTL-5, CTL-7).
    Filtra qué puede navegar el sistema y con qué propósito.
    """
    def __init__(self):
        # CTL-5: Propósitos estrictos declarados
        self.allowed_purposes = [
            "documentación", "norma", "datasheet", "patente",
            "repositorio", "evidencia", "sesión propia del usuario"
        ]

        # CTL-7: Lista negra permanente.
        # Prohíbe interfaces de chat para evitar que el agente use otro LLM evadiendo cuotas.
        self.permanent_blacklist = [
            "chat.openai.com", "claude.ai", "gemini.google.com", "chatgpt.com"
        ]

    def check_gate(self, url: str, purpose: str) -> None:
        """
        CTL-5 y CTL-7: Aplica reglas antes de tocar la red.
        """
        if not purpose or purpose not in self.allowed_purposes:
            logger.error(f"policy: Propósito '{purpose}' no declarado o inválido.")
            raise WebBlockedError(f"policy: Propósito '{purpose}' no declarado o inválido.")

        domain = self._extract_domain(url)
        if domain in self.permanent_blacklist:
             logger.critical(f"blacklist: Dominio '{domain}' bloqueado permanentemente (CTL-7).")
             raise WebBlockedError(f"blacklist: Dominio '{domain}' bloqueado permanentemente (CTL-7).")

        # Mock de revisión robots.txt (A19-1 paso 4)
        if "norobots.com" in domain:
             logger.warning(f"robots: El sitio '{domain}' prohíbe el acceso en robots.txt.")
             raise WebBlockedError(f"robots: El sitio '{domain}' prohíbe el rastreo automatizado.")

    def _extract_domain(self, url: str) -> str:
        if "://" in url:
            return url.split("://")[1].split("/")[0]
        return url
