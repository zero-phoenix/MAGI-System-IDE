import logging

from .adapter import GatewayInfo, RouteAdapter
from .models import InferenceRequest, ModelResponse, RouteDirective
from .privacy_filter import PrivacyFilter
from .quota_ledger import QuotaLedger

logger = logging.getLogger(__name__)

class Gateway:
    """
    Pasarela Universal de Inferencia (MAGI-ROUTE) (P14.a, P14.e).
    Enruta a OmniRoute y maneja el camino de reserva si la pasarela falla.
    """
    def __init__(self):
        self.privacy = PrivacyFilter()
        self.adapter = RouteAdapter()

        # Reservas para el camino de fallback (cuando OmniRoute no está)
        self.cloud_quota = QuotaLedger(limit=100)
        self.local_quota = QuotaLedger(limit=999999)

    async def get_status(self) -> GatewayInfo:
        return await self.adapter.ensure_gateway()

    async def route_request(self, req: InferenceRequest, route: RouteDirective, provider_preference: str = "cloud") -> dict:
        """
        Enruta la petición usando OmniRoute si está disponible.
        Si falla, cae al camino de reserva (fallback).
        """
        # 1. Filtro de Privacidad (aplicable tanto a OmniRoute como a fallback)
        priv_check = self.privacy.check_request(provider_preference, {"privacy_class": route.privacy_class})
        if priv_check["status"] == "blocked":
            return {"success": False, "error": priv_check["reason"]}

        # 2. Intentar usar OmniRoute
        try:
            logger.info("Intentando enrutar a través de OmniRoute...")
            response: ModelResponse = await self.adapter.complete(req, route)
            return {
                "success": True,
                "provider_used": response.telemetry.provider,
                "response": response.text,
                "telemetry": response.telemetry.model_dump()
            }
        except Exception as e:
            if "MAGI-ROUTE_FALLBACK" in str(e):
                logger.warning("OmniRoute no disponible. Usando camino de reserva obligatorio (Fallback).")
                return await self._fallback_route(provider_preference, req, route)
            else:
                logger.error(f"Error fatal en enrutamiento: {e}")
                return {"success": False, "error": str(e)}

    async def _fallback_route(self, provider_preference: str, req: InferenceRequest, route: RouteDirective) -> dict:
        """Camino de reserva: simula llamada directa al proveedor local/cloud."""
        target = provider_preference
        if route.privacy_class == "local_only":
            target = "local"

        estimated_cost = 10
        if target == "cloud":
            if self.cloud_quota.consume(estimated_cost):
                return {"success": True, "provider_used": "cloud_direct", "response": f"[Fallback Cloud] Respondiendo a: {req.prompt}"}
            else:
                target = "local"

        if target == "local":
            if self.local_quota.consume(estimated_cost):
                return {"success": True, "provider_used": "local_direct", "response": f"[Fallback Local] Respondiendo a: {req.prompt}"}
            else:
                return {"success": False, "error": "WAITING_QUOTA: All fallback providers exhausted"}

        return {"success": False, "error": "Unknown Provider"}
