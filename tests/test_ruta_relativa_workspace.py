"""
Las rutas relativas se resuelven contra el workspace.

El flujo del enjambre y una persona común nombran «docs/BITACORA.md»; el
handler exigía la absoluta y el clic del enlace de la v5.21 abría el panel
sin seleccionar el fichero (pase de Balthasar, 4-sep-2026).
"""
import magi.core.rpc.ws_server as ws


async def test_la_ruta_relativa_se_resuelve_contra_el_workspace(tmp_path, monkeypatch):
    from magi.core import paths
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "BITACORA.md").write_text("regla R6", encoding="utf-8")
    falsa = lambda: tmp_path            # noqa: E731
    falsa.cache_clear = lambda: None    # el conftest la limpia al salir
    monkeypatch.setattr(paths, "workspace_dir", falsa)

    rpc = ws.WSServer.__new__(ws.WSServer)     # sin servidor: solo el handler
    r = await rpc._handle_get_file_content({"path": "docs/BITACORA.md"}, None)
    assert r.get("content") == "regla R6"


async def test_la_absoluta_sigue_funcionando(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("hola", encoding="utf-8")
    rpc = ws.WSServer.__new__(ws.WSServer)
    r = await rpc._handle_get_file_content({"path": str(f)}, None)
    assert r.get("content") == "hola"


async def test_ruta_inexistente_sigue_diciendo_error():
    rpc = ws.WSServer.__new__(ws.WSServer)
    r = await rpc._handle_get_file_content({"path": "no/existe.md"}, None)
    assert "error" in r
