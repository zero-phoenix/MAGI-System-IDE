"""
Paralelismo del enjambre (Plan MAGI 9.0 §2.4).

EL PROBLEMA
===========
orchestrator.py:142-161 encadenaba tres `await`: Melchior, luego Balthasar,
luego Casper. La latencia era siempre la suma de las tres, y con proveedores
gratuitos cada una tarda 10-30 s.

Balthasar necesita la propuesta de Melchior, así que esa dependencia es real.
Pero hay dos paralelismos que el grafo sí permite y que no se aprovechaban:

  1. VARIAS PROPUESTAS A LA VEZ. Melchior genera 2-3 enfoques distintos en
     paralelo (semillas y temperaturas distintas). Mismo tiempo de pared, mucha
     mejor exploración — y Balthasar puede compararlos, que es una crítica más
     útil que evaluar uno solo en el vacío.

  2. CRÍTICA MULTI-EJE. Balthasar evalúa seguridad, corrección, rendimiento y
     mantenibilidad como cuatro llamadas concurrentes que se funden en un
     informe. Deja de ser un párrafo genérico.
"""
from __future__ import annotations

import asyncio
import copy
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Ejes de crítica. Cada uno es una llamada corta y concurrente.
CRITIQUE_AXES: dict[str, str] = {
    "correccion": (
        "Evalúa SOLO la CORRECCIÓN: ¿hace lo que dice? ¿casos borde (entrada "
        "vacía, nulos, límites)? ¿errores de lógica off-by-one o de estado?"),
    "seguridad": (
        "Evalúa SOLO la SEGURIDAD y la REVERSIBILIDAD: ¿qué pasa si falla a "
        "mitad? ¿destruye datos sin poder deshacerse? ¿confía en entrada no "
        "validada? ¿ejecuta algo que no se puede parar?"),
    "plataforma": (
        "Evalúa SOLO los LÍMITES DE PLATAFORMA: ¿asume un sistema operativo "
        "distinto del que dice el contexto de ejecución? ¿rutas absolutas? "
        "¿dependencias que no están instaladas? ¿supone claves de API o "
        "modelos locales, que este proyecto no usa?"),
    "rendimiento": (
        "Evalúa SOLO el RENDIMIENTO: ¿complejidad innecesaria? ¿llamadas de "
        "red o disco en bucle? ¿bloquea el hilo asíncrono? ¿carga en memoria "
        "algo que puede ser enorme?"),
}


# Ejes donde ejecutar aporta evidencia real. Seguridad y rendimiento se razonan
# mejor leyendo que corriendo, y ahorran cuota.
_AXES_WITH_TOOLS = {"correccion", "plataforma"}


@dataclass
class Proposal:
    content: str
    variant: int
    provider: str = ""
    family: str = ""
    verified: bool = True
    verification: str = ""

    @property
    def label(self) -> str:
        return f"Enfoque {chr(ord('A') + self.variant)}"


@dataclass
class MultiCritique:
    by_axis: dict[str, str] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        titles = {"correccion": "Corrección", "seguridad": "Seguridad y reversibilidad",
                  "plataforma": "Límites de plataforma", "rendimiento": "Rendimiento"}
        parts = []
        for axis, text in self.by_axis.items():
            parts.append(f"### {titles.get(axis, axis.title())}\n{text.strip()}")
        for axis, err in self.errors.items():
            parts.append(f"### {titles.get(axis, axis)}\n_(no evaluado: {err})_")
        return "\n\n".join(parts)

    @property
    def axes_ok(self) -> int:
        return len(self.by_axis)


async def generate_variants(agent, *, task_id: str, command: str, round_num: int,
                            n: int = 2, engine: str = "fast",
                            narrative_style: str = "tecnico",
                            last_proposal=None, last_critique=None,
                            use_tools: bool = False) -> list[Proposal]:
    """
    N propuestas simultáneas del mismo agente, con semillas distintas.

    Coste en tiempo de pared: el de una sola (van en paralelo).
    Coste en cuota: N llamadas — por eso el valor por defecto es 2 y solo la
    ruta `build` sube a 3.
    """
    base_seed = agent.seed or 0

    async def one(variant: int) -> Proposal | None:
        # UNA COPIA POR VARIANTE, y esto arregla un fallo que llevaba aquí
        # desde el principio.
        #
        # El código anterior hacía `agent.seed = ...` sobre el agente
        # COMPARTIDO, con un `try/finally` para restaurarlo. Eso funciona en
        # secuencial, pero estas N variantes van por `asyncio.gather`: la
        # primera pone su semilla y en el primer `await` cede el control, la
        # segunda la pisa, la tercera también... y las tres acaban llamando
        # con la semilla de la última. Las «variantes con semillas distintas»
        # eran, medido, la misma petición repetida N veces.
        #
        # Con una copia superficial cada rama tiene su semilla y su identidad;
        # el blackboard, el bus y el cliente siguen compartidos, que es lo que
        # se quiere.
        mio = copy.copy(agent)
        mio.seed = base_seed + variant * 101
        # N variantes van EN PARALELO: la redundancia ya existe aquí. Pedir
        # además cobertura (hedge x3) por variante multiplica por 3 el coste —
        # medido en el log del 16-ago: ~50 llamadas HTTP para una petición.
        # El hedge queda solo para las llamadas únicas que no tienen quién las
        # cubra (arbitraje de Casper). Sin esto, un candidato lento no cuesta
        # una llamada, cuesta tres.
        mio.hedge = False
        # Identidad de la rama. Sin esto, las N variantes publican con el mismo
        # task_id y la interfaz no puede separarlas: las apila como si fueran
        # una conversación, cuando son N intentos paralelos del mismo agente.
        mio.rama = f"{task_id}/r{round_num}/melchior/v{variant}"
        mio.rama_rol = f"enfoque {chr(65 + variant)}"
        mio.rama_profundidad = 1
        try:
            # publicar=False: una variante es andamiaje para explorar, no una
            # intervención. Si cada una publicase, el usuario vería «MELCHIOR
            # propone» tres veces por ronda con tres análisis a medias. El
            # orquestador funde las variantes y publica UNA sola.
            result = await mio.generate_proposal(
                task_id, command, round_num, last_proposal, last_critique,
                engine, narrative_style, use_tools, publicar=False)
            return Proposal(content=result["content"], variant=variant,
                            provider=result.get("provider", ""),
                            family=result.get("family", mio.family))
        except Exception as e:
            logger.warning("[parallel] variante %d falló: %s", variant, e)
            return None

    results = await asyncio.gather(*(one(i) for i in range(n)),
                                   return_exceptions=True)
    out = [r for r in results if isinstance(r, Proposal)]
    if not out:
        raise RuntimeError("ninguna variante de propuesta se completó")
    logger.info("[parallel] %d/%d variantes completadas", len(out), n)
    return out


async def critique_multi_axis(agent, *, task_id: str, proposal_text: str,
                              round_num: int, engine: str = "fast",
                              narrative_style: str = "tecnico",
                              axes: list[str] | None = None,
                              evidence: str = "",
                              use_tools: bool = False) -> MultiCritique:
    """
    Los ejes de crítica van en paralelo y se funden.

    Una llamada corta y enfocada por eje produce críticas más concretas que una
    llamada larga que pide "critica esto" y devuelve generalidades.
    """
    selected = axes or list(CRITIQUE_AXES)
    result = MultiCritique()

    async def one(axis: str):
        # Copia por eje, por lo mismo que en las variantes: estos cuatro van
        # por `gather` y mutar el agente compartido los haría pisarse.
        mio = copy.copy(agent)
        # Igual que en las variantes: los ejes van en paralelo, la cobertura de
        # cada uno es el resto de ejes. Hedge apagado — se paga una vez, no x3.
        mio.hedge = False
        mio.rama = f"{task_id}/r{round_num}/balthasar/{axis}"
        mio.rama_rol = f"eje {axis}"
        mio.rama_profundidad = 1
        sys_prompt = (
            f"Eres BALTHASAR, auditor del sistema MAGI, en un pase enfocado.\n\n"
            f"{CRITIQUE_AXES[axis]}\n\n"
            f"Sé concreto: cita la línea o el fragmento exacto. Si en este eje "
            f"no hay defectos reales, dilo en una frase — inventar objeciones "
            f"para parecer riguroso es peor que aprobar.\n"
            f"Máximo 8 líneas. Sin preámbulo.")
        user = f"Propuesta a auditar:\n{proposal_text}"
        if evidence:
            user += f"\n{evidence}"
        try:
            if use_tools and axis in _AXES_WITH_TOOLS:
                # Los ejes de corrección y plataforma se benefician de EJECUTAR:
                # una objeción con el traceback delante vale mucho más que una
                # sospecha. Balthasar puede leer y ejecutar, no escribir.
                content, _, _ = await mio._ask_with_tools(
                    sys_prompt, user, task_id=task_id, engine=engine,
                    narrative_style=narrative_style, max_iters=6)
            else:
                content, _, _ = await mio._ask(
                    sys_prompt, user, engine=engine,
                    narrative_style=narrative_style)
            return axis, content, None
        except Exception as e:
            return axis, None, str(e)

    for axis, content, err in await asyncio.gather(*(one(a) for a in selected)):
        if content:
            result.by_axis[axis] = content
        else:
            result.errors[axis] = err or "sin respuesta"

    logger.info("[parallel] crítica multi-eje: %d/%d ejes",
                result.axes_ok, len(selected))
    return result


def format_variants_for_critic(proposals: list[Proposal]) -> str:
    """Presenta los enfoques para que Balthasar los compare en una sola pasada."""
    if len(proposals) == 1:
        return proposals[0].content
    parts = [f"Se han generado {len(proposals)} enfoques alternativos. "
             f"Compáralos y señala cuál es más sólido y por qué.\n"]
    for p in proposals:
        parts.append(f"===== {p.label} ({p.family}) =====")
        if not p.verified:
            parts.append(f"[NO PASA VERIFICACIÓN]\n{p.verification}")
        parts.append(p.content)
        parts.append("")
    return "\n".join(parts)
