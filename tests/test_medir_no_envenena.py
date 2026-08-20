"""
Medir la salud no puede enfermar al sistema — tercera vez (C13, B8).

La v5.5.1 ya corrigió esto una vez: el filtro antichatarra rechazaba las
respuestas cortas de los canarios y dejaba al sistema sin proveedores. Volvió
por otra puerta el 2026-08-20, en el encargo del ping pong:

    Deriva detectada en g4f-gpt:    solo 0/3 respuestas canarias correctas
    Deriva detectada en g4f-gemini: solo 0/3 respuestas canarias correctas
    Deriva detectada en g4f-llama:  solo 0/3 respuestas canarias correctas

Cuatro familias declaradas «a la deriva» mientras una tarea hacía 50 llamadas
contra esos mismos proveedores. Naoko medía su propia interferencia.
"""
from __future__ import annotations

from magi.core.bus import MagiBus
from magi.modules.infrastructure.naoko import NaokoAgent


class _SwarmFalso:
    def __init__(self, estados):
        self.active_tasks = {f"t{i}": {"status": e} for i, e in enumerate(estados)}


def _naoko(estados) -> NaokoAgent:
    return NaokoAgent(MagiBus(), db=None, swarm=_SwarmFalso(estados))


def test_con_una_tarea_en_vuelo_no_se_sondea():
    assert _naoko(["in_progress"])._hay_tareas_vivas() is True
    assert _naoko(["running", "completed"])._hay_tareas_vivas() is True


def test_con_todo_quieto_si_se_sondea():
    assert _naoko(["completed", "WAITING_USER_APPROVAL"])._hay_tareas_vivas() is False
    assert _naoko([])._hay_tareas_vivas() is False


def test_sin_orquestador_no_se_bloquea_la_vigilancia():
    """
    Naoko puede vivir sin enjambre. Si no puede preguntar, vigila: dejar de
    vigilar por no poder preguntar sería cambiar un falso positivo por un
    punto ciego, que es peor.
    """
    n = NaokoAgent(MagiBus(), db=None, swarm=None)
    assert n._hay_tareas_vivas() is False


async def test_cero_canarios_correctos_no_es_deriva(monkeypatch):
    """
    0/3 significa «no me contestaron», no «el modelo cambió».

    Deriva es que conteste BIEN y DISTINTO. Confundir las dos cosas es el
    error que este sistema ya pagó caro una vez.
    """
    from magi.core.obs import metrics

    class _Informe:
        drifted, matched, total = True, 0, 3

        def to_dict(self):
            return {"provider": "g4f-gpt", "matched": 0, "total": 3}

    class _Reg:
        id = "g4f-gpt"

    class _Registro:
        def healthy(self):
            return [_Reg()]

    async def falso_canario(registry, pid):
        return _Informe()

    async def falso_registro():
        return _Registro()

    monkeypatch.setattr(metrics, "canary_probe", falso_canario)
    import magi.core.providers.cloud as cloud
    monkeypatch.setattr(cloud, "get_registry", falso_registro)

    bus = MagiBus()
    dichos: list = []
    bus.subscribe("naoko.log", lambda e: dichos.append(e.payload))
    n = NaokoAgent(bus, db=None, swarm=_SwarmFalso([]))

    await n._check_drift()

    derivas = [d for d in dichos if "Deriva detectada" in str(d.get("content", ""))]
    assert not derivas, f"0/3 canarios no puede declararse deriva: {derivas}"
