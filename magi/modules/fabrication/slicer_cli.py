from typing import Any


class SlicerCLI:
    """
    Abstracción de Rebanador por CLI (P9.B).
    Mock para PrusaSlicer/CuraEngine.
    """
    def __init__(self):
        pass

    def slice_model(self, model_data: dict[str, Any], profile: str) -> dict[str, Any]:
        """
        Simula rebanar un modelo y devolver un reporte parseado.
        """
        # Simulamos que un modelo muy grande lanza error de fuera de límites
        if model_data.get("volume_cm3", 0) > 100000:
            return {"status": "error", "message": "Model exceeds print volume."}

        # Generar "G-Code" simulado
        gcode = [
            "; estimated printing time (normal mode) = 1h 12m",
            "; filament used [g] = 10.2",
            "M104 S210",
            "M140 S60",
            "G28 ; home",
            "G1 Z0.2 F3000",
            "G1 X10 Y10 E2 F1500"
        ]

        return {
            "status": "success",
            "gcode_lines": gcode,
            "estimated_time": "1h 12m",
            "filament_g": 10.2
        }
