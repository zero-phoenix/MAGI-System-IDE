"""
Lo que viaja ARRIBA del prompt, en un solo sitio.

POR QUÉ UN MÓDULO PARA CUATRO LLAMADAS
======================================
El orchestrator llevaba la secuencia de inyecciones inline — aceptación,
caja de herramientas, bitácora y protocolo de corrida — y cada módulo nuevo
que se añadía lo engordaba. El trinquete de líneas lo paró justo cuando tocaba
la cuarta (ronda_verificada, v5.11.0): cuatro bloques inline ya no son
detalles, son una secuencia con contrato propio.

El contrato: dado un encargo, esto es TODO lo que se inyecta por encima del
prompt del enjambre, en orden. Si algo de lo que el enjambre «sabe de más»
sorprende a alguien, el porqué vive aquí — con su módulo y su razón:

  1. aceptacion  — criterios de aceptación ejecutables del encargo (NAZCA)
  2. caja        — las herramientas que responden A ESTE encargo, por nombre
  3. bitacora    — lo ya medido y lo que no hay que repetir (§2, §5, §3)
  4. ronda       — protocolo R9: corridas de emulador con ojos

QUÉ NO HACE
===========
No decide si inyectar (cada módulo filtra por su cuenta), no ejecuta nada y
no transforma lo inyectado: concatenar aquí sería una edición invisible de lo
que cada módulo escribió.
"""
from __future__ import annotations

__all__ = ["acumuladas"]


def acumuladas(encargo: str) -> str:
    """Todas las inyecciones que aplican a `encargo`, ya concatenadas."""
    from magi.modules.swarm import aceptacion as _acept
    from magi.modules.swarm import bitacora as _bit
    from magi.modules.swarm import caja_de_herramientas as _caja
    from magi.modules.swarm import ronda_verificada as _ronda

    return (
        _acept.para_el_prompt(_acept.criterios(encargo))
        + _caja.para_el_prompt(encargo)
        + _bit.para_el_prompt(encargo)
        + _ronda.para_el_prompt(encargo)
    )
