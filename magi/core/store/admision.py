"""
Libro de admisión: ninguna entrada del usuario se pierde en silencio.

EL HALLAZGO QUE ORIGINA ESTE MÓDULO
===================================
Dos sistemas agénticos sin relación entre sí, examinados en esta misma máquina,
resolvieron el mismo problema de la misma forma:

* **Zcode Desktop** — tabla `session_input`:

      delivery TEXT CHECK (delivery IN ('startNow','guide','queue'))
      status   TEXT CHECK (status IN ('admitted','promoted','cancelled',
                                      'discarded','failed'))
      status_reason TEXT
      admitted_sequence, promoted_sequence, promoted_message_id

* **Claude Code / Cowork** — eventos `command_lifecycle` en `audit.jsonl`:

      b845a2db  [('queued', '...T23:41:19.994Z'), ('started', '...T23:41:21.841Z')]

En 92 filas de Zcode y 16 eventos míos no hay **una sola** entrada de usuario
que desaparezca sin dejar constancia. Cada una se admite con número de
secuencia y después se promociona o se descarta **con motivo escrito**.

Que dos productos maduros converjan en esto no es casualidad: un agente que
trabaja durante minutos NECESITA una cola de admisión. No la tiene por lujo.

LO QUE HACÍA MAGI
=================
`orchestrator.py:296`:

    elif state["status"] == "in_progress":
        return   # Ignorar comandos extra mientras piensa

Un `return` mudo. Ni evento, ni fila, ni motivo. El mensaje se evapora y desde
fuera el sistema parece muerto. Combinado con los zombis rehidratados, dejó
esta instalación bloqueada de forma permanente.

Fíjate en el valor `queue` de Zcode: si el agente está ocupado, la entrada **se
encola**, no se tira. Es literalmente la respuesta al fallo.

EL INVARIANTE
=============
La restricción `CHECK (estado NOT IN ('descartada','fallida') OR motivo <> '')`
de la migración 0004 hace que **descartar algo sin escribir por qué sea
imposible a nivel de base de datos**. No es documentación: es que la escritura
falla.
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

AHORA = "ahora"
ENCOLAR = "encolar"

ADMITIDA = "admitida"
PROMOVIDA = "promovida"
DESCARTADA = "descartada"
FALLIDA = "fallida"


@dataclass
class Entrada:
    """Una cosa que el usuario escribió, con su destino."""
    id: str
    task_id: str | None
    texto: str
    origen: str
    entrega: str
    secuencia_admitida: int
    estado: str
    motivo: str | None = None
    secuencia_promovida: int | None = None
    admitida_en: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "task_id": self.task_id, "texto": self.texto,
            "origen": self.origen, "entrega": self.entrega,
            "secuencia": self.secuencia_admitida, "estado": self.estado,
            "motivo": self.motivo, "admitida_en": self.admitida_en,
        }

    def resumen(self) -> str:
        t = self.texto.strip().replace("\n", " ")
        corto = (t[:70] + "…") if len(t) > 70 else t
        if self.estado == DESCARTADA:
            return f"«{corto}» — descartada: {self.motivo}"
        if self.estado == ADMITIDA and self.entrega == ENCOLAR:
            return f"«{corto}» — en cola, se atenderá al terminar lo actual"
        return f"«{corto}» — {self.estado}"


class LibroDeAdmision:
    """
    Acceso al libro. Comparte la base con `TaskStore`; se le pasa el store para
    no abrir una segunda ruta a la misma base de datos.
    """

    def __init__(self, store):
        self._store = store

    def _conn(self):
        return self._store._conn()

    # ------------------------------------------------------------- escritura

    def admitir(self, texto: str, task_id: str | None = None, *,
                entrega: str = AHORA, origen: str = "usuario") -> Entrada:
        """
        Registra la entrada ANTES de decidir qué hacer con ella.

        Este orden importa: si se registrara después de decidir, una excepción
        entre medias volvería a perder el mensaje, que es justo lo que se está
        arreglando. Primero queda escrito; luego ya se verá.
        """
        eid = f"ent_{uuid.uuid4().hex[:12]}"
        ahora = time.time()
        with self._conn() as c:
            fila = c.execute(
                "SELECT COALESCE(MAX(secuencia_admitida), 0) + 1 "
                "FROM entrada_usuario").fetchone()
            seq = int(fila[0])
            c.execute(
                "INSERT INTO entrada_usuario (id, task_id, texto, origen, "
                "entrega, secuencia_admitida, estado, admitida_en, "
                "actualizada_en) VALUES (?,?,?,?,?,?,?,?,?)",
                (eid, task_id, texto, origen, entrega, seq, ADMITIDA,
                 ahora, ahora))
        return Entrada(id=eid, task_id=task_id, texto=texto, origen=origen,
                       entrega=entrega, secuencia_admitida=seq,
                       estado=ADMITIDA, admitida_en=ahora)


    def promover(self, entrada_id: str, task_id: str | None = None) -> None:
        """La entrada se convirtió en trabajo real."""
        with self._conn() as c:
            fila = c.execute(
                "SELECT COALESCE(MAX(secuencia_promovida), 0) + 1 "
                "FROM entrada_usuario").fetchone()
            c.execute(
                "UPDATE entrada_usuario SET estado=?, secuencia_promovida=?, "
                "task_id=COALESCE(?, task_id), actualizada_en=? WHERE id=?",
                (PROMOVIDA, int(fila[0]), task_id, time.time(), entrada_id))

    def descartar(self, entrada_id: str, motivo: str) -> None:
        """
        No se atendió, y AQUÍ QUEDA POR QUÉ.

        `motivo` no puede ir vacío: la restricción de la migración 0004 hace
        fallar la escritura. Es deliberado — un descarte sin motivo es
        exactamente el fallo que este módulo existe para impedir.
        """
        if not (motivo or "").strip():
            raise ValueError(
                "descartar una entrada sin motivo es el fallo que este libro "
                "existe para impedir")
        with self._conn() as c:
            c.execute("UPDATE entrada_usuario SET estado=?, motivo=?, "
                      "actualizada_en=? WHERE id=?",
                      (DESCARTADA, motivo.strip(), time.time(), entrada_id))
        logger.info("[admision] %s descartada: %s", entrada_id, motivo)

    def fallar(self, entrada_id: str, motivo: str) -> None:
        """Se intentó atender y reventó. También queda escrito."""
        with self._conn() as c:
            c.execute("UPDATE entrada_usuario SET estado=?, motivo=?, "
                      "actualizada_en=? WHERE id=?",
                      (FALLIDA, (motivo or "error sin detalle")[:2000],
                       time.time(), entrada_id))


    # -------------------------------------------------------------- lectura

    def _leer(self, sql: str, args: tuple) -> list[Entrada]:
        with self._conn() as c:
            filas = c.execute(sql, args).fetchall()
        return [Entrada(
            id=f["id"], task_id=f["task_id"], texto=f["texto"],
            origen=f["origen"], entrega=f["entrega"],
            secuencia_admitida=f["secuencia_admitida"], estado=f["estado"],
            motivo=f["motivo"], secuencia_promovida=f["secuencia_promovida"],
            admitida_en=f["admitida_en"]) for f in filas]

    def en_cola(self, task_id: str) -> list[Entrada]:
        """Lo que espera turno para esta tarea, en orden de llegada."""
        return self._leer(
            "SELECT * FROM entrada_usuario WHERE task_id=? AND estado=? "
            "AND entrega=? ORDER BY secuencia_admitida", (task_id, ADMITIDA,
                                                          ENCOLAR))

    def siguiente_en_cola(self, task_id: str) -> Entrada | None:
        c = self.en_cola(task_id)
        return c[0] if c else None

    def recientes(self, limite: int = 50) -> list[Entrada]:
        return self._leer(
            "SELECT * FROM entrada_usuario ORDER BY secuencia_admitida DESC "
            "LIMIT ?", (limite,))

    def perdidas(self) -> list[Entrada]:
        """
        Entradas que se admitieron y nunca llegaron a ninguna parte.

        Debería estar siempre vacío mientras el proceso no esté a mitad de un
        turno. Si crece, hay un camino en el código que no cierra el ciclo — y
        ahora se ve, que era el problema.
        """
        return self._leer(
            "SELECT * FROM entrada_usuario WHERE estado=? AND entrega=? "
            "ORDER BY secuencia_admitida", (ADMITIDA, AHORA))
