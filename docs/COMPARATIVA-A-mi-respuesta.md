# Mi respuesta a la pregunta de la prueba A

> *¿Por qué el dynarec de un emulador de PSP (MIPS R4000 + VFPU) no se puede
> reutilizar tal cual para emular PS Vita (ARM Cortex-A9 + NEON), qué partes sí
> se reutilizan, y cuál es el camino técnico realista para adaptar un emulador
> de PSP a Vita? Orden de trabajo y los tres riesgos que hunden el proyecto.*

Escrita antes de leer la del enjambre, para que la comparación valga algo.

---

## 1. El error de partida: confundir el invitado con el anfitrión

Casi todo el mundo razona así: «PSP es MIPS, Vita es ARM, luego hay que cambiar
el backend del dynarec». Está al revés, y es la confusión que hunde el proyecto
antes de empezar.

Un recompilador dinámico tiene tres capas:

| Capa | De qué depende | Ejemplo PSP |
|---|---|---|
| **Frontend** | de la consola emulada (*guest*) | decodifica MIPS Allegrex + VFPU |
| **IR + optimizador** | de nadie | bloques, asignación de registros, constant folding |
| **Backend** | de la máquina donde corres (*host*) | emite x86-64 o ARM64 |

El backend **no cambia** al pasar de emular PSP a emular Vita: sigues corriendo
en el mismo PC. Lo que cambia por completo es el **frontend**, porque el
invitado pasa de MIPS32 a ARMv7-A con Thumb-2.

Y hay una trampa encima: «si el host es ARM, ejecuto el código ARMv7 del Vita
directamente». No. Los ARM64 modernos han ido eliminando AArch32 en EL0 —Apple
Silicon no lo tiene en absoluto, y buena parte de los Cortex-A recientes
tampoco—, así que la ejecución nativa del código invitado no es un plan; es una
excepción histórica que ya caducó.

## 2. Qué se reutiliza de verdad

Lo valioso de un dynarec maduro casi nunca es el decodificador: es la
infraestructura que hay alrededor, y esa **es agnóstica del invitado**.

**Se reutiliza (~60-70 % del trabajo acumulado):**

- Caché de bloques, hashing, invalidación por escritura y código automodificable.
- Despachador, enlazado de bloques (*block linking*), salidas por excepción.
- Asignador de memoria ejecutable con W^X, que en macOS/iOS y Android moderno
  es la mitad del problema de arrancar un JIT.
- La IR y el asignador de registros, si el emulador tiene una (PPSSPP tiene
  IRJit precisamente por esto).
- Backends de emisión x86-64/ARM64.
- Planificador de eventos, modelo de tiempo, savestates, herramientas de
  depuración y trazas.
- Patrones del renderizador: caché de texturas, caché de shaders, manejo del
  *framebuffer*.

**No se reutiliza nada de esto:**

- **Semántica del ISA.** ARMv7 tiene banderas NZCV y ejecución condicional
  (`IT` blocks en Thumb-2); MIPS no tiene banderas. Emular banderas de forma
  ingenua —calcularlas en cada instrucción— es la forma más común de perder el
  80 % del rendimiento; hay que hacer evaluación perezosa, y eso condiciona el
  diseño entero del frontend.
- **VFPU frente a NEON.** El VFPU del PSP es una unidad vectorial propietaria
  con matrices, prefijos y *swizzles* que no existen en NEON. No hay traducción
  1:1 en ninguna dirección.
- **Formato ejecutable y carga.** PSP: PRX, ISO/CSO. Vita: SELF/velf firmado,
  PKG/NPDRM, resolución de módulos por NID. Es un cargador nuevo entero.
- **Capa de kernel (HLE).** `sceKernel*` del PSP frente a `SceKernel`/
  `SceLibKernel` del Vita: hilos, semáforos, callbacks, `memblocks`, modelo de
  permisos. Además el Vita tiene MMU de verdad y un procesador de seguridad; el
  mapa de memoria plano del PSP deja de servir.
- **GPU.** El GE del PSP es de pipeline fijo con listas de display. El Vita
  lleva un PowerVR SGX543MP4+ **programable**: hay que interpretar el flujo de
  GXM y, sobre todo, **recompilar shaders USSE** a SPIR-V/GLSL.

## 3. Camino realista, en orden

El orden importa porque cada paso desbloquea el siguiente; hacerlo en otro
orden significa depurar a ciegas.

0. **Decidir el alcance en voz alta:** «reutilizo el esqueleto del emulador»,
   no «porto el núcleo de PSP». Si el proyecto se vende como lo segundo, muere
   en el paso 2 con la moral por los suelos.
1. **Cargador**: SELF/velf, descifrado, ELF, tabla de NIDs. Sin esto no arranca
   ni un «hola mundo», y es donde se decide si el proyecto es legal en tu país.
2. **Frontend de CPU**: ARMv7 + Thumb-2 sobre la IR existente, con banderas
   perezosas. Después VFPv3/NEON.
3. **Memoria**: espacio de direcciones con permisos por página e invalidación
   de bloques al escribir.
4. **Kernel HLE**: hilos, sincronización, callbacks, memblocks. Aquí vive el
   80 % de los «el juego no arranca».
5. **Gráficos**: parseo de GXM + traductor de shaders USSE. Es un proyecto de
   compiladores dentro del proyecto.
6. **Audio, entrada, táctil, giroscopio.**
7. **Compatibilidad**: caza de fallos por título, con *differential testing*
   contra trazas de hardware real.

## 4. Los tres riesgos que hunden el proyecto

1. **El traductor de shaders USSE.** Es un compilador completo y se subestima
   siempre. Es, con diferencia, lo que más tiempo ha costado en los intentos
   reales.
2. **Fidelidad del kernel y el descifrado.** Sin SELF correcto ni NIDs
   resueltos no hay nada; y con un planificador de hilos aproximado aparecen
   cuelgues no deterministas, que son imposibles de bisecar. Añade el problema
   de las claves y el firmware, que no son distribuibles.
3. **Intentar «adaptar» el núcleo de CPU del PSP en vez de escribir un frontend
   nuevo.** Cada diferencia semántica —banderas, ejecución condicional, bloques
   IT, accesos no alineados, coprocesadores— se resuelve con un caso especial,
   y al cabo de doscientos casos especiales el núcleo no lo entiende nadie. La
   jugada correcta es frontend nuevo contra la misma IR.

## 5. Cómo se sabe que va bien (y no que lo parece)

Prueba diferencial: se ejecuta el mismo bloque en el emulador y en hardware (o
contra una traza capturada) y se comparan los registros al terminar. La primera
divergencia señala la instrucción culpable. Es lento de montar y es lo único
que convierte «parece que funciona» en «funciona».

## 6. La recomendación incómoda

Vita3K ya existe y lleva años de compatibilidad acumulada. Salvo que el
objetivo sea aprender —que es un objetivo legítimo y excelente—, contribuir a
lo que existe rinde más que empezar de cero. Y si el objetivo es aprender, el
camino con mejor relación aprendizaje/frustración no es «portar un emulador»:
es escribir un intérprete de ARMv7 con pruebas diferenciales, y solo después
mirar el JIT.
