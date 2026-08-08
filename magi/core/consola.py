"""
Salida de consola en UTF-8, siempre.

EL FALLO
========
Del registro del usuario, a mitad de una respuesta:

    [MELCHIOR] streaming falló ('charmap' codec can't encode characters in
    position 99-110: character maps to <undefined>); caigo a no-streaming

No había fallado ningún proveedor. Lo que reventó fue ESCRIBIR el texto: en
Windows, `sys.stdout` usa la página de códigos de la consola (cp1252 o cp850),
y cualquier carácter fuera de ese repertorio lanza `UnicodeEncodeError`.

La consecuencia es peor que un log feo. La excepción sube por el bucle de
streaming, lo aborta, y el agente cae al camino sin streaming: se pierde la
respuesta que ya estaba escribiéndose y se vuelve a pedir entera. El usuario ve
una demora larga y una pantalla parada, y nada indica que la causa fue un
acento.

Y este proyecto habla español. Casi cualquier respuesta lleva acentos, eñes o
comillas tipográficas, así que el fallo no era raro: era el caso normal.

LA CORRECCIÓN
=============
Reconfigurar stdout/stderr a UTF-8 con `errors="replace"` en el arranque del
proceso. Dos efectos:

  · UTF-8 cubre todo lo que puede devolver un modelo.
  · `errors="replace"` garantiza que ESCRIBIR NUNCA LANCE. Aunque apareciera
    algo imposible de codificar, saldría un carácter de reemplazo en el log en
    vez de tumbar la inferencia. Un log degradado es un inconveniente; una
    respuesta perdida, no.

Se llama junto al cortafuegos de navegador, en la primera línea ejecutable de
main.py, porque cualquier módulo que escriba antes ya estaría expuesto.
"""
from __future__ import annotations

import io
import logging
import sys

logger = logging.getLogger(__name__)

_hecho = False


def configurar() -> dict:
    """
    Pone stdout y stderr en UTF-8 tolerante. Idempotente.

    Devuelve qué se cambió, para que la pestaña de configuración pueda
    enseñarlo y Naoko pueda comprobarlo.
    """
    global _hecho
    informe: dict[str, str] = {}

    for nombre in ("stdout", "stderr"):
        flujo = getattr(sys, nombre, None)
        if flujo is None:
            informe[nombre] = "no existe (proceso sin consola)"
            continue

        antes = (getattr(flujo, "encoding", None) or "?").lower()
        tolerante = getattr(flujo, "errors", "") in ("replace", "backslashreplace")
        if antes.replace("-", "") == "utf8" and tolerante:
            informe[nombre] = f"ya estaba en {antes}"
            continue

        try:
            # Python 3.7+: la vía limpia, sin envolver el flujo.
            flujo.reconfigure(encoding="utf-8", errors="replace")
            informe[nombre] = f"{antes} -> utf-8"
        except (AttributeError, ValueError, OSError):
            # Sin `reconfigure` (flujo ya envuelto, o un .exe sin consola):
            # se envuelve el búfer binario si lo hay.
            buffer = getattr(flujo, "buffer", None)
            if buffer is None:
                informe[nombre] = f"{antes} (no se pudo cambiar)"
                continue
            try:
                setattr(sys, nombre,
                        io.TextIOWrapper(buffer, encoding="utf-8",
                                         errors="replace", line_buffering=True))
                informe[nombre] = f"{antes} -> utf-8 (envuelto)"
            except Exception as e:      # pragma: no cover
                informe[nombre] = f"{antes} (falló: {type(e).__name__})"

    if not _hecho:
        _hecho = True
        logger.debug("[consola] %s", informe)
    return informe


def estado() -> dict:
    """Codificación efectiva de cada flujo. Para diagnóstico y para Naoko."""
    out: dict[str, str] = {}
    for nombre in ("stdout", "stderr"):
        flujo = getattr(sys, nombre, None)
        out[nombre] = (f"{getattr(flujo, 'encoding', '?')}"
                       f"/{getattr(flujo, 'errors', '?')}"
                       if flujo is not None else "sin flujo")
    return out


def es_segura() -> bool:
    """
    True si escribir texto con acentos no puede lanzar.

    Lo usa la sonda de Naoko: si esto es False, cualquier respuesta en español
    puede tumbar el streaming, y eso hay que decirlo antes de que pase.
    """
    for nombre in ("stdout", "stderr"):
        flujo = getattr(sys, nombre, None)
        if flujo is None:
            continue
        enc = (getattr(flujo, "encoding", "") or "").lower().replace("-", "")
        err = getattr(flujo, "errors", "") or ""
        if enc != "utf8" and err not in ("replace", "backslashreplace", "ignore"):
            return False
    return True
