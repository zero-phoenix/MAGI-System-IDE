from typing import Dict, Any

class DivergenceReport(Exception):
    pass

class DifferentialTester:
    """
    Prueba Diferencial y Sandboxing Binario (P5.4).
    Lanza la referencia vs candidato y encuentra divergencias.
    """
    def __init__(self):
        pass
        
    def run_differential(self, ref_state: Dict[str, Any], cand_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simula comparar los registros resultantes de dos funciones (Referencia vs Sintetizado).
        Si divergen, lanza un DivergenceReport que el Área 3 usará como Falsificador empírico.
        """
        divergences = []
        for reg, val in ref_state.items():
            if cand_state.get(reg) != val:
                divergences.append(f"Reg {reg} differs: {val} != {cand_state.get(reg)}")
                
        if divergences:
            raise DivergenceReport(" | ".join(divergences))
            
        return {"status": "match", "verified": True}
