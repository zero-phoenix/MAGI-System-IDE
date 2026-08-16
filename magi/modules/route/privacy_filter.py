class PrivacyFilter:
    """
    Guarda de Privacidad de Red (P14.c).
    Evita fuga de información marcada como `local_only` a proveedores de nube.
    """
    def __init__(self):
        pass

    def check_request(self, target_provider: str, payload_metadata: dict) -> dict:
        """
        Bloquea si el destino es la nube y el dato es estrictamente local.
        """
        is_cloud = target_provider.lower() in ["cloud", "claude", "openai"]
        is_local_only = payload_metadata.get("privacy_class") == "local_only"

        if is_cloud and is_local_only:
             return {
                 "status": "blocked",
                 "reason": "PRIVACY_ERROR: Cannot send 'local_only' content to a cloud provider."
             }
        return {"status": "allowed"}
