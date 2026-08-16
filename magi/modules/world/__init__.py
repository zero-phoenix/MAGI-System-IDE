"""
Conocimiento del mundo (Plan MAGI 9.0 §6).

Actualidad, macro, geopolítica y finanzas desde fuentes con datos duros y sin
clave de API, más el registro de tesis que hace medible el criterio del
sistema.

Las cinco propiedades de §6.4 —recuperación antes que recuerdo, herramientas
antes que intuición, verificación antes que afirmación, citación antes que
aserción, calibración antes que confianza— no son un lema: son lo que impone
la forma de este paquete. `Datum` no se construye sin fuente y fecha, `Calc`
no existe sin fórmula, y `ThesisLog` puntúa lo que el sistema afirmó hace seis
meses lo recuerde o no.
"""
from .finance import (
    Calc,
    DCFAssumptions,
    DCFResult,
    FinanceError,
    cash_conversion,
    dcf,
    dcf_sensitivity,
    dilution,
    leverage,
    maintenance_capex,
    owner_earnings,
    quality_checklist,
    roic,
)
from .sources import (
    Datum,
    Fetcher,
    FrozenFetcher,
    HttpFetcher,
    SourceError,
    set_default_fetcher,
)
from .thesis import Thesis, ThesisError, ThesisLog
from .tools import register_world_tools

__all__ = [
    "Datum", "Fetcher", "FrozenFetcher", "HttpFetcher", "SourceError",
    "set_default_fetcher",
    "Calc", "DCFAssumptions", "DCFResult", "FinanceError", "cash_conversion",
    "dcf", "dcf_sensitivity", "dilution", "leverage", "maintenance_capex",
    "owner_earnings", "quality_checklist", "roic",
    "Thesis", "ThesisError", "ThesisLog",
    "register_world_tools",
]
