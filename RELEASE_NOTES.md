# v5.17.1 — dos cosas que dije y no eran ciertas

Ninguna de las dos era del mecanismo. Las dos eran de cómo lo estaba midiendo,
que es peor: un instrumento que miente no avisa de que miente.

## 1. Un test de tiempos que medía el runner, no el código

`test_el_recon_cabe_en_la_ventana_de_melchior` afirmaba `t_melchior_ms < 900`.
El runner de `windows-latest / 3.10` midió **4531** y tumbó el CI.

El arreglo no era subir el umbral. Un umbral absoluto **no distingue** «el
recon se absorbió» de «la máquina va cargada», así que no puede decidir nada.

Y la prueba de que el mecanismo estaba bien la di yo al medirlo otra vez en
esta misma máquina, donde había pasado: **1218 ms**. Por encima de los 900 que
el test exigía. O sea que el umbral tampoco valía aquí — las veces que pasó
fue por suerte, no porque midiera algo. Los dos jobs de Ubuntu pasaron, y el
`lint` y el `gui` también; cayó solo `windows-latest / 3.10`, que es el runner
más caro y más cargado de la matriz. El número que cambiaba era el de la
máquina, no el del código.

Reescrito contra un **control medido en la misma corrida**: el mismo montaje
con el recon a 5,0 s en vez de 0,3 s. Si el recon corriera dentro de la
ventana de Melchior, la fase crecería ~4,7 s. Medido: **decrece 578 ms**, que
es la firma de un recon cancelado por llegar tarde. Un runner lento escala los
dos lados igual, así que la comparación sigue diciendo lo mismo.

Y buscando hermanos apareció otro con el mismo defecto en la misma fase —
`pared_con < 3.0`— que habría caído en el push siguiente. Retirado: la
comparación relativa de la línea de al lado ya cubría el caso entero, así que
la constante solo aportaba fragilidad.

Es la regla **R12**, la que se aprendió midiendo input en el emulador: *se mide
contra un control, no contra una constante*. La tenía escrita y la incumplí.
Está anotada en el automodelo como afirmación **refutada**, con su evidencia.

## 2. El registro de la compuerta estaba sucio, y yo dije que estaba vacío

Las notas de la v5.17.0 decían que `replica.jsonl` estaba «vacío a propósito».
No lo estaba: llevaba **10 filas** con `task_id: "t-r"`.

Yo mismo había quitado dos a mano días antes, y volvieron. Esa era la señal y
no la leí: quitar el síntoma sin cerrar la fuente no arregla nada. La fuente
era que `_ronda` solo aislaba `MAGI_MEMORIA` **cuando el test quería leer el
registro**; las otras tres rondas escribían en el fichero del repo, dos filas
por cada corrida de la suite.

Importa porque ese fichero es la única evidencia que puede **retirar** la
réplica. Medido sobre datos de prueba, mide la prueba — que es literalmente lo
que la propia cabecera del fichero prohíbe.

Ahora el aislamiento es el valor **por defecto**, no una opción, y hay una
prueba que falla si el fichero vuelve a ensuciarse. Comprobado como se
comprueba una compuerta: ensuciándolo a propósito para ver que salta, y
corriendo la suite entera después para ver que ya no entra nada.

---

**1632 pruebas, cero fallos**, ruff limpio, huérfanos en 80. Sin cambios de
comportamiento: las dos fases hacen lo mismo que en la v5.17.0.

---

# v5.17.0 — el enjambre deja de esperar en fila, y Melchior contesta

**Qué cambia:** las dos fases que quedaban del plan de rendimiento y calidad.

**Lo concreto:**

- **Fase 7, abanico paralelo.** Se solapa lo que no depende: la recogida de
  evidencia con la redacción de la tesis, las variantes entre sí, los ejes de
  crítica entre sí, y la verificación **en cascada** según llegan las variantes.
  Medido a través del orquestador real: **3141 ms → 1937 ms, un 38 % menos**.
- **38 %, no el 66 % que yo había prometido.** Ese 66 % salió de un banco
  sintético de tres esperas independientes; la ronda real tiene una dependencia
  irreducible —Balthasar no puede refutar una tesis que aún no existe— y esa no
  se paraleliza. Cuando la medida sintética y la del sistema real discrepan,
  gana la del sistema real.
- **`MAGI_ABANICO=0`** vuelve al modo serial. Una optimización sin forma de
  apagarla no se puede comparar consigo misma.
- **Fase 8, la réplica.** Melchior contesta a la objeción **antes** de que
  Casper arbitre. Condicional (solo si hay objeciones reales, firmadas con
  `OBJECIONES: N`), acotada (1400 caracteres de extracto, 900 de réplica, sin
  herramientas), una sola vuelta, y con salida: si empieza con `CONCESIÓN:`, el
  debate cierra antes del arbitraje.
- **Su compuerta viene armada.** `MAGI_REPLICA_SOMBRA=1` corre el arbitraje
  contrafactual y anota si el veredicto cambió. Si Casper no cambia al menos 1
  de cada 5, la réplica se retira. El registro está **vacío a propósito**: aún
  no ha corrido ninguna ronda real, y una compuerta medida sobre datos de
  prueba mide la prueba.
  > **Errata (v5.17.1).** Esa última frase era falsa cuando se escribió: el
  > fichero llevaba dentro 10 filas de prueba. Corregido en la v5.17.1, con la
  > fuente cerrada y un guardián que lo impide.

- **El techo de líneas obligó a mejorar el diseño.** `orchestrator.py` estaba a
  7 líneas de su tope: se extrajo `contraste.py` y la mecánica del cierre pasó a
  `replica.py`. Quedó más corto que antes con más funcionalidad.
- **El trinquete de huérfanos señaló tres piezas sin sitio de llamada externo.**
  No se escondieron haciéndolas privadas: se les escribió prueba directa, y ahí
  aparecieron sus modos de fallo — si la réplica revienta la ronda se arbitra
  sin ella, y la réplica trabaja sobre una copia para no dejar a Melchior con
  `hedge=False` el resto de la ronda.

**27 pruebas nuevas** entre las tres fases. Ruff limpio, huérfanos en 80,
suite completa en verde antes de publicar.

---

# v5.16.0 — buscar sin gastar red, y saber qué de uno mismo es falso

**Qué cambia:** dos capacidades que no consumen cuota, y una corrección honesta
de lo que yo mismo había propuesto en el megaplan.

**Lo concreto:**

- **`magi/modules/memory/indice.py`** — FTS5 sobre bitácora, memoria, docs y
  código. Responde «¿esto ya se intentó?» **sin gastar una llamada de red**.
  Medido sobre el corpus real: 224 documentos, 2,7 MB, índice completo
  reconstruido en **100 ms**, consulta en **1 ms**.
- **Sin persistencia, sin embeddings, sin GPU — y eso es la decisión, no una
  limitación.** Reconstruir cuesta menos que razonar sobre si el índice está al
  día. Y proponer un modelo de 90 MB para buscar en 2,7 MB era sobre-ingeniería
  mía: la Fase 9 del megaplan queda **retirada**, con su motivo escrito.
- **Buscar `1.27` daba `fts5: syntax error near "."`.** Un buscador que falla
  cuando le pasas un número es un buscador que nadie usa dos veces. Ahora sanea
  la consulta y conserva `AND`, `OR`, `NOT`, `NEAR` y las comillas.
- **`magi/modules/swarm/automodelo.py`** — lo que MAGI cree de MAGI, con la
  prueba que puede tumbarlo. **Una afirmación sin prueba no se admite**: «soy
  bueno razonando» es una opinión, no una afirmación sobre uno mismo.
- **Sembrado con esta sesión: 8 afirmaciones, 4 refutadas por la realidad.** El
  dynarec no arranca (tres builds), NiGHTS no llega al título, el experimento de
  input no aísla la pulsación — y *«corro la compuerta antes de publicar»*, que
  es sobre quien escribe esto y la desmintieron cuatro rebotes en un día.
- **`sin_comprobar` es un estado de primera clase**, no «verdadera hasta que se
  demuestre lo contrario». Y al prompt solo viaja lo refutado y lo frágil: lo
  que se sostiene sin fallar ocupa contexto y no cambia ninguna decisión.
- **Sexta inyección.** La secuencia pasa a aceptación → caja → bitácora → ronda
  → memoria → automodelo, con su test de lista exacta.

Cierra el hueco que la Ronda 0 dejó al descubierto: cuando la medición invalidó
el plan entero, el sistema no tenía dónde anotarlo.

**32 pruebas nuevas.** Ruff 0.16.5 limpio, huérfanos en 80, trinquetes en verde.

---

# v5.15.0 — vista: leer la pantalla como la lee una persona

**Qué cambia:** R9 dio ojos («¿hay algo y se mueve?») y R16 oídos. Ninguno de
los dos sabía **qué** estaba pasando en pantalla. Ahora sí.

**Lo concreto:**

- **`magi/modules/percepcion/vista.py`** con `classify_screen` registrada en el
  enjambre. De una captura saca: en qué clase de pantalla estamos (negro,
  carga, licencia, menú, título, partida), en qué **idioma** habla el juego, y
  **qué botón está pidiendo** — validado contra la memoria de mandos de esa
  consola, para no mandar al agente a pulsar una tecla que el mando no tiene.
- **«NiGHTS se queda en la licencia» pasa a ser comprobable.** En la Ronda 2
  eso hubo que averiguarlo mirando una captura a mano y describiéndola; ahora
  lo dice una función.
- **`Zonas`: FPS por clase de pantalla.** «Va lento» sin decir dónde no es
  diagnóstico: un juego a 60 en el menú y a 17 en partida tiene media 38, y 38
  no ocurre nunca. El informe señala la zona lenta y **avisa por escrito** de
  que su propia media entre clases no describe ninguna pantalla.
- **El idioma se detecta con confianza declarada.** «START» acierta en inglés y
  en nada más, pero un empate a uno entre dos idiomas es una moneda al aire, no
  una detección: la confianza mide la distancia al segundo candidato, no los
  aciertos. Y el japonés se detecta por escritura (kana), no por palabras.
- **Un fallo que solo aparece con OCR real.** Tesseract leyó «PULSA START PARA
  JUGAR» como `PULSASTARTPARA JUGAR`. Un patrón con `\b` detrás del verbo no
  encuentra nada ahí, y ese es el caso normal, no el raro. Hay segunda pasada
  para texto pegado y test de regresión con las cadenas sucias de verdad.
- **Sin OCR se dice SIN COMPROBAR**, igual que los oídos. Una capacidad ausente
  no es un resultado negativo.

**36 pruebas nuevas.** El juicio vive separado de la captura, así que se prueba
con imágenes sintéticas y con OCR real, sin emulador delante.

---

# v5.14.0 — oídos, y el mapa del cable entre la pantalla y el núcleo

**Qué cambia:** R9 puso ojos a las corridas. Faltaban dos cosas: **oír** si el
audio sale entero, y saber qué partes de la interfaz están **realmente
cableadas** al núcleo.

**Lo concreto:**

- **`magi/modules/percepcion/`** — los oídos, con `listen_audio` y
  `audio_available` registradas en el enjambre (52 herramientas). Capturan el
  loopback WASAPI y distinguen tres cosas: `has_sound` (¿salió audio?),
  `choppy` (¿salió entero?) y `sonando_pct`. El log no puede: en YabauseVita
  `scsp_th` gasta los mismos 1,1-1,4 s por ventana con audio limpio que con
  audio a trompicones.
- **«Sin oídos» ≠ «no suena».** Si la máquina no tiene backend (medio CI corre
  en Linux), la herramienta devuelve **SIN COMPROBAR** y lo dice. Inventar un
  veredicto negativo era el fallo que R9 corrigió del lado de la imagen.
- **El veredicto se prueba sin tarjeta de sonido** — vive separado de la
  captura y se le pasan señales sintéticas: continua, silencio, y troceada.
  Un juicio que solo se puede probar con el hardware delante es un juicio que
  nadie prueba, y miente el día que importa.
- **R16 en el protocolo de corrida** — `ronda_verificada` ahora exige el
  veredicto de sonido junto a los de imagen y movimiento.
- **`magi/modules/gui/mapa.py` + `docs/MAPA-INTERFAZ.md`** — el mapa del
  cableado por topics entre `magi-gui/src` y `magi/`, generado y no escrito a
  mano. Resultado medido: **19 comandos conectados, 23 eventos conectados, 0
  topics sin destinatario** y 25 capacidades que el backend emite y ningún
  panel pinta.
- **La primera versión del mapa mentía y por eso hay test.** Contaba un solo
  sentido y declaró 21 «paneles muertos», entre ellos `task.archive`, que
  tiene handler en `kernel.py:72` — la UI lo **manda**, no lo escucha. Un mapa
  que confunde las direcciones manda al enjambre a arreglar 19 fallos
  inexistentes. Ahora comandos y eventos se cuentan aparte, con trinquete.

**34 pruebas nuevas** (18 de oídos, 16 del mapa).

---

# v5.13.0 — memoria permanente: lo descartado deja de perderse

**Qué cambia:** MAGI gana memoria que sobrevive a la tarea, a la sesión y a la
máquina. Hasta ahora `EpisodicMemory` respondía «no repitas esto» dentro de un
`task_id` y moría con él; lo que faltaba era el otro lado: **qué se salvó de
cada enfoque descartado**.

**Lo concreto:**

- **`magi/modules/swarm/memoria_persistente.py`** — lee `magi/data/memoria/`,
  versionado en git, y lo inyecta arriba del prompt. Vive en el repo a
  propósito: la memoria que vive en `%APPDATA%` no viaja con el sistema, no se
  revisa en un diff y se pierde al reinstalar — que es exactamente cómo se
  perdieron los scripts de la sesión del 30-ago.
- **`descartes.jsonl` con campo `rescatable`** — un enfoque que pierde deja
  conocimiento igual que uno que gana, y suele dejar más. Sembrado con los 7
  descartes reales de YabauseVita R1-R3, cada uno con su medición y con lo que
  sobrevive. Ejemplo: revertir `-Ofast -flto -ffast-math` no arregló el cuelgue
  del dynarec — pero queda **falsado** que los flags fueran la causa, y sin ese
  registro el siguiente que los vea en el historial pierde un ciclo
  sospechando de ellos primero.
- **JSONL y no JSON** — se añade con un append, sin releer ni reescribir el
  fichero. Un formato que obliga a reescribirlo todo para añadir una entrada
  acaba con entradas que nadie añade. Una línea corrupta no invalida el
  histórico: se salta.
- **`controles.json` deja de ser huérfano** — existía en disco desde el 30-ago
  y **no lo leía ningún prompt**. Tercer caso de la misma clase tras
  `bitacora.py` (v5.11.0) y el trinquete de versionado (v5.12.0). Ahora entra
  por `inyecciones.acumuladas()` y hay un test que se pone rojo si se
  desconecta.
- **La quinta inyección** — la secuencia del prompt pasa a ser aceptación →
  caja → bitácora → ronda → memoria. Sobre el encargo de la Ronda 4 son 15.076
  caracteres de contexto que el enjambre no tenía que redescubrir.
- **Un test lee la memoria REAL del repo**, no una de mentira: un `descartes.jsonl`
  malformado en un commit se caza antes del release, no después.

**15 pruebas nuevas.** Suite completa en verde, trinquete de líneas incluido.

---

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
