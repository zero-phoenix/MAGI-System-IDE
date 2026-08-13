import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """
    Aísla data_dir/workspace por test.

    Sin esto los tests escribirían en %LOCALAPPDATA%\\MagiSystem del usuario,
    que es exactamente el tipo de efecto colateral que v5.0.28 tenía por todas
    partes (magi_brain.db en el CWD, scratch en una ruta absoluta).
    """
    monkeypatch.setenv("MAGI_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("MAGI_WORKSPACE", str(tmp_path / "ws"))
    from magi.core import paths
    for fn in (paths.project_root, paths.data_dir, paths.workspace_dir):
        fn.cache_clear()
    yield
    for fn in (paths.project_root, paths.data_dir, paths.workspace_dir):
        fn.cache_clear()


@pytest.fixture
def anyio_backend():
    return "asyncio"


# ---------------------------------------------------------------------------
# EL ENTORNO NO SE HEREDA: SE DECIDE
# ---------------------------------------------------------------------------
#
# POR QUÉ EXISTE ESTO
# ===================
# Cinco veces seguidas —cinco— un test mío pasó en la máquina de desarrollo y
# falló en el CI por la misma razón: preguntaba a la máquina si había un
# navegador Camoufox descargado. Aquí sí lo hay (100 MB, bajados a mano). En el
# runner no. El test no comprobaba el código: describía la máquina.
#
# Lo intenté con disciplina y con documentación. La quinta ocurrencia la
# escribí EN EL MISMO COMMIT en el que documentaba que esto se repite. Ahí se
# acaba el argumento: la disciplina no es el mecanismo.
#
# El CI sí lo cazaba, las cinco veces. El problema es que lo cazaba SEIS
# MINUTOS DESPUÉS DE EMPUJAR, cuando ya no estás mirando. Un guardián que
# avisa tarde entrena a ignorarlo.
#
# QUÉ HACE
# ========
# Las funciones que leen el entorno dejan de tener respuesta por defecto
# durante los tests. No devuelven «no» (eso solo cambiaría de sitio el
# problema: pasaría a fallar en tu máquina y a pasar en el CI). **Se niegan a
# contestar** y explican qué escribir.
#
# Así, el test que dependía del entorno sin saberlo falla EN LOCAL, en el
# segundo en que lo escribes, con instrucciones. Y el que sí quiere cruzar
# la frontera lo dice en voz alta con la marca `frontera`.
#
# El coste de equivocarse en la dirección contraria también desaparece: no hay
# un valor por defecto que acertar, así que no hay defecto silencioso posible
# en ninguno de los dos sentidos.
#
# QUÉ SE GUARDA, Y POR QUÉ ESTAS Y NO OTRAS
# =========================================
# Solo las funciones que SALEN de la máquina: leer el disco a ver si hay un
# navegador, arrancarlo, pedir una página. No las que razonan sobre ellas.
#
# La distinción no es estética, y me costó un intento: la primera versión
# guardaba también `puede_abrir`, que es lógica pura sobre `disponible()` más
# el permiso vigente. Guardándola no había forma de probar esa lógica —el
# guardián tapaba justo lo que hay que comprobar—. Con `disponible` simulada,
# `puede_abrir` corre de verdad y es determinista. El guardián va en la
# frontera, no dentro.
_AMBIENTALES = (
    "disponible",             # ¿hay paquete y navegador descargado? -> disco
    "_prueba_arranque",       # arranca un navegador de verdad (10 s)
    "_lanzar_headless",       # arranca un navegador de verdad y navega
    "_cosechar_sin_navegador",  # sale a la red
)


def _se_niega(nombre: str):
    def _negativa(*_a, **_k):
        raise AssertionError(
            f"sesion_web.{nombre}() sale de la MÁQUINA, no prueba el código.\n"
            f"\n"
            f"Se ha llamado desde un test sin decir qué debe contestar. Eso es\n"
            f"justo el defecto que ha aparecido cinco veces: aquí hay navegador\n"
            f"descargado y en el CI no, así que el test pasaría en tu máquina y\n"
            f"fallaría al empujar.\n"
            f"\n"
            f"Elige una de las dos, y ninguna es más trabajo que depurar el CI:\n"
            f"\n"
            f"  1) Decide la respuesta (lo normal — quieres probar el CÓDIGO):\n"
            f"         monkeypatch.setattr(sesion_web, \"{nombre}\",\n"
            f"                             lambda *a, **k: ...)\n"
            f"     Mira la firma real: `disponible` y `_prueba_arranque`\n"
            f"     devuelven (bool, motivo); las dos cosechas, una lista de\n"
            f"     cookies (vacía = no consiguió nada).\n"
            f"\n"
            f"  2) Toca la frontera a propósito (raro):\n"
            f"         @pytest.mark.frontera\n"
            f"     O bien pruebas ESA función simulando más abajo (la red, el\n"
            f"     disco), o bien lees la máquina de verdad — y entonces el\n"
            f"     test no puede afirmar nada que dependa de lo instalado.\n"
            f"     Sin `if`: una aserción condicionada al entorno no comprueba\n"
            f"     nada en la mitad de las máquinas donde corre."
        )
    return _negativa


# ---------------------------------------------------------------------------
# EL CATÁLOGO DE PROVEEDORES NO ES UN HECHO: ES EL PARTE DEL DÍA
# ---------------------------------------------------------------------------
#
# CINCO VECES, Y TODAS DISTINTAS EN APARIENCIA
# ============================================
# 1. `test_una_familia_agotada_lo_dice_en_vez_de_fingir` usaba `claude` como
#    ejemplo de familia muerta. Se puso rojo **porque `claude` revivió**.
# 2. `test_el_orden_pone_delante_al_candidato_mas_rapido` usaba los dos
#    primeros candidatos de `gpt`. Se rompió cuando resultaron estar rotos:
#    `_ordered()` los filtró y el test del ORDEN falló sin que el orden
#    hubiera cambiado.
# 3. `test_la_latencia_es_una_media_movil`, igual.
# 4. `test_los_candidatos_rotos_no_se_intentan` recorría tres familias
#    escritas a mano y reventó con `ValueError: familia desconocida: qwen` el
#    día que esa familia se descartó por no haber forma de acceder a ella.
# 5. `test_ask_rota_cuando_la_familia_propia_responde_en_otro_idioma` fijaba
#    `assert familia == "gpt"`. Se rompió porque `gpt` salió de las
#    verificadas… precisamente porque su único candidato responde en chino,
#    que es lo que ese test persigue.
#
# Las cinco tienen la misma forma: **el test nombra un dato del catálogo**. Y
# el catálogo es una foto de qué servicios gratuitos están vivos hoy, que
# cambia cada semana. Un test que se rompe cuando el sistema MEJORA no está
# comprobando el sistema.
#
# QUÉ HACE ESTA PIEZA
# ===================
# Durante los tests, `FAMILY_SPECS`, `ROTOS`, `VERIFICADAS` y el reparto valen
# un **catálogo de laboratorio fijo**, escrito aquí abajo y que no cambia
# nunca. Los tests que necesitan el de verdad —«toda familia verificada tiene
# candidatos», «el JSON coincide con las constantes»— lo piden con la marca
# `catalogo_real`.
#
# Nota sobre el alcance: se parchea el módulo `g4f_backend`, que es de donde
# leen todos. Si alguien copia el valor a una variable en tiempo de import, se
# le escapa — por eso el catálogo de laboratorio se parece al real en FORMA
# (mismos nombres de familia usados por el enjambre, mismos proveedores
# reales), y solo difiere en que no se mueve.
# QUÉ SE CONGELA Y QUÉ NO — la distinción que costó un intento
# ============================================================
# La primera versión inventaba también los NOMBRES de familia, y saltó al
# instante: `ValueError: familia desconocida: razonamiento`. Otros consumidores
# —el panel de Configuración, el registro— enumeran las familias reales y
# construyen un `G4FProvider` por cada una; si el catálogo de laboratorio no
# las tiene todas, el sistema se contradice a sí mismo dentro del test.
#
# Y la lección es más general que el error: **los nombres de familia no son
# datos volátiles**. Son una decisión de diseño, cambian cuando alguien decide
# cambiarlos, y el enjambre los referencia por nombre. Lo que cambia solo, sin
# que nadie lo decida, es la SALUD de los proveedores: quién responde hoy,
# quién da 402, a quién se le ha caído el servidor.
#
# Así que se congela exactamente eso: cada familia real recibe dos candidatos
# fijos que siempre responden, más una familia agotada de laboratorio para los
# tests que la necesitan.
_CANDIDATOS_FIJOS = [("CohereForAI_C4AI_Command", "command-a-03-2025"),
                     ("Perplexity", "auto")]

#: Familia con un candidato que abre navegador y otro limpio, en ese orden.
#: Para los tests de ordenación, que antes usaban `deepseek` porque ese día
#: contenía Cloudflare. Aquí lo contiene siempre.
_FAMILIA_CON_NAVEGADOR = "_con_navegador"

#: Familia cuyos candidatos están todos en ROTOS. Para los tests de «lo dice
#: en vez de fingir», que antes usaban `claude` y se rompieron cuando `claude`
#: revivió.
_FAMILIA_AGOTADA = "_agotada"

_ROTOS_LABORATORIO = {
    "Claude": "DESCARTADO: exige tu cuenta",
    "LMArena": "DESCARTADO: exige tu cuenta",
}

_REPARTO_LABORATORIO = {
    "BALTHASAR": "claude", "CASPER": "gemini", "MELCHIOR": "command",
}


def _catalogo_de_laboratorio(reales: dict) -> dict:
    """Mismos nombres de familia que el real; candidatos fijos."""
    lab = {nombre: list(_CANDIDATOS_FIJOS) for nombre in reales}
    lab[_FAMILIA_AGOTADA] = [("Claude", None), ("LMArena", "claude-sonnet-4")]
    lab[_FAMILIA_CON_NAVEGADOR] = [("Cloudflare", "llama-3.3-70b"),
                                   ("CohereForAI_C4AI_Command", "command-a-03-2025")]
    return lab


@pytest.fixture(autouse=True)
def catalogo_congelado(request, monkeypatch):
    """
    Congela el catálogo salvo que el test pida el real con `catalogo_real`.

    Como el guardián de la frontera, no se importa el módulo si nadie lo ha
    cargado: `g4f_backend` arrastra g4f y `test_arranque_ligero` lo prohíbe.
    """
    if request.node.get_closest_marker("catalogo_real"):
        yield
        return

    modulo = sys.modules.get("magi.core.providers.backends.g4f_backend")
    if modulo is not None:
        lab = _catalogo_de_laboratorio(modulo.FAMILY_SPECS)
        monkeypatch.setattr(modulo, "FAMILY_SPECS", lab, raising=False)
        monkeypatch.setattr(modulo, "ROTOS", dict(_ROTOS_LABORATORIO),
                            raising=False)
        # Verificadas: todas las reales menos las dos de laboratorio, que no
        # son familias del sistema sino andamios para los tests.
        monkeypatch.setattr(
            modulo, "VERIFIED_FAMILIES",
            tuple(f for f in lab
                  if f not in (_FAMILIA_AGOTADA, _FAMILIA_CON_NAVEGADOR)),
            raising=False)
        monkeypatch.setattr(modulo, "DEFAULT_SWARM_FAMILIES",
                            dict(_REPARTO_LABORATORIO), raising=False)
    yield


@pytest.fixture(autouse=True)
def entorno_explicito(request, monkeypatch):
    """
    Corta el acceso al exterior salvo que el test lo pida por su nombre.

    No se importa `sesion_web` si nadie lo ha cargado: hacerlo metería
    `curl_cffi` y `playwright` en el arranque de CADA test y
    `test_arranque_ligero` —con razón— lo prohíbe.
    """
    if request.node.get_closest_marker("frontera"):
        yield
        return

    modulo = sys.modules.get("magi.core.sesion_web")
    if modulo is not None:
        for nombre in _AMBIENTALES:
            monkeypatch.setattr(modulo, nombre, _se_niega(nombre),
                                raising=False)
    yield
