import collections
import time


class TelemetryStream:
    """
    Stream de Telemetría (P10.b).
    Usa un Ring Buffer (deque) fuera del loop de eventos principal para no
    saturar la UI, soportando 10 000 muestras/seg.
    """
    def __init__(self, max_samples=100000):
        self.buffer = collections.deque(maxlen=max_samples)

    def push_sample(self, device_id: str, channel: str, value: float):
        """Añade muestra a alta velocidad O(1)."""
        self.buffer.append((time.time(), device_id, channel, value))

    def get_batch(self, count: int = 1000) -> list[tuple]:
        """Extrae un lote de muestras para enviar a uPlot en requestAnimationFrame."""
        res = []
        # Consume desde la izquierda (más viejos) hasta `count` o vaciar
        while self.buffer and len(res) < count:
            res.append(self.buffer.popleft())
        return res
