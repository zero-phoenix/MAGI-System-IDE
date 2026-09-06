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


# ------------------------------------------------ v12b: traductor y novedades

def test_traduce_termino_conocido_con_procedencia():
    r = lilim.traduce("emulador", "en")
    assert "emulator" in r and "TRADUCCIÓN LOCAL" in r
    assert "memoria" in r


def test_traduce_no_inventa_lo_desconocido():
    """La palabra que no está se deja tal cual y se avisa: Lilim no inventa
    traducciones — para eso es el puente al enjambre."""
    r = lilim.traduce("paella valenciana", "ja")
    assert "paella" in r            # la palabra desconocida pasa sin traducir
    assert "enjambre" in r          # y se dice que la frase va por la nube


def test_idiomas_del_contrato():
    for destino in ("en", "de", "ru", "ja", "zh"):
        r = lilim.traduce("emulador", destino)
        assert "TRADUCCIÓN LOCAL" in r, destino
    assert "no está en el contrato" in lilim.traduce("emulador", "fr")


def test_detecta_idioma_por_escritura():
    assert lilim.detecta_idioma("привет мир") == "ru"
    assert lilim.detecta_idioma("テスト") == "ja"
    assert lilim.detecta_idioma("测试") == "zh"
    assert lilim.detecta_idioma("Prüfung") == "de"


def test_novedades_con_fuente_y_sin_comprobar():
    r = lilim.novedades("baterias")
    assert "SIN COMPROBAR" in r, "lo no verificado se dice"
    assert "verificar:" in r, "cada entrada trae su fuente falsable"


def test_contexto_para_el_enjambre():
    r = lilim.contexto("crea un juego de tetris en un exe portable")
    assert "CONTEXTO LILIM" in r and "pygame" in r


def test_responde_si_sabe_es_el_puente():
    assert "CONTROLES" in lilim.responde_si_sabe("como se juega ps_vita")
    assert lilim.responde_si_sabe("capital de kirguistan") is None
