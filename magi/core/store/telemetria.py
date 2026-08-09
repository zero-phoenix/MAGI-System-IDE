"""
Telemetría: dónde se va el tiempo, qué herramientas fallan, si el hedging sirve.

LA PREGUNTA QUE NO SE PODÍA CONTESTAR
=====================================
El usuario preguntó varias veces por qué el sistema tardaba. MAGI no podía
responder: solo guardaba una latencia media por proveedor. Un número.

Zcode Desktop guarda por turno:

    time_to_first_token_ms, first_model_start_at, first_token_at, duration_ms,
    model_request_count, model_retry_count, tool_call_count, tool_error_count,
    context_exceeded, retryable, cancelled_by_user, error_type, error_code

Y Claude Code separa `ttft_ms`, `ttft_stream_ms`, `time_to_request_ms`,
`duration_api_ms` y `duration_ms`. Un turno real medido en mi propia
infraestructura:

    ttft 36 s · ttft_stream 16 s · api 588 s · total 636 s

Cuatro números, no uno. De un vistazo se ve que la espera hasta la primera
respuesta y el tiempo de API son problemas distintos. Con la media sola, los
dos se ven igual.

TRES COSAS QUE SOLO APARECEN AL MEDIR
=====================================
1. `contexto_excedido` como modo de fallo CON NOMBRE. Si el prompt no cabe,
   rotar de proveedor no arregla nada: el siguiente falla por lo mismo. MAGI
   lo leía como «proveedor roto» y recorría la familia entera.

2. `truncada` en las herramientas. Una salida cortada explica respuestas
   incoherentes que si no se le achacan al modelo.

3. `peticion_logica` + `indice_intento` + `gano`. MAGI hace hedging
   (HEDGE_AFTER_S=4, HEDGE_MAX=2) y hoy es invisible: no se sabe cuántas veces
   gana el segundo candidato, ni si el hedging ayuda o solo gasta cuota. Con
   esto, HEDGE_AFTER_S se ajusta con datos en vez de a ojo.

REGLA DE ORO
============
**Medir no puede romper lo medido.** Todo lo de aquí traga sus propias
excepciones: si la telemetría falla, el turno sigue. Un sistema que se cae
porque no pudo escribir una métrica es peor que uno sin métricas.
"""
from __future__ import annotations

import logging
import math
import time
import uuid
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

EN_CURSO = "en_curso"
COMPLETADO = "completado"
ERROR = "error"
CANCELADO = "cancelado"


def _ms(a: float | None, b: float | None) -> float | None:
    return round((b - a) * 1000, 1) if (a and b) else None


def clasifica_error(e: BaseException | str) -> tuple[str, bool]:
    """
    Nombre del modo de fallo, y si rotar de proveedor tiene sentido.

    Devolver «rotar no sirve» para `contexto` es el punto entero: hoy MAGI
    recorre toda la familia probando proveedores que van a fallar por la misma
    razón, y acaba declarándola agotada.
    """
    t = str(e).lower()
    if any(k in t for k in ("context length", "context_length", "too long",
                            "maximum context", "token limit", "prompt is too")):
        return "contexto", False
    if any(k in t for k in ("429", "rate limit", "quota", "too many requests")):
        return "cuota", True
    if any(k in t for k in ("timeout", "timed out", "read timeout")):
        return "timeout", True
    if any(k in t for k in ("401", "403", "auth", "cookies", "captcha",
                            ".har", "browser_cookie3")):
        return "credenciales", True
    if "browserblocked" in t or "no abre navegadores" in t:
        return "navegador_bloqueado", True
    if any(k in t for k in ("connection", "dns", "ssl", "network")):
        return "red", True
    return "desconocido", True


@dataclass
class Turno:
    """
    Un turno de un agente, con el tiempo desglosado.

    Se usa como gestor de contexto:

        with tel.turno(task_id, "MELCHIOR", familia="gpt") as t:
            t.primer_token()          # cuando llega el primer trozo
            ...
            t.tokens(entrada=1200, salida=800)

    Cerrar es automático, incluso si el bloque revienta: un turno que muere no
    puede quedarse `en_curso` para siempre. Ese error ya lo cometimos una vez
    con las tareas.
    """
    id: str
    task_id: str
    agente: str = ""
    familia: str = ""
    proveedor: str = ""
    ronda: int | None = None
    inicio: float = field(default_factory=time.time)
    _primer_token: float | None = None
    _fin: float | None = None
    _api: float | None = None
    peticiones: int = 0
    reintentos: int = 0
    herramientas: int = 0
    herramientas_error: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    contexto_excedido: bool = False
    cancelado_por_usuario: bool = False
    estado: str = EN_CURSO
    tipo_error: str | None = None
    detalle_error: str | None = None

    # -- marcas que pone quien ejecuta el turno

    def primer_token(self) -> None:
        """Solo la primera vez cuenta: es el TTFT, no el último trozo."""
        if self._primer_token is None:
            self._primer_token = time.time()

    def api(self, segundos: float) -> None:
        self._api = (self._api or 0) + segundos

    def tokens(self, entrada: int = 0, salida: int = 0) -> None:
        self.tokens_in += int(entrada or 0)
        self.tokens_out += int(salida or 0)

    def intento(self, reintento: bool = False) -> None:
        self.peticiones += 1
        if reintento:
            self.reintentos += 1

    def herramienta(self, ok: bool = True) -> None:
        self.herramientas += 1
        if not ok:
            self.herramientas_error += 1

    def fallo(self, e: BaseException | str) -> None:
        tipo, _ = clasifica_error(e)
        self.estado = ERROR
        self.tipo_error = tipo
        self.detalle_error = str(e)[:1000]
        if tipo == "contexto":
            self.contexto_excedido = True

    @property
    def ms_total(self) -> float | None:
        return _ms(self.inicio, self._fin)

    @property
    def ms_primer_token(self) -> float | None:
        return _ms(self.inicio, self._primer_token)


class Telemetria:
    """
    Escribe en `turno`, `uso_herramienta` y `llamada_modelo`.

    Comparte la base con `TaskStore`. Cada método traga sus excepciones: ver la
    regla de oro de la cabecera.
    """

    def __init__(self, store):
        self._store = store

    def _exec(self, sql: str, args: tuple) -> None:
        try:
            with self._store._conn() as c:
                c.execute(sql, args)
        except Exception as e:                          # pragma: no cover
            logger.debug("[telemetria] no se pudo escribir: %s", e)

    # ------------------------------------------------------------- turnos

    def turno(self, task_id: str, agente: str = "", *, familia: str = "",
              proveedor: str = "", ronda: int | None = None) -> _Contexto:
        t = Turno(id=f"tur_{uuid.uuid4().hex[:12]}", task_id=task_id,
                  agente=agente, familia=familia, proveedor=proveedor,
                  ronda=ronda)
        return _Contexto(self, t)

    def _abrir_turno(self, t: Turno) -> None:
        self._exec(
            "INSERT INTO turno (id, task_id, ronda, agente, familia, proveedor,"
            " estado, inicio) VALUES (?,?,?,?,?,?,?,?)",
            (t.id, t.task_id, t.ronda, t.agente, t.familia, t.proveedor,
             EN_CURSO, t.inicio))

    def _cerrar_turno(self, t: Turno) -> None:
        self._exec(
            "UPDATE turno SET estado=?, fin=?, ms_total=?, ms_primer_token=?,"
            " ms_api=?, peticiones=?, reintentos=?, herramientas=?,"
            " herramientas_error=?, tokens_in=?, tokens_out=?,"
            " contexto_excedido=?, cancelado_por_usuario=?, tipo_error=?,"
            " detalle_error=?, familia=?, proveedor=? WHERE id=?",
            (t.estado, t._fin, t.ms_total, t.ms_primer_token,
             round(t._api * 1000, 1) if t._api else None,
             t.peticiones, t.reintentos, t.herramientas, t.herramientas_error,
             t.tokens_in, t.tokens_out, int(t.contexto_excedido),
             int(t.cancelado_por_usuario), t.tipo_error, t.detalle_error,
             t.familia, t.proveedor, t.id))


    # -------------------------------------------------------- herramientas

    def herramienta(self, nombre: str, *, task_id: str = "", turno_id: str = "",
                    agente: str = "", solo_lectura: bool | None = None,
                    peligrosa: bool | None = None,
                    aprobacion: str = "ninguna") -> str:
        """
        Abre el registro de una llamada. Devuelve su id para cerrarla.

        `solo_lectura` y `peligrosa` salen de `Tool.access` y `Tool.dangerous`,
        que MAGI YA tenía bien clasificados en core/tools/registry.py. Lo que
        faltaba era guardar la llamada: en las 4.641 filas de Zcode ese
        registro revela que las herramientas de solo lectura fallan el 63 % de
        las veces y las de escritura el 5 %. Sin registrar, un dato así es
        invisible.
        """
        uid = f"uso_{uuid.uuid4().hex[:12]}"
        self._exec(
            "INSERT INTO uso_herramienta (id, task_id, turno_id, agente,"
            " herramienta, solo_lectura, peligrosa, aprobacion, estado, inicio)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (uid, task_id or None, turno_id or None, agente or None, nombre,
             None if solo_lectura is None else int(solo_lectura),
             None if peligrosa is None else int(peligrosa),
             aprobacion, EN_CURSO, time.time()))
        return uid

    def herramienta_fin(self, uid: str, *, ok: bool, inicio: float,
                        salida: str = "", truncada: bool = False,
                        codigo: int | None = None,
                        error: str | None = None) -> None:
        tipo = clasifica_error(error)[0] if error else None
        self._exec(
            "UPDATE uso_herramienta SET estado=?, fin=?, ms=?, bytes_salida=?,"
            " truncada=?, codigo_salida=?, tipo_error=?, mensaje_error=?"
            " WHERE id=?",
            ("completada" if ok else ERROR, time.time(),
             round((time.time() - inicio) * 1000, 1),
             len(salida or ""), int(bool(truncada)), codigo, tipo,
             (error or None) and str(error)[:1000], uid))


    # ----------------------------------------------------- llamadas al modelo

    def llamada(self, peticion_logica: str, indice: int, *, task_id: str = "",
                turno_id: str = "", agente: str = "", familia: str = "",
                proveedor: str = "") -> str:
        """Un intento. Varios intentos de la misma `peticion_logica` = hedging."""
        uid = f"lla_{uuid.uuid4().hex[:12]}"
        self._exec(
            "INSERT INTO llamada_modelo (id, peticion_logica, indice_intento,"
            " task_id, turno_id, agente, familia, proveedor, estado, inicio)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (uid, peticion_logica, int(indice), task_id or None,
             turno_id or None, agente or None, familia or None,
             proveedor or None, EN_CURSO, time.time()))
        return uid

    def llamada_fin(self, uid: str, *, ok: bool, inicio: float,
                    gano: bool = False, error: str | None = None) -> None:
        self._exec(
            "UPDATE llamada_modelo SET estado=?, fin=?, ms=?, gano=?,"
            " tipo_error=? WHERE id=?",
            ("completada" if ok else ERROR, time.time(),
             round((time.time() - inicio) * 1000, 1), int(bool(gano)),
             clasifica_error(error)[0] if error else None, uid))


class _Contexto:
    """`with` alrededor de un turno. Cierra pase lo que pase."""

    def __init__(self, tel: Telemetria, t: Turno):
        self._tel, self.t = tel, t

    def __enter__(self) -> Turno:
        self._tel._abrir_turno(self.t)
        return self.t

    def __exit__(self, exc_tipo, exc, tb) -> bool:
        self.t._fin = time.time()
        if exc is not None:
            if isinstance(exc, __import__("asyncio").CancelledError):
                self.t.estado = CANCELADO
                self.t.cancelado_por_usuario = True
            else:
                self.t.fallo(exc)
        elif self.t.estado == EN_CURSO:
            self.t.estado = COMPLETADO
        self._tel._cerrar_turno(self.t)
        return False        # nunca se traga la excepción del turno


# --------------------------------------------------------------- lectura
#
# Estas son las que convierten la tabla en una respuesta. Sin ellas, medir solo
# llena disco.

def resumen(store, task_id: str | None = None, limite: int = 50) -> dict:
    """
    Dónde se va el tiempo, en cuatro números en vez de uno.

    Es la respuesta a «¿por qué tarda?», que hasta ahora MAGI no podía dar.
    """
    try:
        with store._conn() as c:
            donde = "WHERE task_id=?" if task_id else ""
            args = (task_id, limite) if task_id else (limite,)
            filas = c.execute(
                f"SELECT * FROM turno {donde} ORDER BY inicio DESC LIMIT ?",
                args).fetchall()
            herr = c.execute(
                "SELECT herramienta, solo_lectura, estado, COUNT(*) n"
                " FROM uso_herramienta GROUP BY 1,2,3").fetchall()
            hedge = c.execute(
                "SELECT COUNT(DISTINCT peticion_logica) peticiones,"
                " COUNT(*) intentos,"
                " SUM(CASE WHEN indice_intento>0 AND gano=1 THEN 1 ELSE 0 END) gano_cobertura"
                " FROM llamada_modelo").fetchone()
    except Exception as e:                              # pragma: no cover
        return {"error": str(e)}

    def med(campo):
        v = sorted(f[campo] for f in filas if f[campo] is not None)
        return round(v[len(v) // 2], 1) if v else None

    return {
        "turnos": len(filas),
        "mediana_ms_total": med("ms_total"),
        "mediana_ms_primer_token": med("ms_primer_token"),
        "mediana_ms_api": med("ms_api"),
        "reintentos": sum(f["reintentos"] or 0 for f in filas),
        "contexto_excedido": sum(f["contexto_excedido"] or 0 for f in filas),
        "truncados": _truncados(store),
        "herramientas": [dict(h) for h in herr],
        "hedging": dict(hedge) if hedge else {},
    }


def _truncados(store) -> int:
    try:
        with store._conn() as c:
            return c.execute("SELECT COUNT(*) FROM uso_herramienta "
                             "WHERE truncada=1").fetchone()[0]
    except Exception:                                   # pragma: no cover
        return 0


def herramientas_que_fallan(store, minimo: int = 5) -> list[dict]:
    """
    Las que más fallan, con su tasa. En Zcode este listado destapa que las de
    solo lectura fallan 12 veces más que las de escritura.
    """
    try:
        with store._conn() as c:
            filas = c.execute(
                "SELECT herramienta, solo_lectura,"
                " SUM(CASE WHEN estado='error' THEN 1 ELSE 0 END) fallos,"
                " COUNT(*) total FROM uso_herramienta"
                " GROUP BY 1,2 HAVING total >= ? ORDER BY"
                " (CAST(fallos AS REAL)/total) DESC", (minimo,)).fetchall()
    except Exception:                                   # pragma: no cover
        return []
    return [{"herramienta": f["herramienta"],
             "solo_lectura": bool(f["solo_lectura"]),
             "fallos": f["fallos"], "total": f["total"],
             "tasa": round(f["fallos"] / f["total"], 3)} for f in filas]


#: por debajo de esto un p95 es literalmente «lo peor que he visto», no un
#: percentil. Se sigue devolviendo, pero marcado, para no vender como medida lo
#: que es una anécdota.
MUESTRA_FIABLE = 20


def _percentil(valores: list[float], q: float) -> float | None:
    """
    Percentil por rango más cercano. Sin interpolar, y es deliberado.

    Interpolar inventa un número que nunca ocurrió. Aquí el valor devuelto es
    siempre una latencia REAL medida, lo que importa cuando la respuesta se va
    a leer como «esto es lo que llega a tardar».
    """
    if not valores:
        return None
    orden = sorted(valores)
    i = min(len(orden) - 1, max(0, math.ceil(q * len(orden)) - 1))
    return round(orden[i], 1)


def _agrupa(filas, clave: str, valor: str) -> dict[str, list[float]]:
    grupos: dict[str, list[float]] = {}
    for f in filas:
        k = f[clave] or "(sin nombre)"
        grupos.setdefault(k, []).append(f[valor])
    return grupos


def _estadisticas(nombre: str, ms: list[float]) -> dict:
    return {
        "clave": nombre,
        "n": len(ms),
        "mediana_ms": _percentil(ms, 0.50),
        "p95_ms": _percentil(ms, 0.95),
        "peor_ms": round(max(ms), 1),
        "fiable": len(ms) >= MUESTRA_FIABLE,
    }


def cuellos_de_botella(store, *, top: int = 5, minimo: int = 3,
                       muestra: int = 2000) -> dict:
    """
    Dónde se va el tiempo, ordenado por p95 y no por media.

    POR QUÉ p95 Y NO LA MEDIA
    =========================
    Hasta ahora solo se guardaba una latencia media por proveedor. Una media no
    distingue «siempre tarda 4 s» de «suele tardar 1 s y una de cada diez veces
    tarda 30». Las dos dan la misma media y son problemas completamente
    distintos: el primero es un límite del proveedor, el segundo es la cola de
    la distribución, y es la que el usuario recuerda porque es la que le hace
    esperar mirando la pantalla.

    El p95 responde a la pregunta que de verdad se hace: «cuando va mal, ¿cuánto
    tarda?». Por eso también se devuelve `peor_ms`: el p95 acota lo habitual,
    el peor acota lo posible.

    No se calcula nada nuevo. Los turnos y los usos de herramienta ya se
    guardan con su duración desde que existe la telemetría; esto es leer lo que
    llevaba ahí todo el tiempo sin que nadie lo mirara.
    """
    try:
        with store._conn() as c:
            turnos = c.execute(
                "SELECT agente, familia, ms_total FROM turno"
                " WHERE ms_total IS NOT NULL AND estado=?"
                " ORDER BY inicio DESC LIMIT ?",
                (COMPLETADO, muestra)).fetchall()
            usos = c.execute(
                "SELECT herramienta, ms FROM uso_herramienta"
                " WHERE ms IS NOT NULL AND estado='completada'"
                " ORDER BY inicio DESC LIMIT ?", (muestra,)).fetchall()
    except Exception as e:                                  # pragma: no cover
        return {"error": str(e)}

    def top_de(grupos: dict[str, list[float]]) -> list[dict]:
        filas = [_estadisticas(k, v) for k, v in grupos.items() if len(v) >= minimo]
        filas.sort(key=lambda d: d["p95_ms"] or 0, reverse=True)
        return filas[:top]

    return {
        "agentes": top_de(_agrupa(turnos, "agente", "ms_total")),
        "familias": top_de(_agrupa(turnos, "familia", "ms_total")),
        "herramientas": top_de(_agrupa(usos, "herramienta", "ms")),
        "muestra_fiable_desde": MUESTRA_FIABLE,
    }


#: cuánto hay que pasarse del p95 para que merezca un aviso. Ver más abajo.
MARGEN_AVISO = 1.5


def herramientas_fuera_de_su_p95(store, *, minimo: int = MUESTRA_FIABLE,
                                 margen: float = MARGEN_AVISO,
                                 muestra: int = 2000) -> list[dict]:
    """
    Herramientas cuya última ejecución se salió de su propio p95 histórico.

    La comparación es contra SÍ MISMA, no contra un umbral global, y esa es
    toda la idea. `run_tests` tardando 40 s es normal; `read_file` tardando 4 s
    no lo es en absoluto, y un umbral único o bien deja pasar el segundo o bien
    marca el primero cada vez. Cada herramienta trae su propia definición de
    «raro» en su historial.

    POR QUÉ HAY UN MARGEN Y NO BASTA CON «SUPERAR EL p95»
    =====================================================
    Un percentil 95 se supera, por definición, en 1 de cada 20 ejecuciones. Un
    aviso que salte cada vez que se cruza esa línea salta constantemente aunque
    no pase nada — y un aviso que salta siempre deja de leerse, que es la forma
    habitual de que un sistema de alertas acabe sin servir para nada.

    Peor aún: superar el p95 por un 0,25% no significa nada. Una herramienta
    con p95 de 40 s que tarda 40,1 s está comportándose con toda normalidad;
    marcarla es cambiar información por ruido.

    Con `margen`, el aviso deja de decir «esto está por encima de una línea
    estadística» y pasa a decir «esto se ha salido de su carácter». Que es lo
    único que justifica interrumpir a alguien.

    Se exige además `minimo` ejecuciones previas: comparar contra el p95 de
    tres muestras es comparar contra el máximo.
    """
    try:
        with store._conn() as c:
            filas = c.execute(
                "SELECT herramienta, ms, inicio FROM uso_herramienta"
                " WHERE ms IS NOT NULL AND estado='completada'"
                " ORDER BY inicio DESC LIMIT ?", (muestra,)).fetchall()
    except Exception:                                       # pragma: no cover
        return []

    por_herramienta: dict[str, list] = {}
    for f in filas:                       # llegan de más reciente a más antigua
        por_herramienta.setdefault(f["herramienta"] or "(sin nombre)", []).append(f)

    avisos = []
    for nombre, hist in por_herramienta.items():
        if len(hist) <= minimo:
            continue
        ultima, previas = hist[0], [h["ms"] for h in hist[1:]]
        umbral = _percentil(previas, 0.95)
        if umbral is None or ultima["ms"] <= umbral * margen:
            continue
        avisos.append({
            "herramienta": nombre,
            "ultima_ms": round(ultima["ms"], 1),
            "p95_historico_ms": umbral,
            "mediana_ms": _percentil(previas, 0.50),
            "veces_el_p95": round(ultima["ms"] / umbral, 2) if umbral else None,
            "muestras": len(previas),
        })
    avisos.sort(key=lambda d: d["veces_el_p95"] or 0, reverse=True)
    return avisos


def sirve_el_hedging(store) -> dict:
    """
    ¿Compensa lanzar un segundo candidato a los 4 s?

    Si `gana_la_cobertura` es ~0, HEDGE_AFTER_S está demasiado bajo y solo se
    está gastando cuota. Si es alto, el primer candidato falla más de lo que
    parece. Hasta ahora esto no se podía ni preguntar.
    """
    try:
        with store._conn() as c:
            f = c.execute(
                "SELECT COUNT(DISTINCT peticion_logica) peticiones,"
                " COUNT(*) intentos,"
                " SUM(CASE WHEN indice_intento>0 THEN 1 ELSE 0 END) coberturas,"
                " SUM(CASE WHEN indice_intento>0 AND gano=1 THEN 1 ELSE 0 END) gano"
                " FROM llamada_modelo").fetchone()
    except Exception:                                   # pragma: no cover
        return {}
    cob = f["coberturas"] or 0
    return {"peticiones": f["peticiones"], "intentos": f["intentos"],
            "coberturas": cob, "gano_la_cobertura": f["gano"] or 0,
            "utilidad": round((f["gano"] or 0) / cob, 3) if cob else None}
