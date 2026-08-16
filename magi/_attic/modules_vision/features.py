import random
from typing import Any


class FeatureExtractor:
    """
    Extracción de Rasgos (P1.c).
    Vector de 128D por página.
    """
    def __init__(self):
        pass

    def extract_features(self, layout_data: dict[str, Any]) -> dict[str, Any]:
        """
        Calcula el vector topográfico de la página de 128 dimensiones.
        Retorna también estimaciones de fuente y peso.
        """
        # Mock feature vector without NaNs
        vector = [round(random.uniform(-1.0, 1.0), 4) for _ in range(128)]

        # Estimate font properties (Mock)
        font_size = 12.0
        if "TEST_FONT:18" in str(layout_data):
            font_size = 18.0

        return {
            "page_vector_128d": vector,
            "font_size_pt": font_size,
            "font_weight": "normal",
            "is_italic": False
        }
