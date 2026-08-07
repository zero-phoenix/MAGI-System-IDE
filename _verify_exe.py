"""
Verificación del .exe compilado, en frío y de extremo a extremo.

Arranca el binario publicado, le hace la MISMA pregunta que destapó el fallo
("por que la filosofia es la madre de todas las ciencias") por el WebSocket que
usa la GUI, y cuenta procesos de navegador antes y después. Es la prueba que
faltaba: los arreglos anteriores se dieron por buenos sin ejecutar el binario.
"""
import asyncio, json, subprocess, sys, time

EXE = r"C:\Users\D\MAGI-System-IDE\dist\MAGI-IDE-v5.exe"
PREGUNTA = "por que la filosofia es la madre de todas las ciencias"


def navegadores() -> set:
    """PIDs de navegador con depuración remota (la firma de g4f/CDP)."""
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='chrome.exe' or "
          "Name='msedge.exe' or Name='chromium.exe'\" | "
          "Where-Object { $_.CommandLine -like '*remote-debugging-port*' } | "
          "Select-Object -ExpandProperty ProcessId")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, text=True, timeout=60)
    return {l.strip() for l in r.stdout.splitlines() if l.strip().isdigit()}


async def preguntar(port=20128, timeout=180):
    import websockets
    uri = f"ws://127.0.0.1:{port}"
    async with websockets.connect(uri, open_timeout=30, max_size=None) as ws:
        await ws.send(json.dumps({"type": "SYS_EXEC", "id": "verify",
                                  "payload": {"command": PREGUNTA}}))
        fin = time.time() + timeout
        respuestas = 0
        while time.time() < fin:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=fin - time.time())
            except asyncio.TimeoutError:
                break
            respuestas += 1
            d = json.loads(msg)
            topic = d.get("topic") or d.get("type") or ""
            if d.get("id") == "verify":
                print("  RPC:", str(d)[:180])
            elif "log" in str(topic).lower() or "swarm" in str(topic).lower():
                print("  ev:", str(topic)[:40], str(d.get("payload"))[:120])
            if respuestas > 60:
                break
        return respuestas


async def main():
    antes = navegadores()
    print(f"Navegadores con CDP antes de arrancar: {len(antes)}")

    print(f"Arrancando {EXE} ...")
    proc = subprocess.Popen([EXE])
    try:
        await asyncio.sleep(35)          # arranque + sondeo de proveedores
        arranque = navegadores() - antes
        print(f"Navegadores nuevos tras el ARRANQUE: {len(arranque)}")

        print(f"Preguntando: {PREGUNTA!r}")
        n = await preguntar()
        print(f"  ({n} mensajes recibidos)")
        await asyncio.sleep(10)

        despues = navegadores() - antes
        print(f"\n>>> Navegadores nuevos TOTALES: {len(despues)} <<<")
        print("VEREDICTO:", "OK — ninguna ventana" if not despues
              else f"FALLO — se abrieron {despues}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except Exception:
            proc.kill()


asyncio.run(main())
