"""
Subagentes especializados por familia (Megaplan F2).

Invariantes de F2:
1. Misma familia que su nodo (Melchior/gpt -> subagente gpt; Balthasar/gemini -> subagente gemini).
2. Solo lectura: nunca escribe ni muta el sistema.
3. Devuelve conclusión sintetizada, no volcado íntegro de ficheros (ahorro neto de contexto).
4. Turno único y temperatura baja.
5. Tope duro por nodo y ronda (máximo 2 subagentes para evitar agotar cuotas).
6. Traza visible: publica eventos de trazabilidad.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

MAX_SUBAGENTES_POR_NODO_Y_RONDA = 2


def activado() -> bool:
    """
    `MAGI_SUBAGENTES=1` lo enciende. Apagado por defecto, al reves que el
    abanico, y por una razon: la premisa de F2 —invariante 3, «ahorro neto de
    contexto»— NO esta medida. Un subagente por nodo y ronda son llamadas
    extra a proveedores gratuitos que ya se degradan solos (por eso existe D2).
    Encenderlo por defecto seria dar por buena una ganancia que nadie comprobo.

    El modo apagado existe para medir, no para convivir: cuando haya una ronda
    con subagentes y otra sin ellos, medidas en la misma corrida, esto pasa a
    encendido por defecto o se borra el modulo.
    """
    return os.environ.get("MAGI_SUBAGENTES", "0") == "1"


def ejecutor_de_nube(llm: Any = None, *, temperatura: float = 0.2):
    """
    El ejecutor REAL: pregunta a un modelo de la misma familia que el nodo.

    Invariantes 1, 2 y 4 de este modulo, hechos prompt: misma familia, solo
    lectura y turno unico con temperatura baja. El invariante 3 —conclusion
    sintetica, no volcado— tambien va ahi, porque un subagente que devuelve el
    fichero entero gasta mas contexto del que ahorra.
    """
    async def _ejecutar(*, nodo: str, familia: str, mision: str) -> str:
        cliente = llm
        if cliente is None:
            from magi.core.providers.cloud import FreeCloudLLM
            cliente = FreeCloudLLM()
        sistema = (
            f"Eres un subagente de solo lectura de {nodo}. No escribes, no "
            "ejecutas y no propones: lees y resumes. Responde en menos de 50 "
            "palabras, con la conclusion y el dato que la sostiene. Si no "
            "encuentras nada, dilo: inventar un hallazgo es peor que no traer "
            "ninguno."
        )
        texto, _proveedor = await cliente.generate(
            system_prompt=sistema, user_prompt=mision,
            family=familia, temperature=temperatura,
            tag=f"subagente:{nodo.lower()}")
        return (texto or "").strip()

    return _ejecutar


@dataclass
class SubagenteResultado:
    """Resultado sintético emitido por un subagente de solo lectura."""
    nodo: str
    familia: str
    mision: str
    conclusion: str
    tokens_estimados: int = 0
    herramientas_usadas: list[str] = field(default_factory=list)
    exito: bool = True
    error: str = ""

    def render(self) -> str:
        if not self.exito:
            return f"[{self.nodo}/subagente-{self.familia}] Error: {self.error}"
        return (
            f"[{self.nodo}/subagente-{self.familia} · {self.mision}]\n"
            f"Conclusión: {self.conclusion}"
        )


class GestorSubagentes:
    """Controla la invocación, cuotas y límites de subagentes por nodo y ronda."""

    def __init__(self, limite_por_nodo: int = MAX_SUBAGENTES_POR_NODO_Y_RONDA):
        self.limite_por_nodo = limite_por_nodo
        self._conteo: dict[tuple[str, int], int] = {}

    def registrar_intento(self, nodo: str, round_num: int) -> tuple[bool, str]:
        clave = (nodo.upper(), round_num)
        actual = self._conteo.get(clave, 0)
        if actual >= self.limite_por_nodo:
            return False, (
                f"TOPE EXCEDIDO: {nodo} ya invocó {actual} subagentes en la ronda {round_num}. "
                f"Límite máximo permitido: {self.limite_por_nodo}."
            )
        self._conteo[clave] = actual + 1
        return True, ""

    def subagentes_usados(self, nodo: str, round_num: int) -> int:
        return self._conteo.get((nodo.upper(), round_num), 0)

    def reiniciar(self) -> None:
        self._conteo.clear()


_GESTOR_GLOBAL = GestorSubagentes()


async def despachar_subagente(
    *,
    nodo: str,
    familia: str,
    mision: str,
    round_num: int = 1,
    gestor: GestorSubagentes | None = None,
    bus: Any = None,
    task_id: str = "",
    ejecutor: Any = None,
) -> SubagenteResultado:
    """
    Despacha un subagente de solo lectura de la misma familia que su nodo.

    Retorna la conclusión sintética (máximo unas líneas con evidencia directa).
    """
    g = gestor or _GESTOR_GLOBAL
    ok_cuota, err_cuota = g.registrar_intento(nodo, round_num)
    if not ok_cuota:
        logger.warning(err_cuota)
        return SubagenteResultado(
            nodo=nodo,
            familia=familia,
            mision=mision,
            conclusion="",
            exito=False,
            error=err_cuota,
        )

    # Sin ejecutor no hay subagente, y eso se dice.
    #
    # Aquí había un "fallback determinista" que devolvía
    # `f"Análisis de {mision}: verificado sin hallazgos críticos."` con
    # `exito=True`. Es un «no encontré nada» sin haber mirado nada: viaja al bus
    # como SUBAGENT_TRACE y, en cuanto alguien cablee esto al debate, entra como
    # evidencia. Este proyecto ya pagó ese error dos veces —los 53,3 FPS que
    # Melchior no midió y el `vita_gpu.h` que citó sin que existiera— y la regla
    # que salió de ahí es que una conclusión fabricada es peor que el silencio,
    # porque el crítico la defiende y el debate se va detrás de ella.
    if ejecutor is None:
        falta = ("sin ejecutor: no hay ningún modelo al que preguntar. "
                 "Un subagente sin quien lo ejecute no concluye nada.")
        logger.warning("[SUBAGENTE] %s (%s/%s)", falta, nodo, mision)
        return SubagenteResultado(
            nodo=nodo, familia=familia, mision=mision,
            conclusion="", exito=False, error=falta,
        )
    conclusion = await ejecutor(nodo=nodo, familia=familia, mision=mision)

    tokens_estimados = max(1, len(conclusion.split()))
    resultado = SubagenteResultado(
        nodo=nodo,
        familia=familia,
        mision=mision,
        conclusion=conclusion,
        tokens_estimados=tokens_estimados,
    )

    if bus is not None and hasattr(bus, "publish"):
        try:
            from ...core.bus import BusEvent
            await bus.publish(
                BusEvent(
                    topic="SUBAGENT_TRACE",
                    payload={
                        "task_id": task_id,
                        "nodo": nodo,
                        "familia": familia,
                        "mision": mision,
                        "conclusion": conclusion,
                        "tokens_estimados": tokens_estimados,
                    },
                )
            )
        except Exception as e:
            logger.debug(f"No se pudo publicar SUBAGENT_TRACE: {e}")

    return resultado
