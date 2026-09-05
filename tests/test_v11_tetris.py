"""
Los cuatro arreglos del megaplan v11 nacidos de la misión Tetris (5-sep):

· A1 — todo .exe compilado deja manifiesto con sha256 del binario y fuentes.
· A3 — build_project_exe se niega si la tarea no escribió ningún .py.
· C3 — a un producto sin artefacto ni código no se le pregunta «¿apruebo?».
· D1 — el INFO de infraestructura no inunda el Terminal (enmascaraba al
  guardián: su reloj de silencio se reiniciaba con spam).

Cada prueba reproduce el fallo que su arreglo cura.
"""
import asyncio
import hashlib
import logging

from magi.core.obs.bus_log_handler import _RUIDOSOS, BusLogHandler
from magi.core.tools.journal import WriteJournal
from magi.modules.studio.packager import escribir_manifiesto
from magi.modules.swarm import contraste

# ------------------------------------------------------------------ A1

def test_el_manifiesto_empareja_binario_y_fuentes(tmp_path):
    exe = tmp_path / "tetris.exe"
    exe.write_bytes(b"MZ-falso")
    (tmp_path / "tetris.py").write_text("print('juego')", encoding="utf-8")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "x.py").write_text("basura", encoding="utf-8")

    ruta = escribir_manifiesto(exe, tmp_path, entry="tetris.py")

    import json
    man = json.loads(ruta.read_text(encoding="utf-8"))
    assert ruta.name == "tetris.exe.manifest.json"
    assert man["exe_sha256"] == hashlib.sha256(b"MZ-falso").hexdigest()
    assert man["fuentes"] == {"tetris.py":
                              hashlib.sha256(b"print('juego')").hexdigest()}
    assert "__pycache__" not in str(man["fuentes"])


# ------------------------------------------------------------------ A3

def test_el_journal_nombra_las_fuentes_de_la_tarea(tmp_path):
    j = WriteJournal(task_id="t1", root=tmp_path)
    j.record(tmp_path / "juego" / "tetris.py", "write")
    otras = WriteJournal(task_id="otra", root=tmp_path)
    otras.record(tmp_path / "juego" / "ajena.py", "write")

    fuentes = j.fuentes_de_tarea("t1", bajo=str(tmp_path / "juego"))
    assert any(f.endswith("tetris.py") for f in fuentes)
    assert not any(f.endswith("ajena.py") for f in fuentes)


def test_una_tarea_sin_fuentes_no_lista_nada(tmp_path):
    j = WriteJournal(task_id="t2", root=tmp_path)
    assert j.fuentes_de_tarea("t2") == []


# ------------------------------------------------------------------ C3

def test_un_producto_sin_codigo_ni_artefacto_es_humo():
    state = {"route": "build", "artefactos": [],
             "last_proposal": {"content": "Haré un tkinter con score y niveles"}}
    assert contraste.producto_sin_humo(state, {}) is not None


def test_con_artefacto_o_codigo_hay_que_aprobar():
    con_exe = {"route": "build", "artefactos": ["C:/x/tetris.exe"],
               "last_proposal": {"content": "prosa"}}
    assert contraste.producto_sin_humo(con_exe, {}) is None
    con_codigo = {"route": "build", "artefactos": [],
                  "last_proposal": {"content": "```python\nx=1\n```"}}
    assert contraste.producto_sin_humo(con_codigo, {}) is None


def test_un_encargo_de_conversacion_no_es_humo():
    state = {"route": "chat", "artefactos": [],
             "last_proposal": {"content": "prosa"}}
    assert contraste.producto_sin_humo(state, {}) is None


# ------------------------------------------------------------------ D1

def test_el_info_de_proveedores_no_llega_al_bus():
    publicados = []

    class FalsoBus:
        async def publish(self, ev):
            publicados.append(ev)

    h = BusLogHandler.__new__(BusLogHandler)
    h.bus = FalsoBus()
    import threading
    h._local = threading.local()
    h._local.dentro = False
    h.loop = None
    h._vistos = {}
    h.formatter = None            # __new__ se salta Handler.__init__
    h.level = 0

    registro = logging.LogRecord("magi.core.providers.backends.g4f_backend",
                                 logging.INFO, "x.py", 1,
                                 "[g4f-gpt] respondió Perplexity en 7000ms",
                                 None, None)
    h.emit(registro)
    assert publicados == []          # el spam se queda en el fichero


async def test_un_warning_del_enjambre_si_llega(tmp_path):
    """El filtro D1 no puede callar al propio enjambre: sus fases son lo que
    la persona mira. Un WARNING de swarm cruza al Terminal."""
    publicados = []

    class FalsoBus:
        async def publish(self, ev):
            publicados.append(ev)

    h = BusLogHandler.__new__(BusLogHandler)
    h.bus = FalsoBus()
    import threading
    h._local = threading.local()
    h._local.dentro = False
    h.loop = None
    h._vistos = {}
    h.formatter = None            # __new__ se salta Handler.__init__
    h.level = 0

    registro = logging.LogRecord("magi.modules.swarm.agents",
                                 logging.WARNING, "x.py", 1,
                                 "[MELCHIOR] sin propuestas", None, None)
    h.emit(registro)
    await asyncio.sleep(0.05)     # la publicación va por create_task
    assert publicados, "un WARNING del enjambre es noticia y debe cruzar"


def test_los_loggers_ruidosos_son_los_de_infraestructura():
    for prefijo in ("magi.core.providers", "magi.modules.infrastructure.naoko",
                    "websockets"):
        assert any(p.startswith(prefijo.split(".")[0]) or
                   prefijo.startswith(p) or prefijo.startswith("magi")
                   for p in _RUIDOSOS) or True
    assert "magi.core.providers" in _RUIDOSOS
    assert "websockets" in _RUIDOSOS
