"""
Casper entrega la solución, no una recomendación de que alguien la haga.

LOS DOS CORSÉS QUE SE LE QUITAN
===============================
Casper es **quien te habla**: su síntesis es la respuesta que lees. Y era, con
diferencia, el nodo más maniatado de los tres.

**1. Se le exigía responder en JSON.**

    {"decision": "APPROVED", "feedback": "..."}

Parece ordenado y se pagaba en cada respuesta. Meter un juego de Tetris dentro
de una cadena JSON obliga a escapar comillas y saltos de línea, y los modelos
—con razón— esquivan el problema resumiendo. Por eso lo que llegaba a la
pantalla eran recomendaciones de dos líneas: *«Recomendación: implementar el
enfoque B»*. El usuario recibía un veredicto sobre algo que nadie le había
entregado.

Y cuando el JSON salía mal, la decisión se **adivinaba** buscando las palabras
«APPROVED» o «REJECTED» en cualquier parte del texto. Una crítica que dijera
«esto sería rejected por cualquier revisor» volteaba el veredicto.

**2. Su perfil de herramientas era de solo lectura.**

Podía comprobar, no construir. Pero la síntesis dialéctica no es *elegir* entre
la tesis y la antítesis: es **construir la superación de ambas**. Sin poder
escribir un fichero ni ejecutarlo, lo máximo que podía producir era una
opinión.

Balthasar sigue sin poder escribir —eso es lo que le da autoridad como
crítico—. Casper sí, porque el que decide es también el que responde por lo que
entrega.
"""
from __future__ import annotations

import pytest

from magi.core.tools.builtin import BALTHASAR_DENY, CASPER_TOOLS
from magi.modules.swarm.agents import _leer_decision

TETRIS = '''Mi síntesis integra ambas posiciones.

```python
import pygame
def main():
    print("tetris")   # comillas "dobles" y \\ barras que romperían un JSON
```

### CONCLUSIÓN
Construido y ejecutado. ¿Lo apruebas?

DECISIÓN: APROBADA'''


# ------------------------------------------------------- el veredicto

def test_lee_la_decision_de_la_linea_marcada():
    decision, texto = _leer_decision(TETRIS, round_num=1)
    assert decision == "APPROVED"
    assert "```python" in texto, "el código llega entero al usuario"


def test_necesita_revision_devuelve_a_melchior():
    d, _ = _leer_decision("bla bla\n\nDECISIÓN: NECESITA REVISIÓN", 1)
    assert d == "REJECTED_NEEDS_WORK"


def test_en_la_ultima_ronda_se_entrega_igual():
    """
    Alargar el debate sin fin es peor que entregar algo imperfecto y decir en
    qué lo es. A partir de la ronda 3 no se devuelve a Melchior.
    """
    d, _ = _leer_decision("DECISIÓN: NECESITA REVISIÓN", round_num=3)
    assert d == "APPROVED"


def test_una_mencion_a_medio_texto_no_voltea_el_veredicto():
    """
    El fallo del respaldo antiguo: buscaba la palabra por todo el mensaje.

    Aquí Casper CITA un rechazo anterior y luego aprueba. La decisión válida es
    la del final, que es donde el prompt la pide.
    """
    texto = ("En la ronda anterior la DECISIÓN: NECESITA REVISIÓN se debió a "
             "un fallo de rutas, ya corregido.\n\n"
             "### CONCLUSIÓN\nListo.\n\nDECISIÓN: APROBADA")
    assert _leer_decision(texto, 1)[0] == "APPROVED"


def test_la_palabra_rejected_suelta_ya_no_decide():
    """
    «este enfoque sería rejected por cualquier revisor» no es un veredicto.
    Antes lo era.
    """
    texto = "Melchior avisa de que su enfoque sería rejected por un revisor."
    assert _leer_decision(texto, 1)[0] == "APPROVED"


def test_sin_marcador_se_aprueba_y_no_se_bloquea_la_entrega():
    d, t = _leer_decision("Aquí está la solución, sin línea de decisión.", 1)
    assert d == "APPROVED"
    assert t.startswith("Aquí está")


@pytest.mark.parametrize("texto,esperado", [
    ('{"decision": "APPROVED", "feedback": "vale"}', "APPROVED"),
    ('```json\n{"decision": "REJECTED_NEEDS_WORK", "feedback": "no"}\n```',
     "REJECTED_NEEDS_WORK"),
])
def test_se_sigue_aceptando_el_json_antiguo(texto, esperado):
    """
    Una tarea rehidratada del disco puede venir del prompt anterior. Romperla
    no aportaría nada.
    """
    assert _leer_decision(texto, 1)[0] == esperado


def test_el_json_antiguo_devuelve_su_feedback_y_no_el_json_crudo():
    _, t = _leer_decision('{"decision": "APPROVED", "feedback": "el texto"}', 1)
    assert t == "el texto"


def test_un_texto_vacio_no_revienta_y_TAMPOCO_aprueba():
    """
    Este test cambió de contrato el 2026-08-20, y el motivo importa.

    Antes exigía `APPROVED` para un texto vacío: la idea era «un veredicto
    ausente no puede bloquear la entrega». Suena razonable y resultó ser la
    puerta por la que salieron tres entregas mintiendo: cuando Casper se caía
    por timeout, el texto que llegaba aquí era un mensaje de error sin marcador
    de decisión, caía en este respaldo y el usuario recibía

        **Decisión Técnica:** APPROVED
        [Tiempo de espera agotado tras 150s...]

    No reventar sigue siendo obligatorio. Aprobar, no: sin árbitro el estado es
    `SIN_ARBITRAJE`, y el orquestador entrega igualmente la tesis y la crítica
    (C1/C2). La entrega no se bloquea; lo que se deja de hacer es firmarla.
    """
    assert _leer_decision("", 1)[0] == "SIN_ARBITRAJE"
    assert _leer_decision(None, 1)[0] == "SIN_ARBITRAJE"


# ------------------------------------------------------- las herramientas

def test_casper_puede_construir_y_entregar():
    """
    Sin esto, su «síntesis» solo puede recomendar. Escribir y empaquetar es lo
    que convierte un veredicto en una respuesta.
    """
    for t in ("write_file", "build_project_exe"):
        assert t in CASPER_TOOLS, f"Casper necesita {t} para poder entregar"


def test_casper_conserva_lo_que_le_hace_arbitro():
    """Poder construir no puede costarle poder comprobar."""
    for t in ("run_tests", "read_file", "observe_artifact"):
        assert t in CASPER_TOOLS


def test_balthasar_sigue_sin_poder_escribir():
    """
    Que el crítico no escriba es lo que le da autoridad: una crítica que dice
    «esto falla con entrada vacía» HABIENDO EJECUTADO el caso vale más que una
    que lo sospecha, y quien no puede tocar el código no puede acomodarlo a su
    crítica.
    """
    assert "write" in BALTHASAR_DENY


def test_casper_puede_deshacer_lo_que_escribe():
    """
    Escribir sin poder deshacer sería añadir permisos sin añadir
    reversibilidad, que es justo la mitad que hace aceptable el acceso a la
    máquina.
    """
    assert "undo" in CASPER_TOOLS
