"""
La mejor familia va a quien más la necesita.

QUÉ CAMBIA Y POR QUÉ
====================
El reparto se hacía en el orden en que los nodos intervienen —Melchior,
Balthasar, Casper— emparejado con las familias ordenadas por prioridad. Es
decir: **la familia más rápida acababa en el nodo que menos la necesita**.

Melchior lanza 2-3 variantes EN PARALELO: su tiempo de pared es el de una sola
llamada, así que absorbe bien una familia lenta. Balthasar, en cambio, ejecuta
para refutar —el turno más caro en herramientas y el que más se repite cuando
algo falla— y Casper es quien te habla: su síntesis es la respuesta que lees, y
cuando tarda, esperas mirando la pantalla.

De ahí el orden de mérito: **Balthasar, Casper, Melchior**.

El orden de intervención no cambia. Son dos cosas distintas y este test existe
para que sigan siéndolo: quien las vuelva a confundir tendrá que hacerlo a
propósito.
"""
from __future__ import annotations

import pytest

from magi.core.providers.registry import ORDEN_DE_MERITO, SWARM_ROLES


class _Reg:
    """Registro mínimo: lo que `select_for_swarm` mira de un proveedor."""

    def __init__(self, id_, family, priority):
        self.id, self.family, self.priority = id_, family, priority


class _Registro:
    """Registry de mentira con las familias que se le digan."""

    def __init__(self, familias_por_prioridad):
        self._pool = [_Reg(f"g4f-{f}", f, i * 10)
                      for i, f in enumerate(familias_por_prioridad)]

    def healthy(self, **_):
        return list(self._pool)

    # se reutiliza la implementación real
    from magi.core.providers.registry import ProviderRegistry as _P
    select_for_swarm = _P.select_for_swarm


def test_la_mejor_familia_es_para_balthasar():
    """
    Tres familias, de la más rápida a la más lenta. Balthasar se lleva la
    primera; Melchior, la última.
    """
    a = _Registro(["rapida", "media", "lenta"]).select_for_swarm()

    assert a.diversity == "full"
    assert a.families["BALTHASAR"] == "rapida"
    assert a.families["CASPER"] == "media"
    assert a.families["MELCHIOR"] == "lenta"


def test_el_orden_de_merito_no_es_el_de_intervencion():
    """
    Fijado explícitamente: son dos secuencias distintas y confundirlas fue el
    fallo. Si alguien las vuelve a igualar, este test lo dice.
    """
    assert SWARM_ROLES == ("MELCHIOR", "BALTHASAR", "CASPER")
    assert ORDEN_DE_MERITO == ("BALTHASAR", "CASPER", "MELCHIOR")
    assert set(ORDEN_DE_MERITO) == set(SWARM_ROLES), (
        "el orden de mérito tiene que repartir entre TODOS los nodos")


def test_cada_nodo_sigue_teniendo_una_familia_distinta():
    """
    La diversidad es lo que hace que el crítico tenga sesgos diferentes al
    proponente. Sin ella el debate es un modelo hablando solo — que es
    literalmente el fallo del que salió esta arquitectura.
    """
    a = _Registro(["gpt", "gemini", "command"]).select_for_swarm()
    assert len(set(a.families.values())) == 3


def test_con_mas_familias_que_nodos_se_cogen_las_mejores():
    a = _Registro(["1ra", "2da", "3ra", "4ta", "5ta"]).select_for_swarm()

    assert a.families["BALTHASAR"] == "1ra"
    assert a.families["CASPER"] == "2da"
    assert a.families["MELCHIOR"] == "3ra"
    assert "4ta" not in a.families.values()


def test_con_roles_distintos_nadie_se_queda_sin_familia():
    """
    `roles` es un parámetro, y el orden de mérito nombra tres roles concretos.
    Un rol que no figure en él no puede quedarse fuera del reparto: iría sin
    proveedor y fallaría al primer turno.
    """
    a = _Registro(["a", "b", "c"]).select_for_swarm(
        roles=("BALTHASAR", "OTRO", "MELCHIOR"))

    assert set(a.families) == {"BALTHASAR", "OTRO", "MELCHIOR"}
    assert a.families["BALTHASAR"] == "a", "el mérito manda dentro de lo posible"
    assert len(set(a.families.values())) == 3


@pytest.mark.parametrize("familias,esperado", [
    (["unica"], "degraded"),
    (["a", "b"], "partial"),
    (["a", "b", "c"], "full"),
])
def test_la_degradacion_se_sigue_declarando(familias, esperado):
    """
    Repartir por mérito no puede tapar que haya menos familias de las
    necesarias. Un enjambre degradado que no lo diga es peor que uno degradado.
    """
    a = _Registro(familias).select_for_swarm()
    assert a.diversity == esperado
    if esperado != "full":
        assert a.note, "una degradación sin explicación no informa de nada"
