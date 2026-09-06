"""
LILIM — la capa local superveloz de MAGI (megaplan v12).

QUÉ ES
======
La capa LOCAL, determinista y sin red que responde al instante lo que el
sistema ya sabe, CON PROCEDENCIA, y escala al enjambre cuando no lo sabe.

NO es un LLM y no razona: es un índice vivo sobre memoria versionada
(controles.json, repos_top.json, AUTOMODELO). Su honestidad es su valor:

  · Lo que sabe → respuesta en ms con `fuente:` y `falsable contra: <URL>`.
  · Lo que no sabe → "NO LO SÉ (local) — escala al enjambre". NUNCA inventa.

La misión Tetris (5-sep) midió por qué esto importa: los proveedores
gratuitos tardan 3-22 s por llamada, fallan a menudo, y una tarea trivial
puede gastar 20 minutos. Cada pregunta que Lilim responde local es una
llamada de red que no se gasta — y cada respuesta lleva su evidencia.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

__all__ = ["pregunta", "repos_de", "NO_LO_SE"]

NO_LO_SE = "NO LO SÉ (local) — escala al enjambre: razonamiento y verificación de nube."

_RAIZ = Path(__file__).resolve().parents[2] / "data" / "memoria"


def _cargar(nombre: str) -> dict:
    ruta = _RAIZ / nombre
    if not ruta.exists():
        return {}
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _plano(s: str) -> str:
    import unicodedata
    sin = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in sin if not unicodedata.combining(c))


def repos_de(tema: str) -> str:
    """Los repos curados de un tema, con su URL (metadatos, no clones)."""
    datos = _cargar("repos_top.json")
    t = _plano(tema)
    if not t:
        return ("temas del índice: "
                + ", ".join(sorted({r["tema"] for r in datos.get("repos", [])})))
    hits = [r for r in datos.get("repos", [])
            if t in _plano(r.get("tema", "")) or t in _plano(r.get("nombre", ""))
            or any(w in _plano(r.get("para_que", "")) for w in t.split() if len(w) > 3)]
    if not hits:
        return (NO_LO_SE + " Temas disponibles: "
                + ", ".join(sorted({r["tema"] for r in datos.get("repos", [])})))
    filas = [f"- {r['nombre']} — {r['para_que']}\n  {r['url']}"
             f"  (curado {datos.get('curado', '?')}; falsable contra la URL)"
             for r in hits]
    return ("REPOS DEL ÍNDICE PARA '" + tema + "' (memoria local, "
            + str(datos.get("curado", "?")) + "):\n" + "\n".join(filas))


def pregunta(pregunta_texto: str) -> str:
    """
    La respuesta local más rápida posible, o NO_LO_SE. Nada intermedio.
    """
    if not isinstance(pregunta_texto, str) or not pregunta_texto.strip():
        return NO_LO_SE
    t = _plano(pregunta_texto)

    datos = _cargar("controles.json")

    # 1. decomp / puertos
    if re.search(r"\b(decomp|dusklight|ghidra|objdiff|byte.?match|recompil)\w*",
                 t):
        d = datos.get("decompilacion_y_puertos") or {}
        if d:
            pasos = "; ".join(f"{k}: {v[:90]}" for k, v in
                              (d.get("flujo_en_5_pasos") or {}).items())
            return (f"DECOMP (memoria local, {datos.get('actualizado', '?')}): "
                    f"{d.get('que_es', '')} Flujo: {pasos}. "
                    "fuente: controles.json#decompilacion_y_puertos — "
                    "falsable contra: los repos del flujo (ghidra, objdiff).")

    # 2. controles de consola / PC
    consolas = datos.get("consolas") or {}
    for nombre, valor in consolas.items():
        if _plano(nombre).replace("_", " ") in t or _plano(nombre) in t:
            cuerpo = valor if isinstance(valor, str) else json.dumps(
                valor, ensure_ascii=False)
            return (f"CONTROLES {nombre} (memoria local, "
                    f"{datos.get('actualizado', '?')}): {cuerpo[:600]} "
                    "fuente: controles.json — falsable contra: "
                    "la documentación del mando de la consola.")
    if re.search(r"\b(teclado|pc|ordenador|computadora|gamepad|xinput)\b", t):
        pc = datos.get("pc_jugando") or {}
        if pc:
            return ("PC PARA JUGAR (memoria local, "
                    f"{datos.get('actualizado', '?')}): "
                    + json.dumps(pc, ensure_ascii=False)[:700]
                    + " fuente: controles.json#pc_jugando")

    # 3. repos
    if re.search(r"\b(repo|repositorio|github|libreria|biblioteca)\b", t):
        for palabra in t.split():
            if len(palabra) > 3:
                r = repos_de(palabra)
                if NO_LO_SE not in r:
                    return r

    # 4. lo que no está en memoria NO se inventa
    return NO_LO_SE
