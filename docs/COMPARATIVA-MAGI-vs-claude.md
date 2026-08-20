# Dos pruebas contra MAGI, y la misma conclusión

**Fecha:** 2026-08-20 · **Método:** `scripts/auditar_sistema.py`, kernel real,
proveedores reales, motor `deep`.

Dos encargos: uno de razonamiento puro y otro de producto. En los dos el
enjambre hizo trabajo bueno por dentro y **entregó al usuario 252 caracteres de
mensaje de error etiquetados como APPROVED**.

---

## Prueba A — pregunta compleja (dynarec PSP → PS Vita)

Enunciado exacto en `docs/COMPARATIVA-A-mi-respuesta.md`, donde también está
mi respuesta, escrita **antes** de leer la del enjambre.

| | MAGI | Yo |
|---|---|---|
| Tiempo | 135 s | — |
| Llamadas al modelo | 9 completions + 2 directas | — |
| Producido por dentro | 30.866 chars (Melchior) + 2.522 (Balthasar) | 6.800 chars |
| **Entregado al usuario** | **252 chars: un aviso de timeout** | la respuesta entera |
| Herramientas propias usadas | **0** | — |

### Lo que MAGI hizo bien, y no es poco

La crítica de Balthasar es de nivel alto y **coincide con mi propio análisis**
en el punto que más importa. Cazó tres errores reales de las propuestas:

> «Confunde los roles de ejecución planteando una traducción directa de VFPU a
> NEON. En la emulación de Vita, el target de recompilación es x86_64/AArch64
> (host) ejecutando la ISA ARMv7-A/NEON de Vita, no una conversión MIPS→NEON.»

Eso es exactamente la sección 1 de mi respuesta —confundir invitado con
anfitrión— encontrada por el crítico del sistema, sin ayuda. También corrigió
que el Allegrex de PSP no tiene *load-delay slots* (los resuelve por
*interlocks*) y que PSP es little-endian. El nodo que refuta funciona.

### Lo que falló

**El árbitro se cayó y el sistema dijo que había aprobado.** Literal, lo que
recibe el usuario:

```
**Decisión Técnica:** APPROVED

[Tiempo de espera agotado tras 150s en iteración 1. Proveedor: g4f-gpt.
 Error: todos los proveedores fallaron: familia 'hf' agotada (1 candidatos):
 HuggingSpace: TypeError: argument of type 'NoneType' is not iterable]
```

Tres fallos encadenados en cuatro líneas:

1. **Aprobar lo que no se ha leído.** Casper no obtuvo respuesta y aun así
   emitió `APPROVED`. Es el fallo más caro que puede tener este sistema:
   convierte un error en un visto bueno.
2. **Tirar 33.000 caracteres de trabajo bueno.** La tesis y la crítica estaban
   hechas y pagadas. El usuario no vio ni una línea.
3. **150 s tirados y ninguna cobertura.** El *hedge* que cubre una llamada
   lenta con otro candidato no llega al bucle de herramientas, que es
   justamente por donde va el árbitro.

**Y el sistema no usó lo que sabe.** MAGI tiene `analyze_port`,
`console_profile` y `compare_consoles` —un analizador de portabilidad entre
consolas, subsistema a subsistema, escrito para exactamente esta pregunta— y
los llamó **cero veces**. La respuesta salió de la memoria del modelo, no de
las herramientas del sistema.

---

## Prueba B — «una réplica de Tetris en un ejecutable único portable .exe»

| | MAGI | Yo |
|---|---|---|
| Tiempo | 273 s | ~8 min incluida la compilación |
| Llamadas al modelo | 21 completions | — |
| Bloques de código entregados | **1** | 1 fichero de 490 líneas |
| **Ejecutable producido** | **ninguno** | `tetris_claude.exe`, 9,0 MB |
| Llamadas a `entregar_artefacto` | **0** | — |
| Verificación | 3 pasadas de **0,0 s** | autoprueba del binario, 90 fotogramas, exit 0 |

### Lo que entregó MAGI

Una **especificación** del juego, en pasado, de algo que nunca construyó:

> «Para la creación del ejecutable único y portable del juego Tetris en
> Windows, **se implementó** una arquitectura basada en Pygame y **se
> empaquetó** mediante PyInstaller sin dependencias externas dinámicas.»

No se implementó ni se empaquetó nada. Los tres enfoques describen el juego
—7-bag, wall kicks, 10×20, 60 fps— con criterio correcto, pero el encargo era
un `.exe` y lo que hay es prosa sobre un `.exe`. Y el árbitro volvió a caer en
el mismo timeout, así que el usuario recibió otra vez el aviso de error
firmado como `APPROVED`.

Lo más grave no es que fallara: es que **nada lo detectó**. `ProposalVerifier`
corrió tres veces y tardó **0,0 segundos**: no había código que ejecutar, así
que verificó el vacío y lo dio por bueno.

### Lo que entregué yo

`tetris_claude.py` (490 líneas, un fichero) → `tetris_claude.exe` (9,0 MB,
portable, sin dependencias externas). Compilado y **verificado por el propio
binario**: `tetris_claude.exe --autotest 90` → `AUTOPRUEBA OK: 90 fotogramas,
puntos=134` y código de salida 0.

Reglas implementadas: bolsa de 7, SRS **con tablas de patadas de pared**
(JLSTZ e I por separado), *lock delay* de 500 ms con 15 reinicios, hold una vez
por pieza, fantasma, cola de 5, DAS/ARR reales, gravedad por nivel, soft/hard
drop puntuados, pausa y fin de partida.

**Y una decisión de ingeniería que el enjambre no llegó a plantearse:** los
tres enfoques eligieron **pygame** sin discutirlo. Para un «ejecutable único
portable», tkinter —que va en la biblioteca estándar— da 9 MB sin SDL, sin
DLLs de audio y sin depender del Visual C++ Redistributable de la máquina
destino. Con pygame son ~30-40 MB y más sitios donde fallar. La elección de
dependencia **era parte del encargo**, y no la evaluó nadie.

---

## Qué separa las dos respuestas

No es inteligencia bruta: la crítica de Balthasar demuestra que el
razonamiento está ahí. Son cinco cosas concretas, y las cinco tienen arreglo:

1. **El último paso se lleva por delante todo lo anterior.** Un timeout en
   Casper borra el trabajo de Melchior y Balthasar.
2. **El sistema aprueba sin leer.** `APPROVED` sale por defecto, no por juicio.
3. **Pide un producto y acepta una descripción.** Sin contrato de entregable,
   «hazme un exe» se satisface con un párrafo en pasado.
4. **No consulta sus propias herramientas.** Tiene un analizador de
   portabilidad y responde de memoria.
5. **La verificación se conforma con el vacío.** Cero bloques verificados en
   0,0 s cuenta como verificado.

Todo esto está convertido en trabajo con criterio de aceptación en
`docs/MEGAPLAN-VELOCIDAD-v6.md`, bloques **C1 a C10**.
