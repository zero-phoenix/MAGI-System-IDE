"""
El bloque de veredictos, fuera del bucle.

POR QUE ESTA AQUI Y NO EN EL ORQUESTADOR
========================================
`orchestrator.py` iba 1545 lineas de un techo de 1550 y las fases F2, F3 y F4
todavia tienen que cablearse. El techo de un trinquete no se sube nunca: se
conecta, se adelgaza o se extrae. Esto es lo tercero.

Lo que se movio es el bloque que decide que hacer con el veredicto de Casper:
aprobacion, revision, el cuarto veredicto (F5) y el fallo. No cambia ningun
comportamiento; las unicas transformaciones fueron mecanicas —`self` pasa a ser
el parametro `orq`, `break` pasa a `return True` y `continue` a `return False`—
y las cubren los tests del enjambre, que siguen mirando el orquestador real.

QUE DEVUELVE
============
True si el bucle de rondas debe pararse, False si debe seguir. El bloque era lo
ultimo del `while`, asi que `continue` y caer al final eran lo mismo: por eso
basta un booleano y no hace falta un tercer estado.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from magi.core.bus import BusEvent

logger = logging.getLogger(__name__)


async def procesar(orq: Any, *, task_id: str, state: dict, verdict: dict,
                   current_round: int) -> bool:
    """
    Aplica el veredicto de Casper. True = parar el bucle de rondas.
    """
    feedback_text = verdict.get("feedback", "").upper()
    is_asking_approval = "¿APRUEBAS" in feedback_text or "APRUEBAS" in feedback_text or verdict["decision"] == "APPROVED"

    # C1/C2 — SIN_ARBITRAJE entra por la misma puerta que una
    # aprobación, y a propósito.
    #
    # Sin esto caía al `else` final —«Tarea fallida tras N rondas»— y
    # el usuario perdía la tesis y la crítica, que estaban hechas. Una
    # tarea sin árbitro NO es una tarea fallida: es una tarea con dos
    # tercios del trabajo terminados y sin quien los cierre. Se entrega
    # lo que hay, se dice que falta el arbitraje, y decide el usuario.
    sin_arbitro = verdict["decision"] == "SIN_ARBITRAJE"

    if is_asking_approval or sin_arbitro or current_round >= state.get("max_rounds", 3):
        # Si escribiste algo mientras trabajabamos, se atiende ahora.
        if await orq._vaciar_cola(task_id):
            return False
        state["status"] = "WAITING_USER_APPROVAL"
        orq._persist(task_id)

        from . import contraste as _c  # C3 (v11): sin humo no se pregunta
        humo = _c.producto_sin_humo(state, verdict)
        if humo:
            state["status"] = "completed"
            orq._persist(task_id)
            for tema, carga in (("TERMINAL_OUT", {"content": humo}),
                                 ("swarm.entrega_incompleta", {"task_id": task_id, "motivo": humo})):
                await orq.bus.publish(BusEvent(topic=tema, payload=carga))  # noqa: E501
            return True
        from magi.modules.swarm import cierre as _cierre
        _cierre.evaluar_cierre_entrega(
            verdict.get("decision", ""), verdict.get("feedback", ""),
            plan=state.get("plan"))
        await orq._publish_approval(task_id, state, verdict)

        await orq.bus.publish(BusEvent(
            topic="TERMINAL_OUT",
            payload={"content": "[SWARM] Esperando tu aprobacion interactiva."}))
        # AQUÍ NO SE APARCA EL BUCLE: en v5.5.2 await approval_event colgaba la suite entera.
        # Con break la corrutina termina limpiamente y quien reanuda es _spawn_loop.
        return True  # Pausar el bucle hasta recibir input del usuario
    elif verdict["decision"] == "REJECTED_NEEDS_WORK":
        orq.memory_for(task_id).record(
            round_num=current_round,
            approach=(state.get("last_proposal") or {}).get("content", ""),
            outcome="refutado",
            reason=verdict.get("feedback", ""))
        state["round"] += 1
        state["command"] = f"Revisar propuesta considerando crítica: {verdict['feedback']}"
        await asyncio.sleep(1.0)
    elif verdict["decision"] == "LA_PREGUNTA_ERA_OTRA":
        # F5 — cuarto veredicto. El cuerpo vive en cierre.py: aqui no
        # cabe (trinquete) y ahi es donde estan las demas compuertas.
        from magi.modules.swarm import cierre as _f5
        await _f5.cerrar_por_desvio_de_foco(
            bus=orq.bus, task_id=task_id,
            encargo=state.get("command", ""),
            feedback=verdict.get("feedback", ""), ronda=current_round)
        state["status"] = "completed"
        orq._persist(task_id)
        return True
    else:
        state["status"] = "failed"
        await orq.bus.publish(BusEvent(
            topic="TERMINAL_OUT",
            payload={"content": f"[SWARM] Tarea fallida tras {current_round} rondas."}
        ))

    # Revision o fallo: el bucle sigue. Explicito porque la firma promete
    # un bool, y un None implicito solo funciona mientras nadie compare con
    # `is False`.
    return False
