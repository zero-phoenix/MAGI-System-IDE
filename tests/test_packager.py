"""
Tests para magi/modules/studio/packager.py
"""
import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

from magi.modules.studio.packager import (
    _find_entry,
    _looks_like_gui,
    _read_requirements,
    build_project_exe,
)


@pytest.fixture
def hello_project(tmp_path: Path):
    """Proyecto Python simple con main.py que imprime un saludo."""
    p = tmp_path / "hello"
    p.mkdir()
    (p / "main.py").write_text(
        'print("HOLA_MAGI")\n',
        encoding="utf-8",
    )
    return p


@pytest.fixture
def pygame_project(tmp_path: Path):
    """Proyecto con pygame para comprobar detección de GUI."""
    p = tmp_path / "pygame_dummy"
    p.mkdir()
    (p / "main.py").write_text(
        "import pygame\npygame.init()\nprint('ok')\n",
        encoding="utf-8",
    )
    return p


def test_find_entry_default(hello_project: Path):
    assert _find_entry(hello_project, None) == hello_project / "main.py"


def test_find_entry_explicit(hello_project: Path):
    assert _find_entry(hello_project, "main.py") == hello_project / "main.py"


def test_find_entry_missing(hello_project: Path):
    assert _find_entry(hello_project, "no_existe.py") is None


def test_looks_like_gui_pygame(pygame_project: Path):
    assert _looks_like_gui(pygame_project / "main.py") is True


def test_looks_like_gui_console(hello_project: Path):
    assert _looks_like_gui(hello_project / "main.py") is False


def test_read_requirements(tmp_path: Path):
    p = tmp_path / "req_proj"
    p.mkdir()
    (p / "requirements.txt").write_text("requests\n# comentario\n", encoding="utf-8")
    assert _read_requirements(p) == ["requests"]


@pytest.mark.skipif(sys.platform != "win32", reason=".exe solo en Windows")
@pytest.mark.slow
@pytest.mark.timeout(300)
def test_build_project_exe_console_hello(hello_project: Path, tmp_path: Path):
    out = tmp_path / "Hello.exe"
    result = asyncio.run(build_project_exe(
        hello_project,
        output_exe=out,
        name="Hello",
        timeout=240,
    ))
    assert result.ok, result.error
    assert result.exe_path is not None
    assert out.is_file()
    # El exe generado debe pesar algo (no vacío)
    assert out.stat().st_size > 1_000_000


@pytest.mark.skipif(sys.platform != "win32", reason=".exe solo en Windows")
@pytest.mark.slow
@pytest.mark.timeout(300)
def test_build_project_exe_detects_gui(pygame_project: Path, tmp_path: Path):
    out = tmp_path / "DummyGame.exe"
    result = asyncio.run(build_project_exe(
        pygame_project,
        output_exe=out,
        name="DummyGame",
        timeout=240,
    ))
    # Puede fallar si pygame no está en el venv, pero no debe fallar por un
    # motivo de infraestructura. Aceptamos éxito o error de importación claro.
    if result.ok:
        assert out.is_file()
        assert out.stat().st_size > 1_000_000
    else:
        # Si falla, el error debe ser legible y contener la ruta del proyecto.
        assert pygame_project.name in result.error or "PyInstaller" in result.error


def test_build_project_exe_missing_dir(tmp_path: Path):
    result = asyncio.run(build_project_exe(tmp_path / "no_existe"))
    assert not result.ok
    assert "no es un directorio" in result.error
