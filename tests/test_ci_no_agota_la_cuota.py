"""
El CI estaba diseñado para agotar la cuota. Ahora hay quien lo vigile.

QUÉ PASÓ
========
El 2026-08-13 el CI se paró en seco: los seis jobs fallando en 2 segundos, sin
runner asignado y con cero pasos. La anotación de GitHub, literal:

    "The job was not started because recent account payments have failed or
     your spending limit needs to be increased."

Este repositorio es PRIVADO, así que los minutos de Actions se pagan. Medido
sobre la última corrida verde:

    test (windows-latest, 3.11)   9,2 min x2 = 18,4 facturables
    test (windows-latest, 3.10)   7,0 min x2 = 14,0
    test (ubuntu-latest, 3.11)    6,9 min x1 =  6,9
    test (ubuntu-latest, 3.10)    6,1 min x1 =  6,1
    gui + lint                                  0,9
    ------------------------------------------------
    TOTAL                                      46,3 min POR PUSH

Con 2000 minutos al mes son 43 pushes. En una sesión de trabajo se hacen seis.

LO QUE ESTE FICHERO IMPIDE
==========================
Que vuelva a crecer sin que nadie lo decida. No comprueba minutos —eso solo lo
sabe GitHub— sino las dos decisiones que los multiplican: cuántos jobs de
Windows hay (cuestan el doble) y si los tests que compilan un .exe se ejecutan
en cada push.

Y comprueba lo contrario también: que esos tests lentos NO hayan desaparecido.
Quitarlos del CI de cada push está bien; quitarlos de todas partes sería verde
sin comprobar nada, que es peor que rojo.
"""
from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

RAIZ = pathlib.Path(__file__).resolve().parents[1]
CI = RAIZ / ".github/workflows/ci.yml"
RELEASE = RAIZ / ".github/workflows/release.yml"


def _ci() -> dict:
    return yaml.safe_load(CI.read_text(encoding="utf-8"))


#: Windows cuesta x2 y macOS x10. Uno solo basta para la paridad de rutas.
MAX_JOBS_WINDOWS = 1


def test_como_mucho_un_job_de_windows_en_la_matriz():
    """
    Windows factura el DOBLE de minutos que Linux. Había dos jobs de Windows y
    entre los dos se llevaban 32 de los 46 minutos por push — el 70 %.

    El segundo no aportaba información: las diferencias entre Python 3.10 y
    3.11 ya las cubre la matriz de Ubuntu, y la paridad de rutas se comprueba
    igual con un job que con dos.
    """
    matriz = _ci()["jobs"]["test"]["strategy"]["matrix"]
    combinaciones = matriz.get("include") or []
    assert combinaciones, (
        "la matriz volvió a la forma `os: [...] x python: [...]`, que es el "
        "producto cartesiano y por eso salían cuatro jobs. Usa `include` para "
        "elegir las combinaciones una a una")

    windows = [c for c in combinaciones if "windows" in str(c.get("os", ""))]
    assert len(windows) <= MAX_JOBS_WINDOWS, (
        f"{len(windows)} jobs de Windows en la matriz. Cada uno cuesta el "
        f"DOBLE de minutos que uno de Linux, y este repositorio es privado: "
        f"los minutos se pagan y ya se agotaron una vez.\n"
        f"Si de verdad hace falta otro, sube {MAX_JOBS_WINDOWS} aquí y explica "
        f"en el commit qué comprueba que los demás no comprueban.")


def test_los_tests_que_compilan_no_corren_en_cada_push():
    """
    Compilan un .exe con PyInstaller de verdad. Medido en local: 533 s la suite
    entera contra 187 s sin ellos — dos tercios del tiempo. Y se pagaban en los
    cuatro jobs de la matriz, o sea cuatro veces por push.
    """
    pasos = _ci()["jobs"]["test"]["steps"]
    correr = next(s for s in pasos if s.get("name") == "Run tests")
    assert 'not slow' in str(correr["run"]), (
        "el job de cada push volvió a ejecutar los tests marcados `slow`. "
        "Compilan un .exe, cuestan dos tercios del tiempo, y `release.yml` los "
        "vuelve a ejecutar antes de publicar")


def test_pero_los_lentos_SIGUEN_corriendo_en_alguna_parte():
    """
    LA MITAD QUE SE OLVIDA.

    Sacarlos del push está bien. Sacarlos de todas partes sería verde sin
    comprobar nada — y el fallo que cazan, un .exe que no arranca, es justo el
    que pasa todas las comprobaciones baratas.
    """
    ci = _ci()
    assert "lentos" in ci["jobs"], (
        "no hay job para los tests `slow`: se han quedado sin ejecutar en "
        "ninguna parte del CI")

    pasos = "\n".join(str(s.get("run", "")) for s in ci["jobs"]["lentos"]["steps"])
    assert '-m "slow"' in pasos or "-m 'slow'" in pasos, (
        "el job `lentos` no selecciona los tests lentos")

    disparo = ci["jobs"]["lentos"].get("if", "")
    assert "schedule" in disparo, "sin cadencia, «bajo demanda» acaba siendo nunca"


def test_el_release_sigue_ejecutando_la_suite_ENTERA():
    """
    Es la red de seguridad de todo lo anterior: da igual qué se recorte en el
    CI de cada push mientras nada se publique sin la suite completa en verde.
    """
    rel = yaml.safe_load(RELEASE.read_text(encoding="utf-8"))
    pasos = "\n".join(str(s.get("run", "")) for s in rel["jobs"]["test"]["steps"])
    assert "pytest tests/" in pasos
    assert "not slow" not in pasos, (
        "el release dejó de ejecutar los tests que compilan el .exe, que es "
        "justo lo que el release produce")
    assert rel["jobs"]["build"].get("needs") == "test", (
        "sin tests verdes no hay release: esa dependencia es la regla entera")


def test_la_cobertura_no_vuelve_a_correr_la_suite_entera():
    """
    Ese paso lleva `continue-on-error: true` —no puede tumbar nada— y llegó a
    tener el job media hora ocupado repitiendo la suite completa. Media hora de
    runner de pago por un número informativo.
    """
    pasos = _ci()["jobs"]["test"]["steps"]
    cov = next(s for s in pasos if "Coverage" in str(s.get("name", "")))
    assert "not slow" in str(cov["run"])


def test_el_fichero_explica_los_numeros_en_vez_de_solo_recortar():
    """
    Un recorte sin la medida al lado se deshace en el primer «pues subámoslo
    otra vez». Los 46 minutos y su reparto tienen que estar escritos donde se
    toma la decisión.
    """
    texto = CI.read_text(encoding="utf-8")
    assert "46" in texto, "falta el coste medido por push"
    assert "spending limit" in texto or "payments have failed" in texto, (
        "falta la causa real, y sin ella el próximo que lea esto creerá que "
        "fue una manía de optimización")
