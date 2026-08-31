"""
Lo que MAGI cree de MAGI, y qué dice la realidad (Fase 10).

POR QUÉ EXISTE, Y POR QUÉ NO SE LLAMA «CONCIENCIA»
==================================================
Nadie sabe construir conciencia ni verificarla: no hay experimento que la
distinga de un sistema que se comporta como si la tuviera. Ponerle esa etiqueta
a un fichero sería quitarle lo único que lo hace útil — que se puede falsar.

Pero lo que suele quererse decir con ella, cuando lo que se busca es
**rendimiento**, se desmonta en cuatro capacidades concretas, y tres ya están:

  saber qué hace y por qué ...... bitácora + memoria permanente ... SÍ
  notar que se equivocó ......... Ritsuko + los trinquetes ........ SÍ
  mejorar sin que se lo pidan ... naoko.self_improve ............. PARCIAL
  **cambiar de plan ante evidencia contraria** .................. NO

La cuarta es la que falta, y no es teórica. En la Ronda 0 de YabauseVita la
medición invalidó el plan entero —las tres filosofías atacaban el 1,27 % del
tiempo— y **el sistema no tenía forma de decirlo**: las rondas solo saben
producir un ganador.

QUÉ HACE ESTE MÓDULO
====================
Mantiene `docs/AUTOMODELO.md`: una lista de afirmaciones que MAGI hace **sobre
sí mismo**, cada una con su comprobación, su fecha y su estado. Y la contrasta:

    afirmar("se medir el rendimiento del emulador", prueba="ronda_emulador")
    → cada ronda, el resultado real marca la afirmación

Si la corrida falla, la afirmación pasa a `refutada` **sola**, sin que nadie la
revise a mano. Eso es introspección con compuerta: no dice que MAGI se conozca,
dice que lo que MAGI cree de sí mismo tiene fecha de caducidad y se comprueba.

LA REGLA QUE LO SOSTIENE
========================
Una afirmación sin prueba asociada **no se admite**. «Soy bueno razonando» no
es una afirmación sobre uno mismo: es una opinión. «`analyze_port` devuelve la
tabla de subsistemas en menos de 5 s» sí, porque puede fallar.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path

#: La API es esta. Afirmacion es el tipo que devuelven, no algo
#: que se construya desde fuera: exportarla la volvia una definicion
#: publica que nadie llama, y el trinquete de huerfanos tiene razon.
__all__ = ["Automodelo", "cargar", "para_el_prompt"]

FICHERO = "AUTOMODELO.json"
SUBRUTA = Path("docs")

#: Estados posibles. `sin_comprobar` es de primera clase a propósito: una
#: afirmación que nunca se ha puesto a prueba no es verdadera ni falsa, y
#: tratarla como verdadera es el fallo que R9 vino a corregir.
ESTADOS = ("sin_comprobar", "sostenida", "refutada", "retirada")


@dataclass
class Afirmacion:
    #: Qué dice MAGI de sí mismo. Tiene que poder fallar.
    texto: str
    #: Cómo se comprueba. Sin esto no se admite la afirmación.
    prueba: str
    estado: str = "sin_comprobar"
    #: Última vez que la realidad dijo algo al respecto.
    ultima: str = ""
    #: Qué dijo exactamente.
    evidencia: str = ""
    #: Cuántas veces se sostuvo y cuántas se cayó. El historial importa: una
    #: afirmación que se cae una de cada tres veces no es «sostenida».
    veces_ok: int = 0
    veces_mal: int = 0

    @property
    def fiabilidad(self) -> float | None:
        t = self.veces_ok + self.veces_mal
        return round(self.veces_ok / t, 2) if t else None

    def render(self) -> str:
        marca = {"sostenida": "OK", "refutada": "REFUTADA",
                 "sin_comprobar": "SIN COMPROBAR", "retirada": "retirada"}
        linea = f"- [{marca.get(self.estado, self.estado)}] {self.texto}"
        if self.fiabilidad is not None:
            linea += f"  ({self.veces_ok}/{self.veces_ok + self.veces_mal})"
        if self.estado == "refutada" and self.evidencia:
            linea += f"\n      la realidad dijo: {self.evidencia}"
        return linea


class Automodelo:
    def __init__(self, afirmaciones: list[Afirmacion] | None = None):
        self.afirmaciones: list[Afirmacion] = afirmaciones or []

    # -- edición ---------------------------------------------------------

    def afirmar(self, texto: str, prueba: str) -> Afirmacion | None:
        """
        Añade una afirmación. Devuelve None si no trae prueba: una afirmación
        que no puede fallar no es una afirmación sobre uno mismo, es una
        opinión, y este fichero no es para opiniones.
        """
        if not texto.strip() or not prueba.strip():
            return None
        for a in self.afirmaciones:
            if a.texto == texto.strip():
                return a
        a = Afirmacion(texto=texto.strip(), prueba=prueba.strip())
        self.afirmaciones.append(a)
        return a

    def contrastar(self, prueba: str, ok: bool, evidencia: str = "") -> int:
        """
        La realidad habla. Marca todas las afirmaciones que dependen de esa
        prueba y devuelve cuántas tocó.

        No borra las refutadas: una afirmación que se cayó y volvió a
        sostenerse es información distinta de una que nunca falló, y borrarla
        perdería justo eso.
        """
        n = 0
        ahora = time.strftime("%Y-%m-%d %H:%M")
        for a in self.afirmaciones:
            if a.prueba != prueba or a.estado == "retirada":
                continue
            a.estado = "sostenida" if ok else "refutada"
            a.ultima = ahora
            a.evidencia = evidencia[:300]
            if ok:
                a.veces_ok += 1
            else:
                a.veces_mal += 1
            n += 1
        return n

    def retirar(self, texto: str) -> bool:
        for a in self.afirmaciones:
            if a.texto == texto:
                a.estado = "retirada"
                return True
        return False

    # -- consulta --------------------------------------------------------

    @property
    def refutadas(self) -> list[Afirmacion]:
        return [a for a in self.afirmaciones if a.estado == "refutada"]

    @property
    def sin_comprobar(self) -> list[Afirmacion]:
        return [a for a in self.afirmaciones if a.estado == "sin_comprobar"]

    @property
    def fragiles(self) -> list[Afirmacion]:
        """Sostenidas pero que se caen a menudo. Son las que engañan."""
        return [a for a in self.afirmaciones
                if a.fiabilidad is not None and a.fiabilidad < 0.7
                and a.estado != "retirada"]

    def render(self) -> str:
        if not self.afirmaciones:
            return ""
        L = ["# Lo que MAGI cree de MAGI", "",
             "Generado por `magi.modules.swarm.automodelo`. Cada afirmación",
             "lleva la prueba que puede tumbarla. Sin prueba no se admite.", ""]
        for titulo, grupo in (("Refutadas por la realidad", self.refutadas),
                              ("Frágiles (se caen a menudo)", self.fragiles),
                              ("Sin comprobar todavía", self.sin_comprobar),
                              ("Todas", self.afirmaciones)):
            if not grupo:
                continue
            L += [f"## {titulo}", ""] + [a.render() for a in grupo] + [""]
        return "\n".join(L)

    # -- persistencia ----------------------------------------------------

    def guardar(self, ruta: Path) -> None:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(
            json.dumps([asdict(a) for a in self.afirmaciones],
                       ensure_ascii=False, indent=1),
            encoding="utf-8")


def _ruta(inicio=None) -> Path | None:
    env = os.environ.get("MAGI_AUTOMODELO")
    if env:
        return Path(env)
    base = Path(inicio or Path.cwd()).resolve()
    for c in (base, *base.parents):
        if (c / "magi").is_dir():
            return c / SUBRUTA / FICHERO
    return None


def cargar(inicio=None) -> Automodelo:
    r = _ruta(inicio)
    if r is None or not r.is_file():
        return Automodelo()
    try:
        crudo = json.loads(r.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Automodelo()
    fuera = []
    for d in crudo:
        try:
            fuera.append(Afirmacion(**d))
        except TypeError:
            continue        # esquema viejo: se ignora esa, no todas
    return Automodelo(fuera)


def para_el_prompt(encargo: str = "", inicio=None) -> str:
    """
    Lo que va arriba del prompt. Solo lo que puede cambiar una decisión:
    lo refutado y lo frágil. Lo que se sostiene sin fallar no hace falta
    recordarlo — ocupa contexto y no cambia nada.
    """
    m = cargar(inicio)
    interesante = m.refutadas + [a for a in m.fragiles if a not in m.refutadas]
    if not interesante:
        return ""
    filas = "\n".join(a.render() for a in interesante[:8])
    return (
        "\n\nLO QUE CREES DE TI Y LA REALIDAD HA DESMENTIDO:\n"
        f"{filas}\n"
        "No vuelvas a apoyarte en estas capacidades sin comprobarlas antes. "
        "Si crees que alguna ya está arreglada, dilo y trae la corrida que lo "
        "demuestra — se marcan solas con la evidencia, no por opinión."
    )
