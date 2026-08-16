from .schemas import Refutacion


class SycophancyGuard:
    """
    Guardas (P3.d).
    Detecta sicofancia y arrastre cognitivo.
    """
    def __init__(self):
        self.consecutive_agreements = 0

    def check_sycophancy(self, refutacion: Refutacion) -> bool:
        """
        Si Balthasar está de acuerdo demasiadas veces, fuerza un reinicio ciego
        o aborta la regresión.
        Retorna True si hay sicofancia detectada.
        """
        if refutacion.valido:
            self.consecutive_agreements += 1
        else:
            self.consecutive_agreements = 0

        if self.consecutive_agreements >= 2:
            return True # Demasiada complacencia

        return False

    def reset(self):
        self.consecutive_agreements = 0
