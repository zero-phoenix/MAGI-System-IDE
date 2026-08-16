"""
El bus entrega. Siempre. Sea el evento crítico o no, haya sink o no.

EL FALLO QUE ESTO IMPIDE QUE VUELVA
===================================
Al añadir la persistencia de eventos críticos, el método nuevo se insertó
dentro de `publish` y el bucle de broadcast —lo único que hace que un bus sea
un bus— quedó colgando del método nuevo en vez de quedarse donde estaba:

    async def publish(self, event):
        if event.critical and self._critical_sink is not None:
            asyncio.create_task(self._persist_critical(event))

    async def _persist_critical(self, event):
        try:
            await self._critical_sink(event)
        except Exception as e:
            logger.debug(...)

        for glob, queues in self.subscribers.items():   # <-- aquí abajo
            ...

El resultado: `publish()` dejaba de entregar nada a nadie. Los suscriptores
solo recibían eventos de rebote, cuando el evento era `critical=True` Y había
un sink enganchado. Sin sink —tests, y cualquier momento anterior a
`Kernel.start()`— el sistema entero se quedaba mudo: sin interfaz, sin Naoko,
sin telemetría, sin enjambre. Todo por un nivel de indentación.

Lo peligroso no fue el error, sino su forma: no lanza excepción, no escribe en
el log, no rompe ningún import. Un sistema que ya no hace nada tiene el mismo
aspecto que uno inactivo.

Los tres casos de abajo cubren las tres combinaciones que la regresión
distinguía. Un test solo sobre eventos críticos con sink habría pasado.
"""
import asyncio

import pytest

from magi.core.bus import BusEvent, MagiBus


async def _bus_con_suscriptor(topic: str = "x"):
    """Bus con un handler enganchado y la lista donde deja lo que recibe."""
    bus = MagiBus()
    recibido: list = []

    async def handler(event):
        recibido.append(event.payload)

    bus.subscribe(topic, handler)
    return bus, recibido


@pytest.mark.asyncio
async def test_entrega_evento_normal_sin_sink():
    """El caso corriente: evento no crítico, nadie ha enganchado persistencia."""
    bus, recibido = await _bus_con_suscriptor()
    await bus.publish(BusEvent(topic="x", payload={"n": 1}))
    await asyncio.sleep(0.05)
    assert recibido == [{"n": 1}], (
        "publish() debe entregar a los suscriptores SIEMPRE. Si esto falla, el "
        "bucle de broadcast se ha salido de publish otra vez.")
    await bus.shutdown()


@pytest.mark.asyncio
async def test_entrega_evento_critico_aunque_no_haya_sink():
    """
    `critical=True` sin sink era el agujero exacto de la regresión.

    Es además el estado real del sistema entre que se construye el Kernel y
    `Kernel.start()` engancha el sink: cualquier evento crítico de ese tramo
    —incluido el arranque— se perdía entero.
    """
    bus, recibido = await _bus_con_suscriptor()
    assert bus._critical_sink is None, "el bus nace sin sink; ese es el caso"
    await bus.publish(BusEvent(topic="x", payload={"n": 2}, critical=True))
    await asyncio.sleep(0.05)
    assert recibido == [{"n": 2}], (
        "un evento crítico sin sink debe entregarse igual: la persistencia es "
        "un extra, no un requisito para que el bus funcione.")
    await bus.shutdown()


@pytest.mark.asyncio
async def test_entrega_evento_critico_con_sink_y_ademas_persiste():
    """Con sink enganchado: se entrega Y se persiste. No una cosa o la otra."""
    bus, recibido = await _bus_con_suscriptor()
    persistido: list = []

    async def sink(event):
        persistido.append(event.topic)

    bus.attach_critical_sink(sink)
    await bus.publish(BusEvent(topic="x", payload={"n": 3}, critical=True))
    await asyncio.sleep(0.05)
    assert recibido == [{"n": 3}], "el broadcast no puede depender del sink"
    assert persistido == ["x"], "el sink crítico debe recibir el evento"
    await bus.shutdown()


@pytest.mark.asyncio
async def test_un_sink_que_revienta_no_impide_la_entrega():
    """
    El sink es un extra y se comporta como tal: si falla, se traga el fallo.

    Persistir en SQLite puede fallar por disco lleno, bloqueo o permisos. Que
    eso deje al usuario sin interfaz sería cambiar un problema de diagnóstico
    por una caída.
    """
    bus, recibido = await _bus_con_suscriptor()

    async def sink_roto(event):
        raise RuntimeError("disco lleno")

    bus.attach_critical_sink(sink_roto)
    await bus.publish(BusEvent(topic="x", payload={"n": 4}, critical=True))
    await asyncio.sleep(0.05)
    assert recibido == [{"n": 4}], (
        "un sink que revienta no puede llevarse por delante el broadcast")
    await bus.shutdown()


@pytest.mark.asyncio
async def test_la_tarea_de_persistencia_tiene_dueño():
    """
    La tarea del sink se guarda en `_sink_tasks` mientras está en vuelo.

    No es contabilidad decorativa: el bucle de eventos solo mantiene una
    referencia DÉBIL a las tareas, así que una tarea sin dueño puede ser
    recolectada por el GC a mitad de ejecución. El evento crítico se perdería
    en silencio, que es justo lo que la persistencia venía a evitar — y es un
    fallo que no se reproduce a voluntad, así que se comprueba la estructura.
    """
    bus, _ = await _bus_con_suscriptor()
    visto_en_vuelo = asyncio.Event()
    puede_terminar = asyncio.Event()

    async def sink_lento(event):
        visto_en_vuelo.set()
        # Sin sleeps a ciegas: bajo carga de CPU (pytest-xdist) el sink podía
        # terminar antes de que el assert de arriba lo mirara. El test decide
        # cuándo termina el sink, no el reloj.
        await puede_terminar.wait()

    bus.attach_critical_sink(sink_lento)
    await bus.publish(BusEvent(topic="x", payload={"n": 5}, critical=True))
    await visto_en_vuelo.wait()
    assert bus._sink_tasks, "la tarea en vuelo debe tener una referencia viva"

    puede_terminar.set()
    await asyncio.sleep(0.1)
    assert not bus._sink_tasks, (
        "y debe soltarse al terminar: si no, el conjunto crece sin límite "
        "durante toda la sesión")
    await bus.shutdown()
