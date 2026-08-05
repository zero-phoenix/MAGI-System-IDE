"""
Transporte RPC: que un fallo no deje sin kernel a la interfaz (§7.3).

DOS FALLOS, LOS DOS REPRODUCIDOS ANTES DE TOCAR NADA
====================================================
`_process_rpc` solo capturaba `json.JSONDecodeError`. Cualquier excepción de
un handler subía hasta el `async for message in websocket`, que solo captura
`ConnectionClosed`, y cerraba el canal:

    handler que lanza      -> CONEXIÓN CERRADA (1011)
    conexión tras el fallo -> MUERTA

Y `if result is not None` no respondía a los handlers que devuelven None: el
cliente esperaba una respuesta que no llegaba nunca. Con el helper `rpc()` de
la interfaz eso son 180 segundos de panel girando.

Apareció al auditar el panel de Sistema: `naoko.self_improve` corre un banco
completo contra proveedores gratuitos, así que es de los que más fácil
lanzan. Una excepción ahí dejaba al usuario sin conexión y sin explicación.
"""
import asyncio
import contextlib
import itertools
import json

import pytest
import websockets

from magi.core.bus import MagiBus
from magi.core.rpc.ws_server import WSServer

# Un puerto distinto por test. Compartir uno con un fixture de módulo choca
# con pytest-asyncio: el bucle de eventos es por función, así que un servidor
# creado en un fixture de módulo queda atado a un bucle muerto y el cliente se
# queda esperando el handshake.
_PUERTO = itertools.count(8880)


@contextlib.asynccontextmanager
async def servidor_rpc():
    s = WSServer(bus=MagiBus(), host="127.0.0.1", port=next(_PUERTO))

    async def revienta(payload, ws):
        raise ValueError("fallo del handler")

    async def devuelve_none(payload, ws):
        return None

    async def eco(payload, ws):
        return {"visto": payload}

    s.register_handler("revienta", revienta)
    s.register_handler("nada", devuelve_none)
    s.register_handler("eco", eco)
    await s.start()
    await asyncio.sleep(0.25)
    async with websockets.connect(f"ws://127.0.0.1:{s.port}") as ws:
        yield s, ws


async def _pedir(ws, mensaje, timeout=3):
    await ws.send(mensaje if isinstance(mensaje, str) else json.dumps(mensaje))
    return json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))


@pytest.mark.asyncio
async def test_un_handler_que_lanza_no_mata_la_conexion():
    """
    EL FALLO GRAVE. Basta con que un handler falle UNA vez para que la
    interfaz se quede sin kernel, y da igual lo defensivo que sea el resto.
    """
    async with servidor_rpc() as (servidor, ws):
        r = await _pedir(ws, {"type": "revienta", "id": "b"})
        assert r["ok"] is False
        assert "ValueError" in r["error"]

        # Lo que de verdad importa: la conexión sigue sirviendo.
        r2 = await _pedir(ws, {"type": "eco", "id": "c", "payload": {"x": 1}})
        assert r2["ok"] is True


@pytest.mark.asyncio
async def test_siempre_hay_respuesta_aunque_el_handler_devuelva_none():
    """
    Sin respuesta, la promesa del cliente cuelga hasta el tiempo límite y el
    usuario no distingue "tarda" de "no funciona".
    """
    async with servidor_rpc() as (servidor, ws):
        r = await _pedir(ws, {"type": "nada", "id": "a"})
        assert r == {"id": "a", "ok": True, "result": None}


@pytest.mark.asyncio
async def test_json_invalido_responde_y_no_cierra():
    async with servidor_rpc() as (servidor, ws):
        r = await _pedir(ws, "{no soy json")
        assert r["ok"] is False and "JSON" in r["error"]
        assert (await _pedir(ws, {"type": "nada", "id": "z"}))["ok"] is True


@pytest.mark.asyncio
async def test_metodo_desconocido_conserva_el_id():
    """
    Si la respuesta no lleva el id de la petición, el cliente no sabe a cuál
    corresponde y la promesa se queda esperando igual.
    """
    async with servidor_rpc() as (servidor, ws):
        r = await _pedir(ws, {"type": "inventado", "id": "d"})
        assert r["id"] == "d" and r["ok"] is False


@pytest.mark.asyncio
async def test_un_resultado_no_serializable_no_tumba_el_canal():
    """
    `json.dumps` sobre un objeto raro lanza TypeError DENTRO del envío. Sin
    `default=str` eso volvía a matar la conexión por otra vía.
    """
    class Raro:
        pass

    async def raro(payload, ws):
        return {"objeto": Raro()}

    async with servidor_rpc() as (servidor, ws):
        servidor.register_handler("raro", raro)
        r = await _pedir(ws, {"type": "raro", "id": "r"})
        assert r["ok"] is True
        assert (await _pedir(ws, {"type": "nada", "id": "s"}))["ok"] is True


def test_el_despacho_no_deja_escapar_excepciones():
    """Guarda estructural: el bloque que llama al handler tiene que atraparlas."""
    import inspect

    src = inspect.getsource(WSServer._process_rpc)
    assert "except Exception" in src, \
        "una excepción de handler volvería a cerrar la conexión"
    assert "except asyncio.CancelledError" in src, \
        "atrapar todo sin dejar pasar CancelledError impediría parar el servidor"
