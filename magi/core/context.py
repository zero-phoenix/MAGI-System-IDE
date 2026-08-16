"""
Contexto de ejecución (Plan MAGI 9.0 §4.3).

"Que entienda dónde está funcionando, comprenda su lugar en el tiempo y el
espacio cibernético" — petición literal del usuario, y una carencia real:
en v5.0.28 los agentes no sabían qué día era ni en qué máquina corrían.

Consecuencias medibles de esa ceguera:
  - Melchior proponía `apt-get install` en una máquina Windows.
  - Naoko commiteaba sin saber si el árbol estaba sucio.
  - Ningún agente sabía qué versión de sí mismo estaba ejecutando.
  - El sistema no podía razonar sobre su propia cuota ni su propia salud.

Es de las mejoras con mejor relación coste/beneficio del plan: un bloque de
texto inyectado en cada prompt de sistema.
"""
from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import paths

_STARTED = time.monotonic()
_PROC_START = datetime.now(timezone.utc)


def _run(cmd: list[str], cwd: Path | None = None, timeout: float = 3.0) -> str:
    try:
        r = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True,
                           text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


@dataclass
class GitInfo:
    is_repo: bool = False
    branch: str = ""
    commit: str = ""
    dirty: bool = False
    tag: str = ""

    @classmethod
    def probe(cls, root: Path) -> GitInfo:
        if not (root / ".git").exists() or not shutil.which("git"):
            return cls()
        return cls(
            is_repo=True,
            branch=_run(["git", "rev-parse", "--abbrev-ref", "HEAD"], root),
            commit=_run(["git", "rev-parse", "--short", "HEAD"], root),
            dirty=bool(_run(["git", "status", "--porcelain"], root)),
            tag=_run(["git", "describe", "--tags", "--abbrev=0"], root),
        )


@dataclass
class HostInfo:
    hostname: str = ""
    os_name: str = ""
    os_version: str = ""
    arch: str = ""
    cpu_count: int = 0
    ram_gb: float = 0.0
    python: str = ""

    @classmethod
    def probe(cls) -> HostInfo:
        ram = 0.0
        try:
            import psutil  # opcional  # type: ignore[import-not-found]
            ram = psutil.virtual_memory().total / (1024 ** 3)
        except Exception:
            if hasattr(os, "sysconf") and "SC_PAGE_SIZE" in os.sysconf_names:  # type: ignore[attr-defined]
                try:
                    ram = (os.sysconf("SC_PAGE_SIZE")  # type: ignore[attr-defined]
                           * os.sysconf("SC_PHYS_PAGES")) / (1024 ** 3)  # type: ignore[attr-defined]
                except Exception:
                    pass
        return cls(
            hostname=socket.gethostname(),
            os_name=platform.system(),
            os_version=platform.release(),
            arch=platform.machine(),
            cpu_count=os.cpu_count() or 0,
            ram_gb=round(ram, 1),
            python=platform.python_version(),
        )


@dataclass
class ExecutionContext:
    host: HostInfo = field(default_factory=HostInfo.probe)
    git: GitInfo = field(default_factory=lambda: GitInfo.probe(paths.project_root()))
    project_dir: Path | None = None
    user_name: str = ""
    user_locale: str = "es-PE"
    narrative_style: str = "tecnico"
    provider_health: dict[str, Any] = field(default_factory=dict)
    session_tasks: int = 0
    last_task: str = ""

    def uptime_s(self) -> float:
        return time.monotonic() - _STARTED

    def now_local(self) -> datetime:
        return datetime.now().astimezone()

    def _providers_line(self) -> str:
        provs = self.provider_health.get("providers") or []
        if not provs:
            return "sin sondear"
        parts = []
        for p in provs:
            if not p.get("available"):
                continue
            state = p.get("state", "?")
            mark = {"closed": "ok", "half_open": "probando", "open": "CAÍDO"}.get(state, state)
            p95 = p.get("p95_ms") or 0
            parts.append(f"{p.get('family')}:{mark}" + (f"(p95 {p95/1000:.1f}s)" if p95 else ""))
        fams = self.provider_health.get("families_available") or []
        head = f"{len(fams)} familias sanas"
        return head + (" · " + " · ".join(parts[:6]) if parts else "")

    def _project_line(self) -> str:
        if not self.project_dir:
            return f"ninguno abierto (workspace: {paths.workspace_dir()})"
        p = Path(self.project_dir)
        git = GitInfo.probe(p)
        n = sum(1 for _ in p.rglob("*") if _.is_file()) if p.exists() else 0
        bits = [str(p), f"{n} ficheros"]
        if git.is_repo:
            bits.append(f"git {git.branch}" + (" (sucio)" if git.dirty else ""))
        return " · ".join(bits)

    def render(self) -> str:
        """Bloque que se inyecta en el prompt de sistema de todos los agentes."""
        now = self.now_local()
        h, g = self.host, self.git
        up = int(self.uptime_s())
        version = g.tag or "sin etiqueta"
        return f"""=== CONTEXTO DE EJECUCIÓN (real, no supuesto) ===
Ahora:       {now.strftime('%Y-%m-%d %H:%M %z')} · {now.strftime('%A')}
Host:        {h.hostname} · {h.os_name} {h.os_version} · {h.arch} · \
{h.cpu_count} núcleos · {h.ram_gb} GB · Python {h.python}
MAGI:        {version} ({g.commit or 'n/d'}) · rama {g.branch or 'n/d'} · \
árbol {'sucio' if g.dirty else 'limpio'}
Raíz:        {paths.project_root()}
Datos:       {paths.data_dir()}
Proceso:     PID {os.getpid()} · uptime {up // 3600}h {(up % 3600) // 60}m
Inferencia:  {self._providers_line()}
Proyecto:    {self._project_line()}
Usuario:     {self.user_name or 'David'} · {self.user_locale} · estilo {self.narrative_style}
Sesión:      tarea {self.session_tasks} de esta sesión\
{f" · última: {self.last_task[:60]}" if self.last_task else ""}

Implicaciones que DEBES respetar:
- Estás en {h.os_name}. Usa comandos de {h.os_name}, no de otro sistema.
- Tienes acceso real y sin restricciones a esta máquina mediante herramientas.
  Toda escritura es reversible (journal), así que actúa: no pidas permiso.
- Tu conocimiento de entrenamiento tiene fecha de corte. Para cualquier dato del
  presente, usa web_fetch en vez de responder de memoria.
- Solo hay IA de nube gratuita disponible (sin claves, sin modelos locales):
  las cuotas se agotan. Si un proveedor cae, adapta el plan, no lo ignores."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "now": self.now_local().isoformat(),
            "host": self.host.__dict__,
            "git": self.git.__dict__,
            "paths": paths.describe(),
            "pid": os.getpid(),
            "uptime_s": round(self.uptime_s(), 1),
            "project_dir": str(self.project_dir) if self.project_dir else None,
            "narrative_style": self.narrative_style,
            "session_tasks": self.session_tasks,
        }


_ctx: ExecutionContext | None = None


def get_context() -> ExecutionContext:
    global _ctx
    if _ctx is None:
        _ctx = ExecutionContext()
    return _ctx


def refresh_context(**updates) -> ExecutionContext:
    ctx = get_context()
    for k, v in updates.items():
        if hasattr(ctx, k):
            setattr(ctx, k, v)
    ctx.git = GitInfo.probe(paths.project_root())
    return ctx
