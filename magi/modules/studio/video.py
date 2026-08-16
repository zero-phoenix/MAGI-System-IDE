"""
Vídeo programático con FFmpeg (Plan MAGI 9.0 §5.5).

QUÉ ES ALCANZABLE Y QUÉ NO
==========================
El plan ya fue explícito y lo repito donde vive el código, porque es la parte
donde más se promete de más:

    Vídeo programático (FFmpeg, motion graphics, capturas)   ALTA    <- aquí
    Animática desde stills (Ken Burns, transiciones)         ALTA    <- aquí
    Interpolación y upscale (RIFE, Real-ESRGAN)              ALTA
    Gen-vídeo local (AnimateDiff, LTX, Wan)                  MEDIA
    Gen-vídeo de calidad (Veo, Sora, Kling)                  SOLO API, de pago

Los dos primeros dan resultados profesionales HOY y no cuestan nada. El
gen-vídeo largo y coherente no está resuelto localmente en hardware de
escritorio, y montar un módulo que lo finja sería el mismo error que el
`np.random.randint` presentado como índice de riesgo.

Así que esto hace lo que de verdad sale bien: montar imágenes en movimiento,
convertir páginas de manga en animática, grabar un programa en ejecución y —
sobre todo— MIRAR el resultado.

EL BUCLE DE OBSERVACIÓN, TAMBIÉN AQUÍ
=====================================
`artifacts.py` caza el juego que corre y no dibuja nada porque la pantalla es
de un solo color. El vídeo tiene dos fallos equivalentes y aún más fáciles de
no ver, porque el fichero existe, pesa megas y se reproduce:

  · Todo negro — se renderizó la nada durante treinta segundos.
  · Congelado — todos los fotogramas idénticos. La "animación" no animó.
    Es el fallo típico de un filtro mal escrito: FFmpeg no da error, produce
    un vídeo perfectamente válido de una foto fija.

`observe_video` muestrea fotogramas separados en el tiempo y los compara. Sin
eso, "vídeo generado, 12 MB, 30 s" es un informe que suena a éxito.

Y arregla un agujero real: `ArtifactKind.VIDEO` existía en el enum y el schema
de `observe_artifact` lo ofrecía, pero `observe()` no tenía rama para vídeo, así
que un .mp4 caía en `observe_program` y se INTENTABA EJECUTAR como Python. El
agente recibía "SyntaxError: source code cannot contain null bytes" al pedir
que se mirase el vídeo que acababa de hacer.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from .artifacts import ArtifactKind, Observation, _mirar_imagen, pillow_available

logger = logging.getLogger(__name__)

#: Un vídeo con menos de este porcentaje de píxeles distintos entre fotogramas
#: separados se considera congelado. No es cero porque la compresión con
#: pérdida mete ruido: dos fotogramas "idénticos" en H.264 difieren un poco.
FROZEN_THRESHOLD = 0.02


class VideoError(RuntimeError):
    """FFmpeg no está, o se negó a hacer lo que se le pidió."""


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def ffprobe_available() -> bool:
    return shutil.which("ffprobe") is not None


def backends_report() -> dict[str, bool]:
    """Qué se puede hacer con vídeo en esta máquina."""
    return {"ffmpeg": ffmpeg_available(), "ffprobe": ffprobe_available()}


async def _run(args: list[str], timeout: int = 300) -> tuple[int, str]:
    """
    Ejecuta FFmpeg sin shell.

    Sin shell a propósito: las rutas de los usuarios llevan espacios, comillas
    y acentos, y componer una cadena para `sh -c` con eso dentro es una fuente
    inagotable de fallos raros. Con lista de argumentos no hay nada que citar.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT)
    except FileNotFoundError as e:
        raise VideoError(f"{args[0]} no está instalado") from e
    # §7.3 — un render puede durar diez minutos. Sin inscribirlo, pulsar
    # parar decía "no había nada en marcha" con ffmpeg quemando CPU.
    from ...core.cancel import tracked
    async with tracked(proc):
        try:
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()      # sin esto queda un zombi
            raise VideoError(
                f"{args[0]} superó el tiempo límite de {timeout}s") from None
    return proc.returncode or 0, (out or b"").decode("utf-8", "replace")


# ------------------------------------------------------------------- inspección

@dataclass
class VideoInfo:
    path: str
    duration: float
    width: int
    height: int
    fps: float
    codec: str
    has_audio: bool
    size_bytes: int
    nb_frames: int = 0

    def render(self) -> str:
        mm, ss = divmod(self.duration, 60)
        return (f"{self.width}x{self.height} · {self.fps:.3g} fps · "
                f"{int(mm):02d}:{ss:05.2f} · {self.codec} · "
                f"{self.size_bytes / 1e6:.2f} MB · "
                f"{'con audio' if self.has_audio else 'sin audio'}")


async def probe(path: str | Path) -> VideoInfo:
    """Metadatos reales del fichero, leídos por ffprobe."""
    p = Path(path)
    if not p.exists():
        raise VideoError(f"{p} no existe")
    if not ffprobe_available():
        raise VideoError("ffprobe no está instalado: no se puede inspeccionar")

    rc, out = await _run([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(p)], timeout=60)
    if rc != 0:
        raise VideoError(f"ffprobe falló sobre {p.name}: {out.strip()[:200]}")
    try:
        data = json.loads(out)
    except json.JSONDecodeError as e:
        raise VideoError(f"ffprobe devolvió algo que no es JSON: {e}") from e

    streams = data.get("streams", [])
    vid = next((s for s in streams if s.get("codec_type") == "video"), None)
    if vid is None:
        raise VideoError(
            f"{p.name} no tiene pista de vídeo. ¿Es un fichero de audio, o "
            f"un contenedor vacío porque el filtro no produjo fotogramas?")

    # r_frame_rate viene como fracción: "30000/1001".
    fps = 0.0
    raw = str(vid.get("r_frame_rate", "0/1"))
    if "/" in raw:
        num, _, den = raw.partition("/")
        try:
            fps = float(num) / float(den) if float(den) else 0.0
        except ValueError:
            fps = 0.0

    fmt = data.get("format", {})
    return VideoInfo(
        path=str(p),
        duration=float(fmt.get("duration") or vid.get("duration") or 0.0),
        width=int(vid.get("width") or 0), height=int(vid.get("height") or 0),
        fps=fps, codec=str(vid.get("codec_name", "?")),
        has_audio=any(s.get("codec_type") == "audio" for s in streams),
        size_bytes=p.stat().st_size,
        nb_frames=int(vid.get("nb_frames") or 0))


async def extract_frames(path: str | Path, out_dir: str | Path,
                         count: int = 3) -> list[Path]:
    """
    Saca `count` fotogramas repartidos por la duración del vídeo.

    Repartidos, no los primeros: los primeros fotogramas de casi cualquier
    vídeo son parecidos entre sí, y compararlos no distingue una animación de
    una foto fija.
    """
    info = await probe(path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    dur = max(info.duration, 0.1)

    sacados: list[Path] = []
    for i in range(max(1, count)):
        # Se evitan los extremos: el último fotograma a veces no existe por
        # redondeo de duración y ffmpeg devolvería un fichero vacío.
        t = dur * (i + 0.5) / max(1, count)
        destino = out / f"frame_{i:02d}.png"
        rc, err = await _run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{t:.3f}", "-i", str(path),
            "-frames:v", "1", str(destino)], timeout=120)
        if rc == 0 and destino.exists() and destino.stat().st_size > 0:
            sacados.append(destino)
    if not sacados:
        raise VideoError(
            f"no se pudo extraer ningún fotograma de {Path(path).name}: el "
            f"contenedor puede estar corrupto o no tener fotogramas reales")
    return sacados


def _frames_differ(a: Path, b: Path) -> float:
    """
    Fracción de píxeles que cambian entre dos fotogramas, de 0 a 1.

    Se compara en escala de grises y con una tolerancia, porque la compresión
    con pérdida hace que dos fotogramas visualmente idénticos difieran en
    valores bajos. Sin la tolerancia, todo vídeo parecería animado.
    """
    try:
        from PIL import Image, ImageChops
    except ImportError:
        return -1.0
    try:
        with Image.open(a) as ia, Image.open(b) as ib:
            ga, gb = ia.convert("L"), ib.convert("L")
            if ga.size != gb.size:
                return 1.0
            diff = ImageChops.difference(ga, gb)
            total = diff.width * diff.height
            if not total:
                return 0.0
            # Píxeles que cambian más de 12/255: por encima del ruido de códec.
            cambiados = sum(n for v, n in enumerate(diff.histogram()) if v > 12)
            return cambiados / total
    except Exception as e:                        # pragma: no cover
        logger.debug("[video] no se pudieron comparar fotogramas: %s", e)
        return -1.0


async def observe_video(path: str | Path) -> Observation:
    """
    Mira el vídeo de verdad: metadatos, un fotograma y si algo se mueve.

    Es el equivalente para vídeo del bucle de observación de §5. Un fichero de
    12 MB que existe y se abre NO es prueba de que se haya generado nada: el
    modo de fallo caro es el vídeo válido cuyo contenido está en negro o
    congelado, porque pasa todas las comprobaciones baratas.
    """
    p = Path(path)
    if not p.exists():
        return Observation(False, ArtifactKind.VIDEO, "no existe",
                           problems=[f"{p} no existe"])
    if not ffprobe_available():
        return Observation(
            False, ArtifactKind.VIDEO, "sin ffprobe", artifact_path=str(p),
            problems=["ffprobe no está instalado: el vídeo no se puede "
                      "inspeccionar. Instala ffmpeg para cerrar el bucle de "
                      "observación."])

    try:
        info = await probe(p)
    except VideoError as e:
        return Observation(False, ArtifactKind.VIDEO, "ilegible",
                           artifact_path=str(p), problems=[str(e)])

    problemas: list[str] = []
    evidencia: list[str] = [info.render()]

    if info.duration < 0.05:
        problemas.append(
            f"dura {info.duration:.3f}s: el contenedor existe pero está "
            f"prácticamente vacío. Suele significar que el filtro no produjo "
            f"fotogramas.")
    if info.width == 0 or info.height == 0:
        problemas.append("dimensiones nulas: no hay imagen real")

    captura: str | None = None
    # Los fotogramas van a la caché con nombre determinista, NO a un
    # directorio temporal: la captura tiene que sobrevivir a esta función para
    # que el agente pueda mirarla, y un `mkdtemp` que no se puede borrar
    # porque su contenido sigue en uso es una fuga garantizada. Con ruta
    # determinista, observar dos veces el mismo vídeo reescribe en lugar de
    # acumular.
    #
    # El nombre lleva un hash de la RUTA ABSOLUTA, no solo el `stem`. Con solo
    # el stem, dos artefactos llamados igual —y `salida.mp4` es un nombre de
    # salida habitual— compartían carpeta: el `rmtree` de la segunda borraba
    # los fotogramas de la primera y ambas observaciones acababan apuntando a
    # la misma captura. Un vídeo congelado salía aprobado con la evidencia de
    # movimiento de OTRO fichero. Cambiaba una fuga por una corrupción.
    from ...core.paths import cache_dir
    huella = hashlib.sha1(str(p.resolve()).encode("utf-8")).hexdigest()[:10]
    destino = cache_dir() / "video_frames" / f"{p.stem}-{huella}"
    shutil.rmtree(destino, ignore_errors=True)
    try:
        frames = await extract_frames(p, destino, count=3)
        captura = str(frames[0])

        # EL FALLO QUE ESTO CIERRA: sin Pillow no se puede abrir un fotograma,
        # así que ni el negro ni el congelado se detectaban — y el aviso se
        # dejaba en `evidencia`, que no entra en `ok`. Resultado: un vídeo
        # enteramente negro y congelado salía con ok=True y cero problemas.
        # Justo el modo de fallo que esta función existe para cazar. Lo
        # encontró simular el entorno de CI, donde Pillow no está instalado.
        if not pillow_available():
            problemas.append(
                "Pillow no instalado: los fotogramas NO se han mirado. No se "
                "ha comprobado si el vídeo está en negro ni si está "
                "congelado. `pip install pillow` para cerrar el bucle.")
            return Observation(
                False, ArtifactKind.VIDEO, "sin Pillow: contenido sin mirar",
                evidence=evidencia, artifact_path=str(p), screenshot=captura,
                problems=problemas)

        desc, malos = _mirar_imagen(
            frames[0],
            vacia="el fotograma es de un solo color: el vídeo se generó pero "
                  "no hay nada dibujado. Revisa que la fuente no esté en negro "
                  "y que el filtro reciba las imágenes que crees.")
        evidencia.append(f"fotograma central: {desc}")
        problemas.extend(malos)

        if len(frames) < 2:
            # Sin `else` esta rama se saltaba en silencio. Pasa de verdad: si
            # la duración del contenedor supera la de la pista de vídeo (audio
            # más largo, muxeado sin `-shortest`), los `-ss` repartidos sobre
            # `info.duration` caen más allá del final y solo sale un
            # fotograma. Con un solo fotograma no hay con qué comparar, y NO
            # comparar no es «no está congelado».
            problemas.append(
                f"solo se pudo extraer {len(frames)} fotograma: sin dos no hay "
                f"con qué comparar, así que el congelado NO queda descartado. "
                f"Suele pasar cuando la pista de vídeo es más corta que el "
                f"contenedor.")
        else:
            cambios = [_frames_differ(frames[i], frames[i + 1])
                       for i in range(len(frames) - 1)]
            medidos = [c for c in cambios if c >= 0]
            if medidos:
                mayor = max(medidos)
                evidencia.append(
                    f"movimiento entre fotogramas: {mayor:.1%} de píxeles "
                    f"cambian")
                if mayor < FROZEN_THRESHOLD:
                    problemas.append(
                        f"CONGELADO: solo cambia el {mayor:.1%} de los píxeles "
                        f"entre fotogramas separados en el tiempo. El vídeo es "
                        f"válido pero no anima nada — es una foto fija de "
                        f"{info.duration:.1f}s.")
            else:
                # Pillow está (se comprobó arriba), así que llegar aquí
                # significa que la comparación reventó. No medir el movimiento
                # no es «sin novedad»: es congelado NO descartado.
                problemas.append(
                    "no se pudieron comparar los fotogramas: el congelado NO "
                    "queda descartado, solo sin comprobar.")
    except VideoError as e:
        problemas.append(str(e))

    return Observation(
        not problemas, ArtifactKind.VIDEO,
        f"vídeo inspeccionado: {info.render()}",
        evidence=evidencia, artifact_path=str(p), screenshot=captura,
        problems=problemas)


# ---------------------------------------------------------------- generación

@dataclass
class Slide:
    """Una imagen con su tiempo en pantalla y su texto opcional."""
    image: str
    seconds: float = 3.0
    caption: str = ""


@dataclass
class VideoSpec:
    """
    Qué vídeo se quiere. Se valida ANTES de llamar a FFmpeg.

    Mismo criterio que `PageSpec` en manga.py: los errores de composición se
    cazan con aritmética barata, no esperando a que un proceso de dos minutos
    devuelva un mensaje de FFmpeg que nadie sabe leer.
    """
    slides: list[Slide] = field(default_factory=list)
    width: int = 1920
    height: int = 1080
    fps: int = 30
    ken_burns: bool = True
    crossfade: float = 0.5
    audio: str = ""

    @property
    def duration(self) -> float:
        return sum(s.seconds for s in self.slides)

    def validate(self) -> list[str]:
        errores: list[str] = []
        if not self.slides:
            errores.append("no hay imágenes: un vídeo de cero diapositivas no "
                           "es un vídeo")
        for i, s in enumerate(self.slides):
            if not Path(s.image).exists():
                errores.append(f"diapositiva {i}: no existe {s.image}")
            if s.seconds <= 0:
                errores.append(f"diapositiva {i}: duración {s.seconds}s")
            elif s.seconds <= self.crossfade and self.crossfade > 0:
                errores.append(
                    f"diapositiva {i}: dura {s.seconds}s y la transición "
                    f"{self.crossfade}s. Una transición más larga que la "
                    f"diapositiva la consume entera y el resultado parpadea")
        if self.width % 2 or self.height % 2:
            errores.append(
                f"{self.width}x{self.height}: H.264 con yuv420p exige "
                f"dimensiones PARES. FFmpeg fallaría con un error de "
                f"escalado que no dice esto")
        if self.fps < 1:
            errores.append(f"fps {self.fps}: debe ser al menos 1")
        return errores


#: Cuánto se acerca el zoom a lo largo de una diapositiva. Por encima de ~1.3
#: el recorte se come el encuadre y se nota el pixelado del sobremuestreo.
KEN_BURNS_ZOOM = 0.25


def _ken_burns_filter(spec: VideoSpec, idx: int, slide: Slide) -> str:
    """
    Zoom lento con `zoompan`, el efecto que hace mirable una foto fija.

    DOS TRAMPAS DE ZOOMPAN, LAS DOS COMPROBADAS CONTRA FFMPEG
    ---------------------------------------------------------
    1. `d=N` emite N fotogramas POR CADA fotograma de entrada. Con la entrada
       en bucle (`-loop 1 -t 2`, que son 48 fotogramas a 24 fps) el resultado
       eran 48x48 = 2304 fotogramas: una diapositiva de 2 segundos salía de
       100. Y FFmpeg no se queja — produce un vídeo perfectamente válido de la
       duración equivocada. Se usa `d=1`, un fotograma de salida por cada uno
       de entrada, y la duración la fija el `-t` de la entrada.

    2. Con `d=1` la forma `z='zoom+0.0008'` no sirve: `zoom` se reinicia en
       cada fotograma y el zoom no avanza. Se expresa en función de `on` —el
       número de fotograma de salida—, que además hace el movimiento lineal y
       predecible en lugar de depender de una acumulación.

    Lo de escalar antes al doble no es adorno: `zoompan` recorta sobre el
    fotograma de entrada, y sin sobremuestreo el zoom se ve pixelado y a
    saltos. Es lo que hace que una animática casera parezca casera.
    """
    frames = max(1, int(slide.seconds * spec.fps))
    w, h = spec.width, spec.height
    escala = f"scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase"
    recorte = f"crop={w * 2}:{h * 2}"

    if not spec.ken_burns:
        return (f"[{idx}:v]fps={spec.fps},{escala},{recorte},scale={w}:{h},"
                f"setsar=1[v{idx}]")

    # Alterna acercar y alejar: el mismo movimiento en todas las diapositivas
    # se nota más que el propio efecto.
    if idx % 2 == 0:
        z = f"1+{KEN_BURNS_ZOOM}*on/{frames}"
    else:
        z = f"{1 + KEN_BURNS_ZOOM}-{KEN_BURNS_ZOOM}*on/{frames}"
    return (f"[{idx}:v]fps={spec.fps},{escala},{recorte},"
            f"zoompan=z='{z}':d=1:s={w}x{h}:fps={spec.fps}"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',"
            f"setsar=1[v{idx}]")


def build_filtergraph(spec: VideoSpec) -> str:
    """
    Construye el grafo de filtros. Separado de la ejecución A PROPÓSITO.

    Un filtergraph de FFmpeg es un lenguaje, y como todo lenguaje se puede
    escribir mal. Teniéndolo como función pura se puede comprobar en un test
    sin arrancar FFmpeg ni esperar dos minutos, que es la diferencia entre
    tener tests de esto y no tenerlos.
    """
    partes = [_ken_burns_filter(spec, i, s) for i, s in enumerate(spec.slides)]
    n = len(spec.slides)
    if n == 1:
        partes.append("[v0]null[vout]")
        return ";".join(partes)

    if spec.crossfade <= 0:
        entradas = "".join(f"[v{i}]" for i in range(n))
        partes.append(f"{entradas}concat=n={n}:v=1:a=0[vout]")
        return ";".join(partes)

    # xfade encadenado. El desplazamiento se acumula restando la transición ya
    # consumida; calcularlo mal es el fallo clásico y produce un vídeo que se
    # queda congelado al final.
    anterior, desplazamiento = "[v0]", 0.0
    for i in range(1, n):
        desplazamiento += spec.slides[i - 1].seconds - spec.crossfade
        etiqueta = "[vout]" if i == n - 1 else f"[x{i}]"
        partes.append(
            f"{anterior}[v{i}]xfade=transition=fade:"
            f"duration={spec.crossfade}:offset={desplazamiento:.3f}{etiqueta}")
        anterior = etiqueta
    return ";".join(partes)


async def render_slideshow(spec: VideoSpec, out_path: str | Path,
                           timeout: int = 600) -> Observation:
    """
    Monta la animática y DESPUÉS la mira. Las dos cosas, siempre.

    Devolver `Observation` en lugar de la ruta no es capricho: obliga a que el
    resultado pase por la inspección. Una función que devuelve la ruta invita a
    dar por bueno el fichero porque existe.
    """
    if not ffmpeg_available():
        return Observation(False, ArtifactKind.VIDEO, "sin ffmpeg",
                           problems=["ffmpeg no está instalado; sin él no hay "
                                     "vídeo programático. `apt install ffmpeg`"])
    errores = spec.validate()
    if errores:
        return Observation(False, ArtifactKind.VIDEO,
                           "composición inválida", problems=errores)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    for s in spec.slides:
        args += ["-loop", "1", "-t", str(s.seconds), "-i", str(Path(s.image))]
    if spec.audio:
        args += ["-i", str(Path(spec.audio))]

    args += ["-filter_complex", build_filtergraph(spec), "-map", "[vout]"]
    if spec.audio:
        args += ["-map", f"{len(spec.slides)}:a", "-c:a", "aac", "-shortest"]
    args += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(spec.fps),
             "-movflags", "+faststart", str(out)]

    rc, salida = await _run(args, timeout=timeout)
    if rc != 0 or not out.exists():
        return Observation(
            False, ArtifactKind.VIDEO, "ffmpeg falló", artifact_path=str(out),
            problems=[f"ffmpeg terminó con código {rc}",
                      salida.strip()[-600:] or "sin salida de error"])
    return await observe_video(out)


async def manga_to_video(pages: list[str | Path], out_path: str | Path,
                         seconds_per_page: float = 5.0,
                         audio: str = "", **kw) -> Observation:
    """
    Páginas de manga -> animática (§5.5: "manga → vídeo sale casi gratis").

    Compone con `manga.py`: lo que sale del compositor entra aquí sin pasos
    intermedios. El formato es vertical (1080x1920) porque una página de manga
    es más alta que ancha y meterla en 16:9 la deja con dos franjas negras
    ocupando la mitad de la pantalla.
    """
    faltan = [str(p) for p in pages if not Path(p).exists()]
    if faltan:
        return Observation(False, ArtifactKind.VIDEO, "faltan páginas",
                           problems=[f"no existe: {f}" for f in faltan])
    spec = VideoSpec(
        slides=[Slide(str(p), seconds_per_page) for p in pages],
        width=kw.pop("width", 1080), height=kw.pop("height", 1920),
        audio=audio, **kw)
    return await render_slideshow(spec, out_path)


#: Arnés de GRABACIÓN. El de `artifacts.py` guarda UN fotograma al llegar al
#: número N; este guarda una secuencia numerada para poder montarla en vídeo.
#: Son dos cosas distintas y por eso son dos arneses: intentar que el primero
#: hiciera las dos habría metido un parámetro que solo usa la mitad de las
#: llamadas, y ese es el camino a que ninguna de las dos funcione bien.
RECORD_HARNESS = '''"""Arnés de grabación generado por MAGI (§5.5)."""
import os, importlib.util
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

FRAMES = int(os.environ.get("MAGI_FRAMES", "120"))
EVERY = max(1, int(os.environ.get("MAGI_EVERY", "1")))
OUT = os.environ.get("MAGI_OUT", ".")
TARGET = os.environ.get("MAGI_TARGET", "main.py")

pygame.init()
_orig_flip, _orig_update = pygame.display.flip, pygame.display.update
state = {"frames": 0, "saved": 0}


def _cuenta():
    state["frames"] += 1
    if state["frames"] % EVERY == 0:
        surf = pygame.display.get_surface()
        if surf is not None:
            pygame.image.save(surf, os.path.join(
                OUT, "shot_%05d.png" % state["saved"]))
            state["saved"] += 1
    if state["frames"] >= FRAMES:
        pygame.quit()
        raise SystemExit(0)


def _flip(*a, **kw):
    _cuenta()
    return _orig_flip(*a, **kw)


def _update(*a, **kw):
    # flip() no acepta argumentos y update(rect) sí: aliasarlos al mismo
    # envoltorio rompe todo juego con dirty rects.
    _cuenta()
    return _orig_update(*a, **kw)


pygame.display.flip = _flip
pygame.display.update = _update

spec = importlib.util.spec_from_file_location("__main__", TARGET)
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except SystemExit:
    pass
finally:
    print("MAGI_FRAMES_RENDERED=%d" % state["frames"])
    print("MAGI_FRAMES_SAVED=%d" % state["saved"])
'''


async def capture_program(path: str | Path, out_path: str | Path,
                          seconds: float = 6.0, fps: int = 20,
                          entry: str = "main.py",
                          timeout: int = 120) -> Observation:
    """
    Graba un programa gráfico en ejecución y devuelve el vídeo.

    Ver treinta fotogramas de un juego dice cosas que una captura suelta no
    puede: si se mueve, si parpadea, si se congela a los dos segundos. Ese
    último caso es justamente el que una sola captura declara correcto.
    """
    from ...core.paths import python_executable
    from .artifacts import _SIN_PYTHON

    interprete = python_executable()
    if interprete is None:
        return Observation(False, ArtifactKind.VIDEO,
                           "sin intérprete de Python", problems=[_SIN_PYTHON])

    if not ffmpeg_available():
        return Observation(False, ArtifactKind.VIDEO, "sin ffmpeg",
                           problems=["ffmpeg no está instalado"])
    d = Path(path)
    objetivo = d / entry
    if not objetivo.exists():
        return Observation(False, ArtifactKind.VIDEO, "sin punto de entrada",
                           problems=[f"no existe {objetivo}"])
    try:
        import pygame  # noqa: F401
    except ImportError:
        return Observation(False, ArtifactKind.VIDEO, "pygame no instalado",
                           problems=["pip install pygame para poder grabar"])

    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="magi_rec_"))
    # El `finally` que envuelve TODO el cuerpo, no solo la llamada a ffmpeg.
    # Antes, `tmp` se borraba en las dos salidas normales; cancelar durante la
    # grabación —justo lo que el botón de parada de §7.3 existe para hacer—
    # dejaba el directorio entero con sus cientos de PNG. Cancelar no es un
    # camino excepcional en este sistema: es una función.
    try:
        arnes = d / "_magi_record.py"
        arnes.write_text(RECORD_HARNESS, encoding="utf-8")
        try:
            from .artifacts import _run as _run_shell
            rc, salida = await _run_shell(
                f'"{interprete}" "{arnes.name}"', d, timeout,
                {"MAGI_FRAMES": str(max(2, int(seconds * fps))),
                 "MAGI_EVERY": "1", "MAGI_OUT": str(tmp),
                 "MAGI_TARGET": str(objetivo),
                 "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"})
        finally:
            arnes.unlink(missing_ok=True)

        disparos = sorted(tmp.glob("shot_*.png"))
        if not disparos:
            cola = "\n".join(salida.strip().splitlines()[-6:])
            return Observation(
                False, ArtifactKind.VIDEO, "sin fotogramas que grabar",
                artifact_path=str(d),
                problems=["el programa no dibujó ningún fotograma: no es "
                          "gráfico, no llama a display.flip(), o falló antes "
                          "de dibujar",
                          f"código {rc}" + (f":\n{cola}" if cola else "")])

        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            rc2, err = await _run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-framerate", str(fps),
                "-i", str(tmp / "shot_%05d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                # H.264 con yuv420p exige dimensiones pares y las ventanas de
                # juego rara vez lo son.
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                str(out)], timeout=300)
        except VideoError as e:
            # Todas las demás salidas de esta función devuelven Observation;
            # un timeout de ffmpeg escapaba como excepción y el llamador se
            # encontraba con dos contratos distintos según por dónde fallara.
            return Observation(False, ArtifactKind.VIDEO, "ffmpeg falló",
                               problems=[str(e)])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if rc2 != 0 or not out.exists():
        return Observation(False, ArtifactKind.VIDEO, "ffmpeg falló",
                           problems=[f"código {rc2}", err.strip()[-400:]])
    obs = await observe_video(out)
    obs.evidence.insert(0, f"{len(disparos)} fotogramas grabados del programa")
    return obs
