"""
La sonda deja de ser un adorno: dispara sola y el reparto la obedece.

QUÉ ESTABA MAL
==============
`sonda.py` llevaba semanas construida, probada y **sin que nadie la llamara**.
Y no era que faltara el disparador: `medir_candidato` invocaba
`llm.generate(..., proveedor=, modelo=)` y `FreeCloudLLM.generate` no acepta
esos argumentos —elige él dentro de la familia—. La sonda estaba escrita contra
un interfaz que no existía, así que no había con qué dispararla.

Eso importa más de lo que parece: medir «lo que la familia elija» habría dado
siempre la latencia del candidato que respondió, nunca la del que falla. El
panel diría que todo va bien mientras la mitad del catálogo está muerta, que es
exactamente lo que pasó el 13 de agosto.
"""
from __future__ import annotations

import time

import pytest

from magi.core.providers import sonda
from magi.core.providers.registry import ProviderRegistry
from magi.core.store.state import TaskStore


@pytest.fixture()
def store_vacio(tmp_path):
    """Base de datos propia por test: la sonda escribe, y compartirla haría
    que un test dependiera de cuáles corrieron antes."""
    return TaskStore(path=tmp_path / "sonda.db")


# =========================================== el freno: no gastar tu cuota

def test_sin_ninguna_medicion_toca_sondear(store_vacio):
    toca, motivo = sonda.toca_sondear(store_vacio)
    assert toca is True
    assert "ninguna medición" in motivo


def test_recien_medido_NO_vuelve_a_sondear(store_vacio):
    """
    EL FRENO QUE EVITA GASTARTE LA CUOTA.

    El disparo vive en el arranque del kernel, y el arranque ocurre cada vez
    que abres MAGI. Sin freno, abrir y cerrar cinco veces son cinco sondeos
    completos contra proveedores gratuitos — con TU cuota. Una sonda que se
    gasta la cuota del usuario ha empeorado el sistema por muy buenos que sean
    sus datos.
    """
    sonda.registrar(store_vacio, sonda.Medicion(
        "claude", "Perplexity", "claude45sonnet", ok=True, ms=3723.0))

    toca, motivo = sonda.toca_sondear(store_vacio)
    assert toca is False
    assert "dentro de" in motivo, "hay que decir CUÁNDO volverá a tocar"


def test_pasado_el_intervalo_vuelve_a_tocar(store_vacio):
    ayer = time.time() - (25 * 3600)
    sonda.registrar(store_vacio, sonda.Medicion(
        "claude", "Perplexity", "claude45sonnet", ok=True, ms=3723.0, ts=ayer))

    toca, motivo = sonda.toca_sondear(store_vacio)
    assert toca is True
    assert "hace" in motivo


@pytest.mark.asyncio
async def test_refrescar_no_mide_si_no_toca(store_vacio):
    """El freno vive DENTRO de `refrescar_si_toca`, no en quien llama."""
    sonda.registrar(store_vacio, sonda.Medicion(
        "claude", "Perplexity", "x", ok=True, ms=100.0))

    llamado: list[int] = []

    class LlmQueNoDebeUsarse:
        async def generate(self, *a, **k):
            llamado.append(1)
            return "funciona", "x"

    hechas, _ = await sonda.refrescar_si_toca(
        LlmQueNoDebeUsarse(), [("claude", "Perplexity", "x")], store_vacio)
    assert hechas == 0
    assert not llamado, "ha sondeado cuando no tocaba: eso es cuota tuya"


@pytest.mark.asyncio
async def test_un_fallo_de_la_sonda_no_puede_tumbar_el_arranque(store_vacio):
    """
    Un sistema de observación que impide arrancar al sistema observado no es
    una mejora. Si la sonda revienta, se devuelve el motivo y MAGI sigue.
    """
    class LlmQueRevienta:
        async def generate(self, *a, **k):
            raise RuntimeError("la red se cayó")

    hechas, motivo = await sonda.refrescar_si_toca(
        LlmQueRevienta(), [("claude", "P", "m")], store_vacio)
    assert isinstance(hechas, int)
    assert isinstance(motivo, str) and motivo


# =========================================== el reparto obedece a la medida

def _registro_con(familias: dict[str, int]) -> ProviderRegistry:
    """Registro con una familia por proveedor y la prioridad que se indique."""
    from magi.core.providers.backends.echo import EchoProvider

    reg = ProviderRegistry()
    for i, (fam, prioridad) in enumerate(familias.items()):
        p = EchoProvider(f"p{i}", fam, canned="ok")
        reg.register(p, priority=prioridad)
    for r in reg._regs.values():
        r.available = True
    return reg


def test_sin_medidas_manda_la_prioridad_escrita_a_mano():
    """El comportamiento de siempre cuando la sonda aún no ha dicho nada."""
    reg = _registro_con({"lenta": 1, "rapida": 2, "media": 3})
    a = reg.select_for_swarm()
    assert a.families["BALTHASAR"] == "lenta"   # priority 1 gana


def test_con_medidas_manda_LO_MEDIDO_y_no_la_prioridad():
    """
    EL CAMBIO QUE HACE ÚTIL A LA SONDA.

    `priority` es un entero escrito a mano cuando se registró el proveedor.
    Repartir por él es repartir según lo que alguien creyó hace semanas — y el
    2026-08-13, cinco de las seis familias marcadas «verificadas» el día 6
    estaban rotas al medirlas.

    Con medidas, la mejor familia MEDIDA va a BALTHASAR, que es la regla que
    pidió el usuario.
    """
    reg = _registro_con({"lenta": 1, "rapida": 2, "media": 3})
    reg.aplicar_medidas({"lenta": 9000.0, "rapida": 1800.0, "media": 4800.0})

    a = reg.select_for_swarm()
    assert a.families["BALTHASAR"] == "rapida", "la mejor medida va a BALTHASAR"
    assert a.families["CASPER"] == "media", "la segunda, a CASPER"
    assert a.families["MELCHIOR"] == "lenta"


def test_lo_no_medido_va_DETRAS_de_lo_medido():
    """
    «No lo sé» no es «es rápida».

    Si una familia sin medir se colara delante, el enjambre le daría su mejor
    puesto a algo de lo que no se sabe nada — y la sonda habría empeorado el
    reparto en vez de mejorarlo.

    TRES familias y no dos, y el detalle no es cosmético: con solo dos,
    `select_for_swarm` entra en la rama «partial», donde CASPER se AÍSLA en la
    primera y los otros dos comparten la segunda. Ahí el orden no significa lo
    mismo, y la primera versión de este test falló por eso — comprobaba el
    reparto degradado creyendo comprobar el completo.
    """
    reg = _registro_con({"sin_medir": 1, "medida_lenta": 9, "medida_rapida": 8})
    reg.aplicar_medidas({"medida_lenta": 20000.0, "medida_rapida": 3000.0})

    a = reg.select_for_swarm()
    assert a.diversity == "full", "hacen falta 3 familias para el reparto pleno"
    assert a.families["BALTHASAR"] == "medida_rapida"
    assert a.families["CASPER"] == "medida_lenta"
    assert a.families["MELCHIOR"] == "sin_medir", (
        "lo no medido tiene que ir el último, por muy baja que sea su "
        "prioridad escrita a mano")


def test_una_medida_absurda_se_ignora():
    """Un 0 o un negativo no son latencias: entrarían primeros y mandarían."""
    reg = _registro_con({"a": 1, "b": 2})
    reg.aplicar_medidas({"a": 0.0, "b": -5.0, "inexistente": 10.0})
    assert reg._medias_ms == {"inexistente": 10.0}


def test_la_media_de_una_familia_es_la_de_su_mejor_candidato(store_vacio):
    """
    Es el primero que se intenta, así que es el que define la experiencia. La
    media del conjunto castigaría a una familia con un buen primero y una cola
    larga de reservas lentas.
    """
    for prov, ms in (("rapido", 1000.0), ("lento", 9000.0)):
        sonda.registrar(store_vacio, sonda.Medicion(
            "fam", prov, "", ok=True, ms=ms))

    medias = sonda.medias_por_familia(store_vacio)
    assert medias["fam"] == pytest.approx(1000.0, abs=1.0)


def test_una_familia_sin_medidas_no_aparece(store_vacio):
    sonda.registrar(store_vacio, sonda.Medicion(
        "fam", "p", "", ok=False, tipo_error="timeout"))
    assert "fam" not in sonda.medias_por_familia(store_vacio)


# =========================================== auditar el propio medidor

@pytest.mark.asyncio
async def test_la_sonda_no_revienta_con_una_respuesta_con_emoji(store_vacio):
    """
    EL INSTRUMENTO TAMBIÉN SE AUDITA — y esto no es paranoia.

    Midiendo a mano el 2026-08-13 registré `Yqcloud -> FALLO
    UnicodeEncodeError` y estuve a punto de darlo por roto. El error lo lanzaba
    **mi propio `print`** al volcar una respuesta con un emoji en una consola
    cp1252. El proveedor funcionaba. Un plan apoyado en mediciones hereda los
    bugs del medidor.

    Aquí se comprueba que una respuesta con emoji, acentos y CJK atraviesa la
    sonda entera —medir, registrar, resumir— sin lanzar.
    """
    class LlmConEmoji:
        async def generate(self, *a, **k):
            return "¡Funciona! 🚀 conexión établie 中文 ñandú", "x"

    m = await sonda.medir_candidato(LlmConEmoji(), "fam", "prov", "modelo")
    assert m.ok is True

    sonda.registrar(store_vacio, m)
    resumen = sonda.resumen_para_panel(store_vacio)
    assert resumen["familias"]

    # Y el texto tiene que poder IMPRIMIRSE, que es donde reventó de verdad.
    import json
    json.dumps(resumen, ensure_ascii=False).encode("utf-8")
    str(m.detalle).encode("utf-8")


@pytest.mark.asyncio
async def test_una_respuesta_en_chino_se_mide_pero_suspende_el_idioma(store_vacio):
    """
    Yqcloud responde rápido y en chino. Por latencia gana; por utilidad es
    inservible. Sin el eje de idioma, la medida miente por omisión.
    """
    class LlmChino:
        async def generate(self, *a, **k):
            return "看起来你输入的内容里「funciona」是西班牙语，意思是运行。", "x"

    m = await sonda.medir_candidato(LlmChino(), "gpt", "Yqcloud", "gpt-4")
    assert m.ok is True, "responder es responder: la latencia es real"
    assert m.idioma_ok is False, "…pero no sirve, y hay que decirlo"
    assert "[zh]" in (m.detalle or ""), "el detalle debe decir en qué idioma"


@pytest.mark.asyncio
async def test_una_respuesta_en_ingles_SI_vale():
    """
    Es la diferencia que introdujo la regla nueva: el inglés se traduce en una
    llamada corta, el chino hay que descartarlo. Puntuarlos igual sería tirar
    un candidato bueno.
    """
    class LlmIngles:
        async def generate(self, *a, **k):
            return ("A mutex allows one thread at a time, while a semaphore "
                    "has a counter for several."), "x"

    m = await sonda.medir_candidato(LlmIngles(), "fam", "prov", "m")
    assert m.ok is True and m.idioma_ok is True


# =========================================== el canario nuevo

def test_el_canario_es_una_pregunta_de_verdad():
    """
    Era «Responde únicamente con la palabra: funciona», y SUSPENDÍA AL MEJOR
    PROVEEDOR DEL SISTEMA: `Perplexity` es un buscador por dentro y contestaba
    «No entiendo la consulta "di: funciona"». Con una pregunta técnica real
    responde correctamente en 4,2 s.

    El examen medía la capacidad de obedecer una orden artificial, no la de
    servir para lo que este sistema hace.
    """
    p = sonda.PROMPT_CANARIO.lower()
    assert "?" in sonda.PROMPT_CANARIO, "una pregunta, no una orden"
    assert "mutex" in p
    assert "únicamente con la palabra" not in p
    assert len(sonda.PROMPT_CANARIO) < 120, "sigue siendo barato de responder"


def test_hay_señales_para_saber_si_ENTENDIO():
    assert sonda.SEÑALES_ESPERADAS
    assert "mutex" in sonda.SEÑALES_ESPERADAS
