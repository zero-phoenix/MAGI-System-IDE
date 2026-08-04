"""
Herramientas de conocimiento del mundo (Plan MAGI 9.0 §6).

Sin este registro, todo `magi/modules/world/` sería código correcto que ningún
agente puede invocar — el fallo que ya cometí tres veces en esta
reconstrucción y que `tests/test_wiring.py` existe para impedir.

REPARTO POR ROL
===============
La escritura en el registro de tesis (`record_thesis`) es deliberadamente de
Melchior: es quien propone. Balthasar y Casper pueden LEER la calibración —
saber que el sistema exagera su confianza un 15 % es exactamente la clase de
evidencia con la que el crítico debe contrastar una propuesta nueva.
"""
from __future__ import annotations

import logging

from ...core.tools.registry import ToolRegistry, ToolResult
from .sources import SourceError

logger = logging.getLogger(__name__)


def _fail(e: Exception) -> ToolResult:
    return ToolResult(False, "", error=str(e))


def register_world_tools(reg: ToolRegistry) -> ToolRegistry:

    # ------------------------------------------------------------- §6.1 / §6.2

    @reg.tool("macro_snapshot",
              "Macro de EE. UU. (paro, tipos, curva, spreads) con fecha por cifra.",
              {"type": "object", "properties": {
                  "series": {"type": "array", "items": {"type": "string"}}}},
              access={"net"})
    async def macro_snapshot_tool(series: list | None = None, ctx=None):
        from .macro import macro_snapshot
        try:
            return ToolResult(True, macro_snapshot(series=series or None))
        except Exception as e:
            return _fail(e)

    @reg.tool("fred_series",
              "Serie histórica de FRED por nombre: paro, bono_10a, tipo_fed, inflacion.",
              {"type": "object", "properties": {
                  "name": {"type": "string"},
                  "limit": {"type": "integer"}},
               "required": ["name"]}, access={"net"})
    async def fred_series_tool(name: str, limit: int = 12, ctx=None):
        from .macro import fred_series
        try:
            datos = fred_series(name, limit=max(1, min(limit, 200)))
        except SourceError as e:
            return _fail(e)
        cuerpo = "\n".join(f"  {d.as_of}  {d.value:>12,.4g} {d.unit}" for d in datos)
        return ToolResult(
            True, f"{name} — {datos[-1].source}\n{cuerpo}\n\n{datos[-1].cite()}",
            meta={"n": len(datos), "ultimo": datos[-1].value})

    @reg.tool("compare_countries",
              "Compara países en un indicador del Banco Mundial. ISO-3: ESP, USA, CHN.",
              {"type": "object", "properties": {
                  "indicator": {"type": "string"},
                  "countries": {"type": "array", "items": {"type": "string"}}},
               "required": ["indicator", "countries"]}, access={"net"})
    async def compare_countries_tool(indicator: str, countries: list, ctx=None):
        from .macro import compare_countries
        try:
            return ToolResult(True, compare_countries(indicator, list(countries)))
        except Exception as e:
            return _fail(e)

    @reg.tool("news_headlines",
              "Titulares oficiales por RSS (fed, bce, sec, boe, eurostat, un) con fecha.",
              {"type": "object", "properties": {
                  "feeds": {"type": "array", "items": {"type": "string"}},
                  "per_feed": {"type": "integer"}}}, access={"net"})
    async def news_headlines_tool(feeds: list | None = None,
                                  per_feed: int = 5, ctx=None):
        from .feeds import headlines
        try:
            return ToolResult(True, headlines(feeds=feeds or None,
                                              per_feed=max(1, min(per_feed, 20))))
        except Exception as e:
            return _fail(e)

    # ------------------------------------------------------------------- §6.3

    @reg.tool("company_fundamentals",
              "Fundamentales anuales de una cotizada de EE. UU. desde SEC EDGAR XBRL.",
              {"type": "object", "properties": {
                  "ticker": {"type": "string"},
                  "years": {"type": "integer"}},
               "required": ["ticker"]}, access={"net"})
    async def company_fundamentals_tool(ticker: str, years: int = 5, ctx=None):
        from .edgar import fundamentals, render_fundamentals
        try:
            paquete = fundamentals(ticker, years=max(2, min(years, 10)))
        except SourceError as e:
            return _fail(e)
        return ToolResult(True, render_fundamentals(paquete),
                          meta={"cik": paquete["cik"],
                                "conceptos": len(paquete["datos"])})

    @reg.tool("owner_earnings",
              "Ganancias del propietario: flujo operativo menos capex de mantenimiento.",
              {"type": "object", "properties": {
                  "operating_cash_flow": {"type": "number"},
                  "capex": {"type": "number"},
                  "depreciation": {"type": "number"},
                  "revenue": {"type": "array", "items": {"type": "number"}},
                  "ppe": {"type": "number"}},
               "required": ["operating_cash_flow", "capex", "depreciation"]})
    async def owner_earnings_tool(operating_cash_flow: float, capex: float,
                                  depreciation: float,
                                  revenue: list | None = None,
                                  ppe: float | None = None, ctx=None):
        from .finance import maintenance_capex, owner_earnings
        try:
            mc = maintenance_capex(capex, depreciation,
                                   [float(x) for x in revenue] if revenue else None,
                                   float(ppe) if ppe else None)
            oe = owner_earnings(operating_cash_flow, mc.value)
        except Exception as e:
            return _fail(e)
        return ToolResult(True, mc.render() + "\n\n" + oe.render(),
                          meta={"owner_earnings": oe.value})

    @reg.tool("dcf_valuation",
              "Descuento de flujos con rejilla de sensibilidad, nunca un número solo.",
              {"type": "object", "properties": {
                  "base_cash_flow": {"type": "number"},
                  "growth": {"type": "number"},
                  "discount": {"type": "number"},
                  "terminal_growth": {"type": "number"},
                  "years": {"type": "integer"}},
               "required": ["base_cash_flow", "growth", "discount",
                            "terminal_growth"]})
    async def dcf_tool(base_cash_flow: float, growth: float, discount: float,
                       terminal_growth: float, years: int = 10, ctx=None):
        from .finance import DCFAssumptions, dcf_sensitivity
        try:
            a = DCFAssumptions(growth, discount, terminal_growth, years)
            return ToolResult(True, dcf_sensitivity(base_cash_flow, a))
        except Exception as e:
            return _fail(e)

    @reg.tool("quality_checklist",
              "Rúbrica de calidad: ROIC, conversión de caja, deuda/EBITDA, dilución.",
              {"type": "object", "properties": {
                  "metrics": {"type": "object"}},
               "required": ["metrics"]})
    async def quality_checklist_tool(metrics: dict, ctx=None):
        from .finance import quality_checklist
        try:
            limpio = {k: float(v) for k, v in dict(metrics).items()}
            return ToolResult(True, quality_checklist(limpio))
        except (TypeError, ValueError) as e:
            return _fail(e)

    # --------------------------------------------------- §6.3 registro de tesis

    @reg.tool("record_thesis",
              "Congela una tesis falsable con su confianza (0-1) y su horizonte.",
              {"type": "object", "properties": {
                  "subject": {"type": "string"},
                  "claim": {"type": "string"},
                  "confidence": {"type": "number"},
                  "reasoning": {"type": "string"},
                  "horizon_days": {"type": "integer"},
                  "sources": {"type": "array", "items": {"type": "string"}}},
               "required": ["subject", "claim", "confidence"]}, access={"write"})
    async def record_thesis_tool(subject: str, claim: str, confidence: float,
                                 reasoning: str = "", horizon_days: int = 180,
                                 sources: list | None = None, ctx=None):
        from .thesis import ThesisLog
        try:
            t = ThesisLog().record(subject, claim, float(confidence), reasoning,
                                   int(horizon_days),
                                   [str(s) for s in (sources or [])])
        except Exception as e:
            return _fail(e)
        return ToolResult(
            True, f"Tesis {t.thesis_id} registrada.\n  {t.subject}: {t.claim}\n"
            f"  confianza {t.confidence:.0%}, vence {t.horizon}",
            meta={"thesis_id": t.thesis_id})

    @reg.tool("resolve_thesis",
              "Puntúa una tesis vencida como acierto o fallo. Irreversible.",
              {"type": "object", "properties": {
                  "thesis_id": {"type": "string"},
                  "outcome": {"type": "boolean"},
                  "note": {"type": "string"}},
               "required": ["thesis_id", "outcome"]}, access={"write"})
    async def resolve_thesis_tool(thesis_id: str, outcome: bool,
                                  note: str = "", ctx=None):
        from .thesis import ThesisLog
        try:
            t = ThesisLog().resolve(thesis_id, bool(outcome), note)
        except Exception as e:
            return _fail(e)
        return ToolResult(
            True, f"{t.thesis_id}: {'acierto' if t.outcome else 'fallo'}. "
            f"Brier de esta tesis {t.brier:.4f} "
            f"(declaraste {t.confidence:.0%}).")

    @reg.tool("calibration_report",
              "Calibración: confianza declarada frente a acierto real, Brier y base.",
              {"type": "object", "properties": {
                  "subject": {"type": "string"}}})
    async def calibration_report_tool(subject: str = "", ctx=None):
        from .thesis import ThesisLog
        log = ThesisLog()
        try:
            cuerpo = log.calibration_curve(subject=subject or None)
        except Exception as e:
            return _fail(e)
        pend = log.render_pending(limit=10)
        return ToolResult(True, cuerpo + "\n\n" + pend,
                          meta=log.brier_score(subject or None))

    return reg
