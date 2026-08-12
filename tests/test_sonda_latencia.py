"""
La sonda de latencia: medir de verdad, o decir que no se midió.

QUÉ SE PRUEBA AQUÍ Y POR QUÉ
============================
El panel del sistema tiene una columna llamada «latencia medida» en la que casi
todo dice «sin medir», y las pocas cifras salían de una medición suelta escrita
a mano en el catálogo. Con eso, el orden en que se prueban los candidatos era
el de una lista, no el de quién responde antes.

Esta sonda mide. Y como toda métrica que va a decidir cosas, tiene dos formas
de fallar, ambas silenciosas:

  1. **Mentir con la aritmética.** Promediar mal no lanza ninguna excepción:
     devuelve un número perfectamente creíble y equivocado.
  2. **Mentir por omisión.** Devolver 0 ms donde no hay dato pone al candidato
     sin medir en cabeza del ranking.

Los tests van sobre esas dos, más la tercera regla: **medir no puede romper lo
medido**.
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta

import pytest

from magi.core.providers import sonda
from magi.core.store.state import TaskStore


@pytest.fixture()
def store(tmp_path):
    return TaskStore(path=tmp_path / "t.db")


def _ts(dias_atras: int, hora: int = 12) -> float:
    """Marca de tiempo a mediodía de hace N días. Mediodía evita que el cambio
    de día por zona horaria haga fallar el test según a qué hora se ejecute."""
    d = datetime.now().replace(hour=hora, minute=0, second=0, microsecond=0)
    return (d - timedelta(days=dias_atras)).timestamp()


def _mide(store, ms, dias_atras=0, ok=True, familia="gpt",
          proveedor="CopilotApp", modelo="", **kw):
    sonda.registrar(store, sonda.Medicion(
        familia=familia, proveedor=proveedor, modelo=modelo,
        ok=ok, ms=ms, ts=_ts(dias_atras), **kw))


# ============================================================== la aritmética

def test_la_media_historica_es_la_media_de_las_medias_diarias(store):
    """
    El caso que separa las dos definiciones, con números que lo hacen evidente.

        día 1   500 mediciones a 1 000 ms
        día 2     4 mediciones a 30 000 ms   (el proveedor tuvo un mal día)

    Promediando TODAS las mediciones, el día malo se diluye hasta desaparecer
    (~1 230 ms) porque el día bueno aporta 500 muestras. Promediando las medias
    diarias, cada día pesa lo mismo: 15 500 ms.

    La segunda es la que responde a la pregunta que de verdad se hace: «¿de este
    candidato me puedo fiar un día cualquiera?».
    """
    for _ in range(500):
        _mide(store, 1000, dias_atras=1)
    for _ in range(4):
        _mide(store, 30_000, dias_atras=0)

    assert sonda.media_historica(store, "gpt", "CopilotApp") == 15_500.0

    # Y que quede constancia de lo que NO se hace, para que nadie lo "arregle":
    todas = (500 * 1000 + 4 * 30_000) / 504
    assert abs(todas - 1230) < 5
    assert sonda.media_historica(store, "gpt", "CopilotApp") != pytest.approx(todas, rel=0.5)


def test_los_dias_sin_datos_no_entran_en_el_divisor(store):
    """
    Tres días de ventana, mediciones en dos. El divisor es 2, no 3.

    Contar el día vacío como cero mentiría hacia abajo —el candidato parecería
    más rápido por no haber sido medido— y contarlo como el peor caso mentiría
    hacia arriba. No hay dato, no hay día.
    """
    _mide(store, 1000, dias_atras=0)
    _mide(store, 3000, dias_atras=2)          # el día 1 queda vacío

    assert sonda.media_historica(store, "gpt", "CopilotApp", dias=3) == 2000.0
    assert len(sonda.medias_por_dia(store, "gpt", "CopilotApp", dias=3)) == 2


def test_sin_ninguna_medicion_devuelve_None_y_no_cero(store):
    """
    `None` y `0.0` son afirmaciones distintas: «no lo sé» y «es instantáneo».

    Confundirlas pone al candidato del que no se sabe nada en cabeza del
    ranking, que es exactamente el error que esta sonda viene a corregir.
    """
    assert sonda.media_historica(store, "claude", "Claude") is None


def test_las_mediciones_fallidas_no_cuentan_para_la_latencia(store):
    """
    Un fallo no tiene latencia que promediar.

    Mezclar el tiempo hasta el error con el tiempo de respuesta junta dos
    preguntas distintas —«cuánto tarda en responder» y «cuánto tarda en
    fallar»— en un solo número que no contesta ninguna.
    """
    _mide(store, 1000, dias_atras=0, ok=True)
    _mide(store, 45_000, dias_atras=0, ok=False, tipo_error="timeout")

    assert sonda.media_historica(store, "gpt", "CopilotApp") == 1000.0


def test_la_ventana_de_dias_recorta_de_verdad(store):
    _mide(store, 1000, dias_atras=0)
    _mide(store, 90_000, dias_atras=40)       # fuera de una ventana de 7

    assert sonda.media_historica(store, "gpt", "CopilotApp", dias=7) == 1000.0
    assert sonda.media_historica(store, "gpt", "CopilotApp", dias=60) == 45_500.0


# ========================================================== el orden del panel

def test_los_no_medidos_van_al_final_y_no_al_principio(store):
    """
    Sin dato no se puede afirmar que sea rápido.

    Si un candidato sin medir encabezara el ranking, el sistema lo elegiría
    antes que a otro con buena marca demostrada — eligiendo por ignorancia.
    """
    _mide(store, 5000, familia="lenta", proveedor="Lenta")
    _mide(store, 200, familia="rapida", proveedor="Rapida")
    sonda.registrar(store, sonda.Medicion(
        familia="incognita", proveedor="Incognita", ok=False,
        tipo_error="timeout", ts=_ts(0)))

    orden = [e.proveedor for e in sonda.estado_de_candidatos(store)]
    assert orden == ["Rapida", "Lenta", "Incognita"]


def test_el_panel_ordena_familias_por_su_mejor_candidato(store):
    """
    La latencia de una familia es la de su MEJOR candidato: es el primero que
    se prueba, así que es el que define la espera real.
    """
    _mide(store, 9000, familia="gpt", proveedor="Yqcloud")
    _mide(store, 900, familia="gpt", proveedor="CopilotApp")
    _mide(store, 3000, familia="gemini", proveedor="Gemini")

    r = sonda.resumen_para_panel(store)
    assert [f["familia"] for f in r["familias"]] == ["gpt", "gemini"]
    assert r["familias"][0]["mejor_ms"] == 900.0


def test_un_candidato_esta_vivo_si_acerto_la_ultima_vez(store):
    _mide(store, 500, dias_atras=1, ok=True, proveedor="Bueno")
    _mide(store, 500, dias_atras=1, ok=True, proveedor="Cayo")
    _mide(store, None, dias_atras=0, ok=False, proveedor="Cayo",
          tipo_error="cuota")

    por_prov = {e.proveedor: e for e in sonda.estado_de_candidatos(store)}
    assert por_prov["Bueno"].vivo is True
    assert por_prov["Cayo"].vivo is False
    assert por_prov["Cayo"].tipo_error == "cuota"
    # Y su latencia histórica NO se borra: sigue sabiéndose lo que tardaba.
    assert por_prov["Cayo"].media_historica_ms == 500.0


# ================================================ medir no rompe lo medido

@pytest.mark.asyncio
async def test_un_candidato_que_revienta_produce_dato_y_no_excepcion():
    """Un fallo del proveedor ES la medición, no un error de la sonda."""
    class Rota:
        async def generate(self, *a, **k):
            raise RuntimeError("429 rate limit")

    m = await sonda.medir_candidato(Rota(), "gpt", "Yqcloud")
    assert m.ok is False
    assert m.tipo_error == "cuota"
    assert m.ms is not None


@pytest.mark.asyncio
async def test_responder_vacio_no_es_responder():
    """
    Sin esto, el candidato que devuelve cadena vacía se lleva la mejor latencia
    del panel por no hacer nada — y el sistema lo elegiría el primero.
    """
    class Muda:
        async def generate(self, *a, **k):
            return "   ", "g4f-x"

    m = await sonda.medir_candidato(Muda(), "gpt", "Muda")
    assert m.ok is False and m.tipo_error == "respuesta_vacia"


@pytest.mark.asyncio
async def test_se_mide_tambien_el_idioma_de_la_respuesta():
    """
    Un candidato rapidísimo que contesta en otro idioma no sirve para este
    sistema, y la latencia sola no lo distingue de uno bueno.
    """
    class Es:
        async def generate(self, *a, **k):
            return "funciona", "g4f-x"

    class Zh:
        async def generate(self, *a, **k):
            return "运行正常，一切都很好，没有任何问题", "g4f-x"

    assert (await sonda.medir_candidato(Es(), "gpt", "A")).idioma_ok is True
    assert (await sonda.medir_candidato(Zh(), "gpt", "B")).idioma_ok is False


@pytest.mark.asyncio
async def test_el_plazo_corta_a_un_candidato_colgado():
    class Colgada:
        async def generate(self, *a, **k):
            await asyncio.sleep(30)

    t0 = time.perf_counter()
    m = await sonda.medir_candidato(Colgada(), "gpt", "Colgada", plazo_s=0.2)
    assert m.ok is False and m.tipo_error == "timeout"
    assert time.perf_counter() - t0 < 5, "el plazo no cortó"


@pytest.mark.asyncio
async def test_el_tope_diario_protege_la_cuota_del_usuario(store):
    """
    La cuota gratuita es la del usuario. Una sonda que se la gasta ha empeorado
    el sistema, por muy buenos que sean sus datos.
    """
    llamadas = 0

    class Cuenta:
        async def generate(self, *a, **k):
            nonlocal llamadas
            llamadas += 1
            return "funciona", "g4f-x"

    cands = [("gpt", "CopilotApp", "")]
    for _ in range(3):
        await sonda.medir_todo(Cuenta(), cands, store=store, max_por_dia=2)

    assert llamadas == 2, f"el tope diario no frenó: {llamadas} llamadas"


@pytest.mark.asyncio
async def test_una_base_de_datos_rota_no_tumba_la_sonda(tmp_path):
    """Registrar es lo último que puede impedir medir."""
    class SinBase:
        def _conn(self):
            raise OSError("disco lleno")

    ok = sonda.registrar(SinBase(), sonda.Medicion("gpt", "X", ok=True, ms=1.0))
    assert ok is False          # lo dice, pero no lanza
    assert sonda.media_historica(SinBase(), "gpt", "X") is None
    assert sonda.estado_de_candidatos(SinBase()) == []


def test_sin_datos_el_panel_no_inventa_nada(store):
    r = sonda.resumen_para_panel(store)
    assert r["familias"] == []
    assert r["ventana_dias"] == 30


# ================================================= el freno, por separado

def test_mediciones_hoy_solo_cuenta_las_de_hoy(store):
    """
    El contador del tope diario. Se prueba aparte porque es el freno: si
    contara de más, la sonda dejaría de medir; si contara de menos, se gastaría
    la cuota del usuario. Las dos formas de fallar son caras y silenciosas.
    """
    _mide(store, 100, dias_atras=0)
    _mide(store, 100, dias_atras=0)
    _mide(store, 100, dias_atras=1)          # ayer no cuenta para hoy
    _mide(store, 100, dias_atras=0, proveedor="Otro")   # otro candidato tampoco

    assert sonda.mediciones_hoy(store, "gpt", "CopilotApp") == 2
    assert sonda.mediciones_hoy(store, "gpt", "Otro") == 1
    assert sonda.mediciones_hoy(store, "gpt", "NoExiste") == 0


def test_los_fallos_tambien_gastan_tope(store):
    """
    Un intento fallido consumió cuota igual que uno bueno. No contarlo dejaría
    a un candidato caído siendo sondeado sin límite — justo el que menos lo
    merece.
    """
    _mide(store, None, dias_atras=0, ok=False, tipo_error="cuota")
    assert sonda.mediciones_hoy(store, "gpt", "CopilotApp") == 1


def test_el_estado_de_un_candidato_dice_lo_que_sabe_y_lo_que_no(store):
    """
    `EstadoCandidato` es el registro que consume el panel. Se comprueba entero
    porque cada campo es una afirmación que se va a enseñar al usuario.
    """
    _mide(store, 1000, dias_atras=1, ok=True)
    _mide(store, 3000, dias_atras=0, ok=True)

    e = sonda.estado_de_candidatos(store)[0]
    assert isinstance(e, sonda.EstadoCandidato)
    assert e.familia == "gpt" and e.proveedor == "CopilotApp"
    assert e.media_historica_ms == 2000.0      # (1000 + 3000) / 2 días
    assert e.ultima_ms == 3000.0
    assert e.dias_con_datos == 2
    assert e.mediciones == 2 and e.exitos == 2
    assert e.tasa_exito == 1.0
    assert e.vivo is True and e.medido is True


def test_un_candidato_sin_exitos_no_tiene_media_pero_si_historial(store):
    """«No sé cuánto tarda» y «no ha respondido nunca» son dos datos, no uno."""
    _mide(store, None, dias_atras=0, ok=False, tipo_error="credenciales")

    e = sonda.estado_de_candidatos(store)[0]
    assert e.medido is False and e.media_historica_ms is None
    assert e.mediciones == 1 and e.exitos == 0
    assert e.tasa_exito == 0.0
    assert e.tipo_error == "credenciales"
