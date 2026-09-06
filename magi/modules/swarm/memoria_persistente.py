"""
Lo que MAGI sabe entre proyectos, y lo que se rescató de lo descartado (P10).

LAS DOS MEDICIONES QUE OBLIGARON A ESCRIBIR ESTO
================================================
1. `EpisodicMemory` funciona, pero vive dentro de un `task_id`: al cerrar la
   tarea se pierde. En la ronda 1 de YabauseVita se descartó atacar el camino
   de render porque medía el 1,27 % del tiempo. Ese dato no pertenece a una
   tarea: pertenece al sistema. Sin un sitio donde ponerlo, la ronda 4 de otro
   proyecto vuelve a proponerlo.

2. `magi/data/memoria/controles.json` existía en disco desde el 30-ago y **no
   lo llamaba nadie**. El mismo fallo que el release v5.11.0 destapó con
   `bitacora.py`. Un fichero de conocimiento que ningún prompt lee es un
   fichero de conocimiento que no existe.

QUÉ AÑADE SOBRE LA MEMORIA EPISÓDICA
====================================
`EpisodicMemory` responde «no repitas esto». Esto responde algo distinto:
**«esto se descartó, y esto de dentro seguía siendo bueno»**.

Un enfoque perdedor no es basura. La cadena `-Ofast -flto -ffast-math` se
revirtió porque no arreglaba el cuelgue del dynarec — pero medir que NO era la
causa fue el resultado, y sin registrarlo el siguiente que vea esos flags
volverá a sospechar de ellos primero. El campo `rescatable` existe para eso.

QUÉ NO HACE
===========
No resume. Igual que la bitácora, copia literal: un resumen generado es el
mecanismo que produjo un `PORTING_NOTES.md` que fue cierto y dejó de serlo.

No escribe por su cuenta durante el debate. Registrar un descarte es un acto
deliberado al cerrar una ronda, con la medición delante — no un efecto
secundario de que a un agente le pareciera mala una idea.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path

__all__ = [
    "raiz", "cargar_controles", "cargar_descartes", "registrar_descarte",
    "para_el_prompt", "pertinente",
]

#: La memoria vive en el repo, no en %APPDATA%. Es deliberado: si vive fuera
#: del control de versiones no viaja con el sistema, no se revisa en un diff y
#: se pierde al reinstalar — que es exactamente cómo se perdieron los scripts
#: de la sesión del 30-ago.
SUBRUTA = Path("magi") / "data" / "memoria"
DESCARTES = "descartes.jsonl"
CONTROLES = "controles.json"

TOPE_DESCARTES = 8      # cuántos entran en el prompt, los más recientes
TOPE_CONSOLAS = 6


def _plano(s: str) -> str:
    sin = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in sin if not unicodedata.combining(c))


def raiz(inicio: str | os.PathLike | None = None) -> Path | None:
    """
    Dónde vive la memoria. La variable de entorno gana para que una prueba
    pueda apuntar a un directorio de mentira sin tocar el repo real.
    """
    env = os.environ.get("MAGI_MEMORIA")
    if env and Path(env).is_dir():
        return Path(env)
    base = Path(inicio or os.getcwd()).resolve()
    for carpeta in (base, *base.parents):
        cand = carpeta / SUBRUTA
        if cand.is_dir():
            return cand
    return None


def _leer_json(ruta: Path, por_defecto):
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return por_defecto


def cargar_controles(inicio=None) -> dict:
    r = raiz(inicio)
    if r is None:
        return {}
    return _leer_json(r / CONTROLES, {})


def cargar_descartes(inicio=None) -> list[dict]:
    """
    JSONL y no JSON: se añade con una línea, sin releer ni reescribir el
    fichero entero. Un formato que obliga a reescribirlo todo para añadir una
    entrada acaba con entradas que nadie añade.
    """
    r = raiz(inicio)
    if r is None:
        return []
    f = r / DESCARTES
    if not f.is_file():
        return []
    fuera = []
    for linea in f.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        try:
            fuera.append(json.loads(linea))
        except ValueError:
            continue        # una línea rota no invalida el histórico
    return fuera


def registrar_descarte(*, proyecto: str, ronda: str, enfoque: str,
                       filosofia: str = "", motivo: str, medicion: str = "",
                       rescatable: str = "", inicio=None) -> bool:
    """
    Añade un descarte. `rescatable` es el campo que justifica el módulo:
    qué sobrevive del enfoque perdedor.
    """
    r = raiz(inicio)
    if r is None:
        return False
    entrada = {
        "proyecto": proyecto, "ronda": ronda, "enfoque": enfoque,
        "filosofia": filosofia, "motivo": motivo,
        "medicion": medicion, "rescatable": rescatable,
    }
    try:
        with open(r / DESCARTES, "a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


_ENCARGO = re.compile(
    r"\b(emulador|emulacion|consola|mando|control(es)?|boton(es)?|"
    r"yabause|saturn|vita|psp|dynarec|rom|juego|jugar|input|"
    r"optimiz\w*|ronda\s*\d|descart\w*)\b"
)


def pertinente(encargo: str) -> bool:
    return bool(_ENCARGO.search(_plano(encargo)))


def _bloque_controles(encargo: str, datos: dict) -> str:
    consolas = datos.get("consolas") or {}
    if not consolas:
        return ""
    t = _plano(encargo)
    # Primero las consolas que el encargo nombra; si no nombra ninguna, las
    # primeras. Mandar las 30 sería el catálogo de treinta nombres al final del
    # prompt que la caja de herramientas ya demostró que se ignora.
    nombradas = [k for k in consolas if _plano(k) in t]
    elegidas = (nombradas or list(consolas))[:TOPE_CONSOLAS]
    filas = []
    for k in elegidas:
        v = consolas[k]
        if isinstance(v, dict):
            botones = v.get("botones") or v.get("mando") or ""
            notas = v.get("notas") or v.get("nota") or ""
            nota = f" — {notas}" if notas else ""
            filas.append(f"- **{k}**: {botones}{nota}")
        else:
            filas.append(f"- **{k}**: {v}")
    extra = ""
    if datos.get("pc_jugando") and re.search(
            r"\b(teclado|pc|ordenador|computadora|gamepad|mando)\b", t):
        teclas = datos["pc_jugando"].get("teclado", {})
        extra = ("- **pc_jugando**: teclado — "
                 + str(teclas.get("convencion_extendida", "")) + "\n")
    return ("\nMANDOS QUE YA CONOCES (memoria permanente):\n"
            + "\n".join(filas) + "\n" + extra)


def _bloque_descartes(encargo: str, descartes: list[dict]) -> str:
    if not descartes:
        return ""
    t = _plano(encargo)
    propios = [d for d in descartes
               if _plano(str(d.get("proyecto", ""))) in t] or descartes
    filas = []
    for d in propios[-TOPE_DESCARTES:]:
        cabecera = (f"- [{d.get('proyecto', '?')} · {d.get('ronda', '?')}] "
                    f"{d.get('enfoque', '?')}")
        if d.get("filosofia"):
            cabecera += f"  (filosofía: {d['filosofia']})"
        filas.append(cabecera)
        filas.append("    descartado porque: " + str(d.get("motivo", "?")))
        if d.get("medicion"):
            filas.append("    medición: " + str(d["medicion"]))
        if d.get("rescatable"):
            filas.append("    SE RESCATA: " + str(d["rescatable"]))
    return ("\nENFOQUES YA DESCARTADOS, Y QUÉ SE SALVÓ DE CADA UNO:\n"
            + "\n".join(filas) + "\n")


#: Decompilación (estilo dusklight) y puertos PC->consola. Se inyecta SOLO
#: cuando el encargo habla de eso: es conocimiento denso y en cada prompt
#: sería ruido que tapa lo que importa.
_DECOMP = re.compile(
    r"\b(decomp\w*|decompil\w*|recompil\w*|dusklight|ghidra|objdiff|"
    r"reverse\w*|ingenieri\w*\s*inversa|port\w*|puerto|vita2d|vitasdk|"
    r"vpk|byte[- ]?match\w*)\b")


def _bloque_decomp(datos: dict) -> str:
    d = datos.get("decompilacion_y_puertos") or {}
    if not d:
        return ""
    flujo = d.get("flujo_en_5_pasos") or {}
    pasos = "\n".join(f"  {k}: {v}" for k, v in flujo.items())
    reglas = "\n".join(f"  - {r}" for r in d.get("reglas_duras") or [])
    return ("DECOMPILACIÓN Y PUERTOS (memoria permanente):\n"
            + f"  {d.get('que_es', '')}\nFLUJO:\n" + pasos
            + "\nREGLAS DURAS:\n" + reglas + "\n")


def para_el_prompt(encargo: str, inicio=None) -> str:
    """
    Va ARRIBA del prompt. Vacío si no aplica: un aviso repetido en cada
    encargo se convierte en ruido y acaba tapando los que sí importan.
    """
    t = _plano(encargo)
    if not (pertinente(encargo) or _DECOMP.search(t)):
        return ""
    datos = cargar_controles(inicio)
    # CONTEXTO LILIM (v12): los hechos locales que tocan a ESTE encargo, en
    # ms. Si Lilim cae, la memoria permanente sigue — el except es a propósito.
    try:
        from ..lilim import contexto as _ctx_lilim
        ctx_l = _ctx_lilim(encargo)
    except Exception:
        ctx_l = ""
    ctrl = _bloque_controles(encargo, datos)
    desc = _bloque_descartes(encargo, cargar_descartes(inicio))
    decomp = _bloque_decomp(datos) if _DECOMP.search(t) else ""
    if not (ctrl or desc or decomp or ctx_l):
        return ""
    return (
        "\n\nMEMORIA PERMANENTE DE MAGI. Esto no es de esta tarea: es lo que el "
        "sistema sabe de antes y sobrevive a la sesión.\n"
        + ctx_l + ctrl + desc + decomp +
        "\nUn enfoque descartado puede volver a proponerse — pero entonces hay "
        "que decir qué cambió respecto al motivo del descarte. Y lo marcado "
        "como SE RESCATA se reutiliza en vez de volver a descubrirse."
    )
