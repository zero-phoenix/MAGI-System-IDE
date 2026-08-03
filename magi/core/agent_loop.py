"""
Bucle de agente con herramientas (Plan MAGI 9.0 §2.2).

Sustituye el "un turno = una llamada al LLM = un texto" de v5.0.28 por
"un turno = N iteraciones de pensar-actuar-observar hasta terminar".

Es el cambio que convierte a MAGI de un sistema que describe trabajo en uno
que lo hace.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from .providers.base import CompletionRequest, Message
from .providers.registry import ProviderRegistry
from .tools import (
    ToolContext, ToolRegistry, format_results, parse_tool_calls,
    strip_tool_calls, build_system_suffix,
)

logger = logging.getLogger(__name__)

OnEvent = Callable[[str, dict], Awaitable[None]] | None


@dataclass
class AgentTurn:
    text: str
    iterations: int
    tool_calls: list[dict] = field(default_factory=list)
    provider_id: str = ""
    family: str = ""
    model: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    elapsed_s: float = 0.0
    degraded: str | None = None
    hit_limit: bool = False

    def summary(self) -> str:
        return (f"{self.provider_id} ({self.family}) · {self.iterations} iter · "
                f"{len(self.tool_calls)} herramientas · {self.elapsed_s:.1f}s")


async def run_agent(
    *,
    registry: ProviderRegistry,
    tools: ToolRegistry,
    system_prompt: str,
    user_prompt: str,
    ctx: ToolContext,
    prefer_provider: str | None = None,
    max_iters: int = 12,
    temperature: float = 0.4,
    seed: int | None = None,
    on_event: OnEvent = None,
    agent_name: str = "AGENT",
    degraded: str | None = None,
) -> AgentTurn:
    """
    Ciclo: pedir -> ¿pide herramientas? -> ejecutarlas -> devolver resultados
    -> repetir. Termina cuando el modelo responde sin bloques ```tool.
    """
    started = time.monotonic()
    catalog = tools.catalog()
    full_system = f"{system_prompt}\n\n{build_system_suffix(catalog)}" if catalog \
        else system_prompt

    messages = [Message("system", full_system), Message("user", user_prompt)]
    used: list[dict] = []
    tokens_in = tokens_out = 0
    provider_id = family = model = ""

    async def emit(topic: str, payload: dict) -> None:
        if on_event:
            try:
                await on_event(topic, {"agent": agent_name, **payload})
            except Exception:
                logger.debug("[agent_loop] on_event falló", exc_info=True)

    for i in range(1, max_iters + 1):
        req = CompletionRequest(
            messages=messages, temperature=temperature, seed=seed, timeout_s=150.0)
        resp = await registry.complete(req, prefer=prefer_provider)

        provider_id, family, model = resp.provider_id, resp.family, resp.model
        tokens_in += resp.usage.prompt_tokens
        tokens_out += resp.usage.completion_tokens

        calls = parse_tool_calls(resp.content)
        visible = strip_tool_calls(resp.content)

        if not calls:
            await emit("agent.done", {"iterations": i, "provider": provider_id})
            return AgentTurn(
                text=visible or resp.content, iterations=i, tool_calls=used,
                provider_id=provider_id, family=family, model=model,
                tokens_in=tokens_in, tokens_out=tokens_out,
                elapsed_s=time.monotonic() - started, degraded=degraded)

        if visible:
            await emit("agent.thought", {"text": visible, "iteration": i})

        await emit("agent.tool_use", {
            "iteration": i,
            "calls": [{"tool": c.name, "args": c.args} for c in calls],
        })
        logger.info("[%s] iter %d: %s", agent_name, i,
                    ", ".join(c.name for c in calls))

        results = await tools.execute_many([(c.name, c.args) for c in calls], ctx=ctx)
        for c, r in zip(calls, results):
            used.append({"tool": c.name, "args": c.args, "ok": r.ok,
                         "error": r.error, "iteration": i})
        await emit("agent.tool_result", {
            "iteration": i,
            "results": [{"tool": r.tool, "ok": r.ok, "error": r.error}
                        for r in results],
        })

        messages.append(Message("assistant", resp.content))
        messages.append(Message("user", format_results(results)))
        messages = _trim(messages)

    # Se agotaron las iteraciones: pedir cierre explícito.
    messages.append(Message("user",
        "Has alcanzado el límite de iteraciones. Responde AHORA sin usar más "
        "herramientas: resume qué has hecho, qué has averiguado y qué queda."))
    final = await registry.complete(
        CompletionRequest(messages=messages, temperature=temperature),
        prefer=prefer_provider)
    return AgentTurn(
        text=strip_tool_calls(final.content), iterations=max_iters, tool_calls=used,
        provider_id=final.provider_id, family=final.family, model=final.model,
        tokens_in=tokens_in + final.usage.prompt_tokens,
        tokens_out=tokens_out + final.usage.completion_tokens,
        elapsed_s=time.monotonic() - started, degraded=degraded, hit_limit=True)


def _trim(messages: list[Message], keep_recent: int = 12,
          max_chars: int = 60_000) -> list[Message]:
    """
    Poda de contexto. Los proveedores gratuitos tienen ventanas pequeñas e
    impredecibles; sin esto el bucle revienta a la 4ª o 5ª iteración.
    Conserva siempre el system y la petición original.
    """
    if len(messages) <= keep_recent + 2:
        return messages
    head, tail = messages[:2], messages[-keep_recent:]
    total = sum(len(str(m.content)) for m in head + tail)
    while total > max_chars and len(tail) > 4:
        dropped = tail.pop(0)
        total -= len(str(dropped.content))
    return head + [Message("user", "[…contexto intermedio podado…]")] + tail
