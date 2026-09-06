"""
Pruebas para el cliente KoboldCpp y la Vaina de Mielina de Lilim (megaplan v13).

Verifica:
1. ClienteKobold: resiliencia ante servidor apagado, llamadas mockeadas OpenAI-compatible y visión.
2. Mielina: pre-auditoría estática determinista, clasificación de intenciones en 0 ms y lubricación.
3. Fallback transparente: cuando KoboldCpp no está levantado, el sistema no bloquea ni crashea.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from magi.modules.lilim.cliente_kobold import ClienteKobold
from magi.modules.lilim.mielina import (
    clasificar_intencion_local,
    lubricar_arbitraje,
    lubricar_critica,
    lubricar_propuesta,
    lubricar_vision,
    pre_auditoria_estatica,
)


@pytest.mark.asyncio
async def test_cliente_kobold_offline_no_cuelga_ni_falla():
    """Con puerto inexistente o servidor apagado, devuelve False y None sin excepciones."""
    cli = ClienteKobold(url_base="http://127.0.0.1:59999")
    disponible = await cli.esta_disponible(timeout=0.1)
    assert not disponible

    res = await cli.generar("hola", timeout=0.1)
    assert res is None

    res_chat = await cli.chat([{"role": "user", "content": "hola"}], timeout=0.1)
    assert res_chat is None

    res_vision = await cli.vision("qué ves", b"fake_png", timeout=0.1)
    assert res_vision is None


@pytest.mark.asyncio
async def test_cliente_kobold_mock_exitoso(monkeypatch):
    """Simula respuesta estándar de KoboldCpp OpenAI /v1/chat/completions."""
    cli = ClienteKobold(url_base="http://127.0.0.1:5001")

    class MockResponse:
        def __init__(self, data: dict):
            self.data = json.dumps(data).encode("utf-8")

        def read(self):
            return self.data

        def decode(self, *a):
            return self.data.decode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

    def mock_urlopen(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "/api/extra/version" in url:
            return MockResponse({"version": "1.80", "arch": "oldcpu"})
        if "/v1/chat/completions" in url:
            return MockResponse({
                "choices": [{
                    "message": {"content": "class Parser:\n    def parse(self): pass"}
                }]
            })
        return MockResponse({})

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    assert await cli.esta_disponible()
    gen = await cli.generar("escribe un parser")
    assert gen is not None
    assert "class Parser" in gen

    vis = await cli.vision("analiza", b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
    assert vis is not None
    assert "class Parser" in vis


def test_pre_auditoria_estatica():
    """Detecta problemas sintácticos y estructurales obvios sin invocar modelos."""
    assert pre_auditoria_estatica("") == ["Código vacío o ausente"]

    codigo_pass = "def tarea_incompleta():\n    pass\n"
    defectos = pre_auditoria_estatica(codigo_pass)
    assert any("pass" in d for d in defectos)

    codigo_except = "try:\n    x = 1\nexcept:\n    x = 0\n"
    defectos_ex = pre_auditoria_estatica(codigo_except)
    assert any("except" in d for d in defectos_ex)

    codigo_sintaxis = "def rota(\n"
    defectos_sin = pre_auditoria_estatica(codigo_sintaxis)
    assert any("SyntaxError" in d for d in defectos_sin)

    codigo_sano = "def suma(a: int, b: int) -> int:\n    return a + b\n"
    assert pre_auditoria_estatica(codigo_sano) == []


def test_clasificar_intencion_local():
    """Enrutamiento determinista rápido."""
    assert clasificar_intencion_local("") == "vacio"
    assert clasificar_intencion_local("task.cancel") == "comando_directo"
    assert clasificar_intencion_local("/run tests") == "comando_directo"
    assert clasificar_intencion_local("controles de la ps_vita") == "memoria_epd"
    assert clasificar_intencion_local("desarrolla un emulador complejo de sh2") == "deliberacion_enjambre"


@pytest.mark.asyncio
async def test_mielina_offline_graceful():
    """Verifica que las funciones de la vaina de mielina degradan limpiamente si el motor local está apagado."""
    with patch("magi.modules.lilim.mielina.obtener_cliente") as mock_cli_fn:
        mock_cli = MagicMock()
        mock_cli.esta_disponible = AsyncMock(return_value=False)
        mock_cli_fn.return_value = mock_cli

        prop = await lubricar_propuesta("haz un juego")
        assert prop is None

        crit = await lubricar_critica("def x(): pass")
        assert any("pass" in c for c in crit)

        arb = await lubricar_arbitraje("encargo", "prop", ["obj1"])
        assert arb is None

        vis = await lubricar_vision(b"fake", "mira")
        assert vis.get("formato") == "bytes"
        assert "analisis_vlm" not in vis
