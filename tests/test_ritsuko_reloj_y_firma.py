"""
R2 y R4 de Ritsuko: el reloj que el usuario percibe y la firma de entregas.

QUÉ SE PRUEBA AQUÍ, Y CON QUÉ RELOJ
===================================
NO se miden duraciones reales contra umbrales reales: eso vuelve a medir el
runner (R12, la lección de `t_melchior_ms < 900`). El camino rápido se recorre
de verdad —publicar mensaje, publicar eco, ya— porque cuesta milisegundos y
así se comprueba que el reloj no dispara en falso. El camino LENTO no se
espera: se atrasa la marca interna que el reloj guardó, que es la única cosa
que ese reloj lee. Se prueba la decisión, no la paciencia del runner.

Y el caso negativo que importa tanto como los positivos: una cola que AVISA
que es cola no es un cuelgue, y una tarea conversacional sin artefacto no es
una entrega mal hecha.
"""
from __future__ import annotations

import asyncio

from magi.core.bus import BusEvent, MagiBus
from magi.modules.infrastructure.ritsuko import RitsukoAgent


async def _montar():
    bus = MagiBus()
    agente = RitsukoAgent(bus)
    await agente.start()
    return bus, agente


async def _cosechar(bus: MagiBus, tema: str, espera: float = 0.25) -> list[dict]:
    vistos: list[dict] = []
    bus.subscribe(tema, lambda e: vistos.append(e.payload
                                                if isinstance(e.payload, dict)
                                                else {"raw": str(e.payload)}))
    await asyncio.sleep(espera)
    return vistos


# ----------------------------------------------------------- R2: el eco

async def test_el_eco_rapido_no_es_hallazgo():
    """El caso normal no puede disparar: un aviso que sale siempre deja de
    leerse, y este reloj existe para el día en que el eco VUELVA a tardar
    10,6 s como el 23-ago-2026."""
    bus, agente = await _montar()
    hallazgos = await _cosechar(bus, "ritsuko.retraso_percibido")
    await bus.publish(BusEvent(topic="naoko.user_message",
                               payload={"message": "hola naoko"}))
    await asyncio.sleep(0.15)
    await bus.publish(BusEvent(topic="naoko.log",
                               payload={"agent": "NAOKO", "content": "[USER] hola naoko"}))
    await asyncio.sleep(0.15)
    assert hallazgos == []


async def test_el_eco_tardio_es_hallazgo_con_numero():
    """Atrasar la marca interna: el reloj lee SOLO eso, así que la prueba es
    sobre su decisión, no sobre cuánto aguanta el runner esperando."""
    bus, agente = await _montar()
    hallazgos = await _cosechar(bus, "ritsuko.retraso_percibido")
    await bus.publish(BusEvent(topic="naoko.user_message",
                               payload={"message": "hola naoko"}))
    await asyncio.sleep(0.15)
    assert agente._t0_eco_naoko is not None
    agente._t0_eco_naoko -= 10.6            # el caso real, sin esperarlo
    await bus.publish(BusEvent(topic="naoko.log",
                               payload={"agent": "NAOKO", "content": "[USER] hola naoko"}))
    await asyncio.sleep(0.25)
    assert len(hallazgos) == 1, hallazgos
    assert hallazgos[0]["via"] == "naoko"
    assert 10.0 < hallazgos[0]["retraso_s"] <= 11.0


async def test_el_eco_sin_mensaje_previo_no_mide_nada():
    """Un naoko.log suelto (arranque, sondeo) no puede fabricar un retraso."""
    bus, agente = await _montar()
    hallazgos = await _cosechar(bus, "ritsuko.retraso_percibido")
    await bus.publish(BusEvent(topic="naoko.status",
                               payload={"status": "Inactiva"}))
    await asyncio.sleep(0.15)
    assert hallazgos == []
    assert agente._t0_eco_naoko is None


# ---------------------------------------------------- R2: arranque de ronda

async def test_la_ronda_que_arranca_no_es_hallazgo():
    bus, agente = await _montar()
    hallazgos = await _cosechar(bus, "ritsuko.retraso_percibido")
    await bus.publish(BusEvent(topic="SYS_EXEC",
                               payload={"task_id": "t1", "command": "x"}))
    await asyncio.sleep(0.15)
    await bus.publish(BusEvent(topic="swarm.ronda",
                               payload={"task_id": "t1", "round": 1}))
    await asyncio.sleep(0.15)
    assert hallazgos == []
    assert "t1" not in agente._t0_sys_exec   # el reloj se consumió, no quedó colgado


async def test_recibido_y_sin_empezar_es_hallazgo():
    bus, agente = await _montar()
    hallazgos = await _cosechar(bus, "ritsuko.retraso_percibido")
    await bus.publish(BusEvent(topic="SYS_EXEC",
                               payload={"task_id": "t2", "command": "x"}))
    await asyncio.sleep(0.15)
    agente._t0_sys_exec["t2"] -= 45.0
    await bus.publish(BusEvent(topic="swarm.ronda",
                               payload={"task_id": "t2", "round": 1}))
    await asyncio.sleep(0.25)
    assert len(hallazgos) == 1, hallazgos
    assert hallazgos[0]["via"] == "arranque_ronda"
    assert hallazgos[0]["task_id"] == "t2"


async def test_la_cola_que_avisa_no_es_cuelgue():
    """`swarm.entrada_encolada` cancela el reloj: una cola declarada es
    honestidad, no un cuelgue. El camino rápido de esta decisión."""
    bus, agente = await _montar()
    hallazgos = await _cosechar(bus, "ritsuko.retraso_percibido")
    await bus.publish(BusEvent(topic="SYS_EXEC",
                               payload={"task_id": "t3", "command": "x"}))
    await asyncio.sleep(0.15)
    agente._t0_sys_exec["t3"] -= 90.0
    await bus.publish(BusEvent(topic="swarm.entrada_encolada",
                               payload={"task_id": "t3"}))
    await asyncio.sleep(0.15)
    assert hallazgos == []


# ------------------------------------------------------ R4: firma de entrega

async def test_entrega_con_artefacto_queda_verificada():
    bus, agente = await _montar()
    firmas = await _cosechar(bus, "ritsuko.firma_entrega")
    await bus.publish(BusEvent(topic="swarm.artefacto_listo",
                               payload={"task_id": "t4", "ruta": "C:/x/hola.exe",
                                        "bytes": 10}))
    await asyncio.sleep(0.25)               # que _anotar lo deje en la ventana
    await bus.publish(BusEvent(topic="swarm.task_completed",
                               payload={"task_id": "t4", "result": "informe"}))
    await asyncio.sleep(0.25)
    assert len(firmas) == 1, firmas
    assert firmas[0]["firma"] == "VERIFICADA"
    assert "hola.exe" in firmas[0]["detalle"]


async def test_cierre_sin_nada_deja_la_firma_honesta():
    """Ni artefacto ni aviso: la firma dice que la evidencia NO está, sin
    acusar — una tarea conversacional tampoco produce artefacto."""
    bus, agente = await _montar()
    firmas = await _cosechar(bus, "ritsuko.firma_entrega")
    await bus.publish(BusEvent(topic="swarm.task_completed",
                               payload={"task_id": "t5", "result": "respuesta"}))
    await asyncio.sleep(0.25)
    assert len(firmas) == 1, firmas
    assert firmas[0]["firma"] == "SIN_ARTEFACTO"


async def test_incompleta_declarada_no_se_confunde_con_sin_nada():
    bus, agente = await _montar()
    firmas = await _cosechar(bus, "ritsuko.firma_entrega")
    await bus.publish(BusEvent(topic="swarm.entrega_incompleta",
                               payload={"task_id": "t6", "motivo": "sin código"}))
    await asyncio.sleep(0.25)
    await bus.publish(BusEvent(topic="swarm.task_completed",
                               payload={"task_id": "t6", "result": "informe"}))
    await asyncio.sleep(0.25)
    assert len(firmas) == 1, firmas
    assert firmas[0]["firma"] == "DECLARADA_INCOMPLETA"


async def test_la_firma_no_publica_en_el_bus_del_sistema():
    """Ritsuko informa, no ordena: nada suyo puede salir por un topic que el
    enjambre escucha. Es la carta de independencia hecha aserción."""
    bus, agente = await _montar()
    publicados: list[str] = []

    def espiar(e: BusEvent):
        publicados.append(e.topic)

    bus.subscribe("*", espiar)
    await bus.publish(BusEvent(topic="swarm.task_completed",
                               payload={"task_id": "t7", "result": "x"}))
    await asyncio.sleep(0.25)
    de_ritsuko = [t for t in publicados if t.startswith("ritsuko.")]
    assert de_ritsuko, "ni siquiera firmó: algo se rompió antes"
    assert all(t.startswith("ritsuko.") for t in de_ritsuko)
