"""
Oídos: saber si suena, y si suena entero (R16).

LA MEDICIÓN QUE OBLIGÓ A ESCRIBIR ESTO
======================================
R9 puso ojos a las corridas: sin imagen y sin movimiento, no hay corrida. El
sonido es la otra mitad, y faltaba. Un juego con el audio caído o a
trompicones está roto igual, y **el log no lo muestra**: en YabauseVita,
`scsp_th` gasta 1,1-1,4 s de cada ventana de 5 s produciendo audio, y ese
número es idéntico tanto si el audio sale limpio como si no sale.

Un contador de CPU no distingue «suena» de «suena a trompicones» igual que los
FPS no distinguían «hay imagen» de «pantalla negra».

QUÉ MIDE
========
Captura el loopback WASAPI de la salida por defecto y lo trocea en tramos de
100 ms. De ahí salen tres cosas distintas que no hay que confundir:

  - `has_sound`   — hubo energía sostenida (≥30 % de los tramos por encima de
                    ~-48 dBFS). Responde «¿salió audio?».
  - `choppy`      — hubo sonido, pero con ≥8 transiciones sonido→silencio.
                    Responde «¿salió entero?». Un audio continuo tiene pocas
                    caídas a silencio; uno con underruns tiene muchas.
  - `sonando_pct` — cuánto del tiempo hubo señal. Es el dato crudo, por si el
                    umbral binario de arriba se queda corto para un caso.

POR QUÉ pyaudiowpatch Y NO sounddevice
======================================
`sounddevice` está instalado y ve los dispositivos, pero la versión disponible
no expone el loopback WASAPI: se puede grabar del micrófono, no de lo que
suena. Grabar el micrófono para juzgar el audio de un emulador mide la
habitación, no el emulador.

DEGRADACIÓN
===========
El backend es opcional, como capstone o pygame: en Linux (donde corre medio
CI) y en una máquina sin la biblioteca, importar este módulo funciona y
`disponible()` devuelve False con el motivo. Lo que NO hace es fingir un
veredicto: sin captura no hay `has_sound`, hay `error`.
"""
from __future__ import annotations

import time
from typing import Any

__all__ = ["disponible", "motivo_no_disponible", "Oidos", "escuchar",
           "UMBRAL_RMS", "TRAMO_MS"]

#: ~-48 dBFS sobre un tramo de 100 ms. Por debajo se considera silencio.
UMBRAL_RMS = 0.004
TRAMO_MS = 100
#: Fracción de tramos con señal para llamarlo «hubo sonido».
FRAC_MINIMA = 0.30
#: Transiciones sonido→silencio a partir de las cuales se llama entrecortado.
CORTES_MAXIMOS = 8


def _backend():
    """Importa el backend a demanda. Nunca en el import del módulo: la mitad
    del CI corre en Linux y este paquete solo existe en Windows."""
    try:
        import numpy as np
        import pyaudiowpatch as pa
        return pa, np, ""
    except Exception as e:          # pragma: no cover - depende del sistema
        return None, None, str(e)


def disponible() -> bool:
    pa, _, _ = _backend()
    return pa is not None


def motivo_no_disponible() -> str:
    _, _, err = _backend()
    return err


class Oidos:
    """
    Escucha mientras otra cosa corre.

        o = Oidos()
        o.empezar()
        ... arrancar el juego y esperar ...
        veredicto = o.parar()

    `parar()` siempre devuelve un dict. Si no hubo captura devuelve `error`
    en vez de un `has_sound` inventado: «no pude oírlo» y «no sonaba» son
    cosas distintas, y confundirlas es el fallo que R9 vino a corregir del
    lado de la imagen.
    """

    def __init__(self, tramo_ms: int = TRAMO_MS):
        self.tramo_ms = tramo_ms
        self._chunks: list = []
        self._pa = None
        self._stream = None
        self.sr = 0
        self.canales = 0

    # -- captura ----------------------------------------------------------

    def empezar(self) -> bool:
        pa, np, err = _backend()
        if pa is None:
            self._error = err
            return False
        self._np = np
        self._pa = pa.PyAudio()
        salida = self._pa.get_default_output_device_info()
        prefijo = salida["name"][:20]
        lb = None
        for d in self._pa.get_loopback_device_info_generator():
            if prefijo in d["name"]:
                lb = d
                break
        if lb is None:
            try:
                lb = next(self._pa.get_loopback_device_info_generator())
            except StopIteration:
                self._error = "no hay dispositivo de loopback"
                self._pa.terminate()
                self._pa = None
                return False
        self.sr = int(lb["defaultSampleRate"])
        self.canales = int(lb["maxInputChannels"])
        marco = self.sr * self.tramo_ms // 1000
        self._stream = self._pa.open(
            format=pa.paFloat32, channels=self.canales, rate=self.sr,
            input=True, input_device_index=lb["index"],
            frames_per_buffer=marco, stream_callback=self._cb)
        self._stream.start_stream()
        return True

    def _cb(self, datos, n, info, estado):
        import pyaudiowpatch as pa
        x = self._np.frombuffer(datos, dtype=self._np.float32)
        if self.canales >= 2:
            x = x.reshape(-1, self.canales).mean(axis=1)
        self._chunks.append(x.copy())
        return (datos, pa.paContinue)

    def parar(self) -> dict[str, Any]:
        if self._stream is not None:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        if self._pa is not None:
            self._pa.terminate()
            self._pa = None
        if not self._chunks:
            return {"has_sound": None, "choppy": None,
                    "error": getattr(self, "_error", "sin captura")}
        x = self._np.concatenate(self._chunks)
        return veredicto([float(v) for v in x], self.sr, self.tramo_ms)


# -- análisis (separado de la captura para poder probarlo sin tarjeta) -----

def veredicto(muestras: list[float], sr: int,
              tramo_ms: int = TRAMO_MS) -> dict[str, Any]:
    """
    El juicio, a partir de muestras crudas.

    Vive fuera de `Oidos` a propósito: así se puede probar con una señal
    sintética —continua, silenciosa o troceada— sin tarjeta de sonido y sin
    Windows. Un veredicto que solo se puede comprobar teniendo el hardware
    delante es un veredicto que nadie comprueba.
    """
    marco = max(1, sr * tramo_ms // 1000)
    n = len(muestras) // marco
    if n == 0:
        return {"has_sound": None, "choppy": None, "error": "captura demasiado corta"}
    rms = []
    for i in range(n):
        trozo = muestras[i * marco:(i + 1) * marco]
        rms.append((sum(v * v for v in trozo) / len(trozo)) ** 0.5)
    sonando = [r > UMBRAL_RMS for r in rms]
    frac = sum(sonando) / len(sonando)
    cortes = sum(1 for a, b in zip(sonando, sonando[1:], strict=False) if a and not b)
    hay = frac >= FRAC_MINIMA
    return {
        "tramos": len(rms),
        "has_sound": hay,
        "choppy": bool(hay and cortes >= CORTES_MAXIMOS),
        "rms_mediana": round(sorted(rms)[len(rms) // 2], 5),
        "sonando_pct": round(frac * 100, 1),
        "cortes": cortes,
    }


def escuchar(segundos: float = 15.0) -> dict[str, Any]:
    """Oír N segundos AHORA. Lo que suene en el sistema, suene lo que suene."""
    o = Oidos()
    if not o.empezar():
        return {"has_sound": None, "choppy": None,
                "error": f"oidos no disponibles: {motivo_no_disponible()}"}
    time.sleep(segundos)
    return o.parar()
