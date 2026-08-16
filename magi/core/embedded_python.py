"""
Gestión del intérprete Python embebido para el bundle de MAGI.

Plan MAGI 9.0 §1.3 — dentro de un .exe de PyInstaller no hay intérprete Python
real, así que el bundle debe traer el suyo propio para ejecutar/empaquetar
código Python generado sin depender de la máquina destino.
"""
from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path

from .paths import data_dir, is_frozen, project_root

logger = logging.getLogger(__name__)

_EMBEDDED_DIR = Path("assets") / "python-embed" / "extracted"
_RUNTIME_DIR = Path("embedded-python")


def _embedded_source() -> Path | None:
    """Ruta al Python embebido dentro del bundle o en desarrollo."""
    if is_frozen():
        root = Path(getattr(sys, "_MEIPASS", ""))
    else:
        root = project_root()
    candidate = root / _EMBEDDED_DIR
    if candidate.is_dir() and (candidate / "python.exe").is_file():
        return candidate
    return None


def embedded_dir() -> Path:
    """Directorio donde vive el intérprete embebido en runtime."""
    return data_dir() / _RUNTIME_DIR


def ensure_embedded_python() -> Path | None:
    """
    Asegura que existe un intérprete Python embebido usable en disco.

    Si corre como bundle, copia (o sincroniza) el contenido empaquetado a
    ``data_dir()/embedded-python``. En desarrollo apunta al directorio extraído.
    Devuelve la ruta al ``python.exe`` o None si no hay embebido disponible.
    """
    source = _embedded_source()
    if source is None:
        logger.debug("[embedded_python] no hay fuente embebida")
        return None

    target = embedded_dir()
    python_exe = target / "python.exe"

    # Evitar copiar innecesariamente: si ya existe python.exe, está listo.
    if python_exe.is_file():
        return python_exe

    logger.info("[embedded_python] extrayendo intérprete a %s", target)
    target.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copytree(source, target, dirs_exist_ok=True)
    except Exception as e:
        logger.warning("[embedded_python] no se pudo copiar el embebido: %s", e)
        return None

    if python_exe.is_file():
        return python_exe
    return None


def embedded_python_executable() -> str | None:
    """Devuelve la ruta al python.exe embebido si está disponible."""
    exe = ensure_embedded_python()
    return str(exe) if exe else None


def embedded_pip_executable() -> str | None:
    """Ruta a pip del embebido, si existe."""
    exe = ensure_embedded_python()
    if exe is None:
        return None
    pip = exe.parent / "Scripts" / "pip.exe"
    if pip.is_file():
        return str(pip)
    return None


def ensure_pyinstaller(timeout: float = 120.0) -> bool:
    """Asegura que el embebido tiene PyInstaller instalado."""
    python = embedded_python_executable()
    if python is None:
        return False
    try:
        import subprocess  # noqa: PLC0415
        r = subprocess.run(
            [python, "-c", "import PyInstaller"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            return True
    except Exception as e:
        logger.warning("[embedded_python] error comprobando PyInstaller: %s", e)

    pip = embedded_pip_executable()
    if pip is None:
        return False
    try:
        import subprocess  # noqa: PLC0415
        subprocess.run(
            [pip, "install", "pyinstaller"],
            capture_output=True, timeout=timeout, check=True,
        )
        return True
    except Exception as e:
        logger.warning("[embedded_python] no se pudo instalar PyInstaller: %s", e)
    return False
