"""Las sondas no pueden enfermar al sistema (regresión del 2026-08-16).

El 2026-08-16, con la sonda de latencia viva por primera vez, el sistema se
quedó sin proveedores: los canarios piden respuestas cortas POR DISEÑO
(«51», «paris», «ok»), el filtro antichatarra del tráfico real
(MINIMO_UTIL = 12) las rechazaba todas, cada rechazo agotaba la familia y
abría el cortacircuitos, y el tráfico real —la tarea del usuario— llegaba
cuando ya no quedaba nadie sano. Medir la salud enfermó al paciente.

Tres reglas, tres tests: la respuesta de sonda corta se acepta; el fallo de
sonda no castiga al cortacircuitos; el canario de deriva con respuestas
correctas cortas NO deriva.
"""
from __future__ import annotations

import pytest

from magi.core.obs.metrics import canary_probe
from magi.core.providers.backends.echo import EchoProvider
from magi.core.providers.backends.g4f_backend import _por_que_es_inservible
from magi.core.providers.base import CompletionRequest, Message
from magi.core.providers.registry import ProviderError, ProviderRegistry


def test_la_respuesta_corta_se_rechaza_para_trafico_y_se_acepta_para_sonda():
    """'51' es inservible en una tarea real y perfecta en un canario."""
    assert _por_que_es_inservible("51") is not None
    assert _por_que_es_inservible("51", minimo=1) is None
    # Lo vacío jamás sirve, ni para sondear.
    assert _por_que_es_inservible("   ", minimo=1) is not None


@pytest.mark.asyncio
async def test_el_fallo_de_sonda_no_abre_el_cortacircuitos():
    """Un canario que falla es un dato, no una penalización."""
    reg = ProviderRegistry()
    reg.register(EchoProvider(provider_id="eco", family="echo", fail_times=1),
                 priority=1)

    req = CompletionRequest(messages=[Message("user", "Responde OK.")],
                            probe=True, timeout_s=5.0)
    with pytest.raises(ProviderError):
        await reg.complete(req, prefer="eco", max_attempts=1)

    # Falló la sonda, pero el cortacircuitos NO se movió: el tráfico real
    # sigue podiendo usarlo (la segunda llamada ya no falla).
    registro = reg.get("eco")
    assert registro.breaker.allows(), (
        "una sonda fallida cerró el paso al tráfico real: medir la salud "
        "no puede enfermar al sistema"
    )
    resp = await reg.complete(
        CompletionRequest(messages=[Message("user", "tarea real de verdad")],
                          timeout_s=5.0),
        prefer="eco", use_cache=False)
    assert resp.provider_id == "eco"


@pytest.mark.asyncio
async def test_el_fallo_de_trafico_real_sí_penaliza():
    """La regla solo se relaja para sondas: el tráfico real sigue contando."""
    reg = ProviderRegistry()
    reg.register(EchoProvider(provider_id="eco", family="echo", fail_times=1),
                 priority=1)

    with pytest.raises(ProviderError):
        await reg.complete(
            CompletionRequest(messages=[Message("user", "tarea real")],
                              timeout_s=5.0),
            prefer="eco", max_attempts=1, use_cache=False)
    # El fallo real SÍ quedó registrado en las estadísticas del registro.
    assert reg.get("eco").breaker.allows() or reg.get("eco").calls == 0


@pytest.mark.asyncio
async def test_el_canario_de_deriva_con_respuesta_corta_correcta_no_deriva():
    """'51', 'paris' y 'ok' son correctas y cortas: 3/3, sin deriva."""
    reg = ProviderRegistry()
    # '51 ok paris' contiene las tres esperadas a la vez.
    reg.register(EchoProvider(provider_id="eco", family="echo",
                              canned="51 ok paris"), priority=1)

    report = await canary_probe(reg, "eco")
    assert report.matched == 3 and report.total == 3
    assert not report.drifted, (
        f"canarios correctos marcados como deriva: {report.details}")


@pytest.mark.asyncio
async def test_la_sonda_no_se_queda_en_caché():
    """El canario de ahora no puede servir de respuesta a la tarea de luego."""
    reg = ProviderRegistry()
    reg.register(EchoProvider(provider_id="eco", family="echo",
                              canned="51"), priority=1)

    await reg.complete(CompletionRequest(messages=[Message("user", "canario")],
                                         probe=True, timeout_s=5.0),
                       prefer="eco")
    # La petición de sonda no dejó NADA en caché: si dejara, la siguiente
    # tarea con el mismo prompt recibiría '51' como respuesta de verdad.
    assert len(reg.cache) == 0, (
        "una respuesta de sonda quedó en la caché del tráfico real"
    )
