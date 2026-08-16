"""
Test de humo de TODOS los handlers RPC, y del bus que no debe bloquear.

POR QUÉ EXISTE
==============
Se añadió el handler `sys.config` con su panel, sus tests de la lógica y su
componente de interfaz... y nadie lo invocó nunca de extremo a extremo. Dentro
hacía:

    from magi.core.tools import ALL_DOMAINS

y `ALL_DOMAINS` no estaba reexportado en `magi/core/tools/__init__.py`. El
handler lanzaba ImportError en CADA llamada.

Y de ahí, un fallo tonto tumbó la aplicación entera:

    ImportError -> log ERROR -> evento error.critical -> Naoko diagnostica con
    inferencia -> su cola se llena -> el bus BLOQUEA al productor -> el
    productor era el logging -> se para todo.

El usuario escribió «crea un documento de word en mi escritorio» y no ocurrió
nada, porque ya no quedaba nadie libre para atenderle.

La lección no es «acuérdate de exportar el nombre». Es que un handler que
nadie invoca en los tests es un handler que no existe hasta que un usuario lo
pulsa. Este fichero recorre el registro de handlers REAL: cuando se añada el
siguiente, entra solo.
"""
from __future__ import annotations

import asyncio
import logging

import pytest

from magi.core.bus import BusEvent, MagiBus

# ============================================ todos los handlers arrancan

def _kernel_handlers() -> dict:
    """
    Los handlers que el kernel registra DE VERDAD, leídos del registro.

    Se construye el kernel con dependencias mínimas; lo que importa aquí no es
    que hagan su trabajo, sino que se puedan invocar sin reventar al importar.
    """
    from magi.core.blackboard import Blackboard
    from magi.core.kernel import Kernel

    bus = MagiBus()
    try:
        k = Kernel(bus=bus, blackboard=Blackboard())
    except TypeError:
        k = Kernel(bus)
    return k, dict(k.rpc.handlers)


def test_el_kernel_registra_handlers():
    _, handlers = _kernel_handlers()
    assert handlers, "el kernel no registró ningún handler RPC"
    # Los que la interfaz necesita para pintar sus pestañas.
    for imprescindible in ("sys.config", "artifacts.list", "obs.metrics"):
        assert imprescindible in handlers, f"falta el handler {imprescindible}"


@pytest.mark.asyncio
async def test_ningun_handler_falla_por_un_import():
    """
    Se invoca CADA handler registrado y se exige que no muera por un
    ImportError, AttributeError o NameError: los tres fallos que significan
    «este código nunca se ejecutó».

    Un fallo de lógica o de red es aceptable aquí (no hay proveedores ni
    ficheros); un fallo de importación no, porque significa que el handler
    está roto para siempre y nadie lo sabía.
    """
    _, handlers = _kernel_handlers()
    rotos: list[str] = []

    for nombre, fn in handlers.items():
        try:
            await asyncio.wait_for(fn({}, None), timeout=25)
        except (ImportError, AttributeError, NameError) as e:
            rotos.append(f"{nombre}: {type(e).__name__}: {e}")
        except Exception:
            pass          # lógica, red o falta de datos: no es lo que se mide

    assert not rotos, ("estos handlers están rotos de raíz y la interfaz los "
                       "llama: " + " | ".join(rotos))


@pytest.mark.asyncio
async def test_sys_config_devuelve_lo_que_la_interfaz_pinta():
    """
    El contrato concreto del panel de Configuración. Si cambia una clave, la
    pestaña se queda a medias sin que nada avise.
    """
    _, handlers = _kernel_handlers()
    cfg = await asyncio.wait_for(handlers["sys.config"]({}, None), timeout=30)

    for clave in ("enjambre", "familias", "inferencia", "herramientas",
                  "dominios", "rutas", "cortafuegos"):
        assert clave in cfg, f"sys.config ya no devuelve '{clave}'"
    assert "reparto" in cfg["enjambre"] and "diversidad" in cfg["enjambre"]
    assert isinstance(cfg["familias"], list) and cfg["familias"]
    assert {"MELCHIOR", "BALTHASAR", "CASPER"} <= set(cfg["herramientas"])


def test_all_domains_se_puede_importar_del_paquete():
    """El import exacto que hacía el kernel y que lanzaba ImportError."""
    from magi.core.tools import ALL_DOMAINS, registry_for_role  # noqa: F401
    assert ALL_DOMAINS and "core" in ALL_DOMAINS


def test_lo_que_el_paquete_promete_existe():
    """
    `__all__` no puede prometer nombres que no están. Es la comprobación
    genérica del fallo concreto: alguien importa del paquete y no está.
    """
    import magi.core.tools as t
    faltan = [n for n in t.__all__ if not hasattr(t, n)]
    assert not faltan, f"__all__ promete nombres inexistentes: {faltan}"


# ==================================================== el bus no bloquea

@pytest.mark.asyncio
async def test_el_bus_no_bloquea_al_productor_con_la_cola_llena():
    """
    LA REGRESIÓN QUE CONGELÓ EL SISTEMA.

    `publish` hacía `await q.put(event)` cuando la cola estaba llena. Con un
    consumidor lento —Naoko diagnosticando con inferencia real— eso bloqueaba
    a quien publicaba, que era el propio logging. Todo se paraba.
    """
    bus = MagiBus()

    async def consumidor_lento(_e):
        await asyncio.sleep(3600)      # no consume nunca

    # Cola pequeña a propósito: el punto es qué pasa AL LLENARSE, no cuánto
    # cabe. Con la de por defecto (1024) harían falta miles de eventos para
    # provocar lo mismo y el test tardaría en balde.
    bus.subscribe("error.critical", consumidor_lento, maxsize=8)
    bus.start_pending_workers()

    await asyncio.wait_for(
        asyncio.gather(*(bus.publish(BusEvent(topic="error.critical",
                                              payload={"n": i}))
                         for i in range(200))),
        timeout=10)          # antes: se colgaba aquí para siempre

    assert bus.dropped_report().get("error.critical", 0) > 0, \
        "con la cola llena hay que descartar, no esperar"


@pytest.mark.asyncio
async def test_publicar_sin_nadie_escuchando_no_revienta():
    bus = MagiBus()
    await asyncio.wait_for(
        bus.publish(BusEvent(topic="nadie.escucha", payload={})), timeout=5)


# ============================================ el log no se realimenta

class _BusEspia(MagiBus):
    """Anota los tópicos publicados en vez de repartirlos."""

    def __init__(self, eco: bool = False):
        super().__init__()
        self.topicos: list[str] = []
        self._eco = eco

    async def publish(self, event):            # type: ignore[override]
        self.topicos.append(event.topic)
        if self._eco:
            # Publicar genera un log, igual que hace el bus real al descartar.
            logging.getLogger("magi.core.bus").warning("cola llena")


async def _emitir(logger_name: str, nivel: int, mensaje: str, veces: int = 1,
                  eco: bool = False):
    """
    Emite registros con el handler puesto, DENTRO de un bucle en marcha.

    El bucle importa: `BusLogHandler` publica con `asyncio.create_task`, que
    necesita un bucle corriendo. Sin él no publica nada y el test mediría el
    vacío en vez de la conducta.
    """
    from magi.core.obs.bus_log_handler import BusLogHandler

    bus = _BusEspia(eco=eco)
    h = BusLogHandler(bus)
    log = logging.getLogger(logger_name)
    log.addHandler(h)
    try:
        for _ in range(veces):
            log.log(nivel, mensaje)
        await asyncio.sleep(0.05)      # que corran las tareas creadas
    finally:
        log.removeHandler(h)
    return bus, h


@pytest.mark.asyncio
async def test_el_handler_de_log_no_reentra():
    """
    El aviso de «cola llena» era un WARNING, y ese WARNING volvía a pasar por
    el handler generando otro evento. El sistema se ahogaba con sus propios
    mensajes de que se estaba ahogando: cientos de líneas idénticas.
    """
    bus, _ = await _emitir("prueba.reentrada", logging.ERROR, "algo falló",
                           eco=True)
    assert len(bus.topicos) <= 2, \
        f"el handler se realimentó: {len(bus.topicos)} publicaciones"


@pytest.mark.asyncio
async def test_el_handler_de_log_no_repite_el_mismo_error():
    """Doscientas copias del mismo ImportError no informan más que una."""
    _, h = await _emitir("prueba.repetidos", logging.ERROR,
                         "cannot import name 'ALL_DOMAINS'", veces=200)
    assert h.suprimidos >= 190, \
        f"solo se suprimieron {h.suprimidos} de 200 repeticiones"


@pytest.mark.asyncio
async def test_un_panel_roto_no_es_una_emergencia_del_sistema():
    """
    Que falle un handler RPC degrada un panel; no es una avería que merezca
    gastar inferencia del enjambre en diagnosticarla. Antes, cada uno de esos
    errores despertaba a Naoko.
    """
    bus, _ = await _emitir("magi.core.rpc.ws_server", logging.ERROR,
                           "el handler 'sys.config' falló")
    assert "error.critical" not in bus.topicos, \
        "un handler RPC roto no debe despertar el diagnóstico del enjambre"
    assert "TERMINAL_OUT" in bus.topicos, "pero sí debe verse en la terminal"


@pytest.mark.asyncio
async def test_un_fallo_de_verdad_SI_despierta_a_naoko():
    """
    Contraprueba: filtrar de más sería peor que no filtrar. Un error del
    núcleo tiene que seguir llegando al diagnóstico.
    """
    bus, _ = await _emitir("magi.modules.swarm.orchestrator", logging.ERROR,
                           "error catastrófico durante la orquestación")
    assert "error.critical" in bus.topicos
