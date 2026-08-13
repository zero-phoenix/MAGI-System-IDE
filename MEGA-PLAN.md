# MEGA PLAN — reexamen del plan y revisión integral de MAGI

**Fecha:** 2026-08-13 · **Base:** 1007 tests, 192 módulos, 29 589 líneas en `magi/`

Todo lo que sigue está **medido hoy**, con fecha y con el comando que lo produjo.
Donde no hay medida, se dice que no la hay. Esa regla es la única forma de que
un documento así no sea una colección de opiniones con formato de plan.

---

## Parte 0 · Resumen para leer de pie

Cuatro frases, y las cuatro incómodas:

1. **El plan de las cookies apuntaba al sitio equivocado.** La familia `claude`
   —la que más querías— nunca necesitó cookies. `Perplexity`, que ya estaba en
   el catálogo, sirve `claude45sonnet` y `claude40opus` sin cuenta, sin claves
   y sin navegador. Lo bloqueaba un fallo de g4f de dos líneas. **Ya está
   arreglado y medido: 3,7 s.**
2. **La familia `gpt` de MELCHIOR estaba muerta**, y su único superviviente
   responde en chino. Esa —y no el prompt— es la causa raíz de que el enjambre
   contestara en otro idioma.
3. **El catálogo mentía en cinco sitios.** Cinco familias marcadas «verificadas»
   estaban rotas; una marcada «imposible» funcionaba.
4. **`sesion_web.py` rinde 0 de 6 proveedores** bajo tus reglas, y eso hay que
   decirlo entero antes de invertir una hora más en él.

---

## Parte 0.bis · Segunda tanda del 13-ago: idiomas, barrido y Camoufox

### Cuatro idiomas de entrada, uno de salida

Los proveedores pueden contestar en **español, inglés, portugués o italiano**;
**el chino, nunca**. Y todo lo que llega a la interfaz va **en español**,
incluida Naoko sin excepción.

El cambio no es una concesión, es más barato: antes una respuesta perfecta en
inglés se trataba como fallo y disparaba una **regeneración completa** en otra
familia — la latencia entera otra vez, con riesgo de fallar igual y de devolver
un análisis distinto. Ahora se **traduce**: una llamada corta, mismas
conclusiones, y el usuario lee español igualmente.

Naoko además deja de deducir el idioma: informa del estado del sistema, y eso
lo lee siempre la misma persona. Su lista de rotación estaba encabezada por
`gpt-4o` —la familia cuyo único candidato vivo responde en chino— y terminaba
en `llama-3.1-70b`, muerta desde que Groq pide créditos.

### El barrido: 50 candidatos medidos, 7 vivos

| proveedor | modelo | medido | idioma |
|---|---|---|---|
| CohereForAI | `command-a-03-2025` | **1 809 ms** | es |
| Perplexity | `claude40opus` | **2 832 ms** | es |
| Perplexity | `claude45sonnet` | **3 723 ms** | es |
| Perplexity | `grok` | 4 279 ms | es |
| Gemini | `gemini-3.5-flash` | 4 877 ms | es |
| Perplexity | `auto` | 5 964 ms | es |
| Yqcloud | `gpt-4` | 11 795 ms | es/**zh** |
| HuggingSpace | `command-a` | 16 535 ms | es |

**Perplexity expone 46 modelos** —`gpt5`, `o3`, `o4mini`, `grok4`, `mistral`,
`llama_x_large`, `r1`, toda la línea Claude— así que un solo proveedor que
funciona cubre casi todas las familias. El catálogo pasa de 11 familias a 12,
con una nueva (`razonamiento`) que no existía.

**Descartados del sistema, con motivo medido** (ya no son deuda, son historia):
Claude, OpenaiChat, Copilot y LMArena (exigen tu cuenta); Cloudflare, DeepInfra
y Pi (`BrowserBlocked` en 2-5 ms); GLM (captcha); Groq y Pollinations (402);
GeminiPro (429); MetaAI (403); PhindAi (403); Qwen (`success=false`);
CopilotApp (WS 460); Ollama (local). WeWordle se queda sin descartar: su 429 es
un límite de ritmo y puede volver.

### Dos fallos nuevos, uno mío y uno de MAGI

**1. Abrí una ventana.** El script del barrido llamaba a los parches de
compatibilidad pero **no instalaba `no_browser`**. Al llegar a Cloudflare, g4f
hizo `CDPSession(headless=False)` y apareció una ventana de Chrome «AI
Playground» en tu máquina. La cerré, y el arreglo no es acordarse: hay un
guardián (`test_scripts_no_esquivan_el_cortafuegos`) que lee con AST todos los
`scripts/` y exige que el cortafuegos se instale **antes** de importar g4f. El
sistema tenía la puerta bien cerrada; se coló por la de al lado.

**2. `'tud.'` habría llegado a la interfaz.** Tras unas veinte peticiones,
Perplexity empezó a devolver cuatro caracteres —el final de una frase— para
cualquier modelo y cualquier pregunta. El fallo de g4f es de g4f; lo nuestro es
que **MAGI lo daba por bueno**: eso habría aparecido como la antítesis de
BALTHASAR, con su latencia y su nombre de proveedor. Ahora `complete()` rechaza
lo inservible y el failover que ya existía prueba al siguiente candidato. *Un
fallo que se disfraza de éxito no se detecta nunca.*

### Camoufox: verificado, sin ventanas

| comprobación | resultado |
|---|---|
| paquete | `camoufox 152.0.4-beta.28` |
| navegador descargado | sí |
| socket local | conecta (1 ms) |
| arranque headless | **arranca en 9 958 ms** |
| ventanas antes / después | **idénticas** |
| procesos residuales | **0** |

Y un defecto que solo aparece midiendo: `_prueba_arranque()` devolvió
`ok=False, "no respondió en 10s"` **en la misma ejecución** en la que el
diagnóstico midió 9 958 ms. El umbral estaba en 10,0 s y el arranque tarda
9,96: el veredicto dependía de 40 milisegundos. Subido a 25 s —sigue avisando
casi cuatro veces antes que los 93 s del fallo original—. *Un umbral puesto a
ojo que cae justo encima del valor real no es un umbral, es una moneda al aire.*

---

# PARTE I · Reexamen del plan: los errores que tenía

## §1. El error de fondo: comprobar que el muro existe antes de escalarlo

El plan entero (`PLAN-SESION-WEB.md`, `magi/core/sesion_web.py`, 812 líneas,
tres ficheros de tests) partía de esta línea del catálogo:

```
"Claude":  "exige el paquete browser_cookie3 y cookies de un navegador"
"LMArena": "exige fichero de autenticación y nodriver"
```

De ahí salió: cosechar cookies con un Firefox endurecido sin ventana, un
permiso con caducidad de 30 minutos, un almacén con expiración a 14 días, un
importador de tres formatos, una comprobación previa de 10 s, un diagnóstico
ejecutable. Todo correcto. Todo bien probado. Todo apuntando a un problema que
no era el problema.

Lo que nadie hizo en ningún momento fue esta pregunta:

> ¿Hay algún proveedor que YA funciona y que sirva modelos Claude?

La respuesta se obtiene en once líneas de Python:

```python
for p in g4f.Provider.__providers__:
    if p.working and not p.needs_auth:
        if any('claude' in str(m).lower() for m in (p.models or [])):
            print(p.__name__, [m for m in p.models if 'claude' in str(m).lower()])
```

```
Perplexity ['claude2', 'claude37sonnetthinking', 'claude40opus',
            'claude40opusthinking', 'claude41opusthinking', 'claude45sonnet']
```

`Perplexity` estaba **en el mismo fichero, dos familias más arriba**, marcado
como verificado desde el 6 de agosto.

### Por qué no funcionaba, y por qué eso escondía la solución

```
AttributeError: 'JsonConversation' object has no attribute 'thread_title'
```

En `g4f/Provider/Perplexity.py`:

```python
L383    if 'thread_title' in json_data:              # solo SI el servidor lo manda
L384        conversation.thread_title = json_data['thread_title']
...
L448    yield Sources([{"name": f"Perplexity - {conversation.thread_title}", ...
```

El servidor dejó de mandar ese campo. La línea 448 lo lee siempre. **Y lo lee
al final, después de haber recibido la respuesta completa**: el proveedor
contesta en 4 segundos y se pierde todo al adjuntar la metadata de las fuentes.

Desde fuera eso se ve *exactamente* igual que «Perplexity está roto». Ahí está
la trampa: **«roto» y «no lo hemos mirado bien» son indistinguibles desde el
otro lado de una excepción.**

### El arreglo — `magi/core/providers/compat_g4f.py`

Valores por defecto a nivel de clase. No se toca g4f, no se pisa nada: si el
servidor manda el campo, la instancia lo asigna encima y gana.

```python
ATRIBUTOS_POR_DEFECTO = {"thread_title": "", "thread_url_slug": ""}
```

**Medido después del parche**, mismo prompt:

| modelo                   | latencia | resultado |
|--------------------------|----------|-----------|
| `claude45sonnet`         | 3 723 ms | correcto  |
| `claude40opus`           | 2 832 ms | correcto  |
| `claude37sonnetthinking` | —        | disponible|

Y con una pregunta técnica real («¿por qué un mutex no basta para evitar un
interbloqueo?»), `claude45sonnet` en 4 209 ms:

> «porque un mutex solo garantiza exclusión mutua para una sección crítica,
> pero no evita ciclos de espera entre varios recursos si múltiples hilos
> solicitan recursos en diferentes órdenes.»

Correcto, en castellano, en cuatro segundos. Gratis, sin cuenta, sin cookies.

> **La lección, que es la parte reutilizable:** antes de construir
> infraestructura para saltar un muro, gasta cinco minutos en comprobar que el
> muro existe. El coste de no hacerlo aquí fue un módulo de 812 líneas
> apuntando al problema equivocado.

---

## §2. Tu restricción nueva mata cuatro de los seis. Hay que decirlo

> *«recuerda que solo se usan ia de nube sin keys y sin ia local y sin
> logearme con ninguna cuenta en ningun lugar»*

`sesion_web.py` divide sus seis proveedores en dos caminos:

| camino | proveedores | qué necesitan | ¿viable con tu regla? |
|---|---|---|---|
| `COSECHA_IMPORTADA` | Claude, OpenaiChat, Copilot, LMArena | **TU CUENTA** | **No. Nunca.** |
| `COSECHA_AUTOMATICA` | Cloudflare, DeepInfra | sesión anónima | ver §3 |

Los cuatro de arriba no están «pendientes»: son **imposibles por diseño**. El
camino de importar cookies existía precisamente para que tú iniciaras sesión en
tu navegador y exportaras el fichero. Con «sin logearme en ningún lugar», ese
camino no tiene destino.

**Esto no es una pérdida.** Los cuatro servían modelos que ahora tenemos por
otra vía: Claude vía Perplexity (§1), GPT vía la familia `gpt` cuando reviva.

## §3. Cloudflare y DeepInfra: las cookies nunca fueron el artefacto

Leí el fuente de g4f en vez de suponer:

- **`Cloudflare.py`** usa `CDPSession(headless=False)` y habla por
  `wss://playground.ai.cloudflare.com/agents/playground/...`. Lo que necesita es
  una **conexión WebSocket autenticada**, no una cookie. Cosechar cookies para
  Cloudflare es cosechar el objeto equivocado.
- **`DeepInfra.py`** necesita un **token Turnstile** en la cabecera
  `X-DeepInfra-Turnstile`. Turnstile es un captcha. Y `GLM` ya está declarado
  fuera de alcance por, literalmente, *«responde con captcha»*.

O sea: se aplicaron dos criterios distintos al mismo obstáculo. Si el captcha
de GLM lo deja fuera, el de DeepInfra también.

## §4. Veredicto sobre `sesion_web.py`: 0 de 6, y qué hacer con él

| proveedor | veredicto | por qué |
|---|---|---|
| Claude | **imposible** | tu cuenta (regla del usuario) |
| OpenaiChat | **imposible** | tu cuenta |
| Copilot | **imposible** | tu cuenta |
| LMArena | **imposible** | tu cuenta |
| DeepInfra | **fuera de alcance** | captcha, igual que GLM |
| Cloudflare | **abierto** | WebSocket sin navegador: sin medir |

**Rinde entre 0 y 1 proveedor.** Lo honesto es dejar de venderlo como
«desbloqueador de proveedores».

**Pero no se tira**, y no por apego: tres de sus piezas son valiosas por sí
mismas y sobreviven al cambio de propósito.

1. **El permiso con caducidad y `no_browser`** — la invariante §I.3 («ninguna
   ventana salvo la interfaz de MAGI») necesita una única grieta auditada. Eso
   es lo que es, y funciona.
2. **`diagnostico()`** — mide en vez de opinar. Nació de un error mío (afirmé
   que FortiClient era la causa; al medirlo, los sockets locales conectaban en
   0,0 s). Es la herramienta más reutilizable del módulo.
3. **`importar_cookies()`** — sigue valiendo el día que decidas *tú* pegar un
   fichero. No se ejecuta solo, no pide nada, no miente.

**Acción:** reescribir la cabecera del módulo y el panel para que digan lo que
hace de verdad. Cero código nuevo. **Prioridad: alta, coste: bajo.**

---

# PARTE II · Revisión integral del sistema

## §5. Radiografía de proveedores — 2026-08-13, medida uno a uno

Mismo prompt, misma red, salida en UTF-8 (ver §9 sobre por qué eso importa):

| familia | proveedor | latencia | estado |
|---|---|---|---|
| **claude** | Perplexity `claude45sonnet` | **3 723 ms** | ✅ el mejor modelo disponible |
| **command** | CohereForAI `command-a` | **3 576 ms** | ✅ el más fiable de los rápidos |
| **gemini** | Gemini `gemini-3.5-flash` | **4 879 ms** | ✅ castellano impecable |
| **hf** | HuggingSpace | 4 656 ms | ✅ responde |
| **perplexity** | Perplexity `auto` | 5 860 ms | ✅ responde |
| gpt | Yqcloud `gpt-4` | 9 661 ms | ⚠️ **responde en chino** |
| gpt | CopilotApp | 689 ms | ❌ `WSServerHandshakeError 460` |
| gpt | WeWordle | 603 ms | ❌ `HTTP 429` |
| gpt | Pollinations | 5 372 ms | ❌ `HTTP 402` |
| llama | Groq | 1 542 ms | ❌ `402 No cake credits` |
| deepseek | PhindAi | 3 010 ms | ❌ `403 Security` |
| qwen | Qwen | 5 223 ms | ❌ `success=false` |
| auto | AnyProvider | 1 682 ms | ❌ cascada de los anteriores |

## §6. La causa raíz del idioma — no era el prompt

Tu queja original fue: *«las ia ponen sus conclusiones en un idioma que no es
español»*. Se atacó con un guardián de idioma en `agents.py`
(`MAX_REINTENTOS_IDIOMA = 2`, `lang_usuario` fijado una vez). Eso funciona, y
está bien que exista.

Pero mira la tabla: **MELCHIOR usaba la familia `gpt`, y el único candidato
vivo de `gpt` es Yqcloud, un servicio chino que contesta en chino.** Medido:

```
'di: funciona'  →  '看起来你输入的内容里「funciona」是西班牙语…'
```

Los reintentos trataban el síntoma —y encima costaban una llamada extra por
ronda—. La enfermedad era el reparto de familias.

### El reparto nuevo, por mérito medido

Aplicando tus reglas (*la mejor para BALTHASAR, la segunda para CASPER, cada
una en familia distinta*):

| agente | rol | familia | modelo | medido |
|---|---|---|---|---|
| **BALTHASAR** | antítesis | `claude` | Claude Sonnet 4.5 | 3 723 ms |
| **CASPER** | síntesis / árbitro | `gemini` | Gemini 3.5 Flash | 4 879 ms |
| **MELCHIOR** | tesis + ejecución | `command` | command-a | 3 576 ms |

MELCHIOR se lleva el más rápido y fiable a propósito: es quien **propone Y
ejecuta en el mismo turno** y quien menos puede permitirse esperar.

`gpt` sale del enjambre **pese a ser prioritaria para ti**, y el motivo se
escribe entero en el catálogo. Vuelve en cuanto CopilotApp o WeWordle revivan;
la sonda lo detectará sola.

## §7. El catálogo mentía en cinco sitios

`verificada: True` con fecha del 6 de agosto no dice nada del 13. Estos
servicios son gratuitos y se caen sin avisar.

| familia | decía | mide hoy |
|---|---|---|
| `llama` | verificada, 922 ms | Groq `402` |
| `auto` | verificada, 1 671 ms | cascada rota |
| `deepseek` | «revivida por compat_curl» | `403 Security` |
| `qwen` | «revivida por compat_curl» | `success=false` |
| `claude` | «imposible» | **funciona, 3,7 s** |

Sobre `deepseek`/`qwen`: la nota decía *«ya no revienta ≠ responde»* — el
matiz estaba escrito y aun así se les subió a la lista. Un aviso que no cambia
lo que hace el código es decoración.

**Esto es exactamente para lo que existe `sonda.py`.** Está construida y
probada; lo que falta es que **corra sola y que el reparto la obedezca**. Ver
Fase 2.

### Un defecto de diseño que lo facilitaba

El mismo dato vivía en dos sitios (constantes de Python + JSON), sincronizados
a mano y vigilados por un test. Dos copias editadas a mano son una divergencia
con fecha, no un riesgo. **Corregido hoy:** `scripts/sincronizar_catalogo.py`
genera el JSON *desde* las constantes y conserva lo que solo el JSON sabe
(latencias, fechas, notas).

## §8. El defecto que se repitió cinco veces, y el mecanismo que lo cierra

Cinco tests míos seguidos pasaron aquí y fallaron en el CI por el mismo motivo:
preguntaban a la máquina si había un navegador Camoufox descargado. Aquí sí
(100 MB bajados a mano); en el runner no.

**La quinta la escribí en el mismo commit en el que documentaba que esto se
repite.** Ahí se acaba el argumento de «más cuidado».

El CI las cazó las cinco veces — **seis minutos después de empujar**, cuando ya
no estás mirando. Un guardián que avisa tarde entrena a ignorarlo.

### El mecanismo — `tests/conftest.py`

Las funciones que **salen** de la máquina dejan de tener respuesta por defecto
durante los tests. No devuelven «no» (eso solo movería el fallo de sitio): **se
niegan a contestar** y explican qué escribir.

```python
_AMBIENTALES = ("disponible", "_prueba_arranque",
                "_lanzar_headless", "_cosechar_sin_navegador")
```

El guardián va en la **frontera**, no dentro: `puede_abrir()` es lógica pura
sobre `disponible()` y debe poder probarse de verdad. Quien quiera cruzar la
frontera lo dice en voz alta con `@pytest.mark.frontera`.

**Lo que encontró en sus primeros cinco minutos de vida:**

- **8 tests más** que leían la máquina sin saberlo.
- **Uno salía a la red de verdad** en cada corrida.
- **Tres tenían aserciones bajo un `if`**: en esta máquina la rama no entraba y
  **no comprobaban nada, en silencio, pareciendo verdes**. Ahora comprueban las
  dos ramas, simuladas.
- **Un bug real del producto** (§9).
- La suite de sesión bajó de ~10 s a **12,8 s en total** al dejar de arrancar
  navegadores de verdad.

Barrido AST de las 1007 pruebas buscando la misma forma: **una sola** candidata
más (`test_packager.py:92`), y al mirarla es un `if/else` con aserciones en
ambas ramas. Falso positivo de mi propio escáner. **El defecto está contenido.**

## §9. cp1252, cuarta aparición: el instrumento de medida estaba roto

Historial del mismo fallo en este sistema:

1. Una respuesta entera del enjambre perdida por un acento en consola cp1252
   (de ahí `magi/core/consola.py`).
2. `diagnostico_legible()` con `✓` → `UnicodeEncodeError` al imprimirlo.
3. **Hoy, en el producto:** el arreglo de (2) solo cubría *el texto que escribí
   yo*. `detalle` sale de `str(e)` de cualquier excepción, y ahí cabe cualquier
   cosa. La función documentaba con esmero una garantía que no daba en el único
   sitio por donde podía romperse. **Lo destapó el guardián de §8**, cuyo
   mensaje lleva la palabra «MÁQUINA». Arreglado con `_imprimible()`, que
   **pliega** acentos (`conexión`→`conexion`) en vez de borrarlos.
4. **Hoy, en mi instrumento de medida:** mi sonda manual dio
   `Yqcloud → FALLO UnicodeEncodeError`. Falso. El error lo lanzaba **mi propio
   `print`** al volcar una respuesta con un emoji. Yqcloud funciona. **Estuve a
   punto de registrar un proveedor roto que no lo está.**

> La medida (4) es la más importante de las cuatro. Un plan que se apoya en
> mediciones hereda los bugs del medidor. `sonda.py` guarda en SQLite y no
> imprime, así que no tiene este fallo — pero eso hay que **comprobarlo**, no
> suponerlo (Fase 2.3).

## §10. Deuda estructural — lo que se ve al mirar el conjunto

| observación | dato | riesgo |
|---|---|---|
| `naoko.py` | **1 385 líneas** | la GUI tiene tope de 900; el núcleo no tiene ninguno |
| `agents.py` | 991 líneas | idem |
| `kernel.py` | 901 líneas | idem |
| Cobertura `magi/core` | ~79 %, **no bloqueante** | una caída no rompe nada |
| `ruff` completo | `--exit-zero` | la deuda se cuenta, no se frena |
| `pyright` | `continue-on-error` | tipado parcial e invisible |
| Huérfanos | 107 (techo) | trinquete puesto; no baja solo |
| GUI | 7 ficheros de test / 5 469 líneas | mucho menos denso que Python |
| `VENTANA_CONTEXTO` | 120 000 caracteres, **global** | ningún proveedor publica el suyo |

Lo que **falta implementar** (no está roto: no existe):

- **La sonda no corre sola.** Está construida y probada, pero nadie la dispara
  periódicamente ni el reparto la obedece en frío.
- **No hay medida de calidad, solo de latencia.** Yqcloud responde rápido y en
  chino: por latencia gana, por utilidad es inservible. El canario
  (`«responde únicamente con la palabra: funciona»`) además **penaliza a
  Perplexity**, que lo interpreta como búsqueda y contesta «No entiendo la
  consulta» — el mejor proveedor del sistema puntúa mal por culpa del examen.
- **Nada mide el debate.** No hay forma de saber si tres rondas son mejores que
  dos, ni si BALTHASAR aporta algo distinto de MELCHIOR.
- **Naoko no ve el panel de proveedores.** Supervisa el enjambre pero no el
  sustrato que lo hace posible.

---

# PARTE III · El mega plan

Ordenado por **valor medido ÷ coste**. Cada fase lleva criterio de aceptación
comprobable — si no se puede comprobar, no es un criterio.

## Fase 0 · HECHO HOY

| # | qué | estado |
|---|---|---|
| 0.1 | `compat_g4f.py` — desbloquea la familia `claude` | ✅ 5 tests |
| 0.2 | Reparto por mérito medido | ✅ catálogo + respaldo |
| 0.3 | Catálogo corregido con 13 medidas fechadas | ✅ |
| 0.4 | `sincronizar_catalogo.py` — el JSON se deriva | ✅ |
| 0.5 | Guardián de frontera en `conftest.py` | ✅ +9 tests arreglados |
| 0.6 | `_imprimible()` — la promesa del diagnóstico, cumplida | ✅ |
| 0.7 | Quinta ocurrencia del defecto de entorno | ✅ CI en verde |

## Fase 1 · Decir la verdad sobre `sesion_web` — ✅ HECHO

1. Reescribir cabecera del módulo y `PLAN-SESION-WEB.md` con §2–§4.
2. El panel deja de decir «pendiente» para los cuatro imposibles: dice
   **«requiere iniciar sesión — excluido por diseño»**.
3. Reetiquetar el módulo: *puerta auditada + diagnóstico*, no desbloqueador.

**Aceptación:** un test comprueba que el panel no promete nada de los cuatro.

## Fase 2 · Que la sonda mande — ✅ HECHO

2.1 **Disparo automático.** Al arrancar (si la última medida > 24 h) y bajo
    demanda. Presupuesto duro: `MAX_POR_DIA = 24`, `CONCURRENCIA = 4`.

2.2 **El reparto obedece a la sonda en frío.** `ORDEN_DE_MERITO`
    (BALTHASAR, CASPER, MELCHIOR) sobre `media_historica()` — la media de las
    medias diarias que ya está implementada. Familias distintas garantizadas.

2.3 **Auditar el medidor** (lección §9): un test que fuerza una respuesta con
    emoji y acentos y comprueba que la sonda la registra **sin lanzar**.

2.4 **Canario nuevo, y esto no es cosmético.** El actual penaliza a Perplexity.
    Sustituir por una pregunta técnica breve con respuesta verificable
    —*«¿en qué se diferencia un mutex de un semáforo? Una frase.»*— y puntuar
    tres ejes: responde / **idioma correcto** / menciona el concepto clave.
    Yqcloud fallaría el eje de idioma y dejaría de parecer bueno por ser rápido.

**Aceptación:** desconectar `command` a mano y ver que el reparto se recompone
solo tras la siguiente pasada, sin tocar el JSON.

## Fase 3 · Revivir `gpt`, que es prioritaria para ti — 3 h

| candidato | fallo medido | vía |
|---|---|---|
| CopilotApp | `WSServerHandshakeError 460` | ¿cabecera de origen? mirar el fuente como en §1 |
| WeWordle | `HTTP 429` | transitorio: reintento con espera y remedida |
| Pollinations | `HTTP 402` | de pago: fuera, y que lo diga |
| Yqcloud | vivo, **chino** | forzar idioma en el prompt del sistema y **medirlo** |

Y el barrido que faltaba: **enumerar los 37 proveedores `working ∧ ¬needs_auth`
y medirlos todos**, no solo los 13 del catálogo. Así se encontró Claude.

**Aceptación:** `gpt` con ≥1 candidato que responde en castellano en <5 s, o
una línea en el catálogo diciendo por qué no lo hay.

## Fase 4 · Medir la calidad del debate — ✅ HECHO

- **Divergencia entre agentes**: distancia léxica entre las conclusiones de
  MELCHIOR y BALTHASAR por ronda. Si tiende a 0, el debate es teatro.
- **Rendimiento por ronda**: ¿cambió la conclusión de la ronda *n* a la *n+1*?
  Responde empíricamente cuántas rondas valen la pena.
- Ambas al gráfico HDC, que ya agrupa por rondas (`rondas.ts`, 17 tests).

**Aceptación:** un debate real produce las dos métricas y se ven en la GUI.

## Fase 5 · Naoko ve el sustrato — ✅ HECHO

`_info_sonda()` y `_info_sesion_web()` ya existen en el kernel. Falta que Naoko
los **use**: que sepa decir *«MELCHIOR va lento porque su familia perdió al
candidato rápido hace dos días»* en vez de *«MELCHIOR va lento»*.

**Aceptación:** con una familia degradada a mano, Naoko nombra la causa.

## Fase 6 · Frenar la deuda, sin drama — continuo

0. **Congelar el catálogo dentro de los tests** — el hermano del guardián de
   §8, y ya tiene tres instancias medidas hoy:
   `test_una_familia_agotada_lo_dice_en_vez_de_fingir` usaba `claude` como
   ejemplo de familia muerta y se puso rojo **porque `claude` revivió**;
   `test_el_orden_pone_delante_al_candidato_mas_rapido` y
   `test_la_latencia_es_una_media_movil` usaban los dos primeros candidatos de
   `gpt`, que hoy están rotos, así que `_ordered()` los filtraba y el test del
   *orden* fallaba sin que el orden hubiera cambiado.

   Los tres están arreglados con familias sintéticas, pero eso es disciplina
   otra vez. El mecanismo: durante los tests, `FAMILY_SPECS` y `ROTOS` valen
   un catálogo de laboratorio **fijo**, salvo con una marca `catalogo_real`
   para los pocos tests que sí deben leer el de verdad (p. ej.
   «toda familia verificada tiene candidatos»).

   *Un test que se rompe cuando un proveedor mejora está mal escrito.*
   Coste estimado: 2 h y unos 10 tests que tocar.

1. Tope de líneas para `magi/core/**` como el de la GUI, con techo actual y
   trinquete (igual que huérfanos: no baja solo, pero no sube).
2. Cobertura bloqueante a partir del 79 % medido, subiendo 1 punto por release.
3. `ruff` completo a bloqueante **por carpeta**, empezando por
   `magi/core/providers/`.
4. `VENTANA_CONTEXTO` por familia en cuanto la sonda mida el truncado real.

---

## Parte IV · Lo que la ejecución del plan encontró

Ejecutar un plan es la mejor forma de auditarlo. Cinco cosas que solo
aparecieron al hacerlo:

**1. `@pytest.mark.timeout(300)` no hacía nada.** El plugin `pytest-timeout`
no estaba instalado, así que pytest registraba la marca como desconocida y
seguía. Medido: la suite pasó de 533 s a **quedarse colgada indefinidamente**
en `test_build_tetris_executable`, sin que nada la matara, ni en local ni en el
CI. *Una marca que documenta una garantía inexistente es peor que no tenerla,
porque se confía en ella.* Ahora hay plazo global de 120 s y la marca funciona.

**2. La sonda estaba escrita contra un interfaz que no existía.** No era que
faltara el disparador: `medir_candidato` llamaba a
`llm.generate(..., proveedor=, modelo=)` y `FreeCloudLLM.generate` no acepta
esos argumentos — elige él dentro de la familia. **No había con qué
dispararla.** Y el detalle importa: medir «lo que la familia elija» habría dado
siempre la latencia del que respondió, nunca la del que falla. El panel diría
que todo va bien mientras medio catálogo está muerto, que es exactamente lo que
pasó. Ahora existe `LlmDeSonda`, que mide un candidato CONCRETO.

**3. El canario suspendía al mejor proveedor.** `Responde únicamente con la
palabra: funciona` hacía que Perplexity —un buscador por dentro— contestara «No
entiendo la consulta». Con una pregunta técnica real responde bien en 4,2 s. El
examen medía la capacidad de obedecer una orden artificial, no la de servir
para lo que este sistema hace.

**4. Mi umbral de divergencia estaba puesto a ojo, y mal.** Lo fijé en 0,25
«porque suena a poco». Al escribir los tests con ejemplos concretos: una
paráfrasis casi literal da **0,44** y un desacuerdo real **1,00**. Con 0,25 no
se detectaba ni el eco más descarado. Recalibrado a 0,55 con los dos valores
medidos escritos al lado — y con la advertencia de que dos ejemplos a mano son
poca evidencia y habrá que recalibrarlo con debates reales.

**5. `naoko.py` tiene 1 520 líneas.** La interfaz lleva tope de 900 desde hace
tiempo y me cazó dos veces, con razón. El núcleo no tenía ninguno: el fichero
más grande es **un 69 % mayor que el límite que se le exige a la GUI**, y nadie
lo había notado porque nada lo miraba. Ahora hay trinquete por fichero: no baja
solo, pero no sube.

---

## Los tres principios que este documento deja escritos

1. **Comprueba que el muro existe antes de escalarlo.** Un módulo de 812 líneas
   se construyó para saltar un muro que tenía una puerta al lado (§1).
2. **El mecanismo, no la disciplina.** Cinco repeticiones del mismo defecto —la
   quinta mientras lo documentaba— cerradas por veinte líneas en `conftest.py`
   que lo hacen imposible (§8).
3. **Duda de tu instrumento antes que del mundo.** Casi registro un proveedor
   roto porque mi `print` no sabía escribir un emoji (§9).
