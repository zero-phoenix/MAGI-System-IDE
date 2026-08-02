import logging
from .models import RouteDirective, InferenceRequest, ModelResponse, CostTelemetry
from .telemetry import TelemetryMonitor
from .preflight import PreflightChecker

logger = logging.getLogger(__name__)

class RouteAdapter:
    """
    A14-1: Selección con política propia sobre pasarela.
    Aplica la Regla Dura de Privacidad y enruta.
    """
    def __init__(self):
        self.preflight = PreflightChecker()
        self.telemetry = TelemetryMonitor()

    async def complete(self, req: InferenceRequest, route: RouteDirective, test_simulate_cost: bool = False) -> ModelResponse:
        logger.info(f"Iniciando enrutamiento para unidad {route.unit_id} (Rol: {route.role})")
        
        # 2. Regla Dura de Privacidad
        if route.privacy_class == "local_only":
            logger.info("Privacidad local_only detectada: Forzando allow_remote=False y forbid_providers=['*']")
            route.allow_remote = False
            route.forbid_providers = ["*"]
            route.pin_model = "local-llama3"
            
        # Simulación de prohibición de estrategias (e.g. fusion/pipeline)
        if route.strategy in ["fusion", "pipeline"]:
            logger.warning(f"Estrategia {route.strategy} prohibida. Degadando a priority.")
            route.strategy = "priority"
            
        # Llamada simulada a la pasarela
        logger.info(f"Llamando a pasarela con modelo fijado: {route.pin_model} (Estrategia: {route.strategy})")
        
        cost_usd = 0.01 if test_simulate_cost else 0.0
        
        telemetry_data = CostTelemetry(
            provider="local" if not route.allow_remote else "openai_free_tier",
            model=route.pin_model if route.pin_model else "qwen2.5-coder",
            tokens_in=150,
            tokens_out=45,
            cost_usd=cost_usd,
            cache_hit=False
        )
        
        # Validar coste
        self.telemetry.check_cost(telemetry_data)
        
        return ModelResponse(
            text="Respuesta simulada del modelo.",
            telemetry=telemetry_data
        )
