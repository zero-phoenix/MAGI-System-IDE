"""
Tests del versionado de Naoko.

REGRESIÓN REAL QUE ESTOS TESTS BLOQUEAN
=======================================
Commit 1eb7e87 del repositorio:

    "Auto-reparación Naoko: v1.0.0 - ..."

etiquetado ENTRE v5.0.24 y v5.0.25. Causa: naoko.py:191 hacía
`new_tag = "v1.0.0"` como valor inicial, y cuando el regex de la línea 196 no
encontraba `tag_name:` en release.yml, ese default se usaba tal cual.

test_never_invents_a_version y test_rejects_version_regression hacen que ese
fallo no pueda repetirse en silencio.
"""
import pytest

from magi.modules.infrastructure.naoko_repair import (
    RepairOutcome,
    RepairReport,
    current_version,
    next_patch_version,
    validate_version_bump,
)


def test_never_invents_a_version(tmp_path):
    """Sin git no hay versión. Debe devolver None, NO 'v1.0.0'."""
    assert current_version(tmp_path) is None
    assert next_patch_version(tmp_path) is None


def test_rejects_version_regression():
    """El caso exacto del commit 1eb7e87."""
    ok, why = validate_version_bump("v5.0.24", "v1.0.0")
    assert not ok
    assert "REGRESIÓN" in why


def test_rejects_when_current_is_unknown():
    ok, why = validate_version_bump(None, "v1.0.0")
    assert not ok and "no se pudo determinar" in why


def test_rejects_same_version():
    ok, _ = validate_version_bump("v5.0.28", "v5.0.28")
    assert not ok


def test_accepts_forward_patch():
    ok, why = validate_version_bump("v5.0.28", "v5.0.29")
    assert ok and why == "v5.0.28 -> v5.0.29"


def test_rejects_malformed():
    assert not validate_version_bump("v5.0.28", "no-es-semver")[0]
    assert not validate_version_bump("v5.0.28", None)[0]


def test_patch_increments_correctly(monkeypatch):
    import magi.modules.infrastructure.naoko_repair as nr
    monkeypatch.setattr(nr, "current_version", lambda root=None: "v5.0.28")
    assert nr.next_patch_version() == "v5.0.29"


def test_report_renders_outcome():
    r = RepairReport(RepairOutcome.FIXED, hypothesis="timeout ausente",
                     files_touched=["magi/core/providers/cloud.py"],
                     branch="naoko/fix-1")
    out = r.render()
    assert r.success and "fixed" in out and "cloud.py" in out


def test_regressed_report_is_not_success():
    assert not RepairReport(RepairOutcome.TESTS_REGRESSED).success
    assert not RepairReport(RepairOutcome.NOT_REPRODUCIBLE).success


def _executable_source(path) -> str:
    """Código sin docstrings ni comentarios.

    Necesario porque la documentación del módulo CITA el bug para explicarlo;
    lo que no puede volver es el código, no la explicación.
    """
    import ast
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                node.body.pop(0)
    return ast.unparse(tree)


def test_naoko_source_no_longer_defaults_to_v100():
    """Guarda directa: el default peligroso no puede volver al código."""
    from pathlib import Path
    src = _executable_source(Path(__file__).resolve().parents[1]
                             / "magi/modules/infrastructure/naoko.py")
    assert "'v1.0.0'" not in src and '"v1.0.0"' not in src
    assert "git add ." not in src, "git add . arrastraba todo el árbol de trabajo"


def test_naoko_no_longer_appends_to_readme():
    """naoko.py:225 hacía readme_content += ... en cada reparación: el README
    crecía sin fin y quedó con una frase cortada a medias."""
    from pathlib import Path
    src = _executable_source(Path(__file__).resolve().parents[1]
                             / "magi/modules/infrastructure/naoko.py")
    assert "readme_content +=" not in src
    assert "Actualización Autónoma" not in src
