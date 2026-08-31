"""
El índice y el automodelo: las dos piezas que no gastan red.

Se prueban juntas porque comparten la propiedad que las justifica: responden
preguntas que hoy cuestan una llamada al modelo —«¿ya se intentó esto?» y
«¿sé hacer esto de verdad?»— en milisegundos y sin cuota.
"""
import json

import pytest

from magi.modules.memory import indice as I
from magi.modules.swarm import automodelo as A

# ======================================================================
# ÍNDICE
# ======================================================================

@pytest.fixture
def idx():
    i = I.Indice()
    i.añadir("descartes", "descartes.jsonl",
             "atacar el camino de render se descarto: es el 1.27% del tiempo")
    i.añadir("bitacora", "BITACORA.md",
             "el dynarec cuelga al primer frame, cache JIT correcta")
    i.añadir("codigo", "vidgpu.c",
             "composite upload display frames por ventana de 5 s")
    return i


def test_encuentra_lo_que_ya_se_intento(idx):
    r = idx.buscar("render")
    assert r and "descartes" in r[0].fuente


def test_operadores_de_fts5_siguen_valiendo(idx):
    assert idx.buscar("dynarec AND cuelga")
    assert idx.buscar("dynarec OR composite")


def test_un_numero_con_punto_no_revienta(idx):
    """
    `1.27` daba `fts5: syntax error near "."`. Un buscador que falla cuando le
    pasas un número es un buscador que nadie usa dos veces.
    """
    r = idx.buscar("1.27")
    assert r, "deberia encontrar el descarte del 1,27%"


@pytest.mark.parametrize("q", ["(", '"', "a AND", "*", "NEAR(", "-"])
def test_consultas_rotas_devuelven_vacio_no_excepcion(idx, q):
    assert idx.buscar(q) == []


def test_consulta_vacia(idx):
    assert idx.buscar("") == []
    assert idx.buscar("   ") == []


def test_saneo_conserva_operadores():
    assert "AND" in I.sanear_consulta("dynarec and cuelga")
    assert I.sanear_consulta("1.27") == '"1.27"'
    assert I.sanear_consulta('"frase exacta"') == '"frase exacta"'


def test_el_fragmento_situa_el_acierto(idx):
    r = idx.buscar("dynarec")
    assert r[0].fragmento, "sin fragmento hay que abrir el fichero para saber si sirve"


def test_construir_sobre_el_repo_real():
    """Sin fixture: el corpus de verdad. Medido: ~224 docs en ~100 ms."""
    i = I.construir()
    assert i.documentos > 50, "el indice no encontro el corpus"
    assert i.ms_construccion < 5000, (
        "reconstruir tarda demasiado; si el corpus crece, toca persistir")
    assert i.buscar("dynarec") or i.buscar("emulador")


def test_sin_repo_no_revienta(tmp_path):
    i = I.construir(inicio=tmp_path)
    assert i.documentos == 0
    assert i.buscar("lo que sea") == []


# ======================================================================
# AUTOMODELO
# ======================================================================

def test_la_afirmacion_calcula_su_fiabilidad():
    """
    `Afirmacion` es la estructura de la que depende todo lo demás: si su
    fiabilidad miente, `fragiles` señala las equivocadas y el prompt avisa de
    lo que no toca. Se prueba directamente, no a través de `Automodelo`.
    """
    a = A.Afirmacion(texto="x", prueba="p")
    assert a.fiabilidad is None, "sin datos no hay fiabilidad, ni 0 ni 1"
    a.veces_ok, a.veces_mal = 3, 1
    assert a.fiabilidad == 0.75


def test_la_afirmacion_refutada_muestra_la_evidencia():
    a = A.Afirmacion(texto="el dynarec arranca", prueba="corrida",
                     estado="refutada", evidencia="cuelga al primer frame")
    r = a.render()
    assert "REFUTADA" in r
    assert "cuelga al primer frame" in r, (
        "una refutación sin la evidencia obliga a ir a buscarla")


def test_una_afirmacion_sin_prueba_no_se_admite():
    """
    «Soy bueno razonando» no es una afirmación sobre uno mismo: es una opinión.
    Es la regla que sostiene el fichero entero.
    """
    m = A.Automodelo()
    assert m.afirmar("soy bueno razonando", prueba="") is None
    assert m.afirmar("", prueba="run_tests") is None
    assert m.afirmaciones == []


def test_afirmar_con_prueba_si():
    m = A.Automodelo()
    a = m.afirmar("se medir el emulador", prueba="ronda_emulador")
    assert a is not None
    assert a.estado == "sin_comprobar"


def test_la_realidad_refuta_sola():
    """Sin que nadie la revise a mano: esa es toda la idea."""
    m = A.Automodelo()
    m.afirmar("se medir el emulador", prueba="ronda_emulador")
    n = m.contrastar("ronda_emulador", ok=False, evidencia="0 ventanas en 90 s")
    assert n == 1
    assert m.refutadas[0].estado == "refutada"
    assert "0 ventanas" in m.refutadas[0].evidencia


def test_la_realidad_tambien_sostiene():
    m = A.Automodelo()
    m.afirmar("se medir el emulador", prueba="ronda_emulador")
    m.contrastar("ronda_emulador", ok=True)
    assert m.afirmaciones[0].estado == "sostenida"
    assert m.refutadas == []


def test_sin_comprobar_no_es_verdadera():
    """Tratar lo no comprobado como cierto es el fallo que R9 corrigio."""
    m = A.Automodelo()
    m.afirmar("se leer la pantalla", prueba="classify_screen")
    assert m.sin_comprobar
    assert m.afirmaciones[0].estado == "sin_comprobar"


def test_la_fragil_se_distingue_de_la_solida():
    """Una que se cae 1 de cada 3 no es 'sostenida', aunque hoy funcione."""
    m = A.Automodelo()
    m.afirmar("el dynarec arranca", prueba="corrida")
    for ok in (True, False, False, True, False):
        m.contrastar("corrida", ok=ok)
    a = m.afirmaciones[0]
    assert a.fiabilidad == 0.4
    assert a in m.fragiles


def test_una_refutada_que_vuelve_a_sostenerse_conserva_su_historial():
    m = A.Automodelo()
    m.afirmar("compila", prueba="build")
    m.contrastar("build", ok=False)
    m.contrastar("build", ok=True)
    a = m.afirmaciones[0]
    assert a.estado == "sostenida"
    assert a.veces_mal == 1, "borrar el fallo perderia justo la informacion util"


def test_retirar_la_saca_del_contraste():
    m = A.Automodelo()
    m.afirmar("algo viejo", prueba="p")
    assert m.retirar("algo viejo")
    assert m.contrastar("p", ok=False) == 0


def test_no_duplica_afirmaciones():
    m = A.Automodelo()
    a1 = m.afirmar("x", prueba="p")
    a2 = m.afirmar("x", prueba="p")
    assert a1 is a2
    assert len(m.afirmaciones) == 1


# --- prompt --------------------------------------------------------------

def test_el_prompt_solo_lleva_lo_que_cambia_una_decision(tmp_path, monkeypatch):
    """
    Lo que se sostiene sin fallar no hace falta recordarlo: ocupa contexto y no
    cambia nada. Solo viajan lo refutado y lo frágil.
    """
    f = tmp_path / "AUTOMODELO.json"
    m = A.Automodelo()
    m.afirmar("esto falla", prueba="p1")
    m.afirmar("esto va bien", prueba="p2")
    m.contrastar("p1", ok=False, evidencia="reventó")
    m.contrastar("p2", ok=True)
    m.guardar(f)
    monkeypatch.setenv("MAGI_AUTOMODELO", str(f))

    t = A.para_el_prompt("lo que sea")
    assert "esto falla" in t
    assert "esto va bien" not in t


def test_sin_fichero_no_inyecta_nada(tmp_path, monkeypatch):
    monkeypatch.setenv("MAGI_AUTOMODELO", str(tmp_path / "no-existe.json"))
    assert A.para_el_prompt("x") == ""


def test_json_corrupto_no_tumba_el_arranque(tmp_path, monkeypatch):
    f = tmp_path / "AUTOMODELO.json"
    f.write_text("{ esto no es json", encoding="utf-8")
    monkeypatch.setenv("MAGI_AUTOMODELO", str(f))
    assert A.cargar().afirmaciones == []


def test_una_entrada_con_esquema_viejo_no_invalida_las_demas(tmp_path, monkeypatch):
    f = tmp_path / "AUTOMODELO.json"
    f.write_text(json.dumps([
        {"campo_que_ya_no_existe": 1},
        {"texto": "buena", "prueba": "p"},
    ]), encoding="utf-8")
    monkeypatch.setenv("MAGI_AUTOMODELO", str(f))
    m = A.cargar()
    assert len(m.afirmaciones) == 1
    assert m.afirmaciones[0].texto == "buena"


def test_ida_y_vuelta_a_disco(tmp_path, monkeypatch):
    f = tmp_path / "AUTOMODELO.json"
    m = A.Automodelo()
    m.afirmar("persiste", prueba="p")
    m.contrastar("p", ok=False, evidencia="ev")
    m.guardar(f)
    monkeypatch.setenv("MAGI_AUTOMODELO", str(f))
    m2 = A.cargar()
    assert m2.afirmaciones[0].estado == "refutada"
    assert m2.afirmaciones[0].evidencia == "ev"
