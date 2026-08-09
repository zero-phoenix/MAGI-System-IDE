"""
El catálogo externo no puede cambiar el comportamiento, solo dónde vive el dato.

Sacar `FAMILY_SPECS` y compañía a un JSON sirve para no tener que recompilar
158 MB de ejecutable cada vez que un proveedor gratuito se cae. Pero si al
sacarlo cambia UN valor, se ha roto algo. Estos tests comparan las dos fuentes.
"""
from __future__ import annotations

import json

import pytest

from magi.core.providers import catalogo as cat
from magi.core.providers.backends import g4f_backend as g


def test_el_json_dice_lo_mismo_que_las_constantes():
    """El fichero empaquetado y el respaldo tienen que coincidir."""
    respaldo = cat._desde_respaldo()
    actual = cat.catalogo()
    assert actual.family_specs == respaldo.family_specs
    assert set(actual.verificadas) == set(respaldo.verificadas)
    assert actual.rotos == respaldo.rotos
    assert actual.hedge_tras_s == respaldo.hedge_tras_s
    assert actual.hedge_max == respaldo.hedge_max
    assert actual.reparto == respaldo.reparto


def test_los_nombres_publicos_siguen_ahi_y_con_la_forma_de_siempre():
    """Nada de lo que ya consumía estos datos debería notar el cambio."""
    assert isinstance(g.FAMILY_SPECS, dict) and g.FAMILY_SPECS
    for fam, cands in g.FAMILY_SPECS.items():
        assert isinstance(cands, list)
        for c in cands:
            assert isinstance(c, tuple) and len(c) == 2
    assert isinstance(g.ROTOS, dict) and g.ROTOS
    assert isinstance(g.HEDGE_AFTER_S, float)
    assert isinstance(g.HEDGE_MAX, int)
    assert set(g.DEFAULT_SWARM_FAMILIES) == {"MELCHIOR", "BALTHASAR", "CASPER"}


def test_las_familias_verificadas_siguen_teniendo_candidatos():
    """El test que ya salvó de excluir gemini entera por error."""
    for fam in g.VERIFIED_FAMILIES:
        assert g.FAMILY_SPECS.get(fam), f"{fam} verificada y sin candidatos"
        vivos = [c for c in g.FAMILY_SPECS[fam] if c[0] not in g.ROTOS]
        assert vivos, f"{fam} verificada pero todos sus candidatos están rotos"


def test_el_reparto_del_enjambre_apunta_a_familias_vivas():
    for rol, fam in g.DEFAULT_SWARM_FAMILIES.items():
        assert fam in g.FAMILY_SPECS, f"{rol} apunta a {fam}, que no existe"
        vivos = [c for c in g.FAMILY_SPECS[fam] if c[0] not in g.ROTOS]
        assert vivos, f"{rol} apunta a {fam}, sin candidatos vivos"


# ------------------------------------------------- robustez ante un fichero
#                                                    malo
#
# Un catálogo corrupto NO puede dejar al usuario sin aplicación. Ese era el
# riesgo de sacar los datos fuera del código, y es el que estos tests cubren.

@pytest.mark.parametrize("contenido", [
    "{",                                            # truncado
    "[]",                                           # no es objeto
    '{"schemaVersion": 1}',                         # sin familias
    '{"schemaVersion": 99, "familias": {"gpt": {"candidatos": []}}}',
    '{"schemaVersion": 1, "familias": {"gpt": {"candidatos": "no-es-lista"}}}',
])
def test_un_catalogo_malo_no_tumba_nada(tmp_path, monkeypatch, contenido):
    malo = tmp_path / cat.NOMBRE
    malo.write_text(contenido, encoding="utf-8")
    monkeypatch.setattr(cat, "rutas", lambda: [malo])
    c = cat.catalogo(recargar=True)
    assert c.es_respaldo, "un fichero inválido debe caer al respaldo"
    assert c.family_specs
    cat.catalogo(recargar=True)          # deja la caché sana para los demás


def test_el_del_usuario_gana_al_empaquetado(tmp_path, monkeypatch):
    """El objetivo del cambio: arreglar un proveedor sin recompilar."""
    mio = tmp_path / cat.NOMBRE
    mio.write_text(json.dumps({
        "schemaVersion": 1,
        "familias": {"mia": {"verificada": True,
                             "candidatos": [{"proveedor": "P", "modelo": "M"}]}},
        "hedge": {"tras_segundos": 9.5, "maximo": 7},
    }), encoding="utf-8")
    monkeypatch.setattr(cat, "rutas", lambda: [mio, cat._ruta_empaquetada()])
    c = cat.catalogo(recargar=True)
    assert c.family_specs == {"mia": [("P", "M")]}
    assert c.hedge_tras_s == 9.5 and c.hedge_max == 7
    assert not c.es_respaldo
    cat.catalogo(recargar=True)


def test_hay_tope_de_contexto_donde_antes_no_habia_ninguno():
    c = cat.catalogo()
    assert c.ventana_contexto > 0
    assert c.cabe("x" * 100)
    assert not c.cabe("x" * (c.ventana_contexto + 1))
    assert g.VENTANA_CONTEXTO == c.ventana_contexto
