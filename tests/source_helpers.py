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
    """
    Quita comentarios de JS/TS RESPETANDO las cadenas.

    La primera versión era un regex, `re.sub(r"/\\*.*?\\*/|//[^\\n]*", "", src)`,
    y destrozaba el código que decía limpiar:

        entrada: const url = "https://github.com/x"; const y = 1;
        salida : const url = "https:

    El `//` de una URL dentro de una cadena se tragaba el resto de la línea.
    Estaba ocurriendo de verdad sobre `App.tsx` y `useMagiSocket.ts`, y es el
    peor sitio donde tener un fallo: este fichero es el INSTRUMENTO DE MEDIDA
    de varias guardas del tipo «este patrón prohibido no vuelve». Si el
    limpiador borra el patrón, la guarda pasa sin comprobar nada — y pasa en
    verde, que es como no tener guarda pero creyendo que se tiene.

    Se recorre carácter a carácter llevando la cuenta de si estamos dentro de
    una cadena simple, doble o de plantilla. No se intenta detectar literales
    de expresión regular: distinguir `/` de división de `/` de regex exige
    analizar la gramática, y para lo que hace falta aquí basta con no romper
    las cadenas.
    """
    out: list[str] = []
    i, n = 0, len(src)
    comilla: str | None = None          # ' " ` cuando estamos dentro

    while i < n:
        c = src[i]

        if comilla:
            out.append(c)
            if c == "\\" and i + 1 < n:      # escape: copiar el par entero
                out.append(src[i + 1])
                i += 2
                continue
            if c == comilla:
                comilla = None
            i += 1
            continue

        if c in "'\"`":
            comilla = c
            out.append(c)
            i += 1
            continue

        if c == "/" and i + 1 < n:
            if src[i + 1] == "/":
                while i < n and src[i] != "\n":
                    i += 1
                continue
            if src[i + 1] == "*":
                fin = src.find("*/", i + 2)
                trozo = src[i:fin + 2] if fin != -1 else src[i:]
                # Conservar los saltos de línea: los números de línea de un
                # informe de fallo tienen que seguir sirviendo.
                out.append("\n" * trozo.count("\n"))
                i = fin + 2 if fin != -1 else n
                continue

        out.append(c)
        i += 1
    return "".join(out)


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
    #
    # Se reconstruye respetando FILA Y COLUMNA. La primera versión concatenaba
    # los tokens sin más, así que `async def propose_improvement` salía como
    # `asyncdefpropose_improvement` y cualquier búsqueda con espacios fallaba
    # — un limpiador que destruye el texto que se va a buscar no sirve para
    # buscar en él.
    try:
        lineas: list[str] = []
        fila, col = 1, 0
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                continue
            f0, c0 = tok.start
            if f0 > fila:
                lineas.append("\n" * (f0 - fila))
                fila, col = f0, 0
            if c0 > col:
                lineas.append(" " * (c0 - col))
            lineas.append(tok.string)
            fila, col = tok.end
        return "".join(lineas)
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


# ---------------------------------------------------------------- autotest
#
# Este fichero es un instrumento de medida, y un instrumento sin calibrar
# convierte todos los tests que lo usan en ruido. La primera versión unía los
# tokens sin respetar columnas y `async def x` salía como `asyncdefx`, así que
# las guardas que buscaban texto con espacios pasaban sin comprobar nada.

def _autotest() -> None:
    ejemplo = (
        'async def f(self, x):\n'
        '    """Doc con MARCA."""\n'
        '    # comentario con MARCA\n'
        '    s = "cadena # con almohadilla"\n'
        '    return s\n'
    )
    limpio = strip_py_comments(ejemplo)
    assert "async def f(self, x)" in limpio, "se perdieron los espacios"
    assert "MARCA" not in limpio, "no se quitaron docstring y comentario"
    assert "# con almohadilla" in limpio, "se tocó una cadena"

    # JS/TS: lo que de verdad estaba roto. Una URL dentro de una cadena lleva
    # `//` y el regex ingenuo se comía el resto de la línea.
    js = strip_js_comments(
        'const u = "https://github.com/x";  // comentario con MARCA\n'
        "const v = 'a /* no es bloque */ b';\n"
        "const w = `plantilla // tampoco`;\n"
        "/* bloque\n   con MARCA */\n"
        "const z = 1;\n")
    assert '"https://github.com/x"' in js, "se rompió una URL dentro de cadena"
    assert "'a /* no es bloque */ b'" in js, "se tocó una cadena simple"
    assert "`plantilla // tampoco`" in js, "se tocó una plantilla"
    assert "MARCA" not in js, "no se quitaron los comentarios"
    assert "const z = 1;" in js
    assert 'const u = "https://github.com/x";' in js


_autotest()
