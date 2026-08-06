"""
Backend g4f con FAMILIA FIJADA — el arreglo del bug central de v5.0.28.

EL BUG
======
magi/core/providers/cloud.py:117-123 (v5.0.28):

    async def generate(self, system_prompt, user_prompt, model="gpt-4o"):
        if model in ["claude-3.5-sonnet", "qwen-2.5", "deepseek"]:
            model = "gpt-4o"

y luego, en _fetch_from_provider(), la llamada iba SIN parámetro `provider`:

    response = await self.client.chat.completions.create(model=cand, messages=[...])

Resultado: los tres nodos del enjambre pedían familias distintas, las tres se
reescribían a gpt-4o, y g4f auto-ruteaba las tres al mismo sitio. Melchior,
Balthasar y Casper eran EL MISMO MODELO con tres prompts. Por eso las críticas
de Balthasar sonaban genéricas: un modelo criticándose a sí mismo encuentra poco.

EL ARREGLO
==========
g4f sí permite fijar proveedor: create(..., provider=g4f.Provider.Qwen).
Cada instancia de G4FProvider representa UNA familia con una cadena de
candidatos (proveedor, modelo). Si un candidato cae, se prueba el siguiente
DENTRO DE LA MISMA FAMILIA — nunca se salta a otra familia en silencio, porque
eso es justo lo que rompía la diversidad.

Todo gratuito, sin claves de API, sin modelos locales (§I.3 del documento de
arquitectura).
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, AsyncIterator, Iterable

from ..base import (
    BaseProvider, CompletionRequest, CompletionResponse, Delta,
    ProviderError, ProviderUnavailable, Usage,
)

logger = logging.getLogger(__name__)

# (nombre de proveedor g4f, modelo o None para el por defecto del proveedor)
Candidate = tuple[str, str | None]

# Catálogo por familia. Verificado contra g4f 7.9.4: solo proveedores con
# working=True y needs_auth=False.
FAMILY_SPECS: dict[str, list[Candidate]] = {
    "deepseek": [
        ("PhindAi", "deepseek-v3"),
        ("PhindAi", "deepseek"),
        ("Cloudflare", "deepseek-coder-6.7b"),
        ("Cloudflare", "deepseek-distill-qwen-32b"),
    ],
    "qwen": [
        ("Qwen", "qwen3.7-plus"),
        ("Qwen", "qwen3.6-plus"),
        ("Qwen", "qwen3.7-max"),
    ],
    "claude": [
        ("Claude", None),
        ("LMArena", "claude-sonnet-4"),
    ],
    "gemini": [
        ("Gemini", "gemini-3.5-flash"),
        ("Gemini", "gemini-3.1-pro"),
        ("GeminiPro", None),
    ],
    "gpt": [
        ("OpenaiChat", "gpt-5"),
        ("Copilot", "Copilot"),
        ("WeWordle", "gpt-4o"),
        ("Yqcloud", "gpt-4"),
        ("Pollinations", None),
    ],
    "command": [
        ("CohereForAI_C4AI_Command", "command-a-03-2025"),
        ("CohereForAI_C4AI_Command", "command-r-plus"),
    ],
    "glm": [("GLM", None)],
    "llama": [("MetaAI", None), ("Groq", None), ("DeepInfra", None)],
    "perplexity": [("Perplexity", "auto")],
    # Último recurso: auto-router de g4f. Familia "auto" para que el registro
    # sepa que NO garantiza diversidad y lo declare en la GUI.
    "auto": [("AnyProvider", "gpt-4o"), ("AnyProvider", "default")],
}

# Reparto por defecto del enjambre. Coincide con la INTENCIÓN declarada en
# magi/modules/swarm/agents.py (Melchior=deepseek, Balthasar=claude,
# Casper=qwen) que hasta ahora era solo un comentario.
DEFAULT_SWARM_FAMILIES = {
    "MELCHIOR": "deepseek",
    "BALTHASAR": "claude",
    "CASPER": "qwen",
}


def _uses_browser(cls) -> bool:
    """
    True si este proveedor de g4f abre un navegador real para evadir Cloudflare.

    REGLA DEL PROYECTO (§I.3): la inferencia es de nube gratuita y SIN abrir
    nada visible al usuario. Algunos providers de g4f (Gemini, OpenaiChat) lo
    declaran con `use_nodriver=True`; Cloudflare lo niega pero lo activa en
    runtime según el modelo. Abrir una ventana de Chrome rompe la premisa del
    sistema, así que aquí se filtran TODOS los que puedan hacerlo.
    """
    if getattr(cls, "use_nodriver", False):
        return True
    if getattr(cls, "webdriver", None):
        return True
    return False


def _resolve(name: str):
    """Obtiene la clase de proveedor g4f por nombre, o None si no existe.

    Devuelve None (y lo deja caer al siguiente candidato) para cualquier
    proveedor que use navegador: la cadena de la familia salta al siguiente
    candidato que NO abra nada. Si una familia entera dependiera del navegador,
    `complete()` la reporta como agotada en vez de abrir Chrome en silencio.
    """
    try:
        import g4f.Provider as P
    except ImportError:
        return None
    cls = getattr(P, name, None)
    if cls is not None and _uses_browser(cls):
        logger.info(
            "[%s] descartado: abre navegador (prohibido por §I.3)", name)
        return None
    return cls


# Marca para aplicar el guard una sola vez por proceso.
_browser_guard_installed = False


def _disable_g4f_browser() -> None:
    """
    Parchea g4f para que NINGÚN proveedor pueda abrir un navegador.

    La primera línea de defensa (`_resolve`) descarta a los proveedores que
    declaran `use_nodriver`. Pero g4f/requests/__init__.py puede lanzar
    Chrome/zendriver por debajo para evadir retos de Cloudflare en providers
    que NO lo declaran (visto en runtime: una ventana de Chrome se abre al
    pedir inferencia). Aquí se reemplaza el punto de lanzamiento por una
    excepción controlada, así el candidato falla limpio y `complete()` salta
    al siguiente proveedor HTTP en vez de abrir nada visible. §I.3.
    """
    global _browser_guard_installed
    if _browser_guard_installed:
        return
    _browser_guard_installed = True
    try:
        from g4f import requests as g4f_req
    except ImportError:
        return

    # DEFENSA 1 (la que cierra la causa real): que g4f crea que NO tiene
    # ninguna forma de abrir navegador. g4f/requests/__init__.py detecta
    # paquetes al importar y guarda has_webview/has_nodriver/has_cdp; los
    # providers los consultan para decidir si intentan la ruta de navegador.
    # La causa de las ventanas era has_webview=True: g4f detecta pywebview
    # (el backend de la propia GUI de MAGI) y lo reutiliza como navegador
    # para evadir Cloudflare, llamando webview.create_window(). Poner las
    # flags a False hace que ningún provider lo intente.
    for flag in ("has_webview", "has_nodriver", "has_cdp"):
        if hasattr(g4f_req, flag):
            setattr(g4f_req, flag, False)

    class _NoBrowser(Exception):
        """MAGI prohíbe abrir navegadores (§I.3)."""

    # DEFENSA 2: cualquier función de lanzamiento que haya llegado a
    # registrarse queda cortada. Cubre las 6 rutas por las que g4f abre una
    # ventana (nodriver, su sesión, webview, cdp, browser). Por si un provider
    # no consulta las flags y llama directamente.
    async def _blocked(*a, **kw):
        raise _NoBrowser(
            "g4f intentó abrir un navegador, prohibido por §I.3")

    for fn in ("get_nodriver", "get_nodriver_session",
               "get_args_from_nodriver", "get_args_from_browser",
               "get_args_from_webview", "get_args_from_cdp"):
        if hasattr(g4f_req, fn):
            setattr(g4f_req, fn, _blocked)
    logger.info(
        "[g4f] navegador deshabilitado: ningún proveedor abrirá Chrome/webview")


class G4FProvider(BaseProvider):
    """Un backend = UNA familia, con cadena de candidatos dentro de ella."""

    supports_tools = False      # g4f no expone tool-calling fiable; MAGI lo
                                # emula con protocolo de texto (ver tools/protocol.py)
    supports_vision = True
    supports_stream = True
    is_local = False

    def __init__(self, family: str = "auto",
                 candidates: Iterable[Candidate] | None = None,
                 provider_id: str | None = None):
        if family not in FAMILY_SPECS and candidates is None:
            raise ValueError(f"familia desconocida: {family}")
        self.family = family
        self.id = provider_id or f"g4f-{family}"
        self.candidates: list[Candidate] = list(candidates or FAMILY_SPECS[family])
        self.default_model = self.candidates[0][1] or "default"
        self._client = None
        self._live: Candidate | None = None   # candidato que funcionó la última vez

    # ------------------------------------------------------------------ setup

    def _get_client(self):
        if self._client is None:
            _disable_g4f_browser()
            try:
                from g4f.client import AsyncClient
            except ImportError as e:
                raise ProviderUnavailable("g4f no instalado: pip install -U g4f") from e
            self._client = AsyncClient()
        return self._client

    async def available(self) -> bool:
        """Disponible si al menos un candidato de la familia existe en g4f."""
        try:
            self._get_client()
        except ProviderUnavailable:
            return False
        return any(_resolve(name) is not None for name, _ in self.candidates)

    def _ordered(self) -> list[Candidate]:
        """El último candidato que funcionó va primero (afinidad)."""
        if self._live and self._live in self.candidates:
            return [self._live] + [c for c in self.candidates if c != self._live]
        return self.candidates

    # ------------------------------------------------------------- inferencia

    async def complete(self, req: CompletionRequest) -> CompletionResponse:
        started = time.monotonic()
        client = self._get_client()
        messages = [m.to_wire() for m in req.messages]
        errors: list[str] = []

        for name, model in self._ordered():
            cls = _resolve(name)
            if cls is None:
                continue
            try:
                kwargs: dict[str, Any] = {
                    "model": model or "",
                    "messages": messages,
                    "provider": cls,
                }
                if req.temperature is not None:
                    kwargs["temperature"] = req.temperature
                resp = await client.chat.completions.create(**kwargs)
                content = (resp.choices[0].message.content or "") if resp.choices else ""
                if not content.strip():
                    errors.append(f"{name}: respuesta vacía")
                    continue

                self._live = (name, model)
                usage = Usage(
                    prompt_tokens=sum(self.estimate_tokens(str(m["content"]))
                                      for m in messages),
                    completion_tokens=self.estimate_tokens(content),
                )
                logger.info("[%s] respondió %s/%s en %.0fms",
                            self.id, name, model or "default",
                            (time.monotonic() - started) * 1000)
                return self._mk_response(content, f"{name}/{model or 'default'}",
                                         started, usage)
            except Exception as e:
                errors.append(f"{name}: {type(e).__name__}: {e}")
                logger.debug("[%s] candidato %s falló: %s", self.id, name, e)
                continue

        raise ProviderError(
            f"familia '{self.family}' agotada ({len(self.candidates)} candidatos): "
            + " | ".join(errors[:4]))

    async def stream(self, req: CompletionRequest) -> AsyncIterator[Delta]:
        client = self._get_client()
        messages = [m.to_wire() for m in req.messages]
        errors: list[str] = []

        for name, model in self._ordered():
            cls = _resolve(name)
            if cls is None:
                continue
            seq, emitted = 0, False
            try:
                stream = client.chat.completions.stream(
                    model=model or "", messages=messages, provider=cls)
                async for chunk in stream:
                    piece = ""
                    if getattr(chunk, "choices", None):
                        delta = getattr(chunk.choices[0], "delta", None)
                        piece = getattr(delta, "content", "") or ""
                    if piece:
                        emitted = True
                        yield Delta(text=piece, seq=seq, provider_id=self.id)
                        seq += 1
                if emitted:
                    self._live = (name, model)
                    yield Delta(text="", seq=seq, done=True, provider_id=self.id)
                    return
                errors.append(f"{name}: stream vacío")
            except Exception as e:
                errors.append(f"{name}: {e}")
                if emitted:
                    # Ya salió texto a pantalla; reintentar duplicaría.
                    yield Delta(text="", seq=seq, done=True, provider_id=self.id)
                    return
                continue

        raise ProviderError(f"streaming agotado en familia '{self.family}': "
                            + " | ".join(errors[:3]))

    async def complete_vision(self, req: CompletionRequest,
                              image_data_url: str) -> CompletionResponse:
        """Multimodal (lo que Naoko usa para leer capturas de pantalla)."""
        started = time.monotonic()
        client = self._get_client()
        base = [m.to_wire() for m in req.messages[:-1]]
        last = req.messages[-1]
        base.append({
            "role": "user",
            "content": [
                {"type": "text", "text": last.content if isinstance(last.content, str)
                 else str(last.content)},
                {"type": "image_url", "image_url": {"url": image_data_url}},
            ],
        })
        for name, model in self._ordered():
            cls = _resolve(name)
            if cls is None:
                continue
            try:
                resp = await client.chat.completions.create(
                    model=model or "", messages=base, provider=cls)
                content = (resp.choices[0].message.content or "") if resp.choices else ""
                if content.strip():
                    return self._mk_response(content, f"{name}(vision)", started)
            except Exception:
                continue
        raise ProviderError(f"visión no disponible en familia '{self.family}'")


def build_swarm_providers(
    families: dict[str, str] | None = None,
) -> dict[str, G4FProvider]:
    """Un proveedor por nodo del enjambre, cada uno en su familia."""
    fam = families or DEFAULT_SWARM_FAMILIES
    return {role: G4FProvider(family=f, provider_id=f"g4f-{f}")
            for role, f in fam.items()}
