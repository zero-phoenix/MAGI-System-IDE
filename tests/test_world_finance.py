"""
Aritmética financiera determinista y registro de tesis (§6.3).

La regla del plan es que el LLM no calcula. Estos tests comprueban que lo que
calcula el código es correcto Y que se niega a calcular cuando los supuestos
no lo permiten — que es la mitad que casi nadie prueba y donde salen los
números absurdos presentados con cara de tasación.
"""
import pytest

from magi.modules.world.finance import (
    DCFAssumptions, FinanceError, cash_conversion, dcf, dcf_sensitivity,
    dilution, leverage, maintenance_capex, owner_earnings, quality_checklist,
    roic,
)
from magi.modules.world.thesis import ThesisError, ThesisLog


# ------------------------------------------------- ganancias del propietario

def test_owner_earnings_es_fco_menos_mantenimiento():
    oe = owner_earnings(100_000, 30_000)
    assert oe.value == 70_000
    assert "flujo_caja_operativo" in oe.formula


def test_capex_mantenimiento_greenwald_excluye_el_crecimiento():
    """
    Con ingresos creciendo, parte del capex sostiene el crecimiento y no el
    negocio actual: las ganancias del propietario no deben cargar con él.
    """
    mc = maintenance_capex(capex=100.0, depreciation=40.0,
                           revenue=[1000.0, 1200.0], ppe=600.0)
    # intensidad = 600/1200 = 0.5 ; crecimiento = 200 ; capex_crec = 100
    assert mc.value == pytest.approx(0.0)
    assert "Greenwald" in mc.note


def test_capex_mantenimiento_cae_al_proxy_y_lo_dice():
    mc = maintenance_capex(capex=100.0, depreciation=40.0)
    assert mc.value == 40.0
    assert "amortización" in mc.note or "amortizacion" in mc.note


def test_capex_llega_negativo_desde_edgar_y_se_normaliza():
    """EDGAR presenta el capex como pago; algunos emisores lo firman al revés."""
    assert maintenance_capex(-100.0, 40.0).value == 40.0


def test_el_calculo_se_puede_comprobar_a_mano():
    """
    La razón de ser de `Calc`: si no se puede rehacer con una calculadora, no
    vale. El render tiene que traer fórmula y entradas.
    """
    texto = owner_earnings(100.0, 30.0).render()
    assert "fórmula:" in texto and "entradas:" in texto
    assert "flujo_caja_operativo=100" in texto


# ------------------------------------------------------------------ ratios

def test_roic_usa_nopat_sobre_capital_invertido():
    r = roic(operating_income=200.0, tax_rate=0.21,
             total_assets=2000.0, current_liabilities=400.0)
    assert r.value == pytest.approx(200 * 0.79 / 1600)


def test_roic_se_niega_con_capital_invertido_no_positivo():
    """Devolver un ROIC negativo enorme sería peor que negarse."""
    with pytest.raises(FinanceError, match="capital invertido"):
        roic(200.0, 0.21, 500.0, 900.0)


def test_dilucion_detecta_recompra_real():
    d = dilution([1000.0, 980.0, 960.0, 940.0])
    assert d.value < 0


def test_dilucion_detecta_emision_encubierta():
    d = dilution([1000.0, 1020.0, 1045.0])
    assert d.value > 0


def test_dilucion_necesita_dos_ejercicios():
    with pytest.raises(FinanceError, match="dos ejercicios"):
        dilution([1000.0])


def test_apalancamiento_se_niega_con_ebitda_negativo():
    with pytest.raises(FinanceError, match="EBITDA"):
        leverage(1000.0, 100.0, -50.0)


def test_conversion_de_caja():
    assert cash_conversion(120.0, 100.0).value == pytest.approx(1.2)
    with pytest.raises(FinanceError):
        cash_conversion(120.0, 0.0)


# --------------------------------------------------------------------- DCF

def test_dcf_descuenta_de_verdad():
    """Un flujo constante descontado al 10 % vale menos que la suma nominal."""
    a = DCFAssumptions(growth=0.0, discount=0.10, terminal_growth=0.0, years=3)
    r = dcf(100.0, a)
    assert r.discounted[0] == pytest.approx(100 / 1.1)
    assert r.discounted[2] == pytest.approx(100 / 1.1 ** 3)
    assert sum(r.discounted) < 300


def test_dcf_rechaza_crecimiento_terminal_mayor_que_el_descuento():
    """
    Es el error clásico: con g >= r la fórmula de Gordon da infinito o
    negativo, y sin esta guarda saldría un valor de empresa NEGATIVO
    presentado con toda naturalidad.
    """
    with pytest.raises(FinanceError, match="Gordon"):
        dcf(100.0, DCFAssumptions(0.05, 0.08, 0.09))
    with pytest.raises(FinanceError, match="Gordon"):
        dcf(100.0, DCFAssumptions(0.05, 0.08, 0.08))


def test_dcf_rechaza_flujo_base_negativo():
    with pytest.raises(FinanceError, match="flujo base"):
        dcf(-50.0, DCFAssumptions(0.05, 0.10, 0.02))


def test_dcf_confiesa_cuanto_valor_es_terminal():
    """
    El dato incómodo: en un DCF típico el valor terminal es la mayoría del
    resultado, así que la 'proyección detallada' proyecta poco.
    """
    r = dcf(100.0, DCFAssumptions(0.05, 0.09, 0.025, years=10))
    assert 0.5 < r.terminal_share < 0.95


def test_sensibilidad_no_devuelve_un_numero_solo():
    txt = dcf_sensitivity(100.0, DCFAssumptions(0.05, 0.09, 0.025))
    assert txt.count("\n") > 5
    assert "valor terminal" in txt
    assert "%" in txt


def test_sensibilidad_marca_las_combinaciones_imposibles():
    """Al barrer la rejilla, algunas celdas violan g < r: deben decirlo."""
    txt = dcf_sensitivity(100.0, DCFAssumptions(0.05, 0.03, 0.02),
                          discounts=[0.03], terminals=[0.02, 0.05])
    assert "imposible" in txt


# --------------------------------------------------------------- checklist

def test_checklist_marca_lo_que_falla_y_por_que():
    txt = quality_checklist({
        "ROIC": 0.05, "conversión de caja": 1.2,
        "deuda neta / EBITDA": 4.5, "dilución anualizada": 0.03,
        "margen de explotación": 0.22})
    assert "destruye valor" in txt          # ROIC bajo
    assert "apalancamiento" in txt          # deuda alta
    assert "Cumple 2 de 5" in txt


def test_checklist_no_inventa_lo_que_no_sabe():
    txt = quality_checklist({"ROIC": 0.20})
    assert "sin dato" in txt
    assert "Cumple 1 de 1" in txt


# ------------------------------------------------------- registro de tesis

@pytest.fixture
def log(tmp_path):
    return ThesisLog(tmp_path / "tesis.db")


def test_registra_y_recupera(log):
    t = log.record("AAPL", "el margen bruto sigue por encima del 44 %", 0.7,
                   "poder de fijación de precios en servicios", 90,
                   ["SEC EDGAR 10-K FY2025"])
    assert log.get(t.thesis_id).claim.startswith("el margen")
    assert log.pending() and not log.due()


def test_rechaza_la_certeza_absoluta(log):
    """El 0 % y el 100 % no son grados de creencia; rompen la calibración."""
    for c in (0.0, 1.0, -0.1, 1.5):
        with pytest.raises(ThesisError, match="confianza"):
            log.record("X", "algo", c)


def test_rechaza_tesis_vacia_o_sin_futuro(log):
    with pytest.raises(ThesisError, match="afirmación"):
        log.record("X", "   ", 0.6)
    with pytest.raises(ThesisError, match="horizonte"):
        log.record("X", "algo", 0.6, horizon_days=0)


def test_resolver_es_irreversible(log):
    """Reescribir un resultado pasado vacía de sentido el registro entero."""
    t = log.record("X", "subirá", 0.6)
    log.resolve(t.thesis_id, True)
    with pytest.raises(ThesisError, match="ya se resolvió"):
        log.resolve(t.thesis_id, False)


def test_brier_penaliza_la_seguridad_equivocada(log):
    seguro = log.record("A", "a", 0.95)
    dudoso = log.record("B", "b", 0.55)
    log.resolve(seguro.thesis_id, False)
    log.resolve(dudoso.thesis_id, False)
    assert log.get(seguro.thesis_id).brier > log.get(dudoso.thesis_id).brier


def test_detecta_exceso_de_confianza(log):
    """
    Doce tesis al 90 % de las que solo aciertan la mitad: el veredicto tiene
    que nombrar el exceso de confianza, no limitarse a dar un número.
    """
    for i in range(12):
        t = log.record("S", f"afirmación {i}", 0.9)
        log.resolve(t.thesis_id, i % 2 == 0)
    s = log.brier_score()
    assert s["sesgo"] > 0.3
    assert "exceso de confianza" in s["veredicto"]


def test_detecta_defecto_de_confianza(log):
    for i in range(12):
        t = log.record("S", f"a{i}", 0.55)
        log.resolve(t.thesis_id, i != 0)      # acierta 11 de 12 diciendo 55 %
    assert log.brier_score()["sesgo"] < -0.1
    assert "defecto de confianza" in log.brier_score()["veredicto"]


def test_no_habla_de_calibracion_sin_muestra(log):
    """Tres tesis no son una calibración, y decir lo contrario es peor que callar."""
    for i in range(3):
        t = log.record("S", f"a{i}", 0.7)
        log.resolve(t.thesis_id, True)
    assert "no hay muestra" in log.brier_score()["veredicto"]


def test_brier_se_compara_contra_la_linea_base(log):
    """
    Un Brier bajo no vale nada si la tasa base ya lo daba. La comparación es
    obligatoria para no felicitarse por predecir lo obvio.
    """
    for i in range(20):
        t = log.record("S", f"a{i}", 0.9)
        log.resolve(t.thesis_id, True)       # siempre acierta: tasa base 100 %
    s = log.brier_score()
    assert s["brier_linea_base"] == 0.0
    assert s["mejora_sobre_base"] < 0
    assert "NO aporta" in s["veredicto"]


def test_avisa_de_tesis_vencidas_sin_puntuar(log):
    """
    El sesgo que destruye estos registros: solo se recuerda resolver lo que se
    acertó. Si hay vencidas sin puntuar, el informe tiene que decirlo.
    """
    import sqlite3
    t = log.record("S", "algo", 0.6, horizon_days=1)
    with sqlite3.connect(log.path) as c:      # envejecer sin esperar
        c.execute("UPDATE thesis_log SET horizon='2020-01-01' WHERE thesis_id=?",
                  (t.thesis_id,))
    otra = log.record("S", "otra", 0.6)
    log.resolve(otra.thesis_id, True)

    assert log.due() and log.due()[0].thesis_id == t.thesis_id
    assert "vencidas SIN puntuar" in log.calibration_curve()
    assert "VENCIDA" in log.render_pending()


def test_curva_de_calibracion_sin_datos_no_finge(log):
    assert "Sin tesis resueltas" in log.calibration_curve()
    assert log.brier_score()["n"] == 0
