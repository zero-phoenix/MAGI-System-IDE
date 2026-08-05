"""
Cancelación real de tareas y procesos (Plan MAGI 9.0 §7.3).

EL BOTÓN QUE NO PARABA NADA
===========================
La interfaz tiene un botón de parada de emergencia. Manda `KILL_ALL_PROCESSES`,
llega a `Kernel._handle_estop`, y esto es lo que hacía ese handler ENTERO:

    async def _handle_estop(self, payload, websocket):
        logger.critical("E-STOP INVOCADO DESDE LA GUI")
        return "EMERGENCY_STOP_TRIGGERED"

Escribe una línea de log y devuelve una cadena. No cancela ningún bucle, no
mata ningún proceso. Los `_orchestrate_loop` seguían corriendo y cualquier
subproceso lanzado por `run_command` seguía vivo.

Y el del orquestador era peor, porque además lo decía al revés:

    "Abortando operaciones del Enjambre inmediatamente y aplicando
     kill-switch local automatizado."

No se aplicaba ningún kill-switch. Un mensaje que afirma haber parado algo
que sigue corriendo es exactamente lo contrario de lo que hace falta en un
botón de parada.

POR QUÉ ESTO IMPORTA MÁS QUE OTRAS COSAS
========================================
Este sistema tiene acceso sin restricciones a la máquina del usuario, por
decisión suya y con su autorización. Esa decisión es defendible —lo que se
añadió en §4.2 fue REVERSIBILIDAD, no permisos— pero descansa sobre dos
salidas: poder deshacer lo hecho, y poder PARAR lo que se está haciendo. El
journal cubría la primera. La segunda no existía.

Un agente al que puedes parar es un agente al que puedes dejar suelto. Uno que
no puedes parar acabas vigilándolo, y eso sí es una limitación real.

QUÉ HACE ESTE MÓDULO
====================
Lleva la cuenta de lo que hay en marcha —bucles asíncronos y subprocesos, por
tarea— y lo cancela de verdad. Y devuelve un informe de lo que PARÓ
REALMENTE, no de lo que intentó: si un proceso no muere, se dice.
"""
from __future__ import annotations

import asyncio
import contextlib
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

#: Margen para que un proceso atienda a SIGTERM antes de ir a por SIGKILL.
#: Terminar limpio deja que el proceso cierre ficheros y vacíe buffers; matar
#: sin más puede dejar a medias justamente la escritura que se quería parar.
GRACE_SECONDS = 3.0

#: Vueltas máximas al barrer procesos. Hacen falta varias porque una tarea
#: puede inscribir un proceso nuevo mientras se está esperando a otro, pero
#: no pueden ser infinitas: un proceso que se reproduce dejaría la parada
#: colgada, que es justo lo contrario de lo que se quiere.
MAX_SWEEPS = 4


@dataclass
class CancelReport:
    """Lo que se paró DE VERDAD. Sin adornos."""
    task_ids: list[str] = field(default_factory=list)
    loops_cancelled: int = 0
    #: Bucles que agotaron la gracia y SIGUEN VIVOS. Existe porque sin él se
    #: contaban como cancelados y el informe mentía.
    loops_failed: int = 0
    processes_killed: int = 0
    processes_failed: int = 0
    nothing_running: bool = False

    @property
    def stopped_anything(self) -> bool:
        return bool(self.loops_cancelled or self.processes_killed)

    def render(self) -> str:
        if self.nothing_running:
            return ("No había nada en marcha que parar. El sistema ya estaba "
                    "en reposo.")
        partes = []
        if self.loops_cancelled:
            partes.append(f"{self.loops_cancelled} tarea(s) del enjambre "
                          f"canceladas")
        if self.processes_killed:
            partes.append(f"{self.processes_killed} proceso(s) terminados")
        texto = "PARADA: " + (", ".join(partes) if partes
                              else "no se pudo parar nada")
        if self.processes_failed:
            texto += (f"\nAVISO: {self.processes_failed} proceso(s) NO "
                      f"murieron. Compruébalos a mano: pueden seguir "
                      f"escribiendo en disco.")
        if self.loops_failed:
            texto += (f"\nAVISO: {self.loops_failed} tarea(s) del enjambre NO "
                      f"soltaron y siguen corriendo. Pueden seguir gastando "
                      f"cuota y escribiendo ficheros.")
        if self.task_ids:
            texto += f"\nTareas: {', '.join(self.task_ids)}"
        return texto

    def to_payload(self) -> dict[str, Any]:
        return {"task_ids": self.task_ids,
                "loops_cancelled": self.loops_cancelled,
                "loops_failed": self.loops_failed,
                "processes_killed": self.processes_killed,
                "processes_failed": self.processes_failed,
                "nothing_running": self.nothing_running,
                "stopped_anything": self.stopped_anything,
                "detail": self.render()}


class TaskSupervisor:
    """
    Registro de lo que está en marcha, para poder pararlo.

    Los handles de `asyncio.create_task(...)` se descartaban al crearlos
    (`orchestrator.py:245,270`), así que ni siquiera existía un objeto al que
    pedirle que parase. Aquí se guardan.
    """

    def __init__(self):
        self._loops: dict[str, set[asyncio.Task]] = {}
        self._procs: dict[str, set[Any]] = {}

    # ---------------------------------------------------------- inscripción

    def register_loop(self, task_id: str, loop_task: asyncio.Task) -> None:
        self._loops.setdefault(task_id, set()).add(loop_task)
        # Auto-limpieza: sin esto el diccionario crece con cada tarea
        # terminada y `running_tasks()` acabaría mintiendo sobre lo que hay
        # en marcha.
        loop_task.add_done_callback(
            lambda t, tid=task_id: self._forget_loop(tid, t))

    def _forget_loop(self, task_id: str, loop_task: asyncio.Task) -> None:
        s = self._loops.get(task_id)
        if s:
            s.discard(loop_task)
            if not s:
                self._loops.pop(task_id, None)

    def register_process(self, task_id: str | None, proc: Any) -> None:
        """Un subproceso lanzado por una herramienta durante esta tarea."""
        self._procs.setdefault(task_id or "_sin_tarea", set()).add(proc)

    def forget_process(self, task_id: str | None, proc: Any) -> None:
        s = self._procs.get(task_id or "_sin_tarea")
        if s:
            s.discard(proc)

    # ------------------------------------------------------------- consulta

    def running_tasks(self) -> list[str]:
        vivos = [t for t, s in self._loops.items()
                 if any(not x.done() for x in s)]
        return sorted(set(vivos) | {t for t, s in self._procs.items()
                                    if any(p.returncode is None for p in s)})

    def is_running(self, task_id: str) -> bool:
        return task_id in self.running_tasks()

    # ---------------------------------------------------------- cancelación

    async def _kill_one(self, proc: Any) -> tuple[int, int]:
        """Termina un proceso. Devuelve (muertos, fallidos) como 0/1."""
        if proc.returncode is not None:
            return 0, 0
        try:
            proc.terminate()              # SIGTERM: que cierre limpio
            try:
                await asyncio.wait_for(proc.wait(), timeout=GRACE_SECONDS)
            except asyncio.TimeoutError:
                proc.kill()               # no atendió: SIGKILL
                # El wait() tras kill() no es opcional: sin él el transporte
                # queda sin limpiar y el proceso se convierte en zombi, con
                # "Event loop is closed" al recolectarlo.
                await asyncio.wait_for(proc.wait(), timeout=GRACE_SECONDS)
            return 1, 0
        except ProcessLookupError:
            return 1, 0                   # ya había terminado por su cuenta
        except Exception as e:
            logger.error("[cancelar] no se pudo terminar un proceso: %s", e)
            return 0, 1

    async def stop_processes(self, task_id: str) -> tuple[int, int]:
        """
        Mata los procesos de una tarea, incluidos los que aparezcan mientras.

        DOS FALLOS QUE TUVO ESTO Y QUE DEJABAN PROCESOS VIVOS:

        1. Borraba la entrada entera con `pop()` al terminar. Un proceso
           inscrito DURANTE la ventana de gracia —hasta 6 segundos por
           proceso— se perdía del registro sin haber sido tocado: seguía
           corriendo y ya nadie podía alcanzarlo. La siguiente parada decía
           "no había nada en marcha".

        2. Se llamaba DESPUÉS de cancelar el bucle, y eso lo vaciaba (ver
           `cancel`).

        Ahora se repite hasta que no queda nada vivo, con un tope de vueltas
        para que un proceso que se reproduce no bloquee la parada para
        siempre. Y solo se descartan los que de verdad han muerto.
        """
        muertos = fallidos = 0
        for _ in range(MAX_SWEEPS):
            pendientes = [p for p in self._procs.get(task_id, ())
                          if p.returncode is None]
            if not pendientes:
                break
            for proc in pendientes:
                m, f = await self._kill_one(proc)
                muertos += m
                fallidos += f
        # Se descartan SOLO los que ya no están vivos: los que sobrevivieron
        # tienen que seguir siendo visibles para poder intentarlo otra vez.
        vivos = {p for p in self._procs.get(task_id, ()) if p.returncode is None}
        if vivos:
            self._procs[task_id] = vivos
        else:
            self._procs.pop(task_id, None)
        return muertos, fallidos

    async def cancel(self, task_id: str) -> CancelReport:
        """
        Para una tarea concreta: PRIMERO sus procesos, luego su bucle.

        EL ORDEN NO ES UN DETALLE. Estaba al revés y por eso no paraba nada:

            proceso vivo, pid 14750
            PARADA: 1 tarea(s) del enjambre canceladas
            processes_killed: 0
            ¿SIGUE VIVO el proceso tras cancelar? True

        Cancelar el bucle primero ejecuta su `finally`, y el `finally` de
        `run_command` y de `_auto_exec` llama a `forget_process(...)` para dar
        de baja el subproceso. Cuando después llegaba el turno de matarlos, el
        registro ya estaba vacío. El informe decía "PARADA" con el script
        todavía escribiendo en disco — exactamente el fallo que este módulo se
        escribió para eliminar, reproducido dentro de él.

        Matando primero, el proceso muere mientras el bucle sigue esperándolo,
        y el bucle se desenreda solo.
        """
        informe = CancelReport(task_ids=[task_id])

        muertos, fallidos = await self.stop_processes(task_id)
        informe.processes_killed = muertos
        informe.processes_failed = fallidos

        for loop_task in list(self._loops.get(task_id, ())):
            if loop_task.done():
                continue
            loop_task.cancel()
            try:
                # Con timeout: `cancel()` corre dentro de un handler RPC que
                # se atiende en serie, así que un bucle que no atiende a la
                # cancelación bloquearía el canal entero — incluida la
                # siguiente petición de parada.
                await asyncio.wait_for(asyncio.shield(loop_task),
                                       timeout=GRACE_SECONDS)
            except asyncio.TimeoutError:
                # NO cuenta como cancelado. Agotar la gracia significa que el
                # bucle sigue vivo: se come la cancelación, o su limpieza tarda
                # más de GRACE_SECONDS. Sumarlo a `loops_cancelled` hacía que
                # el informe dijera «1 tarea cancelada» de algo que seguía
                # corriendo — exactamente lo que este módulo existe para no
                # hacer, aplicado hasta ahora solo a los procesos.
                logger.warning("[cancelar] %s no soltó en %.1fs: SIGUE VIVO",
                               task_id, GRACE_SECONDS)
                informe.loops_failed += 1
                continue
            except asyncio.CancelledError:
                pass
            except Exception as e:        # el bucle murió por otra razón
                logger.debug("[cancelar] %s terminó con %s", task_id, e)
            informe.loops_cancelled += 1

        # Segunda pasada: al desenredarse, el bucle puede haber lanzado algo.
        m2, f2 = await self.stop_processes(task_id)
        informe.processes_killed += m2
        informe.processes_failed += f2

        informe.nothing_running = not (informe.stopped_anything
                                       or informe.processes_failed
                                       or informe.loops_failed)
        if not any(not t.done() for t in self._loops.get(task_id, ())):
            self._loops.pop(task_id, None)

        logger.warning("[cancelar] %s", informe.render().replace("\n", " · "))
        return informe

    async def cancel_all(self) -> CancelReport:
        """
        Parada de emergencia de verdad.

        Es lo que el botón de la interfaz decía hacer y no hacía.
        """
        ids = sorted(set(self._loops) | set(self._procs))
        total = CancelReport()
        for tid in ids:
            parcial = await self.cancel(tid)
            total.task_ids.extend(parcial.task_ids)
            total.loops_cancelled += parcial.loops_cancelled
            total.processes_killed += parcial.processes_killed
            total.processes_failed += parcial.processes_failed
        total.nothing_running = not (total.stopped_anything
                                     or total.processes_failed)
        return total


#: Supervisor del proceso. Las herramientas lo alcanzan sin tener que
#: recibirlo por parámetro a través de siete capas.
_SUPERVISOR: TaskSupervisor | None = None


def supervisor() -> TaskSupervisor:
    global _SUPERVISOR
    if _SUPERVISOR is None:
        _SUPERVISOR = TaskSupervisor()
    return _SUPERVISOR


def reset_supervisor() -> None:
    """Para tests: cada uno con su supervisor limpio."""
    global _SUPERVISOR
    _SUPERVISOR = None


@contextlib.asynccontextmanager
async def tracked(proc: Any, task_id: str | None = None):
    """
    Inscribe un subproceso mientras dura, y lo da de baja al terminar.

    Existe porque la mitad de los subprocesos del sistema quedaban FUERA del
    alcance de la parada: solo `run_command` y la auto-ejecución se
    inscribían. Se quedaban fuera el verificador —que ejecuta código generado
    por el LLM en cada ronda del debate—, ffmpeg (hasta diez minutos de
    render), el arnés de pygame, `git clone` y `SYS_EXEC_HOST`.

    Pulsar parar durante un render decía "no había nada en marcha" mientras
    ffmpeg seguía quemando CPU.

    `task_id=None` cae en el cajón `_sin_tarea`, que `cancel_all()` también
    barre: puede que no se sepa de qué tarea es un proceso, pero eso no es
    motivo para que la parada de emergencia no lo alcance.

    Repetir try/finally en seis sitios es como se olvida en el séptimo.
    """
    supervisor().register_process(task_id, proc)
    try:
        yield proc
    finally:
        supervisor().forget_process(task_id, proc)
