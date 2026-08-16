#!/usr/bin/env python3
"""
Código público que nadie llama. El trinquete de «conecta o borra».

QUÉ PROBLEMA RESUELVE
=====================
La lección nº2 del proyecto dice «conecta o borra», y hasta ahora era una
norma: algo que se cumple mientras alguien se acuerde. La historia del
repositorio dice que no basta. Aparecieron, una detrás de otra:

  · `MetricsCollector` construido, probado y enganchado al bus — sin nadie que
    llamara a `obs.metrics`. El panel de salud no existía.
  · `eval.run` y `naoko.self_improve`, igual: motor completo, ningún botón.
  · `record_usage()` nunca llamado, con `token_ledger` vacía desde su creación.
  · La tabla `task_event` creada en la migración 0001 y sin una sola escritura
    hasta cuatro fases después.

Ninguno de esos casos rompía un test. El sistema funcionaba; simplemente tenía
piezas que no hacían nada, y la única forma de encontrarlas fue que alguien se
sentara a auditar a mano.

CÓMO DECIDE
===========
Dos técnicas distintas para dos preguntas distintas, y la mezcla es a
propósito:

  DEFINICIONES → AST. Preciso. Solo cuenta lo que de verdad es una clase o
  función pública en el nivel superior de un módulo de `magi/`.

  USOS → búsqueda de texto en TODO el repositorio, incluidos .md, .yml, .json
  y el frontend. Generoso a propósito. Media docena de piezas se registran por
  cadena de texto —handlers RPC, nombres de herramientas, claves de catálogo—
  y un análisis puramente sintáctico las declararía huérfanas sin serlo.

El resultado: solo se señala lo que no aparece NI UNA VEZ fuera de su propio
fichero, en ningún formato. Un aviso caro de producir y difícil de discutir.

Es la misma decisión que en los avisos de latencia: una alarma que salta con
falsos positivos deja de leerse, y entonces no sirve de nada tenerla.

USO
===
    python scripts/huerfanos.py            # informe legible
    python scripts/huerfanos.py --conteo   # solo el número (para el CI)
    python scripts/huerfanos.py --json     # para procesarlo
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PAQUETE = RAIZ / "magi"

#: no se audita. `_attic` es andamiaje retirado que se conserva a propósito
#: como mapa de lo que se probó; señalarlo sería ruido garantizado.
#: 2026-08-16: el conteo LOCAL daba 70 y el CI 80, y el CI tenia razon.
#: El indice de uso leía ficheros que existen en la maquina de desarrollo
#: pero no en un checkout limpio (.venv-lock/site-packages sobre todo):
#: nombres comunes encontrados ahí contaban como "uso" y bajaban el conteo
#: sin que nadie hubiera conectado nada. Un rinquete que mide distinto según
#: dónde corre no es un rinquete.
EXCLUIDOS = {"_attic", "__pycache__", "node_modules", ".git", "dist", "build",
             ".venv-lock", "venv", "env", "release", "journal", "scratch",
             "generated_media", "htmlcov", ".pytest_cache", ".ruff_cache",
             ".idea", ".vscode"}

#: extensiones donde se busca uso. El frontend cuenta: media docena de
#: capacidades del backend solo se invocan desde TypeScript.
EXTENSIONES_DE_USO = {
    ".py", ".md", ".yml", ".yaml", ".json", ".toml", ".spec", ".cfg",
    ".ts", ".tsx", ".js", ".jsx", ".html", ".rs", ".j2", ".proto",
}

#: nombres que son puntos de entrada por contrato: los llama Python, un
#: framework o el sistema operativo, nunca otro fichero del repositorio.
ENTRADAS = {
    "main", "setup", "run", "app",
    # dunder y protocolos
    "Config", "Meta",
}

#: prefijos de nombres que un framework invoca por convención.
PREFIJOS_DE_ENTRADA = ("test_", "pytest_", "handle_", "hook_")


def _ficheros(raiz: Path, extensiones: set[str] | None = None) -> list[Path]:
    out = []
    for p in raiz.rglob("*"):
        if not p.is_file():
            continue
        if any(parte in EXCLUIDOS for parte in p.parts):
            continue
        if extensiones is not None and p.suffix not in extensiones:
            continue
        out.append(p)
    return out


def definiciones_publicas() -> dict[str, list[tuple[Path, int]]]:
    """
    Clases y funciones públicas del nivel superior de cada módulo de `magi/`.

    Solo el nivel superior: un método está dentro de su clase, y si la clase se
    usa, el método tiene dueño. Auditar métodos uno a uno produciría cientos de
    avisos sobre código perfectamente vivo.
    """
    encontradas: dict[str, list[tuple[Path, int]]] = {}
    for fichero in _ficheros(PAQUETE, {".py"}):
        try:
            arbol = ast.parse(fichero.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for nodo in arbol.body:            # nivel superior únicamente
            if not isinstance(nodo, (ast.ClassDef, ast.FunctionDef,
                                     ast.AsyncFunctionDef)):
                continue
            nombre = nodo.name
            if nombre.startswith("_"):
                continue                   # privado: su contrato no es público
            if nombre in ENTRADAS or nombre.startswith(PREFIJOS_DE_ENTRADA):
                continue
            encontradas.setdefault(nombre, []).append((fichero, nodo.lineno))
    return encontradas


_PALABRA = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def indice_de_palabras() -> dict[str, set[Path]]:
    """
    Para cada identificador del repositorio, en qué ficheros aparece.

    Se construye UNA vez. La primera versión de este script recorría el
    repositorio entero por cada definición —unas 600— y no terminaba en tres
    minutos. El índice invertido lo deja en un par de segundos: se lee cada
    fichero una sola vez y después toda pregunta es una consulta a un
    diccionario.
    """
    indice: dict[str, set[Path]] = {}
    for p in _ficheros(RAIZ, EXTENSIONES_DE_USO):
        try:
            texto = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for palabra in set(_PALABRA.findall(texto)):
            indice.setdefault(palabra, set()).add(p)
    return indice


def huerfanos() -> list[dict]:
    """Definiciones públicas cuyo nombre no aparece en ningún otro fichero."""
    defs = definiciones_publicas()
    indice = indice_de_palabras()

    sospechosos: list[dict] = []
    for nombre, sitios in defs.items():
        propios = {f for f, _ in sitios}
        # Se restan los ficheros donde se DEFINE: un módulo que solo se usa a
        # sí mismo es exactamente lo que este script busca.
        if indice.get(nombre, set()) - propios:
            continue
        sospechosos.append({
            "nombre": nombre,
            "sitios": [f"{f.relative_to(RAIZ).as_posix()}:{ln}" for f, ln in sitios],
        })
    sospechosos.sort(key=lambda d: d["nombre"])
    return sospechosos


def _informe(items: list[dict]) -> str:
    if not items:
        return ("Sin código público huérfano.\n"
                "Todo lo que magi/ ofrece tiene quien lo llame.")
    lineas = [
        f"{len(items)} definiciones públicas sin sitio de llamada:",
        "",
    ]
    for it in items:
        lineas.append(f"  {it['nombre']}")
        for s in it["sitios"]:
            lineas.append(f"      {s}")
    lineas += [
        "",
        "«Conecta o borra» (lección nº2). Cada una es una de tres cosas:",
        "  · una capacidad construida a la que le falta el cable — CONÉCTALA;",
        "  · andamiaje que ya no hace falta — BÓRRALO o muévelo a magi/_attic/;",
        "  · un punto de entrada legítimo — añádelo a ENTRADAS en este script,",
        "    con el motivo escrito.",
    ]
    return "\n".join(lineas)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--conteo", action="store_true", help="solo el número")
    ap.add_argument("--json", action="store_true", help="salida en JSON")
    args = ap.parse_args()

    items = huerfanos()
    if args.conteo:
        print(len(items))
    elif args.json:
        print(json.dumps(items, indent=1, ensure_ascii=False))
    else:
        print(_informe(items))
    return 0


if __name__ == "__main__":
    sys.exit(main())
