"""
Sonda de latencia: qué candidato responde, cuánto tarda y en qué idioma.

POR QUÉ EXISTE
==============
El panel del sistema tiene una columna que se llama **«latencia medida»** y en
la que casi todas las filas dicen «sin medir». Las pocas que traen número
salían de una medición suelta guardada a mano en el catálogo. Con eso:

  · el orden en que se prueban los candidatos era el orden de una lista escrita
    a mano, no el de quién responde antes;
  · trece proveedores estaban marcados como «rotos» con una etiqueta fija, sin
    que nada volviera a comprobarlo nunca — incluidos tres cuyo problema es
    temporal (una cuota de 429 se repone en horas);
  · y el usuario veía turnos de 74 segundos mientras en la misma familia había
    un candidato que respondía en uno.

Esta sonda manda un **prompt canario** minúsculo a cada candidato, mide, y
guarda el resultado. Ninguna cifra de este módulo está escrita a mano: o se
midió, o se dice que no hay medición.

LA MEDIA HISTÓRICA ES LA MEDIA DE LAS MEDIAS DIARIAS
====================================================
No es lo mismo que la media de todas las mediciones, y la diferencia importa:

    día 1   500 mediciones,  media  1 000 ms
    día 2     4 mediciones,  media 30 000 ms   (el proveedor tuvo un mal día)

    media de todas las mediciones : ~1 230 ms  ← el día malo desaparece
    media de las medias diarias   : 15 500 ms  ← el día malo cuenta

La primera premia al candidato que se usó mucho un día bueno. La segunda da a
cada día el mismo peso, que es lo que responde a la pregunta que de verdad se
hace: *«¿de este candidato me puedo fiar un día cualquiera?»*.

Formalmente, con `n` días que tienen alguna medición:

    media_historica = ( Σ media_del_dia_i ) / n

Los días SIN mediciones no entran en `n`. Incluirlos como cero mentiría hacia
abajo; incluirlos como el peor caso mentiría hacia arriba. No hay dato, no hay
día.

REGLA DE ORO, HEREDADA DE LA TELEMETRÍA
=======================================
**Medir no puede romper lo medido.** La sonda es cancelable, tiene tope de
concurrencia y de mediciones por candidato y día, y cualquier fallo suyo se
traga: un sistema que se cae porque no pudo medir es peor que uno sin medidas.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

logger = logging.getLogger(__name__)

__all__ = [
    "Medicion", "EstadoCandidato", "PROMPT_CANARIO", "RESPUESTA_ESPERADA",
    "SEÑALES_ESPERADAS",
    "registrar", "medias_por_dia", "media_historica", "estado_de_candidatos",
    "resumen_para_panel", "medir_candidato", "medir_todo",
    "medias_por_familia", "toca_sondear", "refrescar_si_toca",
    "INTERVALO_REFRESCO_S",
]

#: EL CANARIO, Y POR QUÉ DEJÓ DE SER «di: funciona»
#: ================================================
#: La primera versión pedía literalmente `Responde únicamente con la palabra:
#: funciona`. Parecía ideal —barato, verificable— y tenía un defecto que solo
#: se ve midiendo: **suspendía al mejor proveedor del sistema**.
#:
#: Medido el 2026-08-13, `Perplexity` (el que sirve los modelos Claude) es un
#: motor de búsqueda por dentro, y ante esa orden contesta:
#:
#:     'No entiendo la consulta "di: funciona". ¿Podrías...'
#:
#: Con el mismo proveedor y una pregunta técnica de verdad, en cambio, responde
#: correctamente en 4,2 s. O sea: el examen medía la capacidad de obedecer una
#: orden artificial, no la de servir para lo que este sistema hace.
#:
#: El canario nuevo es una pregunta real, breve y con respuesta verificable.
#: Cuesta unos pocos tokens más y mide lo que importa.
PROMPT_CANARIO = ("En una sola frase: ¿qué diferencia hay entre un mutex y "
                  "un semáforo?")

#: Señales de que ENTENDIÓ la pregunta, en cualquiera de los idiomas admitidos.
#: No se puntúa la calidad de la respuesta —eso sería evaluar el modelo, no su
#: disponibilidad—: se comprueba que habla del tema y no de otra cosa.
SEÑALES_ESPERADAS = ("mutex", "semáforo", "semaforo", "semaphore",
                     "exclusión", "exclusion", "hilo", "thread",
                     "contador", "counter", "bloqueo", "lock")

#: Se conserva el nombre antiguo por compatibilidad con quien lo importe.
RESPUESTA_ESPERADA = "mutex"

#: Tope de mediciones por candidato y día. Sondear cuesta cuota, y la cuota es
#: la del usuario: si la sonda se la gasta, ha empeorado el sistema.
MAX_POR_DIA = 24

#: Cuántos candidatos se miden a la vez. Sin tope, sondear 30 candidatos abre
#: 30 conexiones simultáneas y la propia medición se contamina: se estaría
#: midiendo la congestión de la red, no la latencia del proveedor.
CONCURRENCIA = 4

#: Plazo por medición. Un canario de cinco tokens que tarda más de esto está
#: caído a efectos prácticos, y esperar más solo alarga la sonda.
PLAZO_S = 45.0


@dataclass(frozen=True)
class Medicion:
    """Una llamada del canario a un candidato."""
    familia: str
    proveedor: str
    modelo: str = ""
    ok: bool = False
    ms: float | None = None
    tipo_error: str | None = None
    detalle: str | None = None
    idioma_ok: bool | None = None
    ts: float = field(default_factory=time.time)

    @property
    def clave(self) -> tuple[str, str, str]:
        return (self.familia, self.proveedor, self.modelo)


@dataclass(frozen=True)
class EstadoCandidato:
    """
    Lo que la sonda sabe de un candidato. Todo medido, nada supuesto.

    `media_historica_ms` es None cuando no hay ni una medición correcta: es la
    diferencia entre «no lo sé» y «tarda 0 ms», y confundirlas es cómo un panel
    acaba ordenando por un número inventado.
    """
    familia: str
    proveedor: str
    modelo: str
    media_historica_ms: float | None
    ultima_ms: float | None
    dias_con_datos: int
    mediciones: int
    exitos: int
    ultimo_intento: float | None
    ultimo_exito: float | None
    tipo_error: str | None
    idioma_ok: bool | None

    @property
    def tasa_exito(self) -> float | None:
        if not self.mediciones:
            return None
        return round(self.exitos / self.mediciones, 3)

    @property
    def vivo(self) -> bool:
        """Respondió correctamente la última vez que se le preguntó."""
        return self.ultimo_exito is not None and self.ultimo_exito == self.ultimo_intento

    @property
    def medido(self) -> bool:
        return self.media_historica_ms is not None


def _dia(ts: float) -> str:
    """Día local en ISO. Ver la nota de la migración sobre por qué se guarda."""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


# ------------------------------------------------------------------ escritura

def registrar(store, m: Medicion) -> bool:
    """
    Guarda una medición. Devuelve False si no se pudo, sin lanzar.

    Que no lance es deliberado: esto lo llama un bucle de fondo, y una sonda
    que tumba el sistema por no poder escribir su propia métrica es exactamente
    lo que la regla de oro de la telemetría prohíbe.
    """
    try:
        with store._conn() as c:
            c.execute(
                "INSERT INTO sonda_latencia (ts, dia, familia, proveedor, modelo,"
                " ok, ms, tipo_error, detalle, idioma_ok)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (m.ts, _dia(m.ts), m.familia, m.proveedor, m.modelo,
                 1 if m.ok else 0, m.ms, m.tipo_error,
                 (m.detalle or "")[:500] or None,
                 None if m.idioma_ok is None else (1 if m.idioma_ok else 0)))
        return True
    except Exception as e:                                  # pragma: no cover
        logger.debug("[sonda] no se pudo registrar la medición: %s", e)
        return False


def mediciones_hoy(store, familia: str, proveedor: str, modelo: str = "") -> int:
    """Cuántas veces se ha sondeado hoy este candidato (para el tope diario)."""
    try:
        with store._conn() as c:
            f = c.execute(
                "SELECT COUNT(*) n FROM sonda_latencia"
                " WHERE familia=? AND proveedor=? AND modelo=? AND dia=?",
                (familia, proveedor, modelo, _dia(time.time()))).fetchone()
        return int(f["n"] or 0)
    except Exception:                                       # pragma: no cover
        return 0


# ------------------------------------------------------------------- lectura

def medias_por_dia(store, familia: str, proveedor: str, modelo: str = "",
                   dias: int = 30) -> list[tuple[str, float, int]]:
    """
    Media de latencia de cada día con datos: `[(dia, media_ms, n), ...]`.

    Solo cuentan las mediciones CORRECTAS. Una llamada que falló no tiene
    latencia que promediar: meter su tiempo hasta el error mezclaría «cuánto
    tarda en responder» con «cuánto tarda en fallar», que son dos preguntas.
    """
    desde = (date.today() - timedelta(days=max(0, dias - 1))).isoformat()
    try:
        with store._conn() as c:
            filas = c.execute(
                "SELECT dia, AVG(ms) media, COUNT(*) n FROM sonda_latencia"
                " WHERE familia=? AND proveedor=? AND modelo=?"
                "   AND ok=1 AND ms IS NOT NULL AND dia>=?"
                " GROUP BY dia ORDER BY dia",
                (familia, proveedor, modelo, desde)).fetchall()
    except Exception:                                       # pragma: no cover
        return []
    return [(f["dia"], round(f["media"], 1), int(f["n"])) for f in filas]


def media_historica(store, familia: str, proveedor: str, modelo: str = "",
                    dias: int = 30) -> float | None:
    """
    Media de las medias diarias. None si no hay ni un día con datos.

        media_historica = ( Σ media_del_dia_i ) / n_dias_con_datos

    Cada día pesa lo mismo, tenga 4 mediciones o 400. Ver la explicación de la
    cabecera: la alternativa —promediar todas las mediciones— hace desaparecer
    los días malos de los candidatos muy usados, que son justo los que hay que
    ver.

    Los días sin mediciones NO entran en el divisor. Contarlos como cero
    mentiría hacia abajo y contarlos como el peor caso mentiría hacia arriba;
    no hay dato, no hay día.
    """
    dias_con_datos = medias_por_dia(store, familia, proveedor, modelo, dias)
    if not dias_con_datos:
        return None
    return round(sum(d[1] for d in dias_con_datos) / len(dias_con_datos), 1)


def estado_de_candidatos(store, dias: int = 30) -> list[EstadoCandidato]:
    """
    Todo lo que la sonda sabe, un registro por candidato, ordenado del más
    rápido al más lento y con los no medidos al final.

    Los no medidos van al final y no al principio: sin dato no se puede
    afirmar que sea rápido, y ponerlo arriba haría que el sistema lo eligiera
    antes que a uno con buena marca demostrada.
    """
    try:
        with store._conn() as c:
            claves = c.execute(
                "SELECT DISTINCT familia, proveedor, modelo FROM sonda_latencia"
            ).fetchall()
            resumen = {
                (r["familia"], r["proveedor"], r["modelo"]): r
                for r in c.execute(
                    "SELECT familia, proveedor, modelo,"
                    " COUNT(*) n, SUM(ok) exitos,"
                    " MAX(ts) ultimo_intento,"
                    " MAX(CASE WHEN ok=1 THEN ts END) ultimo_exito"
                    " FROM sonda_latencia GROUP BY familia, proveedor, modelo")
            }
            ultimas = {}
            for r in c.execute(
                    "SELECT familia, proveedor, modelo, ms, tipo_error, idioma_ok"
                    " FROM sonda_latencia s WHERE ts = ("
                    "   SELECT MAX(ts) FROM sonda_latencia t"
                    "   WHERE t.familia=s.familia AND t.proveedor=s.proveedor"
                    "     AND t.modelo=s.modelo)"):
                ultimas[(r["familia"], r["proveedor"], r["modelo"])] = r
    except Exception:                                       # pragma: no cover
        return []

    salida: list[EstadoCandidato] = []
    for k in claves:
        clave = (k["familia"], k["proveedor"], k["modelo"])
        res = resumen.get(clave)
        ult = ultimas.get(clave)
        salida.append(EstadoCandidato(
            familia=clave[0], proveedor=clave[1], modelo=clave[2],
            media_historica_ms=media_historica(store, *clave, dias=dias),
            ultima_ms=(ult["ms"] if ult else None),
            dias_con_datos=len(medias_por_dia(store, *clave, dias=dias)),
            mediciones=int(res["n"]) if res else 0,
            exitos=int(res["exitos"] or 0) if res else 0,
            ultimo_intento=(res["ultimo_intento"] if res else None),
            ultimo_exito=(res["ultimo_exito"] if res else None),
            tipo_error=(ult["tipo_error"] if ult else None),
            idioma_ok=(None if not ult or ult["idioma_ok"] is None
                       else bool(ult["idioma_ok"])),
        ))

    # Sin medida, al final: no se puede afirmar que sea rápido.
    salida.sort(key=lambda e: (e.media_historica_ms is None,
                               e.media_historica_ms or 0.0))
    return salida


def resumen_para_panel(store, dias: int = 30) -> dict:
    """
    Lo que el panel necesita, ya ordenado y sin nada que interpretar.

    Lo consume `Kernel._info_sonda()` y llega a la interfaz por `sys.config`.
    """
    estados: list[EstadoCandidato] = estado_de_candidatos(store, dias)
    por_familia: dict[str, list[dict]] = {}
    for e in estados:
        por_familia.setdefault(e.familia, []).append({
            "proveedor": e.proveedor, "modelo": e.modelo or "(por defecto)",
            "media_historica_ms": e.media_historica_ms,
            "ultima_ms": e.ultima_ms,
            # Serie diaria para VER la degradación antes de que la media
            # histórica la absorba: una media de 30 días esconde que algo
            # pasó de 3 s a 9 s esta semana. 14 días bastan para la pendiente
            # y mantienen el payload de sys.config acotado.
            "historico": medias_por_dia(store, e.familia, e.proveedor,
                                        e.modelo, dias=14),
            "dias_con_datos": e.dias_con_datos,
            "mediciones": e.mediciones,
            "tasa_exito": e.tasa_exito,
            "vivo": e.vivo,
            "medido": e.medido,
            "idioma_ok": e.idioma_ok,
            "tipo_error": e.tipo_error,
        })

    familias = []
    for fam, cands in por_familia.items():
        medidos = [c for c in cands if c["media_historica_ms"] is not None]
        familias.append({
            "familia": fam,
            "candidatos": cands,
            # La latencia de una familia es la de su MEJOR candidato: es el que
            # se probará primero, así que es el que define la experiencia.
            "mejor_ms": min((c["media_historica_ms"] for c in medidos),
                            default=None),
            "vivos": sum(1 for c in cands if c["vivo"]),
            "total": len(cands),
        })
    familias.sort(key=lambda f: (f["mejor_ms"] is None, f["mejor_ms"] or 0.0))
    return {"ventana_dias": dias, "familias": familias,
            "generado": datetime.now().isoformat(timespec="seconds")}


# ------------------------------------------------------------------- medición

def _clasifica(e: BaseException) -> tuple[str, bool]:
    """
    Tipo de fallo y si merece la pena reintentar más adelante.

    Reutiliza el clasificador de la telemetría: un 429 de cuota y un fallo de
    red no son lo mismo, y tratarlos igual es lo que congeló trece proveedores
    en «roto» para siempre.
    """
    try:
        from magi.core.store.telemetria import clasifica_error
        return clasifica_error(e)
    except Exception:                                       # pragma: no cover
        return "desconocido", True


async def medir_candidato(llm, familia: str, proveedor: str, modelo: str = "",
                          *, plazo_s: float = PLAZO_S) -> Medicion:
    """
    Una medición. Nunca lanza: un fallo del candidato ES el dato.

    `llm` es cualquier objeto con `generate(sys, user, family=..., ...)`, así
    que esto se prueba sin tocar la red.
    """
    from magi.core import idioma

    t0 = time.perf_counter()
    try:
        texto, _pid = await asyncio.wait_for(
            llm.generate("", PROMPT_CANARIO, family=familia,
                         proveedor=proveedor, modelo=modelo,
                         temperature=0.0),
            timeout=plazo_s)
    except asyncio.TimeoutError:
        return Medicion(familia, proveedor, modelo, ok=False,
                        ms=round((time.perf_counter() - t0) * 1000, 1),
                        tipo_error="timeout",
                        detalle=f"sin respuesta en {plazo_s:.0f}s")
    except Exception as e:
        tipo, _ = _clasifica(e)
        return Medicion(familia, proveedor, modelo, ok=False,
                        ms=round((time.perf_counter() - t0) * 1000, 1),
                        tipo_error=tipo, detalle=str(e)[:500])

    ms = round((time.perf_counter() - t0) * 1000, 1)
    texto = (texto or "").strip()
    if not texto:
        # Responder vacío no es responder. Contarlo como éxito daría al
        # candidato la mejor latencia del panel por no hacer nada.
        return Medicion(familia, proveedor, modelo, ok=False, ms=ms,
                        tipo_error="respuesta_vacia")

    # EL EJE DE IDIOMA, AHORA CON LA REGLA REAL DEL SISTEMA.
    #
    # Era `idioma.coincide(texto, "es")`, o sea «¿está en español?». Con eso,
    # un candidato que contesta un inglés impecable puntuaba igual que uno que
    # contesta en chino, y no son lo mismo: el primero se traduce en una
    # llamada corta y el segundo hay que descartarlo.
    #
    # `admisible()` aplica la regla que de verdad usa el enjambre: es/en/pt/it
    # sí, chino nunca.
    vale, codigo = idioma.admisible(texto)
    return Medicion(familia, proveedor, modelo, ok=True, ms=ms,
                    idioma_ok=vale,
                    detalle=f"[{codigo}] {texto[:180]}")


async def medir_todo(llm, candidatos, *, store=None,
                     concurrencia: int = CONCURRENCIA,
                     max_por_dia: int = MAX_POR_DIA,
                     plazo_s: float = PLAZO_S) -> list[Medicion]:
    """
    Sondea una lista de `(familia, proveedor, modelo)`, con freno.

    El freno tiene dos partes y las dos hacen falta:

    - **Concurrencia acotada.** Sin ella se abren tantas conexiones como
      candidatos y se acaba midiendo la congestión de la propia red en vez de
      la latencia del proveedor. La sonda se contaminaría a sí misma.
    - **Tope diario por candidato.** La cuota gratuita es la del usuario. Una
      sonda que se la gasta ha empeorado el sistema, por muy buenos que sean
      sus datos.
    """
    sem = asyncio.Semaphore(max(1, concurrencia))
    saltados = 0

    async def una(c) -> Medicion | None:
        nonlocal saltados
        familia, proveedor, modelo = (list(c) + ["", "", ""])[:3]
        if store is not None and max_por_dia:
            # `mediciones_hoy` es el freno: sin él la sonda gasta la cuota
            # gratuita del usuario, que es la misma que necesita para trabajar.
            if mediciones_hoy(store, familia, proveedor, modelo) >= max_por_dia:
                saltados += 1
                return None
        async with sem:
            m = await medir_candidato(llm, familia, proveedor, modelo,
                                      plazo_s=plazo_s)
        if store is not None:
            registrar(store, m)
        return m

    hechas = [m for m in await asyncio.gather(*(una(c) for c in candidatos))
              if m is not None]
    logger.info("[sonda] %d candidatos medidos, %d saltados por tope diario",
                len(hechas), saltados)
    return hechas


# ---------------------------------------------------- el disparo automático

#: Cada cuánto se vuelve a sondear si nadie lo pide. Un día.
#:
#: No es un valor cómodo elegido al azar: la unidad de la media histórica es el
#: DÍA (la media de las medias diarias). Sondear varias veces al día mejora la
#: media de hoy; sondear cada varios días deja huecos en la serie. Una vez al
#: día es la cadencia que la propia métrica pide.
INTERVALO_REFRESCO_S = 24 * 3600


def medias_por_familia(store, dias: int = 30) -> dict[str, float]:
    """
    Media histórica de cada familia = la de su MEJOR candidato.

    Es el número con el que `ProviderRegistry.aplicar_medidas` reparte el
    enjambre. Se usa el mejor y no el promedio de la familia porque es el
    primero que se intenta: define la experiencia real.

    Las familias sin ninguna medición NO aparecen. Devolver 0.0 para ellas las
    pondría las primeras, que es exactamente al revés de lo correcto: «no lo
    sé» no puede ganarle a «medido y rápido».
    """
    fuera: dict[str, float] = {}
    for e in estado_de_candidatos(store, dias):
        if e.media_historica_ms is None:
            continue
        actual = fuera.get(e.familia)
        if actual is None or e.media_historica_ms < actual:
            fuera[e.familia] = e.media_historica_ms
    return fuera


def toca_sondear(store, ahora: float | None = None,
                 intervalo_s: float = INTERVALO_REFRESCO_S) -> tuple[bool, str]:
    """
    ¿Hace falta sondear ya? `(sí/no, motivo)`.

    Devuelve el motivo en texto porque acaba en el log y en el panel, y
    «False» no le dice a nadie cuándo volverá a pasar algo.
    """
    ahora = time.time() if ahora is None else ahora
    ultimos = [e.ultimo_intento for e in estado_de_candidatos(store, dias=2)
               if e.ultimo_intento]
    if not ultimos:
        return True, "no hay ninguna medición todavía"
    transcurrido = ahora - max(ultimos)
    if transcurrido >= intervalo_s:
        return True, f"la última medición fue hace {transcurrido / 3600:.1f} h"
    faltan = (intervalo_s - transcurrido) / 3600
    return False, f"medido hace poco; toca dentro de {faltan:.1f} h"


async def refrescar_si_toca(llm, candidatos, store, *,
                            intervalo_s: float = INTERVALO_REFRESCO_S,
                            **kw) -> tuple[int, str]:
    """
    Sondea SOLO si toca. Devuelve `(mediciones hechas, motivo)`.

    POR QUÉ EL FRENO VA AQUÍ Y NO EN QUIEN LLAMA
    ============================================
    Porque quien llama es el arranque del kernel, y el arranque ocurre cada vez
    que abres MAGI. Si el freno estuviera fuera, abrir y cerrar el programa
    cinco veces seguidas dispararía cinco sondeos completos contra proveedores
    gratuitos — con la cuota del usuario. Una sonda que se gasta tu cuota ha
    empeorado el sistema, por muy buenos que sean sus datos.

    Nunca lanza: si la sonda falla, el sistema tiene que arrancar igual. El
    motivo del fallo se devuelve, no se esconde.
    """
    try:
        toca, motivo = toca_sondear(store, intervalo_s=intervalo_s)
        if not toca:
            return 0, motivo
        medidas = await medir_todo(llm, candidatos, store=store, **kw)
        return len(medidas), f"{len(medidas)} mediciones ({motivo})"
    except Exception as e:                                  # pragma: no cover
        logger.warning("[sonda] el refresco falló: %s", e)
        return 0, f"falló: {type(e).__name__}: {e}"
