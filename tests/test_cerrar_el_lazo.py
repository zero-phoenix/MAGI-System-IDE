"""
El modelo propone; la máquina construye (D3), y el veredicto baja con el
contrato incumplido (D2).

POR QUÉ EXISTE ESTE FICHERO
===========================
En cinco pruebas medidas entre el 16 y el 20 de agosto, el sistema escribió
hasta ocho bloques de código para encargos de `.exe` y llamó **cero veces** a
`build_project_exe` o a `entregar_artefacto`. La cadena de fábrica estaba
entera y nadie la invocaba.

Se probó a pedírselo en el prompt, con ejemplo. El contador siguió en cero.

De ahí sale la regla que fijan estos tests: **acordarse no es un mecanismo**.
"""
from __future__ import annotations

import pytest

from magi.core.blackboard import Blackboard
from magi.core.bus import MagiBus
from magi.modules.swarm.orchestrator import SwarmOrchestrator

PROPUESTA = "Aquí tienes el juego:\n\n```python\nprint('hola')\n```\n"


def _swarm() -> SwarmOrchestrator:
    return SwarmOrchestrator(Blackboard(), MagiBus())


@pytest.mark.parametrize("mandato,esperado", [
    ("crea un juego de ping pong en un exe portable", "ping"),
    ("Haz una replica del juego Tetris en un ejecutable unico portable", "tetris"),
    ("hazme un script que ordene ficheros", "ordene"),
])
def test_el_nombre_sale_del_encargo_no_de_un_identificador(mandato, esperado):
    """
    `pong.exe` en el Escritorio se entiende; `auditoria-1787209.exe` no.

    Es cosmético hasta que te toca buscar tu juego entre cinco ficheros con
    nombre de timestamp.
    """
    assert _swarm()._nombre_de_artefacto(mandato, "t-1") == esperado


async def test_construye_cuando_el_encargo_pide_artefacto(monkeypatch):
    swarm = _swarm()
    llamadas: list[dict] = []

    class _Informe:
        ok, ruta, sha256, bytes_ = True, "C:/Escritorio/ping.exe", "abc", 1234
        motivo = None

    # EL DOBLE ES ASÍNCRONO PORQUE EL ORIGINAL LO ES.
    #
    # La primera versión de este test usaba un doble síncrono y pasaba en
    # verde mientras el código real no ejecutaba la fábrica: envolvía una
    # corrutina en `asyncio.to_thread` y se quedaba con el objeto sin esperar.
    # Lo cazó la primera ejecución contra el sistema real, no el test.
    #
    # Un doble que no respeta la firma del original no prueba el original:
    # prueba una función que no existe.
    async def fabrica_falsa(contenido, *, nombre, task_id="", bus=None, **kw):
        llamadas.append({"nombre": nombre, "contenido": contenido})
        return _Informe()

    import magi.modules.studio.entrega as entrega_mod
    monkeypatch.setattr(entrega_mod, "fabricar_y_entregar", fabrica_falsa)

    state = {"command": "crea un ping pong en un exe portable",
             "last_proposal": {"content": PROPUESTA}}
    swarm.active_tasks["t-1"] = state
    await swarm._cerrar_el_lazo("t-1", state)

    assert llamadas, "la fábrica no se llamó: el lazo sigue abierto"
    assert llamadas[0]["nombre"] == "ping"
    assert state["artefactos"] == ["C:/Escritorio/ping.exe"]


async def test_no_construye_una_pregunta(monkeypatch):
    """Preguntar cómo se hace algo no es pedirlo, y fabricar sería peor."""
    swarm = _swarm()
    llamado = []
    import magi.modules.studio.entrega as entrega_mod
    async def _no_deberia_llamarse(*a, **k):
        llamado.append(1)

    monkeypatch.setattr(entrega_mod, "fabricar_y_entregar",
                        _no_deberia_llamarse)

    state = {"command": "explica como se hace un exe portable",
             "last_proposal": {"content": PROPUESTA}}
    await swarm._cerrar_el_lazo("t-2", state)
    assert not llamado


async def test_no_construye_sin_codigo(monkeypatch):
    swarm = _swarm()
    llamado = []
    import magi.modules.studio.entrega as entrega_mod
    async def _no_deberia_llamarse(*a, **k):
        llamado.append(1)

    monkeypatch.setattr(entrega_mod, "fabricar_y_entregar",
                        _no_deberia_llamarse)

    state = {"command": "crea un ping pong en un exe portable",
             "last_proposal": {"content": "Se implementó una arquitectura..."}}
    await swarm._cerrar_el_lazo("t-3", state)
    assert not llamado, "sin bloques no hay nada que construir"


async def test_no_se_interpone_si_el_agente_ya_entrego(monkeypatch):
    """Si el agente lo construyó por su cuenta —lo deseable— aquí no se toca."""
    swarm = _swarm()
    llamado = []
    import magi.modules.studio.entrega as entrega_mod
    async def _no_deberia_llamarse(*a, **k):
        llamado.append(1)

    monkeypatch.setattr(entrega_mod, "fabricar_y_entregar",
                        _no_deberia_llamarse)

    state = {"command": "crea un ping pong en un exe portable",
             "last_proposal": {"content": PROPUESTA},
             "artefactos": ["C:/ya/estaba.exe"]}
    await swarm._cerrar_el_lazo("t-4", state)
    assert not llamado


async def test_el_contrato_incumplido_degrada_el_veredicto():
    """
    D2 — la prueba E entregó APPROVED e [INCOMPLETO] en el mismo mensaje.

    Dos mecanismos que no se hablan dejan al usuario eligiendo a cuál creer, y
    va a creer al que le gusta.
    """
    swarm = _swarm()
    veredicto = {"decision": "APPROVED", "feedback": "aquí tienes tu juego"}
    state = {"command": "crea un ping pong en un exe portable",
             "last_proposal": {"content": "solo prosa, sin código"}}
    swarm.active_tasks["t-5"] = state

    await swarm._publish_approval("t-5", state, veredicto)

    assert veredicto["decision"] == "INCOMPLETO"
    assert state.get("entrega_incompleta")
