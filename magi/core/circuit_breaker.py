"""
Circuit Breaker para ejecución de herramientas (Plan MAGI 9.0 §4.2, B4).

Implementa Parada-Cubre-Hedge:
- Parada: Timeouts duros en ejecución de herramientas para evitar cuelgues.
- Cubre: Los snapshots se delegan a journal.py, pero el CB conoce el límite.
- Hedge: Si falla o hay timeout, se hace rollback automático hasta el snapshot
  y se devuelve un error estructurado al LLM para que tome ruta alternativa.
"""
import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from .tools.journal import WriteJournal
from .tools.registry import ToolRegistry, ToolResult

logger = logging.getLogger(__name__)

@dataclass
class CircuitResult:
    results: list[ToolResult]
    fallback_invoked: bool = False

class ToolCircuitBreaker:
    def __init__(self, registry: ToolRegistry, max_timeout: float = 300.0):
        self.registry = registry
        self.max_timeout = max_timeout

    async def execute_with_hedge(self, calls: list[tuple[str, dict]], ctx: Any = None) -> CircuitResult:
        """Ejecuta herramientas con Parada y Hedge (rollback en fallo crítico)."""
        journal: WriteJournal | None = getattr(ctx, "journal", None) if ctx else None

        # Guardar el ID de la última operación antes de ejecutar
        # para saber hasta dónde revertir si algo sale mal (Cubre).
        last_op = None
        if journal:
            entries = journal.all_entries()
            if entries:
                last_op = entries[-1].op_id

        try:
            # Parada: timeout duro general
            results = await asyncio.wait_for(
                self.registry.execute_many(calls, ctx),
                timeout=self.max_timeout
            )

            # Comprobar si hubo un fallo que requiera rollback
            # Un error de "timeout" interno (e.g. en run_command) activa el Hedge
            fallback_needed = False
            for r in results:
                if not r.ok and r.error and "timeout" in str(r.error).lower():
                    fallback_needed = True
                    break

            if fallback_needed:
                self._rollback(journal, last_op)
                # Modificamos los errores para indicar que se hizo rollback
                for r in results:
                    if not r.ok:
                        r.error = f"{r.error} (Hedge aplicado: cambios revertidos. Busca ruta alternativa)"
                return CircuitResult(results, fallback_invoked=True)

            return CircuitResult(results, fallback_invoked=False)

        except asyncio.TimeoutError:
            logger.warning("[CircuitBreaker] Timeout duro de %ss ejecutando %s", self.max_timeout, calls)
            self._rollback(journal, last_op)

            results = [
                ToolResult(
                    False, "", c[0],
                    f"Timeout duro de {self.max_timeout}s en el entorno. Hedge activado: Rollback completado. Usa otro enfoque."
                ) for c in calls
            ]
            return CircuitResult(results, fallback_invoked=True)

        except Exception as e:
            logger.exception("[CircuitBreaker] Excepción inesperada")
            self._rollback(journal, last_op)
            results = [
                ToolResult(
                    False, "", c[0],
                    f"Excepción interna: {e}. Hedge activado: Rollback completado."
                ) for c in calls
            ]
            return CircuitResult(results, fallback_invoked=True)

    def _rollback(self, journal: WriteJournal | None, last_op: str | None):
        """Hedge: deshace todas las operaciones del journal hasta last_op."""
        if not journal:
            return
        logger.info("[CircuitBreaker] Iniciando rollback (Hedge) hasta %s", last_op)
        entries = journal.all_entries()
        for entry in reversed(entries):
            if last_op and entry.op_id == last_op:
                break
            if not entry.undone:
                journal.undo_op(entry.op_id)
