"""
Tests para magi/core/embedded_python.py
"""
import sys
from pathlib import Path

import pytest

from magi.core import embedded_python as ep


def test_embedded_source_in_development():
    """En desarrollo, el embebido apunta a assets/python-embed/extracted."""
    source = ep._embedded_source()
    if source is None:
        pytest.skip("assets/python-embed/extracted no está presente")
    assert (source / "python.exe").is_file()


def test_ensure_embedded_python_returns_exe(tmp_path, monkeypatch):
    """Asegura que ensure_embedded_python extrae/copia y devuelve python.exe."""
    fake_data = tmp_path / "magi-data"
    fake_data.mkdir()

    real_source = ep._embedded_source()
    if real_source is None:
        pytest.skip("no hay fuente embebida")

    monkeypatch.setattr(ep, "embedded_dir", lambda: fake_data / ep._RUNTIME_DIR.name)

    exe = ep.ensure_embedded_python()
    assert exe is not None
    assert Path(exe).is_file()
    assert Path(exe).name == "python.exe"


def test_embedded_python_executable_returns_path():
    exe = ep.embedded_python_executable()
    if exe is None:
        pytest.skip("no hay embebido disponible")
    assert Path(exe).is_file()


def test_python_executable_prefers_embedded_when_frozen(monkeypatch, tmp_path):
    """Cuando está congelado y no hay Python del sistema, usa el embebido."""
    import shutil

    from magi.core.paths import python_executable

    fake_embedded = tmp_path / "python.exe"
    fake_embedded.write_text("fake", encoding="utf-8")

    original_which = shutil.which

    def fake_which(cmd, *args, **kwargs):
        if cmd in ("python", "python3", "py"):
            return None
        return original_which(cmd, *args, **kwargs)

    # Simular estado congelado sin python del sistema
    monkeypatch.setattr("magi.core.paths.is_frozen", lambda: True)
    monkeypatch.setattr("magi.core.paths.sys.frozen", True, raising=False)
    monkeypatch.setattr("magi.core.paths.sys._MEIPASS", str(tmp_path.parent), raising=False)
    monkeypatch.setattr("magi.core.paths.sys.executable", str(tmp_path / "MAGI.exe"))
    monkeypatch.setattr(ep, "embedded_python_executable", lambda: str(fake_embedded))
    monkeypatch.setattr(shutil, "which", fake_which)

    # Limpiar cache de lru_cache
    python_executable.cache_clear()
    try:
        result = python_executable()
        assert result == str(fake_embedded)
    finally:
        python_executable.cache_clear()
