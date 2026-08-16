"""
Registro de auditoría firmado y encadenado.

POR QUÉ AQUÍ HACE MÁS FALTA QUE EN OTROS SITIOS
===============================================
NAOKO no solo observa: **escribe**. `naoko.py` tiene `_apply_patch()`,
`_git_push()` y `execute_improvement()`. Es decir, un agente con permiso para
modificar el repositorio del usuario y publicar los cambios.

Un agente así sin registro a prueba de manipulación es un riesgo que no
compensa. Y no basta un `.log`: un fichero de texto se edita, se trunca o se
borra sin que nadie lo note — precisamente cuando más importaría notarlo.

CÓMO LO HACE CLAUDE CODE
========================
`audit.jsonl` en el directorio de sesión: 3.808 eventos en mi sesión con este
usuario, cada línea con `_audit_timestamp` y `_audit_hmac`, y una clave en
`.audit-key` al lado. Solo-añadir y verificable.

QUÉ APORTA EL ENCADENADO
========================
Firmar cada línea por separado detecta que una línea CAMBIÓ. Encadenar —meter
la firma anterior en el cálculo de la siguiente— detecta además que una línea
DESAPARECIÓ o que se reordenaron, que es la forma cómoda de esconder algo.

LO QUE ESTO NO ES
=================
No es seguridad contra un atacante con acceso al disco: la clave está en la
misma máquina, y quien pueda leerla puede reescribir la cadena entera. Es
detección de manipulación accidental o descuidada, y una traza fiable de qué
tocó NAOKO y cuándo. Decir más sería vendérselo al usuario como algo que no es.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

NOMBRE = "auditoria.jsonl"
CLAVE = ".auditoria-key"
_GENESIS = "0" * 64


class Auditoria:
    """Diario solo-añadir con cadena HMAC."""

    def __init__(self, raiz: Path | None = None):
        if raiz is None:
            from magi.core.paths import data_dir
            raiz = Path(data_dir())
        self.raiz = Path(raiz)
        self.raiz.mkdir(parents=True, exist_ok=True)
        self.diario = self.raiz / NOMBRE
        self._lock = threading.Lock()
        self._clave = self._cargar_clave()

    def _cargar_clave(self) -> bytes:
        p = self.raiz / CLAVE
        if p.exists():
            try:
                return p.read_bytes().strip()
            except Exception as e:                       # pragma: no cover
                logger.warning("[auditoria] clave ilegible (%s); genero otra", e)
        clave = secrets.token_hex(32).encode()
        p.write_bytes(clave)
        try:
            # En Windows los permisos POSIX no aplican, pero en Linux/macOS sí
            # y no cuesta nada pedirlos.
            os.chmod(p, 0o600)
        except Exception:
            pass
        logger.info("[auditoria] clave nueva en %s", p)
        return clave

    def _firma(self, anterior: str, cuerpo: str) -> str:
        return hmac.new(self._clave, (anterior + cuerpo).encode("utf-8"),
                        hashlib.sha256).hexdigest()

    def _ultima_firma(self) -> str:
        try:
            if not self.diario.exists():
                return _GENESIS
            ultima = None
            with self.diario.open(encoding="utf-8", errors="replace") as f:
                for linea in f:
                    if linea.strip():
                        ultima = linea
            if not ultima:
                return _GENESIS
            return json.loads(ultima).get("firma", _GENESIS)
        except Exception:                                # pragma: no cover
            return _GENESIS


    def registrar(self, accion: str, *, actor: str = "NAOKO",
                  detalle: str = "", **datos: Any) -> dict:
        """
        Añade una entrada. NUNCA lanza.

        Si auditar pudiera reventar la acción auditada, el primer incidente de
        verdad —disco lleno, fichero bloqueado— tumbaría justo lo que se quiere
        proteger. Se registra el fallo y se sigue.
        """
        entrada = {
            "ts": time.time(),
            "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "actor": actor,
            "accion": accion,
            "detalle": str(detalle)[:4000],
            **{k: (v if isinstance(v, (str, int, float, bool, type(None)))
                   else str(v)[:500]) for k, v in datos.items()},
        }
        try:
            with self._lock:
                anterior = self._ultima_firma()
                cuerpo = json.dumps(entrada, ensure_ascii=False,
                                    sort_keys=True, default=str)
                entrada["anterior"] = anterior
                entrada["firma"] = self._firma(anterior, cuerpo)
                with self.diario.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(entrada, ensure_ascii=False,
                                       default=str) + "\n")
        except Exception as e:                           # pragma: no cover
            logger.warning("[auditoria] no se pudo registrar %s: %s", accion, e)
        return entrada

    # ------------------------------------------------------------ lectura

    def entradas(self, limite: int | None = 100) -> list[dict]:
        try:
            if not self.diario.exists():
                return []
            filas = []
            with self.diario.open(encoding="utf-8", errors="replace") as f:
                for linea in f:
                    if linea.strip():
                        try:
                            filas.append(json.loads(linea))
                        except Exception:
                            filas.append({"_ilegible": linea[:200]})
            return filas[-limite:] if limite else filas
        except Exception:                                # pragma: no cover
            return []


    def verificar(self) -> dict:
        """
        Recorre la cadena y dice si cuadra, y desde qué línea deja de cuadrar.

        Devuelve el número de la PRIMERA línea rota: da igual cuántas fallen
        después, porque a partir de ahí todas fallan por arrastre. Lo útil es
        dónde empezó.
        """
        if not self.diario.exists():
            return {"ok": True, "entradas": 0, "intacta": True,
                    "nota": "sin diario todavía"}

        anterior = _GENESIS
        n = 0
        rota_en = None
        try:
            with self.diario.open(encoding="utf-8", errors="replace") as f:
                for i, linea in enumerate(f, 1):
                    if not linea.strip():
                        continue
                    n += 1
                    try:
                        d = json.loads(linea)
                    except Exception:
                        rota_en = rota_en or i
                        break

                    firma = d.pop("firma", "")
                    d.pop("anterior", None)
                    cuerpo = json.dumps(d, ensure_ascii=False, sort_keys=True,
                                        default=str)
                    if not hmac.compare_digest(self._firma(anterior, cuerpo),
                                               firma):
                        rota_en = rota_en or i
                        break
                    anterior = firma
        except Exception as e:                           # pragma: no cover
            return {"ok": False, "error": str(e)}

        return {"ok": rota_en is None, "entradas": n, "intacta": rota_en is None,
                "rota_en_linea": rota_en,
                "nota": ("la cadena cuadra de principio a fin" if rota_en is None
                         else f"alterada o incompleta a partir de la línea {rota_en}")}


_singleton: Auditoria | None = None
_singleton_lock = threading.Lock()


def auditoria() -> Auditoria:
    global _singleton
    if _singleton is None:
        with _singleton_lock:
            if _singleton is None:
                _singleton = Auditoria()
    return _singleton


def registrar(accion: str, **kw) -> dict:
    """Atajo. Que auditar cueste una línea es parte de que se use."""
    try:
        return auditoria().registrar(accion, **kw)
    except Exception as e:                               # pragma: no cover
        logger.warning("[auditoria] %s no registrada: %s", accion, e)
        return {}
