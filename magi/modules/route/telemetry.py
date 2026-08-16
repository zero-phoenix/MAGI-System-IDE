import logging

from .models import CostTelemetry

logger = logging.getLogger(__name__)

class CostAlertError(Exception):
    pass

class TelemetryMonitor:
    """
    A14-3: Conciliación de telemetría de coste y uso.
    """
    def check_cost(self, telemetry: CostTelemetry):
        # 5. cost_usd debe ser 0 en todas las rutas de este plan
        if telemetry.cost_usd > 0:
            logger.critical(f"ALERTA: Proveedor {telemetry.provider} reporta coste > 0 ({telemetry.cost_usd} USD)!")
            raise CostAlertError(f"Cortacircuitos de Economía activado: {telemetry.provider} facturó {telemetry.cost_usd} USD.")

        logger.info(f"Telemetría validada: 0 USD coste. Tokens: {telemetry.tokens_in} IN, {telemetry.tokens_out} OUT.")
