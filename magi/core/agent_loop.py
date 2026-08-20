"""
Bucle de agente con herramientas (Plan MAGI 9.0 §2.2).

Sustituye el "un turno = una llamada al LLM = un texto" de v5.0.28 por
"un turno = N iteraciones de pensar-actuar-observar hasta terminar".

Es el cambio que convierte a MAGI de un sistema que describe trabajo en uno
que lo hace.
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from .providers.base import CompletionRequest, Message, ProviderError, ProviderTimeout
from .providers.registry import ProviderRegistry
from .tools import (
    ToolContext,
    ToolRegistry,
    build_system_suffix,
    format_results,
    parse_tool_calls,
    strip_tool_calls,
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
    iteration_timeout_s: float = 150.0,
    soft_timeout_s: float = 60.0,
    hedge: bool | None = None,
) -> AgentTurn:
    """
    Ciclo: pedir -> ¿pide herramientas? -> ejecutarlas -> devolver resultados
    -> repetir. Termina cuando el modelo responde sin bloques ```tool.

    `iteration_timeout_s` es el toque duro por llamada al LLM. Si se excede,
    se devuelve una respuesta degradada en vez de dejar el agente colgado.
    `soft_timeout_s` avisa por evento cuando una iteración se está alargando.
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
        iter_started = time.monotonic()
        # B4 — LA PUERTA DE LAS HERRAMIENTAS TAMBIÉN SE CUBRE.
        #
        # El hedge —cubrir una llamada lenta lanzando el siguiente candidato—
        # existía solo en `FreeCloudLLM.generate`. Este bucle llama a
        # `registry.complete` directamente, así que las llamadas MÁS LENTAS del
        # sistema iban sin cubrir: medido el 2026-08-20, 19,2 s de media por
        # completion, con candidatos sanos entre 2 y 6 s, y un timeout duro de
        # 150 s que se comió turnos enteros.
        #
        # `hedge` se deja en None —auto— cuando el llamante no dice nada: es el
        # backend quien decide con las latencias medidas. Y en False cuando la
        # rama ya tiene redundancia estructural (las tres variantes en
        # paralelo), porque ahí cubrir multiplicaría la cuota por nada.
        req = CompletionRequest(
            messages=messages, temperature=temperature, seed=seed,
            timeout_s=iteration_timeout_s, hedge=hedge)

        try:
            resp = await asyncio.wait_for(
                registry.complete(req, prefer=prefer_provider),
                timeout=iteration_timeout_s + 5.0)
        except (asyncio.TimeoutError, ProviderTimeout, ProviderError) as e:
            logger.warning("[%s] iteración %d excedió %.1fs; se devuelve "
                           "respuesta degradada: %s", agent_name, i,
                           iteration_timeout_s, e)
            await emit("agent.timeout", {
                "iteration": i,
                "timeout_s": iteration_timeout_s,
                "provider": prefer_provider or "desconocido",
                "error": str(e),
            })
            return AgentTurn(
                text=(f"[Tiempo de espera agotado tras {iteration_timeout_s:.0f}s "
                      f"en iteración {i}. Proveedor: {prefer_provider or 'desconocido'}. "
                      f"Error: {e}]"),
                iterations=i, tool_calls=used,
                provider_id=prefer_provider or "TIMEOUT",
                family="", model="",
                tokens_in=tokens_in, tokens_out=tokens_out,
                elapsed_s=time.monotonic() - started,
                degraded=(degraded or "timeout"))

        provider_id, family, model = resp.provider_id, resp.family, resp.model
        tokens_in += resp.usage.prompt_tokens
        tokens_out += resp.usage.completion_tokens

        elapsed_iter = time.monotonic() - iter_started
        if elapsed_iter > soft_timeout_s:
            await emit("agent.slow_iteration", {
                "iteration": i, "elapsed_s": elapsed_iter,
                "provider": provider_id, "soft_timeout_s": soft_timeout_s})

        calls = parse_tool_calls(resp.content)
        visible = strip_tool_calls(resp.content)

        if not calls:
            await emit("agent.done", {"iterations": i, "provider": provider_id})
            await emit("agent.turn_done", {
                "iterations": i, "provider": provider_id, "family": family,
                "elapsed_s": time.monotonic() - started,
                "tokens": tokens_in + tokens_out,
                "tools_used": len(used)})
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

        # Ejecutar a través del Circuit Breaker (B4: Parada-Cubre-Hedge)
        from .circuit_breaker import ToolCircuitBreaker
        cb = ToolCircuitBreaker(tools)
        cb_res = await cb.execute_with_hedge([(c.name, c.args) for c in calls], ctx=ctx)
        results = cb_res.results

        for c, r in zip(calls, results, strict=True):
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
        CompletionRequest(messages=messages, temperature=temperature,
                          timeout_s=iteration_timeout_s),
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

    Descartar mensajes enteros no basta: la salida de un run_tests o de un
    read_file puede ocupar 40 000 caracteres ella sola, y el bucle antiguo no
    podía bajar de 4 mensajes por muy grandes que fueran. Se descarta primero
    y, si aún no cabe, se recortan los cuerpos.
    """
    if len(messages) <= keep_recent + 2 and \
            sum(len(str(m.content)) for m in messages) <= max_chars:
        return messages

    head = messages[:2]                       # system + petición original
    tail = list(messages[-keep_recent:]) if len(messages) > 2 else []

    def size(msgs) -> int:
        return sum(len(str(m.content)) for m in msgs)

    # 1) descartar los más antiguos de la cola
    while size(head + tail) > max_chars and len(tail) > 2:
        tail.pop(0)

    # 2) si sigue sin caber, recortar cuerpos empezando por los más grandes
    budget = max_chars - size(head)
    if budget > 0 and size(tail) > budget:
        per_msg = max(500, budget // max(1, len(tail)))
        for i, m in enumerate(tail):
            body = str(m.content)
            if len(body) > per_msg:
                keep = per_msg // 2
                tail[i] = Message(
                    m.role,
                    f"{body[:keep]}\n\n[…{len(body) - per_msg} caracteres "
                    f"recortados…]\n\n{body[-keep:]}",
                    m.tool_call_id, m.name)

    marker = [Message("user", "[…contexto intermedio podado…]")] \
        if len(messages) > len(head) + len(tail) else []
    return head + marker + tail
