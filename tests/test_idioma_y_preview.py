"""
Tests de las tres correcciones de interfaz y del idioma.

Los tres fallos venían de la misma captura de pantalla del usuario:
  · Naoko contestó «嗨~请问有什么可以帮你的吗» a un «hola naoko».
  · La pestaña Configuración no pintaba nada.
  · Vista previa enseñaba la página de error del navegador.
"""
from __future__ import annotations

import pytest

from magi.core import idioma
from magi.modules.studio import preview


# =========================================================== idioma

def test_detecta_espanol_en_un_saludo_corto():
    """
    Un «hola» suelto tiene que decidir: es justo el mensaje con el que el
    modelo se despistó y contestó en chino.
    """
    assert idioma.detectar("hola naoko") == "es"
    assert idioma.detectar("porque se demora tanto melchier en responderme") == "es"


def test_detecta_otros_idiomas():
    assert idioma.detectar("hello, how does this work?") == "en"
    assert idioma.detectar("请问有什么可以帮你的吗") == "zh"
    assert idioma.detectar("bonjour, comment ça marche") == "fr"


def test_sin_texto_cae_al_por_defecto():
    assert idioma.detectar("") == "es"
    assert idioma.detectar("   ") == "es"
    assert idioma.detectar("1234 5678") == "es"


def test_pilla_la_respuesta_en_chino_que_se_vio_de_verdad():
    """La regresión exacta: esta cadena salió en la interfaz del usuario."""
    assert idioma.coincide("¡Hola! 嗨~请问有什么可以帮你的吗😊", "es") is False


def test_acepta_una_respuesta_normal_en_espanol():
    assert idioma.coincide(
        "Melchior está en la ronda 1 usando la familia gpt; la última "
        "respuesta tardó 4 segundos.", "es") is True


def test_un_tecnicismo_en_ingles_no_es_cambio_de_idioma():
    """Ser estricto de más aquí obligaría a rechazar respuestas correctas."""
    assert idioma.coincide(
        "El backend usa un timeout de 4 segundos por request y luego hace "
        "failover al siguiente provider de la familia.", "es") is True


def test_una_respuesta_corta_en_ingles_no_pasa_por_espanol():
    """
    La regresión exacta de la captura del usuario: «las 3 ia no me hablan en
    español». Una respuesta corta en inglés se daba por buena porque
    `coincide()` tenía `return len(respuesta.split()) < 12`. La guarda de los
    tres agentes y de Naoko nunca rotaba.
    """
    assert idioma.coincide("Sure! I will create a Tetris game for you.", "es") is False
    assert idioma.coincide("I will build it now.", "es") is False
    assert idioma.coincide("Of course, here is the code.", "es") is False


def test_un_bloque_de_codigo_sin_idioma_no_se_rechaza():
    """
    Un bloque de código puro (sin palabras vacías de ninguna lengua) no es un
    fallo de idioma: `detectar` cae al por defecto y no hay motivo para rotar.
    Sin este caso, afinar la detección rompería la verificación de snippets.
    """
    assert idioma.coincide("def f():\n    return 42", "es") is True
    assert idioma.coincide("x = [i*2 for i in range(10)]", "es") is True


def test_la_instruccion_va_en_el_idioma_pedido():
    assert "español" in idioma.instruccion("es")
    assert "English" in idioma.instruccion("en")
    # Un idioma sin plantilla no puede quedarse sin instrucción.
    assert idioma.instruccion("ru").strip() != ""


def test_una_respuesta_vacia_no_se_marca_como_idioma_erroneo():
    assert idioma.coincide("", "es") is True


# =========================================================== vista previa

def test_clasifica_por_extension(tmp_path):
    from pathlib import Path
    assert preview.clasificar(Path("a.png")) == "imagen"
    assert preview.clasificar(Path("a.html")) == "web"
    assert preview.clasificar(Path("a.py")) == "texto"
    assert preview.clasificar(Path("a.mp4")) == "video"
    assert preview.clasificar(Path("a.pdf")) == "documento"
    assert preview.clasificar(Path("a.bin")) == "binario"


def test_lista_los_artefactos_del_mas_reciente_al_mas_antiguo(tmp_path, monkeypatch):
    import time
    monkeypatch.setattr(preview, "workspace_dir", lambda: tmp_path)
    viejo = tmp_path / "viejo.py"
    viejo.write_text("print(1)", encoding="utf-8")
    time.sleep(0.02)
    nuevo = tmp_path / "nuevo.py"
    nuevo.write_text("print(2)", encoding="utf-8")

    r = preview.listar_artefactos()
    assert [i["nombre"] for i in r["items"]][0] == "nuevo.py", \
        "lo último que generó el enjambre debe salir primero"
    assert r["total"] == 2


def test_no_lista_el_ruido(tmp_path, monkeypatch):
    monkeypatch.setattr(preview, "workspace_dir", lambda: tmp_path)
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "x.pyc").write_bytes(b"\x00\x01")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "y.js").write_text("//", encoding="utf-8")
    (tmp_path / "bueno.md").write_text("# hola", encoding="utf-8")

    nombres = [i["nombre"] for i in preview.listar_artefactos()["items"]]
    assert nombres == ["bueno.md"]


def test_lee_texto_y_normaliza_los_saltos(tmp_path, monkeypatch):
    monkeypatch.setattr(preview, "workspace_dir", lambda: tmp_path)
    (tmp_path / "a.py").write_bytes(b"linea1\r\nlinea2\r\n")
    r = preview.leer_artefacto("a.py")
    assert r["contenido"] == "linea1\nlinea2\n", \
        "el CRLF de Windows saldría como retorno visible en el <pre>"


def test_lee_binario_como_data_url(tmp_path, monkeypatch):
    monkeypatch.setattr(preview, "workspace_dir", lambda: tmp_path)
    png = (b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
    (tmp_path / "i.png").write_bytes(png)
    r = preview.leer_artefacto("i.png")
    assert r["tipo"] == "imagen"
    assert r["data_url"].startswith("data:image/png;base64,")


def test_no_deja_salir_del_workspace(tmp_path, monkeypatch):
    """Sin esto, la interfaz podría pedir cualquier fichero de la máquina."""
    monkeypatch.setattr(preview, "workspace_dir", lambda: tmp_path)
    r = preview.leer_artefacto("../../../etc/passwd")
    assert "error" in r and "fuera del workspace" in r["error"]


def test_un_fichero_que_ya_no_esta_se_dice(tmp_path, monkeypatch):
    monkeypatch.setattr(preview, "workspace_dir", lambda: tmp_path)
    assert "error" in preview.leer_artefacto("no_existe.txt")


def test_un_texto_gigante_se_anuncia_en_vez_de_bloquear(tmp_path, monkeypatch):
    monkeypatch.setattr(preview, "workspace_dir", lambda: tmp_path)
    (tmp_path / "g.txt").write_text("x" * (preview.MAX_TEXTO + 10), encoding="utf-8")
    r = preview.leer_artefacto("g.txt")
    assert "error" in r and "grande" in r["error"]
    assert "contenido" not in r


# =========================================================== cortafuegos

def test_el_self_test_no_cuenta_como_intento_de_abrir_navegador():
    """
    `self_test()` llama a `find_chrome_path()` para comprobar la capa CDP.
    Sin distinguirlo, cada sondeo de Naoko —al arrancar y cada 3 minutos—
    contaba como violación y escupía un WARNING: el log se llenaba y Naoko
    informaba de intentos que nunca ocurrieron.
    """
    from magi.core import no_browser
    no_browser.install()
    antes = no_browser.violation_count()
    for _ in range(3):
        rep = no_browser.self_test()
        assert rep["ok"] is True
    assert no_browser.violation_count() == antes, \
        "comprobarse a sí mismo no es intentar abrir un navegador"


# =========================================================== proveedores

#: Familia de laboratorio: dos candidatos VIVOS de proveedores distintos.
#:
#: Los dos tests de abajo usaban `gpt` y sus dos primeros candidatos. El
#: 2026-08-13 se midieron y resultaron estar rotos (CopilotApp da
#: WSServerHandshakeError 460, WeWordle HTTP 429), asi que `_ordered()` empezo
#: a filtrarlos y los tests se pusieron rojos sin que el codigo del orden
#: hubiera cambiado: describian el catalogo, no el algoritmo.
#:
#: Es la misma leccion que `tests/conftest.py`: lo que se prueba es la logica,
#: y la logica no debe depender de a quien se le haya caido el servidor hoy.
_FAMILIA_DE_LABORATORIO = [
    ("Perplexity", "claude45sonnet"),
    ("CohereForAI_C4AI_Command", "command-a-03-2025"),
]


def test_el_orden_pone_delante_al_candidato_mas_rapido(monkeypatch):
    """
    Antes mandaba la afinidad a secas y `Yqcloud` se quedaba en cabeza aunque
    tardara 13,9 s habiendo alternativas de 2 s en la misma familia.
    """
    pytest.importorskip("g4f.Provider")
    from magi.core.providers.backends import g4f_backend as g
    from magi.core.providers.backends.g4f_backend import G4FProvider

    monkeypatch.setitem(g.FAMILY_SPECS, "_lab", list(_FAMILIA_DE_LABORATORIO))
    p = G4FProvider(family="_lab")
    lento, rapido = p.candidates[0], p.candidates[1]
    p._anota_latencia(lento, 13953)
    p._anota_latencia(rapido, 2000)
    assert p._ordered()[0] == rapido


def test_la_latencia_es_una_media_movil(monkeypatch):
    """Un pico suelto no puede desterrar a un candidato que suele ir bien."""
    pytest.importorskip("g4f.Provider")
    from magi.core.providers.backends import g4f_backend as g
    from magi.core.providers.backends.g4f_backend import G4FProvider

    monkeypatch.setitem(g.FAMILY_SPECS, "_lab", list(_FAMILIA_DE_LABORATORIO))
    p = G4FProvider(family="_lab")
    c = p.candidates[0]
    p._anota_latencia(c, 1000)
    p._anota_latencia(c, 11000)
    assert 1000 < p._latencia[c] < 11000
