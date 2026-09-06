"""
Pruebas para L2: repos_clonar y repos_desregistrar en Lilim.

Compuerta A3:
`build_project_exe` exige que la tarea tenga ficheros fuente registrados en su
journal antes de compilar. `repos_clonar` permite importar repositorios curados
del índice `repos_top.json` (o URLs directas) al workspace de la tarea con clon
shallow y registro automático de cada fichero en el journal, satisfaciendo la
compuerta A3 con trazabilidad y permitiendo un des-registro limpio.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from magi.core.tools.builtin import ToolContext, build_registry
from magi.core.tools.journal import WriteJournal
from magi.modules.lilim import desregistrar_clon, repos_clonar


@pytest.fixture()
def local_git_repo(tmp_path):
    """Crea un repositorio git local de prueba con fuentes .py."""
    repo_dir = tmp_path / "repo_origen"
    repo_dir.mkdir(parents=True, exist_ok=True)
    (repo_dir / "app.py").write_text("print('hola desde repo')", encoding="utf-8")
    (repo_dir / "util.py").write_text("def suma(a, b): return a + b", encoding="utf-8")

    # Iniciar git y hacer commit inicial
    subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@magi.local"], cwd=repo_dir, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "MagiTest"], cwd=repo_dir, capture_output=True, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo_dir, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, capture_output=True, check=True)

    return repo_dir


def test_repo_desconocido_no_clona_y_avisa(tmp_path):
    journal = WriteJournal(task_id="task_fail", root=tmp_path / "journal")
    ok, msg, meta = repos_clonar("repo_inexistente_xyz_123", destino=tmp_path / "dest", journal=journal)
    assert not ok
    assert "repos_top.json" in msg
    assert not (tmp_path / "dest").exists()


def test_clonar_con_registro_en_journal_cumple_compuerta_a3(local_git_repo, tmp_path):
    journal = WriteJournal(task_id="task_l2", root=tmp_path / "journal")
    dest = tmp_path / "workspace" / "clon_prueba"

    ok, msg, meta = repos_clonar(
        str(local_git_repo),
        destino=dest,
        task_id="task_l2",
        journal=journal,
        profundidad=1,
    )

    assert ok, f"Error al clonar: {msg}"
    assert dest.exists()
    assert (dest / "app.py").exists()
    assert (dest / "util.py").exists()

    # Compuerta A3: el journal debe tener los fuentes .py registrados para task_l2
    fuentes = journal.fuentes_de_tarea("task_l2", bajo=str(dest))
    assert len(fuentes) >= 2
    assert any("app.py" in f for f in fuentes)
    assert any("util.py" in f for f in fuentes)


def test_desregistrar_clon_limpia_archivos_y_journal(local_git_repo, tmp_path):
    journal = WriteJournal(task_id="task_desreg", root=tmp_path / "journal")
    dest = tmp_path / "workspace" / "clon_para_borrar"

    ok, _, _ = repos_clonar(
        str(local_git_repo),
        destino=dest,
        task_id="task_desreg",
        journal=journal,
    )
    assert ok
    assert dest.exists()

    # Des-registro limpio
    ok_des, msg_des = desregistrar_clon(dest, task_id="task_desreg", journal=journal)
    assert ok_des
    assert not dest.exists()

    # Todas las entradas del journal para esa ruta deben quedar marcadas como undone
    dest_str = str(dest).replace("\\", "/").lower()
    for e in journal.all_entries():
        target_str = str(e.target).replace("\\", "/").lower()
        if target_str == dest_str or target_str.startswith(dest_str + "/"):
            assert e.undone, f"La entrada {e.op_id} para {e.target} no se marcó como undone"


def test_clonar_sobre_directorio_no_vacio_es_rechazado(local_git_repo, tmp_path):
    dest = tmp_path / "workspace" / "ocupado"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "fichero_previo.txt").write_text("no vacio", encoding="utf-8")

    ok, msg, _ = repos_clonar(str(local_git_repo), destino=dest)
    assert not ok
    assert "no está vacío" in msg


@pytest.mark.asyncio
async def test_herramientas_lilim_en_registry(local_git_repo, tmp_path):
    reg = build_registry()
    assert "repos_clonar" in reg.names()
    assert "repos_desregistrar" in reg.names()

    dest = tmp_path / "workspace" / "tool_dest"
    journal = WriteJournal(task_id="task_tool", root=tmp_path / "journal")
    ctx = ToolContext(
        task_id="task_tool",
        cwd=tmp_path / "workspace",
        journal=journal,
    )

    # 1. Probar tool repos_clonar
    res = await reg.execute("repos_clonar", {"nombre": str(local_git_repo), "destino": str(dest)}, ctx=ctx)
    assert res.ok
    assert dest.exists()
    assert (dest / "app.py").exists()

    # 2. Probar tool repos_desregistrar
    res_des = await reg.execute("repos_desregistrar", {"destino": str(dest)}, ctx=ctx)
    assert res_des.ok
    assert not dest.exists()
