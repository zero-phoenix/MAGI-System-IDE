"""
Fundamentales desde SEC EDGAR XBRL (Plan MAGI 9.0 §6.3).

Cifras auditadas y presentadas ante el regulador, gratis y sin clave. Es la
única fuente de esta lista que no depende de que un tercero decida seguir
regalando una API.

EL FALLO QUE ESTUVO A PUNTO DE COLARSE
======================================
Consultando a Apple en la API real, la respuesta trae ESTO:

    FY2024   2023-10-01 .. 2024-09-28   118.3 B   (10-K)
    FY2025   2023-10-01 .. 2024-09-28   118.3 B   (10-K)   <-- el MISMO periodo
    FY2025   2024-09-29 .. 2025-09-27   111.5 B   (10-K)

El periodo 2023-10 a 2024-09 aparece dos veces porque la 10-K de 2025 incluye
el año anterior como comparativa. Sumar "los últimos tres ejercicios" sobre la
lista cruda cuenta ese año dos veces y las ganancias del propietario salen
infladas un 30 % sin que nada avise.

Por eso `annual_series` deduplica por (start, end) quedándose con la
presentación MÁS RECIENTE — que además es la correcta cuando ha habido
reexpresión contable.

No lo encontré razonando: lo encontré llamando a la API antes de escribir el
parser. Es la cuarta regla del proyecto: arrancar encuentra fallos que leer no
encuentra.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from .sources import Datum, Fetcher, SourceError, default_fetcher

logger = logging.getLogger(__name__)

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
CONCEPT_URL = ("https://data.sec.gov/api/xbrl/companyconcept/"
               "CIK{cik:010d}/us-gaap/{concept}.json")

# Los conceptos XBRL que hacen falta para el análisis de §6.3. Un mismo dato
# vive bajo etiquetas distintas según el emisor y el año, así que cada uno
# lleva su cadena de alternativas y se prueba en orden.
CONCEPTS: dict[str, tuple[str, ...]] = {
    "flujo_operativo": (
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"),
    "capex": (
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets"),
    "ingresos": (
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues", "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueNet"),
    "beneficio_neto": ("NetIncomeLoss",),
    "resultado_explotacion": ("OperatingIncomeLoss",),
    "margen_bruto": ("GrossProfit",),
    "activos": ("Assets",),
    "pasivos": ("Liabilities",),
    "patrimonio": (
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"),
    "deuda_largo_plazo": (
        "LongTermDebtNoncurrent", "LongTermDebt"),
    "efectivo": (
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"),
    "acciones_diluidas": (
        "WeightedAverageNumberOfDilutedSharesOutstanding",),
    "dividendos": ("PaymentsOfDividendsCommonStock", "PaymentsOfDividends"),
    "recompras": ("PaymentsForRepurchaseOfCommonStock",),
    "amortizacion": (
        "DepreciationDepletionAndAmortization",
        "DepreciationAmortizationAndAccretionNet", "Depreciation"),
    "gastos_intereses": ("InterestExpense", "InterestIncomeExpenseNet"),
    "impuestos": ("IncomeTaxExpenseBenefit",),
}


@dataclass(frozen=True)
class Fact:
    """Una observación XBRL ya limpia."""
    start: str | None
    end: str
    value: float
    fy: int | None
    form: str
    filed: str
    accn: str
    #: La clave de `units` de la que salió el número: "USD", "EUR", "shares"…
    #: Va en el hecho y no se supone fuera, porque suponerla era inventarla.
    unit: str = "USD"

    @property
    def days(self) -> int | None:
        if not self.start:
            return None
        from datetime import date
        try:
            return (date.fromisoformat(self.end)
                    - date.fromisoformat(self.start)).days
        except ValueError:
            return None

    @property
    def is_annual(self) -> bool:
        """Un ejercicio dura entre 340 y 400 días — los años fiscales de 52/53
        semanas no caen en 365 clavados."""
        d = self.days
        return d is not None and 340 <= d <= 400


def resolve_cik(ticker: str, *, fetcher: Fetcher | None = None) -> tuple[int, str]:
    """Ticker -> (CIK, nombre). El fichero de la SEC es la lista canónica."""
    body = (fetcher or default_fetcher()).get(TICKERS_URL, "institucion")
    try:
        tabla: dict[str, Any] = json.loads(body)
    except json.JSONDecodeError as e:
        raise SourceError("la SEC no devolvió el índice de tickers") from e

    objetivo = ticker.strip().upper()
    for fila in tabla.values():
        if str(fila.get("ticker", "")).upper() == objetivo:
            return int(fila["cik_str"]), str(fila.get("title", objetivo))
    raise SourceError(
        f"ticker '{ticker}' no está en el índice de la SEC. EDGAR solo cubre "
        f"emisores registrados en EE. UU.: una cotizada europea o japonesa no "
        f"aparece salvo que tenga ADR con presentación 20-F")


def _facts(cik: int, concept: str, *, fetcher: Fetcher | None = None) -> list[Fact]:
    url = CONCEPT_URL.format(cik=cik, concept=concept)
    body = (fetcher or default_fetcher()).get(url, "fundamental")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        raise SourceError(f"EDGAR: respuesta no-JSON para {concept}") from e

    # De qué unidad sale la serie, y se APUNTA. Antes se caía a
    # `next(iter(unidades.values()))` —cualquier unidad— y más abajo se
    # etiquetaba el resultado como "USD" a ciegas. El filtro de formularios
    # acepta `20-F` a propósito, que es justo el que presentan los emisores
    # extranjeros en su moneda: euros, libras o yenes salían rotulados como
    # dólares, y `Datum.cite()` propagaba la mentira al razonamiento del
    # enjambre. En un módulo cuya tesis es que un dato sin procedencia es un
    # rumor, la unidad no se puede dar por hecha.
    unidades = payload.get("units", {})
    for clave in ("USD", "shares"):
        if unidades.get(clave):
            moneda, serie = clave, unidades[clave]
            break
    else:
        moneda, serie = next(iter(unidades.items()), ("USD", []))

    out: list[Fact] = []
    for u in serie:
        try:
            out.append(Fact(
                start=u.get("start"), end=u["end"], value=float(u["val"]),
                fy=u.get("fy"), form=str(u.get("form", "")),
                filed=str(u.get("filed", "")), accn=str(u.get("accn", "")),
                unit=str(moneda)))
        except (KeyError, TypeError, ValueError):
            continue
    return out


def concept_facts(cik: int, name: str, *,
                  fetcher: Fetcher | None = None) -> tuple[str, list[Fact]]:
    """
    Hechos de un concepto legible, probando la cadena de etiquetas XBRL.

    Devuelve también QUÉ etiqueta funcionó: cuando dos empresas usan etiquetas
    distintas para lo mismo, saber cuál se usó es la diferencia entre poder
    auditar el número y tener que fiarte.
    """
    if name not in CONCEPTS:
        raise SourceError(
            f"concepto desconocido: '{name}'. Disponibles: "
            f"{', '.join(sorted(CONCEPTS))}")
    errores = []
    for etiqueta in CONCEPTS[name]:
        try:
            hechos = _facts(cik, etiqueta, fetcher=fetcher)
            if hechos:
                return etiqueta, hechos
        except SourceError as e:
            errores.append(f"{etiqueta}: {e}")
    raise SourceError(
        f"ninguna etiqueta XBRL de '{name}' devolvió datos para CIK {cik}. "
        f"Probadas: {', '.join(CONCEPTS[name])}"
        + (f" · {'; '.join(errores[:2])}" if errores else ""))


def annual_series(cik: int, name: str, *, fetcher: Fetcher | None = None,
                  years: int = 5) -> list[Datum]:
    """
    Serie ANUAL deduplicada de un concepto.

    Aquí es donde se corrige el doble conteo descrito arriba: se agrupa por
    (start, end) y se conserva la presentación con `filed` más reciente, que
    es la que refleja cualquier reexpresión posterior.
    """
    etiqueta, hechos = concept_facts(cik, name, fetcher=fetcher)

    anuales = [h for h in hechos
               if h.form in ("10-K", "20-F") and (h.is_annual or h.start is None)]
    if not anuales:
        anuales = [h for h in hechos if h.is_annual or h.start is None]
    if not anuales:
        raise SourceError(
            f"'{name}' no tiene observaciones anuales para CIK {cik} "
            f"(solo trimestrales)")

    # Deduplicación por periodo, quedándose con la presentación más reciente.
    mejor: dict[tuple[str | None, str], Fact] = {}
    for h in anuales:
        clave = (h.start, h.end)
        actual = mejor.get(clave)
        if actual is None or h.filed > actual.filed:
            mejor[clave] = h

    ordenados = sorted(mejor.values(), key=lambda h: h.end)[-years:]
    url = CONCEPT_URL.format(cik=cik, concept=etiqueta)
    return [Datum(value=h.value, source="SEC EDGAR (XBRL)", as_of=h.end, url=url,
                  unit="acciones" if h.unit == "shares" else h.unit,
                  note=f"{etiqueta} · {h.form} presentada {h.filed}"
                       + ("" if h.unit in ("USD", "shares")
                          else f" · CIFRAS EN {h.unit}, NO en dólares"))
            for h in ordenados]


def fundamentals(ticker: str, *, fetcher: Fetcher | None = None,
                 years: int = 5) -> dict[str, Any]:
    """
    Recoge todo lo que §6.3 necesita para calcular, en una sola pasada.

    Los conceptos que falten se registran en `faltan` en vez de romper la
    consulta: casi ninguna empresa presenta los veintitantos conceptos, y una
    excepción por el primero que falte no dejaría analizar a nadie.
    """
    cik, nombre = resolve_cik(ticker, fetcher=fetcher)
    datos: dict[str, list[Datum]] = {}
    faltan: dict[str, str] = {}
    for concepto in CONCEPTS:
        try:
            datos[concepto] = annual_series(cik, concepto, fetcher=fetcher,
                                            years=years)
        except SourceError as e:
            faltan[concepto] = str(e)[:160]
    if not datos:
        raise SourceError(
            f"EDGAR no devolvió ningún fundamental para {ticker} (CIK {cik})")
    return {"ticker": ticker.upper(), "cik": cik, "nombre": nombre,
            "datos": datos, "faltan": faltan}


def render_fundamentals(paquete: dict[str, Any], limit: int = 5) -> str:
    """Tabla legible con la etiqueta XBRL de cada fila, para poder auditarla."""
    datos: dict[str, list[Datum]] = paquete["datos"]
    años = sorted({d.as_of[:4] for serie in datos.values() for d in serie})[-limit:]

    # La cabecera decía "millones de USD" pasara lo que pasara. Se lee de los
    # datos: un emisor extranjero con 20-F presenta en su moneda.
    monedas = sorted({d.unit for serie in datos.values() for d in serie
                      if d.unit not in ("acciones", "shares")})
    divisa = monedas[0] if len(monedas) == 1 else "/".join(monedas) or "USD"

    out = [f"{paquete['nombre']} ({paquete['ticker']}) — CIK {paquete['cik']}",
           f"Fuente: SEC EDGAR XBRL, cifras en millones de {divisa} salvo "
           f"indicación",
           "", "concepto".ljust(24) + "".join(a.rjust(13) for a in años)
           + "   etiqueta XBRL", "-" * (24 + 13 * len(años) + 20)]

    for concepto, serie in datos.items():
        por_año = {d.as_of[:4]: d for d in serie}
        if not any(a in por_año for a in años):
            continue
        celdas = ""
        for a in años:
            d = por_año.get(a)
            if d is None:
                celdas += "—".rjust(13)
            elif concepto == "acciones_diluidas":
                celdas += f"{float(d.value) / 1e6:,.0f}M".rjust(13)
            else:
                celdas += f"{float(d.value) / 1e6:,.0f}".rjust(13)
        etiqueta = serie[-1].note.split(" · ")[0]
        out.append(concepto.ljust(24) + celdas + "   " + etiqueta)

    if paquete.get("faltan"):
        out += ["", f"No presentados o con otra etiqueta: "
                f"{', '.join(sorted(paquete['faltan']))}"]
    out += ["", "Periodos deduplicados por (inicio, fin) conservando la "
            "presentación más reciente: las 10-K repiten el ejercicio anterior "
            "como comparativa y sumarlos sin deduplicar los cuenta dos veces."]
    return "\n".join(out)
