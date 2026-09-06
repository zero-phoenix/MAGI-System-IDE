"""
Plan visible con estado por tarea (Megaplan F3).

Invariantes de F3:
1. plan.md por tarea con una línea por parte del encargo y su estado
   ('pendiente' / 'haciendo' / 'hecha' / 'no se pudo').
2. Inyectado en el prompt para que el enjambre conteste todas las partes.
3. Compuerta F3: Casper no puede cerrar con partes en 'pendiente' sin decir por qué.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

PlanEstado = Literal["pendiente", "haciendo", "hecha", "no se pudo"]

_ESTADOS_VALIDOS: set[PlanEstado] = {"pendiente", "haciendo", "hecha", "no se pudo"}


@dataclass
class PlanItem:
    """Una parte o hito del encargo."""
    id: str
    descripcion: str
    estado: PlanEstado = "pendiente"
    motivo: str = ""

    def a_linea(self) -> str:
        sufijo = f" (motivo: {self.motivo})" if self.motivo else ""
        marca = {
            "hecha": "[x]",
            "haciendo": "[/]",
            "no se pudo": "[-]",
            "pendiente": "[ ]",
        }.get(self.estado, "[ ]")
        return f"- {marca} [{self.estado}] {self.id}: {self.descripcion}{sufijo}"


@dataclass
class PlanTarea:
    """Plan vivo de una tarea compuesto por items con estado."""
    task_id: str
    items: list[PlanItem] = field(default_factory=list)

    def agregar_item(self, descripcion: str, id_item: str = "") -> PlanItem:
        idx = id_item or f"parte_{len(self.items) + 1}"
        item = PlanItem(id=idx, descripcion=descripcion.strip())
        self.items.append(item)
        return item

    def actualizar_estado(
        self, id_item: str, estado: PlanEstado, motivo: str = ""
    ) -> bool:
        if estado not in _ESTADOS_VALIDOS:
            return False
        for item in self.items:
            if item.id == id_item or item.descripcion.lower() == id_item.lower():
                item.estado = estado
                if motivo:
                    item.motivo = motivo
                return True
        return False

    def a_markdown(self) -> str:
        lineas = [f"# Plan de Tarea: {self.task_id}\n"]
        for item in self.items:
            lineas.append(item.a_linea())
        return "\n".join(lineas)

    def desde_markdown(self, md_text: str) -> None:
        self.items.clear()
        for linea in md_text.splitlines():
            linea = linea.strip()
            if not linea.startswith("- ["):
                continue
            m = re.match(
                r"- \[[ x/\-]\]\s*\[([a-z ]+)\]\s*([^:]+):\s*(.*?)(?:\s*\(motivo:\s*(.*?)\))?$",
                linea,
                re.IGNORECASE,
            )
            if m:
                est = m.group(1).strip().lower()
                estado: PlanEstado = (
                    est if est in _ESTADOS_VALIDOS else "pendiente"  # type: ignore[assignment]
                )
                self.items.append(
                    PlanItem(
                        id=m.group(2).strip(),
                        descripcion=m.group(3).strip(),
                        estado=estado,
                        motivo=(m.group(4) or "").strip(),
                    )
                )

    def para_el_prompt(self) -> str:
        if not self.items:
            return ""
        lineas = [
            "### ESTADO DEL PLAN DE TRABAJO (plan.md)",
            "Regla F3: Todas las partes del encargo deben abordarse. No cierres con "
            "partes pendientes sin justificar.",
        ]
        for it in self.items:
            lineas.append(it.a_linea())
        return "\n".join(lineas)

    def guardar(self, directorio: Path) -> Path:
        p = Path(directorio) / "plan.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.a_markdown(), encoding="utf-8")
        return p


def crear_plan_desde_enunciado(task_id: str, enunciado: str) -> PlanTarea:
    """Extrae las partes de un enunciado (listas numeradas o párrafos)."""
    plan = PlanTarea(task_id=task_id)
    lineas = [line.strip() for line in (enunciado or "").splitlines() if line.strip()]

    # Buscar listas tipo 1. ..., 2. ... o a) ..., b) ...
    partes_encontradas: list[str] = []
    for line in lineas:
        m = re.match(r"^(\d+[\.\)]|[a-zA-Z][\.\)]|\-|\*)\s+(.+)$", line)
        if m and len(m.group(2)) > 5:
            partes_encontradas.append(m.group(2))

    if partes_encontradas:
        for i, parte in enumerate(partes_encontradas, 1):
            plan.agregar_item(parte, id_item=f"parte_{i}")
    else:
        # Enunciado indivisible: una sola parte principal
        plan.agregar_item(enunciado.strip()[:200], id_item="parte_1")

    return plan


def verificar_cierre_plan(plan: PlanTarea | None) -> tuple[bool, str]:
    """Compuerta F3: Casper no puede cerrar con partes en 'pendiente' sin decir por qué."""
    if plan is None or not plan.items:
        return True, "Sin partes de plan declaradas."

    pendientes = [it for it in plan.items if it.estado == "pendiente"]
    if pendientes:
        detalle = ", ".join(f"'{p.id}: {p.descripcion}'" for p in pendientes)
        return (
            False,
            f"COMPUERTA F3 RECHAZADA: El plan aún tiene partes en estado 'pendiente' "
            f"sin justificación: {detalle}. Márcalas como 'hecha' o 'no se pudo' con su motivo.",
        )

    return True, "Todas las partes del plan fueron resueltas o justificadas."
