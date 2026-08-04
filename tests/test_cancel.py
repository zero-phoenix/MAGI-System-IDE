"""
Cancelación real de tareas y procesos (§7.3).

EL BOTÓN QUE NO PARABA NADA
===========================
`Kernel._handle_estop` era, entero:

    logger.critical("E-STOP INVOCADO DESDE LA GUI")
    return "EMERGENCY_STOP_TRIGGERED"

Una línea de log y una cadena con aspecto de éxito. Y el del orquestador
publicaba "aplicando kill-switch local automatizado" sin aplicar ninguno.

Estos tests NO comprueban que se llame a cancel(). Comprueban que un proceso
que estaba vivo deja de estarlo — que es la única forma de probar un botón de
parada, porque el modo de fallo era precisamente decir que paraba.
"""
import asyncio
import sys

import pytest

from magi.core.cancel import CancelReport, TaskSupervisor, reset_supervisor, supervisor
from source_helpers import code_of


@pytest.fixture(autouse=True)
def supervisor_limpio():
    reset_supervisor()
    yield
    reset_supervisor()


async def _proceso_eterno():
    """Un proceso que no termina solo: si sigue vivo, es que no lo mataron."""
    return await asyncio.create_subprocess_exec(
        sys.executable, "-c", "import time\nwhile True: time.sleep(0.2)",
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)


# --------------------------------------------------- lo que de verdad importa

@pytest.mark.asyncio
async def test_mata_un_proceso_que_seguia_vivo():
    """
    LA PRUEBA. No que se llame a terminate(): que el proceso muera.
    """
    sup = TaskSupervisor()
    proc = await _proceso_eterno()
    sup.register_process("t1", proc)
    assert proc.returncode is None, "el proceso debería estar vivo"

    informe = await sup.cancel("t1")

    assert proc.returncode is not None, "EL PROCESO SIGUE VIVO tras cancelar"
    assert informe.processes_killed == 1
    assert informe.stopped_anything


@pytest.mark.asyncio
async def test_cancela_un_bucle_asincrono_en_marcha():
    sup = TaskSupervisor()
    empezado = asyncio.Event()

    async def bucle():
        empezado.set()
        await asyncio.sleep(3600)

    handle = asyncio.create_task(bucle())
    sup.register_loop("t1", handle)
    await empezado.wait()

    informe = await sup.cancel("t1")
    assert handle.cancelled() or handle.done()
    assert informe.loops_cancelled == 1


@pytest.mark.asyncio
async def test_la_parada_de_emergencia_alcanza_a_todas_las_tareas():
    sup = TaskSupervisor()
    procesos = []
    for i in range(3):
        p = await _proceso_eterno()
        sup.register_process(f"t{i}", p)
        procesos.append(p)

    informe = await sup.cancel_all()
    assert informe.processes_killed == 3
    assert all(p.returncode is not None for p in procesos), \
        "la parada de emergencia dejó procesos vivos"


@pytest.mark.asyncio
async def test_cancelar_una_tarea_no_toca_las_demas():
    """
    §7.3 pide "parar un turno a mitad sin matar la app". Si tienes tres
    conversaciones y una se va por las ramas, no quieres tirar las otras dos.
    """
    sup = TaskSupervisor()
    victima = await _proceso_eterno()
    superviviente = await _proceso_eterno()
    sup.register_process("mala", victima)
    sup.register_process("buena", superviviente)

    await sup.cancel("mala")
    assert victima.returncode is not None
    assert superviviente.returncode is None, "se llevó por delante otra tarea"
    await sup.cancel("buena")


@pytest.mark.asyncio
async def test_usa_terminate_antes_que_kill():
    """
    Matar sin avisar puede dejar a medias justamente la escritura que se
    quería parar. Primero SIGTERM, y solo si no atiende, SIGKILL.
    """
    sup = TaskSupervisor()
    # Este proceso SÍ atiende a SIGTERM y sale con código 0.
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-c",
        "import signal,sys,time\n"
        "signal.signal(signal.SIGTERM, lambda *a: sys.exit(0))\n"
        "while True: time.sleep(0.1)",
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    sup.register_process("t1", proc)
    await asyncio.sleep(0.4)          # que llegue a instalar el handler

    await sup.cancel("t1")
    assert proc.returncode == 0, \
        f"salió con {proc.returncode}: se usó SIGKILL sin dar margen a SIGTERM"


@pytest.mark.asyncio
async def test_mata_al_que_ignora_sigterm():
    """Contraprueba: el margen no puede convertirse en 'no se para'."""
    sup = TaskSupervisor()
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-c",
        "import signal,time\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        "while True: time.sleep(0.1)",
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    sup.register_process("t1", proc)
    await asyncio.sleep(0.4)

    informe = await sup.cancel("t1")
    assert proc.returncode is not None, "un proceso que ignora SIGTERM sobrevivió"
    assert informe.processes_killed == 1


# ------------------------------------------------------- informe honesto

@pytest.mark.asyncio
async def test_dice_cuando_no_habia_nada_que_parar():
    """
    No puede devolver algo con aspecto de éxito si no paró nada: es
    exactamente lo que hacía el handler anterior con
    "EMERGENCY_STOP_TRIGGERED".
    """
    informe = await TaskSupervisor().cancel_all()
    assert informe.nothing_running
    assert not informe.stopped_anything
    assert "No había nada en marcha" in informe.render()


def test_avisa_de_los_procesos_que_no_murieron():
    r = CancelReport(task_ids=["t1"], processes_killed=1, processes_failed=2)
    texto = r.render()
    assert "NO murieron" in texto and "a mano" in texto


@pytest.mark.asyncio
async def test_un_proceso_ya_muerto_no_cuenta_como_fallo():
    sup = TaskSupervisor()
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-c", "pass",
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    await proc.wait()
    sup.register_process("t1", proc)
    informe = await sup.cancel("t1")
    assert informe.processes_failed == 0


# ------------------------------------------------------------- contabilidad

@pytest.mark.asyncio
async def test_el_registro_se_limpia_solo():
    """
    Sin auto-limpieza, `running_tasks()` acumularía tareas terminadas y
    acabaría mintiendo sobre lo que hay en marcha — que es el mismo defecto
    que estamos corrigiendo, en otro sitio.
    """
    sup = TaskSupervisor()

    async def corto():
        await asyncio.sleep(0.01)

    handle = asyncio.create_task(corto())
    sup.register_loop("t1", handle)
    assert "t1" in sup.running_tasks()
    await handle
    await asyncio.sleep(0.05)
    assert "t1" not in sup.running_tasks(), "el registro no se limpió"


@pytest.mark.asyncio
async def test_running_tasks_ve_procesos_y_bucles():
    sup = TaskSupervisor()
    proc = await _proceso_eterno()
    sup.register_process("con_proceso", proc)
    handle = asyncio.create_task(asyncio.sleep(3600))
    sup.register_loop("con_bucle", handle)

    assert set(sup.running_tasks()) == {"con_proceso", "con_bucle"}
    assert sup.is_running("con_proceso") and not sup.is_running("fantasma")
    await sup.cancel_all()


def test_el_supervisor_es_unico():
    assert supervisor() is supervisor()


# ---------------------------------------------------------------- cableado

def test_ningun_bucle_del_enjambre_tira_su_handle():
    """
    El handle de `asyncio.create_task(...)` se descartaba, así que no existía
    ningún objeto al que pedirle que parase.

    Se comprueba con AST y no buscando la cadena: `handle = create_task(...)`
    CONTIENE el mismo texto y es exactamente lo correcto. Lo que hay que
    prohibir es la llamada cuyo resultado se tira — un `ast.Expr` — no la
    llamada.
    """
    import ast
    from pathlib import Path

    ruta = (Path(__file__).resolve().parents[1]
            / "magi/modules/swarm/orchestrator.py")
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))

    tirados = []
    for nodo in ast.walk(arbol):
        # Un create_task como sentencia suelta: nadie se queda el handle.
        if not isinstance(nodo, ast.Expr) or not isinstance(nodo.value, ast.Call):
            continue
        fn = nodo.value.func
        if getattr(fn, "attr", None) == "create_task":
            tirados.append(nodo.lineno)

    assert not tirados, (
        f"líneas {tirados}: se descarta el handle de create_task, así que esa "
        f"tarea no se puede cancelar")
    assert "register_loop" in code_of(ruta)


def test_run_command_inscribe_su_subproceso():
    from pathlib import Path
    src = code_of(Path(__file__).resolve().parents[1]
                  / "magi/core/tools/builtin.py")
    assert "register_process" in src, \
        "los procesos del agente quedan fuera del alcance de la parada"
    assert "forget_process" in src, \
        "sin darlos de baja, el supervisor cree que siguen vivos"


def test_el_estop_del_kernel_cancela_de_verdad():
    import inspect

    from magi.core.kernel import Kernel
    from source_helpers import strip_py_comments
    src = strip_py_comments(inspect.getsource(Kernel._handle_estop).lstrip())
    assert "cancel_all" in src, "el botón de parada sigue sin parar nada"
    assert "EMERGENCY_STOP_TRIGGERED" not in src


def test_el_mensaje_de_contingencia_ya_no_promete_un_kill_switch():
    """Decía "aplicando kill-switch local automatizado" sin aplicar ninguno."""
    from pathlib import Path
    src = code_of(Path(__file__).resolve().parents[1]
                  / "magi/modules/swarm/orchestrator.py")
    assert "kill-switch local automatizado" not in src
    assert "Procesos terminados:" in src


def test_la_interfaz_puede_parar_una_sola_tarea():
    """
    §7.3: "poder parar un turno a mitad sin matar la app". Sin el botón, la
    capacidad existiría en el backend y el usuario no podría alcanzarla.
    """
    from pathlib import Path
    raiz = Path(__file__).resolve().parents[1]
    socket = code_of(raiz / "magi-gui/src/useMagiSocket.ts")
    assert "task.cancel" in socket, "la interfaz no sabe pedir la cancelación"
    assert "task.cancelled" in socket, "no escucha el informe de lo que se paró"
    app = code_of(raiz / "magi-gui/src/App.tsx")
    assert "cancelTask" in app and "PARAR ESTA" in app


def test_la_auto_ejecucion_queda_bajo_el_supervisor():
    """
    El proceso que más urge poder parar: un script generado por el modelo
    corriendo en la máquina del usuario, en PowerShell con la política
    saltada. Estaba fuera del alcance de la parada.
    """
    from pathlib import Path
    src = code_of(Path(__file__).resolve().parents[1]
                  / "magi/modules/swarm/orchestrator.py")
    i = src.find("auto_script")
    assert i > 0
    assert "register_process" in src[i:i + 3000], \
        "el script auto-ejecutado no se inscribe: la parada no lo alcanza"
