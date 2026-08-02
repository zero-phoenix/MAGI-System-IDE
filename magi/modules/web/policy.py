class WebBlockedError(Exception):
    pass

class WebPolicy:
    """
    Puerta de Política (CTL-5, CTL-7).
    Filtra qué puede navegar el sistema y con qué propósito.
    """
    def __init__(self):
        self.allowed_purposes = ["documentación", "norma", "datasheet", "patente", "repositorio", "evidencia", "sesión propia del usuario"]
        self.permanent_blacklist = ["chat.openai.com", "claude.ai", "gemini.google.com"]
        
    def check_gate(self, url: str, purpose: str) -> None:
        """
        CTL-5 y CTL-7: Aplica reglas antes de tocar la red.
        """
        if not purpose or purpose not in self.allowed_purposes:
            raise WebBlockedError(f"policy: Propósito '{purpose}' no declarado o inválido.")
            
        domain = self._extract_domain(url)
        if domain in self.permanent_blacklist:
             raise WebBlockedError(f"blacklist: Dominio '{domain}' bloqueado permanentemente (CTL-7).")
             
    def _extract_domain(self, url: str) -> str:
        # Simplificación para el stub
        if "://" in url:
            domain = url.split("://")[1].split("/")[0]
            return domain
        return url
