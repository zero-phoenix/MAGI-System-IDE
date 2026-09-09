"""
Hablarle a Magisys por WebSocket, igual que escribir en su interfaz.

QUE ARREGLA ESTO
================
La primera version escuchaba `topic in ("MELCHIOR", "BALTHASAR", "CASPER")`.
El bus NO publica eso: publica `AGENT_POST` con el nodo dentro del payload
(`magi-gui/src/useMagiSocket.ts:113`). Asi que la sesion corria, el enjambre
debatia, y por aqui no se veia ni una intervencion — solo los "[ESPERA]" de
los timeouts. Un supervisor que no ve el debate no supervisa nada.

Ademas el encargo estaba EMPOTRADO en una constante, asi que solo servia
para mandar esa peticion una vez. Un debate necesita seguimiento: mandar la
primera version, leerla, y pedir la siguiente sobre la misma tarea.

USO
===
    python scripts/interactuar_magi.py "tu encargo"
    python scripts/interactuar_magi.py --tarea task_abc123 "ahora mejoralo"
    python scripts/interactuar_magi.py --escuchar --segundos 600
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid

import websockets

# Windows: la consola cp1252 revienta con «→» o con acentos, y lo que se
# pierde entonces es justo el veredicto que se venia a leer.
# `line_buffering=True` no es cosmetico: sin el, con la salida redirigida a
# un fichero Python acumula todo y no se ve NADA hasta que el proceso
# termina. En una ronda de diez minutos eso convierte una herramienta de
# supervision en un informe post mortem, y lo que se queria era mirar el
# debate mientras ocurre.
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

URI = "ws://127.0.0.1:20128"


def _corto(texto: object, n: int = 400) -> str:
    t = str(texto or "").strip().replace("\r", "")
    t = " ".join(t.split())
    return t if len(t) <= n else t[:n] + " […]"


def _pintar(topic: str, pld: dict) -> bool:
    """Escribe el evento si dice algo. Devuelve True si cierra la ronda."""
    if topic == "AGENT_POST":
        agente = pld.get("agent", "?")
        rol = pld.get("role", "")
        prov = pld.get("provider", "")
        print(f"\n=== {agente} ({rol}) · {prov}\n{_corto(pld.get('content'), 900)}")
    elif topic == "swarm.routed":
        print(f"[RUTA] {pld.get('route')} · confianza {pld.get('confidence')} "
              f"· {_corto(pld.get('reason'), 160)}")
    elif topic == "task.titled":
        print(f"[TITULO] {pld.get('title')}")
    elif topic == "task.plan":
        print(f"[PLAN] {_corto(pld.get('plan') or pld, 400)}")
    elif topic == "swarm.fases":
        print(f"[FASES] ronda {pld.get('round')} · {pld.get('t_ronda_ms')} ms "
              f"· melchior {pld.get('t_melchior_ms')} ms"
              + (" · recon" if pld.get("recon") else "")
              + (" · replica" if pld.get("fired") else ""))
    elif topic == "swarm.verification_failed":
        print(f"[VERIFICACION FALLIDA] {_corto(pld, 300)}")
    elif topic == "swarm.approval_required":
        print(f"\n[!] APROBACION REQUERIDA: {_corto(pld, 400)}")
    elif topic == "agent.tool_use":
        print(f"  · {pld.get('agent', '?')} usa {pld.get('tool')}"
              f"({_corto(pld.get('args'), 120)})")
    elif topic == "agent.tool_result":
        print(f"    -> {_corto(pld.get('result'), 200)}")
    elif topic == "TERMINAL_OUT":
        txt = pld if isinstance(pld, str) else pld.get("content", "")
        if txt:
            print(f"[TERM] {_corto(txt, 300)}")
    elif topic == "task.usage":
        print(f"[COSTE] {pld.get('calls_used')}/{pld.get('techo')} llamadas")
    elif topic in ("naoko.log", "ritsuko.log"):
        print(f"[{topic.split('.')[0].upper()}] {_corto(pld.get('content'), 300)}")
    elif topic == "task.cancelled":
        print("[CANCELADA]")
        return True
    return False


async def sesion(encargo: str | None, task_id: str, segundos: float,
                 engine: str, estilo: str) -> None:
    print(f"[MANOS] Conectando con Magisys en {URI} …")
    async with websockets.connect(URI, max_size=None) as ws:
        print(f"[MANOS] Conectado. Tarea: {task_id}")
        if encargo:
            await ws.send(json.dumps({
                "type": "SYS_EXEC",
                "payload": {"command": encargo, "id": task_id,
                            "engine": engine, "narrative_style": estilo},
            }))
            print(f"[MANOS] Encargo enviado ({len(encargo)} caracteres).\n")

        # Se espera a que hablen los tres nodos, no un tiempo fijo: una
        # ronda real tarda lo que tarda el proveedor mas lento.
        vistos: set[str] = set()
        limite = asyncio.get_running_loop().time() + segundos
        while asyncio.get_running_loop().time() < limite:
            try:
                bruto = await asyncio.wait_for(ws.recv(), timeout=20.0)
            except asyncio.TimeoutError:
                print("  · (sin eventos; el enjambre sigue pensando)")
                continue
            except Exception as e:  # noqa: BLE001
                print(f"[AVISO] conexion perdida: {e}")
                break
            try:
                data = json.loads(bruto)
            except ValueError:
                continue
            topic = data.get("topic") or data.get("type", "")
            pld = data.get("payload", {})
            if not isinstance(pld, dict):
                pld = {"content": pld}
            if topic == "AGENT_POST":
                vistos.add(str(pld.get("agent", "")))
            if _pintar(topic, pld):
                break
            if {"MELCHIOR", "BALTHASAR", "CASPER"} <= vistos:
                print("\n[MANOS] Los tres nodos han hablado: ronda completa.")
                break
    print("[MANOS] Sesion cerrada.")


def main() -> int:
    p = argparse.ArgumentParser(description="Hablarle a Magisys por WebSocket")
    p.add_argument("encargo", nargs="?", default=None,
                   help="lo que se le pide; omitido con --escuchar")
    p.add_argument("--tarea", default=None,
                   help="continuar una tarea existente (task_id)")
    p.add_argument("--segundos", type=float, default=420.0)
    p.add_argument("--engine", default="fast", choices=("fast", "deep"))
    p.add_argument("--estilo", default="tecnico")
    p.add_argument("--escuchar", action="store_true",
                   help="solo mirar el bus, sin mandar nada")
    a = p.parse_args()

    if not a.encargo and not a.escuchar:
        p.error("dame un encargo, o usa --escuchar")

    task_id = a.tarea or f"task_{uuid.uuid4().hex[:8]}"
    try:
        asyncio.run(sesion(None if a.escuchar else a.encargo, task_id,
                           a.segundos, a.engine, a.estilo))
    except KeyboardInterrupt:
        print("\n[MANOS] Interrumpido.")
    except OSError as e:
        print(f"[ERROR] No hay nadie escuchando en {URI}: {e}\n"
              f"        Arranca Magisys antes (dist/unpacked/Magisys.exe o "
              f"`python -m magi.main`).")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
