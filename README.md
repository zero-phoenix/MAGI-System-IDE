# MAGI System IDE

Un entorno de desarrollo con un **enjambre de tres inteligencias que aplican el
método dialéctico** (tesis → antítesis → síntesis) y **herramientas reales sobre
tu máquina** para ejecutar lo que deciden.

Inferencia **100 % de nube gratuita**: sin claves de API, sin modelos locales,
sin suscripciones.

**[⬇ Descargar la última versión para Windows](https://github.com/zero-phoenix/MAGI-System-IDE/releases/latest)** — un `.zip`, se descomprime y se ejecuta. Sin instalador.

---

## Cómo funciona

Escribes una petición. El sistema la procesa en una sola pasada:

1. **Naoko** clasifica tu petición y elige el **estilo** de respuesta que más
   conviene (técnico, sintético, creativo o analítico). Tú no eliges nada: ella
   decide.
2. **MELCHIOR** redacta la **TESIS**: construye la solución, escribe el código,
   la defiende.
3. **BALTHASAR** redacta la **ANTÍTESIS**: refuta a Melchior ejecutando su
   código, buscando el fallo real con evidencia.
4. **CASPER** (Gaspar) redacta la **SÍNTESIS definitiva**: integra tesis y
   antítesis con su propio juicio crítico y te entrega la respuesta consolidada,
   en español.

Una sola ronda por defecto. Si no estás de acuerdo, escribes tu feedback y una
segunda ronda arranca en Melchior con la síntesis previa de Casper + tus
observaciones.

```
TU PETICIÓN
    │
    ▼
NAOKO elige el estilo
    │
    ▼
MELCHIOR  ──TESIS────▶  BALTHASAR  ──ANTÍTESIS────▶  CASPER
(construye)            (refuta con evidencia)       (SÍNTESIS al usuario)
                                                         │
                                                         ▼
                                              RESPUESTA DEFINITIVA (en español)

RITSUKO  ──audita a NAOKO y su relación con los tres──▶  informes y megaplanes
(no toca nada: solo informa, en su propia pestaña)
```

**Ritsuko** es la quinta IA, y existe porque nadie comprobaba a la cuarta.
Naoko corrige al enjambre —detecta deriva, reordena el reparto, aplica
mejoras—, así que un diagnóstico suyo equivocado mueve el sistema entero en la
dirección equivocada con toda la autoridad. Ritsuko revisa eso: mira la
evidencia del bus, dice si el sistema mejora o empeora, señala cuándo un nodo
se ha quedado mudo y deja cada informe escrito en disco para descargar.

No arregla nada, a propósito: un auditor con permiso para aplicar cambios
acaba revisándose a sí mismo. Y usa una familia de modelo que **no comparte con
ninguna de las otras cuatro**, porque un auditor que se cae cuando se cae el
auditado no sirve justo el día que hace falta. Habla español o inglés, nunca
otro idioma.

---

## Los tres motores del enjambre

Cada nodo es una IA anclada a una **familia de modelo distinta**, para que el
crítico tenga sesgos diferentes al proponente. La interfaz muestra siempre la
familia que **de verdad** respondió.

| Nodo | Rol | Familia | Qué hace |
|---|---|---|---|
| **MELCHIOR** | TESIS | `gpt` | Construye: lee, escribe, ejecuta. Anticipa dónde fallará su propia propuesta. |
| **BALTHASAR** | ANTÍTESIS | `gemini` | Refuta: lee y **ejecuta** el código de Melchior, pero no escribe. Aporta evidencia, no sospechas. |
| **CASPER** | SÍNTESIS | `command` | Te habla. Integra ambas posiciones con juicio crítico y redacta la respuesta final. |

Las conclusiones (`### CONCLUSIÓN`) van **siempre en español**. Casper, que es
quien te lee, responde entero en español.

Cada IA es **consciente de su rol** y de que forma parte de un enjambre de tres.
Naoko también conoce los roles y puede explicarte qué hace cada nodo.

---

## Dos motores, nada más

La barra superior tiene un único selector con dos opciones:

- **🔍 Análisis profundo** (por defecto) — baja temperatura, más iteraciones de
  herramientas y verificación. Más lenta y más precisa.
- **⚡ Súper rapidez** — temperatura normal, menos vueltas. Rápida.

El estilo de redacción lo decide **Naoko automáticamente** según tu pregunta.
Ya no hay que elegir un estilo a mano antes de cada petición.

---

## Naoko: la supervisora que entiende el sistema

Naoko es externa al enjambre de tres. **Supervisa, diagnostica y repara**, y
además **decide el estilo** de cada respuesta:

- **Clasifica tu petición** (técnica, sintética, creativa, analítica) y propaga
  ese estilo a los tres agentes. Es la que mejor entiende qué tipo de respuesta
  conviene a lo que preguntaste.
- **Repara sola** cuando hay un fallo con tests que lo demuestran. Sin
  consultar: el usuario no debe ser el cuello de botella de su propio sistema.
- **Mejora contigo** cuando el cambio es de criterio (no de corrección). Ahí va
  con compuertas: tú apruebas cada paso, y publicar es siempre tu decisión.
- **Conoce el enjambre**: si le preguntas «¿por qué Melchior hizo X?» o «¿qué
  tal está el enjambre?», referencia los roles correctamente.

---

## Ritsuko: quien revisa a la revisora

Naoko corrige a los tres nodos. Nadie corregía a Naoko — y eso no es teórico:
la auditoría del 20 de agosto la encontró declarando «deriva del modelo» en dos
familias enteras justo después de una tarea que había agotado la cuota de esos
mismos proveedores. Estaba midiendo su propia interferencia y llamándola avería.

Ritsuko es ese revisor. Corre en una familia de modelos **distinta** de las que
audita, tiene su propio chat y su propia pestaña, y habla solo español o inglés.

- **Solo informa.** No escribe código, no cancela tareas, no toca el reparto del
  enjambre. Su valor entero está en ser independiente de lo que juzga; un
  auditor que también ejecuta acaba auditándose a sí mismo.
- **Revisa los diagnósticos de Naoko** y puede anularlos. Si la muestra de
  canarios no da para afirmar nada, o si el enjambre estaba gastando cuota en
  los dos minutos previos, el veredicto de deriva se anula y se dice por qué.
  Cuando se sostiene, lo confirma — «nadie lo miró» y «lo miré y está bien» son
  cosas distintas.
- **Escribe informes descargables** con la evidencia que los sostiene, en
  `%LOCALAPPDATA%\MagiSystem\informes-ritsuko`.

---

## Cómo trabaja el enjambre

Ocho reglas, sacadas de contrastar lo que hacía MAGI contra lo que hace un
agente que sí entrega. Cada una es un mecanismo con su prueba, no un consejo.

1. **El encargo es un contrato, no un tema.** «Un ping pong de 32 bits a todo
   color en un exe portable» son cuatro promesas separables. MAGI las enumera al
   empezar y comprueba al final cuáles quedaron sin cubrir.
2. **«Hecho» se define antes de empezar, y lo comprueba una máquina.** Nadie de
   este sistema ve la pantalla. Si el encargo es un juego, el artefacto tiene
   que nacer con `--autotest`; si pide un formato de color, con `--formato`. Se
   exigen al escribir, no al terminar.
3. **Mirar la caja antes de razonar de memoria.** Se le señalan por su nombre
   las herramientas que responden a ESE encargo, y para las que se pueden
   ejecutar solas —`analyze_port` entre dos consolas— el resultado ya viene
   puesto en el prompt.
4. **El porqué va pegado al arreglo.** Cada cambio de este repositorio lleva al
   lado la medición que lo forzó, para que quien venga a simplificarlo lea
   primero por qué existe.
5. **Desconfiar del propio informe de éxito.** Toda afirmación comprobable
   —«se compiló», «las pruebas pasan», «según analyze_port»— se contrasta contra
   el registro de lo que el sistema hizo de verdad.
6. **Si el último paso falla, el trabajo se conserva.** Lo hecho no se tira
   porque lo siguiente falle.
7. **Pocas pasadas, bien dirigidas.** Tres propuestas que nadie ejecuta valen
   menos que una que sí: menos enfoques en paralelo, más ciclos de verificación.
8. **Se contestan todas las partes del enunciado.** Un encargo que pide «el
   orden que minimiza el riesgo de abandono» y recibe una respuesta que no
   menciona el abandono está a medias, aunque lo demás sea bueno.

---

## La columna izquierda: tus conversaciones

- **Títulos generados por IA**: cada conversación se nombra con un resumen corto
  de tu petición («Juego Tetris portable»), no con un identificador críptico.
- **Archivar (📦)**: guarda la conversación fuera de la vista sin perderla.
- **Borrar (🗑)**: la elimina de la lista, con confirmación inline.
- **Persistencia**: al cerrar y reabrir, tus conversaciones siguen ahí con sus
  títulos. No se pierden tras un reinicio.

---

## Qué sabe hacer

Más allá de debatir, el enjambre tiene **50 herramientas** reales sobre tu
máquina, repartidas por rol y acotadas por dominio antes de entrar en el prompt.

- **Ingeniería de software**: crear, modificar y ejecutar código, construir
  proyectos, empaquetar a `.exe` portable.
- **Ingeniería inversa y emuladores**: desensamblado (Capstone), emulación
  (Unicorn), entropía de Shannon por regiones.
- **Fábrica de artefactos que se mira a sí misma**: especificar → generar →
  ejecutar/renderizar → **observar** → criticar → iterar. Un juego se arranca
  headless y se captura un fotograma para comprobar que el jugador se distingue
  del fondo.
- **Vídeo programático**: animática Ken Burns, manga → vídeo en vertical, con
  detección de fotogramas en negro o congelados.
- **Mundo real**: macro, geopolítica y finanzas con fuentes gratuitas y sin
  clave (FRED, BCE, Banco Mundial, SEC EDGAR). Un dato no se construye sin
  fuente y fecha.

---

## Reversibilidad y parada

El acceso sin restricciones a tu máquina se sostiene sobre dos salidas:

- **Deshacer.** Antes de tocar un fichero se copia. `undo` lo devuelve, por
  operación o por tarea entera.
- **Parar.** `PARAR ESTA` cancela una conversación; `PARAR TODO` es la parada de
  emergencia. Manda `SIGTERM` primero y solo `SIGKILL` si no atienden, y devuelve
  un informe de lo que paró **de verdad**.

La misma copia que da la reversibilidad alimenta el **panel de aprobación**: qué
ficheros toca el cambio, su contenido antes y después con un diff real, las
órdenes que se ejecutarán y si los tests pasaron.

---

## La interfaz

- **Ctrl+K** abre la paleta de comandos con filtrado difuso.
- **Streaming token a token**: el primer token llega en ~2 s.
- **Traza de herramientas**: ver «leyendo `dynarec.cpp:412`» convierte una caja
  negra en un colaborador.
- **Panel de coste** con avisos — el principal detecta si los tres nodos
  corrieron sobre la misma familia.
- **Panel de sistema**: salud (latencias y tasas de fallo), banco de evaluación
  y auto-mejora medible.
- **Dónde se va el tiempo**: los agentes, familias y herramientas más lentos,
  ordenados por **p95**, no por media.
- **Salud por día** *(nuevo en v5.5.0)*: chispa con la latencia diaria de cada
  candidato (14 días) y su tendencia. La media histórica esconde que un
  proveedor pasó de 3 s a 9 s esta semana; la pendiente no.
- **Por qué faltan proveedores** *(nuevo en v5.5.0)*: los que exigen tu cuenta
  o abren navegador («no van a volver») separados de los caídos («HTTP 429,
  puede volver»), cada uno con su motivo medido — no un «sin verificar»
  eterno.

---

## Instalación

### Binario para Windows (recomendado)

**[⬇ Descargar la última versión](https://github.com/zero-phoenix/MAGI-System-IDE/releases/latest)**

1. En **Assets**, descarga **`MAGI-IDE-v5.zip`**.
2. Verifica la descarga (opcional): `certutil -hashfile MAGI-IDE-v5.zip SHA256`
   contra **`CHECKSUMS.txt`**, que se publica junto al zip.
3. Descomprímelo donde quieras — no hay instalador ni carpetas obligatorias.
4. Ejecuta **`MAGI-IDE-v5.exe`**.

Windows SmartScreen avisará porque el binario no está firmado: *Más
información → Ejecutar de todas formas*.

Va en `.zip` a propósito: Windows y muchos navegadores bloquean o marcan un
`.exe` descargado suelto. Lo compila **GitHub Actions** desde el tag, tras pasar
la suite completa de tests; no hay ninguna subida manual de por medio.

El binario **lleva su propio Python 3.10 dentro**, así que las herramientas que
ejecutan código funcionan sin que tengas Python instalado.

### Desde el código

```bash
git clone https://github.com/zero-phoenix/MAGI-System-IDE
cd MAGI-System-IDE
pip install -r requirements.txt

cd magi-gui && npm ci && npm run build && cd ..
python -m magi.main
```

Opcionales, detectados si están: `capstone` y `unicorn` (ingeniería inversa),
`pygame` y `pillow` (observar juegos e imágenes), `ffmpeg` (vídeo), ComfyUI en
`127.0.0.1:8188` (dibujo). Sin ellos el sistema funciona y **avisa de lo que no
puede hacer**, en vez de fingir.

---

## Cómo está construido esto

Siete reglas, cada una nacida de un fallo real:

1. **Todo cambio se conecta o se borra.** Nunca se añade sin conectar. Tres
   veces se escribió la pieza correcta, con sus tests en verde, y no la llamaba
   nadie.
2. **Un test sobre una pieza aislada no prueba que el sistema la use.** Por eso
   hay una auditoría del grafo de llamadas con AST y un trinquete que solo puede
   bajar.
3. **Cada capacidad del backend tiene que poder invocarse desde la interfaz.**
4. **Arrancar encuentra fallos que leer no encuentra.** El botón de parada de
   emergencia escribía una línea de log y devolvía una cadena con aspecto de
   éxito; el visor de diffs recibía el original vacío y pintaba todo en verde.
5. **«No he podido comprobarlo» no es «está bien».** Sin Pillow, el observador de
   imágenes devolvía «correcto» sobre una captura que nunca llegó a abrir.
6. **El binario publicado no es el mismo programa que el de desarrollo.** Dentro
   del `.exe`, `sys.executable` es el propio `.exe`: seis sitios lanzaban Python
   con él y relanzaban MAGI en vez de ejecutar los tests.
7. **Arreglar algo no es lo mismo que arreglarlo donde importa.** La guarda de
   idioma se puso en `_ask` y el enjambre usa `_ask_stream`. Un cambio no está
   hecho hasta que se comprueba **en el camino por el que pasa el sistema de
   verdad**.

**1260 tests en Python · 122 en la interfaz · sin tests verdes no hay release.**

Y esa regla no depende del CI. Lo mismo que ejecuta GitHub Actions se ejecuta
aquí, con los mismos comandos:

```bash
python scripts/verificar.py            # lo de cada push  (~4 min)
python scripts/verificar.py --todo     # + los que compilan un .exe (~10 min)
```

Existe porque el CI se paró en seco el 13-ago: repositorio privado, minutos de
Actions agotados, seis jobs fallando en dos segundos sin llegar a asignar
runner. Una regla que depende de un servicio de pago no es una regla, es una
suscripción.

<!-- naoko:mejoras -->
