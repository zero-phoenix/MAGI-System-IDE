class RightsBlockedError(Exception):
    pass

class RightsGate:
    """
    Control de Derechos (CTL-8).
    Previene la suplantación de personas reales o marcas registradas antes de generar nada.
    """
    def __init__(self):
        # Lista simulada de términos bloqueados
        self.blocked_terms = ["persona famosa", "actor conocido", "disney", "nintendo", "mario bros"]

    def check_spec(self, request_text: str) -> None:
        """
        Valida que el encargo no viole políticas de derechos (CTL-8).
        """
        lower_req = request_text.lower()
        for term in self.blocked_terms:
            if term in lower_req:
                raise RightsBlockedError(f"rights: La solicitud contiene un término bloqueado por derechos ({term}). Por favor, proporciona una descripción genérica.")
