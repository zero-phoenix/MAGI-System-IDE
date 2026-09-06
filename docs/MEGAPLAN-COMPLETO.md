# MEGAPLAN COMPLETO — MAGI System IDE + YabauseVita
## Consolidado de las sesiones del 2-sep al 6-sep-2026 · Estado: v5.26.0 publicada

**Para:** cualquier agente que continúe (Antigravity IDE, ZCode Desktop, u otro)
**Repositorios:** `zero-phoenix/MAGI-System-IDE` (público) y `zero-phoenix/yabausevita` (público)
**Clones locales de trabajo:** `C:\Users\D\Documents\GitHub\MAGI-System-IDE` y `C:\Users\D\Documents\GitHub\yabausevita-zp`
**Máquina:** `DESKTOP-B6D864U` · Windows 10 22H2 · i7-3770 (8 hilos) · GTX 1050 low profile 2 GB (NO se usa) · 24 GB RAM · C: ~10 GB libres

---

## 0. LA REGLA QUE ORDENA TODO

> **Un documento sobre el sistema no es el sistema. Lee el código.**

Si algo de este megaplan contradice al código, **gana el código** y se corrige
el documento en el mismo commit. Caso fundacional: `PORTING_NOTES.md` describía
un esqueleto y el código real tenía dynarec, CHD y audio — un plan entero se
tiró por creerle al documento.

## 1. QUÉ ES CADA COSA (mapa mínimo)

- **MAGI**: IDE con enjambre de 3 IA (MELCHIOR tesis/BALTHASAR antítesis/CASPER
  síntesis) + NAOKO (supervisora, repara) + RITSUKO (auditora, solo informa) +
  **LILIM** (capa local superveloz, v12). Inferencia gratuita vía g4f
  (alineado a 8.1.1). 63 herramientas. ~1680 pruebas Python + 131 GUI.
- **YabauseVita**: emulador de Sega Saturn para PS Vita. Bitácora:
  `yabausevita-zp/docs/BITACORA-OPTIMIZACION.md` (hallazgos A1-A27, reglas R1-R16).
- **LILIM** (v12): capa LOCAL determinista, 0 ms-3,5 ms, sin GPU, sin red,
  sin inventar: motor EPD (activación escasa reportada), traductor es/en/de/
  ru/ja/zh, novedades 2023-2026 falsables, M4 (conocimiento con URL o no entra),
  CONTEXTO inyectado a los nodos. Plan completo: `docs/MEGAPLAN-v12-lilim.md`.

## 2. ESTADO VERIFICADO AL CIERRE (6-sep-2026)

| Versión | Qué fue | Estado CI/Release |
|---|---|---|
| v5.19.0 | Auditoría en vivo: pie de versión real, Vista previa, C6 (HuggingSpace aliases), Ritsuko R2+R4 | ✅ |
| v5.20.0 | Devorador de encargos arreglado; filosofía C liberada por medición (A9 cayó: drawn/presented/dropped ya se imprimen); motor trivial→fast | ✅ |
| v5.21.0 | Interfaz reconstruida: conversación = columna vertebral, cajón de paneles, línea de estado honesta; tope de 20 s a la llamada de estilo | ✅ |
| v5.21.1 | Pase de Balthasar: aprobación visible, «Ir a X» abre cajón, rutas clicables, cajón persistente, MotoresPanel | ✅ |
| v5.22.0 | Megaplan v11 documentado (misión Tetris: 11 hallazgos con evidencia) | ✅ |
| v5.23.1 | B1 comandos, A1 manifiesto, A3 código-antes-del-build, C3 sin humo, D1 filtro de ruido, B3 SYS_EXEC real, C2 motivo | ✅ (v5.23.0 falló y quedó con errata) |
| v5.24.0 | A2: autotest de teclas de 3 estados (verde/rojo/sin_comprobar) ejecutado por el packager | ✅ |
| v5.25.0 | LILIM v1: `lilim_pregunta`, `repos_de`, controles ampliados (PS2, pc_jugando, decomp/puertos), g4f 8.1.1 auditado (32/32) | ✅ |
| v5.26.0 | LILIM multimodal: motor EPD, traductor 6 idiomas, novedades 2023-2026, lilim_ensenar (M4), CONTEXTO inyectado, A2 con marca por fichero | ✅ |

**Repositorio limpio en `main`, CI verde, todos los releases conservados
(ninguno se borra NUNCA).**

### Los planes y su estado

| Plan | Hecho | Pendiente |
|---|---|---|
| **v6** (fases 1-11) | 6,7,8,10,11 | **F1** web_search/web_read sin navegador; **F2** subagentes por familia; **F3** plan.md vivo; **F4** compuerta obligatoria; **F5** veredicto «la pregunta era otra» |
| **v9** (Ritsuko) | R1, R2, R4 | **R3** portera de la sonda (tras rodar G4 en uso real) |
| **v10** (megaplan base) | D1-D6, M1, M2, P4, auditoría en vivo | **E1** ya superado (A9); **E2** instrumentar SH2LRU/dynarec; **E3** Ronda 4 (BIOS/CDB de NiGHTS); **E4** dynarec solo con Vita real; **P1-P3** diferidas con precondición |
| **v11** (Tetris) | A1, A2, A3, B1, B3, C2, C3, D1 | **C1-GUI** pintar el informe de cancelación; **D2** degradar motor por salud; **T5** el tetris.exe del Escritorio sigue con la R rota (los próximos juegos nacen con A2) |
| **v12** (Lilim) | L1 + motor EPD + traductor + novedades + M4 + contexto inyectado | **L2** `repos_clonar` shallow a demanda; **L3-avanzar** verificación automática de novedades; **L4** enciclopedia por dominios; **L5** panel de Lilim en la GUI |

### Pendientes prioritarios (el orden recomendado)

1. **D2** — degradar motor deep→fast cuando la salud de proveedores se
   degrade (la misión Tetris padeció 45+ min con proveedores moribundos).
   Señal: tasa de respuestas inservibles de la sonda/telemetría.
2. **L2** — `repos_clonar(nombre)`: clon shallow al workspace con registro en
   journal (la compuerta A3 ya lo exige) y des-registro limpio.
3. **F1-F5** del v6 en su orden original (web_search es la que más desbloquea).
4. **C1-GUI** — el informe de CancelReport pintado en la GUI (hoy va al Terminal).
5. **E2/E3** del emulador (instrumentar SH2LRU/dynarec; Ronda 4 BIOS/CDB de
   NiGHTS). **E4** solo con Vita real.
6. **E1-E3 de interfaz**: tarjeta de plan vivo en el flujo, hilos de
   Naoko/Ritsuko en la izquierda, manifiesto visible en la tarjeta de
   aprobación.

## 3. REGLAS NO NEGOCIABLES

1. **Ninguna corrida es evidencia sin ojos y oídos** (R9/R16): `has_image`,
   `has_motion`, veredicto de sonido.
2. **«No lo comprobé» ≠ «no funciona»** → se declara SIN COMPROBAR.
3. **Se mide contra un CONTROL en la misma corrida, nunca contra constantes
   de reloj** (R12 — aprendida cuatro veces).
4. **Compuerta completa antes de publicar**: `python -m ruff check magi/ tests/`
   · `python scripts/huerfanos.py --conteo` (techo 80) ·
   `python -m pytest tests/ -q` entera (~4 min en CI, ~25 local en serie) ·
   `python scripts/verificar.py --todo` (incluye .exe).
5. **Nunca subir el techo de un trinquete** ni tocar `KNOWN_ORPHANS`:
   conectar, adelgazar o extraer módulo. Techos actuales: `kernel.py` 1070,
   `orchestrator.py` 1550, `ritsuko.py` 800, `builtin.py` 800 (va en 798).
6. **Los FPS de Vita3K no son prueba de rendimiento** (R4).
7. **Ficheros con Python**, `newline='\n'`, comprobar BOM
   (`datos[:3] != b'\xef\xbb\xbf'`).
8. **No borrar releases anteriores. Nunca.** No escribir a mano documentos
   generados (AUTOMODELO, MAPA-INTERFAZ).
9. **Hardware no se toca; sin descargas grandes.** Lilim: stdlib pura, sin
   GPU, un hilo — no ahoga la máquina (i7-3770 + GTX 1050 2 GB).
10. **Si te equivocas, dilo y corrígelo en el mismo mensaje/commit.** Las
    erratas van visibles en las notas (v5.17.1, v5.23.1).

## 4. LA REGLA PERMANENTE DEL USUARIO (siempre, en cada versión)

> **Siempre que se compile localmente también se debe compilar en la nube
> (GitHub Actions); reescribir el README; y que en Releases aparezca el exe
> comprimido con la descripción de lo nuevo de la versión compilada en Actions.**

El flujo de publicación que ya está probado (v5.19 → v5.26):

```bash
# 1. compuerta local completa (incluye compilar el .exe en los slow tests)
python scripts/verificar.py --todo
# 2. versión en pyproject.toml + RELEASE_NOTES.md (notas CONCRETAS, nunca genéricas)
# 3. commit + push de main
git add -A && git commit -m "feat(vX.Y.Z): ..." && git push origin main
# 4. tag → Actions compila y publica el release con MAGI-IDE-v5.zip + CHECKSUMS.txt
git tag -a vX.Y.Z -m "..." && git push origin vX.Y.Z
# 5. verificar: gh run list --limit 2 && gh release view vX.Y.Z --json assets
```

- `scripts/publicar.py` (vía local) exige el entorno alineado a
  `requirements.lock` (9 dependencias divergen al cierre: g4f local 8.1.1 ya
  alineado; el resto sigue divergiendo). El camino canónico es el tag + Actions.
- README: actualizar cifras reales (tests, herramientas — las cuenta
  `test_readme_claims.py` contra el registry) y la sección de novedades.
- El `.exe` del CI no incluye los commits de `main` posteriores al tag: si el
  fix importa para el binario, taguear después del fix.

## 5. TRAMPAS QUE YA COSTARON TIEMPO (no repetir)

| Trampa | Arreglo |
|---|---|
| BOM de PowerShell | escribir con Python, `newline='\n'`, verificar 3 primeros bytes |
| Heredocs de bash mangles `\n` y `\\` | generar ficheros con Write/Edit tools o Python con `chr(92)` — NUNCA heredoc para código con escapes |
| Ruff sin fijar | `ruff==0.16.5` en requirements-dev |
| `NODE_ENV=production` local | `_entorno()` de verificar.py lo limpia; `npm` es `npm.cmd` |
| Módulo en disco y no en git | `git add -A` antes de la suite; `test_nada_sin_versionar` caza |
| OpenSSL de Git mata Vita3K | lanzar sin `Git\mingw64\bin` en PATH |
| `.replace()` sin assert | verificar el efecto; el mapa de interfaz caza cadenas |
| Lanzar MAGI con `&` en shell efímera | usar mecanismo persistente del agente |
| Tareas recuperadas tras reinicio | el zombie-resume se cuelga (ticket #1 histórico); conversación nueva como solución operativa |
| Docker: `./vdpm` del checkout | usar el `vdpm` del PATH |

## 6. PROCEDIMIENTOS CLAVE

**Compilar YabauseVita** (Docker, validado): ver v10 §12.1 — vdpm del PATH.
**Corrida verificada del emulador**: `python tools/vita3k_ctl.py run --seconds 60 --windows 6`
(con `has_image`, `has_motion`); config.cfg sin BOM, `cpu_mode=2`, `auto_bios=0`.
**Abrir MAGI**: `python -m magi.main` (persistente, con log a fichero).
GUI en `http://127.0.0.1:1420` (la ventana nativa pywebview es la misma app).

**El ritual de cierre de cada ronda/tarea** (no opcional):
1. Descartes a `magi/data/memoria/descartes.jsonl` con medición y `rescatable`.
2. `contrastar(prueba, ok, evidencia)` en el automodelo — incluidas las
   afirmaciones sobre el propio agente.
3. Hallazgos y reglas a la bitácora del emulador EN EL MISMO COMMIT del cambio.
4. Release con notas concretas + README actualizado + conservar releases.
5. Actualizar el estado de este megaplan.

---

## 7. ÍNDICE DE DOCUMENTOS DEL PROYECTO

- `docs/MEGAPLAN-v10-continuacion.md` — plan base + estado D/E/M/F/P
- `docs/MEGAPLAN-v11-tetris.md` — misión Tetris: 11 hallazgos + plan A-E + estado
- `docs/MEGAPLAN-v12-lilim.md` — Lilim: principios, capas M1-M5, fases L1-L5
- `docs/DECONSTRUCCION-INTERFAZ.md` — los 10 principios de la interfaz reconstruida
- `docs/TRASPASO.md` — traspaso histórico (actualizar al cerrar sesión)
- `docs/BITACORA-OPTIMIZACION.md` (en yabausevita-zp) — A1-A27, R1-R16

---

*Fin del consolidado. Verificado contra el código el 6-sep-2026. Si el código
cambió desde entonces, gana el código.*
