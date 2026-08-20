"""
Ninguna función del socket puede ir en las dependencias de un `useEffect`.

EL FALLO QUE ESTO IMPIDE, MEDIDO
================================
2026-08-20, sobre la aplicación en marcha y en reposo:

    MAGI-IDE-v5.exe  ->  97 % de un núcleo, permanentemente
    el mismo kernel arrancado solo, sin interfaz  ->  0 %

El bucle no estaba en el enjambre ni en los proveedores: estaba en React.
`useMagiSocket` devuelve funciones nuevas en cada render —son arrow functions,
no `useCallback`—, así que ponerlas en las dependencias de un efecto hace que
el efecto se dispare en CADA render. Y si el efecto provoca un cambio de
estado, el ciclo se cierra solo:

    efecto -> RPC -> respuesta -> setState -> render -> identidad nueva -> efecto

Había dos, y uno lo escribí yo (`RitsukoPanel`). El usuario lo notó como «el
sistema va lento y Naoko no responde»: Naoko respondía en 10 s, pero la ventana
estaba ahogada.

Este test es el mecanismo que evita la tercera vez.
"""
from __future__ import annotations

import pathlib
import re

import pytest

GUI = pathlib.Path(__file__).resolve().parents[1] / "magi-gui" / "src"

#: Lo que `useMagiSocket` devuelve. Si mañana devuelve algo más, este test lo
#: pide explícitamente aquí — que es justo la revisión que se quiere provocar.
FUNCIONES_DEL_SOCKET = (
    "sendCommand", "sendGitClone", "cancelTask", "stopEverything", "fetchHealth",
    "runBenchmark", "runSelfImprovement", "fetchRunningTasks", "listImprovements",
    "proposeImprovement", "decideImprovement", "fetchTelemetry",
    "requestFileContent", "sendNaokoChat", "sendRitsukoChat",
    "fetchRitsukoInformes", "fetchConfig", "listArtifacts", "readArtifact",
    "fetchTaskList", "archiveTask", "deleteTask",
)

#: `useEffect(..., [deps])` — se captura el array de dependencias.
_EFECTO = re.compile(r"useEffect\(.*?\}\s*,\s*\[([^\]]*)\]\s*\)", re.DOTALL)


def _fuentes() -> list[pathlib.Path]:
    return sorted(p for p in GUI.rglob("*.tsx")) + sorted(GUI.rglob("*.ts"))


@pytest.mark.skipif(not GUI.is_dir(), reason="sin fuentes de la interfaz")
def test_ninguna_funcion_del_socket_esta_en_las_dependencias():
    culpables: list[str] = []
    for fichero in _fuentes():
        texto = fichero.read_text(encoding="utf-8", errors="replace")
        for m in _EFECTO.finditer(texto):
            deps = {d.strip() for d in m.group(1).split(",") if d.strip()}
            for fn in FUNCIONES_DEL_SOCKET:
                if fn in deps:
                    linea = texto[:m.start()].count("\n") + 1
                    culpables.append(f"{fichero.name}:{linea} -> {fn}")

    assert not culpables, (
        "estas dependencias vuelven a crear el bucle de render que se comió un "
        "núcleo entero:\n  " + "\n  ".join(culpables) +
        "\n\nQuítalas del array (la función es estable en comportamiento aunque "
        "no en identidad) o envuélvela en useCallback en useMagiSocket."
    )


@pytest.mark.skipif(not GUI.is_dir(), reason="sin fuentes de la interfaz")
def test_el_panel_de_ritsuko_pide_sus_informes_una_sola_vez():
    """
    El caso concreto que se rompió, fijado aparte.

    Un test general es fácil de esquivar sin querer al refactorizar; este
    nombra el sitio exacto donde ya pasó.
    """
    panel = (GUI / "components" / "RitsukoPanel.tsx").read_text(encoding="utf-8")
    efecto = _EFECTO.search(panel)
    assert efecto, "el panel ya no tiene el efecto de carga inicial"
    assert efecto.group(1).strip() == "", (
        "el efecto de carga de informes debe tener dependencias vacías: con la "
        "función del socket dentro se dispara en cada render")


@pytest.mark.skipif(not GUI.is_dir(), reason="sin fuentes de la interfaz")
def test_el_socket_devuelve_una_identidad_estable():
    """
    La causa raíz, no los síntomas.

    Los dos tests de arriba persiguen efectos concretos: sirven, pero son una
    caza del gato y el ratón. Mientras `useMagiSocket` devuelva funciones
    nuevas en cada render, el siguiente componente que haga lo que el linter
    de React pide vuelve a abrir el agujero.

    Congelar el objeto devuelto con `useMemo(..., [])` cierra la clase entera
    de fallo: ya no hay ninguna dependencia que pueda cambiar sola. Este test
    fija esa decisión para que un refactor no la deshaga sin darse cuenta.
    """
    fuente = (GUI / "useMagiSocket.ts").read_text(encoding="utf-8")

    m = re.search(r"return\s+useMemo\(\s*\(\)\s*=>\s*\(\{(.*?)\}\)\s*,\s*\[([^\]]*)\]\s*\)",
                  fuente, re.DOTALL)
    assert m, (
        "`useMagiSocket` debe devolver `useMemo(() => ({...}), [])`. Sin eso "
        "cada render entrega funciones nuevas y cualquier efecto que las use "
        "como dependencia se vuelve un bucle infinito.")

    assert m.group(2).strip() == "", (
        "el `useMemo` del socket debe tener dependencias vacías; con algo "
        "dentro vuelve a cambiar de identidad")

    # Y que no se quede ninguna función fuera del objeto congelado: una sola
    # que se devuelva por su cuenta reabre el agujero para esa función.
    devueltas = {n.strip() for n in m.group(1).replace("\n", " ").split(",")}
    faltan = [fn for fn in FUNCIONES_DEL_SOCKET if fn not in devueltas]
    assert not faltan, (
        "estas funciones se devuelven fuera del `useMemo` y siguen cambiando "
        "de identidad en cada render: " + ", ".join(faltan))
