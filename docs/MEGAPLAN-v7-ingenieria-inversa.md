# MEGAPLAN v7 — ingeniería inversa de cómo trabajo yo, aplicada a MAGI

**Base:** las pruebas D y E contra la v5.6.0
(`docs/COMPARATIVA-D-E-v5.6.0.md`). El megaplan anterior arregló que el sistema
**mintiera**. Este ataca lo que queda: que **entregue**.

El encargo era hacerme ingeniería inversa a mí mismo. Lo he hecho sobre lo
único honesto que tengo: **lo que se me ve hacer en esta misma sesión**, con
las marcas en el repositorio. No sobre cómo creo que funciono por dentro.

---

## Parte I — Qué hago yo que MAGI no hace

Ocho diferencias observables. Cada una lleva el momento de esta sesión donde
se puede comprobar, porque una introspección sin evidencia es una opinión con
mejor prensa.

### 1. Leo el encargo como un CONTRATO, no como un tema

«Un ping pong de 32 bits a todo color en un exe portable» no es un tema: son
cuatro compromisos separables y comprobables.

| Compromiso | Cómo lo hice comprobable |
|---|---|
| es un juego con reglas | partida a 11 ganando por 2, rebote por punto de impacto |
| **32 bits a todo color** | framebuffer RGBA + `--formato` que verifica la matemática del alfa |
| **exe único portable** | tkinter (stdlib) → 9,0 MB sin SDL ni DLLs externas |
| funciona | `--autotest 200` → 48 fps, código de salida 0 |

MAGI trata el encargo como un tema sobre el que escribir. Por eso escribe
*sobre* el ping pong y no *el* ping pong.

### 2. Decido qué significa «hecho» ANTES de empezar, y lo hago verificable por máquina

No es pulcritud: **yo tampoco veo la pantalla**. Necesito exactamente la misma
evidencia que el usuario. De ahí salen `--autotest` y `--formato`, y de ahí
sale que pueda afirmar «48 fps» y «alfa correcto» en vez de «debería ir bien».

MAGI tiene la misma limitación —no ve la pantalla— y no actúa en consecuencia.

### 3. Busco en mi propia caja de herramientas antes de razonar de memoria

En esta sesión, antes de tocar nada: busqué `analyze_port`, `_leer_decision`,
`es_degradada`, `_check_drift`, los tests existentes. Encontré que
`AgentTurn.degraded` **ya existía** y se tiraba en la frontera — eso no se
deduce pensando, se encuentra mirando.

MAGI: `menciones_a_herramientas: 0` en las cinco pruebas. Tiene un analizador
de portabilidad entre consolas y contestó de memoria una pregunta de
portabilidad entre consolas.

### 4. Escribo el PORQUÉ pegado al arreglo

Cada cambio de este repositorio lleva al lado la medición que lo forzó. No es
estilo documental: es un mecanismo. Quien venga a «simplificar» tiene que leer
primero por qué existe, y eso es lo que impide que el arreglo se deshaga en
seis meses.

### 5. Desconfío de mi propio informe de éxito

Dos veces en esta sesión, con recibo:

- Mi test de alfa falló (99 frente a 100 esperado). **Sospeché de mi
  expectativa, no del código** — y tenía razón el código: alfa 128 pesa 127/255. Lo dejé escrito en el fichero.
- El primer informe de Ritsuko traía como veredicto el mensaje de error del
  proveedor. Era **exactamente el fallo que Ritsuko existe para denunciar**, cometido por mí. Lo dije y lo arreglé con dos tests.

MAGI firmaba `APPROVED` sobre sus propios timeouts. Ya no; pero sigue sin
contrastar sus afirmaciones contra su registro salvo en el caso de C12.

### 6. Cuando el último paso falla, conservo el trabajo

Ya está en el sistema (C2). Lo incluyo porque es el mismo instinto: lo hecho
no se tira porque lo siguiente falle.

### 7. Acoto el trabajo: pocas pasadas, bien dirigidas

Mi proceso para el pong de 32 bits fue: **escribir una vez → probar → arreglar
una cosa → probar**. Cuatro pasos, uno de ellos porque mi propio test me cazó.

MAGI para lo mismo: **12 llamadas al modelo, 3 enfoques en paralelo, 2 rondas
de debate, 177 s**, y sin `.exe` al final. Tres propuestas que nadie ejecuta
valen menos que una que sí.

### 8. Contesto TODAS las partes del enunciado

La prueba D pedía explícitamente «el orden de trabajo que minimiza el riesgo de
abandono». La respuesta de MAGI —buena en lo técnico— **no menciona el abandono
ni una vez**. Yo enumero las sub-preguntas y las tacho.

---

## Parte II — Los bloques

### D1. Contrato del encargo, extraído y comprobado ⟵ **empezar por aquí**

**Qué se hace:** al admitir la petición, se extraen sus compromisos a una lista
explícita (`contrato = [...]`), se le enseña al usuario en una línea, y **antes
de entregar** se comprueba uno a uno. Lo que no se pueda comprobar se marca
`sin comprobar`, no se da por hecho.

Es la generalización de C4: hoy el contrato solo distingue «pide artefacto» de
«no pide». Con esto, «32 bits», «portable» y «un único fichero» son cada uno
una casilla.

**Se comprueba:** test con el enunciado del ping pong que exige tres casillas
(color, portabilidad, artefacto) y que la entrega las cite.

### D2. `APPROVED` no sobrevive a un contrato incumplido

**Evidencia:** prueba E entregó `**Decisión Técnica:** APPROVED` **y**
`[INCOMPLETO] ... no se ha generado ningún artefacto` en el mismo mensaje. El
contrato dispara el aviso pero no toca el veredicto: los dos mecanismos no se
hablan.

**Qué se hace:** si `_contrato_de_entregable` devuelve algo, la decisión pasa a
`INCOMPLETO` y el encabezado lo dice. Cinco líneas en el orquestador.

### D3. Cerrar el lazo: escribir el fichero, compilarlo y entregarlo

**Evidencia:** ocho bloques de código escritos, cero llamadas a
`build_project_exe`, cero a `entregar_artefacto`, cero artefactos. La cadena
existe entera —`studio/tools.py`, `packager.py`, `entrega.py` con el guardián
GUI real— y nadie la invoca.

**Qué se hace:** cuando el contrato pide artefacto y hay bloques verificados,
**el orquestador cierra el lazo él mismo** en vez de esperar a que un modelo se
acuerde: escribe los bloques, llama al packager y entrega. El modelo propone;
la máquina construye. Es la diferencia entre pedirle a un LLM que se acuerde y
garantizarlo.

**Se comprueba:** encargo `build` con un agente falso que devuelve un bloque
Python válido; el test exige `swarm.artefacto_listo` y un fichero en disco.

### D4. Recuperación de herramientas, no recordatorio en el prompt

**Evidencia:** C5 puso en el prompt «usa tus herramientas» y el resultado
siguió siendo `menciones_a_herramientas: 0` en dos pruebas más. **Pedirlo no
funciona.**

**Qué se hace:** antes de la primera llamada, el orquestador busca en el
catálogo por el enunciado y **ejecuta** lo que claramente aplica —para una
pregunta de portabilidad entre consolas, `analyze_port(origen, destino)`— y
mete el resultado en el prompt como evidencia ya obtenida. El modelo no tiene
que acordarse: se lo encuentra puesto.

**Se comprueba:** el enunciado NDS→PSP tiene que producir al menos una llamada
a herramienta registrada.

### D5. Cobertura del enunciado antes de entregar

**Evidencia:** la parte «minimiza el riesgo de abandono» se perdió sin que
nada lo notara.

**Qué se hace:** se parte el enunciado en sub-peticiones (por oraciones
imperativas y signos de interrogación) y, antes de publicar, se comprueba que
la síntesis toca cada una. Lo que falte se le pide a Casper en una única
llamada dirigida, o se dice que no se ha contestado.

### D6. Menos enfoques, más ciclos de verificación

**Evidencia:** 3 enfoques en paralelo, 27.753 caracteres producidos, 24,7 %
entregado, y ningún artefacto. Mi proceso: 1 propuesta y 3 verificaciones.

**Qué se hace:** invertir el reparto de cuota. `deep` pasa de 3-4 variantes a
**2**, y lo ahorrado se gasta en un segundo ciclo de *verificar → arreglar* con
la evidencia de la ejecución delante. La calidad no sale de tener tres textos;
sale de haber ejecutado el primero.

**Se comprueba:** la auditoría, con el ratio de entrega y el artefacto como
métrica.

### D7. Ritsuko tiene que ver lo que importa

**Evidencia:** dijo «SIN DATOS SUFICIENTES» teniendo delante un encargo de
producto cerrado sin artefacto. No lo vio porque su evidencia no incluye las
métricas de entrega.

**Qué se hace:** `ritsuko.evidencia()` incorpora `calidad_de_entrega`
—producido/entregado, bloques, artefacto, `[INCOMPLETO]`— y las tareas
atascadas que ya sabe detectar. Y su prompt cambia una regla: **con evidencia
de un incumplimiento, el veredicto no puede ser «sin datos»**.

### D8. Elegir candidato por latencia también en la puerta de herramientas (B5)

**Evidencia:** `MELCHIOR iteración 1 lenta (80,2 s con g4f-gpt)`, `CASPER
(78,8 s con g4f-hf)`. El hedge ya cubre, pero se sigue eligiendo mal el
primero.

### D9. Higiene: las tareas no se acumulan abiertas

**Evidencia:** Ritsuko encontró 8 tareas en `WAITING_USER_APPROVAL` y 1
interrumpida. Una tarea sin dueño desde hace días no está esperando a nadie:
está ocupando sitio y ensuciando el diagnóstico.

**Qué se hace:** caducidad por tiempo con aviso, y `task.list` marcando las
huérfanas.

---

## Orden

1. **D2** — cinco líneas, y elimina la última contradicción visible.
2. **D3** — es *el* cambio: convierte propuestas en entregas.
3. **D1 + D5** — el contrato completo y la cobertura del enunciado.
4. **D4** — usar lo que se sabe, ejecutándolo en vez de pidiéndolo.
5. **D6 + D8** — menos texto, más ejecución; y dejar de empezar por el lento.
6. **D7 + D9** — que la auditora vea lo importante y que la casa esté limpia.

## Cómo se sabrá que funcionó

Misma tarea, `scripts/auditar_sistema.py --con-ritsuko`:

| Métrica | v5.5.2 | **v5.6.0** | Objetivo v7 |
|---|---|---|---|
| `APPROVED` sobre degradado | 3/3 | 0/2 | 0 |
| Ratio entregado/producido | 0,8-1,9 % | 12-25 % | ≥ 50 % |
| Artefacto en encargo de producto | no | no (avisado) | **sí** |
| Herramientas propias usadas | 0 | 0 | ≥ 1 |
| Partes del enunciado sin contestar | — | 1 de 3 | 0 |
| Tiempo del encargo de producto | 657 s | 177 s | ≤ 150 s |
