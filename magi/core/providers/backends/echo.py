"""
Backend determinista para tests y modo sin red.

Existe porque en v5.0.28 no había forma de probar el enjambre sin llamar a la
nube: cualquier test dependía de g4f y por tanto no era reproducible.
"""
from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator

from ..base import (
    BaseProvider,
    CompletionRequest,
    CompletionResponse,
    Delta,
    Usage,
)


class EchoProvider(BaseProvider):
    """Devuelve texto predecible. Sin red, sin dependencias, instantáneo."""

    supports_tools = True
    supports_vision = False
    supports_stream = True
    is_local = True
    default_model = "echo-1"

    def __init__(self, provider_id: str = "echo", family: str = "echo",
                 canned: str | None = None, fail_times: int = 0,
                 delay_s: float = 0.0):
        self.id = provider_id
        self.family = family
        self.canned = canned
        self.fail_times = fail_times
        self.delay_s = delay_s
        self._calls = 0

    async def available(self) -> bool:
        return True

    def _render(self, req: CompletionRequest) -> str:
        if self.canned is not None:
            return self.canned
        last = next((m for m in reversed(req.messages) if m.role == "user"), None)
        body = last.content if last else ""
        if not isinstance(body, str):
            body = str(body)
        return f"[{self.id}] {body[:400]}"

    async def complete(self, req: CompletionRequest) -> CompletionResponse:
        started = time.monotonic()
        self._calls += 1
        if self._calls <= self.fail_times:
            raise RuntimeError(f"{self.id}: fallo simulado {self._calls}/{self.fail_times}")
        if self.delay_s:
            await asyncio.sleep(self.delay_s)
        text = self._render(req)
        usage = Usage(
            prompt_tokens=sum(self.estimate_tokens(str(m.content)) for m in req.messages),
            completion_tokens=self.estimate_tokens(text),
        )
        return self._mk_response(text, req.model or self.default_model, started, usage)

    async def stream(self, req: CompletionRequest) -> AsyncIterator[Delta]:
        resp = await self.complete(req)
        words = resp.content.split(" ")
        for i, w in enumerate(words):
            if self.delay_s:
                await asyncio.sleep(self.delay_s / max(1, len(words)))
            yield Delta(text=w + (" " if i < len(words) - 1 else ""),
                        seq=i, done=False, provider_id=self.id)
        yield Delta(text="", seq=len(words), done=True, provider_id=self.id)
