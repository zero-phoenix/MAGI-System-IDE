"""
Ningún script de `scripts/` puede tocar g4f sin instalar antes `no_browser`.

POR QUÉ EXISTE ESTE FICHERO
==========================
El sistema tiene el cortafuegos §I.3 puesto y bien probado: `no_browser` tapa
CDP, nodriver, `webbrowser` y `Popen`, y hay tests que comprueban las cuatro
capas. Todo eso vale para el sistema.

No valía para un script.

`scripts/barrer_proveedores.py`, escrito para medir proveedores, llamaba a los
parches de compatibilidad pero no instalaba el cortafuegos. Al llegar a
`Cloudflare`, g4f hizo lo que hace —`CDPSession(headless=False)`— y **se abrió
una ventana de Chrome titulada «AI Playground» en la máquina del usuario**.

La regla del proyecto es que la única ventana es la interfaz de MAGI. Se rompió
por la puerta de al lado: no por un fallo del cortafuegos, sino porque había
código que no pasaba por él.

LA FORMA DEL GUARDIÁN
=====================
Se lee el FUENTE, con AST, y se comprueba el ORDEN: si un script importa g4f,
la llamada a `install()` tiene que aparecer antes. No se ejecuta el script
—ejecutarlo es justo lo que abriría la ventana— y no se busca texto suelto,
que confundiría un comentario con código.

Es el mismo patrón que `test_nunca_se_lanza_con_ventana`: cuando la consecuencia
de equivocarse es irreversible y visible para el usuario, el guardián mira el
código, no el comportamiento.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

RAIZ = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = sorted((RAIZ / "scripts").glob("*.py"))

#: Nombres cuya importación significa «a partir de aquí se puede abrir un
#: navegador». `g4f` es el evidente; los otros dos son las vías directas.
_PELIGROSOS = ("g4f", "nodriver", "playwright", "camoufox")

#: Lo que cuenta como haber instalado el cortafuegos.
#:
#: Se acepta cualquier nombre que contenga «cortafuegos» y no una lista
#: cerrada: la primera versión enumeraba `instalar_cortafuegos` y falló al
#: renombrarlo a `_instalar_cortafuegos` —un guion bajo—, informando de que el
#: script «NUNCA instala el cortafuegos» cuando lo instalaba en la línea 62.
#:
#: Un guardián que da un falso positivo por un guion bajo enseña a ignorarlo, y
#: este vigila la regla que no se puede romper ni una vez.
_INSTALADORES_EXACTOS = ("install", "_disable_g4f_browser")


def _es_instalador(nombre: str) -> bool:
    return nombre in _INSTALADORES_EXACTOS or "cortafuegos" in nombre


def _linea_de_instalacion(arbol: ast.AST) -> int | None:
    """Primera línea en la que se INVOCA al instalador. None si no se invoca."""
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        nombre = getattr(nodo.func, "id", getattr(nodo.func, "attr", ""))
        if _es_instalador(nombre):
            return nodo.lineno
    return None


def _linea_de_import_peligroso(arbol: ast.AST) -> tuple[int, str] | None:
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for a in nodo.names:
                if a.name.split(".")[0] in _PELIGROSOS:
                    return nodo.lineno, a.name
        elif isinstance(nodo, ast.ImportFrom):
            raiz = (nodo.module or "").split(".")[0]
            if raiz in _PELIGROSOS:
                return nodo.lineno, nodo.module or ""
    return None


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_si_toca_g4f_instala_el_cortafuegos_antes(script: pathlib.Path):
    arbol = ast.parse(script.read_text(encoding="utf-8"))

    peligroso = _linea_de_import_peligroso(arbol)
    if peligroso is None:
        return                                  # no toca g4f: nada que exigir

    linea_import, que = peligroso
    linea_install = _linea_de_instalacion(arbol)

    assert linea_install is not None, (
        f"{script.name} importa `{que}` (línea {linea_import}) y NUNCA instala "
        f"el cortafuegos.\n"
        f"\n"
        f"Esto no es teórico: por esta puerta se abrió una ventana de Chrome "
        f"«AI Playground» en la máquina del usuario. La regla del proyecto es "
        f"que la única ventana es la interfaz de MAGI.\n"
        f"\n"
        f"Pon esto ANTES de importar g4f:\n"
        f"    from magi.core.no_browser import install as instalar_cortafuegos\n"
        f"    instalar_cortafuegos()")

    assert linea_install < linea_import, (
        f"{script.name} instala el cortafuegos en la línea {linea_install}, "
        f"DESPUÉS de importar `{que}` en la {linea_import}.\n"
        f"El orden importa: importar g4f ya deja el módulo cargado con sus "
        f"propias rutas, y algunos proveedores abren el navegador en la "
        f"primera llamada. Instalar después es llegar tarde.")


def test_el_guardian_vigila_algo():
    """
    Un test parametrizado sobre una lista vacía pasa siempre y no comprueba
    nada. Si `scripts/` se renombra o se mueve, esto lo dice en vez de quedarse
    verde en silencio.
    """
    assert SCRIPTS, "no encuentro los scripts: ¿se movió la carpeta?"
    assert any(_linea_de_import_peligroso(ast.parse(s.read_text(encoding="utf-8")))
               for s in SCRIPTS), (
        "ningún script toca g4f: o es cierto, o el detector dejó de detectar")
