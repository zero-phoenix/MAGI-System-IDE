# MEGAPLAN v12 — LILIM: la capa local superveloz, y la memoria enciclopédica falsable

**Fecha:** 6-sep-2026 · **Partida:** v5.24.0 · **Filosofía heredada:** una
afirmación sin evidencia verificada no es una afirmación — Lilim no la cambia:
la OBedece.

---

## 0. La idea en una frase

**Lilim es la capa LOCAL, determinista y superveloz de MAGI**: responde al
instante lo que el sistema ya sabe con procedencia, nunca inventa, y cuando
algo no está en su memoria dice «NO LO SÉ (local)» y escala al enjambre de
nube — que es quien razona. Lilim NO es un LLM: es un índice vivo sobre
memoria versionada, falsable contra internet, con fecha y fuente en cada
entrada.

## 1. Por qué hace al sistema más rápido y preciso

Medido (v5.16.0): el índice FTS5 local responde en **1 ms** sobre 2,7 MB.
Cada pregunta que Lilim responde localmente es una llamada de red que no se
gasta (los proveedores gratuitos tardan 3-22 s y fallan a menudo — misión
Tetris, 20+ min). Y cada respuesta de Lilim viaja CON su procedencia: el
sistema gana velocidad **sin** perder precisión, porque lo que Lilim no sabe
no lo responde.

## 2. La memoria enciclopédica, y por qué no se descarga internet

| Capa | Qué es | Estado |
|---|---|---|
| **M1 · Memoria permanente** | `controles.json` (mandos de 17 consolas + PC para jugar + decomp/puertos estilo dusklight), `descartes.jsonl`, `AUTOMODELO.json` — versionados, vivos en git | ✅ existe; ampliar (M1b) |
| **M2 · Índice local FTS5** | busca en bitácora, memoria, docs y código en 1 ms | ✅ existe (v5.16.0) |
| **M3 · Índice de repositorio** | `repos_top.json`: los mejores repos de GitHub curados por tema (emudev, decomp, gamedev, tooling, IA), cada uno con URL, qué es y fecha de curado — **metadatos, no megabytes** | 🌱 esta versión (semilla) |
| **M4 · Caché de conocimiento verificado** | cada respuesta de web del enjambre se guarda con URL+fecha (la regla 1 de Fase 1 del v6) y alimenta a Lilim | ⏳ depende de F1 |
| **M5 · Enciclopedia técnica** | docs versionados por dominio (SH2, VDP, Vita SDK, PyInstaller…) — se siembra por demanda de las rondas, nunca de una vez | ⏳ |

**Regla dura de M3-M5:** nunca «descargar internet» (C: tiene ~10 GB y un
índice de metadatos pesa kilobytes). Un repo se CLONA shallow a demanda al
workspace cuando el enjambre lo necesita; lo permanente es el índice curado
y su procedencia.

## 3. Lilim — qué hace y qué NO hace

**HACE (en ms, sin red):**

1. **Responder de la memoria permanente**: mandos de consola y PC, decomp/
   ports, reglas del proyecto, hallazgos del automodelo, descartes con lo
   rescatable — siempre con su fuente y fecha.
2. **Recomendar repos por tema** del índice curado (M3), con URL exacta.
3. **Enrutar**: si la pregunta es compleja o no está en memoria →
   «NO LO SÉ (local) — escala al enjambre», y el enjambre responde CON
   verificación (web/ejecución) y su respuesta alimenta M4.

**NO HACE (a propósito):**

- No razona, no escribe código, no debat e — para eso están los tres nodos.
- No inventa: si no está en su base, su única respuesta honesta es
  «NO LO SÉ (local)». Un Lilim que improvisa es el sistema entero mintiendo
  más rápido.
- No consume cuota ni red: su coste es cero.

**El puente:** Lilim corre SIEMPRE antes del enjambre (es barato); si
responde con procedencia, la respuesta llega al instante y queda marcada
como «local, falsable por: <fuente>». El usuario puede pedir siempre la
verificación de nube («verifícalo») y el enjambre contrasta contra internet.

## 4. Las fases

| # | Fase | Compuerta |
|---|---|---|
| **L1** | Semilla funcional (ESTA VERSIÓN): `lilim_pregunta(pregunta)` como herramienta del enjambre + `repos_top.json` sembrado + pruebas de «no inventa» | responde controles/decomp/repos/reglas en ms con procedencia; ante lo desconocido, NO LO SÉ — cero respuestas inventadas en la suite |
| **L2** | Índice de repos por demanda: `repos_clonar(nombre)` clona shallow al workspace con registro en journal | clon de tetris/decomp demo en <60 s y des-clonable |
| **L3** | Alimentar M4: cada respuesta con URL del enjambre se persiste en `conocimiento.jsonl` (URL+fecha+tema) y Lilim pasa a responderla | pregunta repetida → respuesta local con URL original |
| **L4** | Enciclopedia técnica por dominios (SH2, VDP, Vita SDK…) sembrada de las rondas del emulador | cada dominio entra cuando la ronda lo midió |
| **L5** | Lilim en la GUI: panel rápido «pregunta a Lilim» con la procedencia visible | respuesta local <50 ms mostrada con su fuente |

## 5. Curación del índice de repos (cómo se mantiene honesto)

- Cada entrada: `nombre, tema, url, que_es, curado:<fecha>`. Sin estrellas
  vanidosas: el campo es **para qué sirve a MAGI**.
- La curación se hace por rondas (como la bitácora del emulador): una ronda
  que descubrió que `objdiff` es la herramienta del matching la añade con su
  evidencia.
- Falsable: la URL es comprobable; si un repo muere, la entrada se marca
  `muerto:<fecha>` — no se borra (memoria inmutable).
