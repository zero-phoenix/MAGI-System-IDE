"""
Parches de compatibilidad con g4f aguas arriba.

QUÉ RESUELVE, Y POR QUÉ IMPORTA MÁS DE LO QUE PARECE
====================================================
Durante días el plan de este sistema dio por hecho que la familia `claude`
estaba fuera de alcance. El catálogo lo decía así:

    "Claude":  "exige el paquete browser_cookie3 y cookies de un navegador"
    "LMArena": "exige fichero de autenticación y nodriver"

Y de ahí salió medio módulo `sesion_web.py`: cosechar cookies con un Firefox
endurecido sin ventana, importarlas de un fichero, un permiso con caducidad…
Todo correcto, todo bien probado, y todo apuntando al sitio equivocado — porque
esos dos proveedores no piden una SESIÓN, piden TU CUENTA, y la regla del
proyecto es que aquí no se inicia sesión en ningún sitio.

Resulta que **Claude ya estaba disponible sin nada de eso**. `Perplexity`
—`working=True`, `needs_auth=False`, ya en el catálogo— sirve
`claude45sonnet`, `claude40opus` y `claude37sonnetthinking`. No hacía falta
ninguna cookie. Hacía falta mirar la lista de modelos de los proveedores que ya
funcionaban.

Lo que impedía usarlo era un fallo de g4f de dos líneas:

    L384    if 'thread_title' in json_data:
    L384+       conversation.thread_title = json_data['thread_title']
    ...
    L448    yield Sources([{"name": f"Perplexity - {conversation.thread_title}", ...

El atributo se asigna SOLO si el servidor manda ese campo, y hoy no lo manda.
La línea 448 lo lee siempre. Resultado medido:

    AttributeError: 'JsonConversation' object has no attribute 'thread_title'

Y el detalle que lo hace caro: **la respuesta ya había llegado entera**. El
proveedor contesta en ~4 s, y se pierde todo al adjuntar la metadata de las
fuentes, al final. Desde fuera se ve como «Perplexity está roto», que es
justo lo que el catálogo NO decía —lo tenía como `verificada: True`— porque se
midió el 6 de agosto, antes de que esto se rompiera.

CÓMO SE ARREGLA
===============
Valores por defecto A NIVEL DE CLASE en `JsonConversation`. No se toca el
código de g4f, no se pisa nada: si el servidor manda `thread_title`, la
instancia lo asigna encima y gana, como siempre. Solo actúa cuando el atributo
no existiría, que es exactamente el caso que revienta.

Medido después del parche, con el mismo prompt canario:

    claude45sonnet      5768 ms   OK
    claude40opus        3838 ms   OK
    auto                4972 ms   OK

POR QUÉ NO SE APLICA AL IMPORTAR
================================
Misma razón que `compat_curl`: importar g4f en el arranque lo hace más lento
para todo el mundo, incluido quien nunca llega a pedir una respuesta.
`test_arranque_ligero` lo prohíbe, y con razón. Se aplica desde
`_disable_g4f_browser()`, que corre cuando ya se va a usar g4f de verdad.

LA LECCIÓN, QUE ES LA PARTE ÚTIL
================================
«Roto» y «no lo hemos mirado bien» se parecen mucho desde fuera. Antes de
construir infraestructura para sortear un muro, conviene comprobar que el muro
existe: aquí había una puerta abierta a la vuelta de la esquina, y el coste de
no mirarla fue un módulo entero apuntando a un problema que no era el problema.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

__all__ = ["aplicar", "esta_aplicado", "ATRIBUTOS_POR_DEFECTO"]

#: Atributos que `Perplexity.py` lee sin haberlos asignado, con el valor neutro
#: que toca. Cadena vacía y no `None`: se interpolan en un f-string para el
#: nombre de la fuente, y un `None` ahí escribiría literalmente «None».
ATRIBUTOS_POR_DEFECTO: dict[str, str] = {
    "thread_title": "",
    "thread_url_slug": "",
}


def esta_aplicado() -> bool:
    """¿Están ya puestos los valores por defecto? Para el `self_test` y el panel."""
    try:
        from g4f.providers.response import JsonConversation
    except Exception:
        return False
    return all(hasattr(JsonConversation, k) for k in ATRIBUTOS_POR_DEFECTO)


def aplicar() -> bool:
    """
    Pone los valores por defecto. Idempotente y sin efecto si g4f no está.

    Devuelve si quedó aplicado, para que quien llame pueda registrarlo en vez
    de suponerlo.
    """
    try:
        from g4f.providers.response import JsonConversation
    except Exception as e:                      # g4f ausente o reorganizado
        logger.debug("compat_g4f: no se pudo importar JsonConversation (%s)", e)
        return False

    for nombre, valor in ATRIBUTOS_POR_DEFECTO.items():
        # `hasattr` y no `in __dict__`: si una versión futura de g4f ya define
        # el atributo —con el valor que sea— este parche sobra y no debe
        # pisarlo. El objetivo es que no falte, no que valga esto.
        if not hasattr(JsonConversation, nombre):
            setattr(JsonConversation, nombre, valor)

    return esta_aplicado()
