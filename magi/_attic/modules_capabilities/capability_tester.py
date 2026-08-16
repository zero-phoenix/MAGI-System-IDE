class CapabilityTester:
    """
    Simulador de Prueba de Posesión (P12.c).
    Fuerza el criterio Popperiano: "Una capacidad no existe si no puede ser verificada".
    """
    def __init__(self):
        pass

    def verify_capability(self, capability_id: str, result_data: dict) -> dict:
        if capability_id == "C01":
            # Matemáticas: 20/20 exactos
            score = result_data.get("exact_matches", 0)
            if score == 20:
                return {"verified": True, "metric": "20/20 exact matches"}
            return {"verified": False, "metric": f"{score}/20 exact matches"}

        if capability_id == "C02":
            # Reed-Solomon: 100% recuperadas
            recovery = result_data.get("recovery_rate", 0.0)
            if recovery == 1.0:
                return {"verified": True, "metric": "100% recovery"}
            return {"verified": False, "metric": f"{recovery*100}% recovery"}

        return {"verified": False, "metric": "Unknown Capability"}
