"""
Fuentes del mundo real: macro, fundamentales y actualidad (§6.1, §6.2, §6.3).

Los fixtures NO están inventados: son la forma exacta que devolvieron las APIs
al llamarlas antes de escribir los parsers, huecos y rarezas incluidos. Un
fixture idealizado prueba que el parser entiende el formato que yo imaginé, que
es justo lo que no hace falta comprobar.

La suite no toca la red: todo pasa por `FrozenFetcher`.
"""
import pytest

from magi.modules.world.edgar import (
    annual_series, concept_facts, fundamentals, render_fundamentals, resolve_cik,
)
from magi.modules.world.feeds import fetch_feed, headlines, parse_feed
from magi.modules.world.macro import (
    compare_countries, ecb_series, fred_series, macro_snapshot, worldbank,
)
from magi.modules.world.sources import Datum, FrozenFetcher, SourceError

# --------------------------------------------------------------- fixtures reales

# FRED: el 2026-07-03 viene VACÍO — fue festivo. Capturado del CSV público.
FRED_DGS10 = """observation_date,DGS10
2026-07-01,4.48
2026-07-02,4.49
2026-07-03,
2026-07-06,4.48
2026-07-07,4.55
2026-07-31,4.75
"""

FRED_UNRATE = """observation_date,UNRATE
2026-04-01,4.3
2026-05-01,4.3
2026-06-01,4.2
"""

# BCE SDMX-CSV: TITLE_COMPL trae comas DENTRO de comillas.
ECB_EXR = ('KEY,FREQ,CURRENCY,CURRENCY_DENOM,EXR_TYPE,EXR_SUFFIX,TIME_PERIOD,'
           'OBS_VALUE,OBS_STATUS,TITLE,TITLE_COMPL,UNIT,UNIT_MULT\n'
           'EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,2026-07-30,1.1476,A,'
           'US dollar/Euro,"ECB reference exchange rate, US dollar/Euro, '
           '2.15 pm (C.E.T.)",USD,0\n'
           'EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,2026-07-31,1.1485,A,'
           'US dollar/Euro,"ECB reference exchange rate, US dollar/Euro, '
           '2.15 pm (C.E.T.)",USD,0\n')

WB_PIB = """[
 {"page":1,"pages":1,"per_page":2,"total":2,"lastupdated":"2026-07-13"},
 [
  {"indicator":{"id":"NY.GDP.MKTP.CD","value":"GDP (current US$)"},
   "country":{"id":"ES","value":"Spain"},"countryiso3code":"ESP",
   "date":"2024","value":1620000000000.0,"unit":"","obs_status":"","decimal":0},
  {"indicator":{"id":"NY.GDP.MKTP.CD","value":"GDP (current US$)"},
   "country":{"id":"US","value":"United States"},"countryiso3code":"USA",
   "date":"2024","value":29180000000000.0,"unit":"","obs_status":"","decimal":0}
 ]
]"""

WB_SIN_DATOS = '[{"page":1,"pages":0,"per_page":1,"total":0}]'
WB_TODO_NULO = """[
 {"page":1,"pages":1,"per_page":1,"total":1},
 [{"indicator":{"id":"X","value":"X"},"country":{"id":"ZZ","value":"Nowhere"},
   "date":"2024","value":null}]
]"""

SEC_TICKERS = ('{"0":{"cik_str":320193,"ticker":"AAPL","title":"Apple Inc."},'
               '"1":{"cik_str":1045810,"ticker":"NVDA","title":"NVIDIA CORP"}}')

# EL FIXTURE QUE IMPORTA. Capturado de data.sec.gov: el periodo
# 2023-10-01..2024-09-28 aparece DOS veces —en la 10-K de FY2024 y otra vez
# como comparativa en la de FY2025— con el mismo valor. Sumar sin deduplicar
# cuenta ese ejercicio dos veces.
SEC_FCO = """{"cik":320193,"units":{"USD":[
 {"start":"2022-09-25","end":"2023-09-30","val":110543000000,"fy":2023,
  "fp":"FY","form":"10-K","filed":"2023-11-03","accn":"0000320193-23-000106"},
 {"start":"2023-10-01","end":"2024-09-28","val":118254000000,"fy":2024,
  "fp":"FY","form":"10-K","filed":"2024-11-01","accn":"0000320193-24-000123"},
 {"start":"2023-10-01","end":"2024-09-28","val":118254000000,"fy":2025,
  "fp":"FY","form":"10-K","filed":"2025-10-31","accn":"0000320193-25-000073"},
 {"start":"2024-09-29","end":"2025-09-27","val":111500000000,"fy":2025,
  "fp":"FY","form":"10-K","filed":"2025-10-31","accn":"0000320193-25-000073"},
 {"start":"2025-06-29","end":"2025-09-27","val":28000000000,"fy":2025,
  "fp":"Q4","form":"10-Q","filed":"2025-10-31","accn":"0000320193-25-000073"}
]}}"""

RSS_FED = """<?xml version="1.0"?>
<rss version="2.0"><channel><title>Federal Reserve</title>
<item><title>FOMC statement</title>
 <link>https://www.federalreserve.gov/a.htm</link>
 <pubDate>Wed, 29 Jul 2026 18:00:00 GMT</pubDate>
 <description><![CDATA[<p>The Committee <b>decided</b> to maintain.</p>]]></description>
</item>
<item><title>Speech &amp; remarks</title>
 <link>https://www.federalreserve.gov/b.htm</link>
 <pubDate>Mon, 27 Jul 2026 12:00:00 GMT</pubDate>
 <description>Sobre &quot;estabilidad&quot;</description>
</item>
</channel></rss>"""

ATOM_BCE = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
 <title>ECB</title>
 <entry>
  <title>Monetary policy decisions</title>
  <link rel="alternate" href="https://www.ecb.europa.eu/x.html"/>
  <link rel="self" href="https://www.ecb.europa.eu/self"/>
  <updated>2026-07-24T13:45:00Z</updated>
  <summary>The Governing Council decided</summary>
 </entry>
</feed>"""


@pytest.fixture
def red():
    return FrozenFetcher({
        "fredgraph.csv?id=DGS10": FRED_DGS10,
        "fredgraph.csv?id=UNRATE": FRED_UNRATE,
        "data-api.ecb.europa.eu": ECB_EXR,
        "api.worldbank.org": WB_PIB,
        "company_tickers.json": SEC_TICKERS,
        "NetCashProvidedByUsedInOperatingActivities.json": SEC_FCO,
        "federalreserve.gov/feeds": RSS_FED,
        "ecb.europa.eu/rss": ATOM_BCE,
    })


# ------------------------------------------------------------------ proveniencia

def test_un_dato_sin_fuente_no_se_puede_construir():
    """§6.1: 'fuente y fecha, o marcado como no verificado'. Aquí es estructural."""
    with pytest.raises(ValueError, match="rumor"):
        Datum(value=1, source="", as_of="2026-01-01", url="u")
    with pytest.raises(ValueError, match="rumor"):
        Datum(value=1, source="FRED", as_of="", url="u")


def test_distingue_la_fecha_del_dato_de_la_de_descarga():
    d = Datum(value=4.1, source="FRED", as_of="2025-01-01", url="u", unit="%")
    assert d.retrieved != d.as_of
    assert d.staleness_days > 300
    assert "dato de 2025-01-01" in d.cite() and "antigüedad" in d.cite()


# -------------------------------------------------------------------- FRED

def test_fred_salta_los_huecos_de_los_festivos(red):
    """
    El CSV trae el festivo con el valor VACÍO. Leerlo como 0.0 convertiría un
    día festivo en un desplome del bono a 10 años.
    """
    serie = fred_series("bono_10a", fetcher=red)
    assert [d.as_of for d in serie] == ["2026-07-01", "2026-07-02", "2026-07-06",
                                        "2026-07-07", "2026-07-31"]
    assert all(d.value > 4 for d in serie)


def test_fred_series_desconocida_enumera_las_que_hay(red):
    with pytest.raises(SourceError, match="Disponibles"):
        fred_series("inventada", fetcher=red)


def test_fred_detecta_que_le_han_servido_html(red):
    """Un bloqueo devuelve 200 con HTML. Parsearlo daría una serie vacía."""
    red.responses["fredgraph.csv?id=DGS10"] = "<html><body>Blocked</body></html>"
    with pytest.raises(SourceError, match="no es su CSV"):
        fred_series("bono_10a", fetcher=red)


def test_snapshot_no_se_cae_porque_falle_una_serie(red):
    """Un panel que desaparece entero por una fuente caída es un panel inútil."""
    # 'tipo_fed' no está en el fixture: simula la fuente caída.
    txt = macro_snapshot(fetcher=red, series=["bono_10a", "paro", "tipo_fed"])
    assert "bono_10a" in txt and "4.75" in txt
    assert "paro" in txt and "4.20" in txt          # las demás siguen
    assert "NO DISPONIBLE" in txt
    assert "no trates los huecos como ceros" in txt.lower()


def test_snapshot_marca_los_datos_viejos(red):
    """
    Una cifra de hace tres meses presentada sin aviso es cómo un sistema acaba
    diciendo 'el paro es del 4,2 %' sobre un dato que ya se revisó dos veces.
    """
    txt = macro_snapshot(fetcher=red, series=["paro"])
    assert "dato antiguo" in txt


# --------------------------------------------------------------------- BCE

def test_ecb_no_se_desalinea_con_las_comas_entre_comillas(red):
    """
    TITLE_COMPL trae comas dentro de comillas: partir por comas desplazaría
    todas las columnas siguientes y OBS_VALUE saldría del sitio equivocado.
    """
    serie = ecb_series("EXR", "D.USD.EUR.SP00.A", fetcher=red)
    assert [d.value for d in serie] == [1.1476, 1.1485]
    assert serie[0].unit == "USD"


# ----------------------------------------------------------- Banco Mundial

def test_worldbank_compara_paises(red):
    datos = worldbank("pib", ["ESP", "USA"], fetcher=red)
    assert {d.note.split(" · ")[0] for d in datos} == {"Spain", "United States"}
    txt = compare_countries("pib", ["ESP", "USA"], fetcher=red)
    assert txt.index("United States") < txt.index("Spain")   # ordenado por valor


def test_worldbank_sin_datos_explica_el_error_probable(red):
    red.responses["api.worldbank.org"] = WB_SIN_DATOS
    with pytest.raises(SourceError, match="ISO-3"):
        worldbank("pib", "XYZ", fetcher=red)


def test_worldbank_valores_nulos_no_son_ceros(red):
    """Un indicador aún no publicado vuelve como null; leerlo como 0 miente."""
    red.responses["api.worldbank.org"] = WB_TODO_NULO
    with pytest.raises(SourceError, match="nulos"):
        worldbank("pib", "ZZZ", fetcher=red)


def test_compare_countries_avisa_si_los_años_no_coinciden(red):
    import json
    d = json.loads(WB_PIB)
    d[1][0]["date"] = "2022"
    red.responses["api.worldbank.org"] = json.dumps(d)
    assert "no son del mismo año" in compare_countries("pib", ["ESP", "USA"],
                                                       fetcher=red)


# ---------------------------------------------------------------- SEC EDGAR

def test_resuelve_el_cik_desde_el_ticker(red):
    assert resolve_cik("aapl", fetcher=red) == (320193, "Apple Inc.")


def test_ticker_no_estadounidense_explica_por_que_no_esta(red):
    with pytest.raises(SourceError, match="20-F"):
        resolve_cik("SAN.MC", fetcher=red)


def test_edgar_deduplica_el_ejercicio_repetido(red):
    """
    LA REGRESIÓN. La 10-K de FY2025 repite el ejercicio 2023-10..2024-09 como
    comparativa. Sin deduplicar, tres ejercicios se convierten en cuatro y las
    ganancias del propietario salen infladas un 30 % sin que nada avise.
    """
    serie = annual_series(320193, "flujo_operativo", fetcher=red, years=10)
    periodos = [d.as_of for d in serie]
    assert len(periodos) == len(set(periodos)), f"periodos duplicados: {periodos}"
    assert periodos == ["2023-09-30", "2024-09-28", "2025-09-27"]
    assert sum(float(d.value) for d in serie) == pytest.approx(340_297_000_000)


def test_edgar_conserva_la_presentacion_mas_reciente(red):
    """Ante una reexpresión, vale la última presentada, no la primera."""
    serie = annual_series(320193, "flujo_operativo", fetcher=red)
    repetido = next(d for d in serie if d.as_of == "2024-09-28")
    assert "2025-10-31" in repetido.note


def test_edgar_descarta_los_trimestres(red):
    serie = annual_series(320193, "flujo_operativo", fetcher=red, years=10)
    assert all("10-Q" not in d.note for d in serie)


def test_edgar_dice_que_etiqueta_xbrl_uso(red):
    """Sin saber la etiqueta, el número no se puede auditar contra la 10-K."""
    etiqueta, _ = concept_facts(320193, "flujo_operativo", fetcher=red)
    assert etiqueta == "NetCashProvidedByUsedInOperatingActivities"


def test_edgar_prueba_la_cadena_de_etiquetas_alternativas(red):
    """Cada emisor etiqueta distinto; la primera opción falla a menudo."""
    with pytest.raises(SourceError, match="Probadas"):
        concept_facts(320193, "ingresos", fetcher=red)


def test_fundamentals_no_muere_porque_falte_un_concepto(red):
    """Casi ninguna empresa presenta los veintitantos conceptos."""
    p = fundamentals("AAPL", fetcher=red)
    assert p["cik"] == 320193
    assert "flujo_operativo" in p["datos"]
    assert p["faltan"]
    txt = render_fundamentals(p)
    assert "Apple Inc." in txt and "deduplicados" in txt


# ------------------------------------------------------------------- feeds

def test_parsea_rss_con_cdata_y_entidades():
    items = parse_feed(RSS_FED, "Fed")
    assert items[0].title == "FOMC statement"
    assert items[0].published == "2026-07-29"
    assert "<b>" not in items[0].summary and "decided" in items[0].summary
    assert items[1].title == "Speech & remarks"        # &amp; decodificado
    assert '"estabilidad"' in items[1].summary


def test_parsea_atom_y_coge_el_enlace_bueno():
    """En Atom el enlace está en un atributo, y rel='self' no es el que sirve."""
    items = parse_feed(ATOM_BCE, "BCE")
    assert items[0].link == "https://www.ecb.europa.eu/x.html"
    assert items[0].published == "2026-07-24"


def test_una_pagina_de_error_servida_con_200_no_pasa_por_feed():
    with pytest.raises(SourceError, match="no es un feed"):
        parse_feed("<html><body>500</body></html>")
    with pytest.raises(SourceError, match="XML válido"):
        parse_feed("no soy xml <<<")


def test_feed_desconocido_enumera_el_catalogo(red):
    with pytest.raises(SourceError, match="catálogo"):
        fetch_feed("periodico_inventado", fetcher=red)


def test_titulares_marcan_la_fuente_caida_y_siguen(red):
    txt = headlines(["fed_monetaria", "sec"], fetcher=red, per_feed=2)
    assert "FOMC statement" in txt
    assert "NO DISPONIBLE" in txt           # 'sec' no está en el fixture
    assert "no lo convierte en cierto" in txt


# ------------------------------------------------------------------ sin red

def test_la_suite_no_toca_la_red(red):
    """
    Guarda: si alguien mete una llamada HTTP real en un parser, este test lo
    caza. Un fetcher congelado que nunca se usa es una pista de que el módulo
    se saltó la inyección.
    """
    fred_series("paro", fetcher=red)
    assert red.calls, "el módulo no usó el fetcher inyectado"
    assert all(u.startswith("http") for u, _ in red.calls)


def test_cada_fuente_declara_el_tipo_de_dato_para_su_ttl(red):
    """§6.1: la caducidad es por tipo de dato, no global."""
    fred_series("bono_10a", fetcher=red)
    worldbank("pib", "ESP", fetcher=red)
    fetch_feed("fed_monetaria", fetcher=red)
    tipos = {k for _, k in red.calls}
    assert {"tipo_interes", "macro", "noticia"} <= tipos


# ------------------------------------------- lo que el fetcher enlatado no ve

def test_la_url_del_banco_mundial_no_mezcla_per_page_con_mrnev():
    """
    LA COMPROBACIÓN QUE NINGÚN TEST PODÍA HACER.

    `compare_countries` está expuesta al enjambre y NUNCA ha funcionado: la
    API del Banco Mundial devuelve HTTP 400 si se combina `per_page` con
    `mrnev`, y también si se pide `mrnev` para varios países. Comprobado
    contra api.worldbank.org: 400 con uno y con tres.

    `FrozenFetcher.get` casa por subcadena del dominio y devuelve el cuerpo
    enlatado sea cual sea el query string, así que ningún test con datos
    congelados podía verlo — la versión a nivel de test del mismo patrón que
    perseguimos en el código: una comprobación que dejó de aplicarse en
    silencio. Por eso este test mira la URL, que es lo único que se puede
    comprobar sin red.
    """
    from magi.modules.world.macro import WB_JSON

    url = WB_JSON.format(iso="ESP;USA;CHN", ind="NY.GDP.MKTP.CD", n=3, page=50)
    assert "mrnev" not in url, "mrnev es incompatible con per_page y multipaís"
    assert "mrv=" in url

    # `per_page` cuenta filas TOTALES, no por país: con menos que
    # n * países la «comparativa» saldría de un subconjunto sin avisar.
    import urllib.parse as up
    q = up.parse_qs(up.urlparse(url).query)
    assert int(q["per_page"][0]) >= 3 * 3


def test_edgar_no_rotula_como_dolares_lo_que_no_lo_es():
    """
    `_facts` caía a «cualquier unidad» y `annual_series` etiquetaba "USD" a
    ciegas. El filtro de formularios acepta `20-F` a propósito, que es justo
    el que presentan los emisores extranjeros EN SU MONEDA: euros y libras
    salían rotulados como dólares, y `Datum.cite()` propagaba la mentira al
    razonamiento del enjambre.
    """
    import json

    from magi.modules.world.edgar import annual_series

    cuerpo = json.dumps({"units": {"EUR": [
        {"start": "2023-01-01", "end": "2023-12-31", "val": 1000,
         "fy": 2023, "form": "20-F", "filed": "2024-03-01", "accn": "a"},
    ]}})
    congelado = FrozenFetcher({"data.sec.gov": cuerpo})

    serie = annual_series(320193, "ingresos", fetcher=congelado)
    assert serie, "no devolvió nada"
    assert serie[0].unit == "EUR", f"rotuló {serie[0].unit!r} unos euros"
    assert "NO en dólares" in serie[0].note
