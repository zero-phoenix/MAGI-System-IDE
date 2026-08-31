"""
Las tres piezas de la réplica que `ronda()` usa por dentro.

`test_fase8_replica.py` prueba el flujo completo; esto prueba las piezas
sueltas, que es donde viven los modos de fallo que el flujo esconde:

  - si la réplica revienta, ¿se cae la ronda o se arbitra sin ella?
  - si el modelo se enrolla, ¿viaja acotada de verdad?
  - si la réplica pide parada de emergencia, ¿llega esa señal al orquestador?

El trinquete de huérfanos las señaló por no tener sitio de llamada fuera de
su módulo. La respuesta correcta no era esconderlas: era probarlas.
"""
import asyncio

import pytest

from magi.modules.swarm import replica as R

# ---------------------------------------------------------------- sombra

def test_la_sombra_esta_apagada_por_defecto(monkeypatch):
    """
    Es el interruptor de la compuerta de vida o muerte de la Fase 8: con la
    sombra encendida cada ronda paga un arbitraje extra. Encendida por
    defecto duplicaría el coste de todas las rondas en silencio.
    """
    monkeypatch.delenv("MAGI_REPLICA_SOMBRA", raising=False)
    assert R.sombra_activada() is False


@pytest.mark.parametrize("valor,esperado", [
    ("1", True), ("0", False), ("", False), ("true", False), ("si", False),
])
def test_la_sombra_solo_se_enciende_con_uno(monkeypatch, valor, esperado):
    """Estricto a propósito: un `true` que no enciende se nota; un valor
    ambiguo que enciende a medias, no."""
    monkeypatch.setenv("MAGI_REPLICA_SOMBRA", valor)
    assert R.sombra_activada() is esperado


# ---------------------------------------------------------- CierreDebate

def test_el_cierre_no_para_por_defecto():
    """
    `parar` es la parada de emergencia. Si por defecto fuera True, una ronda
    normal abortaría; si el campo no existiera, una parada pedida se
    ignoraría. Ambas son silenciosas, por eso se fija aquí.
    """
    c = R.CierreDebate(verdict={"decision": "APROBADA"}, evento={})
    assert c.parar is False
    assert c.texto == ""


def test_el_cierre_lleva_veredicto_y_evento():
    """El orquestador depende de los cuatro campos; si cambian, esto avisa."""
    c = R.CierreDebate(verdict={"decision": "RECHAZADA"},
                       evento={"replica": True}, texto="t", parar=True)
    assert c.verdict["decision"] == "RECHAZADA"
    assert c.evento["replica"] is True
    assert c.parar is True


# ------------------------------------------------- replica_de_melchior

class _AgenteFalso:
    """
    Lo mínimo que `replica_de_melchior` necesita: `_ask` y los campos que
    copia. No hereda del agente real a propósito — si la firma de `_ask`
    cambia, este test tiene que romperse.

    Detalle que costó tres tests rojos: la réplica hace `copy.copy(agent)` y
    muta la COPIA, no el agente del llamante. Eso está bien —no ensuciar el
    agente de quien llama es correcto—, así que el espía no puede mirar
    `self.rama` desde fuera: tiene que anotarlo en un dict compartido, y
    **mutándolo**, no reasignándolo (una copia superficial comparte el dict,
    pero reasignar lo desengancha).
    """

    def __init__(self, respuesta="", excepcion=None):
        self.respuesta = respuesta
        self.excepcion = excepcion
        self.hedge = True
        self.rama = ""
        self.rama_rol = ""
        self.rama_profundidad = 0
        self.visto = {}

    async def _ask(self, sys_prompt, user, engine=None, narrative_style=None):
        if self.excepcion:
            raise self.excepcion
        self.visto.update({
            "sys": sys_prompt, "user": user, "engine": engine,
            "estilo": narrative_style,
            # Se leen de `self`, que aquí es ya la copia mutada.
            "hedge": self.hedge, "rama": self.rama,
            "rama_rol": self.rama_rol, "profundidad": self.rama_profundidad,
        })
        return self.respuesta, None, None


def _replicar(agent, objeciones="objecion 1"):
    return asyncio.run(R.replica_de_melchior(
        agent, task_id="t", objeciones=objeciones, round_num=1))


def test_la_replica_devuelve_el_texto():
    a = _AgenteFalso("no procede, la linea 12 lo desmiente")
    assert "linea 12" in _replicar(a)


def test_si_la_replica_revienta_se_arbitra_sin_ella():
    """
    El modo de fallo que importa: un proveedor caído en la réplica NO puede
    tumbar la ronda. Devuelve cadena vacía y Casper arbitra como antes de
    que existiera la Fase 8.
    """
    a = _AgenteFalso(excepcion=RuntimeError("proveedor caido"))
    assert _replicar(a) == ""


def test_la_replica_viaja_acotada():
    """«Acotada» es la mitad del diseño: si el modelo se enrolla, se corta."""
    a = _AgenteFalso("x" * 5000)
    assert len(_replicar(a)) == R.TOPE_REPLICA_CHARS


def test_la_replica_no_paga_hedge():
    """
    El hedge duplica la llamada. En la réplica sería pagar dos veces por una
    vuelta que existe justo para ser barata.
    """
    a = _AgenteFalso("vale")
    _replicar(a)
    assert a.visto["hedge"] is False


def test_la_replica_ve_las_objeciones_y_no_la_propuesta():
    """
    Discute lo que hay sobre la mesa; no rehace la tesis. Si la propuesta
    entera viajara aquí, la réplica sería una segunda tesis — la escalera
    sin fin que el tope de una vuelta corta.
    """
    a = _AgenteFalso("ok")
    _replicar(a, objeciones="la funcion no valida la entrada")
    assert "no valida la entrada" in a.visto["user"]
    assert "UNA" in a.visto["sys"]      # se le dice que no habra otra vuelta


def test_la_replica_se_ramifica_aparte():
    """Su traza no se mezcla con la tesis: si no, no se puede auditar quién
    dijo qué en la telemetría."""
    a = _AgenteFalso("ok")
    _replicar(a)
    assert a.visto["rama"].endswith("/melchior/replica")
    assert a.visto["profundidad"] == 1


def test_no_ensucia_el_agente_del_llamante():
    """
    La réplica trabaja sobre una copia. Si mutara el agente real, Melchior
    quedaría con `hedge=False` y la rama de la réplica para el resto de la
    ronda — un efecto secundario invisible que se pagaría en la ronda
    siguiente.
    """
    a = _AgenteFalso("ok")
    _replicar(a)
    assert a.hedge is True, "la replica mutó el agente del llamante"
    assert a.rama == ""
