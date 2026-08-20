"""
Cierre de entrega de artefactos al Escritorio (MEGA PLAN v6.0 §B1 y §C4).

La fábrica ya existe (studio/artifacts.py observa, studio/packager.py empaqueta
a .exe onefile con venv propio); lo que faltaba era el ciclo de ENTREGA con
integridad, y la compuerta C4 ANTES de gastar tiempo y banda de red:

  1. preflight(): qué falta por comprobar antes de fabricar — un .exe sin
     250 MB libres o sin intérprete no se promete, se dice antes.
  2. fabricar_y_entregar(): une los bloques Python de la propuesta final,
     los verifica con el mismo ProposalVerifier (guardián GUI headless que
     corre el Tetris de verdad 30 frames y sale con rc=0), empaqueta con
     studio.packager si hace falta, y entrega:
       - copia final con SHA-256 al Escritorio real (paths.escritorio:
         SHGetKnownFolderPath → OneDrive como debe ser),
       - respaldo en workspace/artifacts/entregas para el preview de la GUI,
       - evento `swarm.artefacto_listo` + TERMINAL_OUT para la consola.

Si algo falla, el InformeEntrega lleva el MOTIVO y el log de pasos, nunca
excepciones mudas: quien prometió el .exe puede decirle al enjambre qué
faltó (Plan v6.0 C4: "fallo temprano con mensaje claro").
"""
from __future__ import annotations

import hashlib
import re
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from ...core.bus import BusEvent
from ...core.paths import data_dir, escritorio, python_executable, workspace_dir
from ...core.verification import ProposalVerifier, extract_blocks
from .packager import build_project_exe

__all__ = ["InformeEntrega", "preflight", "fabricar_y_entregar"]

# Marcadores de GUI compartidos con la heurística de studio/packager: un
# programa con bucle de eventos se empaqueta a .exe (y sin consola) por
# defecto; un script de consola viaja como .py.
_GUI_MARKS = re.compile(r"pygame|tkinter|turtle|PyQt|PySide|mainloop", re.I)

# Caracteres prohibidos en nombres de archivo Windows + colección de los
# nombres reservados (CON, PRN, AUX, NUL, COM1..9, LPT1..9) que dan un
# FileNotFoundError esotérico si se usan como nombre de archivo.
_NOMBRE_NOSANO = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_NOMBRES_RESERVADOS = {"con", "prn", "aux", "nul"} | {
    f"com{i}" for i in range(1, 10)} | {f"lpt{i}" for i in range(1, 10)}

_MB = 1024 * 1024
_PISO_EXE_MB = 250  # un onefile de PyInstaller con pygame ronda los 100 MB de trabajo


@dataclass
class InformeEntrega:
    """Resultado del ciclo fabricar+entregar. `ok=False` SIEMPRE trae motivo."""

    ok: bool
    tipo: str = "script"                  # "script" | "exe"
    ruta: Path | None = None              # archivo final entregado
    nombre: str = ""
    sha256: str = ""
    bytes_: int = 0
    destino: str = ""                     # "Escritorio" | "workspace"
    motivo: str | None = None             # por qué falló, si falló
    pasos: list[str] = field(default_factory=list)


def _nombre_sano(nombre: str) -> str:
    """Nombre de archivo válido en Windows y Unix, sin rutas ni caracteres raros."""
    texto = _NOMBRE_NOSANO.sub("_", (nombre or "artefacto")).strip()
    texto = re.sub(r"\s+", "_", texto)
    if not texto:
        texto = "artefacto"
    # SIN mirar en qué sistema corremos, y a propósito. La entrega termina en
    # el Escritorio de Windows —ahí es donde `con.py` o `aux.exe` se vuelven
    # un fichero que no se puede abrir ni borrar—, así que el nombre tiene que
    # salir sano de aquí venga de donde venga el proceso. Condicionarlo a
    # `sys.platform` hacía además que la misma función devolviera cosas
    # distintas en el CI (Linux) y en tu máquina: el test decía la verdad en
    # una y mentía en la otra, y el job `test` del release llevaba rojo desde
    # que se escribió.
    if texto.lower().split(".", 1)[0] in _NOMBRES_RESERVADOS:
        texto = "magi_" + texto
    if len(texto) > 128:
        raiz, _, ext = texto.rpartition(".")
        texto = (raiz[:120] + ("." + ext if ext else "")) or "artefacto"
    return texto


def _con_extension(nombre_sano: str, exe: bool) -> str:
    """Añade o corrige la extensión según el tipo de entrega."""
    raiz, _, ext = nombre_sano.rpartition(".")
    if ext in ("exe", "py"):
        return raiz + (".exe" if exe else ".py")
    return nombre_sano + (".exe" if exe else ".py")


def _unir_bloques(content: str) -> str:
    """Todos los bloques ```python de la propuesta final, en orden."""
    bloques = [codigo for lang, codigo in extract_blocks(content) if lang == "python"]
    return "\n\n".join(bloques)


def _quiere_gui(nombre: str, fuente: str) -> bool:
    """¿Esta entrega es una ventana/juego y no un script de consola?"""
    return bool(_GUI_MARKS.search(fuente)) or ".exe" in nombre.lower()


def preflight(*, nombre: str, exe: bool) -> dict:
    """
    Compuerta C4: requisitos comprobables antes de fabricar.

    `problemas` bloquea la fabricación; `avisos` solo avisan. Un .exe
    necesita ≈250 MB libres (el onefile trabaja con el doble de su tamaño) y
    un intérprete de verdad — `python_executable()` es None dentro del
    bundle sin Python embebido, y prometer un exe sin intérprete es mandar
    al packager a un error a mitad de camino.
    """
    problemas: list[str] = []
    avisos: list[str] = []
    sano = _nombre_sano(nombre)
    if not nombre.strip():
        problemas.append("el nombre no da un nombre de archivo válido")
    if sano != _nombre_sano(sano):
        avisos.append(f'el nombre se saneó a "{sano}"')
    if python_executable() is None:
        problemas.append("no hay intérprete de Python (python_executable() devuelve None)")
    if exe:
        libre_mb = shutil.disk_usage(data_dir()).free // _MB
        if libre_mb < _PISO_EXE_MB:
            problemas.append(
                f"el empaquetado a .exe necesita ≈{_PISO_EXE_MB} MB libres "
                f"y solo hay {libre_mb} MB en {data_dir()}")
        if shutil.which("pyinstaller") is None:
            avisos.append("PyInstaller no está global; se instalará en el venv "
                          "del empaquetado (requiere red)")
    return {"ok": not problemas, "problemas": problemas, "avisos": avisos,
            "nombre_sano": sano}


def _resumir_error(veredicto) -> str:
    detalle = getattr(veredicto, "detail", None) or veredicto.render()
    return detalle[:1500]


async def fabricar_y_entregar(
    content: str,
    *,
    nombre: str,
    task_id: str = "",
    bus=None,
    empaquetar: bool | None = None,
    destino: str = "escritorio",
) -> InformeEntrega:
    """
    Fabrica la propuesta final y la entrega con integridad.

    `empaquetar=None` decide solo: GUI/juego → .exe; script de consola → .py.
    `destino="escritorio"` cae en el Escritorio real; si no hay Escritorio
    accesible, o se pide `"workspace"`, cae en workspace/entregas.
    """
    informe = InformeEntrega(ok=False, nombre=_nombre_sano(nombre))

    def paso(msg: str) -> None:
        informe.pasos.append(msg)

    fuente = _unir_bloques(content)
    if not fuente:
        informe.motivo = "la propuesta final no contiene bloques de código Python"
        paso("sin bloques de código que fabricar")
        return informe

    exe = (empaquetar if empaquetar is not None else _quiere_gui(nombre, fuente))
    compuerta = preflight(nombre=nombre, exe=exe)
    if not compuerta["ok"]:
        informe.motivo = "preflight C4: " + "; ".join(compuerta["problemas"])
        paso("compuerta C4 bloqueada")
        return informe
    paso("compuerta C4 superada"
         + (f" (aviso: {compuerta['avisos'][0]})" if compuerta["avisos"] else ""))

    proyecto = data_dir() / "entregas" / uuid.uuid4().hex[:12]
    proyecto.mkdir(parents=True, exist_ok=True)
    maestro = proyecto / "main.py"
    maestro.write_text(fuente, encoding="utf-8")
    paso(f"bloques unidos en proyecto temporal {proyecto.name}")

    veredicto = await ProposalVerifier(run_code=True).verify(content)
    if not veredicto.ok:
        informe.motivo = "la verificación falló:\n" + _resumir_error(veredicto)
        paso("verificación NO superada; no se entrega nada")
        shutil.rmtree(proyecto, ignore_errors=True)
        return informe
    paso("verificación superada (guardián GUI incluido)")

    base = _con_extension(_nombre_sano(nombre), exe)
    if exe:
        construccion = await build_project_exe(
            proyecto,
            name=Path(base).stem,
            requirements=["pygame"] if "pygame" in fuente else None,
            # `clean=True` borra el build al terminar: sin output_exe el
            # PackagerResult llega con un exe_path ya eliminado. El exe nace
            # dentro del proyecto temporal y se copia desde ahí, vivo.
            output_exe=proyecto / base,
        )
        if not construccion.ok:
            informe.motivo = "el empaquetado falló: " + (construccion.error or "")
            paso(f"empaquetado a .exe falló: {construccion.error or ''}")
            shutil.rmtree(proyecto, ignore_errors=True)
            return informe
        entregable = construccion.exe_path
        tipo = "exe"
        paso(f".exe construido: {entregable.name}")
    else:
        entregable = maestro
        tipo = "script"
        paso("script listo (sin empaquetar)")

    if destino == "escritorio":
        carpeta = escritorio()
        etiqueta = "Escritorio"
        if carpeta is None:
            paso("sin Escritorio accesible; entrega en workspace/entregas")
            carpeta = workspace_dir() / "entregas"
            etiqueta = "workspace"
    else:
        carpeta = workspace_dir() / "entregas"
        etiqueta = "workspace"
    carpeta.mkdir(parents=True, exist_ok=True)

    final = carpeta / base
    contador = 1
    while final.exists():  # nunca piso lo ya entregado: sufijo _1, _2, ...
        final = carpeta / f"{final.stem}_{contador}{final.suffix}"
        contador += 1
    shutil.copy2(entregable, final)
    sha = hashlib.sha256(final.read_bytes()).hexdigest()
    tam = final.stat().st_size

    respaldo = workspace_dir() / "artifacts" / "entregas"
    respaldo.mkdir(parents=True, exist_ok=True)
    shutil.copy2(final, respaldo / final.name)
    paso("copia de respaldo en workspace/artifacts/entregas para el preview")

    informe.ok = True
    informe.tipo = tipo
    informe.ruta = final
    informe.nombre = final.name
    informe.sha256 = sha
    informe.bytes_ = tam
    informe.destino = etiqueta
    paso(f"{tipo} entregado en {etiqueta}: {final} ({tam} bytes, sha256 {sha[:16]}…)")

    # El proyecto temporal ya está copiado (destino + respaldo); se limpia
    # para no acumular cientos de MB en data_dir/entregas.
    shutil.rmtree(proyecto, ignore_errors=True)

    if bus is not None:
        await bus.publish(BusEvent(
            topic="swarm.artefacto_listo",
            payload={
                "task_id": task_id,
                "nombre": final.name,
                "tipo": tipo,
                "ruta": str(final),
                "sha256": sha,
                "bytes": tam,
                "destino": etiqueta,
            },
        ))
        await bus.publish(BusEvent(
            topic="TERMINAL_OUT",
            payload={
                "agent": "SYSTEM",
                "content": (f"[fábrica] {final.name} entregado en {etiqueta}: {final} "
                            f"({tam} bytes, sha256 {sha[:16]}…)"),
            },
        ))
    return informe
