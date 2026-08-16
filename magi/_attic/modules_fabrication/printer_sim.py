import re


class MarlinSimulator:
    """
    Simulador de Firmware Marlin (P9.a.1).
    Falsa impresora que responde a G-Code, emite telemetría y puede simular fallos.
    """
    def __init__(self):
        self.temp_hotend = 25.0
        self.temp_bed = 25.0
        self.target_hotend = 0.0
        self.target_bed = 0.0
        self.pos = {"X": 0, "Y": 0, "Z": 0, "E": 0}
        self.expected_n = 1
        self.fault_injected = None
        self.connected = False

    def handshake(self) -> str:
        self.connected = True
        return "start\necho:Marlin 2.0.x\n"

    def send_line(self, line: str) -> str:
        if not self.connected:
            return ""

        # Simular fallo térmico (Termistor desconectado)
        if self.fault_injected == "thermal_runaway":
            self.temp_hotend = -14.0 # Absurdo
            return "Error:Thermal Runaway, system stopped! Heater_ID: 0\n"

        if line.startswith("M115"):
            return "FIRMWARE_NAME:Marlin 2.1.2 MACHINE_TYPE:MAGI-Sim EXTRUDER_COUNT:1 Cap:AUTOREPORT_TEMP:1 Cap:EMERGENCY_PARSER:1\nok\n"

        if line.startswith("M105"):
            return f"ok T:{self.temp_hotend} /{self.target_hotend} B:{self.temp_bed} /{self.target_bed} @:0 B@:0\n"

        # Parseo de línea N con Checksum
        match = re.match(r"^N(\d+)\s+(.*)\*(\d+)$", line)
        if match:
            n = int(match.group(1))
            cmd = match.group(2)
            int(match.group(3))

            # (El simulador no valida el checksum real para simplificar los tests)

            # Inyección de Resend
            if self.fault_injected == "resend" and n == self.expected_n + 2:
                self.fault_injected = None # clear after trigger
                return f"Resend: {self.expected_n}\n"

            if n != self.expected_n:
                return f"Resend: {self.expected_n}\n"

            self.expected_n += 1

            # Procesar cmd
            if cmd.startswith("M104 S"):
                self.target_hotend = float(cmd.split("S")[1])
            elif cmd.startswith("M140 S"):
                self.target_bed = float(cmd.split("S")[1])
            elif cmd.startswith("M112"):
                self.connected = False
                return "ok\n"

            return f"ok N{n}\n"

        return "ok\n"
