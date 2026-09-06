"""
A2 (megaplan v11): los juegos entregados se prueban CON TECLAS.

La misión Tetris (5-sep-2026) entregó un .exe cuyo reinicio (tecla R) estaba
roto — y la compuerta no lo vio porque «tests en verde» solo comprobaba que
el fichero existía. Un juego no se verifica mirándolo existir: se verifica
JUGÁNDOLO. El contrato (C16) ya exigía `--autotest`; este módulo lo ejecuta
y exige la marca de éxito.

El autotest que el juego debe traer: con `--autotest` (o `--autotest N`),
el juego SIMULA él mismo las teclas (pygame.event.post / tk event_generate),
fuerza un game over, pulsa su tecla de reinicio y comprueba que el tablero
queda limpio; si todo sale, imprime la marca y sale con código 0. Si la
tecla de reinicio está rota, no puede imprimir la marca — exactamente el
defecto que la misión encontró en el artefacto real.
"""
from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)

__all__ = ["MARCA_OK", "probar_juego_interactivo"]

#: La marca que el autotest del juego debe imprimir para contar como verde.
MARCA_OK = "GAME_AUTOTEST_OK"

#: Los juegos gráficos arrancan ventanas: un autotest colgado no debe
#: bloquear la compuerta más de esto.
TIMEOUT_POR_DEFECTO_S = 60.0


async def probar_juego_interactivo(comando: list[str],
                                   marcador: str = MARCA_OK,
                                   timeout: float = TIMEOUT_POR_DEFECTO_S,
                                   ) -> tuple[str, str]:
    """
    Lanza `comando` (p. ej. `[exe, "--autotest"]`) y devuelve
    `(estado, salida)` con `estado` en:

      · "verde"          — código 0 Y la marca en la salida.
      · "rojo"           — el autotest corrió y NO llegó a la marca: el
                           juego no recorrió su ciclo con teclas.
      · "sin_comprobar"  — cuelgue o lanzamiento imposible. La regla de la
                           casa: no comprobado NO es roto. Un exe de ventana
                           sin salida de consola puede colgar el autotest sin
                           que el juego esté mal.

    Ni el código solo ni la marca sola bastan: un juego que sale 0 sin
    probar las teclas no probó nada.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            *comando,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except Exception as e:
        return "sin_comprobar", f"no se pudo lanzar: {e}"
    try:
        salida, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return ("sin_comprobar",
                f"el autotest no terminó en {timeout:.0f}s: cuelgue")
    texto = salida.decode(errors="ignore")
    if proc.returncode == 0 and marcador in texto:
        return "verde", texto[-2000:]
    return "rojo", texto[-2000:]
