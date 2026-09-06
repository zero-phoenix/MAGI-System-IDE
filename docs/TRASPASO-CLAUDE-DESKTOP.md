# Plan de Traspaso Técnico — MAGI System IDE & YabauseVita

**Fecha:** 6 de septiembre de 2026  
**Autor:** Antigravity (Google DeepMind)  
**Destinatario:** Claude Desktop (Anthropic)  
**Entorno de Ejecución:** `DESKTOP-B6D864U` · Windows 10 22H2 (build 19045.6466) · Intel Core i7-3770 · 24 GB RAM · NVIDIA GeForce GTX 1050 2 GB  

---

## 0. Filosofía del Proyecto y Reglas Innegociables

Antes de tocar una sola línea de código, lee y asimila las reglas canónicas del repositorio:

1. **Un documento no es el sistema: lee el código y mide en runtime.** No asumas que una función hace lo que su nombre dice si no lo has verificado en el código o con una prueba automatizada.
2. **Sin tests verdes no hay release.** No se realiza commit ni push de ninguna versión si `python scripts/verificar.py --rapido` no pasa al 100%.
3. **El trinquete de líneas (`tests/test_trinquete_de_lineas.py`) es inmutable.** Los archivos con techo de líneas (`kernel.py <= 1070`, `orchestrator.py <= 1550`, `builtin.py <= 800`, `App.tsx <= 900`) no pueden exceder su límite. Si agregas lógica, extrae módulos auxiliares.
4. **El README no miente (`tests/test_readme_claims.py`).** Cualquier cambio a las cifras numéricas del README (conteo de herramientas, tests, nodos) romperá la suite si no refleja el estado exacto del registry y la suite.
5. **Cortafuegos de navegador (`magi/core/no_browser.py`).** Está prohibido abrir navegadores web externos con subprocess o Selenium; toda la interfaz corre exclusivamente en el Webview2 local.
6. **Consola UTF-8 tolerante (`PYTHONUTF8=1` o `reconfigure`).** En Windows, la consola estándar cp1252 revienta con caracteres como flechas unicode (`→`) o acentos. Todo script nuevo debe reconfigurar `stdout`/`stderr` en UTF-8 con `errors="replace"`.

---

## 1. Mapa de Rutas del Sistema

### A. Repositorio MAGI System IDE
- **Ruta del repositorio:** `C:\Users\D\Documents\GitHub\MAGI-System-IDE`
- **Rama principal:** `main` (apuntando al tag `v5.27.1` y commit `f671e75`)
- **Ejecutable compilado portable:** `C:\Users\D\Documents\GitHub\MAGI-System-IDE\dist\unpacked\MAGI-IDE-v5.exe`
- **Paquete Zip del release:** `C:\Users\D\Documents\GitHub\MAGI-System-IDE\dist\MAGI-IDE-v5.zip`
- **Acceso directo en el Escritorio:** `C:\Users\D\Desktop\MAGI System IDE.lnk`
- **Frontend nativo:** `magi-gui/` (React + TypeScript + Vite + Tailwind/CSS Evangelion)
- **Servidor HTTP local de GUI:** `http://127.0.0.1:1420`
- **Servidor WebSocket RPC del Kernel:** `ws://127.0.0.1:20128`
- **Módulos de Lilim:** `magi/modules/lilim/`
  - `mielina.py` (Pre-auditoría AST en 0 ms, andamiaje para Melchior, Balthasar y Casper)
  - `motor.py` (Memoria escasa MoE EPD determinista sin latencia)
  - `ojos.py` (Percepción visual/documental tipo Google Lens para imágenes y PDFs)
  - `oidos.py` (Análisis acústico de WAV, MP3 y loopback WASAPI)
  - `brazos.py` (Actuación en workspace, exportación DOCX y hash SHA-256)
  - `cliente_kobold.py` (Cliente asíncrono para KoboldCpp en `http://127.0.0.1:5001`)

### B. Repositorios de YabauseVita
- **Repositorio principal (sincronizado con GitHub):** `C:\Users\D\Documents\GitHub\yabausevita-zp` (`origin: https://github.com/zero-phoenix/yabausevita.git`)
- **Repositorio secundario local:** `C:\Users\D\Documents\GitHub\yabausevita` (apuntando a `origin: https://github.com/davidchaveznge-wq/yabausevita.git`, sincronizado al commit `cb50439`)
- **Emulador Vita3K:**
  - **Ejecutable:** `C:\Users\D\Documents\GitHub\yabausevita\vita3k\Vita3K.exe`
  - **Directorio de datos (AppData):** `C:\Users\D\AppData\Roaming\Vita3K\Vita3K\`
  - **App instalada:** `C:\Users\D\AppData\Roaming\Vita3K\Vita3K\ux0\app\YABA00001\`
  - **Log de telemetría:** `C:\Users\D\AppData\Roaming\Vita3K\Vita3K\ux0\data\yabausevita_log.txt`
  - **Configuración del emulador:** `C:\Users\D\AppData\Roaming\Vita3K\Vita3K\ux0\data\yabause\config.cfg`
  - **ROMs CHD instaladas:** `ux0\data\yabause\roms\` (`Sonic R.chd`, `Panzer Dragoon.chd`, `NiGHTS into Dreams.chd`)
  - **BIOS verificadas:** `ux0\data\yabause\bios\` (`saturn_bios.bin`, `sega_bios.bin`)
- **Harness de automatización:** `C:\Users\D\Documents\GitHub\yabausevita\tools\vita3k_ctl.py`

### C. Repositorio Desacoplado Venim (VeniceMAGI)
- **Ruta:** `C:\Users\D\magi-port\VeniceMAGI`
- **Nota:** MAGI System IDE fue totalmente desacoplado visual y arquitectónicamente de Venim. Si necesitas correr MAGI-IDE, asegúrate de que ningún proceso de Venim esté reteniendo los puertos `1420` o `20128`.

---

## 2. Estado de lo Ejecutado y Verificado por Antigravity

1. **Corrección de Diagrama Mermaid en GitHub:**
   - Se solucionó el error `Unable to render rich display: Cannot read properties of undefined (reading 'render')` reestructurando las aristas entre nodos reales y entrecomillando todas las etiquetas en `README.md`.
   - Commit `f671e75` subido y verificado en `main`.
2. **Identidad Visual Evangelion Táctica:**
   - Se renovó el tema visual en `magi-gui/src/theme/magi.css` y `App.css` adoptando la paleta canónica de Evangelion: Naranja Ámbar NERV (`#FF6600`) y Azul Turquesa Táctico (`#00D2C4`), con el badge `EVANGELION TACTICAL` en cabecera.
   - `npm test` en verde (131/131 tests pasados) y compilación Vite limpia en `magi-gui/dist`.
3. **Suite Completa y Release v5.27.1:**
   - Se ejecutó `python scripts/verificar.py --rapido` pasando los **1788 tests en Python** con 0 errores de tipo en `pyright`.
   - Release oficial publicado en GitHub: [v5.27.1](https://github.com/zero-phoenix/MAGI-System-IDE/releases/tag/v5.27.1) con `MAGI-IDE-v5.zip` (150.4 MB, hash SHA-256 verificado) y `CHECKSUMS.txt`.
4. **Despliegue y Acceso Directo:**
   - Se creó el acceso directo oficial en `C:\Users\D\Desktop\MAGI System IDE.lnk`.
   - Se verificó que `MAGI-IDE-v5.exe` levanta la ventana nativa de Webview2 y el Kernel WebSocket en `ws://127.0.0.1:20128`.
5. **Interacción como Usuario con el Enjambre:**
   - Se programó `scripts/interactuar_magi.py` para interactuar vía WebSocket con el bus de MAGI. La petición de mejora de YabauseVita fue enrutada con éxito a `build` (confianza 0.85) iniciando el debate dialéctico supervisado por Naoko.
6. **Calibración de los Órganos de Lilim:**
   - Se validaron en runtime: Mielina (AST estático en 0 ms), Motor MoE (memoria en 4.9 ms), Brazos (exportación DOCX y hash criptográfico), Oídos (análisis acústico) y Ojos (Lens multimodal).
7. **Prueba y Compilación de YabauseVita a 60 FPS:**
   - Se solucionó el `UnicodeEncodeError` en `tools/vita3k_ctl.py` agregando `reconfigure(encoding="utf-8")`.
   - Se corrió el benchmark de 20 s en Vita3K contra `Sonic R CHD`: **60.2 FPS de mediana**, 0 cuadros descartados y lectura directa de CHD operativa.
   - Se envió el commit `cb50439`, superando el workflow de GitHub Actions en 1m48s y publicando el release automatizado.

---

## 3. Plan de Continuación para Claude Desktop (Misiones Pendientes)

A continuación se detallan las tareas prioritarias que Claude Desktop debe continuar y mejorar:

### Misión 1: Diagnóstico y Reparación de `SH2DynARM` en YabauseVita
- **Ubicación:** `C:\Users\D\Documents\GitHub\yabausevita\src\vita\sh2dyn_arm.c`
- **Problema Actual:** El dynarec ARM genera código en la memoria JIT (8 MB RWX), pero se congela en el primer fotograma al saltar a la ejecución del bloque compilado.
- **Acción Requerida:**
  1. Revisar la llamada a invalidación de caché de instrucciones tras la emisión del bloque: en ARMv7 (Cortex-A9 de PS Vita), escribir código en memoria y ejecutarlo requiere vaciar la caché de datos e invalidar la caché de instrucciones (`__clear_cache` o llamada de sincronización de VitaSDK).
  2. Comprobar si las instrucciones generadas respetan el alineamiento de 4 bytes y si el bit de Thumb (`PC | 1`) está o no activado al saltar.
  3. Probar la estabilidad ejecutando una corrida automatizada con `python tools/vita3k_ctl.py run --seconds 30`.

### Misión 2: Optimización del Tiempo de Arranque de NiGHTS into Dreams
- **Ubicación:** `C:\Users\D\Documents\GitHub\yabausevita\src\cs2.c`, `src\vita\sh2fast.c`
- **Problema Actual:** NiGHTS arranca a ~40 FPS y tarda más de 75 segundos en alcanzar la pantalla de título porque satura simultáneamente el Master SH2 y el Slave SH2.
- **Acción Requerida:**
  1. Aplicar la filosofía ortogonal **"Hacer menos"** o **"Repartir mejor"**: evaluar si el Slave SH2 puede ceder ciclos cuando se encuentra en bucles de espera pasiva (`sh2idle.c`).
  2. Medir la mejora comparando las métricas de `emu_msh2_avg_us` y `emu_ssh2_avg_us` usando `python tools/vita3k_ctl.py metrics`.

### Misión 3: Integración de Motor Local KoboldCpp para Lilim (Qwen 2.5 1.5B GGUF)
- **Ubicación en MAGI:** `magi/modules/lilim/cliente_kobold.py`
- **Objetivo:** Proporcionar un lanzador o supervisor local opcional para que Lilim pueda ejecutar inferencia neural local en KoboldCpp (`http://127.0.0.1:5001`) con el modelo cuantizado `Qwen 2.5 1.5B Instruct GGUF Q4_K_M` en la GPU GTX 1050 (consumo < 1.4 GB VRAM) o CPU i7-3770.
- **Acción Requerida:**
  1. Diseñar un script de arranque opcional (`scripts/lanzar_kobold_lilim.py`) que detecte si KoboldCpp está en el sistema o corriendo en el puerto 5001.
  2. Conectar la respuesta de `esta_disponible()` para que cuando el servidor esté activo, la generación de andamios (`lubricar_propuesta`) y el análisis de imágenes Lens utilicen el modelo local como fallback de ultra-baja latencia sin llamadas cloud.

### Misión 4: Herramienta Nativa de Emulación en el Registry de MAGI
- **Ubicación en MAGI:** `magi/core/tools/emulador_tools.py`
- **Objetivo:** Registrar una herramienta `@reg.tool("emulador_ronda")` para que el enjambre de MAGI (Naoko y los agentes) pueda invocar directamente corridas de Vita3K sin salir del IDE.
- **Acción Requerida:**
  1. Registrar `emulador_ronda(rom, segundos)` conectada a `tools/vita3k_ctl.py run`.
  2. Verificar que la salida JSON se procese en la bitácora de optimización.
  3. Asegurar que los tests pasen y no violen el trinquete de líneas de `builtin.py`.

---

## 4. Comandos de Verificación Inmediata

Claude Desktop puede comprobar la salud del entorno ejecutando:

```powershell
# 1. En MAGI System IDE:
cd C:\Users\D\Documents\GitHub\MAGI-System-IDE
python scripts/verificar.py --rapido
python -m pytest tests/test_readme_claims.py

# 2. En YabauseVita:
cd C:\Users\D\Documents\GitHub\yabausevita
python tools/vita3k_ctl.py metrics
python tools/vita3k_ctl.py run --seconds 20 --windows 2
```
