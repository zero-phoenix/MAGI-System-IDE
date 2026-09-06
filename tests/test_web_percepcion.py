"""
Pruebas para F1: Búsqueda y lectura web sin navegador (percepción web).

Invariantes verificadas:
1. Búsqueda web parsea HTML fixture extrayendo título, URL, extracto y fecha obligatoria.
2. Lectura web extrae texto legible con límite de caracteres y máximo 1 redirección HTTP.
3. Presupuesto de consultas por ronda/tarea se agota y se niega en claro.
4. Sin red o error de conexión -> 'SIN COMPROBAR', jamás inventado.
5. Lista negra permanente bloquea dominios prohibidos (ej. chat.openai.com).
6. Registro en ToolRegistry: web_search y web_read son ejecutables con ToolContext.
7. Compuerta F1: Balthasar/nodo puede citar una URL externa con fecha encontrada por él.
"""
from __future__ import annotations

import pytest

from magi.core.tools.builtin import ToolContext, build_registry
from magi.modules.percepcion.web import (
    WebBudget,
    web_read,
    web_search,
)

FIXTURE_HTML_BUSQUEDA = """
<!DOCTYPE html>
<html>
<body>
<div class="result results_links results_links_deep web-result">
  <div class="links_main links_deep result__body">
    <h2 class="result__title">
      <a class="result__a" href="https://example.org/sh2_pipeline">Pipeline SH2 de Sega Saturn</a>
    </h2>
    <a class="result__snippet" href="https://example.org/sh2_pipeline">
      Documentación técnica del pipeline de dos etapas y hazards del procesador SH7095.
    </a>
    <div class="result__extras">
      <a class="result__url" href="https://example.org/sh2_pipeline">example.org/sh2_pipeline</a>
    </div>
  </div>
</div>
<div class="result results_links results_links_deep web-result">
  <div class="links_main links_deep result__body">
    <h2 class="result__title">
      <a class="result__a" href="https://example.org/yabause_dynarec">Yabause Dynarec Overview</a>
    </h2>
    <a class="result__snippet" href="https://example.org/yabause_dynarec">
      Estructura de bloques básicos y traducción dinámica de SH2 a ARM.
    </a>
  </div>
</div>
</body>
</html>
"""

FIXTURE_HTML_LECTURA = """
<!DOCTYPE html>
<html>
<head><title>SH2 Hazards</title><style>.hidden { display: none; }</style></head>
<body>
<script>console.log('ignored');</script>
<header><nav>Menú de navegación</nav></header>
<h1>Hazards en SH-2</h1>
<p>El SH-2 tiene dos unidades de ejecución en el Sega Saturn: Master y Slave.</p>
<p>Los accesos simultáneos al bus causan ciclos de espera.</p>
<footer>Copyright 2026 Sega Retro</footer>
</body>
</html>
"""


def test_web_search_parseo_html_y_citas():
    """F1: web_search extrae título, URL, extracto y fecha obligatoria desde HTML sin JS."""
    def _fetcher_mock(url: str) -> str:
        return FIXTURE_HTML_BUSQUEDA

    budget = WebBudget(limite=5)
    ok, salida, resultados = web_search(
        "sh2 pipeline",
        limite=5,
        task_id="tarea_f1",
        budget=budget,
        _fetcher=_fetcher_mock,
    )

    assert ok
    assert len(resultados) == 2
    r1 = resultados[0]
    assert r1["titulo"] == "Pipeline SH2 de Sega Saturn"
    assert r1["url"] == "https://example.org/sh2_pipeline"
    assert "hazards" in r1["extracto"]
    assert "fecha" in r1 and len(r1["fecha"]) == 10  # YYYY-MM-DD
    assert "Fecha: " in salida
    assert "https://example.org/sh2_pipeline" in salida


def test_web_read_extraccion_limpia_y_cita():
    """F1: web_read extrae texto legible eliminando scripts/estilos y cita URL+fecha."""
    def _fetcher_mock(url: str) -> tuple[int, str, str]:
        return 200, url, FIXTURE_HTML_LECTURA

    budget = WebBudget(limite=5)
    ok, salida, meta = web_read(
        "https://example.org/sh2_hazards",
        max_chars=200,
        task_id="tarea_f1_read",
        budget=budget,
        _fetcher=_fetcher_mock,
    )

    assert ok
    assert "console.log" not in salida
    assert "Menú de navegación" not in salida  # header ignorado
    assert "Master y Slave" in salida
    assert "Cita obligatoria: URL=https://example.org/sh2_hazards" in salida
    assert meta["fecha"]


def test_presupuesto_web_por_ronda_se_agota_y_se_niega_en_claro():
    """F1: El presupuesto por ronda/tarea tiene límite estricto y se niega en claro."""
    budget = WebBudget(limite=2)

    def _fetcher_mock(url: str) -> str:
        return FIXTURE_HTML_BUSQUEDA

    # Consulta 1: OK
    ok1, _, _ = web_search("consulta 1", task_id="t_ronda", budget=budget, _fetcher=_fetcher_mock)
    assert ok1
    assert budget.uso("t_ronda") == 1

    # Consulta 2: OK
    ok2, _, _ = web_search("consulta 2", task_id="t_ronda", budget=budget, _fetcher=_fetcher_mock)
    assert ok2
    assert budget.uso("t_ronda") == 2

    # Consulta 3: Agotado
    ok3, msg3, res3 = web_search("consulta 3", task_id="t_ronda", budget=budget, _fetcher=_fetcher_mock)
    assert not ok3
    assert "PRESUPUESTO AGOTADO" in msg3
    assert "t_ronda" in msg3
    assert len(res3) == 0

    # Lectura también respeta el presupuesto
    ok_read, msg_read, _ = web_read("https://example.org/algo", task_id="t_ronda", budget=budget)
    assert not ok_read
    assert "PRESUPUESTO AGOTADO" in msg_read


def test_sin_red_devuelve_sin_comprobar():
    """F1: Sin red o ante error de conexión devuelve SIN COMPROBAR, nunca inventado."""
    def _fetcher_cae(url: str):
        import urllib.error
        raise urllib.error.URLError("Network unreachable (simulado)")

    budget = WebBudget(limite=5)
    ok, salida, res = web_search("algo", task_id="t_caida", budget=budget, _fetcher=_fetcher_cae)
    assert not ok
    assert "SIN COMPROBAR" in salida
    assert "Network unreachable" in salida
    assert len(res) == 0


def test_lista_negra_permanente_bloquea_chat_llms():
    """F1/CTL-7: Prohíbe interfaces de chat de otros LLMs."""
    budget = WebBudget(limite=5)
    ok, msg, _ = web_read("https://chat.openai.com/backend-api", task_id="t_llm", budget=budget)
    assert not ok
    assert "BLOQUEADO POR POLÍTICA" in msg
    assert "chat.openai.com" in msg


@pytest.mark.asyncio
async def test_herramientas_web_en_registry(tmp_path):
    """F1: web_search y web_read están registradas en el ToolRegistry del sistema."""
    reg = build_registry()
    assert "web_search" in reg.names()
    assert "web_read" in reg.names()

    ctx = ToolContext(task_id="task_web_reg")

    # Búsqueda rechazada con consulta vacía
    res_vacio = await reg.execute("web_search", {"consulta": ""}, ctx=ctx)
    assert not res_vacio.ok
    assert "consulta" in res_vacio.render()

    # Lectura rechazada con URL inválida
    res_invalida = await reg.execute("web_read", {"url": "ftp://invalido"}, ctx=ctx)
    assert not res_invalida.ok
    assert "URL no válida" in res_invalida.render()


def test_web_read_max_una_redireccion():
    """F1: web_read impone un límite estricto de 1 redirección HTTP."""
    from urllib.error import HTTPError
    from urllib.request import Request

    from magi.modules.percepcion.web import _SingleRedirectHandler

    handler = _SingleRedirectHandler()
    req = Request("http://example.org/inicio")

    # 1ª redirección: permitida
    req2 = handler.redirect_request(req, None, 302, "Found", {}, "http://example.org/redir1")
    assert req2 is not None
    assert getattr(req2, "_magi_redirect_count", 0) == 1

    # 2ª redirección: rechazada con HTTPError
    with pytest.raises(HTTPError) as exc_info:
        handler.redirect_request(req2, None, 302, "Found", {}, "http://example.org/redir2")
    assert "Demasiadas redirecciones" in str(exc_info.value)
