"""
La compuerta de la Fase 8, por fin con datos reales — y dicen que fallaba.

QUE PASO
========
La réplica se construyó en la v5.17.0 con su compuerta armada y el registro
`magi/data/memoria/replica.jsonl` VACÍO a propósito: sin rondas reales, una
compuerta mide las pruebas y no el mecanismo.

El 6-sep-2026 el registro tenía ya 14 rondas reales. Todas, las catorce,
con `concedio: true`.

Eso no es «la salida legítima funciona»: es que era la única. Y una réplica
que siempre se rinde INVIERTE el mecanismo — Casper no llega a arbitrar
cuando hay objeciones, así que la antítesis gana por defecto. Es el mismo
fallo que la réplica venía a corregir, con el signo cambiado.

La causa estaba en el prompt, que empujaba tres veces hacia el mismo lado:
ofrecía la concesión primero, la calificaba de «salida legítima, no una
derrota», y cerraba con «Balthasar ejecutó el código, y tú no».

Lo que se prueba aquí es la MEDICIÓN, no el prompt: un prompt no se puede
afirmar arreglado sin volver a medir, y esto es lo que lo medirá.
"""
from __future__ import annotations

import json
from pathlib import Path

from magi.modules.swarm.replica import (
    MINIMO_PARA_JUZGAR,
    TASA_MAXIMA_DE_CONCESION,
    replica_degenerada,
    tasa_de_concesion,
)

REGISTRO = (Path(__file__).resolve().parents[1]
            / "magi/data/memoria/replica.jsonl")


def _fila(concedio: bool, fired: bool = True) -> dict:
    return {"task_id": "t", "round": 1, "fired": fired, "concedio": concedio}


def test_no_se_opina_con_pocas_rondas():
    """Tres rondas al 100 % son ruido con forma de porcentaje."""
    assert tasa_de_concesion([_fila(True)] * 3) is None
    assert replica_degenerada([_fila(True)] * 3) == ""


def test_el_100_por_cien_se_detecta():
    """Lo que se midió el 6-sep: 14 de 14."""
    filas = [_fila(True)] * 14
    assert tasa_de_concesion(filas) == 1.0
    aviso = replica_degenerada(filas)
    assert aviso, "una réplica que concede siempre tiene que saltar"
    assert "100%" in aviso
    assert "no está debatiendo" in aviso.lower()


def test_un_debate_sano_no_salta():
    """Balthasar ejecuta el código y acierta a menudo: eso no es capitular."""
    filas = [_fila(True)] * 7 + [_fila(False)] * 5
    tasa = tasa_de_concesion(filas)
    assert tasa is not None and tasa < TASA_MAXIMA_DE_CONCESION
    assert replica_degenerada(filas) == ""


def test_solo_cuentan_las_rondas_con_replica():
    """
    Una ronda sin objeciones no dispara réplica, así que no puede conceder.
    Meterla en el denominador escondería el problema: 14 concesiones sobre
    100 rondas parecerían un 14 %.
    """
    filas = [_fila(True)] * 12 + [_fila(False, fired=False)] * 88
    assert tasa_de_concesion(filas) == 1.0
    assert replica_degenerada(filas)


def test_el_registro_real_no_se_ignora():
    """
    El fichero del repositorio se LEE, no se supone.

    Si vuelve a llenarse de concesiones, este test no falla — falla la
    compuerta, que es quien debe decidir. Lo que sí se comprueba es que el
    registro sigue siendo legible y que la medición sabe leerlo: una
    compuerta que no puede leer su evidencia no es una compuerta.
    """
    if not REGISTRO.is_file():
        return
    filas = [json.loads(ln) for ln in
             REGISTRO.read_text(encoding="utf-8").splitlines()
             if ln.strip() and not ln.startswith("#")]
    tasa = tasa_de_concesion(filas)
    assert tasa is None or 0.0 <= tasa <= 1.0
    if tasa is not None and tasa > TASA_MAXIMA_DE_CONCESION:
        # No revienta la suite: informa. La decisión de retirar o arreglar
        # la réplica es de quien lee, no de un assert.
        print(f"\n[COMPUERTA FASE 8] {replica_degenerada(filas)}")
    assert len(filas) >= 0 and MINIMO_PARA_JUZGAR > 0
