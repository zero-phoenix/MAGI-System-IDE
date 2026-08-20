"""
Un bloque de Python sin etiqueta sigue siendo Python.

MEDIDO, NO SUPUESTO
===================
Encargo del ping pong, 2026-08-20: de los 18 bloques de código que escribió
Melchior, **11 venían sin etiqueta**, 6 como `bash` y 1 como `c`. Ninguno como
`python`.

Consecuencia en cadena: `extract_blocks` los marcaba `text`, el verificador no
los ejecutaba, y la fábrica contestaba «la propuesta final no contiene bloques
de código Python» teniendo diez delante. El prompt pide ```python desde hace
versiones; el modelo no obedece.

Pedirlo no es un mecanismo. Mirarlo, sí.
"""
from __future__ import annotations

import pytest

from magi.core.verification import extract_blocks

PY = "import sys\n\ndef main():\n    print('hola')\n"


@pytest.mark.parametrize("etiqueta", ["python", "py", "python3", "PY3", "Python"])
def test_los_alias_de_python_son_python(etiqueta):
    bloques = extract_blocks(f"```{etiqueta}\n{PY}```")
    assert bloques and bloques[0][0] == "python"


def test_sin_etiqueta_pero_con_pinta_de_python():
    bloques = extract_blocks(f"Aquí tienes:\n\n```\n{PY}```")
    assert bloques[0][0] == "python", "11 de 18 bloques reales venían así"


@pytest.mark.parametrize("code", [
    "SELECT * FROM tabla;",
    "gcc -O2 main.c -o main",
    "{\n  \"clave\": 1\n}",
])
def test_no_llama_python_a_lo_que_no_lo_es(code):
    """
    Conservadora a propósito: solo dice python si EMPIEZA como python.

    Equivocarse hacia python significa intentar ejecutar algo que no lo es, y
    aunque el verificador lo cazaría con un fallo limpio, un falso positivo
    gasta una ejecución y ensucia el informe.
    """
    assert extract_blocks(f"```\n{code}\n```")[0][0] == "text"


def test_una_etiqueta_explicita_manda_sobre_la_heuristica():
    bloques = extract_blocks("```bash\npip install x\n```")
    assert bloques[0][0] == "bash"


def test_la_fabrica_ve_el_codigo_que_antes_se_le_escapaba():
    """El caso completo: propuesta con bloque sin etiquetar -> hay python."""
    from magi.modules.studio.entrega import _unir_bloques

    propuesta = f"Propuesta:\n\n```\n{PY}```\n\nY para instalarlo:\n\n```bash\npip install x\n```"
    assert _unir_bloques(propuesta).strip() == PY.strip()
