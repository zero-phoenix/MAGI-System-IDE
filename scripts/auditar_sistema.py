"""
Audita el sistema ENTERO en caliente y deja la evidencia medida.

POR QUE EXISTE
==============
"Funciona" y "va rapido" son afirmaciones, y este proyecto no las acepta sin
numero detras. Este script arranca el kernel de verdad, manda una peticion
real por el enjambre y CRONOMETRA cada llamada al modelo: quien la hizo, a que
familia fue, cuanto tardo, si volvio con error y si llevaba identidad.

Lo que mide, y por que cada cosa:

  - arranque:      importar + levantar el kernel. Es lo que el usuario espera
                   mirando una ventana en blanco.
  - por llamada:   familia, proveedor, tag, segundos, error. El tag dice QUIEN
                   la pidio; una llamada sin tag es trabajo que nadie encargo
                   (reintento de idioma, traduccion) y es donde se va la cuota.
  - por etapa:     Naoko (estilo), Melchior (variantes), Balthasar (ejes),
                   Casper (arbitraje). Sin esto "el sistema va lento" no se
                   puede arreglar, solo sufrir.
  - errores:       cualquier evento de error o alerta que pase por el bus.

USO
===
    python scripts/auditar_sistema.py                       # tarea por defecto
    python scripts/auditar_sistema.py --tarea "..." --motor deep
    python scripts/auditar_sistema.py --salida informe.json

La salida es un JSON con todo lo medido y un resumen legible por consola.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

# El cortafuegos de navegador, ANTES de tocar nada que arrastre g4f. Mismo
# orden que `magi/main.py` y por el mismo motivo: una auditoria que abre un
# Chrome deja de medir el sistema y pasa a medir la maquina.
from magi.core.no_browser import install as _cortafuegos  # noqa: E402

_cortafuegos()


#: Cada llamada al modelo, cronometrada. Se rellena desde el envoltorio.
LLAMADAS: list[dict] = []
#: Todo lo que pasa por el bus y merece mirarse, con su instante.
EVENTOS: list[dict] = []


def _instrumentar(t0: float) -> None:
    """
    Envuelve `FreeCloudLLM.generate` SIN cambiar su comportamiento.

    Envolver y no sustituir importa: una auditoria que altera lo que audita
    mide otra cosa. Aqui solo se anota el antes y el despues.
    """
    from magi.core.providers.cloud import FreeCloudLLM

    original = FreeCloudLLM.generate

    async def cronometrada(self, system_prompt, user_prompt, **kw):
        ini = time.perf_counter()
        fila = {
            "t_rel": round(ini - t0, 2),
            "tag": kw.get("tag"),
            "familia": kw.get("family"),
            "modelo": kw.get("model"),
            "hedge": kw.get("hedge"),
            "chars_prompt": len(system_prompt or "") + len(user_prompt or ""),
        }
        try:
            content, provider_id = await original(self, system_prompt, user_prompt, **kw)
            fila.update(segundos=round(time.perf_counter() - ini, 2),
                        proveedor=provider_id, ok=True,
                        chars_respuesta=len(content or ""))
            return content, provider_id
        except Exception as e:
            fila.update(segundos=round(time.perf_counter() - ini, 2),
                        ok=False, error=f"{type(e).__name__}: {e}")
            raise
        finally:
            LLAMADAS.append(fila)

    FreeCloudLLM.generate = cronometrada


#: Cada etapa cronometrada (agente, verificacion). Nombre -> segundos.
ETAPAS: list[dict] = []


def _cronometrar_etapas(t0: float) -> None:
    """
    Cronometra las etapas por ENCIMA de la llamada al modelo.

    La primera version de esta auditoria solo envolvia
    `FreeCloudLLM.generate` y midio 28 s de modelo en una tarea de 200 s.
    Ese hueco no era misterio: el camino principal del enjambre es
    `_ask_stream` â€”que no pasa por `generate`â€” y ademas la verificacion
    ejecuta codigo de verdad. Medir solo una de las tres puertas y concluir
    "el sistema espera al modelo" habria sido exactamente el tipo de informe
    que este proyecto no quiere.
    """
    from magi.core.verification import ProposalVerifier
    from magi.modules.swarm.agents import SwarmAgentBase

    def envolver(clase, nombre):
        original = getattr(clase, nombre, None)
        if original is None:
            return

        async def medida(self, *a, **kw):
            ini = time.perf_counter()
            etiqueta = kw.get("tag") or getattr(self, "role_name", clase.__name__)
            try:
                return await original(self, *a, **kw)
            finally:
                ETAPAS.append({
                    "t_rel": round(ini - t0, 2),
                    "etapa": f"{clase.__name__}.{nombre}",
                    "quien": etiqueta,
                    "segundos": round(time.perf_counter() - ini, 2),
                })

        setattr(clase, nombre, medida)

    for m in ("_ask", "_ask_with_tools", "_ask_stream"):
        envolver(SwarmAgentBase, m)
    envolver(ProposalVerifier, "verify")

    # LA SEGUNDA PUERTA AL MODELO. `_ask` pasa por FreeCloudLLM.generate, pero
    # el bucle de herramientas (`run_agent`) llama a `ProviderRegistry.complete`
    # directamente. Sin envolver las dos, el informe atribuye a "otras cosas"
    # lo que en realidad es esperar al modelo, y el plan de velocidad ataca el
    # sitio equivocado.
    from magi.core.providers.registry import ProviderRegistry
    envolver(ProviderRegistry, "complete")
    envolver(ProviderRegistry, "stream")


#: Temas del bus que se anotan. No es "todo" a proposito: el bus lleva
#: telemetria de grano fino y el informe tiene que caber en una pantalla.
TEMAS = ("AGENT_POST", "TERMINAL_OUT", "swarm.task_completed",
         "swarm.budget_exhausted", "swarm.artefacto_listo", "naoko.log",
         "naoko.status", "naoko.diagnostico", "naoko.improvement",
         "ritsuko.log", "ritsuko.status", "ritsuko.informe",
         "obs.alert", "error.critical", "sonda.actualizada", "task.cancelled")


#: La respuesta final, ENTERA. Los eventos se recortan a 400 caracteres para
#: que el informe quepa en una pantalla, pero la sintesis de Casper es
#: justamente lo que hay que poder leer y comparar: recortarla convertiria la
#: auditoria en un resumen de si misma.
RESPUESTAS: list[dict] = []


def _escuchar(bus, t0: float) -> None:
    for tema in TEMAS:
        def hacer(tema_fijo):
            async def oir(event):
                p = event.payload if isinstance(event.payload, dict) else {"raw": str(event.payload)}
                texto = str(p.get("content") or p.get("result") or p.get("status") or "")
                EVENTOS.append({
                    "t_rel": round(time.perf_counter() - t0, 2),
                    "tema": tema_fijo,
                    "agente": p.get("agent") or p.get("agente"),
                    "texto": texto[:400],
                })
                if tema_fijo in ("AGENT_POST", "swarm.artefacto_listo") and texto:
                    RESPUESTAS.append({
                        "t_rel": round(time.perf_counter() - t0, 2),
                        "tema": tema_fijo,
                        "agente": p.get("agent") or p.get("agente"),
                        "texto": texto,
                        "extra": {k: v for k, v in p.items()
                                  if k not in ("content", "result")},
                    })
            return oir
        bus.subscribe(tema, hacer(tema))


def _etapas() -> dict:
    """
    Reparte el tiempo de modelo por etapa a partir del tag de cada llamada.

    Los tags del enjambre son `<tarea>/r<ronda>/<rama>`; lo que llega sin tag
    NO es ruido que ignorar, es la etiqueta mas importante del informe: es
    trabajo que ninguna rama pidio (reintento de idioma, traduccion, Naoko) y
    por tanto cuota gastada fuera del presupuesto de la tarea.
    """
    por_etapa: dict[str, dict] = {}
    for ll in LLAMADAS:
        tag = ll.get("tag")
        if not tag:
            etapa = "SIN ETIQUETA (fuera del presupuesto)"
        else:
            partes = str(tag).split("/")
            etapa = partes[2] if len(partes) > 2 else str(tag)
        d = por_etapa.setdefault(etapa, {"llamadas": 0, "segundos": 0.0, "errores": 0})
        d["llamadas"] += 1
        d["segundos"] = round(d["segundos"] + (ll.get("segundos") or 0), 2)
        if not ll.get("ok"):
            d["errores"] += 1
    return por_etapa


def _resumen_etapas() -> dict:
    """Segundos y numero de pasadas por etapa, que es lo accionable."""
    d: dict[str, dict] = {}
    for e in ETAPAS:
        r = d.setdefault(e["etapa"], {"veces": 0, "segundos": 0.0})
        r["veces"] += 1
        r["segundos"] = round(r["segundos"] + e["segundos"], 2)
    return d


def _quien_hablo() -> dict:
    """
    Quien aporto y cuanto. La pregunta que contesta es «¿funcionaron los tres?»,
    y un nodo mudo es la respuesta mas barata de obtener y la que nadie mira.
    """
    d: dict[str, dict] = {}
    for r in RESPUESTAS:
        quien = str(r.get("agente") or "?")
        e = d.setdefault(quien, {"veces": 0, "chars": 0, "t_primera": r["t_rel"]})
        e["veces"] += 1
        e["chars"] += len(r["texto"])
    for nodo in ("MELCHIOR", "BALTHASAR", "CASPER"):
        d.setdefault(nodo, {"veces": 0, "chars": 0, "t_primera": None})
    return d


async def auditar(tarea: str, motor: str, rondas: int, espera_s: float,
                  con_ritsuko: bool = False) -> dict:
    t0 = time.perf_counter()
    _instrumentar(t0)

    t_imp = time.perf_counter()
    from magi.core.bus import BusEvent
    from magi.core.kernel import Kernel
    imports_s = round(time.perf_counter() - t_imp, 2)
    _cronometrar_etapas(t0)

    # Puerto distinto del de la app (20128) para poder auditar con MAGI abierto.
    kernel = Kernel(port=20177)
    t_arr = time.perf_counter()
    await kernel.start()
    arranque_s = round(time.perf_counter() - t_arr, 2)

    _escuchar(kernel.bus, t0)

    from magi.core.providers.cloud import get_registry
    reg = await get_registry()
    familias = sorted({getattr(p, "family", "?") for p in getattr(reg, "_providers", [])}) \
        if hasattr(reg, "_providers") else []

    # ID NUEVO EN CADA AUDITORIA, y no es cosmetico. La primera version usaba
    # "auditoria" fijo: la segunda pasada encontro en la base el estado de la
    # primera â€”esperando aprobacionâ€” y trato la peticion como FEEDBACK de
    # aquella tarea. Resultado: 300 s sin una sola llamada al modelo. El fallo
    # es real y esta en el informe, pero una auditoria no puede medirse a si
    # misma tropezando con su propia huella.
    tid = f"auditoria-{int(time.time())}"
    t_tarea = time.perf_counter()
    await kernel.swarm.submit_task(tid, tarea, engine=motor,
                                   narrative_style="tecnico", route="task",
                                   max_rounds=rondas)

    # Se espera a que la tarea termine o pida aprobacion; lo que no se hace es
    # dar por buena una tarea que sigue viva: eso convertiria un cuelgue en un
    # informe verde.
    fin = None
    limite = time.perf_counter() + espera_s
    while time.perf_counter() < limite:
        await asyncio.sleep(1.0)
        estado = kernel.swarm.active_tasks.get(tid, {})
        if estado.get("status") in ("completed", "failed", "WAITING_USER_APPROVAL"):
            fin = estado.get("status")
            break
    tarea_s = round(time.perf_counter() - t_tarea, 2)

    # RITSUKO, DESPUES DE LA TAREA Y NO ANTES. Auditar el sistema en reposo no
    # dice nada: lo que hay que ver es si sabe leer lo que acaba de pasar. Se
    # le pregunta por el bus, igual que haria el usuario desde su pestana, y
    # se espera a que conteste o se anota que no contesto.
    informe_ritsuko = None
    if con_ritsuko:
        antes = len([e for e in EVENTOS if e["tema"] == "ritsuko.log"])
        await kernel.bus.publish(BusEvent(
            topic="ritsuko.user_message",
            payload={"message": "Audita lo que acaba de pasar en el sistema: "
                                "si Naoko hizo bien su trabajo, si los tres "
                                "nodos funcionaron y que recomiendas cambiar."}))
        limite_r = time.perf_counter() + 240
        while time.perf_counter() < limite_r:
            await asyncio.sleep(1.0)
            dichos = [e for e in EVENTOS if e["tema"] == "ritsuko.log"]
            if len(dichos) > antes + 1:
                break
        informes = kernel.ritsuko._informes
        informe_ritsuko = {
            "contesto": len([e for e in EVENTOS if e["tema"] == "ritsuko.log"]) > antes,
            "informes_escritos": len(informes),
            "ruta_ultimo": str(informes[-1].ruta) if informes else None,
            "veredicto": informes[-1].veredicto if informes else None,
            "evidencia": informes[-1].evidencia if informes else None,
        }

    # Cierre a mano: el Kernel no expone `stop()`. Se apagan las tres cosas
    # que dejan el proceso vivo â€” la sonda periodica, el servidor RPC y los
    # workers del busâ€” en ese orden.
    for cierre in (
        lambda: getattr(kernel, "_tarea_sonda", None) and kernel._tarea_sonda.cancel(),
        lambda: kernel.rpc.close(),
        lambda: kernel.bus.shutdown(),
    ):
        try:
            r = cierre()
            if asyncio.iscoroutine(r):
                await asyncio.wait_for(r, timeout=5)
        except Exception:
            pass

    llamadas_ok = [c for c in LLAMADAS if c.get("ok")]
    fallidas = [c for c in LLAMADAS if not c.get("ok")]
    sin_tag = [c for c in LLAMADAS if not c.get("tag")]
    segundos = sorted(c.get("segundos") or 0 for c in llamadas_ok)
    return {
        "tarea": tarea, "task_id": tid, "motor": motor, "rondas": rondas,
        "estado_final": fin or "SIN TERMINAR (limite de espera)",
        "tiempos": {
            "imports_s": imports_s, "arranque_kernel_s": arranque_s,
            "tarea_s": tarea_s, "total_s": round(time.perf_counter() - t0, 2),
        },
        "llamadas": {
            "total": len(LLAMADAS), "ok": len(llamadas_ok),
            "fallidas": len(fallidas), "sin_etiqueta": len(sin_tag),
            "segundos_modelo": round(sum(segundos), 2),
            "mediana_s": segundos[len(segundos) // 2] if segundos else None,
            "peor_s": segundos[-1] if segundos else None,
        },
        "por_etapa": _etapas(),
        "etapas_cronometradas": sorted(ETAPAS, key=lambda e: -e["segundos"])[:40],
        "resumen_etapas": _resumen_etapas(),
        "respuestas": RESPUESTAS,
        "quien_hablo": _quien_hablo(),
        "ritsuko": informe_ritsuko,
        "naoko": {
            "intervenciones": len([e for e in EVENTOS if e["tema"].startswith("naoko.")]),
            "dijo": [e["texto"][:300] for e in EVENTOS
                     if e["tema"] == "naoko.log" and e["texto"]][:10],
        },
        "familias_registradas": familias,
        "detalle_llamadas": LLAMADAS,
        "errores": [c for c in fallidas],
        "eventos": EVENTOS,
    }


def resumir(inf: dict) -> str:
    t, ll = inf["tiempos"], inf["llamadas"]
    lineas = [
        "",
        "=" * 66,
        f"AUDITORIA  Â·  estado final: {inf['estado_final']}",
        "=" * 66,
        f"  arranque: imports {t['imports_s']}s + kernel {t['arranque_kernel_s']}s",
        f"  tarea:    {t['tarea_s']}s de pared, {ll['segundos_modelo']}s de modelo",
        f"  llamadas: {ll['total']} ({ll['fallidas']} con error, "
        f"{ll['sin_etiqueta']} sin etiqueta)",
        f"  latencia: mediana {ll['mediana_s']}s Â· peor {ll['peor_s']}s",
        "",
        "  por etapa:",
    ]
    for etapa, d in sorted(inf["por_etapa"].items(),
                           key=lambda kv: -kv[1]["segundos"]):
        lineas.append(f"    {etapa:38} {d['llamadas']:3} llam  "
                      f"{d['segundos']:7.1f}s  {d['errores']} err")
    if inf.get("resumen_etapas"):
        lineas += ["", "  donde se va el tiempo de pared:"]
        for etapa, d in sorted(inf["resumen_etapas"].items(),
                               key=lambda kv: -kv[1]["segundos"]):
            lineas.append(f"    {etapa:38} {d['veces']:3} vez  {d['segundos']:7.1f}s")
    if inf["errores"]:
        lineas += ["", "  errores:"]
        for e in inf["errores"][:8]:
            lineas.append(f"    [{e.get('familia')}] {e.get('error')}")
    return "\n".join(lineas)


def main() -> int:
    ap = argparse.ArgumentParser(description="Audita el sistema en caliente.")
    ap.add_argument("--tarea", default="Escribe una funcion python que sume "
                                       "dos numeros y su test con pytest.")
    ap.add_argument("--motor", default="fast", choices=["fast", "deep"])
    ap.add_argument("--rondas", type=int, default=1)
    ap.add_argument("--espera", type=float, default=300.0,
                    help="segundos maximos de espera a que la tarea termine")
    ap.add_argument("--salida", default=str(RAIZ / "artifacts" / "auditoria.json"))
    ap.add_argument("--con-ritsuko", action="store_true",
                    help="al terminar, pide a Ritsuko que audite lo ocurrido")
    args = ap.parse_args()

    inf = asyncio.run(auditar(args.tarea, args.motor, args.rondas, args.espera,
                              con_ritsuko=args.con_ritsuko))
    destino = Path(args.salida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(inf, indent=2, ensure_ascii=False), encoding="utf-8")
    print(resumir(inf))
    print(f"\n  informe completo: {destino}")
    return 0 if inf["estado_final"] != "SIN TERMINAR (limite de espera)" else 1


if __name__ == "__main__":
    raise SystemExit(main())
