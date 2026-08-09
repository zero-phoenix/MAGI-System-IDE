"""
«¿Por qué tarda?» tiene respuesta, y la respuesta no es una media.

QUÉ AÑADE Y POR QUÉ EL PERCENTIL
================================
La telemetría llevaba tiempo guardando la duración de cada turno y de cada uso
de herramienta. Nadie las leía: el panel de sistema enseñaba una latencia media
por proveedor, y una media no distingue dos situaciones que no tienen nada que
ver.

    A: siempre tarda 4 s                    media = 4 s
    B: suele tardar 1 s, y 1 de cada 10     media = 4 s
       veces tarda 30 s

A es un límite del proveedor: se acepta o se cambia de proveedor. B es la cola
de la distribución, y es la que el usuario recuerda, porque es la vez que se
quedó mirando la pantalla sin saber si el sistema estaba vivo. La media las
declara idénticas. El p95 las separa.

Estos tests fijan tres cosas, y la tercera es la que hace útil al resto:

  1. El p95 es un valor REAL medido, no interpolado.
  2. El orden es por p95, no por media: lo que se ve primero es lo que más
     hace esperar.
  3. Una muestra pequeña se marca como poco fiable en vez de presentarse como
     una medida. Un «p95» de tres muestras es el peor de tres, y venderlo como
     percentil es exactamente el tipo de cifra con autoridad falsa que el
     proyecto lleva quitando de en medio.
"""
from __future__ import annotations

import time
import uuid

import pytest

from magi.core.store import telemetria as tl
from magi.core.store.state import TaskStore


@pytest.fixture()
def store(tmp_path):
    return TaskStore(path=tmp_path / "t.db")


def _turno(store, agente: str, ms: float, familia: str = "gpt") -> None:
    """Inserta un turno ya cerrado con una duración concreta."""
    ahora = time.time()
    with store._conn() as c:
        c.execute(
            "INSERT INTO turno (id, task_id, agente, familia, estado, inicio,"
            " fin, ms_total) VALUES (?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), "t1", agente, familia, "completado",
             ahora, ahora + ms / 1000, ms))


def _uso(store, herramienta: str, ms: float, inicio: float | None = None) -> None:
    """Inserta un uso de herramienta ya completado."""
    ini = inicio if inicio is not None else time.time()
    with store._conn() as c:
        c.execute(
            "INSERT INTO uso_herramienta (id, task_id, herramienta, estado,"
            " inicio, fin, ms) VALUES (?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), "t1", herramienta, "completada",
             ini, ini + ms / 1000, ms))


# ------------------------------------------------------------- el percentil

def test_el_p95_es_un_valor_realmente_medido():
    """
    Sin interpolar: el número que se enseña ocurrió de verdad.

    Interpolar produce una latencia que nunca se observó. Cuando la cifra se
    va a leer como «esto es lo que llega a tardar», inventarla es justo lo que
    no se puede hacer.
    """
    valores = [float(x) for x in range(1, 101)]      # 1..100
    assert tl._percentil(valores, 0.95) in valores
    assert tl._percentil(valores, 0.95) == 95.0
    assert tl._percentil(valores, 0.50) == 50.0
    assert tl._percentil([], 0.95) is None
    assert tl._percentil([7.0], 0.95) == 7.0


def test_el_p95_separa_lo_que_la_media_confunde():
    """El caso A/B del encabezado: misma media, p95 muy distinto."""
    estable = [4000.0] * 10
    a_rachas = [1000.0] * 9 + [31000.0]
    assert sum(estable) / 10 == sum(a_rachas) / 10          # misma media
    assert tl._percentil(estable, 0.95) == 4000.0
    assert tl._percentil(a_rachas, 0.95) == 31000.0         # el p95 sí los separa


# ------------------------------------------------------- cuellos de botella

def test_ordena_por_p95_y_no_por_media(store):
    """
    CASPER tiene peor media; BALTHASAR tiene cola. Manda la cola.

    Es la decisión de diseño entera en un test: lo que aparece arriba es lo que
    más hace esperar al usuario, no lo que sale peor en el promedio. CASPER
    tarda 3 s siempre (media 3000); BALTHASAR tarda 0,5 s casi siempre (media
    2450) pero una de cada diez veces tarda 20 s. Por la media, el problema es
    CASPER. Por la espera real, es BALTHASAR.
    """
    for _ in range(20):
        _turno(store, "CASPER", 3000)                       # media 3000, p95 3000
    for _ in range(18):
        _turno(store, "BALTHASAR", 500)
    for _ in range(2):
        _turno(store, "BALTHASAR", 20000)                   # media 2450, p95 20000

    top = tl.cuellos_de_botella(store)["agentes"]
    assert [a["clave"] for a in top][:2] == ["BALTHASAR", "CASPER"]
    assert top[0]["p95_ms"] == 20000.0
    assert top[1]["p95_ms"] == 3000.0


def test_un_pico_aislado_lo_recoge_peor_ms_no_el_p95(store):
    """
    Un solo pico entre veinte NO mueve el p95, y es correcto que no lo mueva.

    1 de cada 20 es exactamente el 5%: por definición, el percentil 95 lo deja
    fuera. Confundir esto lleva a esperar del p95 algo que el p95 no promete y
    a concluir que «la métrica no funciona».

    Por eso se devuelven las dos: `p95_ms` acota lo HABITUAL cuando va mal,
    `peor_ms` acota lo POSIBLE. La segunda es la que recoge el susto puntual.
    """
    for _ in range(19):
        _turno(store, "MELCHIOR", 500)
    _turno(store, "MELCHIOR", 60000)                        # un único pico

    a = tl.cuellos_de_botella(store)["agentes"][0]
    assert a["p95_ms"] == 500.0, "un 5% justo queda fuera del p95, por definición"
    assert a["peor_ms"] == 60000.0, "y para eso está el peor: para que se vea"


def test_una_muestra_pequeña_se_marca_como_poco_fiable(store):
    """
    Con pocas muestras el «p95» es el peor valor visto. Se dice.

    No se oculta el dato —a veces tres muestras es todo lo que hay— pero se
    entrega con la etiqueta puesta, para que nadie tome una decisión creyendo
    que mira una distribución.
    """
    for _ in range(3):
        _turno(store, "MELCHIOR", 1000)
    for _ in range(tl.MUESTRA_FIABLE + 5):
        _turno(store, "CASPER", 900)

    por_clave = {a["clave"]: a for a in tl.cuellos_de_botella(store)["agentes"]}
    assert por_clave["MELCHIOR"]["fiable"] is False
    assert por_clave["CASPER"]["fiable"] is True


def test_ignora_lo_que_no_llego_a_terminar(store):
    """Un turno en curso o cancelado no tiene duración que contar."""
    for _ in range(5):
        _turno(store, "MELCHIOR", 1000)
    with store._conn() as c:
        c.execute("INSERT INTO turno (id, task_id, agente, estado, inicio)"
                  " VALUES (?,?,?,?,?)",
                  (str(uuid.uuid4()), "t1", "MELCHIOR", "en_curso", time.time()))

    agentes = tl.cuellos_de_botella(store)["agentes"]
    assert agentes[0]["n"] == 5, "solo cuentan los turnos completados"


def test_sin_datos_no_inventa_nada(store):
    r = tl.cuellos_de_botella(store)
    assert r["agentes"] == [] and r["herramientas"] == []
    assert "error" not in r


# ----------------------------------------------- avisos por p95 histórico

def test_avisa_cuando_una_herramienta_se_sale_de_su_propio_p95(store):
    """
    La comparación es contra sí misma, y ahí está toda la utilidad.

    `run_tests` tardando 40 s es normal. `read_file` tardando 4 s no lo es. Un
    umbral único o deja pasar el segundo o marca el primero en cada ejecución;
    el historial de cada herramienta trae su propia definición de «raro».
    """
    base = time.time() - 10_000
    for i in range(60):
        _uso(store, "read_file", 30, inicio=base + i)        # siempre ~30 ms
    _uso(store, "read_file", 4000, inicio=base + 1000)       # la última: 4 s

    avisos = tl.herramientas_fuera_de_su_p95(store)
    assert [a["herramienta"] for a in avisos] == ["read_file"]
    assert avisos[0]["ultima_ms"] == 4000.0
    assert avisos[0]["veces_el_p95"] > 100

    # Y una herramienta lenta POR NATURALEZA no aparece solo por ser lenta.
    for i in range(60):
        _uso(store, "run_tests", 40_000, inicio=base + i)
    _uso(store, "run_tests", 40_100, inicio=base + 1001)
    assert "run_tests" not in [a["herramienta"]
                               for a in tl.herramientas_fuera_de_su_p95(store)]


def test_pasarse_del_p95_por_un_pelo_no_es_un_aviso(store):
    """
    El margen existe para que el aviso signifique algo.

    El p95 se supera 1 de cada 20 veces POR DEFINICIÓN. Sin margen, este aviso
    saltaría de continuo con el sistema funcionando perfectamente, y un aviso
    que salta siempre deja de leerse — que es como los sistemas de alertas
    dejan de servir para nada sin que nadie lo decida.

    40,1 s en una herramienta cuyo p95 son 40 s es comportamiento normal.
    60 s en esa misma herramienta ya no lo es.
    """
    base = time.time() - 10_000
    for i in range(60):
        _uso(store, "compilar", 40_000, inicio=base + i)

    _uso(store, "compilar", 40_100, inicio=base + 1000)      # +0,25%
    assert tl.herramientas_fuera_de_su_p95(store) == [], "un pelo no es un aviso"

    _uso(store, "compilar", 70_000, inicio=base + 1001)      # +75%
    avisos = tl.herramientas_fuera_de_su_p95(store)
    assert [a["herramienta"] for a in avisos] == ["compilar"]
    assert avisos[0]["veces_el_p95"] == 1.75


def test_no_avisa_sin_historial_suficiente(store):
    """
    Comparar contra el p95 de tres muestras es comparar contra el máximo.

    Sin este mínimo, cualquier herramienta usada por primera vez dispararía un
    aviso, y un aviso que salta siempre deja de leerse — que es la forma
    habitual de que un sistema de alertas deje de servir para nada.
    """
    base = time.time() - 1000
    for i in range(4):
        _uso(store, "grep", 20, inicio=base + i)
    _uso(store, "grep", 9000, inicio=base + 100)
    assert tl.herramientas_fuera_de_su_p95(store) == []
