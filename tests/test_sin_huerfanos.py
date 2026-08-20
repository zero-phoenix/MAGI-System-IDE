"""
«Conecta o borra» deja de ser una norma y pasa a ser un trinquete.

LA LECCIÓN Nº2, POR ESCRITO Y CON MECANISMO
===========================================
El README lo dice: *conecta o borra*. Era una norma —algo que se cumple
mientras alguien se acuerde— y el historial demuestra que no basta. Aparecieron
una detrás de otra:

  · `MetricsCollector`, construido, probado y enganchado al bus, sin nadie que
    llamara a `obs.metrics`. El panel de salud no existía.
  · `eval.run` y `naoko.self_improve`: motor completo, ningún botón.
  · `record_usage()` nunca llamado, con `token_ledger` vacía desde su creación.
  · La tabla `task_event`, creada en la migración 0001 y sin una sola escritura
    hasta cuatro fases más tarde.

Ninguno rompía un test. El sistema funcionaba: solo tenía piezas que no hacían
nada. La única forma de encontrarlas fue que alguien se sentara a auditar a
mano, y eso no escala ni se repite.

QUÉ HACE ESTE TEST, Y QUÉ NO
============================
NO exige cero. Hoy hay 108, y ponerlo en cero significaría o borrar módulos
enteros de golpe o llenar la lista de excepciones hasta vaciarla de sentido.

Lo que hace es impedir que la cifra SUBA. Es un trinquete: el número puede
bajar cuando alguien conecte o retire una pieza, y bajarlo actualiza el techo.
Lo que no puede es crecer sin que se vea, que es exactamente como llegó a 108.

Mismo criterio que ya se aplica al lint en el CI: la deuda existente se publica
y se salda cuando toca; lo que no se admite es que aumente en silencio.

SOBRE LOS FALSOS POSITIVOS
==========================
Parte de los 108 son tipos internos con nombre público —un `dataclass` que
devuelve una función del mismo módulo y que nadie nombra desde fuera—. No son
código muerto: son nombres que deberían empezar por `_`. Que aparezcan aquí es
correcto y además señala algo real, aunque la acción no sea borrarlos.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SCRIPT = RAIZ / "scripts" / "huerfanos.py"

#: techo actual. Solo puede bajar. Si bajas, baja también este número en el
#: mismo commit: es la mitad del trinquete que hace que sirva de algo.
#:
#: 80 desde el 2026-08-16 (recalibrado): el conteo local daba 70 porque el
#: indice de uso leía .venv-lock/site-packages y otros directorios que no
#: existen en un checkout limpio — nombres comunes contaban como "uso" sin
#: que nadie hubiera conectado nada. El CI tenía razón. Arreglado en
#: scripts/huerfanos.py (EXCLUIDOS) y recalibrado a lo que de verdad hay.
# 94 desde el 2026-08-16: archivado providers/selector.py en _attic (mock
# muerto de una arquitectura anterior: importaba ProviderDef y get_provider,
# que ya no existen). 95 desde el 2026-08-13: bajó de 107 al cablear la sonda —`LlmDeSonda`,
# `candidatos_para_sondear`, `medias_por_familia`, `refrescar_si_toca`— que
# llevaba semanas construida y sin llamar. El trinquete lo detectó y exigió
# consolidarlo, que es la mitad del mecanismo que se olvida siempre: si el
# techo no baja cuando baja el conteo, el margen ganado se puede volver a
# gastar sin que nadie se entere.
TECHO = 80

#: techos por paquete (2026-08-16, tras archivar 6 paquetes sin importadores:
#: device, fabrication, vision, reasoning, os_portable, capabilities -> _attic). El total puede
#: cumplir y aun así acumularse todo en un sitio: el desglose dice DÓNDE
#: crece el andamiaje sin conectar, que es lo accionable. Misma regla que el
#: techo global: solo pueden bajar, y en el mismo commit que la baja real.
TECHOS_POR_PAQUETE = {"magi/modules": 62, "magi/core": 18}


def _cuenta() -> int:
    r = subprocess.run([sys.executable, str(SCRIPT), "--conteo"],
                       capture_output=True, text=True, timeout=600, cwd=str(RAIZ))
    if r.returncode != 0:
        pytest.fail(f"scripts/huerfanos.py falló:\n{r.stderr[-800:]}")
    return int(r.stdout.strip())


def _por_paquete() -> dict[str, int]:
    r = subprocess.run([sys.executable, str(SCRIPT), "--json"],
                       capture_output=True, text=True, timeout=600, cwd=str(RAIZ))
    if r.returncode != 0:
        pytest.fail(f"scripts/huerfanos.py falló:\n{r.stderr[-800:]}")
    import json
    conteo: dict[str, int] = {}
    for item in json.loads(r.stdout):
        partes = item["sitios"][0].replace("\\", "/").split("/")
        paquete = "/".join(partes[:2]) if partes[0] == "magi" and len(partes) > 2 else partes[0]
        conteo[paquete] = conteo.get(paquete, 0) + 1
    return conteo


def test_el_codigo_publico_sin_llamar_no_crece():
    n = _cuenta()
    assert n <= TECHO, (
        f"Hay {n} definiciones públicas sin sitio de llamada; el techo es "
        f"{TECHO}. Algo nuevo se ha quedado sin conectar.\n\n"
        f"Ejecuta `python scripts/huerfanos.py` para ver cuáles. Cada una es "
        f"una de tres cosas: una capacidad a la que le falta el cable "
        f"(CONÉCTALA), andamiaje que sobra (BÓRRALO o llévalo a magi/_attic/), "
        f"o un punto de entrada legítimo (añádelo a ENTRADAS en el script, con "
        f"el motivo escrito).")


def test_el_andamiaje_no_se_acumula_en_un_solo_paquete():
    conteo = _por_paquete()
    for paquete, techo in TECHOS_POR_PAQUETE.items():
        n = conteo.get(paquete, 0)
        assert n <= techo, (
            f"`{paquete}` tiene {n} definiciones públicas sin llamar y su "
            f"techo es {techo}. El total puede cumplir y aun así acumularse "
            f"todo en un sitio: este desglose existe para que el crecimiento "
            f"tenga dirección visible.\n\n"
            f"Reparto actual: {conteo}. Si consolidaste huérfanos de este "
            f"paquete, baja su techo en este mismo commit.")


def test_si_baja_el_conteo_se_baja_el_techo():
    """
    Un trinquete que no se aprieta no es un trinquete.

    Si alguien conecta o retira piezas y el techo se queda arriba, el margen
    recuperado se puede volver a gastar sin que nada avise. Este test obliga a
    consolidar la mejora en el mismo commit que la produce.
    """
    n = _cuenta()
    assert n >= TECHO - 5, (
        f"El conteo ha bajado a {n} y TECHO sigue en {TECHO}. Enhorabuena: "
        f"baja TECHO a {n} en tests/test_sin_huerfanos.py para consolidarlo. "
        f"Si no, el margen que acabas de ganar se puede volver a gastar sin "
        f"que nadie se entere.")


def test_el_script_explica_que_hacer_y_no_solo_que_pasa():
    """
    Un informe que dice «108 huérfanos» y nada más no ayuda a nadie.

    El proyecto lleva media docena de sesiones quitando cifras sin contexto;
    esta no va a ser una más. El informe tiene que decir qué son las tres
    salidas posibles.
    """
    # CODIFICACIÓN FIJADA EN LOS DOS EXTREMOS, y no por manía.
    #
    # Con `text=True` a secas, Python descodifica la salida del hijo con
    # `locale.getpreferredencoding()` — cp1252 en este equipo, UTF-8 en el CI
    # de Ubuntu. El hijo, por su parte, escribe en lo que le diga el entorno.
    # Si los dos no coinciden, «CONÉCTALA» llega convertida en ruido y este
    # test falla por una razón que no tiene NADA que ver con lo que comprueba.
    #
    # Pasó tal cual el 2026-08-20: bastó lanzar la suite con
    # PYTHONIOENCODING=utf-8 en el shell para que fallara, mientras el código
    # que audita estaba perfectamente. Un test que depende del entorno de quien
    # lo lanza no es una red de seguridad: es una fuente de ruido que enseña a
    # ignorar los fallos rojos.
    entorno = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, str(SCRIPT)],
                       capture_output=True, timeout=600, cwd=str(RAIZ),
                       env=entorno, encoding="utf-8", errors="replace")
    assert r.returncode == 0
    for pista in ("CONÉCTALA", "BÓRRALO", "_attic", "ENTRADAS"):
        assert pista in r.stdout, f"el informe debería explicar «{pista}»"
