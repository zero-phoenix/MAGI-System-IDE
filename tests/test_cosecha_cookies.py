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


def test_sin_permiso_no_se_abre_el_navegador(monkeypatch):
    """
    La puerta sigue cerrada por defecto. Se fuerza a que la vía barata no
    consiga nada para llegar al punto donde se pediría el navegador.
    """
    monkeypatch.setattr(sesion_web, "_cosechar_sin_navegador",
                        lambda *a, **k: [])
    # El motor, PRESENTE y simulado. Antes esto no estaba y la aserción de
    # abajo aceptaba «sin permiso» O «sin motor», las dos. Con eso, en el CI
    # —donde no hay navegador— el test pasaba sin llegar nunca a comprobar el
    # permiso, que es lo único que dice comprobar. Verde sin mirar nada.
    #
    # Lo cazó el guardián de conftest.py el día que se puso, no yo.
    monkeypatch.setattr(sesion_web, "disponible",
                        lambda: (True, "motor simulado"))

    ok, motivo = sesion_web.cosechar("Cloudflare")
    assert ok is False
    assert "con navegador:" in motivo, "hay que decir qué pasó en cada intento"
    # Y AHORA sí se puede exigir el motivo exacto, porque solo queda uno.
    assert "no hay permiso vigente" in motivo


# =============================== primero lo barato, luego lo caro

def test_se_intenta_sin_navegador_ANTES_que_con_navegador(monkeypatch):
    """
    EL ARREGLO QUE CONVIERTE 93 s DE FALLO EN 0,2 s DE ÉXITO.

    La primera versión empezaba por el navegador. En la máquina del usuario eso
    eran 93 segundos para acabar fallando… mientras `curl_cffi` con huella de
    navegador —ya instalado— devolvía HTTP 200 en 0,2 s contra esos mismos
    sitios.

    Empezar por el caro convertía un éxito de dos décimas en un fallo de minuto
    y medio. El orden no es un detalle: es la diferencia entre que funcione y
    que no.
    """
    orden: list[str] = []

    def barato(url, timeout_s=30.0):
        orden.append("sin navegador")
        return [{"name": "cf_clearance", "value": "x"}]

    def caro(url, espera_s):
        orden.append("con navegador")
        return []

    monkeypatch.setattr(sesion_web, "_cosechar_sin_navegador", barato)
    monkeypatch.setattr(sesion_web, "_lanzar_headless", caro)

    ok, motivo = sesion_web.cosechar("Cloudflare")
    assert ok is True
    assert orden == ["sin navegador"], (
        "si el barato basta, el navegador NO debe llegar a abrirse")
    assert "sin abrir ningún navegador" in motivo


def test_si_lo_barato_no_basta_se_escala_al_navegador(monkeypatch):
    orden: list[str] = []
    monkeypatch.setattr(sesion_web, "_cosechar_sin_navegador",
                        lambda *a, **k: orden.append("barato") or [])
    monkeypatch.setattr(
        sesion_web, "_lanzar_headless",
        lambda url, espera_s: (orden.append("caro")
                               or [{"name": "a", "value": "1"}]))
    # La comprobación previa también se simula: si no, este test arrancaría un
    # navegador de verdad y tardaría diez segundos en cada corrida.
    monkeypatch.setattr(sesion_web, "_prueba_arranque",
                        lambda *a, **k: (True, "simulado"))
    # `puede_abrir` también se simula, y no es pereza: en el runner del CI no
    # hay navegador descargado, así que la puerta dice que no y la prueba nunca
    # llegaba al punto que quería comprobar. Fallaba describiendo la MÁQUINA en
    # vez del código — el mismo defecto que ya apareció con `python_executable`
    # y con `print` como ejemplo de firma ilegible.
    monkeypatch.setattr(sesion_web, "puede_abrir", lambda: (True, "simulado"))

    ok, motivo = sesion_web.cosechar("Cloudflare")
    assert ok is True and orden == ["barato", "caro"]
    assert "con navegador" in motivo


def test_el_fallo_cuenta_lo_que_paso_en_CADA_intento(monkeypatch):
    """
    «No se pudo» sin más no permite arreglar nada. Con los dos intentos
    detallados, se ve si falló la red, el navegador, o el permiso.
    """
    monkeypatch.setattr(sesion_web, "_cosechar_sin_navegador",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("red caída")))
    monkeypatch.setattr(
        sesion_web, "_lanzar_headless",
        lambda url, espera_s: (_ for _ in ()).throw(RuntimeError("no arrancó")))
    monkeypatch.setattr(sesion_web, "_prueba_arranque",
                        lambda *a, **k: (True, "simulado"))
    monkeypatch.setattr(sesion_web, "puede_abrir", lambda: (True, "simulado"))

    ok, motivo = sesion_web.cosechar("Cloudflare")
    assert ok is False
    assert "sin navegador:" in motivo and "con navegador:" in motivo
    assert "red caída" in motivo and "no arrancó" in motivo


# =============================== el diagnóstico, en vez de la conjetura

def test_el_diagnostico_mide_cada_cosa_por_separado():
    """
    ESTO ES UNA LECCIÓN CONVERTIDA EN HERRAMIENTA.

    Al ver que la cosecha se colgaba, afirmé que la causa era FortiClient
    interceptando la tubería local de Playwright. Lo dije con seguridad y sin
    comprobarlo: lo deduje de verlo en la lista de procesos. Al medirlo, los
    sockets locales conectaban en 0,0 s — mi explicación era una conjetura con
    aspecto de diagnóstico.

    Cada línea de aquí es una comprobación real y separada, con su tiempo. El
    motivo se lee en vez de deducirse, y nadie tiene que creerse la conjetura
    de nadie.
    """
    r = sesion_web.diagnostico(incluir_lentas=False)
    assert r, "un diagnóstico vacío no diagnostica nada"

    nombres = [c["comprobacion"] for c in r]
    assert "socket local 127.0.0.1" in nombres, (
        "es la comprobación que desmintió mi conjetura; no puede faltar")

    for c in r:
        assert isinstance(c["ok"], bool)
        assert c["detalle"], f"{c['comprobacion']} sin detalle no informa"
        assert c["ms"] >= 0, "cada línea trae lo que tardó, medido"


def test_las_comprobaciones_caras_se_pueden_saltar():
    """Un diagnóstico que tarda tanto como el fallo no ayuda a nadie."""
    rapido = sesion_web.diagnostico(incluir_lentas=False)
    completo = sesion_web.diagnostico(incluir_lentas=True)
    assert len(completo) > len(rapido)
    assert "arranque headless" in [c["comprobacion"] for c in completo]


def test_el_diagnostico_se_puede_IMPRIMIR_en_cualquier_consola(monkeypatch):
    """
    La primera versión usaba `✓` y `✗`, y al imprimirla en la consola de
    Windows saltaba:

        UnicodeEncodeError: 'charmap' codec can't encode character '\\u2713'

    Una herramienta de diagnóstico que revienta al imprimirla es peor que no
    tenerla: se llama justo cuando algo va mal, y añade un error propio encima
    del que se investigaba. Es el mismo fallo que ya costó una respuesta entera
    del enjambre por escribir un acento en una consola cp1252.
    """
    # El diagnóstico consulta el motor y arranca el navegador. Aquí no se
    # comprueba lo que responden: se comprueba que el TEXTO se pueda imprimir
    # pase lo que pase. Simulando las dos, el test tarda milisegundos y dice
    # lo mismo en cualquier máquina.
    monkeypatch.setattr(sesion_web, "disponible", lambda: (True, "simulado"))
    monkeypatch.setattr(sesion_web, "_prueba_arranque",
                        lambda *a, **k: (False, "no arranca (simulado)"))
    # Y aquí va lo importante: una comprobación que devuelve texto CON acentos
    # y con un símbolo que no existe en cp1252. Es el caso realista —`detalle`
    # sale de `str(e)` de cualquier excepción, y ahí cabe cualquier cosa— y es
    # justo el que la primera versión no cubría.
    monkeypatch.setattr(sesion_web, "_cosechar_sin_navegador",
                        lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("conexión rehusada ✓ ñandú")))

    texto = sesion_web.diagnostico_legible(incluir_lentas=False)
    texto.encode("cp1252")          # la consola de Windows por defecto
    texto.encode("ascii")           # y el caso más restrictivo

    assert "diagnostico" in texto
    assert "[ok]" in texto or "[NO]" in texto
    assert "ms)" in texto, "sin tiempos no se ve dónde está el cuello"
    assert "conexion rehusada" in texto, (
        "plegar el acento, no borrar la palabra: un diagnostico ilegible no "
        "diagnostica")


def test_hay_una_prueba_de_arranque_corta_y_ajustable():
    """
    ESTE TEST EXIGÍA UN NÚMERO INVENTADO, Y CASI GANA.

    Decía `PLAZO_PRUEBA_S <= 15` porque «el arranque se sabe en diez segundos».
    Nadie lo había medido. Al medirlo en la máquina del usuario, la misma
    ejecución dio las dos cosas:

        _prueba_arranque()    -> ok=False, "no respondió en 10s"  (10 160 ms)
        diagnostico_legible() -> [ok] arranque headless: 9 958 ms

    El navegador arranca en 9,96 s y el plazo cortaba a los 10,00. La
    comprobación previa declaraba «no arranca» en una máquina donde arranca,
    por cuarenta milisegundos.

    Y cuando subí el plazo con la medida delante, ESTE TEST se puso rojo
    defendiendo la suposición contra el dato. Por eso ahora las dos cotas
    citan de dónde salen:

      - por abajo, el máximo MEDIDO (9,96 s) con margen suficiente para una
        máquina cargada o un antivirus inspeccionando el binario;
      - por arriba, muy lejos de los 93 s del fallo que esta pieza vino a
        evitar, que es lo único que de verdad importaba.
    """
    assert sesion_web.PLAZO_PRUEBA_S >= 15, (
        "menos de quince segundos y se corta un arranque legítimo: medido "
        "9 958 ms en la máquina del usuario")
    assert sesion_web.PLAZO_PRUEBA_S <= 30, (
        "más de treinta y vuelve a parecer colgado; el fallo original eran 93 s")
    assert callable(sesion_web._prueba_arranque)


def test_la_cosecha_no_intenta_navegar_si_el_arranque_falla(monkeypatch):
    """Sin esto, el plazo largo de la cosecha se pagaba igual."""
    llamado = []
    monkeypatch.setattr(sesion_web, "_cosechar_sin_navegador", lambda *a, **k: [])
    monkeypatch.setattr(sesion_web, "_prueba_arranque",
                        lambda *a, **k: (False, "no respondió en 10s"))
    monkeypatch.setattr(sesion_web, "_lanzar_headless",
                        lambda *a, **k: llamado.append(1) or [])
    # Y la puerta, simulada. Esta es la QUINTA vez en esta tanda que un test
    # mío depende de lo que haya instalado alrededor: en el runner no hay
    # navegador descargado, `puede_abrir()` dice que no, y la comprobación
    # previa que quiero probar nunca llega a ejecutarse.
    #
    # Escribí este test en el mismo commit en el que documentaba que este
    # defecto se repite. Es la mejor prueba posible de que el mecanismo del
    # plan (§3.bis.2, un CI sin lo opcional) hace falta: la disciplina sola no
    # basta ni cuando la tienes delante escrita.
    monkeypatch.setattr(sesion_web, "puede_abrir", lambda: (True, "simulado"))

    ok, motivo = sesion_web.cosechar("Cloudflare")
    assert ok is False
    assert not llamado, "si no arranca, no se intenta la pasada completa"
    assert "no arranca" in motivo and "10s" in motivo


@pytest.mark.frontera
def test_una_respuesta_de_error_no_cuenta_como_cookies(monkeypatch):
    """
    Marcado `frontera` porque prueba la función de frontera EN SÍ. No lee la
    máquina: simula un escalón más abajo, en `curl_cffi.requests.get`, así que
    sigue siendo determinista en cualquier runner.

    Un HTTP 500 no trae cookies válidas. Guardar lo que venga de una respuesta
    de error dejaría una sesión inservible con aspecto de buena.
    """
    class Falsa:
        status_code = 503
        cookies = {"a": "1"}

    monkeypatch.setattr("curl_cffi.requests.get", lambda *a, **k: Falsa())
    assert sesion_web._cosechar_sin_navegador("https://x") == []


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


def test_importar_deja_al_proveedor_listo_en_el_panel(tmp_path, monkeypatch):
    """De nada sirve importar si el panel sigue diciendo que falta."""
    monkeypatch.setattr(sesion_web, "disponible", lambda: (True, "simulado"))
    assert "Claude" in sesion_web.estado().proveedores_pendientes
    _importa(tmp_path, "c.json", json.dumps([{"name": "s", "value": "1"}]))
    e = sesion_web.estado()
    assert "Claude" in e.proveedores_con_cookies
    assert "Claude" not in e.proveedores_pendientes


# ============================================ el motor, honesto

@pytest.mark.frontera
def test_disponible_distingue_paquete_de_navegador():
    """
    El único test del fichero que mira la máquina de verdad, y por eso está
    marcado. Nota lo que NO afirma: no dice si hay motor o no —eso cambia
    entre tu equipo y el runner—, solo que la respuesta esté bien formada y
    que un «no» venga acompañado de qué falta.

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
