"""
R9 hecha módulo: una corrida del emulador sin ojos no es evidencia.

El origen es la ronda 1 de YabauseVita (30-ago-2026): FPS perfecto en el
log, pantalla negra en realidad. Estos tests fijan las tres conductas que
deben sobrevivir a cualquier refactor:

  1. pertinencia — inyectar el protocolo SOLO cuando el encargo es una
     corrida de emulador (dos condiciones: correr/medir + emulador)
  2. contenido — el protocolo nombra los dos contadores de FPS, el
     veredicto de imagen y movimiento, y la ventana del juego (no la del GUI)
  3. harness — vita3k_ctl.py se localiza hacia arriba, y la variable de
     entorno gana, como en bitacora.localizar
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from magi.modules.swarm import ronda_verificada as rv


@pytest.mark.parametrize("encargo", [
    "mide los FPS de Sonic R en el emulador con la build nueva",
    "corrida de verificacion de NiGHTS en Vita3K, 3 minutos",
    "ronda 2: verificar que el input llega al juego en yabausevita",
    "benchmark de panzer dragoon y captura de pantalla",
])
def test_pertinente_cuando_es_corrida_de_emulador(encargo):
    assert rv.pertinente(encargo)


@pytest.mark.parametrize("encargo", [
    "escribe el README del emulador",
    "explica la arquitectura del dynarec",           # emulador sin corrida
    "mide la latencia del GUI en milisegundos",      # corrida sin emulador
    "arregla el workflow de release",
])
def test_no_pertinente_cuando_no_hay_corrida_de_emulador(encargo):
    assert not rv.pertinente(encargo)
    assert rv.para_el_prompt(encargo) == ""


def test_el_protocolo_exige_los_cuatro_datos():
    texto = rv.para_el_prompt("corre una ronda de medicion del emulador saturn")
    # Los dos contadores de FPS, por separado (R11)
    assert "app" in texto and "ROM" in texto
    # Veredicto de imagen y de movimiento
    assert "has_image" in texto and "has_motion" in texto
    # La ventana DEL juego, no la del GUI
    assert "960x544" in texto
    # Y la consecuencia: sin ojos, la corrida no existe
    assert "sin ojos" in texto


def test_el_protocolo_conecta_con_las_tres_filosofias():
    """Las propuestas no llegan sueltas: cada una de las tres filosofías
    ortogonales (hacer menos / mover menos / repartir mejor) declara su
    métrica, y esta corrida es la que la adjudica. Sin esa conexión, el
    enjambre propondría sin saber quién decide."""
    texto = rv.para_el_prompt("ronda de medicion del emulador saturn")
    assert "hacer menos" in texto and "mover menos" in texto
    assert "repartir mejor" in texto
    assert "composite" in texto and "upload" in texto and "dropped" in texto


def test_harness_se_localiza_hacia_arriba(tmp_path, monkeypatch):
    monkeypatch.delenv("MAGI_HARNESS_VITA3K", raising=False)
    profunda = tmp_path / "a" / "b" / "c"
    profunda.mkdir(parents=True)
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "vita3k_ctl.py").write_text("# harness", encoding="utf-8")
    assert rv.harness(profunda) == tmp_path / "tools" / "vita3k_ctl.py"


def test_la_variable_de_entorno_gana(tmp_path, monkeypatch):
    falso = tmp_path / "falso_ctl.py"
    falso.write_text("#", encoding="utf-8")
    (tmp_path / "tools").mkdir(exist_ok=True)
    (tmp_path / "tools" / "vita3k_ctl.py").write_text("#", encoding="utf-8")
    monkeypatch.setenv("MAGI_HARNESS_VITA3K", str(falso))
    assert rv.harness(tmp_path) == falso


def test_sin_harness_el_prompt_lo_dice_en_vez_de_inventar_ruta(monkeypatch):
    monkeypatch.delenv("MAGI_HARNESS_VITA3K", raising=False)
    monkeypatch.chdir(Path(__file__).resolve().parent)  # sin tools/ arriba… o con él
    texto = rv.para_el_prompt("corrida del emulador saturn")
    assert "vita3k_ctl.py" in texto  # lo nombra siempre
    # y si no lo encontró, avisa que hay que buscarlo en vez de fingir ruta
    if rv.harness() is None:
        assert "no se localiz" in texto
