# Mi respuesta a la pregunta de la prueba D

> *Plan técnico completo para que un emulador de Nintendo DS ya existente
> (ARM9 + ARM7, dos pantallas, GPU de función fija) pueda ejecutar juegos de
> PSP (MIPS Allegrex con VFPU, Media Engine, GPU con listas de display)
> reutilizando su núcleo. Qué se reutiliza, qué se tira, qué se escribe de
> cero; cómo se valida cada etapa con pruebas diferenciales contra hardware; y
> el orden de trabajo que minimiza el riesgo de abandono.*

Escrita antes de leer la del enjambre.

---

## 0. La respuesta incómoda va primero

De un emulador de DS te quedas con **el chasis, no con el motor**. Y hay un
componente que el emulador de DS **no tiene en absoluto** y que es el más
grande de todos los que faltan: un **sistema operativo**.

Los juegos de DS corren a hueso: el emulador emula *hardware*. Los juegos de
PSP corren sobre un SO real —hilos, semáforos, callbacks, módulos PRX,
`sceKernel*`—, así que un emulador de PSP tiene que **reimplementar un SO**
(HLE) o cargar el firmware (LLE, que no puedes distribuir). Ese componente no
se "adapta" desde nada: se escribe.

Si alguien vende este proyecto como «cambiar el núcleo de CPU», el proyecto
muere en el mes dos con la moral por los suelos. Vendido como «reutilizo el
chasis y escribo un emulador de PSP encima», es difícil pero honesto.

## 1. Qué se reutiliza de verdad (~25-30 % del código, ~60 % del esfuerzo acumulado)

Todo esto es **agnóstico del invitado**, y es donde vive el trabajo aburrido
que nadie quiere repetir:

| Pieza | Por qué sobrevive |
|---|---|
| Infraestructura del JIT | Caché de bloques, despachador, enlazado, invalidación por escritura, asignador W^X (medio problema en macOS/Android). No sabe qué ISA traduce. |
| **Backends de emisión** x64/AArch64 | Emiten código del ANFITRIÓN. El anfitrión no cambia. |
| Planificador de eventos | Cola por ciclos, vblank, DMA, IRQ. Cambian los eventos, no el mecanismo. |
| Despacho de memoria por tabla de páginas | El patrón `fastmem` + tabla MMIO es idéntico; el mapa no. |
| Carcasa | Ventana, entrada, ring buffer de audio, presentación, escalado, frame pacing, configuración. |
| Framework de savestates | El mecanismo de serialización versionada. El contenido es nuevo entero. |
| Depurador | Desensamblador, breakpoints, visor de memoria, trazas. |

## 2. Qué se tira

- **Frontends ARM9/ARM7 (ARMv5TE y ARMv4T)**, intérprete y JIT. Nada de eso
  vale para MIPS.
- **Modelo de dos CPUs de DS**: ARM9+ARM7 con FIFO de IPC y WRAM compartida.
  PSP también tiene dos (Allegrex + Media Engine) pero la relación es otra: en
  DS el ARM7 lleva audio, wifi y la pantalla táctil de forma continua; el ME
  del PSP se usa a ráfagas para decodificar. La sincronización no se traduce.
- **Las dos GPU**: motores 2D A/B + motor 3D de 4096 polígonos por frame del
  DS, frente a listas de display del GE del PSP con caché de texturas,
  morphing y splines. Reescritura completa.
- **Mapa de memoria** entero: 4 MB del DS frente a 32/64 MB del PSP con VRAM
  en 0x04000000 y los espejos no cacheados en 0x40000000 — que **no son un
  detalle**: un juego escribe por el espejo no cacheado y lee por el cacheado,
  y si no lo modelas ves basura sin saber por qué.
- Audio: del DS (16 canales PCM/ADPCM) al PSP (ATRAC3, MP3, PCM por
  `sceAudio`).

## 3. Qué hay que escribir de cero

1. **Cargador**: PBP/ELF/PRX, resolución de NIDs, y la frontera de cifrado
   (al principio, solo homebrew sin cifrar — es lo legal y además lo sensato).
2. **Frontend MIPS Allegrex**, y aquí va el detalle que cambia el diseño del
   JIT entero: **MIPS tiene *delay slots* de salto**. Un bloque no puede
   terminar en la instrucción de salto; termina *después* de la instrucción
   que va detrás. Quien venga de ARM lo descubre tarde y mal.
3. **VFPU**: unidad vectorial de 128 bits con matrices, prefijos y swizzles.
   No hay nada parecido en el DS ni en NEON.
4. **Kernel HLE**: hilos, semáforos, event flags, callbacks, `sceIo*`,
   `sceDisplay*`, gestión de módulos. Es un SO. Es el 80 % de los «el juego no
   arranca».
5. **GE**: parseo de listas de display y pipeline propio.
6. **Media Engine y códecs**.

## 4. Cómo se valida cada etapa (pruebas diferenciales, en serio)

La regla: **cada etapa tiene su propio oráculo antes de escribirla**. Sin
oráculo no se escribe.

| Etapa | Oráculo | Qué se compara |
|---|---|---|
| CPU | Trazas de hardware o un intérprete de referencia | Volcado de los 32 registros + HI/LO + PC tras **cada** instrucción. Fuzzing con operandos acotados. La primera divergencia señala la instrucción culpable. |
| Delay slots / saltos | Suites de test de homebrew | Secuencias construidas a propósito: salto tomado/no tomado con delay slot que escribe el registro de la condición. |
| VFPU | Test ROMs vectoriales | Comparación bit a bit: los prefijos y el redondeo son donde falla. |
| Kernel HLE | Trazas capturadas en hardware con un PRX de log | Valor de retorno de cada syscall **y el orden de planificación**. El orden importa: un scheduler «casi» correcto da cuelgues no deterministas. |
| GPU | Golden images | Render de N frames contra imágenes de referencia, con umbral perceptual; y diff de la propia lista de display, que es texto y se lee. |
| Tiempo | Guion de entradas fijo | Contador de vblanks y de frames tras 60 s. Si diverge, el juego irá rápido o lento aunque «funcione». |

## 5. Orden de trabajo que minimiza el abandono

El criterio no es técnico, es psicológico: **cada paso tiene que terminar en
algo que se ve funcionar**. Un plan sin hitos visibles se abandona.

0. Decidir HLE (no LLE) y dejarlo escrito.
1. Cargador + mapa de memoria. → *Hito: cargas un ELF homebrew y vuelcas su
   memoria.*
2. **Intérprete** MIPS, no JIT. → *Hito: pasa las test ROMs de CPU.*
3. Kernel HLE mínimo: hilos, `sceDisplaySetFrameBuf`, `sceIo` básico. →
   *Hito: un homebrew pinta un color en pantalla y sale.*
4. GE mínimo. → *Hito: el cubo texturizado girando.*
5. VFPU cuando un juego lo exija. → *Hito: el primer juego comercial arranca.*
6. **JIT, ahora sí**, reutilizando la infraestructura del emulador de DS. →
   *Hito: velocidad plena con el mismo corpus de tests pasando.*
7. Audio y Media Engine.
8. Compatibilidad por títulos.

## 6. Los tres riesgos que hunden esto

1. **Empezar por el JIT.** Es el error clásico y el más caro: consigues que el
   60 % de los juegos «casi» funcionen y no puedes depurar nada, porque el JIT
   esconde los errores de semántica detrás de la optimización. Intérprete
   primero, siempre.
2. **Subestimar el kernel HLE.** No es un componente: es un sistema operativo.
   Si el plan le dedica un párrafo, el plan está mal.
3. **No tener corpus de pruebas desde el día uno.** Sin test ROMs ni golden
   images, cada arreglo rompe dos cosas en silencio, la compatibilidad va y
   viene sin que sepas por qué, y el proyecto muere de desmoralización, no de
   dificultad técnica.

## 7. Lo que yo haría de verdad

PPSSPP existe y lleva más de una década de compatibilidad acumulada. Si el
objetivo es **tener un emulador de PSP**, contribuir ahí rinde cien veces más
que empezar. Si el objetivo es **aprender** —que es un objetivo legítimo y el
mejor de los dos—, el camino con mejor relación aprendizaje/frustración es
escribir el **intérprete de MIPS con arnés diferencial** y parar ahí: es donde
está el 90 % del aprendizaje y el 10 % del sufrimiento.

Y una nota que viene al caso: MAGI ya tiene ese arnés. `magi/modules/reverse/`
trae emulación MIPS con Unicorn, `differential_test()` y un analizador de
portabilidad entre consolas (`analyze_port`). El paso 2 de este plan se puede
empezar hoy con las herramientas del propio repositorio.
