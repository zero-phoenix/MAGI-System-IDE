"""
Mirar la caja antes de razonar de memoria (P3).

LA MEDICIÓN QUE OBLIGÓ A ESCRIBIR ESTO
======================================
Cinco pruebas seguidas contra el enjambre, agosto de 2026:

    menciones_a_herramientas: 0

Cero. En una de esas pruebas se le preguntó por la portabilidad de un dynarec
entre PSP y PS Vita. MAGI tiene `analyze_port`, `compare_consoles`,
`suggest_port_base`, `console_profile` y `compare_emulators` — herramientas
escritas exactamente para esa pregunta— y contestó de memoria.

La respuesta fue buena. Pero era una respuesta de memoria sobre un sistema del
que se podía obtener el dato, y eso es una diferencia de categoría: lo primero
es una opinión informada, lo segundo es evidencia.

Cuando yo trabajo, lo primero que hago no es pensar: es buscar. En la sesión
del 20 de agosto, antes de tocar nada, busqué `analyze_port`, `_leer_decision`,
`es_degradada`, `_check_drift` y los tests que ya existían. Así encontré que
`AgentTurn.degraded` ya estaba implementado y se tiraba en la frontera. **Eso
no se deduce pensando; se encuentra mirando.**

QUÉ HACE ESTE MÓDULO
====================
El catálogo de herramientas ya viaja al prompt (ver `builtin.domains_for`), y
no bastó: una lista de treinta nombres al final de un prompt es ruido. Esto
hace otra cosa —señalar, en la parte de arriba y por su nombre, las tres o
cuatro que responden A ESTE encargo— y deja constancia de que se señalaron,
para que «no las usó» deje de ser invisible.

QUÉ NO HACE
===========
No obliga a usarlas ni las llama por su cuenta. Un sistema que fuerza una
llamada a herramienta por cada pregunta gasta cuota en preguntas que no la
necesitan. Señala y mide; decidir sigue siendo del agente.
"""
from __future__ import annotations

import re
import unicodedata

__all__ = ["pertinentes", "para_el_prompt", "menciones"]


def _plano(s: str) -> str:
    sin = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in sin if not unicodedata.combining(c))


#: (patrón del encargo) -> herramientas que responden a eso, con por qué.
#:
#: El «por qué» importa tanto como el nombre: «tienes analyze_port» se ignora;
#: «analyze_port te dice qué se puede reutilizar entre dos consolas y qué no»
#: se usa. Un catálogo sin propósito es una lista de la compra.
_MAPA: tuple[tuple[re.Pattern, tuple[tuple[str, str], ...]], ...] = (
    (re.compile(r"\b(port(e|ar|abilidad)?|psp|vita|ps2|nintendo ds|3ds|"
                r"dynarec|recompilad|emulador|emulacion)\b"),
     (("analyze_port", "dice que subsistemas se pueden reutilizar entre dos "
                       "consolas y cuales hay que reescribir"),
      ("compare_consoles", "compara CPU, GPU, memoria y BIOS de dos maquinas"),
      ("suggest_port_base", "propone de que emulador partir y por que"),
      ("compare_emulators", "contrasta dos implementaciones del mismo sistema"),
      ("locate_subsystem", "encuentra donde vive un subsistema en un arbol"))),

    (re.compile(r"\b(exe|ejecutable|binario|portable|onefile|empaquet)\w*\b"),
     (("build_project_exe", "compila un proyecto Python a un .exe unico y "
                            "devuelve la ruta real del artefacto"),
      ("create_venv", "prepara un entorno limpio para que la compilacion sea "
                      "reproducible"))),

    (re.compile(r"\b(test|tests|pruebas|pytest|cobertura|unitari)\w*\b"),
     (("run_tests", "ejecuta la suite y devuelve el resultado de verdad"),
      ("python_exec", "ejecuta un fragmento y ensena su salida"))),

    (re.compile(r"\b(repositorio|repo|commit|rama|branch|git|github|release)\b"),
     (("git", "estado, diff e historia del repositorio"),
      ("gh", "releases, workflows y issues de GitHub"))),

    (re.compile(r"\b(imagen|png|captura|render|sprite|manga|animat)\w*\b"),
     (("inspect_image", "mide una imagen de verdad en vez de describirla"),
      ("observe_artifact", "abre el artefacto y dice que se ve"))),

    (re.compile(r"\b(codigo|fichero|archivo|modulo|funcion|clase|donde esta)\b"),
     (("grep", "busca en el codigo que ya existe antes de reinventarlo"),
      ("read_file", "lee el fichero en vez de suponer lo que contiene"),
      ("glob", "encuentra ficheros por patron"))),
)


def pertinentes(encargo: str) -> list[tuple[str, str]]:
    """Las herramientas que responden a ESTE encargo, sin repetir."""
    t = _plano(encargo)
    if not t.strip():
        return []
    fuera: list[tuple[str, str]] = []
    vistas: set[str] = set()
    for patron, herramientas in _MAPA:
        if patron.search(t):
            for nombre, porque in herramientas:
                if nombre not in vistas:
                    vistas.add(nombre)
                    fuera.append((nombre, porque))
    return fuera


#: Tope de herramientas señaladas. Más de seis vuelve a ser una lista que se
#: ignora, que es el problema que esto viene a resolver.
TOPE = 6


def para_el_prompt(encargo: str) -> str:
    """
    El aviso que va ARRIBA del prompt, no al final.

    La posición no es un detalle: el catálogo completo ya viajaba al final y
    se ignoraba. Esto va donde se lee.
    """
    lista = pertinentes(encargo)[:TOPE]
    if not lista:
        return ""
    filas = "\n".join(f"- `{n}`: {p}" for n, p in lista)
    return ("\n\nMIRA ANTES DE RAZONAR DE MEMORIA. Para este encargo concreto "
            f"tienes estas herramientas:\n{filas}\n"
            "Si la respuesta depende de un dato que alguna de ellas puede "
            "darte, uSALA y cita lo que devolvio. Una respuesta de memoria "
            "sobre algo que el sistema puede medir es una opinion, no "
            "evidencia — y aqui se distingue.")


def menciones(texto: str, encargo: str = "") -> list[str]:
    """
    Qué herramientas se nombran en lo entregado.

    Es la métrica que estaba a cero y nadie miraba. No juzga si el uso fue
    bueno: solo hace visible el caso «tenia la herramienta delante y contesto
    de memoria», que era invisible.
    """
    t = _plano(texto)
    candidatas = ([n for n, _ in pertinentes(encargo)] if encargo
                  else [n for _, hs in _MAPA for n, _ in hs])
    return [n for n in dict.fromkeys(candidatas) if _plano(n) in t]
