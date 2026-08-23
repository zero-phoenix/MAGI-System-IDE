"""
La mediciÃ³n no puede quitarle el turno a la persona que estÃ¡ esperando.

LO QUE PASÃ“, EN EL REGISTRO DEL USUARIO
=======================================
2026-08-23. Abre MAGI, escribe su encargo, y lo siguiente que sale es:

    root@system:~# crea un juego de tetris en un unico ejecutable exe portable
    [g4f-razonamiento] Perplexity devolviÃ³ una respuesta inservible ('tud.')
    [registry] familia 'razonamiento' agotada (3 candidatos)
    [sonda] 32 candidatos medidos, 0 saltados por tope diario
    [sonda] 32 mediciones (la Ãºltima mediciÃ³n fue hace 84.1 h)
    [g4f-gpt] respondiÃ³ Perplexity/gpt4o en 12734ms (cubierto x3)
    [g4f-gpt] respondiÃ³ Perplexity/gpt5  en 15109ms (cubierto x3)
    [naoko] g4f-gpt: 0/3 canarios
    ...

Sesenta y pico llamadas HTTP a proveedores gratuitos â€”limitados por cuotaâ€”
ANTES de atender lo que la persona acababa de pedir. En el panel central,
mientras tanto: Â«Esperando flujos del EnjambreÂ».

POR QUÃ‰ B8 NO BASTÃ“
===================
B8 ya comprobaba si el enjambre estaba ocupado. Pero comprueba UNA vez y
luego se va a medir durante un minuto: es un comprobar-y-actuar con una
ventana enorme en medio. Y esa ventana se abre en el peor momento posible
â€”el arranqueâ€”, porque el freno de 24 h garantiza que la primera sesiÃ³n del
dÃ­a dispare el sondeo justo mientras la persona escribe.
"""
from __future__ import annotations

import inspect

from magi.core.kernel import Kernel


class _Enjambre:
    def __init__(self, tareas=None, pendientes=0):
        self.active_tasks = tareas or {}
        self.admision = _Admision(pendientes)


class _Admision:
    def __init__(self, n):
        self._n = n

    def pendientes(self):
        return ["x"] * self._n


def _kernel(enjambre) -> Kernel:
    k = Kernel.__new__(Kernel)
    k.swarm = enjambre
    return k


def test_una_tarea_en_curso_ocupa_el_enjambre():
    k = _kernel(_Enjambre({"t1": {"status": "in_progress"}}))
    assert k._enjambre_ocupado()


def test_lo_recien_encolado_tambien_cuenta():
    """
    El instante que mÃ¡s importa: entre que el usuario pulsa Â«EjecutarÂ» y que
    el orquestador marca la tarea en curso. Mirar solo `in_progress` dejaba
    ese hueco abierto, y es justo donde caÃ­a el sondeo.
    """
    k = _kernel(_Enjambre({"t1": {"status": "queued"}}))
    assert k._enjambre_ocupado()


def test_lo_que_espera_en_admision_tambien_cuenta():
    """Lo que el usuario ya escribiÃ³ y aÃºn no llegÃ³ al orquestador."""
    k = _kernel(_Enjambre({}, pendientes=1))
    assert k._enjambre_ocupado()


def test_un_sistema_de_verdad_parado_no_esta_ocupado():
    """
    La otra mitad. Si esto diera siempre `True`, la sonda no volverÃ­a a
    medir nunca y el reparto se quedarÃ­a con el catÃ¡logo escrito a mano â€”que
    es un fallo que este proyecto ya tuvo, por un import mal puesto.
    """
    k = _kernel(_Enjambre({"t1": {"status": "completed"},
                           "t2": {"status": "WAITING_USER_APPROVAL"}}))
    assert not k._enjambre_ocupado()


def test_las_tareas_rehidratadas_no_bloquean_la_sonda():
    """
    Al arrancar hay tareas antiguas esperando aprobaciÃ³n. No son trabajo en
    curso y no deben impedir medir para siempre.
    """
    k = _kernel(_Enjambre({f"t{i}": {"status": "interrumpida"} for i in range(13)}))
    assert not k._enjambre_ocupado()


def test_hay_tregua_de_arranque():
    """
    El freno que faltaba: no gastar un solo token durante los primeros
    segundos de sesiÃ³n, que es cuando la persona escribe su primera peticiÃ³n.
    """
    assert Kernel._TREGUA_DE_ARRANQUE_S >= 60, (
        "la tregua tiene que cubrir el rato en que el usuario escribe lo "
        "primero que va a pedir")

    fuente = inspect.getsource(Kernel._refrescar_sonda)
    assert "_TREGUA_DE_ARRANQUE_S" in fuente, (
        "la constante no sirve de nada si el bucle no la respeta")
    # Y la comprobaciÃ³n repetida: una sola, antes de los imports, deja una
    # ventana por la que se cuela la peticiÃ³n del usuario.
    assert fuente.count("_enjambre_ocupado()") >= 2, (
        "hay que volver a mirar justo antes de gastar, no solo al entrar")
