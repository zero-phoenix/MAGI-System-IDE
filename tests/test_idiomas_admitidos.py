"""
Cuatro idiomas de entrada, uno solo de salida.

LA REGLA, EN UNA FRASE
======================
Los proveedores pueden contestar en español, inglés, portugués o italiano —
**nunca en chino**— y lo que llega a la interfaz va **siempre en español**.

POR QUÉ ES UNA MEJORA Y NO UNA CONCESIÓN
========================================
Antes solo valía el idioma del usuario, así que una respuesta perfecta en
inglés era un fallo y disparaba una regeneración completa en otra familia. Eso
cuesta la latencia entera otra vez, puede fallar igual, y —lo peor— devuelve un
análisis DISTINTO: se tiraba un razonamiento correcto por el idioma en que
estaba escrito.

Ahora se traduce. Una llamada corta, mismas conclusiones, y el usuario lee
español igualmente.
"""
from __future__ import annotations

import pytest

from magi.core import idioma

# ------------------------------------------------ qué se acepta y qué no

@pytest.mark.parametrize("texto, codigo", [
    ("El mutex garantiza exclusión mutua entre los hilos que compiten.", "es"),
    ("The mutex guarantees mutual exclusion between the threads that compete.", "en"),
    ("Uma diferença importante é que o semáforo tem um contador para os "
     "recursos que estão disponíveis.", "pt"),
    ("La differenza è che il semaforo ha un contatore per le risorse che "
     "sono disponibili.", "it"),
])
def test_los_cuatro_idiomas_se_aceptan(texto, codigo):
    vale, detectado = idioma.admisible(texto)
    assert vale is True, f"{codigo} debería aceptarse: se detectó {detectado}"


def test_el_chino_NO_se_acepta_nunca():
    """
    EL CASO MEDIDO, NO UNO HIPOTÉTICO.

    `Yqcloud` —durante un tiempo el único candidato vivo de la familia `gpt`,
    la de MELCHIOR— responde esto a un prompt en español:

        'di: funciona' -> '看起来你输入的内容里「funciona」是西班牙语…'

    Esa fue la causa raíz de que el enjambre entregara conclusiones que el
    usuario no podía leer. Aquí no hay traducción que valga: se descarta y se
    vuelve a pedir a otra familia.
    """
    vale, detectado = idioma.admisible(
        "看起来你输入的内容里「funciona」是西班牙语，意思是运行、工作、起作用。")
    assert vale is False
    assert detectado == "zh"
    assert "zh" in idioma.PROHIBIDOS


@pytest.mark.parametrize("texto", [
    "Der Mutex garantiert den gegenseitigen Ausschluss zwischen den Threads.",
    "Le mutex garantit l'exclusion mutuelle entre les threads qui sont là.",
])
def test_lo_que_no_esta_en_la_lista_tampoco_se_acepta(texto):
    """
    Alemán y francés se detectan bien y NO están admitidos: el usuario nombró
    cuatro idiomas, no «los que se parezcan». Un idioma admitido de más es una
    respuesta que hay que traducir sin que nadie lo haya pedido.
    """
    vale, _ = idioma.admisible(texto)
    assert vale is False


def test_un_bloque_de_codigo_no_es_un_fallo_de_idioma():
    """
    Sin esto, `for i in range(10): print(i)` cuenta como «idioma desconocido» y
    dispara un reintento. Reintentar por no encontrar palabras vacías dentro de
    un bucle es gastar una llamada de red en nada.
    """
    vale, _ = idioma.admisible("```python\nfor i in range(10):\n    print(i)\n```")
    assert vale is True


def test_una_respuesta_vacia_no_dispara_reintentos():
    assert idioma.admisible("")[0] is True
    assert idioma.admisible("   \n ")[0] is True


# ------------------------------------------------ la salida, siempre español

def test_el_idioma_final_es_el_espanol_y_no_se_deduce():
    assert idioma.IDIOMA_FINAL == "es"
    assert idioma.necesita_traduccion("en") is True
    assert idioma.necesita_traduccion("pt") is True
    assert idioma.necesita_traduccion("it") is True
    assert idioma.necesita_traduccion("es") is False


def test_el_espanol_no_se_traduce_a_si_mismo():
    """Traducir español a español gasta una llamada y puede empeorar el texto."""
    assert idioma.necesita_traduccion(idioma.IDIOMA_FINAL) is False


def test_el_prompt_de_traduccion_prohibe_lo_que_rompe_una_conclusion():
    """
    Un modelo pequeño, si no se le ata, «mejora» el texto: resume las
    conclusiones y reformatea el código. Lo que se pide es un traductor, no un
    editor — si el enjambre concluyó algo, el usuario tiene que leer ESO.
    """
    p = idioma.instruccion_de_traduccion().lower()
    assert "sin resumir" in p, "sin esto, el modelo acorta las conclusiones"
    assert "código" in p, "los bloques de código no se traducen"
    assert "formato" in p, "las listas y tablas tienen que sobrevivir"
    assert "únicamente" in p, "si no, antepone «Aquí tienes la traducción»"


def test_los_cuatro_admitidos_son_exactamente_los_pedidos():
    """
    El usuario pidió cuatro. Si alguien añade uno «que total, se entiende», el
    contrato cambia sin que nadie lo decida.
    """
    assert set(idioma.ADMITIDOS) == {"es", "en", "pt", "it"}
    assert idioma.IDIOMA_FINAL in idioma.ADMITIDOS
    assert not set(idioma.ADMITIDOS) & set(idioma.PROHIBIDOS)


def test_hay_instruccion_de_idioma_para_los_cuatro():
    """
    La primera capa de la defensa es pedirlo en el prompt. Si un idioma
    admitido no tuviera plantilla, caería al texto genérico en inglés — pedirle
    en inglés a un modelo que responda en italiano funciona peor.
    """
    for codigo in idioma.ADMITIDOS:
        texto = idioma.instruccion(codigo)
        assert idioma.nombre_de(codigo) in texto, codigo
