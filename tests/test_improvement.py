"""
Ciclo de mejora de Naoko con rondas del enjambre.

LO QUE SE PIDIÓ, Y POR QUÉ SON DOS VÍAS
=======================================
    "que naoko siempre autocorrija todo el sistema sin consultarme"
    "cuando naoko tenga una idea de mejora que me consulte"

No es contradictorio: reparar devuelve el sistema a donde ya debía estar y es
verificable con tests; mejorar cambia hacia dónde va, y ese criterio es del
usuario. Publicar es siempre suyo, porque es visible para terceros y no se
deshace con un `undo`.

Estos tests comprueban sobre todo que las COMPUERTAS no se pueden saltar. Están
en la máquina de estados y no en el prompt a propósito: un modelo puede ignorar
"consulta antes de continuar", pero no puede inventarse una transición que no
existe.
"""
import pytest

from magi.modules.infrastructure.improvement import (
    CIRCUITOS, GATES, SECUENCIA, ImprovementError, ImprovementLog, Stage,
    advance, next_actor, prompt_for, record_round, start, user_decides,
)


def _hasta_rondas(origin="naoko"):
    m = start(origin, "Cachear el catálogo de herramientas por dominio")
    user_decides(m, True)          # sí, redacta el plan
    m.plan = "1. Medir. 2. Cachear. 3. Comprobar que no se sirve rancio."
    user_decides(m, True)          # sí, pásalo al enjambre
    return m


# ------------------------------------------------------------- compuertas

def test_una_idea_nace_esperando_permiso():
    """Naoko no redacta el plan hasta que se lo autorizan."""
    m = start("naoko", "Sustituir el bucle de rondas por uno adaptativo")
    assert m.stage is Stage.IDEA
    assert m.awaiting_user
    assert "¿Desarrollo un plan" in m.question


def test_no_se_puede_saltar_del_borrador_a_la_ejecucion():
    """
    LA GUARDA CENTRAL. Si esto fuera una instrucción del prompt, un modelo
    podría decidir que el plan es evidente y aplicarlo.
    """
    m = start("naoko", "x")
    user_decides(m, True)
    assert m.stage is Stage.PLAN_BORRADOR
    with pytest.raises(ImprovementError, match="no se puede pasar"):
        advance(m, Stage.EJECUTANDO)


def test_no_se_puede_ejecutar_sin_pasar_por_el_enjambre():
    m = _hasta_rondas()
    with pytest.raises(ImprovementError):
        advance(m, Stage.EJECUTANDO)


def test_no_se_puede_publicar_sin_ejecutar():
    m = start("naoko", "x")
    with pytest.raises(ImprovementError):
        advance(m, Stage.PUBLICADO)


def test_todas_las_compuertas_esperan_al_usuario():
    for etapa in GATES:
        m = start("naoko", "x")
        m.stage = etapa
        assert m.awaiting_user, f"{etapa} debería esperar decisión"
        assert m.question, f"{etapa} no dice qué se pregunta"


def test_un_no_descarta_y_no_es_un_error():
    """
    Tratar el rechazo como fallo empuja a insistir, y una propuesta que
    insiste deja de ser una propuesta.
    """
    m = start("naoko", "x")
    user_decides(m, False)
    assert m.stage is Stage.DESCARTADA


def test_decidir_donde_no_hay_compuerta_es_un_error():
    m = _hasta_rondas()
    with pytest.raises(ImprovementError, match="no espera"):
        user_decides(m, True)


# ----------------------------------------------------------- el circuito

def test_el_orden_del_recorrido_es_el_pedido():
    m = _hasta_rondas()
    assert next_actor(m) == (1, "MELCHIOR")
    record_round(m, "MELCHIOR", "plan mejorado")
    assert next_actor(m) == (1, "BALTHASAR")
    record_round(m, "BALTHASAR", "crítica")
    assert next_actor(m) == (1, "CASPER")


def test_tras_casper_arranca_el_siguiente_circuito_SOLO():
    """
    Se pidió que Casper "automáticamente lo pase a Melchior". Sin pasar por
    el usuario: la segunda vuelta no es una decisión, es parte del método.
    """
    m = _hasta_rondas()
    for a in SECUENCIA:
        record_round(m, a, f"aportación de {a}")
    assert m.stage is Stage.RONDA, "no debe parar a preguntar entre circuitos"
    assert next_actor(m) == (2, "MELCHIOR")


def test_al_completar_los_circuitos_vuelve_al_usuario():
    m = _hasta_rondas()
    for _ in range(CIRCUITOS):
        for a in SECUENCIA:
            record_round(m, a, "x")
    assert m.stage is Stage.PLAN_FINAL
    assert m.awaiting_user
    assert "hiperperfeccionado" in m.question
    assert next_actor(m) is None


def test_no_se_puede_hablar_fuera_de_turno():
    """El orden del recorrido ES el argumento popperiano, no una preferencia."""
    m = _hasta_rondas()
    with pytest.raises(ImprovementError, match="le toca a MELCHIOR"):
        record_round(m, "BALTHASAR", "me adelanto")


def test_son_dos_vueltas_completas():
    """
    Una sola vuelta son tres opiniones en paralelo disfrazadas de debate: cada
    nodo ve el plan por primera vez y ninguno puede refutar al anterior.
    """
    m = _hasta_rondas()
    for _ in range(CIRCUITOS):
        for a in SECUENCIA:
            record_round(m, a, "x")
    assert len(m.rounds) == CIRCUITOS * 3
    assert {r.circuit for r in m.rounds} == {1, 2}


# ------------------------------------------------------------- los prompts

def test_balthasar_ve_lo_que_dijo_melchior():
    """
    Se pidió que Balthasar examine "el plan y lo que señaló Melchior". Es
    también lo único que hace útil el circuito: un crítico que no ve la
    crítica anterior no puede refutarla.
    """
    m = _hasta_rondas()
    record_round(m, "MELCHIOR", "OJO CON LA CACHÉ RANCIA")
    p = prompt_for(m, "BALTHASAR")
    assert "OJO CON LA CACHÉ RANCIA" in p
    assert "POPPERIANA" in p


def test_casper_recibe_las_tres_cosas_por_separado():
    m = _hasta_rondas()
    record_round(m, "MELCHIOR", "APORTE-MELCHIOR")
    record_round(m, "BALTHASAR", "APORTE-BALTHASAR")
    p = prompt_for(m, "CASPER")
    assert "APORTE-MELCHIOR" in p and "APORTE-BALTHASAR" in p
    assert "por separado" in p
    assert "AÑADE los temas nuevos" in p


def test_a_melchior_se_le_pide_el_plan_entero_no_un_resumen():
    """Quien lo lea después debe poder trabajar solo con su versión."""
    p = prompt_for(_hasta_rondas(), "MELCHIOR")
    assert "No resumas" in p and "íntegro" in p


# --------------------------------------------- la propuesta del usuario

def test_una_propuesta_del_usuario_recorre_lo_mismo():
    """
    "que deberá ser pasado a Melchior con el sistema de rondas, igual que
    cuando Naoko tiene una idea". Que venga de ti no la exime de la crítica.
    """
    m = start("usuario", "Quiero que el enjambre use tres rondas siempre")
    assert m.stage is Stage.IDEA
    user_decides(m, True)
    m.plan = "plan"
    user_decides(m, True)
    assert next_actor(m) == (1, "MELCHIOR")
    assert "el usuario" in prompt_for(m, "MELCHIOR")


def test_el_origen_se_declara_en_lo_que_ve_el_usuario():
    assert "idea propia de Naoko" in start("naoko", "x").render()
    assert "propuesta tuya" in start("usuario", "x").render()


def test_un_origen_inventado_se_rechaza():
    with pytest.raises(ImprovementError):
        start("melchior", "x")


def test_una_mejora_sin_enunciado_no_se_puede_evaluar():
    with pytest.raises(ImprovementError, match="enunciado"):
        start("naoko", "   ")


# ------------------------------------------------------------ narración

def test_naoko_es_expresa_en_lo_que_hace():
    """Se pidió ver cada paso mientras mejora, no un resultado al final."""
    m = _hasta_rondas()
    record_round(m, "MELCHIOR", "x")
    m.stage = Stage.EJECUTANDO
    m.execution_log = ["leo agents.py", "aplico el cambio", "corro los tests"]
    texto = m.render()
    assert "RECORRIDO POR EL ENJAMBRE" in texto
    assert "circuito 1 · MELCHIOR" in texto
    assert "aplico el cambio" in texto


# ---------------------------------------------------------- persistencia

@pytest.fixture
def log(tmp_path):
    return ImprovementLog(tmp_path / "brain.db")


def test_una_mejora_a_medias_sobrevive_al_reinicio(log):
    m = _hasta_rondas()
    record_round(m, "MELCHIOR", "aporte")
    log.save(m)

    recuperada = ImprovementLog(log.path).get(m.improvement_id)
    assert recuperada.stage is Stage.RONDA
    assert len(recuperada.rounds) == 1
    assert recuperada.rounds[0].agent == "MELCHIOR"
    assert next_actor(recuperada) == (1, "BALTHASAR")


def test_las_pendientes_de_decision_no_se_olvidan(log):
    a = start("naoko", "espera permiso")
    b = start("naoko", "descartada")
    user_decides(b, False)
    log.save(a)
    log.save(b)
    pendientes = [m.improvement_id for m in log.pending_user()]
    assert a.improvement_id in pendientes
    assert b.improvement_id not in pendientes


def test_el_payload_viaja_a_la_interfaz(log):
    import json
    m = _hasta_rondas()
    d = m.to_dict()
    assert json.loads(json.dumps(d))["stage"] == "ronda"
    assert "awaiting_user" in d and "question" in d


# ------------------------------------------------------------- cableado

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]


def test_naoko_tiene_las_dos_vias_separadas():
    """
    Reparar va sin consultar (§3.1); mejorar tiene compuertas. Si `draft_plan`
    o `execute_improvement` se llamaran solos, la instrucción "que me consulte"
    quedaría en el prompt y no en el código.
    """
    from source_helpers import code_of
    src = code_of(ROOT / "magi/modules/infrastructure/naoko.py")
    for metodo in ("propose_improvement", "draft_plan", "run_circuit",
                   "execute_improvement", "publish_improvement"):
        assert f"async def {metodo}" in src, f"falta {metodo}"
    # La reparación NO pasa por compuertas: sigue siendo automática.
    assert "VerifiedRepair" in src


def test_publicar_exige_la_aprobacion_explicita():
    """
    Subir a GitHub es visible para terceros y no se deshace con un `undo`.
    `publish_improvement` comprueba el estado, no se fía de quien la llame.
    """
    import inspect

    from magi.modules.infrastructure.naoko import NaokoAgent
    src = inspect.getsource(NaokoAgent.publish_improvement)
    assert "Stage.PUBLICADO" in src and "raise" in src


def test_publicar_no_sigue_con_la_compilacion_rota():
    import inspect

    from magi.modules.infrastructure.naoko import NaokoAgent
    src = inspect.getsource(NaokoAgent.publish_improvement)
    assert "_local_build" in src
    assert "no publico" in src


def test_el_kernel_expone_el_ciclo():
    from source_helpers import code_of
    src = code_of(ROOT / "magi/core/kernel.py")
    for h in ("naoko.improve.propose", "naoko.improve.decide",
              "naoko.improve.list"):
        assert h in src, f"{h} no está registrado"


def test_el_rol_creativo_prohibe_las_propuestas_de_adorno():
    """
    Una propuesta sin un antes y un después medibles es ruido, y el ruido hace
    que se dejen de leer las propuestas buenas.
    """
    from magi.modules.infrastructure.naoko import NaokoAgent
    rol = NaokoAgent.ROL_CREATIVO
    assert "MÁS EFICIENTE" in rol and "MÁS RÁPIDO" in rol
    assert "NO propongas" in rol
    assert "fichero y la línea" in rol
