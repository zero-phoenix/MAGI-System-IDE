"""
Que la bitácora llegue al prompt, y que llegue LITERAL.

El fallo que estas pruebas vigilan no es «el módulo no funciona»: es «el módulo
funciona y el enjambre no lo ve», que fue exactamente lo que pasó con el
catálogo de herramientas (`menciones_a_herramientas: 0` durante cinco pruebas
seguidas mientras el catálogo viajaba correctamente al final del prompt).

Por eso hay una prueba de integración contra el orquestador y no solo unitarias.
"""
import os
from pathlib import Path

import pytest

from magi.modules.swarm import bitacora


BITACORA_FALSA = """# Bitácora de prueba

## 1. Introducción

Texto que NO debe viajar al prompt.

## 2. Las tres filosofías

### A — Hacer menos trabajo

El píxel más rápido es el que no se dibuja.

## 3. Criterio de decisión

1. Compila.
2. No retrocede.
3. Mejora sostenida.

## 4. Rondas

Ruido que no debe copiarse.

## 5. Conocimiento acumulado

### 5.1 Sobre la arquitectura

| # | Hallazgo | Origen |
|---|---|---|
| A1 | VIDCORE_GPU rasteriza por software. | vidgpu.c |

### 5.2 Reglas derivadas

| # | Regla | Por qué |
|---|---|---|
| R1 | No proponer un JIT nuevo de SH-2. | A5 |

## 6. Cómo lo usa MAGI

Más ruido.
"""


@pytest.fixture
def bitacora_falsa(tmp_path, monkeypatch):
    ruta = tmp_path / "docs" / bitacora.NOMBRE
    ruta.parent.mkdir(parents=True)
    ruta.write_text(BITACORA_FALSA, encoding="utf-8")
    monkeypatch.setenv("MAGI_BITACORA", str(ruta))
    return ruta


# --- pertinencia ---------------------------------------------------------

@pytest.mark.parametrize("encargo", [
    "optimiza el emulador yabause",
    "por que baja el FPS en Panzer Dragoon",
    "arranca la ronda 1 de mejora",
    "el composite tarda demasiado",
    "revisa el dynarec",
])
def test_encargos_del_ciclo_son_pertinentes(encargo):
    assert bitacora.pertinente(encargo)


@pytest.mark.parametrize("encargo", [
    "hazme un ping pong de 32 bits",
    "resume este PDF",
    "por que duele la soledad",
])
def test_encargos_ajenos_no_lo_son(encargo):
    assert not bitacora.pertinente(encargo)


# --- recorte de secciones ------------------------------------------------

def test_copia_las_secciones_que_caducan_peor():
    fuera = bitacora.secciones(BITACORA_FALSA)
    assert "A1" in fuera            # conocimiento acumulado
    assert "R1" in fuera            # reglas derivadas
    assert "Mejora sostenida" in fuera   # criterio de decisión


def test_lleva_tambien_el_marco_de_las_tres_filosofias():
    """
    Regresión de un fallo real: la primera versión inyectaba las reglas sin el
    marco. El enjambre recibía qué NO hacer sin recibir de qué tres formas se
    puede atacar el problema, y eso produce propuestas tímidas.
    """
    fuera = bitacora.secciones(BITACORA_FALSA)
    assert "Hacer menos trabajo" in fuera


def test_no_arrastra_secciones_vecinas():
    """5.1 no puede tragarse 5.2, ni 3 tragarse 4."""
    fuera = bitacora.secciones(BITACORA_FALSA)
    assert "Ruido que no debe copiarse" not in fuera
    assert "Más ruido" not in fuera
    assert "Texto que NO debe viajar" not in fuera


def test_seccion_ausente_no_revienta():
    assert bitacora.secciones("# vacío", ("9.9",)) == ""


# --- bloque de prompt ----------------------------------------------------

def test_el_bloque_lleva_hallazgos_y_reglas(bitacora_falsa):
    texto = bitacora.para_el_prompt("optimiza el emulador yabause")
    assert "A1" in texto and "R1" in texto
    assert "LO QUE YA SE MIDIÓ" in texto


def test_calla_en_encargos_ajenos(bitacora_falsa):
    assert bitacora.para_el_prompt("hazme un tetris portable") == ""


def test_calla_si_no_hay_bitacora(monkeypatch, tmp_path):
    """Sin fichero se devuelve vacío, no una advertencia repetida cada vez."""
    monkeypatch.delenv("MAGI_BITACORA", raising=False)
    monkeypatch.chdir(tmp_path)
    assert bitacora.para_el_prompt("optimiza yabause", inicio=tmp_path) == ""


def test_el_bloque_es_copia_literal(bitacora_falsa):
    """
    Nada de resúmenes generados: ese mecanismo es el que produjo un
    PORTING_NOTES.md que fue cierto y dejó de serlo.
    """
    texto = bitacora.para_el_prompt("optimiza yabause")
    assert "| A1 | VIDCORE_GPU rasteriza por software. | vidgpu.c |" in texto


def test_localizar_sube_por_el_arbol(tmp_path, monkeypatch):
    monkeypatch.delenv("MAGI_BITACORA", raising=False)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / bitacora.NOMBRE).write_text("x", encoding="utf-8")
    hondo = tmp_path / "src" / "vita"
    hondo.mkdir(parents=True)
    assert bitacora.localizar(hondo) == tmp_path / "docs" / bitacora.NOMBRE


# --- métrica de uso ------------------------------------------------------

def test_citada_detecta_identificadores():
    assert bitacora.citada("choca con R1 y confirma A2") == ["R1", "A2"]


def test_citada_no_inventa():
    assert bitacora.citada("no cito nada") == []


# --- integración: que el orquestador lo inyecte de verdad ----------------

def test_el_orquestador_inyecta_la_bitacora():
    """
    La prueba que importa. Un módulo correcto que nadie llama es el fallo
    número 1 de este repositorio ("todo cambio se conecta o se borra").

    Desde la v5.11.0 la secuencia de inyecciones vive en `inyecciones.py`
    (la cuarta inyección inline hizo saltar el trinquete del orquestador),
    así que la conducta que se comprueba es la CADENA: el orquestador llama
    al agregador, y el agregador inyecta la bitácora. Exigir el import
    literal aquí sería de nuevo romper el test por una reorganización
    inocua — la misma lección que la del alias, un nivel arriba.
    """
    import re
    orch = Path("magi/modules/swarm/orchestrator.py").read_text(encoding="utf-8")
    iny = Path("magi/modules/swarm/inyecciones.py").read_text(encoding="utf-8")
    assert re.search(r"import\s+inyecciones\s+as\s+\w+", orch) and \
        "acumuladas" in orch, "el orquestador no llama a las inyecciones"
    m = re.search(r"import\s+bitacora\s+as\s+(\w+)", iny)
    assert m, "las inyecciones no importan la bitácora"
    # La LLAMADA, no cómo se llame el alias.
    assert "%s.para_el_prompt" % m.group(1) in iny, (
        "la bitácora se importa pero no se inyecta en el prompt")
