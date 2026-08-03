"""
Catálogo de herramientas (Plan MAGI 9.0 §2.2, §4.1).

ACCESO A LA MÁQUINA: SIN RESTRICCIONES
======================================
Es la máquina del usuario y su autorización. No hay allowlist de directorios,
ni puertas de permiso, ni capacidades denegadas. Lo único que se añade es
REVERSIBILIDAD (journal.py): toda mutación se puede deshacer.
"""
from __future__ import annotations

import asyncio
import fnmatch
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..paths import workspace_dir
from .journal import WriteJournal
from .registry import Tool, ToolRegistry, ToolResult

MAX_READ_BYTES = 400_000


@dataclass
class ToolContext:
    """Estado que comparten las herramientas durante un turno."""
    task_id: str | None = None
    cwd: Path = field(default_factory=workspace_dir)
    journal: WriteJournal | None = None
    dry_run: bool = False
    env: dict[str, str] = field(default_factory=dict)

    def resolve(self, path: str | Path) -> Path:
        p = Path(os.path.expandvars(str(path))).expanduser()
        return p if p.is_absolute() else (self.cwd / p)

    def get_journal(self) -> WriteJournal:
        if self.journal is None:
            self.journal = WriteJournal(task_id=self.task_id)
        return self.journal


def build_registry() -> ToolRegistry:
    reg = ToolRegistry()

    # ------------------------------------------------------------- lectura

    @reg.tool("read_file", "Lee un fichero de texto. Usa offset/limit para ficheros grandes.",
              {"type": "object", "properties": {
                  "path": {"type": "string"},
                  "offset": {"type": "integer", "description": "línea inicial (1-based)"},
                  "limit": {"type": "integer", "description": "número de líneas"}},
               "required": ["path"]}, access={"read"})
    def read_file(path: str, ctx: ToolContext, offset: int = 1, limit: int = 0):
        p = ctx.resolve(path)
        if not p.exists():
            return ToolResult(False, "", error=f"no existe: {p}")
        if p.is_dir():
            return ToolResult(False, "", error=f"es un directorio: {p}")
        if p.stat().st_size > MAX_READ_BYTES:
            data = p.read_bytes()[:MAX_READ_BYTES].decode("utf-8", errors="replace")
            note = f"\n… [truncado, fichero de {p.stat().st_size} bytes]"
        else:
            data, note = p.read_text(encoding="utf-8", errors="replace"), ""
        lines = data.splitlines()
        if offset > 1 or limit:
            end = (offset - 1 + limit) if limit else len(lines)
            lines = lines[offset - 1:end]
        numbered = "\n".join(f"{i + offset:>6}\t{l}" for i, l in enumerate(lines))
        return ToolResult(True, numbered + note, meta={"lines": len(lines), "path": str(p)})

    @reg.tool("list_dir", "Lista un directorio.",
              {"type": "object", "properties": {
                  "path": {"type": "string"}, "recursive": {"type": "boolean"}},
               "required": ["path"]}, access={"read"})
    def list_dir(path: str, ctx: ToolContext, recursive: bool = False):
        p = ctx.resolve(path)
        if not p.is_dir():
            return ToolResult(False, "", error=f"no es un directorio: {p}")
        out, count = [], 0
        it = p.rglob("*") if recursive else p.iterdir()
        for child in sorted(it):
            if any(part in {".git", "node_modules", "__pycache__", ".venv"}
                   for part in child.parts):
                continue
            rel = child.relative_to(p)
            out.append(f"{'d' if child.is_dir() else '-'} {rel}"
                       + ("" if child.is_dir() else f"  ({child.stat().st_size}b)"))
            count += 1
            if count >= 500:
                out.append("… [500+ entradas, acota la ruta]")
                break
        return ToolResult(True, "\n".join(out) or "(vacío)", meta={"count": count})

    @reg.tool("grep", "Busca un patrón (regex) en ficheros.",
              {"type": "object", "properties": {
                  "pattern": {"type": "string"}, "path": {"type": "string"},
                  "glob": {"type": "string", "description": "p.ej. *.py"}},
               "required": ["pattern"]}, access={"read"})
    def grep(pattern: str, ctx: ToolContext, path: str = ".", glob: str = "*"):
        root = ctx.resolve(path)
        try:
            rx = re.compile(pattern)
        except re.error as e:
            return ToolResult(False, "", error=f"regex inválida: {e}")
        hits, files = [], 0
        targets = [root] if root.is_file() else root.rglob(glob)
        for f in targets:
            if not f.is_file() or any(x in f.parts for x in
                                      {".git", "node_modules", "__pycache__"}):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            files += 1
            for n, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{f}:{n}: {line.strip()[:200]}")
                    if len(hits) >= 200:
                        hits.append("… [200+ coincidencias]")
                        return ToolResult(True, "\n".join(hits),
                                          meta={"files": files})
        return ToolResult(True, "\n".join(hits) or "(sin coincidencias)",
                          meta={"files_scanned": files, "hits": len(hits)})

    @reg.tool("glob", "Busca ficheros por patrón de nombre.",
              {"type": "object", "properties": {
                  "pattern": {"type": "string"}, "path": {"type": "string"}},
               "required": ["pattern"]}, access={"read"})
    def glob_tool(pattern: str, ctx: ToolContext, path: str = "."):
        root = ctx.resolve(path)
        found = [str(p) for p in root.rglob(pattern)
                 if ".git" not in p.parts and "node_modules" not in p.parts][:300]
        return ToolResult(True, "\n".join(found) or "(sin resultados)",
                          meta={"count": len(found)})

    # ------------------------------------------------------------- escritura
    # Todas pasan por el journal: reversibles, no restringidas.

    @reg.tool("write_file", "Escribe un fichero (lo crea o lo reemplaza). Reversible.",
              {"type": "object", "properties": {
                  "path": {"type": "string"}, "content": {"type": "string"}},
               "required": ["path", "content"]},
              access={"write"}, dangerous=True)
    def write_file(path: str, content: str, ctx: ToolContext):
        p = ctx.resolve(path)
        if ctx.dry_run:
            return ToolResult(True, f"[dry-run] escribiría {len(content)}b en {p}")
        p.parent.mkdir(parents=True, exist_ok=True)
        entry = ctx.get_journal().record(p, "write" if p.exists() else "create",
                                         tool="write_file")
        p.write_text(content, encoding="utf-8")
        return ToolResult(True, f"escrito {p} ({len(content)} bytes)",
                          meta={"undo_id": entry.op_id, "path": str(p)})

    @reg.tool("edit_file", "Reemplaza una cadena exacta dentro de un fichero. Reversible.",
              {"type": "object", "properties": {
                  "path": {"type": "string"}, "old": {"type": "string"},
                  "new": {"type": "string"}, "all": {"type": "boolean"}},
               "required": ["path", "old", "new"]},
              access={"write"}, dangerous=True)
    def edit_file(path: str, old: str, new: str, ctx: ToolContext, all: bool = False):
        p = ctx.resolve(path)
        if not p.exists():
            return ToolResult(False, "", error=f"no existe: {p}")
        text = p.read_text(encoding="utf-8", errors="replace")
        n = text.count(old)
        if n == 0:
            return ToolResult(False, "", error="la cadena 'old' no aparece en el fichero")
        if n > 1 and not all:
            return ToolResult(False, "", error=(
                f"'old' aparece {n} veces; usa all=true o amplía el contexto "
                f"para que sea único"))
        if ctx.dry_run:
            return ToolResult(True, f"[dry-run] sustituiría {n} ocurrencia(s) en {p}")
        entry = ctx.get_journal().record(p, "write", tool="edit_file")
        p.write_text(text.replace(old, new) if all else text.replace(old, new, 1),
                     encoding="utf-8")
        return ToolResult(True, f"editado {p} ({n if all else 1} sustitución/es)",
                          meta={"undo_id": entry.op_id})

    @reg.tool("delete_path", "Borra un fichero o directorio. Reversible.",
              {"type": "object", "properties": {"path": {"type": "string"}},
               "required": ["path"]}, access={"write"}, dangerous=True)
    def delete_path(path: str, ctx: ToolContext):
        p = ctx.resolve(path)
        if not p.exists():
            return ToolResult(False, "", error=f"no existe: {p}")
        if ctx.dry_run:
            return ToolResult(True, f"[dry-run] borraría {p}")
        entry = ctx.get_journal().record(p, "delete", tool="delete_path")
        shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink()
        return ToolResult(True, f"borrado {p}", meta={"undo_id": entry.op_id})

    @reg.tool("undo", "Deshace la última mutación, o todas las de esta tarea.",
              {"type": "object", "properties": {
                  "scope": {"type": "string", "enum": ["last", "task"]}}},
              access={"write"})
    def undo(ctx: ToolContext, scope: str = "last"):
        j = ctx.get_journal()
        if scope == "task" and ctx.task_id:
            return ToolResult(True, f"revertidas {j.undo_task(ctx.task_id)} operaciones")
        e = j.undo_last()
        return ToolResult(bool(e), f"revertido: {e.target}" if e else "",
                          error=None if e else "nada que deshacer")

    # ------------------------------------------------------------- ejecución

    @reg.tool("run_command", "Ejecuta un comando de shell y devuelve su salida.",
              {"type": "object", "properties": {
                  "command": {"type": "string"}, "cwd": {"type": "string"},
                  "timeout": {"type": "integer"}},
               "required": ["command"]}, access={"exec"}, dangerous=True)
    async def run_command(command: str, ctx: ToolContext,
                          cwd: str | None = None, timeout: int = 120):
        workdir = ctx.resolve(cwd) if cwd else ctx.cwd
        workdir.mkdir(parents=True, exist_ok=True)
        if ctx.dry_run:
            return ToolResult(True, f"[dry-run] ejecutaría en {workdir}: {command}")
        try:
            proc = await asyncio.create_subprocess_shell(
                command, cwd=str(workdir),
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
                env={**os.environ, **ctx.env})
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            text = out.decode("utf-8", errors="replace")
            return ToolResult(proc.returncode == 0,
                              f"$ {command}\n{text}\n[rc={proc.returncode}]",
                              error=None if proc.returncode == 0
                              else f"rc={proc.returncode}",
                              meta={"rc": proc.returncode})
        except asyncio.TimeoutError:
            # kill() sin wait() deja el transporte sin limpiar: el proceso queda
            # zombi y asyncio lanza "Event loop is closed" al recolectarlo.
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
            return ToolResult(False, "", error=f"timeout tras {timeout}s")

    @reg.tool("python_exec", "Ejecuta código Python en un proceso aparte.",
              {"type": "object", "properties": {"code": {"type": "string"}},
               "required": ["code"]}, access={"exec"}, dangerous=True)
    async def python_exec(code: str, ctx: ToolContext):
        script = ctx.cwd / f"_magi_exec_{os.getpid()}.py"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(code, encoding="utf-8")
        try:
            return await run_command(f'"{sys.executable}" "{script.name}"', ctx=ctx,
                                     timeout=120)
        finally:
            script.unlink(missing_ok=True)

    @reg.tool("run_tests", "Ejecuta pytest sobre una ruta. Es la herramienta que "
                           "convierte una opinión sobre el código en evidencia.",
              {"type": "object", "properties": {
                  "path": {"type": "string"}, "k": {"type": "string"}}},
              access={"exec"})
    async def run_tests(ctx: ToolContext, path: str = "tests", k: str = ""):
        cmd = f'"{sys.executable}" -m pytest {path} -q --no-header'
        if k:
            cmd += f' -k "{k}"'
        return await run_command(cmd, ctx=ctx, timeout=300)

    # ------------------------------------------------------------------- red

    @reg.tool("web_fetch", "Descarga una URL y devuelve su texto.",
              {"type": "object", "properties": {"url": {"type": "string"}},
               "required": ["url"]}, access={"net"})
    async def web_fetch(url: str):
        try:
            import httpx
        except ImportError:
            return ToolResult(False, "", error="httpx no instalado")
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30) as c:
                r = await c.get(url, headers={"User-Agent": "MAGI/9.0"})
                r.raise_for_status()
                text = re.sub(r"<script.*?</script>|<style.*?</style>", "",
                              r.text, flags=re.DOTALL | re.I)
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text).strip()
                return ToolResult(True, text[:20000], meta={"status": r.status_code})
        except Exception as e:
            return ToolResult(False, "", error=str(e))

    # §5.3 — toolchain de ingeniería inversa y emuladores.
    # Se registra aquí para que los tres nodos del enjambre lo tengan: sin este
    # enganche, todo magi/modules/reverse/ sería código correcto que ningún
    # agente puede invocar.
    try:
        from magi.modules.reverse.tools import register_reverse_tools
        register_reverse_tools(reg)
    except Exception as e:            # pragma: no cover
        import logging
        logging.getLogger(__name__).warning(
            "[tools] toolchain de RE no disponible: %s", e)

    return reg


# Perfiles por rol (Plan MAGI 9.0 §2.2).
MELCHIOR_TOOLS = None                      # todo: propone y construye
BALTHASAR_DENY = {"write"}                 # lee y ejecuta, no escribe
CASPER_TOOLS = {"read_file", "list_dir", "grep", "glob", "run_tests",
                "run_command",
                # el árbitro necesita poder comprobar afirmaciones sobre
                # arquitecturas sin fiarse de lo que digan los otros dos
                "binary_identify", "console_profile", "analyze_port",
                "compare_consoles"}


def registry_for_role(role: str) -> ToolRegistry:
    base = build_registry()
    r = role.upper()
    if r == "BALTHASAR":
        return base.subset(deny_access=BALTHASAR_DENY)
    if r == "CASPER":
        return base.subset(allowed=CASPER_TOOLS)
    return base
