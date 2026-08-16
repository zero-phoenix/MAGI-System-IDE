from collections.abc import Callable


class HotplugHAL:
    """
    Abstracción de eventos Hotplug de USB (WM_DEVICECHANGE / pyudev).
    """
    def __init__(self):
        self._listeners = []

    def watch(self, callback: Callable[[dict[str, str]], None]):
        self._listeners.append(callback)

    def simulate_connection(self, vid: str, pid: str, extra: dict[str, str] = None):
        """
        Mock para tests: Simula la conexión física de un USB.
        """
        event = {"action": "add", "vid": vid, "pid": pid}
        if extra:
            event.update(extra)

        for cb in self._listeners:
            cb(event)
