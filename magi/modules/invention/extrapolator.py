
class Extrapolator:
    """
    Motor de Extrapolación con Operadores Deterministas y MAP-Elites (P11.c).
    """
    def __init__(self):
        self.niches = {}

    def _map_elites_insert(self, idea: dict, score: float):
        """Rejilla simplificada de costo vs complejidad."""
        niche_key = f"c_{idea['cost']}_comp_{idea['complexity']}"

        if niche_key not in self.niches or score > self.niches[niche_key]["score"]:
            self.niches[niche_key] = {"idea": idea, "score": score}

    def run_extrapolation(self, base_idea: dict) -> list[dict]:
        """Aplica operadores y llena los nichos MAP-Elites."""
        derivadas = []

        # O-c: Inversión de Supuestos
        der_c = base_idea.copy()
        der_c["id"] = "der_01"
        der_c["operator"] = "O-c"
        der_c["cost"] = 50
        der_c["complexity"] = 5
        derivadas.append((der_c, 85.0))

        # O-a: Combinatoria
        der_a = base_idea.copy()
        der_a["id"] = "der_02"
        der_a["operator"] = "O-a"
        der_a["cost"] = 200
        der_a["complexity"] = 12
        derivadas.append((der_a, 70.0))

        # O-h: Biomímesis
        der_h = base_idea.copy()
        der_h["id"] = "der_03"
        der_h["operator"] = "O-h"
        der_h["cost"] = 50
        der_h["complexity"] = 5
        derivadas.append((der_h, 92.0)) # Supera a la der_c en el mismo nicho

        for idea, score in derivadas:
            self._map_elites_insert(idea, score)

        return [v["idea"] for v in self.niches.values()]
