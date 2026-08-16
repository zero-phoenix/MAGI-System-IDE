from typing import Any


class DeviceIdentifier:
    """
    Tabla de Perfiles VID:PID.
    """
    def __init__(self):
        self.profiles = {
            "2341:0043": {"name": "Arduino Uno R3", "modes": ["cdc-acm"]},
            "054c:01c8": {"name": "Sony PSP", "modes": ["msc"]},
            "18d1:4ee2": {"name": "Android Device (MTP+ADB)", "modes": ["mtp", "adb"]}
        }

    def identify(self, vid: str, pid: str) -> dict[str, Any] | None:
        """
        Retorna el perfil del dispositivo en base a su VID:PID.
        """
        key = f"{vid}:{pid}"
        # Matches exactos
        if key in self.profiles:
            return self.profiles[key]

        # Matches parciales (Android general, Sony general)
        if vid == "18d1":
            return {"name": "Generic Android", "modes": ["mtp", "adb", "fastboot"]}

        return None
