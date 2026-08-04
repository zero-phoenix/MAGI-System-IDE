"""
Aritmética financiera determinista (Plan MAGI 9.0 §6.3).

LA REGLA DURA
=============
"Toda aritmética financiera se ejecuta en Python y se muestra la fórmula. El
LLM interpreta y argumenta; no calcula."

Esto no es purismo. Los modelos de lenguaje se equivocan en aritmética de
varios pasos con una frecuencia que en un descuento de flujos es inaceptable,
y —lo peor— se equivocan con la misma prosa segura con la que aciertan. Un
número mal calculado con una explicación convincente al lado es más peligroso
que no tener número.

Aquí cada resultado es un `Calc` que lleva su fórmula y sus entradas. Se puede
comprobar a mano. Si no se puede comprobar a mano, no sale.

LO QUE NO SE PUEDE CONSTRUIR
============================
Pediste "todas las habilidades de Warren Buffett". El plan §6.3 ya fue directo
y lo repito donde vive el código: el juicio de Buffett son sesenta años de
criterio, una red de contactos, acceso a operaciones privadas, capital
permanente y temperamento bajo pánico. Nada de eso es software.

Lo que sí es software es la contabilidad que él hace a mano y casi nadie hace:
ganancias del propietario, ROIC, dilución, conversión de caja, y un descuento
de flujos con sus supuestos a la vista. Eso está aquí, calculado de verdad.

Sustituye a `_attic/quant_simulator.py`, que devolvía `np.random.randint(60, 101)`
como "índice risk-off" ante un shock geopolítico. Un generador de números con
vocabulario financiero es peor que no tener nada, porque parece un análisis.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class FinanceError(ValueError):
    """Los supuestos no admiten el cálculo pedido."""


@dataclass(frozen=True)
class Calc:
    """
    Un número con su fórmula y sus entradas. Auditable a mano, por diseño.
    """
    name: str
    value: float
    formula: str
    inputs: dict[str, float]
    unit: str = ""
    note: str = ""

    def render(self) -> str:
        ent = ", ".join(f"{k}={v:,.4g}" for k, v in self.inputs.items())
        linea = f"{self.name}: {self.value:,.4g} {self.unit}".rstrip()
        return (f"{linea}\n    fórmula: {self.formula}\n    entradas: {ent}"
                + (f"\n    nota: {self.note}" if self.note else ""))


# --------------------------------------------------- ganancias del propietario

def maintenance_capex(capex: float, depreciation: float,
                      revenue: list[float] | None = None,
                      ppe: float | None = None) -> Calc:
    """
    Capex de mantenimiento — el número que Buffett usa y que nadie publica.

    No es observable: las empresas informan del capex total sin separar cuánto
    mantiene el negocio actual y cuánto lo hace crecer. Hay dos aproximaciones
    razonables y aquí se elige explícitamente, porque el resultado cambia y el
    lector tiene derecho a saber cuál se usó:

      · Greenwald: el capex de crecimiento es proporcional al aumento de
        ingresos, con la intensidad de inmovilizado del propio negocio.
        Requiere serie de ingresos y saldo de inmovilizado.
      · Amortización como proxy: más burda, pero es la que el propio Buffett
        usa como primera aproximación en la carta de 1986.

    Ninguna es "la verdad". Las dos son mejores que usar el capex total, que
    infravalora las ganancias del propietario de cualquier empresa en
    crecimiento.
    """
    if capex < 0:
        capex = abs(capex)          # EDGAR lo presenta como pago (positivo)

    if revenue and len(revenue) >= 2 and ppe and revenue[-2] > 0:
        crecimiento = revenue[-1] - revenue[-2]
        intensidad = ppe / revenue[-1] if revenue[-1] else 0.0
        capex_crecimiento = max(0.0, crecimiento * intensidad)
        valor = max(0.0, capex - capex_crecimiento)
        return Calc(
            "capex de mantenimiento", valor,
            "capex_total − (Δingresos × inmovilizado/ingresos)",
            {"capex_total": capex, "Δingresos": crecimiento,
             "intensidad_inmovilizado": intensidad,
             "capex_crecimiento": capex_crecimiento},
            "USD", "método Greenwald; el capex de crecimiento se excluye porque "
                   "no hace falta para sostener el negocio actual")

    return Calc(
        "capex de mantenimiento", min(capex, abs(depreciation)),
        "min(capex_total, amortización)",
        {"capex_total": capex, "amortización": abs(depreciation)},
        "USD", "proxy por amortización (Buffett, carta de 1986). Menos preciso "
               "que Greenwald: sin serie de ingresos ni saldo de inmovilizado")


def owner_earnings(operating_cash_flow: float, maint_capex: float) -> Calc:
    """
    Ganancias del propietario = flujo de caja operativo − capex de mantenimiento.

    Lo que el dueño podría sacar del negocio sin deteriorarlo. Es distinto del
    beneficio contable (que carga amortización de activos ya pagados) y del
    flujo de caja libre (que resta también el capex de crecimiento, castigando
    justamente a las empresas que reinvierten bien).
    """
    return Calc(
        "ganancias del propietario",
        operating_cash_flow - maint_capex,
        "flujo_caja_operativo − capex_mantenimiento",
        {"flujo_caja_operativo": operating_cash_flow,
         "capex_mantenimiento": maint_capex},
        "USD", "lo extraíble sin deteriorar el negocio; no es el beneficio "
               "contable ni el flujo de caja libre")


# ---------------------------------------------------------------- rentabilidad

def roic(operating_income: float, tax_rate: float, total_assets: float,
         current_liabilities: float) -> Calc:
    """
    ROIC = NOPAT / capital invertido.

    La medida de si el negocio crea o destruye valor. Por encima del coste del
    capital crea; por debajo, crecer lo empeora — que es la parte que la prensa
    financiera nunca cuenta cuando celebra un aumento de ingresos.
    """
    invertido = total_assets - current_liabilities
    if invertido <= 0:
        raise FinanceError(
            f"capital invertido no positivo ({invertido:,.0f}): el ROIC no "
            f"significa nada aquí. Pasa con financieras y con empresas de "
            f"caja neta enorme; usa otra medida")
    nopat = operating_income * (1 - tax_rate)
    return Calc("ROIC", nopat / invertido,
                "resultado_explotación × (1 − tipo_impositivo) / "
                "(activos − pasivo_corriente)",
                {"resultado_explotación": operating_income,
                 "tipo_impositivo": tax_rate, "NOPAT": nopat,
                 "capital_invertido": invertido},
                "ratio", "compáralo con el coste del capital: por debajo, "
                         "crecer destruye valor")


def cash_conversion(operating_cash_flow: float, net_income: float) -> Calc:
    """
    Conversión de caja = FCO / beneficio neto.

    Sostenidamente por debajo de 1 significa que el beneficio no se está
    convirtiendo en dinero — el aviso temprano más fiable que existe sobre
    contabilidad agresiva.
    """
    if net_income == 0:
        raise FinanceError("beneficio neto cero: la conversión no está definida")
    return Calc("conversión de caja", operating_cash_flow / net_income,
                "flujo_caja_operativo / beneficio_neto",
                {"flujo_caja_operativo": operating_cash_flow,
                 "beneficio_neto": net_income},
                "veces", "por debajo de 1 de forma sostenida: el beneficio no "
                         "se convierte en caja")


def dilution(shares: list[float]) -> Calc:
    """
    Dilución anualizada de la acción.

    Una recompra que no reduce el número de acciones es una transferencia a los
    empleados vía retribución en acciones, no una devolución al accionista.
    Mirar el gasto en recompras sin mirar el recuento de acciones es el error
    que hace que una empresa parezca que devuelve capital cuando no lo hace.
    """
    if len(shares) < 2:
        raise FinanceError("hacen falta al menos dos ejercicios para medir dilución")
    inicio, fin, n = shares[0], shares[-1], len(shares) - 1
    if inicio <= 0:
        raise FinanceError("recuento de acciones inicial no positivo")
    tasa = (fin / inicio) ** (1 / n) - 1
    return Calc("dilución anualizada", tasa,
                "(acciones_final / acciones_inicio)^(1/años) − 1",
                {"acciones_inicio": inicio, "acciones_final": fin, "años": n},
                "ratio", "positivo = dilución; negativo = recompra neta real")


def leverage(total_debt: float, cash: float, ebitda: float) -> Calc:
    """Deuda neta / EBITDA. Cuántos años de beneficio operativo debe la empresa."""
    if ebitda <= 0:
        raise FinanceError(
            f"EBITDA no positivo ({ebitda:,.0f}): el múltiplo de deuda no es "
            f"interpretable. Una empresa que pierde dinero no tiene 'años de "
            f"deuda', tiene un problema distinto")
    neta = total_debt - cash
    return Calc("deuda neta / EBITDA", neta / ebitda,
                "(deuda_total − efectivo) / EBITDA",
                {"deuda_total": total_debt, "efectivo": cash,
                 "deuda_neta": neta, "EBITDA": ebitda},
                "veces")


# ----------------------------------------------------------------------- DCF

@dataclass
class DCFAssumptions:
    growth: float           # crecimiento anual de los flujos, fase explícita
    discount: float         # tasa de descuento (coste del capital)
    terminal_growth: float  # crecimiento a perpetuidad
    years: int = 10

    def validate(self) -> None:
        if self.discount <= 0:
            raise FinanceError("la tasa de descuento debe ser positiva")
        if self.terminal_growth >= self.discount:
            raise FinanceError(
                f"crecimiento terminal ({self.terminal_growth:.1%}) >= tasa de "
                f"descuento ({self.discount:.1%}): la fórmula de Gordon da un "
                f"valor infinito o negativo. No es un caso extremo, es un "
                f"supuesto imposible — implica una empresa que acaba siendo "
                f"más grande que la economía")
        if self.terminal_growth > 0.05:
            logger.warning(
                "[finanzas] crecimiento terminal del %.1f%% a perpetuidad "
                "supera el crecimiento real de largo plazo de cualquier "
                "economía", self.terminal_growth * 100)
        if self.years < 1 or self.years > 30:
            raise FinanceError("el horizonte explícito debe estar entre 1 y 30 años")


@dataclass
class DCFResult:
    assumptions: DCFAssumptions
    base_cash_flow: float
    flows: list[float] = field(default_factory=list)
    discounted: list[float] = field(default_factory=list)
    terminal_value: float = 0.0
    terminal_discounted: float = 0.0

    @property
    def enterprise_value(self) -> float:
        return sum(self.discounted) + self.terminal_discounted

    @property
    def terminal_share(self) -> float:
        """Cuánto del valor sale del valor terminal — el dato incómodo."""
        ev = self.enterprise_value
        return self.terminal_discounted / ev if ev else 0.0


def dcf(base_cash_flow: float, a: DCFAssumptions) -> DCFResult:
    """
    Descuento de flujos. Aritmética explícita, sin atajos ni magia.

    El valor terminal suele ser el 60-80 % del resultado, lo que significa que
    un DCF es sobre todo una apuesta sobre el año 11 en adelante disfrazada de
    proyección detallada de diez años. `terminal_share` lo pone por escrito.
    """
    a.validate()
    if base_cash_flow <= 0:
        raise FinanceError(
            f"flujo base no positivo ({base_cash_flow:,.0f}): descontar flujos "
            f"negativos a perpetuidad da un valor negativo que no significa "
            f"nada. Una empresa que quema caja se valora de otra forma")

    r = DCFResult(assumptions=a, base_cash_flow=base_cash_flow)
    for t in range(1, a.years + 1):
        flujo = base_cash_flow * (1 + a.growth) ** t
        r.flows.append(flujo)
        r.discounted.append(flujo / (1 + a.discount) ** t)

    ultimo = r.flows[-1]
    r.terminal_value = (ultimo * (1 + a.terminal_growth)
                        / (a.discount - a.terminal_growth))
    r.terminal_discounted = r.terminal_value / (1 + a.discount) ** a.years
    return r


def dcf_sensitivity(base_cash_flow: float, a: DCFAssumptions,
                    discounts: list[float] | None = None,
                    terminals: list[float] | None = None) -> str:
    """
    Rejilla de sensibilidad. Nunca un número solo.

    Un DCF que devuelve "vale 142.300 millones" miente por precisión: mover el
    descuento un punto cambia el resultado un 20 %. La rejilla enseña de qué
    depende de verdad la respuesta, que es lo único que un DCF sabe decir.
    """
    discounts = discounts or [a.discount - 0.02, a.discount, a.discount + 0.02]
    terminals = terminals or [a.terminal_growth - 0.01, a.terminal_growth,
                              a.terminal_growth + 0.01]

    out = ["VALOR DE EMPRESA (millones USD) — sensibilidad",
           "", "descuento \\ crec. terminal".ljust(30)
           + "".join(f"{g:>13.1%}" for g in terminals),
           "-" * (30 + 13 * len(terminals))]
    for d in discounts:
        fila = f"{d:.1%}".ljust(30)
        for g in terminals:
            try:
                sup = DCFAssumptions(a.growth, d, g, a.years)
                fila += f"{dcf(base_cash_flow, sup).enterprise_value / 1e6:>13,.0f}"
            except FinanceError:
                fila += f"{'imposible':>13s}"
        out.append(fila)

    central = dcf(base_cash_flow, a)
    out += ["",
            f"Caso central: {central.enterprise_value / 1e6:,.0f} M USD, "
            f"del cual el {central.terminal_share:.0%} es valor terminal.",
            "",
            "El valor terminal domina el resultado, así que este cálculo es "
            "sobre todo una apuesta sobre lo que pasa después del año "
            f"{a.years}, presentada con la apariencia de una proyección "
            "detallada. Trátalo como un rango de plausibilidad, no como una "
            "tasación."]
    return "\n".join(out)


# ------------------------------------------------------------------- checklist

QUALITY_RULES: list[tuple[str, str, float, str]] = [
    # (clave, comparador, umbral, motivo)
    ("ROIC", ">", 0.12, "por debajo del coste del capital típico, crecer destruye valor"),
    ("conversión de caja", ">", 0.90, "el beneficio no se está convirtiendo en dinero"),
    ("deuda neta / EBITDA", "<", 3.0, "el apalancamiento limita la capacidad de aguantar un mal año"),
    ("dilución anualizada", "<", 0.01, "el accionista pierde participación año tras año"),
    ("margen de explotación", ">", 0.10, "margen fino: poco colchón ante un shock de costes"),
]


def quality_checklist(metrics: dict[str, float]) -> str:
    """
    Rúbrica explícita, con umbrales a la vista y criterio de fallo declarado.

    El valor de una rúbrica es que se puede discutir. Un veredicto de "calidad:
    7,4/10" salido de un LLM no se puede discutir porque no hay nada que
    discutir: no existe el cálculo.
    """
    out = ["CHECKLIST DE CALIDAD — umbrales explícitos", ""]
    pasa = fallan = 0
    for clave, cmp_, umbral, motivo in QUALITY_RULES:
        if clave not in metrics:
            out.append(f"  ?  {clave:<26s} sin dato")
            continue
        v = metrics[clave]
        ok = v > umbral if cmp_ == ">" else v < umbral
        pasa, fallan = (pasa + 1, fallan) if ok else (pasa, fallan + 1)
        marca = "OK" if ok else "NO"
        out.append(f"  {marca:<3s}{clave:<26s} {v:>9.2f}  "
                   f"(umbral {cmp_} {umbral:g})"
                   + ("" if ok else f"  ← {motivo}"))
    total = pasa + fallan
    out += ["", f"Cumple {pasa} de {total} criterios evaluables."]
    if fallan:
        out.append("Los umbrales son convenciones, no leyes: discútelos con el "
                   "caso concreto en la mano. Están escritos para que se puedan "
                   "discutir, que es más de lo que ofrece una puntuación "
                   "inventada por un modelo.")
    return "\n".join(out)
