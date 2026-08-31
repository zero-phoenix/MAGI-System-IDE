# Traspaso — MAGI System IDE + YabauseVita

**Fecha:** 31 de agosto de 2026
**Para:** quien continúe el trabajo (zcode desktop u otro agente)
**Máquina:** `DESKTOP-B6D864U` · Windows 10 22H2 (build 19045.6466) · i7-3770 · 24 GB · GTX 1050 2 GB

---

## 0. Lo primero que tienes que entender

Este proyecto lleva tres versiones aprendiendo **una sola lección**, y si la
ignoras vas a repetir los mismos fallos que ya se pagaron:

> **Un documento sobre el sistema no es el sistema. Lee el código.**

El caso fundacional: `PORTING_NOTES.md` decía que YabauseVita era un esqueleto
sin sonido, sin mando y sin CD. El código real tenía dynarec ARM, carga de CHD,
audio y renderizador GPU, y tres juegos arrancaban. Un plan entero se escribió
sobre ese documento y hubo que tirarlo.

**Por eso este fichero no duplica nada.** Te dice dónde está cada cosa y cómo
comprobarla. Si algo de aquí contradice al código, gana el código — y entonces
corrige este fichero.

---

## 1. Estado verificado (31-ago-2026)

### Repositorios

| | |
|---|---|
| `zero-phoenix/MAGI-System-IDE` | **público**, `main` en `7db9d2e`, versión **5.16.0** |
| `zero-phoenix/yabausevita` | **público**, `main` en `e33ead7` |
| Clones locales | `C:\Users\D\Documents\GitHub\MAGI-System-IDE` y `...\yabausevita-zp` |

Ambos árboles limpios, ambos CI en verde, **14 releases conservados** (ninguno
se borra nunca).

⚠️ **Ojo con las cuentas de GitHub.** Hay tres identidades en esta máquina:
`davidchaveznge-wq` en `git config`, y `zero-phoenix` (activa) + `4n0th1ng` en
`gh` CLI. El clon viejo `Documents\GitHub\yabausevita` (sin `-zp`) apunta a
`davidchaveznge-wq` y **está obsoleto**: no trabajes ahí.

### Releases descargables

- MAGI: `MAGI-IDE-v5.zip` (143 MB) + `CHECKSUMS.txt`, con el `.exe` dentro.
- YabauseVita: `YabauseVita.vpk` por commit, más releases etiquetados.

---

## 2. Mapa de lo construido — dónde está cada cosa

### En MAGI (`magi/modules/`)

| Ruta | Qué es |
|---|---|
| `swarm/inyecciones.py` | **Empieza por aquí.** La secuencia de lo que viaja arriba del prompt, en un solo sitio |
| `swarm/bitacora.py` | Inyecta lo ya medido y las reglas de «no repetir» del repo objetivo |
| `swarm/memoria_persistente.py` | Memoria entre proyectos: mandos + descartes con lo `rescatable` |
| `swarm/ronda_verificada.py` | Protocolo R9/R16: una corrida sin ojos ni oídos no es evidencia |
| `swarm/automodelo.py` | Lo que MAGI cree de MAGI, con la prueba que puede tumbarlo |
| `percepcion/oidos.py` | ¿Hay sonido? ¿Sale entero? Loopback WASAPI |
| `percepcion/vista.py` | Qué hay en pantalla, en qué idioma, qué botón pide |
| `percepcion/tools.py` | Registra `listen_audio`, `audio_available`, `classify_screen` |
| `memory/indice.py` | FTS5 sobre bitácora, memoria, docs y código |
| `memory/tools.py` | Registra `search_memory`, `memory_stats` |
| `gui/mapa.py` | Qué topics de la interfaz están conectados al núcleo |

**Datos versionados:** `magi/data/memoria/controles.json` (16 consolas),
`magi/data/memoria/descartes.jsonl` (7 descartes con su medición).

**Documentos generados, nunca escritos a mano:** `docs/AUTOMODELO.json` y `.md`,
`docs/MAPA-INTERFAZ.md`.

**El megaplan completo:** `docs/MEGAPLAN-v6-subagentes.md` — 25 KB, cuatro
partes. Léelo entero antes de tocar nada.

### En YabauseVita

| Ruta | Qué es |
|---|---|
| `docs/BITACORA-OPTIMIZACION.md` | **La fuente de verdad del ciclo.** Hallazgos A1-A27, reglas R1-R15 |
| `docs/MEGAPLAN-R1-INSTRUMENTACION.md` | El plan de la ronda 1 |
| `tools/vita3k_ctl.py` | Ojos y brazos sobre Vita3K: lanza, pulsa teclas, captura, mide |
| `src/vita/emuprof.h` / `.c` | Contadores por subsistema |
| `src/vita/main.c` | **La fuente de verdad del estado del emulador** |

---

## 3. Las reglas que no puedes ignorar

Están completas en `docs/BITACORA-OPTIMIZACION.md` §5.2. Las que más caro
cuesta romper:

| | |
|---|---|
| **R4** | Los FPS de Vita3K **no** son prueba de rendimiento. Vita3K decide **corrección**; las métricas internas deciden **rendimiento** |
| **R5** | No leas `PORTING_NOTES.md` para saber el estado. Lee `src/vita/main.c` |
| **R6** | No optimices el camino de render: es el **1,27 %** del tiempo. Techo de mejora ~0,2 FPS |
| **R7** | `GPU timing` son totales de la ventana de 5 s, **no** µs por fotograma |
| **R9** | Ninguna corrida se acepta sin verificación de **imagen y movimiento** |
| **R14** | El disco de NiGHTS llega byte-perfecto. No vuelvas a sospechar de él |
| **R15** | La palanca no es cambiar de intérprete: `SH2Fast` y `SH2LRU` dan lo mismo |
| **R16** | Una corrida también trae veredicto de **sonido** |

---

## 4. Lo que el sistema sabe que NO sabe hacer

`docs/AUTOMODELO.json`. Tres afirmaciones **refutadas por la realidad**, y una
frágil. No te apoyes en ellas sin comprobarlas:

| Afirmación | Evidencia en contra |
|---|---|
| El núcleo `SH2DynARM` arranca | cuelga al primer frame en **tres builds** (`-Ofast`, `-O3`, VPK del CI). La caché JIT se aloja bien en `0x82800000`: el fallo está al **ejecutar** el código generado |
| NiGHTS llega al título | se queda en la licencia de SEGA; lee 3 sectores del IP.BIN y abandona |
| Se detecta si una pulsación cruza al juego | el attract ya se mueve solo; el delta de medianas no aísla la pulsación |
| *(frágil, 1 de 2)* Se corre la compuerta antes de publicar | cuatro rebotes de CI en un día |

**Sin comprobar** (no es «no funciona», es «nadie lo ha puesto a prueba contra
un juego real»): `classify_screen` y `listen_audio`.

---

## 5. Estado de las once fases

| # | Fase | Estado |
|---|---|---|
| 1 | Búsqueda web sin ventana (`web_search`) | pendiente |
| 2 | Subagentes por familia | pendiente |
| 3 | Plan visible con estado | pendiente |
| 4 | Compuerta obligatoria antes de «hecho» | pendiente |
| 5 | Veredicto «la pregunta era otra» | pendiente |
| 6 | Índice local FTS5 | **construido** |
| 7 | Abanico paralelo | pendiente — **el de más efecto por esfuerzo** |
| 8 | Réplica (Melchior contesta a la objeción) | especificada, no construida |
| 9 | Embeddings locales | **retirada** — sobre-ingeniería sobre 2,7 MB |
| 10 | Modelo de sí mismo falsable | **construido y sembrado** |
| 11 | Fijar el linter | **aplicada** |

**El siguiente es el 7.** Medido: tres esperas independientes tardan 1,50 s en
serie y 0,51 s en abanico — **66 % menos**. Los ocho núcleos están parados
mientras el enjambre espera tres respuestas de red en fila. No necesita ninguna
descarga.

---

## 6. Procedimientos operativos

### Compilar YabauseVita (no hay toolchain local)

Docker, validado:

```bash
docker run --rm -v "C:\Users\D\Documents\GitHub\yabausevita-zp:/src:ro" \
  -v "...\build-docker:/out" ubuntu:24.04 bash -c '
  apt-get update -qq && apt-get install -y -qq git wget curl bzip2 xz-utils \
    cmake clang-18 lld-18 build-essential python3
  cp -r /src /work && chmod -R u+w /work
  cd /tmp && git clone --depth=1 https://github.com/vitasdk/vdpm.git && cd vdpm
  export VITASDK=/usr/local/vitasdk PATH="/usr/local/vitasdk/bin:$PATH"
  ./bootstrap-vitasdk.sh
  export VDPM_NONINTERACTIVE=1
  vdpm zlib libvita2d          # ¡vdpm del PATH, NO ./vdpm del checkout!
  cd /work && mkdir build && cd build
  cmake -DVITASDK=/usr/local/vitasdk \
    -DCMAKE_TOOLCHAIN_FILE=/usr/local/vitasdk/share/vita.toolchain.cmake \
    -DCMAKE_BUILD_TYPE=Release ..
  cmake --build . -- -j$(nproc)'
```

**Trampa:** `./vdpm` del checkout busca `pacman` en `bin/`; el bootstrap nuevo
lo pone en `libexec/vdpm/`. Eso rompió el CI desde el 23-ago. Usa el `vdpm` del
PATH.

### Medir una corrida

```bash
python tools/vita3k_ctl.py run --seconds 60 --windows 6
```

Lanza Vita3K sin elevar y sin el OpenSSL de Git, arranca solo (`autostart=1`),
captura la ventana **del juego** (Vita3K abre dos; la del juego es la de cliente
960×544) y devuelve FPS, métricas EMU, `has_image` y `has_motion`.

**Config en** `%APPDATA%\Vita3K\Vita3K\ux0\data\yabause\config.cfg`:
`cpu_mode=2` (DYNARM), `auto_bios=0` + `bios_path` explícito, **sin BOM**.

### Antes de publicar MAGI

```bash
python -m ruff check magi/ tests/      # ruff==0.16.5, el mismo del CI
python scripts/huerfanos.py --conteo   # techo 80
python -m pytest tests/ -q             # ~25 min en esta máquina; CI lo hace en 4
```

**Y hazlo entero.** El trinquete `test_wiring` caza módulos escritos, probados y
sin conectar, y ningún subconjunto lo ve. Me cazó a mí en el último commit.

---

## 7. Trampas que ya costaron tiempo

| Trampa | Síntoma | Arreglo |
|---|---|---|
| **BOM** | PowerShell `Set-Content -Encoding UTF8` mete BOM. Rompió `pyproject.toml` y, en el emulador, `config.cfg` (el `sscanf` lee `\ufeffrom_path` y lo ignora en silencio) | Escribe con Python, `newline='\n'`, y comprueba `d[:3] != b'\xef\xbb\xbf'` |
| **Ruff sin fijar** | Pasa en local, rebota en CI | Ya fijado: `requirements-dev.txt` con `ruff==0.16.5` |
| **Trinquetes** | Cuatro tipos: huérfanos (80), líneas por módulo, nada-sin-versionar, y el contador de herramientas del README | **No subas el techo.** Conecta, adelgaza o corrige |
| **OpenSSL de Git** | Vita3K muere con `EVP_MD_CTX_get_size_ex` | Lánzalo con `Git\mingw64\bin` fuera del PATH |
| **Vita3K elevado** | Avisa de propietario equivocado en `ux0` | Lánzalo vía `explorer.exe`, que corre sin elevar |
| **Caché CHD corrupta** | `Unsupported CD image` (−2) | Aparta el `.bin`; se reextrae (~524 MB por juego) |
| **Buffering de pytest** | La salida se queda en el 22 % | Espera a que el PID muera; no interpretes el % |

---

## 8. Restricciones de la máquina

**El hardware no se toca.** Todo lo que se construya tiene que funcionar con lo
que ya hay:

- **GTX 1050, 2 GB VRAM** y `torch 2.13.0+cpu` (sin CUDA). Da para embeddings,
  **no** para un LLM local. Usar la GPU exigiría la rueda CUDA: 2,5 GB.
- **C: con ~10 GB libres.** Docker ya ocupa 15,8 GB y el paquete de Claude 13,7.
  Cada extracción CHD son 524 MB más.
- **D: con 37,8 GB libres** tras vaciar la cuarentena de duplicados.
- **Windows sin parches desde el 18-nov-2025.** Riesgo abierto, aplazado por
  decisión del usuario. No es tarea tuya, pero está encima de todo lo demás.

---

## 9. Qué hacer, en orden

### Inmediato — Fase 7, el abanico paralelo

Solapar lo que no depende: la recogida de evidencia de Balthasar con la
redacción de Melchior, los subagentes entre sí, y la auditoría de Ritsuko con
toda la ronda. **Compuerta:** la ronda tarda menos con la misma calidad medida;
si no baja, se retira.

Lo que **no** se puede solapar: Balthasar no puede refutar una tesis que aún no
existe.

### Después — Fase 8, la réplica

Hoy Melchior nunca contesta a la objeción y Casper arbitra un juicio en
rebeldía. Condicional (solo si hay desacuerdo real), acotada (~300 tokens), una
sola vuelta, y con salida (Melchior puede rendirse).

**Compuerta de vida o muerte:** Casper tiene que cambiar de veredicto al menos
1 de cada 5 respecto a lo que habría dictado sin réplica. Si nunca cambia, se
quita.

### En el emulador — Ronda 4

Dos preguntas abiertas, con la evidencia ya recogida:

1. **Por qué la BIOS abandona el disco de NiGHTS tras 3 sectores del IP.BIN.**
   Descartado: disco corrupto, lector roto, región, y el TOC (`ctrl 0x41`).
   Siguiente hipótesis: el lado BIOS/CDB.
2. **El coste por instrucción de los SH2.** Medido: 51 ns en NiGHTS, 57-81 en
   Panzer. Solo `SH2Fast` lleva contador; `SH2LRU` y el dynarec no.

Y el dynarec sigue colgado — pero **eso puede ser específico de Vita3K**. R4
dice que Vita3K decide corrección, no rendimiento; en hardware real podría
funcionar. No lo des por roto sin una Vita.

### Nunca

- No borres releases anteriores.
- No añadas nada a `KNOWN_ORPHANS` para saltarte el trinquete.
- No cites FPS de Vita3K como prueba de rendimiento.
- No escribas a mano un documento que se genera.

---

## 10. Cómo dejar el traspaso al siguiente

Lo mismo que se hizo aquí:

1. **Registra los descartes** en `magi/data/memoria/descartes.jsonl`, con su
   medición y con lo `rescatable`. Un enfoque que pierde deja conocimiento igual
   que uno que gana, y suele dejar más.
2. **Contrasta el automodelo** al cerrar cada ronda: `contrastar(prueba, ok,
   evidencia)`. Si una afirmación se cae, que se caiga sola.
3. **Añade los hallazgos** a la bitácora con su origen, y las reglas derivadas
   con el hallazgo que las justifica.
4. **Publica con notas concretas** de qué cambió, no genéricas.

El sistema mejora porque cada ronda deja escrito lo que costó descubrir. Si te
saltas ese paso, la ronda siguiente vuelve a pagarlo.
