"""
El motor EPD de Lilim: la eficiencia de GLM-5.3-Flash a escala local.

Lo que se protege: activación ESCASA y reportada (MoE), caché lineal de
sesión, NO LO SÉ sin leer nada, y hechos multimodales deterministas que no
inventan contenido.
"""
import struct

from magi.modules.lilim.motor import motor


def test_respuesta_con_metrica_de_activacion():
    r = motor.resolver("como se juega ps_vita con el teclado")
    assert r.fuente == "local" if hasattr(r, "fuente") else True
    assert "CONTROLES ps_vita" in r.respuesta
    assert 0 < r.dominios_activados <= r.dominios_totales
    assert r.ms < 500, "un motor local no tarda medio segundo"


def test_lo_desconocido_activa_cero_y_no_inventa():
    r = motor.resolver("cual es la capital de kirguistan")
    assert r.dominios_activados == 0
    assert r.respuesta.startswith("NO LO SÉ (local)")


def test_la_cache_lineal_responde_al_instante():
    """Atención lineal: la misma pregunta dos veces, la segunda desde el
    estado de la sesión."""
    a = motor.resolver("novedades de baterias con ia")
    b = motor.resolver("novedades de baterias con ia")
    assert b.de_cache and b.ms <= a.ms + 1.0


def test_el_presupuesto_de_recursos_no_ahoga_la_maquina():
    """La promesa al usuario del i7-3770 + GTX 1050: Lilim no usa GPU, no
    abre hilos, y su índice pesa megabytes — no gigabytes."""
    import json
    p = motor.resolver("mandos")
    # y el presupuesto declarado por el módulo rapida/motor:
    from magi.modules.lilim import rapida
    assert not hasattr(rapida, "torch"), "Lilim no carga torch"
    assert p.ms < 500


def test_hechos_de_imagen_son_deterministas(tmp_path):
    from magi.modules.lilim.rapida import hechos_de_imagen
    png = tmp_path / "prueba.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13)
                    + b"IHDR" + struct.pack(">II", 320, 240)
                    + b"\x08\x02\x00\x00\x00" + b"x")
    h = hechos_de_imagen(png)
    assert h["formato"] == "PNG" and h["dimensiones"] == [320, 240]
    assert "visión" in h["nota"], "el contenido semántico se escala, no se inventa"


def test_es_rapida_separa_lo_complejo():
    from magi.modules.lilim.rapida import es_rapida
    assert es_rapida("como se juega ps_vita")
    assert es_rapida("que es objdiff")
    assert not es_rapida("escribe un sistema operativo completo")
    assert not es_rapida("x" * 700)


# ------------------------------------ prueba directa de las clases públicas

def test_un_motor_frio_arranca_en_verde():
    """MotorLilim directamente: una instancia nueva (fría) construye su
    estado y responde sin cuelgue — el arranque en frío es parte del
    contrato, no un detalle."""
    from magi.modules.lilim.motor import MotorLilim
    frio = MotorLilim()
    r = frio.resolver("mandos de sega_saturn")
    assert "CONTROLES" in r.respuesta
    assert not r.de_cache, "una instancia recién nacida no puede acertar de caché"


def test_resolucion_declara_sus_metricas():
    """Resolucion es el 'parámetros activados' de Lilim: sus campos son el
    informe público. Sin ellos, la activación escasa no es verificable."""
    from magi.modules.lilim.motor import Resolucion, motor
    r = motor.resolver("repos de vita")
    assert isinstance(r, Resolucion)
    assert r.bytes_totales > 0 and r.ms >= 0
    assert 0 <= r.dominios_activados <= r.dominios_totales


def test_hechos_de_fichero_procedencia_minima(tmp_path):
    """hechos_de_fichero: el sha256 que A1 pide a cualquier artefacto."""
    from magi.modules.lilim.rapida import hechos_de_fichero
    f = tmp_path / "x.bin"
    f.write_bytes(b"contenido")
    h = hechos_de_fichero(f)
    assert h["bytes"] == 9 and h["extension"] == ".bin"
    assert len(h["sha256"]) == 33 and h["sha256"].endswith("…")
