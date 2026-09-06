"""
Magisys no depende de Venim, y esto lo mantiene así.

POR QUE HACE FALTA UNA PRUEBA Y NO BASTA HABERLO QUITADO
========================================================
El desacoplamiento ya estaba hecho cuando se escribió esto: se buscó
`venim`/`venice` en `magi/`, `magi-gui/src/` y `scripts/` y salieron CERO
apariciones. Verificado, no supuesto.

Pero un desacoplamiento sin guarda se deshace solo. Basta un `import` de
conveniencia, una ruta absoluta a `C:\\Users\\D\\magi-port\\VeniceMAGI` o
una constante copiada para que vuelva, y nadie se entera hasta que Magisys
deja de arrancar en una máquina donde Venim no existe.

Lo que se comprueba es lo que se puede romper por accidente: que ningún
fichero de producción nombre a Venim ni apunte a su carpeta.
"""
from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

#: Donde vive el código que se publica. `docs/` queda fuera a propósito: un
#: documento PUEDE hablar de Venim para explicar de qué se separó, y esta
#: prueba trata del binario, no de la prosa.
ARBOLES = ("magi", "magi-gui/src", "scripts")

EXTENSIONES = {".py", ".ts", ".tsx", ".css", ".json", ".yaml", ".yml"}

SALTAR = {"node_modules", "__pycache__", "_attic", "dist", "build"}

#: `venice` incluido: el repositorio se llama VeniceMAGI y la marca aparece
#: en las dos formas.
_MARCA = re.compile(r"\bvenim\b|venice", re.I)


def _ficheros():
    for arbol in ARBOLES:
        base = RAIZ / arbol
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if (p.is_file() and p.suffix.lower() in EXTENSIONES
                    and not any(s in p.parts for s in SALTAR)):
                yield p


def test_ningun_fichero_de_produccion_nombra_a_venim():
    culpables = []
    for p in _ficheros():
        try:
            texto = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for n, linea in enumerate(texto.splitlines(), 1):
            if _MARCA.search(linea):
                culpables.append(f"{p.relative_to(RAIZ)}:{n}: {linea.strip()[:90]}")

    assert not culpables, (
        "Magisys ha vuelto a nombrar a Venim en código de producción:\n  "
        + "\n  ".join(culpables[:20])
        + "\n\nMagisys arranca en máquinas donde Venim no existe. Si "
          "necesitas algo de allí, cópialo aquí con su prueba.")


def test_no_hay_rutas_a_la_carpeta_de_venim():
    """
    Una ruta absoluta a `magi-port\\VeniceMAGI` es acoplamiento aunque no
    diga «venim» en un import: en otra máquina es un fichero que no existe.
    """
    ruta = re.compile(r"magi-port", re.I)
    culpables = [
        f"{p.relative_to(RAIZ)}"
        for p in _ficheros()
        if ruta.search(p.read_text(encoding="utf-8", errors="ignore"))
    ]
    assert not culpables, (
        f"rutas a la carpeta de Venim en producción: {culpables}")
