from typing import Any


class DeviceSession:
    def __init__(self, mode: str, profile: dict[str, Any]):
        self.mode = mode
        self.profile = profile
        self.active = True

class ModeSelector:
    """
    Selector de Modos.
    Decide el canal de comunicación óptimo cuando el perfil soporta varios.
    Precedencia (simplificada): adb > dfu > cdc-acm > mtp > msc.
    """
    def __init__(self):
        self.mode_priority = {
            "adb": 50,
            "dfu": 40,
            "cdc-acm": 30,
            "mtp": 20,
            "msc": 10,
            "hid": 5
        }

    def select_mode(self, profile: dict[str, Any], class_hint: str | None = None) -> DeviceSession:
        """
        Abre una sesión en el modo de mayor prioridad disponible.
        """
        modes = profile.get("modes", [])
        if not modes:
            raise ValueError("No modes available for device")

        # Si la clase USB fuerza MTP (por ejemplo FF y no-adb)
        if class_hint == "ff-mtp" and "mtp" in modes:
            return DeviceSession("mtp", profile)

        best_mode = max(modes, key=lambda m: self.mode_priority.get(m, 0))
        return DeviceSession(best_mode, profile)
