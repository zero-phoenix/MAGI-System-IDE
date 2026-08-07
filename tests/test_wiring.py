"""
Auditoría de cableado automatizada.

POR QUÉ EXISTE
==============
Tres veces en esta reconstrucción he escrito la pieza correcta, con sus tests
unitarios en verde, y NO la he conectado:

  1. ProviderRegistry.select_for_swarm() — el enjambre nunca la llamaba.
  2. VerifiedRepair — naoko.py seguía ejecutando el script a ciegas.
  3. run_agent (el bucle de herramientas) — solo lo usaba Naoko; los tres nodos
     del enjambre seguían sin poder abrir un fichero. Y classify() (el
     enrutamiento adaptativo) no se llamaba desde ningún sitio: toda petición
     seguía pagando el debate completo.

Los tests unitarios pasaban en los tres casos. El fallo no estaba en la pieza:
estaba en que nadie la usaba.

Este fichero comprueba el GRAFO DE LLAMADAS con AST. No mira si una función
funciona — mira si el sistema la invoca.
"""
import ast
import pathlib
from collections import defaultdict

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Módulos que son andamiaje conocido (no alcanzables desde main.py). Llamar a
# algo solo desde aquí NO cuenta como estar conectado.
#
# Esta lista se DECLARA a mano y se VERIFICA contra la realidad más abajo
# (test_attic_list_matches_reality / test_every_module_dir_is_declared), en las
# dos direcciones, porque equivocarse en cualquiera de ellas rompe la auditoría
# entera y en silencio:
#
#   · Un directorio VIVO metido en la lista produce falsos NEGATIVOS: se
#     excluye del grafo y sus llamadas dejan de contar. Pasó con `studio` al
#     construirse la fábrica de artefactos (§5): compose_page salía como no
#     conectado estándolo.
#   · Un directorio MUERTO fuera de la lista produce falsos POSITIVOS: entra en
#     el grafo, y una pieza que solo se llama desde ahí parece cableada sin
#     estarlo. Pasó con `logic` y `prompts`, andamiaje de v5.0.28 que nadie
#     importa (SymbolicVerifier quedó sustituido por ProposalVerifier §2.5, y
#     hay dos clases distintas llamadas PromptCompiler que no usa nadie).
#
# La segunda dirección es la peligrosa: es exactamente el fallo que este
# fichero existe para cazar, escondido en el propio instrumento de medida.
ATTIC_DIRS = {
    "_attic", "execution", "capabilities", "debate", "invention", "reasoning",
    "fabrication", "device", "ingest", "os_portable", "logic", "prompts",
    "vision", "gui", "web", "shell", "project", "config",
}


def _call_graph() -> dict[str, set[str]]:
    calls: dict[str, set[str]] = defaultdict(set)
    for f in (ROOT / "magi").rglob("*.py"):
        # `as_posix()`, no `str()`. En Windows `str(Path)` da
        # 'magi\\core\\kernel.py' y la tabla WIRING dice 'magi/core/kernel.py',
        # así que las 31 comprobaciones de cableado fallaban en Windows por el
        # separador. Y lo grave no era eso: el filtro de ATTIC_DIRS de la línea
        # siguiente busca '/attic/', que nunca casaba, de modo que en Windows
        # el grafo de llamadas INCLUÍA el código del ático. Un símbolo que solo
        # se invoca desde código muerto habría pasado por cableado real.
        rel = f.relative_to(ROOT).as_posix()
        if any(f"/{d}/" in rel or rel.startswith(f"magi/{d}/") for d in ATTIC_DIRS):
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                name = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
                if name:
                    calls[name].add(rel)
    return calls


CALL_GRAPH = _call_graph()


def _callers(name: str) -> set[str]:
    return CALL_GRAPH.get(name, set())


# ---------------------------------------------------------- alcanzabilidad real

def _module_name(path: pathlib.Path) -> str:
    parts = list(path.relative_to(ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _magi_imports(path: pathlib.Path) -> set[str]:
    """Imports de `magi.*` de un fichero, resolviendo los relativos."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return set()
    mod = _module_name(path)
    pkg = mod if path.name == "__init__.py" else mod.rpartition(".")[0]

    out: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            if n.level:
                base = pkg.split(".")
                base = base[: len(base) - (n.level - 1)] if n.level > 1 else base
                target = ".".join(base + ([n.module] if n.module else []))
            else:
                target = n.module or ""
            out.add(target)
            # `from x import y`: y puede ser un submódulo, no un símbolo.
            out.update(f"{target}.{a.name}" for a in n.names)
    return {m for m in out if m.startswith("magi")}


def _reachable_modules() -> set[str]:
    """
    Cierre transitivo de imports desde `magi/main.py`.

    Es la definición operativa de "el sistema usa esto": si un módulo no
    aparece aquí, arrancar MAGI nunca ejecuta una línea suya.
    """
    files = {_module_name(f): f for f in (ROOT / "magi").rglob("*.py")}
    seen: set[str] = set()
    pending = ["magi.main"]
    while pending:
        mod = pending.pop()
        if mod in seen:
            continue
        seen.add(mod)
        f = files.get(mod)
        if f is None:
            continue
        for imp in _magi_imports(f):
            for cand in (imp, imp.rpartition(".")[0]):
                if cand in files and cand not in seen:
                    pending.append(cand)
    return seen


REACHABLE = _reachable_modules()


def _dir_is_reachable(d: str) -> bool:
    prefix = f"magi.modules.{d}"
    return any(m == prefix or m.startswith(prefix + ".") for m in REACHABLE)


def _module_dirs() -> list[str]:
    return sorted(p.name for p in (ROOT / "magi/modules").iterdir()
                  if p.is_dir() and any(p.rglob("*.py")))


# Cada pieza del plan con el fichero desde el que DEBE invocarse.
WIRING = [
    ("classify",            "magi/core/kernel.py",                  "§2.3 enrutamiento adaptativo"),
    ("run_agent",           "magi/modules/swarm/agents.py",         "§2.2 bucle de herramientas en el enjambre"),
    ("registry_for_role",   "magi/modules/swarm/agents.py",         "§2.2 perfiles de herramientas por rol"),
    ("_ask_with_tools",     "magi/modules/swarm/agents.py",         "§2.2 nodos que actúan"),
    ("generate_variants",   "magi/modules/swarm/orchestrator.py",   "§2.4 propuestas en paralelo"),
    ("critique_multi_axis", "magi/modules/swarm/orchestrator.py",   "§2.4 crítica multi-eje"),
    ("memory_for",          "magi/modules/swarm/orchestrator.py",   "§2.6 memoria episódica"),
    ("style_fragment",      "magi/modules/swarm/agents.py",         "§2.7 estilo narrativo"),
    ("VerifiedRepair",      "magi/modules/infrastructure/naoko.py", "§3.1 reparación verificada"),
    ("MetricsCollector",    "magi/core/kernel.py",                  "§3.4 colector de métricas"),
    ("attach",              "magi/core/kernel.py",                  "§3.4 enganche al bus"),
    ("record_provider",     "magi/core/providers/registry.py",      "§3.4 el registro mide"),
    ("health_summary",      "magi/modules/infrastructure/naoko.py", "§3.4 salud en el prompt de Naoko"),
    ("canary_probe",        "magi/modules/infrastructure/naoko.py", "§3.4 sonda de deriva"),
    ("default_bench",       "magi/modules/infrastructure/naoko.py", "§3.5 banco de evaluación"),
    ("run_self_improvement","magi/core/kernel.py",                  "§3.5 auto-mejora invocable"),
    ("register_reverse_tools", "magi/core/tools/builtin.py",        "§5.3 toolchain de RE en el enjambre"),
    ("register_studio_tools",  "magi/core/tools/builtin.py",        "§5 fábrica de artefactos en el enjambre"),
    ("index_source_tree",      "magi/modules/reverse/tools.py",     "§5.3 indexado de corpus de emuladores"),
    ("compare_corpora",        "magi/modules/reverse/tools.py",     "§5.3 contraste de código real"),
    ("compose_page",           "magi/modules/studio/tools.py",      "§5.4 composición de manga"),
    ("domains_for",            "magi/core/tools/builtin.py",        "§2.2 catálogo acotado por dominio"),
    ("register_world_tools",   "magi/core/tools/builtin.py",        "§6 conocimiento del mundo en el enjambre"),
    ("fred_series",            "magi/modules/world/tools.py",       "§6.2 macro desde FRED"),
    ("compare_countries",      "magi/modules/world/tools.py",       "§6.2 contraste entre países"),
    ("headlines",              "magi/modules/world/tools.py",       "§6.1 actualidad por RSS"),
    ("fundamentals",           "magi/modules/world/tools.py",       "§6.3 fundamentales de EDGAR"),
    ("owner_earnings",         "magi/modules/world/tools.py",       "§6.3 ganancias del propietario"),
    ("dcf_sensitivity",        "magi/modules/world/tools.py",       "§6.3 DCF con sensibilidad"),
    ("quality_checklist",      "magi/modules/world/tools.py",       "§6.3 rúbrica de calidad"),
    ("ThesisLog",              "magi/modules/world/tools.py",       "§6.3 registro de tesis calibrado"),
]


@pytest.mark.parametrize("symbol,expected_caller,section", WIRING,
                         ids=[w[2] for w in WIRING])
def test_piece_is_actually_invoked(symbol, expected_caller, section):
    callers = _callers(symbol)
    assert callers, f"{section}: '{symbol}' no se llama desde NINGÚN sitio (andamiaje)"
    assert expected_caller in callers, (
        f"{section}: '{symbol}' existe pero {expected_caller} no lo invoca. "
        f"Solo lo llaman: {sorted(callers)}")


def test_proposal_verifier_is_invoked():
    """ProposalVerifier se instancia; se comprueba por nombre de clase."""
    src = (ROOT / "magi/modules/swarm/orchestrator.py").read_text(encoding="utf-8")
    assert "ProposalVerifier(" in src, "§2.5 verificación ejecutable sin conectar"


def test_swarm_agents_can_reach_the_tools():
    """
    Comprobación de contrato: los tres nodos declaran perfil de herramientas y
    tienen el método que las usa.
    """
    from magi.modules.swarm.agents import (
        MelchiorAgent, BalthasarAgent, CasperAgent, SwarmAgentBase)

    assert hasattr(SwarmAgentBase, "_ask_with_tools")
    roles = {MelchiorAgent.tool_role, BalthasarAgent.tool_role, CasperAgent.tool_role}
    assert roles == {"MELCHIOR", "BALTHASAR", "CASPER"}, (
        f"perfiles de herramientas mal asignados: {roles}")


def test_role_profiles_differ_in_capability():
    """El reparto de herramientas debe ser real, no tres veces el mismo."""
    from magi.core.tools import registry_for_role
    m = set(registry_for_role("MELCHIOR").names())
    b = set(registry_for_role("BALTHASAR").names())
    c = set(registry_for_role("CASPER").names())

    assert "write_file" in m and "write_file" not in b and "write_file" not in c
    assert "run_command" in b, "Balthasar debe poder ejecutar para aportar evidencia"
    assert m != b != c


def test_no_dead_parameters_in_the_swarm_path():
    """
    Un parámetro que se acepta y no se usa es la misma clase de mentira que un
    <select> que no envía su valor. use_tools debe llegar hasta el despacho.
    """
    agents = (ROOT / "magi/modules/swarm/agents.py").read_text(encoding="utf-8")
    parallel = (ROOT / "magi/modules/swarm/parallel.py").read_text(encoding="utf-8")
    orch = (ROOT / "magi/modules/swarm/orchestrator.py").read_text(encoding="utf-8")

    assert "if use_tools:" in agents, "agents.py acepta use_tools sin despacharlo"
    assert "use_tools and axis in _AXES_WITH_TOOLS" in parallel, \
        "parallel.py acepta use_tools sin usarlo"
    assert "use_tools=use_tools" in orch, "el orquestador no propaga use_tools"


def test_route_controls_round_budget():
    """El tope de rondas debe venir de la ruta, no ser un 3 fijo."""
    src = (ROOT / "magi/modules/swarm/orchestrator.py").read_text(encoding="utf-8")
    assert 'state.get("max_rounds", 3)' in src
    assert "current_round >= 3" not in src, "el tope de 3 rondas sigue fijo"


def test_attic_list_matches_reality():
    """
    Guarda sobre la propia auditoría, dirección 1: un directorio declarado
    andamiaje que en realidad está conectado.

    Se excluye del grafo de llamadas, así que sus invocaciones dejan de contar
    y las piezas que solo él usa salen como no cableadas. Falsos negativos.
    Me pasó con `studio`.
    """
    vivos = sorted(d for d in ATTIC_DIRS if _dir_is_reachable(d))
    assert not vivos, (
        f"{vivos} están en ATTIC_DIRS pero main.py los alcanza por imports: "
        f"la lista está desactualizada y la auditoría da falsos negativos")


def test_every_module_dir_is_declared():
    """
    Guarda sobre la propia auditoría, dirección 2: un directorio muerto que
    NADIE declaró como andamiaje.

    Entra en el grafo de llamadas, y entonces una pieza invocada únicamente
    desde ese código muerto parece conectada. Falsos positivos — que son peores,
    porque el test se pone verde y deja de mirar.

    Me pasó con `logic` y `prompts`.
    """
    huerfanos = [d for d in _module_dirs()
                 if d not in ATTIC_DIRS and not _dir_is_reachable(d)]
    assert not huerfanos, (
        f"{huerfanos} no se alcanzan desde main.py y no están en ATTIC_DIRS. "
        f"Conéctalos o decláralos andamiaje; mientras tanto sus llamadas "
        f"falsean el grafo")


def test_attic_dirs_all_exist():
    """
    Tercera forma de mentir: excluir un directorio que ya no existe. No rompe
    nada, pero convierte la lista en folclore y esconde las dos entradas que sí
    importan. `quant` llegó a estar aquí siendo un directorio vacío.
    """
    fantasmas = sorted(d for d in ATTIC_DIRS
                       if d != "_attic" and not (ROOT / "magi/modules" / d).is_dir())
    assert not fantasmas, f"ATTIC_DIRS nombra directorios inexistentes: {fantasmas}"


def test_reachability_finds_the_real_system():
    """
    Cordura sobre el propio instrumento: si el BFS de imports se rompiera
    (typo al resolver relativos, por ejemplo) devolvería un conjunto minúsculo
    y los dos tests de arriba se pondrían verdes por vacuidad.
    """
    assert len(REACHABLE) > 40, f"solo {len(REACHABLE)} módulos alcanzables: el BFS está roto"
    for esperado in ("magi.core.kernel", "magi.modules.swarm.orchestrator",
                     "magi.core.tools.builtin", "magi.modules.studio.tools"):
        assert esperado in REACHABLE, f"{esperado} debería ser alcanzable"


def test_kernel_publishes_the_routing_decision():
    """La GUI debe poder mostrar por qué ruta fue una petición."""
    src = (ROOT / "magi/core/kernel.py").read_text(encoding="utf-8")
    assert "swarm.routed" in src


def test_final_resolution_declares_every_parameter_it_uses():
    """
    Regresión: generate_final_resolution usaba `use_tools` sin declararlo en la
    firma. NameError justo en la respuesta final que ve el usuario tras aprobar
    — el punto más visible de todo el flujo. Lo cazó el linter, no un test.
    """
    import ast
    import inspect
    from magi.modules.swarm.agents import CasperAgent

    for fn in (CasperAgent.generate_final_resolution, CasperAgent.arbitrate):
        tree = ast.parse(inspect.getsource(fn).lstrip())
        func = tree.body[0]
        declared = {a.arg for a in func.args.args} | \
                   {a.arg for a in func.args.kwonlyargs}
        assigned = {n.id for n in ast.walk(func)
                    if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
        used = {n.id for n in ast.walk(func)
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
        import builtins
        unknown = used - declared - assigned - set(dir(builtins)) - {
            "self", "logger", "BusEvent", "json", "asyncio", "re"}
        assert not unknown, f"{fn.__name__} usa nombres no declarados: {unknown}"


# ------------------------------------------------------- §6 conocimiento del mundo

def test_world_tools_estan_en_el_catalogo():
    """Sin esto, todo magi/modules/world/ sería andamiaje bien probado."""
    from magi.core.tools import build_registry
    from magi.core.tools.builtin import WORLD_TOOLS
    nombres = set(build_registry().names())
    faltan = WORLD_TOOLS - nombres
    assert not faltan, f"herramientas del mundo sin registrar: {sorted(faltan)}"


def test_el_dominio_del_mundo_se_activa_con_lenguaje_real():
    """
    Las pistas tienen que cubrir cómo se pregunta de verdad, no el vocabulario
    que a mí me salió al escribir la lista.
    """
    from magi.core.tools.builtin import domains_for
    for frase in ("analiza los fundamentales de Apple",
                  "¿cómo está la inflación en Europa?",
                  "compara el gasto militar de España y Francia",
                  "haz una valoración por descuento de flujos",
                  "¿qué haría Buffett con esta empresa?",
                  "registra esta tesis sobre los tipos de interés"):
        assert "world" in domains_for(frase), f"no detectado: {frase!r}"


def test_una_tarea_de_emuladores_no_carga_las_finanzas():
    """El motivo de existir del acotado por dominio (§2.2)."""
    from magi.core.tools import registry_for_role
    from magi.core.tools.builtin import REVERSE_TOOLS, WORLD_TOOLS
    nombres = set(registry_for_role(
        "MELCHIOR", task_hint="portar el dynarec de PPSSPP a Vita").names())
    assert REVERSE_TOOLS <= nombres
    assert not (WORLD_TOOLS & nombres), "el catálogo de finanzas sobra aquí"


def test_sin_pista_se_ofrecen_todos_los_dominios():
    """
    Regresión: los dominios estaban escritos a mano como {"core","reverse",
    "studio"} en dos sitios. Al añadir 'world' esa rama dejó de significar
    "todos" y empezó a recortar el catálogo en silencio.
    """
    from magi.core.tools import registry_for_role
    from magi.core.tools.builtin import (
        ALL_DOMAINS, REVERSE_TOOLS, STUDIO_TOOLS, WORLD_TOOLS, domains_for)
    assert domains_for("") == ALL_DOMAINS
    nombres = set(registry_for_role("MELCHIOR").names())
    for conjunto in (REVERSE_TOOLS, STUDIO_TOOLS, WORLD_TOOLS):
        assert conjunto <= nombres, "sin pista no debe recortarse el catálogo"


def test_cada_dominio_declarado_tiene_su_conjunto_de_herramientas():
    """
    Guarda contra la misma clase de desincronización: un dominio con pistas
    pero sin herramientas se activaría y no añadiría nada, y el síntoma sería
    un agente sin capacidades y ningún error.
    """
    from magi.core.tools.builtin import _DOMAIN_HINTS, _DOMAIN_TOOLSETS
    assert set(_DOMAIN_HINTS) == set(_DOMAIN_TOOLSETS), (
        "pistas y conjuntos de herramientas desalineados: "
        f"{set(_DOMAIN_HINTS) ^ set(_DOMAIN_TOOLSETS)}")


def test_el_simulador_aleatorio_sigue_desconectado():
    """
    §6.3: "el simulator.py actual se borra o se reescribe — un
    np.random.randint presentado como índice risk-off es peor que no tener
    nada, porque parece un análisis". Está en el desván; que no vuelva.
    """
    for m in REACHABLE:
        assert "quant_simulator" not in m and "quantum_oracle" not in m, (
            f"{m} volvió a ser alcanzable: el generador de números con "
            f"vocabulario financiero no puede estar conectado")


def test_nadie_pide_el_catalogo_sin_acotar():
    """
    Guarda sobre el acotado por dominio (§2.2).

    `registry_for_role(rol)` sin `task_hint` devuelve los cuatro dominios: hoy
    41 herramientas y 4,4 KB en el prompt, y creciendo con cada dominio nuevo.
    Naoko lo hacía y por eso su bucle de reparación cargaba el compositor de
    manga para arreglar un traceback.

    El síntoma es invisible —funciona, solo que peor y más caro— así que hace
    falta un test que lo mire.
    """
    import re
    ofensores = []
    for f in (ROOT / "magi").rglob("*.py"):
        rel = str(f.relative_to(ROOT))
        if any(rel.startswith(f"magi/{d}/") for d in ATTIC_DIRS):
            continue
        src = f.read_text(encoding="utf-8")
        for m in re.finditer(r"registry_for_role\(([^)]*)\)", src):
            args = m.group(1)
            if "task_hint" not in args and "def " not in args:
                linea = src[:m.start()].count("\n") + 1
                ofensores.append(f"{rel}:{linea}")
    assert not ofensores, (
        f"piden el catálogo entero sin pista de tarea: {ofensores}. "
        f"Pasa un task_hint para que se acote al dominio")


def test_todo_ArtifactKind_tiene_rama_en_observe():
    """
    §5.5. `ArtifactKind.VIDEO` existía en el enum y el schema de
    `observe_artifact` ofrecía "video", pero `observe()` no lo despachaba: un
    .mp4 caía en `observe_program` y se intentaba EJECUTAR como Python.

    Una capacidad anunciada y no conectada es peor que una que falta, porque
    nadie la busca. Este test recorre el enum entero para que no vuelva a
    pasar con el siguiente tipo que se añada.
    """
    import inspect
    from magi.modules.studio.artifacts import ArtifactKind, observe

    src = inspect.getsource(observe)
    sin_rama = [k.name for k in ArtifactKind
                if f"ArtifactKind.{k.name}" not in src]
    # PROGRAM es el caso por defecto: se despacha sin nombrarse.
    sin_rama = [k for k in sin_rama if k != "PROGRAM"]
    assert not sin_rama, (
        f"{sin_rama} están en ArtifactKind y observe() no los despacha: caen "
        f"en observe_program, que los EJECUTA")


def test_el_schema_de_observe_artifact_no_promete_de_mas():
    """
    El otro lado del mismo contrato: lo que el schema ofrece al agente tiene
    que existir en el enum. Ofrecer un valor inexistente hace que el agente lo
    use y reciba un error incomprensible.
    """
    from magi.core.tools import build_registry
    from magi.modules.studio.artifacts import ArtifactKind

    herramienta = build_registry().get("observe_artifact")
    props = herramienta.parameters["properties"]
    ofrecidos = set(props["kind"].get("enum", []))
    reales = {k.value for k in ArtifactKind}
    assert ofrecidos <= reales, (
        f"el schema ofrece tipos que no existen: {ofrecidos - reales}")


# ------------------------------------------------ huérfanos a nivel de MÓDULO

# Módulos que están dentro de un directorio VIVO pero que nadie alcanza desde
# main.py. Su código entra en el grafo de llamadas, así que una pieza invocada
# solo desde aquí PARECE cableada sin estarlo — la misma clase de falso
# positivo que ATTIC_DIRS evita a nivel de directorio.
#
# La auditoría era ciega a esto: comprobaba directorios y no módulos. Al
# mirarlo aparecieron 24, entre ellos `reverse/decompiler.py`, un mock que
# devolvía código C inventado y una hipótesis fabricada con "confidence: 0.85"
# dentro del módulo de ingeniería inversa. Eso ya está borrado.
#
# Esta lista es un TRINQUETE: puede encogerse, nunca crecer. Cada entrada es
# deuda declarada de v5.0.28, no permiso para añadir más.
KNOWN_ORPHANS = {
    "magi.core.agent", "magi.core.evolution", "magi.core.hive",
    "magi.core.membrane", "magi.core.octopus",
    "magi.core.providers.rate_limit", "magi.core.providers.selector",
    "magi.core.providers.wal",
    "magi.gui.server",
    "magi.modules.memgraph.knowledge_store",
    "magi.modules.memory.compression", "magi.modules.memory.handover",
    "magi.modules.memory.hyperdimensional", "magi.modules.memory.semantic",
    "magi.modules.route.providers", "magi.modules.route.providers.base",
    "magi.modules.route.providers.claude_cli",
    "magi.modules.route.providers.cloud_api",
    "magi.modules.studio.loop", "magi.modules.studio.rights",
    "magi.modules.studio.spec",
}


def _orphan_modules() -> set[str]:
    """Módulos de directorios vivos que no alcanza nadie desde main.py."""
    huerfanos = set()
    for f in (ROOT / "magi").rglob("*.py"):
        mod = _module_name(f)
        if mod in REACHABLE or "_attic" in mod:
            continue
        partes = mod.split(".")
        if len(partes) > 2 and partes[1] == "modules" and partes[2] in ATTIC_DIRS:
            continue
        huerfanos.add(mod)
    return huerfanos


def test_no_aparecen_huerfanos_nuevos():
    """
    Trinquete: la deuda de módulos no conectados puede bajar, nunca subir.

    Sin esto, cada fase nueva puede dejar un módulo escrito, probado y sin
    conectar sin que nada avise — que es literalmente el fallo que este
    fichero existe para impedir, y que se me escapó tres veces.
    """
    nuevos = _orphan_modules() - KNOWN_ORPHANS
    assert not nuevos, (
        f"módulos nuevos sin conectar: {sorted(nuevos)}. Conéctalos desde "
        f"código alcanzable o bórralos; no los añadas a KNOWN_ORPHANS")


def test_la_lista_de_huerfanos_no_se_queda_rancia():
    """
    La otra dirección, igual que con ATTIC_DIRS: un módulo que ya se conectó
    (o que se borró) y sigue en la lista la convierte en folclore, y esconde
    los que sí importan.
    """
    obsoletos = KNOWN_ORPHANS - _orphan_modules()
    assert not obsoletos, (
        f"ya no son huérfanos (conectados o borrados): {sorted(obsoletos)}. "
        f"Quítalos de KNOWN_ORPHANS")


def test_el_toolchain_de_re_no_tiene_mocks_que_inventen_analisis():
    """
    `reverse/decompiler.py` devolvía código C fijo y una hipótesis inventada
    con confianza 0.85, dentro del módulo de ingeniería inversa. Un análisis
    fabricado con aspecto de análisis es la misma familia que el
    `np.random.randint` presentado como índice de riesgo: peor que no tener
    nada, porque se parece a algo.
    """
    for nombre in ("decompiler", "differential", "triage"):
        assert not (ROOT / f"magi/modules/reverse/{nombre}.py").exists(), (
            f"reverse/{nombre}.py volvió: era andamiaje de v5.0.28")
    # La entropía de triage.py sí era útil y se reescribió conectada.
    assert (ROOT / "magi/modules/reverse/entropy.py").exists()


# ------------------------------------- capacidades alcanzables desde la interfaz

# Handlers RPC que NO necesitan botón: son saludos, alias o los usa el propio
# protocolo. Todo lo demás es una capacidad del sistema, y una capacidad que
# el usuario no puede invocar es una capacidad que no tiene.
RPC_SIN_INTERFAZ = {
    "rpc.hello",          # handshake
    "magi_connect",       # handshake
    "magi_estop",         # alias de KILL_ALL_PROCESSES
    "rpc.policy.check",   # lo usa el motor de políticas, no el usuario
    "task.running",       # consulta interna del panel de cancelación
}


def test_toda_capacidad_del_backend_se_puede_invocar_desde_la_interfaz():
    """
    Lo que se pidió al encargar esto: "que la interfaz tenga todas las
    implementaciones necesarias para aplicar todas las funcionalidades".

    Al auditarlo aparecieron TRES capacidades completas, probadas y
    enganchadas al bus que no tenían forma de invocarse:

        obs.metrics         panel de salud (§3.4)
        eval.run            banco de evaluación (§3.5)
        naoko.self_improve  auto-mejora medible (§3.5)

    La última es justo la que se pidió — "que haga perfectible al sistema" —
    así que era el peor sitio posible para dejar un cable suelto. El motor
    estaba hecho; faltaba el botón.
    """
    import re

    kernel = (ROOT / "magi/core/kernel.py").read_text(encoding="utf-8")
    handlers = set(re.findall(r'register_handler\("([^"]+)"', kernel))

    gui = ""
    for f in (ROOT / "magi-gui/src").rglob("*.ts*"):
        gui += f.read_text(encoding="utf-8")
    gui = re.sub(r"/\*.*?\*/|//[^\n]*", "", gui, flags=re.S)

    inalcanzables = sorted(
        h for h in handlers - RPC_SIN_INTERFAZ
        if f"'{h}'" not in gui and f'"{h}"' not in gui)
    assert not inalcanzables, (
        f"capacidades del backend sin forma de invocarlas desde la interfaz: "
        f"{inalcanzables}. Añade el botón o decláralas en RPC_SIN_INTERFAZ "
        f"con el motivo")


def test_la_lista_de_exentos_no_se_queda_rancia():
    """
    Misma disciplina que con ATTIC_DIRS y KNOWN_ORPHANS: una lista de
    excepciones que nombra cosas que ya no existen esconde las que sí
    importan.
    """
    import re
    kernel = (ROOT / "magi/core/kernel.py").read_text(encoding="utf-8")
    handlers = set(re.findall(r'register_handler\("([^"]+)"', kernel))
    fantasmas = sorted(RPC_SIN_INTERFAZ - handlers)
    assert not fantasmas, f"RPC_SIN_INTERFAZ nombra handlers inexistentes: {fantasmas}"


def test_la_paleta_alcanza_todas_las_pestañas():
    """
    §7.3. Una capacidad que hay que ir a buscar a la cuarta pestaña es, en la
    práctica, una capacidad que no se usa — versión suave del mismo problema
    que la pieza construida y no conectada.

    Las pestañas del catálogo se DERIVAN de la misma lista que pinta la barra:
    dos listas a mano se desincronizan, y el síntoma sería una pestaña que
    existe y a la que la paleta no llega.
    """
    from source_helpers import code_of
    app = code_of(ROOT / "magi-gui/src/App.tsx")
    assert "CommandPalette" in app
    assert "PESTAÑAS.map" in app, "el catálogo no se deriva de las pestañas"
    # La barra tiene que usar la misma constante, no una lista repetida.
    assert '{[...PESTAÑAS,' in app, "la barra de pestañas duplica la lista"


def test_las_acciones_de_la_paleta_existen():
    """Un id sin manejador es un comando que no hace nada al pulsarlo."""
    from source_helpers import code_of
    app = code_of(ROOT / "magi-gui/src/App.tsx")
    import re
    ids = set(re.findall(r'\{\s*id:\s*"([a-z]+)"', app))
    despacho = app[app.index("const ejecutarComando"):]
    despacho = despacho[:despacho.index("};")]
    for i in sorted(ids):
        assert f'"{i}"' in despacho, f"el comando '{i}' no tiene manejador"


#: Distribución en requirements.txt -> módulo que se importa, cuando no
#: coinciden. Sin esto, `pyyaml` parecería no instalado porque nadie escribe
#: `import pyyaml`.
_ALIAS_PAQUETE = {
    "pyyaml": "yaml",
    "pytest-asyncio": "pytest_asyncio",
    "pillow": "PIL",
    "python-docx": "docx",
    "scikit-learn": "sklearn",
    "pywebview": "webview",
}


def _modulos_que_el_runner_importa() -> dict[str, pathlib.Path]:
    """
    Todo módulo de `magi` que el runner acabará importando de verdad.

    Son dos raíces, no una: lo que alcanza `main.py` (arrancar el sistema) y
    lo que alcanzan los tests (correr la suite). Mirar el árbol entero daría
    falsos positivos —el desván importa `chardet`, `jinja2`, `ruamel` y
    `python-magic`, y da igual porque nadie lo importa—; mirar solo `main.py`
    dejaría fuera un módulo que solo usan los tests. Esta es la lista exacta
    de ficheros cuyo import duro puede tumbar la compilación.
    """
    files = {_module_name(f): f for f in (ROOT / "magi").rglob("*.py")}
    pendientes = ["magi.main"]
    for t in (ROOT / "tests").glob("*.py"):
        pendientes.extend(_magi_imports(t))

    vistos: set[str] = set()
    while pendientes:
        mod = pendientes.pop()
        for cand in (mod, mod.rpartition(".")[0]):
            if cand in files and cand not in vistos:
                vistos.add(cand)
                pendientes.extend(_magi_imports(files[cand]))
    return {m: files[m] for m in vistos}


def _paquetes_declarados() -> set[str]:
    """Los módulos importables que `requirements.txt` garantiza."""
    import re

    nombres: set[str] = set()
    for linea in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        linea = linea.split("#")[0].strip()
        if not linea:
            continue
        dist = re.split(r"[<>=!~\[; ]", linea)[0].strip().lower()
        if dist:
            nombres.add(dist)
            nombres.add(dist.replace("-", "_"))
            if dist in _ALIAS_PAQUETE:
                nombres.add(_ALIAS_PAQUETE[dist])
    return nombres


def _imports_de_nivel_superior(ruta):
    """
    Módulos importados ARRIBA y sin `try`.

    La distinción es deliberada y es la regla del proyecto: un import a nivel
    de módulo sin proteger declara una dependencia DURA —si falta, el módulo
    entero no se puede importar—. Uno dentro de `try/except ImportError`, o
    dentro de una función, declara una capacidad OPCIONAL. Como los nodos de
    un `try` no están en `arbol.body`, mirar solo el cuerpo distingue las dos
    cosas sin ninguna heurística.
    """
    import ast

    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for n in arbol.body:
        if isinstance(n, ast.Import):
            for a in n.names:
                yield n.lineno, a.name.split(".")[0]
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            yield n.lineno, n.module.split(".")[0]


def test_los_workflows_instalan_desde_requirements():
    """
    La lista de dependencias de CI se escribía a mano en dos ficheros y se
    quedó atrás dos veces: primero sin `websockets`, después sin `numpy`. Una
    lista duplicada a mano SIEMPRE se queda atrás; la única cura es que no
    haya lista. Los workflows instalan de `requirements.txt` y este test
    impide volver a la enumeración.
    """
    for wf in ("ci.yml", "release.yml"):
        texto = (ROOT / ".github/workflows" / wf).read_text(encoding="utf-8")
        assert "pip install -r requirements.txt" in texto, (
            f"{wf} tiene que instalar de requirements.txt, no enumerar "
            f"paquetes a mano: la enumeración se queda atrás y tumba el "
            f"release, que depende de los tests")


def test_requirements_cubre_todo_import_duro_del_sistema_y_de_la_suite():
    """
    LA GUARDA QUE FALTABA, y que costó dos compilaciones.

    Primera versión: `test_rpc_transport.py` importaba `websockets` arriba y
    los workflows instalaban cinco paquetes a mano. La recolección de pytest
    reventaba, el job de tests fallaba y, como el build del release lleva
    `needs: test`, NO se generaba el .exe.

    Segunda versión, que la primera guarda no cazaba porque solo miraba los
    tests: `magi/modules/skills/loader.py` importa `numpy` y `sklearn` arriba,
    el kernel lo importa, y ningún test los nombra. La suite entera se caía
    por una dependencia que ningún fichero de tests menciona. Por eso ahora se
    recorre también el código de producción: lo que rompe la suite no es lo
    que los tests importan, es lo que acaba importándose.

    Se encontró simulando el entorno del runner en un venv limpio. Leer los
    ficheros no lo habría encontrado nunca — cuarta regla del proyecto.
    """
    import sys

    declarados = _paquetes_declarados()
    propios = {"magi", "source_helpers", "conftest", "tests"}

    ficheros = sorted((ROOT / "tests").glob("*.py"))
    ficheros += sorted(_modulos_que_el_runner_importa().values())

    faltan: dict[str, set[str]] = {}
    for f in ficheros:
        for lineno, m in _imports_de_nivel_superior(f):
            if (m in sys.stdlib_module_names or m in declarados
                    or m in propios):
                continue
            faltan.setdefault(m, set()).add(
                f"{f.relative_to(ROOT)}:{lineno}")

    assert not faltan, (
        "estos módulos se importan a nivel de módulo SIN proteger y "
        "requirements.txt no los declara, así que el runner se caerá al "
        "importarlos (y sin tests verdes no hay .exe): "
        + "; ".join(f"{m} <- {', '.join(sorted(fs))}"
                    for m, fs in sorted(faltan.items()))
        + ". O lo añades a requirements.txt, o lo envuelves en "
          "try/except ImportError para declararlo opcional de verdad.")


def test_nadie_lanza_python_con_sys_executable():
    """
    EL FALLO QUE SOLO EXISTE EN EL BINARIO PUBLICADO.

    Dentro de un onefile de PyInstaller, `sys.executable` **es el propio
    .exe**, no un intérprete. Comprobado construyendo uno:

        sys.executable = /tmp/pyi-p/d/probe
        frozen = True

    Media docena de sitios lanzaban `[sys.executable, "-m", "pytest", ...]` o
    `"{sys.executable}" "juego.py"`. En desarrollo funciona, porque ahí
    `sys.executable` sí es python. En el .exe que la gente se descarga de
    Releases, cada una de esas llamadas RELANZA MAGI:

      · `run_test_suite` y `_local_build`, que es la puerta previa a publicar:
        `MAGI-IDE-v5.exe -m pytest` arranca otra GUI y otro servidor.
      · `observe_program`, `observe_game` y `capture_program`: el bucle de
        observación del §5 acababa mirando a MAGI en lugar del artefacto que
        se acababa de generar.

    Ninguno da error. Dan el resultado de otro programa, que es peor. Y
    ninguna de las cuatro reglas anteriores lo caza: el código está conectado,
    tiene tests, se invoca desde la interfaz y arranca — solo que arrancar en
    desarrollo no es arrancar congelado.

    `paths.python_executable()` es la única puerta permitida.
    """
    import ast

    permitidos = {"magi/core/paths.py"}
    culpables: list[str] = []

    for f in sorted((ROOT / "magi").rglob("*.py")):
        rel = str(f.relative_to(ROOT)).replace("\\", "/")
        if rel in permitidos or any(rel.startswith(f"magi/{d}/")
                                    for d in ATTIC_DIRS):
            continue
        try:
            arbol = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for n in ast.walk(arbol):
            # `sys.executable` en cualquier posición: en una lista de
            # argumentos, dentro de una f-string, da igual.
            if (isinstance(n, ast.Attribute) and n.attr == "executable"
                    and getattr(n.value, "id", None) == "sys"):
                culpables.append(f"{rel}:{n.lineno}")

    assert not culpables, (
        "`sys.executable` fuera de magi/core/paths.py: dentro del .exe es el "
        "propio .exe y lanzarlo relanza MAGI en vez de ejecutar Python. Usa "
        "`paths.python_executable()`, que devuelve None si no hay intérprete "
        "en vez de hacer algo raro en silencio. Sitios: " + ", ".join(culpables))


def test_python_executable_no_devuelve_el_propio_ejecutable_congelado(monkeypatch):
    """
    La otra mitad: que la puerta no caiga a `sys.executable` cuando no
    encuentra intérprete. Devolver el .exe «por si acaso» reintroduciría el
    fallo entero con una capa de indirección encima.
    """
    import shutil
    import sys as _sys

    import magi.core.paths as paths

    paths.python_executable.cache_clear()
    monkeypatch.setattr(paths, "is_frozen", lambda: True)
    monkeypatch.setattr(shutil, "which", lambda n: None)
    monkeypatch.setattr(_sys, "platform", "linux")
    try:
        assert paths.python_executable() is None
    finally:
        paths.python_executable.cache_clear()


def test_python_executable_descarta_el_alias_que_apunta_al_exe(monkeypatch):
    """
    Un `python` en el PATH que resuelva al propio binario —un alias, o el .exe
    renombrado— sería el mismo fallo colándose por la puerta buena.
    """
    import shutil
    import sys as _sys

    import magi.core.paths as paths

    paths.python_executable.cache_clear()
    monkeypatch.setattr(paths, "is_frozen", lambda: True)
    monkeypatch.setattr(shutil, "which", lambda n: _sys.executable)
    try:
        assert paths.python_executable() is None
    finally:
        paths.python_executable.cache_clear()
