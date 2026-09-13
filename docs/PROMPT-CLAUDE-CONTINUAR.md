PROMPT PARA CLAUDE (Claude Code / Claude Desktop) — CONTINUAR EL TRABAJO DE MAGI SYSTEM IDE
============================================================================================

Cómo usarlo: en Claude Code, ábrelo con la carpeta del repo como working
directory (`cd C:\Users\D\Documents\GitHub\MAGI-System-IDE` y lanza `claude`)
y pega esta instrucción entera. En Claude Desktop, pégala en la conversación
con el repositorio en el contexto (o usa el conector de filesystem apuntando
a esa carpeta). El documento "MEGAPLAN-COMPLETO-MAGI.md" está en el
escritorio y también en docs/ del repositorio: léelo entero ANTES de
escribir una línea de código.

------------------------------------------------------------------------

Continúas un trabajo en curso sobre dos repositorios míos de GitHub:
zero-phoenix/MAGI-System-IDE y zero-phoenix/yabausevita. La última sesión
cerró la versión v5.26.0 (LILIM multimodal: motor EPD local, traductor de 6
idiomas, memoria de novedades 2023-2026 falsables, M4 de conocimiento con
URL obligatoria). NO empieces de cero y NO improvises el contexto: está todo
escrito y verificado. Este proyecto tiene una regla fundacional que ordena
todo lo demás:

> **Un documento sobre el sistema no es el sistema. Lee el código.**

Si algo de lo que leas contradice al código, gana el código — y corrige el
documento en el mismo commit.

## LO PRIMERO, ANTES DE PROPONER NADA

1. Lee entero el fichero `docs/MEGAPLAN-COMPLETO-MAGI.md` (el estado
   consolidado: las 8 versiones publicadas, los 5 planes con su estado,
   reglas, trampas y procedimientos).
2. Verifica el estado real contra GitHub:
   - `git log --oneline -8` y `git status`
   - `gh run list --limit 3` (CI/Actions)
   - `gh release view v5.26.0 --json assets` (el último release)
   - `python -m pytest tests/ --collect-only -q | tail -1` (las pruebas que
     hay de verdad)
3. Comprueba que el entorno vive: `python -m magi.main` abre la interfaz
   (frontend en http://127.0.0.1:1420, kernel WebSocket en 127.0.0.1:20128).
4. Dime en TRES FRASES qué entendiste del estado y qué paquete vas a atacar
   primero. NO escribas código antes de eso.

## QUÉ ES MAGI (mapa mínimo)

IDE con un enjambre de tres IA que debaten antes de actuar (MELCHIOR tesis,
BALTHASAR antítesis, CASPER síntesis) + NAOKO (supervisora que repara) +
RITSUKO (auditora que solo informa) + **LILIM** (la capa local superveloz de
la v12: determinista, sin GPU, sin red, sin inventar). Inferencia 100 %
gratuita vía g4f. 63 herramientas. ~1680 pruebas Python + 131 de interfaz.
Hermano del sistema: el emulador YabauseVita (PS Vita), con su bitácora de
optimización A1-A27 / R1-R16 en `yabausevita-zp/docs/`.

## REGLAS NO NEGOCIABLES

1. **Compuerta completa antes de publicar**, nunca un subconjunto:
   - `python -m ruff check magi/ tests/` (ruff==0.16.5 fijado)
   - `python scripts/huerfanos.py --conteo` (techo 80)
   - `python -m pytest tests/ -q` ENTERA (~4 min en CI; ~25 min local en serie)
   - `python scripts/verificar.py --todo` (incluye compilar el .exe)
   Los trinquetes cazan cosas que ningún subconjunto ve — cuatro rebotes de
   CI en un día lo demostraron.
2. **Nunca subir el techo de un trinquete** ni tocar KNOWN_ORPHANS: conectar
   el módulo, adelgazar o EXTRAER a components/módulo nuevo (el techo forzó
   extracciones y las tres mejoraron el diseño). Techos actuales:
   kernel.py 1070 · orchestrator.py 1550 · ritsuko.py 800 · builtin.py 800.
3. **Medir contra un CONTROL en la misma corrida, nunca contra constantes de
   reloj** (R12 — aprendida cuatro veces: input del emulador, t_melchior<900,
   la cascada y el recon tardío).
4. **Ninguna corrida del emulador es evidencia sin ojos y oídos** (R9/R16):
   `has_image`, `has_motion`, veredicto de sonido. Y **los FPS de Vita3K no
   son prueba de rendimiento** (R4): Vita3K decide corrección, las métricas
   internas deciden rendimiento.
5. **«No lo comprobé» ≠ «no funciona»**: se declara SIN COMPROBAR. Inventar
   un veredicto negativo es peor que omitirlo.
6. **Ficheros con Python**, `newline='\n'`, verificar sin BOM. PowerShell
   mete BOM y ya rompió pyproject.toml y el config.cfg del emulador.
7. **No borrar releases anteriores. Nunca.** No escribir a mano documentos
   generados (AUTOMODELO, MAPA-INTERFAZ).
8. **Hardware no se toca, sin descargas grandes** (i7-3770 + GTX 1050 2 GB,
   C: con ~10 GB): Lilim es stdlib pura, sin GPU, un hilo — así debe seguir.
9. **Si te equivocas, dilo y corrígelo en el mismo mensaje/commit.** Las
   erratas van visibles en RELEASE_NOTES (v5.17.1, v5.23.1).
10. **trinhqueting de comandos**: `task.cancel`, «parar todo»,
    `EMERGENCY_STOP` tecleados en el input son ÓRDENES (magi/core/comandos.py),
    nunca encargos — no lo "arregles" hacia atrás.

## LA REGLA PERMANENTE DE PUBLICACIÓN (siempre, en cada versión)

Compilar localmente Y en la nube, README actualizado, y el exe comprimido en
Releases con la descripción de lo nuevo:

```bash
# 1. compuerta local completa (compila el .exe en los tests slow)
python scripts/verificar.py --todo
# 2. versión en pyproject.toml + RELEASE_NOTES.md (notas CONCRETAS:
#    qué cambió, qué se midió, qué se encontró probando lo ya escrito)
# 3. commit + push de main
git add -A && git commit -m "feat(vX.Y.Z): ..." && git push origin main
# 4. tag → GitHub Actions compila y publica el release:
git tag -a vX.Y.Z -m "..." && git push origin vX.Y.Z
# 5. verificar el release:
gh run list --limit 2 && gh release view vX.Y.Z --json assets
```

- El camino canónico de release es el TAG + Actions (compila el exe con su
  Python embebido y publica MAGI-IDE-v5.zip + CHECKSUMS.txt).
  `scripts/publicar.py` (vía local) exige el entorno alineado a
  requirements.lock — si diverge, se niega con razón: alinea o taguea.
- README: actualizar cifras reales (el número de tests y de herramientas lo
  cuenta `test_readme_claims.py` contra el registry — ahora 63 herramientas)
  y las novedades de la versión.
- Conservar TODOS los releases anteriores. Nunca se borra uno.

## QUÉ TIENES QUE HACER, EN ORDRE (detalle y compuertas: megaplan §2)

1. **D2** — degradar el motor deep→fast cuando la salud de proveedores se
   degrade (tasa de respuestas inservibles de la sonda/telemetría; la señal
   existe en `registry` y `sonda`). La misión Tetris padeció 45+ minutos con
   proveedores moribundos sin salida limpia.
2. **L2 de Lilim** — `repos_clonar(nombre)`: clon shallow de un repo del
   índice `repos_top.json` al workspace, registrado en el journal (la
   compuerta A3 ya exige fuente escrita) y con des-registro limpio.
3. **F1-F5 del megaplan v6**, en su orden original:
   F1 web_search/web_read SIN navegador (presupuesto por ronda, cita
   obligatoria URL+fecha, sin red → SIN COMPROBAR);
   F2 subagentes por familia (solo lectura, conclusión no volcado, tope por
   ronda; compuerta: gasta MENOS contexto);
   F3 plan.md vivo por tarea (Casper no cierra con partes pendientes);
   F4 el «hecho» no se emite sin verificar.py adjunto;
   F5 veredicto «la pregunta era otra».
4. **C1-GUI** — pintar el informe de cancelación (CancelReport) en la
   interfaz, no solo en el Terminal.
5. **E1-E3 de interfaz** — tarjeta de plan vivo en el flujo, hilos de
   Naoko/Ritsuko en la columna izquierda, manifiesto visible en la tarjeta
   de aprobación.
6. **L3/L4 de Lilim** — verificación automática de las novedades contra sus
   `fuente_verificar` (cambiar verificado:false → true con fecha y URL) y
   enciclopedia por dominios sembrada por las rondas.
7. **Emulador** — **E2** instrumentar SH2LRU y el dynarec con coste por
   instrucción (la palanca real según R15; hoy solo SH2Fast la lleva);
   **E3** Ronda 4: por qué la BIOS abandona el disco de NiGHTS tras 3
   sectores del IP.BIN (hipótesis: lado BIOS/CDB; Panzer como control en la
   misma corrida). El dynarec solo se declara roto/funcionando con una Vita
   real (E4).

## EL RITUAL DE CIERRE DE CADA RONDA/TAREA (no opcional)

1. Descartes a `magi/data/memoria/descartes.jsonl` con medición y campo
   `rescatable`. Un enfoque que pierde deja conocimiento igual que uno que
   gana.
2. `contrastar(prueba, ok, evidencia)` en el automodelo — también sobre tus
   propias afirmaciones.
3. Hallazgos y reglas a la bitácora del emulador, y la entrada de la ronda,
   EN EL MISMO COMMIT que el cambio ganador.
4. Release con notas concretas + README actualizado + conservar releases
   (regla permanente de arriba).
5. Actualizar el estado de los paquetes en `docs/MEGAPLAN-COMPLETO-MAGI.md`.

## TRAMPAS QUE YA COSTARON TIEMPO (no las repitas)

| Trampa | Arreglo |
|---|---|
| BOM de PowerShell | escribir con Python, `newline='\n'`, verificar 3 bytes |
| Heredocs/strings con `\n` y `\\` en bash | generar código con herramientas de fichero o Python con `chr(92)` — un `.replace()` sin assert es un no-op silencioso |
| Ruff sin fijar | 0.16.5 en requirements-dev; no actualizar por libre |
| `NODE_ENV=production` local | `_entorno()` de verificar.py; `npm` es `npm.cmd` |
| Módulo en disco y no en git | `git add -A` antes de la suite |
| OpenSSL de Git mata Vita3K | lanzar sin `Git\mingw64\bin` en PATH |
| Tareas recuperadas tras reinicio | el zombie-resume se cuelga; solución operativa: conversación nueva (ticket #1) |
| Lanzar MAGI con `&` en shell efímera | mecanismo persistente del agente |
| Docker: `./vdpm` del checkout | usar el `vdpm` del PATH |
| exe windowed sin consola | la marca del autotest viaja en `autotest_ok.txt` |

## ENTORNO Y CUENTAS

- Cuenta GitHub activa: **zero-phoenix** (gh CLI ya autenticada). El clon
  `Documents\GitHub\yabausevita` SIN `-zp` está OBSOLETO: usa
  `Documents\GitHub\MAGI-System-IDE` y `Documents\GitHub\yabausevita-zp`.
- Windows 10 22H2, i7-3770, GTX 1050 2 GB (Lilim no la usa), 24 GB RAM.
  C: ~10 GB libres — sin descargas grandes.
- Docker disponible (builds VitaSDK). Vita3K instalado (config en
  `%APPDATA%\Vita3K\Vita3K\ux0\data\yabause\config.cfg`, sin BOM).

## CÓMO QUIERO QUE ME HABLES

En español. Dime lo que **mides**, no lo que supones. Si te equivocas, dilo
y corrígelo en el mismo mensaje. Si algo no se puede comprobar, dilo (SIN
COMPROBAR) en vez de rellenarlo. Y si crees que una de mis instrucciones
está mal, discútela — este proyecto ha mejorado cada vez que alguien señaló
que el plan apuntaba al sitio equivocado.

Empieza por lo primero: leer `docs/MEGAPLAN-COMPLETO-MAGI.md` entero,
verificar el estado real contra GitHub, y devolverme las tres frases.
