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
    CIRCUITOS, GATES, SECUENCIA, TRANSICIONES, ImprovementError,
    ImprovementLog, Stage, advance, fail, next_actor, prompt_for,
    record_round, start, user_decides,
)


def _hasta_rondas(origin="naoko"):
    """
    Lleva una mejora hasta la fase de rondas.

    Pasa por REDACTANDO porque `user_decides` ya no salta directamente a la
    compuerta siguiente: entre la decisión y la compuerta hay un estado de
    TRABAJO, para que la pregunta «¿lo paso al enjambre?» no se presente con
    el plan todavía vacío.
    """
    m = start(origin, "Cachear el catálogo de herramientas por dominio")
    user_decides(m, True)                      # sí, redacta el plan
    assert m.stage is Stage.REDACTANDO
    m.plan = "1. Medir. 2. Cachear. 3. Comprobar que no se sirve rancio."
    advance(m, Stage.PLAN_BORRADOR)            # Naoko termina de redactar
    user_decides(m, True)                      # sí, pásalo al enjambre
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
    advance(m, Stage.PLAN_BORRADOR)
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
    advance(m, Stage.PLAN_BORRADOR)
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


# ============================================================================
# Regresiones de la revisión adversarial. Todas estaban en VERDE: los 28 tests
# anteriores pasaban mientras el ciclo marcaba «publicado» sin publicar nada.
# ============================================================================

def test_la_compuerta_del_plan_no_aparece_con_el_plan_vacio():
    """
    `user_decides` avanzaba directamente al estado siguiente, así que la
    compuerta «¿lo paso al enjambre?» se presentaba con plan == "" mientras
    Naoko aún lo escribía. Aprobar ahí circulaba un plan vacío por seis
    llamadas a la nube.
    """
    m = start("naoko", "x")
    user_decides(m, True)
    assert m.stage is Stage.REDACTANDO, "debe ir a un estado de TRABAJO"
    assert not m.awaiting_user, "no puede pedir decisión mientras escribe"


def test_no_se_marca_publicado_antes_de_publicar():
    """
    EL FALLO MÁS GRAVE. Aprobar la publicación ponía la fila en `publicado`
    —que es terminal— antes de intentar nada. Si la compilación fallaba, ahí
    se quedaba: ni reintento ni descarte.
    """
    m = start("naoko", "x")
    m.stage = Stage.ESPERANDO_PUBLICACION
    user_decides(m, True)
    assert m.stage is Stage.PUBLICANDO, "publicar es un TRABAJO, no un hecho"
    assert m.stage is not Stage.PUBLICADO


def test_solo_se_llega_a_publicado_desde_publicando():
    for etapa in Stage:
        if etapa is Stage.PUBLICANDO:
            continue
        assert Stage.PUBLICADO not in TRANSICIONES.get(etapa, set()), \
            f"se puede llegar a PUBLICADO desde {etapa.value}"


def test_una_fase_rota_deja_el_ciclo_recuperable():
    """
    Antes una excepción dejaba `ronda` o `ejecutando`, que no son compuertas:
    la única salida era editar SQLite.
    """
    m = start("naoko", "x")
    user_decides(m, True)
    advance(m, Stage.PLAN_BORRADOR)
    user_decides(m, True)
    assert m.stage is Stage.RONDA

    fail(m, "el proveedor se cayó")
    assert m.stage is Stage.FALLIDA
    assert m.awaiting_user, "un fallo tiene que poder resolverse"
    assert "el proveedor se cayó" in m.question


def test_reintentar_vuelve_a_la_compuerta_de_la_que_salio():
    """Reintentar es volver a decidir con lo que ya se sabe, no repetir a ciegas."""
    m = start("naoko", "x")
    user_decides(m, True)
    advance(m, Stage.PLAN_BORRADOR)
    user_decides(m, True)          # -> RONDA
    fail(m, "boom")
    user_decides(m, True)          # reintentar
    assert m.stage is Stage.PLAN_BORRADOR


def test_se_puede_descartar_una_fallida():
    m = start("naoko", "x")
    user_decides(m, True)
    fail(m, "boom")
    user_decides(m, False)
    assert m.stage is Stage.DESCARTADA


def test_solo_las_fases_de_trabajo_pueden_fallar():
    m = start("naoko", "x")
    with pytest.raises(ImprovementError, match="no es una fase de trabajo"):
        fail(m, "no tiene sentido")


def test_el_motivo_del_fallo_sobrevive_al_reinicio(tmp_path):
    from magi.modules.infrastructure.improvement import ImprovementLog
    log = ImprovementLog(tmp_path / "b.db")
    m = start("naoko", "x")
    user_decides(m, True)
    fail(m, "se agotaron los proveedores gratuitos")
    log.save(m)
    r = ImprovementLog(log.path).get(m.improvement_id)
    assert r.stage is Stage.FALLIDA
    assert "proveedores gratuitos" in r.failure
    assert r.failed_from == Stage.IDEA.value


def test_naoko_publica_de_verdad_cuando_se_le_autoriza():
    """
    `_git_push` solo hacía un commit local y decía "No hago push ni tag
    automáticos", mientras la narración afirmaba que la etiqueta había
    disparado el workflow de release. El código y el relato decían cosas
    distintas.
    """
    import inspect

    from magi.modules.infrastructure.naoko import NaokoAgent
    src = inspect.getsource(NaokoAgent._git_push)
    assert "publish: bool = False" in src, "falta la vía de publicación"
    assert '"git", "push", "origin"' in src, "sigue sin subir nada"
    assert '"git", "tag"' in src, "sin etiqueta no hay release ni binario"


def test_la_autocorreccion_no_publica_sola():
    """
    La reparación automática commitea y para. Publicar es siempre del usuario,
    aunque el cambio sea un arreglo.
    """
    import inspect

    from magi.modules.infrastructure.naoko import NaokoAgent
    # La reparación vive en `_handle_error_event`: es la que llama a
    # `_git_push` tras verificar, y tiene que hacerlo SIN `publish=True`.
    src = inspect.getsource(NaokoAgent._handle_error_event)
    assert "_git_push(" in src, "la reparación ya no commitea"
    assert "publish=True" not in src, \
        "la autocorrección no puede publicar por su cuenta"


def test_la_guarda_de_publicar_no_esta_invertida():
    """
    Era `if m.stage is not Stage.PUBLICADO: raise`, o sea que exigía estar ya
    publicado para poder publicar: no protegía nada y el test que la vigilaba
    pasaba igual porque solo buscaba las cadenas "Stage.PUBLICADO" y "raise".
    """
    import inspect

    from magi.modules.infrastructure.naoko import NaokoAgent
    src = inspect.getsource(NaokoAgent.publish_improvement)
    assert "is not Stage.PUBLICANDO" in src
    assert "is not Stage.PUBLICADO" not in src


# --------------------------------------------------------- release honesto

def test_las_notas_de_la_release_no_estan_congeladas_en_el_workflow():
    """
    El cuerpo de la release estaba ESCRITO A MANO dentro de `release.yml` con
    las novedades de v5.0.28. Cada versión nueva habría publicado la misma
    lista, describiendo cosas que ya no son las novedades. Una release que
    miente sobre lo que trae es peor que una sin notas.
    """
    import yaml
    wf = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8"))
    pasos = wf["jobs"]["build"]["steps"]
    crear = next(s for s in pasos if s.get("name") == "Create Release")
    assert "body" not in crear["with"], "el cuerpo vuelve a estar incrustado"
    assert crear["with"].get("body_path") == "RELEASE_NOTES.md"
    assert (ROOT / "RELEASE_NOTES.md").exists()


def test_la_release_adjunta_el_exe_dentro_de_un_zip():
    import yaml
    wf = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8"))
    pasos = wf["jobs"]["build"]["steps"]
    comprimir = next(s for s in pasos if s.get("name") == "Zip Release")
    assert ".exe" in comprimir["run"] and ".zip" in comprimir["run"]
    crear = next(s for s in pasos if s.get("name") == "Create Release")
    assert crear["with"]["files"].endswith(".zip")


def test_no_hay_release_sin_tests_verdes():
    import yaml
    wf = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8"))
    assert wf["jobs"]["build"].get("needs") == "test", \
        "el build tiene que depender de los tests"
