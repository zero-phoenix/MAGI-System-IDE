"""
Las tres filosofías ortogonales: por construcción, no por suerte.

QUÉ ESTABA MAL
==============
La bitácora del emulador (§2) exige que las tres propuestas de cada ronda sean
«tres formas distintas de atacar el mismo cuello, mutuamente excluyentes por
diseño. Si las tres apuntaran al mismo mecanismo, la comparación no
distinguiría nada».

Y `generate_variants` las diversificaba **por semilla**: tres llamadas al mismo
agente con `seed + n*101`. Eso da tres redacciones distintas, no tres ataques
distintos. Nada impedía que las tres propusieran recortar `composite` con otras
palabras, y entonces la ronda gasta tres compilaciones para medir una sola
idea.

La ortogonalidad no puede salir de la temperatura del muestreo. Se asigna.

Y §6 de la bitácora pedía además una segunda cosa que tampoco existía:

    «Melchior debe declarar a qué filosofía pertenece cada una y su predicción
    falsable. Si alguna choca con una regla de §5.2, se rechaza sin llegar a
    compilar.»

Rechazar «sin llegar a compilar» es la parte cara: una compilación del .vpk y
una corrida verificada por propuesta. Tres propuestas que violan R6 cuestan
tres ciclos completos para descubrir algo que ya estaba escrito.

ORTOGONAL NO QUIERE DECIR QUE VALGA LA PENA
===========================================
Esto es lo que la ronda 0 enseñó y conviene no perder: las tres filosofías de
la §2 son perfectamente ortogonales entre sí **y las tres atacan el 1,27 % del
tiempo**. Eliminar el camino de render entero subiría de 17,1 a ~17,3 FPS.

Así que este módulo hace dos trabajos separados y no los confunde:

  1. REPARTO — que las N variantes ataquen N mecanismos distintos.
  2. CHOQUES — que ninguna proponga algo que la §5.2 ya prohibió.

Lo segundo es lo que hoy tiene consecuencias: con la bitácora en su estado
actual, las tres filosofías de la §2 están **suspendidas** (R6 para A y B, A9
para C, que ni siquiera tiene su métrica expuesta en el log). El módulo no lo
esconde: lo dice en el prompt de cada variante, con la regla que la suspende y
qué haría falta para levantarla.

Un mecanismo que produce tres propuestas prohibidas en silencio es peor que
uno que no produce ninguna.

TRES VARIANTES, Y POR QUE ESO CONTRADICE A D6
=============================================
`_n_variantes` devuelve 2, por D6: medido el 20-ago, tres enfoques dieron
27.753 caracteres, un 24,7 % entregado y ningun artefacto. «Menos enfoques,
mas ciclos de verificacion.»

Cuando el orquestador reparte filosofias sube a 3, y la contradiccion es solo
aparente: D6 midio variantes diversificadas POR SEMILLA — tres redacciones de
la misma idea, que es justamente el desperdicio que este modulo existe para
quitar. Tres ataques a mecanismos distintos no son tres textos redundantes.

Y con 2 el reparto estaria roto por construccion: `asignada` cicla, asi que
las variantes 0 y 1 se llevan «hacer menos» y «mover menos», y «repartir
mejor» NO SE EXPLORA NUNCA. Un mecanismo que dice ser ortogonal ignorando un
tercio de sus ejes miente en la unica cosa que promete.

Si una medicion futura demuestra que la tercera variante tampoco entrega,
esto se baja a 2 y se dice — pero entonces hay que quitar tambien la palabra
«ortogonal», porque ya no lo seria.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

#: Lo que se llama desde fuera son las funciones y las dos constantes.
#: `Filosofia`, `Regla` y `Reparto` son los tipos que devuelven; se importan
#: para anotar y para comprobar su contrato, no para construirlos.
__all__ = [
    "Filosofia", "Regla", "Reparto",
    "FILOSOFIAS", "REGLAS",
    "pertinente", "asignada", "para_la_variante",
    "clasificar", "revisar", "choques",
]


def _plano(s: str) -> str:
    """Sin tildes y en minúsculas: `composición` y `composicion` son lo mismo."""
    sin = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in sin if not unicodedata.combining(c))


# --------------------------------------------------------------- filosofías

@dataclass(frozen=True)
class Filosofia:
    """Una de las tres formas de atacar el cuello. §2 de la bitácora."""

    clave: str
    nombre: str
    lema: str
    #: El contador que tiene que moverse si funciona. Sin esto la propuesta no
    #: es falsable, y una propuesta que no puede perder no compite.
    metrica: str
    #: Qué se le pide a la variante que explore.
    encargo: str
    #: El fallo típico de ESTA familia. Va en el prompt porque anticiparlo es
    #: barato y descubrirlo compilando no.
    riesgo: str
    #: Vocabulario que delata a qué filosofía pertenece un texto.
    marcas: tuple[str, ...]
    #: Regla o hallazgo que la tiene suspendida hoy. Vacío = disponible.
    suspendida_por: str = ""
    #: Qué haría falta para levantarla.
    levanta: str = ""


FILOSOFIAS: tuple[Filosofia, ...] = (
    Filosofia(
        clave="hacer_menos",
        nombre="A - Hacer menos trabajo",
        lema="El pixel mas rapido es el que no se dibuja.",
        metrica="composite",
        encargo=("Elimina computo redundante sin cambiar el resultado visible: "
                 "planos que no cambiaron entre fotogramas, scanlines "
                 "identicas, capas ocultas bajo otras, regiones fuera del area "
                 "visible."),
        riesgo=("invalidacion incompleta. El fallo tipico no es un crash, es "
                "un fantasma que aparece tres minutos despues."),
        marcas=("composite", "rasteriz", "redundante", "scanline", "plano",
                "capa oculta", "invalidac", "dirty", "no dibuj", "recort",
                "cull", "fuera del area visible"),
        suspendida_por="R6",
        levanta=("telemetria de emulacion que demuestre que en el camino de "
                 "render queda algo. Hoy es el 1,27 % del tiempo (A7)."),
    ),
    Filosofia(
        clave="mover_menos",
        nombre="B - Mover menos datos",
        lema="El bus es un recurso, igual que el reloj.",
        metrica="upload",
        encargo=("Un fotograma de 704x512 a 16 bits son ~700 KB por el bus, 60 "
                 "veces por segundo. Sube solo el rectangulo sucio, o mapea la "
                 "memoria del rasterizador directamente como textura "
                 "(sceGxmMapMemory) y elimina la copia entera."),
        riesgo=("carreras entre el rasterizador y la GPU al compartir memoria; "
                "tearing si desaparece la doble memoria intermedia."),
        marcas=("upload", "bus", "transferencia", "textura", "copia",
                "scegxmmapmemory", "rectangulo sucio", "mapear", "memcpy",
                "ancho de banda", "doble bufer"),
        suspendida_por="R6",
        levanta="lo mismo que A: R6 cubre composite, upload y display por igual.",
    ),
    Filosofia(
        clave="repartir_mejor",
        nombre="C - Repartir mejor entre nucleos",
        lema="La Vita tiene tres nucleos utilizables y el juego usa uno y medio.",
        metrica="dropped",
        encargo=("Hoy hay un hilo de render en el nucleo 1 y el audio en otro. "
                 "Si dropped es alto, el render no da abasto: mover el "
                 "composite al hilo de render, o partirlo en bandas "
                 "horizontales entre dos nucleos."),
        riesgo=("el reparto que va bien en un juego va mal en otro. Es la "
                "categoria donde mas importa medir con los tres juegos."),
        marcas=("dropped", "nucleo", "core", "hilo", "thread", "reparto",
                "banda", "paraleliz", "afinidad", "planific", "scheduler"),
        # No es R6: es que su metrica NO SE IMPRIME. Una filosofia cuyo
        # contador no sale por el log no puede ganar ni perder (A9).
        suspendida_por="A9",
        levanta=("exponer drawn/presented/dropped en el log. vidgpu.c ya los "
                 "lleva; esta build no los imprime."),
    ),
)


# ------------------------------------------------------------------ reglas

@dataclass(frozen=True)
class Regla:
    """Una regla de §5.2: lo que no hay que volver a intentar."""

    clave: str
    dice: str
    #: Todas las piezas tienen que aparecer para que haya choque. Un solo
    #: termino dispararia con cualquier mencion de pasada, y una regla que
    #: bloquea propuestas validas se desactiva sola a la tercera vez.
    exige: tuple[tuple[str, ...], ...]

    def choca(self, texto: str) -> bool:
        t = _plano(texto)
        return all(any(re.search(v, t) for v in grupo) for grupo in self.exige)


REGLAS: tuple[Regla, ...] = (
    Regla(
        clave="R1",
        dice="No proponer un JIT nuevo de SH-2. Ya existe SH2DynARM.",
        exige=((r"\bjit\b", r"dynarec", r"recompilador"),
               (r"\bnuevo\b", r"\bnueva\b", r"escribir", r"implementar",
                r"desde cero", r"\bpropio\b")),
    ),
    Regla(
        clave="R6",
        dice=("No proponer optimizaciones del camino de render (composite, "
              "upload, display) hasta que exista telemetria de emulacion que "
              "demuestre que ahi queda algo. Es el 1,27 % del tiempo."),
        exige=((r"composite", r"\bupload\b", r"\bdisplay\b"),
               (r"optimiz", r"acelera", r"reduc", r"eliminar", r"recort",
                r"\bbaja\b", r"\bbajar\b", r"mejora")),
    ),
    Regla(
        clave="R14",
        dice=("No volver a sospechar del disco de NiGHTS: llega byte-perfecto "
              "y su region es valida."),
        exige=((r"nights",),
               (r"disco", r"\bchd\b", r"volcado"),
               (r"corrupt", r"da(?:n|nn)ad", r"mal volcad",
                r"region equivocada", r"region incorrecta")),
    ),
    Regla(
        clave="R15",
        dice=("La palanca no es cambiar de interprete: SH2Fast y SH2LRU dan lo "
              "mismo. Es el coste por instruccion."),
        exige=((r"sh2fast", r"sh2lru", r"interprete"),
               (r"cambiar", r"sustituir", r"reemplazar", r"pasar a",
                r"en vez de")),
    ),
)


def choques(texto: str) -> list[Regla]:
    """Que reglas de §5.2 rompe esta propuesta. Vacio = ninguna."""
    return [r for r in REGLAS if r.choca(texto)]


# ------------------------------------------------------- ¿aplica el reparto?

#: El reparto por filosofias es para rondas de OPTIMIZACION del emulador. No
#: para «arregla el arranque de NiGHTS» ni para nada fuera del emulador: pedir
#: tres ataques ortogonales a un encargo que no es de rendimiento produce dos
#: variantes forzadas y una buena.
_RE_OPTIMIZA = re.compile(
    r"\b(optimiz\w*|acelera\w*|rendimiento|fps|mas rapido|velocidad|"
    r"cuello|profil\w*)\b")
_RE_EMULADOR = re.compile(
    r"\b(yabause\w*|saturn|vita3k|vita|emulador|emulacion)\b")


def pertinente(encargo: str) -> bool:
    """
    ¿Esta ronda se reparte en filosofias ortogonales?

    Se le pasa el encargo DEL USUARIO, no el prompt ya montado. El montado
    lleva la bitacora inyectada, y la bitacora habla de optimizar el emulador
    en casi cada linea: con ella dentro esto diria que si SIEMPRE, y todas las
    tareas -- escribir un parser, arreglar un test -- se repartirian en tres
    ataques al camino de render.
    """
    t = _plano(encargo)
    return bool(_RE_OPTIMIZA.search(t) and _RE_EMULADOR.search(t))


def asignada(variante: int) -> Filosofia:
    """Que filosofia le toca a la variante n. Ciclo, no azar."""
    return FILOSOFIAS[variante % len(FILOSOFIAS)]


def para_la_variante(variante: int) -> str:
    """El fragmento que convierte a esta variante en SU filosofia."""
    f = asignada(variante)
    partes = [
        f"\n\n---\n**TU FILOSOFIA EN ESTA RONDA: {f.nombre}**",
        f"> *{f.lema}*",
        f"\nAtacas la metrica `{f.metrica}`. {f.encargo}",
        f"\n**Riesgo caracteristico de esta familia:** {f.riesgo}",
        ("\nEsta es UNA de tres propuestas ortogonales por construccion. Las "
         "otras dos atacan mecanismos distintos, asi que no intentes cubrirlo "
         "todo: si las tres apuntan al mismo sitio, la comparacion no "
         "distingue nada y la ronda se gasta midiendo una sola idea."),
        (f"\n**OBLIGATORIO - declara las dos cosas:** a que filosofia "
         f"perteneces ({f.nombre}) y tu prediccion falsable sobre "
         f"`{f.metrica}` con un numero (por ejemplo «`{f.metrica}` baja "
         f">= 15 %»). Una propuesta sin prediccion falsable no puede perder, "
         f"y lo que no puede perder no compite."),
    ]
    if f.suspendida_por:
        partes.append(
            f"\n\n**AVISO - esta filosofia esta SUSPENDIDA por "
            f"{f.suspendida_por}.** Se levantaria con: {f.levanta} "
            f"Si tu propuesta cae dentro de lo que {f.suspendida_por} prohibe, "
            f"dilo y NO la desarrolles: se rechazaria sin llegar a compilar "
            f"(§6), y compilar un .vpk y correrlo verificado cuesta un ciclo "
            f"entero. Propon en su lugar lo que haria falta para levantar la "
            f"suspension, que es trabajo util y si se puede hacer.")
    return "\n".join(partes)


# ------------------------------------------------------------ clasificacion

def clasificar(texto: str) -> Filosofia | None:
    """
    A que filosofia pertenece de verdad un texto, por su vocabulario.

    Devuelve None si no hay una ganadora clara - empate o silencio. None es un
    resultado de primera clase: forzar una etiqueta sobre un texto que no la
    tiene es justo lo que haria creer que el reparto funciono.
    """
    t = _plano(texto)
    puntos = {f.clave: sum(t.count(m) for m in f.marcas) for f in FILOSOFIAS}
    mejor = max(puntos.values(), default=0)
    if mejor == 0:
        return None
    ganadoras = [f for f in FILOSOFIAS if puntos[f.clave] == mejor]
    return ganadoras[0] if len(ganadoras) == 1 else None


@dataclass
class Reparto:
    """El veredicto de ortogonalidad de una tanda de variantes."""

    #: clave de filosofia -> indices de las variantes que cayeron ahi
    por_filosofia: dict[str, list[int]] = field(default_factory=dict)
    #: variantes que no se pudieron clasificar
    sin_clasificar: list[int] = field(default_factory=list)
    total: int = 0

    @property
    def cubiertas(self) -> int:
        return len(self.por_filosofia)

    @property
    def colapsadas(self) -> list[str]:
        """Filosofias con mas de una variante: ahi se perdio la ortogonalidad."""
        return sorted(k for k, v in self.por_filosofia.items() if len(v) > 1)

    @property
    def ok(self) -> bool:
        """
        Ortogonal = cada variante en una filosofia distinta, y todas
        clasificadas. Con una sola variante no hay nada que repartir, asi que
        es trivialmente cierto.
        """
        if self.total <= 1:
            return True
        return not self.sin_clasificar and self.cubiertas == self.total

    def render(self) -> str:
        if self.ok:
            return (f"Reparto ortogonal: {self.cubiertas} filosofias distintas "
                    f"en {self.total} variantes.")
        motivos = []
        if self.colapsadas:
            nombres = {f.clave: f.nombre for f in FILOSOFIAS}
            for k in self.colapsadas:
                cuales = ", ".join(str(i) for i in self.por_filosofia[k])
                motivos.append(
                    f"las variantes {cuales} atacan lo mismo ({nombres[k]})")
        if self.sin_clasificar:
            cuales = ", ".join(str(i) for i in self.sin_clasificar)
            motivos.append(
                f"las variantes {cuales} no declaran mecanismo reconocible")
        return ("Reparto NO ortogonal - " + "; ".join(motivos) +
                ". La comparacion de esta ronda no distingue entre ellas.")


def revisar(textos: list[str]) -> Reparto:
    """Mira lo que las variantes hicieron DE VERDAD, no lo que se les pidio."""
    r = Reparto(total=len(textos))
    for i, texto in enumerate(textos):
        f = clasificar(texto)
        if f is None:
            r.sin_clasificar.append(i)
        else:
            r.por_filosofia.setdefault(f.clave, []).append(i)
    return r
