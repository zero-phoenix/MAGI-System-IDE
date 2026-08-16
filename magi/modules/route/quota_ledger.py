
class QuotaLedger:
    """
    Libro de Cuotas (P14.d).
    Mantiene el consumo y detecta agotamiento de tokens.
    """
    def __init__(self, limit: int = 1000):
        self.limit = limit
        self.used = 0

    def consume(self, amount: int) -> bool:
        """Intenta consumir cuota. Falla si no alcanza, simulando `WAITING_QUOTA`."""
        if self.used + amount > self.limit:
            return False
        self.used += amount
        return True

    def get_status(self) -> str:
        if self.used >= self.limit:
            return "exhausted"
        return "active"
