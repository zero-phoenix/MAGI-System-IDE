"""
Un fallo que se disfraza de éxito no se detecta nunca.

EL CASO REAL
============
Medido el 2026-08-13. Tras unas veinte peticiones seguidas, `Perplexity`
—el proveedor asignado a BALTHASAR, el que sirve los modelos Claude— empezó a
devolver esto para CUALQUIER modelo y cualquier pregunta:

    claude45sonnet   7918 ms   len=4   'tud.'
    gpt5             7831 ms   len=4   'tud.'

Es el final de una frase. Ese proveedor manda la respuesta en parches JSON y
g4f solo acumula los que vienen en un campo concreto; cuando el formato cambia
—o cuando limitan la cuenta— llega el último trozo y nada más.

LO GRAVE NO ERA ESO
===================
El fallo de g4f es de g4f. Lo que hacía MAGI con él sí es nuestro: lo daba por
bueno. `'tud.'` habría llegado a la interfaz como la antítesis de BALTHASAR,
con su latencia medida, su nombre de proveedor y todo el aspecto de una
respuesta legítima. El circuit breaker no se habría enterado, la sonda lo
habría contado como éxito y el usuario habría visto un debate con una réplica
de cuatro letras.

Los proveedores gratuitos fallan; eso se asume. Lo que no se puede asumir es
que fallen EN SILENCIO.
"""
from __future__ import annotations

import pytest

from magi.core.providers.backends.g4f_backend import (
    MINIMO_UTIL, _por_que_es_inservible,
)


@pytest.mark.parametrize("basura", [
    "tud.",              # el caso real, literal
    "",
    "   \n  ",
    ".",
    "...",
    "a",
])
def test_lo_que_no_es_una_respuesta_se_rechaza(basura):
    motivo = _por_que_es_inservible(basura)
    assert motivo, f"{basura!r} debería rechazarse"


def test_el_motivo_dice_QUE_llego_no_solo_que_esta_mal():
    """
    El motivo acaba en el log y en el error de «familia agotada». Un booleano
    obliga a reproducir el fallo para saber qué pasó; el texto lo cuenta.
    """
    motivo = _por_que_es_inservible("tud.")
    assert "4 caracteres" in motivo
    assert "tud." in motivo


def test_None_no_revienta():
    """
    Un proveedor puede devolver None. Si esta función explota ahí, el fallo se
    convierte en una excepción distinta y más confusa justo en el punto donde
    se estaba intentando dar un diagnóstico claro.
    """
    assert _por_que_es_inservible(None) is not None


@pytest.mark.parametrize("valida", [
    "Sí, es correcto.",
    "APROBADO sin objeciones.",
    "El mutex garantiza exclusión mutua; el semáforo lleva un contador.",
    "```python\nprint('hola')\n```",
])
def test_las_respuestas_cortas_pero_LEGITIMAS_pasan(valida):
    """
    La comprobación caza el fallo evidente; no juzga la calidad. Este sistema
    produce respuestas cortas de verdad —una aprobación de CASPER, un «sí»— y
    rechazarlas costaría una llamada de red y un log confuso.
    """
    assert _por_que_es_inservible(valida) is None


def test_el_umbral_esta_entre_el_fallo_medido_y_una_respuesta_util():
    """
    El número no es de gusto: por debajo tiene que quedar el caso medido (4
    caracteres) y por encima las respuestas cortas que el sistema sí emite.
    Un umbral alto convertiría este guardián en un censor.
    """
    assert MINIMO_UTIL > len("tud."), "no cazaría el caso que lo motivó"
    assert MINIMO_UTIL <= 20, "por encima empieza a rechazar respuestas válidas"


def test_esta_conectado_donde_importa():
    """
    Que la función exista no sirve de nada si `complete()` no la llama. Se lee
    el fuente: llamar de verdad exigiría un proveedor real y este test dejaría
    de hablar del código para hablar de la red.
    """
    import ast
    import inspect
    import textwrap

    from magi.core.providers.backends import g4f_backend

    # `textwrap.dedent` no es adorno: `inspect.getsource` de un método devuelve
    # el fuente CON su indentación de clase, y `ast.parse` lo rechaza con
    # «IndentationError: unexpected indent». Es el fallo que da este test la
    # primera vez que se escribe, siempre.
    fuente = textwrap.dedent(inspect.getsource(g4f_backend.G4FProvider.complete))
    arbol = ast.parse(fuente)
    llamadas = [n for n in ast.walk(arbol)
                if isinstance(n, ast.Call)
                and getattr(n.func, "id", "") == "_por_que_es_inservible"]
    assert llamadas, (
        "complete() no comprueba la respuesta: el guardián está escrito pero "
        "desconectado, que es la peor de las dos opciones porque parece puesto")
