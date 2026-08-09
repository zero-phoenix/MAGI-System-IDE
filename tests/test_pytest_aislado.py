"""
Dos corridas de pytest a la vez no se pisan.

EL FALLO, MEDIDO
================
MAGI lanza pytest desde tres sitios: la herramienta `run_tests` con la que
Balthasar critica habiendo ejecutado, la verificación de Naoko antes de
reparar, y la compuerta de publicación. Los tres invocaban `pytest` a secas.

pytest guarda los `tmp_path` en `<temp>/pytest-of-<usuario>/pytest-N` y, al
arrancar, BORRA las corridas antiguas para no dejar basura. Con dos procesos
solapados el segundo borra el directorio del primero mientras lo usa. En la
máquina del usuario, con MAGI abierto y la suite corriendo a la vez:

    732 ERROR ... FileNotFoundError: [WinError 3] No se puede encontrar la
    ruta especificada: 'C:\\...\\Temp\\pytest-of-D\\pytest-2'

Casi todos los tests usan `tmp_path`, así que cayeron casi todos. Y lo peor no
fue el fallo, sino lo que Naoko dedujo de él:

    [naoko] la suite ya estaba roja antes de tocar nada

Se abstuvo de reparar por un diagnóstico falso que había producido su propia
verificación. Es el corolario del proyecto en estado puro: **el instrumento de
medida es el mejor escondite**, y aquí además rompía lo que medía.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from magi.core import paths

RAIZ = Path(__file__).resolve().parents[1]


def _argv():
    argv = paths.pytest_argv("tests")
    if argv is None:
        pytest.skip("no hay intérprete de Python resoluble en este entorno")
    return argv


def test_cada_corrida_pide_su_propio_directorio_temporal():
    argv = _argv()
    basetemps = [a for a in argv if a.startswith("--basetemp=")]
    assert len(basetemps) == 1, (
        "sin --basetemp, dos corridas comparten <temp>/pytest-of-<usuario> y "
        "la que arranca después borra el tmp de la que ya estaba dentro")
    assert "pytest" in argv and "-q" in argv


def test_dos_corridas_seguidas_no_comparten_directorio():
    """
    Dos llamadas dan rutas distintas. Es toda la propiedad que hace falta.

    Si coincidieran, el aislamiento sería decorativo: el segundo proceso
    borraría el directorio del primero exactamente igual que antes.
    """
    a = [x for x in _argv() if x.startswith("--basetemp=")][0]
    b = [x for x in _argv() if x.startswith("--basetemp=")][0]
    assert a != b, "dos corridas no pueden apuntar al mismo directorio"


def test_el_temporal_vive_bajo_los_datos_de_magi_y_no_en_el_repositorio():
    """
    Ni en el repositorio ni en el CWD: eso ya pasó con `magi_brain.db`, que
    acabó versionado con datos reales dentro.
    """
    ruta = Path([x for x in _argv() if x.startswith("--basetemp=")][0]
                .split("=", 1)[1])
    assert paths.data_dir() in ruta.parents, (
        f"{ruta} debería colgar del directorio de datos de MAGI")
    assert RAIZ not in ruta.parents, "el tmp de pytest no va en el repositorio"


def test_la_poda_no_puede_impedir_correr_los_tests(tmp_path):
    """
    Con --basetemp explícito pytest deja de limpiar por su cuenta, así que la
    poda la hacemos nosotros. Y como toda limpieza, no puede tener autoridad
    para tumbar aquello que limpia: si falla, se sigue.
    """
    inexistente = tmp_path / "no" / "existe"
    paths._poda_temporales(inexistente)          # no debe lanzar

    viejo = tmp_path / "run-antiguo"
    viejo.mkdir()
    (viejo / "x.txt").write_text("basura", encoding="utf-8")
    import os
    import time
    antiguo = time.time() - 48 * 3600
    os.utime(viejo, (antiguo, antiguo))

    nuevo = tmp_path / "run-reciente"
    nuevo.mkdir()

    paths._poda_temporales(tmp_path)
    assert not viejo.exists(), "las corridas viejas se borran"
    assert nuevo.exists(), "las recientes se quedan: pueden estar en uso"


@pytest.mark.parametrize("fichero,pista", [
    ("magi/core/tools/builtin.py", "run_tests de Balthasar"),
    ("magi/modules/infrastructure/naoko_repair.py", "verificación de reparación"),
    ("magi/modules/infrastructure/naoko.py", "compuerta de publicación"),
])
def test_los_tres_sitios_que_lanzan_pytest_usan_el_helper(fichero, pista):
    """
    Tres invocaciones a mano son tres oportunidades de que una se quede atrás.

    Es el mismo patrón que ya costó dos releases con la lista de dependencias
    escrita a mano en dos workflows: la copia duplicada SIEMPRE se queda atrás,
    y la única cura es que no haya copia.
    """
    texto = (RAIZ / fichero).read_text(encoding="utf-8")
    assert "pytest_argv" in texto, (
        f"{fichero} ({pista}) debe lanzar pytest con paths.pytest_argv(), no "
        f"a mano: sin --basetemp vuelve a colisionar con las otras corridas")
    suelto = re.search(r'["\']-m["\']\s*,\s*["\']pytest["\']', texto)
    assert not suelto, (
        f"{fichero} sigue construyendo la orden de pytest a mano en "
        f"la línea {texto[:suelto.start()].count(chr(10)) + 1 if suelto else 0}")
