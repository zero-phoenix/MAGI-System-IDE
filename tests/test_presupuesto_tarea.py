"""
Presupuesto por tarea (v6.0 §A1): el freno que el log del 16-ago demostró
que faltaba.

POR QUÉ
=======
«crea un juego de tetris en un unico ejecutable exe portable» quemó ~50
llamadas HTTP para UNA petición: ~16 llamadas lógicas multiplicadas por el
hedge x3 global, y 6 ciclos ENTEROS de Melchior regenerando las 3 variantes
porque la verificación las rechazaba — sin tope y sin entrega. Estos tests
comprueban que una tarea nunca vuelve a hacer eso:

- se cierra sola al alcanzar el techo de llamadas (bloqueando la ronda
  siguiente), con evento `swarm.budget_exhausted` y motivo claro;
- los rebuilds por verificación fallida están acotados: tras el tope, la
  verificación deja de regenerar y el debate sigue con lo que haya;
- los contadores se persisten: una tarea rehidratada no reabre un presupuesto
  ya gastado.
"""
import asyncio

import pytest

from magi.core import presupuesto as pto
from magi.core.blackboard import Blackboard
from magi.core.bus import BusEvent, MagiBus
from magi.core.cancel import supervisor
from magi.core.providers.backends.echo import EchoProvider
from magi.core.providers.backends.g4f_backend import DEFAULT_SWARM_FAMILIES
from magi.core.providers.cloud import set_registry
from magi.core.providers.registry import ProviderRegistry
from magi.modules.swarm.orchestrator import SwarmOrchestrator


class FamilyEcho(EchoProvider):
    """Devuelve su familia en el cuerpo para poder rastrear quién respondió."""

    def _render(self, req):
        return f"[familia={self.family}] propuesta técnica. ### CONCLUSIÓN"


class EchoRechaza(EchoProvider):
    """La síntesis pide más trabajo: fuerza otra ronda de debate."""

    def _render(self, req):
        return ("propuesta razonable pero mejorable.\n\n"
                "### CONCLUSIÓN\nNecesita revisión.\n\n"
                "DECISIÓN: NECESITA REVISIÓN")


class EchoRota(EchoProvider):
    """Melchior propone SIEMPRE código que revienta al arrancar."""

    def _render(self, req):
        return ("Solución:\n\n```python\nraise RuntimeError('boom')\n```\n\n"
                "### CONCLUSIÓN\nPropuesta lista.")


def _registro_con(modo: str) -> ProviderRegistry:
    """Proveedores eco; `modo` elige qué guion interpretan los agentes."""
    casper_fam = DEFAULT_SWARM_FAMILIES.get("CASPER", "gpt")
    melchior_fam = DEFAULT_SWARM_FAMILIES.get("MELCHIOR", "hf")
    reg = ProviderRegistry()
    familias = list(dict.fromkeys(
        list(DEFAULT_SWARM_FAMILIES.values()) + ["llama", "hf", "auto"]))
    for fam in familias:
        if modo == "rechazo" and fam == casper_fam:
            reg.register(EchoRechaza(f"g4f-{fam}", fam), priority=10)
        elif modo == "rota" and fam == melchior_fam:
            reg.register(EchoRota(f"g4f-{fam}", fam), priority=10)
        else:
            reg.register(FamilyEcho(f"g4f-{fam}", fam), priority=10)
    return reg


@pytest.fixture
async def registro_rechazo():
    reg = _registro_con("rechazo")
    await reg.probe_all()
    set_registry(reg)
    yield
    set_registry(None)


@pytest.fixture
async def registro_rota():
    reg = _registro_con("rota")
    await reg.probe_all()
    set_registry(reg)
    yield
    set_registry(None)


@pytest.fixture
async def eventos():
    """Caja de eventos por tema: swarm.* y la salida del terminal."""
    bus = MagiBus()
    caja: dict[str, list[dict]] = {}

    async def captura(event: BusEvent):
        if isinstance(event.payload, dict):
            caja.setdefault(event.topic, []).append(event.payload)
        else:
            caja.setdefault(event.topic, []).append({"raw": event.payload})

    bus.subscribe("swarm.*", captura)
    bus.subscribe("TERMINAL_OUT", captura)
    yield bus, caja


async def esperar_evento(caja: dict, topico: str, veces: int = 1,
                         segundos: float = 20.0) -> bool:
    fin = asyncio.get_event_loop().time() + segundos
    while asyncio.get_event_loop().time() < fin:
        if len(caja.get(topico, [])) >= veces:
            return True
        await asyncio.sleep(0.05)
    return False


@pytest.mark.asyncio
async def test_la_tarea_se_cierra_al_agotar_llamadas(registro_rechazo, eventos):
    """
    Con un techo de 3 llamadas, la primera ronda (2 variantes + ejes +
    arbitraje) ya lo supera; la ronda siguiente NO arranca, se entrega lo
    debatido y el motivo es «llamadas». Antes, esta tarea habría seguido
    debatiendo rondas indefinidas; ahora se para y dice cuánto gastó.
    """
    bus, caja = eventos
    pto.activar({"fast": {"llamadas": 3, "pared_s": 120.0, "rebuilds": 1}})
    try:
        swarm = SwarmOrchestrator(Blackboard(), bus)
        await swarm.submit_task("t-techo", "mejora este módulo", engine="fast")

        assert await esperar_evento(caja, "swarm.budget_exhausted"), (
            "la tarea debía agotar su presupuesto y cerrarse sola")

        ev = caja["swarm.budget_exhausted"][0]
        assert ev["motivo"] == "llamadas"
        assert ev["techo_llamadas"] == 3
        assert ev["calls_used"] >= 3

        est = swarm.active_tasks["t-techo"]
        assert est["status"] == "completed"

        guardado = swarm.store.load("t-techo")
        assert int(guardado.calls_used) >= 3, (
            "los contadores deben persistirse: una tarea rehidratada no "
            "puede reabrir un presupuesto ya gastado")

        textos = " ".join(str(p.get("content", "")) for p in caja["TERMINAL_OUT"])
        assert "Presupuesto agotado (llamadas)" in textos
    finally:
        pto.activar({"fast": {"llamadas": 18, "pared_s": 150.0, "rebuilds": 2}})
        await supervisor().cancel("t-techo")


@pytest.mark.asyncio
async def test_los_rebuilds_estan_acotados_y_el_debate_sigue(registro_rota,
                                                             eventos):
    """
    Melchior propone siempre código que revienta al arrancar. El log del
    16-ago mostró el síntoma sin freno: 6 regeneraciones ENTERAS de las 3
    variantes. Ahora solo se permite `rebuilds=2`, y en la regeneración se
    baja de 3 variantes a 1: la autocuración sigue, pero cuesta una llamada,
    no tres.
    """
    bus, caja = eventos
    try:
        swarm = SwarmOrchestrator(Blackboard(), bus)
        await swarm.submit_task("t-rot", "escribe el módulo", engine="fast")

        assert await esperar_evento(caja, "swarm.verificacion_agotada")
        assert len(caja["swarm.verification_failed"]) == 2
        assert int(swarm.active_tasks["t-rot"]["rebuilds"]) == 2

        textos = " ".join(str(p.get("content", "")) for p in caja["TERMINAL_OUT"])
        assert "rebuild 1/2" in textos and "rebuild 2/2" in textos
        assert "con 1 sola variante" in textos, (
            "tras el primer fallo, la autocuración debe bajar a 1 variante")
        assert "se debate igual" in textos, (
            "tras el tope, lo que haya se debate igual en vez de regenerar")
        assert "rebuild 3" not in textos, (
            "nunca puede haber un tercer ciclo de regeneración")
    finally:
        await supervisor().cancel("t-rot")
