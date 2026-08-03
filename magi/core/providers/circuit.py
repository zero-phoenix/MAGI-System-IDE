"""
Cortacircuitos funcional (Plan MAGI 9.0 §1.1).

En v5.0.28 había DOS implementaciones de esto y ninguna se ejecutaba:
  - cloud.py definía `_is_alive()` y `_mark_failure()` con lógica de cooldown
    correcta y cero sitios de llamada.
  - providers/circuit.py (este fichero) definía otra sobre un ProviderRegistry
    que nadie instanciaba.

El README anunciaba "enfriamiento inteligente de IP" que nunca corrió.
Esta versión se llama de verdad desde ProviderRegistry.select()/complete().
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from .base import ProviderState


@dataclass
class CircuitBreaker:
    """
    CLOSED --(fallos >= threshold)--> OPEN
      ^                                 |
      |                          (pasa cooldown)
      |                                 v
      +---(sonda ok)---- HALF_OPEN <----+
                 (sonda falla -> OPEN otra vez)
    """
    threshold: int = 3
    cooldown_s: float = 300.0

    failures: int = 0
    successes: int = 0
    opened_at: float = 0.0
    _state: ProviderState = ProviderState.CLOSED
    latencies_ms: list[float] = field(default_factory=list)

    def state(self, now: float | None = None) -> ProviderState:
        now = now if now is not None else time.monotonic()
        if self._state is ProviderState.OPEN and now - self.opened_at >= self.cooldown_s:
            self._state = ProviderState.HALF_OPEN
        return self._state

    def allows(self, now: float | None = None) -> bool:
        """OPEN bloquea. HALF_OPEN deja pasar una sonda."""
        return self.state(now) is not ProviderState.OPEN

    def record_success(self, latency_ms: float = 0.0) -> None:
        self.failures = 0
        self.successes += 1
        self._state = ProviderState.CLOSED
        if latency_ms:
            self.latencies_ms.append(latency_ms)
            if len(self.latencies_ms) > 200:
                self.latencies_ms = self.latencies_ms[-200:]

    def record_failure(self, now: float | None = None) -> None:
        now = now if now is not None else time.monotonic()
        self.failures += 1
        if self._state is ProviderState.HALF_OPEN or self.failures >= self.threshold:
            self._state = ProviderState.OPEN
            self.opened_at = now

    def p95_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        s = sorted(self.latencies_ms)
        return s[min(len(s) - 1, int(len(s) * 0.95))]

    def p50_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        s = sorted(self.latencies_ms)
        return s[len(s) // 2]

    def snapshot(self) -> dict:
        return {
            "state": self.state().value,
            "failures": self.failures,
            "successes": self.successes,
            "p50_ms": round(self.p50_ms(), 1),
            "p95_ms": round(self.p95_ms(), 1),
        }
