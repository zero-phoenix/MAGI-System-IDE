"""
LILIM RÁPIDA — el puente multimodal de baja latencia (megaplan v12 §3).

EL MODELO DE ROL: como GLM-5.3-Flash frente a los modelos frontera, Lilim
existe para que lo rápido no pague lo caro. Su cadena de decisión, cada
nivel más costoso que el anterior:

  1. MEMORIA (0 ms)     — lo que MAGI ya sabe, con procedencia.
  2. HECHOS LOCALES (ms)— propiedades deterministas de ficheros/imágenes
                           (dimensiones, formato, peso): sin modelo, sin
                           inventar nada.
  3. PUENTE FLASH (s)   — una sola llamada a un modelo rápido multimodal
                           (glm-5.3-flash si hay clave; si no, la familia
                           gratuita más sana) para lo que SÍ necesita
                           inteligencia: traducir frases, describir una
                           imagen, resumir un fichero corto.
  4. NO LO SÉ           — y el enjambre (el debate de tres nodos) queda para
                           lo complejo: código, builds, verificaciones.

QUÉ NO HACE: tareas complejas — las demandan tiempo y son del enjambre. Si
el encargo huele a trabajo serio, la respuesta es entregarlo al enjambre con
el contexto de Lilim ya montado.
"""
from __future__ import annotations

import os
import struct
from pathlib import Path

__all__ = ["es_rapida", "hechos_de_imagen", "hechos_de_fichero", "puente"]

#: Umbral de longitud: por encima, NO es tarea rápida — es del enjambre.
MAX_RAPIDA = 600


def es_rapida(texto: str) -> bool:
    """
    ¿Esta petición es de las que Lilim atiende sola? Corta, y sin verbos de
    trabajo serio (escribir código, compilar, auditar, debatir). Es la
    heurística del «18B activados de 320B»: poca maquinaria para la mayor
    parte del tráfico real.
    """
    if not isinstance(texto, str) or not texto.strip():
        return False
    if len(texto) > MAX_RAPIDA:
        return False
    t = texto.lower()
    complejos = ("escribe ", "crea ", "compila", "construye", "implementa",
                 "refactoriza", "audita", "optimiza", "debate", "analiza a "
                 "fondo", "hazme un", "haz un", "diseña", "proyecta")
    return not any(c in t for c in complejos)


# ------------------------------------------------------- hechos multimodales

def hechos_de_imagen(ruta: str | Path) -> dict:
    """
    Propiedades DETERMINISTAS de una imagen, sin modelo y sin inventar:
    formato y dimensiones leídos de la cabecera (PNG/JPEG/GIF/BMP). Lo que
    la imagen CONTIENE (semántica) requiere visión: eso lo decide `puente`.
    """
    p = Path(ruta)
    if not p.is_file():
        return {"error": "no existe el fichero"}
    datos = p.read_bytes()[:64]
    peso = p.stat().st_size
    info: dict = {"fichero": p.name, "bytes": peso}
    if datos[:8] == b"\x89PNG\r\n\x1a\n" and len(datos) >= 24:
        info["formato"] = "PNG"
        ancho, alto = struct.unpack(">II", datos[16:24])
        info["dimensiones"] = [ancho, alto]
    elif datos[:3] == b"\xff\xd8\xff":
        info["formato"] = "JPEG"
        dims = _jpeg_dimensiones(p)
        if dims:
            info["dimensiones"] = list(dims)
    elif datos[:6] in (b"GIF87a", b"GIF89a"):
        info["formato"] = "GIF"
        ancho, alto = struct.unpack("<HH", datos[6:10])
        info["dimensiones"] = [ancho, alto]
    elif datos[:2] == b"BM":
        info["formato"] = "BMP"
        ancho, alto = struct.unpack("<ii", datos[18:26])
        info["dimensiones"] = [ancho, alto]
    else:
        info["formato"] = "desconocido (cabecera no reconocida)"
    info["nota"] = ("contenido semántico: requiere visión — pídeselo al "
                    "puente (multimodal) o al enjambre")
    return info


def _jpeg_dimensiones(p: Path) -> tuple[int, int] | None:
    """Dimensiones JPEG caminando los marcadores SOF. Sin dependencias."""
    datos = p.read_bytes()
    i = 2
    while i + 9 < len(datos):
        if datos[i] != 0xFF:
            i += 1
            continue
        marca = datos[i + 1]
        if marca in (0xC0, 0xC1, 0xC2):
            alto, ancho = struct.unpack(">HH", datos[i + 5:i + 9])
            return ancho, alto
        if marca in (0xD8, 0xD9) or 0xD0 <= marca <= 0xD7:
            i += 2
            continue
        longitud = struct.unpack(">H", datos[i + 2:i + 4])[0]
        i += 2 + longitud
    return None


def hechos_de_fichero(ruta: str | Path) -> dict:
    """Peso, extensión y SHA256 — la procedencia mínima de CUALQUIER fichero."""
    import hashlib
    p = Path(ruta)
    if not p.is_file():
        return {"error": "no existe el fichero"}
    return {"fichero": p.name, "bytes": p.stat().st_size,
            "extension": p.suffix.lower(),
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest()[:32] + "…"}


# ----------------------------------------------------------------- el puente

#: Cómo se llama al puente flash. La clave vive en el entorno: sin clave,
#: Lilim cae a las familias gratuitas — y sin red, al NO LO SÉ. Nunca exige.
_API_BASE = os.environ.get(
    "LILIM_API_BASE", "https://api.z.ai/api/paas/v4/chat/completions")
_MODELO_FLASH = os.environ.get("LILIM_MODELO", "glm-5.3-flash")


def _clave() -> str | None:
    return os.environ.get("LILIM_API_KEY") or os.environ.get("ZAI_API_KEY")


async def puente(pregunta: str, imagen_b64: str | None = None) -> str:
    """
    La respuesta rápida con inteligencia REAL pero acotada: una llamada al
    modelo flash con temperatura baja y SIN herramientas. Es la antítesis
    del enjambre: una voz, una vuelta, sin debate.
    """
    clave = _clave()
    if not clave:
        # Sin clave: las familias gratuitas del enjambre en modo flash.
        try:
            from magi.core.providers.base import CompletionRequest, Message
            reg = None
            mensajes = [Message("system",
                                "Responde BREVE y factual. Si no lo sabes, "
                                "di exactamente: NO LO SÉ. No inventes."),
                        Message("user", pregunta[:2000])]
            req = CompletionRequest(messages=mensajes, temperature=0.3,
                                    max_tokens=300)
            from magi.core.providers.cloud import get_registry
            reg = await get_registry()
            resp = await reg.complete(req)
            texto = (resp.content or "").strip()
            return (f"[vía nube gratuita] {texto}" if texto
                    else "NO LO SÉ (puente sin respuesta)")
        except Exception as e:                     # sin red o todo caído
            return f"NO LO SÉ (puente no disponible: {e})"
    # Con clave: el modelo flash multimodal (imagen opcional vía image_url).
    import json as _json
    import urllib.request
    contenido: list | str = pregunta
    if imagen_b64:
        contenido = [
            {"type": "text", "text": pregunta},
            {"type": "image_url",
             "image_url": {"url": f"data:image/png;base64,{imagen_b64}"}},
        ]
    cuerpo = _json.dumps({
        "model": _MODELO_FLASH,
        "messages": [{"role": "user",
                      "content": contenido}],
        "temperature": 0.3, "max_tokens": 500,
    }).encode("utf-8")
    peticion = urllib.request.Request(
        _API_BASE, data=cuerpo, method="POST",
        headers={"Authorization": f"Bearer {clave}",
                 "Content-Type": "application/json"})
    import asyncio
    try:
        def _llamar():
            with urllib.request.urlopen(peticion, timeout=30) as r:
                return _json.loads(r.read())
        respuesta = await asyncio.get_running_loop().run_in_executor(
            None, _llamar)
        texto = (respuesta.get("choices") or [{}])[0].get(
            "message", {}).get("content", "").strip()
        return f"[vía {_MODELO_FLASH}] {texto}" if texto else \
            "NO LO SÉ (puente sin contenido)"
    except Exception as e:
        return f"NO LO SÉ (puente falló: {e})"
