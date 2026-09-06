"""
Cliente interactivo para comunicarse con MAGI System IDE via WebSocket
simulando la entrada manual de usuario en la interfaz GUI.
"""
import asyncio
import json
import sys
import uuid
import websockets

PROMPT_ENCARGO = (
    "Mejora yabausevita de mi GitHub (C:\\Users\\D\\Documents\\GitHub\\yabausevita) "
    "aplicando la filosofía de diseño ortogonal. Integra y prueba yabausevita "
    "en Vita3K (C:\\Users\\D\\Documents\\GitHub\\yabausevita\\vita3k\\Vita3K.exe), "
    "implementando la arquitectura limpia para entrada sceCtrl, separación modular "
    "de subsistemas y verificación de integridad con Lilim (ojos, oídos y brazos)."
)

async def main():
    uri = "ws://127.0.0.1:20128"
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    print(f"[MANOS] Conectando con MAGI System IDE en {uri}...")
    
    async with websockets.connect(uri) as ws:
        print(f"[MANOS] Conectado. Enviando comando como usuario (task_id: {task_id})...")
        
        # Enviar comando igual que handleExecute() de App.tsx
        cmd_msg = {
            "type": "SYS_EXEC",
            "payload": {
                "command": PROMPT_ENCARGO,
                "id": task_id,
                "engine": "fast",
                "narrative_style": "tecnico"
            }
        }
        await ws.send(json.dumps(cmd_msg))
        print(f"[MANOS] Comando enviado con éxito. Escuchando dialéctica del enjambre...")
        
        # Escuchar eventos durante 45 segundos
        t_fin = asyncio.get_event_loop().time() + 45.0
        while asyncio.get_event_loop().time() < t_fin:
            try:
                msg_raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(msg_raw)
                topic = data.get("topic") or data.get("type", "")
                pld = data.get("payload", {})
                
                if topic == "TERMINAL_OUT":
                    txt = pld if isinstance(pld, str) else pld.get("content", str(pld))
                    print(f"  [TERMINAL] {txt}")
                elif topic == "swarm.routed":
                    print(f"  [ENRUTADO] Ruta={pld.get('route')} Confianza={pld.get('confidence')} Razón={pld.get('reason')}")
                elif topic in ("MELCHIOR", "BALTHASAR", "CASPER"):
                    agente = topic
                    contenido = pld.get("content") or pld.get("texto", "")
                    print(f"  [{agente}] {contenido[:150]}...")
                elif topic == "task.titled":
                    print(f"  [TITULO] {pld.get('title')}")
                else:
                    if "event" in str(topic):
                        pass
            except asyncio.TimeoutError:
                print("  [ESPERA] Aguardando turnos de inferencia...")
            except Exception as e:
                print(f"  [AVISO] {e}")
                break

    print("[MANOS] Sesión de interacción completada.")

if __name__ == "__main__":
    asyncio.run(main())
