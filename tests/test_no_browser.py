"""
Tests del cortafuegos §I.3.

Estos tests son la regresión que faltaba. El fallo se reportó tres veces y se
"arregló" dos, sin que nada comprobara la propiedad de verdad: que ningún
proceso de navegador llegue a lanzarse. Los dos arreglos anteriores habrían
pasado cualquier test de los que había, porque ninguno miraba subprocess.
"""
from __future__ import annotations

import subprocess

import pytest

from magi.core import no_browser


@pytest.fixture(autouse=True)
def guard():
    """Instala el cortafuegos y deja el Popen original al terminar."""
    original = subprocess.Popen
    no_browser.install()
    yield
    subprocess.Popen = original


# ------------------------------------------------------- capa 4: subprocess

@pytest.mark.parametrize("cmd", [
    [r"C:\Program Files\Google\Chrome\Application\chrome.exe", "--remote-debugging-port=9222"],
    ["/usr/bin/google-chrome", "--headless=new"],
    ["chromium-browser"],
    ["msedge.exe", "--remote-allow-origins=*"],
    ["/opt/brave/brave"],
])
def test_lanzar_un_navegador_esta_prohibido(cmd):
    with pytest.raises(no_browser.BrowserBlocked):
        subprocess.Popen(cmd)


def test_bloquea_por_la_firma_cdp_aunque_el_binario_no_se_reconozca():
    """El binario puede llamarse cualquier cosa; --remote-debugging-port no."""
    with pytest.raises(no_browser.BrowserBlocked):
        subprocess.Popen(["binario-raro", "--remote-debugging-port=1234"])


def test_no_rompe_los_subprocesos_normales_de_magi():
    """git, gh, python y los tests siguen funcionando."""
    for cmd in (["git", "--version"], ["python", "--version"], ["echo", "hola"]):
        assert not no_browser._is_browser(cmd), cmd


def test_no_bloquea_el_runtime_webview2_de_la_propia_gui():
    """
    La GUI de MAGI es pywebview, que en Windows arranca msedgewebview2.exe.
    Bloquearlo mataría la interfaz: el cortafuegos tiene que distinguirlo de
    msedge.exe, que sí es un navegador.
    """
    assert not no_browser._is_browser([r"C:\...\msedgewebview2.exe"])
    assert no_browser._is_browser([r"C:\...\msedge.exe"])


def test_el_intento_bloqueado_queda_registrado():
    antes = no_browser.violation_count()
    with pytest.raises(no_browser.BrowserBlocked):
        subprocess.Popen(["chrome", "--remote-debugging-port=1"])
    assert no_browser.violation_count() > antes
    assert no_browser.violations()[0]["source"] == "subprocess.Popen"


# ---------------------------------------------------------- capas 1, 2 y 3

def test_self_test_declara_todas_las_capas_puestas():
    rep = no_browser.self_test()
    assert rep["popen"] is True
    assert rep["webbrowser"] is True
    assert rep["ok"] is True


def test_webbrowser_no_abre_nada():
    import webbrowser
    assert webbrowser.open("https://example.com") is False


def test_cdp_no_encuentra_navegador():
    """
    La ruta real del bug: g4f/requests/cdp.py:find_chrome_path localiza
    chrome.exe y get_shared_browser lo lanza. Sin ruta, no hay lanzamiento.
    """
    cdp = pytest.importorskip("g4f.requests.cdp")
    no_browser.install()
    assert cdp.find_chrome_path() is None


def test_cdp_no_secuestra_un_chrome_ya_abierto_del_usuario():
    """
    cdp.py:190 se engancha a cualquier Chrome con depuración remota que
    encuentre en el sistema. Eso abriría pestañas en el navegador del usuario.
    """
    cdp = pytest.importorskip("g4f.requests.cdp")
    no_browser.install()
    assert cdp.find_running_cdp_port("127.0.0.1") is None


# ------------------------------------------- detección por comportamiento

def test_cloudflare_se_detecta_aunque_declare_que_no_usa_navegador():
    """
    El corazón del bug. Cloudflare declara `use_nodriver = False` y aun así
    llama CDPSession(headless=False). Detectarlo por lo que declara fue lo que
    dejó pasar el fallo; hay que detectarlo por lo que hace.
    """
    P = pytest.importorskip("g4f.Provider")
    from magi.core.providers.backends.g4f_backend import _uses_browser

    cf = getattr(P, "Cloudflare", None)
    if cf is None:
        pytest.skip("g4f sin provider Cloudflare")
    assert getattr(cf, "use_nodriver", False) is False, (
        "si g4f cambia y ya lo declara, este test deja de ser interesante")
    assert _uses_browser(cf) is True, (
        "Cloudflare abre Chrome vía CDPSession; debe detectarse")


def test_deepinfra_tambien_se_detecta():
    P = pytest.importorskip("g4f.Provider")
    from magi.core.providers.backends.g4f_backend import _uses_browser

    di = getattr(P, "DeepInfra", None)
    if di is None:
        pytest.skip("g4f sin provider DeepInfra")
    assert _uses_browser(di) is True


def test_los_candidatos_con_navegador_van_al_final_de_la_cola():
    """
    No se descartan (Gemini declara use_nodriver y funciona por HTTP), pero se
    intentan los últimos.
    """
    pytest.importorskip("g4f.Provider")
    from magi.core.providers.backends.g4f_backend import (
        G4FProvider,
        _resolve,
        _uses_browser,
    )

    # La familia viene del catálogo de laboratorio (tests/conftest.py) y
    # contiene SIEMPRE un candidato con navegador y otro limpio, en ese orden.
    #
    # Antes era `family="deepseek"`, porque ese día contenía Cloudflare. Cuando
    # `deepseek` se reescribió, el test dejó de probar lo que dice probar sin
    # que nada avisara: una familia sin candidatos de navegador cumple
    # `marcas == sorted(marcas)` trivialmente.
    from tests.conftest import _FAMILIA_CON_NAVEGADOR

    p = G4FProvider(family=_FAMILIA_CON_NAVEGADOR)
    orden = p._ordered()
    marcas_previas = [_uses_browser(_resolve(n)) for n, _ in orden if _resolve(n)]
    assert any(marcas_previas), (
        "esta familia debe tener al menos un candidato con navegador; si no, "
        "el test pasa sin comprobar nada")
    marcas = [_uses_browser(_resolve(n)) if _resolve(n) else False for n, _ in orden]
    # Ningún candidato limpio puede quedar detrás de uno con navegador.
    assert marcas == sorted(marcas), f"orden incorrecto: {orden}"
