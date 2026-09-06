"""
A2 (v11): un juego se verifica jugándolo, no existiendo.

El autotest del juego simula las teclas él mismo y solo imprime la marca
cuando recorrió el ciclo completo: caer, game over, reinicio, tablero limpio.
La misión Tetris entregó un .exe con la R de reinicio rota — este helper es
la prueba que la habría cazado antes de entregar.
"""
import sys
import textwrap

from magi.modules.studio.interactivo import probar_juego_interactivo


async def test_un_juego_sano_pasa_el_autotest(tmp_path):
    juego = tmp_path / "juego.py"
    juego.write_text(textwrap.dedent("""
        import sys
        if "--autotest" in sys.argv:
            # simula: caer -> game over -> R -> tablero limpio
            print("piezas caen, game over, reinicio, tablero limpio")
            print("GAME_AUTOTEST_OK")
            sys.exit(0)
        print("ventana normal")
    """), encoding="utf-8")
    estado, salida = await probar_juego_interactivo(
        [sys.executable, str(juego), "--autotest"], timeout=30)
    assert estado == "verde", salida


async def test_un_juego_con_la_reiniciacion_rota_falla(tmp_path):
    """El caso real del 5-sep: el juego corre, pero R no reinicia — el
    autotest no puede completar el ciclo y NO imprime la marca."""
    juego = tmp_path / "roto.py"
    juego.write_text(textwrap.dedent("""
        import sys
        if "--autotest" in sys.argv:
            print("piezas caen, game over")
            print("reinicio no funciona")   # la marca nunca llega
            sys.exit(1)
        print("ventana normal")
    """), encoding="utf-8")
    estado, salida = await probar_juego_interactivo(
        [sys.executable, str(juego), "--autotest"], timeout=30)
    assert estado == "rojo", salida
    assert "GAME_AUTOTEST_OK" not in salida


async def test_un_cuelgue_no_bloquea_la_compuerta(tmp_path):
    """Un juego cuyo autotest se cuelga se mata al timeout y cuenta como
    fallo — no como una compuerta eterna."""
    juego = tmp_path / "colgado.py"
    juego.write_text(textwrap.dedent("""
        import time
        time.sleep(120)
    """), encoding="utf-8")
    estado, salida = await probar_juego_interactivo(
        [sys.executable, str(juego), "--autotest"], timeout=3)
    assert estado == "sin_comprobar", salida
    assert "cuelgue" in salida


async def test_un_binario_que_no_existe_falla_en_claro(tmp_path):
    estado, salida = await probar_juego_interactivo(
        [str(tmp_path / "no-existe.exe"), "--autotest"], timeout=10)
    assert estado == "sin_comprobar"
    assert "no se pudo lanzar" in salida
