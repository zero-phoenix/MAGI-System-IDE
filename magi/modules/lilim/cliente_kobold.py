"""
Cliente local para KoboldCpp — el motor neural de Lilim en MAGI.

QUÉ ES
======
Cliente asíncrono y ligero (basado en la biblioteca estándar) para
comunicarse con la instancia local de KoboldCpp (típicamente ejecutando
`koboldcpp-oldpc.exe` con Qwen 2.5 1.5B Instruct GGUF Q4_K_M).

SOPORTE DE HARDWARE LEGACY
==========================
- Compatible con CPUs sin AVX2 (Intel Core i7-3770 Ivy Bridge).
- Conexión sobre HTTP loopback (127.0.0.1:5001).
- API dual: `/v1/chat/completions` (OpenAI format con soporte multimodal)
  y `/api/v1/generate` (Kobold nativo).
- Si KoboldCpp no está levantado, degrada limpiamente sin bloquear.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

URL_POR_DEFECTO = "http://127.0.0.1:5001"
MODELO_LOCAL = "qwen2.5-1.5b-instruct"


class ClienteKobold:
    """Cliente HTTP asíncrono para el runtime local KoboldCpp."""

    def __init__(self, url_base: str | None = None) -> None:
        self.url_base = (
            url_base
            or os.getenv("MAGI_KOBOLD_URL")
            or URL_POR_DEFECTO
        ).rstrip("/")

    async def _post_json(
        self, endpoint: str, payload: dict[str, Any], timeout: float = 30.0
    ) -> dict[str, Any] | None:
        url = f"{self.url_base}{endpoint}"
        datos = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=datos,
            method="POST",
            headers={"Content-Type": "application/json"},
        )

        def _enviar():
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except (urllib.error.URLError, TimeoutError, OSError) as err:
                logger.debug("KoboldCpp no disponible en %s: %s", url, err)
                return None
            except Exception as err:
                logger.warning("Error inesperado en KoboldCpp (%s): %s", url, err)
                return None

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _enviar)

    async def _get_json(self, endpoint: str, timeout: float = 2.0) -> dict[str, Any] | None:
        url = f"{self.url_base}{endpoint}"
        req = urllib.request.Request(url, method="GET")

        def _enviar():
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except Exception:
                return None

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _enviar)

    async def esta_disponible(self, timeout: float = 1.5) -> bool:
        """Comprueba si el servidor local de KoboldCpp está respondiendo."""
        info = await self._get_json("/api/extra/version", timeout=timeout)
        if info is not None:
            return True
        modelos = await self._get_json("/v1/models", timeout=timeout)
        return modelos is not None

    async def chat(
        self,
        mensajes: list[dict[str, Any]],
        max_tokens: int = 512,
        temperature: float = 0.2,
        timeout: float = 45.0,
    ) -> str | None:
        """
        Ejecuta una petición de chat OpenAI-compatible en KoboldCpp.
        """
        payload = {
            "model": MODELO_LOCAL,
            "messages": mensajes,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        res = await self._post_json("/v1/chat/completions", payload, timeout=timeout)
        if not res:
            return None
        try:
            return res["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError):
            return None

    async def generar(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.2,
        timeout: float = 45.0,
    ) -> str | None:
        """
        Generación de texto simple sobre el modelo cargado.
        """
        mensajes = [{"role": "user", "content": prompt}]
        return await self.chat(
            mensajes, max_tokens=max_tokens, temperature=temperature, timeout=timeout
        )

    async def vision(
        self,
        pregunta: str,
        imagen: bytes | str | Path,
        max_tokens: int = 512,
        timeout: float = 45.0,
    ) -> str | None:
        """
        Análisis multimodal pasando una imagen (bytes, base64 o ruta a archivo)
        junto con la instrucción al proyector visual de KoboldCpp.
        """
        b64_str: str = ""
        if isinstance(imagen, (str, Path)) and Path(imagen).is_file():
            b64_str = base64.b64encode(Path(imagen).read_bytes()).decode("ascii")
        elif isinstance(imagen, bytes):
            b64_str = base64.b64encode(imagen).decode("ascii")
        elif isinstance(imagen, str):
            b64_str = imagen
        else:
            return None

        contenido = [
            {"type": "text", "text": pregunta},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_str}"}},
        ]
        mensajes = [{"role": "user", "content": contenido}]
        return await self.chat(mensajes, max_tokens=max_tokens, temperature=0.1, timeout=timeout)

    async def estado(self) -> dict[str, Any]:
        """Obtiene información de versión y rendimiento del motor local."""
        version = await self._get_json("/api/extra/version") or {}
        perf = await self._get_json("/api/extra/perf") or {}
        modelos = await self._get_json("/v1/models") or {}
        return {
            "disponible": bool(version or modelos),
            "version": version.get("version", "desconocida"),
            "modelo": (modelos.get("data") or [{}])[0].get("id", MODELO_LOCAL),
            "perf": perf,
        }
