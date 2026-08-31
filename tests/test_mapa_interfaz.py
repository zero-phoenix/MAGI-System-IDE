"""
El cable entre la pantalla y el núcleo, con trinquete.

`test_sin_huerfanos` vigila el código que nadie llama. Esto vigila lo otro:
el topic que la interfaz nombra y que nadie atiende (**hueco en pantalla**) y
el que el backend emite sin que ningún panel lo pinte (**capacidad
invisible**).

Mismo criterio que el resto de trinquetes de este repositorio: no exige cero,
impide que suba.

UNA LECCIÓN QUE YA COSTÓ UNA VERSIÓN DE ESTE MÓDULO
===================================================
La primera versión contaba un solo sentido —lo que el backend *publica*— y
declaró 21 paneles muertos, entre ellos `task.archive`, que tiene handler en
`kernel.py:72`. La UI **manda** ese topic, no lo escucha.

Un mapa que confunde las dos direcciones manda al enjambre a arreglar 19
fallos que no existen. Por eso `comandos` y `eventos` se cuentan aparte, y por
eso hay un test que lo fija.
"""
from pathlib import Path

import pytest

from magi.modules.gui import mapa as M

#: Techos actuales, medidos el 31-ago-2026. Bajan cuando alguien conecte algo;
#: subirlos exige justificarlo en el diff, que es todo el propósito.
TECHO_SIN_NADIE = 0
TECHO_INVISIBLES = 25


@pytest.fixture(scope="module")
def m():
    return M.mapa()


# --- el trinquete --------------------------------------------------------

def test_ningun_topic_de_la_ui_se_queda_sin_destinatario(m):
    """Un hueco en pantalla que no se llenará nunca."""
    assert len(m.paneles_muertos) <= TECHO_SIN_NADIE, (
        f"topics sin destinatario: {sorted(m.paneles_muertos)}")


def test_las_capacidades_invisibles_no_crecen(m):
    """Trabajo que se hace y ningún panel muestra. Hoy 25; que no suba."""
    assert len(m.capacidades_invisibles) <= TECHO_INVISIBLES, (
        f"capacidades invisibles nuevas: {sorted(m.capacidades_invisibles)}")


def test_el_cable_existe_en_los_dos_sentidos(m):
    """
    Si un sentido queda a cero, el extractor se rompió — no es que la
    aplicación haya perdido la mitad de su interfaz de golpe.
    """
    assert m.comandos_conectados, "ningún comando UI→handler: ¿cambió el bus?"
    assert m.eventos_conectados, "ningún evento backend→UI: ¿cambió el bus?"


# --- que el mapa no mienta -----------------------------------------------

def test_los_comandos_conocidos_se_reconocen_como_conectados(m):
    """
    `task.archive` fue el caso que destapó el error de la primera versión.
    Se fija aquí para que no vuelva.
    """
    assert "task.archive" in m.atendidos
    assert "task.archive" not in m.paneles_muertos


def test_las_claves_de_localstorage_no_son_topics(m):
    """`magi.engine` es un getItem/setItem, no un topic del bus."""
    assert "magi.engine" not in m.interfaz


def test_las_refs_de_react_no_son_topics(m):
    assert "ws.current" not in m.interfaz


@pytest.mark.parametrize("basura", [
    "App.tsx", "magi.core.bus", "process.env", "ws.current",
    "algo.muy.largo.de.mas",
])
def test_el_filtro_de_ruido_hace_su_trabajo(basura):
    assert M._es_ruido(basura)


@pytest.mark.parametrize("bueno", ["task.archive", "agent.done", "eval.run"])
def test_el_filtro_no_se_come_topics_buenos(bueno):
    assert not M._es_ruido(bueno)


# --- el documento generado -----------------------------------------------

def test_el_documento_esta_al_dia(m):
    """
    `docs/MAPA-INTERFAZ.md` se genera, no se escribe a mano. Si alguien lo
    edita a mano o lo deja viejo, esto lo caza — que es la lección de
    `PORTING_NOTES.md`: un documento a mano es un documento que fue cierto.
    """
    doc = Path("docs/MAPA-INTERFAZ.md")
    if not doc.is_file():
        pytest.skip("todavía no generado")
    texto = doc.read_text(encoding="utf-8")
    assert ("| Comandos conectados (UI → handler) | %d |"
            % len(m.comandos_conectados)) in texto, (
        "el mapa del repo está desfasado: regenéralo con "
        "`python -m magi.modules.gui.mapa > docs/MAPA-INTERFAZ.md`")


def test_sin_repo_no_revienta(tmp_path):
    vacio = M.mapa(inicio=tmp_path)
    assert vacio.interfaz == set()
    assert vacio.paneles_muertos == set()
