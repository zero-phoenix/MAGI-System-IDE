# MEGAPLAN v8 — «demora tanto en funcionar» y «le escribí a Naoko y no me responde»

**Fecha:** 2026-08-20 · **Versión de partida:** v5.7.1 · **Versión de salida:** v5.8.0

---

## 0. La queja, y lo que resultó ser

> «analiza el sistema magi ahora mismo y mira porque demora tanto en
> funcionar, le escribi a naoko y no me responde, verifica si ritsuko tambien
> funciona»

Tres afirmaciones. Las tres se midieron antes de tocar una línea de código, y
el resultado no fue el esperado:

| Afirmación | Lo que se midió | Veredicto |
|---|---|---|
| «Naoko no responde» | Naoko respondió en **10,8 s** por sonda WebSocket directa | **Falso** — responde; no llegaba a pintarse |
| «verifica si Ritsuko funciona» | Ritsuko respondió en **8,1 s** por la misma sonda | **Funciona** |
| «demora tanto en funcionar» | **Cierto**, y por dos causas distintas y sin relación entre sí | **Confirmado ×2** |

Que las dos primeras fueran falsas *como diagnóstico* no significa que el
usuario se equivocara. Escribió a Naoko y no vio respuesta. Eso es un fallo
real. Solo que el fallo no estaba donde parecía.

---

## 1. Causa A — la interfaz se comía un núcleo entero estando parada

### La medición que lo decidió

```
MAGI-IDE-v5.exe (PID 16288), en reposo, sin ninguna tarea corriendo
    100,3 % de un núcleo    (media de 12 s, psutil)

el mismo kernel arrancado solo, sin interfaz, con las 13 tareas rehidratadas
    0 %
```

Un experimento más, decisivo, hecho al matar el proceso:

```
matar SOLO los procesos hijos (el renderizador), dejando el kernel vivo
    -> 1,0 % de un núcleo
    -> puerto 20128 sigue escuchando  (True)
```

Mismo árbol de procesos, mismo kernel, misma base de datos: **muere el
renderizador y el consumo cae de 100,3 % a 1,0 %**. El bucle estaba en React.
No en el enjambre, no en los proveedores, no en el rehidratado.

### La causa exacta

`useMagiSocket` devolvía veintidós funciones nuevas en un objeto nuevo **en
cada render**. Son arrow functions, no `useCallback`. Cualquier `useEffect`
que pusiera una de ellas en su array de dependencias —que es exactamente lo
que el linter de React pide hacer— se volvía a disparar en cada render. Y si
ese efecto llamaba al kernel y guardaba el resultado, el ciclo se cerraba
solo:

```
efecto -> RPC -> respuesta -> setState -> render -> identidad nueva -> efecto -> …
```

Cuatro efectos lo hacían. Uno de ellos, `ProveedoresEnCabecera`, vive en la
cabecera: está montado **siempre**, en todas las pestañas, desde que se abre
la ventana. Por eso el consumo era permanente y no dependía de dónde estuviera
el usuario.

### Por qué esto explica «Naoko no me responde»

Naoko contestaba en 10,8 s —medido— y publicaba `naoko.status: "Pensando
(claude45sonnet)…"` mientras tanto. Los dos eventos llegaban al navegador. Lo
que no había era un hilo de render libre para pintarlos. El usuario veía una
ventana quieta, que es indistinguible de un sistema roto.

### El arreglo

Se arreglaron los cuatro efectos, **y luego se arregló la causa**. Arreglar
efectos uno a uno es jugar al gato y al ratón: el siguiente componente que se
escriba y haga lo que el linter pide vuelve a abrir el agujero.

`useMagiSocket` ahora devuelve `useMemo(() => ({…}), [])`. El objeto y sus
veintidós funciones tienen identidad estable para siempre. Ninguna dependencia
puede volver a cambiar sola.

Congelar la primera versión es correcto y no es un atajo: ninguna de esas
funciones cierra sobre estado que cambie. Todas leen `ws.current` —una ref—
en el momento de llamarse, o `useMagiStore.getState()`, que es de módulo.

De paso, el hook dejó de suscribirse al store entero (`useMagiStore()` sin
selector) y pasó a tres selectores. Antes, **cada línea de terminal** que
llegaba por el socket re-renderizaba App aunque el hook solo necesitara tres
setters que no cambian nunca.

### La red de seguridad

`tests/test_gui_sin_bucles_de_render.py`, tres pruebas:

1. Ninguna función del socket aparece en las dependencias de ningún `useEffect`
   de ningún `.ts`/`.tsx` del proyecto.
2. El efecto de carga de `RitsukoPanel` —el sitio exacto donde ya pasó— tiene
   dependencias vacías.
3. `useMagiSocket` devuelve `useMemo(…, [])` y **las veintidós** funciones van
   dentro. Una sola que se escape por fuera reabre el agujero para esa función.

---

## 2. Causa B — el failover multiplicaba la espera por tres, en silencio

### La medición

`token_ledger` de este equipo, latencia real de llamada lógica:

| Agente | Familia | n | Mediana | p90 | **Máximo** |
|---|---|---:|---:|---:|---:|
| CASPER | gemini | 10 | 44 726 ms | 390 391 ms | **390 391 ms** |
| MELCHIOR | gemini | 35 | 25 000 ms | 172 297 ms | **355 078 ms** |
| MELCHIOR | gpt | 33 | 50 906 ms | 84 359 ms | 138 641 ms |
| MELCHIOR | hf | 32 | 20 828 ms | 182 438 ms | 254 578 ms |
| CASPER | command | 11 | 16 579 ms | 77 297 ms | 89 859 ms |
| BALTHASAR | gemini | 67 | 8 875 ms | 16 422 ms | 33 484 ms |

**390 segundos.** Seis minutos y medio esperando una sola respuesta.

### La causa exacta

`registry.complete` prueba hasta `max_attempts` (3) candidatos, y **cada uno
estrenaba su propio `timeout_s`**. Con el valor por defecto de 150 s que pone
`cloud.generate_text`, el techo de pared de una llamada lógica era
3 × 150 = **450 s**. El máximo medido, 390 s, encaja exactamente con dos
timeouts encadenados más una respuesta lenta.

Nadie lo acotaba porque nadie lo miraba al nivel correcto: cada intento, por
separado, se portaba bien. Había incluso un techo dinámico por proveedor
(`3 × mejor_latencia + 5 s`), pero solo se activa cuando ese proveedor ya tiene
mediciones — y un proveedor nuevo o recién reiniciado no las tiene.

Peor: el reintento por negativa (`_REFUSAL_HINTS`) abría una **segunda** cadena
completa. Techo real: 900 s.

### El arreglo (§E1)

`CompletionRequest.presupuesto_s`: reloj para la **cadena entera**, no para un
intento. Cada candidato recibe lo que queda; cuando no queda, la cadena se
rinde en vez de abrir otro turno de 150 s.

El valor por defecto es **igual a `timeout_s`** (150 s), y esa elección es
deliberada: **ningún candidato dispone de menos tiempo que antes**. Lo único
que desaparece es la multiplicación.

```
techo de pared, una llamada lógica:   450 s  ->  150 s
con reintento por negativa:           900 s  ->  195 s   (150 + 45)
```

El reintento por negativa lleva presupuesto corto (45 s) por una razón
concreta: en ese punto **ya hay una respuesta en la mano**. Esa segunda cadena
solo intenta mejorarla, así que no puede costar lo mismo que conseguirla.

Las sondas quedan exentas. Medir no es producir: el tiempo de una sonda *es* el
dato que se busca, y recortarlo devolvería una medición falsa de lo rápido que
va el sistema.

### La red de seguridad

`tests/test_presupuesto_de_reloj.py`, cinco pruebas. Las dos que importan de
verdad no son la del caso feliz:

- **`test_el_candidato_bueno_no_pierde_su_turno`** — un presupuesto mal puesto
  convierte una mejora de latencia en pérdida de respuestas. Con presupuesto de
  sobra, el candidato lento se agota por su propio techo y el rápido contesta
  igual que siempre.
- **`test_la_capa_de_compatibilidad_pone_el_presupuesto`** — que el mecanismo
  exista no sirve de nada si `generate_text` no lo rellena. Ese es exactamente
  el modo en que este arreglo podría no arreglar nada.

---

## 3. Causa C — la herramienta de diagnóstico ensuciaba lo que medía

### La medición

Estado real de `magi_brain.db` al empezar:

```
total: 23    WAITING_USER_APPROVAL: 14    interrumpida: 7    completed: 2
```

De esas 23, **quince** eran sintéticas: `auditoria-<epoch>` (una por cada pasada
de `scripts/auditar_sistema.py`), más `t-techo` y `auditoria` a secas.

Ninguna la abrió el usuario. Cada una quedaba esperando una aprobación que
nadie iba a dar, el kernel la rehidrataba en cada arranque y la interfaz la
listaba como una conversación pendiente **suya**.

Entre sus conversaciones reales había quince falsas. La lista dejó de decirle
nada — y eso es parte de por qué «le escribí a Naoko y no me responde» se
sintió como se sintió.

### El arreglo

`TaskStore.purgar_sinteticas()` borra las tareas cuyo id empieza por un prefijo
de instrumentación. `auditar_sistema.py` la llama antes de cerrar el kernel, y
el informe anota qué purgó en `huella_purgada`.

Se **borra** en vez de archivar a propósito: archivar la saca de la vista pero
la deja en la tabla, y estas filas no tienen valor histórico — la medición vive
en `artifacts/auditoria.json`, que es donde debe vivir.

Nunca toca una tarea con `bifurcada_de`: si alguien ramificó trabajo real desde
una auditoría, ese trabajo es del usuario.

### La red de seguridad

`tests/test_purga_de_huella.py`, cuatro pruebas. La que importa es
**`test_no_toca_las_conversaciones_del_usuario`**: una purga demasiado ansiosa
es infinitamente peor que la basura que limpia, porque borrar sin avisar el
trabajo de alguien no tiene arreglo. Se comprueba explícitamente que
`task_auditoria_de_seguridad` —que *contiene* el prefijo pero no empieza por
él— sobrevive.

Ejecutada sobre la base real, con copia de seguridad previa:

```
copia: magi_brain.db.bak-1787225494
reanudables antes:  13
purgadas:           15
reanudables después:  0
```

---

## 4. Lo que NO era, y se comprobó

Registrar las hipótesis descartadas vale tanto como registrar las confirmadas:
evita volver a pagarlas.

| Hipótesis | Cómo se descartó |
|---|---|
| «`_rehydrate` re-lanza los bucles de las tareas al arrancar» | Se leyó: solo construye diccionarios. No hay `create_task`. |
| «El kernel se atasca con 13 tareas rehidratadas» | Kernel solo, con esas mismas 13 tareas: **0 % de CPU**. |
| «Naoko está caída» | Sonda WebSocket directa: contestó en **10,8 s**. |
| «Ritsuko no llegó a funcionar» | Sonda: contestó en **8,1 s**. |
| «Naoko no avisa de que está pensando» | Publica `naoko.status: "Pensando (modelo)…"`. El evento salía; nadie lo pintaba. |

---

## 5. Ejecución

| # | Acción | Estado |
|---|---|---|
| A1 | Quitar las funciones del socket de los 4 arrays de dependencias | ✅ |
| A2 | `useMemo(…, [])` en `useMagiSocket` — la causa raíz | ✅ |
| A3 | Selectores en vez del store entero en el hook | ✅ |
| A4 | `test_gui_sin_bucles_de_render.py` (3 pruebas) | ✅ verde |
| B1 | `TaskStore.purgar_sinteticas()` | ✅ |
| B2 | `auditar_sistema.py` recoge su huella | ✅ |
| B3 | `test_purga_de_huella.py` (4 pruebas) | ✅ verde |
| B4 | Purgar la base real, con copia de seguridad | ✅ 15 filas |
| E1 | `presupuesto_s` en `CompletionRequest` + reparto en `registry.complete` | ✅ |
| E2 | `generate_text` fija 150 s; el reintento por negativa, 45 s | ✅ |
| E3 | `test_presupuesto_de_reloj.py` (5 pruebas) | ✅ verde |
| E4 | Ritsuko: sin actividad no es avería (falso `EMPEORA`) | ✅ |
| E5 | `test_ritsuko_sin_actividad.py` (7 pruebas) | ✅ verde |
| V1 | Recompilar interfaz y ejecutable | ✅ |
| V2 | Medir el consumo en reposo del binario nuevo | ✅ **1,1 %** |
| V3 | Suite completa + sonda en caliente contra el exe nuevo | ✅ 1382/0 |
| V4 | Publicar v5.8.0 | ✅ |

### §E4 — encontrado verificando este mismo plan

La sonda contra el binario nuevo destapó un fallo que no estaba en el plan.
Sistema recién arrancado, sin una sola tarea lanzada, y Ritsuko contestó:

```
**Veredicto:** EMPEORA
1. Todos los nodos están mudos: MELCHIOR, BALTHASAR y CASPER…
```

Los tres estaban intactos. `evidencia()["nodos"]["mudos"]` los listaba siempre
que `AGENT_POST` valiera cero, y cero es el valor normal de un sistema que
acaba de arrancar. El auditor recibía «los tres callados» como hecho.

Es el mismo error que ya se corrigió en el canario de deriva de Naoko (C13):
**0 de N no es «falla el 100 %», es «no hay medición»**. Ahora, con cero
actividad, `sin_actividad: true`, `mudos: []`, y la regla escrita en el prompt
para que el modelo no pueda saltársela.

Comprobado en caliente tras recompilar: el veredicto pasó a
`SIN DATOS SUFICIENTES`, citando `nodos.total: 0, nodos.sin_actividad: true`.

---

## 6. Criterio de aceptación — CUMPLIDO

No se daba por bueno hasta cumplir las cuatro, medidas y no supuestas. El
resultado sobre el binario compilado el 2026-08-20 a las 07:00:

| # | Criterio | Medido |
|---|---|---|
| 1 | Consumo en reposo < 10 % de un núcleo | **1,1 %** (partida 100,3 %) |
| 2 | Naoko contesta y se ve | **34,3 s**, «Sí, estoy aquí…» |
| 3 | Ritsuko contesta | **33,3 s**, veredicto `SIN DATOS SUFICIENTES` |
| 4 | Suite entera en verde | **1382 pruebas, 0 fallos, 0 errores** |

Sobre el punto 2: 34,3 s frente a los 10,8 s del primer sondeo. Es varianza
del proveedor gratuito —el modelo tardó ~33 s—, no una regresión. El techo de
cadena es de 150 s y la llamada terminó holgadamente dentro. §E1 no baja la
latencia media, que depende de terceros: elimina la cola de 390 s que nadie
acotaba.

### El criterio original, para el registro

1. **El binario recién compilado consume < 10 % de un núcleo en reposo**
   (partida: 100,3 %).
2. **Naoko contesta por la sonda WebSocket** contra ese binario, y su respuesta
   **se ve en la ventana**.
3. **Ritsuko contesta** por su propio canal.
4. **La suite entera pasa**, incluidas las doce pruebas nuevas.
