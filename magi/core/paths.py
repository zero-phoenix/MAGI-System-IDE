"""
Anclaje de rutas (Plan MAGI 9.0 §1.3).

Sustituye las 8 apariciones de "D:/PROYECTOS/MAGI System IDE" que hacían que
el ejecutable publicado en Releases solo funcionara en la máquina del autor.

Toda ruta del sistema se resuelve aquí y solo aquí.
"""
from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path

__all__ = [
    "project_root", "data_dir", "workspace_dir", "journal_dir",
    "db_path", "logs_dir", "cache_dir", "is_frozen", "describe",
]

_ENV_ROOT = "MAGI_ROOT"
_ENV_DATA = "MAGI_DATA_DIR"
_ENV_WORKSPACE = "MAGI_WORKSPACE"


def is_frozen() -> bool:
    """True si corremos dentro de un bundle de PyInstaller."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


@lru_cache(maxsize=1)
def project_root() -> Path:
    """
    Raíz del proyecto MAGI.

    - Bajo PyInstaller: el directorio temporal de extracción (sys._MEIPASS).
    - En desarrollo: dos niveles por encima de este fichero (magi/core/paths.py).
    - Sobrescribible con MAGI_ROOT para tests y despliegues raros.
    """
    override = os.environ.get(_ENV_ROOT)
    if override:
        return Path(override).expanduser().resolve()
    if is_frozen():
        return Path(sys._MEIPASS).resolve()  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def data_dir() -> Path:
    """
    Directorio de datos persistentes del usuario (BD, journal, logs, caché).

    Nunca dentro del bundle: un .exe onefile se extrae en un temporal que se
    borra al salir, así que escribir ahí perdería la base de datos.
    """
    override = os.environ.get(_ENV_DATA)
    if override:
        p = Path(override).expanduser().resolve()
    elif sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
        p = Path(base) / "MagiSystem"
    elif sys.platform == "darwin":
        p = Path.home() / "Library" / "Application Support" / "MagiSystem"
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        p = Path(base) / "magi"
    p.mkdir(parents=True, exist_ok=True)
    return p


@lru_cache(maxsize=1)
def workspace_dir() -> Path:
    """Donde MAGI construye proyectos (antes: .../scratch en una ruta absoluta)."""
    override = os.environ.get(_ENV_WORKSPACE)
    p = Path(override).expanduser().resolve() if override else data_dir() / "workspace"
    p.mkdir(parents=True, exist_ok=True)
    return p


def journal_dir() -> Path:
    """Journal de escrituras para deshacer (§4.2)."""
    p = data_dir() / "journal"
    p.mkdir(parents=True, exist_ok=True)
    return p


def logs_dir() -> Path:
    p = data_dir() / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def cache_dir() -> Path:
    p = data_dir() / "cache"
    p.mkdir(parents=True, exist_ok=True)
    return p


def db_path() -> Path:
    """
    Ruta de magi_brain.db.

    Antes vivía en el CWD y acabó commiteada al repositorio con datos reales
    dentro. Ahora vive en el directorio de datos del usuario.
    """
    return data_dir() / "magi_brain.db"


def describe() -> dict:
    """Volcado para el bloque de contexto de ejecución y para diagnóstico."""
    return {
        "project_root": str(project_root()),
        "data_dir": str(data_dir()),
        "workspace_dir": str(workspace_dir()),
        "db_path": str(db_path()),
        "frozen": is_frozen(),
        "platform": sys.platform,
    }
