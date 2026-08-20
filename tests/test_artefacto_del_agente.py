"""
Si el agente ya lo construyó, hay que reconocerlo — y comprobarlo (D10).

EL FALLO MÁS IRÓNICO DE LA SERIE
================================
20-ago, encargo «ping pong de 32 bits a todo color en un .exe portable».
Melchior construyó **dos ejecutables de verdad** —tkinter, 9 MB, con
`--formato` y `--autotest`, citando las reglas C10 y C16 del prompt— y los dejó
en `workspace/`. Se comprobó después a mano: los dos arrancan y salen con
código 0.

El sistema los ignoró, intentó fabricar otro desde bloques que no existían, y
cerró la entrega como `[INCOMPLETO]`. **El trabajo estaba hecho y el propio
sistema decía que no.**

La causa: el estado de la tarea no se enteraba de lo que hacían las
herramientas del agente.
"""
from __future__ import annotations

from magi.core.blackboard import Blackboard
from magi.core.bus import MagiBus
from magi.modules.swarm.orchestrator import SwarmOrchestrator


def _swarm() -> SwarmOrchestrator:
    return SwarmOrchestrator(Blackboard(), MagiBus())


async def test_reconoce_el_exe_que_construyo_el_agente(tmp_path):
    exe = tmp_path / "ping_pong.exe"
    exe.write_bytes(b"MZ" + b"\0" * 500)

    state = {"command": "crea un ping pong en un exe portable"}
    texto = (f"**Ruta del Artefacto**: `{exe}`\n"
             "**Hash SHA256**: `2C80DBCA...`\n"
             "Portabilidad: tkinter, 9.39 MB.")

    swarm = _swarm()
    swarm.active_tasks["t-1"] = state
    assert await swarm._registrar_artefactos_del_agente("t-1", state, texto) is True
    assert state["artefactos"] == [str(exe)]
    assert state["exe_path"] == str(exe)


async def test_una_ruta_que_no_existe_es_prosa_no_evidencia():
    """
    Este proyecto ya pagó caro tratar una afirmación como un hecho: «se
    compiló exitosamente el binario ejecutable único portable», sin binario.
    """
    state = {"command": "crea un ping pong en un exe portable"}
    texto = "Ruta: `C:\\Users\\nadie\\no_existe_jamas_12345.exe`"
    swarm = _swarm()
    assert await swarm._registrar_artefactos_del_agente("t-2", state, texto) is False
    assert "artefactos" not in state


async def test_un_exe_vacio_tampoco_cuenta(tmp_path):
    vacio = tmp_path / "hueco.exe"
    vacio.write_bytes(b"")
    state = {"command": "crea un juego en un exe portable"}
    swarm = _swarm()
    assert await swarm._registrar_artefactos_del_agente("t-3", state, f"`{vacio}`") is False


async def test_con_artefacto_del_agente_la_fabrica_no_se_interpone(tmp_path, monkeypatch):
    """Lo deseable es que lo construya el agente; entonces aquí no se toca."""
    exe = tmp_path / "juego.exe"
    exe.write_bytes(b"MZ" + b"\0" * 100)
    llamado = []

    import magi.modules.studio.entrega as entrega_mod

    async def _no_deberia(*a, **k):
        llamado.append(1)

    monkeypatch.setattr(entrega_mod, "fabricar_y_entregar", _no_deberia)

    swarm = _swarm()
    state = {"command": "crea un juego en un exe portable",
             "last_proposal": {"content": f"Listo en `{exe}`\n```\nprint(1)\n```"}}
    swarm.active_tasks["t-4"] = state
    await swarm._cerrar_el_lazo("t-4", state)

    assert not llamado, "no hay que reconstruir lo que ya existe"
    assert state["artefactos"] == [str(exe)]
