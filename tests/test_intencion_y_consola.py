"""
Tests de los fallos vistos en el registro del usuario.

El más grave no era la lentitud: era que su pregunta se tragó como si fuera la
aprobación de otra tarea, y nunca se contestó.
"""
from __future__ import annotations

import pytest

from magi.core import consola
from magi.modules.swarm import intencion


# ============================================ absorción de peticiones nuevas

def test_la_pregunta_exacta_del_usuario_no_es_una_aprobacion():
    """
    La regresión literal:

        root@system:~# dime por que la soledad duele
        [SWARM] task_84hkn8xp se trata como respuesta a task_29ceb5d6
        [SWARM] Feedback del usuario recibido. Reanudando debate (Ronda 2)

    Una pregunta nueva se gastó como comentario a una propuesta pendiente.
    """
    assert intencion.es_respuesta_a_aprobacion("dime por que la soledad duele") is False


@pytest.mark.parametrize("texto", [
    "dime por que la soledad duele",
    "explicame como funciona un dynarec",
    "hazme un juego de tetris en python",
    "crea un script que ordene fotos por fecha",
    "¿cual es la capital de Mongolia?",
    "que es la entropia de Shannon",
    "escribe un correo para mi jefe pidiendo vacaciones",
    "analiza el rendimiento de este emulador de PSP y dame alternativas",
])
def test_las_peticiones_nuevas_abren_su_propia_tarea(texto):
    assert intencion.es_respuesta_a_aprobacion(texto) is False, texto


@pytest.mark.parametrize("texto", [
    "si", "sí", "ok", "vale", "apruebo", "adelante", "dale", "perfecto",
    "no", "rechazo", "cancela", "mal",
    "cambia el nombre de la funcion",
    "quita la dependencia de requests",
    "añade manejo de errores",
    "mejor usa sqlite en vez de json",
    "revisa la propuesta otra vez",
])
def test_las_respuestas_de_verdad_si_se_absorben(texto):
    assert intencion.es_respuesta_a_aprobacion(texto) is True, texto


# ================================================== aprobación por subcadena

@pytest.mark.parametrize("texto", [
    "siempre falla en el mismo punto",
    "el analisis no me convence",
    "sigue asi de lento",
    "no, no apruebo",
    "okupa el disco entero",
])
def test_no_aprueba_por_accidente(texto):
    """
    Se comprobaba con `any(w in command.lower() for w in ["si", "ok", ...])`,
    o sea por SUBCADENA. El «si» de «siempre» o de «análisis» daba la tarea por
    aprobada, la cerraba Y disparaba la ejecución automática de sus bloques de
    código en la máquina del usuario.
    """
    assert intencion.aprueba(texto) is False, texto


@pytest.mark.parametrize("texto", ["si", "Sí", "SÍ", "ok", "apruebo",
                                   "vale, adelante", "perfecto, ejecuta"])
def test_si_aprueba_cuando_toca(texto):
    assert intencion.aprueba(texto) is True, texto


def test_un_rechazo_gana_a_una_aprobacion_en_la_misma_frase():
    assert intencion.aprueba("no, mejor no lo apruebes") is False


def test_texto_vacio_no_decide_nada():
    assert intencion.aprueba("") is False
    assert intencion.es_respuesta_a_aprobacion("") is False


# ================================================================== consola

def test_la_consola_queda_en_utf8_y_no_puede_lanzar():
    """
    'charmap' codec can't encode characters in position 99-110 — eso abortaba
    el streaming a mitad de respuesta y forzaba repetir la llamada entera. En
    un proyecto que habla español no era un caso raro: era el caso normal.
    """
    consola.configurar()
    assert consola.es_segura() is True


def test_escribir_acentos_no_lanza(capsys):
    consola.configurar()
    texto = "¿Por qué la filosofía es la madre de todas las ciencias? — ñ á é í ó ú"
    print(texto)          # antes: UnicodeEncodeError en consola cp1252
    assert texto.split()[0] in capsys.readouterr().out


def test_configurar_es_idempotente():
    a = consola.configurar()
    b = consola.configurar()
    assert isinstance(a, dict) and isinstance(b, dict)
    assert consola.es_segura() is True


def test_el_estado_se_puede_consultar():
    consola.configurar()
    e = consola.estado()
    assert "stdout" in e and "stderr" in e


# ======================================================= familias del enjambre

def test_los_nodos_ya_no_llevan_familias_muertas_cableadas():
    """
    `family = "deepseek"` / `"claude"` / `"qwen"` estaba fijo en las clases.
    Al reverificar el catálogo esas tres familias se quedaron sin ningún
    candidato vivo, se actualizó DEFAULT_SWARM_FAMILIES y a los agentes NO les
    llegó: cada ronda gastaba seis intentos condenados antes de acertar.
    """
    from magi.core.bus import MagiBus
    from magi.core.blackboard import Blackboard
    from magi.core.providers.backends.g4f_backend import (
        DEFAULT_SWARM_FAMILIES, VERIFIED_FAMILIES,
    )
    from magi.modules.swarm.agents import (
        MelchiorAgent, BalthasarAgent, CasperAgent,
    )

    bb, bus = Blackboard(), MagiBus()
    for cls, rol in ((MelchiorAgent, "MELCHIOR"),
                     (BalthasarAgent, "BALTHASAR"),
                     (CasperAgent, "CASPER")):
        a = cls(bb, bus)
        assert a.family == DEFAULT_SWARM_FAMILIES[rol], rol
        assert a.family in VERIFIED_FAMILIES, (
            f"{rol} apunta a {a.family}, que no está verificada")
        assert a.provider == a.family, (
            f"{rol}: el texto del log dice '{a.provider}' y de verdad usa "
            f"'{a.family}'")


def test_los_tres_nodos_siguen_en_familias_distintas():
    from magi.core.providers.backends.g4f_backend import DEFAULT_SWARM_FAMILIES
    fams = list(DEFAULT_SWARM_FAMILIES.values())
    assert len(set(fams)) == len(fams), (
        "el crítico tiene que tener sesgos distintos al proponente (§1.1)")


# ============================================== candidatos rotos del catálogo

def test_los_candidatos_rotos_no_se_intentan():
    """
    Seis llamadas condenadas por ronda en el registro del usuario: PhindAi por
    incompatibilidad de curl_cffi, Claude por browser_cookie3, LMArena por
    fichero de auth, Cloudflare por abrir navegador.
    """
    pytest.importorskip("g4f.Provider")
    from magi.core.providers.backends.g4f_backend import G4FProvider, ROTOS

    # Se recorren TODAS las familias del catálogo, no tres elegidas a mano.
    #
    # Antes eran ("deepseek", "claude", "qwen") y el test reventó con
    # `ValueError: familia desconocida: qwen` el día que se descartó esa
    # familia — porque su único proveedor devolvía `success=false` y no había
    # forma de acceder. Un test que se rompe cuando el catálogo se LIMPIA está
    # nombrando datos en vez de comprobar una propiedad.
    #
    # La propiedad es: ninguna familia, ninguna, ofrece un candidato roto.
    from magi.core.providers.backends.g4f_backend import FAMILY_SPECS

    for familia in FAMILY_SPECS:
        p = G4FProvider(family=familia)
        for nombre, _ in p._ordered():
            assert nombre not in ROTOS, (
                f"{familia}: {nombre} está roto y aun así se intenta")


def test_una_familia_agotada_lo_dice_en_vez_de_fingir(monkeypatch):
    """
    LA FAMILIA SE FABRICA AQUÍ, Y ESA ES LA PARTE IMPORTANTE.

    La primera versión usaba `claude` como ejemplo de familia agotada, porque
    ese día lo estaba. El 2026-08-13 dejó de estarlo —Perplexity sirve
    claude45sonnet sin cuenta— y el test se puso rojo sin que el código hubiera
    cambiado: describía el catálogo, no el comportamiento.

    Un test que se rompe cuando algo MEJORA está mal escrito. Aquí la familia
    agotada se construye a mano, así que sigue diciendo lo mismo aunque
    revivan todos los proveedores del mundo.
    """
    pytest.importorskip("g4f.Provider")
    from magi.core.providers.backends import g4f_backend as g

    monkeypatch.setitem(g.FAMILY_SPECS, "_agotada_de_prueba",
                        [("Claude", None), ("LMArena", "claude-sonnet-4")])

    p = g.G4FProvider(family="_agotada_de_prueba")
    assert p._ordered() == [], "todos sus candidatos están en ROTOS"
    motivos = p.motivos_descartados()
    assert "Claude" in motivos and "LMArena" in motivos
    assert all(m for m in motivos.values()), "cada descarte debe llevar motivo"


def test_las_familias_verificadas_si_tienen_candidatos():
    pytest.importorskip("g4f.Provider")
    from magi.core.providers.backends.g4f_backend import (
        G4FProvider, VERIFIED_FAMILIES,
    )
    for f in VERIFIED_FAMILIES:
        assert G4FProvider(family=f)._ordered(), f"{f} se quedó sin candidatos"
