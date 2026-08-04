"""
Ingesta de RSS/Atom (Plan MAGI 9.0 §6.1).

Actualidad desde las fuentes que publican en abierto: bancos centrales,
boletines oficiales y agencias. Sin clave y sin scraping — un feed es un
contrato publicado, y por tanto no se rompe cada vez que alguien rediseña una
página.

DOS FORMATOS, UNA SALIDA
========================
RSS 2.0 y Atom describen lo mismo con etiquetas distintas (`item` frente a
`entry`, `pubDate` frente a `updated`, y en Atom el enlace vive en un atributo
y no en el texto). Se normalizan aquí para que nada aguas arriba tenga que
saber cuál era.

Se parsea con `xml.etree` y no con expresiones regulares. Un feed real trae
CDATA, entidades HTML y namespaces; el regex funciona con los tres primeros
que pruebas y falla en silencio con el cuarto.
"""
from __future__ import annotations

import html
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from .sources import Fetcher, SourceError, default_fetcher

logger = logging.getLogger(__name__)

# Fuentes oficiales, en abierto, sin clave. Datos y comunicados, no opinión.
FEEDS: dict[str, tuple[str, str]] = {
    "bce":           ("https://www.ecb.europa.eu/rss/press.html",
                      "Banco Central Europeo — notas de prensa"),
    "fed":           ("https://www.federalreserve.gov/feeds/press_all.xml",
                      "Reserva Federal — comunicados"),
    "fed_monetaria": ("https://www.federalreserve.gov/feeds/press_monetary.xml",
                      "Reserva Federal — política monetaria"),
    "sec":           ("https://www.sec.gov/news/pressreleases.rss",
                      "SEC — notas de prensa"),
    "boe":           ("https://www.boe.es/rss/canal.php?c=ultimas",
                      "Boletín Oficial del Estado (España)"),
    "un":            ("https://news.un.org/feed/subscribe/en/news/all/rss.xml",
                      "Naciones Unidas — noticias"),
    "eurostat":      ("https://ec.europa.eu/eurostat/api/dissemination/rss/en/euroindicators.rss",
                      "Eurostat — indicadores europeos"),
}

_TAG = re.compile(r"\{[^}]+\}")          # quita el namespace: {http://...}entry


def _local(tag: str) -> str:
    return _TAG.sub("", tag)


def _text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    return html.unescape("".join(el.itertext())).strip()


def _parse_date(raw: str) -> str:
    """Normaliza a ISO. RSS usa RFC-822 y Atom ISO-8601; los dos aparecen."""
    raw = raw.strip()
    if not raw:
        return ""
    try:
        return parsedate_to_datetime(raw).astimezone(timezone.utc).date().isoformat()
    except (TypeError, ValueError, IndexError):
        pass
    try:
        return datetime.fromisoformat(
            raw.replace("Z", "+00:00")).astimezone(timezone.utc).date().isoformat()
    except ValueError:
        return raw[:10]


@dataclass(frozen=True)
class Item:
    title: str
    link: str
    published: str
    summary: str
    feed: str

    def render(self) -> str:
        fecha = self.published or "sin fecha"
        return f"[{fecha}] {self.title}\n    {self.link}"


def parse_feed(xml_text: str, feed_name: str = "") -> list[Item]:
    """Parsea RSS 2.0 o Atom indistintamente."""
    try:
        root = ET.fromstring(xml_text.strip())
    except ET.ParseError as e:
        raise SourceError(f"el feed no es XML válido: {e}") from e

    nodos = [e for e in root.iter() if _local(e.tag) in ("item", "entry")]
    if not nodos:
        raise SourceError(
            "XML sin <item> ni <entry>: no es un feed RSS ni Atom "
            "(¿una página de error servida con 200?)")

    salida: list[Item] = []
    for n in nodos:
        campos: dict[str, ET.Element] = {}
        enlace = ""
        for hijo in n:
            nombre = _local(hijo.tag)
            campos.setdefault(nombre, hijo)
            # Atom: <link href="..."/>, y rel="alternate" es el enlace bueno.
            if nombre == "link" and hijo.get("href") and not enlace:
                if hijo.get("rel", "alternate") == "alternate":
                    enlace = hijo.get("href", "")

        titulo = _text(campos.get("title"))
        if not enlace:
            enlace = _text(campos.get("link")) or _text(campos.get("id"))
        fecha = _parse_date(_text(campos.get("pubDate"))
                            or _text(campos.get("updated"))
                            or _text(campos.get("published"))
                            or _text(campos.get("date")))
        resumen = (_text(campos.get("description"))
                   or _text(campos.get("summary"))
                   or _text(campos.get("content")))
        resumen = re.sub(r"<[^>]+>", " ", resumen)
        resumen = re.sub(r"\s+", " ", resumen).strip()

        if titulo or enlace:
            salida.append(Item(titulo, enlace, fecha, resumen[:400], feed_name))
    return salida


def fetch_feed(name_or_url: str, *, fetcher: Fetcher | None = None,
               limit: int = 15) -> list[Item]:
    """Descarga y parsea un feed del catálogo, o una URL cualquiera."""
    if name_or_url in FEEDS:
        url, etiqueta = FEEDS[name_or_url]
    elif name_or_url.startswith("http"):
        url, etiqueta = name_or_url, name_or_url
    else:
        raise SourceError(
            f"feed desconocido: '{name_or_url}'. Del catálogo: "
            f"{', '.join(sorted(FEEDS))} — o pasa una URL completa")
    cuerpo = (fetcher or default_fetcher()).get(url, "noticia")
    return parse_feed(cuerpo, etiqueta)[:limit]


def headlines(feeds: list[str] | None = None, *, fetcher: Fetcher | None = None,
              per_feed: int = 5) -> str:
    """
    Titulares con fuente y fecha. Un feed caído se marca; no tumba el resto.
    """
    feeds = feeds or ["fed_monetaria", "bce", "sec"]
    out = ["ACTUALIDAD — fuentes oficiales, con fecha y enlace", ""]
    for f in feeds:
        etiqueta = FEEDS.get(f, (f, f))[1]
        out.append(f"── {etiqueta}")
        try:
            for it in fetch_feed(f, fetcher=fetcher, limit=per_feed):
                out.append("  " + it.render().replace("\n", "\n  "))
        except SourceError as e:
            out.append(f"  NO DISPONIBLE — {e}")
        out.append("")
    out.append("Son comunicados oficiales, no análisis. Que una nota de prensa "
               "diga algo no lo convierte en cierto ni en relevante: es el dato "
               "de que se dijo, con su fecha.")
    return "\n".join(out)
