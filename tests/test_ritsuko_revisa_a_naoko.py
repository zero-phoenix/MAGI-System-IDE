"""
Ritsuko deja de ser documentación y pasa a ser control de calidad (§R1).

EL ENCARGO, Y LA MITAD QUE FALTABA
==================================
Ritsuko se pidió para «verificar que Naoko corrige adecuadamente a las 3 IA …
y redireccionar su funcionamiento». La primera mitad estaba hecha desde el
principio: miraba, medía y escribía informes. La segunda, no. Nada de lo que
concluía tocaba jamás una decisión del sistema.

Un auditor cuyas conclusiones no cambian nada no es un auditor: es
documentación.

EL CASO MEDIDO QUE LO JUSTIFICA
===============================
2026-08-23, sistema del usuario PARADO, sin una sola tarea en curso, en
doscientos segundos de observación por sonda externa:

    Deriva detectada en g4f-gpt:    solo 1/3 respuestas canarias correctas
    Deriva detectada en g4f-gemini: solo 1/3 respuestas canarias correctas

Dos veredictos críticos sobre proveedores intactos. Naoko no estaba midiendo
el modelo: estaba midiendo proveedores gratuitos que ese día devolvían basura
—«tud.», cuatro caracteres, tres veces seguidas—.

«Deriva» no es una anotación inocente: se publica como crítica e invalida las
comparaciones del sistema. Un diagnóstico contaminado mueve MAGI en la
dirección equivocada con toda la autoridad, y hasta ahora nadie lo revisaba.
"""
from __future__ import annotations

import time

import pytest

from magi.core.bus import BusEvent, MagiBus
from magi.modules.infrastructure.ritsuko import RitsukoAgent


def _auditora(eventos=None) -> RitsukoAgent:
    r = RitsukoAgent.__new__(RitsukoAgent)
    r.bus = MagiBus()
    r._eventos = eventos if eventos is not None else []
    r._t0 = time.monotonic()
    r.metrics = None
    r.store = None
    r.swarm = None
    return r


def _deriva(matched: int, total: int = 3) -> BusEvent:
    return BusEvent(topic="provider.model_drift",
                    payload={"provider": "g4f-gpt", "matched": matched,
                             "total": total, "drifted": True})


async def _publicados(r: RitsukoAgent, event: BusEvent) -> list[BusEvent]:
    vistos: list[BusEvent] = []

    async def espia(e: BusEvent):
        vistos.append(e)

    r.bus.subscribe("*", espia)
    await r._revisar_deriva(event)
    # Dar un turno al bus para que sus workers vacíen la cola.
    import asyncio
    await asyncio.sleep(0.05)
    return vistos


@pytest.mark.asyncio
async def test_anula_la_deriva_con_muestra_insuficiente():
    """El caso exacto del 23-ago: 1 de 3."""
    r = _auditora()
    vistos = await _publicados(r, _deriva(matched=1, total=3))

    vetos = [e for e in vistos if e.topic == "ritsuko.veto_de_deriva"]
    assert vetos, "1/3 canarios no sostiene un veredicto de deriva"
    assert "muestra insuficiente" in vetos[0].payload["motivo"]

    dichos = [e for e in vistos if e.topic == "ritsuko.log"]
    assert dichos, "el veto tiene que verse en el panel de Ritsuko"


@pytest.mark.asyncio
async def test_anula_la_deriva_medida_sobre_su_propia_interferencia():
    """
    Aunque la muestra sea buena, si el enjambre estaba quemando cuota contra
    esos mismos proveedores, lo medido es la interferencia, no el modelo.
    """
    r = _auditora()
    r._eventos.append({"t": round(time.monotonic() - r._t0, 1),
                       "tema": "AGENT_POST", "quien": "MELCHIOR",
                       "texto": "propuesta"})

    vistos = await _publicados(r, _deriva(matched=3, total=3))

    vetos = [e for e in vistos if e.topic == "ritsuko.veto_de_deriva"]
    assert vetos, "no se puede diagnosticar con la cuota que uno mismo gasta"
    assert "cuota gastada" in vetos[0].payload["motivo"]


@pytest.mark.asyncio
async def test_sostiene_la_deriva_cuando_si_se_sostiene():
    """
    La mitad que hace que el veto valga algo.

    Un revisor que anula SIEMPRE es tan inútil como uno que no revisa nunca:
    con muestra suficiente y el sistema en reposo, el diagnóstico de Naoko se
    confirma y no se publica ningún veto.
    """
    r = _auditora()
    vistos = await _publicados(r, _deriva(matched=3, total=3))

    assert not [e for e in vistos if e.topic == "ritsuko.veto_de_deriva"]
    assert any(e["tema"] == "ritsuko.revision" for e in r._eventos), (
        "la revisión debe quedar anotada aunque confirme: 'nadie lo miró' y "
        "'lo miré y está bien' son cosas distintas")


@pytest.mark.asyncio
async def test_el_trabajo_viejo_no_cuenta_como_interferencia():
    """
    La ventana de interferencia es de dos minutos. Una tarea de hace media
    hora no puede seguir invalidando mediciones para siempre — eso volvería a
    Ritsuko una anuladora universal.
    """
    r = _auditora()
    r._eventos.append({"t": round(time.monotonic() - r._t0, 1)
                            - r.VENTANA_DE_INTERFERENCIA_S - 60,
                       "tema": "AGENT_POST", "quien": "MELCHIOR", "texto": "x"})

    vistos = await _publicados(r, _deriva(matched=3, total=3))
    assert not [e for e in vistos if e.topic == "ritsuko.veto_de_deriva"]


@pytest.mark.asyncio
async def test_esta_suscrita_a_las_derivas():
    """
    Que el método exista no sirve si nadie lo llama. `start()` tiene que
    engancharlo: es exactamente la forma que tendría este arreglo de no
    arreglar nada.
    """
    import pathlib
    fuente = (pathlib.Path(__file__).resolve().parents[1] / "magi" / "modules"
              / "infrastructure" / "ritsuko.py").read_text(encoding="utf-8")
    assert 'subscribe("provider.model_drift", self._revisar_deriva)' in fuente
