## MAGI System IDE v5.1.4

Reconstrucción completa sobre v5.0.28. **Suite completa en verde en Linux y
Windows**: sin tests verdes no hay release.

**Descarga:** `MAGI-IDE-v5.zip` más abajo contiene el ejecutable de Windows,
compilado por GitHub Actions tras pasar la suite completa.

---

### Qué corrige v5.1.4

**Tu pregunta se perdía sin avisar.** Mientras una tarea esperaba tu
aprobación, cualquier cosa que escribieras se absorbía como su respuesta. Una
pregunta nueva y sin relación se gastaba como comentario a otra propuesta y
nunca se contestaba. Desde fuera parecía que el sistema no responde. Ahora se
mira **qué** has escrito, no solo en qué estado está lo anterior; ante la duda,
pregunta nueva.

**Se podía aprobar por accidente.** La comprobación era por subcadena: el «si»
de «siempre», de «análisis» o de «sigue así» daba la propuesta por aprobada, la
cerraba y **disparaba la ejecución automática de su código**. Ahora se comparan
palabras enteras y un rechazo en la misma frase gana.

**El enjambre seguía llamando a proveedores muertos.** Los tres nodos tenían su
familia escrita a fuego (`deepseek`, `claude`, `qwen`). Cuando el catálogo se
reverificó y esas familias se quedaron sin candidatos vivos, la corrección no
les llegó: seguían gastando seis intentos condenados por ronda —dos de ellos
intentando abrir Chrome— antes de dar con uno que respondiera. **Esa era la
demora.** Ahora la familia se deriva del único sitio donde se decide.

**Un acento tumbaba la respuesta a medias.** `'charmap' codec can't encode` no
era un fallo de proveedor: era la consola de Windows reventando al escribir una
tilde, y esa excepción abortaba el streaming y obligaba a pedir la respuesta
entera otra vez. En un proyecto que habla español ocurría casi siempre.

**Naoko no respondía a lo que se le preguntaba.** A «hice una pregunta pero
nadie me responde» contestó «¿qué pregunta era?», teniendo delante, en su
propio prompt, la tarea que estaba esperándole a él. Ahora ante una queja
operativa la primera frase lleva el dato concreto.

**`prov-a`, `prov-b`, `prov-c`** no significaban nada y ya ni correspondían a
proveedores reales. Se sustituyen por el rol, la familia que lo atiende y su
latencia medida. **MOTOR** y **ESTILO** explican qué hacen: el primero cambia
cuánto se piensa, no qué modelo se usa; el segundo solo afecta a la redacción.

Medido tras el cambio: tres preguntas reales en **13,1 s** (antes ~49 s solo de
proveedor), las tres en español, sin un solo intento condenado.

---

### Qué corrigió v5.1.3

Todo sale de una captura de pantalla de la interfaz y del registro que la
acompañaba.

**Dos pestañas que no enseñaban nada.**
«Configuración» estaba en la barra, se podía pulsar y no aparecía nada: el
panel nunca se había escrito. Ahora muestra el estado real del sistema —reparto
del enjambre, latencia medida por candidato, cortacircuitos, capas del
cortafuegos, herramientas por rol y rutas—, todo leído en vivo.

«Vista previa» tenía un `<iframe src="http://localhost:3000">` fijo en el
código. Nadie levanta ese puerto, así que lo que se veía era la página de error
del navegador: un cuadro blanco con una nube, a fondo blanco dentro de una
interfaz negra. El error de fondo era asumir que MAGI construye servidores web;
MAGI construye **artefactos**. Ahora los lista del más reciente al más antiguo,
con visor por tipo: imágenes sobre tablero de ajedrez para que un PNG
transparente no parezca vacío, HTML, vídeo, audio, PDF y texto. La URL sigue
disponible en su propio modo.

**Naoko respondía en chino.**
A un «hola naoko» contestó `嗨~请问有什么可以帮你的吗`. Los proveedores gratuitos
son puertas a modelos con sesgos de idioma distintos y un saludo corto da poca
señal. Ahora se le dice en qué idioma contestar **y se comprueba la respuesta**:
si vino en otro alfabeto se rota de proveedor en vez de entregarla. La misma
defensa se aplica a los tres nodos del enjambre.

**Naoko no sabía quién es Melchior.**
Ante «¿por qué se demora tanto Melchior?» habló de servidores saturados, planes
de pago y de escribir al soporte de Melchior, como si fuera un producto de otra
empresa. Melchior es un nodo de este mismo proceso y Naoko tenía el dato
delante. Ahora su identidad declara que el enjambre son compañeros suyos, y su
prompt incluye el reparto real, la latencia medida y las tareas en curso.

**El sistema iba lento.**
El registro mostraba 11 llamadas y ~49 s de proveedor, con un pico de 13.953 ms
de Yqcloud que arrastraba la etapa entera de Melchior habiendo alternativas de
2 s en la misma familia. Ahora hay **petición cubierta**: si un candidato no
contesta en 4 s se lanza el siguiente en paralelo y gana el que responda antes.
El caso bueno no cambia; el malo deja de pagar la cola de latencia. Y el orden
de intento lo decide la latencia medida, no la afinidad a secas.

**Un aviso falso, que era mío.**
`self_test()` consultaba la ruta de Chrome para comprobar la capa CDP, y eso
contaba como intento de abrir navegador: el registro se llenaba de
`BLOQUEADO cdp.find_chrome_path` y Naoko informaba de intentos que nunca
ocurrieron. Avisar de algo que no ha pasado gasta la credibilidad del aviso que
sí importa.

---

### Qué corrigió v5.1.2: MAGI abría ventanas de navegador

Se reportó tres veces y se «arregló» dos, sin éxito. La causa estaba en un
sitio que ninguno de los dos arreglos miraba.

**La causa, con traza de ejecución capturada:**

```
g4f/Provider/Cloudflare.py:117   CDPSession(headless=False).start()
  -> g4f/requests/cdp.py:284     start()
  -> g4f/requests/cdp.py:233     subprocess.Popen([chrome.exe,
                                   --remote-debugging-port=56014])
                                 sin --headless  =>  ventana visible
```

`Cloudflare` declara `use_nodriver = False`, así que pasaba limpiamente el
filtro del primer arreglo. E importa `CDPSession` *dentro* del método, en
tiempo de llamada, así que tampoco tocaba ninguna de las funciones parcheadas
por el segundo. Y era justo el proveedor que respondía en todos los registros
del usuario: **cada respuesta correcta abría una ventana**. `DeepInfra` hace lo
mismo. Peor: `cdp.py` se engancha a un Chrome del usuario que ya esté abierto
con depuración remota, y le abre pestañas.

**La defensa ahora** (`magi/core/no_browser.py`, 4 capas):

1. CDP cortado: `find_chrome_path`, `find_running_cdp_port`,
   `get_shared_browser`, `CDPSession` y `SyncCDPSession`.
2. `nodriver`/`webview` con re-parcheo de las copias que los módulos de
   proveedor **ya habían importado por valor** — el motivo real de que el
   segundo arreglo no hiciera nada.
3. `webbrowser.open` neutralizado.
4. Interruptor sobre `subprocess.Popen`: ningún binario de navegador se
   ejecuta, venga de donde venga. Excluye `msedgewebview2.exe`, que es la
   propia interfaz de MAGI.

Se instala en la primera línea ejecutable de `main.py`, antes de importar
nada. **Verificado:** 44 proveedores probados contra la red real, 0 ventanas.

### El catálogo de proveedores, verificado uno a uno

El catálogo anterior se construyó filtrando por lo que g4f **dice** de sí
mismo (`working=True and needs_auth=False`). Al probar los 44 candidatos
contra la red real respondieron 11: HuggingSpace 890ms, Groq 922ms, Cohere
`command-a` 1078ms, CopilotApp 1156ms, Yqcloud 2000ms, WeWordle 2389ms,
Gemini `3.5-flash` 3421ms, Perplexity 7921ms y el auto-router.

El reparto del enjambre pasa de `deepseek`/`claude`/`qwen` —las tres **sin un
solo candidato vivo**, que es por lo que el kernel caía al clasificador por
defecto— a `gpt`/`gemini`/`command`: tres linajes verificados y realmente
distintos, que es lo que §1.1 pedía de verdad.

### Naoko: memoria eterna y autoconocimiento

Naoko no detectó el fallo del navegador ni una sola vez, por dos carencias
distintas:

- **No sabía qué debe ser verdad.** Vigilaba excepciones y métricas, o sea
  cosas que fallan ruidosamente. El fallo del navegador no fallaba: MAGI
  respondía bien y de paso abría Chrome. Ahora comprueba **invariantes**
  ejecutando una sonda por cada una, y una invariante rota se anuncia antes
  que cualquier otra cosa.
- **No recordaba nada.** Tenía los 5 errores más recientes de una base que se
  recrea. Ahora la memoria vive en `%LOCALAPPDATA%\MagiSystem\naoko\`, fuera
  del `.exe` —un onefile se extrae en un temporal que se borra al salir—, así
  que sobrevive al cierre y a recompilar el binario: identidad, invariantes,
  episodios y lecciones, en append-only. Y reconoce recurrencias: si un
  síntoma ya está en sus episodios, lo dice antes de diagnosticar.

---

### Qué corrigió v5.1.1 respecto a v5.1.0

v5.1.0 salió con su workflow roto y nunca generó ejecutable. Esta versión
cierra los tres bloqueos:

- **El CI no compilaba.** Los workflows instalaban una lista de paquetes
  escrita a mano a la que le faltaban `websockets`, `numpy`, `scikit-learn`
  y `pyyaml`. Como `build` depende de `test`, no se generaba el `.exe`.
  Ahora ambos workflows instalan desde `requirements.txt`.
- **El `.exe` relanzaba MAGI.** Dentro de un onefile de PyInstaller,
  `sys.executable` es el propio `.exe`, no un intérprete. Seis sitios que
  lanzaban Python relanzaban MAGI en su lugar. `magi.core.paths.python_executable()`
  resuelve un intérprete real o devuelve `None` en vez de hacer algo raro.
- **README reescrito.**

---

### El hallazgo que motivó todo

El «debate popperiano» de v5.0.28 era ficticio: los tres nodos llamaban a
`gpt-4o-mini`. Un modelo hablando solo, con tres nombres distintos. Ahora cada
nodo está anclado a una familia de modelo real y la interfaz muestra la familia
que **de verdad** respondió, no la que tenía asignada.

### Los agentes ahora actúan, no solo hablan

`run_agent` existía, tenía tests y solo lo usaba Naoko: los tres nodos del
enjambre no podían abrir un fichero. Melchior escribía planes para analizar
código sin poder leerlo y Balthasar «criticaba» sin poder ejecutar nada. Ya
están conectados, con **44 herramientas** repartidas por rol y acotadas por
dominio para que quepan en el prompt de un proveedor gratuito.

### Naoko: repara sola, mejora contigo

Dos vías separadas a propósito. **Reparar** devuelve el sistema a donde ya debía
estar, es verificable con tests y va sin consultar. **Mejorar** cambia hacia
dónde va el sistema, y ese criterio es del usuario: va con compuertas.

Naoko tiene ahora rol creativo de desarrollo. Cuando detecta un método más
eficiente o más rápido —citando fichero y línea—, el plan da **dos vueltas
completas** al enjambre antes de volver a ti: Melchior analiza y mejora,
Balthasar examina el plan *y lo de Melchior* con crítica popperiana, y Casper
evalúa las tres cosas por separado y añade temas nuevos. Solo entonces te llega
el plan hiperperfeccionado. Tus propias propuestas recorren lo mismo.

Publicar es siempre tuyo, aunque el cambio sea una reparación.

### Controles que decían funcionar y no funcionaban

- **La parada de emergencia no paraba nada.** El handler escribía una línea de
  log y devolvía `"EMERGENCY_STOP_TRIGGERED"`. Además el botón ni siquiera
  llegaba ahí: se enviaba como si fuera una petición del usuario, así que
  lanzaba un debate del enjambre sobre la cadena «KILL_ALL_PROCESSES». Ahora
  cancela de verdad, con `SIGTERM` antes que `SIGKILL`, e informa de lo que paró
  **realmente**, incluidos los procesos que no murieron y las tareas que no
  soltaron.
- **El visor de diffs recibía el original vacío** y pintaba todo en verde: no
  era un diff, era el texto nuevo con fondo de color. El estado de aprobación se
  deducía raspando el terminal en busca de una frase.
- **La contabilidad de tokens se calculaba y se tiraba.** El esquema existía,
  los métodos existían, y nadie los llamaba: la tabla llevaba vacía desde que se
  creó.
- **Un fallo en cualquier handler cerraba la conexión** con la interfaz.

### Lo que encontró la última revisión adversarial

Veinte fallos confirmados, cada uno reproducido antes de tocar nada. Los que
más importan:

- **Publicar podía etiquetar un commit que no existía.** `commit_files` devuelve
  un booleano y se traga el fallo; ese booleano se descartaba. Con un simple
  renombrado de fichero —`git status` lo reporta como `R viejo -> nuevo` y se
  tomaba entero como una ruta— el `git add` salía con código 128, el commit no
  se hacía, y aun así se etiquetaba **el commit anterior** y se empujaba. La
  release se construía sin la mejora dentro, marcada como publicada y sin
  salida posible.
- **La compuerta de publicación no tenía ni un solo test de comportamiento.**
  Los cinco que la custodiaban leían el código fuente buscando subcadenas.
  Cuatro mutantes que conservaban esas subcadenas y rompían la compuerta de
  verdad —uno de ellos hacía que la autocorrección empujara a GitHub sin
  permiso— dejaban la suite entera en verde. Ahora se ejecuta la función y se
  comprueba lo que hace: los cuatro mutantes mueren.
- **La verificación de una mejora vivía en el prompt.** La única comprobación
  de «no rompas los tests» era una frase pidiéndoselo al modelo. Ahora la suite
  se ejecuta en código, y un turno que no llamó a ninguna herramienta o que
  agotó el límite de iteraciones no pasa a publicación.
- **El botón de parada podía dejar una mejora atascada para siempre.**
  `CancelledError` no hereda de `Exception`, así que el manejador no la veía y
  la mejora quedaba en un estado de trabajo que no es compuerta: ni «sí» ni
  «no», y la única salida era editar la base de datos a mano.
- **Las notas de la release se generaban y no las leía nadie.** El workflow
  publica el cuerpo desde `RELEASE_NOTES.md` y ese fichero no lo escribía
  ningún sitio: cada versión nueva salía con las notas de la anterior.
- **La comparación entre países nunca ha funcionado.** La URL del Banco Mundial
  combinaba `per_page` con `mrnev`, y la API rechaza esa combinación con HTTP
  400 siempre. Los tests con datos congelados no podían verlo porque el fetcher
  de pruebas casa solo el dominio e ignora los parámetros.
- **EDGAR rotulaba como dólares lo que no lo era.** El filtro acepta el
  formulario `20-F` a propósito, que es justo el que presentan los emisores
  extranjeros en su moneda: euros y libras salían etiquetados «USD» y esa
  unidad viajaba a la cita.
- **Las llamadas de red congelaban el kernel entero.** Medido: 2,33 s de
  consulta a FRED y cero latidos de un heartbeat de 50 ms. Durante ese rato el
  websocket no responde y la petición de parada de emergencia ni siquiera se
  puede entregar.
- **La compilación del release se habría caído.** El job de tests instalaba una
  lista de paquetes escrita a mano que se había quedado atrás dos veces: sin
  `websockets` y sin `numpy`/`scikit-learn`. Y como el build declara
  `needs: test`, no habría habido `.exe`. Ahora se instala de
  `requirements.txt` y un test impide volver a enumerar.

### El fallo que solo existía en el .exe

Dentro de un onefile de PyInstaller, `sys.executable` **es el propio
ejecutable**, no un intérprete de Python. Media docena de sitios lanzaban
`sys.executable -m pytest ...` o `"{sys.executable}" "juego.py"`. En
desarrollo funciona, porque allí sí es python. En el `.exe` que se descarga de
Releases, cada una de esas llamadas **relanzaba MAGI**:

- `run_tests` y `python_exec`, las herramientas con las que el enjambre
  ejecuta código. Que Balthasar critique *habiendo ejecutado* es lo que le da
  autoridad, y en el binario no ejecutaba nada.
- La verificación ejecutable de propuestas (§2.5).
- `observe_program`, `observe_game` y `capture_program`: el bucle de
  observación acababa mirando a MAGI en lugar del artefacto recién generado.
- La suite que Naoko corre antes de publicar.

Ninguno daba error: daban el resultado de otro programa, que es peor. Ahora
todo pasa por `paths.python_executable()`, que busca un intérprete de verdad y
devuelve `None` si no lo hay —incluido el caso de un `python` en el PATH que
resuelva al propio binario—, para que el sistema diga que no puede en vez de
hacer algo raro en silencio. Comprobado construyendo un bundle real, con y sin
Python en la máquina.

Y el `.exe` se compila ahora con la misma versión de Node y el mismo `npm ci`
que usa CI para dejar el frontend en verde: antes eran Node 20 con
`npm install` frente a Node 22 con `npm ci`, dos diferencias con lo probado.

### «No he podido comprobarlo» no es «está bien»

La quinta regla del proyecto, y la más cara, porque el fallo se disfraza de
éxito. Sin Pillow, el observador de imágenes devolvía `ok` sobre una captura
que nunca llegó a abrir —y lo mismo el de juegos y el de vídeo—; sin pypdf, un
PDF de páginas en blanco salía aprobado; un `.parquet` que nadie sabía leer se
resumía como «1 registros». En todos los casos el aviso existía, enterrado en
la evidencia, que no entra en el veredicto. Ahora, cuando el sistema no puede
mirar, lo dice entre los problemas y el veredicto es negativo.

### Capacidades nuevas

- **Ingeniería inversa y emuladores:** Capstone, Unicorn, prueba diferencial,
  matriz de portabilidad entre consolas, indexado del código real de un emulador
  y **entropía de Shannon** para distinguir un binario cifrado de código roto.
- **Fábrica de artefactos que se mira a sí misma:** juegos, programas,
  documentos, imágenes, **vídeo** (detecta el vídeo en negro y el congelado) y
  **datos** (detecta el CSV con cabecera y cero filas).
- **Vídeo programático** con FFmpeg: animática Ken Burns y manga → vídeo.
- **Manga:** composición con orden de lectura derecha-a-izquierda y validación
  de solapes antes de gastar generaciones.
- **Mundo real:** macro y geopolítica desde FRED, BCE y Banco Mundial;
  fundamentales desde SEC EDGAR; aritmética financiera determinista que muestra
  su fórmula; y un registro de tesis con calibración medible por regla de Brier.
  Todas las fuentes gratuitas y **sin clave de API**.

### Interfaz

Paleta de comandos con **Ctrl+K**, panel de coste, panel de sistema (salud,
banco de evaluación, auto-mejora), panel de mejoras, y historiales acotados
—el terminal crecía sin límite y se recorría entero dos veces por repintado—.

### Reversibilidad

Antes de tocar un fichero se copia. `undo` lo devuelve, por operación o por
tarea entera. No añade permisos: añade reversibilidad. Y esa misma copia es la
que alimenta el panel de aprobación.

---

**Requisitos opcionales**, detectados si están: `capstone` y `unicorn`,
`pygame` y `pillow`, `ffmpeg`, y ComfyUI en `127.0.0.1:8188`. Sin ellos el
sistema funciona y avisa de lo que no puede hacer, en vez de fingir.
