"""
Lo que el .spec deja fuera del .exe, el código no puede necesitarlo dentro.

EL FALLO QUE ESTO IMPIDE
========================
`MAGI-IDE-v5.spec` excluye del binario una pila de ML que MAGI no usa y que
entraba de polizón por una integración opcional de g4f:

    g4f/tools/files.py -> g4f.integration.markitdown -> markitdown
    -> magika -> onnxruntime  (y de ahí torch, transformers, tensorflow)

Excluirlos quitó peso y arregló además un cuelgue reproducible de la
compilación (PyInstaller se quedaba parado en torch/__init__.py:265 resolviendo
DLLs). Todo correcto.

Pero esa exclusión es una AFIRMACIÓN sobre el código: «nada de magi/ importa
esto». Y esa afirmación no la vigila nadie. El día que alguien escriba
`import torch` en un módulo —para una utilidad, para una prueba que se queda—
pasará esto, en este orden:

  1. Los tests siguen verdes: en la máquina de desarrollo torch está instalado.
  2. El CI sigue verde: en el runner también.
  3. El .exe compila sin protestar.
  4. El usuario lo abre y revienta con ModuleNotFoundError.

Es decir: el fallo aparece exactamente donde no hay nadie mirando, después de
pasar por todos los sitios donde sí lo había. Y es el peor sitio posible, porque
para el usuario no es «una función no va»: es que el programa no arranca.

Es el mismo patrón que ya se cazó con la ruta absoluta en pyrightconfig.json —
una afirmación de configuración que el código puede desmentir en silencio— y se
cierra igual: comprobándola.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SPEC = RAIZ / "MAGI-IDE-v5.spec"
PAQUETE = RAIZ / "magi"

#: se salta: andamiaje retirado, conservado como mapa y fuera del binario.
IGNORADOS = {"_attic", "__pycache__"}


def _excluidos_del_spec() -> set[str]:
    """Los `excludes=[...]` del .spec, leídos del .spec y no copiados aquí."""
    texto = SPEC.read_text(encoding="utf-8")
    m = re.search(r"excludes\s*=\s*\[(.*?)\]", texto, re.DOTALL)
    assert m, "no encuentro `excludes=[...]` en MAGI-IDE-v5.spec"
    return set(re.findall(r"['\"]([A-Za-z0-9_.]+)['\"]", m.group(1)))


def _modulos_importados_por_magi() -> dict[str, list[str]]:
    """Raíz de cada módulo importado en `magi/`, con dónde se importa."""
    encontrados: dict[str, list[str]] = {}
    for fichero in PAQUETE.rglob("*.py"):
        if any(p in IGNORADOS for p in fichero.parts):
            continue
        try:
            arbol = ast.parse(fichero.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for nodo in ast.walk(arbol):
            raices: list[str] = []
            if isinstance(nodo, ast.Import):
                raices = [a.name.split(".")[0] for a in nodo.names]
            elif isinstance(nodo, ast.ImportFrom) and nodo.module and not nodo.level:
                raices = [nodo.module.split(".")[0]]
            for r in raices:
                encontrados.setdefault(r, []).append(
                    f"{fichero.relative_to(RAIZ).as_posix()}:{nodo.lineno}")
    return encontrados


def test_el_spec_sigue_teniendo_sus_exclusiones():
    """
    Sin ellas el binario engorda y la compilación se cuelga en torch.

    No es una precaución teórica: tres compilaciones seguidas se quedaron
    paradas en «Looking for dynamic libraries» antes de que se añadieran.
    """
    excluidos = _excluidos_del_spec()
    for imprescindible in ("torch", "tensorflow", "transformers", "onnxruntime"):
        assert imprescindible in excluidos, (
            f"'{imprescindible}' ya no está en excludes del .spec. Entra de "
            f"polizón por g4f -> markitdown -> magika, hincha el binario y "
            f"cuelga la compilación.")


def test_nada_de_magi_importa_lo_que_el_spec_deja_fuera():
    """
    La comprobación que faltaba: la exclusión y el código, de acuerdo.

    Si esto falla tienes dos salidas, y la primera es casi siempre la buena:

      · El import sobra o puede ser opcional → quítalo, o envuélvelo en un
        try/except que degrade con un mensaje claro.
      · La dependencia hace falta de verdad → sácala de `excludes` en el .spec,
        asumiendo el peso en el binario, y anota por qué.

    Lo que no vale es dejarlo así: el .exe se publicaría roto.
    """
    excluidos = _excluidos_del_spec()
    importados = _modulos_importados_por_magi()

    choques = {mod: sitios for mod, sitios in importados.items() if mod in excluidos}
    assert not choques, (
        "magi/ importa módulos que el .spec excluye del binario. El .exe "
        "publicado reventaría al arrancar, y ni los tests ni el CI lo verían "
        "porque en esas máquinas el paquete SÍ está instalado:\n" +
        "\n".join(f"  {mod}: {', '.join(sitios[:3])}"
                  for mod, sitios in sorted(choques.items())))


def test_los_datos_que_el_exe_necesita_viajan_dentro():
    """
    `datas` del .spec contra lo que el sistema lee en tiempo de ejecución.

    Un .exe sin `magi/data` arranca igual: se cae al respaldo de constantes y
    funciona. Por eso este fallo es silencioso, y por eso se comprueba — lo que
    se pierde es justo lo que se buscaba al externalizar el catálogo: arreglar
    un proveedor caído sin recompilar 158 MB.
    """
    texto = SPEC.read_text(encoding="utf-8")
    for necesario in ("magi/data", "magi-gui/dist", "assets"):
        assert necesario in texto, (
            f"'{necesario}' no viaja dentro del .exe según el .spec")

    assert (RAIZ / "magi/data/catalogo_proveedores.json").exists(), (
        "el catálogo de proveedores no está en el repositorio: el .spec lo "
        "empaquetaría vacío y el binario caería al respaldo sin avisar")
