"""
Adaptador de firma para curl_cffi: dos proveedores que no estaban caídos.

EL FALLO
========
El catálogo marcaba `PhindAi` y `Qwen` como rotos, con este motivo:

    PhindAi : BaseSession.__init__() no acepta 'proxy'
    Qwen    : AsyncSession.request() no acepta 'proxy'

No es que el proveedor no responda: es que **g4f llama a curl_cffi con un
argumento que la versión instalada ya no admite**. Medido en la máquina del
usuario, con curl_cffi 0.16.0:

    AsyncSession.__init__  acepta proxy: False
    AsyncSession.request   acepta proxy: True

`proxy` se movió del constructor al método. g4f lo sigue pasando al
constructor, salta `TypeError`, y dos familias enteras quedan enterradas en la
lista de rotos por un argumento de más.

POR QUÉ NO SE ARREGLA FIJANDO LA VERSIÓN
========================================
Sería la solución cómoda y dura poco: `requirements.txt` pide
`curl_cffi==0.5.10` y en esta máquina hay 0.16.0, porque g4f arrastra la suya.
Clavar una versión te deja a merced de la siguiente vez que se mueva un
parámetro, y además el problema volvería con otro nombre.

CÓMO DECIDE QUÉ QUITAR
======================
Leyendo la firma REAL de lo que hay instalado con `inspect.signature`, no con
una lista de nombres escrita a mano. Una lista se queda atrás sola —es el mismo
error que ya costó dos releases con las dependencias del CI enumeradas a mano—
y aquí se quedaría atrás en silencio, que es peor.

Si la firma acepta `**kwargs`, no se toca nada: quien acepta cualquier cosa no
necesita que le filtren.

QUÉ SE PIERDE AL QUITAR `proxy`
===============================
Que no se aplique el proxy. MAGI no configura ninguno —no hay ajuste para
ello y §I.3 no lo contempla—, así que el valor que g4f pasa es `None` en la
práctica. Aun así, cada descarte se registra: quitar un argumento en silencio
es exactamente cómo se pierde una funcionalidad sin que nadie se entere.
"""
from __future__ import annotations

import inspect
import logging

logger = logging.getLogger(__name__)

__all__ = ["aplicar", "filtrar_kwargs", "esta_aplicado"]

#: Marca en la función envuelta, para no envolver dos veces. Aplicar el
#: adaptador dos veces no rompería nada, pero cada capa añade una llamada a
#: `inspect` por cada sesión creada, y esto está en el camino de cada petición.
_MARCA = "_magi_compat_curl"


def nombres_aceptados(cls, metodo: str) -> set[str] | None:
    """
    Argumentos con nombre que `cls.<metodo>` admite, MIRANDO TODA LA HERENCIA.

    POR QUÉ LA HERENCIA ENTERA Y NO SOLO LA CLASE
    =============================================
    Mirar solo la clase hoja fue un fallo real de la primera versión, y lo cazó
    el CI en un runner con otra versión de curl_cffi:

        AsyncSession.__init__   **kwargs=True    proxy=False
        BaseSession.__init__    **kwargs=False   proxy=?

    `AsyncSession` acepta `**kwargs`, así que el filtro concluía «esta firma
    admite cualquier cosa» y no tocaba nada… y el argumento seguía bajando
    hasta `BaseSession`, que es quien lanza el TypeError. En la máquina de
    desarrollo `BaseSession` sí aceptaba `proxy` y por eso pasaba en local:
    el adaptador dependía de la versión instalada, que es justo lo que venía a
    evitar.

    Los kwargs recorren la cadena de herencia, así que la pregunta correcta no
    es «¿los acepta esta clase?» sino «¿los acepta ALGUIEN de la cadena?».

    Devuelve None si no se puede leer ninguna firma: ante la duda, no tocar.
    """
    nombres: set[str] = set()
    leido = False
    for base in getattr(cls, "__mro__", [cls]):
        if base is object:
            # `object.__init__(self, /, *args, **kwargs)` declara **kwargs y no
            # acepta ninguno: contarlo diría que todo vale.
            continue
        fn = base.__dict__.get(metodo)
        if fn is None:
            continue
        fn = getattr(fn, "__wrapped__", fn)
        try:
            nombres |= set(inspect.signature(fn).parameters)
            leido = True
        except (TypeError, ValueError):                   # pragma: no cover
            continue
    return nombres if leido else None


def filtrar_kwargs(func, kwargs: dict, *, donde: str = "",
                   admitidos: set[str] | None = None) -> dict:
    """
    Deja solo los argumentos que `func` admite de verdad.

    Devuelve el diccionario tal cual si la firma acepta `**kwargs` o si no se
    puede leer: ante la duda, no tocar. Filtrar por si acaso podría quitar un
    argumento que sí importaba, y eso sería cambiar un fallo ruidoso —un
    TypeError— por uno silencioso.

    `admitidos` permite pasar el conjunto ya calculado sobre toda la herencia
    (ver `nombres_aceptados`), que es lo que usa el envoltorio.
    """
    if admitidos is None:
        try:
            params = inspect.signature(func).parameters
        except (TypeError, ValueError):
            return kwargs
        if any(p.kind is p.VAR_KEYWORD for p in params.values()):
            return kwargs
        admitidos = set(params)

    sobran = [k for k in kwargs if k not in admitidos]
    if not sobran:
        return kwargs

    logger.debug("[compat_curl] %s no admite %s; se descarta(n)",
                 donde or getattr(func, "__qualname__", "?"), ", ".join(sobran))
    return {k: v for k, v in kwargs.items() if k in admitidos}


def _envolver(cls, nombre: str) -> bool:
    """Envuelve `cls.<nombre>` para que tolere argumentos de más."""
    original = getattr(cls, nombre, None)
    if original is None or getattr(original, _MARCA, False):
        return False

    # Se calcula UNA vez, al envolver, y no en cada llamada: esto está en el
    # camino de cada petición y recorrer el MRO con `inspect` por sesión creada
    # sería pagar el diagnóstico una y otra vez.
    admitidos = nombres_aceptados(cls, nombre)

    def envuelto(self, *args, **kwargs):
        limpios = filtrar_kwargs(original, kwargs,
                                 donde=f"{cls.__name__}.{nombre}",
                                 admitidos=admitidos)
        return original(self, *args, **limpios)

    envuelto.__name__ = getattr(original, "__name__", nombre)
    envuelto.__doc__ = getattr(original, "__doc__", None)
    setattr(envuelto, _MARCA, True)
    setattr(cls, nombre, envuelto)
    return True


def esta_aplicado() -> bool:
    """¿Ya se envolvió? Para el panel y para los tests."""
    try:
        from curl_cffi.requests import AsyncSession
    except Exception:                                     # pragma: no cover
        return False
    return getattr(getattr(AsyncSession, "__init__", None), _MARCA, False)


def aplicar() -> int:
    """
    Aplica el adaptador. Devuelve cuántos métodos se envolvieron.

    Idempotente y silencioso ante la ausencia de curl_cffi: es una dependencia
    de g4f, no del sistema, y no tenerla no puede impedir arrancar.
    """
    try:
        from curl_cffi.requests import AsyncSession, Session
    except Exception as e:
        logger.debug("[compat_curl] curl_cffi no disponible: %s", e)
        return 0

    n = 0
    for cls in (AsyncSession, Session):
        for metodo in ("__init__", "request"):
            if _envolver(cls, metodo):
                n += 1
    if n:
        logger.info("[compat_curl] adaptador de firma aplicado a %d métodos "
                    "de curl_cffi (revive PhindAi y Qwen)", n)
    return n
