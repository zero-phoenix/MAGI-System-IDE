"""
Ciclo de reparación verificada de Naoko (Plan MAGI 9.0 §3.1-§3.3).

QUÉ HACÍA NAOKO EN v5.0.28 (naoko.py:117-247)
=============================================
    error -> pedir script a un LLM -> powershell -File <script>  (sin revisar)
          -> git add .  -> commit -> tag -> git push origin HEAD

Sin reproducir el fallo, sin tests, sin comprobar si el parche arregló algo,
sin poder deshacerlo. `git add .` arrastraba cualquier cosa del árbol.

DAÑO REAL Y DOCUMENTADO
=======================
Commit 1eb7e87 del repositorio, entre v5.0.24 y v5.0.25:

    "Auto-reparación Naoko: v1.0.0 - ... {'message': '[CRITICAL] magi.core.providers.cloud:"

Causa exacta: naoko.py:191 inicializaba `new_tag = "v1.0.0"` y el regex de la
línea 196 no encontró `tag_name:` en release.yml, así que el default se usó tal
cual. Naoko etiquetó una REGRESIÓN de versión (v5.0.24 -> v1.0.0). Además
naoko.py:225 hacía `readme_content += ...` en cada reparación, y por eso el
README termina con una frase cortada a medias que sigue ahí hoy.

QUÉ HACE ESTA VERSIÓN
=====================
    DETECTAR -> REPRODUCIR -> LOCALIZAR -> PARCHEAR (rama) -> VERIFICAR -> DECIDIR

El paso VERIFICAR es el que no existía. Sin él, Naoko no sabía si había
arreglado algo o roto otra cosa.
"""
from __future__ import annotations

import asyncio
import logging
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ...core.paths import project_root

logger = logging.getLogger(__name__)


class RepairOutcome(str, Enum):
    FIXED = "fixed"
    NOT_REPRODUCIBLE = "not_reproducible"
    PATCH_FAILED = "patch_failed"
    TESTS_REGRESSED = "tests_regressed"
    NO_HYPOTHESIS = "no_hypothesis"
    ABORTED = "aborted"


@dataclass
class RepairReport:
    outcome: RepairOutcome
    hypothesis: str = ""
    files_touched: list[str] = field(default_factory=list)
    branch: str = ""
    tests_before: str = ""
    tests_after: str = ""
    undo_ids: list[str] = field(default_factory=list)
    detail: str = ""

    @property
    def success(self) -> bool:
        return self.outcome is RepairOutcome.FIXED

    def render(self) -> str:
        icon = {"fixed": "OK", "not_reproducible": "?", "patch_failed": "X",
                "tests_regressed": "X", "no_hypothesis": "?",
                "aborted": "X"}[self.outcome.value]
        lines = [f"[{icon}] {self.outcome.value}"]
        if self.hypothesis:
            lines.append(f"hipótesis: {self.hypothesis}")
        if self.files_touched:
            lines.append(f"ficheros: {', '.join(self.files_touched)}")
        if self.branch:
            lines.append(f"rama: {self.branch}")
        if self.detail:
            lines.append(self.detail)
        return "\n".join(lines)


# --------------------------------------------------------------------- versión

_SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def current_version(root: Path | None = None) -> str | None:
    """
    Versión actual leída de git. Devuelve None si no se puede determinar.

    NUNCA inventa un valor por defecto: ese fue exactamente el bug que produjo
    el tag v1.0.0 en medio de la serie v5.0.x.
    """
    root = root or project_root()
    if not shutil.which("git") or not (root / ".git").exists():
        return None
    try:
        out = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=str(root), capture_output=True, text=True, timeout=10)
        tag = out.stdout.strip()
        return tag if out.returncode == 0 and _SEMVER.match(tag) else None
    except Exception:
        return None


def next_patch_version(root: Path | None = None) -> str | None:
    """
    Siguiente patch. None si no se puede determinar la actual.

    El contrato es el arreglo: quien llame DEBE tratar None como "no etiquetar",
    no como "usar v1.0.0".
    """
    cur = current_version(root)
    if cur is None:
        return None
    m = _SEMVER.match(cur)
    if not m:
        return None
    major, minor, patch = (int(g) for g in m.groups())
    return f"v{major}.{minor}.{patch + 1}"


def validate_version_bump(old: str | None, new: str | None) -> tuple[bool, str]:
    """Guarda de seguridad: rechaza cualquier retroceso de versión."""
    if not new:
        return False, "no se pudo determinar la nueva versión"
    if not _SEMVER.match(new):
        return False, f"formato inválido: {new}"
    if not old:
        return False, "no se pudo determinar la versión actual; no se etiqueta"
    om, on, op = (int(g) for g in _SEMVER.match(old).groups())
    nm, nn, np_ = (int(g) for g in _SEMVER.match(new).groups())
    if (nm, nn, np_) <= (om, on, op):
        return False, f"REGRESIÓN DE VERSIÓN bloqueada: {old} -> {new}"
    return True, f"{old} -> {new}"


# ------------------------------------------------------------------- ejecución

async def _sh(cmd: list[str], cwd: Path, timeout: float = 300) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return 124, f"timeout tras {timeout}s"
    return proc.returncode or 0, out.decode("utf-8", errors="replace")


async def run_test_suite(root: Path | None = None,
                         path: str = "tests") -> tuple[bool, str]:
    """La verificación que no existía en v5.0.28."""
    root = root or project_root()
    import sys
    rc, out = await _sh([sys.executable, "-m", "pytest", path, "-q", "--no-header"],
                        root, timeout=600)
    return rc == 0, out[-4000:]


# ------------------------------------------------------------------------ git

async def create_branch(name: str, root: Path | None = None) -> bool:
    root = root or project_root()
    rc, _ = await _sh(["git", "checkout", "-b", name], root, timeout=30)
    return rc == 0


async def commit_files(files: list[str], message: str,
                       root: Path | None = None) -> bool:
    """
    Commitea SOLO los ficheros del parche.

    v5.0.28 hacía `git add .`, que arrastraba cualquier cosa presente en el
    árbol de trabajo — incluida la base de datos con datos reales.
    """
    root = root or project_root()
    if not files:
        return False
    rc, out = await _sh(["git", "add", *files], root, timeout=30)
    if rc != 0:
        logger.error("[naoko] git add falló: %s", out)
        return False
    rc, out = await _sh(["git", "commit", "-m", message], root, timeout=30)
    if rc != 0:
        logger.error("[naoko] git commit falló: %s", out)
    return rc == 0


async def revert_branch(branch: str, base: str = "main",
                        root: Path | None = None) -> None:
    root = root or project_root()
    await _sh(["git", "checkout", base], root, timeout=30)
    await _sh(["git", "branch", "-D", branch], root, timeout=30)


# ------------------------------------------------------------------ orquestación

class VerifiedRepair:
    """
    Reparación con verificación obligatoria.

    Un parche que no pasa la suite no se mergea: se revierte y se prueba la
    siguiente hipótesis.
    """

    def __init__(self, root: Path | None = None, *, max_hypotheses: int = 3):
        self.root = root or project_root()
        self.max_hypotheses = max_hypotheses

    async def repair(self, *, error_details: str, agent_runner,
                     task_id: str = "naoko") -> RepairReport:
        """
        `agent_runner(prompt) -> AgentTurn` es el bucle de herramientas: Naoko
        edita con edit_file (cambios revisables como diff), no generando scripts
        que reescriben ficheros a bulto.
        """
        green_before, out_before = await run_test_suite(self.root)
        if not green_before:
            logger.info("[naoko] la suite ya estaba roja antes de tocar nada")

        branch = f"naoko/fix-{task_id}"
        if not await create_branch(branch, self.root):
            return RepairReport(RepairOutcome.ABORTED,
                                detail=f"no se pudo crear la rama {branch}")

        for attempt in range(1, self.max_hypotheses + 1):
            prompt = self._prompt(error_details, attempt, out_before)
            try:
                turn = await agent_runner(prompt)
            except Exception as e:
                await revert_branch(branch, root=self.root)
                return RepairReport(RepairOutcome.ABORTED, detail=f"agente falló: {e}")

            touched = sorted({
                str(c["args"].get("path", ""))
                for c in turn.tool_calls
                if c["tool"] in {"write_file", "edit_file"} and c.get("ok")
                and c["args"].get("path")
            })
            undo_ids = [c.get("undo_id") for c in turn.tool_calls if c.get("undo_id")]

            if not touched:
                if attempt == self.max_hypotheses:
                    await revert_branch(branch, root=self.root)
                    return RepairReport(RepairOutcome.NO_HYPOTHESIS,
                                        detail=turn.text[:600])
                continue

            green_after, out_after = await run_test_suite(self.root)
            if green_after:
                await commit_files(
                    touched,
                    f"fix(naoko): {error_details[:60].replace(chr(10), ' ')}",
                    self.root)
                return RepairReport(
                    RepairOutcome.FIXED, hypothesis=turn.text[:400],
                    files_touched=touched, branch=branch,
                    tests_before=out_before[-800:], tests_after=out_after[-800:],
                    undo_ids=undo_ids)

            # Rojo: deshacer y probar otra hipótesis.
            logger.warning("[naoko] hipótesis %d dejó la suite roja; revierto", attempt)
            from ...core.tools.journal import WriteJournal
            WriteJournal(task_id=task_id).undo_task(task_id)
            error_details += (
                f"\n\n[intento {attempt} descartado]\n"
                f"Ficheros: {', '.join(touched)}\nSalida de tests:\n{out_after[-1500:]}")

        await revert_branch(branch, root=self.root)
        return RepairReport(RepairOutcome.TESTS_REGRESSED,
                            detail=f"{self.max_hypotheses} hipótesis descartadas")

    @staticmethod
    def _prompt(error: str, attempt: int, tests_before: str) -> str:
        return f"""Fallo detectado en MAGI (intento {attempt}).

ERROR
-----
{error[:3000]}

ESTADO DE LA SUITE ANTES DE TOCAR NADA
--------------------------------------
{tests_before[-1500:]}

Procede en este orden y no te lo saltes:
1. REPRODUCE el fallo (run_tests o run_command). Si no lo reproduces, dilo y para.
2. LOCALIZA el origen con grep/read_file. Cita fichero y línea.
3. PARCHEA con edit_file, el cambio mínimo que resuelva la causa.
4. Añade o ajusta un test que FALLE sin tu parche y PASE con él.
5. Ejecuta run_tests y comprueba que toda la suite queda verde.

No generes scripts que reescriban ficheros a bulto: usa edit_file para que el
cambio sea revisable como diff."""
