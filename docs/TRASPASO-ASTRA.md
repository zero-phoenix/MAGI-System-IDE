# Traspaso a Astra — Magisys y YabauseVita

**De:** Claude (Anthropic) · **Para:** ChatGPT con Astra (OpenAI)
**Fecha:** 10 de septiembre de 2026
**Máquina:** `DESKTOP-B6D864U` · Windows 10 22H2 · i7-3770 · 24 GB · GTX 1050 2 GB

---

## 0. Lee esto antes que nada

**Este documento no es el sistema.** Verifica cada cifra antes de apoyarte en
ella. No es una fórmula de cortesía: es la regla que me costó una ronda entera
hace cuatro días, y la que rompió el traspaso anterior.

El traspaso que yo recibí afirmaba «44 herramientas» (son **67**), «60,2 FPS de
mediana en Sonic R» (sin veredicto de imagen ni movimiento, o sea sin evidencia
según R9) y daba por arreglado un diagrama Mermaid que seguía roto en GitHub.
Yo mismo, después, le pedí al enjambre que «añadiera los contadores `drawn`,
`presented` y `dropped` al log porque esta build no los imprime» — y **ya los
imprimía**. Me fié del hallazgo A9 de la bitácora en vez de abrir el fichero.

El comando que zanja cualquier duda:

```powershell
cd C:\Users\D\Documents\GitHub\MAGI-System-IDE
python scripts/verificar.py --rapido
```

---

## 1. Reglas innegociables

1. **Un documento no es el sistema: lee el código y mide en runtime.**
2. **Sin tests verdes no hay release.** `python scripts/verificar.py --rapido`
   al 100 %, y `--todo` antes de publicar.
3. **Los trinquetes no se suben, nunca.** Si algo no cabe, extrae un módulo.
   Medido hoy: `kernel.py` 1069/1070 · `orchestrator.py` 1534/1550 ·
   `builtin.py` 797/800 · `App.tsx` 886/900. Tres de los cuatro van al límite.
4. **El README no miente** (`tests/test_readme_claims.py`): el conteo de
   herramientas se compara con el registry en **igualdad exacta**.
5. **Nada de navegadores externos** (`magi/core/no_browser.py`). Toda la UI en
   WebView2. Hay 16 tests que lo vigilan y un cortafuegos que bloquea intentos.
6. **Consola UTF-8 tolerante**: `reconfigure(encoding="utf-8", errors="replace")`
   en todo script nuevo, o cp1252 revienta con una flecha o un acento.
7. **Los ficheros se escriben con Python y `newline="\n"`.** PowerShell mete BOM
   y ya ha roto `pyproject.toml` y el `config.cfg` del emulador (hallazgo A16).
8. **Ningún dato del usuario se borra.** Los duplicados van a `D:\_DUPLICADOS`
   con inventario, para que decida él.

---

## 2. Qué es cada cosa

**Magisys** (antes «MAGI System IDE») es un IDE cuyo motor es un enjambre de
tres inteligencias que **debaten antes de actuar**: Melchior propone la tesis,
Balthasar la refuta ejecutando el código, Casper sintetiza. Naoko supervisa y
Ritsuko audita a Naoko. Cada nodo está anclado a una **familia de modelo
distinta** a propósito: un crítico con los mismos sesgos que el proponente no
critica nada.

- Repo: `C:\Users\D\Documents\GitHub\MAGI-System-IDE` → GitHub
  **`zero-phoenix/Magisys`** (renombrado el 6-sep; GitHub redirige el nombre
  viejo). La carpeta local conserva el nombre antiguo a propósito: renombrarla
  rompe rutas de la máquina.
- Kernel WebSocket: `ws://127.0.0.1:20128` · GUI: `http://127.0.0.1:1420`
- Arranque desde fuente: `python -m magi.main`
- Versión en `pyproject.toml`: **5.27.0** (ojo: existe un tag `v5.27.1`; esa
  discrepancia venía del traspaso anterior y sigue sin resolverse).

**YabauseVita** es un emulador de Sega Saturn en C para PS Vita, probado en
Vita3K.

- Repo primario: `C:\Users\D\Documents\GitHub\yabausevita-zp` →
  `zero-phoenix/yabausevita`
- Secundario: `C:\Users\D\Documents\GitHub\yabausevita`
- Vita3K: `...\yabausevita\vita3k\Vita3K.exe`
- Harness: `tools/vita3k_ctl.py` (lanza sin elevar, autostart, capturas)
- ROMs CHD: Sonic R, Panzer Dragoon, NiGHTS into Dreams
- **La bitácora `docs/BITACORA-OPTIMIZACION.md` es la fuente de verdad del
  emulador**, con hallazgos A1–A27 y reglas R1–R16. Léela entera antes de
  proponer nada — pero contrasta cada hallazgo con el código, porque **A9 ya
  está caducado** (ver §5).

---

## 3. Lo que hice, y por qué

Cinco commits, todos en `main` y publicados. Revísalos: `git log c806e9a~5..`

### 3.1 Filosofías ortogonales por asignación (v5.18.0)

La bitácora §2 exige tres propuestas que ataquen **mecanismos distintos**.
`generate_variants` las diversificaba **por semilla** (`seed + n*101`): eso da
tres redacciones, no tres ataques. Nada impedía que las tres recortaran
`composite` con otras palabras y la ronda gastara tres compilaciones para medir
una sola idea.

Ahora `magi/modules/swarm/filosofias.py` **asigna**: variante 0 → `composite`,
1 → `upload`, 2 → `dropped`, cada una con su riesgo y su predicción falsable.

Dos cosas que salieron de construirlo:

- **Con 2 variantes el reparto estaba roto por diseño.** `_n_variantes`
  devuelve 2 (hallazgo D6), y `asignada` cicla, así que «repartir mejor» no se
  exploraría jamás. Sube a 3 solo en rondas del emulador.
- **§6 de la bitácora estaba sin implementar.** Decía: «si alguna choca con una
  regla de §5.2, se rechaza sin llegar a compilar». No lo hacía nadie. Ahora R1,
  R6, R14 y R15 se comprueban sobre el texto y el choque llega **pegado** a la
  propuesta infractora.

Escribí el test esperando 2 choques con R6 y el comprobador dijo **3**: la
filosofía C mueve el `composite` entre núcleos, y eso sigue siendo camino de
render. Redescubrió solo lo que la ronda 0 concluyó midiendo. La expectativa
equivocada era la mía.

### 3.2 Renombrado a Magisys

94 apariciones en 35 ficheros, más el artefacto (`MAGI-IDE-v5` → `Magisys`) y
el repo en GitHub. **No toqué** `docs/historial/`, `artifacts/` ni las citas de
`D:/PROYECTOS/MAGI System IDE`: reescribir el registro de lo que se publicó con
el nombre viejo lo falsifica.

**El renombrado iba a romper el release y se cazó antes de publicar.**
`.gitignore` ignora `*.spec` con una excepción **por nombre**. Al renombrar,
`Magisys.spec` cayó bajo la regla general y git dejó de verlo — ni como no
seguido. Aquí todo pasaba porque un test lo lee del disco; en un checkout
limpio, `pyinstaller Magisys.spec` no encuentra nada y no hay `.exe`.
Guardado ahora por `test_lo_que_el_release_necesita_esta_en_git`, que mira
**git** y no el disco.

### 3.3 La mielina fabricaba un defecto en cada propuesta real

`pre_auditoria_estatica` pasaba el texto **entero** a `ast.parse`. Medido antes
de tocar nada:

```
propuesta real (prosa + bloque cercado) -> "SyntaxError en línea 1"   FALSO
código C (el emulador entero)           -> "SyntaxError en línea 1"   FALSO
```

Le inyectaba a Balthasar una objeción inventada en **cada** propuesta real, y
Balthasar gastaba su turno defendiéndola. Ahora extrae solo los bloques Python,
**calla ante C en vez de mentir**, ve `async def` y no deja que un docstring
disfrace una función vacía.

Su `except Exception: pass` —el mismo defecto que la función audita— devolvía
«sin defectos» al fallar por dentro: un verde falso justo donde se decide si
hay que criticar.

### 3.4 La réplica capitulaba el 100 % de las veces

La compuerta de la Fase 8 por fin tenía datos: **14 rondas reales, `concedio:
true` en las 14.** No era «la salida legítima funciona»: era la única. Y una
réplica que siempre se rinde **invierte** el mecanismo — Casper no llega a
arbitrar y la antítesis gana por defecto, que es el mismo fallo con el signo
cambiado.

La causa estaba en el prompt, empujando tres veces al mismo lado: ofrecía la
concesión primero, la llamaba «salida legítima, no una derrota», y cerraba con
«Balthasar ejecutó el código, y tú no». Reescrito simétrico: separar qué
objeciones aciertan y cuáles no, conceder una por una, **defender el resto**.

Verificado en una ronda real posterior: Melchior concedió dos objeciones y
**refutó** la tercera. Casper volvió a arbitrar. Con su medición
(`tasa_de_concesion`, techo 85 %, mínimo 10 rondas) para que no vuelva a
degenerar en silencio.

### 3.5 Otros agujeros cerrados

- **El lint no miraba `scripts/`.** Ahí viven `verificar.py`, `publicar.py` y
  `huerfanos.py`: la compuerta, el publicador y un trinquete. 7 errores, todos
  en el script recién escrito por el agente anterior.
- **El cliente de interacción no veía el debate.** Escuchaba
  `topic in ("MELCHIOR", ...)` y el bus publica `AGENT_POST` con el nodo en el
  payload. Reescrito, con `line_buffering=True` (sin él no se ve nada hasta que
  el proceso muere: un informe post mortem, no una supervisión).
- **El diagrama Mermaid del README**, roto dos veces seguidas en GitHub. El
  cilindro `[( )]` con etiqueta larga y tres `subgraph` con aristas cruzando su
  frontera. Guardado por `tests/test_mermaid_renderiza.py`.
- **Venim**: ya no había acoplamiento; le puse la prueba que lo impide, y cazó
  que la interfaz se presentaba como «independiente de Venim». Un producto que
  se define por lo que no es sigue atado a ello.

---

## 4. En qué me equivoqué yo — corrígeme

El usuario te ha pedido explícitamente que revises mi trabajo. Estos son los
sitios donde ya sé que fallé; busca los que no sé.

1. **Le di al enjambre un encargo con premisa falsa.** Le pedí «añade `drawn`,
   `presented` y `dropped` al log, que esta build no los imprime», apoyándome
   en el hallazgo **A9** de la bitácora. Fui a comprobarlo después:
   `VIDGPUVdp2LogTiming` en `src/vita/vidgpu.c` **ya los imprime**. A9 está
   caducado y **hay que corregirlo en la bitácora**. Melchior tenía razón al
   decir que no encontraba lo que yo describía, y yo lo tomé por incompetencia.
2. **Dejé que el enjambre escribiera en el repo del emulador sin red.** Truncó
   `src/vita/vidgpu.c` de **417 líneas a 15**. Lo restauré con `git checkout`
   y no llegó a commitearse, pero el agujero sigue abierto (ver §5.1).
3. **Mi cliente de supervisión pinta campos mal**: `[COSTE] None/None`,
   `usa None()`, `[TITULO] None`. Los nombres de campo del payload no
   coinciden. Es cosmético pero estorba justo cuando hay que mirar.
4. **No verifiqué el diagrama Mermaid en GitHub.** Lo arreglé y le puse
   guardas, pero el navegador se me cayó y **no llegué a ver la página**.
   Compruébalo tú: <https://github.com/zero-phoenix/Magisys>. Si sigue roto,
   mi arreglo no valía y el test que escribí tampoco.
5. **`pyproject.toml` dice 5.27.0 y existe un tag `v5.27.1`.** Lo detecté y no
   lo resolví.
6. **Tres umbrales absolutos de tiempo siguen vivos** en
   `test_fase2_velocidad.py:223` y `test_phase2.py:106,191`. Son la misma
   clase de bomba que tumbó el CI en la v5.17.0: miden el runner, no el
   código. Se arreglan **contra un control medido en la misma corrida**, nunca
   subiendo la constante.

---

## 5. Lo que queda por hacer

### 5.1 URGENTE — la red que falta antes de dejar al enjambre tocar código

**Nada impide que una herramienta de escritura destruya un fichero.** Medido:
`vidgpu.c` pasó de 14 267 bytes a 523. Dos guardas concretas:

- **Escritura que reduce un fichero por debajo de ~25 % de su tamaño no es una
  edición, es un borrado**: debe rechazarse y pedir confirmación explícita.
  Mira `magi/core/tools/builtin.py` (ojo: 797/800 líneas — extrae módulo).
- **Las citas deben comprobarse.** En la ronda del 8-sep, Melchior se defendió
  diciendo «las variables están definidas en `vita_gpu.h`, líneas 42-45».
  **Ese fichero no existe.** Es el mismo patrón que cuando inventó «53,3 FPS»
  sin ejecutar nada. Una réplica que capitula es inútil; una que se defiende
  con citas inventadas es peligrosa, porque suena convincente. Si cita
  `fichero:línea`, que exista y diga eso.

### 5.2 La interfaz, rehecha desde cero — funcional y gráfica

Es el encargo grande y está sin empezar. El estado de partida, medido:

```
magi-gui/src : 6932 líneas de TS/TSX, 45 ficheros
App.tsx      : 886 líneas de 900 — quedan 14
ConfigPanel  : 502   useMagiSocket: 446   store.ts: 314
tests GUI    : 131 (npm test), en verde
```

**El techo de `App.tsx` no es un obstáculo: es el diagnóstico.** Un componente
de 886 líneas que lo orquesta todo es lo que hay que deshacer. Rehacerla «desde
cero» aquí significa **extraer y recomponer**, no borrar 6932 líneas probadas.

Lo que el usuario pidió, literal: *«que sea más operativa y fácil de usar»*.
Tres cosas concretas que sé que hoy fallan, por haberlas visto:

- **El debate no se sigue.** Los tres nodos publican, pero para entender en qué
  punto va una ronda hay que leer mensajes largos. La información que importa
  —ruta elegida, fase actual, coste, si hubo réplica, si concedió— existe en el
  bus (`swarm.routed`, `swarm.fases`, `task.usage`) y está mal aprovechada.
- **La aprobación bloquea sin decirlo.** Cuando el enjambre queda en
  `WAITING_USER_APPROVAL` se para y no es evidente que te espera a ti. Naoko ya
  traduce el estado a lenguaje llano (`naoko_lenguaje.py`); úsalo.
- **Los mandos no explican qué hacen.** Ya hay un comentario en `App.tsx` sobre
  esto: «MOTOR: Inferencia Optimizada» y «ESTILO: Técnico» son nombres, no
  explicaciones.

Restricciones que no puedes saltarte: WebView2 (nada de navegador externo), la
paleta Evangelion existente (naranja `#FF6600`, turquesa `#00D2C4`), `npm test`
en verde, y `npm run build` limpio.

### 5.3 El icono del .exe

Pendiente. Pedido: **más minimalista**, conservando los colores del actual, que
siga representando **claramente las tres IAs**, y que **no se vea pequeño**.
Ese último punto suele ser margen interior excesivo: el glifo debe llenar el
lienzo. Hay que generar el `.ico` multi-resolución (16/32/48/256) y comprobarlo
a 16 px, que es donde un diseño «minimalista» se convierte en una mancha.

### 5.4 El encargo del emulador, sin terminar

El usuario quiere que **Magisys** (no tú) mejore YabauseVita con las tres
filosofías ortogonales, lo pruebe en Vita3K con Sonic R y los demás, y luego lo
suba compilado por Actions con README reescrito y un release con un párrafo de
descripción. **Hasta que existan las guardas de §5.1, no le sueltes el
repositorio.**

Tres rondas dieron: análisis correcto (identificó bien R6 y A7), una
fabricación de datos, una fabricación de citas y un fichero destruido.

---

## 6. Orden que yo seguiría

No es una orden, es un razonamiento; si ves uno mejor, sigue el tuyo y di por
qué.

1. **Verifica** (§0) y **revisa mis cinco commits**. Si algo de lo que escribí
   está mal, corrígelo antes de construir encima.
2. **Comprueba el Mermaid en GitHub** — es de un minuto y cierra el único
   arreglo mío que no llegué a ver funcionando.
3. **Las guardas de §5.1**, porque desbloquean todo lo demás y porque el daño
   ya ocurrió una vez.
4. **La interfaz** (§5.2): empieza extrayendo de `App.tsx`, con los 131 tests
   como red. Cada extracción, verde antes de la siguiente.
5. **El icono** (§5.3), que es aislado y se puede colar entre medias.
6. **Devuelve el encargo del emulador a Magisys** (§5.4), ya con red.

---

## 7. Cómo se publica

```powershell
python scripts/verificar.py --todo        # compuerta completa
git add -A && git commit                  # mensaje que explique POR QUE
gh repo edit --visibility public --accept-visibility-change-consequences
git push origin main
git tag -a vX.Y.Z -m "..." && git push origin vX.Y.Z
# esperar CI + Build and Release en verde
gh release download vX.Y.Z                # y verificar el SHA-256 de verdad
gh repo edit --visibility private --accept-visibility-change-consequences
```

Público solo mientras compila —los minutos de Actions se pagan en privado— y
privado al terminar. **Ninguna release anterior se borra jamás**, y una
etiqueta que ya tiene artefactos publicados **no se mueve**: se corrige con una
versión nueva y una errata en las notas.

---

## 8. Lo que este proyecto ha aprendido a base de fallar

Cada una nació de un fallo concreto. No son consejos.

- **Un intérprete roto también «hace 60 FPS»** (A12). Ninguna corrida es
  evidencia sin veredicto de imagen, movimiento y sonido (R9, R16).
- **Se mide contra un control, no contra una constante** (R12). Un umbral
  absoluto mide el runner. `t_melchior_ms < 900` reventó el CI con 4531 ms, y
  al medirlo otra vez en la máquina donde «pasaba» dio 1218: nunca valió.
- **Quitar el síntoma sin cerrar la fuente no arregla nada.** Limpié dos filas
  de prueba de `replica.jsonl` y volvieron a la siguiente corrida.
- **Una objeción fabricada es peor que el silencio**, porque el crítico la
  defiende y el debate se va detrás de ella.
- **Verde sin comprobar es peor que rojo.**
- **Si el techo estorba, el diseño está mal**, no el techo.
