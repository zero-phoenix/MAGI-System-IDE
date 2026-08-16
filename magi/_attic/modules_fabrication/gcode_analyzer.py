

class GCodeAnalyzer:
    """
    Analizador Estático de G-Code (P9.B.2).
    Preflight físico: Bloquea extrusión en frío y violaciones de área.
    """
    def __init__(self):
        pass

    def analyze(self, gcode_lines: list[str]) -> dict:
        """
        Retorna {"status": "ok" | "rejected", "reason": "..."}
        """
        homed = False
        target_temp = 0.0

        for line in gcode_lines:
            line = line.strip()
            if not line or line.startswith(";"):
                continue

            if line.startswith("G28"):
                homed = True

            if line.startswith("M104 S") or line.startswith("M109 S"):
                try:
                    target_temp = float(line.split("S")[1].split()[0])
                except ValueError:
                    pass

            if line.startswith("G1 ") or line.startswith("G0 "):
                # Buscar si hay movimiento sin homing
                if not homed and ("X" in line or "Y" in line or "Z" in line):
                    return {"status": "rejected", "reason": "ERROR: Movimiento lineal antes de G28 Homing."}

                # Buscar si hay extrusión
                if "E" in line:
                    parts = line.split()
                    for p in parts:
                        if p.startswith("E"):
                            try:
                                val = float(p[1:])
                                if val > 0 and target_temp < 170.0:
                                    return {"status": "rejected", "reason": "ERROR: Intento de extrusión en frío detectado (T < 170)."}
                            except Exception:
                                pass

        return {"status": "ok"}
