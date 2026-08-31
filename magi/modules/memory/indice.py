"""
«¿Esto ya se intentó?» en un milisegundo y sin gastar red (Fase 6).

LA MEDICIÓN QUE ORDENÓ EL DISEÑO
================================
Antes de escribir esto medí el corpus de verdad: **224 documentos, 2,7 MB** de
texto entre bitácora, memoria, docs y código. Con eso:

    índice completo reconstruido .... 100 ms
    consulta ......................... 1 ms

Ese número decide toda la arquitectura, y decide en contra de lo que yo mismo
había propuesto. Con 2,7 MB **no hace falta nada más**:

  - No hay persistencia. Reconstruir cuesta 100 ms; mantener un índice en disco
    sincronizado cuesta invalidación, corrupción y un fichero que se queda
    viejo. Se reconstruye y punto.
  - No hay embeddings. Yo propuse un modelo de 90 MB sobre la GPU. Sobre 2,7 MB
    de texto eso es sobre-ingeniería: añade una descarga, una dependencia y un
    modo de fallo nuevo para buscar en algo que FTS5 recorre en un milisegundo.
    Vuelve a tener sentido si el corpus crece dos órdenes de magnitud.
  - No hay GPU. Con `torch` compilado sin CUDA, usar la tarjeta exigiría
    descargar 2,5 GB. Para 224 documentos.

FTS5 viene dentro de Python: cero instalación, cero descarga, cero clave.

QUÉ RESUELVE
============
Que Melchior pueda preguntar «¿alguien ya intentó esto?» **antes** de proponer,
sin gastar una llamada de red y sin depender de que se acuerde. Es el mismo
problema que la bitácora, en el otro sentido: la bitácora empuja lo importante
al prompt; esto deja buscar lo que no cabía.
"""
from __future__ import annotations

import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

__all__ = ["Indice", "construir", "sanear_consulta"]

#: Qué se indexa y con qué etiqueta. El orden importa: es el de utilidad para
#: la pregunta «¿ya se intentó?», no el de tamaño.
FUENTES = (
    ("descartes", ("magi/data/memoria",), (".jsonl", ".json")),
    ("bitacora", ("../yabausevita-zp/docs", "docs"), (".md",)),
    ("docs", ("docs",), (".md",)),
    ("codigo", ("magi",), (".py",)),
)

EXCLUIR = ("python-embed", "_attic", "node_modules", "__pycache__", ".git")
MAX_BYTES = 512 * 1024      # un fichero mayor que esto no es prosa buscable


def sanear_consulta(q: str) -> str:
    """
    FTS5 tiene sintaxis propia y revienta con puntuación corriente: buscar
    `1.27` da `fts5: syntax error near "."`. Un buscador que falla cuando le
    pasas un número es un buscador que nadie usa dos veces.

    Se conservan los operadores que sí valen (`AND`, `OR`, `NOT`, `NEAR`,
    comillas) y se entrecomilla el resto.
    """
    q = (q or "").strip()
    if not q:
        return ""
    if '"' in q:
        return q                     # el usuario ya sabe lo que hace
    fuera = []
    for pieza in q.split():
        if pieza.upper() in ("AND", "OR", "NOT") or pieza.upper().startswith("NEAR"):
            fuera.append(pieza.upper() if pieza.upper() in ("AND", "OR", "NOT")
                         else pieza)
            continue
        # Un token con algo que no sea letra/dígito/guion bajo va entrecomillado.
        if re.fullmatch(r"[\w\-]+", pieza, re.UNICODE):
            fuera.append(pieza)
        else:
            limpio = pieza.replace('"', "")
            fuera.append(f'"{limpio}"')
    return " ".join(fuera)


@dataclass
class Acierto:
    fuente: str
    ruta: str
    fragmento: str

    def __str__(self) -> str:
        return f"[{self.fuente}] {self.ruta}\n    …{self.fragmento}…"


class Indice:
    """
    Índice en memoria. Vive lo que viva el proceso: reconstruirlo cuesta menos
    que razonar sobre si está al día.
    """

    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute(
            "CREATE VIRTUAL TABLE d USING fts5(fuente, ruta, texto)")
        self.documentos = 0
        self.caracteres = 0
        self.ms_construccion = 0.0

    def añadir(self, fuente: str, ruta: str, texto: str) -> None:
        self.db.execute("INSERT INTO d VALUES (?,?,?)", (fuente, ruta, texto))
        self.documentos += 1
        self.caracteres += len(texto)

    def buscar(self, consulta: str, limite: int = 12) -> list[Acierto]:
        q = sanear_consulta(consulta)
        if not q:
            return []
        try:
            filas = self.db.execute(
                "SELECT fuente, ruta, snippet(d, 2, '', '', '…', 18) "
                "FROM d WHERE d MATCH ? ORDER BY rank LIMIT ?",
                (q, limite)).fetchall()
        except sqlite3.OperationalError:
            # Consulta que ni saneada es válida: devolver vacío, no reventar.
            return []
        return [Acierto(f, r, s) for f, r, s in filas]

    def resumen(self) -> dict:
        return {"documentos": self.documentos,
                "caracteres": self.caracteres,
                "ms_construccion": round(self.ms_construccion, 1)}


def _raiz(inicio=None) -> Path | None:
    base = Path(inicio or Path.cwd()).resolve()
    for c in (base, *base.parents):
        if (c / "magi").is_dir():
            return c
    return None


def construir(inicio=None) -> Indice:
    """Reconstruye el índice entero. Medido: ~100 ms sobre 224 documentos."""
    t0 = time.time()
    idx = Indice()
    raiz = _raiz(inicio)
    if raiz is None:
        idx.ms_construccion = (time.time() - t0) * 1000
        return idx

    vistos: set[Path] = set()
    for etiqueta, carpetas, sufijos in FUENTES:
        for carpeta in carpetas:
            d = (raiz / carpeta).resolve()
            if not d.is_dir():
                continue
            for p in d.rglob("*"):
                if p in vistos or not p.is_file() or p.suffix not in sufijos:
                    continue
                if any(x in str(p) for x in EXCLUIR):
                    continue
                try:
                    if p.stat().st_size > MAX_BYTES:
                        continue
                    texto = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                vistos.add(p)
                idx.añadir(etiqueta, str(p.relative_to(raiz)
                                         if raiz in p.parents else p), texto)
    idx.db.commit()
    idx.ms_construccion = (time.time() - t0) * 1000
    return idx
