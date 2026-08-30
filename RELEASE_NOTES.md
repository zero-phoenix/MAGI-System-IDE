# v5.12.0 — la Ronda 2 ejecutada y supervisada, y el huérfano que rompía el CI

**Qué cambia:** la Ronda 2 de YabauseVita se ejecutó con el procedimiento del
sistema (`scripts/ronda_emulador.py`) y la supervisión encontró dos fallos del
propio procedimiento — que ya no están. Además, el release v5.11.0 destapó una
clase de huérfano nueva, que ahora tiene trinquete.

**Lo concreto:**

- **Experimento de input rediseñado** — la v5.11.0 medía diff antes/después en
  el attract de Sonic R, que ya se mueve: la pulsación quedaba diluida y el
  veredicto era falso. Ahora: capturas a 1 s, PICO de transición y CONTROL de
  6 s sin pulsar. Resultado medido con el protocolo correcto: ENTER en el
  attract no produce transición (pico 5,31 % vs control 5,16 %) — con el matiz
  declarado de que el attract puede ignorar START (regla R13: todo veredicto
  dice en qué pantalla se midió).
- **Resultados de la Ronda 2** (verificados con capturas): NiGHTS no llega al
  título en 3 min — queda en la pantalla de licencia SEGA esperando al disco;
  el dynarec cuelga al primer frame por tercera build independiente; y el
  perfil SH2 queda fijado: 69,9 % (Sonic R), 64,7 % (Panzer, que aun así corre
  a 59,8 FPS) y 90,7 % (NiGHTS) del hilo principal.
- **El harness expone los diffs por captura** (`diffs_por_captura`) — sin eso
  no hay picos de transición, solo medianas.
- **Trinquete de versionado** (`test_nada_sin_versionar.py`) — `bitacora.py`
  existía en el disco de desarrollo y NO en git: la suite local pasaba y el CI
  reventaba con ImportError en el release v5.11.0. Un módulo con test pero sin
  versionar pasa la suite local siempre, presente o no en el repo. Ahora todo
  `.py` bajo `magi/` y `tests/` que git no conozca es un fallo con nombre.
- **Refactor con el trinquete contento** — la cuarta inyección inline hizo
  saltar el límite de líneas del orquestador; la secuencia de inyecciones
  (aceptación, caja, bitácora, protocolo de corrida) vive ahora en
  `inyecciones.py`: el orquestador bajó de 1557 a 1543 líneas sin subir el
  techo.

**Compatibilidad:** sin cambios de interfaz ni de configuración.
