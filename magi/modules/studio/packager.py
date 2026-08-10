"""
Empaquetado de proyectos Python a ejecutables .exe portables.

Plan MAGI 9.0 §5.5 — extiende la fábrica de artefactos para producir
binarios onefile que se ejecuten sin Python en el sistema destino.
"""
from __future__ import annotations

import asyncio
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import logging

from ...core.paths import python_executable, data_dir

logger = logging.getLogger(__name__)

_GUI_MARKERS = re.compile(
    r"\b(import\s+pygame|from\s+pygame|"
    r"import\s+tkinter|from\s+tkinter|"
    r"import\s+turtle|from\s+turtle|"
    r"import\s+PyQt|from\s+PyQt|"
    r"import\s+PySide|from\s+PySide|"
    r"\.mainloop\s*\()\b",
    re.IGNORECASE,
)


def _looks_like_gui(entry_path: Path) -> bool:
    """Heurística para decidir si el programa abre una ventana."""
    try:
        text = entry_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    return bool(_GUI_MARKERS.search(text))


def _find_entry(project_dir: Path, entry: str | None) -> Path | None:
    if entry:
        p = project_dir / entry
        if p.is_file():
            return p
        return None
    for name in ("main.py", "app.py", "run.py", f"{project_dir.name}.py"):
        p = project_dir / name
        if p.is_file():
            return p
    # Fallback: primer .py de nivel superior
    for p in sorted(project_dir.iterdir()):
        if p.is_file() and p.suffix == ".py":
            return p
    return None


def _read_requirements(project_dir: Path) -> list[str]:
    for name in ("requirements.txt", "requirements.lock"):
        p = project_dir / name
        if p.is_file():
            try:
                lines = p.read_text(encoding="utf-8").splitlines()
                return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]
            except Exception:
                pass
    return []


@dataclass
class PackagerResult:
    ok: bool
    exe_path: Path | None = None
    content: str = ""
    error: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_tool_result(self) -> "ToolResult":  # type: ignore[name-defined]
        from ...core.tools.registry import ToolResult
        return ToolResult(
            ok=self.ok,
            content=self.content,
            error=self.error,
            meta=self.meta,
        )


async def _run(
    cmd: list[str],
    cwd: Path,
    timeout: float = 600.0,
    env: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    """Ejecuta un comando y devuelve (rc, stdout, stderr)."""
    merged_env = {**os.environ, **(env or {})}
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(cwd),
            env=merged_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout)
        return (
            proc.returncode or 0,
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
        )
    except asyncio.TimeoutError:
        try:
            proc.kill()
            await proc.wait()
        except Exception:
            pass
        return 124, "", f"timeout tras {timeout}s"


async def build_project_exe(
    project_dir: Path,
    *,
    entry: str | None = None,
    output_exe: Path | None = None,
    name: str | None = None,
    icon: Path | None = None,
    console: bool | None = None,
    clean: bool = True,
    requirements: list[str] | None = None,
    datas: list[tuple[str, str]] | None = None,
    hiddenimports: list[str] | None = None,
    python_exe: str | None = None,
    timeout: float = 600.0,
) -> PackagerResult:
    """
    Empaqueta un proyecto Python en un .exe onefile portable.

    Si ``python_exe`` es None, usa ``python_executable()`` (sistema o embebido).
    Instala dependencias en un venv temporal bajo ``data_dir()``.
    """
    project_dir = Path(project_dir).resolve()
    if not project_dir.is_dir():
        return PackagerResult(False, error=f"no es un directorio: {project_dir}")

    entry_path = _find_entry(project_dir, entry)
    if entry_path is None:
        return PackagerResult(
            False, error=f"no se encontró punto de entrada en {project_dir}")

    if name is None:
        name = project_dir.name or "output"
    # Sanitizar nombre para evitar espacios y caracteres raros en --name
    name = re.sub(r"[^\w\-_.]", "_", name).strip("._") or "output"

    if console is None:
        console = not _looks_like_gui(entry_path)

    interpreter = python_exe or python_executable()
    if interpreter is None:
        return PackagerResult(
            False,
            error=(
                "no se encontró intérprete Python. "
                "Instala Python o incluye el intérprete embebido en el bundle."
            ),
        )
    interpreter = str(Path(interpreter).resolve())

    # Entorno virtual temporal bajo data_dir para no contaminar el sistema
    venv_id = f"magi-pkg-{uuid.uuid4().hex[:12]}"
    venv_dir = data_dir() / "packager-venvs" / venv_id
    venv_dir.mkdir(parents=True, exist_ok=True)

    # Directorio de trabajo de PyInstaller
    work_base = data_dir() / "packager-builds" / venv_id
    work_base.mkdir(parents=True, exist_ok=True)

    dist_dir = work_base / "dist"
    build_dir = work_base / "build"

    logs: list[str] = []

    try:
        # 1) Crear venv
        logs.append(f"Creando venv temporal: {venv_dir}")
        rc, out, err = await _run(
            [interpreter, "-m", "venv", str(venv_dir)],
            cwd=project_dir,
            timeout=120,
        )
        if rc != 0:
            return PackagerResult(
                False,
                error=f"no se pudo crear el venv:\n{out}\n{err}",
            )

        venv_python = venv_dir / ("Scripts" if sys.platform == "win32" else "bin") / "python.exe"
        if sys.platform != "win32":
            venv_python = venv_dir / "bin" / "python"

        # 2) Asegurar PyInstaller
        logs.append("Instalando/actualizando PyInstaller en el venv")
        rc, out, err = await _run(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pyinstaller"],
            cwd=project_dir,
            timeout=180,
        )
        if rc != 0:
            return PackagerResult(
                False,
                error=f"no se pudo instalar PyInstaller:\n{out}\n{err}",
            )

        # 3) Instalar requirements del proyecto
        reqs = list(requirements or [])
        reqs.extend(_read_requirements(project_dir))
        if reqs:
            logs.append(f"Instalando dependencias: {', '.join(reqs[:10])}")
            rc, out, err = await _run(
                [str(venv_python), "-m", "pip", "install", "--upgrade", *reqs],
                cwd=project_dir,
                timeout=300,
            )
            if rc != 0:
                return PackagerResult(
                    False,
                    error=f"falló instalación de dependencias:\n{out}\n{err}",
                )

        # 4) Construir argumentos de PyInstaller
        args = [
            str(venv_python), "-m", "PyInstaller",
            "--clean",
            "--onefile",
            "--noconsole" if not console else "--console",
            "--name", name,
            "--distpath", str(dist_dir),
            "--workpath", str(build_dir),
            "--specpath", str(work_base),
        ]

        if icon and Path(icon).is_file():
            args.extend(["--icon", str(icon)])

        for src, dst in (datas or []):
            src_p = project_dir / src if not Path(src).is_absolute() else Path(src)
            args.extend(["--add-data", f"{src_p}{os.pathsep}{dst}"])

        for mod in (hiddenimports or []):
            args.extend(["--hidden-import", mod])

        args.append(str(entry_path))

        logs.append(f"Ejecutando PyInstaller: {' '.join(args[:12])} ...")
        rc, out, err = await _run(
            args,
            cwd=project_dir,
            timeout=timeout,
        )
        full_output = f"{out}\n{err}".strip()
        if rc != 0:
            return PackagerResult(
                False,
                error=f"PyInstaller falló (rc={rc}):\n{full_output[:4000]}",
                meta={"pyinstaller_output": full_output[:8000]},
            )

        exe_name = f"{name}.exe" if sys.platform == "win32" else name
        built_exe = dist_dir / exe_name
        if not built_exe.is_file():
            return PackagerResult(
                False,
                error=(
                    f"PyInstaller terminó pero no se encontró el .exe esperado "
                    f"en {built_exe}"
                ),
                meta={"pyinstaller_output": full_output[:8000]},
            )

        final_exe = output_exe or built_exe
        if output_exe and output_exe.resolve() != built_exe.resolve():
            final_exe.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(built_exe, final_exe)
            logs.append(f"Copiado a: {final_exe}")
        else:
            final_exe = built_exe
            logs.append(f"Generado: {final_exe}")

        return PackagerResult(
            True,
            exe_path=final_exe,
            content="\n".join(logs) + f"\n{final_exe} ({final_exe.stat().st_size} bytes)",
            meta={
                "exe": str(final_exe),
                "size": final_exe.stat().st_size,
                "pyinstaller_output": full_output[:4000],
            },
        )

    finally:
        if clean:
            shutil.rmtree(venv_dir, ignore_errors=True)
            shutil.rmtree(work_base, ignore_errors=True)
