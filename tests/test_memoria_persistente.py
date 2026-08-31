"""
Que la memoria permanente llegue al prompt, y que un huérfano no vuelva a pasar.

El fallo que estas pruebas vigilan no es «el módulo no funciona»: es «el módulo
funciona y nadie lo llama». Ya pasó dos veces en este repositorio —`bitacora.py`
(v5.11.0) y `controles.json` (v5.12.0)—, así que la prueba de integración
contra `inyecciones.py` no es opcional.
"""
import json
import os

import pytest

from magi.modules.swarm import memoria_persistente as mem


CONTROLES = {
    "consolas": {
        "Sega Saturn": {
            "botones": "A B C X Y Z, L R, Start, cruceta",
            "notas": "sin analogico salvo el 3D Control Pad",
        },
        "PS Vita": {"botones": "cruz circulo cuadrado triangulo, L R, dos sticks"},
    },
    "emuladores": {"YabauseVita": "PERCORE_DUMMY; el pad se lee en el bucle"},
}


@pytest.fixture
def memoria(tmp_path, monkeypatch):
    d = tmp_path / "magi" / "data" / "memoria"
    d.mkdir(parents=True)
    (d / mem.CONTROLES).write_text(json.dumps(CONTROLES), encoding="utf-8")
    (d / mem.DESCARTES).write_text(
        "# comentario que debe ignorarse\n"
        + json.dumps({"proyecto": "yabausevita", "ronda": "R1",
                      "enfoque": "atacar el render",
                      "filosofia": "hacer menos",
                      "motivo": "es el 1,27% del tiempo",
                      "medicion": "62,7ms de 5000ms",
                      "rescatable": "la descomposicion en tres etapas"},
                     ensure_ascii=False) + "\n"
        + "{ linea rota que no es json\n",
        encoding="utf-8")
    monkeypatch.setenv("MAGI_MEMORIA", str(d))
    return d


# --- lectura -------------------------------------------------------------

def test_carga_controles(memoria):
    d = mem.cargar_controles()
    assert "Sega Saturn" in d["consolas"]


def test_una_linea_rota_no_invalida_el_historico(memoria):
    """El JSONL se lee línea a línea justo para esto."""
    ds = mem.cargar_descartes()
    assert len(ds) == 1
    assert ds[0]["proyecto"] == "yabausevita"


def test_sin_memoria_no_revienta(tmp_path, monkeypatch):
    monkeypatch.delenv("MAGI_MEMORIA", raising=False)
    monkeypatch.chdir(tmp_path)
    assert mem.cargar_descartes(inicio=tmp_path) == []
    assert mem.para_el_prompt("optimiza el emulador", inicio=tmp_path) == ""


# --- escritura -----------------------------------------------------------

def test_registrar_descarte_hace_append(memoria):
    antes = len(mem.cargar_descartes())
    assert mem.registrar_descarte(
        proyecto="otro", ronda="R9", enfoque="algo",
        motivo="porque si", rescatable="la sonda")
    ds = mem.cargar_descartes()
    assert len(ds) == antes + 1
    assert ds[-1]["rescatable"] == "la sonda"


def test_el_append_no_pisa_lo_anterior(memoria):
    mem.registrar_descarte(proyecto="a", ronda="1", enfoque="x", motivo="y")
    mem.registrar_descarte(proyecto="b", ronda="2", enfoque="z", motivo="w")
    ds = mem.cargar_descartes()
    assert [d["proyecto"] for d in ds[-2:]] == ["a", "b"]


# --- bloque de prompt ----------------------------------------------------

def test_el_bloque_lleva_lo_rescatable(memoria):
    """
    Es lo que distingue esto de la memoria episódica: no basta con decir
    «ya se intentó», hay que decir qué sobrevive.
    """
    t = mem.para_el_prompt("por que va lento el emulador yabause")
    assert "SE RESCATA" in t
    assert "la descomposicion en tres etapas" in t


def test_el_bloque_lleva_los_mandos(memoria):
    t = mem.para_el_prompt("como conecto el mando a la consola Sega Saturn")
    assert "Sega Saturn" in t
    assert "A B C X Y Z" in t


def test_prioriza_la_consola_nombrada(memoria):
    t = mem.para_el_prompt("botones de PS Vita")
    assert "PS Vita" in t


def test_calla_en_encargos_ajenos(memoria):
    assert mem.para_el_prompt("resume este PDF trimestral") == ""


@pytest.mark.parametrize("encargo", [
    "que botones tiene la consola",
    "el dynarec va lento",
    "ronda 4 del emulador",
    "quiero jugar y que el input funcione",
])
def test_pertinencia(encargo):
    assert mem.pertinente(encargo)


# --- integración: que ALGUIEN lo llame -----------------------------------

def test_esta_en_la_secuencia_de_inyecciones(memoria):
    """
    La prueba que evita el tercer huérfano. `controles.json` vivió en disco
    sin que ningún prompt lo leyera; esto lo hace imposible sin que un test
    se ponga rojo.
    """
    from magi.modules.swarm import inyecciones
    t = inyecciones.acumuladas("optimiza el emulador yabause, ronda 4")
    assert "MEMORIA PERMANENTE DE MAGI" in t


def test_la_memoria_real_del_repo_es_legible():
    """
    Sin fixture: se lee la memoria de verdad del repositorio. Si alguien deja
    un JSONL malformado en un commit, esto lo caza antes del release.
    """
    os.environ.pop("MAGI_MEMORIA", None)
    ds = mem.cargar_descartes()
    ctrl = mem.cargar_controles()
    assert isinstance(ds, list) and isinstance(ctrl, dict)
    for d in ds:
        assert d.get("enfoque") and d.get("motivo"), (
            "todo descarte necesita enfoque y motivo: %r" % d)
