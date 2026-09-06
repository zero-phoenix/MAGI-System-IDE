"""
Búsqueda y lectura web sin navegador (Megaplan F1).

Invariantes de F1:
1. Sin navegador (sin Selenium, Playwright ni Chromium). HTTP estándar sobre HTML sin JS.
2. Presupuesto por ronda/tarea: cuota estricta de consultas web para evitar bucles o consumo infinito.
3. Cita obligatoria con URL y fecha: todo resultado y lectura viaja con URL y fecha de consulta.
4. Sin red o fallo de conexión -> 'SIN COMPROBAR', jamás inventado.
5. web_read: texto legible, límite de tamaño y máximo 1 redirección HTTP.
"""
from __future__ import annotations

import html
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

PRESUPUESTO_DEFECTO = 5
MAX_READ_CHARS_DEFECTO = 4000
MAX_BYTES_DESCARGA = 200_000
TIMEOUT_DEFECTO = 10.0
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MAGI-IDE/5.26 (compatible; Research/1.0)"

LISTA_NEGRA_DOMINIOS = {
    "chat.openai.com",
    "claude.ai",
    "gemini.google.com",
    "chatgpt.com",
}


@dataclass
class WebBudget:
    """Control de presupuesto de consultas web por tarea / ronda."""
    limite: int = PRESUPUESTO_DEFECTO
    _usos: dict[str, int] = field(default_factory=dict)

    def consumir(self, task_id: str = "default") -> tuple[bool, str]:
        tid = task_id or "default"
        actual = self._usos.get(tid, 0)
        if actual >= self.limite:
            return False, (
                f"PRESUPUESTO AGOTADO: se alcanzó el límite de {self.limite} consultas "
                f"web para la tarea '{tid}'. Negado por presupuesto de ronda."
            )
        self._usos[tid] = actual + 1
        return True, ""

    def uso(self, task_id: str = "default") -> int:
        return self._usos.get(task_id or "default", 0)

    def reiniciar(self, task_id: str = "default") -> None:
        if task_id in self._usos:
            del self._usos[task_id]


_GLOBAL_BUDGET = WebBudget()


def _fecha_hoy() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _extraer_dominio(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc.lower() or url.split("/")[0].lower()
    except Exception:
        return url.lower()


def _limpiar_html(html_raw: str) -> str:
    """Extrae texto legible de un fragmento o documento HTML."""
    if not html_raw:
        return ""
    s = re.sub(r"(?is)<script.*?>.*?</script>", " ", html_raw)
    s = re.sub(r"(?is)<style.*?>.*?</style>", " ", s)
    s = re.sub(r"(?is)<!--.*?-->", " ", s)
    s = re.sub(r"(?is)<header.*?>.*?</header>", " ", s)
    s = re.sub(r"(?is)<footer.*?>.*?</footer>", " ", s)
    s = re.sub(r"(?i)<(p|br|h[1-6]|li|tr|div)[^>]*>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    lineas = [re.sub(r"[ \t]+", " ", line).strip() for line in s.splitlines()]
    lineas = [line for line in lineas if line]
    return "\n".join(lineas)


def _parsear_resultados_ddg(html_content: str, limite: int = 5) -> list[dict[str, str]]:
    """Extrae títulos, URLs y extractos de la página de resultados HTML."""
    resultados: list[dict[str, str]] = []
    fecha = _fecha_hoy()

    bloques = re.findall(
        r'(<div class="result results_links[^"]*".*?</div>\s*</div>)',
        html_content,
        re.DOTALL,
    )
    if not bloques:
        bloques = re.findall(
            r'(<div class="[^"]*result[^"]*".*?</div>)', html_content, re.DOTALL
        )

    for b in bloques:
        if len(resultados) >= limite:
            break
        m_title = re.search(
            r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            b,
            re.DOTALL,
        )
        if m_title:
            url_raw = m_title.group(1)
            titulo = _limpiar_html(m_title.group(2))
        else:
            m_link = re.search(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', b, re.DOTALL)
            if not m_link:
                continue
            url_raw = m_link.group(1)
            titulo = _limpiar_html(m_link.group(2))

        if "uddg=" in url_raw:
            m_uddg = re.search(r"uddg=([^&]+)", url_raw)
            if m_uddg:
                url_raw = urllib.parse.unquote(m_uddg.group(1))

        m_snip = re.search(
            r'<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>',
            b,
            re.DOTALL,
        ) or re.search(
            r'<div[^>]+class="[^"]*snippet[^"]*"[^>]*>(.*?)</div>',
            b,
            re.DOTALL,
        )
        extracto = _limpiar_html(m_snip.group(1)) if m_snip else ""

        if url_raw.startswith(("http://", "https://")):
            resultados.append({
                "titulo": titulo,
                "url": url_raw,
                "extracto": extracto,
                "fecha": fecha,
            })

    return resultados


class _SingleRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Permite como máximo 1 redirección HTTP para web_read."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        count = getattr(req, "_magi_redirect_count", 0)
        if count >= 1:
            raise urllib.error.HTTPError(
                newurl,
                code,
                "Demasiadas redirecciones: superado el límite estricto de 1 redirección",
                headers,
                fp,
            )
        new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_req is not None:
            new_req._magi_redirect_count = count + 1
        return new_req


def web_search(
    consulta: str,
    limite: int = 5,
    task_id: str = "",
    budget: WebBudget | None = None,
    _fetcher: Callable[[str], str] | None = None,
) -> tuple[bool, str, list[dict[str, str]]]:
    """
    Búsqueda web sin navegador con presupuesto por ronda y cita obligatoria.

    Retorna: (ok, mensaje_o_contenido, lista_de_resultados)
    """
    if not isinstance(consulta, str) or not consulta.strip():
        return False, "Indica una consulta para buscar en la web.", []

    b = budget or _GLOBAL_BUDGET
    ok_presupuesto, msg_presupuesto = b.consumir(task_id)
    if not ok_presupuesto:
        return False, msg_presupuesto, []

    if os.environ.get("MAGI_OFFLINE") == "1":
        return (
            False,
            "SIN COMPROBAR: sin red o proveedor inaccesible (modo MAGI_OFFLINE activo).",
            [],
        )

    url_buscar = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(consulta.strip())}"
    fecha = _fecha_hoy()

    try:
        if _fetcher is not None:
            html_content = _fetcher(url_buscar)
        else:
            req = urllib.request.Request(
                url_buscar,
                headers={"User-Agent": USER_AGENT, "Accept-Language": "es,en;q=0.8"},
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT_DEFECTO) as resp:
                raw_bytes = resp.read(MAX_BYTES_DESCARGA)
                html_content = raw_bytes.decode("utf-8", errors="replace")

        resultados = _parsear_resultados_ddg(html_content, limite=max(1, limite))
        if not resultados:
            return (
                True,
                f"No se encontraron resultados web para: '{consulta}'. (Fecha de consulta: {fecha})",
                [],
            )

        lineas = [f"Resultados de búsqueda web para '{consulta}' [Fecha: {fecha}]:"]
        for i, r in enumerate(resultados, 1):
            lineas.append(f"{i}. {r['titulo']}")
            lineas.append(f"   URL: {r['url']}")
            lineas.append(f"   Fecha: {r['fecha']}")
            if r["extracto"]:
                lineas.append(f"   Extracto: {r['extracto']}")

        return True, "\n".join(lineas), resultados

    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
        logger.warning(f"Error de red en web_search: {e}")
        return False, f"SIN COMPROBAR: sin red o proveedor inaccesible: {e}", []
    except Exception as e:
        logger.exception(f"Fallo inesperado en web_search: {e}")
        return False, f"SIN COMPROBAR: fallo durante la búsqueda web: {e}", []


def web_read(
    url: str,
    max_chars: int = MAX_READ_CHARS_DEFECTO,
    task_id: str = "",
    budget: WebBudget | None = None,
    _fetcher: Callable[[str], tuple[int, str, str]] | None = None,
) -> tuple[bool, str, dict[str, Any]]:
    """
    Lectura web sin navegador: extrae texto legible con límite de tamaño y máx 1 redirección.

    Retorna: (ok, texto_con_cita, metadatos)
    """
    if not isinstance(url, str) or not url.strip():
        return False, "Indica la URL web a leer.", {}

    url_n = url.strip()
    if not url_n.startswith(("http://", "https://")):
        return False, f"URL no válida (debe empezar por http:// o https://): {url_n}", {}

    dominio = _extraer_dominio(url_n)
    if dominio in LISTA_NEGRA_DOMINIOS:
        return (
            False,
            f"BLOQUEADO POR POLÍTICA: el dominio '{dominio}' está prohibido en navegación automatizada.",
            {},
        )

    b = budget or _GLOBAL_BUDGET
    ok_presupuesto, msg_presupuesto = b.consumir(task_id)
    if not ok_presupuesto:
        return False, msg_presupuesto, {}

    if os.environ.get("MAGI_OFFLINE") == "1":
        return (
            False,
            "SIN COMPROBAR: sin red o proveedor inaccesible (modo MAGI_OFFLINE activo).",
            {},
        )

    fecha = _fecha_hoy()

    try:
        if _fetcher is not None:
            status, final_url, html_content = _fetcher(url_n)
        else:
            opener = urllib.request.build_opener(_SingleRedirectHandler())
            req = urllib.request.Request(
                url_n,
                headers={"User-Agent": USER_AGENT, "Accept-Language": "es,en;q=0.8"},
            )
            with opener.open(req, timeout=TIMEOUT_DEFECTO) as resp:
                status = getattr(resp, "status", 200)
                final_url = resp.geturl()
                raw_bytes = resp.read(MAX_BYTES_DESCARGA)
                html_content = raw_bytes.decode("utf-8", errors="replace")

        texto_limpio = _limpiar_html(html_content)
        if len(texto_limpio) > max_chars:
            texto_limpio = (
                texto_limpio[:max_chars]
                + f"\n\n… [recortado a {max_chars} caracteres por límite de lectura] …"
            )

        cuerpo = (
            f"Contenido web de {final_url}\n"
            f"Cita obligatoria: URL={final_url} · Fecha={fecha}\n\n"
            f"{texto_limpio}"
        )

        return True, cuerpo, {
            "url_origen": url_n,
            "final_url": final_url,
            "fecha": fecha,
            "http_status": status,
            "longitud": len(texto_limpio),
        }

    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
        logger.warning(f"Error al leer URL '{url_n}': {e}")
        return False, f"SIN COMPROBAR: no se pudo leer {url_n}: {e}", {}
    except Exception as e:
        logger.exception(f"Fallo inesperado al leer '{url_n}': {e}")
        return False, f"SIN COMPROBAR: error al procesar {url_n}: {e}", {}
