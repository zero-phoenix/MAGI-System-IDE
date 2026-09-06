"""
LILIM — la capa local superveloz (v12). Su contrato en tres reglas:

  1. lo que está en memoria → respuesta en ms CON procedencia
  2. lo que no está → NO LO SÉ (local). NUNCA inventa.
  3. cero red: su coste es cero y por eso puede correr antes de todo.
"""
from magi.modules import lilim


def test_responde_controles_con_procedencia():
    r = lilim.pregunta("como se juega ps_vita")
    assert "CONTROLES ps_vita" in r
    assert "fuente: controles.json" in r


def test_responde_decomp_con_procedencia():
    r = lilim.pregunta("explica el flujo de una decompilacion dusklight")
    assert "DECOMP" in r and "fuente: controles.json" in r


def test_recomienda_repos_con_url():
    r = lilim.repos_de("decomp")
    assert "objdiff" in r or "ghidra" in r
    assert "https://" in r and "falsable" in r


def test_lo_desconocido_no_se_inventa():
    """LA REGLA: si no está en memoria, la única respuesta honesta es
    NO LO SÉ (local). Un Lilim que improvisa es el sistema mintiendo rápido."""
    for pregunta in ("cual es la capital de kirguistan",
                     "receta de paella valenciana",
                     "predicame la loteria de mañana"):
        assert lilim.pregunta(pregunta) == lilim.NO_LO_SE, pregunta


def test_repos_de_tema_ajeno_tampoco_inventa():
    assert lilim.NO_LO_SE in lilim.repos_de("cosmetica")


def test_vacio_y_no_texto():
    assert lilim.pregunta("") == lilim.NO_LO_SE
    assert lilim.pregunta(None) == lilim.NO_LO_SE
