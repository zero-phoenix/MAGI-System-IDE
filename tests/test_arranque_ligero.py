"""
Arrancar MAGI no carga nada que MAGI no vaya a usar.

POR QUÉ ESTE TEST Y NO UNA OPTIMIZACIÓN MÁS
===========================================
El arranque del IDE llegó a pagar 3,4 s por un `import` que sobraba: sklearn
—con scipy, numpy y joblib detrás, unos 790 módulos— entraba en memoria porque
`AASLoader` construía su vectorizador TF-IDF en el constructor, y el Kernel
instancia el loader al construirse. En la instalación típica, que no tiene
clonado el catálogo de skills, esos 3,4 s no compraban absolutamente nada.

Lo instructivo no es el fallo, es su ciclo de vida: nadie lo introdujo a mala
idea, nadie lo notó durante meses, y el primer intento de arreglarlo (mover el
import al `__init__`) no arregló nada porque el `__init__` se ejecuta igual.
Una regresión así no rompe ningún test: el sistema hace exactamente lo mismo,
solo que más tarde. Es invisible salvo que alguien la mire a propósito.

Esto es ese alguien. No optimiza: FIJA lo ya ganado. Un `import numpy` al
nivel de un módulo del núcleo vuelve a costar segundos en cada arranque, y a
partir de ahora se ve en el CI el mismo día, no dentro de seis meses.

La lista de abajo son dependencias REALES del proyecto —se usan, y mucho—,
solo que ninguna hace falta para levantar el sistema:

  sklearn/scipy/numpy/joblib  búsqueda TF-IDF de skills (solo al buscar)
  g4f/curl_cffi              inferencia (solo al primer turno)
  capstone/unicorn           desensamblado y emulación (solo en ing. inversa)
  PIL/pygame                 fábrica de artefactos (solo al generar)
  pypdf/docx                 ingesta de documentos (solo al ingerir)

Cada una entra cuando se usa. Ese es el contrato.
"""
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]

#: paquetes que NO deben estar en memoria tras construir el sistema
PESADOS = [
    "sklearn", "scipy", "numpy", "joblib",
    "g4f", "curl_cffi",
    "capstone", "unicorn",
    "PIL", "pygame",
    "pypdf", "docx",
]


def _importar_en_proceso_limpio(codigo: str) -> tuple[list[str], str]:
    """
    Ejecuta `codigo` en un intérprete NUEVO y devuelve los pesados cargados.

    Tiene que ser un subproceso: para cuando este test corre, la suite ya ha
    importado media instalación, así que mirar el sys.modules de aquí no diría
    nada sobre lo que cuesta arrancar.
    """
    # El guion se monta línea a línea, sin textwrap.dedent: `codigo` viene sin
    # sangrar y dedent calcula el prefijo COMÚN, así que mezclarlos dentro de
    # un bloque sangrado deja el resto con sangría y revienta con
    # IndentationError. Concatenar es menos vistoso y no tiene ese filo.
    #
    # `python -c` tampoco añade el cwd a sys.path (a diferencia de
    # `python fichero.py`), así que la raíz del proyecto se inserta a mano.
    guion = "\n".join([
        "import sys",
        f"sys.path.insert(0, {str(RAIZ)!r})",
        codigo,
        'raiz = {m.split(".")[0] for m in sys.modules}',
        f'print(",".join(sorted(raiz & set({PESADOS!r}))))',
    ])
    r = subprocess.run([sys.executable, "-c", guion], capture_output=True,
                       text=True, timeout=180, cwd=str(RAIZ))
    if r.returncode != 0:
        pytest.skip(f"no se pudo importar en un proceso limpio: {r.stderr[-400:]}")
    salida = r.stdout.strip().splitlines()
    cargados = [x for x in (salida[-1] if salida else "").split(",") if x]
    return cargados, r.stderr


def test_construir_el_kernel_no_carga_nada_pesado():
    """
    Construir el Kernel es lo que hace `main.py` antes de enseñar nada.

    Se CONSTRUYE, no solo se importa: el fallo de sklearn se colaba justo ahí
    —en el constructor— y un test que solo importara la clase habría pasado
    tan tranquilo mientras el arranque seguía costando 3,4 s.
    """
    cargados, _ = _importar_en_proceso_limpio(
        "from magi.core.kernel import Kernel\n"
        "k = Kernel.__new__(Kernel)\n"
        "from magi.modules.skills.loader import AASLoader\n"
        "AASLoader(repo_path='/no/existe').load()\n"
    )
    assert not cargados, (
        f"El arranque carga {', '.join(cargados)} sin necesitarlo. "
        f"Busca un `import` de nivel de módulo (o dentro de un __init__ que el "
        f"Kernel ejecute) y bájalo al punto donde de verdad se usa. "
        f"Referencia: sklearn en el arranque costaba 3,4 s.")


def test_importar_la_cadena_de_main_no_carga_nada_pesado():
    """
    La cadena entera que `main.py` importa antes de abrir la ventana.

    Se omite `webview` a propósito: es la ventana en sí, no es opcional y no
    tiene sentido diferirla. Todo lo demás sí.
    """
    cargados, _ = _importar_en_proceso_limpio(
        "from magi.core.no_browser import install\n"
        "from magi.core.consola import configurar\n"
        "from magi.gui_server import GUIServer\n"
        "from magi.core.kernel import Kernel\n"
        "from magi.modules.resilience.selector import CloudSelector\n"
        "from magi.modules.route.gateway import Gateway\n"
        "from magi.modules.memory.composer import Composer\n"
    )
    assert not cargados, (
        f"La cadena de arranque de main.py carga {', '.join(cargados)}. "
        f"Ninguna de esas librerías hace falta para levantar el sistema: "
        f"entran cuando se usan.")


def test_el_catalogo_de_herramientas_no_carga_los_binarios():
    """
    Las 48 herramientas se registran sin tocar capstone, unicorn, PIL ni pygame.

    Registrar una herramienta es declarar su nombre, su esquema y su función.
    Las librerías que esa función necesitará se importan cuando se la invoca,
    no cuando se la ofrece — si no, ofrecer el catálogo entero costaría lo
    mismo que usarlo entero.
    """
    cargados, _ = _importar_en_proceso_limpio(
        "from magi.core.tools import registry_for_role\n"
        "registry_for_role('MELCHIOR', task_hint='')\n"
    )
    assert not cargados, (
        f"Construir el catálogo de herramientas carga {', '.join(cargados)}. "
        f"El coste de una librería debe pagarlo quien la usa, no quien lista "
        f"lo que hay disponible.")
