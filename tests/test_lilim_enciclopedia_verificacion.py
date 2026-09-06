"""
Pruebas para L3 y L4: Verificación de novedades contra fuentes y Enciclopedia por dominios.

Verifica:
- L4: Enciclopedia técnica por dominios (SH2, VDP, Vita, Decomp) con procedencia falsable.
- L4: pregunta() responde de forma determinista usando la enciclopedia técnica.
- L3: verificar_novedades_fuente() verifica con lectura web sin navegador y actualiza fecha.
- L3: Sin coincidencia o ante fallo de red -> permanece SIN COMPROBAR (nunca inventa).
"""
from __future__ import annotations

import pytest

from magi.modules.lilim import (
    NO_LO_SE,
    enciclopedia,
    pregunta,
    verificar_novedades_fuente,
)


def test_enciclopedia_dominios_conocidos():
    """L4: Consulta la enciclopedia técnica por dominios curados con procedencia."""
    # SH2
    r_sh2 = enciclopedia("sh2")
    assert "Hitachi SuperH SH-2" in r_sh2
    assert "pipeline de 2 etapas" in r_sh2
    assert "fuente: https://segaretro.org/Hitachi_SH-2" in r_sh2

    # VDP
    r_vdp = enciclopedia("vdp")
    assert "VDP1" in r_vdp and "VDP2" in r_vdp
    assert "frame buffer" in r_vdp

    # Vita
    r_vita = enciclopedia("vita")
    assert "VitaSDK" in r_vita
    assert "sceCtrl" in r_vita

    # Decomp
    r_decomp = enciclopedia("decomp")
    assert "Matching" in r_decomp
    assert "objdiff" in r_decomp


def test_enciclopedia_dominio_desconocido():
    """L4: Si el dominio no está en la enciclopedia, responde NO_LO_SE sin inventar."""
    r = enciclopedia("dominio_inexistente_xyz")
    assert r == NO_LO_SE


def test_pregunta_responde_con_enciclopedia():
    """L4: lilim pregunta() consulta la enciclopedia técnica en milisegundos."""
    r = pregunta("que arquitectura tiene el procesador sh2 de saturn")
    assert "SH2" in r
    assert "SDRAM principal" in r
    assert "fuente: https://segaretro.org" in r


def test_verificar_novedades_fuente_actualiza_con_evidencia(monkeypatch, tmp_path):
    """L3: verificar_novedades_fuente valida la fuente y marca verificado: true."""
    # Mock lector web que simula lectura exitosa de la URL
    def _lector_mock(url: str):
        if "openai.com" in url:
            return True, "OpenAI announced GPT-4 multimodal language models", {}
        return False, "", {}

    nuevos, total, reporte = verificar_novedades_fuente("GPT-4", _lector=_lector_mock)
    assert total >= 1
    assert "GPT-4" in reporte


def test_verificar_novedades_sin_red_permanece_sin_comprobar():
    """L3: Si no hay red o la fuente no coincide, permanece SIN COMPROBAR."""
    def _lector_fallido(url: str):
        return False, "SIN COMPROBAR: conexión rechazada", {}

    nuevos, total, reporte = verificar_novedades_fuente("Llama 2", _lector=_lector_fallido)
    assert nuevos == 0
    assert "SIN COMPROBAR" in reporte
