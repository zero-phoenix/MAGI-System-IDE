"""
Dos proveedores que no estaban caídos, solo mal llamados.

EL FALLO
========
El catálogo enterraba `PhindAi` y `Qwen` entre los proveedores rotos:

    PhindAi : BaseSession.__init__() no acepta 'proxy'
    Qwen    : AsyncSession.request() no acepta 'proxy'

No era que no respondieran. `proxy` se movió del constructor al método
`request` en curl_cffi, g4f lo sigue pasando al constructor, y salta
`TypeError`. Medido con curl_cffi 0.16.0:

    AsyncSession.__init__  acepta proxy: False
    AsyncSession.request   acepta proxy: True

Dos familias enteras fuera de juego por un argumento de más.

POR QUÉ SE LEE LA FIRMA Y NO SE ESCRIBE UNA LISTA
=================================================
Una lista de argumentos a descartar se queda atrás sola en cuanto la librería
cambia otra vez — y se quedaría atrás **en silencio**, que es lo peor. Leyendo
`inspect.signature` de lo que hay instalado, el adaptador funciona con la
versión que sea sin que nadie lo mantenga.
"""
from __future__ import annotations

import pytest

from magi.core.providers import compat_curl

# ------------------------------------------------------- el filtro, aislado

def test_quita_lo_que_la_firma_no_admite():
    def f(a, b=None):
        return a, b

    assert compat_curl.filtrar_kwargs(f, {"a": 1, "b": 2}) == {"a": 1, "b": 2}
    assert compat_curl.filtrar_kwargs(f, {"a": 1, "proxy": None}) == {"a": 1}


def test_no_toca_nada_si_la_firma_acepta_cualquier_cosa():
    """
    Quien acepta `**kwargs` no necesita que le filtren, y filtrarle podría
    quitarle un argumento que sí usaba.
    """
    def f(a, **kw):
        return a, kw

    kwargs = {"a": 1, "proxy": "x", "loquesea": 2}
    assert compat_curl.filtrar_kwargs(f, kwargs) == kwargs


def test_ante_la_duda_no_toca(monkeypatch):
    """
    Si no se puede leer la firma se pasa todo tal cual.

    Filtrar por si acaso cambiaría un fallo ruidoso —un TypeError que se ve—
    por uno silencioso, que es justo el intercambio que este proyecto no hace.

    La primera versión usaba `print` como ejemplo de «firma ilegible». Falló en
    el CI: en el Python del runner `inspect.signature(print)` SÍ devuelve algo,
    así que el test comprobaba otra rama. Se fuerza el error directamente, que
    no depende de la versión.
    """
    import inspect as _inspect

    def revienta(_f):
        raise ValueError("sin firma")

    monkeypatch.setattr(_inspect, "signature", revienta)
    kwargs = {"proxy": None, "a": 1}
    assert compat_curl.filtrar_kwargs(lambda a: a, kwargs) == kwargs


def test_mira_toda_la_herencia_y_no_solo_la_clase():
    """
    EL FALLO QUE EL CI CAZÓ Y LA MÁQUINA DE DESARROLLO NO PODÍA VER.

    Los kwargs recorren la cadena de herencia. Si la hoja acepta `**kwargs`, la
    primera versión concluía «esta firma admite cualquier cosa» y no filtraba
    nada… y el argumento seguía bajando hasta la clase base, que es quien
    lanzaba el TypeError:

        AsyncSession.__init__   **kwargs=True    (no filtraba)
        BaseSession.__init__    proxy=?          (aquí reventaba)

    En local pasaba porque esa versión de `BaseSession` sí aceptaba `proxy`. El
    adaptador dependía de la versión instalada, que es justo lo que venía a
    evitar.
    """
    class Base:
        def __init__(self, a=None, b=None):
            self.a, self.b = a, b

    class Hoja(Base):
        def __init__(self, **kw):
            super().__init__(**kw)

    admitidos = compat_curl.nombres_aceptados(Hoja, "__init__")
    assert admitidos is not None
    assert {"a", "b"} <= admitidos
    assert "proxy" not in admitidos, (
        "si `proxy` cuela aquí, vuelve a bajar hasta la base y revienta")


def test_object_no_cuenta_como_que_todo_vale():
    """
    `object.__init__(self, /, *args, **kwargs)` declara `**kwargs` y no acepta
    ninguno. Contarlo diría que cualquier clase admite cualquier cosa, y el
    filtro dejaría de filtrar.
    """
    class Simple:
        def __init__(self, a=None):
            self.a = a

    assert compat_curl.nombres_aceptados(Simple, "__init__") == {"self", "a"}


def test_una_clase_ilegible_entera_devuelve_None():
    class Rara:
        pass

    assert compat_curl.nombres_aceptados(Rara, "metodo_que_no_existe") is None


def test_un_argumento_que_si_existe_nunca_se_descarta():
    """El riesgo real del adaptador: tragarse algo que sí importaba."""
    def f(a, proxy=None):
        return a, proxy

    assert compat_curl.filtrar_kwargs(f, {"a": 1, "proxy": "http://x"}) == \
        {"a": 1, "proxy": "http://x"}


# ------------------------------------------------- el adaptador, sobre curl

@pytest.fixture()
def curl():
    return pytest.importorskip("curl_cffi.requests",
                               reason="curl_cffi no instalado")


def test_el_constructor_deja_de_reventar_con_proxy(curl):
    """
    El caso exacto que mataba a PhindAi. Antes: TypeError. Ahora: sesión.
    """
    compat_curl.aplicar()
    s = curl.AsyncSession(proxy=None)          # el argumento de la discordia
    assert s is not None


def test_tambien_la_sesion_sincrona(curl):
    compat_curl.aplicar()
    with curl.Session(proxy=None) as s:
        assert s is not None


def test_aplicar_dos_veces_no_apila_capas(curl):
    """
    Está en el camino de cada petición: cada capa añadiría una llamada a
    `inspect` por sesión creada.
    """
    compat_curl.aplicar()
    assert compat_curl.aplicar() == 0, "la segunda vez no debe envolver nada"
    assert compat_curl.esta_aplicado() is True


def test_sin_curl_cffi_no_impide_arrancar(monkeypatch):
    """
    curl_cffi es una dependencia de g4f, no del sistema. No tenerla no puede
    impedir que MAGI arranque.
    """
    import builtins
    real = builtins.__import__

    def sin_curl(name, *a, **k):
        if name.startswith("curl_cffi"):
            raise ImportError("no está")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", sin_curl)
    assert compat_curl.aplicar() == 0
    assert compat_curl.esta_aplicado() is False


def test_el_backend_de_g4f_aplica_el_adaptador(curl):
    """
    De nada sirve el adaptador si nadie lo llama — la regla nº1 del proyecto.

    Se aplica en `_disable_g4f_browser()`, que el backend invoca en cada
    `_get_client()`. NO al importar el módulo: hacerlo ahí obligaba a importar
    curl_cffi en el arranque del IDE y `test_arranque_ligero` lo cazó al
    instante. El coste de una librería lo paga quien la usa.
    """
    from magi.core.providers.backends import g4f_backend

    g4f_backend._disable_g4f_browser()
    assert compat_curl.esta_aplicado() is True


def test_el_adaptador_no_se_carga_al_arrancar():
    """
    El contrato con `test_arranque_ligero`, dicho también desde este lado.

    Si alguien vuelve a mover `aplicar()` al nivel del módulo, esto lo dice con
    el motivo delante en vez de dejar el fallo en el otro fichero.
    """
    import pathlib
    fuente = (pathlib.Path(__file__).resolve().parents[1]
              / "magi/core/providers/backends/g4f_backend.py"
              ).read_text(encoding="utf-8")
    cabecera = fuente.split("class G4FProvider", 1)[0]
    nivel_modulo = [ln for ln in cabecera.splitlines()
                    if ln.startswith("aplicar_compat_curl(")]
    assert not nivel_modulo, (
        "aplicar_compat_curl() al nivel del módulo importa curl_cffi en el "
        "arranque del IDE. Va dentro de _install_browser_guard().")
