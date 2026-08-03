"""
Protocolo de herramientas por texto (Plan MAGI 9.0 §2.2).

POR QUÉ NO USAMOS function-calling NATIVO
=========================================
El proyecto usa exclusivamente IA de nube gratuita sin claves (restricción del
usuario, y §I.3 del documento de arquitectura). Los proveedores que g4f expone
no soportan tool-calling de forma fiable ni uniforme: unos lo ignoran, otros
devuelven formatos distintos, y cambian sin avisar.

La solución que sí funciona con CUALQUIER modelo: un protocolo de texto. El
modelo emite un bloque cercado y el parser lo extrae. Es robusto, depurable, y
degrada con elegancia — si el modelo no emite ninguna llamada, simplemente ha
terminado su turno.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

# ```tool
# {"tool": "read_file", "args": {"path": "magi/core/bus.py"}}
# ```
_FENCE = re.compile(
    r"```(?:tool|tool_call|magi_tool)\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)
# Variante sin cercado, que algunos modelos producen igualmente.
_BARE = re.compile(
    r"<tool>\s*(\{.*?\})\s*</tool>",
    re.DOTALL | re.IGNORECASE,
)


@dataclass
class ParsedCall:
    name: str
    args: dict[str, Any]
    raw: str


def _coerce(obj: Any) -> tuple[str, dict] | None:
    if not isinstance(obj, dict):
        return None
    name = obj.get("tool") or obj.get("name") or obj.get("function")
    if not isinstance(name, str):
        return None
    args = obj.get("args") or obj.get("arguments") or obj.get("parameters") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = {"_raw": args}
    if not isinstance(args, dict):
        args = {}
    return name.strip(), args


def parse_tool_calls(text: str) -> list[ParsedCall]:
    """Extrae llamadas. Tolerante: los modelos gratuitos formatean regular."""
    calls: list[ParsedCall] = []
    for pattern in (_FENCE, _BARE):
        for m in pattern.finditer(text or ""):
            blob = m.group(1).strip()
            try:
                obj = json.loads(blob)
            except json.JSONDecodeError:
                # a veces meten varios objetos JSON seguidos
                for piece in re.findall(r"\{.*?\}", blob, re.DOTALL):
                    try:
                        c = _coerce(json.loads(piece))
                        if c:
                            calls.append(ParsedCall(c[0], c[1], piece))
                    except json.JSONDecodeError:
                        continue
                continue
            if isinstance(obj, list):
                for item in obj:
                    c = _coerce(item)
                    if c:
                        calls.append(ParsedCall(c[0], c[1], blob))
            else:
                c = _coerce(obj)
                if c:
                    calls.append(ParsedCall(c[0], c[1], blob))
    return calls


def strip_tool_calls(text: str) -> str:
    """Texto visible para el usuario, sin la fontanería."""
    out = _FENCE.sub("", text or "")
    out = _BARE.sub("", out)
    return re.sub(r"\n{3,}", "\n\n", out).strip()


def format_results(results: list) -> str:
    """Resultados de vuelta al modelo, en un formato que entiende sin ambigüedad."""
    parts = []
    for r in results:
        status = "OK" if getattr(r, "ok", False) else "ERROR"
        parts.append(
            f"<tool_result tool=\"{getattr(r, 'tool', '?')}\" status=\"{status}\">\n"
            f"{r.render() if hasattr(r, 'render') else r}\n"
            f"</tool_result>"
        )
    return "\n\n".join(parts)


PROTOCOL_INSTRUCTIONS = """\
## HERRAMIENTAS

Tienes acceso real a la máquina del usuario. Para usar una herramienta, emite un
bloque EXACTAMENTE así (JSON válido, una herramienta por bloque):

```tool
{"tool": "read_file", "args": {"path": "magi/core/bus.py"}}
```

Puedes emitir VARIOS bloques en un mismo turno; se ejecutan en paralelo.
Recibirás los resultados en bloques <tool_result> y podrás seguir trabajando.

Reglas:
- NO inventes el contenido de un fichero: léelo con read_file.
- NO afirmes que un código funciona: ejecútalo con run_command o run_tests.
- Cuando termines, responde SIN ningún bloque ```tool y da tu conclusión.
- Si una herramienta falla, lee el error y prueba otra cosa; no repitas la
  misma llamada idéntica dos veces.

### Catálogo disponible
{catalog}
"""


def build_system_suffix(catalog: str) -> str:
    return PROTOCOL_INSTRUCTIONS.replace("{catalog}", catalog)
