import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """
    Aísla data_dir/workspace por test.

    Sin esto los tests escribirían en %LOCALAPPDATA%\\MagiSystem del usuario,
    que es exactamente el tipo de efecto colateral que v5.0.28 tenía por todas
    partes (magi_brain.db en el CWD, scratch en una ruta absoluta).
    """
    monkeypatch.setenv("MAGI_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("MAGI_WORKSPACE", str(tmp_path / "ws"))
    from magi.core import paths
    for fn in (paths.project_root, paths.data_dir, paths.workspace_dir):
        fn.cache_clear()
    yield
    for fn in (paths.project_root, paths.data_dir, paths.workspace_dir):
        fn.cache_clear()


@pytest.fixture
def anyio_backend():
    return "asyncio"
