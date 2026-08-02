from magi.modules.web.policy import WebPolicy

class ServerStub:
    """
    Adaptador al servidor de navegación (Camoufox simulado).
    Asegura CTL-6 (sin exposición de proxy) y CTL-10 (no retorna inferencia).
    """
    def __init__(self):
        self.policy = WebPolicy()
        
    def open_page(self, url: str, purpose: str) -> dict:
        """
        Abre una página asegurando que pasa la puerta de política.
        No acepta parámetros de configuración de proxy/huella por diseño (CTL-6).
        """
        self.policy.check_gate(url, purpose)
        
        # Simula extraer instantánea de accesibilidad
        return {
             "url": url,
             "status": 200,
             "a11y_snapshot": f"Snapshot for {url}",
             "html_size": 40000,
             "snapshot_size": 3000
        }
        
    # CTL-10: Por diseño, este módulo NO contiene ningún método que devuelva ModelResponse.
    # Es imposible usar este módulo como fuente de inferencia.
