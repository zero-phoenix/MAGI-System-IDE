"""
Registro de tesis con calibración medible (Plan MAGI 9.0 §6.3).

POR QUÉ ESTA ES LA PIEZA QUE IMPORTA
====================================
De todo lo que pediste bajo "las habilidades de Warren Buffett", esto es lo
único que de verdad se le parece, y es la parte que casi nadie construye
porque no luce: llevar cuenta de tus errores.

Un sistema que predice no vale nada si nadie comprueba después si acertó. Y la
comprobación tiene que ser automática y molesta, porque la memoria humana
reescribe las tesis fallidas hasta que parecen aciertos con mala suerte. Aquí
la tesis se congela con su fecha, su razonamiento, sus fuentes y —sobre todo—
su CONFIANZA DECLARADA, y luego se puntúa contra lo que pasó.

CALIBRACIÓN, NO ACIERTO
=======================
Acertar mucho es fácil: predice solo lo obvio. Lo que mide de verdad el
criterio es la CALIBRACIÓN: que cuando dices 70 % aciertes el 70 % de las
veces. Alguien calibrado al 55 % es más útil que alguien que acierta el 80 %
pero dice 99 % siempre, porque del primero te puedes fiar para dimensionar una
apuesta y del segundo no.

La puntuación de Brier mide exactamente eso, y tiene la propiedad de ser una
regla de puntuación PROPIA: se minimiza diciendo la probabilidad que de verdad
crees. No se puede jugar declarando más o menos confianza de la que tienes.

    Brier = media( (confianza − resultado)² )     resultado ∈ {0, 1}

    0.00  perfecto
    0.25  lo mismo que decir 50 % a todo — línea base de no saber nada
    1.00  máxima seguridad, siempre equivocado

Y se compara siempre contra la línea base, porque un Brier de 0,20 suena bien
y es peor que la moneda si la tasa de acierto del dominio ya era del 90 %.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ...core.paths import db_path

logger = logging.getLogger(__name__)


class ThesisError(ValueError):
    pass


@dataclass
class Thesis:
    """Una afirmación falsable con fecha de caducidad."""
    thesis_id: str
    subject: str                 # "AAPL", "tipos BCE", "elecciones DE"
    claim: str                   # afirmación concreta y comprobable
    confidence: float            # 0..1 — probabilidad declarada
    reasoning: str
    horizon: str                 # fecha ISO en la que se resuelve
    created_at: str
    sources: list[str] = field(default_factory=list)
    resolved: bool = False
    outcome: int | None = None   # 1 acertó, 0 falló
    resolved_at: str | None = None
    resolution_note: str = ""

    @property
    def brier(self) -> float | None:
        if self.outcome is None:
            return None
        return (self.confidence - self.outcome) ** 2

    @property
    def overdue(self) -> bool:
        """Vencida y sin puntuar: la deuda que hace inútil todo el registro."""
        if self.resolved:
            return False
        try:
            return date.fromisoformat(self.horizon[:10]) < date.today()
        except ValueError:
            return False

    def to_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        d["brier"] = self.brier
        d["overdue"] = self.overdue
        return d


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


class ThesisLog:
    """
    Registro persistente de tesis. SQLite, misma base que el resto del sistema.
    """

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
                CREATE TABLE IF NOT EXISTS thesis_log (
                    thesis_id       TEXT PRIMARY KEY,
                    subject         TEXT NOT NULL,
                    claim           TEXT NOT NULL,
                    confidence      REAL NOT NULL,
                    reasoning       TEXT NOT NULL DEFAULT '',
                    horizon         TEXT NOT NULL,
                    created_at      TEXT NOT NULL,
                    sources         TEXT NOT NULL DEFAULT '[]',
                    resolved        INTEGER NOT NULL DEFAULT 0,
                    outcome         INTEGER,
                    resolved_at     TEXT,
                    resolution_note TEXT NOT NULL DEFAULT '',
                    ts              REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_thesis_pendiente
                    ON thesis_log(resolved, horizon);
                CREATE INDEX IF NOT EXISTS idx_thesis_subject
                    ON thesis_log(subject, created_at DESC);
            """)

    # ------------------------------------------------------------- escritura

    def record(self, subject: str, claim: str, confidence: float,
               reasoning: str = "", horizon_days: int = 180,
               sources: list[str] | None = None) -> Thesis:
        """
        Congela una tesis. La confianza al 0 % o al 100 % se rechaza.

        No es pedantería estadística: un 100 % declarado hace infinita la
        penalización logarítmica y, más importante, es casi siempre falso.
        Quien dice 100 % no está midiendo su confianza, está enfatizando.
        """
        if not 0.0 < confidence < 1.0:
            raise ThesisError(
                f"confianza {confidence}: debe estar estrictamente entre 0 y 1. "
                f"El 0 % y el 100 % no son grados de creencia, son retórica — y "
                f"hacen que la calibración deje de poder medirse")
        if not claim.strip():
            raise ThesisError("una tesis sin afirmación no se puede puntuar")
        if horizon_days < 1:
            raise ThesisError("el horizonte debe ser futuro; si no, no es una "
                              "predicción, es una observación")

        t = Thesis(
            thesis_id=f"th_{uuid.uuid4().hex[:12]}", subject=subject.strip(),
            claim=claim.strip(), confidence=float(confidence),
            reasoning=reasoning.strip(),
            horizon=(date.today() + timedelta(days=horizon_days)).isoformat(),
            created_at=_today(), sources=list(sources or []))
        with self._conn() as c:
            c.execute(
                "INSERT INTO thesis_log (thesis_id, subject, claim, confidence,"
                " reasoning, horizon, created_at, sources, ts)"
                " VALUES (?,?,?,?,?,?,?,?,?)",
                (t.thesis_id, t.subject, t.claim, t.confidence, t.reasoning,
                 t.horizon, t.created_at, json.dumps(t.sources, ensure_ascii=False),
                 time.time()))
        logger.info("[tesis] registrada %s (%s, %.0f%%)",
                    t.thesis_id, t.subject, t.confidence * 100)
        return t

    def resolve(self, thesis_id: str, outcome: bool, note: str = "") -> Thesis:
        """Puntúa una tesis. Una vez resuelta no se puede reescribir."""
        t = self.get(thesis_id)
        if t is None:
            raise ThesisError(f"no existe la tesis {thesis_id}")
        if t.resolved:
            raise ThesisError(
                f"{thesis_id} ya se resolvió el {t.resolved_at} como "
                f"{'acierto' if t.outcome else 'fallo'}. Reescribir un "
                f"resultado pasado vacía de sentido el registro entero")
        with self._conn() as c:
            c.execute("UPDATE thesis_log SET resolved=1, outcome=?, "
                      "resolved_at=?, resolution_note=? WHERE thesis_id=?",
                      (int(outcome), _today(), note.strip(), thesis_id))
        t.resolved, t.outcome = True, int(outcome)
        t.resolved_at, t.resolution_note = _today(), note.strip()
        return t

    # -------------------------------------------------------------- lectura

    @staticmethod
    def _row(r: sqlite3.Row) -> Thesis:
        return Thesis(
            thesis_id=r["thesis_id"], subject=r["subject"], claim=r["claim"],
            confidence=r["confidence"], reasoning=r["reasoning"],
            horizon=r["horizon"], created_at=r["created_at"],
            sources=json.loads(r["sources"] or "[]"),
            resolved=bool(r["resolved"]), outcome=r["outcome"],
            resolved_at=r["resolved_at"], resolution_note=r["resolution_note"])

    def get(self, thesis_id: str) -> Thesis | None:
        with self._conn() as c:
            r = c.execute("SELECT * FROM thesis_log WHERE thesis_id=?",
                          (thesis_id,)).fetchone()
        return self._row(r) if r else None

    def all(self, subject: str | None = None) -> list[Thesis]:
        q = "SELECT * FROM thesis_log"
        args: tuple = ()
        if subject:
            q += " WHERE subject=?"
            args = (subject,)
        q += " ORDER BY created_at DESC"
        with self._conn() as c:
            return [self._row(r) for r in c.execute(q, args)]

    def pending(self) -> list[Thesis]:
        return [t for t in self.all() if not t.resolved]

    def due(self) -> list[Thesis]:
        """Vencidas y sin puntuar. Lo que hay que resolver para no engañarse."""
        return [t for t in self.pending() if t.overdue]

    # ---------------------------------------------------------- calibración

    def brier_score(self, subject: str | None = None) -> dict[str, Any]:
        """
        Brier, línea base y descomposición en resolución y calibración.

        La línea base es la que da decir siempre la tasa base observada. Si tu
        Brier no la mejora, tus predicciones no aportan nada sobre contar la
        frecuencia histórica — un resultado incómodo y frecuente.
        """
        resueltas = [t for t in self.all(subject) if t.resolved]
        n = len(resueltas)
        if n == 0:
            return {"n": 0, "mensaje": "no hay tesis resueltas todavía: sin "
                                       "resolver, el registro no mide nada"}

        brier = sum(t.brier for t in resueltas) / n          # type: ignore[misc]
        tasa_base = sum(t.outcome for t in resueltas) / n    # type: ignore[misc]
        base = tasa_base * (1 - tasa_base)                   # Brier de decir siempre la tasa base
        confianza_media = sum(t.confidence for t in resueltas) / n

        return {
            "n": n,
            "brier": round(brier, 4),
            "brier_linea_base": round(base, 4),
            "mejora_sobre_base": round(base - brier, 4),
            "tasa_acierto": round(tasa_base, 4),
            "confianza_media": round(confianza_media, 4),
            "sesgo": round(confianza_media - tasa_base, 4),
            "veredicto": self._veredicto(brier, base, confianza_media - tasa_base, n),
        }

    @staticmethod
    def _veredicto(brier: float, base: float, sesgo: float, n: int) -> str:
        if n < 10:
            return (f"solo {n} tesis resueltas: no hay muestra para hablar de "
                    f"calibración. Hacen falta ~30 para que el número signifique algo")
        partes = []
        partes.append("aporta sobre la tasa base" if brier < base
                      else "NO aporta sobre decir siempre la tasa base")
        if sesgo > 0.10:
            partes.append(f"exceso de confianza de {sesgo:+.0%}: dices más "
                          f"seguridad de la que aciertas")
        elif sesgo < -0.10:
            partes.append(f"defecto de confianza de {sesgo:+.0%}: aciertas más "
                          f"de lo que te atreves a declarar")
        else:
            partes.append("bien calibrado")
        return "; ".join(partes)

    def calibration_curve(self, buckets: int = 5,
                          subject: str | None = None) -> str:
        """
        Curva de calibración: confianza declarada frente a acierto real.

        Es el diagnóstico que el Brier resume en un número y por tanto esconde:
        se puede tener buen Brier global y estar mal calibrado en los extremos,
        que es justo donde se toman las decisiones grandes.
        """
        resueltas = [t for t in self.all(subject) if t.resolved]
        if not resueltas:
            return ("Sin tesis resueltas. El registro solo empieza a valer "
                    "cuando se puntúan las predicciones vencidas.")

        cestas: list[list[Thesis]] = [[] for _ in range(buckets)]
        for t in resueltas:
            i = min(int(t.confidence * buckets), buckets - 1)
            cestas[i].append(t)

        out = [f"CALIBRACIÓN — {len(resueltas)} tesis resueltas"
               + (f" · {subject}" if subject else ""), "",
               f"{'confianza declarada':<22s}{'n':>4s}{'acierto real':>15s}"
               f"{'desvío':>10s}", "-" * 51]
        for i, cesta in enumerate(cestas):
            lo, hi = i / buckets, (i + 1) / buckets
            etiqueta = f"{lo:.0%}–{hi:.0%}"
            if not cesta:
                out.append(f"{etiqueta:<22s}{0:>4d}{'—':>15s}{'—':>10s}")
                continue
            real = sum(t.outcome for t in cesta) / len(cesta)   # type: ignore[misc]
            declarada = sum(t.confidence for t in cesta) / len(cesta)
            out.append(f"{etiqueta:<22s}{len(cesta):>4d}{real:>14.0%} "
                       f"{real - declarada:>+9.0%}")

        s = self.brier_score(subject)
        out += ["", f"Brier {s['brier']} frente a línea base {s['brier_linea_base']} "
                f"({'mejor' if s['mejora_sobre_base'] > 0 else 'peor'}). "
                f"{s['veredicto']}.",
                "",
                "Desvío positivo = aciertas más de lo que declaras. Negativo = "
                "exceso de confianza, que es el sesgo por defecto de casi todo "
                "el mundo y de casi todos los modelos."]

        vencidas = self.due()
        if vencidas:
            out.append("")
            out.append(f"AVISO: {len(vencidas)} tesis vencidas SIN puntuar. "
                       f"Un registro con vencidas sin resolver se sesga solo, "
                       f"porque las que se recuerdan resolver son las que se "
                       f"acertaron.")
        return "\n".join(out)

    def render_pending(self, limit: int = 20) -> str:
        pend = sorted(self.pending(), key=lambda t: t.horizon)[:limit]
        if not pend:
            return "No hay tesis abiertas."
        out = ["TESIS ABIERTAS", ""]
        for t in pend:
            marca = " ← VENCIDA, hay que puntuarla" if t.overdue else ""
            out.append(f"  {t.thesis_id}  {t.subject:<14s} {t.confidence:>4.0%}  "
                       f"vence {t.horizon}{marca}")
            out.append(f"      {t.claim[:100]}")
        return "\n".join(out)
