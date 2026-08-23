"""
Desconfiar del propio informe de éxito, no solo en el caso que ya pillaron (P5).

C12 nació de un caso concreto: una síntesis que decía «Se compiló exitosamente
el binario ejecutable único portable (onefile)» con cero bloques de código,
cero llamadas a la herramienta de entrega y cero artefactos en el registro.

Pero la forma del fallo no tiene nada que ver con compilar. Es **atribuirse un
hecho comprobable que el registro no sostiene**, y eso se dice de muchas
maneras: «las pruebas pasan», «he escrito el fichero», «según analyze_port…».

Un sistema que solo se revisa en el caso que ya le pillaron aprende a esquivar
ese caso, no a ser honesto.

Es el mismo principio que aplico sobre mi propio trabajo, y me cazó dos veces
en la sesión del 20 de agosto: una prueba de alfa que fallaba porque mi
expectativa estaba mal —no el código—, y un primer informe de Ritsuko cuyo
veredicto era literalmente el mensaje de error del proveedor, que es
exactamente el fallo que Ritsuko existe para denunciar.
"""
from __future__ import annotations

import pytest

from magi.modules.swarm.orchestrator import SwarmOrchestrator


@pytest.fixture()
def orq():
    return SwarmOrchestrator.__new__(SwarmOrchestrator)


def _v(texto: str) -> dict:
    return {"feedback": texto, "decision": "APPROVED"}


# ---------------------------------------------------------- el caso original

def test_decir_que_compilo_sin_artefacto_se_avisa(orq):
    aviso = orq._contraste_con_el_registro({}, _v("Se compiló exitosamente."))
    assert aviso and "no hay fichero que buscar" in aviso


def test_con_artefacto_en_el_registro_no_se_avisa(orq):
    aviso = orq._contraste_con_el_registro(
        {"exe_path": r"C:\Users\D\Desktop\pong.exe"},
        _v("Se compiló exitosamente."))
    assert aviso is None


# ------------------------------------------------------------ la ampliación

def test_decir_que_las_pruebas_pasan_sin_haberlas_corrido(orq):
    aviso = orq._contraste_con_el_registro(
        {}, _v("Los tests pasan y la suite queda en verde."))
    assert aviso and "previsión, no un resultado" in aviso


def test_si_se_corrieron_de_verdad_no_se_avisa(orq):
    aviso = orq._contraste_con_el_registro(
        {"verification": {"passed": True}},
        _v("Los tests pasan y la suite queda en verde."))
    assert aviso is None


def test_decir_que_escribio_un_fichero_sin_escribirlo(orq):
    aviso = orq._contraste_con_el_registro(
        {}, _v("He escrito el fichero en la ruta indicada."))
    assert aviso and "no consta ninguno" in aviso


def test_citar_una_herramienta_que_no_se_ejecuto(orq):
    """
    La cita de memoria disfrazada de dato. Es la más peligrosa de las tres:
    suena a evidencia y no lo es.
    """
    aviso = orq._contraste_con_el_registro(
        {}, _v("Según analyze_port, el 62 % del backend se reutiliza."))
    assert aviso and "cita de memoria" in aviso


def test_si_la_herramienta_si_corrio_la_cita_es_legitima(orq):
    """
    La mitad que protege el trabajo bien hecho.

    Cuando `evidencia_previa` ejecuta `analyze_port` de verdad, citarlo es
    exactamente lo que se le pide al agente. Avisar ahí sería castigar la
    conducta correcta, y una alarma falsa sobre trabajo bien hecho enseña a
    ignorar las alarmas — que es como se pierden las que sí importan.
    """
    aviso = orq._contraste_con_el_registro(
        {"evidencia_previa": True},
        _v("Según analyze_port, el 62 % del backend se reutiliza."))
    assert aviso is None


def test_una_sintesis_que_no_se_atribuye_nada_no_recibe_avisos(orq):
    """Sin afirmación no hay nada que contrastar. El silencio no es sospechoso."""
    aviso = orq._contraste_con_el_registro(
        {}, _v("Propongo la siguiente arquitectura por capas, con sus riesgos."))
    assert aviso is None
