"""
Los comandos de administración que puede escribir una persona en el input.

MEGAPLAN v11 B1. Medido el 5-sep-2026: «task.cancel task_x» tecleado arrancó
una tarea cuyo «proyecto» fue proponer desregistrar una tarea programada de
Windows — Balthasar la frenó, pero la ronda corrió y llegó a pedir aprobación.
Una ORDEN no se debate: se ejecuta. Este módulo decide si un texto es orden y
cuál; el kernel la despacha.

Lo que NO es orden aquí sigue su camino normal (ruta, clasificador, enjambre).
"""
from __future__ import annotations

__all__ = ["clasificar"]

#: Prefijos que reconocen las tres órdenes que una persona escribe sin
#: recordar dónde está el botón. Comparados en minúsculas y sin tildes.
_CANCEL = ("task.cancel", "cancelar tarea", "cancel task")
_ESTOP = ("parar todo", "parar_todo", "emergency_stop", "emergencia",
          "stop all")


def clasificar(comando: str) -> tuple[str, str]:
    """
    Devuelve `("cancel", objetivo)` o `("estop", "")` si `comando` es una
    orden de administración; `("", "")` si es un encargo normal.

    `objetivo` es el task_id citado tras la orden, o "" si no lo citó (el
    llamador decide entonces: tarea activa actual, por ejemplo).
    """
    if not isinstance(comando, str):
        return "", ""
    plano = comando.strip().lower()
    if not plano:
        return "", ""
    for prefijo in _CANCEL:
        if plano.startswith(prefijo):
            resto = plano[len(prefijo):].strip().split()
            objetivo = resto[0] if resto else ""
            return "cancel", objetivo
    if plano in _ESTOP or plano.startswith("parar todo "):
        return "estop", ""
    return "", ""
