"""
Verificación ejecutable antes del arbitraje (Plan MAGI 9.0 §2.5).

REGLA
=====
Ninguna propuesta que contenga código llega a Casper sin haberse ejecutado.

    Melchior escribe -> sandbox -> lint / import / tests
        ├─ pasa  -> va a Balthasar CON la evidencia adjunta
        └─ falla -> vuelve a Melchior con el traceback, sin gastar ronda

EL PROBLEMA QUE ELIMINA
=======================
En v5.0.28 los tres agentes debatían elegantemente sobre código que no
compilaba. Balthasar criticaba el estilo de una función con un SyntaxError
dentro, y Casper arbitraba entre dos textos. El fallo más común y más caro del
sistema era ese: tres rondas de deliberación sobre algo que no arranca.
"""
from __future__ import annotations

import ast
import asyncio
import logging
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# ```python … ```   /   ```py … ```   /   ```powershell … ```
_BLOCK = re.compile(r"```(\w+)?\s*\n(.*?)```", re.DOTALL)

CHECKABLE = {"python", "py", "json", "yaml", "yml"}


@dataclass
class BlockResult:
    lang: str
    index: int
    ok: bool
    stage: str            # "syntax" | "import" | "run" | "skipped"
    detail: str = ""
    excerpt: str = ""

    def render(self) -> str:
        mark = "OK" if self.ok else "FALLA"
        head = f"[{mark}] bloque {self.index + 1} ({self.lang}) — {self.stage}"
        return head if self.ok else f"{head}\n{self.detail[:1200]}"


@dataclass
class VerificationReport:
    blocks: list[BlockResult] = field(default_factory=list)
    had_code: bool = False

    @property
    def ok(self) -> bool:
        return all(b.ok for b in self.blocks)

    @property
    def failures(self) -> list[BlockResult]:
        return [b for b in self.blocks if not b.ok]

    def render(self) -> str:
        if not self.had_code:
            return "Sin bloques de código que verificar."
        lines = [b.render() for b in self.blocks]
        head = ("Todos los bloques verificados correctamente."
                if self.ok else
                f"{len(self.failures)} de {len(self.blocks)} bloques fallan.")
        return head + "\n\n" + "\n\n".join(lines)

    def feedback_for_author(self) -> str:
        """Lo que se le devuelve a Melchior cuando algo no arranca."""
        parts = ["Tu propuesta NO pasa la verificación. Corrige esto antes de "
                 "que nadie la evalúe:\n"]
        for b in self.failures:
            parts.append(f"--- bloque {b.index + 1} ({b.lang}), fase {b.stage} ---")
            if b.excerpt:
                parts.append(b.excerpt)
            parts.append(b.detail[:1500])
            parts.append("")
        parts.append("Devuelve la propuesta corregida y verificable.")
        return "\n".join(parts)

    def evidence_for_critic(self) -> str:
        """Lo que se le adjunta a Balthasar cuando sí arranca."""
        if not self.had_code:
            return ""
        return ("\n\n--- EVIDENCIA DE EJECUCIÓN (no es una suposición) ---\n"
                + self.render())


def extract_blocks(text: str) -> list[tuple[str, str]]:
    out = []
    for m in _BLOCK.finditer(text or ""):
        lang = (m.group(1) or "").lower().strip()
        code = m.group(2)
        if code.strip():
            out.append((lang or "text", code))
    return out


async def _run(cmd: list[str], cwd: Path, timeout: float = 45.0,
               task_id: str | None = None) -> tuple[int, str]:
    from .cancel import tracked

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    except FileNotFoundError as e:
        return 127, str(e)

    # §7.3 — este proceso ejecuta CÓDIGO GENERADO POR EL MODELO en cada ronda
    # del debate, y quedaba fuera del alcance de la parada de emergencia:
    # pulsar parar informaba de que no había nada en marcha mientras seguía
    # corriendo.
    async with tracked(proc, task_id):
        try:
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return 124, f"timeout tras {timeout}s"
    return proc.returncode or 0, out.decode("utf-8", errors="replace")


class ProposalVerifier:
    """
    Verificación barata y progresiva. Se para en el primer fallo de cada bloque:
    si hay SyntaxError no tiene sentido intentar ejecutarlo.

    Fases:
      1. sintaxis  — ast.parse / json.loads / yaml.safe_load   (milisegundos)
      2. import    — compila y ejecuta en subproceso aislado    (segundos)
      3. run       — solo si el bloque parece ejecutable
    """

    def __init__(self, workdir: Path | None = None, *, run_code: bool = True,
                 timeout_s: float = 45.0):
        self.workdir = workdir
        self.run_code = run_code
        self.timeout_s = timeout_s

    async def verify(self, proposal_text: str) -> VerificationReport:
        blocks = extract_blocks(proposal_text)
        report = VerificationReport(had_code=bool(blocks))
        if not blocks:
            return report

        tmp = Path(self.workdir) if self.workdir else Path(tempfile.mkdtemp(
            prefix="magi-verify-"))
        tmp.mkdir(parents=True, exist_ok=True)

        results = await asyncio.gather(*[
            self._verify_block(i, lang, code, tmp)
            for i, (lang, code) in enumerate(blocks)
        ])
        report.blocks = list(results)
        return report

    async def _verify_block(self, i: int, lang: str, code: str,
                            tmp: Path) -> BlockResult:
        if lang not in CHECKABLE:
            return BlockResult(lang, i, True, "skipped",
                               f"lenguaje '{lang}' no verificable automáticamente")

        if lang in ("json",):
            import json
            try:
                json.loads(code)
                return BlockResult(lang, i, True, "syntax")
            except json.JSONDecodeError as e:
                return BlockResult(lang, i, False, "syntax", str(e),
                                   self._excerpt(code, e.lineno))

        if lang in ("yaml", "yml"):
            try:
                import yaml
                yaml.safe_load(code)
                return BlockResult(lang, i, True, "syntax")
            except ImportError:
                return BlockResult(lang, i, True, "skipped", "pyyaml no instalado")
            except Exception as e:
                return BlockResult(lang, i, False, "syntax", str(e))

        # Python
        try:
            ast.parse(code)
        except SyntaxError as e:
            return BlockResult(lang, i, False, "syntax",
                               f"{e.msg} (línea {e.lineno})",
                               self._excerpt(code, e.lineno or 1))

        if not self.run_code:
            return BlockResult(lang, i, True, "syntax")

        script = tmp / f"block_{i}.py"
        script.write_text(code, encoding="utf-8")
        rc, out = await _run([sys.executable, str(script)], tmp, self.timeout_s)
        if rc == 0:
            return BlockResult(lang, i, True, "run", out[-800:])
        return BlockResult(lang, i, False, "run", out[-2000:])

    @staticmethod
    def _excerpt(code: str, lineno: int, ctx: int = 2) -> str:
        lines = code.splitlines()
        lo, hi = max(0, lineno - 1 - ctx), min(len(lines), lineno + ctx)
        return "\n".join(
            f"{'>' if n == lineno else ' '} {n:>4} | {lines[n - 1]}"
            for n in range(lo + 1, hi + 1))
