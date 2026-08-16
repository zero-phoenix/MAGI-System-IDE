"""
Catálogo de proveedores: datos versionados, no constantes de Python.

EL PROBLEMA
===========
`FAMILY_SPECS`, `ROTOS`, `VERIFIED_FAMILIES`, `HEDGE_AFTER_S` y
`DEFAULT_SWARM_FAMILIES` vivían como literales dentro de
`backends/g4f_backend.py`. Son datos, no lógica, y cambian constantemente:
estos proveedores son gratuitos y se caen, resucitan, empiezan a pedir captcha
o cambian de modelo cada pocas semanas.

Consecuencia medida: **arreglar un proveedor caído obligaba a recompilar 158 MB
de ejecutable**. Con PyInstaller eso son unos 40 minutos y una descarga para el
usuario, por cambiar una línea de una tabla.

DE DÓNDE SALE LA IDEA
=====================
Zcode Desktop declara sus proveedores en
`resources/model-providers/models_catalog_*.json`, con `schemaVersion` y, por
modelo, `contextWindow`, `maxOutputTokens`, `modalities` y los niveles de
razonamiento mapeados a cada protocolo. Cero de eso está en su código.

QUÉ SE CONSERVA
===============
Todo. Las constantes de Python siguen ahí y actúan de RESPALDO: si el JSON
falta, no valida o trae una versión de esquema que este código no entiende, se
usan ellas y el sistema arranca igual. Un catálogo corrupto no puede dejar a
nadie sin aplicación.

DÓNDE SE BUSCA (gana el primero)
================================
1. `%LOCALAPPDATA%\\MagiSystem\\catalogo_proveedores.json` — el del usuario.
   Editable sin recompilar nada. ESTE es el objetivo del cambio.
2. `magi/data/catalogo_proveedores.json` — el que viaja dentro del .exe.
3. Las constantes de Python.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

#: Versión de esquema que este código sabe leer. Si el fichero trae una mayor,
#: es de una versión de MAGI más nueva: se ignora y se avisa, en vez de
#: interpretarlo mal en silencio.
ESQUEMA_SOPORTADO = 1

NOMBRE = "catalogo_proveedores.json"


def _ruta_usuario() -> Path | None:
    try:
        from magi.core.paths import data_dir
        return Path(data_dir()) / NOMBRE
    except Exception:
        import os
        base = os.environ.get("LOCALAPPDATA")
        return Path(base) / "MagiSystem" / NOMBRE if base else None


def _ruta_empaquetada() -> Path:
    """
    El que viaja dentro del ejecutable.

    Bajo PyInstaller los datos se extraen a `sys._MEIPASS`, así que la ruta
    relativa al módulo sigue funcionando: `magi/data/` va declarado en el
    `.spec`. Si no estuviera, `existe()` da False y se cae al respaldo, que es
    el comportamiento correcto.
    """
    return Path(__file__).resolve().parent.parent.parent / "data" / NOMBRE


def rutas() -> list[Path]:
    salida = []
    u = _ruta_usuario()
    if u is not None:
        salida.append(u)
    salida.append(_ruta_empaquetada())
    return salida


def _valida(d: Any) -> bool:
    """
    Comprobación mínima pero real.

    No es un validador de esquema completo: es lo justo para que un fichero
    truncado, con la versión cambiada o sin familias NO llegue a sustituir a
    unos valores que sí funcionan.
    """
    if not isinstance(d, dict):
        return False
    v = d.get("schemaVersion")
    if v != ESQUEMA_SOPORTADO:
        logger.warning("[catalogo] schemaVersion %r; este MAGI lee %d. "
                       "Se ignora el fichero.", v, ESQUEMA_SOPORTADO)
        return False
    fams = d.get("familias")
    if not isinstance(fams, dict) or not fams:
        logger.warning("[catalogo] sin familias utilizables; se ignora")
        return False
    for nombre, f in fams.items():
        if not isinstance(f, dict) or not isinstance(f.get("candidatos"), list):
            logger.warning("[catalogo] familia %r mal formada; se ignora "
                           "el fichero entero", nombre)
            return False
    return True


def cargar_bruto() -> tuple[dict | None, Path | None]:
    """Devuelve el primer catálogo válido y de dónde salió."""
    for p in rutas():
        try:
            if not p.exists():
                continue
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("[catalogo] %s ilegible (%s); sigo buscando", p, e)
            continue
        if _valida(d):
            return d, p
    return None, None


class Catalogo:
    """
    Vista del catálogo con la misma forma que tenían las constantes.

    Deliberado: `g4f_backend` sigue viendo `FAMILY_SPECS` como el mismo dict de
    listas de tuplas que antes. Externalizar los datos no debe obligar a
    reescribir a quien los consume.
    """

    def __init__(self, datos: dict, origen: Path | None, respaldo: bool = False):
        self.datos = datos
        self.origen = origen
        self.es_respaldo = respaldo

    # -- forma antigua, para que nada de lo que ya funciona tenga que cambiar

    @property
    def family_specs(self) -> dict[str, list[tuple]]:
        return {
            nombre: [(c.get("proveedor"), c.get("modelo"))
                     for c in f.get("candidatos", [])]
            for nombre, f in self.datos["familias"].items()
        }

    @property
    def verificadas(self) -> tuple[str, ...]:
        return tuple(n for n, f in self.datos["familias"].items()
                     if f.get("verificada"))

    @property
    def rotos(self) -> dict[str, str]:
        return dict(self.datos.get("rotos", {}))

    @property
    def hedge_tras_s(self) -> float:
        return float(self.datos.get("hedge", {}).get("tras_segundos", 4.0))

    @property
    def hedge_max(self) -> int:
        return int(self.datos.get("hedge", {}).get("maximo", 2))

    @property
    def reparto(self) -> dict[str, str]:
        return dict(self.datos.get("reparto_enjambre", {}))


    # -- lo que ANTES no existía en ninguna parte

    @property
    def ventana_contexto(self) -> int:
        """
        Tope de caracteres del prompt.

        MAGI no comprobaba NINGUNO. Monta prompts largos —orden del usuario,
        memoria episódica, estado del enjambre, evidencia de ejecución— y los
        manda. Cuando no caben, el proveedor devuelve un error que el código
        interpreta como «proveedor roto» y rota al siguiente… que falla por lo
        mismo, porque el prompt sigue sin caber. Se recorre la familia entera
        para acabar reportándola como agotada.

        Zcode declara `contextWindow` por modelo. Aquí no se puede copiar el
        dato: estos proveedores gratuitos no publican el suyo, y ponerlo a ojo
        sería inventárselo. Lo que sí se puede es tener un tope conservador
        configurable — que es infinitamente mejor que ninguno.
        """
        return int(self.datos.get("limites", {})
                   .get("ventana_contexto_caracteres", 120_000))

    def cabe(self, texto: str) -> bool:
        return len(texto) <= self.ventana_contexto

    def latencia_declarada(self, proveedor: str, modelo: str | None) -> int | None:
        """Latencia medida en la verificación, si la hay. Para ordenar en frío."""
        for f in self.datos["familias"].values():
            for c in f.get("candidatos", []):
                if c.get("proveedor") == proveedor and c.get("modelo") == modelo:
                    return c.get("latencia_medida_ms")
        return None

    def informe(self) -> dict:
        """Para la pestaña Configuración: de dónde salieron estos datos."""
        return {
            "origen": str(self.origen) if self.origen else "constantes del código",
            "es_respaldo": self.es_respaldo,
            "esquema": self.datos.get("schemaVersion"),
            "generado": self.datos.get("generado"),
            "familias": len(self.datos.get("familias", {})),
            "verificadas": list(self.verificadas),
            "rotos": len(self.rotos),
            # Degradación honesta: un número no dice nada accionable. Los
            # IMPOSIBLES (exigen TU cuenta o abren navegador: no vuelven)
            # separados de los CAÍDOS (429/403/captcha: pueden volver), con
            # su motivo, para que el panel pueda decir «no disponible —
            # requiere tu cuenta» en vez de un «sin verificar» que suena a
            # trabajo pendiente que nadie va a hacer.
            "rotos_imposibles": sorted(
                p for p, motivo in self.rotos.items()
                if "tu cuenta" in motivo or "navegador" in motivo),
            "rotos_caidos": sorted(
                p for p, motivo in self.rotos.items()
                if "tu cuenta" not in motivo and "navegador" not in motivo),
            "rotos_motivos": dict(self.rotos),
            "ventana_contexto_caracteres": self.ventana_contexto,
            "editable_en": str(_ruta_usuario()) if _ruta_usuario() else None,
        }


def _desde_respaldo() -> Catalogo:
    """
    Reconstruye el catálogo desde las constantes de Python.

    Se importa dentro de la función a propósito: `g4f_backend` importa este
    módulo, así que hacerlo arriba sería un ciclo.
    """
    from magi.core.providers.backends import g4f_backend as g

    datos = {
        "schemaVersion": ESQUEMA_SOPORTADO,
        "generado": "constantes del código",
        "limites": {"ventana_contexto_caracteres": 120_000},
        "hedge": {"tras_segundos": g._HEDGE_AFTER_S_BASE,
                  "maximo": g._HEDGE_MAX_BASE},
        "reparto_enjambre": dict(g._REPARTO_BASE),
        "rotos": dict(g._ROTOS_BASE),
        "familias": {
            fam: {"verificada": fam in g._VERIFICADAS_BASE,
                  "candidatos": [{"proveedor": p, "modelo": m}
                                 for p, m in cands]}
            for fam, cands in g._FAMILY_SPECS_BASE.items()
        },
    }
    return Catalogo(datos, None, respaldo=True)


_cache: Catalogo | None = None


def catalogo(recargar: bool = False) -> Catalogo:
    global _cache
    if _cache is not None and not recargar:
        return _cache
    datos, origen = cargar_bruto()
    if datos is not None:
        _cache = Catalogo(datos, origen)
        logger.info("[catalogo] %d familias desde %s",
                    len(datos["familias"]), origen)
    else:
        _cache = _desde_respaldo()
        logger.info("[catalogo] sin fichero utilizable; uso las constantes "
                    "del codigo (el sistema funciona igual)")
    return _cache
