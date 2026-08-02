from magi.modules.route.privacy_filter import PrivacyFilter
from magi.modules.route.quota_ledger import QuotaLedger

class Gateway:
    """
    Pasarela Universal de Inferencia (MAGI-ROUTE) (P14.a, P14.e).
    Enruta, filtra y delega según la disponibilidad.
    """
    def __init__(self):
        self.privacy = PrivacyFilter()
        self.cloud_quota = QuotaLedger(limit=100) # Límite muy bajo para forzar el fallback
        self.local_quota = QuotaLedger(limit=999999)
        
    def route_request(self, provider_preference: str, payload: dict, estimated_cost: int = 10) -> dict:
        """Simula el enrutamiento y ejecución."""
        
        # 1. Filtro de Privacidad
        priv_check = self.privacy.check_request(provider_preference, payload.get("metadata", {}))
        if priv_check["status"] == "blocked":
            return {"success": False, "error": priv_check["reason"]}
            
        # 2. Enrutamiento con Fallback
        target = provider_preference
        if target == "cloud":
            if self.cloud_quota.consume(estimated_cost):
                return {"success": True, "provider_used": "cloud", "response": "Cloud Response"}
            else:
                # Agotado, fallback a local
                target = "local"
                
        if target == "local":
            if self.local_quota.consume(estimated_cost):
                return {"success": True, "provider_used": "local", "response": "Local Response"}
            else:
                return {"success": False, "error": "WAITING_QUOTA: All providers exhausted"}
                
        return {"success": False, "error": "Unknown Provider"}
