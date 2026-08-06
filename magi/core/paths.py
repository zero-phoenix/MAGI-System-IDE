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
    "python_executable",
]

_ENV_ROOT = "MAGI_ROOT"
_ENV_DATA = "MAGI_DATA_DIR"
_ENV_WORKSPACE = "MAGI_WORKSPACE"


def is_frozen() -> bool:
    """True si corremos dentro de un bundle de PyInstaller."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


@lru_cache(maxsize=1)
def python_executable() -> str | None:
    """
    Un intérprete de Python de VERDAD, o `None` si no hay ninguno.

    EL FALLO QUE ESTO CIERRA, y que solo existe en el binario publicado.
    Dentro de un onefile de PyInstaller, `sys.executable` **es el propio
    .exe**, no un intérprete. Comprobado:

        sys.executable = /tmp/pyi-p/d/probe
        frozen = True

    Media docena de sitios lanzaban `[sys.executable, "-m", "pytest", ...]` o
    `"{sys.executable}" "juego.py"`. En desarrollo funciona porque
    `sys.executable` sí es python. En el .exe que se descarga de Releases,
    cada una de esas llamadas **relanza MAGI entero**:

      · `run_test_suite` y `_local_build` (la puerta previa a publicar):
        MAGI-IDE-v5.exe -m pytest -> arranca otra GUI y otro servidor.
      · `observe_program`, `observe_game`, `capture_program`: el bucle de
        observación del §5 acababa mirando a MAGI en vez de al artefacto que
        acababa de generar.

    Ninguno daba error: daban resultados de otro programa. Que es peor.

    Devuelve `None` en vez de caer a `sys.executable` a propósito: quien no
    tenga Python instalado necesita que se lo digan, no que el sistema haga
    algo raro en silencio. Quinta regla del proyecto.
    """
    if not is_frozen():
        return sys.executable

    import shutil
    import subprocess

    for nombre in ("python3", "python"):
        ruta = shutil.which(nombre)
        if ruta and Path(ruta).resolve() != Path(sys.executable).resolve():
            return ruta

    # Windows: el lanzador `py` existe aunque `python` no esté en el PATH.
    if sys.platform == "win32":
        lanzador = shutil.which("py")
        if lanzador:
            try:
                r = subprocess.run([lanzador, "-3", "-c",
                                    "import sys; print(sys.executable)"],
                                   capture_output=True, text=True, timeout=15)
                salida = r.stdout.strip()
                if r.returncode == 0 and salida and Path(salida).exists():
                    return salida
            except Exception:
                pass
    return None


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
