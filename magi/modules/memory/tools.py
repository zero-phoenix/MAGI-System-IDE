"""
El índice, enchufado al enjambre.

`test_wiring` me cazó dejando `indice.py` escrito, probado y sin conectar: el
fallo número 1 de este repositorio, por quinta vez. El test dice literalmente
qué hacer —«conéctalos desde código alcanzable o bórralos; no los añadas a
KNOWN_ORPHANS»— y esto es lo primero.

Quién lo necesita: **Melchior**, antes de proponer. La bitácora empuja al prompt
lo que no puede olvidarse; esto deja buscar lo que no cabía. Sin él, «¿alguien
ya intentó esto?» cuesta una llamada de red y depende de que se acuerde.
"""
from __future__ import annotations

import logging

from ...core.tools.registry import ToolRegistry, ToolResult

logger = logging.getLogger(__name__)

#: El índice se reconstruye en ~100 ms sobre 224 documentos, así que cabría
#: rehacerlo en cada llamada. Se cachea igualmente porque dentro de una misma
#: ronda el corpus no cambia, y 100 ms × N búsquedas sí se nota.
_CACHE: dict[str, object] = {}

MAX_RESULTADOS = 20


def register_memory_tools(reg: ToolRegistry) -> ToolRegistry:
    """Añade la búsqueda en memoria a un registro existente."""

    @reg.tool("search_memory",
              "Busca en TODA la memoria del sistema —bitácora, descartes, docs "
              "y código— sin gastar una llamada de red. Úsala ANTES de "
              "proponer: responde «¿esto ya se intentó?» en milisegundos, y "
              "un enfoque ya descartado con su medición vale más que uno "
              "nuevo sin ella.",
              {"type": "object",
               "properties": {
                   "query": {"type": "string",
                             "description": "términos; admite AND, OR, NOT, "
                                            "NEAR y \"frases exactas\""},
                   "limit": {"type": "integer",
                             "description": "máximo de aciertos (1-20)"}},
               "required": ["query"]},
              access={"read"})
    def search_memory(query: str, limit: int = 8, ctx=None):
        from .indice import construir

        try:
            n = max(1, min(int(limit), MAX_RESULTADOS))
        except (TypeError, ValueError):
            n = 8

        idx = _CACHE.get("idx")
        if idx is None:
            idx = construir()
            _CACHE["idx"] = idx

        aciertos = idx.buscar(query, limite=n)
        if not aciertos:
            # No es un fallo: que no haya nada es un resultado, y uno útil —
            # significa que la idea no se ha intentado todavía.
            return ToolResult(
                True,
                f"Sin coincidencias para {query!r} en {idx.documentos} "
                f"documentos. Nadie ha registrado esto: es terreno nuevo.",
                meta={"aciertos": 0, "documentos": idx.documentos})

        cuerpo = "\n".join(str(a) for a in aciertos)
        return ToolResult(
            True,
            f"{len(aciertos)} coincidencia(s) en {idx.documentos} documentos:\n"
            f"{cuerpo}",
            meta={"aciertos": len(aciertos),
                  "documentos": idx.documentos,
                  "rutas": [a.ruta for a in aciertos]})

    @reg.tool("memory_stats",
              "Cuánta memoria hay indexada y cuánto cuesta consultarla.",
              {"type": "object", "properties": {}}, access={"read"})
    def memory_stats(ctx=None):
        from .indice import construir

        idx = construir()
        _CACHE["idx"] = idx
        r = idx.resumen()
        return ToolResult(
            True,
            f"{r['documentos']} documentos, {r['caracteres']:,} caracteres, "
            f"índice reconstruido en {r['ms_construccion']} ms.",
            meta=r)

    return reg
