from typing import Any


class FraudDetectors:
    """
    Detectores de Fraude Topográfico (D1-D9).
    """
    def __init__(self):
        pass

    def _compute_ncc(self, patchA: bytes, patchB: bytes) -> float:
        """
        Normalized Cross Correlation (D7).
        Similitud entre dos recortes de imagen (ej: firmas).
        """
        # Mock calculation
        if b"CLONE" in patchA and b"CLONE" in patchB:
            return 0.98 # Alto = Clon detectado
        return 0.82

    def detect(self, image_data: bytes, page_features: dict[str, Any]) -> dict[str, Any]:
        """
        Ejecuta todos los detectores.
        """
        results = {}

        # D7: Clon de Firma (NCC)
        ncc_score = self._compute_ncc(image_data, image_data)
        results["D7_signature_clone"] = {
            "score": ncc_score,
            "flagged": ncc_score >= 0.97
        }

        # D8-D9: Revisión incremental (Mock)
        results["D8_incremental_revision"] = {
            "flagged": b"EDITED" in image_data
        }

        return results
