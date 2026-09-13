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
    Las DOS pasadas de lint del CI, no solo la barata.

    Este test decía: «el CI hace bloqueante SOLO E9,F63,F7,F82 y deja el resto
    informativo». Dejó de ser verdad el 2026-08-16, cuando el lint completo
    pasó a bloqueante, y `scripts/` entró el 2026-09-06. La compuerta local se
    quedó con la pasada barata y el test lo bendecía: describía un CI que ya no
    existía.

    Lo que costó, medido: el 13-sep-2026 un import sin usar (F401) pasó
    `verificar.py --rapido` en verde y tumbó Actions. La compuerta local decía
    verde donde el CI decía rojo, que es exactamente el fallo contrario al que
    este test vigilaba.
    """
    fuente = _fuente()
    lint_ci = _pasos_ci("lint")

    assert "E9,F63,F7,F82" in fuente
    assert "E9,F63,F7,F82" in lint_ci

    # La pasada completa: mismos paths que el CI, y `scripts/` incluido.
    assert "ruff check magi/ tests/ scripts/" in lint_ci, (
        "el CI ya no hace el lint completo; si es a propósito, este test y "
        "verificar.py cambian juntos")
    # La cadena exacta del comando, no un "scripts/" suelto: ese aparece
    # cuatro veces mas en el fichero (rutas, docstrings) y la asercion pasaba
    # aunque el paso no lo incluyera. Comprobado quitandolo: no fallaba.
    assert '"ruff", "check", "magi/", "tests/", "scripts/"' in fuente, (
        "verificar.py no pasa el lint completo por scripts/, donde viven la "
        "compuerta, el publicador y un trinquete")


def test_el_lint_completo_no_se_mide_con_otra_version_de_ruff():
    """
    Un lint completo con otra versión de ruff no dice si el CI pasará.

    Medido el 13-sep-2026 sobre el mismo árbol, sin tocar una línea: ruff 0.6.9
    (el de la máquina) marca 17 `UP038` que ruff 0.16.5 (el del CI, fijado en
    requirements-dev.txt) no marca. Correr la pasada completa con la versión
    equivocada no es medir de más: es medir otra cosa.

    Por eso el paso lleva precondición y, si las versiones no coinciden, sale
    como NO HECHO —código 2— en vez de como verde. Es la misma distinción que
    el script ya hacía con las herramientas ausentes: «no lo he mirado» no es
    «está bien».
    """
    fuente = _fuente()
    assert "precondicion" in fuente, "el paso del lint completo no la declara"
    assert "_ruff_desalineado" in fuente
    assert "requirements-dev.txt" in fuente, (
        "la version fijada tiene que leerse del pin, no escribirse a mano en "
        "dos sitios")


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
