"""
La versión fuera de pip: pyproject.toml es la única fuente.

El 2-sep-2026 el pie de la interfaz decía «v0.0.0» en un arranque desde
fuente con el sistema en la 5.19: el fallback de `magi/__init__.py` prometía
leer pyproject.toml y devolvía una constante. La suite corre siempre desde
el checkout, así que este test no puede pasar por estar instalado con pip:
si el fallback vuelve a mentir, se pone rojo aquí primero.
"""
import re
from pathlib import Path

import magi


def test_la_version_desde_fuente_es_la_del_pyproject():
    pyproject = Path(magi.__file__).resolve().parent.parent / "pyproject.toml"
    declarada = re.search(r'^version\s*=\s*"([^"]+)"',
                          pyproject.read_text(encoding="utf-8"), re.M).group(1)
    assert magi.__version__ == declarada, (
        f"magi.__version__ dice {magi.__version__!r} y pyproject dice "
        f"{declarada!r}: el fallback de fuente volvió a mentir")
    assert magi.__version__ != "0.0.0", (
        "0.0.0 es la constante de emergencia, no una versión")
