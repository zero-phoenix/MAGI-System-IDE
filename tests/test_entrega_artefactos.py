"""
Vacunas de la Fase 3: cierre de entrega de artefactos (MEGA PLAN v6.0 §B1, §C4).

Estos tests no tocan la red ni PyInstaller: el único camino a .exe pasa por
un `build_project_exe` falsificado que escribe un binario cualquiera — lo que
se prueba aquí es el CICLO (preflight → verificación → copia con hash →
evento), no el empaquetado, que ya cubre su propia suite.

El Tetris que se fabrica es el mismo patrón del informe original: pygame con
mainloop. Se verifica DE VERDAD con el guardián GUI (30 frames y rc=0) y se
entrega como .py — exactamente el flujo que quemó ~50 llamadas HTTP sin
entregar nada.

El conftest global ya redirige MAGI_DATA_DIR y MAGI_WORKSPACE a un tmp y
limpia los caches de `paths`; aquí solo se aísla el Escritorio (MAGI_DESKTOP),
que el conftest no toca.
"""
from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path

import pytest

from magi.core.bus import MagiBus
from magi.core.paths import workspace_dir
from magi.modules.studio import entrega
from magi.modules.studio.packager import PackagerResult

TETRIS_PY = """
import pygame


def main():
    pygame.init()
    ventana = pygame.display.set_mode((300, 600))
    reloj = pygame.time.Clock()
    corriendo = True
    while corriendo:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                corriendo = False
        pygame.display.flip()
        reloj.tick(30)
    pygame.quit()


if __name__ == "__main__":
    main()
"""

TETRIS = "Esta es la propuesta final:\n\n```python\n" + TETRIS_PY + "\n```\n"

ROTO = ("Propuesta:\n\n```python\n"
        "raise RuntimeError('pum')\n```\n")

SIN_CODIGO = "La propuesta final no trae bloques de código. Solo texto."


@pytest.fixture
def escritorio_tmp(tmp_path, monkeypatch):
    """Escritorio aislado: nada de este test toca el Escritorio real."""
    monkeypatch.setenv("MAGI_DESKTOP", str(tmp_path / "Escritorio"))
    return tmp_path / "Escritorio"


@pytest.fixture
def bus_evento():
    b = MagiBus()

    class Caja:
        def __init__(self):
            self.eventos: list = []

        def suscriptor(self, ev):
            self.eventos.append(ev)
    caja = Caja()
    b.subscribe("swarm.artefacto_listo", caja.suscriptor)
    b.subscribe("TERMINAL_OUT", caja.suscriptor)
    return b, caja


def _correr(coro):
    return asyncio.run(coro)


def test_preflight_nombre_vacio_bloquea():
    r = entrega.preflight(nombre="", exe=False)
    assert not r["ok"]
    assert any("nombre" in p for p in r["problemas"])


def test_preflight_exe_supera_en_entorno_normal(escritorio_tmp):
    r = entrega.preflight(nombre="tetris.exe", exe=True)
    assert r["ok"], r["problemas"]
    assert r["nombre_sano"] == "tetris.exe"


def test_nombre_sano_limpia_caracteres_y_reservados():
    assert entrega._nombre_sano("mal<|>nombre \"raro\".py") == "mal___nombre__raro_.py"
    assert entrega._nombre_sano("con.py") == "magi_con.py"
    assert entrega._nombre_sano("") == "artefacto"


def test_entrega_script_del_tetris_con_hash_y_evento(escritorio_tmp, bus_evento):
    bus, caja = bus_evento
    informe = _correr(entrega.fabricar_y_entregar(
        TETRIS, nombre="tetris_prueba", task_id="t-1", bus=bus,
        empaquetar=False, destino="escritorio"))
    assert informe.ok, informe.motivo
    assert informe.tipo == "script"
    assert informe.destino == "Escritorio"
    assert informe.nombre == "tetris_prueba.py"
    assert informe.ruta == escritorio_tmp / "tetris_prueba.py"
    assert informe.ruta.exists()

    rehash = hashlib.sha256(informe.ruta.read_bytes()).hexdigest()
    assert informe.sha256 == rehash
    assert informe.bytes_ == informe.ruta.stat().st_size

    respaldo = workspace_dir() / "artifacts" / "entregas" / "tetris_prueba.py"
    assert respaldo.exists()
    assert hashlib.sha256(respaldo.read_bytes()).hexdigest() == rehash

    topico = [e for e in caja.eventos if e.topic == "swarm.artefacto_listo"]
    assert len(topico) == 1
    assert topico[0].payload["task_id"] == "t-1"
    assert topico[0].payload["sha256"] == rehash
    assert topico[0].payload["tipo"] == "script"
    assert any(e.topic == "TERMINAL_OUT" for e in caja.eventos)


def test_la_segunda_entrega_no_pisa_la_primera(escritorio_tmp, bus_evento):
    bus, _ = bus_evento
    primero = _correr(entrega.fabricar_y_entregar(
        TETRIS, nombre="mismo_nombre", bus=bus, empaquetar=False))
    segundo = _correr(entrega.fabricar_y_entregar(
        TETRIS, nombre="mismo_nombre", bus=bus, empaquetar=False))
    assert primero.ok and segundo.ok
    assert primero.nombre == "mismo_nombre.py"
    assert segundo.nombre == "mismo_nombre_1.py"
    assert segundo.ruta.exists()


def test_entrega_exe_via_empaquetado_falsificado(escritorio_tmp, bus_evento, monkeypatch):
    bus, caja = bus_evento

    async def falso_build(project_dir, **kw):
        dist = Path(project_dir) / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        exe = dist / "simulacro.exe"
        exe.write_bytes(b"MZ" + b"\x00" * 1024)
        return PackagerResult(ok=True, exe_path=exe)

    monkeypatch.setattr(entrega, "build_project_exe", falso_build)
    informe = _correr(entrega.fabricar_y_entregar(
        TETRIS, nombre="tetris_exe", task_id="t-2", bus=bus,
        empaquetar=True, destino="escritorio"))
    assert informe.ok, informe.motivo
    assert informe.tipo == "exe"
    assert informe.nombre == "tetris_exe.exe"
    assert informe.ruta.read_bytes().startswith(b"MZ")
    assert informe.sha256 == hashlib.sha256(informe.ruta.read_bytes()).hexdigest()

    topico = [e for e in caja.eventos if e.topic == "swarm.artefacto_listo"]
    assert topico and topico[0].payload["tipo"] == "exe"


def test_entrega_a_workspace_cuando_se_pide(escritorio_tmp):
    informe = _correr(entrega.fabricar_y_entregar(
        TETRIS, nombre="via_workspace", empaquetar=False, destino="workspace"))
    assert informe.ok, informe.motivo
    assert informe.destino == "workspace"
    assert informe.ruta == workspace_dir() / "entregas" / "via_workspace.py"


def test_sin_escritorio_accesible_cae_en_workspace(escritorio_tmp, bus_evento, monkeypatch):
    monkeypatch.setattr(entrega, "escritorio", lambda: None)
    bus, _ = bus_evento
    informe = _correr(entrega.fabricar_y_entregar(
        TETRIS, nombre="sin_desk", bus=bus, empaquetar=False))
    assert informe.ok, informe.motivo
    assert informe.destino == "workspace"
    assert informe.ruta == workspace_dir() / "entregas" / "sin_desk.py"


def test_codigo_roto_no_se_entrega_y_explica_motivo(escritorio_tmp, bus_evento):
    bus, caja = bus_evento
    informe = _correr(entrega.fabricar_y_entregar(
        ROTO, nombre="roto", bus=bus, empaquetar=False))
    assert not informe.ok
    assert "verificación" in informe.motivo.lower()
    assert informe.ruta is None
    assert not (escritorio_tmp / "roto.py").exists()
    assert not [e for e in caja.eventos if e.topic == "swarm.artefacto_listo"]


def test_sin_bloques_de_codigo_no_hay_entrega(escritorio_tmp, bus_evento):
    bus, caja = bus_evento
    informe = _correr(entrega.fabricar_y_entregar(
        SIN_CODIGO, nombre="solo_texto", bus=bus))
    assert not informe.ok
    assert "bloques" in informe.motivo.lower()
    assert not [e for e in caja.eventos if e.topic == "swarm.artefacto_listo"]


def test_la_tool_se_registra_en_la_fabrica():
    """`entregar_artefacto` es alcanzable desde el enjambre (grafo de wiring)."""
    from magi.core.tools.registry import ToolRegistry
    from magi.modules.studio.tools import register_studio_tools

    reg = ToolRegistry()
    register_studio_tools(reg)
    t = reg.get("entregar_artefacto")
    assert t is not None
    assert t.parameters["required"] == ["nombre", "codigo"]
    assert t.access and {"write", "exec"} <= t.access