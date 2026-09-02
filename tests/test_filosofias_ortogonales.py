"""
Las tres filosofías ortogonales, comprobadas donde se rompen.

QUÉ TIENE QUE PROBAR ESTE FICHERO
=================================
Tres cosas distintas, y la tercera es la que el usuario pidió por su nombre:

  1. REPARTO — las N variantes reciben N filosofías DISTINTAS, y eso llega
     de verdad al prompt de cada una. Sin esto, «ortogonal» es una palabra
     en un documento.
  2. DETECCIÓN — cuando las variantes colapsan en el mismo mecanismo, se
     dice. Un revisor que nunca falla no está revisando.
  3. QUE NO SE TRABE — la ronda termina aunque una variante reviente o
     tarde. El fan-out va por `asyncio.gather`, y ahí un cuelgue no da
     error: se queda esperando para siempre, que es peor.

Sobre los tiempos: aquí no hay ni un umbral absoluto. Se aprendió el
31-ago-2026 con `t_melchior_ms < 900`, que reventó en el runner de Windows
midiendo 4531 y resultó no valer tampoco en local. R12: contra un control,
o con un tope de seguridad que solo distingue «terminó» de «se colgó».
"""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import pytest
from swarm_helpers import (
    FAM_BALTHASAR,
    FAM_CASPER,
    FAM_MELCHIOR,
    GuionProvider,
    montar_registro,
)

from magi.core.blackboard import Blackboard
from magi.core.bus import BusEvent, MagiBus
from magi.core.providers.cloud import set_registry
from magi.core.store.state import TaskStore
from magi.modules.swarm import filosofias as filo
from magi.modules.swarm.filosofias import Filosofia
from magi.modules.swarm.orchestrator import SwarmOrchestrator
from magi.modules.swarm.parallel import (
    Proposal,
    format_variants_for_critic,
    generate_variants,
)

# Textos que un Melchior real produciría por cada filosofía. Cortos, pero con
# el vocabulario que de verdad delata a cada familia.
TEXTO_A = ("Cacheo de planos: si el plano NBG1 no cambio entre fotogramas, no "
           "se rasteriza. Reduce composite saltando scanlines identicas. "
           "Prediccion: composite baja >= 20 %.")
TEXTO_B = ("Subir solo el rectangulo sucio en vez del framebuffer entero, y "
           "mapear la memoria del rasterizador como textura con "
           "sceGxmMapMemory para eliminar la copia. Prediccion: upload baja "
           ">= 30 %.")
TEXTO_C = ("Partir el composite en dos bandas horizontales entre el nucleo 1 "
           "y el 2, con afinidad fija por hilo. Prediccion: dropped baja "
           ">= 50 %.")


class _AgenteFalso:
    """Melchior con guion: apunta el encargo que recibio cada variante."""

    def __init__(self, respuestas=None, tarda=0.0, revienta_en=()):
        self.seed = 7
        self.hedge = True
        self.family = "fam-melchior"
        self.rama = None
        self.rama_rol = ""
        self.rama_profundidad = 0
        self.encargos: list[str] = []
        self.respuestas = respuestas or [TEXTO_A, TEXTO_B, TEXTO_C]
        self.tarda = tarda
        self.revienta_en = set(revienta_en)

    def _variante(self) -> int:
        """
        Qué variante soy, leído de `rama` — NO de un contador propio.

        `generate_variants` hace `copy.copy(agent)` por variante, así que un
        `self._n = 0` le da a cada copia su propio contador y las tres se
        creen la variante 0. Ya me costó una vez, en las pruebas de la
        réplica: lo que se comparte entre copias son los objetos mutables
        (la lista `encargos`), nunca los enteros.
        """
        return int(str(self.rama).rsplit("/v", 1)[-1])

    async def generate_proposal(self, task_id, command, round_num,
                                last_proposal=None, last_critique=None,
                                engine="fast", narrative_style="tecnico",
                                use_tools=False, publicar=True):
        # `command` es lo que de verdad se le pidio a ESTA variante: es donde
        # tiene que haber aterrizado la filosofia asignada.
        i = self._variante()
        self.encargos.append((i, command))
        if i in self.revienta_en:
            raise RuntimeError(f"la variante {i} se cayo")
        if self.tarda:
            await asyncio.sleep(self.tarda)
        return {"content": self.respuestas[i % len(self.respuestas)],
                "provider": "falso", "family": self.family}


# --------------------------------------------------------------- 1. REPARTO

@pytest.mark.asyncio
async def test_cada_variante_recibe_una_filosofia_distinta():
    """
    LA COMPUERTA. Tres variantes, tres filosofias, y cada una en SU prompt.

    Antes esto lo decidia `seed + n*101`: tres redacciones del mismo ataque
    contaban como tres propuestas. La ronda gastaba tres compilaciones para
    medir una sola idea.
    """
    agente = _AgenteFalso()
    props = await generate_variants(
        agente, task_id="t", command="optimiza el emulador YabauseVita",
        round_num=1, n=3, repartir_filosofias=True)

    assert len(props) == 3
    asignadas = [p.filosofia for p in props]
    assert sorted(asignadas) == sorted(f.clave for f in filo.FILOSOFIAS), (
        f"no se repartieron las tres filosofias: {asignadas}")

    # Y que llegó al PROMPT, no solo al campo. Un reparto que no cruza al
    # encargo es contabilidad, no comportamiento.
    #
    # Se ordena por indice de variante: van por `gather` y el orden de
    # llegada no está garantizado. Un test que dependa de él pasa hoy y
    # falla el martes.
    por_variante = dict(agente.encargos)
    assert sorted(por_variante) == [0, 1, 2]
    metricas = [f.metrica for f in filo.FILOSOFIAS]
    for i, metrica in enumerate(metricas):
        encargo = por_variante[i]
        assert "TU FILOSOFIA EN ESTA RONDA" in encargo
        assert f"Atacas la metrica `{metrica}`" in encargo, (
            f"la variante {i} no recibio su metrica {metrica}")
        # Y sigue conteniendo el encargo original: la filosofia se suma, no
        # sustituye lo que el usuario pidio.
        assert "optimiza el emulador YabauseVita" in encargo
        # Y NO recibe las otras dos: si cada variante viera las tres, no
        # habria reparto, habria un menu.
        for j, ajena in enumerate(metricas):
            if j != i:
                assert f"Atacas la metrica `{ajena}`" not in encargo


@pytest.mark.asyncio
async def test_sin_reparto_las_variantes_van_desnudas():
    """El reparto es para rondas de optimizacion del emulador, no para todo.

    Pedir tres ataques ortogonales a «escribe un parser» produce dos
    variantes forzadas y una buena.
    """
    agente = _AgenteFalso()
    props = await generate_variants(
        agente, task_id="t", command="escribe un parser de ROM",
        round_num=1, n=3, repartir_filosofias=False)
    assert all(p.filosofia == "" for p in props)
    assert all("TU FILOSOFIA" not in e for _, e in agente.encargos)


def test_pertinente_separa_las_rondas_de_optimizacion():
    assert filo.pertinente("optimiza el rendimiento del emulador")
    assert filo.pertinente("sube los FPS de YabauseVita en Vita3K")
    # Encargo del emulador que NO es de rendimiento: R14 y la ronda 3 van de
    # por que NiGHTS no arranca, y eso no se ataca en tres filosofias.
    assert not filo.pertinente("averigua por que NiGHTS no llega al titulo")
    # Optimizacion que no es del emulador.
    assert not filo.pertinente("optimiza el arranque de la interfaz")


# ------------------------------------------------------------- 2. DETECCION

def test_se_detecta_cuando_las_tres_atacan_lo_mismo():
    """
    El fallo que la ortogonalidad existe para impedir: tres redacciones del
    mismo ataque. Si el revisor no lo caza, el reparto no sirve de nada.
    """
    tres_veces_lo_mismo = [
        "Cachear planos para no rasterizar composite de nuevo.",
        "Saltar scanlines identicas y recortar composite redundante.",
        "No dibujar capas ocultas: menos composite.",
    ]
    r = filo.revisar(tres_veces_lo_mismo)
    assert not r.ok
    assert r.colapsadas == ["hacer_menos"]
    assert "atacan lo mismo" in r.render()


def test_tres_ataques_distintos_pasan():
    r = filo.revisar([TEXTO_A, TEXTO_B, TEXTO_C])
    assert r.ok, r.render()
    assert r.cubiertas == 3
    assert not r.colapsadas
    assert "ortogonal" in r.render()


def test_una_variante_sin_mecanismo_no_se_clasifica_a_la_fuerza():
    """
    `None` es un resultado de primera clase. Forzar una etiqueta sobre un
    texto que no la tiene es lo que haria creer que el reparto funciono.
    """
    assert filo.clasificar("Habria que mejorar el rendimiento general.") is None
    r = filo.revisar([TEXTO_A, "propuesta vaga sin mecanismo", TEXTO_C])
    assert not r.ok
    assert r.sin_clasificar == [1]
    assert "no declaran mecanismo reconocible" in r.render()


# ------------------------------------- 2b. LOS CHOQUES CON §5.2 DE LA BITACORA

def test_las_reglas_de_la_bitacora_frenan_antes_de_compilar():
    """
    §6: «Si alguna choca con una regla de §5.2, se rechaza sin llegar a
    compilar». Compilar un .vpk y correrlo verificado cuesta un ciclo
    entero por propuesta; leer la regla cuesta cero.
    """
    # R6 — el camino de render es el 1,27 % del tiempo (A7).
    assert [r.clave for r in filo.choques(TEXTO_A)] == ["R6"]
    assert [r.clave for r in filo.choques(TEXTO_B)] == ["R6"]
    # R1 — ya existe SH2DynARM.
    jit = "Escribir un JIT nuevo de SH-2 optimizado para Cortex-A9."
    assert "R1" in [r.clave for r in filo.choques(jit)]
    # R15 — cambiar de interprete no es la palanca.
    interp = "Cambiar SH2Fast por SH2LRU para ganar velocidad."
    assert "R15" in [r.clave for r in filo.choques(interp)]
    # R14 — el disco de NiGHTS llega byte-perfecto.
    disco = "El disco de NiGHTS esta corrupto: volver a volcar el CHD."
    assert "R14" in [r.clave for r in filo.choques(disco)]


def test_las_reglas_no_disparan_con_mencionar_la_palabra():
    """
    La otra mitad, y la que decide si esto sobrevive: una regla que bloquea
    propuestas validas se desactiva sola a la tercera vez que estorba.

    Por eso cada regla exige VARIOS grupos de terminos a la vez. Nombrar
    `composite` para decir que NO se toca no es proponer tocarlo.
    """
    honesta = ("El camino de render es el 1,27 % del tiempo (A7), asi que no "
               "propongo tocar composite. En su lugar: instrumentar msh2 y "
               "ssh2 por separado en YabauseExec.")
    assert filo.choques(honesta) == []
    # Nombrar el dynarec que YA existe no es proponer uno nuevo (R1).
    assert filo.choques("Medir el coste por instruccion en SH2DynARM.") == []
    # Nombrar los interpretes para comparar sus tiempos no es cambiarlos (R15).
    assert filo.choques("SH2Fast reporta 51 ns/instr; SH2LRU no lo lleva.") == []


def test_la_suspension_viaja_en_el_prompt():
    """
    Hoy las tres estan suspendidas: R6 tapa A y B, y A9 tapa C porque su
    metrica `dropped` ni siquiera se imprime en el log. El prompt lo dice y
    dice que hacer en su lugar. Un mecanismo que produce tres propuestas
    prohibidas en silencio es peor que uno que no produce ninguna.
    """
    for i, f in enumerate(filo.FILOSOFIAS):
        txt = filo.para_la_variante(i)
        assert f.suspendida_por, (
            f"{f.clave} ya no esta suspendida: si la bitacora levanto la "
            f"regla, actualiza tambien este test y di con que medicion")
        assert f"SUSPENDIDA por {f.suspendida_por}" in txt
        assert f.levanta.split(".")[0][:20] in txt


# --------------------------------------------------------- 3. QUE NO SE TRABE

#: Tope de seguridad, no umbral de rendimiento.
#:
#: Solo distingue «termino» de «se quedo esperando para siempre». Por eso es
#: generoso: un runner cargado puede tardar diez veces mas que esta maquina
#: sin que nada este mal, y ese es justo el error que costo la v5.17.0 —
#: `t_melchior_ms < 900` medía el runner, no el codigo. Un tope de 20 s sobre
#: un trabajo de 0,3 s no puede confundir lentitud con cuelgue.
TOPE_ANTICUELGUE = 20.0


@pytest.mark.asyncio
async def test_una_variante_que_revienta_no_cuelga_la_ronda():
    """
    El fan-out va por `asyncio.gather`. Una variante que lanza excepcion se
    recoge; lo que no puede pasar es que se lleve por delante a las otras
    dos, porque entonces un fallo transitorio de un proveedor cuesta la
    ronda entera.
    """
    agente = _AgenteFalso(revienta_en=(1,))
    props = await asyncio.wait_for(
        generate_variants(agente, task_id="t",
                          command="optimiza el emulador YabauseVita",
                          round_num=1, n=3, repartir_filosofias=True),
        timeout=TOPE_ANTICUELGUE)
    assert len(props) == 2, "las hermanas de la que reventó no sobrevivieron"
    # Y las supervivientes conservan SU filosofia: la caida de una no
    # renumera a las otras.
    assert {p.filosofia for p in props} == {"hacer_menos", "repartir_mejor"}


@pytest.mark.asyncio
async def test_si_revientan_todas_falla_rapido_en_vez_de_esperar():
    """
    Fallar es aceptable; colgarse no. Sin la excepcion, el orquestador se
    quedaria esperando una lista que nunca llega.
    """
    agente = _AgenteFalso(revienta_en=(0, 1, 2))
    with pytest.raises(RuntimeError):
        await asyncio.wait_for(
            generate_variants(agente, task_id="t",
                              command="optimiza el emulador YabauseVita",
                              round_num=1, n=3, repartir_filosofias=True),
            timeout=TOPE_ANTICUELGUE)


@pytest.mark.asyncio
async def test_las_tres_esperas_se_solapan_y_la_ronda_termina():
    """
    Que no se trabe, medido contra un CONTROL en la misma corrida (R12).

    Tres variantes que tardan 0,4 s cada una: en serie son 1,2 s, en
    paralelo ~0,4. La comparacion es contra n=1, medido aqui mismo, asi que
    un runner lento escala los dos lados igual y la conclusion no cambia.
    """
    async def carrera(n):
        agente = _AgenteFalso(tarda=0.4)
        t0 = asyncio.get_running_loop().time()
        props = await asyncio.wait_for(
            generate_variants(agente, task_id="t",
                              command="optimiza el emulador YabauseVita",
                              round_num=1, n=n, repartir_filosofias=True),
            timeout=TOPE_ANTICUELGUE)
        return len(props), asyncio.get_running_loop().time() - t0

    n_una, t_una = await carrera(1)
    n_tres, t_tres = await carrera(3)
    assert (n_una, n_tres) == (1, 3)
    # Tres no puede costar como tres seguidas. El margen es la mitad del
    # ahorro esperado (0,8 s), no un numero de reloj.
    assert t_tres < t_una + 0.4, (
        f"las variantes no se solaparon: 1 tardo {t_una:.2f}s y 3 tardaron "
        f"{t_tres:.2f}s. En paralelo deberian costar casi lo mismo.")


# ------------------------------------------------- 4. LO QUE VE EL CRITICO

def _props(textos, con_filosofia=True):
    claves = [f.clave for f in filo.FILOSOFIAS]
    return [Proposal(content=t, variant=i, family="fam",
                     filosofia=claves[i % 3] if con_filosofia else "")
            for i, t in enumerate(textos)]


def test_el_critico_ve_la_filosofia_y_los_choques_pegados_a_cada_una():
    """
    Un choque con §5.2 que se lee tres pantallas mas abajo no cambia el
    juicio de la propuesta que lo comete. Va pegado.
    """
    txt = format_variants_for_critic(_props([TEXTO_A, TEXTO_B, TEXTO_C]))
    for f in filo.FILOSOFIAS:
        assert f.nombre in txt, f"falta la etiqueta de {f.clave}"

    # LAS TRES, no dos. Escribí este test esperando 2 —A y B— y el
    # comprobador dijo 3, con razón: la filosofía C mueve el `composite`
    # entre núcleos, y eso sigue siendo el camino de render que R6 tapa.
    #
    # Es exactamente lo que la ronda 0 concluyó midiendo: «las tres
    # filosofías de la §2 quedan en suspenso». Que la regla lo redescubra
    # sola desde el texto de las propuestas es la señal de que sirve.
    assert txt.count("[CHOCA CON R6]") == 3, (
        "las tres atacan el camino de render, que es el 1,27 % del tiempo")
    # El choque aparece ANTES del texto de su propuesta, no al final.
    assert txt.index("[CHOCA CON R6]") < txt.index(TEXTO_A[:40])


def test_el_critico_recibe_el_aviso_cuando_el_reparto_colapsa():
    colapsadas = ["Recortar composite redundante saltando scanlines.",
                  "Cachear planos para no rasterizar composite otra vez.",
                  "No dibujar capas ocultas: menos composite."]
    txt = format_variants_for_critic(_props(colapsadas))
    assert "[REPARTO]" in txt
    assert "atacan lo mismo" in txt

    # Y NO aparece cuando el reparto es correcto: un aviso que sale siempre
    # deja de leerse.
    limpio = format_variants_for_critic(_props([TEXTO_A, TEXTO_B, TEXTO_C]))
    assert "[REPARTO]" not in limpio

    # Ni cuando la ronda no reparte filosofias: ahi no hay nada que revisar.
    sin = format_variants_for_critic(
        _props(colapsadas, con_filosofia=False))
    assert "[REPARTO]" not in sin


# ---------------------------------------------- 5. LA RONDA REAL, DE VERDAD

@pytest.mark.asyncio
async def test_una_ronda_real_reparte_las_tres_y_no_se_traba(monkeypatch):
    """
    LA PRUEBA QUE IMPORTA: el orquestador de verdad, no `generate_variants`
    suelto.

    Todo lo de arriba puede pasar y MAGI seguir sin repartir nada, porque
    quien decide es el orquestador: mira el encargo del usuario, sube a tres
    variantes y enciende el reparto. Aquí corre la cadena entera — encargo →
    reparto → tres prompts distintos → propuesta fundida → Balthasar.

    El proveedor de Melchior responde SEGÚN LA MÉTRICA que le llega en el
    prompt. Si el reparto no cruzase, las tres caerían en la respuesta por
    defecto y el test lo diría.
    """
    monkeypatch.setenv("MAGI_ABANICO", "1")
    bus = MagiBus()
    posts: list[dict] = []

    async def on_post(event: BusEvent):
        if isinstance(event.payload, dict):
            posts.append(event.payload)

    bus.subscribe("AGENT_POST", on_post)

    melchior = GuionProvider(
        f"g4f-{FAM_MELCHIOR}", FAM_MELCHIOR,
        reglas=[("Atacas la metrica `composite`", TEXTO_A, 0.0),
                ("Atacas la metrica `upload`", TEXTO_B, 0.0),
                ("Atacas la metrica `dropped`", TEXTO_C, 0.0)],
        por_defecto=("SIN FILOSOFIA ASIGNADA", 0.0))
    balthasar = GuionProvider(
        f"g4f-{FAM_BALTHASAR}", FAM_BALTHASAR,
        por_defecto=("sin defectos en este eje. OBJECIONES: 0", 0.0))
    casper = GuionProvider(
        f"g4f-{FAM_CASPER}", FAM_CASPER,
        por_defecto=("veredicto. DECISION: APROBADA", 0.0))

    reg = montar_registro(melchior, balthasar, casper)
    await reg.probe_all()
    set_registry(reg)
    try:
        db = Path(tempfile.mkdtemp(prefix="magi-filo-")) / "t.db"
        swarm = SwarmOrchestrator(Blackboard(), bus, store=TaskStore(db))
        # El tope existe para que un cuelgue sea un FALLO y no una suite que
        # nunca termina. No es un umbral de rendimiento: ver TOPE_ANTICUELGUE.
        await asyncio.wait_for(
            swarm.submit_task("t-filo",
                              "optimiza el rendimiento del emulador "
                              "YabauseVita en Vita3K",
                              use_tools=False, max_rounds=1),
            timeout=TOPE_ANTICUELGUE)
        for _ in range(int(30.0 / 0.05)):
            await asyncio.sleep(0.05)
            if {"MELCHIOR", "BALTHASAR", "CASPER"} <= {
                    p.get("agent") for p in posts}:
                break
        await asyncio.sleep(0.3)
    finally:
        set_registry(None)

    # 1. LA RONDA TERMINO. Los tres nodos hablaron: no se trabó en el
    #    fan-out de tres, que es el cambio de esta versión.
    assert {"MELCHIOR", "BALTHASAR", "CASPER"} <= {
        p.get("agent") for p in posts}, "la ronda no llegó al final"

    # 2. TRES VARIANTES, NO DOS. Con las 2 de D6, «repartir mejor» no se
    #    exploraría nunca y el reparto sería ortogonal de boquilla.
    pedidos = [v for v in melchior.vistos if "TU FILOSOFIA EN ESTA RONDA" in v]
    assert len(pedidos) == 3, (
        f"el orquestador pidió {len(pedidos)} variantes con filosofía, no 3")

    # 3. TRES ATAQUES DISTINTOS, uno por métrica. Si el reparto no cruzara
    #    al prompt, el proveedor habría caído en su respuesta por defecto.
    for f in filo.FILOSOFIAS:
        assert sum(1 for v in pedidos
                   if f"Atacas la metrica `{f.metrica}`" in v) == 1, (
            f"la filosofía {f.clave} no se pidió exactamente una vez")
    assert not any("SIN FILOSOFIA ASIGNADA" in v for v in balthasar.vistos), (
        "alguna variante llegó sin filosofía: el reparto no cruzó al prompt")

    # 4. Y BALTHASAR LO VIO: las tres etiquetas y los choques con R6 en el
    #    texto que se le pasó a criticar. Un aviso que no llega al crítico no
    #    cambia ninguna decisión.
    critica = "\n".join(balthasar.vistos)
    for f in filo.FILOSOFIAS:
        assert f.nombre in critica, (
            f"Balthasar no vio la etiqueta de {f.clave}")
    assert "[CHOCA CON R6]" in critica, (
        "las tres atacan el camino de render y Balthasar no fue avisado: "
        "§6 dice que se rechazan SIN llegar a compilar")


def test_una_ronda_normal_no_reparte_filosofias():
    """El interruptor tiene que poder estar apagado, o no es un interruptor.

    Se comprueba en el sitio donde el orquestador decide, sin correr una
    ronda entera: lo que importa es la condición, no el camino.
    """
    assert not filo.pertinente("crea un juego de Tetris portable en un .exe")
    assert not filo.pertinente("arregla el test que falla en CI")


# ------------------------------------------------- 6. EL CONTRATO DEL TIPO

def test_toda_filosofia_esta_completa():
    """
    Lo que hace falta para que una filosofía sirva de algo, comprobado sobre
    el tipo.

    Escrita porque el trinquete de huérfanos señaló `Filosofia` como
    definición pública sin sitio de llamada. La salida no era esconderla
    haciéndola privada —eso apaga el trinquete y no arregla nada— sino
    preguntarse qué invariante suyo no estaba comprobado. Este: una cuarta
    filosofía añadida sin métrica, sin marcas o sin riesgo pasaría el resto
    de la suite y rompería el reparto en silencio.
    """
    assert len(FILOSOFIAS_ESPERADAS := {f.clave for f in filo.FILOSOFIAS}) == 3
    assert FILOSOFIAS_ESPERADAS == {"hacer_menos", "mover_menos",
                                    "repartir_mejor"}
    metricas = set()
    for f in filo.FILOSOFIAS:
        assert isinstance(f, Filosofia)
        assert f.metrica, f"{f.clave} no declara metrica: no seria falsable"
        assert f.marcas, f"{f.clave} no tiene marcas: no se podria clasificar"
        assert f.riesgo and f.lema and f.encargo, f"{f.clave} incompleta"
        # Una filosofia suspendida tiene que decir COMO se levanta, o la
        # suspension es permanente por olvido.
        if f.suspendida_por:
            assert f.levanta, f"{f.clave} suspendida sin salida documentada"
        metricas.add(f.metrica)
    # Metricas distintas: dos filosofias que se miden con el mismo contador
    # no son ortogonales, midan lo que midan.
    assert len(metricas) == 3, f"metricas repetidas: {metricas}"

    # Y `asignada` devuelve siempre una de ESTAS, nunca otra cosa.
    for i in range(len(filo.FILOSOFIAS) * 2):
        assert filo.asignada(i) in filo.FILOSOFIAS


def test_las_reglas_del_emulador_no_se_aplican_a_otras_rondas():
    """
    §5.2 es la bitacora DEL EMULADOR. Fuera de sus rondas no manda.

    Encontrado probando el codigo ya escrito: `choques` corria sobre toda
    propuesta de toda ronda, y R6 exige (composite|upload|display) mas un
    verbo de optimizar. Medido, disparaban las tres:

        «Optimizar el display de la pantalla del Tetris»   -> R6
        «Reducir el tiempo de upload de archivos»          -> R6
        «Acelerar el display de resultados en la web»      -> R6

    Balthasar habria recibido la orden de rechazar sin compilar una
    propuesta valida, citando una regla de otro proyecto. Una regla que
    bloquea trabajo bueno se desactiva sola a la tercera vez que estorba.
    """
    ajenas = ["Optimizar el display de la pantalla del Tetris.",
              "Reducir el tiempo de upload de archivos al servidor.",
              "Acelerar el display de resultados en la interfaz web."]
    # La funcion suelta si las marca: no se le ha quitado potencia.
    assert all(filo.choques(t) for t in ajenas)
    # Pero en una ronda que NO reparte filosofias no llegan al critico.
    txt = format_variants_for_critic(_props(ajenas, con_filosofia=False))
    assert "[CHOCA CON" not in txt, (
        "una regla del emulador se aplico a una ronda que no es del emulador")
    # Y en una ronda del emulador siguen llegando.
    txt_emu = format_variants_for_critic(_props([TEXTO_A, TEXTO_B, TEXTO_C]))
    assert "[CHOCA CON R6]" in txt_emu
