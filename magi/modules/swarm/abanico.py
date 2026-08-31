"""
Fase 7 del megaplan v6: el abanico paralelo.

EL PROBLEMA MEDIDO
==================
Tres esperas independientes tardan 1,50 s en serie y 0,51 s en abanico —
un 66 % menos — mientras los ocho núcleos de la máquina están parados
esperando respuestas de red una detrás de otra.

Las variantes de Melchior y los ejes de Balthasar ya van en `gather`
(`parallel.py`, §2.4). Lo que quedaba en serie:

  1. La EVIDENCIA de Balthasar se recoge DESPUÉS de la tesis, cuando su
     parte command-dependiente (qué se intentó antes, qué hay en el
     workspace, qué restricciones de plataforma hay) no necesita tesis
     ninguna. Aquí esa parte se arranca EN PARALELO con la redacción de
     Melchior: mismo coste de cuota, cero coste de pared mientras quepa
     en la ventana de Melchior.

  2. La verificación de cada variante esperaba a que terminasen TODAS.
     Con `tras_cada`, cada variante se verifica EN CUANTO existe: la
     verificación de la variante temprana corre durante el tiempo en que
     las demás siguen generándose. La ganancia no es teórica: el
     verificador ejecuta el código propuesto con timeouts de hasta 45 s.

Lo que NO se solapa, a propósito: Balthasar no puede refutar una tesis
que aún no existe. Tesis → antítesis → síntesis es una dependencia real,
no una ineficiencia.

LA COMPUERTA
============
La ronda tiene que tardar menos con la misma calidad medida, o esto se
retira. Para poder medirlo hay dos cosas aquí:

  - `CronoDeRonda`: la pared de cada fase se publica en el bus
    (`swarm.fases`) para que cualquier ronda deje sus números.
  - `activado()`: `MAGI_ABANICO=0` apaga el mecanismo y devuelve el
    flujo anterior, para comparar A/B con el mismo código.

Ritsuko no aparece aquí porque ya no bloquea a nadie: audita bajo
demanda y anota por suscripción al bus. Esa fila del plan estaba
resuelta por arquitectura antes de esta fase.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time

logger = logging.getLogger(__name__)

#: Cuánto puede crecer el dossier del recon. Un dossier sin tope es una
#: forma elegante de inflar el prompt de los cuatro ejes con prosa.
TOPE_DOSSIER_CHARS = 1500


def activado() -> bool:
    """`MAGI_ABANICO=0` lo apaga. Todo lo demás (incluido sin la variable)
    lo deja encendido: el mecanismo es el camino por defecto y el modo
    apagado existe para MEDIR, no para convivir."""
    return os.environ.get("MAGI_ABANICO", "1") != "0"


class CronoDeRonda:
    """
    La pared de cada fase, medida y publicada.

    Sin números no hay compuerta: «parece más rápido» es exactamente el
    tipo de afirmación que este sistema lleva tres versiones aprendiendo
    a rechazar. Cada fase se marca al terminar; `payload()` produce lo
    que viaja al bus para que la ronda deje su medición escrita.
    """

    def __init__(self) -> None:
        self._t0 = time.monotonic()
        self._fases: dict[str, float] = {}
        self._inicio_fase: dict[str, float] = {}

    def inicio(self, fase: str) -> None:
        self._inicio_fase[fase] = time.monotonic()

    def fin(self, fase: str) -> None:
        arranca = self._inicio_fase.pop(fase, self._t0)
        self._fases[fase] = time.monotonic() - arranca

    def ms(self, fase: str) -> int:
        return round(self._fases.get(fase, 0.0) * 1000)

    def payload(self, **extra) -> dict:
        datos = {f"t_{f}_ms": self.ms(f) for f in self._fases}
        datos["t_ronda_ms"] = round((time.monotonic() - self._t0) * 1000)
        datos.update(extra)
        return datos


async def recon_de_encargo(agent, *, task_id: str, command: str,
                           round_num: int, engine: str = "fast",
                           narrative_style: str = "tecnico") -> str:
    """
    Evidencia de Balthasar que NO depende de la tesis.

    Arranca cuando arranca la ronda —con el encargo, sin propuesta— y
    reúne HECHOS: intentos previos en la memoria, artefactos que ya
    existen, restricciones de plataforma. Cuando la propuesta existe,
    los cuatro ejes reciben este dossier ya hecho y empiezan su crítica
    con el terreno reconocido en vez de explorarlo cada uno por su
    cuenta después de que la tesis ya esté encima de la mesa.

    Es UNA llamada corta con herramientas de lectura, no un segundo
    crítico: sin opinión, sin propuesta, con tope de líneas. Si falla o
    no encuentra nada, devuelve "" — un dossier vacío no es un error,
    es un encargo sin antecedentes.
    """
    import copy

    mio = copy.copy(agent)
    # Sin hedge: el recon es evidencia opcional, no una llamada que la
    # ronda necesite cubrir. Triplicarlo es quemar cuota en un informe
    # que los ejes pueden vivir sin él.
    mio.hedge = False
    mio.rama = f"{task_id}/r{round_num}/balthasar/recon"
    mio.rama_rol = "recon"
    mio.rama_profundidad = 1
    sys_prompt = (
        "Eres BALTHASAR en modo RECONOCIMIENTO. AÚN NO HAY PROPUESTA: no "
        "critiques nada, no propongas nada.\n\n"
        "Reúne HECHOS verificables sobre el ENCARGO que llega abajo, para "
        "poder criticar con el terreno reconocido cuando la propuesta "
        "exista:\n"
        "- intentos previos sobre lo mismo y cómo acabaron (search_memory);\n"
        "- ficheros o artefactos relevantes que ya existan en el workspace;\n"
        "- restricciones de plataforma reales (dependencias disponibles, "
        "sistema, rutas).\n\n"
        "SOLO hechos con su fuente. Máximo 12 líneas. Si no hay nada, "
        "escribe exactamente «nada relevante»: inventar antecedentes es "
        "peor que no tenerlos. Sin preámbulo.")
    user = f"ENCARGO:\n{command}"
    try:
        content, _, _ = await mio._ask_with_tools(
            sys_prompt, user, task_id=task_id, engine=engine,
            narrative_style=narrative_style,
            max_iters=(2 if engine == "fast" else 3))
    except Exception as e:
        logger.info("[abanico] recon falló (se sigue sin dossier): %s", e)
        return ""
    dossier = (content or "").strip()[:TOPE_DOSSIER_CHARS]
    if dossier and dossier.lower() != "nada relevante":
        logger.info("[abanico] recon listo: %d chars", len(dossier))
        return dossier
    return ""


def cosechar_recon(task: asyncio.Task | None) -> str:
    """
    Recoge el recon SIN esperar jamás.

    La regla que sostiene el abanico: el recon puede acabar dentro de la
    ventana de Melchior o no existir, pero NUNCA puede alargar la ronda.
    Si no ha terminado cuando la tesis está lista, se cancela y se sigue
    sin dossier — lo que se pierde es evidencia opcional, no la pared.
    """
    if task is None:
        return ""
    if task.done():
        try:
            return task.result()
        except Exception:
            return ""
    task.cancel()
    logger.info("[abanico] recon no llegó a tiempo; se cancela y se "
                "continúa sin dossier")
    return ""
