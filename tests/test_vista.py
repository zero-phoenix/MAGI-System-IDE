"""
Que la vista lea bien, sin necesitar el emulador delante.

Mismo criterio que los oídos: el juicio vive separado de la captura, así que
se le dan pantallas descritas por sus estadísticas y textos reales de juego
—incluido OCR sucio— y se comprueba que las distingue.
"""
import pytest

from magi.modules.percepcion import vista

SATURN = ["up", "down", "left", "right", "A", "B", "C", "X", "Y", "Z",
          "L", "R", "start"]


# --- idioma ---------------------------------------------------------------

@pytest.mark.parametrize("texto,esperado", [
    ("PRESS START BUTTON to continue the game", "en"),
    ("PULSA START para continuar el juego con las opciones", "es"),
    ("APPUYEZ SUR START pour le jeu", "fr"),
])
def test_idioma_por_palabras_funcion(texto, esperado):
    codigo, conf = vista.idioma(texto)
    assert codigo == esperado
    assert conf > 0


def test_japones_por_escritura_no_por_palabras():
    """Un solo kana basta y no hay falso positivo desde el alfabeto latino."""
    codigo, conf = vista.idioma("スタートボタンをおしてください")
    assert codigo == "ja"
    assert conf > 0.5


@pytest.mark.parametrize("texto", ["", "   ", "!!! ???", "\x0c\n"])
def test_sin_texto_no_inventa_idioma(texto):
    codigo, conf = vista.idioma(texto)
    assert codigo == ""
    assert conf == 0.0


def test_una_palabra_ambigua_no_da_confianza_alta():
    """«START» acierta en inglés y en nada más, pero no es una detección."""
    _, conf = vista.idioma("START")
    assert conf < 0.7


# --- botones --------------------------------------------------------------

@pytest.mark.parametrize("texto,esperado", [
    ("PRESS START", ["start"]),
    ("PULSA A PARA CONTINUAR", ["A"]),
    ("Press any button", ["start"]),
    ("PUSH C", ["C"]),
])
def test_reconoce_el_boton_que_pide_la_pantalla(texto, esperado):
    assert vista.botones_pedidos(texto, SATURN) == esperado


def test_valida_contra_el_mando_de_esa_consola():
    """
    Si la pantalla pide un botón que la consola no tiene, es OCR sucio o es
    otra consola. Devolverlo mandaría al agente a pulsar una tecla que no
    existe.
    """
    sin_z = [b for b in SATURN if b != "Z"]
    assert vista.botones_pedidos("PRESS Z", sin_z) == []
    assert vista.botones_pedidos("PRESS Z", SATURN) == ["Z"]


def test_sin_peticion_no_devuelve_nada():
    assert vista.botones_pedidos("SONIC TEAM PRESENTS", SATURN) == []


@pytest.mark.parametrize("sucio", [
    "PULSASTARTPARA JUGAR",     # lo que Tesseract leyó de verdad
    "PRESSSTART",
    "pulsaAparacontinuar",
])
def test_ocr_que_pega_las_palabras(sucio):
    """
    Regresión de un fallo encontrado con OCR real, no sintético: Tesseract
    leyó «PULSA START PARA JUGAR» como `PULSASTARTPARA JUGAR`. Un patrón con
    `\\b` detrás del verbo no ve nada ahí, y ese es el caso normal.
    """
    assert vista.botones_pedidos(sucio, SATURN)


# --- clasificación --------------------------------------------------------

def test_pantalla_negra():
    p = vista.clasificar(negro_pct=99.2, movimiento_pct=0.0)
    assert p.clase == "negro"


def test_negro_no_intenta_leer_idioma():
    """Preguntar el idioma de una pantalla negra produce ruido con pinta de
    dato. Es la regla que ordena las comprobaciones."""
    p = vista.clasificar(negro_pct=99.0, movimiento_pct=0.0,
                         texto="basura de OCR el la los")
    assert p.clase == "negro"
    assert p.idioma == ""


def test_pantalla_de_licencia():
    """El caso real: NiGHTS se queda aquí y no llega al título."""
    p = vista.clasificar(
        negro_pct=70.0, movimiento_pct=0.2,
        texto="LICENSED BY SEGA ENTERPRISES LTD.")
    assert p.clase == "licencia"


def test_pantalla_de_carga():
    p = vista.clasificar(negro_pct=80.0, movimiento_pct=0.4,
                         texto="NOW LOADING...")
    assert p.clase == "carga"


def test_titulo_pide_boton_y_no_se_mueve():
    p = vista.clasificar(negro_pct=40.0, movimiento_pct=0.8,
                         texto="PRESS START BUTTON", botones_consola=SATURN)
    assert p.clase == "titulo"
    assert p.botones == ["start"]


def test_partida_por_movimiento():
    p = vista.clasificar(negro_pct=10.0, movimiento_pct=8.5)
    assert p.clase == "partida"


def test_menu_por_texto_sin_movimiento():
    p = vista.clasificar(
        negro_pct=30.0, movimiento_pct=0.1,
        texto="OPCIONES SONIDO VIDEO CONTROLES GUARDAR SALIR CONTINUAR")
    assert p.clase == "menu"


def test_desconocida_se_llama_desconocida():
    """No forzar una clase cuando no hay evidencia."""
    p = vista.clasificar(negro_pct=50.0, movimiento_pct=0.1, texto="x")
    assert p.clase == "desconocida"


# --- zonas ----------------------------------------------------------------

def test_la_media_global_miente_y_por_eso_hay_zonas():
    """
    60 en el menú y 17 en partida dan una media de 38, y 38 no ocurre nunca.
    El informe tiene que señalar la partida como zona lenta, no promediar.
    """
    z = vista.Zonas()
    for _ in range(5):
        z.registrar("menu", 60.0)
        z.registrar("partida", 17.0)
    inf = z.informe()
    assert inf["zona_mas_lenta"] == "partida"
    assert inf["fps_zona_mas_lenta"] == 17.0
    assert inf["por_clase"]["menu"]["fps_mediana"] == 60.0


def test_ignora_fps_invalidos():
    z = vista.Zonas()
    z.registrar("partida", 0)
    z.registrar("partida", None)
    z.registrar("partida", 30.0)
    assert z.informe()["por_clase"]["partida"]["muestras"] == 1


def test_zonas_vacias_no_revientan():
    assert vista.Zonas().informe()["zona_mas_lenta"] is None


def test_el_informe_avisa_de_su_propio_limite():
    z = vista.Zonas()
    z.registrar("partida", 20.0)
    assert "media" in z.informe()["aviso"]


# --- degradación sin OCR --------------------------------------------------

def test_sin_backend_devuelve_vacio_no_falso(monkeypatch):
    monkeypatch.setattr(vista, "_ocr", lambda: (None, "sin tesseract"))
    assert vista.disponible() is False
    assert vista.leer_texto(object()) == ""


# --- la herramienta del enjambre -----------------------------------------

def _registro():
    from magi.core.tools.registry import ToolRegistry
    from magi.modules.percepcion.tools import register_percepcion_tools
    return register_percepcion_tools(ToolRegistry())


def test_classify_screen_registrada():
    assert "classify_screen" in _registro().names()


def test_classify_screen_solo_lee():
    t = _registro().get("classify_screen")
    assert t.access == {"read"}
    assert t.dangerous is False


def test_classify_screen_con_imagen_real(tmp_path):
    """De punta a punta: imagen en disco → OCR → clase, idioma y botón."""
    pytest.importorskip("PIL")
    if not vista.disponible():
        pytest.skip("sin OCR en esta maquina")
    from PIL import Image, ImageDraw
    p = tmp_path / "titulo.png"
    img = Image.new("RGB", (640, 120), "black")
    ImageDraw.Draw(img).text((20, 45), "PRESS START BUTTON", fill="white")
    img.save(p)

    r = _registro().get("classify_screen").handler(
        path=str(p), black_pct=72.0, motion_pct=0.3, console="sega_saturn")
    assert r.ok is True
    assert r.meta["clase"] == "titulo"
    assert "start" in r.meta["botones"]
    assert r.meta["idioma"] == "en"


def test_classify_screen_sin_fichero_falla_claro():
    r = _registro().get("classify_screen").handler(path="no/existe.png")
    assert r.ok is False
    assert "no existe" in r.error


def test_sin_ocr_lo_declara_no_lo_finge(tmp_path, monkeypatch):
    """Misma regla que los oídos: capacidad ausente ≠ resultado negativo."""
    pytest.importorskip("PIL")
    from PIL import Image
    p = tmp_path / "x.png"
    Image.new("RGB", (32, 32), "black").save(p)
    monkeypatch.setattr(vista, "_ocr", lambda: (None, "sin tesseract"))
    r = _registro().get("classify_screen").handler(path=str(p))
    assert r.ok is True
    assert "SIN COMPROBAR" in r.content
    assert r.meta["ocr_disponible"] is False
