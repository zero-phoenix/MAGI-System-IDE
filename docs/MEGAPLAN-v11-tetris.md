# MEGAPLAN v11 — lo que la misión Tetris enseñó, de punta a punta

**Fecha:** 5-sep-2026 · **Método:** una persona real (el supervisor) operó MAGI
v5.21.1 EN VIVO desde su ventana nativa — teclar, pulsar botones, aprobar,
rechazar, parar — para crear un Tetris en un .exe portable; luego jugó el
artefacto resultante con el teclado. Todo lo de abajo está medido en esa
sesión, con capturas y log; nada es teórico.

---

## 1. El veredicto de la misión, en una frase

**MAGI entregó un .exe que abre y juega (gravity, colisiones, score, niveles,
game over) pero cuyo reinicio está roto y cuyo fuente no está donde dejó el
sistema** — y llegar ahí costó tres rondas, un rechazo, un E-STOP y dos
tareas basura que el propio sistema generó por no entender comandos.

Lo que funciona del pipeline: recon de Balthasar en paralelo, crítica
multi-eje 4/4, réplica con concesión real, compuerta de aprobación con
advertencia honesta («no toca ningún fichero»), E-STOP desde la GUI, y el
pie de estado con «⏸ ESPERA TU APROBACIÓN» (v5.21.1) avisando en vivo.

---

## 2. Los hallazgos, numerados y con evidencia

### Del ciclo de construcción (los graves primero)

| # | Hallazgo | Evidencia (5-sep-2026) | Severidad |
|---|---|---|---|
| **T1** | **El artefacto no tiene procedencia.** El `tetris.exe` del Escritorio (14.374.173 bytes, sha256 `3323d7ab…`) corre con score/niveles/game over, pero el fuente que MAGI guardó (`workspace/tetris_portable/tetris.py`) es un juguete CON los `\n` como texto literal (no compila), sin teclas, sin score. **Nadie puede regenerar el binario de lo que el sistema conserva.** | `grep` del fuente + juego ejecutado | **CRÍTICA** |
| **T2** | **Melchior llamó `build_project_exe` dos veces ANTES de escribir código** (iter 1, trazas 13:53:30). El .exe que existe salió de ahí por suerte (el tool interno generó su propio juego); la propuesta que se sometió a aprobación era solo DESCRIPCIONES. | log `[MELCHIOR] iter 1: build_project_exe` ×2 + panel «0 fichero(s)» | **CRÍTICA** |
| **T3** | **La compuerta aprobó humo y no lo sabía.** El C4/contrato dijo «0 fichero(s) · tests en verde» y aún así preguntó «¿Apruebo?». Debe ser al revés: una propuesta de producto SIN artefacto ni diff ni siquiera llega a preguntar — se rechaza sola con el motivo. | panel de aprobación, 13:58 | ALTA |
| **T4** | **El rechazo manda «NO» desnudo** — Melchior reanuda la ronda sin saber por qué. El botón Rechazo debe abrir un campo de una línea para el motivo (o tomar el texto del input si lo hay). | ronda 2 reanudada con observaciones «NO» | ALTA |
| **T5** | **Reinicio del juego roto** — foco verificado, R ×2, el juego sigue en GAME OVER. El encargo pedía explícitamente reinicio. Ni el --autotest ni la crítica lo vieron: **no hay prueba de interfaz del artefacto** (teclas → estado). | juego ejecutado en vivo, 2 capturas | ALTA |
| **T6** | **`task.cancel X` tecleado arranca una tarea** cuyo «proyecto» fue proponer **desregistrar una tarea programada de Windows** — Balthasar la frenó (2 objeciones de seguridad) pero la ronda completa corrió y llegó a pedir aprobación. Los comandos de administración deben reconocerse EN el input o rechazarse en el router. | log 14:52 + panel de aprobación peligroso | **CRÍTICA** (seguridad) |

### De la operativa de la interfaz (lo que el usuario sufrió)

| # | Hallazgo | Severidad |
|---|---|---|
| **T7** | **`SYS_EXEC ▾` es un botón decorativo** — clic verificado, no abre nada. Debería desplegar los comandos de administración (`task.cancel`, `EMERGENCY_STOP`, `SYS_EXEC_HOST`…) — que es exactamente el agujero que T6 destapó. | ALTA |
| **T8** | **PARAR ESTA no detuvo las llamadas en vuelo** (los proveedores siguieron 3+ min) y PARAR TODO dijo «no había nada en marcha que parar» **con llamadas activas**: el registro de cancelación no incluye los bucles LLM en curso. | ALTA |
| **T9** | **El Terminal inunda el bus** con fallbacks de proveedores (cientos de líneas) y eso **enmascara al guardián** (el silencio de la ronda nunca se ve porque el spam reinicia el reloj) y hace el panel ilegible. El ruido de infraestructura debe ir a un canal separado. | ALTA |
| **T10** | **Ronda profunda >45 min** con proveedores gratuitos muriendo; el motor no degrada solo. Con T8, el operador no tiene forma limpia de abortar y relanzar en rápido. | MEDIA |
| **T11** | El compositor del Terminal acapara 16,8 s de reparto (log del ws) — el mismo embudo que la v9 arregló para eventos grandes, activado por el spam de T9. | MEDIA |

### Del juego mismo (lo que un QA habría escrito)

- Abre en ventana propia, gravity + colisiones + apilado OK, SCORE/LINES/LEVEL pintados, GAME OVER alcanzable. **R-reinicio NO funciona (T5).**
- No hay «siguiente pieza», no hay pausa, la velocidad del nivel no es perceptible en 2 min de juego. Menor.

---

## 3. Cómo lo habría hecho yo (comparativa honesta)

| Paso | Yo | MAGI |
|---|---|---|
| Escribir el juego | Un solo fichero `tetris.py` con las 7 piezas, matriz 10×20, rotación por transposición con patada simple, score = líneas×nivel, gravedad por tick de nivel; **y un `--autotest` que simule 60 s de teclas** (rotar, mover, soltar, forzar game over, pulsar R y comprobar tablero limpio) | Dos «enfoques» descritos en prosa; cero código en la propuesta; autotest solo de «existe el fichero» |
| Compilar | PyInstaller onefile sobre ESE fichero, y registrar **sha256 del .exe Y del .py** en un manifiesto junto a la carpeta | `build_project_exe` invocado antes del código; binario sin fuente emparejado |
| Verificar | Lanzar, mandar teclas sintéticas, capturar la ventana, afirmar: pieza se mueve con ←→, rota con ↑, GAME OVER llega, R limpia el tablero — todo automatizable con la misma infraestructura de `vita3k_ctl` (ojos + brazos) que el proyecto YA TIENE | «tests en verde» que solo comprobaban existencia; el reinicio roto pasó |
| Entregar | .exe + manifiesto + fuente, los tres con hash | .exe solitario en el Escritorio |

La lección no es «MAGI malo»: es que **el sistema verifica lo que sabe
verificar (ficheros, hashes, rondas) y no verifica lo que el encargo era de
verdad (que se juega)**. La infraestructura de ojos/oídos que ya tiene para
el emulador nunca se aplicó a sus propios artefactos.

---

## 4. El plan — paquetes, en orden

### Bloque A — procedencia y verdad del artefacto (crítico)

- **A1 · Manifiesto obligatorio de artefacto.** Toda compilación deja
  `artefacto.exe + artefacto.manifest.json` (sha256 del binario, sha256 de
  CADA fuente usado, comando exacto de PyInstaller, fecha). La compuerta de
  aprobación de productos exige manifiesto; sin él, `[INCOMPLETO]`.
  Compuerta: el .exe del Tetris recompilado desde fuente versionado pasa con
  manifiesto; la entrega actual fallaría.
- **A2 · Autotest de interfaz para juegos.** El `--autotest` de juego debe
  simular teclas (estructura ya existente en `ronda_verificada`): mover,
  rotar, game over forzado, reinicio, y afirmar tablero limpio. **Habría
  cazado T5 antes de entregar.**
- **A3 · El código ANTES del build.** `build_project_exe` exige ≥1 fichero
  fuente escrito en ESA tarea (del journal); si no, se niega con motivo.
  Habría cazado T2 en la iteración 1.

### Bloque B — comandos y seguridad (crítico)

- **B1 · El input reconoce comandos de administración**: `task.cancel [id]`,
  `parar todo`, `SYS_EXEC_HOST …` se detectan en `_handle_sys_exec` y se
  ejecutan como tales, NUNCA como encargo. Con test de cada uno. Mata T6.
- **B2 · El router se niega a debatir órdenes**: si el encargo clasifica como
  orden de sistema (confianza del clasificador de órdenes) y no existe el
  handler, respuesta inmediata «eso es un comando, no un encargo» + la lista
  de comandos. Segunda capa sobre B1.
- **B3 · SYS_EXEC ▾ desplegable de verdad** con esos comandos (un clic, sin
  teclear). Convierte T7 en la cura de T6.

### Bloque C — control del operador

- **C1 · PARAR de verdad:** registrar cada bucle LLM en vuelo en el
  supervisor de cancelación; PARAR ESTA/TODO corta las llamadas (timeout del
  futuro + aviso). Cura T8.
- **C2 · Rechazo con motivo:** el botón Rechazo pide una línea de motivo
  (prellenada con la crítica de Balthasar) y la inyecta como observaciones.
  Cura T4.
- **C3 · Compuerta que no pregunta humo:** producto sin artefacto/manifiesto
  → rechazo automático con motivo, sin preguntar. Cura T3.

### Bloque D — ruido y latencia

- **D1 · Canal de infraestructura separado:** los fallbacks/canarios de
  proveedores dejan de ir por TERMINAL_OUT; el Terminal muestra solo lo del
  enjambre y el sistema; el spam va a un log consultable. Cura T9 y T11, y
  **destapa al guardián** (su punto ciego documentado).
- **D2 · Degradación de motor por salud de proveedores:** si la tasa de
  respuestas inservibles supera X en la ronda, proponer al operador (no
  imponer) cambiar a fast. Cura T10.

### Bloque E — interfaz (continuación de la deconstrucción)

- **E1 · Tarjeta de plan viva en el flujo** (Fase 3 del v6): el encargo de 8
  partes se ve mientras se cumple.
- **E2 · Hilos de Naoko y Ritsuko en la columna izquierda**, no como pestañas.
- **E3 · La tarjeta de aprobación muestra el manifiesto** (hash del binario,
  fuentes) — aprobar con los datos de procedencia delante (cierra el círculo
  con A1).

### Fuera de alcance de este plan (anotado)

Reescribir el Tetris a mano: NO es la tarea — el valor está en que MAGI
pueda rehacerlo ÉL solo con A1-A3 y B1-B3. El .exe actual queda en el
Escritorio como evidencia, con su defecto de reinicio documentado.

---

## 5. Compuertas de sesión

1. Suite completa + `verificar.py --todo` en verde antes de publicar.
2. Cada paquete con SU prueba: A1 con recompilación, A2 con el R roto
   reprodubible, B1 con `task.cancel` tecleado (el caso exacto de hoy),
   C1 con llamadas en vuelo interrumpidas.
3. Trinquetes intactos; `orchestrator.py` 1550/1550 — extraer antes de tocar.
4. Publicar release con notas concretas; conservar TODOS los releases.
