# v5.8.0 — «demora tanto en funcionar» y «no me responde»

El usuario reportó tres cosas. Se midieron las tres antes de tocar código, y
dos resultaron ser síntomas de un problema que estaba en otro sitio.

## Lo medido

| Reporte | Medición | Realidad |
|---|---|---|
| «le escribí a Naoko y no me responde» | Naoko contestó en **10,8 s** por sonda WebSocket | Responde. No llegaba a pintarse. |
| «verifica si Ritsuko funciona» | Contestó en **8,1 s** | Funciona. |
| «demora tanto en funcionar» | Confirmado, **por dos causas sin relación** | Ambas arregladas. |

## A — La interfaz se comía un núcleo entero estando parada

```
MAGI-IDE-v5.exe en reposo, sin tareas          100,3 %  de un núcleo
el mismo kernel arrancado solo, sin interfaz     0,0 %
matar solo el renderizador, kernel vivo          1,0 %   (puerto 20128 sigue OK)
```

Mismo árbol de procesos, mismo kernel: muere el renderizador y el consumo cae
de 100,3 % a 1,0 %. El bucle estaba en React.

`useMagiSocket` devolvía veintidós funciones nuevas en cada render. Cualquier
`useEffect` con una de ellas en sus dependencias —lo que el linter de React
pide— se disparaba en cada render, y si guardaba estado, el ciclo se cerraba
solo. Uno de los cuatro culpables vivía en la cabecera, montada siempre: por
eso el consumo era permanente.

Naoko contestaba y publicaba `naoko.status: "Pensando…"`. Los eventos llegaban
al navegador. Lo que no había era un hilo de render libre para pintarlos.

**Arreglo:** los cuatro efectos, y después la causa —`useMemo(() => ({…}), [])`
en el hook, que congela las veintidós identidades para siempre. Arreglar
efectos uno a uno es jugar al gato y al ratón; el siguiente componente que se
escriba reabre el agujero. El hook además dejó de suscribirse al store entero.

**Resultado medido sobre el binario nuevo: 1,1 % de un núcleo en reposo.**

## B — El failover multiplicaba la espera por tres, en silencio

`token_ledger` de este equipo:

| Agente / familia | n | Mediana | Máximo |
|---|---:|---:|---:|
| CASPER / gemini | 10 | 44 726 ms | **390 391 ms** |
| MELCHIOR / gemini | 35 | 25 000 ms | 355 078 ms |
| MELCHIOR / gpt | 33 | 50 906 ms | 138 641 ms |

390 segundos en una sola llamada. `registry.complete` prueba hasta tres
candidatos y **cada uno estrenaba su propio `timeout_s`** de 150 s: techo real
de 450 s, y 900 s si se disparaba el reintento por negativa.

**Arreglo (§E1):** `CompletionRequest.presupuesto_s` acota la **cadena entera**.
Cada candidato recibe lo que queda. El valor por defecto es igual a `timeout_s`,
así que **ningún candidato dispone de menos tiempo que antes** — lo único que
desaparece es la multiplicación.

```
450 s  ->  150 s
900 s  ->  195 s   (con reintento por negativa, que va a 45 s: ya hay
                    una respuesta en la mano y no puede costar lo mismo
                    que conseguirla)
```

Las sondas quedan exentas: el tiempo de una sonda *es* el dato que se busca.

## C — La herramienta de diagnóstico ensuciaba lo que medía

```
total: 23   WAITING_USER_APPROVAL: 14   interrumpida: 7
```

Quince de esas filas eran sintéticas: `auditoria-<epoch>`, una por cada pasada
de `scripts/auditar_sistema.py`. Ninguna la abrió el usuario. Todas se
rehidrataban en cada arranque y aparecían en su lista de conversaciones.

**Arreglo:** `TaskStore.purgar_sinteticas()`, llamada por el arnés antes de
cerrar. Nunca toca una tarea con `bifurcada_de`. Purgadas 15 sobre la base
real, con copia de seguridad previa.

## D — Ritsuko daba una alarma falsa sobre un sistema intacto

Encontrado verificando este mismo release. Binario recién arrancado, sin una
sola tarea lanzada:

> **Veredicto:** EMPEORA
> 1. **Todos los nodos están mudos**: MELCHIOR, BALTHASAR y CASPER…

Los tres estaban perfectamente. `mudos` los listaba siempre que `AGENT_POST`
valiera cero, y cero es el valor normal de un sistema recién arrancado.

Mismo error que ya se corrigió en el canario de deriva de Naoko (C13): **0 de N
no es «falla el 100 %», es «no hay medición»**.

**Arreglo (§E4):** con cero actividad, `sin_actividad: true` y `mudos: []`; y la
regla escrita en el prompt para que el modelo no pueda saltársela. Una alarma
falsa sobre un sistema sano entrena al usuario a ignorar al auditor, y entonces
deja de servir el día que tenga razón.

## Pruebas nuevas

| Fichero | n | Qué fija |
|---|---:|---|
| `test_gui_sin_bucles_de_render.py` | 3 | Ninguna función del socket en dependencias; el hook devuelve `useMemo(…, [])` con las 22 dentro |
| `test_presupuesto_de_reloj.py` | 5 | La cadena respeta el techo, y **el candidato bueno no pierde su turno** |
| `test_purga_de_huella.py` | 4 | Se borra lo sintético y **no se toca nada del usuario** |
| `test_ritsuko_sin_actividad.py` | 7 | Sin actividad no se acusa a nadie, **con actividad el nodo callado sí se señala** |

En los cuatro casos la prueba que importa no es la del caso feliz, sino la que
impide que el arreglo se convierta en un daño nuevo.

Además: `test_sin_huerfanos.py` fija ahora la codificación en los dos extremos
del `subprocess`. Fallaba solo por lanzar la suite con `PYTHONIOENCODING=utf-8`,
con el código que audita perfectamente sano — un test que depende del entorno
de quien lo lanza enseña a ignorar los fallos rojos.

## Verificación

Todo medido sobre el binario recién compilado, no supuesto:

- **Consumo en reposo: 1,1 % de un núcleo** (partida: 100,3 %). Criterio de
  aceptación era < 10 %.
- **Naoko contesta** por sonda WebSocket: 34,3 s («Sí, estoy aquí. ¿En qué
  puedo ayudarte?»).
- **Ritsuko contesta**: 33,3 s, y ahora con el veredicto correcto —
  `SIN DATOS SUFICIENTES`, citando `nodos.total: 0, nodos.sin_actividad: true`,
  donde antes firmaba `EMPEORA`.
- **Suite completa: 1382 pruebas, 0 fallos, 0 errores, 1 omitida, 254 s.**

Una nota honesta sobre la latencia de Naoko: 34,3 s aquí frente a los 10,8 s
del primer sondeo. La diferencia es varianza del proveedor gratuito —el modelo
tardó ~33 s en contestar—, no una regresión: el techo de cadena es de 150 s y
la llamada terminó holgadamente dentro. Lo que §E1 elimina no es la latencia
media, que depende de terceros, sino la cola: los 390 s que nadie acotaba.
