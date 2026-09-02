"""
El parche que devolvió la familia `claude` sin cookies, sin cuenta y sin
navegador.

QUÉ SE COMPRUEBA AQUÍ, Y QUÉ NO
===============================
NO se comprueba que Perplexity responda: eso depende de la red y del humor de
un servicio gratuito, y un test que lo exija estaría rojo la mitad de los días
por motivos que no son del código. Para eso está la sonda, que lo MIDE y lo
fecha.

Lo que sí se comprueba es la propiedad que hace falta para que responda: que el
atributo que `Perplexity.py` lee sin asignar exista siempre, que el parche no
pise nada que g4f ya defina, y que aplicarlo no arrastre a g4f al arranque.
"""
from __future__ import annotations

import pytest

from magi.core.providers import compat_g4f

g4f = pytest.importorskip("g4f", reason="el parche solo aplica si g4f está")


@pytest.fixture
def conversacion_limpia():
    """
    Deja `JsonConversation` como estaba al terminar.

    Sin esto el parche se filtraría a los demás tests del proceso y este
    fichero pasaría a describir el ORDEN de la suite en vez del código — la
    misma clase de defecto que persigue `tests/conftest.py`.
    """
    from g4f.providers.response import JsonConversation
    previos = {k: JsonConversation.__dict__.get(k, ...)
               for k in compat_g4f.ATRIBUTOS_POR_DEFECTO}
    for k in compat_g4f.ATRIBUTOS_POR_DEFECTO:
        if k in JsonConversation.__dict__:
            delattr(JsonConversation, k)
    yield JsonConversation
    for k, v in previos.items():
        if v is ...:
            if k in JsonConversation.__dict__:
                delattr(JsonConversation, k)
        else:
            setattr(JsonConversation, k, v)


def test_el_atributo_que_reventaba_existe_tras_aplicar(conversacion_limpia):
    """
    EL FALLO EXACTO QUE ESTO ARREGLA.

        AttributeError: 'JsonConversation' object has no attribute 'thread_title'

    Lo lanzaba `Perplexity.py:448` al adjuntar las fuentes —o sea, DESPUÉS de
    haber recibido la respuesta completa—. Se perdía todo por un campo que el
    servidor ya no manda.
    """
    conv = conversacion_limpia()
    with pytest.raises(AttributeError):
        conv.thread_title                                   # noqa: B018

    assert compat_g4f.aplicar() is True
    assert conv.thread_title == ""
    assert f"Perplexity - {conv.thread_title}"              # se interpola sin reventar


def test_no_pisa_lo_que_g4f_ya_defina(conversacion_limpia):
    """
    Si una versión futura de g4f arregla esto por su cuenta, el parche debe
    apartarse. Un remiendo que sobrevive a su causa es deuda: acaba imponiendo
    su valor sobre el bueno y el fallo resultante no se parece en nada a este.
    """
    conversacion_limpia.thread_title = "lo que diga g4f"
    compat_g4f.aplicar()
    assert conversacion_limpia.thread_title == "lo que diga g4f"


def test_es_idempotente(conversacion_limpia):
    """Se llama en cada `_get_client()`; llamarlo dos veces no puede hacer daño."""
    assert compat_g4f.aplicar() is True
    assert compat_g4f.aplicar() is True
    assert compat_g4f.esta_aplicado() is True


def test_una_instancia_hereda_el_defecto(conversacion_limpia):
    """
    El parche va en la CLASE, y lo que revienta es el acceso desde una
    INSTANCIA. Si la herencia no funcionara —por `__slots__`, por ejemplo— el
    parche parecería aplicado y no arreglaría nada.
    """
    compat_g4f.aplicar()
    assert conversacion_limpia().thread_title == ""


def test_no_importa_g4f_al_importar_el_modulo():
    """
    Todas las importaciones de g4f van DENTRO de las funciones. Aplicarlo al
    importar metería g4f en el arranque de MAGI y `test_arranque_ligero` lo
    prohíbe: el sistema haría lo mismo, solo que más tarde y peor.
    """
    import ast
    import pathlib

    fuente = pathlib.Path(compat_g4f.__file__).read_text(encoding="utf-8")
    arbol = ast.parse(fuente)
    for nodo in arbol.body:                       # SOLO el nivel superior
        if isinstance(nodo, (ast.Import, ast.ImportFrom)):
            nombre = getattr(nodo, "module", "") or ""
            nombre += " ".join(a.name for a in nodo.names)
            assert "g4f" not in nombre, (
                f"import de g4f en el nivel superior de compat_g4f: {nombre}")


# ------------------------------------------------ HuggingSpace (C6, 2-sep-2026)

@pytest.fixture
def aliases_restabables():
    """
    Deja `HuggingSpace` y sus sub-proveedores como estaban al terminar.

    Mismo motivo que `conversacion_limpia`: sin esto el parche se filtra al
    resto de la suite y el test describiría el ORDEN de ejecución, no el
    código.
    """
    from g4f.Provider import HuggingSpace
    clases = [HuggingSpace, *getattr(HuggingSpace, "providers", [])]
    previos = {c.__name__: c.__dict__.get("model_aliases", ...)
               for c in clases}
    yield clases
    for c in clases:
        p = previos[c.__name__]
        if p is ...:
            c.__dict__.pop("model_aliases", None)
        else:
            c.model_aliases = p


def test_el_alias_que_reventaba_deja_de_ser_none(aliases_restabables):
    """
    EL FALLO EXACTO QUE ESTO ARREGLA (C6), medido en ronda real el 2-sep-2026:

        g4f-hf falló: familia 'hf' agotada (1 candidatos):
        HuggingSpace: TypeError: argument of type 'NoneType' is not iterable

    Lo lanza `hf_space/__init__.py` al hacer `model in provider.model_aliases`
    con `model_aliases = None` — el default de `ProviderModelMixin` en g4f
    7.9.4. Y no es que HuggingSpace estuviera roto: quince minutos después
    respondió con normalidad por la familia `command` cuando el modelo sí
    resolvió. Estaba sin aliases en el momento de la comprobación.
    """
    clases = aliases_restabables
    compat_g4f.aplicar()
    for c in clases:
        assert c.model_aliases is not None, (
            f"{c.__name__} siguió con model_aliases=None: `model in None` "
            "lanzaría TypeError")
        # La operación que reventaba, ejecutada tal cual: ya no lanza, y
        # contesta False, que es lo que un modelo desconocido debe obtener.
        assert "modelo-que-no-existe" not in c.model_aliases


def test_el_parche_no_pisa_aliases_reales(aliases_restabables):
    """Un sub-proveedor con aliases de verdad los conserva intactos."""
    clases = aliases_restabables
    alguna = clases[-1]
    alguna.model_aliases = {"real": "alias-real"}
    compat_g4f.aplicar()
    assert alguna.model_aliases == {"real": "alias-real"}


def test_esta_aplicado_detecta_el_none(aliases_restabables):
    """El self-test tiene que ver el hueco, o no está vigilando nada."""
    clases = aliases_restabables
    clases[0].model_aliases = None
    assert not compat_g4f.esta_aplicado()
    assert compat_g4f.aplicar() is True
    assert compat_g4f.esta_aplicado()
