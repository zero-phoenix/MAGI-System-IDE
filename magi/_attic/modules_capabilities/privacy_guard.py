class PrivacyGuard:
    """
    Guarda de Privacidad y Procedencia de Datos (P12.b).
    Actúa sobre C08 (Psicometría y Segmentación).
    """
    def __init__(self):
        pass

    def check_data_provenance(self, capability_id: str, dataset_metadata: dict) -> dict:
        """
        Bloquea procesamientos si la data no tiene procedencia explícita o consentimiento.
        """
        if capability_id == "C08":
            if not dataset_metadata.get("consent_certified", False):
                return {
                    "status": "blocked",
                    "reason": "PRIVACY_GUARD_ERROR: Dataset lacks explicit consent provenance (Required for C08 Psychometrics)."
                }
        return {"status": "allowed"}
