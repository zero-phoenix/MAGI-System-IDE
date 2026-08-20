"""
El encargo como contrato, y ninguna promesa perdida en silencio (D1, D5).

La prueba D del 2026-08-20 pedía explícitamente «el orden de trabajo que
minimiza el riesgo de abandono». La respuesta fue técnicamente buena y **no
mencionó el abandono ni una vez**. Nadie lo notó porque nadie llevaba la lista.
"""
from __future__ import annotations

from magi.modules.swarm import contrato

PING_PONG = "Crea un juego de ping pong de 32 bits a todo color en un unico ejecutable exe portable."
NDS_PSP = ("Disena el plan para portar un emulador de NDS a PSP. Di que se "
           "reutiliza, como se valida cada etapa con pruebas diferenciales, y "
           "cual es el orden de trabajo que minimiza el riesgo de abandono.")


def test_extrae_los_compromisos_de_un_encargo_de_producto():
    ques = [c["que"] for c in contrato.compromisos(PING_PONG)]
    assert "entregar un ejecutable" in ques
    assert "que sea portable" in ques
    assert "el formato de color pedido" in ques
    assert "que sea jugable" in ques


def test_cada_compromiso_dice_como_se_comprueba():
    """Un compromiso que no dice cómo se comprueba es un deseo."""
    for c in contrato.compromisos(PING_PONG):
        assert c["como"], f"{c['que']} no dice como se comprueba"


def test_extrae_las_partes_de_una_pregunta_larga():
    ques = [c["que"] for c in contrato.compromisos(NDS_PSP)]
    assert "hablar de los riesgos" in ques
    assert "dar un orden de trabajo" in ques
    assert "decir como se valida" in ques


def test_caza_la_parte_que_la_respuesta_se_dejo():
    """
    El caso real, reproducido: respuesta buena en lo técnico que se come el
    riesgo de abandono.
    """
    lista = contrato.compromisos(NDS_PSP)
    respuesta = ("Fase 1: interprete MIPS. Fase 2: VFPU. Fase 3: kernel HLE. "
                 "Se valida comparando registros contra trazas.")
    faltan = contrato.sin_cubrir(respuesta, lista)
    assert "hablar de los riesgos" in faltan
    # Y lo que SÍ contestó no se reporta como pendiente.
    assert "dar un orden de trabajo" not in faltan
    assert "decir como se valida" not in faltan


def test_una_respuesta_completa_no_deja_pendientes():
    lista = contrato.compromisos(NDS_PSP)
    respuesta = ("Fases en orden: 1 cargador, 2 interprete. Se valida con "
                 "pruebas diferenciales contra trazas de hardware. Los riesgos "
                 "que hunden el proyecto son empezar por el JIT y subestimar "
                 "el kernel, que es como se llega al abandono.")
    assert contrato.sin_cubrir(respuesta, lista) == []


def test_un_encargo_vacio_no_inventa_compromisos():
    assert contrato.compromisos("") == []
    assert contrato.render([]) == ""
