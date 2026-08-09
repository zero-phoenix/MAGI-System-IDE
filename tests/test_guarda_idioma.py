"""
Test del fix de idioma del enjambre (Fase D, Bug 1).

Reproduce el caso del terminal: CASPER entregó su aprobación en chino
(三个方案...) porque nadie validaba el idioma de la respuesta. Ahora _ask
tiene una guarda que rota de familia si la respuesta viene en otro idioma.

Este test mockea el provider para simular el escenario de forma determinista:
- La familia propia del nodo (command) responde en chino.
- Otra familia (gpt) responde en español.
El test verifica que _ask devuelve la respuesta en español, no la china.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from magi.core.bus import MagiBus
from magi.modules.swarm.agents import MelchiorAgent


def _agente_con_llm_mock(respuestas_por_familia: dict):
    """
    Construye un MelchiorAgent cuyo llm.generate devuelve respuestas distintas
    según la familia pedida. Simula el comportamiento del proveedor real sin
    tocar la red.
    """
    agente = MelchiorAgent.__new__(MelchiorAgent)  # sin __init__ (evita Naoko etc.)
    agente.role_name = "MELCHIOR"
    agente.family = "command"
    agente.seed = 42
    agente.rama = False
    agente.bus = MagicMock()

    async def fake_generate(sys_prompt, user_prompt, family=None, **kw):
        texto = respuestas_por_familia.get(family,
                    respuestas_por_familia.get("command", ""))
        # devuelve (contenido, provider_id)
        return texto, f"g4f-{family}"

    agente.llm = MagicMock()
    agente.llm.generate = fake_generate
    return agente


@pytest.mark.asyncio
async def test_ask_rota_cuando_la_familia_propia_responde_en_otro_idioma():
    """La familia propia (command) responde en chino; la guarda debe rotar a gpt."""
    agente = _agente_con_llm_mock({
        "command": "三个方案（A、B、C）再次提交的内容完全相同，未包含任何技术实现。",  # chino
        "gpt": "Las tres propuestas son idénticas y no contienen código.",  # español
    })

    contenido, provider_id, familia = await agente._ask(
        sys_prompt="Eres Melchior.",
        user_prompt="Resume las tres propuestas.",
    )

    # La guarda debe haber rotado a gpt y devuelto la respuesta en español.
    assert "tres propuestas" in contenido.lower(), (
        f"Se esperaba la respuesta en español, se obtuvo: {contenido!r}")
    assert familia == "gpt", f"Se esperaba rotación a gpt, se obtuvo {familia!r}"


@pytest.mark.asyncio
async def test_ask_no_rota_si_la_respuesta_ya_esta_en_el_idioma_correcto():
    """Si la familia propia responde bien, no hay rotación: eficiencia."""
    agente = _agente_con_llm_mock({
        "command": "Las tres propuestas son idénticas y no contienen código.",
    })
    contenido, provider_id, familia = await agente._ask(
        sys_prompt="Eres Melchior.",
        user_prompt="Resume las tres propuestas.",
    )
    assert "tres propuestas" in contenido.lower()
    assert familia == "command", "No debió rotar si la respuesta era correcta"


@pytest.mark.asyncio
async def test_ask_devuelve_algo_aunque_ninguna_familia_acierte_el_idioma():
    """Si todas fallan, devuelve la última respuesta (algo es mejor que nada)."""
    agente = _agente_con_llm_mock({
        "command": "三个方案完全相同",   # chino
        "gpt": "All three proposals are identical",  # inglés
        "gemini": "Les trois propositions sont identiques",  # francés
    })
    contenido, provider_id, familia = await agente._ask(
        sys_prompt="Eres Melchior.",
        user_prompt="Resume las tres propuestas.",
    )
    # No debe estar vacío: entregar algo ilegible es mejor que entregar nada.
    assert contenido, "Debió devolver la última respuesta aunque fuera en otro idioma"
