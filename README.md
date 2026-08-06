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

Las **44 herramientas** se reparten por rol y se acotan por dominio antes de
entrar en el prompt. No es una optimización cosmética: el catálogo completo son
4,7 KB en cada turno, y un proveedor gratuito con eso delante deja de responder.
Acotado por lo que se está haciendo, Melchior reparando código ve 12
herramientas y 890 bytes.

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

### El ciclo de mejora

Cuando Naoko detecta un método más eficiente o más rápido —citando fichero y
línea, nunca una vaguedad— o cuando la propuesta es tuya, el plan da **dos
vueltas completas** al enjambre antes de volver a ti:

```
        tú apruebas la idea
                │
                ▼
        NAOKO redacta el plan
                │
                ▼
        tú apruebas el borrador
                │
                ▼
   ┌────────────────────────────────┐
   │  MELCHIOR   analiza y mejora   │
   │       ▼                        │   ×2 circuitos
   │  BALTHASAR  crítica popperiana │
   │       ▼      del plan Y de lo  │
   │             que dijo Melchior  │
   │  CASPER     evalúa las tres    │
   │             cosas por separado │
   │             y añade temas      │
   └────────────────────────────────┘
                │
                ▼
     plan hiperperfeccionado → tú decides
                │
                ▼
   NAOKO ejecuta, narrando cada paso
                │
                ▼
        tú autorizas publicar
```

Las compuertas viven en la **máquina de estados**, no en el prompt. La
diferencia importa: un modelo puede ignorar «consulta antes de continuar», pero
no puede inventarse una transición que no existe. Y lo mismo vale para la
verificación — la suite se ejecuta en código, no se le pide amablemente al
modelo que la ejecute.

Mientras trabaja, Naoko es **expresa**: cada herramienta que llama, cada fichero
que toca y cada resultado de la suite salen a la vista en el panel de mejoras y
en el terminal.

---

## Qué sabe hacer

### Ingeniería inversa y emuladores

Desensamblado con **Capstone** (MIPS, ARM, x86), emulación con **Unicorn**,
prueba diferencial entre dos implementaciones, matriz de portabilidad entre
consolas e indexado del código real de un emulador para poder citarlo.

Y **entropía de Shannon** por regiones, que es lo que distingue un binario
cifrado de código roto: la media global de un EBOOT no dice nada porque mezcla
cabecera y carga útil, y una sección cifrada dentro de un fichero por lo demás
normal solo se ve mirando por tramos.

### Fábrica de artefactos que se mira a sí misma

    ESPECIFICAR → GENERAR → EJECUTAR/RENDERIZAR → OBSERVAR → CRITICAR → ITERAR

La clave es OBSERVAR. Un sistema que genera un juego y te lo entrega sin
haberlo arrancado ha *generado código de juego*; uno que lo arranca, captura un
fotograma y lo mira, ha *hecho un juego*.

Hay rama de observación para las seis clases: programas, juegos, imágenes,
documentos, **vídeo** y **datos**. Las dos últimas faltaban, y su ausencia no
daba error: un `.mp4` y un `.csv` se despachaban a «ejecutar como Python» y el
agente recibía `SyntaxError: source code cannot contain null bytes` al pedir que
se mirase el vídeo que acababa de hacer.

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
meses. La unidad tampoco se supone: un emisor extranjero que presenta 20-F ante
la SEC lo hace en su moneda, y rotular esos euros como dólares es inventarse el
dato con aspecto de rigor.

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
  verdad**: los procesos que murieron, los que no, y las tareas del enjambre que
  agotaron el margen y siguen corriendo. Un botón de parada que dice haber
  parado algo que sigue vivo es peor que no tenerlo.

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
- **Panel de mejoras**: el ciclo de Naoko con sus compuertas, y lo que va
  haciendo mientras lo hace.

---

## Instalación

```bash
git clone https://github.com/4n0th1ng/MAGI-System-IDE
cd MAGI-System-IDE
pip install -r requirements.txt

cd magi-gui && npm ci && npm run build && cd ..
python -m magi.main
```

Opcionales, detectados si están: `capstone` y `unicorn` (ingeniería inversa),
`pygame` y `pillow` (observar juegos e imágenes), `ffmpeg` (vídeo), ComfyUI en
`127.0.0.1:8188` (dibujo). Sin ellos el sistema funciona y **avisa de lo que no
puede hacer**, en vez de fingir.

### Binario para Windows

Cada release publica el ejecutable dentro de un `.zip` listo para descargar,
compilado por GitHub Actions tras pasar la suite completa.

El `.exe` funciona por sí solo, pero **para ejecutar código Python necesita un
Python instalado en la máquina**. Es una consecuencia de cómo funciona un
empaquetado onefile, y afecta a las herramientas que ejecutan (`run_tests`,
`python_exec`), a la verificación de propuestas y al bucle de observación de
programas y juegos. Si no lo encuentra, lo dice; no lo intenta a medias.

---

## Cómo está construido esto

Seis reglas, cada una nacida de un fallo real de esta reconstrucción:

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
5. **«No he podido comprobarlo» no es «está bien».** Es la más cara de las seis,
   porque el fallo se disfraza de éxito. Sin Pillow, el observador de imágenes
   devolvía «correcto» sobre una captura que nunca llegó a abrir; sin pypdf, un
   PDF de páginas en blanco salía aprobado; un `.parquet` que nadie sabía leer
   se resumía como «1 registros». En los tres casos el aviso existía, enterrado
   en la evidencia, que no entra en el veredicto. Ahora, cuando el sistema no
   puede mirar, lo dice entre los problemas y el veredicto es negativo.
6. **El binario publicado no es el mismo programa que el que ejecutas al
   desarrollar.** Dentro del `.exe`, `sys.executable` es el propio `.exe`: seis
   sitios lanzaban Python con él y, en el binario que la gente se descarga,
   relanzaban MAGI en vez de ejecutar los tests, el código propuesto o el juego
   recién generado. Nada daba error; daban el resultado de otro programa.

Y el corolario, que apareció una y otra vez: **el instrumento de medida es el
mejor escondite**. El listado del desván comprobaba tres ficheros por
subcadena; el limpiador de comentarios pegaba los tokens sin espacios y dejaba
pasar en vacío todas las guardas que buscaban una frase; el fetcher congelado de
los tests casaba solo el dominio, así que una URL con parámetros que la API real
rechaza siempre con HTTP 400 llevaba meses en verde; y los cinco tests que
custodiaban la compuerta de publicación leían el código fuente buscando
subcadenas, de modo que cuatro mutantes que rompían la compuerta de verdad
—uno hacía que la autocorrección publicara sin permiso— dejaban la suite entera
en verde.

Todos verdes. Ninguno comprobando nada.

<!-- naoko:mejoras -->
