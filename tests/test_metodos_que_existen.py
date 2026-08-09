"""
Ningún `self._metodo()` apunta a un método que no existe.

EL FALLO QUE ESTO HABRÍA CAZADO
===============================
Al añadir la guarda de idioma, un método se renombró:

    _familias_disponibles  ->  _otras_familias_del_registry

Se actualizó la llamada de `_ask` y se quedó sin actualizar la de
`_ask_with_tools`. Lo que el usuario vio, en producción:

    [parallel] variante 1 falló: 'MelchiorAgent' object has no attribute
               '_familias_disponibles'
    [parallel] variante 0 falló: ...
    [parallel] variante 2 falló: ...
    [SWARM] Error catastrófico: ninguna variante de propuesta se completó

Tres minutos de espera, tres respuestas ya generadas y tiradas, y el enjambre
entero caído por un nombre.

POR QUÉ NO LO VIO NADIE
=======================
Python resuelve los atributos en tiempo de EJECUCIÓN. La línea mala solo se
ejecuta cuando la respuesta llega en otro idioma, así que:

  · el import funciona,
  · la sintaxis es válida,
  · los 855 tests pasan,
  · el CI pasa en cuatro combinaciones de sistema y versión,
  · el .exe compila.

Y revienta en la máquina del usuario, en la rama que solo se recorre de vez en
cuando. Es la misma familia que el `import torch` que el .spec excluye: código
correcto en todas las comprobaciones baratas y roto donde importa.

Un lenguaje con comprobación estática lo habría dicho al compilar. Python no,
así que se comprueba aquí.

CÓMO EVITA LOS FALSOS POSITIVOS
===============================
Se salta una clase entera si hereda de algo que no está definido en `magi/`
—`BaseModel`, `Protocol`, `Enum`, cualquier cosa de la librería estándar—,
porque entonces el método podría venir de arriba y no hay forma barata de
saberlo. Prefiere callar a acusar en falso: una alarma con ruido deja de
leerse, y entonces no sirve de nada tenerla.
"""
from __future__ import annotations

import ast
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PAQUETE = RAIZ / "magi"
IGNORADOS = {"_attic", "__pycache__"}

#: métodos que Python o un framework inyectan y que no aparecen como `def`.
SIEMPRE_EXISTEN = {
    "__init__", "__class__", "__dict__", "__doc__", "__module__",
    # pydantic v2
    "model_dump", "model_dump_json", "model_validate", "model_copy",
    "dict", "json", "copy",
    # dataclasses
    "__post_init__",
}


def _ficheros() -> list[Path]:
    return [p for p in PAQUETE.rglob("*.py")
            if not any(x in p.parts for x in IGNORADOS)]


class _Clase:
    def __init__(self, nombre: str, bases: list[str]):
        self.nombre = nombre
        self.bases = bases
        self.definidos: set[str] = set()     # def ... y self.x = ...
        self.usados: list[tuple[str, str, int]] = []   # (attr, fichero, línea)


def _es_self(nodo) -> bool:
    return isinstance(nodo, ast.Name) and nodo.id == "self"


def _objetivos(nodo) -> list[ast.expr]:
    """
    Aplana los destinos de una asignación, deshaciendo tuplas y listas.

    Sin esto, `self._tel, self.t = tel, t` no cuenta como definición de nada:
    el destino es una Tupla y los Attribute están dentro. Fue el primer falso
    positivo de este test, y es representativo — un analizador que no entiende
    una forma corriente de escribir acusa a código perfectamente sano.
    """
    if isinstance(nodo, (ast.Tuple, ast.List)):
        return [x for t in nodo.elts for x in _objetivos(t)]
    if isinstance(nodo, ast.Starred):
        return _objetivos(nodo.value)
    return [nodo]


def _cuerpo_sin_clases_anidadas(clase: ast.ClassDef):
    """
    Recorre el cuerpo de la clase SIN entrar en las clases de dentro.

    Un `ast.walk` normal mete los `self.x` de una clase anidada en la cuenta de
    la de fuera. `WriteJournal._Guard` usa `self.entry`, que existe en _Guard y
    no en WriteJournal: sin este corte, la anidada acusa a la que la contiene.
    """
    pila = list(clase.body)
    while pila:
        nodo = pila.pop()
        yield nodo
        for hijo in ast.iter_child_nodes(nodo):
            if isinstance(hijo, ast.ClassDef):
                continue                   # territorio de otra clase
            pila.append(hijo)


def _recoge_clases() -> dict[str, list[_Clase]]:
    """Todas las clases de `magi/`, con lo que definen y lo que usan de `self`."""
    clases: dict[str, list[_Clase]] = {}
    for fichero in _ficheros():
        try:
            arbol = ast.parse(fichero.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        rel = fichero.relative_to(RAIZ).as_posix()
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.ClassDef):
                continue
            bases = [b.id for b in nodo.bases if isinstance(b, ast.Name)]
            bases += [b.attr for b in nodo.bases if isinstance(b, ast.Attribute)]
            c = _Clase(nodo.name, bases)

            # Una clase anidada es un atributo de la de fuera: `self._Guard(...)`.
            for hijo in nodo.body:
                if isinstance(hijo, ast.ClassDef):
                    c.definidos.add(hijo.name)

            for hijo in _cuerpo_sin_clases_anidadas(nodo):
                # lo que la clase DEFINE
                if isinstance(hijo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    c.definidos.add(hijo.name)
                elif isinstance(hijo, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                    brutos = (hijo.targets if isinstance(hijo, ast.Assign)
                              else [hijo.target])
                    for t in [x for b in brutos for x in _objetivos(b)]:
                        if isinstance(t, ast.Attribute) and _es_self(t.value):
                            c.definidos.add(t.attr)
                        elif isinstance(t, ast.Name):
                            c.definidos.add(t.id)      # atributo de clase
                # lo que la clase USA de self
                elif isinstance(hijo, ast.Attribute) and _es_self(hijo.value):
                    c.usados.append((hijo.attr, rel, hijo.lineno))

            clases.setdefault(nodo.name, []).append(c)
    return clases


def _heredados(c: _Clase, clases: dict[str, list[_Clase]],
               vistos: set[str] | None = None) -> set[str] | None:
    """
    Todo lo que la clase hereda. None si alguna base es de fuera de `magi/`.

    None significa «no puedo saberlo», y ante eso la clase no se audita. Es la
    diferencia entre un aviso que se lee y uno que se ignora.
    """
    vistos = vistos or set()
    fuera: set[str] = set()
    for base in c.bases:
        if base in vistos:
            continue
        vistos.add(base)
        if base not in clases:
            return None                    # base desconocida: no auditamos
        for padre in clases[base]:
            fuera |= padre.definidos
            arriba = _heredados(padre, clases, vistos)
            if arriba is None:
                return None
            fuera |= arriba
    return fuera


def test_ningun_self_apunta_a_un_metodo_inexistente():
    clases = _recoge_clases()
    fallos: list[str] = []

    for versiones in clases.values():
        for c in versiones:
            heredado = _heredados(c, clases)
            if heredado is None:
                continue                   # hereda de fuera: no se puede saber
            disponibles = c.definidos | heredado | SIEMPRE_EXISTEN
            for attr, fichero, linea in c.usados:
                if attr in disponibles:
                    continue
                fallos.append(f"  {fichero}:{linea}  {c.nombre}.self.{attr}")

    assert not fallos, (
        "Hay accesos a `self.<algo>` que no existen en la clase ni en sus "
        "bases. En Python esto no falla hasta que se ejecuta esa línea, así "
        "que puede pasar los tests, el CI y la compilación y reventar en la "
        "máquina del usuario:\n" + "\n".join(sorted(set(fallos))))


def test_la_guarda_de_idioma_llama_a_un_metodo_que_existe():
    """
    El caso concreto que se rompió, fijado por su nombre.

    El test de arriba lo cubre, pero este falla con un mensaje que dice qué
    pasó y dónde, en vez de una entrada más en una lista.
    """
    from magi.modules.swarm.agents import BalthasarAgent, MelchiorAgent

    for clase in (MelchiorAgent, BalthasarAgent):
        assert hasattr(clase, "_otras_familias_del_registry"), (
            f"{clase.__name__} no tiene _otras_familias_del_registry")
        assert not hasattr(clase, "_familias_disponibles"), (
            f"{clase.__name__} conserva el nombre viejo _familias_disponibles: "
            f"o hay dos verdades sobre cómo se listan las familias, o alguien "
            f"lo reintrodujo")
