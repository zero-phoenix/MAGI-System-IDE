"""
Pruebas integrales para F2, F3, F4 y F5 (Megaplan v6 / continuacion).

Verifica:
- F2: Subagentes por familia (misma familia, conclusión sintética, tope por nodo y ronda, traza).
- F3: Plan visible con estado (plan.md, inyección en prompt, compuerta contra partes pendientes).
- F4: La compuerta deja de ser opcional (rechazo automático si verificación falla, adjunto si pasa).
- F5: Veredicto «la pregunta era otra» (extracción, cierre sin ganador y registro en descartes.jsonl).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from magi.core.bus import BusEvent, MagiBus
from magi.modules.swarm.agents import _leer_decision
from magi.modules.swarm.cierre import (
    DECISION_APROBADO,
    DECISION_PREGUNTA_OTRA,
    DECISION_RECHAZADO,
    ejecutar_compuerta_rapida,
    evaluar_cierre_entrega,
    registrar_descarte_pregunta_otra,
)
from magi.modules.swarm.memoria_persistente import cargar_descartes
from magi.modules.swarm.plan import (
    PlanItem,
    PlanTarea,
    crear_plan_desde_enunciado,
    verificar_cierre_plan,
)
from magi.modules.swarm.subagentes import (
    GestorSubagentes,
    SubagenteResultado,
    despachar_subagente,
)

# =========================================================================
# F2: Subagentes por familia
# =========================================================================

@pytest.mark.asyncio
async def test_f2_subagente_misma_familia_y_conclusion_sintetica():
    """F2: El subagente adopta la familia de su nodo y devuelve conclusión, no volcado."""
    bus = MagiBus()
    eventos_traza = []

    async def _on_trace(e: BusEvent):
        eventos_traza.append(e.payload)

    bus.subscribe("SUBAGENT_TRACE", _on_trace)

    async def _ejecutor_mock(nodo: str, familia: str, mision: str) -> str:
        # Devuelve conclusión concisa, ahorrando miles de tokens
        return f"Hallazgo en {mision}: bloque de lectura validado sin desbordamiento."

    gestor = GestorSubagentes(limite_por_nodo=2)
    res = await despachar_subagente(
        nodo="Melchior",
        familia="gpt",
        mision="inspeccionar parser_cdb.py",
        round_num=1,
        gestor=gestor,
        bus=bus,
        task_id="tarea_f2_1",
        ejecutor=_ejecutor_mock,
    )

    assert res.exito
    assert isinstance(res, SubagenteResultado)
    assert res.familia == "gpt"
    assert res.nodo == "Melchior"
    assert "sin desbordamiento" in res.conclusion
    # Ahorro de contexto: menos de 50 palabras
    assert len(res.conclusion.split()) < 50

    # Traza visible publicada en el bus
    import asyncio
    await asyncio.sleep(0.05)
    assert len(eventos_traza) == 1
    assert eventos_traza[0]["mision"] == "inspeccionar parser_cdb.py"
    assert eventos_traza[0]["familia"] == "gpt"


@pytest.mark.asyncio
async def test_f2_tope_duro_por_nodo_y_ronda():
    """F2: Tope estricto de subagentes por nodo por ronda (máximo 2 para evitar agotar cuota)."""
    gestor = GestorSubagentes(limite_por_nodo=2)

    # El ejecutor se inyecta porque esta prueba mide el TOPE, no de dónde sale
    # la conclusión. Antes no se pasaba y el módulo devolvía un texto fabricado
    # con exito=True: la prueba pasaba gracias al defecto que había debajo.
    async def _ejecutor(*, nodo, familia, mision):
        return f"leído y resumido: {mision}"

    # 1º OK
    r1 = await despachar_subagente(
        nodo="Balthasar", familia="gemini", mision="m1", round_num=1,
        gestor=gestor, ejecutor=_ejecutor
    )
    assert r1.exito

    # 2º OK
    r2 = await despachar_subagente(
        nodo="Balthasar", familia="gemini", mision="m2", round_num=1,
        gestor=gestor, ejecutor=_ejecutor
    )
    assert r2.exito

    # 3º Rechazado por tope excedido
    r3 = await despachar_subagente(
        nodo="Balthasar", familia="gemini", mision="m3", round_num=1,
        gestor=gestor, ejecutor=_ejecutor
    )
    assert not r3.exito
    assert "TOPE EXCEDIDO" in r3.error
    assert "Balthasar ya invocó 2" in r3.error


# =========================================================================
# F3: Plan visible con estado (plan.md)
# =========================================================================

def test_f3_creacion_y_persistencia_plan_md(tmp_path):
    """F3: Genera plan desde enunciado, serializa a markdown y lo guarda."""
    enunciado = """
    Por favor haz lo siguiente:
    1. Identificar registros de entrada del mando Saturn.
    2. Compilar el stub de lectura con gcc.
    3. Probar el movimiento en el emulador.
    """
    plan = crear_plan_desde_enunciado("task_plan_1", enunciado)
    assert len(plan.items) == 3
    assert isinstance(plan.items[0], PlanItem)
    assert plan.items[0].estado == "pendiente"
    assert "Identificar registros" in plan.items[0].descripcion

    # Actualizar estado
    plan.actualizar_estado("parte_1", "hecha")
    plan.actualizar_estado("parte_2", "haciendo")
    plan.actualizar_estado("parte_3", "no se pudo", motivo="sin binario de vita")

    # Guardar plan.md
    ruta_guardada = plan.guardar(tmp_path)
    assert ruta_guardada.exists()
    contenido = ruta_guardada.read_text(encoding="utf-8")
    assert "[x] [hecha] parte_1" in contenido
    assert "[/] [haciendo] parte_2" in contenido
    assert "[-] [no se pudo] parte_3" in contenido
    assert "sin binario de vita" in contenido

    # Deserializar en otro objeto
    plan_recargado = PlanTarea(task_id="task_plan_1")
    plan_recargado.desde_markdown(contenido)
    assert len(plan_recargado.items) == 3
    assert plan_recargado.items[0].estado == "hecha"
    assert plan_recargado.items[2].motivo == "sin binario de vita"


def test_f3_compuerta_rechaza_cierre_con_partes_pendientes():
    """F3: Casper no puede cerrar con partes en 'pendiente' sin justificar."""
    plan = PlanTarea(task_id="task_compuerta")
    plan.agregar_item("Paso A", id_item="p1")
    plan.agregar_item("Paso B", id_item="p2")

    # Ambas pendientes -> rechaza
    ok, err = verificar_cierre_plan(plan)
    assert not ok
    assert "COMPUERTA F3 RECHAZADA" in err
    assert "p1" in err and "p2" in err

    # Marcamos una hecha y otra justificada ("no se pudo")
    plan.actualizar_estado("p1", "hecha")
    plan.actualizar_estado("p2", "no se pudo", motivo="recurso no disponible")

    ok2, msg2 = verificar_cierre_plan(plan)
    assert ok2
    assert "resueltas o justificadas" in msg2


# =========================================================================
# F4: La compuerta deja de ser opcional
# =========================================================================

def test_f4_entrega_sin_verificacion_se_rechaza_sola():
    """F4: Si Casper intenta aprobar pero la verificación falló, se rechaza solo."""
    plan_ok = PlanTarea(task_id="t_f4")
    plan_ok.agregar_item("Paso 1", id_item="p1")
    plan_ok.actualizar_estado("p1", "hecha")

    # Intento de aprobación con compuerta_ok=False
    decision, feedback = evaluar_cierre_entrega(
        DECISION_APROBADO,
        "La solución cumple todos los requisitos.",
        plan=plan_ok,
        compuerta_ok=False,
        compuerta_info="Fallo en test_pipeline.py: 1 assertion error",
    )

    assert decision == DECISION_RECHAZADO
    assert "COMPUERTA F4 RECHAZADA" in feedback
    assert "Fallo en test_pipeline.py" in feedback


def test_f4_entrega_con_verificacion_aprobada_adjunta_resultado():
    """F4: Cuando la verificación pasa, se aprueba adjuntando el reporte de la compuerta."""
    plan_ok = PlanTarea(task_id="t_f4_pass")
    plan_ok.agregar_item("Paso 1", id_item="p1")
    plan_ok.actualizar_estado("p1", "hecha")

    decision, feedback = evaluar_cierre_entrega(
        DECISION_APROBADO,
        "Solución completa y probada.",
        plan=plan_ok,
        compuerta_ok=True,
        compuerta_info="199 passed in 2.5s (verificar.py --rapido OK)",
    )

    assert decision == DECISION_APROBADO
    assert "Compuerta de verificación superada" in feedback
    assert "199 passed" in feedback


def test_f4_ejecutar_compuerta_rapida():
    """F4: ejecutar_compuerta_rapida corre el runner y evalúa retorno."""
    ok, salida = ejecutar_compuerta_rapida(runner=lambda: (0, "199 passed in 2.5s"))
    assert ok
    assert "199 passed" in salida

    ok_fallo, err = ejecutar_compuerta_rapida(runner=lambda: (1, "1 failed"))
    assert not ok_fallo
    assert "1 failed" in err


# =========================================================================
# F5: Veredicto «la pregunta era otra»
# =========================================================================

def test_f5_extraccion_decision_la_pregunta_era_otra():
    """F5: _leer_decision extrae LA_PREGUNTA_ERA_OTRA ante desvío de foco."""
    texto_casper = """
    Hemos medido el tiempo de render en la escena de prueba.
    Las tres propuestas optimizan la rutina de sombreado que representa apenas el 1.2% del tiempo total.
    El verdadero cuello de botella está en los accesos al bus del Slave SH2.

    DECISIÓN: LA PREGUNTA ERA OTRA
    """
    decision, feedback = _leer_decision(texto_casper, round_num=1)
    assert decision == DECISION_PREGUNTA_OTRA
    assert "1.2%" in feedback


def test_f5_registro_descarte_pregunta_otra(tmp_path, monkeypatch):
    """F5: Una ronda con 'la pregunta era otra' se registra en descartes.jsonl."""
    mem_dir = tmp_path / "memoria"
    mem_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MAGI_MEMORIA", str(mem_dir))

    ok = registrar_descarte_pregunta_otra(
        proyecto="yabausevita",
        ronda="ronda_4",
        enfoque="optimizacion shader gouraud",
        motivo="el cuello de botella es el bus SH2, no los shaders",
        medicion="shader representa 1.2% del tiempo de frame",
        rescatable="la medicion de bus maestro-esclavo sirve para la ronda 5",
        inicio=tmp_path,
    )
    assert ok

    # Verificar lectura
    descartes = cargar_descartes(inicio=tmp_path)
    assert len(descartes) >= 1
    ultimo = descartes[-1]
    assert ultimo["proyecto"] == "yabausevita"
    assert ultimo["ronda"] == "ronda_4"
    assert "la pregunta era otra" in ultimo["filosofia"]
    assert "cuello de botella es el bus" in ultimo["motivo"]
