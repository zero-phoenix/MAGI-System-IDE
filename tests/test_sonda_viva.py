"""La sonda no puede volver a morir en silencio (regresión del 2026-08-16).

`Kernel._refrescar_sonda` importaba `get_registry` de
`magi.core.providers.registry`, pero vive en `magi.core.providers.cloud`.
El `except Exception` protector se tragaba el ImportError y la sonda NO se
ejecutaba nunca: el reparto del enjambre obedecía al catálogo escrito a mano
para siempre, y ningún test lo notó porque la sonda «no falla, no está».

Un mecanismo protector cuyo alcance es tan amplio convierte cualquier fallo
tonto en una función desactivada. Este fichero es la vacuna: comprueba que
cada import que hace la sonda existe de verdad, sin ejecutarla.
"""
from __future__ import annotations

import importlib
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
KERNEL = RAIZ / "magi" / "core" / "kernel.py"


def _imports_del_fuente():
    """Los módulos que kernel.py importa DENTRO de _refrescar_sonda."""
    src = KERNEL.read_text(encoding="utf-8")
    ini = src.index("async def _refrescar_sonda")
    fin = src.index("\n    async def ", ini + 10)  # siguiente método
    cuerpo = src[ini:fin]
    return [ln.strip() for ln in cuerpo.splitlines()
            if ln.strip().startswith(("from ", "import "))]


def test_la_sonda_importa_modulos_que_existen():
    """Cada import de la sonda debe resolver. Si no, está muerta en silencio."""
    imports = _imports_del_fuente()
    assert imports, "no se encontró _refrescar_sonda o no tiene imports"
    for linea in imports:
        try:
            if linea.startswith("from "):
                modulo = linea.split()[1]
                importlib.import_module(modulo)
            else:
                importlib.import_module(linea.split()[1])
        except ImportError as e:                       # pragma: no cover
            raise AssertionError(
                f"La sonda está muerta: `{linea}` no resuelve ({e}). "
                f"El except del arranque se lo tragaba y nadie lo vería."
            ) from e


def test_la_sonda_esta_cableada_al_arranque():
    """Debe existir la tarea que la lanza, o está construida y desconectada."""
    src = KERNEL.read_text(encoding="utf-8")
    assert "_tarea_sonda = asyncio.create_task" in src, (
        "la sonda existe pero nadie la arranca: construida y sin llamar, "
        "que es justo lo que el trinquete de huérfanos existe para impedir"
    )


def test_get_registry_vive_donde_se_importa():
    """El bug concreto: importarlo del módulo equivocado no da error visible."""
    import magi.core.providers.registry as reg
    from magi.core.providers.cloud import get_registry  # noqa: F401

    assert not hasattr(reg, "get_registry"), (
        "get_registry apareció en providers.registry: si se movió de sitio, "
        "actualizar también el test de la sonda y el import de kernel.py"
    )
