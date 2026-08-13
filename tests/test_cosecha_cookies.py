"""
La cosecha de cookies: sin ventanas, y sin fingir lo que no se puede.

LA TENSIÓN QUE ESTO RESUELVE
============================
La regla es «ninguna ventana salvo la interfaz de MAGI». Tiene una consecuencia
que conviene no disimular: **sin ventana no puedes escribir tu contraseña**. Un
inicio de sesión interactivo necesita que veas la página.

Así que los seis proveedores que exigen sesión no son un grupo, son dos:

  AUTOMÁTICO (Cloudflare, DeepInfra)
      Necesitan una SESIÓN de navegador, no una CUENTA. Se visita la página
      headless, se deja que el desafío anti-bot se resuelva solo, y las
      cookies que quedan sirven. Cero intervención, cero ventanas.

  IMPORTADO (Claude, OpenaiChat, Copilot, LMArena)
      Necesitan TU CUENTA. Aquí no hay forma honesta sin ventana: o te la
      enseñamos, o le damos tu contraseña a un robot. Las dos son malas. La
      tercera —la que se implementa— es que tú exportes las cookies desde tu
      navegador, donde ya has iniciado sesión, y MAGI lea el fichero.

Fingir que el segundo grupo funciona solo sería vender humo. Los tests de abajo
comprueban que se dice, no que se disimula.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from magi.core import sesion_web

RAIZ = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def sin_permiso():
    sesion_web.revocar_permiso()
    yield
    sesion_web.revocar_permiso()


# ============================================ NINGUNA VENTANA. NUNCA.

def test_nunca_se_lanza_con_ventana():
    """
    LA COMPROBACIÓN QUE NO PUEDE FALLAR.

    Se lee el fichero fuente en vez de llamar a la función, porque llamarla
    lanzaría un navegador de verdad y este test tiene que valer también donde
    Camoufox no está. Lo que se vigila es que nadie escriba `headless=False`
    «solo para depurar un momento»: así es como una regla se pierde.

    Tampoco vale `headless="virtual"`: eso levanta un display virtual, que es
    una ventana más aunque no la veas, y una dependencia más.

    Se mira la llamada con AST y no buscando texto: la primera versión hacía
    `"headless=False" not in fuente` y saltó con su propio comentario, que
    explicaba por qué no se usa. Un guardián que no distingue el código de lo
    que se dice SOBRE el código va a dar falsos positivos siempre.
    """
    import ast

    arbol = ast.parse((RAIZ / "magi/core/sesion_web.py").read_text(encoding="utf-8"))
    llamadas = [n for n in ast.walk(arbol)
                if isinstance(n, ast.Call)
                and getattr(n.func, "id", getattr(n.func, "attr", "")) == "Camoufox"]

    assert llamadas, "no encuentro la llamada a Camoufox"
    for c in llamadas:
        kw = {k.arg: k.value for k in c.keywords}
        assert "headless" in kw, "headless tiene que ir EXPLÍCITO, no por defecto"
        v = kw["headless"]
        assert isinstance(v, ast.Constant) and v.value is True, (
            f"headless={ast.dump(v)}: la única ventana de MAGI es su interfaz. "
            f"Ni False para depurar, ni 'virtual' (un display virtual es una "
            f"ventana más y una dependencia más)")


def test_no_se_usa_el_toolkit_de_ventanas_de_camoufox():
    """
    Camoufox trae un extra `gui` que arrastra PySide6 — un toolkit de ventanas
    entero. No se instala ni se importa: sería meter en el sistema justo lo que
    la regla prohíbe, y de paso decenas de megas.
    """
    fuente = (RAIZ / "magi/core/sesion_web.py").read_text(encoding="utf-8")
    assert "PySide6" not in fuente
    reqs = (RAIZ / "requirements.txt").read_text(encoding="utf-8")
    assert "camoufox[gui]" not in reqs


# ============================================ los dos caminos, separados

def test_cada_proveedor_esta_en_un_camino_y_solo_en_uno():
    """
    Los seis, repartidos sin solapes ni huecos. Un proveedor en los dos
    caminos, o en ninguno, sería un hueco silencioso en el panel.
    """
    auto = set(sesion_web.COSECHA_AUTOMATICA)
    imp = set(sesion_web.COSECHA_IMPORTADA)
    assert not (auto & imp), "un proveedor no puede estar en los dos caminos"
    assert auto | imp == set(sesion_web.PROVEEDORES_QUE_LA_NECESITAN)


def test_los_que_piden_cuenta_dicen_que_hacer_en_vez_de_fallar():
    """
    El caso más importante de esta pieza: **no se intenta y se falla con un
    error críptico**. Se explica por qué no se puede y qué hacer.
    """
    ok, motivo = sesion_web.cosechar("Claude")
    assert ok is False
    assert "contraseña" in motivo
    assert "claude.ai" in motivo, "hay que decir de DÓNDE exportarlas"
    assert "importar_cookies" in motivo, "y CON QUÉ importarlas"


def test_un_proveedor_que_no_necesita_sesion_lo_dice():
    ok, motivo = sesion_web.cosechar("Gemini")
    assert ok is False and "no necesita sesión web" in motivo


def test_sin_permiso_no_se_cosecha_ni_lo_automatico():
    """La puerta sigue cerrada por defecto también para esto."""
    ok, motivo = sesion_web.cosechar("Cloudflare")
    assert ok is False
    assert "permiso" in motivo or "Camoufox" in motivo


# ============================================ importar lo que tú exportaste

def _importa(tmp_path, nombre: str, contenido: str) -> tuple[bool, str]:
    f = tmp_path / nombre
    f.write_text(contenido, encoding="utf-8")
    return sesion_web.importar_cookies("Claude", f)


def test_importa_el_json_de_una_extension(tmp_path):
    ok, msg = _importa(tmp_path, "cookies.json", json.dumps([
        {"name": "sessionKey", "value": "abc", "domain": ".claude.ai"},
        {"name": "otra", "value": "x", "domain": ".claude.ai"},
    ]))
    assert ok is True and "2 cookie(s)" in msg
    assert len(sesion_web.cookies_de("Claude")) == 2


def test_importa_un_cookies_txt_de_netscape(tmp_path):
    contenido = (
        "# Netscape HTTP Cookie File\n"
        ".claude.ai\tTRUE\t/\tTRUE\t1799999999\tsessionKey\tabc123\n"
        ".claude.ai\tTRUE\t/\tFALSE\t0\totra\tvalor\n")
    ok, _ = _importa(tmp_path, "cookies.txt", contenido)
    assert ok is True

    cookies = sesion_web.cookies_de("Claude")
    assert {c["name"] for c in cookies} == {"sessionKey", "otra"}
    primera = next(c for c in cookies if c["name"] == "sessionKey")
    assert primera["secure"] is True and primera["domain"] == ".claude.ai"


def test_importa_un_har_del_panel_de_red(tmp_path):
    har = {"log": {"entries": [
        {"request": {"cookies": [{"name": "sessionKey", "value": "abc"}]}},
        {"request": {"cookies": [{"name": "sessionKey", "value": "abc"},
                                 {"name": "cf_bm", "value": "z"}]}},
    ]}}
    ok, msg = _importa(tmp_path, "red.har", json.dumps(har))
    assert ok is True
    # La misma cookie repetida en varias peticiones se cuenta una vez: un HAR
    # de una sesión normal trae cientos de entradas con las mismas cookies.
    assert "2 cookie(s)" in msg


def test_el_formato_se_deduce_del_contenido_y_no_de_la_extension(tmp_path):
    """
    Un `.txt` puede llevar JSON dentro. Fiarse del nombre del fichero es cómo
    se rechaza uno perfectamente válido y se le dice al usuario que su
    exportación está mal cuando no lo está.
    """
    ok, _ = _importa(tmp_path, "esto_es_json.txt",
                     json.dumps([{"name": "a", "value": "1"}]))
    assert ok is True


def test_un_fichero_sin_cookies_lo_dice_con_los_formatos_admitidos(tmp_path):
    ok, motivo = _importa(tmp_path, "vacio.txt", "aquí no hay nada")
    assert ok is False
    for formato in ("JSON", "cookies.txt", "har"):
        assert formato in motivo


def test_un_fichero_que_no_existe_no_revienta():
    ok, motivo = sesion_web.importar_cookies("Claude", "/no/existe/x.json")
    assert ok is False and "no existe" in motivo


def test_un_json_roto_se_trata_como_fichero_sin_cookies(tmp_path):
    ok, motivo = _importa(tmp_path, "roto.json", '[{"name": "a",')
    assert ok is False and "Formatos admitidos" in motivo


def test_importar_deja_al_proveedor_listo_en_el_panel(tmp_path):
    """De nada sirve importar si el panel sigue diciendo que falta."""
    assert "Claude" in sesion_web.estado().proveedores_pendientes
    _importa(tmp_path, "c.json", json.dumps([{"name": "s", "value": "1"}]))
    e = sesion_web.estado()
    assert "Claude" in e.proveedores_con_cookies
    assert "Claude" not in e.proveedores_pendientes


# ============================================ el motor, honesto

def test_disponible_distingue_paquete_de_navegador():
    """
    El paquete de pip son 1,3 MB y es solo el lanzador; el navegador son ~100
    MB aparte. Dar por bueno el import dejaría el fallo para el primer uso
    real, disfrazado de error del proveedor en vez de «falta descargar el
    navegador», que sí es accionable.
    """
    hay, motivo = sesion_web.disponible()
    assert isinstance(hay, bool) and motivo
    if not hay:
        assert ("no está instalado" in motivo
                or "no se ha descargado" in motivo), motivo
        assert "camoufox" in motivo.lower(), "hay que decir qué falta"
