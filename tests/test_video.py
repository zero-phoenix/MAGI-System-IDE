"""
Vídeo programático y su bucle de observación (§5.5).

Dos clases de test, a propósito:

  · El filtergraph es una FUNCIÓN PURA y se comprueba sin arrancar FFmpeg.
    Un filtergraph es un lenguaje y se puede escribir mal; tenerlo separado de
    la ejecución es lo que permite tener tests de esto en vez de no tenerlos.
  · Lo que solo se puede saber ejecutando —duraciones reales, detección de
    vídeo congelado— se ejecuta de verdad, con FFmpeg, y se salta si no está.
    Es la cuarta regla del proyecto: arrancar encuentra fallos que leer no.
"""
import shutil
import subprocess

import pytest

from magi.core.tools import ToolContext, WriteJournal, build_registry
from magi.modules.studio.artifacts import VIDEO_EXTS, ArtifactKind, observe
from magi.modules.studio.video import (
    FROZEN_THRESHOLD, Slide, VideoError, VideoSpec, backends_report,
    build_filtergraph, capture_program, ffmpeg_available, manga_to_video,
    observe_video, probe, render_slideshow,
)

sin_ffmpeg = pytest.mark.skipif(not ffmpeg_available(),
                                reason="ffmpeg no instalado")


def _lavfi(path, fuente, dur=3, size="320x240", rate=10):
    # La primera opción de una fuente lavfi se separa con '=', las siguientes
    # con ':'. Componerlo siempre con ':' da 'testsrc:size=...' y ffmpeg lo
    # rechaza con "No option name near" — aunque 'color=c=black:size=...' sí
    # funciona, que es por qué el error solo salía en la mitad de los tests.
    sep = ":" if "=" in fuente else "="
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
         "-i", f"{fuente}{sep}size={size}:rate={rate}:duration={dur}",
         "-pix_fmt", "yuv420p", str(path)], check=True)
    return path


@pytest.fixture
def imagenes(tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image
    salida = []
    for i, c in enumerate([(200, 40, 40), (40, 160, 80), (40, 80, 200)]):
        p = tmp_path / f"pag{i}.png"
        im = Image.new("RGB", (800, 600), c)
        for x in range(0, 800, 40):          # damero: da textura que medir
            for y in range(0, 600, 40):
                if (x // 40 + y // 40 + i) % 2 == 0:
                    im.paste((255, 255, 255), (x, y, x + 20, y + 20))
        im.save(p)
        salida.append(str(p))
    return salida


# --------------------------------------------------- validación sin ejecutar

def test_rechaza_dimensiones_impares():
    """
    H.264 con yuv420p exige dimensiones pares. Sin esta guarda, FFmpeg falla
    con un error de escalado que no menciona la paridad y cuesta media hora.
    """
    errores = VideoSpec(slides=[Slide("x.png")], width=1921, height=1080).validate()
    assert any("PARES" in e for e in errores)


def test_rechaza_transicion_mas_larga_que_la_diapositiva():
    errores = VideoSpec(slides=[Slide("x.png", 0.3)], crossfade=0.5).validate()
    assert any("parpadea" in e for e in errores)


def test_rechaza_vídeo_sin_diapositivas():
    assert any("cero diapositivas" in e for e in VideoSpec().validate())


def test_avisa_de_imagenes_que_no_existen(tmp_path):
    errores = VideoSpec(slides=[Slide(str(tmp_path / "fantasma.png"))]).validate()
    assert any("no existe" in e for e in errores)


# ------------------------------------------------------ filtergraph puro

def test_zoompan_usa_d_igual_a_1():
    """
    LA REGRESIÓN DE §5.5. `d=N` emite N fotogramas POR CADA fotograma de
    entrada; con la entrada en bucle salían 48x48 y una diapositiva de 2
    segundos duraba 100. FFmpeg no protesta: produce un vídeo válido de la
    duración equivocada.
    """
    fg = build_filtergraph(VideoSpec(slides=[Slide("a.png", 2.0)], fps=24))
    assert "zoompan" in fg
    assert ":d=1:" in fg, f"zoompan debe llevar d=1: {fg}"
    assert ":d=48:" not in fg


def test_el_zoom_avanza_por_numero_de_fotograma():
    """Con d=1, `zoom+0.0008` se reinicia cada fotograma y no avanza nada."""
    fg = build_filtergraph(VideoSpec(slides=[Slide("a.png", 2.0)], fps=24))
    assert "on/" in fg, "el zoom debe expresarse en función de `on`"
    assert "zoom+" not in fg


def test_alterna_el_sentido_del_zoom():
    """El mismo movimiento en todas las diapositivas se nota más que el efecto."""
    fg = build_filtergraph(
        VideoSpec(slides=[Slide("a.png", 2.0), Slide("b.png", 2.0)], fps=24))
    zooms = [t for t in fg.split(";") if "zoompan" in t]
    assert len(zooms) == 2
    assert zooms[0] != zooms[1]


def test_los_desplazamientos_del_xfade_se_acumulan():
    """
    Calcular mal el offset de xfade es el fallo clásico: el vídeo se queda
    congelado al final en lugar de encadenar.
    """
    spec = VideoSpec(slides=[Slide(f"{i}.png", 4.0) for i in range(3)],
                     crossfade=1.0)
    fg = build_filtergraph(spec)
    assert "offset=3.000" in fg      # 4 - 1
    assert "offset=6.000" in fg      # (4-1) + (4-1)
    assert fg.endswith("[vout]")


def test_sin_transicion_se_concatena():
    fg = build_filtergraph(
        VideoSpec(slides=[Slide("a.png"), Slide("b.png")], crossfade=0.0))
    assert "concat=n=2" in fg and "xfade" not in fg


def test_una_sola_diapositiva_no_intenta_encadenar():
    fg = build_filtergraph(VideoSpec(slides=[Slide("a.png")]))
    assert "xfade" not in fg and "concat" not in fg
    assert fg.endswith("[vout]")


def test_sin_ken_burns_no_hay_zoompan():
    fg = build_filtergraph(
        VideoSpec(slides=[Slide("a.png")], ken_burns=False))
    assert "zoompan" not in fg


# ------------------------------------------ el agujero de ArtifactKind.VIDEO

@pytest.mark.asyncio
@sin_ffmpeg
async def test_un_mp4_ya_no_se_ejecuta_como_python(tmp_path):
    """
    EL AGUJERO. `ArtifactKind.VIDEO` estaba en el enum y el schema de
    `observe_artifact` ofrecía "video", pero `observe()` no tenía rama: el
    .mp4 caía en `observe_program` y se INTENTABA EJECUTAR. El agente que
    pedía mirar su vídeo recibía "SyntaxError: source code cannot contain
    null bytes".
    """
    v = _lavfi(tmp_path / "d.mp4", "testsrc")
    por_extension = await observe(v)
    explicito = await observe(v, "video")
    for o in (por_extension, explicito):
        assert o.kind is ArtifactKind.VIDEO, f"despachado a {o.kind}"
        assert "SyntaxError" not in o.render()
        assert o.ok


def test_todas_las_extensiones_de_video_se_reconocen():
    assert ".mp4" in VIDEO_EXTS and ".webm" in VIDEO_EXTS and ".gif" in VIDEO_EXTS


# ------------------------------------------------- bucle de observación real

@pytest.mark.asyncio
@sin_ffmpeg
async def test_detecta_el_video_en_negro(tmp_path):
    v = _lavfi(tmp_path / "negro.mp4", "color=c=black")
    o = await observe_video(v)
    assert not o.ok
    assert any("un solo color" in p for p in o.problems)


@pytest.mark.asyncio
@sin_ffmpeg
async def test_detecta_el_video_congelado(tmp_path):
    """
    El fallo caro: el fichero existe, pesa, se reproduce y es una foto fija.
    Pasa todas las comprobaciones baratas.
    """
    v = _lavfi(tmp_path / "fijo.mp4", "color=c=red")
    o = await observe_video(v)
    assert not o.ok
    assert any("CONGELADO" in p for p in o.problems)


@pytest.mark.asyncio
@sin_ffmpeg
async def test_un_video_que_si_anima_pasa(tmp_path):
    """Contraprueba: sin esto, un detector que dijera 'congelado' a todo pasaría."""
    v = _lavfi(tmp_path / "vivo.mp4", "testsrc")
    o = await observe_video(v)
    assert o.ok, o.problems
    assert not o.problems
    assert any("movimiento" in e for e in o.evidence)
    assert o.screenshot


@pytest.mark.asyncio
@sin_ffmpeg
async def test_probe_lee_los_metadatos_de_verdad(tmp_path):
    v = _lavfi(tmp_path / "m.mp4", "testsrc", dur=2, size="640x480", rate=25)
    info = await probe(v)
    assert (info.width, info.height) == (640, 480)
    assert info.fps == pytest.approx(25, abs=0.1)
    assert info.duration == pytest.approx(2.0, abs=0.2)
    assert not info.has_audio
    assert "640x480" in info.render()


@pytest.mark.asyncio
async def test_observar_un_video_inexistente_no_revienta(tmp_path):
    o = await observe_video(tmp_path / "no_existe.mp4")
    assert not o.ok and "no existe" in o.problems[0]


@pytest.mark.asyncio
@sin_ffmpeg
async def test_un_fichero_que_no_es_video_se_explica(tmp_path):
    falso = tmp_path / "falso.mp4"
    falso.write_text("esto no es un vídeo", encoding="utf-8")
    o = await observe_video(falso)
    assert not o.ok
    assert o.problems


# ------------------------------------------------------------- renderizado

@pytest.mark.asyncio
@sin_ffmpeg
async def test_la_duracion_del_resultado_es_la_pedida(tmp_path, imagenes):
    """
    El test que habría cazado el fallo de zoompan en el momento. Tres
    diapositivas de 2s con transiciones de 0,5s son 6 - 2x0,5 = 5 segundos.
    Salían 103.
    """
    spec = VideoSpec(slides=[Slide(i, 2.0) for i in imagenes],
                     width=320, height=240, fps=15, crossfade=0.5)
    out = tmp_path / "a.mp4"
    obs = await render_slideshow(spec, out)
    assert obs.ok, obs.problems
    info = await probe(out)
    assert info.duration == pytest.approx(5.0, abs=0.35), \
        f"duración {info.duration}s, esperada 5.0"


@pytest.mark.asyncio
@sin_ffmpeg
async def test_sin_transicion_la_duracion_es_la_suma(tmp_path, imagenes):
    spec = VideoSpec(slides=[Slide(i, 1.0) for i in imagenes],
                     width=320, height=240, fps=15, crossfade=0.0)
    out = tmp_path / "b.mp4"
    assert (await render_slideshow(spec, out)).ok
    assert (await probe(out)).duration == pytest.approx(3.0, abs=0.35)


@pytest.mark.asyncio
@sin_ffmpeg
async def test_la_animatica_se_inspecciona_sola(tmp_path, imagenes):
    """
    `render_slideshow` devuelve Observation y no una ruta a propósito: obliga
    a que el resultado pase por la inspección en lugar de darlo por bueno
    porque el fichero existe.
    """
    spec = VideoSpec(slides=[Slide(i, 1.0) for i in imagenes],
                     width=320, height=240, fps=15)
    obs = await render_slideshow(spec, tmp_path / "c.mp4")
    assert obs.kind is ArtifactKind.VIDEO
    movimiento = [e for e in obs.evidence if "movimiento" in e]
    assert movimiento, "la animática no midió si se mueve"
    pct = float(movimiento[0].split()[3].rstrip("%")) / 100
    assert pct > FROZEN_THRESHOLD, "una animática Ken Burns tiene que moverse"


@pytest.mark.asyncio
@sin_ffmpeg
async def test_manga_a_video_sale_vertical(tmp_path, imagenes):
    """
    Una página de manga es más alta que ancha: en 16:9 quedaría con dos
    franjas negras ocupando media pantalla.
    """
    obs = await manga_to_video(imagenes, tmp_path / "m.mp4",
                               seconds_per_page=1.0)
    assert obs.ok, obs.problems
    info = await probe(tmp_path / "m.mp4")
    assert info.height > info.width


@pytest.mark.asyncio
async def test_manga_avisa_de_paginas_que_faltan(tmp_path):
    obs = await manga_to_video([tmp_path / "no_esta.png"], tmp_path / "x.mp4")
    assert not obs.ok and "no existe" in obs.problems[0]


@pytest.mark.asyncio
@sin_ffmpeg
async def test_grabar_algo_que_no_dibuja_lo_dice(tmp_path):
    """No debe devolver un vídeo vacío fingiendo que grabó algo."""
    pytest.importorskip("pygame")
    (tmp_path / "main.py").write_text("print('sin gráficos')", encoding="utf-8")
    obs = await capture_program(tmp_path, tmp_path / "v.mp4", seconds=1)
    assert not obs.ok
    assert any("fotograma" in p for p in obs.problems)


@pytest.mark.asyncio
async def test_grabar_sin_punto_de_entrada_lo_dice(tmp_path):
    obs = await capture_program(tmp_path, tmp_path / "v.mp4")
    assert not obs.ok and "no existe" in obs.problems[0]


def test_backends_report_dice_la_verdad():
    r = backends_report()
    assert r["ffmpeg"] == (shutil.which("ffmpeg") is not None)
    assert "ffprobe" in r


@pytest.mark.asyncio
async def test_probe_de_algo_que_no_existe_lanza(tmp_path):
    with pytest.raises(VideoError, match="no existe"):
        await probe(tmp_path / "nada.mp4")


# ---------------------------------------------------------------- cableado

def test_las_herramientas_de_video_estan_en_el_catalogo():
    nombres = set(build_registry().names())
    for t in ("render_animatic", "record_program"):
        assert t in nombres, f"{t} no está conectada al enjambre"


@pytest.mark.asyncio
@sin_ffmpeg
async def test_render_animatic_extremo_a_extremo(tmp_path, imagenes):
    ctx = ToolContext(task_id="t", cwd=tmp_path,
                      journal=WriteJournal("t", tmp_path / ".j"))
    r = await build_registry().execute("render_animatic", {
        "images": imagenes, "out_path": "salida.mp4", "seconds_each": 1.0,
        "width": 320, "height": 240, "fps": 15}, ctx)
    assert r.ok, r.error
    assert (tmp_path / "salida.mp4").exists()
    assert "movimiento" in r.content


@pytest.mark.asyncio
async def test_render_animatic_valida_antes_de_gastar_dos_minutos(tmp_path):
    ctx = ToolContext(task_id="t", cwd=tmp_path,
                      journal=WriteJournal("t", tmp_path / ".j"))
    r = await build_registry().execute("render_animatic", {
        "images": ["fantasma.png"], "out_path": "s.mp4"}, ctx)
    assert not r.ok and "no existe" in r.error


# ------------------------------------------------- la otra rama que faltaba

@pytest.mark.asyncio
async def test_un_csv_ya_no_se_ejecuta_como_python(tmp_path):
    """
    `ArtifactKind.DATA` tenía el mismo agujero que VIDEO: en el enum, ofrecido
    por el schema, y sin rama en observe(). Lo encontró el test que recorre el
    enum entero, no uno escrito para este caso — que es la diferencia entre
    una guarda y una anécdota.
    """
    from magi.modules.studio.artifacts import observe_data
    csv = tmp_path / "d.csv"
    csv.write_text("a,b,c\n1,2,3\n4,5,6\n", encoding="utf-8")
    o = await observe(csv)
    assert o.kind is ArtifactKind.DATA
    assert o.ok and "2 registros" in o.summary
    assert any("3 columnas" in e for e in o.evidence)
    assert (await observe(csv, "datos")).kind is ArtifactKind.DATA
    assert (await observe_data(csv)).ok


@pytest.mark.asyncio
async def test_detecta_el_csv_con_cabecera_y_cero_filas(tmp_path):
    """El fallo que más fácil pasa por bueno: el fichero se abre sin errores."""
    csv = tmp_path / "vacio.csv"
    csv.write_text("nombre,valor\n", encoding="utf-8")
    o = await observe(csv)
    assert not o.ok
    assert any("cero filas" in p for p in o.problems)


@pytest.mark.asyncio
async def test_json_y_jsonl_se_cuentan(tmp_path):
    j = tmp_path / "a.json"
    j.write_text('[{"x":1},{"x":2},{"x":3}]', encoding="utf-8")
    assert "3 registros" in (await observe(j)).summary

    jl = tmp_path / "b.jsonl"
    jl.write_text('{"x":1}\n{"x":2}\n', encoding="utf-8")
    assert "2 registros" in (await observe(jl)).summary


@pytest.mark.asyncio
async def test_json_corrupto_se_explica_no_revienta(tmp_path):
    j = tmp_path / "roto.json"
    j.write_text("{no soy json", encoding="utf-8")
    o = await observe(j)
    assert not o.ok and "no se pudo leer" in o.problems[0]


def test_studio_backends_devuelve_texto_no_un_dict():
    """
    Regresión propia: al añadir vídeo cambié `studio_backends` para fusionar
    dos informes con `{**a, **b}` dando por hecho que ambos eran dicts.
    `artifacts.backends_report()` devuelve TEXTO, así que la herramienta
    empezó a fallar con "'str' object is not a mapping" — y solo se vio al
    arrancar el kernel y llamarla, porque ningún test la ejecutaba.
    """
    from magi.modules.studio.artifacts import available_backends, backends_report
    informe = backends_report()
    assert isinstance(informe, str) and informe.strip()
    assert "ffprobe" in available_backends()


@pytest.mark.asyncio
async def test_studio_backends_se_ejecuta_de_verdad(tmp_path):
    ctx = ToolContext(task_id="t", cwd=tmp_path,
                      journal=WriteJournal("t", tmp_path / ".j"))
    r = await build_registry().execute("studio_backends", {}, ctx)
    assert r.ok, r.error
    assert isinstance(r.content, str) and r.content.strip()
    assert "ffmpeg" in r.content


def test_avisa_si_hay_ffmpeg_pero_no_ffprobe(monkeypatch):
    """
    Sin ffprobe se pueden GENERAR vídeos y no inspeccionarlos: el bucle de
    observación se rompe justo donde no se nota.
    """
    import magi.modules.studio.artifacts as art
    monkeypatch.setattr(art.shutil, "which",
                        lambda n: "/usr/bin/ffmpeg" if n == "ffmpeg" else None)
    assert "no ffprobe" in art.backends_report()


# ------------------------------------- «no he podido mirar» != «está bien»

@pytest.mark.asyncio
async def test_sin_pillow_la_imagen_no_se_da_por_buena(tmp_path, monkeypatch):
    """
    EL FALLO, encontrado simulando el entorno de CI.

    `_describe_image` sin Pillow devolvía «no se puede inspeccionar». Esa
    cadena no contiene "VACÍA" ni "ilegible", así que `observe_image` no
    apuntaba ningún problema y devolvía ok=True: certificaba como buena una
    imagen que jamás llegó a abrir.

    Este test no necesita Pillow ni que falte: fuerza la respuesta de
    `pillow_available`, así que vigila en cualquier máquina.
    """
    import magi.modules.studio.artifacts as art
    p = tmp_path / "captura.png"
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)

    monkeypatch.setattr(art, "pillow_available", lambda: False)
    o = await art.observe_image(p)

    assert not o.ok, "sin poder mirar, la imagen NO puede darse por buena"
    assert any("Pillow" in x for x in o.problems)
    assert not any("Pillow" in e for e in o.evidence), (
        "el aviso tiene que ir en problems, que es lo que entra en ok; "
        "en evidence no lo lee nadie")


@pytest.mark.asyncio
@sin_ffmpeg
async def test_sin_pillow_el_video_no_se_da_por_bueno(tmp_path, monkeypatch):
    """
    Mismo fallo y peor: un vídeo entero en negro y congelado salía con ok=True
    y cero problemas. Detectar eso es la única razón de ser de `observe_video`.
    """
    import magi.modules.studio.video as vid
    v = _lavfi(tmp_path / "negro.mp4", "color=c=black")

    monkeypatch.setattr(vid, "pillow_available", lambda: False)
    o = await vid.observe_video(v)

    assert not o.ok
    assert any("Pillow" in p for p in o.problems)
    assert any("congelado" in p.lower() for p in o.problems), (
        "tiene que decir QUÉ se ha dejado sin comprobar, no solo que falta "
        "una librería")
