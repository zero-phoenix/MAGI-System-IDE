"""
Compuertas de cierre del debate y veredictos especiales (Megaplan F4 y F5).

Invariantes de F4:
- Antes de que Casper emita 'APPROVED', se ejecuta verificar.py (--rápido).
- Una entrega sin verificación o con verificación fallida se rechaza sola.

Invariantes de F5:
- Veredicto «la pregunta era otra»: cuarto veredicto sin ganador.
- Se registra automáticamente en bitácora / descartes.jsonl para no repetir el desvío.
"""
from __future__ import annotations

import logging
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from magi.core.paths import python_executable

from .memoria_persistente import registrar_descarte
from .plan import PlanTarea, verificar_cierre_plan

logger = logging.getLogger(__name__)

DECISION_APROBADO = "APPROVED"
DECISION_RECHAZADO = "REJECTED_NEEDS_WORK"
DECISION_PREGUNTA_OTRA = "LA_PREGUNTA_ERA_OTRA"
DECISION_SIN_ARBITRAJE = "SIN_ARBITRAJE"


def ejecutar_compuerta_rapida(
    runner: Callable[[], tuple[int, str]] | None = None,
    timeout: float = 120.0,
    cwd: Path | str | None = None,
) -> tuple[bool, str]:
    """
    F4: Ejecuta scripts/verificar.py --rapido antes del cierre.

    Retorna (ok, reporte_detallado).
    """
    if runner is not None:
        codigo, salida = runner()
        return codigo == 0, salida

    raiz = Path(__file__).resolve().parents[3]
    script_verificar = raiz / "scripts" / "verificar.py"
    if not script_verificar.exists():
        return False, f"No se encontró scripts/verificar.py en {script_verificar}"

    py = python_executable()
    if not py:
        return False, "No se encontró un intérprete de Python válido"
    cmd = [py, str(script_verificar), "--rapido"]
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd or raiz),
            check=False,
        )
        salida = res.stdout or res.stderr
        ok = res.returncode == 0
        return ok, salida.strip()
    except subprocess.TimeoutExpired:
        return False, f"Timeout ({timeout}s) ejecutando verificar.py --rapido"
    except Exception as e:
        return False, f"Fallo al ejecutar compuerta de verificación: {e}"


def evaluar_cierre_entrega(
    decision_original: str,
    feedback: str,
    *,
    plan: PlanTarea | None = None,
    compuerta_ok: bool = True,
    compuerta_info: str = "",
) -> tuple[str, str]:
    """
    Aplica las compuertas obligatorias F3 y F4 sobre la decisión de Casper.

    Retorna (decision_final, feedback_final).
    """
    # Si la decisión es «la pregunta era otra», pasa directamente
    if decision_original == DECISION_PREGUNTA_OTRA:
        return DECISION_PREGUNTA_OTRA, feedback

    # Si la decisión no es de aprobación, no bloqueamos con compuerta de tests
    if decision_original != DECISION_APROBADO:
        return decision_original, feedback

    # 1. Compuerta F3: Partes pendientes en el plan
    if plan is not None:
        ok_plan, err_plan = verificar_cierre_plan(plan)
        if not ok_plan:
            logger.warning(f"[CIERRE] Rechazado por compuerta F3: {err_plan}")
            return (
                DECISION_RECHAZADO,
                f"{feedback}\n\n---\n⚠️ {err_plan}",
            )

    # 2. Compuerta F4: Verificación de tests obligatoria
    if not compuerta_ok:
        logger.warning("[CIERRE] Rechazado por compuerta F4 (verificación en rojo)")
        msg_f4 = (
            f"{feedback}\n\n---\n"
            "⚠️ COMPUERTA F4 RECHAZADA: La entrega no puede aprobarse porque la "
            f"verificación automática falló:\n{compuerta_info}"
        )
        return DECISION_RECHAZADO, msg_f4

    # Ambas compuertas en verde: se adjunta el sello de verificación
    adjunto = f"\n\n---\n✅ Compuerta de verificación superada:\n{compuerta_info}" if compuerta_info else ""
    return DECISION_APROBADO, f"{feedback}{adjunto}"


def registrar_descarte_pregunta_otra(
    *,
    proyecto: str,
    ronda: str,
    enfoque: str,
    motivo: str,
    medicion: str = "",
    rescatable: str = "",
    inicio: Any = None,
) -> bool:
    """
    F5: Registra en bitácora/descartes.jsonl una ronda cerrada por 'la pregunta era otra'.
    """
    return registrar_descarte(
        proyecto=proyecto,
        ronda=ronda,
        enfoque=enfoque,
        filosofia="la pregunta era otra (desvío de foco)",
        motivo=motivo,
        medicion=medicion,
        rescatable=rescatable,
        inicio=inicio,
    )
