"""
El .exe publicado se puede volver a compilar igual.

EL PROBLEMA
===========
`requirements.txt` mezcla tres cosas:

    requests==2.31.0      pin exacto
    capstone>=5.0         rango
    g4f                   sin pin

Con eso, el binario de una versión publicada NO es reproducible. Recompilar el
tag v5.1.6 dentro de seis meses instala lo que haya ese día en PyPI, y el .exe
resultante no es el que se probó. Peor: cuando un upstream publica una versión
incompatible, la compilación se rompe sin que nada haya cambiado en este
repositorio — el peor tipo de fallo, porque el commit culpable no es tuyo y no
hay nada que revertir.

`requirements.lock` fija las 66 dependencias, directas y transitivas, con las
que se compiló. Estos tests impiden los dos accidentes que dejarían el lock sin
valor: que se separe de requirements.txt, y que alguien lo use donde no puede
funcionar.
"""
from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LOCK = RAIZ / "requirements.lock"
REQS = RAIZ / "requirements.txt"

#: paquetes del lock que SOLO existen en Windows. Casi todos vienen de
#: pywebview, que en Windows usa el WebView2 de Edge a través de .NET.
SOLO_WINDOWS = {"pythonnet", "clr-loader", "pywin32-ctypes", "proxy-tools"}


def _normaliza(nombre: str) -> str:
    """PEP 503: `pywin32_ctypes`, `PyWin32-CTypes` y `pywin32-ctypes` son uno."""
    return re.sub(r"[-_.]+", "-", nombre).lower()


def _directas() -> set[str]:
    """Lo que requirements.txt pide explícitamente, sin versiones ni comentarios."""
    fuera = set()
    for linea in REQS.read_text(encoding="utf-8").splitlines():
        linea = linea.split("#")[0].strip()
        if not linea:
            continue
        m = re.match(r"^([A-Za-z0-9._-]+)", linea)
        if m:
            fuera.add(_normaliza(m.group(1)))
    return fuera


def _bloqueadas() -> dict[str, str]:
    """Nombre -> versión exacta de todo lo que el lock fija."""
    out = {}
    for linea in LOCK.read_text(encoding="utf-8").splitlines():
        linea = linea.split("#")[0].strip()
        if not linea or linea.startswith("-"):
            continue
        m = re.match(r"^([A-Za-z0-9._-]+)==([^\s;]+)", linea)
        if m:
            out[_normaliza(m.group(1))] = m.group(2)
    return out


def test_el_lock_existe_y_fija_versiones_exactas():
    assert LOCK.exists(), "falta requirements.lock: el .exe no sería reproducible"
    bloqueadas = _bloqueadas()
    assert len(bloqueadas) >= 50, (
        f"el lock solo fija {len(bloqueadas)} paquetes: parece truncado o mal "
        f"generado. Regenéralo con pip-compile.")


def test_no_queda_ninguna_dependencia_sin_fijar():
    """
    Un solo paquete sin pin basta para que el binario deje de ser reproducible.

    Es la clase de agujero que no se nota: 65 de 66 fijados funciona
    perfectamente hasta el día en que el que falta publica una versión mala.
    """
    texto = LOCK.read_text(encoding="utf-8")
    sueltas = []
    for linea in texto.splitlines():
        linea = linea.split("#")[0].strip()
        if not linea or linea.startswith("-"):
            continue
        if "==" not in linea:
            sueltas.append(linea)
    assert not sueltas, f"sin versión exacta en el lock: {sueltas}"


def test_toda_dependencia_directa_esta_en_el_lock():
    """
    El accidente que deja el lock sin valor: añadir un paquete y no regenerar.

    Ya pasó dos veces con la lista de dependencias del CI escrita a mano —
    primero sin `websockets`, después sin `numpy`— y las dos veces el release
    se quedó sin .exe. Un lock desincronizado es la misma clase de fallo con
    otro disfraz: pareces tener versiones fijadas y en realidad no las tienes.
    """
    faltan = sorted(_directas() - set(_bloqueadas()))
    assert not faltan, (
        f"en requirements.txt pero no en el lock: {faltan}\n"
        f"Regenera el lock EN EL MISMO COMMIT en el que tocas requirements.txt:\n"
        f"  python -m piptools compile --strip-extras "
        f"-o requirements.lock requirements.txt")


def test_el_lock_solo_se_usa_donde_puede_funcionar():
    """
    El lock lleva paquetes que no existen fuera de Windows.

    Está generado sin marcadores de entorno, así que un `pip install -r
    requirements.lock` en Linux falla en `pythonnet`. Usarlo en el job de tests
    —que corre en Ubuntu— dejaría el release sin .exe, porque el build depende
    de los tests. Se comprueba aquí en vez de descubrirlo en el runner.
    """
    lock_tiene_windows = SOLO_WINDOWS & set(_bloqueadas())
    assert lock_tiene_windows, (
        "el lock ya no lleva paquetes de Windows; revisa si sigue siendo "
        "específico de plataforma y actualiza su cabecera")

    ci = (RAIZ / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "requirements.lock" not in ci, (
        "ci.yml corre en Ubuntu y el lock es de Windows: instalarlo ahí falla "
        "en pythonnet y, como el build del release lleva `needs: test`, no "
        "habría .exe.")

    release = (RAIZ / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "pip install -r requirements.lock" in release, (
        "el job de build del release debe compilar desde el lock: es lo único "
        "que hace reproducible el binario que se publica")
