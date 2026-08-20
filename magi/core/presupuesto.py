"""
Presupuesto por tarea: el freno que el log del 16-ago demostró que faltaba.

UNA PETICIÓN REAL, MEDIDA
=========================
«crea un juego de tetris en un unico ejecutable exe portable» quemó ~50
llamadas HTTP a proveedores gratuitos (18 gpt + 14 gemini + 18 command, casi
todas a 8-9 s). Sin presupuesto, una tarea puede gastar cuota sin límite: el
bucle de re-verificación de Melchior regeneraba las 3 variantes enteras una y
otra vez, y el hedge multiplicaba por 3 cada llamada lógica.

QUÉ PONE TECHO, Y DÓNDE
=======================
- `llamadas`: llamadas LÓGICAS de modelo por tarea. Cada `_ask` o iteración de
  `_ask_with_tools` de un agente suma una. Es lo que el orquestador consulta
  antes de cada paso.
- `pared_s`: tiempo de pared desde que la tarea empieza a trabajar. Un
  proveedor que tarda 24 s no puede secuestrar la tarea para siempre.
- `rebuilds`: cuántas veces Melchior puede regenerar TODAS sus variantes
  porque la verificación las rechazó. El log mostró 6 ciclos seguidos; con 2,
  la mejor variante se debate igual y se dice que no verificó.

Los valores viven en `PERFILES`. `factory.yaml` (`presupuesto:`) puede
sobrescribirlos sin tocar código; `cargar()` es tolerante: si el YAML no está,
se usan los valores por defecto.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Presupuesto:
    llamadas: int
    pared_s: float
    rebuilds: int


#: Por defecto del proyecto. `fast` es el perfil frugal: pocas llamadas, poca
#: pared, pocos rebuilds. `deep` conserva más margen para el debate.
_PERFILES: dict[str, Presupuesto] = {
    "fast": Presupuesto(llamadas=18, pared_s=150.0, rebuilds=2),
    "deep": Presupuesto(llamadas=40, pared_s=480.0, rebuilds=3),
}

_cargado = False
#: Perfiles ajustados por `activar()` DESPUÉS de que `cargar()` leyera el YAML
#: (o antes). El YAML es la fábrica; un ajuste explícito —prueba u operación— le
#: gana: si no, `cargar()` sobrescribiría un techo puesto a mano con otro
#: leído del disco, y la prueba que fija 3 llamadas se encontraría con 18.
_ajustados: set[str] = set()


def activar(profiles: dict[str, dict]) -> None:
    """Overrides para pruebas y operación. Solo se tocan perfiles conocidos."""
    for k, raw in (profiles or {}).items():
        if k not in _PERFILES or not isinstance(raw, dict):
            continue
        base = _PERFILES[k]
        _PERFILES[k] = Presupuesto(
            llamadas=int(raw.get("llamadas", base.llamadas)),
            pared_s=float(raw.get("pared_s", base.pared_s)),
            rebuilds=int(raw.get("rebuilds", base.rebuilds)),
        )
        _ajustados.add(k)
        logger.info("[presupuesto] perfil %s ajustado: %d llamadas, "
                    "%.0fs de pared, %d rebuilds",
                    k, _PERFILES[k].llamadas, _PERFILES[k].pared_s,
                    _PERFILES[k].rebuilds)


def cargar() -> None:
    """
    Aplica `presupuesto:` de magi/config/factory.yaml, una vez.

    No lanza nunca: si no hay YAML, si falta la sección o si el fichero no se
    puede leer, los perfiles por defecto ya están en pie.
    """
    global _cargado
    if _cargado:
        return
    _cargado = True
    try:
        from pathlib import Path

        import yaml

        from .paths import project_root
        f = Path(project_root()) / "magi" / "config" / "factory.yaml"
        if not f.exists():
            return
        raw = yaml.safe_load(
            f.read_text(encoding="utf-8", errors="replace")) or {}
        p = raw.get("presupuesto")
        if isinstance(p, dict):
            ajustados = {k: v for k, v in p.items() if k not in _ajustados}
            if ajustados:
                activar(ajustados)
    except Exception as e:
        logger.debug("[presupuesto] factory.yaml no aplicado: %s", e)


def para(engine: str | None) -> Presupuesto:
    """El presupuesto del motor pedido. Motores extraños caen a `fast`."""
    cargar()
    return _PERFILES.get(engine or "fast", _PERFILES["fast"])
