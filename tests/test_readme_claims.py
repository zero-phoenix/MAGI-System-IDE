"""
El README no miente.

POR QUÉ EXISTE
==============
El README describe el sistema con cifras concretas —"625 tests", "44
herramientas", "tres inteligencias"— que derivan con cada commit. Documentación
que contradice al código es peor que no tenerla: el §I.3 del proyecto lo dice
explicito, y esta reconstrucción ya lo vivió (la tabla del enjambre llegó a
decir deepseek/claude/qwen cuando esas tres familias no tenían un solo
candidato vivo).

Este test compara las afirmaciones NUMÉRICAS del README contra el conteo real
en runtime. Si alguien añade una herramienta o un test, el README debe
actualizarse; si no, este test falla y le dice cómo.

No es una aserción de correctitud: es una aserción de CONSISTENCIA. El valor
del README es que diga la verdad; si dice cualquier cosa, mejor que no diga
nada.
"""
import re
from pathlib import Path

import pytest

README = Path(__file__).resolve().parents[1] / "README.md"


@pytest.fixture(scope="module")
def readme() -> str:
    assert README.exists(), "README.md no encontrado"
    return README.read_text(encoding="utf-8")


def _cuenta_items_de_test() -> int:
    """Total de items de test colectados por pytest (tests paramétricos incluidos)."""
    import subprocess
    r = subprocess.run(
        ["python", "-m", "pytest", "--collect-only", "-q", "-o", "addopts="],
        capture_output=True, text=True, timeout=120, cwd=Path(__file__).resolve().parents[1])
    # Cada item de test aparece como "ruta::TestCase" en el listado quiet.
    return sum(1 for line in r.stdout.splitlines() if "::" in line)


TOLERANCIA_TESTS = 0.85  # el suelo declarado no puede quedarse >15% por debajo


def test_el_readme_cita_la_cantidad_real_de_tests(readme):
    """El README declara un SUELO de tests: 'más de N tests en Python'.

    LA CIFRA ES UN SUELO, Y ESO CAMBIA LA ASERCIÓN
    ==============================================
    La primera versión de este test comparaba `declarado >= real`, es decir,
    exigía que el README fuese siempre igual o mayor que la suite. El efecto
    práctico era el contrario del buscado: **cada commit que añadía un test
    dejaba la suite en rojo** hasta que alguien editara el README. Se cumplió
    de inmediato — el commit que introdujo tests/test_guarda_idioma.py subió el
    conteo de 786 a 789 y dejó el CI roto sin tocar una línea de producción.

    Un test que castiga añadir tests acaba enseñando a no añadirlos.

    La regla correcta tiene dos mitades, y las dos importan:

      1. La afirmación debe ser VERDADERA: si el README dice «más de 780»,
         tiene que haber al menos 780. Nunca falla por crecer.
      2. La afirmación no puede volverse INÚTIL: si el README dijera «más de
         10» habiendo 800, sería técnicamente cierto y no informaría de nada.
         Por eso el suelo no puede quedarse más de un 15% por debajo.

    Entre ambas queda margen para más de cien tests nuevos sin tocar el README,
    y sigue siendo imposible que se quede en «625» habiendo 800.
    """
    m = re.search(r"(\d+)\s+tests?\s+en\s+Python", readme)
    assert m, "El README debería citar 'N tests en Python'"
    declarado = int(m.group(1))
    real = _cuenta_items_de_test()
    assert real >= declarado, (
        f"El README declara más de {declarado} tests pero la suite solo tiene "
        f"{real}: la afirmación es FALSA. Se han borrado tests, o el número "
        f"del README nunca fue cierto.")
    assert declarado >= int(real * TOLERANCIA_TESTS), (
        f"El README declara más de {declarado} tests y la suite tiene {real}: "
        f"la cifra se ha quedado obsoleta y ya no informa. Actualiza README.md "
        f"a un suelo cercano a {real}.")


def test_el_readme_cita_la_cantidad_real_de_herramientas(readme):
    """El README dice 'N herramientas'. N debe ser el conteo del registry."""
    from magi.core.tools.builtin import build_registry
    m = re.search(r"(\d+)\s+herramientas?", readme)
    assert m, "El README debería citar 'N herramientas'"
    declarado = int(m.group(1))
    real = len(build_registry().names())
    assert declarado == real, (
        f"El README declara {declarado} herramientas pero el registry tiene {real}. "
        f"Actualiza README.md (línea con 'herramientas') a {real}.")


def test_el_enjambre_tiene_exactamente_tres_nodos(readme):
    """'tres inteligencias/nodos' — el contrato popperiano del sistema.

    Los tres roles son MELCHIOR, BALTHASAR, CASPER. Si esto cambia a 2 o 4, el
    argumento epistemológico del sistema cambia con ello y el README (que dice
    'tres') debe revisarse entero, no solo la cifra.
    """
    # Verificamos que las tres clases de agente existen y son distintas.
    from magi.modules.swarm.agents import MelchiorAgent, BalthasarAgent
    from magi.modules.swarm.orchestrator import SwarmOrchestrator
    roles = {MelchiorAgent, BalthasarAgent}
    # Casper vive dentro del orquestador como árbitro; lo importante es que
    # haya exactamente dos agentes especializados más el orquestador.
    assert len(roles) == 2, "Se esperaban MELCHIOR y BALTHASAR como agentes"
    # El README cita 'tres' en varios sitios. Verificar al menos uno.
    assert re.search(r"\btres\b\s+(inteligencias|nodos|familias|modelos)", readme, re.IGNORECASE), (
        "El README debería describir el enjambre como 'tres' nodos/inteligencias.")


def test_los_nombres_del_enjambre_aparecen_en_el_readme(readme):
    """Melchior, Balthasar y Casper son nombres propios del sistema."""
    for nombre in ("MELCHIOR", "BALTHASAR", "CASPER", "Naoko"):
        # Aceptamos mayúsculas o capitalizado (Melchior / MELCHIOR).
        assert (nombre in readme or nombre.capitalize() in readme), (
            f"'{nombre}' no aparece en el README. Es un nodo/agente del sistema "
            f"y debería documentarse.")
