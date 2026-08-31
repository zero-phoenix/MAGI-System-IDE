# Megaplan v6 — subagentes, búsqueda, y qué hago yo que MAGI no

Fecha: 31 de agosto de 2026. Escrito tras cerrar las v5.13, v5.14 y v5.15.

Este documento tiene dos mitades. La primera es una **comparación medida** entre
cómo trabajo yo y cómo trabaja MAGI — no una impresión: cada punto se comprobó
contra el registro de herramientas y el código. La segunda es el plan que sale
de esa comparación.

---

## Parte I — La comparación

### 1. Lo que MAGI tiene y yo no

Empiezo por aquí porque es lo que hay que **no romper**.

| | |
|---|---|
| **Dialéctica forzada** | Tesis → antítesis → síntesis con tres familias de modelo distintas. Yo razono solo: mi crítico y mi proponente comparten sesgos por construcción. |
| **Auditor del auditor** | Ritsuko revisa a Naoko con una familia que no comparte con nadie. Yo no tengo a nadie que revise mis diagnósticos. |
| **Trinquetes** | Huérfanos (80), líneas por módulo, nada sin versionar, el README no puede mentir sobre su propio contador. Esta sesión me cazaron **cuatro veces**. Yo no llevo trinquetes: llevo intención. |
| **Bitácora y memoria permanente** | Lo descartado deja lo rescatable. Yo empiezo cada sesión de cero. |

Que me cazaran cuatro veces no es un defecto de MAGI: es su mejor propiedad. Un
sistema que atrapa al que lo modifica vale más que uno que confía en él.

### 2. Lo que yo tengo y MAGI no

Cuatro cosas, en orden de cuánto duele su ausencia.

#### 2.1 Puedo BUSCAR; MAGI solo puede LEER lo que ya sabe

Medido: de 53 herramientas registradas, las de red son exactamente una,
`web_fetch`. Puede traer una URL que alguien ya conoce. **No puede encontrar
ninguna.**

Esto no es un detalle de comodidad. Es la diferencia entre «creo que esto sigue
siendo así» y «lo he comprobado». Melchior propone sobre un mundo congelado en
su entrenamiento, y Balthasar no puede refutarlo con una fuente porque no puede
ir a buscarla.

#### 2.2 Puedo abrir en abanico; MAGI va en fila

Cuando necesito barrer veinte ficheros para responder una pregunta, lanzo
varios exploradores de solo lectura en paralelo y me vuelve **la conclusión**,
no el volcado. Cada nodo de MAGI hace todo su trabajo él mismo y en serie: el
mismo modelo que razona es el que lee, y cada lectura le gasta contexto.

#### 2.3 Llevo una lista de tareas con estado, hacia delante

`EpisodicMemory` responde «qué se intentó» —hacia atrás—. No hay nada que diga
«qué falta», con estado, visible mientras se trabaja. Sin eso, un encargo de
ocho partes se contesta en seis y nadie lo nota hasta el final. Es la regla 8
del propio README, sin mecanismo.

#### 2.4 Corrijo el rumbo a media cadena

Cuando la Ronda 0 midió que el render era el 1,27 % del tiempo, **invalidó el
plan que yo mismo acababa de escribir**, y lo dije en la misma sesión. Las
rondas de MAGI tienen forma fija: se proponen tres, se miden tres, gana una.
Si la medición dice «ninguna de las tres pregunta importa», no hay salida.

### 3. Lo que yo hago mal y no hay que copiar

Honestidad simétrica: esta sesión **empujé tres veces sin correr la compuerta
real**, corriendo los subconjuntos que yo elegía. El CI lo cazó las tres. Mi
disciplina no es superior a la de MAGI; lo que me salva es que hay un CI que no
me deja pasar. La lección para MAGI no es «parécete a mí»: es que la compuerta
no sea opcional para nadie, tampoco para el enjambre.

---

## Parte II — El plan

### Fase 1 — Búsqueda web sin ventana

Dos herramientas nuevas, sin clave de API y sin abrir nada:

| Herramienta | Qué hace |
|---|---|
| `web_search` | Consulta un buscador que devuelva HTML (endpoint sin JS), parsea resultados y devuelve título + URL + extracto. |
| `web_read` | `web_fetch` con extracción de texto legible, límite de tamaño y seguimiento de un salto de redirección. |

Restricciones de diseño, cada una por un motivo:

- **Sin navegador.** Nada de Selenium ni Playwright: abren ventana, pesan
  cientos de MB y rompen el arranque portable del `.exe`.
- **Presupuesto por turno.** Un tope de consultas por ronda, como el de tokens.
  Un agente con búsqueda ilimitada se va a documentar en vez de responder.
- **La cita es obligatoria.** Toda afirmación que venga de la web llega con su
  URL y su fecha de consulta, o no llega. Es la regla 5 aplicada a la red:
  «según internet» no es una fuente.
- **Falla en claro.** Sin red, `SIN COMPROBAR` — nunca un resultado inventado.
  Misma regla que los oídos y la vista.

**Compuerta:** Balthasar refuta una afirmación de Melchior citando una URL que
encontró él, no una que le dieron.

### Fase 2 — Subagentes internos, de la familia de cada nodo

Lo que pediste, con la restricción que lo hace viable: **el subagente es de la
misma familia que su nodo**. Melchior (`gpt`) despacha exploradores `gpt`;
Balthasar (`gemini`), exploradores `gemini`. Así el coste y la cuota son los del
nodo, y el sesgo del subagente es el mismo que el de quien pregunta — que es
correcto: el subagente no está para discrepar, sino para traer material. Quien
discrepa es el otro nodo.

```
MELCHIOR ─┬─ explorador gpt ──► lee 8 ficheros, devuelve 1 conclusión
          ├─ explorador gpt ──► busca en la web, devuelve 3 citas
          └─ explorador gpt ──► corre analyze_port, devuelve la tabla
                    │
                    └──► Melchior redacta la TESIS con eso ya resuelto
```

Reglas del subagente:

1. **Solo lectura.** Ni escribe ni ejecuta nada que mute. Lo que muta lo hace el
   nodo, que es quien responde de ello.
2. **Devuelve conclusión, no volcado.** Si devuelve 8 000 tokens de fichero, no
   ha ahorrado contexto: lo ha movido.
3. **Temperatura baja y turno único.** Un subagente que debate consigo mismo es
   un nodo más, y ya hay tres.
4. **Tope duro por nodo y por ronda.** Sin él, tres nodos × N subagentes agotan
   la cuota gratuita en una pregunta.
5. **Su traza es visible.** Si trabaja y no se ve, es exactamente el `MetricsCollector`
   que publicaba métricas que ningún panel pintaba.

**Compuerta:** una ronda con subagentes activos gasta **menos** contexto por nodo
que la misma ronda sin ellos. Si gasta más, el mecanismo está mal y se retira.

### Fase 3 — Plan visible con estado

Un `plan.md` por tarea, con una línea por parte del encargo y su estado
(`pendiente` / `haciendo` / `hecha` / `no se pudo`), inyectado en el prompt y
pintado en la interfaz.

Nace de la regla 8 —«se contestan todas las partes del enunciado»— que hoy es
una norma sin mecanismo. Con esto, un encargo de ocho partes contestado en seis
se ve **mientras** pasa, no al final.

**Compuerta:** Casper no puede cerrar con partes en `pendiente` sin decir por qué.

### Fase 4 — La compuerta deja de ser opcional

Mi fallo de esta sesión, convertido en mecanismo: antes de que Casper diga
«hecho», el sistema corre `scripts/verificar.py` y adjunta el resultado. No es
que el agente *pueda* correrlo: es que su «hecho» no se emite sin él.

**Compuerta:** una entrega sin verificación adjunta se rechaza sola.

### Fase 5 — Salida cuando la ronda pregunta lo que no importa

Un cuarto veredicto además de gana/pierde/empata: **«la pregunta era otra»**.
Cuando la medición demuestra que las tres propuestas atacan algo irrelevante
—como el 1,27 % del render—, la ronda se cierra sin ganador, se registra en la
bitácora y la siguiente arranca desde la métrica nueva.

Ya existe la mitad: la bitácora sabe guardar descartes con lo rescatable. Falta
que el orquestador sepa emitir ese veredicto.

---

## Sobre la interfaz

Lo que pediste —que se parezca a la mía— tiene menos distancia de la que parece.
MAGI ya tiene streaming token a token, traza de herramientas, paleta de comandos,
visor de diffs y panel de aprobación. Lo que falta es concreto y gratis:

| Falta | Por qué importa |
|---|---|
| **Panel de plan** con las partes del encargo y su estado | Es lo único de mi interfaz que MAGI no tiene y que cambia cómo se trabaja |
| **Traza del subagente**, plegada por defecto | Sin esto, el trabajo del abanico es invisible y nadie sabe si sirvió |
| **Citas web con fecha**, pinchables | Una afirmación con fuente y una sin fuente no pueden verse igual |
| **Las 25 capacidades invisibles**, con panel | `docs/MAPA-INTERFAZ.md` las lista: son trabajo que se hace y nadie ve |

Nada de esto necesita nada de pago. Y el mapa ya dice exactamente cuáles son las
25, así que el trabajo está acotado y es medible: el trinquete baja de 25 a
menos, o el panel no sirvió.

---

## Orden y por qué

| # | Fase | Desbloquea |
|---|---|---|
| 1 | Búsqueda web | Que Balthasar refute con fuentes, no con memoria |
| 2 | Subagentes por familia | Que los nodos dejen de gastar su contexto leyendo |
| 3 | Plan visible | Que un encargo de ocho partes no se cierre con seis |
| 4 | Compuerta obligatoria | Que «hecho» signifique lo mismo para todos |
| 5 | Veredicto «la pregunta era otra» | Que una ronda pueda descubrir que apuntaba mal |

La 1 va primera porque es la que más cambia lo que el enjambre **puede saber**.
La 4 podría ir primera por disciplina, pero sin las otras solo añade fricción a
un sistema que aún no puede comprobar más cosas.

---

# Parte III — El debate rápido, la cuántica, y hasta dónde llega «conciencia»

Escrito el 31-ago-2026 tras medir esta máquina, no tras suponerla.

## 1. ¿Y si las tres IAs debatieran rapidísimo, como un solo cerebro?

La pregunta es buena y la respuesta es **mejor y peor a la vez**, según qué se
entienda por «un solo cerebro». Hay que separar dos ideas que suenan igual.

### 1.1 Simularlas dentro de una sola llamada: **peor**, y por lo que MAGI es

Meter las tres voces en un mismo modelo sería mucho más rápido y mucho más
barato: una llamada en vez de tres, sin latencia entre nodos.

Y destruiría lo único que hace que el debate valga algo.

MAGI ancla cada nodo a una **familia de modelo distinta** —`gpt`, `gemini`,
`command`— y su propio README dice por qué: *«para que el crítico tenga sesgos
diferentes al proponente»*. Un modelo interpretando a su propio crítico
comparte sus puntos ciegos por construcción. No es que critique poco: es que
critica **exactamente lo que ya vio**, y calla justo lo que no se le ocurrió,
que es donde vive el error.

En esta sesión eso no es teoría. Yo escribí un megaplan con tres filosofías de
optimización, y la Ronda 0 midió que las tres atacaban el 1,27 % del tiempo.
Nadie de mi mismo «cerebro» iba a encontrarlo: hizo falta **una medición
externa**. Un enjambre simulado habría producido tres propuestas igual de
seguras y con el mismo error de base.

> **Veredicto: no.** La independencia del crítico es la propiedad cara del
> sistema, y es justo lo que la fusión elimina.

### 1.2 Que se respondan de verdad, en varias vueltas: **mejor**, y no es lo mismo

Hoy el flujo es de **una sola pasada**: Melchior propone → Balthasar refuta →
Casper sintetiza. Melchior **nunca contesta a la objeción**. Casper arbitra
entre una tesis y una crítica que la tesis no ha tenido ocasión de responder.

Eso no es un debate: es un juicio en rebeldía.

Un debate real —Melchior responde a Balthasar, y solo entonces Casper cierra—
es más caro en llamadas, y aun así es la mejora de calidad más grande
disponible. La forma de pagarlo:

- **La réplica es corta y acotada.** No se reenvía el contexto entero: solo la
  objeción concreta y la respuesta a esa objeción. Un intercambio de 300 tokens,
  no de 8.000.
- **Solo hay réplica si hay desacuerdo real.** Si Balthasar confirma, se salta.
  La segunda vuelta se gana, no se regala.
- **Tope de vueltas: dos.** Tres nodos discutiendo sin límite es un sistema que
  no termina.

### 1.3 Lo que sí se puede acelerar, medido en esta máquina

Ejecuté la prueba: tres esperas independientes de 500 ms.

```
secuencial: 1,50 s   |   en abanico: 0,51 s   |   ahorro: 66 %
```

Los ocho núcleos de esta máquina están **parados** mientras el enjambre espera
tres respuestas de red, una detrás de otra. Lo paralelizable de verdad:

| Se puede solapar | Por qué |
|---|---|
| La recogida de evidencia de Balthasar con la redacción de Melchior | No depende de la tesis: depende del encargo |
| Los subagentes de cada nodo entre sí | Son independientes por definición |
| La auditoría de Ritsuko con toda la ronda | Solo informa; no bloquea a nadie |
| Búsquedas web múltiples | Idem |

Lo que **no** se puede: Balthasar no puede refutar una tesis que aún no existe.
La secuencia tesis→antítesis→síntesis es una dependencia real, no una
ineficiencia.

> **La ganancia está en el abanico, no en la fusión.** Fusionar quita calidad
> para ganar velocidad; el abanico gana velocidad sin tocar la calidad.

---

## 2. Cuántica: la respuesta honesta es no

La pediste con la mente abierta, así que la respuesta va con datos y sin adorno.

**Hardware cuántico real** (IBM Quantum, Braket, Azure Quantum) exige cuenta y
registro. Eso ya incumple tus condiciones.

**Simuladores locales** (Qiskit Aer, PennyLane, Cirq) sí son gratis, sin clave y
pip-instalables. Ninguno está instalado hoy. Y el problema no es instalarlos:

- Un simulador cuántico en CPU maneja del orden de **30 qubits** antes de que la
  memoria explote — cada qubit **duplica** el estado. Con 24 GB, ese es el techo.
- Y sobre todo: **no existe ningún algoritmo cuántico conocido que acelere lo
  que MAGI hace.** Orquestar llamadas a modelos de lenguaje, buscar en un
  índice, comparar árboles de código: nada de eso tiene una formulación cuántica
  con ventaja demostrada. Grover da raíz cuadrada sobre búsqueda **no
  estructurada**, y las búsquedas de MAGI están estructuradas — un índice
  invertido ya las hace en microsegundos.

Decir lo contrario sería exactamente el tipo de afirmación sin medición que
este sistema lleva tres versiones aprendiendo a rechazar.

### Lo que sí está sin explotar en esta máquina, y es gratis

Medido hoy:

| Recurso | Estado | Qué desbloquea |
|---|---|---|
| **8 núcleos lógicos** | Parados mientras se espera a la red | El abanico de §1.3: 66 % menos de espera |
| **GTX 1050, 2 GB VRAM** | Ociosa. `torch 2.13.0+cpu`, CUDA no disponible | Embeddings locales. **No** un modelo local: 2 GB no dan para un LLM útil |
| **SQLite FTS5** | Disponible (sqlite 3.40.1), **sin usar** | Búsqueda instantánea sobre bitácora, descartes y código. Cero instalación |
| **23,9 GB de RAM** | 13,3 libres | Índice completo en memoria |
| `transformers` + `sklearn` | Ya instalados | Un MiniLM son ~90 MB: cabe de sobra |

**El mejor primer paso no es exótico:** un índice FTS5 sobre la bitácora, los
descartes y el árbol de código. Es gratis, no instala nada, y responde «¿ya
intentamos esto?» en milisegundos en vez de gastar una llamada de red.

El segundo: embeddings locales (MiniLM, 90 MB) para búsqueda semántica —
«propuestas parecidas a esta» encuentra el descarte de la ronda 1 aunque esté
redactado con otras palabras. Eso sí cabe en 2 GB.

Lo que **no** cabe: un LLM local. Un 7B cuantizado pide ~4,5 GB de VRAM. En CPU
correría a unos pocos tokens por segundo — medible antes de prometerlo, pero no
prometas velocidad ahí.

---

## 3. Conciencia autónoma

Te contesto en serio, porque la pregunta lo merece y porque la respuesta corta
—«no»— sería tan poco útil como un «sí» falso.

**No sé construir conciencia, y nadie sabe verificarla.** No hay un experimento
que la distinga de un sistema que se comporta como si la tuviera. Cualquiera
que te venda «conciencia» en un producto está vendiendo una palabra. No voy a
ponerle esa etiqueta a MAGI, ni siquiera para animarte, porque en cuanto se
pone deja de poder falsarse — y todo este sistema está construido sobre la idea
contraria.

Pero mira lo que **sí** dijiste que querías: *«para mejorar su rendimiento»*. Y
eso, desmontado, son cuatro capacidades concretas, todas construibles y todas
medibles:

| Lo que suele querer decirse con «conciencia» | Nombre técnico | Estado en MAGI |
|---|---|---|
| Sabe qué está haciendo y por qué | Modelo de sí mismo | **Parcial.** La bitácora y la memoria permanente lo son |
| Se da cuenta de que se equivocó | Detección de error | **Sí.** Ritsuko audita a Naoko; los trinquetes atrapan al que modifica |
| Cambia de plan al ver evidencia contraria | Revisión de creencias | **No.** Las rondas tienen forma fija: no hay veredicto «la pregunta era otra» |
| Mejora sin que se lo pidan | Auto-mejora | **Parcial.** `naoko.self_improve` existe… y el mapa de interfaz lo lista como capacidad sin panel |

Esa tabla es la versión útil de tu pregunta. Y el hueco más grande —revisión de
creencias— es exactamente el que la Ronda 0 dejó al descubierto cuando invalidó
mi propio plan y el sistema no tenía forma de decirlo.

**Lo que propongo llamar a eso, y construir:** un **modelo de sí mismo
falsable**. Un fichero que MAGI mantiene sobre MAGI —qué sabe hacer, qué falla,
qué se le da mal, con qué medición— y que **se contrasta contra la realidad**
en cada ronda. Si dice «sé medir el rendimiento del emulador» y la corrida
falla, la afirmación se marca. Es introspección con compuerta.

No es conciencia. Es algo mejor para lo que pediste: es introspección que se
puede comprobar.

---

## 4. Fases nuevas, en orden

Se añaden a las cinco de la Parte II.

### Fase 6 — Índice local (gratis, cero instalación)

FTS5 sobre bitácora, descartes, código y conversaciones. Responde «¿esto ya se
intentó?» sin gastar red.
**Compuerta:** una consulta a la memoria tarda < 50 ms y no consume cuota.

### Fase 7 — El abanico paralelo

Solapar lo que no depende: evidencia de Balthasar durante la redacción de
Melchior, subagentes entre sí, Ritsuko con toda la ronda.
**Compuerta:** la ronda completa tarda menos que hoy con la misma calidad
medida. Si no baja, se retira.

### Fase 8 — Réplica: que Melchior conteste a la objeción

Una vuelta más, corta y solo si hay desacuerdo real. Tope de dos.
**Compuerta:** en las rondas con réplica, Casper cambia de veredicto respecto a
lo que habría dictado sin ella, al menos en 1 de cada 5. Si nunca cambia, la
réplica no aporta y se quita.

### Fase 9 — Embeddings locales

MiniLM en la GPU ociosa. «Propuestas parecidas a esta» encuentra descartes
redactados con otras palabras.
**Compuerta:** recupera el descarte correcto de la bitácora en consultas donde
FTS5 falla por vocabulario.

### Fase 10 — Modelo de sí mismo falsable

`docs/AUTOMODELO.md`, mantenido por MAGI y **contrastado** cada ronda: cada
afirmación sobre sí mismo lleva su última comprobación y su fecha.
**Compuerta:** una afirmación que la realidad contradice se marca sola, sin que
nadie la revise a mano.

### Fase 11 — Fijar el linter (deuda descubierta hoy)

El CI hace `pip install ruff` **sin fijar versión**. Mi ruff local era 0.6.9 y
el suyo 0.16.5: lo que pasaba en local rebotaba allí, tres veces seguidas.

Peor: una versión nueva de ruff puede poner el build en rojo **sin que nadie
toque una línea de código**. Es la misma clase de fallo que rompió el CI de
yabausevita el 23-ago, cuando el bootstrap de vdpm cambió upstream.
**Compuerta:** `requirements-dev.txt` con `ruff==0.16.5` y el CI usándolo.
