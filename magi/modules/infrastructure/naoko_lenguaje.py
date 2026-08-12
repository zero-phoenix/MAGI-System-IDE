"""
Cómo cuenta Naoko el estado del sistema, en lenguaje que sirva para decidir.

EL PROBLEMA
===========
Lo que Naoko decía era exacto y no se podía accionar:

    Hay 2 tareas bloqueadas esperando por ti (WAITING_USER_APPROVAL):
    task_29ceb5d6 (ronda 2), task_c95b7d00 (ronda 2)
    Hay 4 tareas en estado interrumpido (task_50f418e5, task_6c0c00a9, …)

Tres cosas fallan a la vez ahí:

1. **`task_29ceb5d6` no le dice nada a nadie.** Las conversaciones ya tienen
   título generado —«Juego Tetris portable»—; el identificador es de la base de
   datos, no del usuario.
2. **`WAITING_USER_APPROVAL` es un nombre de estado interno**, y aparecía tal
   cual en el mensaje. El usuario no tiene por qué conocer la máquina de
   estados de su propio programa.
3. **No dice qué hacer.** Enumerar sin proponer acción deja el trabajo a medias:
   el dato está, la decisión sigue siendo un acertijo.

Y todo iba mezclado: lo que espera al usuario junto a lo que espera al sistema,
cuando son cosas distintas y solo una le toca a él.

QUÉ HACE ESTE MÓDULO
====================
Convierte el estado crudo en frases con nombre y con acción. Son funciones
puras —dentro entra un diccionario, fuera sale texto— para poder probar lo que
se dice sin levantar el sistema entero.

El detalle técnico NO se pierde: se pliega. Naoko sigue teniendo los
identificadores y los estados internos en su contexto para diagnosticar; lo que
cambia es lo que le pone delante al usuario.
"""
from __future__ import annotations

__all__ = ["nombre_de_tarea", "en_cristiano", "que_te_toca", "resumen_humano"]

#: Nombres internos de estado -> lo que significan para quien lee.
#:
#: La clave no es traducir por traducir: es que cada estado venga con lo que
#: implica. «interrumpida» no dice si se perdió el trabajo; «se quedó a medias
#: y se retoma sola» sí.
_ESTADOS = {
    "WAITING_USER_APPROVAL": "esperando tu visto bueno",
    "in_progress": "trabajando",
    "interrumpida": "a medias, se retoma sola",
    "completed": "terminada",
    "cancelada": "cancelada por ti",
    "error": "falló",
}

#: Qué puede hacer el usuario con una tarea en cada estado. Vacío = nada que
#: hacer, y decirlo es tan útil como decir lo contrario.
_ACCIONES = {
    "WAITING_USER_APPROVAL": ("responde «sí» para cerrarla, o pide un cambio "
                              "concreto"),
    "interrumpida": "escríbele y sigue donde lo dejó",
    "error": "cuéntame el error y lo miro",
}

#: Más allá de esto, el enunciado se corta. Un título de tres líneas dentro de
#: una lista deja de ser un título.
_MAX_TITULO = 48


def nombre_de_tarea(tid: str, datos: dict | None = None) -> str:
    """
    Cómo llamar a una tarea delante del usuario.

    Prioridad: el título que ya se genera para la columna izquierda, luego el
    enunciado recortado, y solo si no hay nada, el identificador. Ese último
    caso es el que había siempre.
    """
    datos = datos or {}
    titulo = (datos.get("titulo") or "").strip()
    if titulo:
        return titulo
    orden = (datos.get("command") or "").strip().replace("\n", " ")
    if orden:
        if len(orden) > _MAX_TITULO:
            orden = orden[:_MAX_TITULO - 1].rstrip() + "…"
        return f"«{orden}»"
    return tid


def en_cristiano(estado: str) -> str:
    """El estado interno, dicho en lo que significa."""
    return _ESTADOS.get(estado, estado)


def que_te_toca(estado: str) -> str:
    """Qué puede hacer el usuario. Cadena vacía si no le toca a él."""
    return _ACCIONES.get(estado, "")


def resumen_humano(tareas: dict, vivo=None) -> str:
    """
    El estado del enjambre en frases con nombre y con acción.

    `vivo(tid)` dice si una tarea tiene bucle de ejecución de verdad. Se pasa
    como parámetro y no se consulta aquí para que esto siga siendo una función
    pura: sin eso, probar lo que Naoko DICE exigiría levantar el supervisor.

    La separación en dos bloques —lo tuyo y lo del sistema— es lo que más
    cambia respecto a la lista anterior: antes todo iba junto y había que
    deducir qué parte requería acción.
    """
    if not tareas:
        return "No hay ninguna conversación abierta ahora mismo."

    vivo = vivo or (lambda _t: False)
    tuyas: list[str] = []
    del_sistema: list[str] = []

    for tid, d in tareas.items():
        estado = d.get("status", "?")
        nombre = nombre_de_tarea(tid, d)
        ronda = d.get("round", 1)

        if estado == "WAITING_USER_APPROVAL":
            tuyas.append(f"**{nombre}** — el enjambre terminó su parte "
                         f"(ronda {ronda}) y {en_cristiano(estado)}. "
                         f"{que_te_toca(estado).capitalize()}.")
        elif estado == "in_progress" and vivo(tid):
            del_sistema.append(f"**{nombre}** — trabajando ahora mismo, "
                               f"ronda {ronda}.")
        elif estado == "in_progress":
            # Figura en curso y no lo está. Decir que trabaja seria falso, y es
            # justo el dato que llevó a Naoko a explicar demoras inexistentes.
            del_sistema.append(f"**{nombre}** — figura en curso pero no tiene "
                               f"nada ejecutándose; se quedó a medias y se "
                               f"retoma cuando le escribas.")
        elif estado == "interrumpida":
            del_sistema.append(f"**{nombre}** — {en_cristiano(estado)}.")
        elif estado in ("error",):
            tuyas.append(f"**{nombre}** — {en_cristiano(estado)}. "
                         f"{que_te_toca(estado).capitalize()}.")

    partes: list[str] = []
    if tuyas:
        partes.append("**Te toca a ti:**\n" + "\n".join(f"- {t}" for t in tuyas))
    if del_sistema:
        partes.append("**En marcha, sin que tengas que hacer nada:**\n"
                      + "\n".join(f"- {t}" for t in del_sistema))
    if not partes:
        return "No hay nada pendiente ni en marcha."
    return "\n\n".join(partes)
