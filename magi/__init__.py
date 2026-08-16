# magi package
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

try:
    __version__ = _version("magi-system-ide")
except PackageNotFoundError:
    # Fuera de pip (PyInstaller, checkout sin instalar): pyproject.toml es
    # la unica fuente. Migraciones lo usa para saber si debe correr.
    __version__ = "0.0.0"
