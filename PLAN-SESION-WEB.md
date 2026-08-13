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

La causa real del cuelgue de Camoufox sigue **sin determinar**, y eso es lo que
hay que decir hasta saberlo.

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
