"""
Ciclo de mejora de Naoko con rondas del enjambre.

QUÉ SE PIDIÓ, Y POR QUÉ SON DOS VÍAS Y NO UNA
=============================================
La instrucción tiene dos mitades que parecen contradecirse y no lo hacen:

    "que naoko siempre autocorrija todo el sistema sin consultarme"
    "cuando naoko tenga una idea de mejora que me consulte"

No es lo mismo REPARAR que MEJORAR:

  · Reparar es devolver el sistema a donde ya debía estar. Hay un fallo, hay
    tests que lo demuestran, y la corrección es verificable — si los tests
    quedan verdes, acertó. Consultar cada arreglo convierte al usuario en el
    cuello de botella de su propio sistema. Va sin puertas (§3.1).

  · Mejorar es cambiar hacia dónde va el sistema. No hay un "correcto"
    contra el que comprobar: hay un criterio, y el criterio es del usuario.
    Un agente que reescribe la arquitectura porque le pareció más elegante,
    sin preguntar, no es autónomo — es incontrolable.

Y publicar es siempre del usuario, aunque el cambio sea una reparación: subir
a GitHub es visible para terceros y no se deshace con un `undo`.

EL CIRCUITO
===========
Cuando Naoko tiene una idea (o el usuario propone una), el plan da DOS vueltas
completas al enjambre antes de volver al usuario:

    Naoko redacta el plan
        │
        ├─ [COMPUERTA] el usuario autoriza redactarlo
        │
    ┌───▼──────────────────────────────────────────────┐
    │  MELCHIOR   analiza, mejora y añade sus críticas  │
    │  BALTHASAR  examina el plan Y lo que dijo         │
    │             Melchior; crítica popperiana          │
    │  CASPER     evalúa las tres cosas por separado,   │
    │             se pronuncia y puede añadir temas      │
    └───┬──────────────────────────────────────────────┘
        │  vuelve automáticamente (2 circuitos)
        │
    CASPER entrega el plan hiperperfeccionado
        │
        ├─ [COMPUERTA] el usuario aprueba
        │
    NAOKO ejecuta, narrando cada paso
        │
        └─ [COMPUERTA] el usuario autoriza publicar

Dos vueltas y no una porque la segunda es donde el circuito gana algo: en la
primera cada nodo ve el plan por primera vez; en la segunda ve el plan YA
criticado por los otros dos, que es cuando una crítica puede refutar a otra.
Una sola vuelta es tres opiniones en paralelo disfrazadas de debate.

LAS COMPUERTAS NO SE PUEDEN SALTAR
==================================
Están en la máquina de estados, no en el prompt. Un modelo puede ignorar una
instrucción del prompt; no puede saltarse una transición que no existe. Es la
diferencia entre pedirle a un agente que consulte y hacer que no le quede otra.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from ...core.paths import db_path

logger = logging.getLogger(__name__)

#: Vueltas completas al enjambre antes de volver al usuario. Dos porque la
#: segunda es donde cada nodo ve el plan ya criticado por los otros.
CIRCUITOS = 2


class Stage(str, Enum):
    """
    Dónde está una mejora. Cada valor es un estado real, no una etiqueta.

    Hay estados de ESPERA (compuertas) y estados de TRABAJO. La distinción no
    es cosmética: la primera versión no tenía estados de trabajo, así que la
    decisión del usuario avanzaba directamente al estado siguiente ANTES de
    que la fase hubiera hecho nada. Dos consecuencias medidas:

      · La compuerta `plan_borrador` se presentaba con el plan VACÍO, porque
        `draft_plan` aún estaba escribiéndolo.
      · Al aprobar la publicación, la fila decía `publicado` antes de
        publicar. Si la compilación fallaba, se quedaba en `publicado` — que
        es terminal — sin reintento ni descarte posibles.

    Un estado que afirma algo que no ha ocurrido es la misma clase de fallo
    que el botón de parada que no paraba.
    """
    IDEA = "idea"                       # espera: ¿redacto el plan?
    REDACTANDO = "redactando"           # trabajo: Naoko escribe el plan
    PLAN_BORRADOR = "plan_borrador"     # espera: ¿lo paso al enjambre?
    RONDA = "ronda"                     # trabajo: circula por los tres nodos
    PLAN_FINAL = "plan_final"           # espera: ¿lo apruebo y ejecuto?
    EJECUTANDO = "ejecutando"           # trabajo: Naoko lo aplica
    ESPERANDO_PUBLICACION = "esperando_publicacion"   # espera: ¿publico?
    PUBLICANDO = "publicando"           # trabajo: build, README, tag, push
    PUBLICADO = "publicado"             # terminal, y solo si SALIÓ BIEN
    FALLIDA = "fallida"                 # espera: ¿reintento o descarto?
    DESCARTADA = "descartada"


#: Compuertas del usuario. Salir de estos estados EXIGE una decisión suya.
GATES = {Stage.IDEA, Stage.PLAN_BORRADOR, Stage.PLAN_FINAL,
         Stage.ESPERANDO_PUBLICACION, Stage.FALLIDA}

#: Estados desde los que se puede caer a FALLIDA. Son los de trabajo: si una
#: fase revienta, el ciclo tiene que quedar en un sitio del que se pueda salir.
#: Antes se quedaba en `ronda` o `ejecutando`, que no son compuertas — ni
#: `user_decides` los aceptaba ni había forma de reanudar: solo se salía
#: editando SQLite a mano.
TRABAJO = {Stage.REDACTANDO, Stage.RONDA, Stage.EJECUTANDO, Stage.PUBLICANDO}

#: De dónde vino cada fase de trabajo, para poder reintentarla.
REINTENTO: dict[Stage, Stage] = {
    Stage.REDACTANDO: Stage.IDEA,
    Stage.RONDA: Stage.PLAN_BORRADOR,
    Stage.EJECUTANDO: Stage.PLAN_FINAL,
    Stage.PUBLICANDO: Stage.ESPERANDO_PUBLICACION,
}

#: Transiciones permitidas. Lo que no está aquí no puede pasar.
TRANSICIONES: dict[Stage, set[Stage]] = {
    Stage.IDEA: {Stage.REDACTANDO, Stage.DESCARTADA},
    Stage.REDACTANDO: {Stage.PLAN_BORRADOR, Stage.FALLIDA, Stage.DESCARTADA},
    Stage.PLAN_BORRADOR: {Stage.RONDA, Stage.DESCARTADA},
    Stage.RONDA: {Stage.RONDA, Stage.PLAN_FINAL, Stage.FALLIDA, Stage.DESCARTADA},
    # Sin vuelta a RONDA: con las seis rondas ya registradas,
    # `next_actor` devuelve None, el bucle de `run_circuit` no da una
    # sola vuelta y la mejora queda en `ronda`, que no es compuerta.
    # Volver a criticar un plan final es empezar una mejora nueva.
    Stage.PLAN_FINAL: {Stage.EJECUTANDO, Stage.DESCARTADA},
    Stage.EJECUTANDO: {Stage.ESPERANDO_PUBLICACION, Stage.FALLIDA, Stage.DESCARTADA},
    Stage.ESPERANDO_PUBLICACION: {Stage.PUBLICANDO, Stage.DESCARTADA},
    # Solo se llega a PUBLICADO desde PUBLICANDO y habiendo salido bien.
    Stage.PUBLICANDO: {Stage.PUBLICADO, Stage.FALLIDA, Stage.DESCARTADA},
    Stage.PUBLICADO: set(),
    Stage.FALLIDA: {Stage.IDEA, Stage.PLAN_BORRADOR, Stage.PLAN_FINAL,
                    Stage.ESPERANDO_PUBLICACION, Stage.DESCARTADA},
    Stage.DESCARTADA: set(),
}

#: El orden dentro de un circuito. No es configurable a propósito: el sentido
#: del recorrido es el argumento popperiano, no una preferencia.
SECUENCIA = ("MELCHIOR", "BALTHASAR", "CASPER")


class ImprovementError(RuntimeError):
    """La transición pedida no existe, o falta una decisión del usuario."""


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class RoundEntry:
    """Lo que un nodo aportó en su turno."""
    circuit: int          # 1..CIRCUITOS
    agent: str            # MELCHIOR | BALTHASAR | CASPER
    content: str
    at: str = field(default_factory=_ahora)

    @property
    def label(self) -> str:
        papel = {"MELCHIOR": "análisis y mejoras",
                 "BALTHASAR": "crítica popperiana",
                 "CASPER": "arbitraje"}.get(self.agent, "aportación")
        return f"circuito {self.circuit} · {self.agent} ({papel})"


@dataclass
class Improvement:
    improvement_id: str
    origin: str                  # "naoko" (idea propia) | "usuario" (propuesta)
    title: str
    rationale: str = ""          # por qué cree que mejora
    plan: str = ""               # el plan extenso, se reescribe cada circuito
    stage: Stage = Stage.IDEA
    circuit: int = 0
    rounds: list[RoundEntry] = field(default_factory=list)
    execution_log: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_ahora)
    updated_at: str = field(default_factory=_ahora)
    release_notes: str = ""
    #: Por qué falló, y desde qué fase, para poder reintentar exactamente esa.
    failure: str = ""
    failed_from: str = ""

    @property
    def awaiting_user(self) -> bool:
        return self.stage in GATES

    @property
    def question(self) -> str:
        """Qué se le está preguntando exactamente al usuario, ahora mismo."""
        if self.stage is Stage.IDEA:
            return (f"¿Desarrollo un plan detallado para «{self.title}»? "
                    f"(sí / no)")
        if self.stage is Stage.PLAN_BORRADOR:
            return ("¿El plan te parece bien para pasarlo al enjambre? "
                    "(sí / no)")
        if self.stage is Stage.PLAN_FINAL:
            return (f"Plan hiperperfeccionado tras {self.circuit} circuito(s) "
                    f"del enjambre. ¿Lo apruebo y lo ejecuto? (sí / no)")
        if self.stage is Stage.ESPERANDO_PUBLICACION:
            return "Mejora aplicada. ¿La subo a GitHub y publico release? (sí / no)"
        if self.stage is Stage.FALLIDA:
            return (f"La fase falló: {self.failure or 'sin detalle'}. "
                    f"¿Lo reintento? (sí / no)")
        return ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["stage"] = self.stage.value
        d["awaiting_user"] = self.awaiting_user
        d["question"] = self.question
        return d

    def render(self) -> str:
        """Lo que ve el usuario. Naoko es EXPRESA en todo lo que hace."""
        origen = ("idea propia de Naoko" if self.origin == "naoko"
                  else "propuesta tuya")
        out = [f"MEJORA {self.improvement_id} — {self.title}",
               f"origen: {origen} · estado: {self.stage.value}", ""]
        if self.rationale:
            out += [f"Por qué: {self.rationale}", ""]
        if self.plan:
            out += ["PLAN:", self.plan, ""]
        if self.rounds:
            out.append("RECORRIDO POR EL ENJAMBRE:")
            for r in self.rounds:
                out.append(f"  · {r.label}")
            out.append("")
        if self.execution_log:
            out.append("EJECUCIÓN:")
            out += [f"  {p}" for p in self.execution_log]
            out.append("")
        if self.awaiting_user:
            out.append(f">>> {self.question}")
        return "\n".join(out)


class ImprovementLog:
    """Persistencia. Una mejora a medias no puede perderse al cerrar la app."""

    def __init__(self, path: str | Path | None = None):
        self.path = str(path or db_path())
        self._init()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path, check_same_thread=False)
        c.row_factory = sqlite3.Row
        return c

    def _init(self) -> None:
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS improvement (
                    improvement_id TEXT PRIMARY KEY,
                    origin         TEXT NOT NULL,
                    title          TEXT NOT NULL,
                    rationale      TEXT NOT NULL DEFAULT '',
                    plan           TEXT NOT NULL DEFAULT '',
                    stage          TEXT NOT NULL,
                    circuit        INTEGER NOT NULL DEFAULT 0,
                    rounds         TEXT NOT NULL DEFAULT '[]',
                    execution_log  TEXT NOT NULL DEFAULT '[]',
                    release_notes  TEXT NOT NULL DEFAULT '',
                    failure        TEXT NOT NULL DEFAULT '',
                    failed_from    TEXT NOT NULL DEFAULT '',
                    created_at     TEXT NOT NULL,
                    updated_at     TEXT NOT NULL,
                    ts             REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_improvement_stage
                    ON improvement(stage, updated_at DESC);
            """)
            # Migración: una base creada antes de los estados de fallo no
            # tiene estas columnas, y perder mejoras a medias por añadir un
            # campo sería absurdo.
            existentes = {r["name"] for r in
                          c.execute("PRAGMA table_info(improvement)")}
            for col in ("failure", "failed_from"):
                if col not in existentes:
                    c.execute(f"ALTER TABLE improvement ADD COLUMN "
                              f"{col} TEXT NOT NULL DEFAULT ''")

    def save(self, m: Improvement) -> None:
        m.updated_at = _ahora()
        with self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO improvement (improvement_id, origin,"
                " title, rationale, plan, stage, circuit, rounds,"
                " execution_log, release_notes, failure, failed_from,"
                " created_at, updated_at, ts)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (m.improvement_id, m.origin, m.title, m.rationale, m.plan,
                 m.stage.value, m.circuit,
                 json.dumps([asdict(r) for r in m.rounds], ensure_ascii=False),
                 json.dumps(m.execution_log, ensure_ascii=False),
                 m.release_notes, m.failure, m.failed_from,
                 m.created_at, m.updated_at, time.time()))

    @staticmethod
    def _row(r: sqlite3.Row) -> Improvement:
        return Improvement(
            improvement_id=r["improvement_id"], origin=r["origin"],
            title=r["title"], rationale=r["rationale"], plan=r["plan"],
            stage=Stage(r["stage"]), circuit=r["circuit"],
            rounds=[RoundEntry(**d) for d in json.loads(r["rounds"] or "[]")],
            execution_log=json.loads(r["execution_log"] or "[]"),
            release_notes=r["release_notes"],
            failure=r["failure"] if "failure" in r.keys() else "",
            failed_from=r["failed_from"] if "failed_from" in r.keys() else "",
            created_at=r["created_at"], updated_at=r["updated_at"])

    def get(self, improvement_id: str) -> Improvement | None:
        with self._conn() as c:
            r = c.execute("SELECT * FROM improvement WHERE improvement_id=?",
                          (improvement_id,)).fetchone()
        return self._row(r) if r else None

    def all(self) -> list[Improvement]:
        with self._conn() as c:
            return [self._row(r) for r in
                    c.execute("SELECT * FROM improvement ORDER BY updated_at DESC")]

    def pending_user(self) -> list[Improvement]:
        """Las que están esperando una decisión tuya. Sin esto se olvidan."""
        return [m for m in self.all() if m.awaiting_user]

    def active(self) -> Improvement | None:
        """La que está en curso, si hay alguna."""
        vivos = [m for m in self.all()
                 if m.stage not in (Stage.PUBLICADO, Stage.DESCARTADA)]
        return vivos[0] if vivos else None


# --------------------------------------------------------------- transiciones

def advance(m: Improvement, destino: Stage) -> Improvement:
    """
    Mueve una mejora de estado, comprobando que la transición existe.

    Las compuertas viven AQUÍ y no en el prompt de Naoko. Un modelo puede
    ignorar "consulta antes de continuar"; no puede inventarse una transición
    que la máquina de estados no tiene. Es la diferencia entre pedirle a un
    agente que consulte y hacer que no le quede otra.
    """
    permitidas = TRANSICIONES.get(m.stage, set())
    if destino not in permitidas:
        raise ImprovementError(
            f"no se puede pasar de {m.stage.value} a {destino.value}. "
            f"Permitido desde aquí: "
            f"{', '.join(sorted(s.value for s in permitidas)) or 'nada, es final'}")
    m.stage = destino
    m.updated_at = _ahora()
    return m


def user_decides(m: Improvement, approve: bool) -> Improvement:
    """
    Aplica la decisión del usuario en una compuerta.

    Un "no" NO es un fallo: descarta la mejora y se sigue. Tratar el rechazo
    como un error empuja a insistir, y una propuesta que insiste deja de ser
    una propuesta.
    """
    if not m.awaiting_user:
        raise ImprovementError(
            f"{m.improvement_id} está en {m.stage.value} y no espera ninguna "
            f"decisión tuya")
    if not approve:
        return advance(m, Stage.DESCARTADA)

    if m.stage is Stage.FALLIDA:
        # Reintentar es volver a la compuerta de la que salió la fase rota, no
        # repetirla a ciegas: el usuario vuelve a decidir con lo que ya sabe.
        destino = Stage(m.failed_from) if m.failed_from else Stage.IDEA
        m.failure = ""
        m.failed_from = ""
        return advance(m, destino)

    siguiente = {
        Stage.IDEA: Stage.REDACTANDO,
        Stage.PLAN_BORRADOR: Stage.RONDA,
        Stage.PLAN_FINAL: Stage.EJECUTANDO,
        # NO a PUBLICADO: a PUBLICANDO. Marcar publicado antes de publicar es
        # exactamente lo que este proyecto lleva media reconstrucción
        # corrigiendo en otros sitios.
        Stage.ESPERANDO_PUBLICACION: Stage.PUBLICANDO,
    }[m.stage]
    return advance(m, siguiente)


def fail(m: Improvement, motivo: str) -> Improvement:
    """
    Una fase de trabajo reventó. Deja la mejora en un sitio del que se sale.

    Antes las excepciones dejaban el estado en `ronda` o `ejecutando`, que no
    son compuertas: `user_decides` los rechazaba, no había RPC de reanudar, y
    `active()` los devolvía para siempre. La única salida era editar SQLite.
    """
    if m.stage not in TRABAJO:
        raise ImprovementError(
            f"{m.stage.value} no es una fase de trabajo; no puede fallar")
    m.failed_from = REINTENTO[m.stage].value
    m.failure = str(motivo)[:400]
    return advance(m, Stage.FALLIDA)


def next_actor(m: Improvement) -> tuple[int, str] | None:
    """
    A quién le toca ahora dentro del circuito, o None si ya se completaron.

    Devuelve (circuito, agente). El recorrido es Melchior → Balthasar →
    Casper, y al acabar Casper empieza el circuito siguiente
    AUTOMÁTICAMENTE — sin pasar por el usuario, que es lo que se pidió.
    """
    if m.stage is not Stage.RONDA:
        return None
    hechos = len(m.rounds)
    if hechos >= CIRCUITOS * len(SECUENCIA):
        return None
    return hechos // len(SECUENCIA) + 1, SECUENCIA[hechos % len(SECUENCIA)]


def record_round(m: Improvement, agent: str, content: str) -> Improvement:
    """Anota la aportación de un nodo y avanza el circuito."""
    siguiente = next_actor(m)
    if siguiente is None:
        raise ImprovementError(
            f"{m.improvement_id} no está en fase de rondas o ya las completó")
    circuito, esperado = siguiente
    if agent != esperado:
        raise ImprovementError(
            f"le toca a {esperado} en el circuito {circuito}, no a {agent}. "
            f"El orden del recorrido es el argumento, no una preferencia")

    m.rounds.append(RoundEntry(circuit=circuito, agent=agent, content=content))
    m.circuit = circuito
    m.updated_at = _ahora()

    if next_actor(m) is None:
        advance(m, Stage.PLAN_FINAL)
    return m


def start(origin: str, title: str, rationale: str = "",
          plan: str = "") -> Improvement:
    """
    Abre una mejora.

    Las dos entradas —idea de Naoko y propuesta del usuario— arrancan en el
    MISMO estado a propósito. Se pidió que la propuesta del usuario "deberá
    ser pasada a Melchior con el sistema de rondas, igual que cuando Naoko
    tiene una idea": mismo recorrido, mismas compuertas. Que la idea venga de
    ti no la exime de la crítica; si acaso al revés.
    """
    if origin not in ("naoko", "usuario"):
        raise ImprovementError("el origen es 'naoko' o 'usuario'")
    if not title.strip():
        raise ImprovementError("una mejora sin enunciado no se puede evaluar")
    return Improvement(
        improvement_id=f"mej_{uuid.uuid4().hex[:10]}", origin=origin,
        title=title.strip(), rationale=rationale.strip(), plan=plan.strip())


# ------------------------------------------------------------------- prompts

def prompt_for(m: Improvement, agent: str) -> str:
    """
    Qué se le pide a cada nodo, con TODO lo anterior delante.

    Balthasar recibe el plan Y lo que dijo Melchior; Casper recibe las tres
    cosas por separado y no un resumen. Es literalmente lo que se pidió, y
    además es lo único que hace que el circuito valga algo: un crítico que no
    ve la crítica anterior no puede refutarla.
    """
    previo = "\n\n".join(
        f"--- {r.label} ---\n{r.content}" for r in m.rounds)
    cabecera = (
        f"PLAN DE MEJORA propuesto por "
        f"{'Naoko' if m.origin == 'naoko' else 'el usuario'}: {m.title}\n"
        f"Motivo: {m.rationale}\n\n{m.plan}")

    if agent == "MELCHIOR":
        tarea = (
            "Analiza este plan, MEJÓRALO y añade tus críticas, buenas y malas. "
            "Devuelve el plan reescrito e íntegro con tus correcciones "
            "incorporadas, y al final una sección 'CRÍTICAS DE MELCHIOR' con lo "
            "que no te convence. No resumas el plan: quien lo lea después debe "
            "poder trabajar solo con tu versión.")
    elif agent == "BALTHASAR":
        tarea = (
            "Examina el plan Y lo que ha señalado Melchior. Haz una crítica "
            "POPPERIANA: busca cómo podría FALLAR esto, qué supuesto lo haría "
            "falso, y qué comprobación concreta lo refutaría. Señala también "
            "dónde Melchior se equivoca. Ejecuta lo que puedas ejecutar: una "
            "objeción con evidencia vale más que una sospecha.")
    elif agent == "CASPER":
        tarea = (
            "Evalúa por separado: (a) el plan original, (b) el análisis y las "
            "mejoras de Melchior, (c) la crítica de Balthasar. Emite un "
            "pronunciamiento crítico sobre las tres cosas y AÑADE los temas "
            "nuevos que consideres pertinentes al plan y que nadie haya "
            "tratado. Devuelve el plan consolidado y listo para la siguiente "
            "vuelta.")
    else:
        raise ImprovementError(f"agente desconocido: {agent}")

    return f"{cabecera}\n\n{previo}\n\n=== TU TAREA ({agent}) ===\n{tarea}"
