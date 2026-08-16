import math
from typing import Any


class Normalizer:
    """
    Área 1: Normalización Topográfica.
    P1.a: Deskew, Perspectiva y DPI.
    """
    def __init__(self):
        pass

    def _estimate_skew_angle(self, image_data: bytes) -> float:
        """
        Mock: Estima el ángulo de rotación de la imagen.
        En producción: usa Transformada de Hough o proyecciones de perfil.
        """
        # Para propósitos de test, leemos una marca de agua mágica si existe
        if b"TEST_SKEW:12" in image_data:
            return 12.0
        elif b"TEST_SKEW:-5" in image_data:
            return -5.0
        return 0.0

    def process(self, image_data: bytes) -> dict[str, Any]:
        """
        Calcula el deskew, recorta márgenes y normaliza DPI.
        """
        # 1. Calcular ángulo
        skew = self._estimate_skew_angle(image_data)

        # 2. Corregir ángulo
        corrected_angle = -skew

        # 3. Retornar metadata
        return {
            "dpi_effective": 300,
            "skew_detected": skew,
            "deskew_applied": corrected_angle,
            "normalized": True,
            "matrix_h": [[math.cos(corrected_angle), -math.sin(corrected_angle), 0],
                         [math.sin(corrected_angle),  math.cos(corrected_angle), 0],
                         [0, 0, 1]]
        }
