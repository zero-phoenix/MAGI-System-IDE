"""
Que los oídos juzguen bien, sin necesitar tarjeta de sonido.

El veredicto vive separado de la captura justo para esto: se le dan señales
sintéticas —continua, silenciosa, entrecortada— y se comprueba que las
distingue. Un veredicto que solo se puede probar con el hardware delante es
un veredicto que nadie prueba, y acaba mintiendo el día que importa.
"""
import math

import pytest

from magi.modules.percepcion import oidos

SR = 8000          # suficiente para el análisis; no se reproduce nada
TRAMO = oidos.TRAMO_MS


def tono(segundos, sr=SR, amplitud=0.3, hz=440.0):
    n = int(segundos * sr)
    return [amplitud * math.sin(2 * math.pi * hz * i / sr) for i in range(n)]


def silencio(segundos, sr=SR):
    return [0.0] * int(segundos * sr)


# --- los tres casos que hay que distinguir -------------------------------

def test_sonido_continuo():
    v = oidos.veredicto(tono(3.0), SR)
    assert v["has_sound"] is True
    assert v["choppy"] is False
    assert v["sonando_pct"] > 95


def test_silencio_no_es_sonido():
    v = oidos.veredicto(silencio(3.0), SR)
    assert v["has_sound"] is False
    assert v["sonando_pct"] == 0.0


def test_entrecortado():
    """Sonido con caídas repetidas a silencio: hay señal, pero rota."""
    señal = []
    for _ in range(12):
        señal += tono(0.2) + silencio(0.2)
    v = oidos.veredicto(señal, SR)
    assert v["has_sound"] is True
    assert v["choppy"] is True
    assert v["cortes"] >= oidos.CORTES_MAXIMOS


def test_un_solo_corte_no_es_entrecortado():
    """Que el juego pare la música una vez no lo vuelve defectuoso."""
    v = oidos.veredicto(tono(2.0) + silencio(1.0), SR)
    assert v["has_sound"] is True
    assert v["choppy"] is False
    assert v["cortes"] == 1


# --- «no pude oírlo» no es «no sonaba» -----------------------------------

def test_captura_corta_no_inventa_veredicto():
    v = oidos.veredicto([0.1] * 10, SR)
    assert v["has_sound"] is None
    assert "error" in v


def test_parar_sin_captura_devuelve_error_no_falso():
    o = oidos.Oidos()
    v = o.parar()
    assert v["has_sound"] is None
    assert v.get("error")


# --- degradación sin backend ---------------------------------------------

def test_el_modulo_importa_sin_backend(monkeypatch):
    """Media CI corre en Linux: importar no puede depender de pyaudiowpatch."""
    monkeypatch.setattr(oidos, "_backend", lambda: (None, None, "no en linux"))
    assert oidos.disponible() is False
    assert oidos.motivo_no_disponible() == "no en linux"
    v = oidos.escuchar(0.1)
    assert v["has_sound"] is None
    assert "no disponibles" in v["error"]


def test_empezar_sin_backend_devuelve_false(monkeypatch):
    monkeypatch.setattr(oidos, "_backend", lambda: (None, None, "sin backend"))
    assert oidos.Oidos().empezar() is False


# --- la herramienta del enjambre -----------------------------------------

def _registro():
    from magi.core.tools.registry import ToolRegistry
    from magi.modules.percepcion.tools import register_percepcion_tools
    return register_percepcion_tools(ToolRegistry())


def test_las_herramientas_se_registran():
    reg = _registro()
    nombres = set(reg.names())
    assert "listen_audio" in nombres
    assert "audio_available" in nombres


def test_solo_leen_no_mutan():
    """Escuchar no puede tocar el sistema: Balthasar las usa y él no escribe."""
    reg = _registro()
    for n in ("listen_audio", "audio_available"):
        t = reg.get(n)
        assert t.access == {"read"}
        assert t.dangerous is False


@pytest.mark.parametrize("segundos", [0, 0.5, 999, "hola", None])
def test_rechaza_duraciones_absurdas(segundos, monkeypatch):
    """Escuchar bloquea: 10 minutos de captura cuelgan el turno del enjambre."""
    monkeypatch.setattr(oidos, "disponible", lambda: True)
    r = _registro().get("listen_audio").handler(seconds=segundos)
    assert r.ok is False


def test_sin_oidos_dice_SIN_COMPROBAR_no_no_suena(monkeypatch):
    """
    La distinción que justifica el módulo entero: una capacidad ausente no
    puede reportarse como un veredicto negativo.
    """
    monkeypatch.setattr(oidos, "_backend", lambda: (None, None, "sin backend"))
    r = _registro().get("listen_audio").handler(seconds=5)
    assert r.ok is False
    assert "SIN COMPROBAR" in r.error


def test_audio_available_no_falla_nunca(monkeypatch):
    """Preguntar si hay oídos tiene que responder, haya o no haya."""
    monkeypatch.setattr(oidos, "_backend", lambda: (None, None, "sin backend"))
    r = _registro().get("audio_available").handler()
    assert r.ok is True
    assert r.meta["available"] is False


# --- integración: que builtin.py lo enganche -----------------------------

def test_builtin_registra_la_percepcion():
    """Un módulo que nadie registra es andamiaje. Ya pasó tres veces."""
    from pathlib import Path
    fuente = Path("magi/core/tools/builtin.py").read_text(encoding="utf-8")
    assert "register_percepcion_tools" in fuente, (
        "los oídos no están enganchados en builtin.py")
