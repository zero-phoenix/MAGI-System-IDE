"""
Lo mismo que hace el CI, aquí y gratis.

POR QUÉ EXISTE
==============
El 2026-08-13 el CI dejó de arrancar: repositorio privado, minutos de Actions
agotados, seis jobs fallando en dos segundos sin llegar a asignar runner. Y con
el CI caído se cae también la regla que sostiene el proyecto —«sin tests verdes
no hay release»—, porque la única forma de saber si están verdes era el CI.

Una regla que depende de un servicio de pago no es una regla, es una
suscripción. Esto la devuelve a la máquina.

QUÉ COMPRUEBA, Y POR QUÉ ESTAS COSAS
====================================
Exactamente los mismos pasos del `ci.yml`, en el mismo orden y con los mismos
comandos. No una aproximación: si aquí sale verde y allí rojo, o al revés, este
script no sirve para nada.

    1. ruff (bloqueante)  -> sintaxis y nombres indefinidos
    2. pytest (rápidos)   -> las ~1250 pruebas de cada push
    3. imports del núcleo -> que los módulos centrales carguen
    4. npm test           -> los 112 tests de la interfaz
    5. npm run build      -> que la interfaz compile

Los tests marcados `slow` NO entran por defecto: compilan un .exe con
PyInstaller y son dos tercios del tiempo. `--todo` los incluye, que es lo que
hay que pasar antes de publicar una versión.

USO
===
    python scripts/verificar.py            # lo de cada push (~4 min)
    python scripts/verificar.py --todo     # + los que compilan (~10 min)
    python scripts/verificar.py --rapido   # solo Python, sin interfaz

SALIDA
======
Un resumen al final con lo que pasó y lo que no, y código de salida distinto de
cero si algo falla — para poder encadenarlo con `&&` antes de un `git push`.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def plegar(texto: str) -> str:
    """
    ASCII imprimible en cualquier consola.

    No es remilgo: la consola de Windows por defecto es cp1252 y un acento en
    un `print` ha tumbado ya cuatro cosas en este proyecto, incluida una
    medición que dio por roto a un proveedor que funcionaba. Una herramienta
    que revienta al informar es peor que no tenerla.
    """
    d = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in d if not unicodedata.combining(c)).encode(
        "ascii", "replace").decode("ascii")


def _entorno() -> dict:
    """
    El entorno de los subprocesos se DECIDE, no se hereda. Ver `publicar.py`.

    En corto: esta máquina tiene `NODE_ENV=production`, y con eso `npm ci` se
    salta TypeScript, Vite y Vitest. El CI no la lleva, así que el fallo solo
    aparece en local — la peor clase de diferencia, porque nadie la busca.
    """
    import os

    e = dict(os.environ)
    e.pop("NODE_ENV", None)
    e["NPM_CONFIG_OMIT"] = ""
    e["NPM_CONFIG_PRODUCTION"] = ""
    e["PYTHONUTF8"] = "1"
    return e


def _que_falta(salida: str) -> str | None:
    """Nombre del paquete o programa ausente, si el fallo es ese. `None` si no."""
    import re

    m = re.search(r"No module named ['\"]?([A-Za-z0-9_.-]+)", salida or "")
    if m:
        return m.group(1)
    if "no se pudo ejecutar" in (salida or ""):
        return "el programa"
    return None


class Paso:
    def __init__(self, nombre: str, orden: list[str], *,
                 cwd: Path = RAIZ, opcional: bool = False):
        self.nombre = nombre
        self.orden = orden
        self.cwd = cwd
        self.opcional = opcional
        self.ok: bool | None = None
        self.segundos = 0.0
        self.salida = ""
        #: Nombre de lo que falta, si el paso no se pudo ejecutar.
        self.falta: str | None = None

    def correr(self) -> bool:
        print(plegar(f"\n=== {self.nombre} ==="), flush=True)
        print(plegar(f"    {' '.join(self.orden)}"), flush=True)
        t0 = time.perf_counter()
        try:
            r = subprocess.run(self.orden, cwd=self.cwd, capture_output=True,
                               text=True, encoding="utf-8", errors="replace",
                               env=_entorno())
            self.salida = (r.stdout or "") + (r.stderr or "")
            self.ok = r.returncode == 0
        except FileNotFoundError as e:
            # Falta la herramienta (npm sin instalar, por ejemplo). Se dice,
            # no se disimula: un paso que no se ejecutó no es un paso que pasó.
            self.salida = f"no se pudo ejecutar: {e}"
            self.ok = None if self.opcional else False

        # «No module named X» no es un fallo de la comprobación: es que falta
        # la herramienta. Distinguirlo importa —y me costó un intento—: al
        # compilar desde el entorno del release, `ruff` no estaba (es una
        # herramienta de desarrollo, no una dependencia de ejecución) y el
        # script dijo «FALLA» a secas. Parecía que el código tenía errores de
        # sintaxis. Un diagnóstico que confunde «está mal» con «no lo he
        # mirado» es peor que no diagnosticar.
        self.falta = _que_falta(self.salida)
        if self.falta:
            self.ok = None
        self.segundos = time.perf_counter() - t0

        self._informar()
        return bool(self.ok)

    def _informar(self) -> None:
        """
        Si pasó, las últimas líneas. Si falló, LAS DEL FALLO.

        La primera versión enseñaba siempre la cola, y falló en su estreno: un
        test se puso rojo y en el registro solo quedaron avisos de `vite` sobre
        el tamaño de los chunks. Hubo que volver a lanzar la suite entera —tres
        minutos— para averiguar QUÉ había fallado.

        Una herramienta de diagnóstico que obliga a repetir el diagnóstico no
        está diagnosticando.
        """
        lineas = [l for l in self.salida.splitlines() if l.strip()]
        if self.falta:
            print(plegar(f"    NO INSTALADO: {self.falta}"), flush=True)
            print(plegar(f"    Instalalo y vuelve a pasar:  pip install "
                         f"{self.falta}"), flush=True)
            print(plegar("    (no es un fallo del codigo: es que no se ha "
                         "comprobado)"), flush=True)
            return
        if self.ok:
            for l in lineas[-8:]:
                print(plegar("    " + l[:160]), flush=True)
            return

        # Lo que de verdad importa cuando algo está en rojo. `FAILED` y `ERROR`
        # son de pytest; `error`/`Error` cubren ruff, npm y tsc.
        pistas = [l for l in lineas
                  if l.lstrip().startswith(("FAILED", "ERROR", "E   "))
                  or "error" in l.lower()[:40]]
        for l in (pistas[:14] or lineas[-14:]):
            print(plegar("    " + l[:170]), flush=True)
        if pistas:
            print(plegar(f"    ... y {len(lineas)} lineas mas en la salida "
                         f"completa"), flush=True)


def _npm() -> list[str]:
    """
    `npm` en Windows es `npm.cmd`, y `subprocess` no lo encuentra sin ayuda.

    Sin esto el paso de la interfaz falla con `FileNotFoundError` en la única
    plataforma donde se compila el .exe — o sea, siempre que importa.
    """
    exe = shutil.which("npm") or shutil.which("npm.cmd")
    return [exe] if exe else ["npm"]


def construir_pasos(todo: bool, rapido: bool) -> list[Paso]:
    py = [sys.executable, "-m"]
    marca = [] if todo else ["-m", "not slow"]

    pasos = [
        # Igual que en ci.yml: solo E9/F63/F7/F82 son bloqueantes. El lint
        # completo es informativo allí, así que aquí tampoco puede tumbar nada.
        Paso("ruff (sintaxis y nombres indefinidos)",
             [*py, "ruff", "check", "magi/", "tests/",
              "--select", "E9,F63,F7,F82"]),
        Paso("pytest" + ("" if todo else " (sin los que compilan)"),
             [*py, "pytest", "tests/", "-q", "--tb=line",
              "-p", "no:cacheprovider", *marca]),
        Paso("imports del nucleo",
             [sys.executable, "-c",
              "import magi.core.paths, magi.core.context, magi.core.router;"
              "import magi.core.prompts, magi.core.agent_loop;"
              "import magi.core.providers.registry, magi.core.providers.cloud;"
              "import magi.core.tools;"
              "print('todos los modulos del nucleo importan')"]),
    ]
    if not rapido:
        gui = RAIZ / "magi-gui"
        pasos += [
            Paso("interfaz: tests", [*_npm(), "test"], cwd=gui, opcional=True),
            Paso("interfaz: build", [*_npm(), "run", "build"], cwd=gui,
                 opcional=True),
        ]
    return pasos


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--todo", action="store_true",
                    help="incluye los tests que compilan un .exe")
    ap.add_argument("--rapido", action="store_true",
                    help="solo Python, sin la interfaz")
    args = ap.parse_args()

    pasos = construir_pasos(args.todo, args.rapido)
    t0 = time.perf_counter()
    for p in pasos:
        p.correr()

    print(plegar("\n" + "=" * 66))
    fallos = 0
    for p in pasos:
        if p.ok is None:
            estado = "NO HECHO" if p.falta else "SALTADO"
        elif p.ok:
            estado = "  OK   "
        else:
            estado = " FALLA "
            fallos += 1
        print(plegar(f"  [{estado}] {p.nombre:<44} {p.segundos:6.1f}s"))
    print(plegar(f"  total: {time.perf_counter() - t0:.1f}s"))

    if fallos:
        print(plegar(f"\n{fallos} paso(s) en rojo. NO subas esto."))
        return 1

    sin_hacer = [p.nombre for p in pasos if p.falta]
    if sin_hacer:
        # Ni verde ni rojo: hay comprobaciones que NO se han hecho. Decir
        # «todo verde» aquí seria mentir por omision, que es la clase de
        # mentira mas cara porque nadie la ve.
        print(plegar(f"\nNada en rojo, pero {len(sin_hacer)} comprobacion(es) "
                     f"no se han hecho por falta de herramientas:"))
        for n in sin_hacer:
            print(plegar(f"  - {n}"))
        return 2
    if not args.todo:
        print(plegar("\nTodo verde. Antes de publicar una version, pasa "
                     "tambien:\n    python scripts/verificar.py --todo"))
    else:
        print(plegar("\nTodo verde, incluidos los que compilan. Listo para "
                     "publicar."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
