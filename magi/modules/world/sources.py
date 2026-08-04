"""
Capa de fuentes del mundo real (Plan MAGI 9.0 §6.1).

POR QUÉ ASÍ
===========
Dos restricciones tuyas mandan sobre el diseño:

  · "no usaré mis keys ni keys para el sistema"
  · "solo usaremos ia de nube gratuita sin keys"

Eso descarta FRED con API key, Alpha Vantage, Polygon y casi todo lo que se
recomienda por defecto. Lo que queda, y que he comprobado que responde 200 sin
clave alguna, es esto:

    World Bank   api.worldbank.org/v2         JSON, sin clave, sin límite duro
    FRED CSV     fred.stlouisfed.org/graph    el CSV público NO pide clave
    ECB SDMX     data-api.ecb.europa.eu       CSV, sin clave
    SEC EDGAR    data.sec.gov/api/xbrl        sin clave; exige User-Agent con contacto

Stooq devuelve HTML de bloqueo con frecuencia, así que no se construye nada
encima: una fuente que falla en silencio es peor que una fuente que falta.

PROVENIENCIA, NO ADORNO
=======================
§6.1 pide que "cada afirmación sobre el presente salga con fuente y fecha, o
salga marcada como no verificada". Aquí eso no es un campo opcional: `Datum`
no se puede construir sin `source` y `as_of`. Un dato sin procedencia no
existe en este módulo.

Y se distinguen DOS fechas que casi todo el mundo confunde:

    as_of      — a qué momento se refiere el dato (el PIB de 2024)
    retrieved  — cuándo lo bajamos nosotros (hoy)

Confundirlas es cómo un sistema acaba diciendo "el paro es del 4,1 %" citando
una cifra de hace catorce meses con la fecha de descarga de ayer.

TESTS SIN RED
=============
Todo pasa por `Fetcher`, que es un protocolo. Los tests inyectan
`FrozenFetcher` con respuestas capturadas de las APIs reales, así que la suite
no depende de la red ni del humor de un servidor ajeno, y aun así ejercita el
parseo contra la forma exacta que devuelven de verdad.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from ...core.paths import cache_dir

logger = logging.getLogger(__name__)

USER_AGENT = "MAGI-System-IDE/9.0 (contacto en el repositorio)"

# §6.1: caducidad por TIPO de dato, no una TTL global. Un tipo de cambio y la
# composición de un gobierno no envejecen al mismo ritmo, y tratarlos igual
# significa o machacar la API o servir datos rancios.
TTL: dict[str, float] = {
    "cotizacion":   300,          # 5 min
    "tipo_cambio":  3600,         # 1 h
    "tipo_interes": 86400,        # 1 día
    "macro":        7 * 86400,    # 1 semana — el PIB no se revisa a diario
    "fundamental":  30 * 86400,   # 1 mes — las 10-K salen trimestralmente
    "institucion":  90 * 86400,   # 1 trimestre
    "noticia":      900,          # 15 min
}
DEFAULT_TTL = 3600.0


class SourceError(RuntimeError):
    """La fuente no respondió, o respondió algo que no es lo que dice ser."""


@dataclass(frozen=True)
class Datum:
    """
    Un valor con su procedencia. No hay constructor que permita omitirla.
    """
    value: Any
    source: str            # "World Bank", "SEC EDGAR", "FRED"
    as_of: str             # a qué fecha se refiere el dato (ISO)
    url: str
    unit: str = ""
    retrieved: str = ""    # cuándo lo bajamos nosotros (ISO)
    note: str = ""

    def __post_init__(self):
        if not self.source or not self.as_of:
            raise ValueError(
                "un Datum sin fuente o sin fecha no es un dato, es un rumor")
        if not self.retrieved:
            object.__setattr__(
                self, "retrieved",
                datetime.now(timezone.utc).date().isoformat())

    @property
    def staleness_days(self) -> int | None:
        """Cuántos días han pasado desde la fecha A LA QUE SE REFIERE el dato."""
        try:
            d = date.fromisoformat(self.as_of[:10])
        except ValueError:
            return None
        return (date.today() - d).days

    def cite(self) -> str:
        """Texto de cita para que el enjambre no pueda afirmar sin atribuir."""
        edad = self.staleness_days
        antiguedad = f", {edad} días de antigüedad" if edad and edad > 0 else ""
        u = f" {self.unit}" if self.unit else ""
        return (f"{self.value}{u} — {self.source}, dato de {self.as_of}"
                f"{antiguedad}. Fuente: {self.url}")


# ------------------------------------------------------------------ fetchers

class Fetcher(Protocol):
    """Lo mínimo que necesita este módulo de un cliente HTTP."""

    def get(self, url: str, kind: str = "macro") -> str: ...


class HttpFetcher:
    """Cliente real, con caché en disco y TTL por tipo de dato."""

    def __init__(self, root: Path | None = None, timeout: float = 30.0,
                 user_agent: str = USER_AGENT):
        self.root = root or (cache_dir() / "world")
        self.root.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.user_agent = user_agent

    def _slot(self, url: str) -> Path:
        import hashlib
        return self.root / f"{hashlib.sha256(url.encode()).hexdigest()[:24]}.json"

    def _cached(self, url: str, kind: str) -> str | None:
        slot = self._slot(url)
        if not slot.exists():
            return None
        try:
            blob = json.loads(slot.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        edad = time.time() - blob.get("ts", 0)
        if edad > TTL.get(kind, DEFAULT_TTL):
            return None
        return blob.get("body")

    def _store(self, url: str, body: str) -> None:
        try:
            self._slot(url).write_text(
                json.dumps({"ts": time.time(), "url": url, "body": body}),
                encoding="utf-8")
        except OSError as e:                       # pragma: no cover
            logger.debug("[world] no se pudo cachear %s: %s", url, e)

    def get(self, url: str, kind: str = "macro") -> str:
        hit = self._cached(url, kind)
        if hit is not None:
            logger.debug("[world] caché (%s) %s", kind, url)
            return hit
        try:
            import httpx
        except ImportError as e:                   # pragma: no cover
            raise SourceError("httpx no instalado") from e
        try:
            r = httpx.get(url, timeout=self.timeout, follow_redirects=True,
                          headers={"User-Agent": self.user_agent,
                                   "Accept-Encoding": "gzip, deflate"})
            r.raise_for_status()
        except Exception as e:
            raise SourceError(f"{url}: {e}") from e
        self._store(url, r.text)
        return r.text


@dataclass
class FrozenFetcher:
    """
    Fetcher de pruebas: respuestas fijas capturadas de las APIs reales.

    Existe para que la suite ejercite el PARSEO contra la forma exacta que
    devuelven las fuentes, sin depender de la red. Una URL no prevista es un
    error ruidoso y no un `None` silencioso — si un test pide algo que no
    preparé, quiero enterarme.
    """
    responses: dict[str, str] = field(default_factory=dict)
    calls: list[tuple[str, str]] = field(default_factory=list)

    def get(self, url: str, kind: str = "macro") -> str:
        self.calls.append((url, kind))
        for pattern, body in self.responses.items():
            if pattern in url:
                return body
        raise SourceError(f"FrozenFetcher no tiene respuesta para {url}")


_DEFAULT: Fetcher | None = None


def default_fetcher() -> Fetcher:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = HttpFetcher()
    return _DEFAULT


def set_default_fetcher(f: Fetcher | None) -> None:
    """Para tests y para inyectar un cliente distinto sin tocar los módulos."""
    global _DEFAULT
    _DEFAULT = f
