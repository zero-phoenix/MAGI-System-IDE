# MAGI System IDE

Entorno de desarrollo con un **enjambre de tres inteligencias que debaten antes
de actuar** y **herramientas reales sobre tu máquina** para ejecutar lo que
deciden.

Inferencia **100 % de nube gratuita**: sin claves de API, sin modelos locales,
sin suscripciones.

**602 tests en Python · 66 en la interfaz · sin tests verdes no hay release.**

---

## Índice

- [La idea](#la-idea)
- [El enjambre](#el-enjambre)
- [Naoko: repara sola, mejora contigo](#naoko-repara-sola-mejora-contigo)
- [Qué sabe hacer](#qué-sabe-hacer)
- [Cómo decide qué esfuerzo merece cada petición](#cómo-decide-qué-esfuerzo-merece-cada-petición)
- [Reversibilidad y parada](#reversibilidad-y-parada)
- [La interfaz](#la-interfaz)
- [Instalación](#instalación)
- [Cómo está construido esto](#cómo-está-construido-esto)

---

## La idea

Tres modelos discutiendo entre sí no valen nada si los tres son el mismo
modelo. La versión anterior de este sistema tenía un «debate popperiano» en el
que los tres nodos llamaban a `gpt-4o-mini`: un modelo hablando solo, con tres
nombres distintos.

Ahora cada nodo está anclado a una **familia de modelo diferente** y la interfaz
muestra la familia que **de verdad** respondió, no la que tenía asignada. Si un
proveedor se cae y el registro conmuta a otro, se dice.

Y un agente que solo emite texto no es un colaborador. Los tres nodos pueden
**leer, escribir, ejecutar y verificar** sobre tu máquina.

---

## El enjambre

| Nodo | Rol popperiano | Familia | Puede |
|---|---|---|---|
| **MELCHIOR** | Creador / sintetizador | `deepseek` | leer, escribir, ejecutar |
| **BALTHASAR** | Crítico hostil / falsacionista | `claude` | leer y **ejecutar**, no escribir |
| **CASPER** | Juez / árbitro | `qwen` | leer y verificar tests |

Que Balthasar no pueda escribir no es una restricción de seguridad: es lo que le
da autoridad. Una crítica que dice *«esto falla con entrada vacía»* **habiendo
ejecutado el caso** vale mucho más que una que lo sospecha.

---

## Naoko: repara sola, mejora contigo

Naoko supervisa el sistema, y tiene **dos vías separadas a propósito**, porque
reparar y mejorar no son lo mismo:

- **Reparar** devuelve el sistema a donde ya debía estar. Hay un fallo, hay
  tests que lo demuestran, y la corrección es verificable. Va **sin consultar**:
  consultar cada arreglo convierte al usuario en el cuello de botella de su
  propio sistema.
- **Mejorar** cambia *hacia dónde va* el sistema. No hay un «correcto» contra el
  que comprobar: hay un criterio, y el criterio es tuyo. Va **con compuertas**.

**Publicar es siempre tuyo**, aunque el cambio sea una reparación: subir a
GitHub es visible para terceros y no se deshace con un `undo`.

### El circuito de mejora

Naoko tiene rol creativo de desarrollo: propone cuando detecta un método más
eficiente o más rápido —citando fichero y línea— y tiene **prohibido** proponer
reescrituras por elegancia o cambios de nomenclatura. Una propuesta sin un antes
y un después medibles es ruido, y el ruido hace que se dejen de leer las buenas.

Cuando tiene una idea (o cuando la propones tú), el plan da **dos vueltas
completas** al enjambre antes de volver a ti:

```
Naoko detecta algo mejorable
    │
    ├─ [COMPUERTA] ¿desarrollo un plan?
    │
Naoko redacta un plan extenso
    │
    ├─ [COMPUERTA] ¿lo paso al enjambre?
    │
┌───▼───────────────────────────────────────────────┐
│  MELCHIOR   analiza, mejora y añade sus críticas   │
│  BALTHASAR  examina el plan Y lo de Melchior;      │
│             crítica popperiana, con ejecución      │
│  CASPER     evalúa las tres cosas por separado,    │
│             se pronuncia y añade temas nuevos      │
└───┬───────────────────────────────────────────────┘
    │  vuelve automáticamente — 2 circuitos
    │
CASPER entrega el plan hiperperfeccionado
    │
    ├─ [COMPUERTA] ¿lo apruebo y lo ejecuto?
    │
NAOKO ejecuta, narrando cada paso
    │
    └─ [COMPUERTA] ¿lo publico?
           └─ compilación local → README → etiqueta
              → Actions compila el .exe y lo adjunta en .zip
```

**Dos vueltas y no una** porque la segunda es donde el circuito gana algo: en la
primera cada nodo ve el plan por primera vez; en la segunda lo ve **ya criticado
por los otros dos**, que es cuando una crítica puede refutar a otra. Una sola
vuelta son tres opiniones en paralelo disfrazadas de debate.

Tus propias propuestas entran por el mismo sitio y recorren lo mismo: que la
idea sea tuya no la exime de la crítica.

**Las compuertas viven en la máquina de estados, no en el prompt.** Un modelo
puede ignorar «consulta antes de continuar»; no puede inventarse una transición
que no existe. Y si una fase revienta, la mejora queda en un estado del que se
sale —reintentar o descartar—, no bloqueada para siempre.

---

## Qué sabe hacer

44 herramientas que el enjambre invoca directamente. El catálogo entero no cabe
en el prompt de un proveedor gratuito, así que **cada tarea recibe solo su
dominio**:

| Tarea | Herramientas | Catálogo |
|---|---|---|
| «arregla el bug del scroll» | 12 | 890 chars |
| «dibuja una página de manga» | 19 | 1 865 chars |
| «analiza los fundamentales de Apple» | 23 | 2 185 chars |
| «porta el dynarec de PPSSPP a Vita» | 26 | 2 485 chars |

### Ingeniería inversa y emuladores

| Herramienta | Qué hace |
|---|---|
| `binary_identify` | formato, ISA, endianness, punto de entrada, consola probable **y entropía** |
| `binary_entropy` | detecta binarios cifrados o comprimidos, y localiza las zonas |
| `console_profile` | CPU, RAM, GPU, base de carga y formatos de PSP, NDS, Vita, GBA, PSX, N64, 3DS |
| `disassemble` | Capstone: MIPS y ARM, con modo Thumb y endianness explícitos |
| `emulate_code` | ejecuta un fragmento con Unicorn y devuelve los registros |
| `differential_test` | compara tu emulador contra Unicorn y localiza la instrucción que diverge |
| `compare_consoles` · `analyze_port` · `suggest_port_base` | qué cuesta portar, subsistema a subsistema |
| `index_emulator` · `locate_subsystem` · `compare_emulators` | sobre el **código real** de un emulador |

La entropía va integrada en `binary_identify` a propósito: un EBOOT.BIN cifrado
se ve igual que código roto, y al pasarlo por Capstone salen instrucciones sin
sentido. La conclusión natural —y equivocada— es que falla el decodificador.

```
analyze_port psp vita
─────────────────────────────────────────────────────────────
gpu       irreducible   pipeline fijo → programable: el backend
                        gráfico se reescribe entero, no se adapta
dynarec   reemplazar    frontend de MIPS y emisión para ARM; la IR
                        intermedia sí se reutiliza
frontend  reutilizable  interfaz, configuración, entrada, grabación
─────────────────────────────────────────────────────────────
reutilización estimada: 55 %
```

Y `suggest_port_base vita` responde **Nintendo 3DS** (71 %) antes que PSP (55 %),
porque ARMv6K→ARMv7-A con shaders en ambas reutiliza más que MIPS→ARM con
pipeline fijo — aunque PPSSPP sea el emulador más conocido.

### Fábrica de artefactos con bucle de observación

El sistema **mira lo que produce** antes de dártelo:

| Artefacto | Qué observa |
|---|---|
| Programa | lo arranca y captura salida y código de retorno |
| Juego | lo ejecuta headless, avanza fotogramas y **captura la pantalla** |
| Imagen | tamaño, número de colores, color dominante |
| Documento | páginas, párrafos, palabras; detecta plantillas vacías |
| Vídeo | duración, códec, y si está **en negro o congelado** |
| Datos | filas, columnas; detecta el CSV con cabecera y cero filas |

El caso que justifica el bucle entero: un juego donde el jugador es del mismo
color que el fondo. El código es correcto, los tests pasarían, y en pantalla no
se ve nada.

```
[FALLA] juego: 30 fotogramas dibujados
  · 320x240, 1 colores; el dominante (20, 20, 30) ocupa el 100%
  problemas observados:
  · la pantalla es de un solo color: el juego dibuja pero no se ve nada
```

No gasta cuota de visión: es análisis de histograma con Pillow.

### Vídeo programático

Animática Ken Burns, manga → vídeo en vertical, y grabación de un programa
gráfico en ejecución. Un vídeo tiene dos formas de salir mal que ninguna
comprobación barata ve, porque el fichero existe, pesa megas y se reproduce:
**todo negro** y **congelado** —todos los fotogramas idénticos, la animación que
no animó—. `observe_video` muestrea fotogramas separados en el tiempo y los
compara.

Solo están construidos los escalones que dan resultado profesional hoy y sin
coste. El gen-vídeo largo y coherente no está resuelto localmente en hardware de
escritorio, y fingirlo sería vender humo.

### Manga

La composición —rejilla, orden de lectura **derecha a izquierda**, globos,
validación de solapes— es geometría determinista y está construida y probada. La
generación de los dibujos necesita ComfyUI local (gratis, sin claves) y va
detrás de un backend enchufable: sin ComfyUI las viñetas salen como marcadores
de posición y el sistema **lo dice**, en vez de fingir que dibujó.

`validate_manga_layout` comprueba solapes, huecos y viñetas fuera de página
**antes** de generar nada: descubrir después que dos viñetas se pisan es tirar
ocho generaciones.

### Mundo real: macro, geopolítica y finanzas

Todas las fuentes son **gratuitas y sin clave de API**, probadas contra la red
antes de escribir los parsers: FRED, BCE, Banco Mundial, SEC EDGAR y RSS
oficiales.

Un dato **no se puede construir sin fuente y fecha** — no es un campo opcional.
Y se distinguen dos fechas que casi todo el mundo confunde: a qué momento se
refiere el dato, y cuándo lo descargamos nosotros. Confundirlas es cómo un
sistema acaba diciendo «el paro es del 4,2 %» citando una cifra de hace catorce
meses.

#### Sobre «las habilidades de Warren Buffett»

Conviene que quede escrito, porque es donde más fácil sería vender humo. El
juicio de Buffett —sesenta años de criterio, una red de contactos, capital
permanente y temperamento bajo pánico— **no es software**, y cualquier producto
que diga tenerlo te está vendiendo un generador de números con vocabulario
financiero. El `quant/simulator.py` de la versión anterior devolvía literalmente
`np.random.randint(60, 101)` como «índice risk-off»; está retirado.

Lo que sí es construible es la contabilidad que él hace a mano y casi nadie
hace: ganancias del propietario con el capex de mantenimiento separado, ROIC,
dilución medida sobre el recuento real de acciones, conversión de caja, y un
descuento de flujos que **nunca devuelve un número solo** sino la rejilla de
sensibilidad y qué porcentaje del valor es terminal. Toda la aritmética se
ejecuta en Python y enseña su fórmula y sus entradas: el modelo interpreta, no
calcula.

Y lo que de verdad se le parece: el **registro de tesis**. Cada afirmación se
congela con su fecha, su razonamiento, sus fuentes y su confianza declarada, y
se puntúa al vencer con la regla de Brier contra la línea base. Acertar mucho es
fácil si solo predices lo obvio; lo que mide el criterio es la calibración —que
cuando dices 70 % aciertes el 70 %— y el sistema informa de su propio exceso de
confianza.

---

## Cómo decide qué esfuerzo merece cada petición

No todo merece un debate de tres rondas.

| Ruta | Cuándo | Coste |
|---|---|---|
| `chat` | saludo, confirmación | 1 llamada |
| `lookup` | pregunta factual | 1 llamada + web |
| `task` | acción concreta sobre ficheros o código | Melchior + verificación |
| `build` | proyecto, juego, emulador, investigación | debate completo iterado |

---

## Reversibilidad y parada

El acceso sin restricciones a tu máquina es una decisión tuya, y se sostiene
sobre **dos salidas**:

- **Deshacer.** Antes de tocar un fichero se copia. `undo` lo devuelve, por
  operación o por tarea entera. No añade permisos: añade reversibilidad. Un
  agente que puede deshacer lo que hizo es un agente al que puedes dejar suelto;
  uno que no puede, acabas vigilándolo.
- **Parar.** `PARAR ESTA` cancela una conversación; `PARAR TODO` es la parada de
  emergencia. Manda primero `SIGTERM` para que los procesos cierren limpio y
  solo `SIGKILL` si no atienden, y devuelve un informe de lo que paró **de
  verdad**, incluidos los procesos que no murieron.

La misma copia que da la reversibilidad alimenta el **panel de aprobación**: qué
ficheros toca el cambio, su contenido antes y después con un diff real, las
órdenes que se ejecutarán y si los tests pasaron.

---

## La interfaz

- **Ctrl+K** abre la paleta de comandos. Filtra por subsecuencia: «pse»
  encuentra «Parar Solo Esta tarea» sin mirar el teclado.
- **Streaming token a token**: el primer token llega en ~2 s en vez de esperar
  la respuesta completa.
- **Traza de herramientas**: ver «leyendo `dynarec.cpp:412`» convierte una caja
  negra en un colaborador cuyo razonamiento se puede seguir.
- **Panel de coste**: tokens y tiempo por tarea y por agente. Lo útil no es la
  tabla sino los avisos — el principal detecta que los tres nodos corrieron
  sobre la misma familia de modelo.
- **Panel de sistema**: salud (latencias y tasas de fallo), banco de evaluación
  y auto-mejora medible.
- **Panel de mejoras**: el ciclo de Naoko con sus compuertas.

---

## Instalación

```bash
git clone https://github.com/4n0th1ng/MAGI-System-IDE
cd MAGI-System-IDE
pip install -r requirements.txt

cd magi-gui && npm install && npm run build && cd ..
python -m magi.main
```

Opcionales, detectados si están: `capstone` y `unicorn` (ingeniería inversa),
`pygame` y `pillow` (observar juegos e imágenes), `ffmpeg` (vídeo), ComfyUI en
`127.0.0.1:8188` (dibujo). Sin ellos el sistema funciona y **avisa de lo que no
puede hacer**, en vez de fingir.

### Binario para Windows

Cada release publica el ejecutable dentro de un `.zip` listo para descargar,
compilado por GitHub Actions tras pasar la suite completa.

---

## Cómo está construido esto

Cuatro reglas, cada una nacida de un fallo real de esta reconstrucción:

1. **Todo cambio se conecta o se borra.** Nunca se añade sin conectar. Tres
   veces se escribió la pieza correcta, con sus tests en verde, y no la llamaba
   nadie.
2. **Un test sobre una pieza aislada no prueba que el sistema la use.** Por eso
   hay una auditoría del grafo de llamadas con AST, y un trinquete de módulos
   huérfanos que solo puede bajar.
3. **Cada capacidad del backend tiene que poder invocarse desde la interfaz.**
   Auditarlo encontró tres capacidades completas e inalcanzables.
4. **Arrancar encuentra fallos que leer no encuentra.** El botón de parada de
   emergencia escribía una línea de log y devolvía una cadena con aspecto de
   éxito; el visor de diffs recibía el original vacío y pintaba todo en verde;
   la contabilidad de tokens se calculaba y se tiraba. Ninguno daba error.
5. **«No he podido comprobarlo» no es «está bien».** Es la regla más cara de
   las cinco, porque el fallo se disfraza de éxito. Sin Pillow, el observador
   de imágenes devolvía «correcto» sobre una captura que nunca llegó a abrir;
   sin pypdf, un PDF de páginas en blanco salía aprobado; un vídeo con un solo
   fotograma extraído se daba por no congelado sin haber comparado nada. En
   los tres casos el aviso existía —enterrado en la evidencia, que no entra en
   el veredicto—. Ahora, cuando el sistema no puede mirar, lo dice en los
   problemas y el veredicto es negativo.
6. **El binario publicado no es el mismo programa que el que ejecutas al
   desarrollar.** Dentro del `.exe`, `sys.executable` es el propio `.exe`: seis
   sitios lanzaban Python con él y, en el binario que la gente se descarga,
   relanzaban MAGI en vez de ejecutar los tests, el código propuesto o el juego
   recién generado. Nada daba error; daban el resultado de otro programa.

Y su corolario, que apareció una y otra vez: **el instrumento de medida es el
mejor escondite**. El listado del desván comprobaba tres ficheros por
subcadena; el limpiador de comentarios pegaba los tokens sin espacios y dejaba
pasar todas las guardas que buscaban una frase; el fetcher congelado de los
tests casaba solo el dominio, así que una URL con parámetros incompatibles
—que la API real rechaza siempre con HTTP 400— pasaba en verde para siempre.
Todos verdes, todos sin comprobar nada.

<!-- naoko:mejoras -->
