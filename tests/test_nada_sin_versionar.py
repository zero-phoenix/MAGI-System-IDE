"""
Un módulo que no está en git no está en ninguna parte.

EL FALLO QUE OBLIGÓ A ESCRIBIR ESTO
===================================
30 de agosto de 2026, release v5.11.0 de MAGI. La suite local: verde.
El CI: `ImportError: cannot import name 'bitacora' from
'magi.modules.swarm'`.

`bitacora.py` existía en el disco de la máquina de desarrollo — la sesión
que la escribió jamás la committeó — y su test, también huérfano, pasaba
contra el fichero de mentira. Un módulo nuevo con un test nuevo pasa la
suite local SIEMPRE, esté en git o no: los dos viven en el mismo disco.

El detector de huérfanos existente no podía cazarla porque comprueba que
el código esté CONECTADO, no que esté VERSIONADO. Esta es la otra mitad:
un `.py` bajo `magi/` que git no conoce es un módulo que solo existe en
una máquina, y todo test que lo importe está probando un fantasma.

QUÉ HACE
========
Compara los `.py` presentes en el árbol de trabajo con los que git tiene
registrados. Cualquier diferencia no ignorada es un fallo con nombre y
apellido: el fichero, y el arreglo (git add o borrar).

Qué NO hace: no comprueba contenido ni conexiones — solo existencia en
git. Y si no hay git (raro, pero un zip no lo trae), se salta diciéndolo:
un test que falla porque falta una herramienta enseña a ignorar tests.
"""
from __future__ import annotations

import pathlib
import subprocess

import pytest

RAIZ = pathlib.Path(__file__).resolve().parents[1]


def _git_disponible() -> bool:
    try:
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                       cwd=RAIZ, capture_output=True, check=True)
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _git_disponible(), reason="sin git no hay nada que comparar")
def test_todo_py_de_magi_y_tests_esta_versionado():
    registrados = set(
        subprocess.run(["git", "ls-files", "*.py"],
                       cwd=RAIZ, capture_output=True, text=True,
                       check=True).stdout.split())

    presentes = {str(p.relative_to(RAIZ)).replace("\\", "/")
                 for p in RAIZ.glob("magi/**/*.py")}
    presentes |= {str(p.relative_to(RAIZ)).replace("\\", "/")
                  for p in RAIZ.glob("tests/*.py")}

    huerfanos = sorted(p for p in presentes if p not in registrados)
    assert not huerfanos, (
        "ficheros .py que existen en disco pero NO en git — todo test que los "
        "importe pasa en esta máquina y revienta en el CI:\n  "
        + "\n  ".join(huerfanos)
        + "\n(arregla con `git add` o bórralos)")
