class PatentScreen:
    """
    Cribado de Patentabilidad y Novedad (P11.d).
    Verifica arte previo y emite dictámenes.
    """
    def __init__(self):
        pass

    def screen(self, invention_data: dict) -> dict:
        """
        Retorna el reporte de viabilidad legal simulado.
        """
        disclaimer = "Orientación técnica documentada. No constituye asesoría legal. La presentación debe ser revisada por un agente de la propiedad industrial."

        # Simular rechazo si el título contiene "perpetuo"
        if "perpetuo" in invention_data.get("title", "").lower():
            return {
                "novelty_score": 0.0,
                "status": "falsified",
                "reason": "Carece de Aplicación Industrial",
                "disclaimer": disclaimer
            }

        return {
            "novelty_score": 0.85,
            "status": "survives",
            "reason": "No se encontraron divulgaciones idénticas",
            "disclaimer": disclaimer
        }
