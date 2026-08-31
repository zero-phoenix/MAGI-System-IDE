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
