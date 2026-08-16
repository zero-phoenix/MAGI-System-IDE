"""
Journal de escrituras con deshacer (Plan MAGI 9.0 §4.2).

POR QUÉ EXISTE
==============
El usuario tiene acceso total a su máquina y no quiere puertas de permiso: es
su equipo, su autorización. Correcto. Pero en v5.0.28 el enjambre ejecutaba
código generado por un LLM con

    powershell -ExecutionPolicy Bypass -File auto_script_0.ps1   (orchestrator.py:69)

sin ninguna forma de deshacerlo. Y Naoko hacía `git add .` + commit + push tras
ejecutar un script que nunca revisó nadie (naoko.py:145-149).

Esto NO añade permisos. Añade REVERSIBILIDAD: antes de tocar un fichero, se
copia. `undo()` lo devuelve. Un agente que puede deshacer lo que hizo es un
agente al que puedes dejar suelto; uno que no puede, acabas vigilándolo — y eso
sí es una limitación real.

Coste: unos milisegundos por escritura.
"""
from __future__ import annotations

import json
import logging
import shutil
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from ..paths import journal_dir

logger = logging.getLogger(__name__)

OpKind = Literal["write", "create", "delete", "mkdir"]


@dataclass
class JournalEntry:
    op_id: str
    kind: OpKind
    target: str
    backup: str | None      # copia previa, None si el fichero no existía
    ts: float
    task_id: str | None = None
    tool: str | None = None
    undone: bool = False
    size_before: int | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


class WriteJournal:
    """
    Registro append-only de mutaciones del sistema de ficheros.

    Uso:
        j = WriteJournal(task_id="task_42")
        with j.guard(path, "write"):
            path.write_text(new_content)
        ...
        j.undo_last()        # revierte una operación
        j.undo_task("task_42")  # revierte toda una tarea
    """

    def __init__(self, task_id: str | None = None, root: Path | None = None):
        self.task_id = task_id
        self.root = root or journal_dir()
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "journal.ndjson"
        self._entries: list[JournalEntry] = []

    # ------------------------------------------------------------------ core

    def _backup(self, target: Path, op_id: str) -> tuple[str | None, int | None]:
        if not target.exists():
            return None, None
        bdir = self.root / op_id
        bdir.mkdir(parents=True, exist_ok=True)
        dest = bdir / target.name
        if target.is_dir():
            shutil.copytree(target, dest, dirs_exist_ok=True)
            return str(dest), None
        shutil.copy2(target, dest)
        return str(dest), target.stat().st_size

    def record(self, target: Path | str, kind: OpKind = "write",
               tool: str | None = None) -> JournalEntry:
        """Copia el estado previo y devuelve la entrada. Llamar ANTES de mutar."""
        target = Path(target)
        op_id = f"{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}"
        backup, size = self._backup(target, op_id)
        entry = JournalEntry(
            op_id=op_id, kind=kind, target=str(target.resolve()),
            backup=backup, ts=time.time(), task_id=self.task_id,
            tool=tool, size_before=size,
        )
        self._entries.append(entry)
        with self.index_path.open("a", encoding="utf-8") as f:
            f.write(entry.to_json() + "\n")
        return entry

    class _Guard:
        def __init__(self, journal: WriteJournal, entry: JournalEntry):
            self.journal, self.entry = journal, entry

        def __enter__(self):
            return self.entry

        def __exit__(self, exc_type, exc, tb):
            return False   # nunca traga excepciones

    def guard(self, target: Path | str, kind: OpKind = "write",
              tool: str | None = None):
        return self._Guard(self, self.record(target, kind, tool))

    # ---------------------------------------------------------------- deshacer

    def all_entries(self) -> list[JournalEntry]:
        if not self.index_path.exists():
            return []
        out = []
        for line in self.index_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    out.append(JournalEntry(**json.loads(line)))
                except (json.JSONDecodeError, TypeError):
                    continue
        return out

    def _restore(self, entry: JournalEntry) -> bool:
        target = Path(entry.target)
        try:
            if entry.backup is None:
                # No existía antes: deshacer = borrarlo.
                if target.is_dir():
                    shutil.rmtree(target, ignore_errors=True)
                elif target.exists():
                    target.unlink()
            else:
                src = Path(entry.backup)
                if not src.exists():
                    logger.warning("[journal] copia perdida para %s", entry.op_id)
                    return False
                target.parent.mkdir(parents=True, exist_ok=True)
                if src.is_dir():
                    shutil.rmtree(target, ignore_errors=True)
                    shutil.copytree(src, target)
                else:
                    shutil.copy2(src, target)
            entry.undone = True
            self._mark_undone(entry.op_id)
            logger.info("[journal] deshecho %s -> %s", entry.op_id, entry.target)
            return True
        except Exception as e:
            logger.error("[journal] fallo al deshacer %s: %s", entry.op_id, e)
            return False

    def _mark_undone(self, op_id: str) -> None:
        entries = self.all_entries()
        for e in entries:
            if e.op_id == op_id:
                e.undone = True
        self.index_path.write_text(
            "\n".join(e.to_json() for e in entries) + "\n", encoding="utf-8")

    def undo_last(self) -> JournalEntry | None:
        for entry in reversed(self.all_entries()):
            if not entry.undone:
                return entry if self._restore(entry) else None
        return None

    def undo_task(self, task_id: str) -> int:
        """Revierte todas las operaciones de una tarea, en orden inverso."""
        n = 0
        for entry in reversed(self.all_entries()):
            if entry.task_id == task_id and not entry.undone:
                if self._restore(entry):
                    n += 1
        return n

    def undo_op(self, op_id: str) -> bool:
        for entry in self.all_entries():
            if entry.op_id == op_id and not entry.undone:
                return self._restore(entry)
        return False

    def prune(self, keep_days: float = 7.0) -> int:
        """Limpia copias viejas para que el journal no crezca sin fin."""
        cutoff = time.time() - keep_days * 86400
        removed = 0
        for entry in self.all_entries():
            if entry.ts < cutoff and entry.backup:
                bdir = Path(entry.backup).parent
                if bdir.exists() and bdir.parent == self.root:
                    shutil.rmtree(bdir, ignore_errors=True)
                    removed += 1
        return removed

    def summary(self, limit: int = 20) -> list[dict]:
        return [asdict(e) for e in self.all_entries()[-limit:]]
