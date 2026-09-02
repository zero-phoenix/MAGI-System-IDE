# ESTADO DE EJECUCIÓN — sesión del 2-sep-2026 (v5.19.0)

Lo que este plan ya dejó hecho en su primera sesión, con su evidencia:

| Paq | Estado | Evidencia |
|---|---|---|
| D1 | ✅ | R16 commiteada en la bitácora del emulador (`80d5dc0`) — estaba en disco desde el 31-ago y nunca llegó al commit |
| D2 | ✅ | suelo de tests del README subido en la v5.19.0 |
| D4 | ✅ | docstring de `Regla.exige` corregido a lo que existe; contador de estorbo aplazado hasta que haya rondas reales con choques |
| D5 | ✅ | `pertinente()` estrechado (`vita` suelta fuera; guardia de entregable ajeno). Medido antes: 3/10 falsos positivos |
| D6 | ✅ | R7 en `REGLAS`, con valor-con-unidades para no flagrar la negación honesta |
| D3 | ✅ | `TRASPASO.md` actualizado a v5.19.0 |
| M1 (R2) | ✅ | Ritsuko mide el eco del chat (>2 s) y el arranque de ronda (>30 s): `ritsuko.retraso_percibido` |
| M2 (R4) | ✅ | Ritsuko firma las entregas al cerrar: `ritsuko.firma_entrega` (VERIFICADA / DECLARADA_INCOMPLETA / SIN_ARTEFACTO) |
| M3 (R3) | ⏳ | igual que en v9: tras rodar G4. La auditoría en vivo volvió a ver canarios con tarea viva — la motivación sigue ahí |
| P4 (C6) | ✅ | resuelto al reproducirse en ronda real: parche de `model_aliases` en `compat_g4f.py` |
| E1-E4, F1-F5, P1-P3 | ⏳ | sin empezar; el orden está en §11 |
| D8 (parcial) | ◐ | `replica.jsonl` tiene su PRIMERA fila real: task_btyy3gcn, réplica disparada, Melchior CONCEDIÓ (1 objeción). La compuerta de vida-o-muerte ya tiene de qué alimentarse — queda correr el contrafactual (`MAGI_REPLICA_SOMBRA=1`) en rondas reales |
| Auditoría en vivo | ✅ |
- **Tercer hallazgo del pie, ya en vivo:** tras arreglar la constante «v3.0», el pie decía «v0.0.0» — el fallback de `magi/__init__.py` prometía leer pyproject y devolvía la constante. Corregido leyendo pyproject (regex, sin tomllib en 3.10) con test de regresión. El .exe del CI no se afecta (pip-instala antes de compilar); viaja desde main en la próxima versión.
 tarea real por la GUI: eco instantáneo, abanico+crítica 4/4+réplica con concesión, failover en vivo, `no_browser` cazando un Chrome. Fallos hallados y corregidos: pie «v3.0», Vista previa nacía rota, test de la cascada con margen absoluto |

---

# MEGAPLAN v10 — Continuación integral de MAGI-System-IDE + YabauseVita

**Fecha:** 2 de septiembre de 2026
**Para:** ZCode Desktop (Z.ai AI Agent Coding Desktop App) o cualquier agente que continúe
**Partida:** MAGI-System-IDE **v5.18.0** (`0b7316b`) · YabauseVita `e33ead7`
**Procedencia:** auditoría independiente del repositorio público + todo el historial documental
(docs/, RELEASE_NOTES.md, bitácora del emulador, automodelo) verificada contra el código.

---

## 0. Cómo usar este documento — y la regla que ordena todo

> **Un documento sobre el sistema no es el sistema. Lee el código.**

Es la lección fundacional del proyecto: `PORTING_NOTES.md` describía un esqueleto sin
sonido ni mando y el código real tenía dynarec ARM, CHD y audio. Un plan entero se
escribió sobre el documento y hubo que tirarlo. **Si algo de este megaplan contradice
al código, gana el código** — y entonces corriges este megaplan, en el mismo commit.

Orden de lectura obligatorio antes de tocar nada:

1. Este documento, entero.
2. `docs/TRASPASO.md` del repo MAGI — el mapa (⚠️ describe el estado a v5.16.0;
   está desactualizado en las fases 7/8/filosofías, ya construidas — ver §10.D3).
3. `C:\Users\D\Documents\GitHub\yabausevita-zp\docs\BITACORA-OPTIMIZACION.md` —
   hallazgos A1-A27 y reglas R1-R15 (R16 vive solo en MAGI — ver §10.D1).
4. `docs/MEGAPLAN-v6-subagentes.md` — el plan de 4 partes con las 11 fases.
5. `docs/AUTOMODELO.json` — lo que el sistema sabe que NO sabe hacer.

Cuando termines, resume en tres frases qué entendiste del estado actual. Si no
puedes, no has terminado de leer.

---

## 1. Estado verificado (2-sep-2026)

### Repositorios

| | |
|---|---|
| `zero-phoenix/MAGI-System-IDE` | público, `main` en `0b7316b`, **v5.18.0**, 200 commits |
| `zero-phoenix/yabausevita` | público, `main` en `e33ead7` (Ronda 3 documentada) |
| Clones locales de trabajo | `C:\Users\D\Documents\GitHub\MAGI-System-IDE` y `C:\Users\D\Documents\GitHub\yabausevita-zp` |

⚠️ **Tres identidades GitHub en esta máquina:** `davidchaveznge-wq` en `git config`,
`zero-phoenix` (la activa) + `4n0th1ng` en `gh` CLI. El clon `Documents\GitHub\yabausevita`
(sin `-zp`) apunta a la cuenta vieja y **está obsoleto**: no trabajes ahí.

**Releases:** todos se conservan, ninguno se borra NUNCA. El `.zip` de Windows
(~144 MB con el `.exe` y su Python 3.10 embebido) se construye en GitHub Actions
desde cada tag, junto con `CHECKSUMS.txt`. El `.exe` no va firmado (SmartScreen
avisa) — decisión asumida, no un fallo a arreglar sin encargo explícito.

### Dimensiones medidas

| Métrica | Valor |
|---|---|
| Ficheros `.py` bajo `magi/` | 215 |
| Líneas bajo `magi/` | 37.107 |
| Ficheros de test (`tests/`) | 111 |
| Pruebas Python | ~1.651 (v5.18.0; el README declara suelo «1472» — ver §10.D2) |
| Pruebas de interfaz (`magi-gui`, Vitest) | 122 |
| Herramientas reales del enjambre | 55 (guardadas por `test_readme_claims.py`) |
| Compresores del pipeline | `orchestrator.py` en **1550/1550 líneas — en su techo exacto** (§10.D7) |

### Última versión publicada — v5.18.0, qué hizo y qué dejó abierto

Hizo: las tres filosofías dejaron de depender de la semilla. Ahora se **asignan**
(variante 0 → `composite`, 1 → `upload`, 2 → `dropped`), las rondas de optimización
del emulador generan **3** variantes (antes 2, y la filosofía C nunca se exploraba),
las reglas §5.2 (R1, R6, R14, R15) se comprueban **sobre el texto de la propuesta
antes de compilar**, cada variante recibe en su prompt qué regla suspende su
filosofía y qué haría falta para levantarla, el reparto se revisa a posteriori
(`filosofias.revisar`), y las reglas del emulador quedaron acotadas a rondas que
de verdad reparten filosofías (un Tetris o una subida web ya no disparan R6).

Dejó abierto (cito la propia nota de release y el resumen de sesión):

- **Las tres filosofías siguen suspendidas.** R6 tapa A y B (camino de render =
  1,27 % del tiempo, hallazgo A7); A9 tapa C (su métrica `dropped` no se imprime
  en el log). Levantarlas exige dos cosas concretas: **exponer
  `drawn/presented/dropped` en el log** (levanta A9) y **telemetría de emulación
  que demuestre que en render queda algo** (levanta R6). Es el paquete E1 de §11.
- El reparto filosófico aún no ha corrido **ninguna ronda real** con las tres
  variantes activas (la evidencia es de test + ronda sintética por el orquestador
  real). La primera ronda real que lo ejercite debe medirse.

---

## 2. Qué es MAGI — mapa completo

Entorno de desarrollo con un **enjambre de tres IA** que debaten antes de actuar
(tesis → antítesis → síntesis), en español, con **55 herramientas reales** que se
ejecutan en la máquina, e inferencia **100 % en tiers gratuitos de la nube vía
g4f** (sin claves de API, sin modelos locales, sin suscripciones). Regla rectora:
*«una afirmación sin evidencia verificada no es una afirmación»*.

### Los cinco agentes (+1)

| Agente | Rol | Familia de modelos |
|---|---|---|
| **MELCHIOR** | Tesis: construye, escribe y ejecuta código, anticipa sus propios fallos | `gpt` |
| **BALTHASAR** | Antítesis: refuta a Melchior **ejecutando** su código; lee y ejecuta, nunca escribe | `gemini` |
| **CASPER** | Síntesis: integra ambas posiciones, entrega la respuesta final | `command` |
| **NAOKO** | Supervisora externa: clasifica peticiones, elige estilo de respuesta, puede autoreparar el sistema | — |
| **RITSUKO** | Audita a Naoko: solo informa, nunca modifica; informes descargables en `%LOCALAPPDATA%\MagiSystem\informes-ritsuko` | familia que nadie más usa |

Por defecto una ronda; el feedback del usuario abre la segunda empezando por Melchior.
Dos modos: **análisis profundo** (por defecto, temperatura baja, más verificación) y
**super rápido**.

### El núcleo (`magi/core/`)

`kernel.py` (1066 líneas), `bus.py`, `agent.py`/`agent_loop.py`, `verification.py`,
`presupuesto.py` (techo por iteración sale del presupuesto restante — C3),
`providers/` (`g4f_backend.py` 1016 líneas, `registry.py`, `sonda.py` con canarios,
`wal.py`, `rate_limit.py`, `circuit.py`), `tools/`, `store/` (SQLite + telemetría),
`rpc/ws_server.py` (reparto a la GUI con techo de 2 s por envío — G1), `policy/`,
`octopus.py`, `hive.py`, `membrane.py`, `eval/bench.py`.

### El enjambre (`magi/modules/swarm/`) — empezar por `inyecciones.py`

| Fichero | Qué es |
|---|---|
| `inyecciones.py` | **La secuencia de lo que viaja arriba del prompt, en un solo sitio.** Seis inyecciones en orden: aceptación → caja → bitácora → ronda → memoria → automodelo |
| `orchestrator.py` | El director de la ronda. **1550/1550 líneas — techo exacto** |
| `agents.py` | Prompts y turno de los tres nodos (1200 líneas) |
| `filosofias.py` | **v5.18.0.** Las tres filosofías asignadas por variante + comprobación de reglas §5.2 antes de compilar + revisión de ortogonalidad a posteriori |
| `abanico.py` / `parallel.py` | Fase 7: fan-out de lo que no depende. `MAGI_ABANICO=0` vuelve a serie |
| `replica.py` | Fase 8: Melchior contesta a la objeción antes del arbitraje. `MAGI_REPLICA_SOMBRA=1` corre el arbitraje contrafactual y anota en `magi/data/memoria/replica.jsonl` |
| `contraste.py` | La mecánica del cierre (C12: lo que la síntesis dice que pasó vs. lo que consta) |
| `bitacora.py` | Inyecta lo ya medido y las reglas de «no repetir» del repo objetivo |
| `memoria_persistente.py` | Memoria entre proyectos: mandos + descartes con lo `rescatable` |
| `automodelo.py` | Lo que MAGI cree de MAGI, cada afirmación con la prueba que puede tumbarla |
| `ronda_verificada.py` | Protocolo R9/R16: corrida sin ojos y oídos no es evidencia |
| `aceptacion.py`, `caja_de_herramientas.py`, `contrato.py`, `intencion.py` | Criterios ejecutables (NAZCA), herramientas pertinentes al encargo, contrato de entregable, detección de intención |

### Percepción y memoria

| Ruta | Qué es |
|---|---|
| `magi/modules/percepcion/oidos.py` | `listen_audio` / `audio_available` — loopback WASAPI; distingue `has_sound`, `choppy`, `sonando_pct`. Sin backend → **SIN COMPROBAR**, nunca veredicto negativo inventado |
| `magi/modules/percepcion/vista.py` | `classify_screen` — clase de pantalla, idioma (kana para japonés), botón pedido validado contra la memoria de mandos. Segunda pasada para texto pegado del OCR |
| `magi/modules/memory/indice.py` | FTS5 sobre bitácora, memoria, docs y código: 224 docs / 2,7 MB indexados en 100 ms, consulta en 1 ms. Sanea consultas (buscar `1.27` ya no revienta) |
| `magi/modules/infrastructure/naoko.py` | 1628 líneas — la supervisora |
| `magi/modules/infrastructure/ritsuko.py` | La auditora; veto de derivas (R1 de v9) implementado |
| `magi/modules/studio/` | Vídeo programático, artefactos |

### Datos versionados (en git, a propósito)

`magi/data/memoria/controles.json` (16 consolas), `descartes.jsonl` (descartes con
medición y campo `rescatable`), `replica.jsonl` (compuerta de la réplica — **debe
estar limpio de datos de prueba**; hay guardián).

### Documentos generados, nunca escritos a mano

`docs/AUTOMODELO.json` y `.md`, `docs/MAPA-INTERFAZ.md` — se regeneran; editarlos
a mano es crear un documento que miente sobre su propio origen.

### La interfaz (`magi-gui/`)

Tauri + Vite + React/TypeScript. Streaming token a token (~2 s el primero), traza
de herramientas, paleta Ctrl+K, visor de diffs, panel de aprobación, panel de coste
y salud, rankings p95. 122 tests Vitest + build en la compuerta.
`docs/MAPA-INTERFAZ.md` mide el cableado por topics (v5.14.0): había **25
capacidades que el backend emite y ningún panel pinta** — backlog vivo de GUI.

---

## 3. Los trinquetes — y cómo vivir con ellos

Cuatro tipos. La regla: **nunca se sube el techo** y **nunca se toca `KNOWN_ORPHANS`**
para colar algo. Se conecta el módulo, se adelgaza o se corrige.

| Trinquete | Techo / forma | Dónde |
|---|---|---|
| Huérfanos | ≤ 80 | `python scripts/huerfanos.py --conteo` |
| Líneas por módulo | p. ej. `orchestrator.py` = 1550 (**está EXACTO**), `naoko.py` = 1628 | suite de trinquetes |
| Nada sin versionar | todo `.py` bajo `magi/` y `tests/` que git no conozca es fallo con nombre (nacido del release v5.11.0 que reventó en CI por `bitacora.py` en disco y no en git) | `tests/test_nada_sin_versionar.py` |
| Contador del README | las 55 herramientas y el suelo de tests | `tests/test_readme_claims.py` |
| Guardián de `replica.jsonl` | el registro de la compuerta de réplica no puede ensuciarse con datos de prueba (v5.17.1) | suite |

El techo de líneas **ya demostró mejorar el diseño**: obligó a extraer `inyecciones.py`,
`contraste.py` y `replica.py`, y el orquestador quedó más corto con más funcionalidad.

---

## 4. La compuerta de verificación — qué se corre y cuándo

### En cada push (lo mismo que CI, ~4 min)

```bash
python scripts/verificar.py
```

Réplica local exacta del `ci.yml`: ruff bloqueante (`E9,F63,F7,F82`) → pytest
paralelo sin los `slow` (`-n auto --dist loadfile`) → imports del núcleo →
`npm test` → `npm run build`. Exit 0 = verde; 1 = fallo; 2 = **algo no se llegó a
comprobar por falta de herramienta** — ni verde ni rojo, y decir «todo verde» ahí
es mentir por omisión.

### Antes de publicar una versión (compuerta completa)

```bash
python -m ruff check magi/ tests/        # ruff==0.16.5 FIJADO, requirements-dev.txt
python scripts/huerfanos.py --conteo     # techo 80
python -m pytest tests/ -q               # suite COMPLETA, ~25 min en esta máquina
python scripts/verificar.py --todo       # + los tests que compilan .exe, ~10 min
python scripts/publicar.py               # publica (tag, zip, CHECKSUMS)
```

**Se corre entera, no el subconjunto que elijas.** El trinquete `test_wiring` caza
módulos escritos, probados y sin conectar, y ningún subconjunto lo ve. Ya cazó al
agente anterior en su último commit. Los cuatro rebotes de CI en un día quedaron
registrados en el automodelo como afirmación refutada («corro la compuerta antes
de publicar», veces_ok 2 / veces_mal 1).

---

## 5. Reglas no negociables (transversales)

1. **Ninguna corrida es evidencia sin ojos y oídos.** Pasó de verdad: 59,9 FPS
   estables media hora con la pantalla negra. Toda medición trae `has_image`,
   `has_motion` y veredicto de sonido (R9/R16).
2. **«No lo comprobé» ≠ «no funciona».** Capacidad ausente en la máquina → se
   declara **SIN COMPROBAR**. Inventar un veredicto negativo es peor que omitirlo.
3. **Se mide contra un CONTROL en la misma corrida, no contra constantes** (R12,
   aprendida dos veces: input del emulador y `t_melchior_ms < 900` que medía el
   runner de CI, no el código — v5.17.1). Un umbral absoluto de tiempo no
   distingue «regresión» de «máquina cargada», así que no puede decidir nada.
   Cuando la medida sintética y la del sistema real discrepan, **gana la real**
   (38 % medido, no el 66 % prometido del banco).
4. **Escribe ficheros con Python**, `newline='\n'`, y comprueba
   `datos[:3] != b'\xef\xbb\xbf'`. PowerShell mete BOM y ya rompió
   `pyproject.toml` y el `config.cfg` del emulador (el `sscanf` lee
   `\ufeffrom_path` y lo ignora en silencio).
5. **Nunca subas un techo de trinquete** ni añadas nada a `KNOWN_ORPHANS`.
6. **Los FPS de Vita3K no son prueba de rendimiento** (R4). Vita3K decide
   *corrección*; las métricas internas del emulador deciden *rendimiento*.
7. **No borres releases anteriores. Nunca.**
8. **No escribas a mano un documento que se genera** (AUTOMODELO, MAPA-INTERFAZ).
9. **Optimización sin forma de apagarla no se puede comparar consigo misma**
   (por eso existen `MAGI_ABANICO=0` y `MAGI_REPLICA_SOMBRA=1`).
10. **Si te equivocas, dilo y corrígelo en el mismo mensaje.** El proyecto mejora
    cada vez que alguien señala que el plan apuntaba al sitio equivocado; las
    erratas de las notas de release se corrigen con errata visible (v5.17.1), no
    reescribiendo el pasado.

---

## 6. Estado real de las once fases del megaplan v6

| # | Fase | Estado | Compuerta / nota |
|---|---|---|---|
| 1 | Búsqueda web sin ventana (`web_search`, `web_read`) | **PENDIENTE** | Balthasar refuta con URL que encontró él. Sin navegador; presupuesto por turno; cita con URL+fecha obligatoria; sin red → SIN COMPROBAR |
| 2 | Subagentes por familia | **PENDIENTE** | Solo lectura, devuelven conclusión no volcado, temp baja, turno único, tope por nodo/ronda, traza visible. Compuerta: gasta MENOS contexto por nodo |
| 3 | Plan visible con estado (`plan.md` por tarea) | **PENDIENTE** | Casper no cierra con partes `pendiente` sin decir por qué |
| 4 | Compuerta obligatoria antes de «hecho» | **PENDIENTE** | Una entrega sin `verificar.py` adjunto se rechaza sola |
| 5 | Veredicto «la pregunta era otra» | **PENDIENTE** | Cuarto veredicto además de gana/pierde/empata; cierre sin ganador + registro |
| 6 | Índice local FTS5 | **CONSTRUIDA** (v5.16.0) | 2,7 MB en 100 ms; consulta 1 ms |
| 7 | Abanico paralelo | **CONSTRUIDA** (v5.17.0) | 3141→1937 ms por el orquestador real, **38 %** (no 66 %). `MAGI_ABANICO=0` |
| 8 | Réplica | **CONSTRUIDA** (v5.17.0) | Condicional, acotada (1400/900 chars), una vuelta, salida por `CONCESIÓN:`. Compuerta armada: `MAGI_REPLICA_SOMBRA=1`, Casper cambia ≥1/5 o se retira |
| 9 | Embeddings locales | **RETIRADA** | Sobre-ingeniería sobre 2,7 MB; retirada con motivo escrito. No la resucites |
| 10 | Modelo de sí mismo falsable | **CONSTRUIDA** (v5.16.0) | 9 afirmaciones: 3 sostenidas, 4 refutadas, 2 sin comprobar |
| 11 | Fijar el linter | **APLICADA** | `ruff==0.16.5` en requirements-dev |

Orden original del v6 para las pendientes: **1 → 2 → 3 → 4 → 5** (la 1 va primera
porque más cambia lo que el enjambre *puede saber*; la 4 sin las otras solo añade
fricción). Este megaplan mantiene ese orden dentro del bloque F (§11.F).

**Nota crítica sobre la compuerta de la Fase 8:** `replica.jsonl` aún no tiene
ninguna ronda real registrada — la compuerta de vida o muerte de la réplica
(Casper cambia ≥1 de cada 5) **no se ha medido todavía**. La primera sesión con
rondas reales debe llevar `MAGI_REPLICA_SOMBRA=1` activo para alimentarla.

---

## 7. Pendiente del megaplan v9 (Ritsuko) — con su tabla de estado

| # | Acción | Estado |
|---|---|---|
| G1 | Techo por envío (2 s) + descarte de clientes muertos + medición del retraso | ✅ |
| G2 | El ruido (TERMINAL_OUT) no desaloja lo que el usuario necesita ver | ✅ |
| G3 | La deriva exige mayoría estricta de canarios correctos | ✅ |
| G4 | Tregua de arranque 120 s + `_enjambre_ocupado()` con encolado + doble comprobación | ✅ |
| R1 | Ritsuko revisa y puede **anular** las derivas de Naoko (`ritsuko.veto_de_deriva`) | ✅ |
| R2 | Ritsuko mide el retraso percibido (user_message → eco > 2 s = hallazgo) | ⏳ siguiente |
| R3 | Ritsuko decide cuándo puede medir la sonda (portera) | ⏳ **tras rodar G4** — regla simple que funciona > decisión inteligente sin verificar |
| R4 | Segunda firma de Ritsuko en las entregas (antes de decir «hecho» al usuario) | ⏳ siguiente |

Lo que **no** se le da nunca a Ritsuko: escribir código, tocar el reparto, hablar
con los tres nodos. Su valor entero es ser independiente de lo que juzga.

---

## 8. Deuda diferida, con sus precondiciones (bloque P)

Estas NO se atacan por libre. Cada una tiene una precondición medida:

| Ítem | Qué es | Precondición | Por qué se aplazó |
|---|---|---|---|
| **B7** | Subir el factor de solape de 1,4× a 2,5× | Primero **diagnosticar** dónde se serializan los 294 s de espera en 206 s de pared | Reducir el candado «por si acaso» sin diagnóstico es exactamente cómo se meten carreras |
| **B3** | Caché de propuesta por (tarea, ronda, rama) | Tener estables las medidas de B4 delante | Una caché mal invalidada devuelve la propuesta anterior: el usuario ve un sistema que ignora sus correcciones. La de más riesgo de todas |
| **B5** | Una sola política de selección consultada desde las dos puertas | No tocarla a la vez que B4/B7 | Dos cambios simultáneos en el camino caliente impiden saber cuál movió los números |
| **C6** | `TypeError: argument of type 'NoneType'` de HuggingSpace | Reproducible contra el proveedor real | Arreglar a ciegas un adaptador de terceros mete fallos peores. Evidencia guardada en `docs/comparativa/prueba-A-magi.json`. Lo que SÍ está hecho: un proveedor roto ya no se confunde con agotado (C11) |

---

## 9. El emulador — bitácora condensada y Ronda 4

### Lo que la bitácora ya estableció (no lo redescubras)

- **Arquitectura** (A1-A5): `VIDCORE_GPU` rasteriza por software y la GPU solo
  sube/presenta; ya hay hilo de render con doble búfer y descarte (`dropped_presents`);
  el audio ya corre en hilo dedicado; tres modos de CPU (`DYNARM`, `SH2LRU`, `SH2Fast`)
  — comparar propuestas con modos distintos invalida la comparación (R3).
- **El cuello NO está en render** (A7): el camino de render es el **1,27 %** del
  tiempo. Optimizarlo entero sube ~0,2 FPS sobre 17,1. Está en la **emulación SH2**:
  69,9 % (Sonic R), 64,7 % (Panzer, que aun así va a 59,8 FPS), 90,7 % (NiGHTS).
- **Coste por instrucción** (A25): 51 ns/instr en NiGHTS, 57-81 ns en Panzer. Solo
  `SH2Fast` lleva contador; `SH2LRU` y el dynarec siguen sin instrumentar.
- **Cambiar de intérprete no es la palanca** (A26/R15): `SH2LRU` ≈ `SH2Fast` (~44 FPS
  en Sonic R).
- **El disco de NiGHTS llega byte-perfecto** (A23): sync correcto, `SEGA SEGASATURN`,
  región `JTU` válida con BIOS USA. Ni corrupto, ni lector roto, ni región. **R14:
  no volver a sospechar de él.**
- **El síntoma real de NiGHTS** (A19/A24): se queda en la licencia SEGA; lee **3
  sectores del IP.BIN y abandona** (Panzer lee los 16 y streamea); luego busca por
  zonas de audio (FAD 4963→20051) — patrón de una BIOS tratando el disco como CD de
  música. El TOC está bien (A27, `ctrl 0x41` = datos).
- **El dynarec cuelga al primer frame en TRES builds** (`-Ofast`, `-O3`, VPK del CI);
  la caché JIT se aloja bien en `0x82800000`: el fallo es al **ejecutar** el código
  generado. **Pero puede ser específico de Vita3K** (R4: Vita3K decide corrección,
  no rendimiento). En hardware real podría funcionar — **no lo declares roto sin
  una Vita**.
- Rondas ejecutadas: **0** (línea base; el resultado que cambió el plan), **1**
  (instrumentación que se volvió rescate: cinco bloqueos silenciosos arreglados,
  Panzer a 59,8 FPS — el FPS del log mentía, A12), **2** (NiGHTS/input/dynarec/perfil
  SH2 con veredictos R9), **3** (disco byte-perfecto + coste por instrucción).

### Las dos preguntas abiertas de la Ronda 4

1. **Por qué la BIOS abandona el disco de NiGHTS tras 3 sectores del IP.BIN.**
   Descartado: disco corrupto, lector, región, TOC. Siguiente hipótesis: **el lado
   BIOS/CDB** (la BIOS pide, el CDB sirve — algo en lo que la BIOS hace con los
   primeros sectores hace que cambie de opinión sobre qué clase de disco es).
2. **El coste por instrucción de los SH2** — instrumentar `SH2LRU` y el dynarec
   para que la métrica de A25 exista en los tres núcleos, no en uno.

### El puente MAGI↔emulador: cómo la bitácora entra en la ronda

El enjambre lee la bitácora **entera** antes de proponer (`bitacora.py` la inyecta).
Melchior redacta las tres propuestas declarando filosofía y predicción falsable;
si chocan con §5.2 se rechazan **sin compilar** (v5.18.0, `filosofias.choques`);
Balthasar compila/corre/trae números; Casper aplica el criterio §3 y redacta la
entrada de la ronda; al cerrar, **la ronda se escribe en la bitácora y se sube en
el mismo commit que el cambio ganador** — la medición viaja pegada al código que
la forzó.

### Lo que hay que hacer en el emulador para desbloquear las filosofías

- **Levantar A9** (desbloquea la filosofía C): exponer
  `drawn/presented/dropped` en el log. `vidgpu.c` **ya los lleva**; esta build no
  los imprime. Es un cambio C pequeño + build Docker + corrida verificada.
- **Levantar R6** (desbloquea A y B): telemetría de emulación que demuestre que en
  el camino de render queda algo. Hoy no hay evidencia de que quede; hasta que
  exista, R6 sigue en pie y las tres filosofías siguen suspendidas — **y el prompt
  de cada variante ya lo dice** (v5.18.0).

---

## 10. Hallazgos de ESTA auditoría (2-sep-2026) — lo nuevo que trae v10

Verificados contra el código hoy, no copiados de ningún documento:

| # | Hallazgo | Evidencia | Severidad |
|---|---|---|---|
| **D1** | **R16 no está escrita en la bitácora del emulador.** §5.2 termina en R15. R16 («toda corrida trae veredicto de sonido») existe solo en `ronda_verificada.py:126` y en `TRASPASO.md`. El documento que es «la fuente de verdad del ciclo» no contiene una regla que el protocolo ya exige — y `filosofias.REGLAS` tampoco la puede comprobar. | `grep R16` en `docs/BITACORA-OPTIMIZACION.md` del repo del emulador: 0 resultados | Media — consistencia documental |
| **D2** | **El README declara suelo «1472 tests» con ~1651 reales.** No es mentira (el test del README define la cifra como SUELO con 15 % de tolerancia a la baja), pero queda conservador a la baja en ~11 %. Al publicar la próxima versión, subir el suelo declarado. | `README.md:332` vs. notas v5.18.0 (1651) | Baja |
| **D3** | **`TRASPASO.md` está desactualizado**: dice «v5.16.0» y «el siguiente es el 7» cuando Fases 7/8 (v5.17.0) y filosofías (v5.18.0) ya están construidas. Un agente nuevo que siga su §9 reharía trabajo hecho. Este megaplan lo sustituye; al cerrar la sesión, actualizar `TRASPASO.md` (o reemplazarlo por el traspaso nuevo — §18). | `docs/TRASPASO.md:33` («versión 5.16.0»), §5 (fase 7 «pendiente») vs. RELEASE_NOTES v5.17.0/v5.18.0 | **Alta** — es el documento que se le da al siguiente |
| **D4** | **El comentario de `Regla.exige` promete un mecanismo que no existe**: «una regla que bloquea propuestas válidas se desactiva sola a la tercera vez». No hay contador de estorbo implementado; lo único real es el diseño de `exige` (todos los grupos deben aparecer). O se implementa el contador (con test) o se corrige el comentario — un comentario que promete comportamiento inexistente es exactamente la clase de documento-que-no-es-el-sistema que este proyecto caza. | `filosofias.py:185` (docstring) — no hay «desactiva» en código | Media |
| **D5** | **`pertinente()` puede dar falsos positivos** con encargos que mencionen «vita»/«velocidad»/«rápido» sin ser rondas del emulador (p. ej. «acelera la web que muestra el estado de la Vita»). La v5.18.0 acotó las REGLAS a rondas repartidas, pero `pertinente()` sigue siendo la única puerta. Faltan tests de casos borde NEGATIVOS. | `filosofias.py:241-259` (`_RE_OPTIMIZA` ∩ `_RE_EMULADOR`) | Media |
| **D6** | **`REGLAS` cubre 4 de 15** (R1, R6, R14, R15). R7 («no interpretar `GPU timing` como µs/fotograma») es textualmente detectable en una propuesta y no está. Decidir: añadirla con `exige` de dos grupos, o documentar en el módulo por qué solo esas cuatro. | `filosofias.py:193-227` | Baja-media |
| **D7** | **`orchestrator.py` está en su techo EXACTO (1550/1550).** Toda adición futura al orquestador exige extracción previa. Que el siguiente agente lo sepa ANTES de escribir la funcionalidad, no cuando el trinquete lo pare. | `wc -l` | Informativa — condiciona todo el bloque F |
| **D8** | **La compuerta de la réplica sigue sin medir**: `replica.jsonl` sin rondas reales; el «≥1 de cada 5» de la Fase 8 es aún una promesa sin dato. Primera sesión con rondas reales: activar `MAGI_REPLICA_SOMBRA=1` y alimentarla. | `replica.py:184` + notas v5.17.0/5.17.1 | Media |
| **D9** | **25 capacidades del backend sin panel que las pinte** (MAPA-INTERFAZ v5.14.0). Backlog de GUI vivo y medido, útil para I1 (§11). | `docs/MAPA-INTERFAZ.md` | Baja |
| **D10** | **DOS capacidades `sin_comprobar` en el automodelo** (`classify_screen`, `listen_audio`): probadas con sintéticos, nunca contra un juego real. Cualquier corrida verificada de la Ronda 4 es la ocasión de contrastarlas de verdad (`contrastar(prueba, ok, evidencia)`). | `docs/AUTOMODELO.json` | Media — cierra afirmaciones abiertas gratis |

---

## 11. EL PLAN — paquetes de trabajo, en orden

Reglas de orden: primero lo que **desbloquea** (E1), luego lo **barato que previene
retrabajo** (D), luego lo que **usa** lo desbloqueado (E2, E3), en paralelo lo que
mejora el sistema mismo (M, F), y las diferidas solo con su precondición (P).

Cada paquete trae: objetivo · pasos · dónde · pruebas · **compuerta** · qué NO hacer.

---

### D — Consistencia documental (barato, primero, ~1 hora en total)

#### D1. Escribir R16 en §5.2 de la bitácora del emulador

- **Dónde:** `yabausevita-zp/docs/BITACORA-OPTIMIZACION.md`, tabla de §5.2, con su
  hallazgo de origen (Ronda 2 / protocolo v5.14.0).
- **Texto propuesto:** «R16 — Toda corrida trae también veredicto de sonido
  (`listen_audio`); un log limpio no distingue audio continuo de audio a
  trompicones. | Origen: v5.14.0, `scsp_th` gasta lo mismo con audio limpio que
  roto».
- **Compuerta:** el commit de la bitácora viaja solo o con E1; nada más depende.
- **NO:** no renumerar nada; R16 entra al final de la tabla.

#### D2. Subir el suelo de tests del README al publicar la próxima

- **Dónde:** `README.md:332` («1472 tests» → el conteo real del momento).
- **Regla del test:** es un SUELO con 15 % de tolerancia — no lo conviertas en
  igualdad (un test que castiga añadir tests acaba enseñando a no añadirlos; el
  propio docstring de `test_readme_claims.py` lo cuenta).
- **Compuerta:** `pytest tests/test_readme_claims.py` en verde.

#### D3. Actualizar `TRASPASO.md` al estado v5.18.0+

- **Qué:** sección 1 (versión/commit), §5 (fases 7/8 construidas, réplica con
  compuerta sin medir), §9 (el «siguiente» pasa a ser este megaplan v10), y añadir
  el puntero a este documento.
- **Cuándo:** al cierre de la sesión, no antes (si no, vuelve a quedar viejo).
- **Compuerta:** releerlo como si fueras el siguiente agente: ¿podrías empezar sin
  rehacer nada?

#### D4. El comentario de `Regla` que promete lo que no hay

- **Opción A (recomendada):** implementar el contador de estorbo — una regla cuyos
  choques se marcan como «estorbo» (propuesta válida bloqueada) 3 veces se ignora
  con aviso en el prompt, persistido en `magi/data/memoria/` (JSONL, mismo criterio
  que `descartes.jsonl`), con test que compruebe las tres transiciones.
- **Opción B:** corregir el docstring a lo que es («el diseño de `exige` mitiga el
  falso positivo; no hay contador de estorbo»).
- **Compuerta A:** test del contador con los tres estados + reinicio manual;
  **compuerta B:** el docstring ya no afirma nada sin implementación.

#### D5. Tests de casos borde NEGATIVOS en `pertinente()`

- **Qué:** añadir a `tests/test_filosofias_ortogonales.py` casos que NO son rondas
  del emulador y hoy podrían colarse: «acelera la web que muestra la velocidad de
  la Vita», «optimiza el tiempo de subida al servidor», «el Tetris va lento en
  modo velocidad».
- **Si alguno da `True`:** estrechar `_RE_EMULADOR` (p. ej. exigir `yabause|saturn|
  vita3k|emulador|emulacion` y quitar `vita` sola, o exigir co-ocurrencia con
  juego/consola) — **y medir que los encargos reales del emulador siguen dando
  `True`** (control en la misma corrida, R12).
- **Compuerta:** los negativos dan `False` y los positivos históricos («optimiza
  el rendimiento del emulador», «ronda de FPS de NiGHTS») siguen dando `True`.

#### D6. Decidir cobertura de `REGLAS` (R7)

- **Opción A:** añadir R7 a `REGLAS` con `exige` de dos grupos —
  `((gpu timing|gpu_timing), (µs|us por fotograma|por frame|por fotograma))` —
  para cazar propuestas que citen GPU timing como por-fotograma.
- **Opción B:** un comentario de una línea en `REGLAS` explicando el criterio de
  pertenencia (solo reglas que pueden leerse en el TEXTO de una propuesta).
- **Compuerta A:** test con una propuesta que cite «GPU timing: 1200 µs por frame»
  → choque R7 pegado a esa propuesta.

#### D7. (Informativa) `orchestrator.py` en su techo

No es tarea: es una condición. **Antes** de añadir cualquier cosa al orquestador
(bloques F3, F4, F5 lo tocarán), decide el módulo de extracción y su nombre
(`plan_visible.py`, `compuerta_entrega.py`, …). El techo ya obligó tres veces a
extraer y las tres veces el diseño mejoró.

---

### E — El emulador: desbloquear, instrumentar, Ronda 4

#### E1. Exponer `drawn/presented/dropped` en el log (levanta A9)

- **Objetivo:** que la métrica de la filosofía C exista. `vidgpu.c` ya lleva los
  contadores; la build no los imprime.
- **Pasos:** (1) localizar los contadores en `vidgpu.c` y la línea de log
  `GPU timing: composite/upload/display/frames`; (2) añadir al mismo punto la
  impresión de `drawn/presented/dropped` con el MISMO formato de ventana de 5 s
  (no µs/fotograma — R7); (3) build Docker (§12.1); (4) corrida verificada
  (`vita3k_ctl.py run --seconds 60 --windows 6`, §12.2) comprobando que la línea
  sale y los números son plausibles (presented ≤ drawn, dropped = drawn−presented);
  (5) **contrastar el automodelo** si aplica y anotar el hallazgo (A9 pasa a
  «superado por medición», la filosofía C queda desbloqueada); (6) commit de
  emulador + entrada en bitácora **en el mismo commit**.
- **Pruebas MAGI:** ninguna nueva obligatoria; opcionalmente un test de que
  `ronda_verificada` tolera la línea nueva del log.
- **Compuerta:** la línea aparece en una corrida verificada (con `has_image`,
  `has_motion` y veredicto de sonido) en al menos un juego; la bitácora queda
  actualizada con la medición.
- **NO:** no tocar `composite/upload/display` existentes; no «aprovechar» para
  optimizar nada (R6 sigue en pie); no imprimir por fotograma.

#### E2. Instrumentar `SH2LRU` y el dynarec con coste por instrucción

- **Objetivo:** que la métrica de A25 (51-81 ns/instr) exista en los TRES núcleos.
  Es la palanca real según R15, y hoy solo `SH2Fast` la lleva
  (`sh2fast_instr_total`).
- **Pasos:** (1) leer cómo `SH2Fast` acumula instrucciones y tiempo; (2) replicar
  el contador en `SH2LRU` (simetría con el existente, mismo nombre de métrica);
  (3) para el dynarec: contar bloques traducidos + instrucciones emuladas y
  exponer el mismo cociente — **aunque el dynarec cuelgue al primer frame**, el
  contador debe imprimirse ANTES del cuelgue para que la próxima investigación
  tenga número; (4) build Docker; (5) corrida verificada por modo (R3: nunca
  comparar modos mezclados); (6) bitácora: entrada de ronda con la tabla de los
  tres núcleos.
- **Compuerta:** tabla con ns/instr de `SH2Fast`, `SH2LRU` y (parcial) dynarec en
  al menos un juego, con corrida verificada.
- **NO:** no intentar arreglar el cuelgue del dynarec aquí (es la pregunta de
  hardware de E4); no cambiar el intérprete por defecto.

#### E3. Ronda 4 del emulador — la BIOS/CDB de NiGHTS (+ contrastar percepción)

- **Objetivo:** responder por qué la BIOS abandona el disco tras 3 sectores del
  IP.BIN. Hipótesis activa: lado BIOS/CDB — la BIOS decide que es un CD de música
  (patrón de búsqueda FAD 4963→20051, A24).
- **Pasos:** (1) sonda de traza en el camino BIOS↔CDB (ya existe precedente: la
  sonda `CDREAD` de `cd_chd.c` que dio A23); registrar QUÉ pide la BIOS (sector,
  comando, longitud) y QUÉ contesta el CDB, en los primeros 16 sectores, en NiGHTS
  y en Panzer **en la misma corrida de análisis** (control incluido); (2) comparar:
  ¿la BIOS de NiGHTS pide distinto, o el CDB contesta distinto con el mismo pedido?;
  (3) según la bifurcación, seguir el lado que difiera (registro del CDB en
  `saturn.c`/bios o en `cd_chd.c`); (4) escribir la entrada de Ronda 4 en la
  bitácora con la plantilla §4 (hipótesis, medición, ganadora, sin comprobar,
  hallazgos, reglas nuevas si las hay); (5) **de regalo, en las mismas corridas:
  contrastar `classify_screen` y `listen_audio` contra juego real** (D10): llamar
  a las herramientas sobre las capturas/audio de la corrida y registrar
  `contrastar(prueba, ok, evidencia)` en el automodelo — dos afirmaciones
  `sin_comprobar` se cierran sin trabajo extra.
- **Compuerta:** la entrada de Ronda 4 existe con evidencia medida (traza
  petición/respuesta), o con un «sin comprobar» honesto si la sonda no alcanza;
  el automodelo registra el veredicto de `classify_screen`/`listen_audio`.
- **NO:** no volver a sospechar del disco (R14); no citar FPS de Vita3K como
  rendimiento (R4); no cerrar la ronda sin capturas (R9).

#### E4. El dynarec — solo con hardware real

Mantenido EXACTAMENTE como lo dejó el traspaso: cuelga al primer frame en tres
builds; puede ser específico de Vita3K; **no se declara roto sin una Vita real**.
Si el usuario consigue hardware: el plan es instalar el VPK del CI, correr con
corrida verificada si es posible capturar, y contrastar la afirmación refutada del
automodelo («`SH2DynARM` arranca el juego») en ambas direcciones. Sin hardware:
nada que hacer aquí.

---

### M — MAGI calidad (megaplan v9 pendiente)

#### M1. Ritsuko R2 — guardiana del reloj percibido

- **Objetivo:** que el retraso usuario→pantalla (>2 s) lo mida el sistema, no el
  usuario. Ya ocurrió una vez (eco de Naoko a 10,6 s — v9 §1) y el detector fue
  el usuario.
- **Pasos:** Ritsuko ya marca cada evento con timestamp; añadirle la medición
  `user_message → eco en el bus` por agente y un hallazgo `ritsuko.retraso_percibido`
  cuando supere 2 s. Es SOLO lectura/escritura de informe — no toca reparto (su
  valor es ser independiente de lo que juzga).
- **Dónde:** `magi/modules/infrastructure/ritsuko.py`; techo propio (662 líneas,
  margen).
- **Pruebas:** evento rápido no genera hallazgo; evento tardío sí; y el control:
  el mismo par de eventos con timestamp artificialmente separado en la MISMA
  corrida (R12).
- **Compuerta:** en una sesión real con la GUI, un eco retrasado a propósito
  (p. ej. inyección de latencia en el socket de prueba) produce el hallazgo con
  su número; un eco normal no produce nada.

#### M2. Ritsuko R4 — segunda firma en las entregas

- **Objetivo:** antes de decir «hecho» al usuario en un encargo de producto con
  `APPROVED`, Ritsuko comprueba la evidencia de entrega
  (`entrega.artefactos_listos`, `entrega.marcada_incompleta`) y firma. Es C12/D3
  con un segundo par de ojos que no tiene nada que defender.
- **Pasos:** suscribir a Ritsuko al cierre de entrega; si la evidencia no
  sostiene el `APPROVED`, el evento lleva la objeción (hecho auditable, no orden).
- **Compuerta:** un cierre sin artefacto llega al usuario CON la firma de
  advertencia de Ritsuko visible; un cierre con artefacto llega con firma limpia.
- **Sinergia:** esto es la mitad de la Fase 4 (F2) hecha desde el lado auditor;
  la otra mitad (el «hecho» no se emite sin `verificar.py`) es la F2.

#### M3. Ritsuko R3 — portera de la sonda (condicional)

**Solo tras rodar G4** en uso real (la regla simple primero; la decisión
inteligente después, tal como quedó escrito en v9 §5). Si G4 no ha acumulado uso
real, este paquete NO se empieza.

---

### F — Las fases pendientes del v6, en su orden original (1→2→3→4→5)

⚠️ D7 aplica a todas: el orquestador está en su techo; extraer módulo ANTES de
escribir. ⚠️ D8 aplica a la primera sesión de rondas reales: `MAGI_REPLICA_SOMBRA=1`
activo para alimentar la compuerta de la réplica.

#### F1. Búsqueda web sin ventana (`web_search`, `web_read`)

- **Diseño (del v6, se mantiene):** buscador con endpoint HTML sin JS, parseo a
  título+URL+extracto; `web_read` con extracción legible, límite de tamaño y UNA
  redirección. **Sin navegador** (nada de Selenium/Playwright: rompen el arranque
  portable del `.exe`). Presupuesto de consultas POR RONDA (como el de tokens).
  Cita obligatoria con URL y fecha. Sin red → SIN COMPROBAR, nunca inventado.
- **Dónde:** módulo nuevo (`magi/modules/percepcion/web.py` o `tools/`), registro
  en el enjambre (el contador del README subirá — actualizar README en el mismo
  commit, D2).
- **Pruebas:** parseo con HTML fixture; presupuesto que se agota y se niega en
  claro; sin red → SIN COMPROBAR; la cita viaja con URL+fecha.
- **Compuerta:** Balthasar refuta una afirmación de Melchior citando una URL que
  encontró ÉL, no una que le dieron.

#### F2. Subagentes por familia

- **Diseño:** el subagente es de la MISMA familia que su nodo (Melchior/gpt
  despacha gpt; Balthasar/gemini despacha gemini). Solo lectura; devuelve
  **conclusión, no volcado**; temperatura baja, turno único; tope duro por nodo y
  ronda; traza visible (si trabaja y no se ve, es el `MetricsCollector` que
  publicaba métricas que ningún panel pintaba).
- **Compuerta:** una ronda con subagentes gasta MENOS contexto por nodo que la
  misma ronda sin ellos. Si gasta más, el mecanismo está mal y SE RETIRA.
- **Sinergia natural con F1:** el explorador que busca en la web es el caso de
  uso canónico.

#### F3. Plan visible con estado (`plan.md` por tarea)

- **Diseño:** una línea por parte del encargo con estado
  (`pendiente`/`haciendo`/`hecha`/`no se pudo`), inyectado en el prompt y pintado
  en la GUI (nace de la regla 8 «se contestan todas las partes», hoy norma sin
  mecanismo). Un encargo de ocho partes contestado en seis se ve MIENTRAS pasa.
- **Compuerta:** Casper no cierra con partes `pendiente` sin decir por qué.
- **GUI:** el panel de plan es «lo único de mi interfaz que MAGI no tiene y que
  cambia cómo se trabaja» (v6 §interfaz) — I1 puede empezar por él.

#### F4. La compuerta deja de ser opcional

- **Diseño:** antes de que Casper diga «hecho», el sistema corre
  `scripts/verificar.py` (modo `--rapido` para el cierre de ronda; el completo
  antes de publicar) y adjunta el resultado. No es que el agente *pueda* correrlo:
  su «hecho» **no se emite** sin él.
- **Compuerta:** una entrega sin verificación adjunta se rechaza sola.
- **Ojo:** es el fallo del propio agente anterior convertido en mecanismo — las
  cuatro afirmaciones refutadas del automodelo incluyen «corro la compuerta antes
  de publicar». Que el mecanismo la haga infalible, no la virtud del agente.

#### F5. Veredicto «la pregunta era otra»

- **Diseño:** cuarto veredicto además de gana/pierde/empata. Cuando la medición
  demuestra que las tres propuestas atacan algo irrelevante (como el 1,27 % del
  render), la ronda se cierra SIN ganador, se registra en bitácora y la siguiente
  arranca desde la métrica nueva. La mitad ya existe: la bitácora sabe guardar
  descartes con lo rescatable.
- **Compuerta:** una ronda sintética cuyas tres propuestas ataquen lo prohibido
  por R6 cierra con «la pregunta era otra» y sin ganador, y el registro queda en
  bitácora/descartes.

---

### I — Interfaz (backlog medido, no bloqueante)

#### I1. Panel de plan + traza de subagente plegada + citas web pinchables

Depende de F3 (panel de plan) y F1/F2 (traza y citas). El MAPA-INTERFAZ se
**regenera** (nunca se edita a mano) y el trinquete de topics debe seguir en verde
(0 topics sin destinatario). Las 25 capacidades sin panel (D9) son el backlog:
elegir por orden de valor al usuario, no por comodidad.

#### I2. Regenerar `MAPA-INTERFAZ.md` tras cada cambio de topics

Es parte de la compuerta de cualquier cambio GUI: el mapa se regenera y el
trinquete cuenta comandos y eventos por separado (la primera versión confundió
direcciones y declaró 21 «paneles muertos» inexistentes).

---

### P — Diferidas: SOLO con su precondición medida

| Paq | Hacer | Precondición (medida, no supuesta) |
|---|---|---|
| P1 (B7) | Subir solape 1,4×→2,5× | Diagnóstico de dónde se serializan los 294 s de espera en 206 s de pared |
| P2 (B3) | Caché de propuestas (tarea, ronda, rama) | Medidas de B4 estables; y recordar: una caché mal invalidada = el sistema ignora las correcciones del usuario |
| P3 (B5) | Política única de selección | No simultáneo con P1/P2 (saber qué cambio movió el número) |
| P4 (C6) | Arreglar HuggingSpace `TypeError: NoneType` | Reproducible contra el proveedor real (evidencia en `docs/comparativa/prueba-A-magi.json`) |

---

## 12. Procedimientos operativos

### 12.1 Compilar YabauseVita (no hay toolchain local; Docker, validado)

```bash
docker run --rm -v "C:\Users\D\Documents\GitHub\yabausevita-zp:/src:ro" \
  -v "C:\Users\D\Documents\GitHub\build-docker:/out" ubuntu:24.04 bash -c '
  apt-get update -qq && apt-get install -y -qq git wget curl bzip2 xz-utils \
    cmake clang-18 lld-18 build-essential python3
  cp -r /src /work && chmod -R u+w /work
  cd /tmp && git clone --depth=1 https://github.com/vitasdk/vdpm.git && cd vdpm
  export VITASDK=/usr/local/vitasdk PATH="/usr/local/vitasdk/bin:$PATH"
  ./bootstrap-vitasdk.sh
  export VDPM_NONINTERACTIVE=1
  vdpm zlib libvita2d          # vdpm del PATH, NO ./vdpm del checkout
  cd /work && mkdir build && cd build
  cmake -DVITASDK=/usr/local/vitasdk \
    -DCMAKE_TOOLCHAIN_FILE=/usr/local/vitasdk/share/vita.toolchain.cmake \
    -DCMAKE_BUILD_TYPE=Release ..
  cmake --build . -- -j$(nproc)'
```

**Trampa:** `./vdpm` del checkout busca `pacman` en `bin/`; el bootstrap nuevo lo
pone en `libexec/vdpm/`. Eso rompió el CI desde el 23-ago. Usa el `vdpm` del PATH.

### 12.2 Medir una corrida

```bash
python tools/vita3k_ctl.py run --seconds 60 --windows 6
```

Lanza Vita3K **sin elevar** (vía `explorer.exe`) y **sin el OpenSSL de Git en el
PATH**, arranca solo (`autostart=1`), captura la ventana **del juego** (Vita3K
abre dos; la del juego es la de cliente 960×544 — A17) y devuelve FPS, métricas
EMU, `has_image`, `has_motion`.

**Config:** `%APPDATA%\Vita3K\Vita3K\ux0\data\yabause\config.cfg`:
`cpu_mode=2` (DYNARM), `auto_bios=0` + `bios_path` explícito, **sin BOM** (A16).

### 12.3 Antes de publicar MAGI

§4, la compuerta completa. `python scripts/publicar.py` al final. Notas de release
**concretas** («qué cambió y qué se midió»), nunca genéricas. Los releases
anteriores se conservan.

### 12.4 Escribir ficheros de texto/config sin BOM

Python, `open(..., 'w', encoding='utf-8', newline='\n')`, y verificación
`datos[:3] != b'\xef\xbb\xbf'`. Nunca `Set-Content -Encoding UTF8` de PowerShell.

### 12.5 Entorno de subprocesos

Esta máquina tiene `NODE_ENV=production`, con lo que `npm ci` se salta TypeScript,
Vite y Vitest — solo pasa en local. `scripts/verificar.py` ya lo limpia
(`_entorno()`); cualquier script nuevo que invoque npm debe hacer lo mismo. `npm`
en Windows es `npm.cmd` (`shutil.which` lo resuelve).

---

## 13. Trampas que ya costaron tiempo (no las pagues otra vez)

| Trampa | Síntoma | Arreglo |
|---|---|---|
| **BOM** | `sscanf` lee `\ufeffrom_path` y lo ignora en silencio; `pyproject.toml` roto | Escribir con Python, `newline='\n'`, comprobar los 3 bytes (§12.4) |
| **Ruff sin fijar** | Verde en local, rebota en CI | `ruff==0.16.5` en requirements-dev; no actualizarlo por libre |
| **Trinquetes** | Cuatro tipos (§3) | Nunca subir techos; conectar, adelgazar o corregir |
| **OpenSSL de Git** | Vita3K muere con `EVP_MD_CTX_get_size_ex` | Lanzarlo con `Git\mingw64\bin` fuera del PATH |
| **Vita3K elevado** | Aviso de propietario equivocado en `ux0` | Lanzar vía `explorer.exe` (sin elevar) |
| **Caché CHD corrupta** | `Unsupported CD image` (−2) | Apartar el `.bin`; se reextrae (~524 MB/juego — ojo con C:) |
| **Buffering de pytest** | La salida se queda en el 22 % | Esperar a que el PID muera; no interpretar el % |
| **`NODE_ENV=production`** | npm se salta TS/Vite/Vitest solo en local | `_entorno()` de verificar.py; replicarlo |
| **`npm` en Windows** | `FileNotFoundError` en subprocess | `shutil.which('npm') or shutil.which('npm.cmd')` |
| **Dos ventanas de Vita3K** | Se captura la GUI en vez del juego | Por PID y tamaño de cliente 960×544 (A17) |
| **FPS del log del emulador** | Un intérprete roto «hace 60 FPS» (A12) | Solo vale con verificación de imagen (R9) |
| **Módulo en disco y no en git** | Suite local verde, CI ImportErro (v5.11.0) | `test_nada_sin_versionar.py` — añadir al git SIEMPRE antes de publicar |
| **Fichero de compuerta sucio** | `replica.jsonl` con datos de prueba midiendo la prueba (v5.17.1) | Aislamiento por defecto + guardián; comprender la fuente, no el síntoma |

---

## 14. Restricciones de la máquina (no se negocian)

**El hardware no se toca; no se instalan descargas grandes.**

- `DESKTOP-B6D864U` · Windows 10 22H2 (19045.6466) · i7-3770 · 24 GB · **GTX 1050
  2 GB** · `torch 2.13.0+cpu` (sin CUDA): da para embeddings, **no** para un LLM
  local. La rueda CUDA serían 2,5 GB — no.
- **C: ~10 GB libres** (Docker ya ocupa 15,8 GB; cada extracción CHD son 524 MB).
  **D: ~37,8 GB libres.**
- **Windows sin parches desde el 18-nov-2025.** Riesgo abierto, aplazado por
  decisión del usuario. No es tarea del agente, pero está encima de todo.
- Docker disponible (builds VitaSDK). Vita3K instalado (con sus trampas §12.2).
- Sin teclado/juego físicos de Vita: el input se mide por protocolo (A20/A21).

---

## 15. El ritual de cierre de cada ronda (no opcional — es lo que hace que el sistema mejore en vez de repetirse)

1. **Registra los descartes** en `magi/data/memoria/descartes.jsonl` con su
   medición y el campo `rescatable`. Un enfoque que pierde deja conocimiento igual
   que uno que gana, y suele dejar más.
2. **Contrasta el automodelo:** `contrastar(prueba, ok, evidencia)`. Si una
   afirmación se cae, que se caiga sola, con su evidencia.
3. **Añade hallazgos y reglas** a la bitácora (con origen), y la entrada de la
   ronda con la plantilla §4 — en el MISMO commit que el cambio ganador.
4. **Publica** con notas concretas (qué cambió, qué se midió, qué se encontró
   probando lo ya escrito — esas secciones valen oro), conservando TODOS los
   releases anteriores.
5. **Actualiza los documentos de traspaso** (TRASPASO.md / este megaplan) para que
   el siguiente no rehaga nada.

---

## 16. Lo que nunca se hace

- No borrar releases anteriores.
- No subir el techo de un trinquete ni tocar `KNOWN_ORPHANS`.
- No citar FPS de Vita3K como prueba de rendimiento (R4).
- No escribir a mano un documento que se genera.
- No declarar «no funciona» lo que está «sin comprobar».
- No optimizar el camino de render sin la telemetría que levante R6.
- No volver a sospechar del disco de NiGHTS (R14).
- No proponer un JIT nuevo de SH-2 (R1); no comparar propuestas con `cpu_mode`
  distinto (R3); no medir con el audio apagado (R2).
- No dar a Ritsuko escritura de código, reparto, ni voz con los tres nodos.
- No instalar descargas grandes ni tocar el hardware.
- No resucitar la Fase 9 (embeddings) — retirada con motivo escrito.
- No dejar un test de tiempo con umbral absoluto sin control en la misma corrida (R12).

---

## 17. Criterios de aceptación de la sesión (lo que «terminar» significa)

1. **Compuerta completa en verde** antes de cualquier publicación: ruff completo,
   huérfanos ≤ 80, suite completa, `verificar.py --todo`.
2. Cada paquete terminado con **su** compuerta cumplida y con la evidencia dicha
   (número, captura o traza — no «parece que sí»).
3. La bitácora del emulador con las entradas de las rondas ejecutadas, en el mismo
   commit que los cambios.
4. `descartes.jsonl` y el automodelo actualizados con lo aprendido (incluidas las
   afirmaciones que se caigan — especialmente las del propio agente).
5. README coherente (contador de herramientas y suelo de tests).
6. `TRASPASO.md` y este megaplan actualizados al estado final real (§18).
7. Si algo no se pudo comprobar, está escrito como SIN COMPROBAR — no rellenado.

---

## 18. Cómo dejar el traspaso al siguiente

Lo mismo que hicieron las sesiones anteriores:

1. Actualiza este fichero (o su sucesor) marcando qué paquetes quedaron hechos,
   con qué evidencia, y cuáles siguen abiertos y por qué.
2. Actualiza `TRASPASO.md` al estado real (D3): versión, commit, fases, siguientes.
3. Deja los descartes con lo rescatable y el automodelo contrastado.
4. Publica con notas concretas.
5. **Regla de oro del proyecto:** si algo de lo escrito contradice al código,
   gana el código — y se corrige el documento en el mismo commit.

---

*Fin del MEGAPLAN v10. Verificado contra el código el 2-sep-2026. Si el código
ha cambiado desde entonces, gana el código.*

## Publicación — cierre de la sesión

- **v5.19.0 publicada por CI** (tag `v5.19.0`, workflow 8m43s en verde):
  `MAGI-IDE-v5.zip` 143,4 MB + `CHECKSUMS.txt`
  (zip sha256 `13af1e3b7843…`). El `.exe` del CI no arrastra los dos fixes
  post-release —ambos de cara al desarrollo, no al binario— que viajan en
  `main` desde ya.
- **`publicar.py` (vía local) se frenó con razón**: 9 dependencias directas
  divergen de `requirements.lock` (g4f 7.9.4 vs 8.1.1, websockets 16 vs 12…).
  El entorno local es el medido; el lock, el del CI. Alinear una de las dos
  partes es tarea de la próxima sesión, con la suite delante.
- **El CI cazó un flaky real** en `test_el_recon_tardio_se_cancela`: el
  «tardío» era absoluto (5 s) y un runner cargado lo convertía en «a tiempo».
  Endurecido a relativo (12 s). El CI del commit anterior pasó con el mismo
  código: varianza, no regresión — y el fix la elimina igualmente.

## Aprendizajes de cierre de la sesión (2-sep-2026, tarde)

- **Un `str.replace` sin `assert` es un no-op silencioso.** El segundo intento
  de quitar la cadena «v3.0» del comentario de App.tsx no cambió nada y el
  mapa de interfaz lo volvió a cazar como topic huérfano. La tercera vez
  llevó `assert viejo in t` y `assert '"v3.0"' not in resultado`. Mismo
  espíritu que la regla de los BOM: comprobar el efecto, no confiar en la
  intención.
- **La ronda real sobrevivió a un sueño de la máquina** (salto de reloj
  01:41 → 05:16) y siguió reintentando proveedores, pero nunca cerró:
  `task_completed` no llegó. El sistema es resiliente; el cierre bajo
  interrupciones largas no está garantizado. Candidato a hallazgo de la
  próxima ronda de auditoría.
- **Una tarea trivial en modo profundo no cabe en la paciencia de nadie** con
  proveedores gratuitos. Naoko clasificando «trivial → motor fast» es la
  mejora de UX con mejor retorno pendiente.
