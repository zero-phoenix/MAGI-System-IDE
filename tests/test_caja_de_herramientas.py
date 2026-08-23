"""
Mirar la caja antes de razonar de memoria (P3).

LA MEDICIÓN
===========
Cinco pruebas seguidas contra el enjambre, agosto de 2026:

    menciones_a_herramientas: 0

En una de ellas se preguntó por la portabilidad de un dynarec entre PSP y PS
Vita. MAGI tiene `analyze_port`, `compare_consoles`, `suggest_port_base`,
`console_profile` y `compare_emulators` —escritas exactamente para esa
pregunta— y contestó de memoria.

La respuesta fue buena. Pero era una respuesta de memoria sobre un sistema del
que se podía sacar el dato, y esa es una diferencia de categoría: lo primero es
una opinión informada; lo segundo, evidencia.

El catálogo completo ya viajaba al prompt y no bastó: treinta nombres al final
de un prompt son ruido. Esto señala por su nombre las que responden A ESTE
encargo, y mide si se usaron.
"""
from __future__ import annotations

from magi.modules.swarm import caja_de_herramientas as caja


def _nombres(encargo):
    return [n for n, _ in caja.pertinentes(encargo)]


def test_la_pregunta_de_portabilidad_saca_las_herramientas_de_portabilidad():
    """El caso exacto que se midió, nombrado para que no vuelva en silencio."""
    n = _nombres("Explica por que el dynarec de un emulador de PSP no se puede "
                 "portar tal cual a PS Vita")
    assert "analyze_port" in n
    assert "compare_consoles" in n


def test_un_encargo_de_compilacion_saca_el_compilador():
    n = _nombres("crea un juego de tetris en un unico ejecutable exe portable")
    assert "build_project_exe" in n


def test_cada_herramienta_viene_con_su_para_que():
    """
    «Tienes analyze_port» se ignora; «analyze_port te dice qué se puede
    reutilizar entre dos consolas» se usa. Un catálogo sin propósito es una
    lista de la compra.
    """
    for nombre, porque in caja.pertinentes("portar un emulador de psp a vita"):
        assert len(porque) > 15, f"{nombre} no explica para qué sirve"


def test_una_pregunta_sin_herramientas_no_las_inventa():
    """
    La mitad que evita el ruido. Ofrecer `analyze_port` a quien pregunta por
    filosofía empuja al modelo a usarla, gasta cuota y no aporta nada.
    """
    assert caja.pertinentes("por que duele la soledad") == []
    assert caja.para_el_prompt("por que duele la soledad") == ""


def test_no_se_ofrecen_mas_de_las_que_se_leen():
    """
    El problema original era una lista larga que se ignora. Sustituirla por
    otra lista larga no arregla nada.
    """
    texto = caja.para_el_prompt(
        "portar un emulador de psp a vita, compilar un exe, correr los tests "
        "y subirlo a github con capturas del render y buscando en el codigo")
    assert texto.count("- `") <= caja.TOPE


def test_el_aviso_explica_por_que_importa():
    texto = caja.para_el_prompt("portar un dynarec de psp a vita")
    assert "memoria" in texto
    assert "evidencia" in texto


def test_se_puede_medir_si_las_uso():
    """
    La métrica que estaba a cero y nadie miraba. Sin esto, «tenía la
    herramienta delante y contestó de memoria» es invisible.
    """
    encargo = "portar un dynarec de psp a vita"
    de_memoria = ("El dynarec no se puede portar porque la arquitectura de la "
                  "MIPS de PSP difiere del ARM de Vita.")
    con_datos = ("Segun analyze_port, el 62 % del backend se reutiliza; "
                 "compare_consoles confirma que la MMU difiere.")

    assert caja.menciones(de_memoria, encargo) == []
    usadas = caja.menciones(con_datos, encargo)
    assert "analyze_port" in usadas
    assert "compare_consoles" in usadas
