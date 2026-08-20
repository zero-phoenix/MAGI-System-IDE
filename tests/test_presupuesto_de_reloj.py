"""
El failover no puede multiplicar el tiempo de espera del usuario.

LO QUE MEDÍ, Y POR QUÉ IMPORTA
==============================
`token_ledger` de este equipo el 2026-08-20, latencia REAL por llamada lógica:

    CASPER   / gemini   n=10   mediana  44 726 ms   p90 390 391 ms
    MELCHIOR / gemini   n=35   mediana  25 000 ms   p90 172 297 ms
    MELCHIOR / gpt      n=33   mediana  50 906 ms   p90  84 359 ms

390 segundos. Seis minutos y medio esperando una sola respuesta, sin que la
interfaz dijera nada. El usuario lo describió como «el sistema demora tanto en
funcionar» y «le escribí a Naoko y no me responde» — y tenía razón las dos
veces.

La causa: `registry.complete` prueba hasta `max_attempts` candidatos y cada uno
estrenaba su propio `timeout_s`. Con el valor por defecto de 150 s, el techo de
pared de UNA llamada lógica era 3 × 150 = 450 s. Nadie lo acotaba porque nadie
lo miraba a nivel de cadena: cada intento, por separado, se portaba bien.

El arreglo (§E1) es un presupuesto de reloj para la cadena entera. Cada intento
recibe lo que QUEDA, y cuando no queda nada la cadena se rinde en vez de abrir
otro turno de 150 s. El valor por defecto es igual a `timeout_s`, así que
ningún candidato dispone de menos tiempo que antes: lo único que desaparece es
la multiplicación.
"""
from __future__ import annotations

import asyncio
import time

import pytest

from magi.core.providers.base import (
    CompletionRequest,
    CompletionResponse,
    Message,
    ProviderError,
    Usage,
)


class ProveedorLento:
    """Nunca contesta. Es el candidato que se comía los 150 s."""

    def __init__(self, pid: str):
        self.id = pid
        self.family = "lenta"
        self.llamado_durante: list[float] = []

    async def complete(self, req):
        t0 = time.monotonic()
        try:
            await asyncio.sleep(3600)
        finally:
            self.llamado_durante.append(time.monotonic() - t0)
        raise AssertionError("no debería llegar aquí")


class ProveedorRapido:
    def __init__(self, pid: str):
        self.id = pid
        self.family = "rapida"

    async def complete(self, req):
        await asyncio.sleep(0.01)
        return CompletionResponse(content="listo", provider_id=self.id,
                                  model="m", family=self.family,
                                  usage=Usage(1, 1), latency_ms=10.0)


def _registro(reg_cls, proveedores):
    """Un ProviderRegistry con los candidatos que se le den, sin red."""
    r = reg_cls.__new__(reg_cls)
    from magi.core.providers.cache import TTLCache
    from magi.core.providers.circuit import CircuitBreaker

    class Entrada:
        def __init__(self, p):
            self.id = p.id
            self.provider = p
            self.breaker = CircuitBreaker()
            self.available = True
            self.calls = 0
            self.tokens_in = 0
            self.tokens_out = 0

    r._entradas = [Entrada(p) for p in proveedores]
    r.cache = TTLCache()
    r.metrics = None
    r._candidates = lambda *a, **kw: r._entradas
    return r


@pytest.fixture()
def Registro():
    from magi.core.providers.registry import ProviderRegistry
    return ProviderRegistry


@pytest.mark.asyncio
async def test_la_cadena_entera_respeta_el_presupuesto(Registro):
    """
    Tres candidatos colgados, presupuesto de 1,5 s.

    Sin §E1 esto tardaba `3 × timeout_s`. Con él, tarda el presupuesto.
    """
    lentos = [ProveedorLento(f"lento-{i}") for i in range(3)]
    reg = _registro(Registro, lentos)

    req = CompletionRequest(messages=[Message("user", "hola")],
                            timeout_s=60.0, presupuesto_s=1.5)

    t0 = time.monotonic()
    with pytest.raises(ProviderError):
        await reg.complete(req, use_cache=False)
    gastado = time.monotonic() - t0

    # Holgura generosa: lo que se comprueba es que NO se pagó 3 × 60 s.
    assert gastado < 4.0, f"la cadena gastó {gastado:.1f}s con 1,5s de techo"


@pytest.mark.asyncio
async def test_sin_presupuesto_se_comporta_como_antes(Registro):
    """
    El presupuesto es opcional y su ausencia no cambia nada: `presupuesto_s`
    por defecto es None. Una regresión aquí rompería a todo el que construya
    su propia `CompletionRequest`.
    """
    reg = _registro(Registro, [ProveedorLento("lento"), ProveedorRapido("rapido")])

    req = CompletionRequest(messages=[Message("user", "hola")], timeout_s=0.2)
    assert req.presupuesto_s is None

    resp = await reg.complete(req, use_cache=False)
    assert resp.provider_id == "rapido"


@pytest.mark.asyncio
async def test_el_candidato_bueno_no_pierde_su_turno(Registro):
    """
    La parte que hace el arreglo seguro.

    Un presupuesto mal puesto que corte al segundo candidato convierte una
    mejora de latencia en pérdida de respuestas. Con presupuesto de sobra, el
    lento se agota por su propio techo y el rápido contesta igual que siempre.
    """
    reg = _registro(Registro, [ProveedorLento("lento"), ProveedorRapido("rapido")])

    req = CompletionRequest(messages=[Message("user", "hola")],
                            timeout_s=0.3, presupuesto_s=10.0)

    resp = await reg.complete(req, use_cache=False)
    assert resp.provider_id == "rapido"
    assert resp.content == "listo"


@pytest.mark.asyncio
async def test_la_sonda_no_lleva_presupuesto(Registro):
    """
    Medir no es producir. El tiempo de una sonda ES el dato que se busca;
    recortarlo devolvería una medición falsa de lo rápido que va el sistema.
    """
    lento = ProveedorLento("lento")
    reg = _registro(Registro, [lento, ProveedorRapido("rapido")])

    req = CompletionRequest(messages=[Message("user", "ping")],
                            timeout_s=0.2, presupuesto_s=0.05, probe=True)

    resp = await reg.complete(req, use_cache=False)
    # Con presupuesto de 0,05 s el lento ni se habría intentado; como es
    # sonda, se le da su techo completo y luego pasa el turno al rápido.
    assert resp.provider_id == "rapido"
    assert lento.llamado_durante, "la sonda debe llegar a probar al lento"


def test_la_capa_de_compatibilidad_pone_el_presupuesto():
    """
    Que el mecanismo exista no basta: quien construye las peticiones reales es
    `FreeCloudLLM.generate_text`, y si no lo rellena, el techo sigue siendo
    3 × 150 s en producción aunque los tests de arriba pasen.
    """
    import pathlib

    fuente = (pathlib.Path(__file__).resolve().parents[1] / "magi" / "core"
              / "providers" / "cloud.py").read_text(encoding="utf-8")
    assert "presupuesto_s=150.0" in fuente, (
        "generate_text debe fijar el presupuesto de cadena")
    assert "presupuesto_s=45.0" in fuente, (
        "el reintento por negativa debe llevar presupuesto corto: ya hay una "
        "respuesta en la mano y no puede costar lo mismo que conseguirla")
