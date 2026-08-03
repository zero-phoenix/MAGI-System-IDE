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
ATTIC_DIRS = {
    "_attic", "execution", "capabilities", "debate", "invention", "reasoning",
    "fabrication", "device", "ingest", "os_portable", "studio", "quant",
    "vision", "resilience", "gui", "web", "shell", "project", "config",
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
