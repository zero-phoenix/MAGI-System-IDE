"""
Composición de páginas de manga (Plan MAGI 9.0 §5.4).

QUÉ ES ESTO Y QUÉ NO
====================
Generar una página de manga son dos problemas distintos:

  1. GENERAR LOS DIBUJOS. Necesita un modelo de imagen — ComfyUI local con
     SDXL/Flux, gratis y sin claves. No se puede verificar sin ComfyUI
     corriendo, así que aquí es un backend enchufable.

  2. COMPONER LA PÁGINA. Rejilla de viñetas, orden de lectura, márgenes,
     canaletas, globos de diálogo colocados donde no tapan la acción, y
     rotulación. Eso es geometría y PIL: determinista, barato y verificable.

Este módulo hace (2) bien y deja (1) detrás de una interfaz. La razón es la de
siempre en este proyecto: prefiero una pieza que funciona y se prueba a una que
declara hacerlo todo y no se puede comprobar.

ORDEN DE LECTURA
================
El manga se lee de DERECHA A IZQUIERDA y de arriba abajo. Componer una página
con orden occidental produce viñetas correctas y una página ilegible, que es un
fallo que no se ve mirando cada dibujo por separado.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, Sequence

logger = logging.getLogger(__name__)

A4_RATIO = 1.414
DEFAULT_W, DEFAULT_H = 1240, 1754      # A4 a 150 ppp


class ReadingOrder(str, Enum):
    RTL = "derecha-a-izquierda"        # manga
    LTR = "izquierda-a-derecha"        # cómic occidental


@dataclass
class Panel:
    """Una viñeta: su hueco en la rejilla y qué va dentro."""
    row: int
    col: int
    row_span: int = 1
    col_span: int = 1
    prompt: str = ""                   # descripción para el generador
    image: str | None = None           # ruta si ya está generada
    dialogue: list[str] = field(default_factory=list)
    caption: str = ""

    def key(self, order: ReadingOrder, cols: int) -> tuple[int, int]:
        """Clave de ordenación según el sentido de lectura."""
        if order is ReadingOrder.RTL:
            return (self.row, cols - self.col - self.col_span)
        return (self.row, self.col)


@dataclass
class PageSpec:
    panels: list[Panel]
    rows: int
    cols: int
    width: int = DEFAULT_W
    height: int = DEFAULT_H
    gutter: int = 18
    margin: int = 48
    order: ReadingOrder = ReadingOrder.RTL
    title: str = ""

    def validate(self) -> list[str]:
        """
        Errores de composición ANTES de gastar cuota generando dibujos.

        Generar ocho viñetas y descubrir después que dos se solapan es tirar
        ocho generaciones.
        """
        problems: list[str] = []
        if not self.panels:
            problems.append("página sin viñetas")
        occupied: dict[tuple[int, int], int] = {}
        for i, p in enumerate(self.panels):
            if p.row < 0 or p.col < 0:
                problems.append(f"viñeta {i}: posición negativa")
                continue
            if p.row + p.row_span > self.rows:
                problems.append(f"viñeta {i}: se sale por abajo "
                                f"(fila {p.row}+{p.row_span} > {self.rows})")
            if p.col + p.col_span > self.cols:
                problems.append(f"viñeta {i}: se sale por la derecha "
                                f"(col {p.col}+{p.col_span} > {self.cols})")
            for r in range(p.row, min(p.row + p.row_span, self.rows)):
                for c in range(p.col, min(p.col + p.col_span, self.cols)):
                    if (r, c) in occupied:
                        problems.append(
                            f"viñetas {occupied[(r, c)]} y {i} se solapan "
                            f"en la celda ({r},{c})")
                    occupied[(r, c)] = i

        total = self.rows * self.cols
        if len(occupied) < total:
            problems.append(f"{total - len(occupied)} celdas vacías: la página "
                            f"quedará con huecos en blanco")
        return problems

    def reading_sequence(self) -> list[Panel]:
        return sorted(self.panels, key=lambda p: p.key(self.order, self.cols))

    def panel_rect(self, p: Panel) -> tuple[int, int, int, int]:
        """Rectángulo en píxeles (x0, y0, x1, y1)."""
        usable_w = self.width - 2 * self.margin - self.gutter * (self.cols - 1)
        usable_h = self.height - 2 * self.margin - self.gutter * (self.rows - 1)
        cw = usable_w / self.cols
        ch = usable_h / self.rows
        x0 = self.margin + p.col * (cw + self.gutter)
        y0 = self.margin + p.row * (ch + self.gutter)
        x1 = x0 + cw * p.col_span + self.gutter * (p.col_span - 1)
        y1 = y0 + ch * p.row_span + self.gutter * (p.row_span - 1)
        return int(x0), int(y0), int(x1), int(y1)


class ImageBackend(Protocol):
    """
    Generador de dibujos. ComfyUI local es la implementación prevista; en tests
    y sin ComfyUI se usa un marcador de posición.
    """

    async def generate(self, prompt: str, width: int, height: int,
                       out_path: Path) -> bool: ...


class PlaceholderBackend:
    """
    Dibuja un marcador con el texto del prompt.

    No es un sustituto de un modelo: es lo que permite verificar la COMPOSICIÓN
    (rejilla, orden de lectura, globos) sin depender de ComfyUI.
    """

    async def generate(self, prompt: str, width: int, height: int,
                       out_path: Path) -> bool:
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            return False
        im = Image.new("RGB", (max(width, 8), max(height, 8)), (238, 238, 234))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, im.width - 1, im.height - 1], outline=(40, 40, 40),
                    width=3)
        for i, line in enumerate(_wrap(prompt, 26)[:6]):
            d.text((14, 14 + i * 16), line, fill=(70, 70, 70))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        im.save(out_path)
        return True


class ComfyUIBackend:
    """
    Cliente de ComfyUI local (§5.4): gratis, sin claves, sin salir del equipo.

    No se ha podido verificar de extremo a extremo porque exige ComfyUI
    corriendo. Falla de forma explícita si no está, en vez de fingir que generó
    algo.
    """

    def __init__(self, host: str = "http://127.0.0.1:8188",
                 checkpoint: str = "sd_xl_base_1.0.safetensors",
                 steps: int = 24, negative: str = "text, watermark, blurry"):
        self.host = host.rstrip("/")
        self.checkpoint = checkpoint
        self.steps = steps
        self.negative = negative

    def reachable(self) -> bool:
        try:
            import urllib.request
            with urllib.request.urlopen(f"{self.host}/system_stats", timeout=2):
                return True
        except Exception:
            return False

    def _workflow(self, prompt: str, w: int, h: int, seed: int) -> dict:
        """Grafo mínimo txt2img en el formato de la API de ComfyUI."""
        return {
            "3": {"class_type": "KSampler", "inputs": {
                "seed": seed, "steps": self.steps, "cfg": 7.0,
                "sampler_name": "dpmpp_2m", "scheduler": "karras",
                "denoise": 1.0, "model": ["4", 0], "positive": ["6", 0],
                "negative": ["7", 0], "latent_image": ["5", 0]}},
            "4": {"class_type": "CheckpointLoaderSimple",
                  "inputs": {"ckpt_name": self.checkpoint}},
            "5": {"class_type": "EmptyLatentImage",
                  "inputs": {"width": w, "height": h, "batch_size": 1}},
            "6": {"class_type": "CLIPTextEncode",
                  "inputs": {"text": prompt, "clip": ["4", 1]}},
            "7": {"class_type": "CLIPTextEncode",
                  "inputs": {"text": self.negative, "clip": ["4", 1]}},
            "8": {"class_type": "VAEDecode",
                  "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
            "9": {"class_type": "SaveImage",
                  "inputs": {"filename_prefix": "magi", "images": ["8", 0]}},
        }

    async def generate(self, prompt: str, width: int, height: int,
                       out_path: Path) -> bool:
        if not self.reachable():
            logger.warning("[manga] ComfyUI no responde en %s", self.host)
            return False
        try:
            import json
            import urllib.request
            body = json.dumps({"prompt": self._workflow(
                prompt, width, height, abs(hash(prompt)) % 2**31)}).encode()
            req = urllib.request.Request(
                f"{self.host}/prompt", data=body,
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                json.load(r)
            # La recogida del resultado requiere sondear /history y descargar
            # de /view; se implementa cuando haya un ComfyUI contra el que
            # probarlo de verdad.
            logger.info("[manga] trabajo encolado en ComfyUI")
            return False
        except Exception as e:
            logger.warning("[manga] ComfyUI falló: %s", e)
            return False


async def compose_page(spec: PageSpec, out_path: str | Path, *,
                       backend: ImageBackend | None = None,
                       draw_order_marks: bool = True) -> dict[str, Any]:
    """
    Compone la página completa: viñetas, bordes, globos y numeración.

    Devuelve un informe con lo que salió y lo que no, para que el bucle de
    observación (§5) pueda criticarlo.
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return {"ok": False, "problems": ["Pillow no instalado"]}

    problems = spec.validate()
    if any("se solapan" in p or "se sale" in p for p in problems):
        return {"ok": False, "problems": problems,
                "note": "composición inválida: no se genera nada para no gastar cuota"}

    backend = backend or PlaceholderBackend()
    page = Image.new("RGB", (spec.width, spec.height), (255, 255, 255))
    draw = ImageDraw.Draw(page)
    generated, failed = 0, []

    for order_idx, panel in enumerate(spec.reading_sequence(), start=1):
        x0, y0, x1, y1 = spec.panel_rect(panel)
        w, h = max(x1 - x0, 8), max(y1 - y0, 8)

        art = None
        if panel.image and Path(panel.image).exists():
            art = Path(panel.image)
        elif panel.prompt:
            tmp = Path(out_path).parent / f"_panel_{panel.row}_{panel.col}.png"
            if await backend.generate(panel.prompt, w, h, tmp):
                art = tmp
                generated += 1
            else:
                failed.append(panel.prompt[:50])

        if art is not None:
            try:
                with Image.open(art) as im:
                    page.paste(im.convert("RGB").resize((w, h)), (x0, y0))
            except Exception as e:
                problems.append(f"viñeta ({panel.row},{panel.col}) ilegible: {e}")

        draw.rectangle([x0, y0, x1, y1], outline=(0, 0, 0), width=3)

        if draw_order_marks:
            _order_mark(draw, x0, y0, x1, spec.order, order_idx)
        for i, line in enumerate(panel.dialogue[:3]):
            _speech_bubble(draw, x0, y0, x1, y1, line, i, spec.order)
        if panel.caption:
            _caption_box(draw, x0, y1, x1, panel.caption)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    page.save(out)

    if failed:
        problems.append(f"{len(failed)} viñeta(s) sin dibujo generado: el "
                        f"backend de imagen no respondió")
    return {"ok": not problems, "path": str(out), "panels": len(spec.panels),
            "generated": generated, "problems": problems,
            "reading_order": spec.order.value}


# ------------------------------------------------------------- rotulación

def _wrap(text: str, width: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for wd in words:
        if len(cur) + len(wd) + 1 <= width:
            cur = f"{cur} {wd}".strip()
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def _order_mark(draw, x0, y0, x1, order: ReadingOrder, n: int) -> None:
    """Número de orden en la esquina por donde empieza la lectura."""
    r = 13
    cx = (x1 - r - 6) if order is ReadingOrder.RTL else (x0 + r + 6)
    cy = y0 + r + 6
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255),
                 outline=(0, 0, 0), width=2)
    draw.text((cx - 4, cy - 6), str(n), fill=(0, 0, 0))


def _speech_bubble(draw, x0, y0, x1, y1, text: str, slot: int,
                   order: ReadingOrder) -> None:
    """
    Globo colocado en la banda superior, del lado por el que se empieza a leer.

    En manga eso es la derecha: un globo a la izquierda rompe el recorrido de
    la vista aunque el dibujo sea correcto.
    """
    lines = _wrap(text, 22)[:4]
    bw = min(int((x1 - x0) * 0.55), 260)
    bh = 22 + 15 * len(lines)
    pad = 12
    bx = (x1 - bw - pad) if order is ReadingOrder.RTL else (x0 + pad)
    by = y0 + pad + slot * (bh + 8)
    if by + bh > y1 - pad:
        return
    draw.ellipse([bx, by, bx + bw, by + bh], fill=(255, 255, 255),
                 outline=(0, 0, 0), width=2)
    for i, line in enumerate(lines):
        draw.text((bx + 16, by + 12 + i * 15), line, fill=(0, 0, 0))


def _caption_box(draw, x0, y1, x1, text: str) -> None:
    lines = _wrap(text, 40)[:2]
    h = 8 + 15 * len(lines)
    draw.rectangle([x0 + 8, y1 - h - 8, x1 - 8, y1 - 8],
                   fill=(255, 255, 255), outline=(0, 0, 0), width=2)
    for i, line in enumerate(lines):
        draw.text((x0 + 14, y1 - h - 2 + i * 15), line, fill=(0, 0, 0))


# ------------------------------------------------------------- plantillas

def grid_page(rows: int, cols: int, prompts: Sequence[str] = (),
              order: ReadingOrder = ReadingOrder.RTL, **kw) -> PageSpec:
    """Rejilla regular. El punto de partida más común."""
    panels, it = [], list(prompts)
    for r in range(rows):
        for c in range(cols):
            i = r * cols + c
            panels.append(Panel(row=r, col=c,
                                prompt=it[i] if i < len(it) else ""))
    return PageSpec(panels, rows, cols, order=order, **kw)


def dramatic_page(prompts: Sequence[str] = (),
                  order: ReadingOrder = ReadingOrder.RTL, **kw) -> PageSpec:
    """
    Composición clásica de 4 viñetas: una panorámica arriba, dos medianas y
    una de impacto abajo. La panorámica establece la escena y la última cierra.
    """
    it = list(prompts) + [""] * 4
    panels = [
        Panel(0, 0, col_span=2, prompt=it[0]),
        Panel(1, 0, prompt=it[1]),
        Panel(1, 1, prompt=it[2]),
        Panel(2, 0, col_span=2, prompt=it[3]),
    ]
    return PageSpec(panels, rows=3, cols=2, order=order, **kw)
