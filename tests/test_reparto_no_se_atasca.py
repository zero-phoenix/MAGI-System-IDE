"""
Un cliente muerto no puede dejar muda a la interfaz entera.

LOS 7,9 SEGUNDOS, MEDIDOS
=========================
2026-08-23, sonda externa contra la aplicación del usuario, por el mismo
socket que usa la interfaz:

    [ 6,1 s]  RPC {'status': 'ok'}         <- el kernel ya publicó
    [14,0 s]  naoko.user_message           <- el bus lo entrega 7,9 s después
    [16,7 s]  naoko.log [USER] hola naoko  <- el eco, 10,6 s tarde

El usuario escribió «hola naoko», no vio nada en diez segundos y concluyó que
su mensaje no se había registrado. Con Ritsuko, en el mismo sistema y unos
segundos más tarde, el eco fue instantáneo.

LA CAUSA
========
`ws_server` se suscribe a `"*"`: cada evento del sistema pasa por una única
cola con un único worker que espera a que el handler termine. Y el handler
hacía `await asyncio.gather(*[client.send(...)])` con un `send` SIN tiempo
límite. Un socket medio abierto —lo normal cuando el webview se recarga y deja
la conexión anterior colgando— no lanza `ConnectionClosed`: se queda esperando.
Y con un solo worker, eso deja sin eventos a TODOS los clientes, para siempre,
mientras el kernel sigue contestando por RPC como si nada.
"""
from __future__ import annotations

import asyncio
import time

import pytest

from magi.core.bus import BusEvent, MagiBus
from magi.core.rpc.ws_server import WSServer


class ClienteColgado:
    """Un socket medio abierto: acepta el send y no vuelve nunca."""

    def __init__(self):
        self.recibidos = 0

    async def send(self, mensaje: str):
        await asyncio.sleep(3600)


class ClienteSano:
    def __init__(self):
        self.recibidos: list[str] = []

    async def send(self, mensaje: str):
        self.recibidos.append(mensaje)


def _servidor() -> WSServer:
    s = WSServer.__new__(WSServer)
    s.bus = MagiBus()
    s.clients = set()
    s.handlers = {}
    return s


@pytest.mark.asyncio
async def test_un_cliente_colgado_no_para_a_los_demas():
    srv = _servidor()
    colgado, sano = ClienteColgado(), ClienteSano()
    srv.clients.update({colgado, sano})

    t0 = time.monotonic()
    await srv._handle_bus_event(
        BusEvent(topic="naoko.log", payload={"agent": "NAOKO", "content": "hola"}))
    gastado = time.monotonic() - t0

    assert sano.recibidos, "el cliente sano tiene que recibir el evento"
    assert gastado < srv._TECHO_ENVIO_S + 1.5, (
        f"el reparto tardó {gastado:.1f}s: un cliente colgado lo está frenando")


@pytest.mark.asyncio
async def test_el_cliente_colgado_se_descarta():
    """
    Que no bloquee UNA vez no basta: si se queda en la lista, cada evento
    siguiente vuelve a pagar el tiempo límite. Dos segundos por evento, con
    cientos de eventos, es la misma parálisis un poco más lenta.
    """
    srv = _servidor()
    colgado, sano = ClienteColgado(), ClienteSano()
    srv.clients.update({colgado, sano})

    await srv._handle_bus_event(BusEvent(topic="naoko.log", payload={}))

    assert colgado not in srv.clients, "un cliente que no traga debe salir"
    assert sano in srv.clients, "el sano se queda"


@pytest.mark.asyncio
async def test_el_reparto_normal_es_inmediato():
    """El arreglo no puede costarle nada al caso bueno, que es el habitual."""
    srv = _servidor()
    sanos = [ClienteSano() for _ in range(5)]
    srv.clients.update(sanos)

    t0 = time.monotonic()
    for i in range(50):
        await srv._handle_bus_event(
            BusEvent(topic="AGENT_POST", payload={"content": f"m{i}"}))
    gastado = time.monotonic() - t0

    assert all(len(c.recibidos) == 50 for c in sanos)
    assert gastado < 1.0, f"50 eventos a 5 clientes costaron {gastado:.2f}s"


# --------------------------------------------------------------- prioridad


def test_el_ruido_no_desaloja_lo_que_importa():
    """
    Cuando la cola se llena, «el más viejo» era una política ciega.

    La cola de la interfaz se llena de `TERMINAL_OUT` —cada línea de log de
    cada proveedor; con cobertura x3 son cientos en segundos—. Al llenarse, lo
    primero que salía era lo más antiguo, que podía ser la respuesta de Naoko
    esperando turno detrás de trescientas líneas de registro.
    """
    bus = MagiBus()
    q: asyncio.Queue = asyncio.Queue(maxsize=2)
    importante = BusEvent(topic="naoko.log",
                          payload={"agent": "NAOKO", "content": "la respuesta"})
    q.put_nowait(importante)
    q.put_nowait(BusEvent(topic="AGENT_POST", payload={}))

    # Llega ruido con la cola llena: el ruido se queda fuera.
    bus._descartar_el_mas_viejo(
        q, BusEvent(topic="TERMINAL_OUT", payload={"content": "[INFO] ..."}))

    assert q.qsize() == 2
    assert q.get_nowait() is importante, (
        "la respuesta de Naoko no puede caerse por una línea de log")


def test_lo_importante_si_desaloja_cuando_no_cabe():
    """
    La otra mitad: si lo que entra es importante y no cabe, entra igual.
    Un bus que se niega a aceptar lo importante cuando va lleno es tan malo
    como uno que lo tira.
    """
    bus = MagiBus()
    q: asyncio.Queue = asyncio.Queue(maxsize=1)
    q.put_nowait(BusEvent(topic="TERMINAL_OUT", payload={"content": "viejo"}))

    nuevo = BusEvent(topic="naoko.log", payload={"content": "importante"})
    bus._descartar_el_mas_viejo(q, nuevo)

    assert q.qsize() == 1
    assert q.get_nowait() is nuevo
