# magi package
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

try:
    # El nombre de la distribucion, que es el de `[project].name` en
    # pyproject.toml. Al renombrar el producto a Magisys este quedo pidiendo
    # "magi-system-ide", que ya no existe: no rompia nada porque el respaldo
    # de abajo lee pyproject, pero entonces la rama de pip no se usaba nunca
    # y un fallo suyo habria pasado inadvertido.
    __version__ = _version("Magisys")
except PackageNotFoundError:
    # Fuera de pip (PyInstaller, checkout sin instalar): pyproject.toml es
    # la unica fuente. Migraciones lo usa para saber si debe correr, y el
    # pie de la interfaz pinta exactamente esto — el 2-sep-2026 decia
    # "v0.0.0" en un arranque desde fuente con el sistema en la 5.19: el
    # comentario de aqui abajo prometia leer pyproject y el codigo no lo
    # hacia. Python 3.10 no trae tomllib, de ahi el regex.
    import re
    from pathlib import Path

    try:
        _pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        __version__ = re.search(
            r'^version\s*=\s*"([^"]+)"',
            _pyproject.read_text(encoding="utf-8"), re.M).group(1)
    except Exception:
        __version__ = "0.0.0"
