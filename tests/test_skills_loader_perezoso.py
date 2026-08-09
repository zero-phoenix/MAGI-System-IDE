"""
El catálogo de skills no cobra por adelantado.

QUÉ SE ARREGLÓ Y POR QUÉ ESTE TEST EXISTE
=========================================
`AASLoader` usa TF-IDF (scikit-learn) para buscar skills por relevancia.
sklearn arrastra scipy, numpy y joblib: unos 790 módulos y ~3,4 s de import
en frío. Y `kernel.py` construye el loader en su propio constructor:

    self.skills_loader = AASLoader()

Con los imports en el nivel del módulo, esos 3,4 s se pagaban en CADA arranque
del IDE, incluso en la instalación típica —que no tiene clonado
agentic-awesome-skills y por tanto nunca busca nada—.

Un primer intento movió el import al `__init__` de AASLoader. Eso no arregla
nada: el `__init__` se ejecuta igual, porque el Kernel INSTANCIA el loader, no
solo lo importa. Es la trampa de este tipo de optimización — parece diferido y
no lo es, y como el sistema sigue funcionando, nadie lo comprueba.

El diferimiento real baja el import hasta el punto donde de verdad hace falta:
crear el vectorizador la primera vez que hay corpus que vectorizar.

Los dos tests de abajo fijan las dos mitades del contrato: que no se paga si no
se usa, y que sigue funcionando cuando se usa.
"""
import sys

import pytest

from magi.modules.skills.loader import AASLoader

_PESADOS = {"sklearn", "scipy", "joblib"}


def _pesados_cargados() -> set[str]:
    return {m.split(".")[0] for m in sys.modules} & _PESADOS


def test_sin_skills_no_se_paga_sklearn(tmp_path):
    """
    El caso normal: no hay repositorio de skills. No debe tocarse sklearn.

    Si sklearn ya estaba importado por otro test de la sesión, la comprobación
    directa no diría nada, así que se mira lo que sí es observable siempre: que
    el loader no ha construido vectorizador.
    """
    loader = AASLoader(repo_path=str(tmp_path / "no-existe"))
    assert loader.load() == 0
    assert loader.vectorizer is None, (
        "sin skills que indexar no debe crearse el vectorizador: crearlo es "
        "exactamente lo que arrastra sklearn al arranque del IDE")
    assert loader.tfidf_matrix is None


def test_con_skills_indexa_y_busca_igual_que_antes(tmp_path):
    """
    El contrato de siempre: si hay skills, se indexan y la búsqueda ordena por
    relevancia. Diferir un import no puede cambiar lo que el sistema hace.
    """
    pytest.importorskip("sklearn", reason="scikit-learn no instalado")

    plugins = tmp_path / "plugins"
    for nombre, texto in [
        ("emulator-tools", "Disassemble MIPS binaries and inspect dynarec code"),
        ("cooking-recipes", "Recipes for bread, pasta and desserts"),
    ]:
        d = plugins / nombre
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(texto, encoding="utf-8")

    loader = AASLoader(repo_path=str(tmp_path))
    assert loader.load() == 2
    assert loader.vectorizer is not None, "con corpus SÍ debe crearse"
    assert loader.tfidf_matrix is not None

    resultado = loader.search("disassemble a MIPS binary")
    assert "emulator-tools" in resultado
    assert resultado.index("emulator-tools") < resultado.index("cooking-recipes") \
        if "cooking-recipes" in resultado else True


def test_buscar_sin_indice_no_revienta(tmp_path):
    """
    `search()` antes del índice devuelve un mensaje, no una excepción.

    Con el vectorizador perezoso, `self.vectorizer` puede ser None cuando antes
    siempre era un objeto. Cualquier ruta que lo usara sin comprobarlo daría
    AttributeError; esto fija que no ocurre.
    """
    loader = AASLoader(repo_path=str(tmp_path / "no-existe"))
    loader.load()
    assert loader.search("lo que sea") == "No hay skills disponibles."
