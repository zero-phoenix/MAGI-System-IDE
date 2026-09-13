"""
El CI se puso rojo sin que nadie tocara una línea de código. Otra vez.

QUÉ PASÓ
========
Del 2026-09-10 al 2026-09-13, tres corridas seguidas de `main` en rojo. El
paso que fallaba era «Type check nucleo (bloqueante)», y el error, uno solo:

    magi/core/no_browser.py:243:24 - error: "SyncCDPSession" is not a known
    attribute of module ".cdp" (reportAttributeAccessIssue)

Los commits de esos tres días son `docs:`. El código de `no_browser.py` no se
tocó desde el 6-sep. Medido contra las corridas, que es el único control que
había disponible:

    corrida 34312710220   9-sep   pyright 1.1.411   VERDE
    corrida 34458014802  10-sep   pyright 1.1.413   ROJO
    corrida 34733894754  13-sep   pyright 1.1.414   ROJO

El CI hacía `pip install pyright` sin fijar versión. Lo que cambió fue el
instrumento, no lo medido.

LO IRÓNICO
==========
Esto ya había pasado el 2026-08-31 con ruff, y la lección quedó escrita en
`requirements-dev.txt`: «una version nueva puede poner el build en rojo sin
que nadie toque una linea de codigo». Se fijó ruff y se dejaron sin fijar
pyright, pip-audit y pyinstaller — las tres siguen instalándose flotantes hoy.
La de pyinstaller es la peor de las tres: compila el `.exe` que se publica.

Arreglar solo pyright habría sido quitar el síntoma. Este fichero cierra la
fuente: ninguna herramienta se instala sin versión, en ningún workflow.

LA TERCERA GUARDA
=================
`no_browser.py` NO estaba mal en runtime: la línea que pyright rechaza está
dentro de un `if hasattr(cdp, "SyncCDPSession")`. El módulo `.cdp` es de un
tercero (g4f) y ese atributo es opcional POR DISEÑO — por eso el `hasattr`.
Pero escrito con punto, el acceso depende de lo que el stub declare ese mes.
`getattr` dice lo mismo sin atarse a un stub, y es lo que el tercer test
obliga: si guardas un atributo con `hasattr`, no lo leas con punto.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest

yaml = pytest.importorskip("yaml")

RAIZ = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = RAIZ / ".github" / "workflows"
REQUIREMENTS_DEV = RAIZ / "requirements-dev.txt"
NO_BROWSER = RAIZ / "magi" / "core" / "no_browser.py"

#: `python -m pip install --upgrade pip` es el arranque estándar de un runner:
#: actualiza el propio instalador antes de leer ningún pin. Fijar pip es otra
#: discusión; lo que esta guarda persigue son las HERRAMIENTAS que miden o
#: compilan, porque son las que cambian el veredicto.
PAQUETES_EXENTOS = {"pip", "setuptools", "wheel"}

#: Herramientas cuyo pin vive en requirements-dev.txt. Si alguna desaparece de
#: ahí, el CI vuelve a depender de la versión del día.
HERRAMIENTAS_FIJADAS = ("ruff", "pyright", "pip-audit")


def _pasos_con_run():
    """Devuelve (fichero, nombre del paso, comando) de cada paso con `run:`.

    Se parsea el YAML en vez de mirar el texto crudo a propósito: los
    comentarios de estos workflows CITAN el patrón prohibido para explicar por
    qué está prohibido (`ci.yml` dice literalmente «pip install ruff sin
    version»). Un regex sobre el fichero entero se dispararía con la
    explicación, y la única forma de ponerlo en verde sería borrarla. Es el
    mismo motivo por el que existe `tests/source_helpers.py`.
    """
    for ruta in sorted(WORKFLOWS.glob("*.yml")):
        datos = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
        for job in (datos.get("jobs") or {}).values():
            for paso in (job or {}).get("steps") or []:
                comando = (paso or {}).get("run")
                if comando:
                    yield ruta.name, (paso.get("name") or "sin nombre"), comando


def _instalaciones_sin_version(comando: str):
    """Paquetes instalados sin `==` en un bloque `run:`.

    Ignora las líneas de comentario del shell y las instalaciones desde
    fichero (`-r requirements.txt`), que es justo la forma correcta.
    """
    sueltos = []
    for linea in comando.splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        if not re.search(r"\bpip\s+install\b", linea):
            continue
        resto = re.split(r"\bpip\s+install\b", linea, maxsplit=1)[1]
        if re.search(r"(^|\s)-r(\s|=)", resto) or " -e " in resto:
            continue
        for token in resto.split():
            if token.startswith("-"):
                continue
            nombre = re.split(r"[=<>!~\[]", token, maxsplit=1)[0].lower()
            if not nombre or nombre in PAQUETES_EXENTOS:
                continue
            if "==" not in token:
                sueltos.append(nombre)
    return sueltos


def test_ningun_workflow_instala_una_herramienta_sin_version():
    """
    La guarda que faltaba el 31-ago. Cuando se fijó ruff se arregló el caso, no
    la clase: pyright, pip-audit y pyinstaller seguían flotando, y uno de los
    tres acabó estallando doce días después.

    Un `pip install <herramienta>` sin `==` en un workflow es una bomba con
    temporizador aleatorio: el día que el proyecto de turno publique una
    versión, el CI se pone rojo (o el `.exe` cambia) sin que nadie haya tocado
    el repositorio.
    """
    culpables = []
    for fichero, nombre_paso, comando in _pasos_con_run():
        for paquete in _instalaciones_sin_version(comando):
            culpables.append(f"{fichero} · paso «{nombre_paso}» · {paquete}")

    assert not culpables, (
        "Herramientas instaladas sin version fija en los workflows:\n  "
        + "\n  ".join(culpables)
        + "\n\nFijalas con == (o instalalas con -r requirements-dev.txt). "
        "Una version nueva no puede decidir si el build es verde."
    )


@pytest.mark.parametrize("herramienta", HERRAMIENTAS_FIJADAS)
def test_las_herramientas_de_la_compuerta_tienen_pin_exacto(herramienta: str):
    """
    `requirements-dev.txt` es donde vive el pin. Si una herramienta que decide
    el veredicto del CI no está aquí con `==`, el CI mide con lo que haya ese
    día.
    """
    texto = REQUIREMENTS_DEV.read_text(encoding="utf-8")
    patron = re.compile(
        rf"^{re.escape(herramienta)}==\d+\.\d+(\.\d+)?",
        re.IGNORECASE | re.MULTILINE,
    )
    assert patron.search(texto), (
        f"{herramienta} no esta fijada con == en requirements-dev.txt.\n"
        f"Contenido actual:\n{texto}"
    )


def test_no_se_lee_con_punto_lo_que_se_guarda_con_hasattr():
    """
    La clase de fallo, no el síntoma de esta versión.

    `no_browser.py` bloquea navegadores parcheando módulos de terceros. Esos
    módulos cambian de forma entre versiones, así que cada parche se protege
    con `hasattr(...)`. Leer después el atributo con punto vuelve a atar el
    fichero a lo que el stub declare: en runtime funciona, y el analizador
    estático lo tumba. Con `getattr` se dice exactamente lo mismo sin depender
    del stub, y sin añadir un `# type: ignore` que apaga la comprobación.
    """
    arbol = ast.parse(NO_BROWSER.read_text(encoding="utf-8"))
    fallos = []

    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.If):
            continue
        prueba = nodo.test
        if not (
            isinstance(prueba, ast.Call)
            and isinstance(prueba.func, ast.Name)
            and prueba.func.id == "hasattr"
            and len(prueba.args) == 2
            and isinstance(prueba.args[0], ast.Name)
            and isinstance(prueba.args[1], ast.Constant)
            and isinstance(prueba.args[1].value, str)
        ):
            continue

        base, atributo = prueba.args[0].id, prueba.args[1].value
        for hijo in nodo.body:
            for interno in ast.walk(hijo):
                if (
                    isinstance(interno, ast.Attribute)
                    and interno.attr == atributo
                    and isinstance(interno.value, ast.Name)
                    and interno.value.id == base
                ):
                    fallos.append(
                        f"linea {interno.lineno}: {base}.{atributo} dentro de "
                        f'un hasattr({base}, "{atributo}")'
                    )

    assert not fallos, (
        "Atributos opcionales leidos con punto en no_browser.py:\n  "
        + "\n  ".join(fallos)
        + f"\n\nUsa getattr({'<modulo>'}, \"<Atributo>\"): el hasattr ya dice "
        "que puede no estar, y el punto obliga al stub de terceros a "
        "declararlo."
    )
