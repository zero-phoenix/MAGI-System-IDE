# Plan de mejora — MAGI v6

Escrito después de arreglar los tres fallos que impedían usar el sistema
(idioma contaminado, agentes hablando tres veces por ronda, tareas de
aprobación tiradas al reiniciar). Lo que queda aquí es lo que sigue.

Cada punto lleva **por qué**, **cómo se comprueba** y **qué puede salir mal**.
Un plan sin la tercera columna es una lista de deseos.

---

## 0. El principio que ordena todo lo demás

Los fallos de las últimas versiones no fueron de código: fueron de **fuente de
verdad**. La guarda de idioma miraba el prompt en vez de al usuario. El panel
enseñaba la familia asignada en vez de la que respondió. El README contaba
herramientas de memoria. Naoko diagnosticaba con el resultado de una suite que
ella misma rompía.

En todos: la pieza funcionaba y **el dato de entrada venía del sitio
equivocado**. Ningún test unitario ve eso.

> **Regla para v6:** todo dato que el sistema muestre o sobre el que decida
> debe tener un **origen único y declarado**, y ese origen debe poder
> comprobarse en un test que diga de dónde sale.

---

## 1. Proveedores: medir de verdad, y desbloquear los que exigen navegador

### 1.1 El problema, tal y como se ve hoy

En «Proveedores y latencia medida»:

- 5 de 11 familias salen **«sin verificar»** (deepseek, qwen, claude, glm, auto).
- 2 salen con **«cortacircuitos»** (gpt, llama) — el cortacircuitos abierto
  significa «esta familia ha fallado tanto que la aparto», y aun así gpt es la
  de Melchior.
- La mayoría de candidatos dicen **«sin medir»**. La columna se llama «latencia
  medida» y casi no hay ninguna medida.
- 8 de 13 proveedores rotos lo están por algo que **una sesión de navegador
  resolvería**: `Claude` (cookies), `OpenaiChat` y `Copilot` (fichero `.har`),
  `Cloudflare` y `DeepInfra` (CDP), `LMArena` (auth + nodriver).

### 1.2 Sonda de latencia real, no una tabla escrita a mano

Una tarea programable que, por cada candidato vivo, manda un *prompt canario*
corto y registra: responde / no responde, latencia, y si la respuesta llegó en
el idioma pedido.

El resultado va a la misma telemetría que ya alimenta el p95, así que el orden
de candidatos y la tabla del panel salen **del mismo sitio** — hoy el reparto
sale del catálogo JSON y las latencias de la telemetría, y pueden contradecirse.

- **Se comprueba con:** un test que verifica que ningún candidato con
  `verificada: true` lleva más de N días sin medición, y que el orden mostrado
  coincide con el p95 registrado.
- **Puede salir mal:** sondear cuesta cuota. La sonda debe ser barata (un
  prompt de 5 tokens), espaciada, y cancelable. Si la sonda gasta la cuota que
  necesita el usuario, ha empeorado el sistema.

### 1.3 Cookies de navegador — el «sí, pero controlado»

Pediste que MAGI pueda usar cookies de navegador, con Camoufox o algo
equivalente. Es la decisión más delicada del plan, porque **el sistema tiene
prohibido abrir navegadores** y esa prohibición es una de las cuatro
invariantes que Naoko verifica.

Conviene ser exacto sobre qué prohíbe y por qué. `no_browser.py` no existe
porque los navegadores sean malos: existe porque g4f abría **el Chrome del
usuario, sin avisar, en mitad de una petición**, secuestraba su sesión y a
veces se quedaba colgado. El problema era la apertura **invisible y no
consentida**, no el navegador.

**Propuesta: sustituir la prohibición general por una puerta única, explícita y
auditada.**

```
   g4f pide un navegador
            │
            ▼
   ¿viene por la PUERTA de MAGI?
            │
     ┌──────┴───────┐
     │              │
    NO             SÍ
     │              │
 se bloquea    Camoufox en perfil PROPIO
 y se anota    · headless, aislado
 (como hoy)    · nunca toca tu Chrome ni tu perfil
               · lo lanzas TÚ desde el panel
               · las cookies se guardan cifradas y caducan
               · cada apertura queda en la auditoría firmada
```

Concretamente:

1. **Módulo `magi/core/sesion_web.py`** — única vía autorizada. Lanza Camoufox
   (Firefox endurecido contra fingerprinting, headless, perfil propio bajo el
   directorio de datos de MAGI). Nunca lee el perfil del usuario: eso sería
   exactamente el secuestro que se prohibió.
2. **Cosecha explícita.** Un botón en el panel de proveedores: «Iniciar sesión
   en Claude / OpenAI». Se abre la ventana, **tú** te autenticas, MAGI guarda
   las cookies y cierra. Sin ese acto tuyo, no hay cookies.
3. **Almacén con caducidad.** Cookies cifradas en reposo, con fecha de
   expiración visible en el panel y borrado con un clic. Una cookie de sesión
   es una credencial: tratarla como un fichero de configuración sería
   irresponsable.
4. **`no_browser` sigue vivo** para todo lo demás. La invariante cambia de «no
   se abre ningún navegador» a **«ningún navegador se abre sin que tú lo hayas
   pedido, y todos quedan registrados»**, y Naoko lo dice con esas palabras.
5. **Degradación honesta.** Sin sesión, esos proveedores siguen marcados como
   no disponibles con el motivo — nunca se intenta a medias.

- **Se comprueba con:** un test que confirma que cualquier ruta a un navegador
  que no pase por `sesion_web` sigue bloqueada y anotada; otro que verifica que
  las cookies caducan y se borran; y uno que comprueba que el perfil usado
  **no** es el del usuario.
- **Puede salir mal:** (a) Camoufox pesa y engorda el `.exe` — evaluar
  descargarlo bajo demanda en vez de empaquetarlo; (b) los términos de servicio
  de algunos proveedores prohíben el acceso automatizado, y eso hay que decirlo
  en el panel antes de que inicies sesión, no después; (c) una sesión caducada
  puede colgar una petición: plazo corto y fallo limpio.

### 1.3.bis Los 13 proveedores rotos, uno por uno

«Roto» es hoy una etiqueta escrita a mano que agrupa cosas muy distintas: un
bug de versión de una librería, una cuota que se repone sola y una decisión de
diseño están todas en el mismo cajón. Separadas, **11 de los 13 son
recuperables** y solo 2 lo están por voluntad propia.

| Vía | Proveedores | Qué hace falta |
|---|---|---|
| **A · Adaptador de compatibilidad** | PhindAi, Qwen | Nada de red: es un bug de firma |
| **B · Sesión web headless** | Claude, LMArena, OpenaiChat, Copilot, Cloudflare, DeepInfra | La puerta de 1.3 |
| **C · Reclasificación por sonda** | GeminiPro, MetaAI, Pollinations | Dejar de tratar lo transitorio como permanente |
| **D · Fuera por diseño** | Ollama, GLM | Se quedan fuera, y se dice por qué |

#### A · Adaptador de compatibilidad (2 proveedores, coste bajo)

```
PhindAi : BaseSession.__init__() no acepta 'proxy'
Qwen    : AsyncSession.request() no acepta 'proxy'
```

Esto no es un proveedor caído: es que g4f pasa `proxy=None` a una versión de
`curl_cffi` que ya no lo acepta. Dos proveedores marcados como muertos por un
argumento de más.

Un envoltorio fino que **filtre los argumentos que la firma instalada no
admite** —leyendo la firma con `inspect.signature`, no con una lista escrita a
mano que se quedaría atrás— los revive sin tocar g4f ni fijar versiones.

- **Se comprueba con:** un test que llama al envoltorio con `proxy=` sobre una
  firma que no lo acepta y verifica que pasa igualmente, y otro que confirma
  que un argumento que **sí** existe no se descarta.
- **Puede salir mal:** tragarse un argumento que sí importaba. Por eso se filtra
  por firma real y se registra en debug cada descarte.

#### B · Sesión web headless (6 proveedores) — **puerta construida**

> **Estado:** la puerta está hecha y probada (`magi/core/sesion_web.py`). Lo que
> falta es el motor: instalar Camoufox y escribir la cosecha de cookies por
> proveedor. La arquitectura, el permiso caducable, el almacén de credenciales
> y la integración con `no_browser` están en su sitio y con tests.
>
> Se dejó a propósito sin la dependencia: Camoufox pasa de cien megas y solo
> hace falta para estos seis proveedores. Sin él, `disponible()` dice que no y
> **por qué**, y el resto del sistema funciona igual. Añadirlo al binario es
> una decisión aparte, con su coste en tamaño de descarga.


La puerta de 1.3. Aquí es donde se concentra el rescate: seis proveedores,
entre ellos `Claude` y `OpenaiChat`, que son justo los que pediste priorizar.

Los seis piden lo mismo con nombres distintos: una sesión autenticada.
`Claude` quiere cookies, `OpenaiChat` y `Copilot` un `.har`, `Cloudflare` y
`DeepInfra` una conexión CDP, `LMArena` un fichero de auth. Una única sesión
headless los cubre todos si además **exporta en los tres formatos**: cookies,
`.har` y punto CDP.

#### C · Reclasificación por sonda (3 proveedores)

```
GeminiPro   : responde 429 (cuota agotada)   ← se repone sola
MetaAI      : responde 403 desde esta red    ← depende de dónde estés
Pollinations: responde 402 (pago requerido)  ← puede volver a abrirse
```

Ninguno está roto: los tres están **temporalmente indisponibles**, y el
catálogo los congela como muertos para siempre. Una cuota de 429 se repone en
horas; un 403 depende de la red desde la que se conecta.

La sonda (1.2) los reintenta con espaciado creciente y **el estado lo escribe
ella**, no una etiqueta a mano. El catálogo pasa a decir *cuándo se comprobó por
última vez y con qué resultado*, no *si está roto*.

- **Se comprueba con:** un test que verifica que un candidato con error de cuota
  vuelve a la rotación cuando una medición posterior tiene éxito.
- **Puede salir mal:** martillear un proveedor que devuelve 429 empeora el
  bloqueo. Espaciado exponencial y tope diario por candidato.

#### D · Fuera por diseño (2 proveedores)

- **Ollama** es un motor **local**. Lo prohíbe §I.3 y ahí se queda: meterlo
  cambiaría lo que el proyecto dice ser.
- **GLM** responde con captcha. Resolver captchas automáticamente es saltarse
  una medida de acceso puesta a propósito; no se hace. Queda fuera, con el
  motivo escrito.

Que estos dos sigan fuera **es el resultado correcto**, no una carencia. La
diferencia con hoy es que estarán separados de los once que sí se pueden
recuperar, en vez de mezclados en la misma lista.

### 1.4 Reparto del enjambre por mérito medido

Hoy el reparto (`gpt` / `gemini` / `command`) está escrito en el catálogo. Con
1.2 y 1.3 funcionando, pasa a calcularse desde la latencia media histórica.

**El orden de reparto no es arbitrario, y conviene que quede el porqué:**

| Puesto | Nodo | Motivo |
|---|---|---|
| **1.ª mejor** | **BALTHASAR** | Es el único que **ejecuta para refutar**. Su turno es el más caro en herramientas y el que más veces se repite si falla, así que es donde una familia lenta más daño hace. Y si la refutación llega tarde o incompleta, el debate pierde su parte más valiosa: la que caza los fallos reales. |
| **2.ª mejor** | **CASPER** | Es **quien te habla**. Su síntesis es la respuesta que lees, y además ahora propone y ejecuta para demostrarla. Si tarda, tú esperas mirando la pantalla. |
| **3.ª** | **MELCHIOR** | Su tesis se lanza en 2-3 variantes **en paralelo**, así que el tiempo de pared es el de una sola llamada. Es el nodo que mejor absorbe una familia algo más lenta. |

La restricción de familias distintas se mantiene: es lo que hace que el crítico
tenga sesgos diferentes al proponente, y sin eso el debate es un modelo
hablando solo.

- **Se comprueba con:** el test de diversidad que ya existe, más uno nuevo que
  verifica el orden de asignación por latencia y que las tres están vivas.
- **Puede salir mal:** que el reparto baile en cada arranque y los resultados
  dejen de ser comparables. Se fija por sesión y el cambio se anuncia.

---

## 2. Los tres roles: menos verborrea, más evidencia

El debate hoy produce texto correcto y poco accionable. Tres cambios:

### 2.1 Melchior — propone Y ejecuta, una vez (ya hecho)

Su mensaje único lleva la evidencia de ejecución pegada. Lo que falta: que la
propuesta **declare sus supuestos falsables** en una sección fija, para que
Balthasar tenga a qué disparar en vez de tener que buscarlo.

### 2.2 Balthasar — refutar es ejecutar, no opinar

Los cuatro ejes (corrección, seguridad, rendimiento, mantenibilidad) producen
párrafos. Debería producir **casos**: entrada concreta, salida esperada, salida
real. Una crítica sin caso reproducible pasa a ser una sospecha, y se etiqueta
como tal.

- **Se comprueba con:** un test que exige que al menos un eje traiga evidencia
  ejecutada cuando la propuesta contiene código.

### 2.3 Casper — síntesis con decisión y coste

Hoy arbitra. Debería además decir **qué se descartó y por qué**, y **qué queda
sin verificar**. La quinta regla del proyecto aplicada al veredicto: lo no
comprobado se nombra, no se omite.

### 2.4 Velocidad

Las latencias del log (36-74 s por turno) vienen de candidatos lentos, no de
los prompts. 1.2 y 1.4 son el arreglo real. Además: recortar el contexto que se
arrastra entre rondas — hoy se pega el debate entero y crece cada ronda, que es
también lo que contaminó el idioma.

---

## 3. Naoko: que entienda lo que tú estás viendo

### 3.1 El problema

Su mensaje dice «1 tarea activa, 2 bloqueadas esperando, 4 interrumpidas» con
identificadores como `task_50f418e5`. Es exacto y no se puede accionar: no dices
qué son esas tareas ni qué hacer con ellas.

### 3.2 Qué cambia

- **Nombres, no identificadores.** Cada tarea ya tiene título generado; usarlo.
- **Una frase de estado y una acción.** «*Juego Tetris portable* — el enjambre
  terminó y espera tu «sí». Responde para cerrarla.»
- **Distinguir lo que te toca de lo que le toca al sistema.** Hoy van mezcladas.
- **Que sepa lo que hay en pantalla.** Naoko no conoce la interfaz: qué pestaña
  miras, qué panel está abierto, qué se ve. Con eso puede decir «lo que buscas
  está en la pestaña Coste» en vez de describir datos que ya tienes delante.
- **Diagnóstico bajo demanda, no por defecto.** El detalle técnico completo
  detrás de «ver diagnóstico», no en el primer mensaje.

- **Se comprueba con:** un test que verifica que ningún mensaje de Naoko al
  usuario contiene un identificador crudo cuando existe título.
- **Puede salir mal:** perder precisión al resumir. El detalle no se borra, se
  pliega.

### 3.3 Autoconciencia real

Naoko afirma «las 4 invariantes están OK». Debería poder responder, con datos y
no de memoria: qué versión corre, qué familias están vivas y por qué las otras
no, cuánto tardó el último turno y dónde se fue el tiempo, qué cambió en el
último commit, qué tests están en rojo. Todo eso ya se guarda; nadie lo une.

---

## 4. Gráfico HDC: en qué ronda vamos y qué se decidió

### 4.1 El problema

No dice en qué ronda estás, ni qué concluyó cada ronda. Es un diagrama de
cajas, no una traza.

### 4.2 Qué cambia

```
RONDA 1  ✔ cerrada     Melchior: 3 enfoques · 2 verificados
                       Balthasar: 4 ejes · 2 fallos reales
                       Casper: enfoque B, con reservas de rendimiento
RONDA 2  ● en curso    Melchior ✔ · Balthasar ⟳ · Casper —
```

Una línea por ronda, el veredicto de Casper como resumen, y el estado de cada
nodo en la ronda actual. Lo detallado, al hacer clic.

- **Se comprueba con:** tests de la lógica de resumen como funciones puras, al
  estilo de `lib/latencia.ts`.

---

## 5. Orden de ejecución

| # | Qué | Por qué primero | Riesgo |
|---|---|---|---|
| 1 | Sonda de latencia (1.2) | Sin medir, todo lo demás son suposiciones | bajo |
| 2 | Naoko clara (3.2) | Es lo que lees cada día | bajo |
| 3 | Gráfico HDC (4) | Mismo motivo, y ya hay datos | bajo |
| 4 | Roles (2) | Mejora la calidad del debate | medio |
| 5 | Sesión web (1.3) | Desbloquea claude y compañía | **alto** |
| 6 | Reparto por mérito (1.4) | Necesita 1.2 y 1.3 | medio |

El 5 va tarde a propósito: toca una invariante de seguridad y conviene hacerlo
con el resto estable y con tiempo para probarlo, no en medio de otra cosa.

---

## 6. Lo que este plan NO propone

- **Modelos locales.** Sigue fuera (§I.3). Un motor local cambia el proyecto.
- **Claves de API.** Lo mismo.
- **Abrir tu navegador.** Ni con la puerta de 1.3: perfil propio y aislado.
  Leer tu perfil de Chrome es exactamente el fallo que `no_browser` cerró.
- **Subir el techo de huérfanos.** Baja o se queda.
