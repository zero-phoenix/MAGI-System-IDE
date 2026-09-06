"""
Pruebas para los Sentidos y Brazos de Lilim (megaplan v13).

Verifica:
1. OJOS: Rasterización PDF a imagen, extracción de layout/bloques y análisis Google Lens.
2. OÍDOS: Inspección de metadatos de audio (WAV sintético), duración y escucha WASAPI.
3. BRAZOS: Exportación estructurada a Markdown, generación de Word DOCX, recorte y hash SHA256.
"""
from __future__ import annotations

import struct
import wave
from pathlib import Path

import pytest

from magi.modules.lilim.brazos import (
    calcular_sha256,
    exportar_a_docx,
    exportar_a_markdown,
    recortar_region_imagen,
)
from magi.modules.lilim.oidos import (
    InfoAudio,
    escuchar_subsistema_emulador,
    inspeccionar_fichero_audio,
)
from magi.modules.lilim.ojos import (
    ResultadoLens,
    analizar_documento_escaneado,
    extraer_texto_y_layout_pdf,
    rasterizar_pagina_pdf,
)


@pytest.fixture
def dummy_wav(tmp_path) -> Path:
    """Genera un archivo WAV PCM real sintético de 0.5 segundos a 16kHz."""
    ruta = tmp_path / "prueba.wav"
    sample_rate = 16000
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        # 0.5s de muestras a 440Hz
        muestras = [int(10000 * (i % 36) / 36) for i in range(8000)]
        datos = struct.pack(f"<{len(muestras)}h", *muestras)
        w.writeframes(datos)
    return ruta


@pytest.fixture
def dummy_pdf(tmp_path) -> Path:
    """Crea un documento PDF mínimo usando PyMuPDF (fitz)."""
    fitz = pytest.importorskip("fitz", reason="PyMuPDF (fitz) no instalado en este entorno")
    ruta = tmp_path / "documento.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 72), "RESOLUCIÓN N° 001-2026/INDECOPI", fontsize=14)
    page.insert_text((50, 120), "EXPEDIENTE: 0042-2026/CC1", fontsize=11)
    page.insert_text((50, 150), "ADMITIR A TRÁMITE la denuncia de consumo.", fontsize=11)
    doc.save(str(ruta))
    doc.close()
    return ruta


@pytest.fixture
def dummy_img(tmp_path) -> Path:
    """Crea una imagen PNG mínima con PIL."""
    Image = pytest.importorskip("PIL.Image", reason="Pillow no instalado")
    ruta = tmp_path / "captura.png"
    img = Image.new("RGB", (200, 100), color=(73, 109, 137))
    img.save(ruta)
    return ruta


# --- TESTS DE OJOS (VISIÓN / DOCUMENTAL) ---

def test_ojos_pdf_texto_y_layout(dummy_pdf):
    texto, bloques, pags = extraer_texto_y_layout_pdf(dummy_pdf)
    assert pags == 1
    assert "RESOLUCIÓN" in texto
    assert "ADMITIR" in texto
    assert len(bloques) >= 2
    assert "bbox" in bloques[0]


def test_ojos_rasterizar_pdf(dummy_pdf):
    png = rasterizar_pagina_pdf(dummy_pdf, num_pagina=0, dpi=72)
    assert png is not None
    assert png.startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.asyncio
async def test_ojos_analizar_documento_pdf(dummy_pdf):
    res_pdf = await analizar_documento_escaneado(dummy_pdf)
    assert res_pdf.tipo == "pdf"
    assert res_pdf.total_paginas == 1
    assert "RESOLUCIÓN" in res_pdf.texto_crudo


@pytest.mark.asyncio
async def test_ojos_analizar_documento_imagen(dummy_img):
    res_img = await analizar_documento_escaneado(dummy_img)
    assert res_img.tipo == "imagen"
    assert res_img.dimensiones == [200, 100]


@pytest.mark.asyncio
async def test_ojos_analizar_documento_inexistente():
    res_inexistente = await analizar_documento_escaneado("no_existe.pdf")
    assert res_inexistente.tipo == "error"


# --- TESTS DE OÍDOS (ACÚSTICA / SEÑAL) ---

def test_oidos_inspeccionar_wav(dummy_wav):
    info = inspeccionar_fichero_audio(dummy_wav)
    assert info.formato == "WAV"
    assert info.sample_rate == 16000
    assert info.canales == 1
    assert info.duracion_segundos > 0.4
    assert info.tiene_senal is True


def test_oidos_inexistente():
    info = inspeccionar_fichero_audio("no_existe.wav")
    assert info.formato == "error"


def test_oidos_escucha_emulador():
    res = escuchar_subsistema_emulador(segundos=0.1)
    assert "disponible" in res


# --- TESTS DE BRAZOS (TRANSFORMACIÓN / ACTUACIÓN) ---

def test_brazos_exportar_markdown(tmp_path):
    res = ResultadoLens(
        tipo="pdf",
        ruta="expediente.pdf",
        total_paginas=2,
        texto_crudo="Texto de prueba",
        analisis_vlm="Documento legal verificado.",
    )
    salida = tmp_path / "informe.md"
    p = exportar_a_markdown(res, salida)
    assert p.exists()
    contenido = p.read_text(encoding="utf-8")
    assert "Lilim Lens" in contenido
    assert "Documento legal verificado." in contenido


def test_brazos_exportar_docx(tmp_path):
    pytest.importorskip("docx", reason="python-docx no instalado")
    salida = tmp_path / "resolucion.docx"
    p = exportar_a_docx(
        titulo="RESOLUCIÓN ADMISORIA",
        parrafos=["Se admite a trámite la denuncia.", "Notifíquese a las partes."],
        ruta_salida=salida,
        tablas=[[["N°", "Parte"], ["1", "Denunciante"], ["2", "Denunciado"]]],
    )
    assert p is not None
    assert p.exists()
    assert p.stat().st_size > 1000


def test_brazos_recortar_imagen(dummy_img, tmp_path):
    pytest.importorskip("PIL.Image", reason="Pillow no instalado")
    salida = tmp_path / "recorte.png"
    p = recortar_region_imagen(dummy_img, (10, 10, 50, 50), salida)
    assert p is not None
    assert p.exists()


def test_brazos_calcular_sha256(dummy_img):
    h = calcular_sha256(dummy_img)
    assert len(h) == 64
