"""
Qué significa «hecho», decidido antes de empezar y comprobable por máquina (P2).

EL PRINCIPIO
============
Cuando hice el ping pong de 32 bits, lo primero que escribí no fue el juego:
fue cómo iba a saber que estaba bien.

    pong32.exe --autotest 200   -> 200 fotogramas, imprime fps, sale con 0
    pong32.exe --formato        -> comprueba la matemática del alfa RGBA

No es pulcritud. Es que **yo tampoco veo la pantalla**, y necesito exactamente
la misma evidencia que necesita el usuario. Sin esos dos modos, lo único que
podría afirmar es «debería funcionar»; con ellos puedo decir «48 fps» y «alfa
correcto».

MAGI tiene la misma limitación y no actuaba en consecuencia. De ahí salieron
frases como «Se compiló exitosamente el binario ejecutable único portable
(onefile)» con cero bloques de código y cero artefactos en todo el registro.
"""
from __future__ import annotations

from magi.modules.swarm import aceptacion


def _nombres(lista):
    return [c["que"] for c in lista]


def test_un_juego_en_exe_exige_autoprueba_y_fichero():
    c = aceptacion.criterios(
        "crea un juego de tetris en un unico ejecutable exe portable")
    assert "arranca y avanza solo" in _nombres(c)
    assert "el fichero existe de verdad" in _nombres(c)


def test_el_formato_de_color_se_verifica_solo():
    """
    El criterio que separa «es de 32 bits» de «dice que es de 32 bits». Nadie
    de este sistema ve los píxeles: o el programa comprueba su propio alfa, o
    la afirmación no se puede sostener.
    """
    c = aceptacion.criterios(
        "un juego de ping pong de 32 bits a todo color en un exe portable")
    assert "el formato de color es el pedido" in _nombres(c)
    assert any("--formato" in x["como"] for x in c)


def test_los_criterios_traen_un_comando_literal():
    """
    «Autoprueba» es un deseo; `--autotest 200` es una comprobación. Si el
    criterio no dice qué se ejecuta, no se puede ejecutar.
    """
    for c in aceptacion.criterios("haz un juego en un exe"):
        assert c["como"].strip(), f"criterio sin comando: {c['que']}"
        assert c["espera"].strip(), f"criterio sin resultado esperado: {c['que']}"


def test_una_pregunta_sin_artefacto_no_inventa_criterios():
    """
    La mitad que evita el ritual vacío.

    «Explica por qué la filosofía es la madre de las ciencias» no produce nada
    ejecutable. Fabricar criterios ahí solo sirve para que alguien los declare
    cumplidos sin haber comprobado nada — un criterio incomprobable da falsa
    confianza, que es peor que no tener ninguno.
    """
    assert aceptacion.criterios(
        "explica por que la filosofia es la madre de todas las ciencias") == []
    assert aceptacion.criterios("") == []


def test_el_prompt_dice_que_nadie_ve_la_pantalla():
    """
    Es la razón, y sin la razón la instrucción se ignora. Un modelo al que se
    le pide «añade --autotest» lo trata como un extra; uno al que se le explica
    que nadie va a poder mirar el resultado, lo construye.
    """
    texto = aceptacion.para_el_prompt(aceptacion.criterios("un juego en un exe"))
    assert "--autotest" in texto
    assert "ve la pantalla" in texto
    assert "DESDE EL PRINCIPIO" in texto


def test_lo_no_construido_se_detecta():
    c = aceptacion.criterios("un juego de pong de 32 bits en un exe")
    faltan = aceptacion.sin_comprobar(
        "He diseñado un juego excelente con un bucle de render muy pulido.", c)
    assert "arranca y avanza solo" in faltan
    assert "el formato de color es el pedido" in faltan


def test_lo_construido_de_verdad_no_se_marca_como_falta():
    """
    La otra mitad: si la comprobación se queja de trabajo que SÍ está hecho,
    el usuario aprende a ignorar el aviso y el mecanismo muere.
    """
    c = aceptacion.criterios("un juego de pong de 32 bits en un exe")
    entregado = (
        "```python\n"
        "if '--autotest' in sys.argv: ...\n"
        "if '--formato' in sys.argv: verificar_alfa()\n"
        "```\n"
        "Compilado a dist/pong32.exe"
    )
    assert aceptacion.sin_comprobar(entregado, c) == []


def test_sin_criterios_no_hay_nada_que_reprochar():
    assert aceptacion.sin_comprobar("cualquier cosa", []) == []
    assert aceptacion.render([]) == ""
    assert aceptacion.para_el_prompt([]) == ""
