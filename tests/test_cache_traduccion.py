"""Caché de traducciones (mejora 5.19 del plan maestro).

La traducción es determinista (temperature=0, prompt fijo) y la cuota no:
repetir la llamada para el mismo texto solo gasta proveedor gratuito y
añade latencia. Estos tests fijan el contrato de la caché.
"""
from __future__ import annotations

from magi.core import idioma


def _limpia():
    idioma._CACHE_TRADUCCIONES.clear()


def test_lo_que_no_esta_no_sale():
    _limpia()
    assert idioma.traduccion_cacheada("hello world") is None


def test_lo_guardado_sale_y_no_gasta():
    _limpia()
    idioma.recordar_traduccion("hello world", "hola mundo")
    assert idioma.traduccion_cacheada("hello world") == "hola mundo"


def test_el_tamaño_no_crece_sin_limite():
    _limpia()
    for i in range(idioma._CACHE_TRADUCCIONES_MAX + 50):
        idioma.recordar_traduccion(f"texto {i}", f"texto traducido {i}")
    assert len(idioma._CACHE_TRADUCCIONES) == idioma._CACHE_TRADUCCIONES_MAX
    # Lo más viejo (textos 0..49) ha salido; lo último sigue.
    assert idioma.traduccion_cacheada("texto 0") is None
    ultimo = f"texto {idioma._CACHE_TRADUCCIONES_MAX + 49}"
    assert idioma.traduccion_cacheada(ultimo) is not None


def test_el_acceso_reciente_no_es_lo_primero_que_sale():
    _limpia()
    for i in range(idioma._CACHE_TRADUCCIONES_MAX):
        idioma.recordar_traduccion(f"t{i}", f"trad {i}")
    # El primero se acaba de usar: deja de ser el candidato a expulsar.
    assert idioma.traduccion_cacheada("t0") == "trad 0"
    idioma.recordar_traduccion("nuevo", "nuevo trad")   # llena una más
    assert idioma.traduccion_cacheada("t0") == "trad 0"      # sobrevivió
    assert idioma.traduccion_cacheada("t1") is None          # el viejo real
