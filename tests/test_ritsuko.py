"""
Ritsuko audita, y solo audita.

Estos tests fijan las cuatro cosas que la hacen útil, y que son justo las que
se pierden cuando alguien "mejora" un auditor: que no comparta proveedor con
quien vigila, que no actúe, que hable en un idioma que el usuario lee, y que
lo que dice quede escrito.
"""
from __future__ import annotations

import asyncio

import pytest

from magi.core.bus import BusEvent, MagiBus
from magi.modules.infrastructure.ritsuko import (
    FAMILIAS_AUDITADAS,
    FAMILIAS_RITSUKO,
    MODELOS_RITSUKO,
    RitsukoAgent,
)


@pytest.fixture
async def ritsuko(monkeypatch, tmp_path):
    bus = MagiBus()
    agente = RitsukoAgent(bus)
    await agente.start()
    return agente


def test_ritsuko_no_comparte_familia_con_nadie_del_sistema():
    """
    La independencia es tecnica, no ceremonial.

    Si Ritsuko usara la familia de Casper, el dia que ese proveedor se cayera
    se caerian los dos: el auditado y quien tenia que avisar de que se habia
    caido. Este test es el que impide que alguien "arregle" a Ritsuko
    poniendole el modelo que mejor va hoy.
    """
    from magi.core.providers.backends.g4f_backend import (
        DEFAULT_SWARM_FAMILIES,
        FAMILY_SPECS,
    )

    modelos_del_enjambre = set()
    for familia in DEFAULT_SWARM_FAMILIES.values():
        modelos_del_enjambre |= {m for _, m in FAMILY_SPECS.get(familia, [])}

    for modelo in MODELOS_RITSUKO:
        assert modelo not in modelos_del_enjambre, (
            f"{modelo} lo usa el enjambre: Ritsuko dejaria de ser independiente")

    for familia in FAMILIAS_AUDITADAS:
        for _, modelo in FAMILY_SPECS.get(familia, []):
            assert modelo not in MODELOS_RITSUKO, (
                f"{modelo} pertenece a {familia}, que Ritsuko audita")


async def test_no_actua_aunque_se_lo_pidan(monkeypatch):
    """Le pides que arregle y contesta lo que SI puede hacer, sin tocar nada."""
    bus = MagiBus()
    agente = RitsukoAgent(bus)
    await agente.start()

    async def falso(user_prompt, lang="es"):
        return "Veredicto: IGUAL. Sin cambios relevantes."

    monkeypatch.setattr(agente, "_pensar", falso)

    dichos: list[dict] = []
    bus.subscribe("ritsuko.log", lambda e: dichos.append(e.payload))

    await agente._handle_user_message(BusEvent(
        topic="ritsuko.user_message",
        payload={"message": "arregla el orquestador ahora mismo"}))
    # El bus entrega en su worker, no en la llamada: sin ceder el control, el
    # test comprobaria el buzon antes de que llegue el correo.
    await asyncio.sleep(0.2)

    respuestas = [d for d in dichos if d.get("agent") == "RITSUKO"]
    assert respuestas, "Ritsuko no contesto"
    texto = respuestas[-1]["content"].lower()
    assert "solo audito" in texto or "only audit" in texto


@pytest.mark.parametrize("mensaje,espera", [
    ("arregla esto", True),
    ("aplica el parche", True),
    ("que opinas del sistema", False),
    # La trampa clasica: `in` sobre subcadenas daria positivo aqui por "aplica"
    # dentro de "aplicacion", y por "corrige" dentro de "correnos". Se comparan
    # palabras enteras justo por eso.
    ("como va la aplicacion", False),
])
def test_distingue_pedir_accion_de_preguntar(mensaje, espera):
    agente = RitsukoAgent(MagiBus())
    assert agente._piden_actuar(mensaje) is espera


def test_solo_espanol_o_ingles():
    agente = RitsukoAgent(MagiBus())
    assert agente._idioma_del_usuario("¿como va el sistema?") == "es"
    assert agente._idioma_del_usuario("how is the system doing") in ("es", "en")
    # Lo que no puede pasar bajo ningun concepto es devolver otro idioma.
    assert agente._idioma_del_usuario("システムはどうですか") in ("es", "en")


async def test_el_informe_queda_escrito_y_se_puede_descargar(monkeypatch):
    bus = MagiBus()
    agente = RitsukoAgent(bus)
    await agente.start()

    async def falso(user_prompt, lang="es"):
        return "Veredicto: MEJORA. Naoko acerto con el reparto."

    monkeypatch.setattr(agente, "_pensar", falso)
    inf = await agente.auditar(motivo="test")

    assert inf.ruta is not None and inf.ruta.is_file()
    contenido = inf.ruta.read_text(encoding="utf-8")
    assert "Veredicto" in contenido and "Evidencia medida" in contenido
    assert "solo audita" in contenido.lower()


async def test_ve_lo_que_hace_naoko_y_lo_que_callan_los_nodos():
    """
    La evidencia sale del bus, sin preguntarle a nadie.

    Un nodo mudo es la senal mas barata de que algo se rompio y la que nadie
    mira: el sistema sigue "funcionando" con dos de tres.
    """
    bus = MagiBus()
    agente = RitsukoAgent(bus)
    await agente.start()

    await agente._anotar(BusEvent(topic="naoko.log", payload={
        "agent": "NAOKO", "content": "Deriva detectada en g4f-gpt"}))
    await agente._anotar(BusEvent(topic="AGENT_POST", payload={
        "agent": "MELCHIOR", "content": "propuesta"}))
    await agente._anotar(BusEvent(topic="AGENT_POST", payload={
        "agent": "BALTHASAR", "content": "critica"}))

    ev = agente.evidencia()
    assert ev["naoko"]["intervenciones"] == 1
    assert ev["naoko"]["derivas_declaradas"] == 1
    assert ev["nodos"]["aportaciones"]["MELCHIOR"] == 1
    assert "CASPER" in ev["nodos"]["mudos"]


async def test_sin_proveedores_lo_dice_en_vez_de_inventarse_un_veredicto(monkeypatch):
    """
    Preferimos "no puedo auditar" a un informe firmado por el auditado.

    Es la misma regla que el resto del sistema: decirlo entero en vez de
    entregar algo que parece bueno y no lo es.
    """
    bus = MagiBus()
    agente = RitsukoAgent(bus)

    async def siempre_falla(system_prompt, user_prompt, **kw):
        raise RuntimeError("proveedor caido")

    monkeypatch.setattr(agente.llm, "generate", siempre_falla)
    texto = await agente._pensar("audita esto", "es")
    assert "no he podido emitir veredicto" in texto.lower()


async def test_un_fallo_disfrazado_de_texto_no_es_un_veredicto(monkeypatch):
    """
    Lo cazó la prueba del 20-ago: el informe de Ritsuko traía como veredicto
    `[Inferencia no disponible: todos los proveedores fallaron...]`.

    `cloud.py` devuelve ese texto con `provider_id == "SYSTEM_ERROR"`, y la
    primera version de `_pensar` solo miraba el texto. Es EXACTAMENTE el fallo
    que Ritsuko existe para denunciar en el enjambre —firmar un veredicto
    encima de un error—, cometido por ella misma.
    """
    bus = MagiBus()
    agente = RitsukoAgent(bus)
    intentos: list[str] = []

    familias: list[str] = []

    async def degradada(system_prompt, user_prompt, **kw):
        intentos.append(kw.get("model"))
        familias.append(kw.get("family"))
        return "[Inferencia no disponible: todos los proveedores fallaron]", "SYSTEM_ERROR"

    monkeypatch.setattr(agente.llm, "generate", degradada)
    texto = await agente._pensar("audita esto", "es")

    # C14 — y se pide por FAMILIA, que es el eje que garantiza independencia.
    assert intentos and all(f is None for f in intentos), (
        "Ritsuko debe pedir por familia, no por alias de modelo")

    assert "no he podido emitir veredicto" in texto.lower()
    # El veredicto es SUYO y dice que no puede opinar. Puede citar el error
    # como causa —eso es informar—, pero el error no puede SER el veredicto.
    assert texto.startswith("[RITSUKO]")
    # Y se prueba TODA su cadena antes de rendirse, no solo el primero.
    assert familias == list(FAMILIAS_RITSUKO)
    assert not (set(familias) & set(FAMILIAS_AUDITADAS)), (
        "ni como último recurso puede caer en una familia que audita")


async def test_un_timeout_del_bucle_de_herramientas_tampoco_cuela(monkeypatch):
    bus = MagiBus()
    agente = RitsukoAgent(bus)

    async def timeout(system_prompt, user_prompt, **kw):
        return ("[Tiempo de espera agotado tras 150s en iteracion 1. "
                "Proveedor: g4f-gpt]"), "g4f-gpt"

    monkeypatch.setattr(agente.llm, "generate", timeout)
    texto = await agente._pensar("audita esto", "es")
    assert "no he podido emitir veredicto" in texto.lower()
