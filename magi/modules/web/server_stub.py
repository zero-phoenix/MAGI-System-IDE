import logging

from magi.modules.web.policy import WebPolicy

logger = logging.getLogger(__name__)

class ServerStub:
    """
    Adaptador al servidor de navegación (Camoufox simulado).
    Asegura CTL-6 (sin exposición de proxy) y CTL-10 (no retorna inferencia).
    """
    def __init__(self, bind_host: str = "127.0.0.1"):
        if bind_host != "127.0.0.1":
            logger.critical("Security: El servidor web debe ejecutarse en loopback exclusivo.")
            raise ValueError("Bind address must be 127.0.0.1")

        self.policy = WebPolicy()

    def open_page(self, url: str, purpose: str, **kwargs) -> dict:
        """
        Abre una página asegurando que pasa la puerta de política.
        CTL-6: El parámetro de proxy_strategy no se expone ni se lee.
        """
        if 'proxy' in kwargs or 'fingerprint' in kwargs:
             logger.warning("CTL-6: Intento de inyectar proxy o huella dinámica interceptado y descartado.")

        self.policy.check_gate(url, purpose)

        # Simula extraer instantánea de accesibilidad frente al HTML crudo (A19-3)
        html_size_simulated = len(url) * 1000 + 35000  # Ej: 45000 chars
        a11y_snapshot_simulated = f"[Snapshot A11y] Title: Documentación de {url}\n[Content]: Esto ocupa el 10% del original."
        snapshot_size = len(a11y_snapshot_simulated)

        return {
             "url": url,
             "status": 200,
             "a11y_snapshot": a11y_snapshot_simulated,
             "html_size": html_size_simulated,
             "snapshot_size": snapshot_size
        }

    # CTL-10: Por diseño, este módulo NO contiene ningún método que devuelva ModelResponse.
    # Es imposible usar este módulo como fuente de inferencia porque sus retornos son exclusivamente dicts de evidencia.
