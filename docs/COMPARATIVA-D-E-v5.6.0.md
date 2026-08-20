# Pruebas D y E contra la v5.6.0 — qué arregló el megaplan y qué falta

**Fecha:** 2026-08-20 · kernel real, proveedores reales, motor `deep`, Naoko y
Ritsuko vivas · Evidencia: `docs/comparativa/prueba-D-magi.json` y
`prueba-E-magi.json`

Las mismas dos formas de encargo que en agosto —una pregunta muy difícil y un
producto— contra el sistema ya parcheado. Comparadas con lo que entrego yo.

---

## Lo primero, porque cambia el juicio de todo lo demás

| | v5.5.2 (pruebas A/B/C) | **v5.6.0 (pruebas D/E)** |
|---|---|---|
| `APPROVED` sobre un turno degradado | **3 de 3** | **0 de 2** |
| Respuesta final al usuario | 252 chars de error | **5.436 y 6.847 chars reales** |
| Ratio entregado/producido | 0,8 % y 1,9 % | **12,3 % y 24,7 %** |
| Bloques de código en un encargo de `.exe` | **0** | **8** |
| Verificación ejecutada | 0,0 s (el vacío) | **2,06 s (código real)** |
| Encargo sin artefacto | cerrado como éxito | **marcado `[INCOMPLETO]`** |
| Derivas falsas de Naoko durante la tarea | 4 | **0** |
| Veredicto de Ritsuko | el error del proveedor | **veredicto propio con evidencia** |
| Tiempo (ping pong) | 657 s | **177 s** |

El fallo que motivó todo —firmar como aprobado un mensaje de error— **no ha
vuelto a aparecer**.

---

## Prueba D — pregunta súper compleja (emulador NDS → PSP)

Enunciado y mi respuesta completa: `docs/COMPARATIVA-D-mi-respuesta.md`,
escrita antes de leer la del enjambre.

### El procedimiento

162 s de pared, 10 completions, 3 nodos activos. Melchior escribió 36.498
caracteres (3 enfoques), Balthasar 1.886, Casper entregó 5.436.

### La respuesta final: buena de verdad

No es una concesión: es una respuesta que un ingeniero de emuladores firmaría.
Acierta el núcleo de la pregunta —lo reutilizable es la **infraestructura
agnóstica**, no el hardware— y lo demuestra con detalle real:

> **Reutilizable al 100 %:** `EventScheduler`, `BusDeviceInterface`
> (`read8/16/32`), `SaveStateManager` (zlib), `Debugger & Tracer` desacoplado
> de la ISA por callbacks, `AudioMixer & Resampler`.
> **Descartado:** núcleos ARM946E-S y ARM7TDMI con CP15, engine 2D/3D dual
> screen, `DISPCNT`/`BGxCNT`, táctil SPI, micrófono ADC.
> **Nuevo:** MIPS Allegrex (con `bitrev`, `rotr`), VFPU, GE por listas de
> display, HLE + FFmpeg para ATRAC3plus.

Y cazó un error real en uno de sus propios enfoques: proponer probar con
juegos comerciales en la Fase 1 «omitiendo que sin GPU, DMA y Kernel HLE un
ejecutable de PSP colapsa inmediatamente».

**Es más concreto que yo en hardware**: direcciones exactas (RAM `0x08000000`,
VRAM `0x04000000`, registros `0x1E000000`), nombres de comandos del GE,
instrucciones específicas del Allegrex. Eso no lo tenía yo a ese nivel.

### Dónde sigo por delante, y por qué importa

1. **Se dejó una parte de la pregunta sin contestar.** El enunciado pedía
   explícitamente *«el orden de trabajo que minimiza el riesgo de abandono»*.
   La respuesta da un faseado técnico correcto y **no menciona el abandono ni
   una vez**. Yo trato el orden como un problema psicológico —cada fase
   termina en algo que se ve funcionar— y listo los tres asesinos del
   proyecto.
2. **El *delay slot* de MIPS.** Cambia el modelo de bloques del JIT entero: un
   bloque no puede terminar en el salto, termina *después* de la instrucción
   siguiente. Quien viene de ARM lo descubre tarde y mal. No aparece.
3. **Los espejos no cacheados** (`0x40000000`). Un juego escribe por uno y lee
   por el otro; sin modelarlos ves basura sin saber por qué.
4. **«Intérprete primero, JIT después», dicho como riesgo.** MAGI pone el JIT
   en la fase 7 —correcto— pero nunca dice por qué, así que nada impide que
   alguien lo suba.
5. **El oráculo de cada etapa.** MAGI valida contra «trazados sintéticos»; yo
   exijo trazas de hardware, orden de planificación de hilos, golden images y
   contador de vblanks. La diferencia entre «tengo tests» y «tengo un oráculo».
6. **La recomendación incómoda** (PPSSPP existe; contribuye) no aparece.
7. **Cero uso de herramientas propias.** Otra vez: el repo tiene
   `analyze_port`, `console_profile` y `differential_test` escritos para
   exactamente esta pregunta. `menciones_a_herramientas: 0`.

---

## Prueba E — «ping pong de 32 bits a todo color en un .exe portable»

### El procedimiento: 3,7× más rápido y con código de verdad

177 s (eran 657 con el de 16 bits), 12 completions, **8 bloques de código**, y
`ProposalVerifier` corriendo **2,06 s** sobre código real en vez de 0,0 s sobre
el vacío.

### La propuesta final, y el aviso que antes no existía

Casper empieza diciendo cómo entendió el encargo (C15) y evalúa los tres
enfoques con criterio. Y entonces aparece esto, que es el cambio importante:

```
[INCOMPLETO] Pediste algo construido y esto no lo está: no se ha generado
ningún artefacto. Lo que sigue es una propuesta, no una entrega.
```

**El sistema ya no dice que ha compilado lo que no ha compilado.** En la prueba
C escribió «se compiló exitosamente el binario ejecutable único portable» sin
que existiera ningún fichero; aquí dice exactamente lo que hay.

Y un detalle que da gusto ver: entre los aciertos del Enfoque A, Casper anota
que **«incluye un modo de autoprueba»**. Es mi propia práctica —C16, el
artefacto trae su propia prueba— propagada al enjambre por el prompt y
reconocida por el árbitro como una virtud.

### Los tres fallos que quedan

1. **`APPROVED` e `[INCOMPLETO]` conviven en la misma entrega.** El contrato
   dispara el aviso pero no toca el veredicto. Los dos mecanismos no se
   hablan: hay que degradar la decisión, no solo añadir una línea.
2. **Sigue sin producirse el `.exe`.** Melchior escribe el código; nadie llama
   a `build_project_exe` ni a `entregar_artefacto`. El contrato lo detecta y lo
   dice —que es infinitamente mejor que mentir— pero el usuario sigue sin su
   juego.
3. **Llamadas lentísimas:** `MELCHIOR iteración 1 lenta (80,2 s con g4f-gpt)`,
   `CASPER iteración 1 lenta (78,8 s con g4f-hf)`. El hedge ya cubre esta
   puerta; el problema es de elección de candidato (B5, pendiente).

### Mi versión

`pong32_claude.py` (481 líneas, un fichero) → `pong32_claude.exe`, **9,0 MB**,
verificado por el propio binario:

```
FORMATO 32 BITS: OK
AUTOPRUEBA OK: 200 fotogramas en 4.1s (48 fps) · RGBA8888 con alfa verificado
              · framebuffer 320x200x4 · recorrido 856px
```

Aquí «32 bits a todo color» es una propiedad comprobable: **framebuffer RGBA
real** con composición `src-over` (`dst = src·a + dst·(1-a)`), y `--formato`
verifica la **matemática del mezclador**, no una constante. Ese test me cazó a
mí: exigí que negro al 50 % sobre (200,100,50) diera (100,50,25) y el código
devolvió (99,49,24). Tenía razón el código —alfa 128 pesa 127/255, no la
mitad exacta— y el número bonito era mío. Lo dejé escrito en el fichero.

Lo que trae, y por qué: degradado de 8 bits por canal **sin dithering** (en 16
bits bandeaba y por eso la versión anterior lo necesitaba), sombras y estela
compuestas con alfa, halo de la bola en dos capas, fondo precalculado una vez
para que componer cueste 6.000 píxeles por fotograma en vez de 64.000 —48 fps
en Python puro—, rebote por punto de impacto, efecto de pala, y partida a 11
ganando por dos.

---

## Naoko y Ritsuko: ¿hicieron bien su trabajo?

**Naoko: sí, por primera vez.** Cero intervenciones en las dos pruebas. Suena a
poco y es exactamente lo correcto: en la prueba C declaró cuatro «derivas»
falsas mientras la tarea consumía la cuota de esos mismos proveedores. Ahora
espera a que el enjambre esté quieto y un canario que no contesta cuenta como
*no concluyente*. **Dejar de hacer daño es trabajo.**

**Ritsuko: sí, y con una pega.** Su veredicto ya es suyo —«SIN DATOS
SUFICIENTES», con la evidencia citada por su clave JSON— y no el mensaje de
error del proveedor, que es lo que entregaba antes. Midió bien a los tres
nodos con sus latencias (`MELCHIOR p50 37.234 ms`, `BALTHASAR 14.844 ms`,
`CASPER 78.813 ms`) y verificó que ninguno estaba mudo.

Y encontró algo que yo no estaba mirando:

> «Existen 8 tareas atascadas en estado `WAITING_USER_APPROVAL` y 1 marcada
> como `interrumpida`.»

Es real: mis auditorías repetidas dejaron tareas abiertas en la base. Un
auditor que encuentra basura que el operador no había visto está haciendo su
trabajo.

**La pega:** dice «SIN DATOS SUFICIENTES» teniendo delante el hallazgo más
importante de la sesión —un encargo de producto cerrado sin artefacto y marcado
`[INCOMPLETO]`—. No lo ve porque su evidencia no incluye las métricas de
entrega. Se arregla pasándole `calidad_de_entrega`; va al megaplan.
