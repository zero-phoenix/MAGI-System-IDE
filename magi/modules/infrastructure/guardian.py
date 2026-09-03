"""
El perro guardián de la ronda dormida.

QUÉ PROTEGE
===========
La supervisión del 2-sep-2026 dejó una tarea real en «in_progress» con el
bus MUDO durante más de 20 minutos: la ronda se quedó colgada entre la
réplica y la síntesis, sin error, sin log y sin que nadie lo dijera. R2
vigila el ARRANQUE de la ronda; nada vigilaba que una ronda viva siga
produciendo eventos.

LA REGLA, DICHA SIMPLE
======================
Si hay tareas vivas y el bus lleva `umbral` segundos sin emitir NADA, eso
no es pausa de proveedor — los proveedores fallan ruidosamente, con
timeouts y failovers que dejan traza. Es una ronda dormida, y se publica
como `ritsuko.ronda_dormida` con los task_id y los segundos de silencio.

Igual que R2 y R4: es un hecho auditable, no una orden. El guardián no
cancela, no reinvida la ronda ni toca al orquestador.
"""
from __future__ import annotations

import asyncio
import logging
import time

from magi.core.bus import BusEvent

logger = logging.getLogger(__name__)

__all__ = ["UMBRAL_SILENCIO_S", "deberia_alertar", "vigilar"]

#: Diez minutos de bus MUDO con tareas vivas. Los proveedores gratuitos
#: fallan ruidosamente (timeouts, failovers, «tud.»); el silencio total no
#: es una parada de red, es un cuelgue. El margen es holgado para no
#: confundirlo con una verificación larga de verdad.
UMBRAL_SILENCIO_S = 600.0


def deberia_alertar(vivas: dict, silencio_s: float,
                    umbral: float = UMBRAL_SILENCIO_S) -> dict | None:
    """
    El juicio, separado del reloj para poder probarlo sin esperar.

    `vivas` es {task_id: status} tal cual estén: el juicio filtra aquí
    qué cuenta como viva, para que cualquier llamador aplique la misma
    definición. Devuelve la carga del hallazgo, o None si no hay nada
    que decir.
    """
    en_curso = {tid: st for tid, st in (vivas or {}).items()
                if st in ("in_progress", "running", "STARTED",
                          "WAITING_VERIFICATION")}
    if not en_curso or silencio_s <= umbral:
        return None
    return {"vivas": sorted(en_curso), "silencio_s": round(silencio_s),
            "umbral_s": umbral}


async def vigilar(bus, swarm, umbral: float = UMBRAL_SILENCIO_S) -> None:
    """Bucle eterno: marca el último evento y alerta si el silencio crece."""
    ultimo = time.monotonic()

    async def anota(_: BusEvent) -> None:
        nonlocal ultimo
        ultimo = time.monotonic()

    bus.subscribe("*", anota)
    while True:
        await asyncio.sleep(60)
        activas = getattr(swarm, "active_tasks", None) or {}
        vivas = {tid: (st or {}).get("status") for tid, st in activas.items()}
        carga = deberia_alertar(vivas, time.monotonic() - ultimo, umbral)
        if carga is None:
            continue
        logger.info("[guardian] ronda dormida: %s", carga)
        await bus.publish(BusEvent(topic="ritsuko.ronda_dormida",
                                   payload=carga))
        await bus.publish(BusEvent(topic="ritsuko.log", payload={
            "agent": "RITSUKO",
            "content": (f"[GUARDIÁN] Tareas {', '.join(carga['vivas'])} "
                        f"vivas y {carga['silencio_s']} s sin un solo "
                        "evento. No es pausa de proveedor: es una ronda "
                        "dormida. Un reinicio de la tarea es la salida "
                        "razonable; este aviso no la toca.")}))
        # Y no repetir el mismo aviso cada minuto: reiniciar la marca de
        # silencio equivale a haberlo dicho, no a haberlo arreglado.
        ultimo = time.monotonic()
