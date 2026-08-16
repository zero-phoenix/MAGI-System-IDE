from .schemas import Acta, Refutacion, Tesis


class EvidenceRubric:
    """
    Rúbrica y Veredictos (P3.c).
    Puntúa matemáticamente la Tesis vs Refutación.
    Precedencia: Física (Área 1) > Lógica (Área 2) > LLM Base.
    """
    def __init__(self):
        # Mocks of evidence tiers
        self.evidence_tier = {
            "ev_fisica_01": 3,
            "ev_legal_01": 2,
            "ev_llm_01": 1
        }

    def evaluate(self, tesis: Tesis, refutacion: Refutacion) -> Acta:
        """
        Decide el ganador del debate.
        """
        if refutacion.valido:
            # Balthasar está de acuerdo, Casper aprueba
            return Acta(
                tesis_id="tesis_01",
                veredicto="aprobado",
                score=1.0,
                justificacion="Consenso alcanzado"
            )

        # Hay conflicto
        t_tier = self.evidence_tier.get(tesis.evidencia_id, 1)
        r_tier = self.evidence_tier.get(refutacion.evidencia_contra_id, 1)

        if r_tier > t_tier:
            return Acta(
                tesis_id="tesis_01",
                veredicto="rechazado",
                score=-1.0,
                justificacion=f"Refutación con evidencia superior (Tier {r_tier} > {t_tier})"
            )
        elif t_tier > r_tier:
            return Acta(
                tesis_id="tesis_01",
                veredicto="aprobado",
                score=0.8,
                justificacion=f"Tesis sobrevive por precedencia física (Tier {t_tier} > {r_tier})"
            )
        else:
            return Acta(
                tesis_id="tesis_01",
                veredicto="undecided",
                score=0.0,
                justificacion="Empate de evidencias, requiere desempate manual o reejecución"
            )
