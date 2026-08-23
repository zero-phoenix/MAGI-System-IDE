"""
Qué significa «hecho», decidido ANTES de empezar y comprobable por máquina (P2).

EL PRINCIPIO, Y POR QUÉ NO ES PULCRITUD
=======================================
Cuando yo hice el ping pong de 32 bits, lo primero que escribí no fue el juego:
fue cómo iba a saber que estaba bien. Salieron dos modos:

    pong32.exe --autotest 200   -> juega 200 fotogramas, imprime fps, sale con 0
    pong32.exe --formato        -> comprueba la matemática del alfa RGBA

No es orden ni buenas maneras. Es que **yo tampoco veo la pantalla**. Necesito
exactamente la misma evidencia que necesita el usuario, y sin esos dos modos lo
único que podría decir es «debería funcionar».

MAGI tiene la misma limitación y no actuaba en consecuencia. De ahí salían
frases como «Se compiló exitosamente el binario ejecutable único portable» con
cero bloques de código y cero artefactos en todo el registro.

QUÉ HACE ESTE MÓDULO
====================
De los compromisos del contrato deduce criterios de aceptación **ejecutables**:
un comando concreto y qué debe ocurrir. Se le entregan al agente al empezar
—para que los construya, no para que los adivine— y se comprueban al final.

QUÉ NO HACE
===========
No inventa criterios para lo que no puede comprobar. Si el encargo es «explica
por qué la filosofía es la madre de las ciencias», aquí no hay nada que
ejecutar y este módulo devuelve una lista vacía en vez de fabricar un ritual.
Un criterio que no se puede comprobar es peor que ninguno: da falsa confianza.
"""
from __future__ import annotations

import re
import unicodedata

__all__ = ["criterios", "render", "para_el_prompt", "sin_comprobar"]


def _plano(s: str) -> str:
    sin = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in sin if not unicodedata.combining(c))


#: Un criterio es (nombre, comando, qué se espera). El comando es literal a
#: propósito: «autoprueba» es un deseo, `--autotest 200` es una comprobación.
_AUTOTEST = {
    "que": "arranca y avanza solo",
    "como": "--autotest 200",
    "espera": "sale con codigo 0 e imprime los fotogramas por segundo",
}
_FORMATO = {
    "que": "el formato de color es el pedido",
    "como": "--formato",
    "espera": "el propio programa verifica la matematica del color y sale con 0",
}
_EXISTE = {
    "que": "el fichero existe de verdad",
    "como": "comprobar la ruta y el tamano en disco",
    "espera": "ruta absoluta, tamano > 0 y hash en el informe",
}
_TESTS = {
    "que": "las pruebas pasan",
    "como": "pytest -q",
    "espera": "codigo de salida 0",
}

#: Señales del encargo -> criterio que exige. Se mantienen cortas y literales:
#: este módulo acierta o calla, no interpreta.
_JUEGO = re.compile(r"\b(juego|jugab|game|tetris|pong|snake|arkanoid|"
                    r"plataformas|shooter)\b")
_COLOR = re.compile(r"\b(\d{1,2}\s*bits|rgba?|rgb565|a todo color|paleta)\b")
_BINARIO = re.compile(r"\b(exe|ejecutable|binario|onefile|portable)\b")
_PRUEBAS = re.compile(r"\b(test|tests|pruebas|pytest|unitari)\w*\b")


def criterios(encargo: str) -> list[dict]:
    """
    Los criterios de aceptación ejecutables que exige este encargo.

    Vacío cuando no hay nada que ejecutar, y eso es correcto: no todo encargo
    produce un artefacto, y fabricar criterios para una explicación solo sirve
    para que alguien los declare cumplidos sin haberlos comprobado.
    """
    t = _plano(encargo)
    if not t.strip():
        return []
    fuera: list[dict] = []
    if _BINARIO.search(t):
        fuera.append(dict(_EXISTE))
    if _JUEGO.search(t):
        fuera.append(dict(_AUTOTEST))
    if _COLOR.search(t):
        fuera.append(dict(_FORMATO))
    if _PRUEBAS.search(t):
        fuera.append(dict(_TESTS))
    return fuera


def render(lista: list[dict]) -> str:
    """Lo que se le enseña al usuario nada más empezar."""
    if not lista:
        return ""
    filas = "\n".join(f"  · {c['que']}  ->  `{c['como']}`  ({c['espera']})"
                      for c in lista)
    return ("[ACEPTACION] Antes de escribir nada, esto es lo que voy a "
            f"considerar «hecho», y como lo voy a comprobar:\n{filas}")


def para_el_prompt(lista: list[dict]) -> str:
    """
    Los criterios, redactados como una exigencia de construcción.

    Lo importante es el orden: se le dan ANTES de escribir, para que el
    programa NAZCA con la forma de poder comprobarse. Pedirlos al final es
    pedir que se añada un modo de prueba a algo ya escrito, y eso casi nunca
    se hace.
    """
    if not lista:
        return ""
    filas = "\n".join(f"- {c['que']}: el artefacto debe aceptar `{c['como']}` "
                      f"y {c['espera']}." for c in lista)
    return ("\n\nCRITERIOS DE ACEPTACION — se comprueban ejecutando, no "
            f"leyendo:\n{filas}\n"
            "IMPORTANTE: nadie de este sistema ve la pantalla. Un programa "
            "que solo se puede juzgar mirandolo es un programa que no se "
            "puede juzgar. Construye estos modos DESDE EL PRINCIPIO, no al "
            "final: son parte del encargo, no un extra.")


#: Huellas de que un criterio se construyó de verdad. Se buscan en el codigo y
#: en el texto entregado: si el modo `--autotest` existe, la cadena aparece.
_HUELLAS = {
    "arranca y avanza solo": ("--autotest", "autotest"),
    "el formato de color es el pedido": ("--formato", "--format", "verifica_formato"),
    "el fichero existe de verdad": (".exe", "dist", "artefacto"),
    "las pruebas pasan": ("pytest", "def test_", "unittest"),
}


def sin_comprobar(entregado: str, lista: list[dict]) -> list[str]:
    """
    Qué criterios NO se ven construidos en lo entregado.

    Tolerante a propósito, igual que `contrato.sin_cubrir`: basta una huella.
    No puntúa la calidad; impide que un criterio entero desaparezca sin que
    nadie lo note, que es como se cuelan los «se compiló exitosamente» sobre
    binarios que no existen.
    """
    t = _plano(entregado)
    faltan = []
    for c in lista:
        huellas = _HUELLAS.get(c["que"], ())
        if huellas and not any(_plano(h) in t for h in huellas):
            faltan.append(c["que"])
    return faltan
