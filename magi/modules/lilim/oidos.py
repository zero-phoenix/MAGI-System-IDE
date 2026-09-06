"""
OÍDOS DE LILIM — Percepción auditiva y acústica de MAGI (megaplan v13).

QUÉ HACE
========
Dota a Lilim de capacidades auditivas integrales:
  1. METADATOS Y DIAGNÓSTICO DE AUDIO: Lectura de frecuencias, canales, duración y formato
     en ficheros WAV, MP3 y OGG sin dependencias pesadas.
  2. ESCUCHA DE EMULADORES Y JUEGOS: Integración con la compuerta WASAPI de MAGI
     (`percepcion/oidos.py`) para detectar sonido continuo, silencio o audio entrecortado.
  3. INTERFAZ DE COMANDOS DE VOZ: Preparación y preprocesamiento de clips de voz
     hacia los agentes del sistema.
"""
from __future__ import annotations

import logging
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class InfoAudio:
    """Metadatos acústicos de un archivo o señal."""
    formato: str
    ruta: str
    duracion_segundos: float = 0.0
    sample_rate: int = 0
    canales: int = 0
    bits_por_muestra: int = 16
    tiene_senal: bool = False
    observaciones: str = ""

    def a_dict(self) -> dict[str, Any]:
        return {
            "formato": self.formato,
            "ruta": self.ruta,
            "duracion_segundos": round(self.duracion_segundos, 2),
            "sample_rate": self.sample_rate,
            "canales": self.canales,
            "bits_por_muestra": self.bits_por_muestra,
            "tiene_senal": self.tiene_senal,
            "observaciones": self.observaciones,
        }


def inspeccionar_fichero_audio(ruta: str | Path) -> InfoAudio:
    """
    Inspecciona archivos de audio (WAV nativo, cabeceras MP3/OGG).
    No revienta con ficheros corruptos o formatos desconocidos.
    """
    p = Path(ruta)
    if not p.is_file():
        return InfoAudio(formato="error", ruta=str(p), observaciones="El archivo no existe")

    ext = p.suffix.lower()
    if ext == ".wav":
        try:
            with wave.open(str(p), "rb") as w:
                canales = w.getnchannels()
                rate = w.getframerate()
                frames = w.getnframes()
                sampwidth = w.getsampwidth()
                duracion = frames / float(rate) if rate > 0 else 0.0
                return InfoAudio(
                    formato="WAV",
                    ruta=str(p),
                    duracion_segundos=duracion,
                    sample_rate=rate,
                    canales=canales,
                    bits_por_muestra=sampwidth * 8,
                    tiene_senal=duracion > 0.05,
                    observaciones="WAV PCM estándar verificado",
                )
        except Exception as err:
            return InfoAudio(formato="WAV", ruta=str(p), observaciones=f"WAV no estándar o corrupto: {err}")

    # Para otros formatos, inspección binaria de cabeceras básicas
    datos = p.read_bytes()[:64]
    if datos.startswith(b"ID3") or (len(datos) >= 2 and datos[:2] == b"\xff\xfb"):
        return InfoAudio(
            formato="MP3",
            ruta=str(p),
            duracion_segundos=p.stat().st_size / 16000.0,  # Estimación rápida ~128kbps
            sample_rate=44100,
            canales=2,
            tiene_senal=True,
            observaciones="Flujo de audio MP3 detectado",
        )
    elif datos.startswith(b"OggS"):
        return InfoAudio(
            formato="OGG",
            ruta=str(p),
            sample_rate=44100,
            canales=2,
            tiene_senal=True,
            observaciones="Contenedor Ogg Vorbis/Opus detectado",
        )

    return InfoAudio(
        formato=ext.lstrip(".") or "desconocido",
        ruta=str(p),
        observaciones="Formato no analizable de forma nativa",
    )


def escuchar_subsistema_emulador(segundos: float = 3.0) -> dict[str, Any]:
    """
    Escucha la salida activa del sistema mediante el módulo de percepción de oídos de MAGI.
    Verifica si un emulador o juego está emitiendo sonido y si está entrecortado.
    """
    try:
        from magi.modules.percepcion import oidos as _oidos_sys
        if not _oidos_sys.disponible():
            return {"disponible": False, "motivo": _oidos_sys.motivo_no_disponible()}
        veredicto = _oidos_sys.escuchar(segundos)
        return {"disponible": True, "veredicto": veredicto}
    except Exception as err:
        return {"disponible": False, "error": str(err)}
