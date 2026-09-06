"""
BRAZOS DE LILIM — Ejecución, transformación documental y actuación en el workspace (megaplan v13).

QUÉ HACE
========
Confiere a Lilim la capacidad de actuar físicamente sobre el sistema de archivos:
  1. TRANSFORMACIÓN DOCUMENTAL: Exportación de resultados de escaneo a Markdown o Word (.docx)
     formateado profesionalmente (usando python-docx si está disponible).
  2. RECORTE VISUAL DE ZONAS: Recorte de cajas delimitadoras (bounding boxes) sobre imágenes o PDFs.
  3. DESPACHO DE ARTEFACTOS: Entrega de transcripciones y contratos hacia el workspace del usuario
     con cálculo de hash SHA-256 de procedencia.
"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from .ojos import ResultadoLens

logger = logging.getLogger(__name__)


def exportar_a_markdown(resultado: ResultadoLens, ruta_salida: str | Path) -> Path:
    """
    Guarda el análisis visual/documental en formato Markdown estructurado con procedencia.
    """
    p = Path(ruta_salida)
    p.parent.mkdir(parents=True, exist_ok=True)

    lineas = [
        "# Transcripción y Análisis Documental (Lilim Lens)",
        f"- **Archivo Origen**: `{resultado.ruta}`",
        f"- **Tipo**: {resultado.tipo.upper()}",
        f"- **Páginas**: {resultado.total_paginas}",
    ]
    if resultado.dimensiones:
        lineas.append(f"- **Dimensiones**: {resultado.dimensiones[0]}x{resultado.dimensiones[1]} px")

    if resultado.analisis_vlm:
        lineas.extend([
            "",
            "## Síntesis Visual y Estructura (VLM Local)",
            resultado.analisis_vlm,
        ])

    if resultado.texto_crudo:
        lineas.extend([
            "",
            "## Contenido Textual Extraído",
            resultado.texto_crudo,
        ])

    if resultado.bloques_layout:
        lineas.extend([
            "",
            f"## Bloques de Layout Espacial ({len(resultado.bloques_layout)} detectados)",
            "| Página | Bounding Box [x0, y0, x1, y1] | Muestra |",
            "| :---: | :---: | :--- |",
        ] + [
            f"| {b['pagina']} | `{b['bbox']}` | {b['texto'][:60]}... |"
            for b in resultado.bloques_layout[:25]
        ])

    contenido = "\n".join(lineas)
    p.write_text(contenido, encoding="utf-8")
    return p


def exportar_a_docx(
    titulo: str,
    parrafos: list[str],
    ruta_salida: str | Path,
    tablas: list[list[list[str]]] | None = None,
) -> Path | None:
    """
    Genera un documento Word (.docx) formal a partir del contenido procesado.
    Utiliza python-docx. Si no está instalado, retorna None.
    """
    p = Path(ruta_salida)
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        import docx
        doc = docx.Document()
        doc.add_heading(titulo, level=1)
        for parrafo in parrafos:
            if parrafo.strip():
                doc.add_paragraph(parrafo.strip())

        if tablas:
            for matriz in tablas:
                if not matriz:
                    continue
                filas = len(matriz)
                cols = len(matriz[0]) if filas > 0 else 0
                tabla = doc.add_table(rows=filas, cols=cols)
                tabla.style = "Table Grid"
                for i, fila in enumerate(matriz):
                    for j, celda in enumerate(fila):
                        tabla.cell(i, j).text = str(celda)

        doc.save(str(p))
        return p
    except Exception as err:
        logger.warning("Fallo al exportar docx en %s: %s", p, err)
        return None


def recortar_region_imagen(
    ruta_imagen: str | Path,
    bbox: tuple[int, int, int, int],
    ruta_salida: str | Path,
) -> Path | None:
    """
    Recorta una región específica (x0, y0, x1, y1) de una imagen escaneada.
    """
    origen = Path(ruta_imagen)
    destino = Path(ruta_salida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image
        with Image.open(origen) as img:
            recorte = img.crop(bbox)
            recorte.save(destino)
            return destino
    except Exception as err:
        logger.warning("Fallo al recortar imagen %s: %s", origen, err)
        return None


def calcular_sha256(ruta: str | Path) -> str:
    """Calcula el hash SHA-256 de procedencia de cualquier artefacto generado."""
    p = Path(ruta)
    if not p.exists():
        return ""
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()
