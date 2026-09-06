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


# ---------------------------------------------------- LO QUE DE VERDAD LLEGA

#: Una propuesta de Melchior tal cual sale: prosa con bloque cercado. NUNCA
#: llega código desnudo, que es lo único que la primera versión sabía leer.
PROPUESTA_REAL = """Voy a cachear los planos que no cambian entre fotogramas.

```python
def compone(plano):
    pass
```

Predicción: composite baja >= 20 %."""

#: El emulador entero es C. Esto es lo que llega en una ronda de YabauseVita.
PROPUESTA_C = """Reduzco el trabajo del SH2 esclavo en espera pasiva.

```c
static void sh2_step(SH2_struct *ctx) {
    u32 op = fetch(ctx->pc);
    ctx->pc += 2;
    dispatch(ctx, op);
}
```"""


def test_no_inventa_un_syntaxerror_en_cada_propuesta_real():
    """
    EL FALLO QUE ESTO CIERRA, medido antes de arreglarlo:

        propuesta real (prosa + cerca) -> "SyntaxError en línea 1"
        código C (el emulador entero)  -> "SyntaxError en línea 1"

    `pre_auditoria_estatica` pasaba el texto ENTERO a `ast.parse`, así que
    fabricaba un defecto inexistente en cada propuesta que no fuera Python
    desnudo — es decir, en todas. Balthasar recibía esa objeción y gastaba
    su turno defendiéndola.

    Una objeción fabricada es peor que el silencio.
    """
    defectos = pre_auditoria_estatica(PROPUESTA_REAL)
    assert not any("SyntaxError" in d for d in defectos), (
        f"sigue inventando un error de sintaxis sobre prosa: {defectos}")
    # Y sí ve el defecto REAL que hay dentro del bloque de Python.
    assert any("pass" in d for d in defectos), (
        f"se saltó el defecto de verdad al filtrar: {defectos}")


def test_sobre_codigo_c_calla_en_vez_de_mentir():
    """C no es Python roto: es otro lenguaje. El `ast` de Python no opina."""
    assert pre_auditoria_estatica(PROPUESTA_C) == []
    c_desnudo = ("static void paso(SH2 *ctx) {\n"
                 "    ctx->pc += 2;\n"
                 "}\n")
    assert pre_auditoria_estatica(c_desnudo) == []
    assert pre_auditoria_estatica("#include <stdio.h>\nint main(){return 0;}") == []


def test_sigue_viendo_python_roto_sin_cercas():
    """Callar ante C no puede volverse callar ante todo."""
    assert any("SyntaxError" in d for d in pre_auditoria_estatica("def rota(\n"))


def test_el_docstring_no_disfraza_una_funcion_vacia():
    con_doc = 'def tarea():\n    """Documentada."""\n    pass\n'
    assert any("pass" in d for d in pre_auditoria_estatica(con_doc))


def test_tambien_audita_funciones_async():
    """La mitad de este proyecto es `async def`; la versión anterior no las veía."""
    assert any("pass" in d for d in pre_auditoria_estatica(
        "async def tarea():\n    pass\n"))


def test_varios_bloques_se_auditan_todos():
    texto = ("Primero:\n\n```python\ndef a():\n    pass\n```\n\n"
             "Y luego:\n\n```python\ntry:\n    x = 1\nexcept:\n    x = 0\n```\n")
    defectos = pre_auditoria_estatica(texto)
    assert any("pass" in d for d in defectos)
    assert any("except" in d for d in defectos)


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
