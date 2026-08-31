"""
Fase 8 del megaplan v6: la réplica — que Melchior conteste a la objeción.

EL JUICIO EN REBELDÍA
=====================
Hasta ahora el flujo era de una pasada: Melchior propone, Balthasar
refuta, Casper sintetiza. Melchior NUNCA contestaba a la objeción, y
Casper arbitraba entre una tesis y una crítica que la tesis no había
podido responder. No es un debate: es un juicio en rebeldía.

El diseño, con lo que lo hace pagable (cuatro condiciones, ninguna
negociable):

  1. CONDICIONAL. Solo si hay desacuerdo real. Los ejes de Balthasar
     firman cuántas objeciones sostienen (`OBJECIONES: N`); si la suma
     es cero, no hay réplica. La segunda vuelta se gana, no se regala.
  2. ACOTADA. Viaja solo el extracto de objeciones y la respuesta a ese
     extracto: ~300 tokens, no el contexto entero.
  3. UNA SOLA VUELTA. Tope duro. Tres nodos discutiendo sin límite es
     un sistema que no termina.
  4. CON SALIDA. Melchior puede empezar su réplica con «CONCESIÓN:» —
     rendirse ante una objeción válida y cerrar ANTES de Casper. Una
     réplica que no puede rendirse es teatro.

LA COMPUERTA DE VIDA O MUERTE
=============================
Casper tiene que cambiar de veredicto al menos 1 de cada 5 rondas con
réplica respecto a lo que habría dictado sin ella. Si nunca cambia, la
réplica no aporta y se retira.

El contrafactual («lo que habría dictado sin réplica») no se puede
saber sin correrlo. Por eso existe el modo sombra: con
`MAGI_REPLICA_SOMBRA=1`, cada réplica defensiva va acompañada de un
arbitraje paralelo SIN la réplica (callado, sin publicar), las dos
decisiones se comparan y el resultado se registra en
`magi/data/memoria/replica.jsonl`. Con ese fichero, la compuerta se
evalúa con datos, no con impresiones — y si el contador da cero, la
propia evidencia pide retirar el mecanismo.
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

__all__ = [
    "MARCADOR", "contar_objeciones", "extracto_de_objeciones",
    "replica_de_melchior", "es_concesion", "veredicto_por_concesion",
    "sombra_activada", "registrar",
]

#: La firma del desacuerdo. Cada eje de Balthasar cierra con
#: `OBJECIONES: N` — cuántas objeciones REALES sostiene en ese eje.
#: Un marcador extraído de texto libre, como la línea DECISIÓN de Casper:
#: pedir JSON aquí volvió ilegible a Casper y no va a funcionar mejor
#: en Balthasar.
MARCADOR = re.compile(r"OBJECIONES\s*:\s*(\d+)", re.IGNORECASE)

#: La réplica viaja acotada: este es el techo del extracto de objeciones
#: que se le enseña a Melchior. ~300 tokens de intercambio, no 8.000.
TOPE_EXTRACTO_CHARS = 1400
TOPE_REPLICA_CHARS = 900


def contar_objeciones(por_eje: dict[str, str]) -> tuple[int, int]:
    """
    (total de objeciones firmadas, cuántos ejes firmaron el marcador).

    El segundo número importa para el diagnóstico: si los proveedores
    dejan de firmar `OBJECIONES: N`, el mecanismo se apaga solo sin que
    nadie lo note — y eso hay que poder verlo en la telemetría, no
    descubrirlo cuando alguien eche de menos el debate.
    """
    total, firmas = 0, 0
    for texto in (por_eje or {}).values():
        m = MARCADOR.search(texto or "")
        if m:
            firmas += 1
            try:
                total += max(0, int(m.group(1)))
            except ValueError:
                pass
    return total, firmas


def extracto_de_objeciones(por_eje: dict[str, str]) -> str:
    """Las objeciones, acotadas, para que la réplica no arrastre el
    contexto entero de la crítica."""
    partes = []
    for eje, texto in (por_eje or {}).items():
        m = MARCADOR.search(texto or "")
        if m:
            try:
                n = int(m.group(1))
            except ValueError:
                n = 0
            if n > 0:
                cuerpo = (texto or "").split("OBJECIONES", 1)[0].strip()
                partes.append(f"[{eje}] {cuerpo}")
    extracto = "\n\n".join(partes)[:TOPE_EXTRACTO_CHARS]
    return extracto


async def replica_de_melchior(agent, *, task_id: str, objeciones: str,
                              round_num: int, engine: str = "fast",
                              narrative_style: str = "tecnico") -> str:
    """
    LA réplica: una vuelta, sin herramientas, máximo 8 líneas.

    Sin herramientas a propósito: la réplica discute las objeciones que
    ya están sobre la mesa, no rehace la propuesta. Rehacerla aquí sería
    una segunda tesis, y eso es exactamente la escalera sin fin que el
    tope de una vuelta existe para cortar.
    """
    import copy

    mio = copy.copy(agent)
    mio.hedge = False
    mio.rama = f"{task_id}/r{round_num}/melchior/replica"
    mio.rama_rol = "réplica"
    mio.rama_profundidad = 1
    sys_prompt = (
        "Eres MELCHIOR. Balthasar ha objetado tu propuesta y tienes UNA "
        "réplica. Una sola: no habrá otra vuelta.\n\n"
        "Responde SOLO a las objeciones, en máximo 8 líneas, sin "
        "preámbulo.\n"
        "Si una objeción es correcta, EMPIEZA tu primera línea con "
        "«CONCESIÓN:» y di cuál aceptas — rendirse ante una objeción "
        "válida cierra el debate antes y es una salida legítima, no una "
        "derrota.\n"
        "Si la objeción viene de un malentendido, cita la línea exacta "
        "que lo desmiente. Lo que NO vale es defender lo indefendible: "
        "Balthasar ejecutó el código, y tú no.")
    user = f"OBJECIONES DE BALTHASAR:\n\n{objeciones}\n\nTu réplica:"
    try:
        content, _, _ = await mio._ask(
            sys_prompt, user, engine=engine, narrative_style=narrative_style)
    except Exception as e:
        logger.info("[replica] falló (se arbitra sin réplica): %s", e)
        return ""
    return (content or "").strip()[:TOPE_REPLICA_CHARS]


def es_concesion(texto: str) -> bool:
    """¿Melchior se rindió? Se mira la PRIMERA línea, no cualquier sitio:
    una réplica que mencione «concesión» a mitad de defensa no es una
    rendición, y tratarla como tal cerraría debates abiertos."""
    for linea in (texto or "").splitlines():
        linea = linea.strip().lstrip("*#>- ")
        if linea:
            return linea.upper().startswith("CONCESIÓN") or \
                linea.upper().startswith("CONCESION")
    return False


def veredicto_por_concesion(critique: dict, texto_replica: str) -> dict:
    """
    El veredicto cuando Melchior se rinde: sin Casper.

    La concesión ya ES el arbitraje — hay acuerdo entre tesis y
    antítesis, que es lo que Casper existe para producir. Llamarlo
    aquí sería gastar una llamada en firmar lo que las dos partes ya
    dicen. Se entra por la misma puerta que un REJECTED_NEEDS_WORK:
    ronda de revisión con la objeción aceptada como instrucción.
    """
    cuerpo = (critique or {}).get("content", "")
    return {
        "decision": "REJECTED_NEEDS_WORK",
        "feedback": (
            "**Melchior concede ante la objeción de Balthasar.** La réplica "
            "cerró el debate antes del arbitraje: hay acuerdo en que la "
            f"propuesta debe corregirse.\n\n## Concesión de Melchior\n\n"
            f"{texto_replica}\n\n## Crítica que la motivó\n\n{cuerpo}"),
    }


def sombra_activada() -> bool:
    """Modo medición: corre el contrafactual y regístralo."""
    return os.environ.get("MAGI_REPLICA_SOMBRA", "0") == "1"


@dataclass
class CierreDebate:
    """Lo que `ronda()` le devuelve al orquestador: un veredicto SIEMPRE
    (de Casper o de la concesión), el evento para la telemetría, y `parar`
    si la réplica pidió la parada de emergencia."""
    verdict: dict
    evento: dict
    texto: str = ""
    parar: bool = False


async def ronda(melchior, casper, *, task_id: str, multi, proposal: dict,
                critique: dict, round_num: int, engine: str, style: str,
                use_tools: bool, techo: int, usadas: int, bus) -> CierreDebate:
    """
    El cierre del debate con segunda vuelta: réplica y, si no hay concesión,
    arbitraje con la réplica sobre la mesa.

    Vive aquí y no en el orquestador porque el orquestador roza su techo de
    líneas y esta mecánica es cohesiva: decide si hay réplica, la publica,
    detecta la concesión, corre la sombra si se pidió, y arbitra. El bucle
    se queda con lo que le toca — el flujo: qué veredicto sale, si hay que
    parar y qué se registra.
    """
    from magi.core.bus import BusEvent

    n_obj, n_firmas = contar_objeciones(getattr(multi, "by_axis", {}) or {})
    evento = {"fired": False, "concedio": False, "firmas": n_firmas}
    texto = ""
    if n_obj > 0 and usadas + 2 < techo:
        texto = await replica_de_melchior(
            melchior, task_id=task_id,
            objeciones=extracto_de_objeciones(multi.by_axis),
            round_num=round_num, engine=engine, narrative_style=style)
    if not texto:
        return CierreDebate(verdict=await casper.arbitrate(
            task_id, proposal, critique, round_num, engine, style,
            use_tools=use_tools), evento=evento)

    if "SYS_EMERGENCY_STOP" in texto:
        return CierreDebate(verdict={"decision": "SIN_ARBITRAJE",
                                     "feedback": texto},
                            evento=evento, texto=texto, parar=True)
    evento.update(fired=True, objeciones=n_obj)
    await bus.publish(BusEvent(topic="AGENT_POST", payload={
        "type": "AGENT_POST", "task_id": task_id, "agent": "MELCHIOR",
        "role": "replica", "provider": melchior.family,
        "family": melchior.family, "content": texto, "changes": 0,
        "stats": f"réplica a {n_obj} objeción(es)"}))

    if es_concesion(texto):
        evento["concedio"] = True
        return CierreDebate(
            verdict=veredicto_por_concesion(critique, texto),
            evento=evento, texto=texto)

    critique["replica"] = texto
    # COMPUERTA (modo medición): el contrafactual «qué habría dictado SIN
    # réplica» no se sabe sin correrlo. Con MAGI_REPLICA_SOMBRA=1 se arbitra
    # una copia sin réplica, callada, y las dos decisiones se comparan en
    # replica.jsonl. Es una llamada extra: solo para medir.
    sombra = None
    if sombra_activada():
        crit_sombra = dict(critique)
        crit_sombra.pop("replica", None)
        sombra = {"sin": (await casper.arbitrate(
            task_id, proposal, crit_sombra, round_num, engine, style,
            use_tools=use_tools, publicar=False))["decision"], "con": None}
    verdict = await casper.arbitrate(
        task_id, proposal, critique, round_num, engine, style,
        use_tools=use_tools)
    if sombra is not None:
        sombra["con"] = verdict.get("decision")
        sombra["cambia"] = (sombra["sin"] != sombra["con"])
        evento["sombra"] = sombra
    return CierreDebate(verdict=verdict, evento=evento, texto=texto)


def registrar(evento: dict, inicio=None) -> bool:
    """
    Una línea JSONL por ronda con réplica, en memoria permanente.

    Mismo formato y misma casa que `descartes.jsonl`: append de una
    línea, sin releer el histórico. Si no se puede escribir, la ronda
    sigue — la medición no puede tener autoridad para tumbar el
    mecanismo que mide.
    """
    from magi.modules.swarm.memoria_persistente import raiz

    r = raiz(inicio)
    if r is None:
        return False
    entrada = dict(evento)
    entrada["ts"] = datetime.datetime.now().isoformat(timespec="seconds")
    try:
        with open(r / "replica.jsonl", "a", encoding="utf-8",
                  newline="\n") as f:
            f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
        return True
    except OSError as e:
        logger.warning("[replica] no se pudo registrar: %s", e)
        return False
