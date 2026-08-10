"""
Test E2E: flujo Tetris -> .exe portable.

Construye un pequeño juego pygame, lo empaqueta con build_project_exe y
verifica que el ejecutable resultante existe y arranca (headless) en una
máquina Windows sin depender del Python de desarrollo.
"""
import asyncio
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from magi.core.paths import python_executable
from magi.core.tools.builtin import ToolContext, build_registry
from magi.modules.studio.packager import build_project_exe


TETRIS_MAIN = r'''
import sys
import pygame

pygame.init()
screen = pygame.display.set_mode((200, 200))
clock = pygame.time.Clock()
running = True
frames = 0
while running and frames < 5:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill((0, 0, 0))
    pygame.display.flip()
    clock.tick(5)
    frames += 1
pygame.quit()
print("TETRIS_OK")
sys.exit(0)
'''


@pytest.fixture
def tetris_project(tmp_path):
    project = tmp_path / "tetris_demo"
    project.mkdir()
    (project / "main.py").write_text(TETRIS_MAIN, encoding="utf-8")
    (project / "requirements.txt").write_text("pygame\n", encoding="utf-8")
    return project


@pytest.mark.slow
@pytest.mark.timeout(300)
@pytest.mark.asyncio
async def test_build_tetris_executable(tetris_project, tmp_path):
    """Empaqueta un Tetris pygame mínimo y verifica el .exe resultante."""
    exe_path = tmp_path / "TetrisDemo.exe"
    result = await build_project_exe(
        tetris_project,
        entry="main.py",
        output_exe=exe_path,
        name="TetrisDemo",
        console=False,
    )
    assert result.ok, f"build_project_exe falló: {result.error}"
    assert exe_path.is_file(), f"no se generó el .exe en {exe_path}"

    # El .exe debe arrancar y salir limpio en modo headless (el juego solo
    # corre 5 fotogramas y sale solo).
    proc = await asyncio.create_subprocess_exec(
        str(exe_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=30.0)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise AssertionError("el .exe del Tetris no terminó en 30s")

    output = (stdout.decode(errors="ignore") +
              stderr.decode(errors="ignore")).strip()
    assert proc.returncode == 0, (
        f"el .exe del Tetris terminó con código {proc.returncode}: {output}")
    assert "TETRIS_OK" in output, (
        f"el .exe del Tetris no imprimió TETRIS_OK: {output}")


@pytest.mark.slow
@pytest.mark.timeout(300)
def test_build_tetris_via_tool_registry(tetris_project, tmp_path):
    """Invoca build_project_exe a través del registro real de herramientas."""
    registry = build_registry()
    ctx = ToolContext(task_id="e2e_tetris", cwd=tmp_path)

    result = asyncio.run(registry.execute("build_project_exe", {
        "path": str(tetris_project),
        "entry": "main.py",
        "output": str(tmp_path / "TetrisTool.exe"),
        "name": "TetrisTool",
    }, ctx=ctx))

    assert result.ok, f"tool build_project_exe falló: {result.error}"
    exe = tmp_path / "TetrisTool.exe"
    assert exe.is_file()


@pytest.mark.skipif(not sys.platform.startswith("win"),
                    reason="solo Windows onefile")
def test_python_executable_returns_interpreter():
    """Hay un intérprete Python disponible para empaquetar."""
    exe = python_executable()
    assert exe is not None
    assert Path(exe).is_file()
