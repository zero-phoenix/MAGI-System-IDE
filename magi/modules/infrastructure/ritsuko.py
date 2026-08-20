"""
RITSUKO — la quinta IA: audita a Naoko, no al usuario ni al código.

QUÉ VIGILA, Y POR QUÉ HACÍA FALTA
=================================
El sistema tiene tres nodos que debaten (Melchior, Balthasar, Casper) y una
cuarta IA, Naoko, que los corrige: detecta deriva, reordena el reparto, propone
mejoras y las aplica. Naoko es, literalmente, quien arregla al enjambre.

Nadie comprobaba a Naoko.

Ese hueco no es teórico: la auditoría del 2026-08-20 encontró a Naoko
declarando «deriva» en dos familias enteras justo después de una tarea real,
con 0/3 canarios correctos — un diagnóstico que casi con seguridad medía la
cuota agotada, no el modelo. Un corrector que se equivoca sin que nadie lo
revise mueve el sistema en la dirección equivocada con toda la autoridad.

Ritsuko es ese revisor. Su trabajo es exactamente el que haría un auditor
externo: mirar la evidencia, decir si el sistema mejora o empeora, y señalar
cuándo Naoko no está haciendo bien su trabajo.

LO QUE RITSUKO NO PUEDE HACER, A PROPÓSITO
==========================================
No escribe código, no ejecuta nada, no aplica parches, no toca el reparto, no
cancela tareas y no habla con los tres nodos. **Solo informa.** Un auditor con
permiso para arreglar deja de ser auditor a la segunda vez que arregla algo,
porque a partir de ahí se está revisando a sí mismo.

Todo lo que quiere cambiar sale como informe o como megaplan, en un fichero que
el usuario puede leer, descargar y decidir.

FAMILIA DISTINTA, Y ESTO NO ES UN DETALLE
=========================================
Melchior usa `hf`, Balthasar `gemini`, Casper `gpt`, y Naoko rota entre
`claude`, `gemini`, `command` y `gpt`. Ritsuko usa `razonamiento` y su cadena
de respaldo **nunca** cae en una familia auditada.

El motivo es el mismo por el que un auditor no puede compartir contabilidad con
el auditado: si el proveedor que sostiene a Casper se cae o empieza a responder
basura, un auditor de esa misma familia se cae con él — y justo cuando más
falta hace. La independencia aquí es técnica, no ceremonial.

IDIOMA
======
Español o inglés. Nada más, y no por gusto: los informes de Ritsuko se leen
para decidir. Un informe en un idioma que el usuario no lee es un informe que
no existe, y este sistema ya tuvo el problema de verdad (un «hola» contestado
en chino). Si el modelo se sale del idioma, se reintenta con otro proveedor
antes de entregar.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from magi.core import idioma
from magi.core.bus import BusEvent, MagiBus
from magi.core.paths import data_dir
from magi.core.providers.cloud import FreeCloudLLM

logger = logging.getLogger(__name__)

__all__ = ["RitsukoAgent", "Informe", "FAMILIAS_AUDITADAS", "MODELOS_RITSUKO"]

#: Las familias que usa el resto del sistema. Ritsuko no puede usar ninguna:
#: ver la cabecera. Se declara aquí y no se deduce en caliente porque un
#: auditor que elige proveedor según el estado del auditado ya no es
#: independiente.
FAMILIAS_AUDITADAS = ("hf", "gemini", "gpt", "claude", "command")

#: Cadena de Ritsuko, en orden. Todos son de familias que NO audita nadie más
#: (`razonamiento`, `grok`, `perplexity`). Si un día entran al enjambre, hay
#: que sacarlos de aquí — y el test `test_ritsuko_no_comparte_familia` lo exige.
MODELOS_RITSUKO = ("o3", "o4mini", "pplx_reasoning", "grok4")

#: C14 — la cadena que SE USA, por familia y no por alias de modelo.
#:
#: El eje que garantiza la independencia es la familia. Los alias se resuelven
#: a familia por una tabla que Ritsuko no controla, y la prueba del 20-ago la
#: dejó fallando con «familia 'deepseek' agotada» —que no es ninguna de las
#: suyas—, así que su independencia dependía de un mapeo que puede cambiar sin
#: que nadie se entere. Pidiendo por familia, no puede pasar.
FAMILIAS_RITSUKO = ("razonamiento", "grok", "perplexity")

#: Idiomas que Ritsuko puede hablar. No es configurable.
IDIOMAS_PERMITIDOS = ("es", "en")

#: Cuántos eventos del bus se guardan para razonar sobre ellos. Es una ventana,
#: no un historial: Ritsuko opina sobre lo que está pasando, y para lo antiguo
#: está la base de datos.
VENTANA_EVENTOS = 400


#: Marcas con las que el sistema devuelve un fallo DISFRAZADO de respuesta.
#: Están aquí y no dispersas porque el patrón se repite: `cloud.py` devuelve
#: `[Inferencia no disponible: ...]` con proveedor `SYSTEM_ERROR`, y el bucle
#: de herramientas devuelve `[Tiempo de espera agotado ...]`. Las dos son
#: cadenas normales que cualquiera puede tratar como contenido bueno, y así es
#: como se acaba firmando un veredicto sobre un error.
MARCAS_DEGRADADAS = ("[Inferencia no disponible",
                     "[Tiempo de espera agotado",
                     "todos los proveedores fallaron")


def _es_degradada(texto: str | None) -> bool:
    t = (texto or "").strip()
    return any(t.startswith(m) or m in t[:200] for m in MARCAS_DEGRADADAS)


@dataclass
class Informe:
    """Lo que Ritsuko entrega: un veredicto con la evidencia que lo sostiene."""

    motivo: str                                   # qué disparó la auditoría
    veredicto: str = ""                           # el texto del modelo
    evidencia: dict = field(default_factory=dict)  # lo medido, sin interpretar
    ruta: Path | None = None                      # el .md descargable
    instante: str = ""

    def to_dict(self) -> dict:
        return {
            "motivo": self.motivo,
            "veredicto": self.veredicto,
            "evidencia": self.evidencia,
            "ruta": str(self.ruta) if self.ruta else None,
            "instante": self.instante,
        }


class RitsukoAgent:
    """
    Audita la relación entre Naoko y los tres nodos, y solo eso.

    Se alimenta de lo que ya pasa por el bus —no instrumenta nada ni pregunta
    a nadie— porque un observador que modifica lo observado mide otra cosa.
    """

    ROL = "RITSUKO"

    def __init__(self, bus: MagiBus, db=None, swarm=None, naoko=None,
                 metrics=None):
        self.bus = bus
        self.db = db
        self.swarm = swarm
        self.naoko = naoko
        self.metrics = metrics
        self.llm = FreeCloudLLM()
        self.activa = False
        #: Ventana de evidencia. Cada entrada: (t, tema, quién, texto).
        self._eventos: list[dict] = []
        self._informes: list[Informe] = []
        self._t0 = time.monotonic()

    # ------------------------------------------------------------ arranque

    async def start(self) -> None:
        """
        Se suscribe a lo que hace falta para juzgar, y a nada más.

        Los cuatro grupos son deliberados:
          · `naoko.*`      — lo que el corrector dice y decide. Es el sujeto.
          · `AGENT_POST`   — lo que producen los tres corregidos.
          · `swarm.*`      — si las tareas terminan, se agotan o se rompen.
          · alertas        — lo que el propio sistema considera anómalo.
        """
        for tema in ("naoko.log", "naoko.status", "naoko.diagnostico",
                     "naoko.improvement", "AGENT_POST", "swarm.task_completed",
                     "swarm.budget_exhausted", "obs.alert", "error.critical",
                     "sonda.actualizada"):
            self.bus.subscribe(tema, self._anotar)
        self.bus.subscribe("ritsuko.user_message", self._handle_user_message)
        self.activa = True
        logger.info("[ritsuko] auditora en linea (familia razonamiento)")

    async def _anotar(self, event: BusEvent) -> None:
        p = event.payload if isinstance(event.payload, dict) else {"raw": str(event.payload)}
        self._eventos.append({
            "t": round(time.monotonic() - self._t0, 1),
            "tema": event.topic,
            "quien": p.get("agent") or p.get("agente") or p.get("status"),
            "texto": str(p.get("content") or p.get("result") or
                         p.get("motivo") or p.get("status") or "")[:600],
        })
        if len(self._eventos) > VENTANA_EVENTOS:
            del self._eventos[:len(self._eventos) - VENTANA_EVENTOS]


    # ----------------------------------------------------------- evidencia

    def evidencia(self) -> dict:
        """
        Lo que se puede afirmar del sistema AHORA, sin pedirle nada a nadie.

        Todo sale de estructuras vivas. Si una no está disponible se dice que
        no está, en vez de rellenar con un valor plausible: un informe con un
        número inventado es peor que un informe con un hueco.
        """
        ev: dict = {"ventana_eventos": len(self._eventos)}

        naoko_dice = [e for e in self._eventos if e["tema"].startswith("naoko.")]
        ev["naoko"] = {
            "intervenciones": len(naoko_dice),
            "derivas_declaradas": sum(1 for e in naoko_dice
                                      if "deriva" in e["texto"].lower()),
            "ultimas": [e["texto"][:200] for e in naoko_dice[-3:]],
        }

        posts = [e for e in self._eventos if e["tema"] == "AGENT_POST"]
        por_nodo: dict[str, int] = {}
        for e in posts:
            por_nodo[str(e["quien"])] = por_nodo.get(str(e["quien"]), 0) + 1
        ev["nodos"] = {"aportaciones": por_nodo, "total": len(posts)}
        # Un nodo callado es la señal más barata de que algo se rompió, y la
        # que nadie mira: el sistema sigue "funcionando" con dos de tres.
        ev["nodos"]["mudos"] = [n for n in ("MELCHIOR", "BALTHASAR", "CASPER")
                                if not por_nodo.get(n)]

        # D7 — LO QUE MÁS IMPORTA TIENE QUE ESTAR EN LA EVIDENCIA.
        #
        # En la prueba del 20-ago Ritsuko dijo «SIN DATOS SUFICIENTES» teniendo
        # delante el hallazgo más importante de la sesión: un encargo de
        # producto cerrado sin artefacto y marcado `[INCOMPLETO]`. No lo vio
        # porque su evidencia no incluía nada sobre la entrega. Un auditor solo
        # puede ver lo que le pones en la mesa.
        entregas = [e for e in self._eventos
                    if "[INCOMPLETO]" in e["texto"] or "[FÁBRICA]" in e["texto"]
                    or e["tema"] == "swarm.artefacto_listo"]
        ev["entrega"] = {
            "artefactos_listos": sum(1 for e in self._eventos
                                     if e["tema"] == "swarm.artefacto_listo"),
            "marcada_incompleta": any("[INCOMPLETO]" in e["texto"]
                                      for e in self._eventos),
            "sin_contestar": [e["texto"][:200] for e in self._eventos
                              if "[SIN CONTESTAR]" in e["texto"]],
            "mensajes": [e["texto"][:200] for e in entregas[-5:]],
        }

        ev["incidencias"] = {
            "alertas": sum(1 for e in self._eventos if e["tema"] == "obs.alert"),
            "errores": sum(1 for e in self._eventos if e["tema"] == "error.critical"),
            "presupuestos_agotados": sum(1 for e in self._eventos
                                         if e["tema"] == "swarm.budget_exhausted"),
        }

        if self.metrics is not None:
            try:
                ev["metricas"] = self.metrics.snapshot()
            except Exception as e:                        # pragma: no cover
                ev["metricas"] = {"no_disponible": str(e)}

        if self.swarm is not None:
            try:
                ev["tareas_vivas"] = {
                    tid: st.get("status")
                    for tid, st in getattr(self.swarm, "active_tasks", {}).items()
                }
            except Exception as e:                        # pragma: no cover
                ev["tareas_vivas"] = {"no_disponible": str(e)}

        ultima = data_dir() / "auditoria.json"
        alterna = Path("artifacts") / "auditoria.json"
        for candidata in (ultima, alterna):
            if candidata.is_file():
                try:
                    datos = json.loads(candidata.read_text(encoding="utf-8"))
                    ev["ultima_auditoria"] = {
                        "estado": datos.get("estado_final"),
                        "tiempos": datos.get("tiempos"),
                        "llamadas": datos.get("llamadas"),
                        "por_etapa": datos.get("resumen_etapas"),
                    }
                except Exception:                          # pragma: no cover
                    pass
                break
        return ev


    # -------------------------------------------------------------- prompt

    PROMPT = (
        "Eres RITSUKO, la auditora del sistema MAGI. Tu unico trabajo es "
        "revisar si NAOKO corrige bien a los tres nodos del enjambre "
        "(MELCHIOR propone, BALTHASAR refuta, CASPER arbitra).\n\n"
        "REGLAS QUE NO PUEDES ROMPER:\n"
        "1. No arreglas nada. No escribes codigo para aplicar, no ejecutas "
        "nada, no cambias configuracion. Solo informas.\n"
        "2. Cada afirmacion va con la evidencia que la sostiene, sacada de los "
        "datos que se te dan. Si un dato no esta, se dice que falta; no se "
        "estima ni se rellena.\n"
        "3. Juzgas a NAOKO y a su relacion con los tres nodos: si sus "
        "diagnosticos se sostienen, si sus correcciones mejoran o empeoran el "
        "sistema, y si algun nodo esta mudo o degradado.\n"
        "4. Distingues SIEMPRE entre 'el modelo falla' y 'la cuota se agoto'. "
        "Confundirlos es el error mas caro de este sistema.\n"
        "5. Respondes en el idioma del usuario si es espanol o ingles. Nunca "
        "en otro idioma.\n"
        "6. CON EVIDENCIA DE UN INCUMPLIMIENTO, EL VEREDICTO NO PUEDE SER "
        "'SIN DATOS SUFICIENTES'. Si `entrega.marcada_incompleta` es cierto, o "
        "si un encargo de producto acabo con `artefactos_listos: 0`, o si hay "
        "algo en `entrega.sin_contestar`, eso YA es un hallazgo: nombralo. "
        "'Sin datos' es para cuando no hay datos, no para cuando los datos son "
        "incomodos.\n\n"
        "FORMATO: un veredicto de una linea (MEJORA / IGUAL / EMPEORA / SIN "
        "DATOS SUFICIENTES), despues los hallazgos con su evidencia, y al "
        "final lo que recomiendas que NAOKO haga distinto."
    )

    def _idioma_del_usuario(self, texto: str) -> str:
        detectado = idioma.detectar(texto or "", por_defecto="es")
        return detectado if detectado in IDIOMAS_PERMITIDOS else "es"

    async def _pensar(self, user_prompt: str, lang: str = "es") -> str:
        """
        Rota por los modelos de Ritsuko, y solo por los suyos.

        Dos guardas, las dos aprendidas de fallos reales del proyecto:

        · Ninguna familia auditada, ni siquiera como ultimo recurso. Preferimos
          decir "no hay auditora disponible" a entregar un veredicto emitido
          por el mismo proveedor que sostiene al auditado.
        · Si la respuesta no viene en espanol o ingles, se descarta y se pasa
          al siguiente. Un informe ilegible no es un informe.
        """
        instruccion = ("Responde en espanol." if lang == "es"
                       else "Answer in English.")
        sistema = f"{self.PROMPT}\n\nIDIOMA: {instruccion}"
        ultimo_error = "sin proveedores"
        for familia in FAMILIAS_RITSUKO:
            await self.bus.publish(BusEvent(
                topic="ritsuko.status",
                payload={"status": f"Auditando ({familia})..."}))
            try:
                texto, proveedor = await self.llm.generate(sistema, user_prompt,
                                                           family=familia)
            except Exception as e:
                ultimo_error = f"{type(e).__name__}: {e}"
                logger.debug("[ritsuko] %s fallo: %s", familia, e)
                continue
            # UN FALLO QUE VIENE COMO TEXTO SIGUE SIENDO UN FALLO.
            #
            # `cloud.py` devuelve `("[Inferencia no disponible: ...]",
            # "SYSTEM_ERROR")` y el bucle de herramientas devuelve
            # "[Tiempo de espera agotado tras 150s...]". Las dos son cadenas
            # normales: quien no mire el `provider_id` se las traga como
            # respuesta. Esto lo cazo en mi propia primera version —la prueba
            # del 20-ago dejo un informe de Ritsuko cuyo veredicto era
            # literalmente el mensaje de error— y es exactamente el mismo fallo
            # que el enjambre comete al firmar APPROVED sobre un timeout.
            if proveedor == "SYSTEM_ERROR" or _es_degradada(texto):
                ultimo_error = f"{familia}: respuesta degradada ({(texto or '')[:80]})"
                logger.warning("[ritsuko] %s", ultimo_error)
                continue
            if not (texto or "").strip():
                ultimo_error = f"{familia} devolvio vacio"
                continue
            if not idioma.coincide(texto, lang):
                ultimo_error = f"{familia} contesto fuera de idioma"
                logger.warning("[ritsuko] %s", ultimo_error)
                continue
            return texto
        return ("[RITSUKO] No he podido emitir veredicto: ninguno de mis "
                f"proveedores respondio en condiciones ({ultimo_error}). "
                "No uso las familias del enjambre ni las de Naoko a proposito, "
                "asi que prefiero decirlo a firmar un informe que no es mio.")


    # ------------------------------------------------------------ informes

    def carpeta_informes(self) -> Path:
        destino = data_dir() / "informes-ritsuko"
        destino.mkdir(parents=True, exist_ok=True)
        return destino

    async def auditar(self, motivo: str = "peticion", lang: str = "es",
                      pregunta: str = "") -> Informe:
        """
        Emite un informe con veredicto y lo deja escrito en disco.

        Escribirlo SIEMPRE, incluso cuando el veredicto es "sin datos": la
        serie de informes es la unica forma de responder a la pregunta que de
        verdad importa —«¿esto va mejorando?»— y una serie con huecos donde no
        habia datos no sirve para comparar.
        """
        ev = self.evidencia()
        pregunta = pregunta or "Emite tu informe de auditoria del sistema."
        cuerpo = (
            f"{pregunta}\n\n"
            f"EVIDENCIA (JSON, medida, sin interpretar):\n"
            f"{json.dumps(ev, ensure_ascii=False, indent=2)[:6000]}\n\n"
            f"ULTIMOS EVENTOS DEL BUS:\n"
            + "\n".join(f"  [{e['t']}s] {e['tema']} {e['quien'] or ''}: "
                        f"{e['texto'][:180]}"
                        for e in self._eventos[-25:])
        )
        veredicto = await self._pensar(cuerpo, lang)
        inf = Informe(motivo=motivo, veredicto=veredicto, evidencia=ev,
                      instante=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        inf.ruta = self._escribir(inf)
        self._informes.append(inf)
        await self.bus.publish(BusEvent(topic="ritsuko.informe",
                                        payload=inf.to_dict()))
        return inf

    def _escribir(self, inf: Informe) -> Path:
        sello = time.strftime("%Y%m%d-%H%M%S")
        ruta = self.carpeta_informes() / f"informe-{sello}.md"
        ruta.write_text(
            f"# Informe de Ritsuko — {inf.instante}\n\n"
            f"**Motivo:** {inf.motivo}\n\n"
            f"## Veredicto\n\n{inf.veredicto}\n\n"
            f"## Evidencia medida\n\n```json\n"
            f"{json.dumps(inf.evidencia, ensure_ascii=False, indent=2)}\n```\n\n"
            f"## Ultimos eventos observados\n\n"
            + "\n".join(f"- `[{e['t']}s]` **{e['tema']}** {e['quien'] or ''}: "
                        f"{e['texto'][:220]}"
                        for e in self._eventos[-30:])
            + "\n\n---\n_Ritsuko solo audita. No aplica cambios: lo que ves "
              "aqui es una recomendacion, y decides tu._\n",
            encoding="utf-8")
        return ruta

    async def megaplan(self, lang: str = "es") -> Informe:
        """
        Un plan de mejora listo para descargar, con la misma regla de siempre:
        cada punto lleva que se gana y como se comprueba. Un plan que no se
        puede verificar es una lista de deseos.
        """
        inf = await self.auditar(
            motivo="megaplan", lang=lang,
            pregunta=("Redacta un MEGAPLAN de mejora del sistema. Cada punto: "
                      "problema con su evidencia, que se hace, que se gana "
                      "(estimado sobre lo medido) y como se comprueba que "
                      "funciono. Ordenado por relacion beneficio/coste."))
        return inf


    # ---------------------------------------------------------------- chat

    #: Verbos que delatan que se le esta pidiendo ACTUAR, no informar. Ritsuko
    #: no los ejecuta: contesta con lo que si puede hacer. Se comparan palabras
    #: enteras y sin acentos —el mismo error que ya costo caro en el
    #: orquestador, donde un `in` sobre subcadenas aprobaba tareas por el «si»
    #: de «siempre»—.
    VERBOS_DE_ACCION = ("arregla", "arreglalo", "corrige", "aplica", "cambia",
                        "modifica", "instala", "borra", "ejecuta", "lanza",
                        "despliega", "fix", "apply", "deploy", "run", "delete")

    def _piden_actuar(self, mensaje: str) -> bool:
        limpio = idioma.sin_acentos(mensaje).lower() if hasattr(idioma, "sin_acentos") \
            else mensaje.lower()
        palabras = {p.strip(".,;:!?¿¡()") for p in limpio.split()}
        return bool(palabras & set(self.VERBOS_DE_ACCION))

    async def _handle_user_message(self, event: BusEvent) -> None:
        p = event.payload if isinstance(event.payload, dict) else {}
        mensaje = str(p.get("message", "")).strip()
        if not mensaje:
            return
        lang = self._idioma_del_usuario(mensaje)
        await self.bus.publish(BusEvent(
            topic="ritsuko.log", payload={"agent": "USER", "content": mensaje}))
        await self.bus.publish(BusEvent(
            topic="ritsuko.status", payload={"status": "Revisando..."}))
        try:
            bajo = mensaje.lower()
            if any(k in bajo for k in ("megaplan", "mega plan", "plan de mejora")):
                inf = await self.megaplan(lang=lang)
                respuesta = inf.veredicto
                extra = (f"\n\n[Descargable] {inf.ruta}" if inf.ruta else "")
            elif self._piden_actuar(mensaje):
                # No es una negativa decorativa: es la razon por la que Ritsuko
                # puede juzgar a Naoko sin ser juez y parte.
                respuesta = (
                    "No puedo hacerlo yo: solo audito. Puedo decirte que "
                    "encuentro, con la evidencia, y dejarte el informe "
                    "escrito para que lo decidas tu o se lo pases a Naoko."
                    if lang == "es" else
                    "I can't do that myself: I only audit. I can tell you what "
                    "I find, with the evidence, and leave you the written "
                    "report so you or Naoko can act on it.")
                inf = await self.auditar(motivo="peticion de accion", lang=lang)
                respuesta += "\n\n" + inf.veredicto
                extra = (f"\n\n[Descargable] {inf.ruta}" if inf.ruta else "")
            else:
                inf = await self.auditar(motivo="pregunta del usuario",
                                         lang=lang, pregunta=mensaje)
                respuesta = inf.veredicto
                extra = (f"\n\n[Descargable] {inf.ruta}" if inf.ruta else "")
            await self.bus.publish(BusEvent(
                topic="ritsuko.log",
                payload={"agent": "RITSUKO", "content": respuesta + extra}))
        except Exception as e:                             # pragma: no cover
            logger.exception("[ritsuko] fallo atendiendo al usuario")
            await self.bus.publish(BusEvent(
                topic="ritsuko.log",
                payload={"agent": "RITSUKO",
                         "content": f"Error interno en Ritsuko: {e}"}))
        finally:
            await self.bus.publish(BusEvent(
                topic="ritsuko.status", payload={"status": "Inactiva"}))


    # ------------------------------------------------------- superficie RPC

    async def rpc_chat(self, payload, websocket=None) -> dict:
        """Entrada del chat propio de Ritsuko (`ritsuko.chat`)."""
        msg = payload.get("message", "") if isinstance(payload, dict) else str(payload)
        await self.bus.publish(BusEvent(topic="ritsuko.user_message",
                                        payload={"message": msg}))
        return {"status": "ok"}

    async def rpc_informes(self, payload=None, websocket=None) -> dict:
        """
        Lista los informes para poder descargarlos.

        Devuelve la RUTA REAL en disco, no un identificador opaco: se pidieron
        informes descargables, y un botón que no sabe decir dónde está el
        fichero acaba siendo un botón que no descarga nada.
        """
        carpeta = self.carpeta_informes()
        informes = sorted(carpeta.glob("informe-*.md"), reverse=True)[:50]
        return {"carpeta": str(carpeta),
                "informes": [{"nombre": p.name, "ruta": str(p),
                              "bytes": p.stat().st_size,
                              "modificado": p.stat().st_mtime}
                             for p in informes]}
