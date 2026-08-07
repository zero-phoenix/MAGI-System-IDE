"""Tests de la memoria eterna y el autoconocimiento de Naoko."""
from __future__ import annotations

import json

import pytest

from magi.modules.infrastructure.naoko_memory import (
    EternalMemory, SystemIntrospector,
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


def test_las_lecciones_se_deduplican_por_clave(mem):
    mem.remember_lesson(clave="k", leccion="primera versión")
    mem.remember_lesson(clave="k", leccion="versión corregida")
    ks = [l for l in mem.lessons() if l["clave"] == "k"]
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
