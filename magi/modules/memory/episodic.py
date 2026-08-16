"""
Memoria episódica del debate (Plan MAGI 9.0 §2.6).

EL PROBLEMA
===========
Cada ronda del enjambre arrancaba con la propuesta y la crítica anteriores, pero
sin registro de QUÉ SE INTENTÓ Y FALLÓ. En la práctica, Melchior proponía en la
ronda 3 una variante del enfoque que ya había sido refutado en la ronda 1, y
Balthasar volvía a escribir la misma objeción.

v5.0.28 tenía SemanticRAG, HierarchicalMemory, HyperdimensionalMemory y las
tablas mem_knowledge / mem_project. Ninguna entraba en el prompt de ningún
agente: se instanciaban en main.py y no se llamaban nunca.

Esto es la versión pequeña que sí se usa: un registro de intentos por tarea que
se inyecta en la siguiente ronda. Deliberadamente modesto — cabe en la ventana
de contexto de un proveedor gratuito, que es la restricción real.
"""
from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

MAX_ATTEMPTS_IN_PROMPT = 6
# Tope de la lista en memoria. El bloque del prompt ya estaba acotado, pero
# _attempts crecía toda la sesión y _load() reproducía TODO el histórico al
# rehidratar: fuga lenta más arranque cada vez más lento.
MAX_ATTEMPTS_RETAINED = 50


@dataclass
class Attempt:
    round_num: int
    approach: str            # resumen del enfoque propuesto
    outcome: str             # "refutado" | "no_verifica" | "aprobado" | "descartado"
    reason: str = ""         # por qué falló, en una línea
    ts: float = field(default_factory=time.time)

    def render(self) -> str:
        return (f"- Ronda {self.round_num}: {self.approach} "
                f"-> {self.outcome.upper()}"
                + (f" ({self.reason})" if self.reason else ""))


class EpisodicMemory:
    """
    Qué se intentó en esta tarea y con qué resultado.

    Se persiste en task_event para sobrevivir a un reinicio, igual que el resto
    del estado (§1.4).
    """

    def __init__(self, task_id: str, store=None):
        self.task_id = task_id
        self._attempts: list[Attempt] = []
        self.store = store
        if store is not None:
            self._load()

    def _load(self) -> None:
        try:
            for ev in self.store.events(self.task_id):
                if ev["topic"] == "memory.attempt" and ev["payload"]:
                    try:
                        self._attempts.append(Attempt(**ev["payload"]))
                    except TypeError:
                        # Esquema antiguo: ignorar la entrada en vez de tumbar
                        # la carga entera del histórico.
                        continue
            self._trim()
        except Exception as e:
            logger.debug("[memoria] no se pudo cargar el histórico: %s", e)

    def _trim(self) -> None:
        if len(self._attempts) > MAX_ATTEMPTS_RETAINED:
            self._attempts = self._attempts[-MAX_ATTEMPTS_RETAINED:]

    def record(self, *, round_num: int, approach: str, outcome: str,
               reason: str = "") -> Attempt:
        a = Attempt(round_num=round_num,
                    approach=_summarize(approach), outcome=outcome,
                    reason=_one_line(reason))
        self._attempts.append(a)
        self._trim()
        if self.store is not None:
            try:
                self.store.append_event(self.task_id, "memory.attempt", asdict(a))
            except Exception as e:
                logger.debug("[memoria] no se pudo persistir el intento: %s", e)
        return a

    @property
    def attempts(self) -> list[Attempt]:
        return list(self._attempts)

    def failed_approaches(self) -> list[Attempt]:
        return [a for a in self._attempts
                if a.outcome in {"refutado", "no_verifica", "descartado"}]

    def render_for_prompt(self) -> str:
        """
        Bloque que se inyecta en la ronda siguiente.

        Vacío si no hay historial: no gastar contexto en decir que no hay nada.
        """
        failed = self.failed_approaches()[-MAX_ATTEMPTS_IN_PROMPT:]
        if not failed:
            return ""
        lines = ["=== YA INTENTADO EN ESTA TAREA (no lo repitas) ==="]
        lines += [a.render() for a in failed]
        lines.append("Propón algo DISTINTO, o explica por qué un enfoque ya "
                     "refutado sigue siendo el correcto pese a la objeción.")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {"task_id": self.task_id,
                "attempts": [asdict(a) for a in self._attempts]}


def _summarize(text: str, limit: int = 160) -> str:
    """
    Primera frase con contenido de la propuesta, sin bloques de código.

    El respaldo tenía que quitar los cercados también: si ninguna línea
    calificaba (propuestas que son casi todo código), devolvía el texto crudo
    con ```python dentro, y la memoria acababa llena de fragmentos ilegibles.
    """
    if not text:
        return "(sin contenido)"

    import re as _re
    prose = _re.sub(r"```.*?```", " [código] ", text, flags=_re.DOTALL)

    for line in prose.splitlines():
        line = line.strip().lstrip("#").strip()
        if len(line) > 25:
            return line[:limit] + ("…" if len(line) > limit else "")

    # Ninguna línea larga: aplanar lo que quede, ya sin cercados.
    flat = " ".join(prose.split())
    return (flat[:limit] + ("…" if len(flat) > limit else "")) or "(solo código)"


def _one_line(text: str, limit: int = 120) -> str:
    if not text:
        return ""
    flat = " ".join(text.split())
    return flat[:limit] + ("…" if len(flat) > limit else "")
