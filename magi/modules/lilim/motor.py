"""
El MOTOR de Lilim: la arquitectura de GLM-5.3-Flash traducida a un sistema
local determinista (megaplan v12 §3). No imita el modelo — imita su FORMA
DE TRABAJAR:

  · ACTIVACIÓN ESCASA (MoE: 18B de 320B)     → de todos los dominios de
    memoria, solo se "activan" los que la pregunta necesita. El resto no se
    lee ni se gasta. Y se REPORTA: `[activado 2/6 dominios, 0.4 %]`.
  · ATENCIÓN HÍBRIDA (lineal + dispersa)     → un "estado" lineal (la caché
    de la sesión: lo preguntado hace un momento) más recuperación dispersa
    por palabras clave sobre el índice.
  · INDEXPOOL (4 claves → 1)                 → UNA sola pasada de índice que
    devuelve todo el contexto de una vez, no cuatro búsquedas separadas.
  · CUANTIZACIÓN (W8A8)                      → la memoria vive compacta
    (JSON/JSONL en disco) y se carga PEREZOSA: un dominio frío no ocupa
    memoria hasta que se activa.
  · EPD (encode → prefill → decode)          → tres etapas separadas y
    medibles: codificar la pregunta, recuperar el contexto, componer.

La respuesta lleva su métrica de activación pegada — como el modelo declara
sus parámetros activados, Lilim declara los suyos.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from . import NO_LO_SE, _plano
from . import novedades as _novedades
from . import pregunta as _pregunta_base
from . import repos_de as _repos_de

__all__ = ["MotorLilim", "motor", "Resolucion"]


# ------------------------------------------------------------- los dominios
#
# Cada dominio es un "experto" del MoE: un cargador PEREZOSO (nunca se lee
# hasta que se activa) y el patrón que lo activa. Añadir conocimiento nuevo
# = añadir un dominio aquí; el motor no cambia.

def _dom_controles_pregunta(texto: str) -> str | None:
    r = _pregunta_base(texto)
    return None if r == NO_LO_SE else r


@dataclass
class Dominio:
    nombre: str
    patron: re.Pattern
    responder: object          # callable(texto) -> str | None
    _cargado: bool = field(default=False, repr=False)
    _peso_bytes: int = field(default=0, repr=False)


def _peso_de(nombre_fichero: str) -> int:
    from . import _RAIZ
    p = _RAIZ / nombre_fichero
    return p.stat().st_size if p.exists() else 0


DOMINIOS: list[Dominio] = [
    Dominio("controles", re.compile(
        r"\b(mando|control|consola|teclado|gamepad|xinput|jugar|juego|"
        r"boton|ps_vita|saturn|ps2|nintendo|xbox)\w*\b"),
        _dom_controles_pregunta),
    Dominio("decomp", re.compile(
        r"\b(decomp|dusklight|ghidra|objdiff|byte.?match|recompil|puerto|"
        r"port)\w*\b"),
        _pregunta_base),
    Dominio("repos", re.compile(
        r"\b(repo|repositorio|github|libreria|biblioteca)\w*\b"),
        lambda t: _repos_de(_palabra_clave(t))),
    Dominio("novedades", re.compile(
        r"\b(novedad|noticia|nuevo|avance|2023|2024|2025|2026|bateria|llm|"
        r"ia|modelo)\w*\b"),
        lambda t: _novedades(_palabra_clave(t)) or NO_LO_SE),
]


def _palabra_clave(texto: str) -> str:
    """La palabra más 'temática' del texto (la clave del índice)."""
    mejores = ("baterias", "ia", "vita", "decomp", "gamedev", "emudev")
    t = _plano(texto)
    for m in mejores:
        if m in t:
            return m
    palabras = re.findall(r"[a-záéíóúñü]{4,}", t)
    return palabras[0] if palabras else ""


@dataclass
class Resolucion:
    respuesta: str
    dominios_activados: int
    dominios_totales: int
    bytes_activados: int
    bytes_totales: int
    ms: float
    de_cache: bool

    def activacion(self) -> str:
        """La línea MoE: qué fracción de Lilim se activó para responder."""
        pct = (100 * self.bytes_activados / self.bytes_totales
               if self.bytes_totales else 0)
        return (f"[activado {self.dominios_activados}/"
                f"{self.dominios_totales} dominios, "
                f"{pct:.1f}% de la memoria, {self.ms:.1f} ms"
                + (", de caché" if self.de_cache else "") + "]")


class MotorLilim:
    """
    El ciclo EPD de Lilim. Una sola instancia viva: su `_estado` es la
    atención lineal (la sesión), su `activar()` la dispersa.
    """

    def __init__(self):
        self._estado: dict[str, str] = {}      # caché de sesión (lineal)
        self._bytes_totales = sum(_peso_de(f) for f in
                                  ("controles.json", "repos_top.json",
                                   "novedades.json", "idiomas.json",
                                   "descartes.jsonl", "AUTOMODELO.json"))
        self._dominios_vivos = [d for d in DOMINIOS]
        self._dominios_vivos[0]._peso_bytes = _peso_de("controles.json")
        self._dominios_vivos[1]._peso_bytes = _peso_de("controles.json")
        self._dominios_vivos[2]._peso_bytes = _peso_de("repos_top.json")
        self._dominios_vivos[3]._peso_bytes = _peso_de("novedades.json")

    # --------------------------------------------- 1. ENCODE: la pregunta
    def _codificar(self, texto: str) -> set[str]:
        """Dispersa: qué dominios activa esta pregunta. 0 activados es una
        respuesta válida — significa NO LO SÉ sin leer nada."""
        t = _plano(texto)
        return {d.nombre for d in self._dominios_vivos
                if d.patron.search(t)}

    # ------------------------------------------ 2. PREFILL: recuperación
    def _recuperar(self, texto: str,
                   activos: set[str]) -> tuple[str | None, bool]:
        """Devuelve (respuesta, de_cache). Atención lineal primero: el estado
        de la sesión manda — una repetición no vuelve a calcular nada."""
        for previo, respuesta in reversed(list(self._estado.items())):
            if previo == texto:
                return respuesta, True
        for d in self._dominios_vivos:
            if d.nombre in activos:
                r = d.responder(texto)
                d._cargado = True               # el dominio frío se calienta
                if r and r != NO_LO_SE:
                    self._estado[texto] = r     # el estado crece (lineal)
                    return r, False
        return None, False

    # -------------------------------------------- 3. DECODE: la respuesta
    def resolver(self, texto: str) -> Resolucion:
        t0 = time.perf_counter()
        if not isinstance(texto, str) or not texto.strip():
            activos: set[str] = set()
            respuesta = NO_LO_SE
            de_cache = False
        else:
            activos = self._codificar(texto)
            respuesta, de_cache = self._recuperar(texto, activos)
            if respuesta is None:
                respuesta = NO_LO_SE
        activados = {d.nombre for d in self._dominios_vivos
                     if d.nombre in activos and d._peso_bytes}
        bytes_activados = sum(d._peso_bytes for d in self._dominios_vivos
                              if d.nombre in activos)
        ms = (time.perf_counter() - t0) * 1000
        return Resolucion(respuesta, len(activados & {d.nombre for d in
                                                      self._dominios_vivos}),
                          len(self._dominios_vivos), bytes_activados,
                          self._bytes_totales, ms, de_cache)


#: La instancia única. Un motor, como un modelo servido: se calienta y vive.
motor = MotorLilim()
