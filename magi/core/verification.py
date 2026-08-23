"""
Verificación ejecutable antes del arbitraje (Plan MAGI 9.0 §2.5).

REGLA
=====
Ninguna propuesta que contenga código llega a Casper sin haberse ejecutado.

    Melchior escribe -> sandbox -> lint / import / tests
        ├─ pasa  -> va a Balthasar CON la evidencia adjunta
        └─ falla -> vuelve a Melchior con el traceback, sin gastar ronda

EL PROBLEMA QUE ELIMINA
=======================
En v5.0.28 los tres agentes debatían elegantemente sobre código que no
compilaba. Balthasar criticaba el estilo de una función con un SyntaxError
dentro, y Casper arbitraba entre dos textos. El fallo más común y más caro del
sistema era ese: tres rondas de deliberación sobre algo que no arranca.
"""
from __future__ import annotations

import ast
import asyncio
import logging
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .paths import python_executable

logger = logging.getLogger(__name__)

# ```python … ```   /   ```py … ```   /   ```powershell … ```
_BLOCK = re.compile(r"```(\w+)?\s*\n(.*?)```", re.DOTALL)

CHECKABLE = {"python", "py", "json", "yaml", "yml"}

# Marcadores de bloques que abren una ventana o entran en un bucle de eventos
# que NUNCA termina por sí solo. Sin detección, `verify()` colgaba 45s en un
# Tetris y lo marcaba como "no arranca" cuando sí arrancaba — el fallo más
# frustrante: código correcto devuelto al autor una y otra vez.
#
# Se busca el framework o la llamada al mainloop, no `while True` a secas: un
# bucle infinito sin bucle de eventos es un bug real (FALLA por timeout), no
# una GUI. El patrón del log del usuario era un juego pygame.
_GUI_MARKERS = re.compile(
    r"\b(import\s+pygame|from\s+pygame|"
    r"import\s+tkinter|from\s+tkinter|\.mainloop\s*\(|"
    r"import\s+turtle|from\s+turtle|"
    r"import\s+arcade|from\s+arcade|"
    r"\.after\s*\()\b")

# Tope de ejecución para un bloque GUI: no hace falta 45s para saber si un
# juego arranca; con un par de segundos alcanza para levantar la ventana,
# renderizar algún frame y detectar un traceback si lo hay.
#
# 8 s ERA DEMASIADO POCO, y la forma de fallar era la peor posible (§G5).
# Medido en este equipo el 2026-08-23, con `SDL_VIDEODRIVER=dummy`:
#
#     import pygame   1,61 s
#     pygame.init()   0,31 s
#     ------------------------
#     total           1,91 s   ANTES de ejecutar una sola línea del usuario
#
# Más el arranque del intérprete y con la máquina ocupada, el margen que
# quedaba para ejecutar el código no daba. Y al agotarse el plazo, un bloque
# GUI salía como `skipped` con `ok=True`: **un Tetris roto se aprobaba**. Se
# reprodujo con un script de tres líneas cuya tercera es `x = no_existe`; con
# 20 s se detecta el NameError, con 6 s se aprueba.
#
# Un plazo que al agotarse APRUEBA es un plazo peligroso. Se sube el tope, y
# —más importante— la ausencia de fotogramas deja de ser un aprobado: ver
# `_MARCA_PRIMER_FOTOGRAMA`.
_GUI_TIMEOUT_S = 25.0

#: El guardián lo imprime en cuanto el bloque pinta su primer fotograma. Es la
#: única prueba de que el código llegó de verdad al bucle de dibujo.
_MARCA_PRIMER_FOTOGRAMA = "[MAGI-GUI] primer fotograma"


def _es_bloque_gui(code: str) -> bool:
    """¿Abre este bloque una ventana o un bucle de eventos que no termina?"""
    return bool(_GUI_MARKERS.search(code))


# Prefijo que se inyecta en el bloque para que el bucle de eventos se cancele
# solo tras N iteraciones. Reutiliza el patrón del PYGAME_HARNESS de
# studio/artifacts.py: parchear display.flip/update para contar frames y
# salir por SystemExit; y parchear Tk.after y turtle para no colgarse.
#
# Así un Tetris correcto ejecuta unos fotogramas y termina con rc=0 → OK,
# en vez de colgar hasta el timeout y salir como FALLA.
#
# OJO con DISPLAY: NO se fija a "" aquí. pygame basta con SDL_VIDEODRIVER=dummy,
# pero tkinter necesita un servidor X real y forzar DISPLAY="" lo rompe en Linux
# (no hay display en el runner de CI). Si una GUI no puede abrirse sin display
# —caso de tkinter en Linux headless— el error se captura abajo y se marca como
# `skipped` (requiere display), no como FALLA: el código puede ser correcto y
# solo no verificable en este entorno.
_GUI_GUARD = '''
import sys as _magi_sys
_magi_sys.path.insert(0, "")
try:
    import os as _magi_os
    _magi_os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    _magi_os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    try:
        import pygame as _magi_pg
        _magi_flip = _magi_pg.display.flip
        _magi_upd = _magi_pg.display.update
        _magi_n = {"f": 0}
        def _magi_stop():
            _magi_pg.quit()
            raise SystemExit(0)
        def _magi_marca():
            if _magi_n["f"] == 1:
                print("[MAGI-GUI] primer fotograma", flush=True)
        def _magi_flip_wrap(*a, **k):
            _magi_n["f"] += 1
            _magi_marca()
            if _magi_n["f"] >= 30:
                _magi_stop()
            return _magi_flip(*a, **k)
        def _magi_upd_wrap(*a, **k):
            _magi_n["f"] += 1
            _magi_marca()
            if _magi_n["f"] >= 30:
                _magi_stop()
            return _magi_upd(*a, **k)
        _magi_pg.display.flip = _magi_flip_wrap
        _magi_pg.display.update = _magi_upd_wrap
    except Exception:
        pass
    try:
        import tkinter as _magi_tk
        _magi_after = _magi_tk.Tk.after
        _magi_tk_count = {"n": 0}
        def _magi_after_wrap(self, ms, func=None, *args):
            _magi_tk_count["n"] += 1
            if _magi_tk_count["n"] >= 30:
                try:
                    self.destroy()
                except Exception:
                    pass
                raise SystemExit(0)
            return _magi_after(self, ms, func, *args)
        _magi_tk.Tk.after = _magi_after_wrap
    except Exception:
        pass
    try:
        import turtle as _magi_tr
        _magi_done = _magi_tr.done
        def _magi_done_wrap():
            raise SystemExit(0)
        _magi_tr.done = _magi_done_wrap
        if hasattr(_magi_tr, "mainloop"):
            _magi_tr.mainloop = _magi_done_wrap
    except Exception:
        pass
except Exception:
    pass
'''

# Errores que delatan "esta GUI no puede abrirse porque no hay display", no
# "este código está mal". En Linux sin servidor X (el runner de CI) tkinter
# muere con TclError: couldn't connect to display. Marcarlo como FALLA sería
# rechazar código correcto por el entorno donde se verifica.
_FALTA_DISPLAY = re.compile(
    r"couldn't connect to display|no display|can't open display|"
    r"DISPLAY.*not set|unable to open.*display|"
    r"_tkinter\.TclError", re.IGNORECASE)


@dataclass
class BlockResult:
    lang: str
    index: int
    ok: bool
    stage: str            # "syntax" | "import" | "run" | "skipped"
    detail: str = ""
    excerpt: str = ""

    def render(self) -> str:
        mark = "OK" if self.ok else "FALLA"
        head = f"[{mark}] bloque {self.index + 1} ({self.lang}) — {self.stage}"
        return head if self.ok else f"{head}\n{self.detail[:1200]}"


@dataclass
class VerificationReport:
    blocks: list[BlockResult] = field(default_factory=list)
    had_code: bool = False

    @property
    def ok(self) -> bool:
        """
        ¿Ha fallado algo de lo que se ejecutó?

        Sin código, nada falló: una respuesta en prosa NO se bloquea, y eso es
        deliberado (`test_prose_without_code_is_not_blocked`).
        """
        return all(b.ok for b in self.blocks)

    @property
    def verificado(self) -> bool:
        """
        C7 — ¿se ha comprobado algo DE VERDAD?

        `ok` y `verificado` no son lo mismo, y confundirlos es lo que dejó
        pasar dos entregas vacías el 2026-08-20: en los encargos del Tetris y
        del ping pong, `verify` corrió tres veces en **0,0 s** —no había ni un
        bloque de código— y `ok` valía True porque `all([])` es True. El vacío
        pasaba la verificación con nota.
        """
        return self.had_code and self.ok

    @property
    def estado(self) -> str:
        """VERIFICADO / NO VERIFICADO / FALLA, que son tres cosas distintas."""
        if not self.had_code:
            return "NO VERIFICADO"
        return "VERIFICADO" if self.ok else "FALLA"

    @property
    def failures(self) -> list[BlockResult]:
        return [b for b in self.blocks if not b.ok]

    def render(self) -> str:
        if not self.had_code:
            return "Sin bloques de código que verificar."
        lines = [b.render() for b in self.blocks]
        head = ("Todos los bloques verificados correctamente."
                if self.ok else
                f"{len(self.failures)} de {len(self.blocks)} bloques fallan.")
        return head + "\n\n" + "\n\n".join(lines)

    def feedback_for_author(self) -> str:
        """Lo que se le devuelve a Melchior cuando algo no arranca."""
        parts = ["Tu propuesta NO pasa la verificación. Corrige esto antes de "
                 "que nadie la evalúe:\n"]
        for b in self.failures:
            parts.append(f"--- bloque {b.index + 1} ({b.lang}), fase {b.stage} ---")
            if b.excerpt:
                parts.append(b.excerpt)
            parts.append(b.detail[:1500])
            parts.append("")
        parts.append("Devuelve la propuesta corregida y verificable.")
        return "\n".join(parts)

    def evidence_for_critic(self) -> str:
        """Lo que se le adjunta a Balthasar cuando sí arranca."""
        if not self.had_code:
            return ""
        return ("\n\n--- EVIDENCIA DE EJECUCIÓN (no es una suposición) ---\n"
                + self.render())


#: Alias de lenguaje que significan Python. `py` y `python3` los escribe
#: cualquiera; tratarlos como lenguajes distintos deja el bloque sin verificar
#: y sin empaquetar, que es peor que un nombre feo.
_ALIAS_PYTHON = {"py", "python", "python3", "py3"}

#: Primeras palabras que delatan Python en un bloque SIN etiqueta.
_HUELLAS_PYTHON = ("import ", "from ", "def ", "class ", "print(", "async def",
                   "#!/usr/bin/env python", "if __name__")


def _adivinar_lenguaje(code: str) -> str:
    """
    Qué lenguaje es un bloque que no se etiquetó.

    POR QUÉ HACE FALTA ADIVINAR
    ===========================
    Medido el 2026-08-20 en el encargo del ping pong: de 18 bloques de código
    que escribió Melchior, **11 venían sin etiqueta**, 6 como `bash` y 1 como
    `c`. Ni uno como `python`.

    Con la etiqueta vacía, `extract_blocks` los marcaba como `text`, así que
    el verificador no los ejecutaba y la fábrica respondía «la propuesta no
    contiene bloques de código Python» teniendo diez delante. El prompt pide
    ```python desde hace versiones y el modelo no obedece: pedirlo no es un
    mecanismo, mirarlo sí.

    La heurística es deliberadamente conservadora —solo dice «python» si el
    bloque empieza como Python— porque equivocarse hacia python significa
    intentar ejecutar algo que no lo es, y eso ya lo cubre el verificador con
    un fallo limpio.
    """
    cabeza = "\n".join(code.strip().splitlines()[:6]).lstrip()
    return "python" if cabeza.startswith(_HUELLAS_PYTHON) else "text"


def extract_blocks(text: str) -> list[tuple[str, str]]:
    out = []
    for m in _BLOCK.finditer(text or ""):
        lang = (m.group(1) or "").lower().strip()
        code = m.group(2)
        if not code.strip():
            continue
        if lang in _ALIAS_PYTHON:
            lang = "python"
        elif not lang:
            lang = _adivinar_lenguaje(code)
        out.append((lang, code))
    return out


async def _run(cmd: list[str], cwd: Path, timeout: float = 45.0,
               task_id: str | None = None,
               extra_env: dict | None = None) -> tuple[int, str]:
    from .cancel import tracked

    # PYTHONIOENCODING: la salida se decodifica más abajo como UTF-8, pero un
    # Python hijo en Windows escribe con la página de códigos de la consola
    # (cp1252/cp850), no UTF-8. Resultado: cualquier acento del traceback
    # llegaba como U+FFFD. Y este proyecto habla español, así que el mensaje
    # de error de la verificación —lo que se le enseña al usuario Y lo que se
    # le devuelve al modelo para que corrija— salía mutilado justo en la
    # palabra que explicaba el fallo. Fijar la codificación del hijo lo hace
    # determinista en las dos plataformas.
    entorno = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    if extra_env:
        entorno.update(extra_env)
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, cwd=str(cwd), env=entorno,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    except FileNotFoundError as e:
        return 127, str(e)

    # §7.3 — este proceso ejecuta CÓDIGO GENERADO POR EL MODELO en cada ronda
    # del debate, y quedaba fuera del alcance de la parada de emergencia:
    # pulsar parar informaba de que no había nada en marcha mientras seguía
    # corriendo.
    async with tracked(proc, task_id):
        try:
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return 124, f"timeout tras {timeout}s"
    return proc.returncode or 0, out.decode("utf-8", errors="replace")


class ProposalVerifier:
    """
    Verificación barata y progresiva. Se para en el primer fallo de cada bloque:
    si hay SyntaxError no tiene sentido intentar ejecutarlo.

    Fases:
      1. sintaxis  — ast.parse / json.loads / yaml.safe_load   (milisegundos)
      2. import    — compila y ejecuta en subproceso aislado    (segundos)
      3. run       — solo si el bloque parece ejecutable
    """

    def __init__(self, workdir: Path | None = None, *, run_code: bool = True,
                 timeout_s: float = 45.0):
        self.workdir = workdir
        self.run_code = run_code
        self.timeout_s = timeout_s

    async def verify(self, proposal_text: str) -> VerificationReport:
        blocks = extract_blocks(proposal_text)
        report = VerificationReport(had_code=bool(blocks))
        if not blocks:
            return report

        tmp = Path(self.workdir) if self.workdir else Path(tempfile.mkdtemp(
            prefix="magi-verify-"))
        tmp.mkdir(parents=True, exist_ok=True)

        # B1 — LOS BLOQUES DE UN MISMO LENGUAJE SE VERIFICAN JUNTOS PRIMERO.
        #
        # El modelo hace lo natural: la función en un bloque y su test en otro.
        # Verificar cada bloque como un fichero suelto hace que el test no
        # encuentre a la función y devuelve `ModuleNotFoundError: No module
        # named 'suma'`, que NO es un fallo del modelo: es que se le está
        # ejecutando algo distinto de lo que escribió.
        #
        # Medido el 2026-08-20: eso forzó un ciclo de reconstrucción entero
        # —unas cuatro llamadas, 60-80 s— en la tarea más simple posible.
        #
        # Se prueba primero el conjunto unido; solo si el conjunto falla se cae
        # al modo por bloque, que sigue siendo útil para localizar CUÁL rompe.
        # TODO A LA VEZ: el conjunto unido Y los bloques sueltos.
        #
        # La primera versión de B1 probaba primero el conjunto y solo caía a
        # los sueltos si fallaba. Correcto en resultado y **serializaba la
        # verificación**: `test_blocks_are_verified_in_parallel` —cinco bloques
        # con 0,4 s de pausa, que en serie son 2 s— pasó de 0,8 s a 2,0 s y lo
        # cazó el CI. Un arreglo que arregla una cosa y estropea otra sin que
        # nadie lo mida es medio arreglo.
        #
        # Lanzándolo todo junto se conserva lo que B1 buscaba (que la función y
        # su test se ejecuten en el mismo módulo, sin el
        # `ModuleNotFoundError` que forzaba un rebuild entero) y el tiempo de
        # pared sigue siendo el del bloque más lento. El coste es una
        # ejecución de más, en paralelo, que es exactamente lo que sobra aquí.
        unido = self._unir_por_lenguaje(blocks)
        tareas_juntas = [self._verify_block(0, lang, codigo, tmp)
                         for lang, codigo in unido.items()]
        tareas_sueltas = [self._verify_block(i, lg, code, tmp)
                          for i, (lg, code) in enumerate(blocks)]
        juntas, sueltas = await asyncio.gather(
            asyncio.gather(*tareas_juntas), asyncio.gather(*tareas_sueltas))

        # Si el conjunto de un lenguaje pasa, ese veredicto MANDA sobre los
        # sueltos de ese mismo lenguaje: es el que refleja cómo se va a usar el
        # código de verdad, todo junto en un fichero.
        juntas_ok = {lang for lang, r in zip(unido, juntas, strict=True) if r.ok}
        report.blocks.extend(r for lang, r in zip(unido, juntas, strict=True)
                             if r.ok)
        report.blocks.extend(r for (lg, _), r in zip(blocks, sueltas, strict=True)
                             if lg not in juntas_ok)
        return report

    @staticmethod
    def _unir_por_lenguaje(blocks) -> dict[str, str]:
        """
        Junta los bloques del mismo lenguaje en un único fuente, en orden.

        Solo para lenguajes donde concatenar significa algo (Python): pegar dos
        bloques de JSON produce basura, y pegar dos de bash puede ejecutar el
        segundo con el estado del primero, que es justo lo que no se quiere en
        una verificación.
        """
        unibles: dict[str, list[str]] = {}
        for lang, code in blocks:
            if lang == "python":
                unibles.setdefault(lang, []).append(code)
        return {lang: "\n\n".join(trozos)
                for lang, trozos in unibles.items() if len(trozos) > 1}

    async def _verify_block(self, i: int, lang: str, code: str,
                            tmp: Path) -> BlockResult:
        if lang not in CHECKABLE:
            return BlockResult(lang, i, True, "skipped",
                               f"lenguaje '{lang}' no verificable automáticamente")

        if lang in ("json",):
            import json
            try:
                json.loads(code)
                return BlockResult(lang, i, True, "syntax")
            except json.JSONDecodeError as e:
                return BlockResult(lang, i, False, "syntax", str(e),
                                   self._excerpt(code, e.lineno))

        if lang in ("yaml", "yml"):
            try:
                import yaml
                yaml.safe_load(code)
                return BlockResult(lang, i, True, "syntax")
            except ImportError:
                return BlockResult(lang, i, True, "skipped", "pyyaml no instalado")
            except Exception as e:
                return BlockResult(lang, i, False, "syntax", str(e))

        # Python
        try:
            ast.parse(code)
        except SyntaxError as e:
            return BlockResult(lang, i, False, "syntax",
                               f"{e.msg} (línea {e.lineno})",
                               self._excerpt(code, e.lineno or 1))

        if not self.run_code:
            return BlockResult(lang, i, True, "syntax")

        script = tmp / f"block_{i}.py"
        # ¿Abre una ventana o un bucle de eventos? Un Tetris, un snake, un
        # juego de pygame: código correcto que ANTES salía como FALLA-timeout
        # porque su mainloop nunca termina. Se inyecta un guardián que
        # cuenta frames y sale limpio (SystemExit=0) tras unos pocos, y se
        # reduce el timeout: no hacen falta 45s para saber si arranca.
        es_gui = _es_bloque_gui(code)
        if es_gui:
            script.write_text(_GUI_GUARD + code, encoding="utf-8")
            timeout = min(self.timeout_s, _GUI_TIMEOUT_S)
        else:
            script.write_text(code, encoding="utf-8")
            timeout = self.timeout_s
        interprete = python_executable()
        if interprete is None:
            # No se puede verificar ejecutando. Se dice, no se aprueba: la
            # verificación ejecutable del §2.5 es justo lo que distingue una
            # propuesta comprobada de una plausible.
            return BlockResult(
                lang, i, False, "run",
                "no hay intérprete de Python con el que ejecutar el bloque: "
                "NO se ha verificado. Dentro del .exe `sys.executable` es el "
                "propio .exe y lanzarlo relanzaría MAGI.")
        rc, out = await _run([interprete, str(script)], tmp, timeout)
        # SystemExit(0) del guardián GUI termina con rc=0: el bloque arrancó.
        # Es exactamente lo que queremos distinguir del "cuelga para siempre".
        if rc == 0:
            etapa = "run-headless" if es_gui else "run"
            return BlockResult(lang, i, True, etapa, out[-800:])
        # rc=124 es timeout. Para un GUI, colgar significa que el guardián no
        # pudo enganchar el bucle (p.ej. framework no instalado o API
        # distinta): se dice que requiere GUI en vez de FALLA, porque el
        # código puede ser correcto y solo no verificable headless.
        if rc == 124 and es_gui:
            # §G5 — UN PLAZO QUE AL AGOTARSE APRUEBA ES UN PLAZO PELIGROSO.
            #
            # Antes, cualquier bloque GUI que llegara al tiempo límite salía
            # `skipped` con `ok=True`. La intención era buena: un juego pygame
            # correcto no termina solo, y marcarlo como fallo era injusto.
            #
            # Pero eso convertía «no me dio tiempo a comprobarlo» en «está
            # bien», y las dos cosas no se parecen en nada. Reproducido el
            # 2026-08-23 con tres líneas —`import pygame`, `pygame.init()`,
            # `x = no_existe`—: con plazo corto el NameError nunca llega a
            # verse y el bloque se aprueba. En una máquina lenta, un Tetris
            # roto pasaba la verificación.
            #
            # La diferencia la da la prueba de que el código llegó a dibujar.
            # El guardián imprime una marca en su primer fotograma:
            #
            #   · con marca -> llegó al bucle de dibujo y no termina solo.
            #                  Eso SÍ es un juego que arranca: `skipped`.
            #   · sin marca -> no sabemos nada. No se aprueba.
            if _MARCA_PRIMER_FOTOGRAMA in out:
                return BlockResult(
                    lang, i, True, "skipped",
                    "bloque con interfaz gráfica (GUI): arrancó, pintó "
                    "fotogramas y no termina por sí solo, que es lo normal en "
                    "un juego. Sintaxis, imports y bucle de dibujo "
                    "verificados; la comprobación visual requiere abrirlo a "
                    "mano. NO se marca como fallo.")
            return BlockResult(
                lang, i, False, "run",
                "NO VERIFICADO: el bloque con interfaz gráfica agotó el plazo "
                f"de {timeout:.0f} s sin llegar a pintar un solo fotograma. No "
                "se sabe si arranca —puede ser lento, puede estar colgado antes "
                "del bucle, puede reventar—, así que no se da por bueno. "
                f"Salida:\n{out[-1200:]}")
        # Fallo por falta de display (tkinter en Linux sin X): el código puede
        # ser correcto, solo no se puede verificar gráficamente aquí.
        if rc != 0 and es_gui and _FALTA_DISPLAY.search(out):
            return BlockResult(
                lang, i, True, "skipped",
                "bloque con interfaz gráfica (GUI): no hay servidor gráfico "
                "(display) en este entorno, así que no se pudo ejecutar. La "
                "sintaxis y los imports están verificados; ábrelo a mano para "
                "comprobarlo. NO se marca como fallo: tkinter/turtle "
                "necesitan un display real.")
        return BlockResult(lang, i, False, "run", out[-2000:])

    @staticmethod
    def _excerpt(code: str, lineno: int, ctx: int = 2) -> str:
        lines = code.splitlines()
        lo, hi = max(0, lineno - 1 - ctx), min(len(lines), lineno + ctx)
        return "\n".join(
            f"{'>' if n == lineno else ' '} {n:>4} | {lines[n - 1]}"
            for n in range(lo + 1, hi + 1))
