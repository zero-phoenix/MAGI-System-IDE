"""
Registro de proveedores con diversidad de familias REAL (Plan MAGI 9.0 §1.1).

EL BUG QUE ESTO ARREGLA
=======================
v5.0.28, magi/core/providers/cloud.py:122-123:

    if model in ["claude-3.5-sonnet", "qwen-2.5", "deepseek"]:
        model = "gpt-4o"

Melchior pedía deepseek, Balthasar claude-3.5-sonnet, Casper qwen-2.5.
Los tres se reescribían a gpt-4o. El enjambre entero era UN modelo con tres
prompts, y todo el valor epistemológico del debate popperiano (que el crítico
tenga sesgos distintos al proponente) no existía.

Aquí cada backend declara su `family`. `select_for_swarm()` reparte familias
distintas entre los tres nodos, y cuando no puede, lo DICE en vez de disimularlo.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import AsyncIterator, Iterable, Sequence

from .base import (
    BaseProvider, CompletionRequest, CompletionResponse, Delta,
    ProviderError, ProviderTimeout, Usage,
)
from .cache import TTLCache, make_key
from .circuit import CircuitBreaker

logger = logging.getLogger(__name__)

SWARM_ROLES = ("MELCHIOR", "BALTHASAR", "CASPER")


@dataclass
class Registration:
    provider: BaseProvider
    priority: int = 100          # menor = se prueba antes
    breaker: CircuitBreaker = field(default_factory=CircuitBreaker)
    available: bool | None = None   # None = aún no sondeado
    tokens_in: int = 0
    tokens_out: int = 0
    calls: int = 0

    @property
    def id(self) -> str:
        return self.provider.id

    @property
    def family(self) -> str:
        return self.provider.family


@dataclass
class SwarmAssignment:
    """Qué proveedor le toca a cada nodo, y si la diversidad se degradó."""
    by_role: dict[str, str]
    families: dict[str, str]
    diversity: str            # "full" | "partial" | "degraded" | "none"
    note: str = ""

    def degraded_reason_for(self, role: str) -> str | None:
        if self.diversity == "full":
            return None
        others = [r for r in self.by_role if r != role
                  and self.families.get(r) == self.families.get(role)]
        if others:
            return f"misma familia ({self.families.get(role)}) que {', '.join(others)}"
        return None


class ProviderRegistry:
    """
    Selecciona proveedores, aplica cortacircuitos, caché y contabilidad.

    Todo lo que en v5.0.28 estaba definido-pero-no-llamado, aquí se llama.
    """

    def __init__(self, cache_maxsize: int = 500, cache_ttl_s: float = 3600.0):
        self._regs: dict[str, Registration] = {}
        self.cache: TTLCache[CompletionResponse] = TTLCache(cache_maxsize, cache_ttl_s)
        self._probe_lock = asyncio.Lock()

    # ---------------------------------------------------------------- registro

    def register(self, provider: BaseProvider, priority: int = 100) -> None:
        self._regs[provider.id] = Registration(provider=provider, priority=priority)
        logger.info("[registry] %s registrado (familia=%s, local=%s, prio=%d)",
                    provider.id, provider.family, provider.is_local, priority)

    def unregister(self, provider_id: str) -> None:
        self._regs.pop(provider_id, None)

    def get(self, provider_id: str) -> Registration | None:
        return self._regs.get(provider_id)

    def all(self) -> list[Registration]:
        return sorted(self._regs.values(), key=lambda r: r.priority)

    async def probe_all(self, timeout_s: float = 5.0) -> None:
        """Sondea disponibilidad en paralelo. Se llama al arrancar."""
        async with self._probe_lock:
            async def probe(reg: Registration) -> None:
                try:
                    reg.available = await asyncio.wait_for(
                        reg.provider.available(), timeout=timeout_s)
                except Exception as e:
                    logger.debug("[registry] sonda %s falló: %s", reg.id, e)
                    reg.available = False
            await asyncio.gather(*(probe(r) for r in self._regs.values()),
                                 return_exceptions=True)
        ok = [r.id for r in self._regs.values() if r.available]
        logger.info("[registry] disponibles: %s", ", ".join(ok) or "NINGUNO")

    # -------------------------------------------------------------- selección

    def healthy(self, *, need_tools: bool = False, need_vision: bool = False,
                need_stream: bool = False) -> list[Registration]:
        out = []
        for reg in self.all():
            if reg.available is False:
                continue
            if not reg.breaker.allows():
                continue
            p = reg.provider
            if need_tools and not p.supports_tools:
                continue
            if need_vision and not p.supports_vision:
                continue
            if need_stream and not p.supports_stream:
                continue
            out.append(reg)
        return out

    def families_available(self) -> list[str]:
        seen, out = set(), []
        for reg in self.healthy():
            if reg.family not in seen:
                seen.add(reg.family)
                out.append(reg.family)
        return out

    def select_for_swarm(self, roles: Sequence[str] = SWARM_ROLES,
                         **caps) -> SwarmAssignment:
        """
        Reparte proveedores entre los nodos maximizando familias distintas.

        - 3+ familias sanas -> "full": cada nodo, una familia.
        - 2 familias        -> "partial": CASPER (el juez) se aísla en la suya,
                               los otros dos comparten. Se declara.
        - 1 familia         -> "degraded": divergencia forzada por temperatura
                               y semilla, y se dice en la tarjeta de la GUI.
        - 0                 -> "none".
        """
        pool = self.healthy(**caps)
        if not pool:
            return SwarmAssignment({}, {}, "none", "no hay proveedores sanos")

        by_family: dict[str, list[Registration]] = {}
        for reg in pool:
            by_family.setdefault(reg.family, []).append(reg)
        fams = sorted(by_family, key=lambda f: by_family[f][0].priority)

        by_role: dict[str, str] = {}
        families: dict[str, str] = {}

        if len(fams) >= len(roles):
            for role, fam in zip(roles, fams):
                by_role[role] = by_family[fam][0].id
                families[role] = fam
            return SwarmAssignment(by_role, families, "full")

        if len(fams) >= 2:
            judge = roles[-1]                      # CASPER se aísla
            by_role[judge] = by_family[fams[0]][0].id
            families[judge] = fams[0]
            for role in roles[:-1]:
                by_role[role] = by_family[fams[1]][0].id
                families[role] = fams[1]
            return SwarmAssignment(
                by_role, families, "partial",
                f"solo {len(fams)} familias sanas; {judge} aislado en {fams[0]}")

        only = fams[0]
        for role in roles:
            by_role[role] = by_family[only][0].id
            families[role] = only
        return SwarmAssignment(
            by_role, families, "degraded",
            f"una sola familia disponible ({only}); "
            f"divergencia forzada por temperatura y semilla")

    # -------------------------------------------------------------- inferencia

    async def complete(
        self, req: CompletionRequest, *,
        prefer: str | None = None,
        need_tools: bool = False, need_vision: bool = False,
        use_cache: bool = True, max_attempts: int = 3,
    ) -> CompletionResponse:
        """
        Ejecuta con failover. A diferencia de v5.0.28:
          - hay timeout duro por intento (antes: ninguno, cuelgue infinito)
          - el cortacircuitos se consulta y se actualiza de verdad
          - la caché tiene tope (antes: crecía sin límite)
          - se contabilizan tokens
          - el provider que se reporta es el que RESPONDIÓ
        """
        key = None
        if use_cache and not req.tools:
            key = make_key("complete", prefer, req.model, req.temperature,
                           [m.to_wire() for m in req.messages])
            hit = self.cache.get(key)
            if hit is not None:
                logger.debug("[registry] acierto de caché (%s)", hit.provider_id)
                return hit

        candidates = self._candidates(prefer, need_tools, need_vision)
        if not candidates:
            raise ProviderError("no hay proveedores sanos que cumplan los requisitos")

        last_err: Exception | None = None
        for reg in candidates[:max_attempts]:
            started = time.monotonic()
            try:
                resp = await asyncio.wait_for(
                    reg.provider.complete(req), timeout=req.timeout_s)
            except asyncio.TimeoutError as e:
                reg.breaker.record_failure()
                last_err = ProviderTimeout(f"{reg.id} excedió {req.timeout_s}s")
                logger.warning("[registry] %s TIMEOUT (%.0fs)", reg.id, req.timeout_s)
                continue
            except Exception as e:
                reg.breaker.record_failure()
                last_err = e
                logger.warning("[registry] %s falló: %s", reg.id, e)
                continue

            latency = (time.monotonic() - started) * 1000.0
            reg.breaker.record_success(latency)
            reg.calls += 1
            reg.tokens_in += resp.usage.prompt_tokens
            reg.tokens_out += resp.usage.completion_tokens
            if key:
                self.cache.set(key, resp)
            return resp

        raise ProviderError(f"todos los proveedores fallaron: {last_err}") from last_err

    async def stream(
        self, req: CompletionRequest, *, prefer: str | None = None,
        need_tools: bool = False,
    ) -> AsyncIterator[Delta]:
        """Streaming con failover en el primer fallo antes del primer token."""
        candidates = self._candidates(prefer, need_tools, False)
        if not candidates:
            raise ProviderError("no hay proveedores sanos para streaming")

        last_err: Exception | None = None
        for reg in candidates:
            started = time.monotonic()
            emitted = False
            try:
                async for delta in reg.provider.stream(req):
                    emitted = True
                    yield delta
                reg.breaker.record_success((time.monotonic() - started) * 1000.0)
                reg.calls += 1
                return
            except Exception as e:
                last_err = e
                reg.breaker.record_failure()
                if emitted:
                    # Ya salieron tokens: reintentar duplicaría texto en pantalla.
                    logger.error("[registry] %s cortó a mitad de stream: %s", reg.id, e)
                    raise
                logger.warning("[registry] %s falló antes del 1er token: %s", reg.id, e)
                continue
        raise ProviderError(f"streaming falló en todos: {last_err}") from last_err

    def _candidates(self, prefer: str | None, need_tools: bool,
                    need_vision: bool) -> list[Registration]:
        pool = self.healthy(need_tools=need_tools, need_vision=need_vision)
        if prefer:
            pool.sort(key=lambda r: (r.id != prefer, r.priority))
        return pool

    # ----------------------------------------------------------- observabilidad

    def telemetry(self) -> dict:
        """Alimenta el panel de salud de la GUI y la vigilancia de Naoko."""
        return {
            "providers": [
                {
                    "id": r.id, "family": r.family,
                    "local": r.provider.is_local,
                    "available": r.available,
                    "tools": r.provider.supports_tools,
                    "vision": r.provider.supports_vision,
                    "calls": r.calls,
                    "tokens_in": r.tokens_in, "tokens_out": r.tokens_out,
                    **r.breaker.snapshot(),
                }
                for r in self.all()
            ],
            "families_available": self.families_available(),
            "cache": self.cache.stats(),
        }
