"""
Macro y geopolítica desde fuentes duras (Plan MAGI 9.0 §6.2).

"Datos duros, no titulares." Un titular te dice que la inflación preocupa; la
serie de FRED te dice que pasó del 3,1 % al 2,7 % en cuatro meses. Solo una de
las dos cosas se puede contrastar.

TRES FUENTES, CERO CLAVES
=========================
    FRED    fred.stlouisfed.org/graph/fredgraph.csv   series de EE. UU.
    ECB     data-api.ecb.europa.eu                    tipos de cambio y zona euro
    WB      api.worldbank.org/v2                      comparativa entre países

CATÁLOGO DE INDICADORES
=======================
`NY.GDP.MKTP.CD` no se adivina. Sin un catálogo, un agente pidiendo "el PIB de
España" tiene que inventarse el código, se equivoca, y la API devuelve una
lista vacía que parece "no hay datos" en vez de "preguntaste mal". Por eso los
nombres legibles se traducen aquí y un nombre desconocido produce un error que
enumera lo que sí existe.

DEGRADACIÓN HONESTA
===================
World Bank tiene cortes con regularidad. La regla es que una fuente caída
produzca `SourceError` con el motivo, nunca una lista vacía que el enjambre
pueda leer como "el indicador vale cero". El silencio es la peor respuesta
posible para un sistema que va a razonar encima.
"""
from __future__ import annotations

import csv
import io
import json
import logging
from typing import Any

from .sources import Datum, Fetcher, SourceError, default_fetcher

logger = logging.getLogger(__name__)

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
ECB_CSV = ("https://data-api.ecb.europa.eu/service/data/{flow}/{key}"
           "?lastNObservations={n}&format=csvdata")
# `mrv` y NO `mrnev`. La API rechaza con HTTP 400 dos cosas que la URL
# anterior hacía a la vez: combinar `per_page` con `mrnev`, y pedir `mrnev`
# para varios países. Comprobado contra api.worldbank.org: la forma anterior
# devolvía 400 SIEMPRE, con uno o con tres países, así que `compare_countries`
# —herramienta expuesta al enjambre— no ha funcionado nunca. Los nulos que
# `mrnev` evitaba los filtra igual el bucle de más abajo.
#
# `per_page` cuenta filas TOTALES, no por país: con `per_page=1` y tres países
# volvía uno solo, y la «comparativa» habría salido de un país sin avisar.
WB_JSON = ("https://api.worldbank.org/v2/country/{iso}/indicator/{ind}"
           "?format=json&per_page={page}&mrv={n}")

# Series de FRED que de verdad se usan al razonar sobre macro de EE. UU.
FRED_SERIES: dict[str, tuple[str, str]] = {
    "paro":                  ("UNRATE", "%"),
    "inflacion":             ("CPIAUCSL", "índice"),
    "inflacion_subyacente":  ("CPILFESL", "índice"),
    "pce_subyacente":        ("PCEPILFE", "índice"),
    "tipo_fed":              ("DFF", "%"),
    "bono_10a":              ("DGS10", "%"),
    "bono_2a":               ("DGS2", "%"),
    "curva_10a_2a":          ("T10Y2Y", "puntos %"),
    "pib_real":              ("GDPC1", "MM USD 2017"),
    "masa_monetaria_m2":     ("M2SL", "MM USD"),
    "petroleo_wti":          ("DCOILWTICO", "USD/barril"),
    "indice_dolar":          ("DTWEXBGS", "índice"),
    "expectativa_inflacion_5a": ("T5YIE", "%"),
    "viviendas_iniciadas":   ("HOUST", "miles"),
    "peticiones_desempleo":  ("ICSA", "personas"),
    "spread_alto_rendimiento": ("BAMLH0A0HYM2", "puntos %"),
}

# Indicadores del Banco Mundial: lo que permite COMPARAR países.
WB_INDICATORS: dict[str, tuple[str, str]] = {
    "pib":                ("NY.GDP.MKTP.CD", "USD"),
    "pib_per_capita":     ("NY.GDP.PCAP.CD", "USD"),
    "pib_crecimiento":    ("NY.GDP.MKTP.KD.ZG", "%"),
    "inflacion_anual":    ("FP.CPI.TOTL.ZG", "%"),
    "paro_total":         ("SL.UEM.TOTL.ZS", "% pobl. activa"),
    "poblacion":          ("SP.POP.TOTL", "personas"),
    "deuda_publica":      ("GC.DOD.TOTL.GD.ZS", "% del PIB"),
    "gasto_militar":      ("MS.MIL.XPND.GD.ZS", "% del PIB"),
    "exportaciones":      ("NE.EXP.GNFS.ZS", "% del PIB"),
    "gasto_id":           ("GB.XPD.RSDV.GD.ZS", "% del PIB"),
    "energia_renovable":  ("EG.FEC.RNEW.ZS", "% del consumo"),
    "esperanza_vida":     ("SP.DYN.LE00.IN", "años"),
}


def _unknown(name: str, catalog: dict, que: str) -> SourceError:
    return SourceError(
        f"{que} desconocido: '{name}'. Disponibles: {', '.join(sorted(catalog))}")


# ------------------------------------------------------------------------ FRED

def fred_series(name: str, *, fetcher: Fetcher | None = None,
                limit: int = 24) -> list[Datum]:
    """
    Serie de FRED por nombre legible. El CSV público no pide clave.

    El CSV trae huecos reales —festivos en las series diarias salen con el
    valor vacío— y saltárselos es obligatorio: interpretarlos como cero
    convierte un día festivo en un desplome del bono a 10 años.
    """
    if name not in FRED_SERIES:
        raise _unknown(name, FRED_SERIES, "serie de FRED")
    sid, unit = FRED_SERIES[name]
    url = FRED_CSV.format(sid=sid)
    kind = "tipo_interes" if "bono" in name or "tipo" in name else "macro"
    body = (fetcher or default_fetcher()).get(url, kind)

    if not body.lstrip().lower().startswith("observation_date"):
        raise SourceError(
            f"FRED devolvió algo que no es su CSV para {sid} "
            f"(¿bloqueo o mantenimiento?): {body[:120]!r}")

    out: list[Datum] = []
    for row in csv.DictReader(io.StringIO(body)):
        raw = (row.get(sid) or "").strip()
        fecha = (row.get("observation_date") or "").strip()
        if not raw or raw == "." or not fecha:
            continue                      # hueco real: festivo o no publicado
        try:
            val = float(raw)
        except ValueError:
            continue
        out.append(Datum(value=val, source="FRED (Reserva Federal de St. Louis)",
                         as_of=fecha, url=url, unit=unit,
                         note=f"serie {sid}"))
    if not out:
        raise SourceError(f"FRED devolvió el CSV de {sid} sin observaciones útiles")
    return out[-limit:]


# ------------------------------------------------------------------------- ECB

def ecb_series(flow: str, key: str, *, fetcher: Fetcher | None = None,
               n: int = 12) -> list[Datum]:
    """
    Serie del BCE en formato SDMX-CSV.

    Se parsea con el módulo `csv` y no partiendo por comas: la columna
    TITLE_COMPL trae comas dentro de comillas y un split ingenuo desplaza
    todas las columnas siguientes.
    """
    url = ECB_CSV.format(flow=flow, key=key, n=n)
    body = (fetcher or default_fetcher()).get(url, "tipo_cambio")
    rows = list(csv.DictReader(io.StringIO(body)))
    if not rows:
        raise SourceError(f"BCE sin observaciones para {flow}/{key}")

    out: list[Datum] = []
    for r in rows:
        raw = (r.get("OBS_VALUE") or "").strip()
        fecha = (r.get("TIME_PERIOD") or "").strip()
        if not raw or not fecha:
            continue
        try:
            val = float(raw)
        except ValueError:
            continue
        out.append(Datum(value=val, source="Banco Central Europeo",
                         as_of=fecha, url=url,
                         unit=(r.get("UNIT") or "").strip(),
                         note=(r.get("TITLE") or "").strip()))
    if not out:
        raise SourceError(f"BCE devolvió filas sin valores para {flow}/{key}")
    return out


def eur_usd(*, fetcher: Fetcher | None = None, n: int = 5) -> list[Datum]:
    """Tipo de cambio de referencia EUR/USD del BCE."""
    return ecb_series("EXR", "D.USD.EUR.SP00.A", fetcher=fetcher, n=n)


# ---------------------------------------------------------------- Banco Mundial

def worldbank(indicator: str, countries: list[str] | str, *,
              fetcher: Fetcher | None = None, n: int = 1) -> list[Datum]:
    """
    Indicador del Banco Mundial para uno o varios países.

    `mrnev=n` pide las n observaciones más recientes CON valor, que es lo que
    casi siempre se quiere: sin eso los últimos años vuelven con `value: null`
    porque aún no están publicados, y una serie que acaba en nulos se lee como
    una caída a cero.
    """
    if indicator not in WB_INDICATORS:
        raise _unknown(indicator, WB_INDICATORS, "indicador del Banco Mundial")
    ind, unit = WB_INDICATORS[indicator]
    lista = countries if isinstance(countries, list) else [countries]
    iso = ";".join(lista)
    url = WB_JSON.format(iso=iso, ind=ind, n=max(n, 1),
                         page=max(max(n, 1) * len(lista), 50))
    body = (fetcher or default_fetcher()).get(url, "macro")

    try:
        payload: Any = json.loads(body)
    except json.JSONDecodeError as e:
        raise SourceError(f"Banco Mundial no devolvió JSON: {body[:120]!r}") from e

    # Forma: [meta, [observaciones]] — o [meta] a secas si no hay datos.
    if not isinstance(payload, list) or not payload:
        raise SourceError(f"Banco Mundial: respuesta inesperada para {ind}")
    if len(payload) < 2 or not payload[1]:
        msg = ""
        if isinstance(payload[0], dict):
            msg = payload[0].get("message", [{}])[0].get("value", "") \
                if isinstance(payload[0].get("message"), list) else ""
        raise SourceError(
            f"Banco Mundial no tiene datos de {indicator} para '{iso}'"
            + (f": {msg}" if msg else "")
            + " (¿código de país mal escrito? usa ISO-3: ESP, USA, CHN)")

    out: list[Datum] = []
    for obs in payload[1]:
        if not isinstance(obs, dict) or obs.get("value") is None:
            continue                       # aún no publicado: se omite, no vale 0
        pais = (obs.get("country") or {}).get("value", "?")
        out.append(Datum(
            value=obs["value"], source="Banco Mundial", as_of=str(obs.get("date", "")),
            url=url, unit=unit, note=f"{pais} · {indicator}"))
    if not out:
        raise SourceError(
            f"Banco Mundial devolvió solo valores nulos para {indicator}/{iso}: "
            f"el indicador existe pero no está publicado para ese país")

    # Una comparativa a la que le falta un país no es la comparativa que se
    # pidió. Antes se devolvía igual y nadie se enteraba.
    if len(lista) > 1:
        vistos = {(o.get("countryiso3code") or "").upper()
                  for o in payload[1] if isinstance(o, dict)}
        faltan = [c for c in lista if c.upper() not in vistos]
        if faltan:
            logger.warning("[macro] el Banco Mundial no devolvió %s para %s",
                           faltan, indicator)
            out.append(Datum(
                value=0.0, source="Banco Mundial", as_of=out[-1].as_of, url=url,
                unit=unit,
                note=f"AVISO: sin datos de {', '.join(faltan)} para "
                     f"{indicator}; la comparativa NO los incluye"))
    return out


# ---------------------------------------------------------------------- lectura

def macro_snapshot(*, fetcher: Fetcher | None = None,
                   series: list[str] | None = None) -> str:
    """
    Foto del estado macro de EE. UU. con la fecha de cada dato.

    Tolerante a fallos por diseño: una serie caída se marca como no disponible
    y las demás siguen. Un panel que desaparece entero porque una fuente falló
    es un panel que no se usa.
    """
    series = series or ["paro", "tipo_fed", "bono_10a", "bono_2a",
                        "curva_10a_2a", "expectativa_inflacion_5a",
                        "spread_alto_rendimiento"]
    lineas = ["ESTADO MACRO (EE. UU.) — cada cifra con su fecha", ""]
    fallos = 0
    for s in series:
        try:
            d = fred_series(s, fetcher=fetcher, limit=1)[-1]
            edad = d.staleness_days
            aviso = "  ⚠ dato antiguo" if edad is not None and edad > 45 else ""
            lineas.append(f"  {s:<26s} {d.value:>10.2f} {d.unit:<10s} "
                          f"({d.as_of}){aviso}")
        except SourceError as e:
            fallos += 1
            lineas.append(f"  {s:<26s} {'NO DISPONIBLE':>10s}  — {e}")
    lineas += ["", "Fuente: FRED, Reserva Federal de St. Louis. "
               "Series sin clave de API."]
    if fallos:
        lineas.append(f"AVISO: {fallos} de {len(series)} series no respondieron. "
                      f"No trates los huecos como ceros.")
    return "\n".join(lineas)


def compare_countries(indicator: str, countries: list[str], *,
                      fetcher: Fetcher | None = None) -> str:
    """Contraste entre países sobre un indicador, con el año de cada cifra."""
    try:
        data = worldbank(indicator, countries, fetcher=fetcher, n=1)
    except SourceError as e:
        return f"No se pudo comparar {indicator}: {e}"

    unit = data[0].unit
    lineas = [f"{indicator.upper()} ({unit}) — Banco Mundial", ""]
    for d in sorted(data, key=lambda x: -float(x.value)):
        pais = d.note.split(" · ")[0]
        lineas.append(f"  {pais:<28s} {float(d.value):>18,.2f}   ({d.as_of})")
    años = {d.as_of for d in data}
    if len(años) > 1:
        lineas += ["", f"AVISO: las cifras no son del mismo año ({', '.join(sorted(años))}). "
                   f"Comparar años distintos como si fueran el mismo es el error "
                   f"más común con estos datos."]
    return "\n".join(lineas)
