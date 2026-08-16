"""Tests de la memoria eterna y el autoconocimiento de Naoko."""
from __future__ import annotations

import json

import pytest

from magi.modules.infrastructure.naoko_memory import (
    EternalMemory,
    SystemIntrospector,
)


@pytest.fixture
def mem(tmp_path):
    return EternalMemory(root=tmp_path / "naoko")


# ------------------------------------------------------------- persistencia

def test_se_siembra_sola_la_primera_vez(mem):
    assert mem.identity_path.exists()
    assert mem.invariants_path.exists()
    assert len(mem.lessons()) >= 3
    assert len(mem.episodes()) >= 4


def test_sobrevive_a_reabrir_el_proceso(tmp_path):
    """Lo que hace que la memoria sea 'eterna': está en disco, no en el .exe."""
    root = tmp_path / "naoko"
    a = EternalMemory(root=root)
    a.remember_episode(tipo="incidente", resumen="el disco se llenó")
    del a

    b = EternalMemory(root=root)          # proceso nuevo, misma carpeta
    assert any("disco se llenó" in e["resumen"] for e in b.episodes())


def test_no_pisa_lo_ya_escrito_al_re_sembrar(tmp_path):
    root = tmp_path / "naoko"
    a = EternalMemory(root=root)
    n = len(a.episodes(limit=None))
    EternalMemory(root=root)
    EternalMemory(root=root)
    assert len(EternalMemory(root=root).episodes(limit=None)) == n


# ------------------------------------------------------- actualización

def test_una_identidad_vieja_sin_editar_se_actualiza(tmp_path):
    """
    Una mejora que solo llega a las instalaciones nuevas no es una mejora.
    Al añadir a la identidad que el enjambre son compañeros de Naoko —la
    corrección de que hablara de «el soporte de Melchior»—, la instalación
    que ya existía se quedó con la versión vieja.
    """
    from magi.modules.infrastructure import naoko_memory as nm

    root = tmp_path / "naoko"
    root.mkdir(parents=True)
    vieja = nm.IDENTITY_SEED.split("\n", 1)[0] + "\n\nversión antigua y corta.\n"
    (root / "identity.md").write_text(vieja, encoding="utf-8")

    m = EternalMemory(root=root)
    assert m.identity() == nm.IDENTITY_SEED


def test_una_identidad_editada_por_el_usuario_NO_se_toca(tmp_path):
    from magi.modules.infrastructure import naoko_memory as nm

    root = tmp_path / "naoko"
    root.mkdir(parents=True)
    mia = ("# Mi Naoko\n\nLa he reescrito entera a mi gusto y quiero que se "
           "quede así, con bastante texto para que no parezca una semilla "
           "recortada de las nuestras ni por asomo.\n" + "relleno. " * 200)
    (root / "identity.md").write_text(mia, encoding="utf-8")

    assert EternalMemory(root=root).identity() == mia


def test_una_invariante_nueva_llega_a_una_memoria_existente(tmp_path):
    import json as _json

    from magi.modules.infrastructure import naoko_memory as nm

    root = tmp_path / "naoko"
    root.mkdir(parents=True)
    (root / "invariants.json").write_text(
        _json.dumps({"version": 1, "invariantes": [nm.INVARIANT_SEED[0]]}),
        encoding="utf-8")

    ids = {i["id"] for i in EternalMemory(root=root).invariants()}
    assert ids == {i["id"] for i in nm.INVARIANT_SEED}


def test_una_leccion_nueva_llega_a_una_memoria_existente(tmp_path):
    from magi.modules.infrastructure import naoko_memory as nm

    root = tmp_path / "naoko"
    root.mkdir(parents=True)
    (root / "lessons.jsonl").write_text(
        '{"clave": "vieja", "leccion": "algo"}\n', encoding="utf-8")

    claves = {ln["clave"] for ln in EternalMemory(root=root).lessons()}
    assert "vieja" in claves, "no se pierde lo que ya había"
    assert {ln["clave"] for ln in nm.LESSON_SEED} <= claves


def test_la_identidad_nombra_a_los_tres_nodos_del_enjambre():
    """
    Naoko respondió a «¿por qué se demora tanto Melchior?» hablando de
    servidores saturados y del soporte de Melchior, como si fuera un producto
    de otra empresa. Melchior es un nodo de este mismo sistema.
    """
    from magi.modules.infrastructure import naoko_memory as nm
    for nodo in ("MELCHIOR", "BALTHASAR", "CASPER"):
        assert nodo in nm.IDENTITY_SEED
    assert "terceros" in nm.IDENTITY_SEED


def test_las_lecciones_se_deduplican_por_clave(mem):
    mem.remember_lesson(clave="k", leccion="primera versión")
    mem.remember_lesson(clave="k", leccion="versión corregida")
    ks = [ln for ln in mem.lessons() if ln["clave"] == "k"]
    assert len(ks) == 1
    assert ks[0]["leccion"] == "versión corregida"


def test_un_jsonl_corrupto_no_tumba_la_memoria(mem):
    mem.episodes_path.write_text('{"roto": \n no json\n', encoding="utf-8")
    assert mem.episodes() == []          # degrada, no revienta


# -------------------------------------------------------------- recurrencia

def test_detecta_que_un_fallo_ya_habia_pasado(mem):
    mem.remember_episode(
        tipo="queja",
        resumen="se abrieron ventanas de navegador al preguntar al sistema")
    hits = mem.seen_before(
        "otra vez se abren ventanas de navegador cuando pregunto al sistema")
    assert hits, "debería reconocer la recurrencia"


def test_no_inventa_recurrencias(mem):
    assert mem.seen_before("cómo cambio el color del tema") == []


def test_el_brief_lleva_identidad_invariantes_y_lecciones(mem):
    b = mem.brief()
    assert "Naoko" in b
    assert "I.3-sin-navegador" in b
    assert "Cloudflare" in b             # la lección que costó 3 sesiones


# ------------------------------------------------------------- invariantes

def test_la_sonda_de_navegador_detecta_el_cortafuegos_puesto():
    from magi.core import no_browser
    no_browser.install()
    intro = SystemIntrospector()
    ok, detalle = intro._sonda_no_browser()
    assert ok is True
    assert "íntegro" in detalle


def test_check_invariants_devuelve_una_entrada_por_invariante(mem):
    intro = SystemIntrospector()
    rep = intro.check_invariants(mem.invariants())
    assert len(rep) == len(mem.invariants())
    assert all("ok" in r and "detalle" in r for r in rep)


def test_una_sonda_que_revienta_no_tumba_la_comprobacion(mem):
    intro = SystemIntrospector()
    rep = intro.check_invariants([{"id": "x", "regla": "r", "sonda": "no_existe",
                                   "severidad": "baja"}])
    assert rep[0]["ok"] is True          # sonda desconocida no acusa en falso


def test_la_sonda_de_rutas_no_encuentra_rutas_del_autor():
    ok, detalle = SystemIntrospector()._sonda_rutas()
    assert ok is True, detalle


# ---------------------------------------------------------- autoconocimiento

def test_la_introspeccion_reporta_el_runtime_real():
    r = SystemIntrospector().runtime()
    assert "python" in r and "data_dir" in r
    assert isinstance(r["congelado_en_exe"], bool)


def test_el_brief_de_introspeccion_no_miente_sin_registro():
    b = SystemIntrospector().brief()
    assert "Proveedores registrados" not in b   # sin registro, no lo afirma


def test_la_introspeccion_lista_los_proveedores_cuando_los_hay():
    class FakeReg:
        def all(self):
            class R:
                id, family, available = "g4f-gpt", "gpt", True
                provider = type("P", (), {"is_local": False})()
            return [R()]

    intro = SystemIntrospector(registry=FakeReg())
    p = intro.providers()
    assert p["registrados"] == ["g4f-gpt"]
    assert intro._sonda_providers_gratuitos()[0] is True


def test_la_sonda_de_gratuidad_acusa_a_un_proveedor_local():
    class FakeReg:
        def all(self):
            class R:
                id, family, available = "ollama", "local", True
                provider = type("P", (), {"is_local": True})()
            return [R()]

    ok, detalle = SystemIntrospector(registry=FakeReg())._sonda_providers_gratuitos()
    assert ok is False
    assert "ollama" in detalle
