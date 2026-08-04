"""
Aprobación con contexto (§7.4).

El banner de v5.0.28 pedía aprobar sin decir QUÉ se aprobaba. La interfaz
deducía el estado de aprobación raspando el terminal en busca de una frase, y
al no haber datos el visor de diffs recibía `originalCode=""` y pintaba todo
en verde. Aprobar ahí era aprobar a ciegas con la apariencia de haber
revisado.

Estos tests cubren las dos mitades: que el contexto se reúne bien desde el
journal, y que el contrato con el frontend no se desincroniza.
"""
import json
import re
from pathlib import Path

import pytest

from magi.core.approval import (
    MAX_BYTES_PER_FILE, ApprovalRequest, FileChange, build_approval_request,
    changes_from_journal,
)
from magi.core.tools.journal import WriteJournal

ROOT = Path(__file__).resolve().parents[1]


# Era una copia local del mismo regex; ya iba por la tercera. Vive en
# `source_helpers` porque tres copias es como empiezan las divergencias.
from source_helpers import strip_js_comments as _sin_comentarios


@pytest.fixture
def entorno(tmp_path):
    """Un proyecto con journal, como lo deja una tarea real."""
    proyecto = tmp_path / "proy"
    proyecto.mkdir()
    journal = WriteJournal(task_id="t1", root=tmp_path / ".journal")
    return proyecto, journal


def _modificar(journal, path: Path, contenido: str):
    """Escribe pasando por el journal, igual que hacen las herramientas."""
    with journal.guard(path, "write" if path.exists() else "create"):
        path.write_text(contenido, encoding="utf-8")


# ------------------------------------------------- reconstrucción del cambio

def test_recupera_el_contenido_anterior_desde_el_journal(entorno):
    """
    El punto de todo esto: el journal ya guardaba el estado previo para poder
    deshacer (§4.2), y esa misma copia es el "antes" que le faltaba al diff.
    """
    proyecto, journal = entorno
    f = proyecto / "a.py"
    f.write_text("def viejo():\n    pass\n", encoding="utf-8")
    _modificar(journal, f, "def nuevo():\n    return 42\n")

    cambios = changes_from_journal("t1", journal)
    assert len(cambios) == 1
    assert cambios[0].before == "def viejo():\n    pass\n"
    assert cambios[0].after == "def nuevo():\n    return 42\n"
    assert cambios[0].kind == "modificado"


def test_un_fichero_nuevo_se_marca_como_creado(entorno):
    proyecto, journal = entorno
    _modificar(journal, proyecto / "nuevo.py", "print('hola')\n")
    c = changes_from_journal("t1", journal)[0]
    assert c.kind == "creado"
    assert c.before == ""
    assert "hola" in c.after


def test_un_fichero_borrado_se_marca_como_borrado(entorno):
    proyecto, journal = entorno
    f = proyecto / "sobra.py"
    f.write_text("contenido\n", encoding="utf-8")
    journal.record(f, "delete")
    f.unlink()
    c = changes_from_journal("t1", journal)[0]
    assert c.kind == "borrado"
    assert c.before == "contenido\n"
    assert c.after == ""


def test_se_queda_con_el_estado_de_ANTES_DE_EMPEZAR(entorno):
    """
    Si una tarea toca el mismo fichero tres veces, el "antes" que le interesa
    a quien revisa es el original, no el de la penúltima escritura. Coger la
    última mostraría un diff diminuto de un cambio grande.
    """
    proyecto, journal = entorno
    f = proyecto / "iterado.py"
    f.write_text("versión 0\n", encoding="utf-8")
    for i in range(1, 4):
        _modificar(journal, f, f"versión {i}\n")

    c = changes_from_journal("t1", journal)[0]
    assert c.before == "versión 0\n", "debe enseñar el original, no el anterior"
    assert c.after == "versión 3\n"


def test_solo_cuenta_los_cambios_de_esta_tarea(tmp_path):
    proyecto = tmp_path / "p"
    proyecto.mkdir()
    raiz = tmp_path / ".j"
    otra = WriteJournal(task_id="OTRA", root=raiz)
    _modificar(otra, proyecto / "ajena.py", "no es mía\n")
    mia = WriteJournal(task_id="MIA", root=raiz)
    _modificar(mia, proyecto / "mia.py", "sí es mía\n")

    rutas = [Path(c.path).name for c in changes_from_journal("MIA", mia)]
    assert rutas == ["mia.py"]


def test_ignora_lo_ya_deshecho(entorno):
    """Un cambio revertido no está pendiente de aprobación."""
    proyecto, journal = entorno
    f = proyecto / "revertido.py"
    f.write_text("original\n", encoding="utf-8")
    _modificar(journal, f, "cambiado\n")
    journal.undo_last()
    assert changes_from_journal("t1", journal) == []


# ------------------------------------------------------- casos incómodos

def test_un_binario_no_se_intenta_mostrar_como_texto(entorno):
    proyecto, journal = entorno
    img = proyecto / "logo.png"
    with journal.guard(img, "create"):
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + bytes(400))
    c = changes_from_journal("t1", journal)[0]
    assert "binario" in c.note
    assert c.after == ""


def test_detecta_binarios_por_contenido_no_solo_por_extension(entorno):
    """
    Fiarse de la extensión falla con lo que de verdad aparece: un `.dat`, un
    fichero sin extensión, un `.py` con basura dentro.
    """
    proyecto, journal = entorno
    raro = proyecto / "datos.dat"
    with journal.guard(raro, "create"):
        raro.write_bytes(b"texto\x00\x00binario")
    assert "bytes nulos" in changes_from_journal("t1", journal)[0].note


def test_un_fichero_enorme_se_recorta_y_lo_dice(entorno):
    """Un .log de 40 MB por el websocket bloquea la interfaz al pintarlo."""
    proyecto, journal = entorno
    grande = proyecto / "enorme.txt"
    with journal.guard(grande, "create"):
        grande.write_text("x" * (MAX_BYTES_PER_FILE + 5000), encoding="utf-8")
    c = changes_from_journal("t1", journal)[0]
    assert len(c.after) < MAX_BYTES_PER_FILE + 200
    assert "recortado" in c.after


def test_no_revienta_si_la_copia_se_perdio(entorno):
    """
    `journal.prune()` borra copias viejas. Si falta, el cambio deja de ser
    reversible — y eso cambia lo que significa aprobar, así que se dice ANTES
    en vez de descubrirlo al intentar deshacer.
    """
    proyecto, journal = entorno
    f = proyecto / "a.py"
    f.write_text("antes\n", encoding="utf-8")
    entrada = journal.record(f, "write")
    f.write_text("después\n", encoding="utf-8")
    Path(entrada.backup).unlink()

    c = changes_from_journal("t1", journal)[0]
    assert c.revertible is False
    assert build_approval_request("t1", journal=journal).reversible is False


def test_un_journal_ilegible_no_tumba_la_aprobacion():
    """
    Una tarea que se queda colgada porque el panel de revisión reventó es peor
    que una revisión incompleta.
    """
    class JournalRoto:
        def all_entries(self):
            raise OSError("disco lleno")

    p = build_approval_request("t1", journal=JournalRoto())
    assert p.changes == []
    assert isinstance(p.render(), str)


# --------------------------------------------------------- la petición

def test_cuenta_lineas_añadidas_y_borradas():
    c = FileChange(path="x.py", before="a\nb\nc\n", after="a\nb\nc\nd\ne\n")
    assert c.added == 2 and c.removed == 0


def test_avisa_de_que_no_se_ejecutaron_tests():
    p = build_approval_request("t1")
    assert "no se ejecutaron" in p.render().lower()


def test_avisa_de_tests_en_rojo():
    p = build_approval_request("t1", tests_ran=True, tests_passed=False,
                               tests_detail="3 fallos en test_swarm")
    texto = p.render()
    assert "EN ROJO" in texto and "test_swarm" in texto


def test_enumera_las_ordenes_que_se_van_a_ejecutar():
    """
    §7.4 pide saber "qué se va a ejecutar exactamente". Es lo que v5.0.28
    hacía a ciegas con powershell -ExecutionPolicy Bypass.
    """
    p = build_approval_request("t1", commands=["rm -rf build/", "npm publish"])
    assert "npm publish" in p.render()


def test_el_payload_es_serializable_a_json(entorno):
    proyecto, journal = entorno
    _modificar(journal, proyecto / "a.py", "print(1)\n")
    payload = build_approval_request("t1", journal=journal,
                                     summary="cambia algo").to_payload()
    assert json.loads(json.dumps(payload))["files_touched"] == 1


# --------------------------------------- contrato entre Python y TypeScript

def test_el_payload_coincide_con_el_tipo_del_frontend():
    """
    El contrato que nadie verifica se desincroniza a la primera. Un campo
    renombrado en Python y no en TypeScript no da error: da `undefined`
    pintado en la interfaz, que es exactamente cómo se llegó a un panel de
    aprobación que no enseñaba el cambio.
    """
    ts = (ROOT / "magi-gui/src/lib/approval.ts").read_text(encoding="utf-8")

    def campos(interfaz: str) -> set[str]:
        cuerpo = re.search(rf"interface {interfaz} \{{(.*?)\n\}}", ts, re.S)
        assert cuerpo, f"no se encontró la interfaz {interfaz}"
        return set(re.findall(r"^\s*(\w+)\??:", cuerpo.group(1), re.M))

    payload = ApprovalRequest(task_id="t").to_payload()
    assert campos("ApprovalRequest") == set(payload), (
        "ApprovalRequest de TypeScript no coincide con to_payload()")

    assert campos("FileChange") == set(FileChange(path="x").to_payload()), (
        "FileChange de TypeScript no coincide con to_payload()")


def test_el_orquestador_publica_el_evento():
    """
    Cableado: sin la llamada, `magi/core/approval.py` sería andamiaje muy bien
    probado — el fallo que ya cometí tres veces en esta reconstrucción.
    """
    src = (ROOT / "magi/modules/swarm/orchestrator.py").read_text(encoding="utf-8")
    assert "_publish_approval" in src
    assert "swarm.approval_required" in src


def test_el_frontend_escucha_el_evento():
    socket = (ROOT / "magi-gui/src/useMagiSocket.ts").read_text(encoding="utf-8")
    assert "swarm.approval_required" in socket, \
        "el backend publica el evento y la interfaz no lo escucha"
    app = (ROOT / "magi-gui/src/App.tsx").read_text(encoding="utf-8")
    # Sin quitar comentarios, este test lo disparaba el propio comentario que
    # explica el fallo corregido. Un test que se autodenuncia obliga a borrar
    # la explicación para ponerlo en verde, que es exactamente al revés.
    codigo = _sin_comentarios(app)
    assert 'originalCode=""' not in codigo, \
        "el visor de diffs vuelve a recibir un original vacío"
    assert "approval={approval}" in codigo, \
        "el visor ya no recibe el contexto estructurado"


# ------------------------------------------------------ higiene de la interfaz

def test_la_interfaz_tiene_tests_y_estan_en_ci():
    """
    Durante toda la reconstrucción hubo 443 tests en Python y CERO en la GUI,
    así que "sin tests verdes no hay release" valía para media casa. El diff
    de aprobación llevaba quién sabe cuánto sin enseñar nada y nada lo cazó,
    porque nada lo miraba.
    """
    gui = ROOT / "magi-gui"
    tests = list((gui / "src").rglob("*.test.ts")) + \
        list((gui / "src").rglob("*.test.tsx"))
    assert tests, "la interfaz no tiene ni un test"

    package = json.loads((gui / "package.json").read_text(encoding="utf-8"))
    assert "test" in package.get("scripts", {}), "falta el script `npm test`"

    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "npm test" in ci, "los tests de la interfaz no se ejecutan en CI"
    assert "npm run build" in ci, "la compilación de la interfaz no está en CI"


def test_app_tsx_no_vuelve_a_crecer_sin_limite():
    """
    §7.1: 42 KB en un fichero, con AgentMessageCard dentro. El límite no es
    estético — cada feature nueva en un fichero así cuesta más que la
    anterior, que es lo que hace que un proyecto se atasque.

    Si esto salta, el arreglo es EXTRAER un panel a `components/`, no subir
    el número.
    """
    app = ROOT / "magi-gui/src/App.tsx"
    lineas = len(app.read_text(encoding="utf-8").splitlines())
    assert lineas < 900, (
        f"App.tsx tiene {lineas} líneas. Extrae un panel a components/ "
        f"en lugar de subir este límite")
    assert (ROOT / "magi-gui/src/components/AgentMessageCard.tsx").exists()


def test_el_diff_no_vuelve_al_algoritmo_roto():
    """
    `!oldLines.includes(line)` no muestra borrados, se traga las líneas
    movidas y no distingue las repetidas. Que no vuelva.
    """
    visor = _sin_comentarios(
        (ROOT / "magi-gui/src/DiffViewer.tsx").read_text(encoding="utf-8"))
    assert "oldLines.includes" not in visor
    assert "diffLines" in visor, "el visor no usa el diff por LCS"
    diff = (ROOT / "magi-gui/src/lib/diff.ts").read_text(encoding="utf-8")
    assert "borrada" in diff, "el diff no contempla borrados"


# ------------------------------------------- regresiones de la revisión

def test_cuenta_las_lineas_que_cambian_no_la_diferencia_de_tamaño():
    """
    `added`/`removed` eran `max(0, len(después) - len(antes))`, o sea la
    diferencia de TAMAÑO. Reescribir un fichero de treinta líneas entero salía
    como "+0 −0 líneas" en el resumen que lee quien aprueba desde el terminal:
    "sin cambios" para una reescritura total.
    """
    antes = "\n".join(f"linea {i}" for i in range(30))
    despues = "\n".join(f"REESCRITA {i}" for i in range(30))
    c = FileChange(path="core.py", before=antes, after=despues)
    assert c.added == 30 and c.removed == 30
    assert "+30 −30" in ApprovalRequest(task_id="t", changes=[c]).render()


def test_una_linea_cambiada_cuenta_como_una_de_cada():
    c = FileChange(path="x.py", before="a\nb\nc", after="a\nX\nc")
    assert (c.added, c.removed) == (1, 1)


def test_un_journal_ilegible_no_promete_reversibilidad(entorno):
    """
    Si el journal falla, `changes_from_journal` devolvía [] y
    `reversible=all([])` daba True. El panel decía "No toca ningún fichero" y
    "Reversible: el journal guarda el estado previo" — dos afirmaciones
    tranquilizadoras cuando lo único cierto era que no se pudo leer nada.
    """
    class JournalRoto:
        def all_entries(self):
            raise OSError("permiso denegado")

    p = build_approval_request("t1", journal=JournalRoto())
    assert p.journal_error
    texto = p.render()
    assert "NO SE PUDO LEER EL JOURNAL" in texto
    assert "Trátalo como irreversible" in texto
    assert "No toca ningún fichero" not in texto
    assert p.to_payload()["reversible"] is False
