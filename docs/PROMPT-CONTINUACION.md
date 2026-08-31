# Prompt para zcode desktop

Copia y pega desde la línea de abajo. Adjunta también `TRASPASO-MAGI-YABAUSEVITA.md`.

---

Continúas un trabajo en curso sobre dos repositorios míos. **No empieces de
cero y no improvises el contexto: está todo escrito y verificado.**

## Lo primero, antes de proponer nada

Lee estos cuatro ficheros **enteros**, en este orden:

1. `TRASPASO-MAGI-YABAUSEVITA.md` (adjunto) — el mapa de todo
2. `C:\Users\D\Documents\GitHub\yabausevita-zp\docs\BITACORA-OPTIMIZACION.md` — hallazgos A1-A27 y reglas R1-R16
3. `C:\Users\D\Documents\GitHub\MAGI-System-IDE\docs\MEGAPLAN-v6-subagentes.md` — el plan, cuatro partes
4. `C:\Users\D\Documents\GitHub\MAGI-System-IDE\docs\AUTOMODELO.json` — lo que el sistema sabe que NO sabe hacer

Cuando termines, dime en tres frases qué entendiste del estado actual. Si algo
de lo que leas contradice al código, **gana el código**: dímelo y corrige el
documento.

## La regla que ordena todo lo demás

> **Un documento sobre el sistema no es el sistema. Lee el código.**

Esto no es un consejo: es la lección que costó tirar un plan entero.
`PORTING_NOTES.md` decía que el emulador era un esqueleto sin sonido ni mando;
el código real tenía dynarec ARM, CHD y audio, y tres juegos arrancaban. Para
saber el estado del emulador se lee `src/vita/main.c`, nunca un `.md`.

## Reglas de trabajo, no negociables

1. **Ninguna corrida es evidencia sin ojos y oídos.** FPS con la pantalla negra
   pasó de verdad: 59,9 FPS estables durante media hora sin una sola imagen.
   Toda medición trae `has_image`, `has_motion` y veredicto de sonido.
2. **«No lo comprobé» ≠ «no funciona».** Si falta una capacidad en la máquina,
   se declara **SIN COMPROBAR**. Inventar un veredicto negativo es peor que
   omitirlo.
3. **Corre la compuerta completa antes de publicar**, no el subconjunto que
   elijas: `ruff check magi/ tests/`, `scripts/huerfanos.py --conteo` (techo
   80) y `pytest tests/` entero. Tarda ~25 min en esta máquina. Hazlo igual:
   los trinquetes cazan cosas que ningún subconjunto ve.
4. **Nunca subas el techo de un trinquete** para que pase el build, ni añadas
   nada a `KNOWN_ORPHANS`. Conecta el módulo, adelgázalo o bórralo.
5. **Los FPS de Vita3K no son prueba de rendimiento.** Vita3K decide
   *corrección*; las métricas internas del emulador deciden *rendimiento*.
6. **Escribe ficheros con Python**, `newline='\n'`, y comprueba que no llevan
   BOM. PowerShell mete BOM y ya rompió `pyproject.toml` y el `config.cfg` del
   emulador.
7. **No borres releases anteriores. Nunca.**

## Restricción de hardware

**No se modifica el hardware en ningún sentido, ni se instalan descargas
grandes.** GTX 1050 con 2 GB y torch sin CUDA: da para embeddings, no para un
LLM local. C: tiene ~10 GB libres. Todo lo que construyas funciona con lo que
ya hay instalado.

## Qué tienes que hacer, en orden

### 1. Fase 7 — el abanico paralelo (empieza por aquí)

Medido en esta máquina: tres esperas independientes tardan **1,50 s en serie y
0,51 s en abanico, un 66 % menos**. Los ocho núcleos están parados mientras el
enjambre espera tres respuestas de red en fila.

Solapa lo que no depende: la recogida de evidencia de Balthasar con la
redacción de Melchior, los subagentes entre sí, y la auditoría de Ritsuko con
toda la ronda. Lo que **no** se puede solapar: Balthasar no puede refutar una
tesis que aún no existe.

**Compuerta:** la ronda completa tiene que tardar menos con la misma calidad
medida. Si no baja, retira el mecanismo y dilo.

### 2. Fase 8 — la réplica

Hoy Melchior nunca contesta a la objeción de Balthasar, y Casper arbitra entre
una tesis y una crítica que la tesis no ha podido responder. Eso no es un
debate: es un juicio en rebeldía.

Diseño: **condicional** (solo si hay desacuerdo real), **acotada** (~300
tokens, solo la objeción y su respuesta), **una sola vuelta**, y **con salida**
(Melchior puede decir «tienes razón» y cerrar antes de llegar a Casper).

**Compuerta de vida o muerte:** Casper tiene que cambiar de veredicto al menos
1 de cada 5 respecto a lo que habría dictado sin réplica. Si nunca cambia, la
réplica no aporta: quítala.

### 3. Ronda 4 del emulador

Dos preguntas abiertas, con lo ya descartado documentado:

- **Por qué la BIOS abandona el disco de NiGHTS** tras leer 3 sectores del
  IP.BIN (Panzer lee los 16 y sigue). Ya descartados: disco corrupto, lector
  roto, región (`JTU` es válida con BIOS USA) y el TOC (`ctrl 0x41` = datos).
  La siguiente hipótesis está del lado BIOS/CDB.
- **El coste por instrucción de los SH2**: 51 ns en NiGHTS, 57-81 en Panzer.
  Solo `SH2Fast` lleva contador; instrumenta `SH2LRU` y el dynarec.

El dynarec sigue colgando al primer frame en tres builds — pero **puede ser
específico de Vita3K**. No lo declares roto sin hardware real.

## Cómo cerrar cada ronda

Esto no es opcional: es lo que hace que el sistema mejore en vez de repetirse.

1. **Registra los descartes** en `magi/data/memoria/descartes.jsonl` con su
   medición y con el campo `rescatable`. Un enfoque que pierde deja
   conocimiento igual que uno que gana, y suele dejar más.
2. **Contrasta el automodelo**: `contrastar(prueba, ok, evidencia)`. Si una
   afirmación se cae, que se caiga sola, con su evidencia.
3. **Añade hallazgos y reglas** a la bitácora, cada uno con su origen.
4. **Publica** con notas concretas de qué cambió — nunca genéricas — y
   conservando los releases anteriores.

## Cómo quiero que me hables

Dime lo que mides, no lo que supones. Si te equivocas, dilo y corrígelo en el
mismo mensaje. Si algo no se puede comprobar, dilo en vez de rellenarlo. Y si
crees que una de mis instrucciones está mal, discútela — este proyecto ha
mejorado cada vez que alguien señaló que el plan apuntaba al sitio equivocado.
