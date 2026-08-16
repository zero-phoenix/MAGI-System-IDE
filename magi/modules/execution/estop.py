import threading


class EmergencyStop:
    """
    E-STOP (P8.4).
    Interruptor de Seguridad. Opera de forma independiente al Thread Principal.
    """
    def __init__(self):
        self.triggered = False
        self._lock = threading.Lock()

    def trigger(self, reason: str = "Manual Intervention"):
        with self._lock:
            self.triggered = True
            # Aquí iría el código real de matar árboles de procesos y liberar hardware.
            # ej. os.kill(pid, SIGKILL)

    def check(self):
        with self._lock:
            if self.triggered:
                raise RuntimeError("SYSTEM HALTED: E-STOP TRIGGERED")
