# v5.7.1 — lo que encontró el CI en la v5.7.0

Tres fallos que la suite local no vio y el CI sí, porque **el CI corre en
Linux y la máquina de desarrollo es Windows**. Los tres eran míos y los tres
son la misma lección: una prueba que solo se ejecuta donde se escribió
comprueba menos de lo que parece.

**La detección de artefactos asumía Windows.** El reconocimiento de los
ejecutables que construye el agente (D10) buscaba rutas con letra de unidad
(`C:\…`). En Ubuntu, la ruta temporal de pytest empieza por `/tmp/`, así que no
encontraba nada y los dos tests de D10 caían. El producto es de Windows; el
código no tiene por qué serlo, y una expresión regular que da por supuesto el
sistema operativo falla en cuanto alguien la ejecuta en otro. Ahora acepta las
dos formas.

**La verificación había dejado de ser paralela.** Al hacer que los bloques de
Python se verifiquen unidos (B1), la primera versión probaba el conjunto y solo
después caía a los bloques sueltos: correcto en el resultado y **el doble de
lento**. `test_blocks_are_verified_in_parallel` —cinco bloques con 0,4 s de
pausa— pasó de 0,8 a 2,0 segundos y lo cazó el CI. Ahora se lanza todo a la vez
y manda el veredicto del conjunto cuando pasa: se conserva lo que B1 buscaba y
el tiempo de pared vuelve a ser el del bloque más lento.

Un arreglo que arregla una cosa y estropea otra sin que nadie lo mida es medio
arreglo.

---

# v5.7.0 — el lazo se cierra: de proponer un .exe a entregarlo

La v5.6.0 consiguió que el sistema dejara de mentir. Esta consigue que
**entregue**. Y está verificado contra el sistema real, no contra tests:

```
[FÁBRICA] Construyendo «ping» desde la propuesta verificada...
[fábrica] ping.exe entregado en Escritorio: C:\Users\D\Desktop\ping.exe
          (14370685 bytes, sha256 03d515a99b72fd2e…)
```

El fichero existe, arranca y sale con código 0. Comprobado a mano después.

| Métrica | v5.5.2 | v5.6.0 | **v5.7.0** |
|---|---|---|---|
| Ratio entregado/producido | 0,8 % | 12-25 % | **49,9 %** |
| Artefacto en encargo de producto | no | no (avisado) | **sí, en el Escritorio con hash** |
| `APPROVED` sobre un turno degradado | 3/3 | 0/2 | **0** |

## Lo que cambia

**El modelo propone; la máquina construye (D3).** En cinco pruebas medidas, el
sistema escribió hasta ocho bloques de código para encargos de `.exe` y llamó
**cero veces** a la cadena de fábrica que tenía escrita. Se le pidió en el
prompt, con ejemplo, y el contador siguió en cero. Ahora lo hace el
orquestador: si el encargo pide un fichero y hay código verificado, se
construye y se entrega, sin depender de que nadie se acuerde.

**Si el agente ya lo construyó, se reconoce — y se comprueba (D10).** El fallo
más irónico de la serie: Melchior fabricó dos ejecutables de verdad (tkinter,
9 MB, con `--formato` y `--autotest`) y el sistema los ignoró, intentó
construir otro desde bloques inexistentes y cerró la tarea como `INCOMPLETO`.
El trabajo estaba hecho y el propio sistema decía que no. Ahora las rutas que
aparecen en la propuesta **se comprueban contra el disco**: una ruta que existe
es evidencia; una que no, es prosa.

**El encargo se lee como contrato (D1).** «Un ping pong de 32 bits a todo color
en un exe portable» son cuatro promesas comprobables, no un tema. Se enseñan al
empezar, con cómo se va a comprobar cada una, y viajan al prompt.

**Ninguna parte del enunciado se pierde en silencio (D5).** La prueba anterior
pedía «el orden de trabajo que minimiza el riesgo de abandono» y la respuesta
—buena en todo lo demás— no mencionó el abandono ni una vez. Ahora lo que no se
conteste sale dicho: `[SIN CONTESTAR] El encargo pedía esto y no lo veo…`.

**`APPROVED` no sobrevive a un contrato incumplido (D2).** Antes convivían
«Decisión Técnica: APPROVED» y «[INCOMPLETO] no se ha generado ningún
artefacto» en el mismo mensaje. Dos mecanismos que no se hablan dejan al
usuario eligiendo a cuál creer.

**Un bloque de Python sin etiqueta sigue siendo Python.** De 18 bloques que
escribió el modelo, 11 venían sin etiquetar: el verificador no los ejecutaba y
la fábrica decía «no hay código Python» teniendo diez delante.

**Se ejecutan las herramientas propias en vez de pedirlas (D4).** Ante una
pregunta de portabilidad entre consolas, el sistema tenía `analyze_port`
escrito para exactamente eso y lo usó cero veces en cinco pruebas. Ahora el
orquestador lo ejecuta y pone el resultado en el prompt como evidencia ya
obtenida.

**Dos enfoques en vez de tres o cuatro (D6).** Medido: tres enfoques, 27.753
caracteres producidos, 24,7 % entregado y ningún artefacto. La calidad no salía
de tener tres textos. La cuota liberada se gasta en verificar y construir.

**Y Ritsuko ve lo que importa (D7).** Su evidencia incluye ahora las métricas
de entrega, y su prompt tiene una regla nueva: con un incumplimiento delante,
el veredicto no puede ser «sin datos suficientes».

## De dónde sale este plan

De hacer ingeniería inversa a un procedimiento externo y aplicarlo aquí: leer
el encargo como contrato, decidir qué significa «hecho» antes de empezar y
hacerlo comprobable por máquina, buscar en la propia caja de herramientas antes
de razonar de memoria, y desconfiar del propio informe de éxito. Está escrito
entero en `docs/MEGAPLAN-v7-ingenieria-inversa.md`, con las diferencias
observables y la evidencia de cada una.

---

# v5.6.0 — el sistema deja de firmar lo que no ha leído

Esta versión sale de tres pruebas contra el sistema real, contrastadas con lo
que entregaría un modelo externo: una pregunta compleja (dynarec PSP→Vita), un
Tetris en `.exe` portable y un ping pong a color de 16 bits. Las tres
terminaron igual, y el resultado es el motivo de todo lo que hay aquí.

## Lo que pasaba

El usuario recibía esto, tres veces de tres:

```
**Decisión Técnica:** APPROVED

[Tiempo de espera agotado tras 150s en iteración 1. Proveedor: g4f-gpt...]
```

252 caracteres. Un aviso de error firmado como aprobado, con **33.000
caracteres de tesis y crítica ya producidos y pagados** que nadie llegó a ver.
Y en el encargo del ping pong, un escalón peor: cero bloques de código, cero
artefactos, y el árbitro escribiendo «se compiló exitosamente el binario
ejecutable único portable». El informe parecía perfecto. El fichero no existía.

Lo demás son consecuencias de lo mismo: nada distinguía una respuesta de un
mensaje de error.

## Lo que cambia

**El árbitro no firma lo que no ha leído.** Un turno degradado —timeout,
proveedor caído, respuesta vacía— produce `SIN_ARBITRAJE`, nunca `APPROVED`. Y
entonces se entrega la tesis y la crítica con una cabecera honesta, en vez de
tirar el trabajo: *«No apruebo lo que no he leído, así que te entrego lo que sí
está hecho»*.

**Un fallo que viene como texto sigue siendo un fallo.** El sistema tenía dos
formas de devolver un error disfrazado de respuesta normal —`[Inferencia no
disponible...]` con proveedor `SYSTEM_ERROR`, y `[Tiempo de espera agotado...]`
del bucle de herramientas—, y ningún consumidor miraba la marca. Ahora hay una
sola función que lo decide, usada en los tres sitios que importan.

**Si pediste un `.exe`, un texto sobre el `.exe` sale marcado.** El sistema
reconoce cuándo el encargo espera un fichero y exige tres cosas para cerrarlo:
código, verificación que lo ejecute y artefacto entregado. Si falta alguna, la
entrega sale como `[INCOMPLETO]` diciendo qué falta. Y una síntesis que afirme
haber compilado algo se contrasta contra el registro de la tarea: si no consta
artefacto, sale el aviso.

**Verificar cero bloques ya no es verificar.** `all([])` es `True`, así que una
propuesta sin una línea de código pasaba la verificación con nota — medido:
tres pasadas en **0,0 s** dando el vacío por bueno.

**Los bloques de Python se verifican unidos.** El modelo pone la función en un
bloque y su test en otro; ejecutarlos por separado daba `ModuleNotFoundError` y
forzaba un ciclo de reconstrucción entero (~4 llamadas, 60-80 s) por un fallo
que no era del modelo.

**Medir deja de envenenar lo medido.** Naoko declaró cuatro veces «deriva
detectada» durante una tarea que estaba haciendo 50 llamadas contra esos mismos
proveedores: medía su propia interferencia. Ahora la sonda espera a que el
enjambre esté quieto, y un canario que no contesta es *no concluyente*, no
deriva.

**Velocidad.** El hedge llega por fin a la puerta de las herramientas —las 14
llamadas más lentas del sistema iban sin cubrir—, el motor `fast` usa 4
iteraciones en vez de 10, y el timeout por iteración sale del presupuesto
restante en vez de una constante de 150 s que se comía turnos enteros.

**Y una tarea reanudada sin rondas ya no se queda muda.** Antes decía
«reanudando debate» y no volvía a hablar nunca.

## Ritsuko, la quinta IA

Naoko corrige al enjambre y hasta ahora nadie la comprobaba a ella. Ritsuko
audita esa relación: mira la evidencia del bus, dice si el sistema mejora o
empeora, señala si un nodo se ha quedado mudo, y deja cada informe escrito en
disco para descargar. **Solo informa** —no escribe código, no ejecuta nada, no
toca configuración— porque un auditor con permiso para arreglar acaba
revisándose a sí mismo. Usa una familia de modelo que no comparte con ninguna
de las otras cuatro, con un test que lo impide. Habla español o inglés, nunca
otro idioma. Tiene su propia pestaña, separada de la de Naoko.

## Además

`scripts/auditar_sistema.py`: arranca el kernel de verdad, lanza una petición
real y cronometra las dos puertas al modelo. Es lo que produjo todos los
números de arriba, y lo que permite comprobar si la próxima versión mejora.

Detalle completo en `docs/MEGAPLAN-ESTADO.md`, incluidos los cuatro bloques que
se quedan fuera y por qué.

---

# v5.5.2 — la fábrica entrega de verdad, y el enjambre deja de quemar cuota

Cuatro frentes, todos con medida detrás. Dos de ellos eran fallos que **no
daban error**: el sistema decía haber hecho el trabajo y el trabajo no estaba.

## La fábrica devolvía un archivo que ya no existía

`build_project_exe(clean=True)` borraba `work_base` —el build entero— en su
`finally`, y devolvía `PackagerResult(ok=True)` con un `exe_path` apuntando a
un fichero ya eliminado. Quien llamara sin `output_exe` recibía un éxito
vacío: esa es la causa de las llamadas quemadas construyendo binarios que se
evaporaban. Ahora el .exe se rescata a `data_dir()/entregas-built` antes de
purgar, así que ningún llamante vuelve a recibir una ruta muerta.

Encima de eso, `fabricar_y_entregar()` (`magi/modules/studio/entrega.py`):
une los bloques Python, los verifica con el guardián GUI real (Tetris, 30
frames, rc=0), empaqueta y deja el .exe en el Escritorio real
—`SHGetKnownFolderPath`, OneDrive incluido— con su SHA-256, respaldo en
`artifacts/entregas` y evento `swarm.artefacto_listo`, sin pisar entregas
previas. Verificado de extremo a extremo: 14,3 MB con hash en el Escritorio.
Preflight antes de empezar: intérprete, nombre sano y 250 MB libres.

## Una sola petición quemaba ~50 llamadas

Medido el 16-ago: «crea un juego de tetris en un único ejecutable exe
portable» gastó 18 llamadas gpt + 14 gemini + 18 command, casi todas a 8-9 s.
Sin techo, el bucle de re-verificación de Melchior regeneraba las tres
variantes enteras una y otra vez, y el hedge multiplicaba por tres cada
llamada lógica.

`magi/core/presupuesto.py` pone tres frenos por tarea —llamadas lógicas,
tiempo de pared y número de regeneraciones— configurables desde
`factory.yaml` sin tocar código. Con `rebuilds: 2`, la mejor variante se
debate igual y se dice claramente que no verificó, en vez de reintentar seis
veces en silencio.

## Velocidad: fan-out por motor, techo por latencia, cortesía de tasa

El hedge deja de ser global y pasa a repartirse por motor, con un techo de
latencia por candidato y una cortesía de tasa que evita el 429 en cadena.

## Resiliencia del orquestador (B3–B6)

- **Carreras**: las decisiones de enrutamiento van bajo `asyncio.Lock`; dos
  peticiones interactivas simultáneas ya no pueden corromper el estado.
- **Aprobación**: se probó a aparcar el bucle en un `asyncio.Event` en vez de
  cortarlo con `break`, y se revirtió antes de publicar. Costaba dos cosas y
  no aportaba ninguna: la tarea no terminaba nunca —lo que colgaba la suite
  entera en el desmontaje, sin fallo ni traza que señalara aquí— y, al
  responder con objeciones, `_spawn_loop` arrancaba un segundo debate sobre
  la misma tarea mientras el aparcado despertaba: gasto duplicado de cuota,
  justo lo que esta versión venía a frenar. Quien reanuda sigue siendo
  `_spawn_loop`, que ya se llama en los tres caminos de vuelta.
- **Parada-Cubre-Hedge**: `magi/core/circuit_breaker.py` aplica timeout duro
  a cada herramienta y, si cuelga o revienta, revierte al último snapshot del
  journal y devuelve un error estructurado para que el LLM busque otra ruta.
- **Auto-ejecución idempotente**: las herramientas de la fábrica trabajan
  dentro de un `TemporaryDirectory`; los ficheros a medio cocer no asoman al
  disco real, y solo con `ok=True` el bloque se extrae al `out_path`.

## La sonda ya no espera a que le pregunten

`_refrescar_sonda()` pasa a ser tarea periódica en segundo plano con freno
propio: la latencia histórica se recolecta sola, sin bloquear el arranque, y
el reparto por mérito del registro trabaja con datos frescos.

## Familia gpt: viva otra vez

Yqcloud responde en chino cuando le apetece, y eso fue la causa raíz de las
respuestas del enjambre en otro idioma. Ahora se le inyecta la orden de
sistema a nivel de API antes de cada llamada (~2,7 s medidos, castellano).
WeWordle vuelve a los candidatos: su descarte por 429 sobra desde que el
circuit breaker y el hedge gestionan la cuota.

Barrido completo de los 37 proveedores `working` sin login: sobreviven
Yqcloud y WeWordle (y PollinationsImage para imagen). El resto son timeouts,
402/403 o directamente no existen. Se dice entero en vez de prometer magia.

## Además

El job `lint` del CI no instalaba las dependencias que pyright importa, así
que analizaba un árbol incompleto. Corregido.

---

# v5.5.1 — corregido: medir la salud no puede enfermar al sistema

**Corrección de la v5.5.0.** Al despertar la sonda de latencia por primera
vez, el sistema se quedaba sin proveedores a los pocos minutos de uso.

## Qué pasaba

Los canarios piden respuestas cortas **por diseño** («51», «paris», «ok»).
El filtro antichatarra del tráfico real (`MINIMO_UTIL = 12` caracteres,
creado para cazar respuestas truncas como `'tud.'`) las rechazaba todas.
Cada rechazo agotaba la familia, abría el cortacircuitos, y el siguiente
chequeo de salud atacaba a otras familias: cascada total. Cuando llegaba
tu tarea real, no quedaba nadie sano. La sonda llevaba muerta desde que
nació, así que estas dos piezas jamás habían coincidido en ejecución —
la v5.5.0 las despertó juntas y el choque apareció en tu máquina.

## Qué cambia

- **El tráfico de sonda se marca como tal** (`probe=True` en la petición)
  y se juzga con su propia regla: cualquier respuesta no vacía cuenta.
- **Un fallo de sonda ya no castiga al cortacircuitos** ni a las métricas:
  «este candidato está caído ahora mismo» es un dato, no una penalización.
- **Las sondas no usan la caché** del tráfico real: el '51' de un canario
  nunca podrá servir de respuesta a una tarea.
- Cinco tests de regresión nuevos (`test_sonda_no_envenena.py`) fijan las
  tres reglas para que no vuelva a pasar.

---

# v5.5.0 — la sonda despierta y el sistema se audita a sí mismo

Esta versión nace de auditar el propio MAGI con su propio método: medir antes
de suponer. Lo que apareció fueron cuatro bugs reales que ningún test veía,
y cada uno con su vacuna para no volver.

## La sonda de latencia llevaba muerta desde que se escribió

`kernel.py` importaba `get_registry` del módulo equivocado. El `except` que
protegía el arranque se tragaba el ImportError y la sonda —la tarea que mide
la latencia real de cada proveedor y reparte el enjambre por mérito— **no se
ejecutaba nunca**. El reparto obedecía al catálogo escrito a mano desde el
primer día. Ahora corre en cada arranque, y un test nuevo
(`test_sonda_viva.py`) comprueba que cada import de la sonda resuelve de
verdad: no puede volver a morir en silencio.

## El panel de configuración enseña la salud, no solo el estado

- **Salud por día**: chispa con la latencia diaria (14 días) de cada
  candidato y su tendencia (mejora / empeora). La media histórica de 30 días
  esconde que un proveedor pasó de 3 s a 9 s esta semana; la pendiente no.
- **Por qué faltan proveedores**: los que exigen tu cuenta o abren navegador
  («no van a volver») separados de los caídos («HTTP 429, puede volver»),
  cada uno con su motivo medido. Antes todo era un «sin verificar» que
  sonaba a trabajo pendiente que nadie haría.

## Integridad verificable de la descarga

Cada release publica **`CHECKSUMS.txt`** con el SHA256 del `.zip` y del
`.exe` interno. El binario sigue sin firma (SmartScreen avisará: *Más
información → Ejecutar de todas formas*), pero la integridad ya se puede
comprobar: `certutil -hashfile MAGI-IDE-v5.zip SHA256`.

## Dependencias sin vulnerabilidades conocidas

`requests` 2.31.0 → 2.33.0 y `scikit-learn` 1.4.1 → 1.5.0 (4 CVE, ambos
pineados a mano); `dompurify` corregido en la interfaz vía override. La
auditoría (`pip-audit` + `npm audit`) es ahora bloqueante en el CI: si sale
un CVE nuevo, el pin sube en el mismo commit o no hay release.

## Más rápido y más limpio

- La suite de tests corre en paralelo (`pytest-xdist`): de ~7 min a ~2,5 min
  en local, también en el CI.
- Lint a cero en errores reales (1 527 → 0) y tipado estricto en `magi/core`
  (26 → 0), ambos bloqueantes. El tipado destapó dos de los cuatro bugs.
- Seis paquetes de andamiaje sin un solo importador (`device`,
  `fabrication`, `vision`, `reasoning`, `os_portable`, `capabilities`)
  archivados en `_attic` como mapa de lo probado. Huérfanos: 94 → 70.
- Traducciones con caché LRU: mismas entradas, cero llamadas repetidas —
  la cuota gratuita se queda donde debe estar.

## Los otros dos bugs corregidos

- La lista de tareas de la interfaz fallaba **en silencio** desde siempre:
  `t.nombre()` llamaba a una property. El `try/except` lo escondía y la
  columna salía vacía tras cada reinicio.
- `SecurityPolicyError` se lanzaba al detectar la pasarela expuesta… y nadie
  la capturaba. Ahora `adapter.py` la atrapa y reporta `BLOCKED`.

---

Suite completa en verde, incluidos los tests que compilan el `.exe`:
**1255 pruebas en Python y 122 en la interfaz**, verificadas en local antes
de etiquetar. Sin tests verdes no hay release.

## Cómo instalarlo

1. Descarga **`MAGI-IDE-v5.zip`** de la sección **Assets**, aquí abajo.
2. Verifica (opcional): `certutil -hashfile MAGI-IDE-v5.zip SHA256` contra
   `CHECKSUMS.txt`.
3. Descomprímelo donde quieras — no hay instalador ni carpetas obligatorias.
4. Ejecuta **`MAGI-IDE-v5.exe`**.

Windows SmartScreen avisará porque el binario no está firmado: *Más
información → Ejecutar de todas formas*. El `.zip` lo compila GitHub Actions
desde este mismo tag, tras pasar la suite completa; no hay ninguna subida
manual de por medio.

No hace falta configurar nada: **sin claves de API, sin modelos locales, sin
suscripciones**.

---

# v5.4.0 — los proveedores, medidos en vez de supuestos

Esta versión sale de auditar el sistema con mediciones en lugar de con
suposiciones. Lo que apareció fue incómodo y está corregido.

## La familia `claude` nunca necesitó cookies

Figuraba como imposible («exige cookies de un navegador») y de ahí salió medio
módulo de sesión web. Resultó que `Perplexity` —ya en el catálogo, sin cuenta y
sin claves— sirve `claude45sonnet` y `claude40opus`. Lo bloqueaba un fallo de
g4f de dos líneas, ahora parcheado en `providers/compat_g4f.py`.

*Antes de construir infraestructura para saltar un muro, conviene comprobar que
el muro existe.*

## Cuatro idiomas de entrada, uno de salida

Los proveedores pueden responder en **español, inglés, portugués o italiano**;
**el chino, nunca**. Todo lo que llega a la interfaz va traducido al español,
**incluida Naoko sin excepción**.

No es una concesión, es más barato: antes una respuesta en inglés se trataba
como fallo y disparaba una regeneración completa en otra familia. Ahora se
traduce con una llamada corta y las conclusiones no cambian.

Y la causa raíz del problema del idioma no era el prompt: la familia de
MELCHIOR tenía un único candidato vivo, y respondía en chino.

## Un fallo que se disfrazaba de éxito

Un proveedor empezó a devolver cuatro caracteres —`'tud.'`— para cualquier
pregunta. MAGI lo daba por bueno: habría aparecido en la interfaz como la
antítesis de BALTHASAR, con su latencia y su nombre de proveedor. Ahora se
rechaza y se prueba el siguiente candidato.

## El catálogo ya no se cree a sí mismo

Cinco familias marcadas «verificadas» estaban rotas al medirlas, y dos de ellas
se cayeron **en las ocho horas** que separaron dos mediciones del mismo día. Esa
es la vida útil real de una lista escrita a mano.

Por eso la sonda de latencia —que llevaba semanas construida y **sin que nadie
la llamara**— ahora dispara sola una vez al día, con freno para no gastar
cuota, y el reparto del enjambre obedece a la media histórica medida en lugar
de a una prioridad escrita a mano.

## Naoko ve el suelo que pisa

Antes podía decir «MELCHIOR va lento». Ahora sabe cuántos candidatos vivos tiene
cada familia y avisa cuando alguna se queda con uno solo — que es la diferencia
entre arreglarlo el martes y descubrirlo el viernes con el enjambre parado.

## El gráfico dice si el debate es un debate

Mide si BALTHASAR aporta algo distinto de MELCHIOR y si cada ronda cambia algo
respecto de la anterior. Solo avisa cuando hay un problema: un cartel permanente
de «todo va bien» se deja de leer a la tercera vez.

## Camoufox, verificado sin ventanas

Arranca headless en 9,9 s, la lista de ventanas del sistema es **idéntica antes
y después**, y no deja procesos. La regla se mantiene: la única ventana es la
interfaz de MAGI.

## Y un fallo que habría llegado hasta aquí

`requirements.txt` clavaba `curl_cffi==0.5.10`. Al construir un entorno limpio
desde el fichero de versiones bloqueadas —lo mismo que hace la compilación—
Perplexity ni siquiera conectaba: *impersonate chrome is not supported*. **El
binario habría llevado la familia `claude` muerta** y en la máquina de
desarrollo nadie lo habría notado, porque allí hay una versión más nueva
instalada.

*Un pin que nadie usa no protege: engaña.*

---

# v5.3.2 — README reescrito, mismo binario

Reescritura completa del README para reflejar el enjambre dialéctico
(tesis/antítesis/síntesis), Naoko eligiendo el estilo, los dos motores y la
columna izquierda con títulos IA + archivar/borrar. Misma funcionalidad que
v5.3.1; este release corrige el README del release anterior, que se publicó
antes de la reescritura.

---

# v5.3.1 — el enjambre dialéctico, Naoko elige el estilo, y la columna izquierda vive

Una reconstrucción del enjambre y la interfaz a partir de cómo se usa el sistema
de verdad. Menos mandos, más sentido.

### 1. Dos motores, sin selector de estilo

La barra superior tenía dos selectores: MOTOR (2 opciones) y ESTILO (4 opciones).
El ESTILO desaparece de la interfaz. El MOTOR se simplifica a dos:

- **🔍 Análisis profundo** (por defecto): baja temperatura, más iteraciones.
- **⚡ Súper rapidez**: temperatura normal, menos vueltas.

### 2. Naoko decide el estilo

¿Quién decide si tu pregunta merece una respuesta técnica, sintética, creativa o
analítica? **Naoko**, no tú. Clasifica tu comando y propaga ese estilo a los tres
agentes. Es la que mejor entiende qué tipo de respuesta conviene a lo que
preguntaste. Ya no hay que elegir a mano antes de cada pregunta.

### 3. El enjambre aplica el método dialéctico

Los tres nodos tienen roles claros y lo saben:

- **MELCHIOR** es la **TESIS**: construye y defiende la solución.
- **BALTHASAR** es la **ANTÍTESIS**: refuta con evidencia (ejecuta el código).
- **CASPER (Gaspar)** es la **SÍNTESIS**: integra ambas en la respuesta
  definitiva que le habla al usuario. Es el nodo más activo.

Por defecto **una sola ronda** (tesis → antítesis → síntesis). Si no estás de
acuerdo, escribes tu feedback y una **segunda ronda arranca en Melchior** con la
síntesis previa de Casper + tus observaciones.

### 4. Conclusiones siempre en español

El cuerpo de las respuestas puede ir en inglés (los proveedores gratuitos tienen
sus sesgos), pero las **`### CONCLUSIÓN` van siempre en español**. Casper, que
es quien le habla al usuario, responde entero en español.

### 5. La columna izquierda vive

- **Títulos generados por IA**: la columna ya no muestra `task_a3f9c2b1`; Naoko
  resume tu pregunta en un título corto («Juego Tetris portable»).
- **Archivar (📦)** y **borrar (🗑)** cada conversación, con confirmación inline.
- **Persistencia**: al reconectar, la lista de tareas se repuebla desde el store
  con sus títulos. Ya no se pierde tras reiniciar.

### Detalles

- Suite completa en verde (Linux y Windows).
- Naoko conoce el enjambre y sus roles; te puede explicar qué hace cada nodo.
- No se toca el reparto de familias, la verificación ejecutable ni el flujo de
  aprobación.

---

# v5.3.0 — MAGI empaqueta proyectos Python a .exe portable

### 1. Nueva herramienta `build_project_exe`

`magi/core/tools/builtin.py` registra `build_project_exe`, que convierte
cualquier proyecto Python en un ejecutable `.exe` onefile portable:

- Lee `requirements.txt` si existe e instala dependencias en un venv temporal.
- Detecta automáticamente si el punto de entrada es una GUI (pygame, tkinter,
  turtle, PyQt/PySide) y elige `--noconsole` o `--console`.
- Usa un intérprete Python real, ya sea el del sistema o el embebido que
  ahora viaja dentro del bundle.
- Soporta assets, iconos y hidden imports.

Código en `magi/modules/studio/packager.py`.

### 2. Python embebido dentro del bundle

`magi/core/embedded_python.py` gestiona un intérprete Python 3.10 portable
que el `.exe` de MAGI extrae a `%LOCALAPPDATA%\MagiSystem\embedded-python`
la primera vez que hace falta. Esto cierra el agujero histórico por el que
`sys.executable` dentro del bundle era el propio MAGI y relanzar Python
real ejecutaba otra instancia del IDE.

`magi/core/paths.py::python_executable()` ahora devuelve, en orden:
1. el intérprete real del sistema (si no estamos congelados),
2. `python` / `py` del PATH (cuando estamos congelados),
3. el intérprete embebido del bundle.

### 3. Prompts para tareas `.exe`

- **Melchior**: si el usuario pide un `.exe` portable, debe crear el proyecto
  en `workspace/` y luego invocar `build_project_exe`.
- **Balthasar**: si la propuesta genera un juego, GUI, vídeo, imagen o
  artefacto ejecutable, debe usar `observe_artifact`/`record_program` y citar
  lo que SE VE en su crítica.
- **Casper**: no aprueba un `.exe`/juego/artefacto visual sin exigir y citar
  el resultado de la observación.

### 4. UX: timeout y lentitud visibles en terminal

Los eventos `agent.timeout` y `agent.slow_iteration` ahora se convierten en
mensajes `TERMINAL_OUT` automáticamente, así el usuario ve cuándo un proveedor
está atascado en lugar de mirar una pantalla quieta.

### 5. Estabilidad: timeouts controlados en `agent_loop.py`

`run_agent` ahora acepta `iteration_timeout_s` y `soft_timeout_s`. Si una
llamada al LLM se alarga, el agente devuelve una respuesta degradada en lugar
de quedarse colgado, y emite eventos `agent.timeout` / `agent.slow_iteration`
para que la interfaz pueda mostrar el retraso.

### 6. Velocidad: proveedores ordenados por latencia observada

`ProviderRegistry._candidates()` ahora ordena, tras el proveedor preferido,
por estado del circuit breaker y por latencia **p95** real. Los proveedores
lentos van al final sin perder la prioridad estática.

### Tests

- `tests/test_packager.py`: empaquetado de proyectos Python.
- `tests/test_embedded_python.py`: extracción y uso del intérprete embebido.
- `tests/test_agent_loop_timeout.py`: timeout y respuesta degradada.
- `tests/test_provider_latency_sort.py`: ordenación por latencia p95.
- `tests/test_e2e_tetris_exe.py`: flujo completo Tetris pygame -> `.exe`
  portable onefile que arranca y ejecuta sin Python de desarrollo.

---

# v5.2.2 — las tres IA vuelven a hablar tu idioma, y el Tetris arranca

Tres fallos confirmados a partir de la captura y el log de un usuario real:
un «crear un juego tetris» que se quedó dando vueltas en la Ronda 5 sin
avanzar, con las tres IA respondiendo en inglés y `Yqcloud/gpt-4` tardando
entre 53 y 75 segundos por respuesta.

### 1. La guarda de idioma se libraba en las respuestas cortas

El módulo de idioma tenía, en su última línea, `return len(respuesta.split())
< 12`: **cualquier respuesta de menos de doce palabras se daba por buena, en
el idioma que fuera**. Una frase como *«Sure! I will create a Tetris game for
you.»* pasaba por español válida, así que la guarda que debería rotar de
familia nunca lo hacía. El usuario veía a los tres nodos contestarle en otro
idioma con la guarda «arreglada».

Ahora se exige señal real del idioma esperado —mínimo dos palabras vacías—,
por corta que sea la respuesta. Un tecnicismo inglés aislado dentro de texto
español sigue siendo válido; un bloque de código sin idioma también.

### 2. La verificación no colgaba con un juego

`ProposalVerifier` ejecuta cada bloque de código antes de debatirlo. Un Tetris
pygame entra en un `mainloop` que **nunca termina**: colgaba 45 s y salía como
`FALLA — timeout`, así que el orquestador devolvía la propuesta a Melchior una
y otra vez sin gastar ronda. Código correcto rechazado en bucle.

Ahora se detectan los bloques con interfaz gráfica (pygame, tkinter, turtle,
arcade, mainloop) y se ejecutan **headless**: se inyecta un guardián que
cuenta fotogramas y sale limpio tras unos pocos. Un juego que arranca da
`OK — run-headless`; un `while True: pass` puro sigue dando `FALLA` por timeout
(no se enmascara un bug real). Reutiliza el patrón del `PYGAME_HARNESS` del
estudio de artefactos.

### 3. La familia gpt ya no espera al más lento

`Yqcloud/gpt-4` declaraba 2000 ms pero respondía en 53–75 s en uso sostenido,
arrastrando cada etapa de Melchior aunque hubiera alternativas de 1–2 s en la
misma familia. El catálogo se ha reordenado para poner primero a los
candidatos rápidos verificados (`CopilotApp` ~1,1 s, `WeWordle` ~2,4 s), y la
cobertura paralela (`hedge`) sube de 2 a 3, para que un rápido pueda ganar la
carrera mientras el lento sigue su curso. Todo sigue siendo gratuito y sin
claves.

### Detalles

- **865 tests** en la suite (Linux y Windows), 0 fallos.
- No se toca la orquestación, el libro de admisión, el flujo de aprobación ni
  los prompts de los agentes.
- No se añaden dependencias: pygame ya era opcional.

---

# v5.3.0 — el binario trae su propio Python, y ahora fabrica ejecutables

La versión más grande desde la reconstrucción. Tres capacidades nuevas y el
arreglo de lo que impedía usarlas.

### El `.exe` ya no depende de que tengas Python instalado

Dentro de un empaquetado onefile, `sys.executable` **es el propio `.exe`**. Eso
significaba que en el binario descargado no había ningún intérprete con el que
ejecutar nada: `run_tests`, `python_exec`, la verificación de propuestas y el
bucle de observación se quedaban sin trabajar. Lo decían —no fingían— pero media
capacidad del sistema estaba fuera de alcance si no tenías Python aparte.

Ahora viaja un **Python 3.10 embebido** dentro del binario. El orden de búsqueda
es: Python del sistema, lanzador `py`, y el embebido. Si no hay ninguno, se dice;
nunca se intenta a medias.

### Fabrica ejecutables portables de lo que genera

`build_project_exe` empaqueta un proyecto Python en un **`.exe` onefile** que
corre en una máquina sin Python. Es el último escalón de la fábrica: el sistema
no solo genera el juego y lo mira funcionar, también te lo deja en un fichero
que puedes pasarle a alguien.

Es la misma receta con la que se compila MAGI, aplicada a lo que MAGI produce.

### Un juego correcto ya no se declara colgado

Verificar código que abre una ventana tiene una trampa: **un juego correcto no
termina nunca**. Se queda en su bucle esperando a que juegues, y una
verificación con temporizador lo mata y lo declara roto.

Eso hacía que pedir un Tetris se quedara dando vueltas en la ronda 5: el juego
estaba bien, la comprobación lo mataba a los 45 segundos y el enjambre volvía a
proponer otro, indefinidamente.

Ahora los bloques con `pygame`, `tkinter`, `turtle` o un `mainloop` se ejecutan
**headless**, con un guardián que cuenta fotogramas y sale limpio en cuanto ve
que la cosa se mueve. Un `while True: pass` pelado sigue dando fallo: la
excepción es para las ventanas, no para los cuelgues.

### Dentro de una familia, gana el que ha demostrado ser rápido

En un turno real medido, Yqcloud tardó **74 segundos** en responder lo que otro
candidato de la misma familia daba en cinco. El orden ya no es el de la lista:
los candidatos se ordenan por **estado del cortacircuitos y latencia p95
medida**, y la cobertura en paralelo sube a tres.

### Y ningún turno se queda esperando para siempre

Plazos controlados en el bucle del agente. Al vencer se entrega lo que haya, con
la degradación dicha en voz alta. Media respuesta anunciada como media respuesta
es utilizable; una pantalla quieta sin explicación no lo es.

### Lo que se arregló para que todo lo anterior fuera usable

- **Las tres IA respondían en inglés.** La comprobación de idioma daba por buena
  cualquier respuesta de menos de doce palabras *en el idioma que fuera*. «Sure!
  I will create a Tetris game for you.» pasaba por español válido. Ahora se
  exige señal del idioma esperado por corta que sea la respuesta.
- **Esa misma guarda tumbaba el enjambre.** Llamaba a un método renombrado,
  fuera del `try`, y el `AttributeError` se llevaba por delante las tres
  variantes: ninguna respuesta, tras haberlas generado. Ahora, si el reintento
  falla, se entrega la original. Una mejora de calidad no puede tener autoridad
  sobre lo que mejora.
- **Naoko decía que la suite estaba rota, y la rompía ella.** Tres sitios
  lanzaban pytest con el mismo directorio temporal; con dos corridas solapadas,
  la segunda le borraba el temporal a la primera y caían 732 tests. Cada corrida
  tiene ahora el suyo.
- **La interfaz se descuadraba con un error largo.** Un diccionario de 200
  caracteres sin espacios es, para el navegador, una sola palabra: empujaba la
  barra de pestañas fuera de la pantalla. Y las pestañas ya no se esconden con
  la ventana estrecha, pasan a la línea siguiente.

**886 tests en Python · 80 en la interfaz · 49 herramientas.**

---

# v5.2.1 — la guarda que mataba lo que venía a proteger

Si en v5.2.0 pediste algo al enjambre y recibiste esto, esta versión lo arregla:

```
[parallel] variante 1 falló: 'MelchiorAgent' object has no attribute
           '_familias_disponibles'
[SWARM] Error catastrófico: ninguna variante de propuesta se completó
```

### Qué pasaba

La guarda de idioma —la que impide que las tres IA te contesten en chino—
llamaba a un método que se había renombrado. Solo en uno de los dos caminos: el
de `_ask` se actualizó, el de `_ask_with_tools` se quedó con el nombre viejo.

Y la llamada estaba **fuera** del `try`, así que el `AttributeError` subía hasta
arriba y se llevaba por delante la variante entera. Las tres variantes muertas,
la orquestación caída, y tú esperando tres minutos para no recibir nada —
después de que los modelos hubieran generado ya tres respuestas perfectamente
válidas, que se tiraron a la basura.

### Lo que se ha cambiado, que es más que el nombre

Corregir el nombre era una línea. Lo importante es lo otro: **una mejora de
calidad no puede tener autoridad para matar lo que mejora.** Ahora el reintento
entero va dentro de un `try`: si falla, por el motivo que sea, se entrega la
respuesta original. Una respuesta en otro idioma es un problema; ninguna
respuesta es otro mucho peor.

Y tiene tope de un reintento en el camino con herramientas, porque ahí cada
intento reejecuta el bucle completo — entre 50 y 74 segundos por pasada en el
caso real. Un turno de un minuto se convertía en uno de diez.

### Por qué no lo vio nadie, y qué se ha hecho al respecto

Python resuelve los atributos al ejecutar. Esa línea solo se recorre cuando la
respuesta llega en otro idioma, así que el import funcionaba, la sintaxis era
válida, los 855 tests pasaban, el CI pasaba en cuatro combinaciones de sistema
y versión, y el `.exe` compilaba. Reventaba en tu máquina.

Hay ahora un test que recorre todas las clases de `magi/` y comprueba que cada
`self.<algo>` existe en la clase o en sus bases. Un lenguaje con comprobación
estática lo habría dicho al compilar; Python no, así que se comprueba. Verificado
inyectando una llamada fantasma a propósito: la caza con fichero y línea.

### Naoko decía que la suite estaba rota, y no lo estaba

```
[naoko] la suite ya estaba roja antes de tocar nada
```

Era falso, y lo causaba la propia verificación. MAGI lanza pytest desde tres
sitios —la herramienta `run_tests` de Balthasar, la verificación de Naoko y la
compuerta de publicación— y los tres compartían el directorio temporal por
defecto. pytest borra las corridas antiguas al arrancar, así que con dos
procesos solapados el segundo borraba el tmp del primero mientras lo usaba:

```
732 ERROR ... FileNotFoundError: [WinError 3] No se puede encontrar la ruta:
'C:\...\Temp\pytest-of-D\pytest-2'
```

Casi todos los tests usan `tmp_path`, así que caían casi todos, y Naoko deducía
que el proyecto estaba roto y se abstenía de reparar nada. Cada corrida tiene
ahora su propio directorio.

### La interfaz

- **El panel de Naoko ya no se descuadra.** Un diccionario de error de 200
  caracteres sin espacios es, para el navegador, una sola palabra — y una
  palabra no se parte. El bloque se salía de su tarjeta, la tarjeta ensanchaba
  la columna y la barra de pestañas se iba fuera de la pantalla. Un mensaje de
  error dejaba media interfaz inalcanzable, justo cuando más falta hace poder
  navegarla.
- **Las pestañas ya no se esconden.** Antes se desplazaban horizontalmente y
  con la ventana estrecha las últimas (Sistema, Mejoras) quedaban fuera de
  alcance. Ahora pasan a la línea siguiente: ocupan un poco más de alto y están
  todas visibles siempre.

---

# v5.2.0 — el bus volvió a entregar, y ahora se ve por qué tarda

Esta versión sale de auditar los cambios de la anterior antes de publicarlos. La
auditoría encontró **siete fallos**, y uno de ellos habría dejado el programa sin
hacer absolutamente nada.

### El grave: el bus de eventos había dejado de entregar

Al añadir la persistencia de eventos críticos, el bucle de reparto de
`MagiBus.publish` acabó **dentro del método nuevo** en vez de quedarse donde
estaba. Un nivel de indentación.

El efecto era total y silencioso: `publish()` dejaba de entregar nada a los
suscriptores. El reparto solo ocurría de rebote, para eventos marcados como
críticos y únicamente si había un receptor de disco enganchado — es decir, nunca
antes de que el kernel terminara de arrancar. Sin interfaz, sin Naoko, sin
telemetría, sin enjambre.

No lanzaba excepción, no escribía en el log y no rompía ningún import. Un
sistema que ya no hace nada tiene el mismo aspecto que uno inactivo. Ahora hay
cinco tests que cubren las tres combinaciones que distinguían el fallo, y se ha
comprobado que fallan al reintroducirlo.

### Las tres IA hablan tu idioma, esta vez de verdad

Casper llegó a entregar su aprobación en chino con la instrucción de idioma
puesta en el prompt. La versión anterior añadió una comprobación… en `_ask`, y el
enjambre usa `_ask_stream`. **El arreglo estaba escrito y no arreglaba nada.**

Ahora se comprueba en los dos caminos. Si la respuesta llega en otro alfabeto se
rota de familia y se reintenta, con tope de dos intentos: el detector es
heurístico y sin tope un solo falso negativo disparaba hasta treinta llamadas de
red por turno. Y Naoko ha dejado de comentar cada rotación — llenaba la pantalla
de mensajes que no describían tu problema.

### Arranque: 3,4 segundos menos

`scikit-learn` —con scipy, numpy y joblib detrás, unos 790 módulos— se cargaba en
**cada apertura del IDE** por una búsqueda de skills que la mayoría de
instalaciones no usa nunca. El intento anterior de arreglarlo movió el import al
constructor de la clase, y el kernel **instancia** esa clase al arrancar: se
seguía pagando entero.

Medido: 3565 ms → 191 ms. Y hay un test que falla si sklearn, g4f, capstone,
Pillow o cualquiera de las doce librerías pesadas vuelve a colarse en el
arranque, porque una regresión así no rompe nada: el sistema hace exactamente lo
mismo, solo que más tarde.

### Nuevo panel: dónde se va el tiempo

La telemetría llevaba desde su creación guardando la duración de cada turno y de
cada uso de herramienta. **Nadie las leía.** El panel enseñaba una media, y una
media no distingue dos situaciones que no se parecen en nada:

```
A: siempre tarda 4 s                          media = 4 s
B: suele tardar 1 s, y 1 de cada 10, 30 s     media = 4 s
```

A es un límite del proveedor. B es la cola de la distribución, y es la que
recuerdas, porque es la vez que te quedaste mirando la pantalla sin saber si el
sistema seguía vivo.

Ahora se ven los cinco agentes, familias y herramientas más lentos ordenados por
**p95**, con su mediana y su peor caso, y una frase que dice si el problema es
*lento* o *irregular* —que no se arreglan igual—. Se avisa además cuando una
herramienta se sale de **su propio** histórico: que `run_tests` tarde 40 s es
normal y que `read_file` tarde 4 s no lo es, y un umbral común no puede
distinguirlas.

### Los eventos críticos sobreviven a una caída

La tabla `task_event` existía desde la primera migración y nadie escribía en
ella. Ahora el arranque, los errores graves y las alertas de observabilidad se
guardan antes de perderse — en un hilo aparte, porque persistir lo que se mide no
puede frenar lo medido, y cerrando la conexión, porque `with sqlite3.connect(...)`
hace commit pero **no** cierra y eso fuga un descriptor por evento.

### Y lo que no se ve

- **Finales de línea.** El árbol de trabajo era CRLF y el repositorio LF. En
  Windows no se notaba; desde el CI o desde WSL, git daba **todo** el repositorio
  por modificado (+57.378/−57.029). Un `git add -A` desde ahí lo habría reescrito
  entero y dejado `git blame` inservible.
- **Binario reproducible.** `requirements.lock` fija las 66 dependencias con las
  que se compiló esta versión. Recompilar este tag dentro de seis meses da el
  mismo `.exe`.
- **«Conecta o borra» con mecanismo.** `scripts/huerfanos.py` encuentra el código
  público que nadie llama —108 hoy— y el CI falla si mañana son 109. Era una
  norma; ahora es un trinquete.
- **El .spec y el código, de acuerdo.** El binario excluye la pila de ML que MAGI
  no usa. Si alguien escribiera `import torch`, los tests seguirían verdes, el CI
  también, el `.exe` compilaría… y reventaría al abrirlo en tu máquina. Ahora se
  comprueba.
- **Un test que castigaba añadir tests.** El guardián del README exigía que la
  cifra declarada fuese mayor o igual que la real, así que cada commit con tests
  nuevos dejaba el CI en rojo. Ahora la cifra es un suelo.

**845 tests en Python · 80 en la interfaz.**

---

# v5.1.6 — el sistema estaba bloqueado de forma permanente

Si en v5.1.5 escribías algo y no pasaba absolutamente nada, no era lentitud ni
un fallo intermitente. **Estaba bloqueado, y lo iba a seguir estando en cada
reinicio.**

### La causa

Dos mitades que por separado parecen inocentes:

```python
# orchestrator.py:296  (ANTES)
elif state["status"] == "in_progress":
    return   # Ignorar comandos extra mientras piensa
```

Un `return` mudo: ni evento, ni registro, ni motivo. Y `_rehydrate()` devolvía
las tareas `in_progress` a memoria **sin volver a lanzar su bucle**: zombis que
figuran trabajando sin que nadie las ejecute.

Encadenado: la interfaz siempre manda el mismo identificador de conversación.
En cuanto una sesión moría a mitad de una tarea, esa fila quedaba `in_progress`
para siempre, y **todo lo que escribieras después chocaba contra ella y
desaparecía**. En una instalación real llevaba así desde hacía dos días.

### El arreglo, y de dónde salió

Dos sistemas agénticos sin ninguna relación entre sí resolvieron esto igual:

| | Cómo lo llaman |
|---|---|
| Zcode Desktop | `session_input`, con `delivery IN ('startNow','guide','queue')` y `status_reason` |
| Claude Code | `command_lifecycle`, con `queued → started` |

En 92 filas de uno y 16 eventos del otro no hay **una sola** entrada de usuario
que desaparezca sin dejar constancia. Y el valor `queue` es la respuesta
literal al fallo: **si el agente está ocupado, tu mensaje se encola, no se
tira.**

Ahora hay un **libro de admisión**: tu mensaje se escribe *antes* de decidir
qué hacer con él, y una restricción de la base de datos hace **imposible**
descartarlo sin escribir por qué. No es documentación: la escritura falla.

Y al arrancar se **reconcilia**: lo que figure en curso sin bucle vivo pasa a
`interrumpida` y se retoma con lo próximo que escribas.

### Lo demás que cambia

**NAOKO deja de inventarse cosas.** Ante «pedí al sistema crear un juego pero
no responde» llegó a contestar con una excusa genérica **y una partida de tres
en raya inventada**. No fue mala redacción: su resumen de estado decía
literalmente *«EN CURSO: … si se queja de demora, ESTO es la demora»* sobre
tareas muertas del día anterior. Premisa falsa, explicación falsa, y sin nada
verdadero que añadir, rellenó.

Ahora las preguntas sobre el propio sistema se contestan con un **catálogo de
diagnóstico** —síntoma → causa → arreglo— construido con datos reales y **sin
modelo**. Es determinista: mismo estado, mismo texto. Y si ningún caso encaja,
dice *«no lo sé, esto es lo que veo»* y enseña los datos. Eso es la respuesta
correcta, no un fallo: un diagnóstico improvisado da confianza falsa.

También distingue por fin **una tarea en curso de verdad** —con bucle vivo
comprobado— de un zombi. Y **no secuestra tus preguntas**: si dices «el
emulador que me hiciste no funciona», mira tu código, no se pone a hablar de sí
misma.

**Arreglar un proveedor caído ya no cuesta recompilar 158 MB.** El catálogo de
proveedores sale de `catalogo_proveedores.json` y se puede sobreescribir en
`%LOCALAPPDATA%\MagiSystem\`. Trae además un tope de contexto que antes no
existía: si un prompt no cabía, el error se leía como «proveedor roto» y se
rotaba a otro que fallaba por lo mismo.

**Migraciones de esquema con checksum.** `CREATE TABLE IF NOT EXISTS` no añade
columnas a una base ya creada, así que cualquier columna nueva no llegaba a
quien ya hubiera abierto MAGI una vez. Siete migraciones, verificadas contra
una base real.

**Las tareas se archivan.** Sin esto solo crecían: siete acumuladas en una
instalación de dos días.

**Telemetría por turno.** A «¿por qué tarda?» ya se puede responder: primer
token, tiempo de API y total por separado, más reintentos, salidas cortadas y
si el segundo candidato del *hedging* llega a ganar alguna vez.

**Auditoría firmada.** NAOKO aplica parches y hace `git push` sobre tu
repositorio; ahora cada acción queda en un diario solo-añadir con HMAC
encadenado. Encadenar —y no solo firmar— detecta además que una línea
desapareció.

**Interfaz.** Fuera `prov-a` / `prov-b` / `prov-c` de las tarjetas centrales:
enseñan el reparto real. El cableado además estaba mal y daba `prov-c` a
BALTHASAR.

### Cuatro fallos encontrados auditando lo anterior

- **Reventaba al aprobar una tarea reanudada.** `state.get("last_proposal", {})`
  no protege de nada: el valor por defecto solo actúa si la clave *falta*, no si
  está y vale `None`.
- **Las variantes paralelas compartían semilla.** `generate_variants` mutaba el
  agente compartido dentro de un `asyncio.gather`: las N «variantes con semillas
  distintas» eran la misma petición repetida N veces.
- El catálogo de diagnóstico secuestraba preguntas que no eran sobre MAGI.
- La entrada del libro se archivaba bajo el identificador equivocado.

### Cambios que quizá notes

- Ninguna funcionalidad se ha retirado.
- Tareas que llevaban colgadas de sesiones anteriores aparecerán como
  **interrumpidas**. Es correcto: son reanudables y se retoman con tu próximo
  mensaje.
- La primera vez que arranque, migrará tu base de datos. No se pierde nada.

---

## Versiones anteriores

### Qué corrige v5.1.5: un import olvidado congelaba la aplicación entera

`ALL_DOMAINS` no estaba reexportado en `magi/core/tools/__init__.py`, así que
el panel de Configuración lanzaba `ImportError` en cada llamada. Eso solo
debería haber roto una pestaña. Rompió el sistema:

```
ImportError  →  log ERROR  →  evento error.critical  →  Naoko diagnostica
con inferencia real  →  su cola se llena  →  el bus BLOQUEA al productor
→  el productor era el propio logging  →  todo se para
```

Y el aviso de «cola llena» era a su vez un WARNING, que volvía a pasar por el
mismo camino generando otro evento: **el sistema se ahogaba con sus propios
mensajes de que se estaba ahogando**. De ahí los cientos de líneas idénticas.
Escribir «crea un documento de word en mi escritorio» no hacía nada, porque ya
no quedaba nadie libre para atenderlo.

**Los tres defectos de diseño que convirtieron un typo en un congelamiento:**

- **El bus bloqueaba al productor** cuando la cola se llenaba. Ahora descarta
  el evento más antiguo y sigue: un bus de diagnóstico jamás debe hacer
  esperar a quien produce. *Medido: 500 eventos con el consumidor colgado
  pasan en 31 ms; antes se colgaba indefinidamente.*
- **El puente de logs se realimentaba.** Ahora no reentra, no repite el mismo
  mensaje dentro de 30 s, y un handler RPC roto no despierta al enjambre.
  *Medido: 200 errores idénticos → 1 evento.*
- **La cabecera sondeaba cada 30 s pasara lo que pasara.** Ahora espacia los
  reintentos y se aparta a los cinco fallos, avisando en pantalla.

Y un test de humo que recorre el registro de handlers **real** e invoca cada
uno: un handler que nadie llama en los tests no existe hasta que un usuario
pulsa la pestaña. Cuando se añada el siguiente, entra solo.

---

### Qué corrigió v5.1.4

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
