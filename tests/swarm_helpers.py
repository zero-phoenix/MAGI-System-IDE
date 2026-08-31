"""
Infraestructura compartida para correr rondas del enjambre en los tests.

POR QUÉ ESTO EXISTE Y NO VIVE EN UN TEST
========================================
Nació dentro de `test_fase7_abanico.py`, y `test_fase8_replica.py` lo
importaba de allí. El trinquete `test_requirements_cubre_todo_import_duro`
lo cazó y tiene razón: un test que importa a otro test declara una
dependencia que `requirements.txt` no puede satisfacer, y el runner del
release se cae al importarlo — *«sin tests verdes no hay .exe»*.

Un módulo de ayuda no es un test: pytest no lo recolecta, y ambos tests
pueden importarlo sin que ninguno dependa del otro.

QUÉ TRAE
========
Proveedores `EchoProvider` con **guion y retardo**. Los retardos son lo que
se mide: sin ellos no hay espera que solapar y la compuerta de la Fase 7 no
mide nada.
"""
from __future__ import annotations

import asyncio
import tempfile
import time
from pathlib import Path

from magi.core.providers.backends.echo import EchoProvider
from magi.core.providers.backends.g4f_backend import DEFAULT_SWARM_FAMILIES
from magi.core.providers.base import Usage
from magi.core.providers.registry import ProviderRegistry

__all__ = [
    "FAM_MELCHIOR", "FAM_BALTHASAR", "FAM_CASPER",
    "CODIGO_LENTO", "CODIGO_CORTO", "ENCARGO",
    "GuionProvider", "EscalonadoProvider", "montar_registro", "store_aislado",
]

# El reparto real de familias: cada agente prefiere la suya.
FAM_MELCHIOR = DEFAULT_SWARM_FAMILIES["MELCHIOR"]
FAM_BALTHASAR = DEFAULT_SWARM_FAMILIES["BALTHASAR"]
FAM_CASPER = DEFAULT_SWARM_FAMILIES["CASPER"]

#: Código que el verificador ejecuta DE VERDAD: dormir es la forma más
#: predecible de darle trabajo medible (arranca un intérprete real).
CODIGO_LENTO = "```python\nimport time\ntime.sleep(1.5)\nprint('ok')\n```"
CODIGO_CORTO = "```python\nprint('ok')\n```"

ENCARGO = "diseña un parser de ROM"


class GuionProvider(EchoProvider):
    """
    Echo con guion y retardo: mira el prompt, decide qué contestar y cuánto
    tardar. La primera marca que aparezca en el prompt gana.
    """

    def __init__(self, provider_id, family, reglas=(),
                 por_defecto=("ok", 0.0)):
        self.reglas = list(reglas)
        self.por_defecto = por_defecto
        self.vistos: list[str] = []
        super().__init__(provider_id, family)

    def _elegir(self, req) -> tuple[str, float]:
        todo = "\n".join(str(m.content) for m in req.messages)
        self.vistos.append(todo)
        for marca, respuesta, retardo in self.reglas:
            if marca in todo:
                return respuesta, retardo
        return self.por_defecto

    async def complete(self, req):
        started = time.monotonic()
        self._calls += 1
        respuesta, retardo = self._elegir(req)
        if retardo:
            await asyncio.sleep(retardo)
        usage = Usage(prompt_tokens=8, completion_tokens=8)
        return self._mk_response(respuesta, req.model or "guion-1",
                                 started, usage)


class EscalonadoProvider(GuionProvider):
    """
    Cambia de guion a partir de la segunda llamada: sirve para que una
    variante termine pronto (con código lento de verificar) y la otra tarde
    (con código corto). El orden de las llamadas lo fija el `gather`; la
    ganancia de la cascada es simétrica ante el intercambio.
    """

    def __init__(self, *args, primera, siguientes, **kw):
        super().__init__(*args, **kw)
        self._primera = primera
        self._siguientes = siguientes
        self._guion = 0

    def _elegir(self, req):
        self._guion += 1
        self.por_defecto = self._primera if self._guion == 1 \
            else self._siguientes
        return super()._elegir(req)


def montar_registro(melchior, balthasar, casper) -> ProviderRegistry:
    reg = ProviderRegistry()
    for prov in (melchior, balthasar, casper):
        reg.register(prov, priority=10)
    return reg


def store_aislado():
    """
    Un `TaskStore` en directorio temporal, por ronda.

    El de la máquina es compartido y una tarea rehidratada de una corrida
    anterior llegó a interferir: la vieja se quedaba `in_progress` y la nueva
    no arrancaba. Un test de tiempos no puede heredar el estado de lo que
    pasó fuera de él.
    """
    from magi.core.store.state import TaskStore

    return TaskStore(Path(tempfile.mkdtemp()) / "task.db")
