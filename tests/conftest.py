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
