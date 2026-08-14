"""
La verificación local tiene que hacer LO MISMO que el CI, no algo parecido.

POR QUÉ IMPORTA TANTO
=====================
`scripts/verificar.py` existe porque el CI dejó de arrancar —repositorio
privado, minutos agotados— y con él se cayó la regla que sostiene el proyecto:
«sin tests verdes no hay release». Si la comprobación local y la del CI se
separan, se obtiene lo peor de las dos: verde en casa y rojo al publicar, o al
revés, y en cualquiera de los dos casos se deja de confiar en las dos.

Estos tests comparan los dos ficheros. Es aburrido y es exactamente el tipo de
cosa que nadie recuerda actualizar a mano — que es justo el motivo de
automatizarlo.
"""
from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

RAIZ = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = RAIZ / "scripts/verificar.py"
CI = RAIZ / ".github/workflows/ci.yml"


def _fuente() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def _pasos_ci(job: str) -> str:
    ci = yaml.safe_load(CI.read_text(encoding="utf-8"))
    return "\n".join(str(s.get("run", "")) for s in ci["jobs"][job]["steps"])


def test_el_script_existe_y_se_puede_ejecutar():
    assert SCRIPT.is_file()
    import ast
    ast.parse(_fuente())          # que al menos sea Python válido


def test_comprueba_lo_mismo_que_el_lint_del_CI():
    """
    El CI hace bloqueante SOLO `E9,F63,F7,F82` —errores de sintaxis y nombres
    indefinidos— y deja el resto informativo. Si aquí se exigiera más, el
    script diría rojo donde el CI dice verde, y se dejaría de usar.
    """
    assert "E9,F63,F7,F82" in _fuente()
    assert "E9,F63,F7,F82" in _pasos_ci("lint")


def test_comprueba_lo_mismo_que_los_tests_del_CI():
    """Mismo selector de marcas: sin los que compilan, salvo con `--todo`."""
    fuente = _fuente()
    assert "not slow" in fuente
    assert "not slow" in _pasos_ci("test")
    assert "--todo" in fuente, (
        "sin una forma de incluir los lentos, no hay manera local de "
        "reproducir lo que `release.yml` exige antes de publicar")


def test_comprueba_los_imports_del_nucleo_igual_que_el_CI():
    """
    El paso que caza el fallo más caro: un módulo del núcleo que no importa
    deja la aplicación sin arrancar, y no lo detecta ningún test unitario
    porque los tests importan lo que necesitan, no todo.
    """
    fuente = _fuente()
    for modulo in ("magi.core.paths", "magi.core.router",
                   "magi.core.providers.registry", "magi.core.tools"):
        assert modulo in fuente, f"falta {modulo}"
        assert modulo in _pasos_ci("test")


def test_incluye_la_interfaz_como_el_CI():
    fuente = _fuente()
    assert '"test"' in fuente and '"build"' in fuente
    gui = _pasos_ci("gui")
    assert "npm test" in gui and "npm run build" in gui


def test_devuelve_codigo_distinto_de_cero_si_algo_falla():
    """
    Sin esto no se puede encadenar con `&&` antes de un `git push`, que es
    justo para lo que sirve. Un verificador que siempre devuelve 0 informa,
    pero no protege.
    """
    fuente = _fuente()
    assert "return 1" in fuente
    assert "SystemExit(main())" in fuente


def test_un_paso_que_no_se_pudo_ejecutar_NO_cuenta_como_verde():
    """
    Si falta `npm`, el paso de la interfaz no se ejecuta. Marcarlo como OK
    sería la mentira más peligrosa de todas: verde por no haber mirado.
    """
    fuente = _fuente()
    assert "SALTADO" in fuente, (
        "un paso no ejecutado tiene que distinguirse de uno que pasó")


def test_la_salida_es_imprimible_en_cualquier_consola():
    """
    Quinta vez que cp1252 aparece en este proyecto. Una herramienta que
    revienta justo cuando la usas para diagnosticar añade un problema encima
    del que investigabas.
    """
    # Se EJECUTA la función en vez de buscar su código: la primera versión de
    # este test comparaba cadenas del fuente y dependía de cómo estuviera
    # partida la línea. Un guardián que se rompe con un salto de línea no
    # vigila el comportamiento, vigila el formateo.
    import importlib.util

    spec = importlib.util.spec_from_file_location("verificar_local", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    salida = modulo.plegar("conexión ✓ 中文 ñandú 🚀")
    salida.encode("cp1252")        # la consola de Windows por defecto
    salida.encode("ascii")         # y el caso más restrictivo
    assert "conexion" in salida, "plegar el acento, no borrar la palabra"


def test_el_readme_dice_como_verificar_sin_CI():
    """
    Un script que nadie sabe que existe no protege nada, y ahora mismo es la
    ÚNICA forma de comprobar el proyecto: el CI no arranca.
    """
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    assert "scripts/verificar.py" in readme
