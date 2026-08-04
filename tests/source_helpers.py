"""
Utilidades para tests que vigilan el CÓDIGO, no el comportamiento.

POR QUÉ EXISTE
==============
Varios tests de esta suite prohíben que vuelva un patrón concreto:
`originalCode=""`, `oldLines.includes`, `EMERGENCY_STOP_TRIGGERED`… Son
guardas útiles, porque son fallos que ya ocurrieron una vez.

El problema apareció tres veces seguidas: el comentario que EXPLICA el fallo
corregido contiene el patrón prohibido, así que la guarda se dispara sola. Y
la única forma de ponerla en verde es borrar la explicación.

Un test que castiga documentar el porqué acaba dejando el código sin porqué.
Así que las guardas miran el código ejecutable y no los comentarios.

Se resuelve aquí y no en cada fichero porque ya iba por la tercera copia del
mismo regex, que es como empiezan las divergencias.
"""
from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path


def strip_js_comments(src: str) -> str:
    """Quita comentarios de bloque y de línea de JS/TS."""
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", src, flags=re.S)


def strip_py_comments(src: str) -> str:
    """
    Quita comentarios Y docstrings de Python.

    Los comentarios se quitan con `tokenize` en vez de con una expresión
    regular: un `#` dentro de una cadena no es un comentario, y el regex no
    sabe distinguirlo. Los docstrings se localizan con AST, que es la única
    forma de saber si una cadena suelta es documentación o un valor.
    """
    # 1. Docstrings, por posición exacta según el AST.
    lineas = src.splitlines(keepends=True)
    try:
        arbol = ast.parse(src)
    except SyntaxError:
        arbol = None

    if arbol is not None:
        a_borrar: list[tuple[int, int]] = []
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, (ast.Module, ast.FunctionDef,
                                     ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            cuerpo = getattr(nodo, "body", None)
            if not cuerpo:
                continue
            primero = cuerpo[0]
            if (isinstance(primero, ast.Expr)
                    and isinstance(primero.value, ast.Constant)
                    and isinstance(primero.value.value, str)):
                a_borrar.append((primero.lineno, primero.end_lineno))
        for ini, fin in a_borrar:
            for i in range(ini - 1, min(fin, len(lineas))):
                lineas[i] = "\n"
        src = "".join(lineas)

    # 2. Comentarios, con el tokenizador.
    try:
        salida, ultima = [], (1, 0)
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                continue
            if tok.start[0] > ultima[0]:
                salida.append("\n" * (tok.start[0] - ultima[0]))
            salida.append(tok.string)
            ultima = tok.end
        return "".join(salida)
    except (tokenize.TokenError, IndentationError):
        return src


def code_of(path: str | Path) -> str:
    """Código ejecutable de un fichero, sin comentarios ni docstrings."""
    p = Path(path)
    src = p.read_text(encoding="utf-8")
    if p.suffix in (".ts", ".tsx", ".js", ".jsx"):
        return strip_js_comments(src)
    if p.suffix == ".py":
        return strip_py_comments(src)
    return src
