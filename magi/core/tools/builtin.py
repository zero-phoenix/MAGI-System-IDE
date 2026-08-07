"""
Catálogo de herramientas (Plan MAGI 9.0 §2.2, §4.1).

ACCESO A LA MÁQUINA: SIN RESTRICCIONES
======================================
Es la máquina del usuario y su autorización. No hay allowlist de directorios,
ni puertas de permiso, ni capacidades denegadas. Lo único que se añade es
REVERSIBILIDAD (journal.py): toda mutación se puede deshacer.
"""
from __future__ import annotations

import asyncio
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ..paths import python_executable, workspace_dir
from .journal import WriteJournal
from .registry import ToolRegistry, ToolResult

#: Ver `paths.python_executable`: dentro del bundle `sys.executable` es el
#: propio .exe y lanzarlo relanzaría MAGI en vez de ejecutar Python.
_SIN_PYTHON = (
    "no hay un intérprete de Python en esta máquina. Dentro del .exe de "
    "MAGI, lanzar `sys.executable` relanzaría MAGI en vez de ejecutar "
    "esto. Instala Python y vuelve a intentarlo.")
MAX_READ_BYTES = 400_000


@dataclass
class ToolContext:
    """Estado que comparten las herramientas durante un turno."""
    task_id: str | None = None
    cwd: Path = field(default_factory=workspace_dir)
    journal: WriteJournal | None = None
    dry_run: bool = False
    env: dict[str, str] = field(default_factory=dict)

    def resolve(self, path: str | Path) -> Path:
        p = Path(os.path.expandvars(str(path))).expanduser()
        return p if p.is_absolute() else (self.cwd / p)

    def get_journal(self) -> WriteJournal:
        if self.journal is None:
            self.journal = WriteJournal(task_id=self.task_id)
        return self.journal


def build_registry() -> ToolRegistry:
    reg = ToolRegistry()

    # ------------------------------------------------------------- lectura

    @reg.tool("read_file", "Lee un fichero de texto. Usa offset/limit para ficheros grandes.",
              {"type": "object", "properties": {
                  "path": {"type": "string"},
                  "offset": {"type": "integer", "description": "línea inicial (1-based)"},
                  "limit": {"type": "integer", "description": "número de líneas"}},
               "required": ["path"]}, access={"read"})
    def read_file(path: str, ctx: ToolContext, offset: int = 1, limit: int = 0):
        p = ctx.resolve(path)
        if not p.exists():
            return ToolResult(False, "", error=f"no existe: {p}")
        if p.is_dir():
            return ToolResult(False, "", error=f"es un directorio: {p}")
        if p.stat().st_size > MAX_READ_BYTES:
            data = p.read_bytes()[:MAX_READ_BYTES].decode("utf-8", errors="replace")
            note = f"\n… [truncado, fichero de {p.stat().st_size} bytes]"
        else:
            data, note = p.read_text(encoding="utf-8", errors="replace"), ""
        lines = data.splitlines()
        if offset > 1 or limit:
            end = (offset - 1 + limit) if limit else len(lines)
            lines = lines[offset - 1:end]
        numbered = "\n".join(f"{i + offset:>6}\t{l}" for i, l in enumerate(lines))
        return ToolResult(True, numbered + note, meta={"lines": len(lines), "path": str(p)})

    @reg.tool("list_dir", "Lista un directorio.",
              {"type": "object", "properties": {
                  "path": {"type": "string"}, "recursive": {"type": "boolean"}},
               "required": ["path"]}, access={"read"})
    def list_dir(path: str, ctx: ToolContext, recursive: bool = False):
        p = ctx.resolve(path)
        if not p.is_dir():
            return ToolResult(False, "", error=f"no es un directorio: {p}")
        out, count = [], 0
        it = p.rglob("*") if recursive else p.iterdir()
        for child in sorted(it):
            if any(part in {".git", "node_modules", "__pycache__", ".venv"}
                   for part in child.parts):
                continue
            rel = child.relative_to(p)
            out.append(f"{'d' if child.is_dir() else '-'} {rel}"
                       + ("" if child.is_dir() else f"  ({child.stat().st_size}b)"))
            count += 1
            if count >= 500:
                out.append("… [500+ entradas, acota la ruta]")
                break
        return ToolResult(True, "\n".join(out) or "(vacío)", meta={"count": count})

    @reg.tool("grep", "Busca un patrón (regex) en ficheros.",
              {"type": "object", "properties": {
                  "pattern": {"type": "string"}, "path": {"type": "string"},
                  "glob": {"type": "string", "description": "p.ej. *.py"}},
               "required": ["pattern"]}, access={"read"})
    def grep(pattern: str, ctx: ToolContext, path: str = ".", glob: str = "*"):
        root = ctx.resolve(path)
        try:
            rx = re.compile(pattern)
        except re.error as e:
            return ToolResult(False, "", error=f"regex inválida: {e}")
        hits, files = [], 0
        targets = [root] if root.is_file() else root.rglob(glob)
        for f in targets:
            if not f.is_file() or any(x in f.parts for x in
                                      {".git", "node_modules", "__pycache__"}):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            files += 1
            for n, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{f}:{n}: {line.strip()[:200]}")
                    if len(hits) >= 200:
                        hits.append("… [200+ coincidencias]")
                        return ToolResult(True, "\n".join(hits),
                                          meta={"files": files})
        return ToolResult(True, "\n".join(hits) or "(sin coincidencias)",
                          meta={"files_scanned": files, "hits": len(hits)})

    @reg.tool("glob", "Busca ficheros por patrón de nombre.",
              {"type": "object", "properties": {
                  "pattern": {"type": "string"}, "path": {"type": "string"}},
               "required": ["pattern"]}, access={"read"})
    def glob_tool(pattern: str, ctx: ToolContext, path: str = "."):
        root = ctx.resolve(path)
        found = [str(p) for p in root.rglob(pattern)
                 if ".git" not in p.parts and "node_modules" not in p.parts][:300]
        return ToolResult(True, "\n".join(found) or "(sin resultados)",
                          meta={"count": len(found)})

    # ------------------------------------------------------------- escritura
    # Todas pasan por el journal: reversibles, no restringidas.

    @reg.tool("write_file", "Escribe un fichero (lo crea o lo reemplaza). Reversible.",
              {"type": "object", "properties": {
                  "path": {"type": "string"}, "content": {"type": "string"}},
               "required": ["path", "content"]},
              access={"write"}, dangerous=True)
    def write_file(path: str, content: str, ctx: ToolContext):
        p = ctx.resolve(path)
        if ctx.dry_run:
            return ToolResult(True, f"[dry-run] escribiría {len(content)}b en {p}")
        p.parent.mkdir(parents=True, exist_ok=True)
        entry = ctx.get_journal().record(p, "write" if p.exists() else "create",
                                         tool="write_file")
        p.write_text(content, encoding="utf-8")
        return ToolResult(True, f"escrito {p} ({len(content)} bytes)",
                          meta={"undo_id": entry.op_id, "path": str(p)})

    @reg.tool("edit_file", "Reemplaza una cadena exacta dentro de un fichero. Reversible.",
              {"type": "object", "properties": {
                  "path": {"type": "string"}, "old": {"type": "string"},
                  "new": {"type": "string"}, "all": {"type": "boolean"}},
               "required": ["path", "old", "new"]},
              access={"write"}, dangerous=True)
    def edit_file(path: str, old: str, new: str, ctx: ToolContext, all: bool = False):
        p = ctx.resolve(path)
        if not p.exists():
            return ToolResult(False, "", error=f"no existe: {p}")
        text = p.read_text(encoding="utf-8", errors="replace")
        n = text.count(old)
        if n == 0:
            return ToolResult(False, "", error="la cadena 'old' no aparece en el fichero")
        if n > 1 and not all:
            return ToolResult(False, "", error=(
                f"'old' aparece {n} veces; usa all=true o amplía el contexto "
                f"para que sea único"))
        if ctx.dry_run:
            return ToolResult(True, f"[dry-run] sustituiría {n} ocurrencia(s) en {p}")
        entry = ctx.get_journal().record(p, "write", tool="edit_file")
        p.write_text(text.replace(old, new) if all else text.replace(old, new, 1),
                     encoding="utf-8")
        return ToolResult(True, f"editado {p} ({n if all else 1} sustitución/es)",
                          meta={"undo_id": entry.op_id})

    @reg.tool("delete_path", "Borra un fichero o directorio. Reversible.",
              {"type": "object", "properties": {"path": {"type": "string"}},
               "required": ["path"]}, access={"write"}, dangerous=True)
    def delete_path(path: str, ctx: ToolContext):
        p = ctx.resolve(path)
        if not p.exists():
            return ToolResult(False, "", error=f"no existe: {p}")
        if ctx.dry_run:
            return ToolResult(True, f"[dry-run] borraría {p}")
        entry = ctx.get_journal().record(p, "delete", tool="delete_path")
        shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink()
        return ToolResult(True, f"borrado {p}", meta={"undo_id": entry.op_id})

    @reg.tool("undo", "Deshace la última mutación, o todas las de esta tarea.",
              {"type": "object", "properties": {
                  "scope": {"type": "string", "enum": ["last", "task"]}}},
              access={"write"})
    def undo(ctx: ToolContext, scope: str = "last"):
        j = ctx.get_journal()
        if scope == "task" and ctx.task_id:
            return ToolResult(True, f"revertidas {j.undo_task(ctx.task_id)} operaciones")
        e = j.undo_last()
        return ToolResult(bool(e), f"revertido: {e.target}" if e else "",
                          error=None if e else "nada que deshacer")

    # ------------------------------------------------------------- ejecución

    @reg.tool("run_command", "Ejecuta un comando de shell y devuelve su salida.",
              {"type": "object", "properties": {
                  "command": {"type": "string"}, "cwd": {"type": "string"},
                  "timeout": {"type": "integer"}},
               "required": ["command"]}, access={"exec"}, dangerous=True)
    async def run_command(command: str, ctx: ToolContext,
                          cwd: str | None = None, timeout: int = 120):
        workdir = ctx.resolve(cwd) if cwd else ctx.cwd
        workdir.mkdir(parents=True, exist_ok=True)
        if ctx.dry_run:
            return ToolResult(True, f"[dry-run] ejecutaría en {workdir}: {command}")
        try:
            proc = await asyncio.create_subprocess_shell(
                command, cwd=str(workdir),
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
                env={**os.environ, **ctx.env})
            # §7.3 — inscribir el proceso para que la parada de emergencia
            # pueda alcanzarlo. Sin esto, pulsar "parar" dejaba corriendo
            # cualquier cosa que hubiera lanzado el agente.
            from ..cancel import supervisor
            supervisor().register_process(ctx.task_id, proc)
            try:
                out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            finally:
                supervisor().forget_process(ctx.task_id, proc)
            text = out.decode("utf-8", errors="replace")
            return ToolResult(proc.returncode == 0,
                              f"$ {command}\n{text}\n[rc={proc.returncode}]",
                              error=None if proc.returncode == 0
                              else f"rc={proc.returncode}",
                              meta={"rc": proc.returncode})
        except asyncio.TimeoutError:
            # kill() sin wait() deja el transporte sin limpiar: el proceso queda
            # zombi y asyncio lanza "Event loop is closed" al recolectarlo.
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
            return ToolResult(False, "", error=f"timeout tras {timeout}s")

    @reg.tool("python_exec", "Ejecuta código Python en un proceso aparte.",
              {"type": "object", "properties": {"code": {"type": "string"}},
               "required": ["code"]}, access={"exec"}, dangerous=True)
    async def python_exec(code: str, ctx: ToolContext):
        # `python_executable()` y NO `sys.executable`: dentro del .exe este
        # último es el propio .exe, así que la herramienta con la que el
        # enjambre ejecuta Python relanzaba MAGI y devolvía su salida como si
        # fuera la del código. Ver `paths.python_executable`.
        interprete = python_executable()
        if interprete is None:
            return ToolResult(False, "", error=_SIN_PYTHON)
        script = ctx.cwd / f"_magi_exec_{os.getpid()}.py"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(code, encoding="utf-8")
        try:
            return await run_command(f'"{interprete}" "{script.name}"', ctx=ctx,
                                     timeout=120)
        finally:
            script.unlink(missing_ok=True)

    @reg.tool("run_tests", "Ejecuta pytest sobre una ruta. Es la herramienta que "
                           "convierte una opinión sobre el código en evidencia.",
              {"type": "object", "properties": {
                  "path": {"type": "string"}, "k": {"type": "string"}}},
              access={"exec"})
    async def run_tests(ctx: ToolContext, path: str = "tests", k: str = ""):
        # Sin esto, en el .exe la herramienta que «convierte una opinión en
        # evidencia» devolvía la salida de MAGI arrancando. Balthasar critica
        # habiendo ejecutado: eso es lo que le da autoridad, y en el binario
        # publicado no ejecutaba nada.
        interprete = python_executable()
        if interprete is None:
            return ToolResult(False, "", error=_SIN_PYTHON)
        cmd = f'"{interprete}" -m pytest {path} -q --no-header'
        if k:
            cmd += f' -k "{k}"'
        return await run_command(cmd, ctx=ctx, timeout=300)

    # ------------------------------------------------------------------- red

    @reg.tool("web_fetch", "Descarga una URL y devuelve su texto.",
              {"type": "object", "properties": {"url": {"type": "string"}},
               "required": ["url"]}, access={"net"})
    async def web_fetch(url: str):
        try:
            import httpx
        except ImportError:
            return ToolResult(False, "", error="httpx no instalado")
        # User-Agent de navegador real: con "MAGI/9.0" los sitios devuelven
        # 403 (visto con britannica.com) porque lo identifican como bot.
        headers = {
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/131.0.0.0 Safari/537.36"),
            "Accept": ("text/html,application/xhtml+xml,application/xml;"
                       "q=0.9,*/*;q=0.8"),
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
        }
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30,
                                         headers=headers) as c:
                r = await c.get(url)
                r.raise_for_status()
                text = re.sub(r"<script.*?</script>|<style.*?</style>", "",
                              r.text, flags=re.DOTALL | re.I)
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text).strip()
                return ToolResult(True, text[:20000], meta={"status": r.status_code})
        except Exception as e:
            return ToolResult(False, "", error=str(e))

    # -------------------------------------------------- git / gh / build
    # Acceso real al sistema de desarrollo: git y gh CLI con las credenciales
    # del usuario (heredadas vía os.environ en run_command), compilación del
    # binario y entornos aislados. Todas se apoyan en run_command, que ya
    # inscribe el proceso en el supervisor de parada (§7.3).

    @reg.tool("git", "Ejecuta un comando de git en el repo. Operaciones comunes: "
              "status, add, commit -m, push, pull, log, diff, branch, checkout.",
              {"type": "object",
               "properties": {"args": {"type": "string",
                                       "description": "argumentos tras 'git', ej: 'status --short'"}},
               "required": ["args"]}, access={"exec"}, dangerous=True)
    async def git(args: str, ctx: ToolContext):
        return await run_command(f"git {args}", ctx=ctx)

    @reg.tool("gh", "Ejecuta la GitHub CLI. Para runs de Actions, releases, "
              "workflows y gestión del repo. Ej: 'run list', 'workflow run "
              "release.yml -f tag=v5.1.1', 'release list'.",
              {"type": "object",
               "properties": {"args": {"type": "string",
                                       "description": "argumentos tras 'gh'"}},
               "required": ["args"]}, access={"exec"}, dangerous=True)
    async def gh(args: str, ctx: ToolContext):
        return await run_command(f"gh {args}", ctx=ctx)

    @reg.tool("build_exe", "Compila el ejecutable de MAGI con PyInstaller "
              "(onefile, noconsole). Reproduce el build del workflow release.yml. "
              "Devuelve la ruta del .exe generado.",
              {"type": "object",
               "properties": {"name": {"type": "string",
                                       "description": "nombre base (sin .exe)",
                                       "default": "MAGI-IDE-v5"}},
               "required": []}, access={"exec"}, dangerous=True)
    async def build_exe(name: str = "MAGI-IDE-v5", ctx: ToolContext = None):
        if ctx is None:
            return ToolResult(False, "", error="sin contexto")
        raiz = ctx.cwd
        front = raiz / "magi-gui" / "dist"
        if not front.exists():
            return ToolResult(False, "",
                              error="falta magi-gui/dist: ejecuta primero el build del frontend (npm run build)")
        # Las exclusiones son las mismas que release.yml, para que compilar
        # desde el enjambre y compilar en CI den el mismo binario. Sin ellas,
        # PyInstaller se cuelga importando torch al resolver DLLs.
        excluidos = ("torch torchvision torchaudio tensorflow transformers "
                     "onnxruntime markitdown magika PyQt5 PySide2 PySide6")
        cmd = (f'python -m PyInstaller --clean --onefile --noconsole '
               f'--name "{name}" --icon "assets/icon.ico" '
               f'--add-data "assets;assets" '
               f'--add-data "magi-gui/dist;magi-gui/dist" '
               + "".join(f'--exclude-module {m} ' for m in excluidos.split())
               + 'magi/main.py')
        res = await run_command(cmd, ctx=ctx, timeout=600)
        if res.ok:
            exe = raiz / "dist" / f"{name}.exe"
            res.meta = {**(res.meta or {}), "exe": str(exe)}
        return res

    @reg.tool("create_venv", "Crea un entorno virtual Python limpio para "
              "reproducir el entorno de CI. Devuelve la ruta del python del venv.",
              {"type": "object",
               "properties": {"path": {"type": "string",
                                       "description": "ruta del venv (defecto: .venv)",
                                       "default": ".venv"},
                              "python": {"type": "string",
                                         "description": "intérprete base",
                                         "default": "python"}},
               "required": []}, access={"exec"}, dangerous=True)
    async def create_venv(path: str = ".venv", python: str = "python",
                          ctx: ToolContext = None):
        if ctx is None:
            return ToolResult(False, "", error="sin contexto")
        res = await run_command(f'"{python}" -m venv "{path}"', ctx=ctx, timeout=120)
        if res.ok:
            venv_python = (ctx.cwd / path / "Scripts" / "python.exe"
                           if sys.platform == "win32"
                           else ctx.cwd / path / "bin" / "python")
            res.meta = {**(res.meta or {}), "python": str(venv_python)}
        return res

    # §5.3 — toolchain de ingeniería inversa y emuladores.
    # Se registra aquí para que los tres nodos del enjambre lo tengan: sin este
    # enganche, todo magi/modules/reverse/ sería código correcto que ningún
    # agente puede invocar.
    # §6 — conocimiento del mundo: macro, actualidad, fundamentales y el
    # registro de tesis calibrado. Mismo motivo que el enganche de abajo: sin
    # esta línea, todo magi/modules/world/ sería andamiaje.
    try:
        from magi.modules.world.tools import register_world_tools
        register_world_tools(reg)
    except Exception as e:            # pragma: no cover
        import logging
        logging.getLogger(__name__).warning(
            "[tools] herramientas del mundo no disponibles: %s", e)

    try:
        from magi.modules.reverse.tools import register_reverse_tools
        register_reverse_tools(reg)
    except Exception as e:            # pragma: no cover
        import logging
        logging.getLogger(__name__).warning(
            "[tools] toolchain de RE no disponible: %s", e)

    # §5 — fábrica de artefactos con bucle de observación. Es lo que permite
    # que Balthasar ARRANQUE un juego y mire la captura en vez de opinar sobre
    # el código.
    try:
        from magi.modules.studio.tools import register_studio_tools
        register_studio_tools(reg)
    except Exception as e:            # pragma: no cover
        import logging
        logging.getLogger(__name__).warning(
            "[tools] fábrica de artefactos no disponible: %s", e)

    return reg


# Perfiles por rol (Plan MAGI 9.0 §2.2).
MELCHIOR_TOOLS = None                      # todo: propone y construye
BALTHASAR_DENY = {"write"}                 # lee y ejecuta, no escribe
CASPER_TOOLS = {"read_file", "list_dir", "grep", "glob", "run_tests",
                "run_command",
                # el árbitro necesita poder comprobar afirmaciones sobre
                # arquitecturas sin fiarse de lo que digan los otros dos
                "binary_identify", "console_profile", "analyze_port",
                "compare_consoles",
                # el árbitro debe poder mirar el artefacto, no fiarse del acta
                "observe_artifact", "inspect_image"}

# ---------------------------------------------------------------------------
# Dominios de herramientas (§2.2).
#
# El catálogo entra ENTERO en cada prompt de cada agente. Con 30 herramientas
# pasó de 3200 caracteres, y compactar las descripciones ya no daba más de sí.
# La respuesta correcta no es recortar texto: es no ofrecer el toolchain de
# ingeniería inversa a quien está escribiendo un informe, ni el compositor de
# manga a quien depura un dynarec.
# ---------------------------------------------------------------------------

CORE_TOOLS = {
    "read_file", "write_file", "edit_file", "delete_path", "list_dir", "grep",
    "glob", "run_command", "python_exec", "run_tests", "web_fetch", "undo",
}

# Herramientas de repositorio y publicación.
#
# Estaban en CORE_TOOLS, o sea en el prompt de TODOS los dominios, y eso puso
# rojo a test_catalog_stays_within_a_free_provider_window: el catálogo de
# reverse/MELCHIOR llegó a 2782 caracteres con el techo en 2700.
#
# El propio test dice qué hacer cuando salta: "reducir PARÁMETROS o afinar el
# dominio, no reescribir textos". Afinar el dominio es lo correcto aquí, y no
# solo por el número: quien está portando un dynarec de PSP a Vita no necesita
# `gh workflow run` ni `build_exe` en su prompt. Son herramientas de otra
# tarea, y ofrecerlas es ruido que empuja al modelo a usarlas.
DEVOPS_TOOLS = {
    "git", "gh", "build_exe", "create_venv",
}

REVERSE_TOOLS = {
    "binary_identify", "console_profile", "disassemble", "binary_strings",
    "emulate_code", "differential_test", "compare_consoles", "analyze_port",
    "suggest_port_base", "re_toolchain_status", "index_emulator",
    "locate_subsystem", "compare_emulators", "binary_entropy",
}

STUDIO_TOOLS = {
    "observe_artifact", "inspect_image", "studio_backends",
    "compose_manga_page", "validate_manga_layout",
    "render_animatic", "record_program",
}

WORLD_TOOLS = {
    "macro_snapshot", "fred_series", "compare_countries", "news_headlines",
    "company_fundamentals", "owner_earnings", "dcf_valuation",
    "quality_checklist", "record_thesis", "resolve_thesis",
    "calibration_report",
}

_DOMAIN_HINTS = {
    # Repositorio y publicación. Sin estas pistas, `git` y `gh` quedarían
    # inalcanzables cuando se los pide por su nombre — el mismo fallo que
    # tuvo "gasto militar" en el dominio del mundo.
    "devops": (
        "git", "commit", "rama", "branch", "push", "pull", "merge",
        "repositorio", "repo", "github", "actions", "workflow", "runner",
        "ci", "release", "publicar", "tag", "etiqueta", "compilar",
        "compila", "build", "ejecutable", ".exe", "pyinstaller", "venv",
        "entorno virtual", "despliegue", "desplegar", "versión", "version",
    ),
    "reverse": (
        "binario", "firmware", "rom", "emulador", "emular", "desensambl",
        "dynarec", "ensamblador", "ingenieria inversa", "ingeniería inversa",
        "psp", "vita", "nintendo", "gba", "nds", "n64", "playstation",
        "mips", "arm", "opcode", "instruccion", "instrucción", "elf", "dump",
        "decompil", "portar", "port ", "consola",
    ),
    "studio": (
        "juego", "videojuego", "manga", "cómic", "comic", "viñeta", "vineta",
        "imagen", "dibujo", "documento", "informe", "pdf", "docx", "vídeo",
        "video", "pantalla", "captura", "sprite", "render",
    ),
    # Estas pistas se comprueban en tests/test_wiring.py contra frases escritas
    # como se pregunta de verdad, no como me salió a mí al redactar la lista.
    # Así apareció que "gasto militar" —un indicador que el módulo SÍ ofrece—
    # no activaba el dominio: la herramienta existía y era inalcanzable.
    "world": (
        "macro", "economia", "economía", "inflacion", "inflación", "pib",
        "tipos de interes", "tipos de interés", "bono", "curva", "paro",
        "desempleo", "geopolit", "geopolít", "mercado", "bolsa", "accion",
        "acción", "acciones", "invertir", "inversion", "inversión", "valorar",
        "valoracion", "valoración", "empresa", "cotizada", "balance",
        "beneficio", "dividendo", "buffett", "dcf", "flujo de caja",
        "fundamentales", "actualidad", "noticia", "banco central", "fed",
        "bce", "reserva federal", "deuda", "divisa", "tipo de cambio",
        "tesis", "calibrac", "prediccion", "predicción", "pronostico",
        "pronóstico",
        # Indicadores del Banco Mundial: sin estas, el catálogo los ofrece y
        # el enrutado no llega a ellos.
        "militar", "armament", "poblacion", "población", "demograf",
        "exportacion", "exportación", "comercio", "arancel", "sancion",
        "sanción", "banco mundial", "per capita", "per cápita",
        "esperanza de vida", "renovable", "pais", "país", "paises", "países",
    ),
}


# Los dominios y sus conjuntos de herramientas, DERIVADOS de _DOMAIN_HINTS.
#
# Estaban escritos a mano como {"core", "reverse", "studio"} en dos sitios.
# Al añadir el dominio del mundo (§6) las dos copias quedaron desfasadas a la
# vez, y el síntoma habría sido silencioso: `domains_for("")` devolvía un
# conjunto que ya no era "todos", así que la rama de "sin pista, ofrécelo
# todo" empezaba a recortar el catálogo sin que nadie lo pidiera.
#
# Es la misma clase de fallo que la lista de andamiaje de test_wiring.py: una
# lista mantenida a mano que se desincroniza de la realidad. Si se deriva, no
# puede desincronizarse.
_DOMAIN_TOOLSETS: dict[str, set[str]] = {
    "devops": DEVOPS_TOOLS,
    "reverse": REVERSE_TOOLS,
    "studio": STUDIO_TOOLS,
    "world": WORLD_TOOLS,
}
ALL_DOMAINS: set[str] = {"core"} | set(_DOMAIN_HINTS)


def domains_for(task_hint: str) -> set[str]:
    """
    Qué dominios de herramientas necesita una tarea.

    Sin pista, se ofrecen todos: es preferible un catálogo grande a que el
    agente no pueda hacer su trabajo por una heurística demasiado estrecha.
    """
    hint = (task_hint or "").lower()
    if not hint.strip():
        return set(ALL_DOMAINS)
    found = {"core"}
    for domain, needles in _DOMAIN_HINTS.items():
        if any(n in hint for n in needles):
            found.add(domain)
    return found


def registry_for_role(role: str, task_hint: str = "") -> ToolRegistry:
    """
    Catálogo de un nodo, acotado al dominio de la tarea cuando se conoce.

    `task_hint` es el enunciado del usuario. Con él, una tarea de emuladores no
    carga el compositor de manga y viceversa: menos tokens por turno y menos
    ruido para el modelo.
    """
    base = build_registry()
    domains = domains_for(task_hint)

    allowed: set[str] | None = None
    if domains != ALL_DOMAINS:
        allowed = set(CORE_TOOLS)
        for dominio in domains:
            allowed |= _DOMAIN_TOOLSETS.get(dominio, set())

    r = role.upper()
    if r == "BALTHASAR":
        return base.subset(allowed=allowed, deny_access=BALTHASAR_DENY)
    if r == "CASPER":
        keep = CASPER_TOOLS if allowed is None else (CASPER_TOOLS & allowed)
        return base.subset(allowed=keep)
    return base.subset(allowed=allowed)
