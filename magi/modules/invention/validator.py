
class Validator:
    """
    Validador por Primeros Principios (P11.b).
    En el MVP, simula un chequeo matemático algebraico basado en parámetros declarados.
    """
    def __init__(self):
        pass

    def validate(self, invention_data: dict) -> dict:
        """
        Evalúa si la invención viola leyes físicas (ej: termodinámica).
        """
        params = {p["name"]: p["value"] for p in invention_data.get("parameter_vector", [])}

        # Simulación: Detección estricta de Móvil Perpetuo
        if "energy_out" in params and "energy_in" in params:
            if params["energy_out"] > params["energy_in"]:
                return {
                    "status": "inviable",
                    "reason": f"Violación Termodinámica (Primera Ley): energy_out ({params['energy_out']}) > energy_in ({params['energy_in']})"
                }

        # Simulación: Detección de límite de Carnot superado
        if "rendimiento" in params and "rendimiento_carnot" in params:
            if params["rendimiento"] > params["rendimiento_carnot"]:
                 return {
                    "status": "inviable",
                    "reason": f"Violación Termodinámica (Segunda Ley): Rendimiento esperado ({params['rendimiento']}) > Límite de Carnot ({params['rendimiento_carnot']})"
                }

        return {"status": "viable"}
