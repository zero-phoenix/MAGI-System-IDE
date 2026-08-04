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
        rel = str(f.relative_to(ROOT))
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
