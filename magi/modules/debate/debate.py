import hashlib
from typing import Any

from .guards import SycophancyGuard
from .rubric import EvidenceRubric
from .schemas import Acta, Refutacion, Tesis


class DebateOrchestrator:
    """
    Orquestador de rondas (P3.b).
    Controla el ciclo M -> B -> C y el aislamiento de contexto.
    """
    def __init__(self):
        self.rubric = EvidenceRubric()
        self.guard = SycophancyGuard()

    def _mock_llm_melchior(self) -> Tesis:
        return Tesis(
            afirmacion="La firma es auténtica",
            evidencia_id="ev_llm_01",
            confianza=0.9
        )

    def _mock_llm_balthasar(self, tesis: Tesis, mode: str) -> tuple[Refutacion, str]:
        # Aislamiento: Balthasar no debe ver el razonamiento interno de A.
        prompt_b = f"Audita la siguiente tesis: {tesis.afirmacion}. Evidencia aportada: {tesis.evidencia_id}."
        prompt_hash = hashlib.sha256(prompt_b.encode('utf-8')).hexdigest()

        if mode == "sycophant":
            return Refutacion(valido=True, mecanismo="Estoy de acuerdo"), prompt_hash
        elif mode == "hostile":
            return Refutacion(
                valido=False,
                mecanismo="El análisis físico indica clonación",
                evidencia_contra_id="ev_fisica_01"
            ), prompt_hash

    def run_round(self, mode: str = "hostile") -> dict[str, Any]:
        """
        Ejecuta una ronda completa (MVP).
        """
        tesis = self._mock_llm_melchior()

        refutacion, p_hash = self._mock_llm_balthasar(tesis, mode)

        if self.guard.check_sycophancy(refutacion):
            acta = Acta(tesis_id="tesis_01", veredicto="undecided", score=0.0, justificacion="Sicofancia detectada")
        else:
            acta = self.rubric.evaluate(tesis, refutacion)

        return {
            "acta": acta,
            "b_prompt_hash": p_hash,
            "b_prompt_text": f"Audita la siguiente tesis: {tesis.afirmacion}. Evidencia aportada: {tesis.evidencia_id}."
        }
