"""
Entropía de Shannon para triaje de binarios (§5.3).

Reescribe `reverse/triage.py`, que estaba en el directorio de ingeniería
inversa y no lo importaba nadie. Se salvó porque la capacidad SÍ era útil —
distinguir un EBOOT cifrado de código roto es la primera pregunta al abrir un
binario de consola— pero tenía dos defectos que había que corregir al
conectarla.
"""
import os

import pytest

from magi.core.tools import ToolContext, WriteJournal, build_registry
from magi.modules.reverse.entropy import (
    BLOCK,
    HIGH_ENTROPY,
    EntropyReport,
    analyze_file,
    reading,
    shannon,
)


def _codigo(n_bloques: int = 20000) -> bytes:
    """Patrón repetido tipo prólogo MIPS: entropía baja, como el código real."""
    return b"".join(bytes([0x27, 0xbd, 0xff, 0xe0, 0xaf, 0xbf, 0x00, 0x1c])
                    for _ in range(n_bloques))


# ------------------------------------------------------------ el cálculo

def test_todo_ceros_es_entropia_cero():
    assert shannon(bytes(1000)) == 0.0


def test_bytes_equiprobables_dan_el_maximo():
    assert shannon(bytes(range(256)) * 10) == pytest.approx(8.0)


def test_vacio_no_divide_por_cero():
    assert shannon(b"") == 0.0


def test_coincide_con_el_calculo_de_referencia():
    """
    El histograma en una pasada tiene que dar EXACTAMENTE lo mismo que la
    versión ingenua de 256 pasadas que sustituye. Es 5x más rápido (1,81 s
    frente a 0,35 s por cada 10 MB), no distinto.
    """
    import math
    datos = os.urandom(50_000)
    esperado = 0.0
    for x in range(256):
        p = datos.count(x) / len(datos)
        if p > 0:
            esperado -= p * math.log2(p)
    assert shannon(datos) == pytest.approx(esperado, abs=1e-12)


def test_una_sola_pasada_sobre_el_buffer():
    """Contrato de rendimiento: 5 MB no pueden tardar segundos."""
    import time
    datos = os.urandom(5_000_000)
    t0 = time.time()
    shannon(datos)
    assert time.time() - t0 < 2.5


# ------------------------------------------------------------- la lectura

def test_lo_aleatorio_se_marca_como_cifrado():
    r = reading(shannon(os.urandom(100_000)))
    assert "cifrado o comprimido" in r
    assert "NO intentes desensamblar" in r


def test_el_codigo_no_se_marca_como_cifrado():
    """Contraprueba: un detector que dijera 'cifrado' a todo también pasaría."""
    assert "cifrado" not in reading(shannon(_codigo()))


def test_la_lectura_es_una_frase_util_y_no_un_booleano():
    """
    `triage.py` devolvía `is_encrypted_or_compressed` a secas. Un binario con
    recursos incrustados da 6,8: decir "no cifrado" ahí informa tan poco como
    decir "sí".
    """
    assert "recursos incrustados" in reading(7.0)
    assert reading(6.0) != reading(7.0) != reading(7.9)


# -------------------------------------------------------------- ficheros

def test_detecta_un_binario_cifrado_entero(tmp_path):
    f = tmp_path / "eboot.bin"
    f.write_bytes(os.urandom(200_000))
    informe = analyze_file(f)
    assert informe.encrypted
    assert informe.overall > HIGH_ENTROPY
    assert "antes de desensamblar" in informe.render()


def test_localiza_la_zona_cifrada_que_la_media_esconde(tmp_path):
    """
    EL CASO QUE JUSTIFICA EL MAPA POR BLOQUES. Un binario mayormente normal
    con una sección cifrada dentro da una media baja: mirar solo el valor
    global diría "es código" y se perdería la sección.
    """
    codigo = _codigo()
    f = tmp_path / "mixto.bin"
    f.write_bytes(codigo[:100_000] + os.urandom(40_000) + codigo[:60_000])

    informe = analyze_file(f)
    assert not informe.encrypted, "la media global no debe dispararse"
    zonas = informe.hot_regions()
    assert len(zonas) == 1
    inicio, fin = zonas[0]
    assert 96_000 <= inicio <= 104_000, f"zona mal localizada: {hex(inicio)}"
    assert 136_000 <= fin <= 148_000
    assert "la media global las escondía" in informe.render()


def test_un_binario_normal_no_tiene_zonas_calientes(tmp_path):
    f = tmp_path / "codigo.bin"
    f.write_bytes(_codigo())
    assert analyze_file(f).hot_regions() == []


def test_zona_caliente_al_final_del_fichero(tmp_path):
    """
    Un tramo que llega hasta el final se cerraba mal si el bucle solo cierra
    al encontrar un bloque bajo. Aquí no hay bloque bajo detrás.
    """
    f = tmp_path / "cola.bin"
    f.write_bytes(_codigo()[:80_000] + os.urandom(40_000))
    zonas = analyze_file(f).hot_regions()
    assert zonas and zonas[-1][1] >= 116_000


def test_fichero_mas_pequeño_que_un_bloque(tmp_path):
    f = tmp_path / "mini.bin"
    f.write_bytes(b"hola mundo")
    informe = analyze_file(f)
    assert informe.size == 10
    assert len(informe.blocks) == 1


def test_fichero_vacio_no_revienta(tmp_path):
    f = tmp_path / "vacio.bin"
    f.write_bytes(b"")
    informe = analyze_file(f)
    assert informe.overall == 0.0 and informe.blocks == []
    assert isinstance(informe.render(), str)


def test_errores_claros(tmp_path):
    with pytest.raises(FileNotFoundError):
        analyze_file(tmp_path / "no_existe.bin")
    with pytest.raises(IsADirectoryError):
        analyze_file(tmp_path)


def test_el_tamaño_real_se_informa_aunque_se_recorte(tmp_path):
    """Recortar para no bloquear el turno no puede falsear el tamaño."""
    f = tmp_path / "grande.bin"
    f.write_bytes(os.urandom(300_000))
    informe = analyze_file(f, max_bytes=50_000)
    assert informe.size == 300_000
    assert len(informe.blocks) == 50_000 // BLOCK + (1 if 50_000 % BLOCK else 0)


def test_to_dict_es_serializable(tmp_path):
    import json
    f = tmp_path / "a.bin"
    f.write_bytes(os.urandom(20_000))
    assert json.loads(json.dumps(analyze_file(f).to_dict()))["encrypted_or_compressed"]


# -------------------------------------------------------------- cableado

def test_la_herramienta_esta_en_el_catalogo():
    assert "binary_entropy" in build_registry().names()


@pytest.mark.asyncio
async def test_binary_identify_avisa_solo(tmp_path):
    """
    La entropía se integra en `binary_identify` y no solo como herramienta
    aparte, porque el momento en que evita perder horas es justo antes de
    desensamblar. Si el agente tiene que acordarse de pedirla, no se acordará.
    """
    f = tmp_path / "cifrado.bin"
    f.write_bytes(os.urandom(120_000))
    ctx = ToolContext(task_id="t", cwd=tmp_path,
                      journal=WriteJournal("t", tmp_path / ".j"))
    r = await build_registry().execute("binary_identify", {"path": "cifrado.bin"}, ctx)
    assert r.ok
    assert "entropía" in r.content
    assert "NO intentes desensamblar" in r.content
    assert r.meta["encrypted"] is True


@pytest.mark.asyncio
async def test_binary_entropy_extremo_a_extremo(tmp_path):
    f = tmp_path / "b.bin"
    f.write_bytes(_codigo()[:80_000] + os.urandom(40_000))
    ctx = ToolContext(task_id="t", cwd=tmp_path,
                      journal=WriteJournal("t", tmp_path / ".j"))
    reg = build_registry()
    r = await reg.execute("binary_entropy", {"path": "b.bin"}, ctx)
    assert r.ok and r.meta["hot_regions"]

    r = await reg.execute("binary_entropy", {"path": "fantasma.bin"}, ctx)
    assert not r.ok and "no existe" in r.error
