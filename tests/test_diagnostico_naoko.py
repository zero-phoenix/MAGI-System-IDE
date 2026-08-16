"""
NAOKO no puede volver a inventarse una partida de tres en raya.

Lo que pasó: el usuario escribió «pedi al sistema crear un juego de tris pero
no responde». NAOKO tenía el estado del enjambre delante, contó bien las tareas
—7, tres esperando y cuatro «en curso»— y contestó con la excusa genérica que
su prompt prohibía, más un tablero de tres en raya inventado.

Dos causas, ninguna de redacción:

1. El resumen decía «EN CURSO: … Si se queja de demora, ESTO es la demora».
   Esas cuatro tareas llevaban muertas desde el día anterior. Premisa falsa,
   explicación falsa.
2. Sin nada verdadero que decir, rellenó.
"""
from __future__ import annotations

import pytest

from magi.modules.infrastructure.diagnostico import (
    CATALOGO,
    Situacion,
    catalogo_legible,
    diagnosticar,
    es_operativa,
)

# ------------------------------------------------- reconocer la queja

@pytest.mark.parametrize("frase", [
    "pedi al sistema crear un juego de tris pero no responde",
    "no me responde",
    "el sistema no funciona",
    "por que tarda tanto",
    "esta muy lento",
    "la respuesta esta a medias",
])
def test_reconoce_las_quejas_operativas(frase):
    assert es_operativa(frase)


@pytest.mark.parametrize("frase", [
    "por que la filosofia es la madre de todas las ciencias",
    "crea un juego de tetris en un ejecutable portable",
    "explicame como funciona un emulador de psp",
])
def test_no_secuestra_las_preguntas_normales(frase):
    """Si no es sobre el sistema, NAOKO contesta como siempre."""
    assert not es_operativa(frase)
    assert diagnosticar(frase, Situacion()) is None


@pytest.mark.parametrize("frase", [
    "el emulador de psp que me hiciste no funciona",
    "compila pero el juego no responde al mando",
    "revisa este codigo, no funciona la funcion de decompilado",
    "el dynarec de mips no funciona bien en ppsspp",
    "el script de descompilado se quedo colgado",
    "el exe que generaste no responde",
])
def test_una_queja_sobre_TU_codigo_no_se_secuestra(frase):
    """
    El riesgo de tener catálogo. Estas seis frases hablan del trabajo, no del
    sistema, y todas habrían recibido un diagnóstico de MAGI en lugar de que
    alguien mirara el código.

    Cambiar «NAOKO se inventa cosas» por «NAOKO ignora tu pregunta y habla de
    sí misma» no habría sido un arreglo.
    """
    assert not es_operativa(frase)


@pytest.mark.parametrize("frase", [
    "el sistema no funciona",
    "pedi al sistema crear un juego de tris pero no responde",
    "te pregunte algo y no me contestas",
    "el enjambre no responde",
    "naoko tarda demasiado",
])
def test_y_las_quejas_sobre_MAGI_si_se_reconocen(frase):
    """
    El otro lado de la moneda, y donde caí una vez: al excluir «funcion» —de
    «la función que escribiste»— dejó de reconocerse «el sistema no FUNCIONA»,
    porque una está dentro de la otra. Y al excluir «juego» se perdió la frase
    original del usuario, que habla de un juego pero se queja del sistema.
    """
    assert es_operativa(frase)


# ---------------------------------------------- el caso real, palabra por
#                                                 palabra

PREGUNTA_REAL = "pedi al sistema crear un juego de tris pero no responde"


def test_el_caso_del_tres_en_raya_ahora_se_diagnostica():
    """
    Mismo estado que tenía la máquina del usuario: cuatro tareas marcadas
    `in_progress` y ninguna con bucle vivo.
    """
    s = Situacion(
        tareas={t: {"status": "in_progress"} for t in
                ("default", "task_6c0c00a9", "task_7edd3cda", "task_c195c65e")},
        zombis=["default", "task_6c0c00a9", "task_7edd3cda", "task_c195c65e"])

    d = diagnosticar(PREGUNTA_REAL, s)
    assert d is not None and d.seguro
    assert d.caso.id == "zombi"
    assert "default" in d.texto


def test_la_respuesta_no_puede_contener_la_excusa_generica():
    """La frase exacta que salió en la captura, prohibida en todo el catálogo."""
    prohibidas = ("fallos temporales", "es muy comun", "es muy común",
                  "intenta de nuevo", "vuelve a intentarlo", "paciencia")
    for caso in CATALOGO:
        texto = (caso.causa + " " + caso.arreglo(Situacion())).lower()
        for p in prohibidas:
            assert p not in texto, f"{caso.id} contiene «{p}»"


def test_es_determinista():
    """Mismo estado, mismo texto. Un modelo no puede garantizar esto."""
    s = Situacion(tareas={"t": {"status": "in_progress"}}, zombis=["t"])
    a = diagnosticar(PREGUNTA_REAL, s)
    b = diagnosticar(PREGUNTA_REAL, s)
    assert a.texto == b.texto


# ------------------------------------------------------- los demás casos

def test_esperando_al_usuario_no_es_un_fallo():
    s = Situacion(tareas={"t1": {"status": "WAITING_USER_APPROVAL"}},
                  esperando_usuario=["t1"])
    d = diagnosticar("no responde", s)
    assert d.caso.id == "espera_al_usuario"
    assert "apruebo" in d.texto


def test_sin_ninguna_tarea_la_peticion_no_llego():
    d = diagnosticar("pregunte y no responde", Situacion())
    assert d.caso.id == "no_llego"
    assert "no existe" in d.texto


def test_lo_encolado_se_explica_como_encolado():
    s = Situacion(tareas={"t1": {"status": "in_progress"}},
                  en_curso_de_verdad=["t1"], en_cola=2)
    d = diagnosticar("no responde", s)
    assert d.caso.id == "en_cola"
    assert "2" in d.texto


def test_una_demora_real_dice_donde_se_va_el_tiempo():
    s = Situacion(tareas={"t1": {"status": "in_progress"}},
                  en_curso_de_verdad=["t1"],
                  latencias={"gpt": 4.1, "gemini": 3.8})
    d = diagnosticar("por que tarda tanto", s)
    assert d.caso.id == "demora_real"
    assert "gpt" in d.texto


def test_una_salida_cortada_no_se_le_achaca_al_modelo():
    s = Situacion(tareas={"t1": {"status": "in_progress"}}, truncados=1)
    d = diagnosticar("la respuesta no tiene sentido", s)
    assert d.caso.id == "truncado"
    assert "cort" in d.texto.lower()


# ------------------------------------------- lo más importante de todo:
#                                              admitir que no lo sabe

def test_si_ningun_caso_encaja_dice_que_no_lo_sabe():
    """
    ESTA es la respuesta correcta, no un fallo.

    Un sistema de diagnóstico que improvisa sobre su propio estado da
    confianza falsa, que es peor que no tener diagnóstico. El tres en raya fue
    exactamente eso: rellenar un hueco.
    """
    s = Situacion(tareas={"t1": {"status": "raro_desconocido"}})
    d = diagnosticar("no responde", s)
    assert d is not None
    assert d.seguro is False
    assert "no se" in d.texto.lower() or "no sé" in d.texto.lower()


def test_cuando_no_sabe_ensena_los_datos_igualmente():
    """
    Situación que el catálogo NO reconoce: hay tareas, pero ninguna esperando,
    ninguna viva, ninguna zombi y nada en cola. Aun así se enseña lo que hay.
    """
    s = Situacion(tareas={"tarea_rara": {"status": "estado_inedito"}},
                  interrumpidas=["tarea_rara"])
    d = diagnosticar("no responde", s)
    assert not d.seguro
    assert "tarea_rara" in d.texto
    assert "libro de admision" in d.texto or "libro de admisión" in d.texto


def test_el_catalogo_se_puede_leer_entero():
    """Es contenido versionado, no magia: tiene que poder enseñarse."""
    texto = catalogo_legible()
    for c in CATALOGO:
        assert c.id in texto
        assert c.sintoma in texto


def test_todos_los_casos_producen_texto_util_sin_datos():
    """Ningún caso puede reventar cuando la situación viene vacía."""
    for c in CATALOGO:
        salida = c.arreglo(Situacion())
        assert isinstance(salida, str) and salida.strip()
