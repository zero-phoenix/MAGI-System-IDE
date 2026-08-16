import collections
from typing import Any


class AdaptiveSampler:
    """
    Muestreador Adaptativo y Backpressure (P4.5).
    Mantiene un ring buffer de 1MB (simulado). Drop-oldest behavior.
    """
    def __init__(self, max_items: int = 10000):
        # deque con maxlen actúa como Ring Buffer automático
        self.buffer = collections.deque(maxlen=max_items)
        self.dropped = 0

    def push_sample(self, sample: Any):
        if len(self.buffer) == self.buffer.maxlen:
            self.dropped += 1
        self.buffer.append(sample)

    def read_all(self) -> list[Any]:
        items = list(self.buffer)
        self.buffer.clear()
        return items
