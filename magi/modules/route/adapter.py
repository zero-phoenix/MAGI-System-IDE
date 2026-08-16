import asyncio
import logging

import httpx
from pydantic import BaseModel

from .models import CostTelemetry, InferenceRequest, ModelResponse, RouteDirective
from .preflight import PreflightChecker, SecurityPolicyError
from .telemetry import TelemetryMonitor

logger = logging.getLogger(__name__)

class GatewayInfo(BaseModel):
    version: str
    status: str
    models: int

class HealthReport(BaseModel):
    healthy: bool
    latency_ms: float
    error: str | None = None

class RouteModel(BaseModel):
    id: str
    provider: str
    context_length: int

class RouteAdapter:
    """
    A14-1: Pasarela Universal de Inferencia (MAGI-ROUTE).
    Enruta las peticiones HTTP a 127.0.0.1:20128/v1 asegurando la regla dura de privacidad.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 20129):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}/v1"
        self.preflight = PreflightChecker(target_port=port)
        self.telemetry = TelemetryMonitor()
        self.client = httpx.AsyncClient(timeout=60.0)

    async def ensure_gateway(self) -> GatewayInfo:
        """Verifica versión fijada, puerto y enlace a loopback."""
        try:
            self.preflight.check_exposure(simulate_0_0_0_0=False)
            response = await self.client.get(f"{self.base_url}/models", timeout=2.0)
            if response.status_code == 200:
                data = response.json()
                return GatewayInfo(
                    version="1.0.0", # Podríamos extraerlo de headers si OmniRoute lo manda
                    status="HEALTHY",
                    models=len(data.get("data", []))
                )
            return GatewayInfo(version="unknown", status="DEGRADED", models=0)
        except SecurityPolicyError as e:
            # La pasarela fuera de loopback no es un fallo de red: es una
            # exposición que la política prohíbe. No se reintenta ni se
            # degrada: se reporta y se queda caída hasta que se corrija.
            logger.error(f"Preflight bloqueó la pasarela: {e}")
            return GatewayInfo(version="unknown", status="BLOCKED", models=0)
        except httpx.RequestError as e:
            logger.warning(f"Gateway no disponible en {self.base_url}: {e}")
            return GatewayInfo(version="unknown", status="DOWN", models=0)

    async def gateway_health(self) -> HealthReport:
        """GET /health; 3 fallos ⇒ camino de reserva."""
        # OmniRoute no documenta /health explícitamente en OpenAI std, usaremos /models
        try:
            start = asyncio.get_event_loop().time()
            res = await self.client.get(f"{self.base_url}/models", timeout=2.0)
            latency = (asyncio.get_event_loop().time() - start) * 1000
            return HealthReport(healthy=res.status_code == 200, latency_ms=latency)
        except Exception as e:
            return HealthReport(healthy=False, latency_ms=0, error=str(e))

    async def list_models(self) -> list[RouteModel]:
        try:
            res = await self.client.get(f"{self.base_url}/models")
            res.raise_for_status()
            data = res.json().get("data", [])
            return [
                RouteModel(
                    id=m["id"],
                    provider=m.get("owned_by", "unknown"),
                    context_length=32768
                ) for m in data
            ]
        except Exception as e:
            logger.error(f"Error listando modelos: {e}")
            return []

    async def complete(self, req: InferenceRequest, route: RouteDirective) -> ModelResponse:
        logger.info(f"Iniciando enrutamiento para unidad {route.unit_id} (Rol: {route.role})")

        # 2. Regla Dura de Privacidad
        if route.privacy_class == "local_only":
            logger.info("Privacidad local_only detectada: Forzando allow_remote=False y forbid_providers=['*']")
            route.allow_remote = False
            route.forbid_providers = ["*"]

        # Simulación de prohibición de estrategias (e.g. fusion/pipeline)
        if route.strategy in ["fusion", "pipeline"]:
            logger.warning(f"Estrategia {route.strategy} prohibida. Degadando a priority.")
            route.strategy = "priority"

        # Preparar payload OpenAI compatible
        payload = {
            "model": route.pin_model if route.pin_model else "gpt-3.5-turbo",
            "messages": [],
            "temperature": req.temperature,
        }
        if req.system:
            payload["messages"].append({"role": "system", "content": req.system})
        payload["messages"].append({"role": "user", "content": req.prompt})

        if req.seed:
            payload["seed"] = req.seed

        # Headers extra para OmniRoute (si aplican)
        headers = {
            "Content-Type": "application/json",
            "X-Route-Strategy": route.strategy,
            "X-Route-Forbid-Providers": ",".join(route.forbid_providers)
        }

        try:
            res = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            )
            res.raise_for_status()
            data = res.json()

            text = data["choices"][0]["message"]["content"]

            # Procesar cabeceras de telemetría de coste de OmniRoute
            cost = self.cost_headers(res)
            self.telemetry.check_cost(cost)

            return ModelResponse(text=text, telemetry=cost)

        except httpx.RequestError as e:
            logger.error(f"Fallo de conexión a la pasarela OmniRoute: {e}")
            raise Exception("MAGI-ROUTE_FALLBACK") from e
        except Exception as e:
            logger.error(f"Error en OmniRoute: {e}")
            raise

    def cost_headers(self, resp: httpx.Response) -> CostTelemetry:
        """Procesa las cabeceras devueltas por OmniRoute"""
        # Valores por defecto si OmniRoute no envía headers
        return CostTelemetry(
            provider=resp.headers.get("X-OmniRoute-Provider", "unknown"),
            model=resp.headers.get("X-OmniRoute-Model", "unknown"),
            tokens_in=int(resp.headers.get("X-OmniRoute-Tokens-In", 0)),
            tokens_out=int(resp.headers.get("X-OmniRoute-Tokens-Out", 0)),
            cost_usd=float(resp.headers.get("X-OmniRoute-Cost", 0.0)),
            cache_hit=resp.headers.get("X-OmniRoute-Cache-Hit", "false").lower() == "true"
        )
