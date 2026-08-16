"""
Migraciones de esquema con checksum.

EL PROBLEMA
===========
`TaskStore._init()` creaba las tablas con `CREATE TABLE IF NOT EXISTS`. Eso
funciona exactamente una vez: en una máquina limpia.

En una máquina que YA tiene la base creada —es decir, la de cualquier usuario
que haya abierto MAGI alguna vez— `IF NOT EXISTS` ve la tabla, no hace nada, y
**las columnas nuevas no llegan nunca**. La aplicación arranca sin quejarse y
revienta al escribir, con un `no such column` que no dice de dónde viene.

Había un parche, `_migrate()`, que añadía dos columnas a mano comprobando
`PRAGMA table_info`. Funcionaba, pero no escala: no hay orden, no hay registro
de qué se aplicó, no hay forma de saber si una máquina está al día, y nadie se
entera si alguien edita una migración ya publicada.

CÓMO LO RESUELVEN LOS QUE SÍ LO TIENEN
======================================
Zcode Desktop lleva `schema_migration(id, checksum, app_version, time_applied)`
con 18 migraciones aplicadas en este equipo. Tres propiedades que importan:

1. **Orden explícito.** Se aplican en secuencia, no "cuando toque".
2. **Registro de lo aplicado.** Se puede responder "¿esta máquina está al día?"
   sin adivinar.
3. **Checksum.** Si alguien edita una migración ya publicada, se detecta. Sin
   esto, dos usuarios con la misma versión pueden tener esquemas distintos y
   nadie lo sabe.

Este módulo es eso mismo, en español y sin dependencias.

DECISIÓN: UNA MIGRACIÓN PUBLICADA NO SE EDITA
=============================================
Si el checksum no cuadra, NO se reaplica y NO se aborta el arranque: se avisa
fuerte y se sigue. Abortar deja al usuario sin aplicación por un problema que
casi siempre es de desarrollo; reaplicar corrompe datos. Avisar y seguir es lo
único honesto de las tres.
"""
from __future__ import annotations

import hashlib
import logging
import sqlite3
import time
from collections.abc import Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

Paso = Callable[[sqlite3.Connection], None]


@dataclass(frozen=True)
class Migracion:
    """Un cambio de esquema, identificado y verificable."""
    id: str
    descripcion: str
    sql: str | None = None
    paso: Paso | None = None

    def huella(self) -> str:
        """
        Checksum del contenido.

        Para las migraciones en SQL es el texto. Para las de código es el nombre
        de la función: el cuerpo no se puede hashear de forma estable cuando el
        programa va congelado en un .exe (`inspect.getsource` no tiene fuentes
        que leer), y una huella que cambia según cómo se ejecute el programa es
        peor que una huella gruesa.
        """
        base = (self.sql if self.sql is not None
                else f"paso:{getattr(self.paso, '__name__', '?')}")
        return hashlib.sha256(base.encode("utf-8")).hexdigest()[:32]

    def aplicar(self, c: sqlite3.Connection) -> None:
        if self.sql is not None:
            c.executescript(self.sql)
        if self.paso is not None:
            self.paso(c)


# --------------------------------------------------------------- utilidades

def columnas(c: sqlite3.Connection, tabla: str) -> set[str]:
    return {r[1] for r in c.execute(f"PRAGMA table_info({tabla})")}


def anadir_columna(c: sqlite3.Connection, tabla: str, col: str, ddl: str) -> None:
    """
    `ALTER TABLE ... ADD COLUMN` idempotente.

    SQLite no admite `IF NOT EXISTS` en `ADD COLUMN`, así que hay que preguntar
    antes. Sin esta comprobación, una migración que se reintenta tras un fallo
    a medias muere con "duplicate column name" y bloquea el arranque para
    siempre.
    """
    if col in columnas(c, tabla):
        return
    c.execute(f"ALTER TABLE {tabla} ADD COLUMN {col} {ddl}")
    logger.info("[migraciones] %s.%s anadida", tabla, col)


# ------------------------------------------------------------- migraciones
#
# REGLA: una vez publicada, una migración NO se toca. Los cambios van en una
# nueva. El checksum está para hacer cumplir esto, no para adornar.

_BASE = """
CREATE TABLE IF NOT EXISTS task_state (
    task_id         TEXT PRIMARY KEY,
    command         TEXT NOT NULL,
    status          TEXT NOT NULL,
    round_num       INTEGER NOT NULL DEFAULT 1,
    engine          TEXT NOT NULL DEFAULT 'fast',
    narrative_style TEXT NOT NULL DEFAULT 'tecnico',
    route           TEXT NOT NULL DEFAULT 'task',
    max_rounds      INTEGER NOT NULL DEFAULT 3,
    use_tools       INTEGER NOT NULL DEFAULT 1,
    last_proposal   TEXT,
    last_critique   TEXT,
    created_at      REAL NOT NULL,
    updated_at      REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_task_state_status
    ON task_state(status, updated_at DESC);

CREATE TABLE IF NOT EXISTS task_event (
    seq      INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id  TEXT NOT NULL,
    topic    TEXT NOT NULL,
    payload  TEXT,
    ts       REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_task_event_task ON task_event(task_id, seq);

CREATE TABLE IF NOT EXISTS token_ledger (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id    TEXT,
    agent      TEXT,
    provider   TEXT,
    family     TEXT,
    tokens_in  INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    latency_ms REAL DEFAULT 0,
    ts         REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_token_ledger_task ON token_ledger(task_id, ts);
"""


def _rondas(c: sqlite3.Connection) -> None:
    """Las dos columnas que añadía el `_migrate()` a mano, ya formalizadas."""
    anadir_columna(c, "task_state", "max_rounds", "INTEGER NOT NULL DEFAULT 3")
    anadir_columna(c, "task_state", "use_tools", "INTEGER NOT NULL DEFAULT 1")


def _ciclo_de_vida(c: sqlite3.Connection) -> None:
    """
    Ciclo de vida completo de la tarea.

    Sin `archivada`, `task_state` solo crece y `resumable()` devuelve todo para
    siempre: es la causa de que en esta máquina se acumularan 7 tareas desde el
    7 de agosto, 4 de ellas "en curso" sin que nadie las ejecutara.

    `titulo` separado de `command` porque en la base real hay dos filas con
    `command` vacío: tareas que se crearon sin orden y que nadie pudo nombrar.

    `bifurcada_de` es la respuesta correcta a escribir algo nuevo mientras otra
    tarea espera aprobación: ni absorberlo (se pierde la pregunta) ni abrir una
    tarea huérfana (se pierde el contexto). Se bifurca.
    """
    anadir_columna(c, "task_state", "titulo", "TEXT NOT NULL DEFAULT ''")
    anadir_columna(c, "task_state", "archivada", "INTEGER NOT NULL DEFAULT 0")
    anadir_columna(c, "task_state", "borrada", "INTEGER NOT NULL DEFAULT 0")
    anadir_columna(c, "task_state", "sin_leer_en", "REAL")
    anadir_columna(c, "task_state", "bifurcada_de", "TEXT")
    anadir_columna(c, "task_state", "motivo_cierre", "TEXT")
    c.execute("CREATE INDEX IF NOT EXISTS idx_task_state_vivas "
              "ON task_state(archivada, borrada, status, updated_at DESC)")


# El libro de admisión. Zcode lo llama `session_input` y yo `command_lifecycle`;
# dos sistemas sin relación entre sí llegaron a la misma solución, lo que dice
# bastante sobre si hace falta. En 92 filas de Zcode y 16 eventos míos no hay
# una sola entrada de usuario que desaparezca sin registro.
#
# La restricción sobre `motivo` es lo que le da dientes: descartar algo SIN
# escribir por qué es imposible a nivel de base de datos. Esa es exactamente la
# línea que hoy falta en `orchestrator.py:296`.
_ADMISION = """
CREATE TABLE IF NOT EXISTS entrada_usuario (
    id                  TEXT PRIMARY KEY,
    task_id             TEXT,
    texto               TEXT NOT NULL,
    origen              TEXT NOT NULL DEFAULT 'usuario',
    entrega             TEXT NOT NULL
        CHECK (entrega IN ('ahora', 'encolar')),
    secuencia_admitida  INTEGER NOT NULL,
    secuencia_promovida INTEGER,
    estado              TEXT NOT NULL
        CHECK (estado IN ('admitida', 'promovida', 'descartada', 'fallida')),
    motivo              TEXT,
    admitida_en         REAL NOT NULL,
    actualizada_en      REAL NOT NULL,
    CHECK (estado NOT IN ('descartada', 'fallida')
           OR (motivo IS NOT NULL AND motivo <> ''))
);
CREATE INDEX IF NOT EXISTS idx_entrada_pendiente
    ON entrada_usuario(task_id, estado, secuencia_admitida);
"""


# Telemetría por turno. Hoy MAGI solo guarda latencia media por proveedor, así
# que a la pregunta "¿por qué tarda?" no puede contestar. Un turno real medido
# en mi propia infraestructura da ttft 36 s / api 588 s / total 636 s: son tres
# problemas distintos y con un solo número se ven como uno.
#
# `contexto_excedido` va como columna propia, no como error genérico: si el
# prompt no cabe, rotar a otro proveedor no arregla nada — el siguiente falla
# por lo mismo. Hoy MAGI lo trata como "proveedor roto" y rota.
_TELEMETRIA = """
CREATE TABLE IF NOT EXISTS turno (
    id                    TEXT PRIMARY KEY,
    task_id               TEXT NOT NULL,
    ronda                 INTEGER,
    agente                TEXT,
    familia               TEXT,
    proveedor             TEXT,
    estado                TEXT NOT NULL
        CHECK (estado IN ('en_curso', 'completado', 'error', 'cancelado')),
    inicio                REAL NOT NULL,
    fin                   REAL,
    ms_total              REAL,
    ms_primer_token       REAL,
    ms_api                REAL,
    peticiones            INTEGER NOT NULL DEFAULT 0,
    reintentos            INTEGER NOT NULL DEFAULT 0,
    herramientas          INTEGER NOT NULL DEFAULT 0,
    herramientas_error    INTEGER NOT NULL DEFAULT 0,
    tokens_in             INTEGER NOT NULL DEFAULT 0,
    tokens_out            INTEGER NOT NULL DEFAULT 0,
    contexto_excedido     INTEGER NOT NULL DEFAULT 0,
    cancelado_por_usuario INTEGER NOT NULL DEFAULT 0,
    tipo_error            TEXT,
    detalle_error         TEXT
);
CREATE INDEX IF NOT EXISTS idx_turno_task ON turno(task_id, inicio DESC);
"""


# Uso de herramientas. MAGI ya clasifica bien (`Tool.access`, `Tool.dangerous`
# en core/tools/registry.py) — eso no se toca. Lo que falta es REGISTRAR la
# llamada. En las 4.641 filas de Zcode ese registro revela algo que de otro
# modo es invisible: las herramientas de solo lectura fallan el 63 % de las
# veces y las de escritura el 5 %. MAGI tiene un dato así esperando.
#
# `truncada` merece columna propia: saber que una salida se cortó explica
# respuestas incoherentes que si no se le achacan al modelo.
_HERRAMIENTAS = """
CREATE TABLE IF NOT EXISTS uso_herramienta (
    id            TEXT PRIMARY KEY,
    task_id       TEXT,
    turno_id      TEXT,
    agente        TEXT,
    herramienta   TEXT NOT NULL,
    solo_lectura  INTEGER,
    peligrosa     INTEGER,
    aprobacion    TEXT NOT NULL DEFAULT 'ninguna'
        CHECK (aprobacion IN ('ninguna', 'pedida', 'concedida', 'denegada')),
    estado        TEXT NOT NULL
        CHECK (estado IN ('en_curso', 'completada', 'error', 'cancelada')),
    inicio        REAL NOT NULL,
    fin           REAL,
    ms            REAL,
    bytes_salida  INTEGER,
    truncada      INTEGER NOT NULL DEFAULT 0,
    codigo_salida INTEGER,
    tipo_error    TEXT,
    mensaje_error TEXT
);
CREATE INDEX IF NOT EXISTS idx_uso_herramienta_task
    ON uso_herramienta(task_id, inicio DESC);
CREATE INDEX IF NOT EXISTS idx_uso_herramienta_nombre
    ON uso_herramienta(herramienta, estado);
"""


# Llamadas al modelo agrupadas por petición lógica. MAGI hace hedging
# (HEDGE_AFTER_S = 4.0, HEDGE_MAX = 2): lanza un segundo candidato a los 4 s y
# gana el primero que conteste. Es buena idea, pero hoy es invisible — no se
# sabe cuántas veces ganó el segundo, ni si el hedging ayuda o solo gasta
# cuota. Con `peticion_logica` + `indice_intento` + `gano` eso se mide, y
# HEDGE_AFTER_S se puede ajustar con datos en vez de a ojo.
_LLAMADAS = """
CREATE TABLE IF NOT EXISTS llamada_modelo (
    id              TEXT PRIMARY KEY,
    peticion_logica TEXT NOT NULL,
    indice_intento  INTEGER NOT NULL DEFAULT 0,
    task_id         TEXT,
    turno_id        TEXT,
    agente          TEXT,
    familia         TEXT,
    proveedor       TEXT,
    estado          TEXT NOT NULL
        CHECK (estado IN ('en_curso', 'completada', 'error', 'cancelada')),
    gano            INTEGER NOT NULL DEFAULT 0,
    inicio          REAL NOT NULL,
    fin             REAL,
    ms              REAL,
    tipo_error      TEXT
);
CREATE INDEX IF NOT EXISTS idx_llamada_logica
    ON llamada_modelo(peticion_logica, indice_intento);
"""


_SONDA = """
-- Mediciones de la sonda de latencia.
--
-- POR QUÉ UNA TABLA APARTE Y NO REUSAR `llamada_modelo`
-- ====================================================
-- `llamada_modelo` registra el trabajo REAL del usuario: peticiones con su
-- tamaño, su contexto y su suerte. Mezclar ahí las mediciones de la sonda
-- —prompts diminutos y controlados— envenenaría las dos lecturas: el p95 del
-- trabajo real bajaría por culpa de los canarios, y la latencia de la sonda
-- subiría por culpa de las peticiones largas. Dos preguntas distintas, dos
-- tablas.
--
-- `dia` se guarda ya calculado (YYYY-MM-DD, hora local) porque la media
-- histórica es «la media de las medias diarias»: agrupar por día en cada
-- consulta obligaría a repetir la conversión de zona horaria, y basta con que
-- una lectura la haga distinta para que dos números que deberían coincidir no
-- coincidan.
CREATE TABLE IF NOT EXISTS sonda_latencia (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          REAL NOT NULL,
    dia         TEXT NOT NULL,
    familia     TEXT NOT NULL,
    proveedor   TEXT NOT NULL,
    modelo      TEXT NOT NULL DEFAULT '',
    ok          INTEGER NOT NULL,
    ms          REAL,
    tipo_error  TEXT,
    detalle     TEXT,
    -- Si la respuesta llegó en el idioma pedido. Un candidato rapidísimo que
    -- contesta en otro idioma no sirve para este sistema, y la latencia sola
    -- no lo distingue de uno bueno.
    idioma_ok   INTEGER
);
CREATE INDEX IF NOT EXISTS idx_sonda_candidato
    ON sonda_latencia(familia, proveedor, modelo, dia);
CREATE INDEX IF NOT EXISTS idx_sonda_dia ON sonda_latencia(dia);
"""


MIGRACIONES: tuple[Migracion, ...] = (
    Migracion("0001_esquema_base",
              "Tablas originales: task_state, task_event, token_ledger",
              sql=_BASE),
    Migracion("0002_rondas",
              "max_rounds y use_tools (formaliza el antiguo _migrate)",
              paso=_rondas),
    Migracion("0003_ciclo_de_vida",
              "titulo, archivada, borrada, sin_leer_en, bifurcada_de",
              paso=_ciclo_de_vida),
    Migracion("0004_libro_de_admision",
              "entrada_usuario: ninguna entrada se pierde en silencio",
              sql=_ADMISION),
    Migracion("0005_telemetria_turno",
              "turno: ttft, ms_api, reintentos, contexto_excedido",
              sql=_TELEMETRIA),
    Migracion("0006_uso_herramienta",
              "uso_herramienta: solo_lectura, peligrosa, truncada",
              sql=_HERRAMIENTAS),
    Migracion("0007_llamada_modelo",
              "llamada_modelo: intentos de una misma peticion logica",
              sql=_LLAMADAS),
    Migracion("0008_sonda_latencia",
              "sonda_latencia: medicion periodica por candidato, con dia",
              sql=_SONDA),
)


_REGISTRO = """
CREATE TABLE IF NOT EXISTS migracion_esquema (
    id          TEXT PRIMARY KEY,
    checksum    TEXT NOT NULL,
    version_app TEXT,
    aplicada_en REAL NOT NULL
);
"""


def _version_app() -> str:
    try:
        from magi import __version__
        return str(__version__)
    except Exception:
        return "desconocida"


def aplicadas(c: sqlite3.Connection) -> dict[str, str]:
    """Qué migraciones tiene esta base y con qué huella."""
    c.executescript(_REGISTRO)
    return {r[0]: r[1]
            for r in c.execute("SELECT id, checksum FROM migracion_esquema")}


def ejecutar(c: sqlite3.Connection,
             migraciones: tuple[Migracion, ...] = MIGRACIONES) -> list[str]:
    """
    Aplica en orden lo que falte. Devuelve los ids aplicados en esta llamada.

    Se confirma tras CADA migración, no al final. Si la quinta falla, las
    cuatro anteriores quedan aplicadas y registradas y el siguiente arranque
    reintenta solo la quinta. Confirmar únicamente al final haría que un fallo
    tardío revirtiera trabajo bueno y el problema se repitiera igual.

    NO se usa BEGIN/COMMIT explícito. `executescript()` de sqlite3 confirma por
    su cuenta antes de ejecutar, así que una transacción abierta a mano se
    cierra sola a mitad y el INSERT en el registro se queda fuera: eso hacía
    que la segunda pasada creyera que no había nada aplicado y lo reaplicara
    todo. Se apoya en `commit()`/`rollback()` del propio conector.

    Esto se puede hacer porque **todas las migraciones son idempotentes**
    (`IF NOT EXISTS`, y `anadir_columna` comprueba antes). Un corte a mitad se
    recupera repitiendo, no revirtiendo.
    """
    ya = aplicadas(c)
    hechas: list[str] = []

    for m in migraciones:
        huella = m.huella()
        if m.id in ya:
            if ya[m.id] != huella:
                logger.error(
                    "[migraciones] %s YA APLICADA con checksum distinto "
                    "(base %s, codigo %s). Alguien edito una migracion "
                    "publicada: esta base y una recien creada NO tienen el "
                    "mismo esquema. No se reaplica.",
                    m.id, ya[m.id], huella)
            continue

        try:
            m.aplicar(c)
            c.execute("INSERT INTO migracion_esquema "
                      "(id, checksum, version_app, aplicada_en) VALUES (?,?,?,?)",
                      (m.id, huella, _version_app(), time.time()))
            c.commit()
            hechas.append(m.id)
            logger.info("[migraciones] aplicada %s - %s", m.id, m.descripcion)
        except Exception as e:
            try:
                c.rollback()
            except Exception:
                pass
            logger.error("[migraciones] fallo %s: %s", m.id, e)
            raise

    return hechas


def al_dia(c: sqlite3.Connection,
           migraciones: tuple[Migracion, ...] = MIGRACIONES) -> bool:
    """¿Esta base tiene todo lo que el código espera? Sin adivinar."""
    ya = aplicadas(c)
    return all(m.id in ya for m in migraciones)


def informe(c: sqlite3.Connection,
            migraciones: tuple[Migracion, ...] = MIGRACIONES) -> dict:
    """Para la pestaña Configuración: qué hay, qué falta y qué no cuadra."""
    ya = aplicadas(c)
    return {
        "aplicadas": len(ya),
        "esperadas": len(migraciones),
        "al_dia": all(m.id in ya for m in migraciones),
        "pendientes": [m.id for m in migraciones if m.id not in ya],
        "discrepantes": [m.id for m in migraciones
                         if m.id in ya and ya[m.id] != m.huella()],
        "version_app": _version_app(),
    }
