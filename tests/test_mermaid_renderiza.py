"""
Los diagramas del README tienen que dibujarse en GitHub.

POR QUE EXISTE
==============
El README ha ido a GitHub roto DOS veces seguidas, con dos errores
distintos del mismo diagrama:

    "Cannot read properties of undefined (reading 'render')"
    "Could not find a suitable point for the given distance"

La segunda llegó DESPUÉS de un commit que decía haberlo arreglado. Es la
lección de siempre: se declaró arreglado sin mirarlo en el renderizador que
falla, que es el de GitHub y no el editor de nadie.

Un test no puede ejecutar el Mermaid de GitHub. Lo que sí puede es prohibir
las construcciones que lo han roto, que es donde estaba el fallo las dos
veces: formas exóticas con etiquetas largas, y nodos declarados dentro de
`subgraph` con aristas cruzando su frontera. Ninguna de las dos aporta nada
que un rectángulo no diga igual.

Esto NO sustituye a mirar la página. Sustituye a olvidarse de mirarla.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

README = Path(__file__).resolve().parents[1] / "README.md"

_BLOQUE = re.compile(r"```mermaid\r?\n(.*?)```", re.S)


def bloques() -> list[str]:
    return _BLOQUE.findall(README.read_text(encoding="utf-8"))


def test_hay_al_menos_un_diagrama():
    assert bloques(), "el README ya no trae ningún diagrama Mermaid"


#: Formas cuyo cálculo de intersección con la arista es el que falla.
#: `[( )]` (cilindro) es la que estaba puesta cuando saltó "Could not find a
#: suitable point for the given distance": la arista busca dónde tocar el
#: borde del cilindro y con una etiqueta larga no encuentra el punto.
_FORMAS_FRAGILES = {
    r"\[\(": "cilindro `[( )]`",
    r"\(\[": "estadio `([ ])`",
    r"\{\{": "hexágono `{{ }}`",
    r"\[\[": "subrutina `[[ ]]`",
    r"\[/": "paralelogramo `[/ /]`",
    r"\[\\": "trapecio `[\\ \\]`",
}


@pytest.mark.parametrize("i", range(len(bloques())))
def test_sin_formas_que_rompen_el_trazado(i: int):
    diagrama = bloques()[i]
    culpables = [
        nombre for patron, nombre in _FORMAS_FRAGILES.items()
        if re.search(patron, diagrama)
    ]
    assert not culpables, (
        f"el diagrama {i} usa {culpables}. Esas formas son las que rompen el "
        f"trazado en GitHub con «Could not find a suitable point for the "
        f"given distance»: el renderizador no encuentra dónde debe tocar la "
        f"arista el borde de la figura. Usa `[\"texto\"]`, que dice lo mismo "
        f"y se dibuja siempre.")


@pytest.mark.parametrize("i", range(len(bloques())))
def test_sin_subgraph(i: int):
    """
    Una arista que cruza la frontera de un `subgraph` es la otra fuente del
    mismo fallo, y aquí había tres cruzándola.

    El agrupamiento visual no vale un diagrama que no se ve. Si hace falta
    agrupar, se hace con prosa alrededor del diagrama.
    """
    assert "subgraph" not in bloques()[i], (
        f"el diagrama {i} usa `subgraph`. Las aristas que cruzan su frontera "
        f"son la segunda causa conocida de que este README no renderice.")


@pytest.mark.parametrize("i", range(len(bloques())))
def test_las_etiquetas_van_entrecomilladas(i: int):
    """
    Sin comillas, un acento o un `·` dentro de la etiqueta rompe el parseo.
    Fue el primero de los dos fallos («Cannot read properties of undefined»).
    """
    malas = [ln.strip() for ln in bloques()[i].splitlines()
             if re.search(r"\[[^\"\]\[]*[áéíóúñÁÉÍÓÚÑ·][^\"\]\[]*\]", ln)]
    assert not malas, (
        f"etiquetas sin comillas con acentos o separadores: {malas[:4]}. "
        f"Escríbelas como [\"texto\"].")


@pytest.mark.parametrize("i", range(len(bloques())))
def test_ningun_nodo_apunta_a_si_mismo(i: int):
    """Una arista de longitud cero no tiene punto de corte que encontrar."""
    bucles = [ln.strip() for ln in bloques()[i].splitlines()
              if (m := re.match(r"\s*(\w+)\s*-[.-]*->.*?\|?\s*(\w+)\s*$", ln))
              and m.group(1) == m.group(2)]
    assert not bucles, f"aristas de un nodo a sí mismo: {bucles}"
