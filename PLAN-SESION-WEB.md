# Plan: la sesión web que se colgaba 93 segundos

## 0. Primero, una corrección

Escribí que la causa era **FortiClient interceptando la tubería local de
Playwright**. Lo dije con seguridad y **no lo había comprobado**: lo deduje de
ver FortiClient en la lista de procesos. Eso es exactamente lo que el proyecto
llama «no he podido comprobarlo» disfrazado de «está bien».

Lo he medido. Tres resultados, y los tres desmienten o reencuadran esa
explicación:

| Prueba | Resultado |
|---|---|
| Socket local `127.0.0.1` | **conecta en 0,0 s** |
| `curl_cffi` a Cloudflare | **HTTP 200 en 0,2 s**, sin navegador |
| `curl_cffi` a DeepInfra | **HTTP 200 en 0,7 s**, sin navegador |

**Los sockets locales funcionan.** Si un agente de seguridad estuviera cortando
la tubería de Playwright, lo más probable es que esta prueba también fallara.
Mi atribución era una conjetura con aspecto de diagnóstico.

### Y el diagnóstico me desmintió una segunda vez

Nada más existir la herramienta de §3, la ejecuté. Esto es lo que salió:

```
  [ok] paquete camoufox                 instalado              (2287 ms)
  [ok] navegador descargado             152.0.4-beta.28          (87 ms)
  [ok] socket local 127.0.0.1           conecta                   (1 ms)
  [ok] via sin navegador (curl_cffi)    responde                (428 ms)
  [ok] arranque headless                arranca en 9581 ms     (9583 ms)
```

**El navegador arranca. En 9,6 segundos, sin problema.**

Así que no solo era falso que FortiClient cortara la tubería: era falso que el
arranque fallara. Lo que se agota es **cargar la página o resolver su
desafío**, que es otra cosa y está en otro sitio.

El mensaje de error seguía diciendo «suele ser un agente de seguridad» — es
decir, repetía la conjetura ya desmentida, dentro del propio arreglo que la
corregía. Ya no: ahora describe lo que se sabe (arrancó, la página no cargó) y
apunta al diagnóstico para el resto.

La lección no es que me equivocara. Es que **una conjetura escrita en un
mensaje de error sobrevive a la corrección del código**, porque nadie vuelve a
leer los mensajes. Por eso la herramienta tenía que existir.

---

## 1. El giro: puede que el navegador sobre

El dato importante no es por qué falla Camoufox. Es que **los dos sitios que
supuestamente exigían navegador contestan HTTP 200 en menos de un segundo con
`curl_cffi`**, que ya es dependencia del sistema.

`curl_cffi` imita la huella TLS y HTTP/2 de un Chrome real
(`impersonate="chrome"`). Para buena parte de las protecciones anti-bot, eso es
suficiente: lo que miran primero es el apretón de manos TLS, no si hay un
navegador de verdad detrás.

Que g4f diga «su única vía es CDPSession» describe **cómo lo implementó g4f**,
no lo que el servidor exige.

### Orden de intentos, del más barato al más caro

```
1. curl_cffi con huella de navegador     0,2 s   ·  ya instalado
        │ ¿bastó?  → hecho
        ▼ no
2. Camoufox headless                     ~10 s   ·  ~100 MB descargados
        │ ¿bastó?  → hecho
        ▼ no
3. se dice que no se pudo, con el motivo de cada intento
```

Hoy se empieza por el 2, que es el caro y el que falla. Invertirlo convierte un
fallo de 93 segundos en un éxito de 0,2 en el caso normal.

- **Se comprueba con:** un test que verifica que el camino sin navegador se
  intenta **primero**, y que el navegador solo entra si el primero no bastó.
- **Puede salir mal:** que `curl_cffi` devuelva 200 con una página de desafío
  en vez de la real. Un 200 no es un éxito: hay que mirar si la respuesta trae
  lo que se buscaba, igual que se hace con los proveedores.

---

## 1.bis «Responden 200 pero no dan cookies» — porque las cookies nunca fueron el artefacto

Dije que Cloudflare y DeepInfra respondían 200 sin entregar cookies y lo dejé
ahí, como un hecho raro. No lo es. Fui a leer **qué necesita g4f de verdad** de
cada uno, en vez de seguir suponiendo que eran cookies:

```python
# g4f/Provider/Cloudflare.py
session = CDPSession(headless=False)
#   ...y dentro de la página, en JavaScript:
#   const wsUrl = `wss://playground.ai.cloudflare.com/agents/playground/
#                  ${agentId}?_pk=${pk}&model=${modelStr}`;

# g4f/Provider/DeepInfra.py
session = SyncCDPSession(headless=False)      # "Turnstile token retrieval"
headers["X-DeepInfra-Turnstile"] = token
base_url = "https://api.deepinfra.com/v1/openai"
```

**Ninguno de los dos lee una sola cookie.** Lo que necesitan es otra cosa:

| Proveedor | Artefacto real | Qué es |
|---|---|---|
| **DeepInfra** | un **token Turnstile** | se manda en la cabecera `X-DeepInfra-Turnstile` y luego la inferencia va por una API normal |
| **Cloudflare** | un **contexto JS con WebSocket** | la conversación viaja por `wss://…/agents/playground/…`, abierto desde dentro de la página |

Es decir: **por muy bien que cosechara cookies, esos dos nunca iban a
funcionar**. Estaba puliendo la llave equivocada. Que respondan 200 y no den
cookies no es una anomalía: es lo esperable cuando lo que hace falta no son
cookies.

### Cómo se resuelve de verdad cada uno

**DeepInfra — cosechar el TOKEN, no cookies.** El token es lo único que hace
falta del navegador; después la inferencia es una llamada HTTPS corriente a una
API compatible con OpenAI. Así que:

1. Se obtiene el token una vez, headless.
2. Se guarda **con su caducidad** (los Turnstile duran minutos, no días — muy
   distinto de una cookie de sesión, y guardarlo con la caducidad de una cookie
   sería guardarlo mal).
3. Todas las peticiones siguientes van por HTTPS, sin navegador.

El almacén ya existe; lo que cambia es **qué** se guarda y **cuánto** vale.

**Cloudflare — hablar el WebSocket directamente, sin navegador.** La URL está
a la vista en el propio código de g4f. Si `agentId` y `pk` se pueden sacar de la
página con una petición HTTP normal, MAGI puede abrir ese WebSocket por su
cuenta con `websockets`, que **ya es dependencia** del sistema. Sería el mejor
resultado posible: cero navegador, cero Turnstile, cero descarga de 100 MB.

Y si no se pueden sacar sin ejecutar JavaScript, entonces hace falta el
navegador — y se dice, en vez de dejar al proveedor en una lista de rotos con
un motivo equivocado.

- **Se comprueba con:** para DeepInfra, que una petición con el token cacheado
  no abra ningún navegador; para Cloudflare, un test que intente extraer
  `agentId`/`pk` por HTTP y declare el resultado.
- **Puede salir mal:** un token Turnstile caducado da un error de autorización
  que parece «el proveedor está caído». Hay que distinguirlo por su código y
  renovar en vez de marcar el proveedor como roto — el mismo error de
  clasificación que ya congeló trece proveedores.

### Y el nombre, que estaba mal

Se llama «cosecha de cookies» y lo que se cosecha son **credenciales de
sesión**: unas veces cookies, otras un token, otras un fichero `.har`. El
nombre estrecho es parte de por qué apunté a la llave equivocada.

---

## 2. Saber en 5 segundos, no en 93

Aunque el navegador siga haciendo falta a veces, 93 segundos para descubrir que
no arranca es el sistema pareciendo colgado.

**Comprobación previa**: antes de la cosecha completa, un arranque de prueba
con plazo de 10 s y sin navegar a ninguna parte. Si el navegador no responde en
ese margen, no va a responder después.

- **Se comprueba con:** un test que mide que el fallo total no pasa de ~15 s.
- **Puede salir mal:** una máquina lenta de verdad donde 10 s sean pocos. El
  plazo se declara como constante ajustable, no se esconde en el código.

---

## 3. Averiguar QUÉ falla, en vez de suponerlo

La lección de la sección 0, convertida en herramienta: un diagnóstico que el
usuario pueda ejecutar y que diga **qué** falla, no qué me parece a mí.

```
Sesión web — diagnóstico
  ✓ paquete camoufox instalado         0,1 s
  ✓ navegador descargado (152.0.4)
  ✓ socket local 127.0.0.1             0,0 s
  ✗ arranque headless                  agotó 10 s
  ✓ curl_cffi con huella de navegador  HTTP 200 en 0,2 s

  → la vía sin navegador funciona; la sesión no hace falta hoy
```

Cada línea es una comprobación real y separada. Con eso, la próxima vez que
algo no vaya, el motivo se lee en vez de deducirse — y nadie tiene que creerse
la conjetura de nadie.

- **Se comprueba con:** un test de que cada línea sale de una medición y no de
  un valor por defecto.
- **Puede salir mal:** que el diagnóstico tarde tanto como el fallo. Cada
  comprobación con su plazo, y las caras al final.

---

## 4. Lo que ya está resuelto y no se toca

- **Cero navegadores huérfanos.** El proceso hijo con plazo propio funciona: al
  matarlo muere el navegador. Verificado — 0 procesos tras el fallo.
- **Ninguna ventana.** Verificado con vigilancia de procesos durante una
  cosecha real: `MainWindowTitle` vacío en los dos procesos de Camoufox.
- **La puerta cerrada por defecto.** Sin permiso explícito y vigente no se abre
  nada.

---

## 5. Orden

| # | Qué | Por qué | Riesgo |
|---|---|---|---|
| 1 | Vía sin navegador primero (§1) | Convierte 93 s de fallo en 0,2 s de éxito | bajo |
| 2 | Comprobación previa de 10 s (§2) | Que el fallo, cuando toque, sea rápido | bajo |
| 3 | Diagnóstico ejecutable (§3) | Que no vuelva a haber conjeturas | bajo |

Ninguno toca la puerta ni el permiso: eso está probado y funciona.

---

## 6. Lo que este plan NO promete

- **No promete que Camoufox vaya a funcionar en esta máquina.** No sé por qué
  falla, y hasta saberlo no voy a decir que lo arreglo.
- **No promete saltarse protecciones anti-bot.** Si un servidor exige un
  navegador de verdad y lo comprueba bien, no lo tendrá, y se dirá.
- **No vuelve a culpar a FortiClient.** Puede seguir siendo la causa; lo que no
  puede es darse por buena sin medirla.
