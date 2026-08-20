"""
Hedge selectivo (v6.0 §A1): la cobertura por candidato deja de ser global.

POR QUÉ
=======
El log del 16-ago —«crea un juego de tetris en un unico ejecutable exe
portable»— quemó ~50 llamadas HTTP para UNA petición. El hedge global x3
cubría también las variantes y ejes que YA se cubren entre sí: 3 variantes de
Melchior con hedge x3 eran hasta 9 HTTP en una sola etapa. Desde este cambio,
quien tiene redundancia estructural pide `hedge=False` y el backend decide en
las llamadas únicas.

CUBRE DOS CAPAS
===============
- La política del backend (`_hedge_max_politica`): True siempre cubre, False
  nunca, y el modo auto (None) según la latencia medida de la familia.
- El cableado del enjambre (`parallel.py` / `agents.py`): las variantes y los
  ejes piden explícitamente `hedge=False`; el arbitraje único deja None
  (auto), para que el backend decida con sus medidas.
"""
import pytest

from magi.core.blackboard import Blackboard
from magi.core.bus import MagiBus
from magi.core.providers.backends.g4f_backend import HEDGE_MAX, G4FProvider
from magi.core.providers.base import CompletionRequest, Message
from magi.core.providers.cloud import FreeCloudLLM
from magi.modules.swarm.agents import BalthasarAgent, CasperAgent, MelchiorAgent
from magi.modules.swarm.parallel import critique_multi_axis, generate_variants


def _backend():
    return G4FProvider("gpt",
                       candidates=[("nostalgia", "v1"), ("elsewhere", "v2")])


def _peticion(hedge=None):
    return CompletionRequest(
        messages=[Message(role="user", content="x")],
        hedge=hedge, tag="t/r1/melchior/v0")


# ------------------------------------------------------------ la política

def test_hedge_explicito_siempre_cubre():
    assert _backend()._hedge_max_politica(_peticion(True)) == HEDGE_MAX


def test_hedge_false_nunca_cubre():
    assert _backend()._hedge_max_politica(_peticion(False)) == 1


def test_auto_sin_medidas_cubre_por_prudencia():
    # Familia sin medir: no se puede saber si es lenta, y el costo de
    # equivocarse es un solo candidato colgado, no un techo de llamadas.
    assert _backend()._hedge_max_politica(_peticion(None)) == HEDGE_MAX


def test_auto_con_familia_rapida_no_cubre():
    b = _backend()
    b._latencia = {"cualquiera": 2000.0}   # mejor medido: 2 s
    assert b._hedge_max_politica(_peticion(None)) == 1


def test_auto_con_familia_lenta_cubre():
    b = _backend()
    b._latencia = {"cualquiera": 9000.0}   # mejor medido: 9 s
    assert b._hedge_max_politica(_peticion(None)) == HEDGE_MAX


# ----------------------------------------------------------- el cableado

@pytest.mark.asyncio
async def test_variantes_y_ejes_piden_hedge_false(monkeypatch):
    """
    Las llamadas con redundancia estructural (N variantes de Melchior, N ejes
    de Balthasar) deben llegar al transporte con `hedge=False`: su cobertura
    es el resto de llamadas paralelas, y pedir además el hedge x3 del backend
    es lo que multiplicó ~16 llamadas lógicas hasta ~50 HTTP el 16-ago.
    """
    vistos: list[tuple[str, object]] = []
    #: Quién hizo cada llamada. Solo se rellena para las que llegan SIN tag,
    #: que son las que no deberían existir: cuando este test falló en la suite
    #: en paralelo (y pasaba al ejecutarlo solo) el mensaje era un
    #: `AttributeError: 'NoneType' has no attribute 'startswith'`, que no dice
    #: quién llamó. Un fallo que no nombra al culpable se archiva como
    #: «flaky» y se ignora, que es como se pierden los guardianes.
    culpables: list[str] = []

    async def falso(self, *a, **kw):
        vistos.append((kw.get("tag"), kw.get("hedge")))
        if kw.get("tag") is None:
            import traceback
            culpables.append("".join(traceback.format_stack(limit=12)))
        return ("Respuesta válida en español. ### CONCLUSIÓN", "g4f-cualquiera")

    monkeypatch.setattr(FreeCloudLLM, "generate", falso)

    bus = MagiBus()
    melchior = MelchiorAgent(Blackboard(), bus)
    await generate_variants(
        melchior, task_id="t", command="escribe algo", round_num=1, n=3,
        engine="fast", narrative_style="tecnico",
        last_proposal=None, last_critique=None, use_tools=False)

    balthasar = BalthasarAgent(Blackboard(), bus)
    await critique_multi_axis(
        balthasar, task_id="t", proposal_text="x", round_num=1, engine="fast",
        narrative_style="tecnico", evidence="", use_tools=False)

    assert vistos, "ninguna llamada llegó al transporte"
    for tag, hedge in vistos:
        assert tag is not None, (
            "una llamada al modelo llegó sin identidad; la hizo esto:\n"
            + "\n".join(culpables))
        assert tag.startswith("t/r1/"), f"rama sin identidad en el tag: {tag}"
        assert hedge is False, (
            f"{tag} pidió hedge={hedge} teniendo redundancia estructural")


@pytest.mark.asyncio
async def test_el_arbitraje_unico_deja_el_hedge_en_auto(monkeypatch):
    """
    Casper arbitra una sola vez por ronda: nadie más le cubre, así que su
    llamada llega con `hedge=None` y es el backend quien decide con las
    latencias medidas (deja de cubrir una familia rápida, cubre una lenta).
    """
    bus = MagiBus()
    casper = CasperAgent(Blackboard(), bus)
    escuchadas: list[object] = []

    async def falso(self, *a, **kw):
        escuchadas.append(casper.hedge)
        return ("Análisis en español.\n\n### CONCLUSIÓN\nAprobado.\n\n"
                "DECISIÓN: APROBADA", "g4f-x", "gpt")

    monkeypatch.setattr(casper, "_ask_stream", falso)

    await casper.arbitrate("t", {"content": "x"}, {"content": "y"}, 1,
                           "fast", "tecnico", use_tools=False)

    assert escuchadas == [None], (
        f"el arbitraje único debe dejar el hedge en auto (None), "
        f"pero llegó: {escuchadas}")
