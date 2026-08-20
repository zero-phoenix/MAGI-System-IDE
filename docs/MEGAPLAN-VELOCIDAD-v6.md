# MEGAPLAN v6 — que el sistema vaya rápido y entregue lo que promete

> **Segunda tanda (2026-08-20).** A las fases de velocidad se suman los
> bloques **C1-C10**, que salen de dos pruebas nuevas: una pregunta compleja y
> un encargo de producto, contrastadas con la respuesta y el ejecutable que
> haría yo. El detalle está en `docs/COMPARATIVA-MAGI-vs-claude.md`.
>
> Resumen de lo que enseñaron: el enjambre **razona bien** —la crítica de
> Balthasar cazó tres errores técnicos reales y coincidió con mi análisis— y
> **entrega mal**: en las dos pruebas el usuario recibió 252 caracteres de
> aviso de timeout firmados como `APPROVED`, con 33.000 caracteres de trabajo
> bueno tirados a la basura y, en la prueba del `.exe`, ningún ejecutable.
>
> Si solo se pudiera hacer una cosa de todo este documento, sería **C1**.

Base de todo lo que sigue: la auditoría de `docs/INFORME-AUDITORIA-v5.5.2.md`.
**206 s de pared, 98 % esperando al proveedor, 16 llamadas para sumar dos
números, factor de solape 1,4×.**

De ahí sale la única estrategia posible, y también lo que NO hay que hacer:

> No se optimiza Python. Se quitan llamadas, se acortan las que quedan y se
> solapan mejor. Todo lo demás es mover 4 segundos de 206.

Cada bloque lleva **qué se gana** (estimado sobre lo medido) y **cómo se
comprueba**, porque un plan sin forma de verificarlo es una lista de deseos.

---

## Fase 1 — Quitar llamadas (la más barata, la que más devuelve)

### B1. Verificar la propuesta como UN módulo, no como bloques sueltos
**Problema:** §3.1 del informe. `ModuleNotFoundError: No module named 'suma'`
fuerza un rebuild entero por un error que no es del modelo.
**Qué se hace:** `ProposalVerifier` une los bloques del mismo lenguaje antes de
ejecutar —igual que `entrega._unir_bloques()`, que ya existe y ya funciona— y
solo cae al modo por-bloque si el conjunto no compila.
**Se gana:** un ciclo de rebuild ≈ 4 llamadas ≈ **60-80 s** en la tarea mínima.
**Se comprueba:** test con propuesta de dos bloques (función + test) que hoy
falla y debe pasar; y la auditoría vuelve a correr sin `rebuild 1/2`.

### B2. Cortar el turno cuando ya hay respuesta buena
**Problema:** 14 completions para una tarea trivial. El bucle de herramientas
gasta iteraciones confirmando lo que ya tiene.
**Qué se hace:** en `run_agent`, si una iteración no pide herramientas y el
texto ya verifica, se termina. Y `max_iters` pasa a depender del motor: `fast`
no necesita 10.
**Se gana:** 2-4 llamadas por turno de Melchior ≈ **40-70 s**.
**Se comprueba:** contador de iteraciones por turno en la auditoría, antes y
después.

### B3. Caché de propuesta por (tarea, ronda, rama)
**Problema:** un rebuild regenera variantes que ya se habían generado.
**Qué se hace:** cachear la respuesta por hash del prompt dentro de la misma
tarea. Ya existe caché de traducción (`idioma.traduccion_cacheada`); es el
mismo mecanismo, otro nivel.
**Se gana:** todo el rebuild cuando el fallo estaba en una sola variante.

---

## Fase 2 — Acortar las llamadas que queden

### B4. Hedge también en la puerta de las herramientas
**Problema:** §2 del informe. Las 14 llamadas más lentas van por
`ProviderRegistry.complete`, que **no cubre** una llamada lenta con un segundo
candidato. El hedge existe y funciona, pero solo en la otra puerta.
**Qué se hace:** `run_agent` pide la completion con la misma política de
cobertura que `generate`: pasados `hedge_tras_s`, se lanza el siguiente
candidato y gana el primero que conteste.
**Se gana:** la cola de latencia. Con media de 19,2 s y candidatos sanos entre
2 y 6 s, cubrir a los 4 s debería bajar la media a **8-10 s**: ~**40 % del
tiempo total**.
**Cuidado:** cubrir multiplica el gasto de cuota. Va con el presupuesto por
tarea delante, y con `hedge=False` cuando la rama ya tiene redundancia
estructural (lo que la v5.5.2 hizo bien y no hay que romper).

### B5. Elegir por latencia medida también en el bucle de herramientas
**Problema:** la sonda mide y `ProviderRegistry` reparte por mérito… en la
puerta de `generate`. `run_agent` coge el candidato del catálogo.
**Qué se hace:** una sola política de selección, consultada desde las dos
puertas.
**Se gana:** dejar de mandar el turno largo al proveedor lento.

### B6. Presupuesto de tiempo por turno, no solo por tarea
**Problema:** `iteration_timeout_s = 150 s`. Una iteración puede comerse sola
tres cuartas partes del presupuesto de pared de la tarea.
**Qué se hace:** el timeout por iteración se deriva del presupuesto restante de
la tarea, no de una constante.

---

## Fase 3 — Solapar de verdad

### B7. Llevar el factor de solape de 1,4× a 2,5×
**Problema:** 294 s de espera acumulada en 206 s de pared. Las variantes de
Melchior y los ejes de Balthasar deberían ir en paralelo y no lo están del todo.
**Qué se hace:** medir dónde se serializa (el candado de `_despachar` es
sospechoso: serializa el despacho entero, no solo la decisión de enrutado) y
reducir la sección crítica a lo que de verdad comparte estado.
**Se gana:** con 2,5× y las fases 1 y 2 aplicadas, la tarea de referencia baja
de 206 s a **60-80 s**.
**Se comprueba:** el propio informe de auditoría: `suma(segundos) / pared`.

---

## Fase 4 — Que medir no enferme al paciente

### B8. La sonda y la deriva no corren con una tarea viva
**Problema:** §3.3. Dos familias declaradas «a la deriva» justo después de una
tarea real, con 0/3 canarios. El sistema se diagnostica solo, con la cuota que
acaba de gastar.
**Qué se hace:** la sonda y `_check_drift` esperan a que no haya tareas en
vuelo, y un 429 o un rate-limit **no cuenta como deriva**: se anota como «no
concluyente». Un canario que falla por cuota no dice nada del modelo.

### B9. Arreglar el silencio de la tarea reanudada
**Problema:** §3.2. Rondas agotadas + reanudación = mudez permanente.
**Qué se hace:** al reanudar, si `round > max_rounds`, o se amplía el margen o
se le dice al usuario que esa tarea está cerrada y se abre una nueva. Lo que no
puede es no contestar.
**Se comprueba:** test que reanuda una tarea con las rondas agotadas y exige
respuesta en el bus.

### B10. Limpiar el ruido de arranque
`AASLoader` (§3.5) y el intento de abrir navegador (§3.6). Ninguno cuesta
segundos; los dos cuestan credibilidad, que es lo que hace que un aviso de
verdad se lea.

---

## Orden recomendado

1. **B1** — el mejor ratio de todo el plan: un test y una llamada a una función
   que ya existe, contra 60-80 s.
2. **B4** — el mayor ahorro absoluto, con el presupuesto puesto delante.
3. **B9 y B8** — dos fallos que el usuario nota (silencio y falsas alarmas).
4. **B2, B5, B7** — el resto del tiempo.
5. **B3, B6, B10** — pulido.

## Cómo se mide si el plan funcionó

`python scripts/auditar_sistema.py` antes y después, misma tarea y mismo motor.
Tres números y ninguna interpretación:

| Métrica | Hoy | Objetivo v6 |
|---|---|---|
| Pared de la tarea de referencia | 206 s | ≤ 80 s |
| Llamadas al modelo | 16 | ≤ 8 |
| Media por llamada | 19,2 s | ≤ 10 s |
| Factor de solape | 1,4× | ≥ 2,5× |
| Rebuilds por tarea trivial | 1 | 0 |


---

# Fase C — que lo que llega al usuario valga lo que costó

Todo lo de abajo sale de las pruebas A y B del 2026-08-20
(`docs/COMPARATIVA-MAGI-vs-claude.md`). Las fases 1-4 hacen el sistema rápido;
esta lo hace **fiable**, que es lo que decide si alguien lo usa dos veces.

## C1. `APPROVED` deja de ser lo que sale por defecto  ⟵ **empezar por aquí**

**Evidencia:** las dos pruebas terminaron con
`**Decisión Técnica:** APPROVED` seguido de un aviso de timeout. Casper no
recibió respuesta del modelo y aun así el veredicto salió aprobado.

**Qué se hace:** el veredicto se construye desde la respuesta del árbitro, y si
no hay respuesta el estado es `SIN ARBITRAJE`, nunca `APPROVED`. Un turno
degradado no puede producir un visto bueno, en ninguna rama.

**Cómo se comprueba:** test que simula el timeout del árbitro y exige que el
evento final NO contenga `APPROVED`.

**Por qué es lo primero:** es la diferencia entre un sistema que se equivoca y
un sistema que miente. Todo lo demás de este documento asume que cuando MAGI
dice «aprobado» es porque alguien lo leyó.

## C2. Si el último paso falla, se entrega lo penúltimo

**Evidencia:** 30.866 chars de tesis + 2.522 de crítica producidos y pagados;
252 chars entregados. El trabajo estaba hecho.

**Qué se hace:** ante un fallo del árbitro, el usuario recibe la mejor variante
verificada más la crítica, con una cabecera honesta: «sin arbitraje final, esto
es lo que hay y por qué». Degradar es legítimo; desaparecer no.

**Cómo se comprueba:** mismo test de C1, exigiendo que el mensaje final
contenga la propuesta.

## C3. El prompt del árbitro crece con el fan-out; el timeout no

**Evidencia:** 3 variantes → 30.866 chars → el árbitro muere a los 150 s. En la
prueba B, 21 completions y el mismo final.

**Qué se hace:** dos cosas, y las dos son necesarias:
1. Al árbitro le llega **la variante elegida y la crítica**, no las tres
   variantes enteras. Arbitrar no es releerlo todo.
2. El timeout por iteración se calcula desde el tamaño del prompt y el
   presupuesto restante, en vez de ser la constante `150.0`.

**Se gana:** además de dejar de morir, menos tokens por llamada en el paso más
caro de la cadena.

## C4. Un encargo de producto se cierra con el producto

**Evidencia:** «haz una réplica de Tetris en un .exe portable» → **0** llamadas
a `entregar_artefacto`, **1** bloque de código en toda la conversación, y una
especificación redactada en pasado («se implementó… se empaquetó…») de algo que
no existía.

**Qué se hace:** cuando la intención es `build`, el turno tiene **contrato de
entregable**: no puede cerrarse sin (a) código ejecutable, (b) verificación que
lo arranque de verdad y (c) artefacto entregado. Si falta cualquiera de las
tres, el estado es `INCOMPLETO` con el motivo, jamás `APPROVED`.

**Cómo se comprueba:** test de extremo a extremo con un encargo `build` cuyo
agente devuelve solo prosa: debe terminar en `INCOMPLETO`.

## C5. El sistema tiene que usar lo que sabe

**Evidencia:** pregunta de portabilidad PSP→Vita. MAGI tiene `analyze_port`,
`console_profile` y `compare_consoles` —un analizador subsistema a subsistema
escrito para justo eso— y los usó **cero veces**. Contestó de memoria.

**Qué se hace:**
1. La selección de herramientas por enunciado (`registry_for_role(task_hint=)`)
   se mide: registrar qué herramientas se ofrecieron y cuáles se usaron.
2. El prompt de Melchior incluye el catálogo disponible **con ejemplos de
   cuándo usar cada una**, no solo la firma.
3. Balthasar refuta también por omisión: «había una herramienta que respondía
   esto y no se consultó» es un defecto, y de los caros.

**Se gana:** la diferencia entre un modelo con acceso a herramientas y un
sistema que las usa. Es donde está la ventaja real de MAGI sobre un chat.

## C6. Un proveedor que revienta no es un proveedor agotado

**Evidencia:** `familia 'hf' agotada (1 candidatos): HuggingSpace: TypeError:
argument of type 'NoneType' is not iterable`. Eso no es cuota: es un fallo del
adaptador, y se está informando como agotamiento.

**Qué se hace:** arreglar el `TypeError` del adaptador de HuggingSpace, y
separar en la contabilidad **agotado** (cuota, 429) de **roto** (excepción).
Llevan a decisiones opuestas: uno se espera, el otro se descarta.

## C7. Verificar cero bloques no es verificar

**Evidencia:** `ProposalVerifier.verify` corrió 3 veces en **0,0 s** en la
prueba del Tetris. No había código, así que verificó el vacío y pasó.

**Qué se hace:** sin bloques ejecutables el resultado es `NO VERIFICADO`, no
`OK`. Y si el encargo era `build`, `NO VERIFICADO` bloquea el cierre (C4).

## C8. La calidad de la entrega se mide, no se opina

**Qué se hace:** `scripts/auditar_sistema.py` añade cuatro números al informe,
y Ritsuko los sigue versión a versión:

| Métrica | Prueba A | Prueba B | Objetivo |
|---|---|---|---|
| Caracteres entregados / producidos | 252 / 33.388 (0,8 %) | 252 / 13.140 (1,9 %) | ≥ 60 % |
| Bloques de código con encargo `build` | — | 1 | ≥ 1 y verificado |
| Artefacto entregado con encargo `build` | — | no | sí |
| Herramientas propias usadas | 0 | 0 | ≥ 1 cuando existan para el tema |

## C9. El artefacto trae su propia prueba

**De dónde sale:** mi Tetris expone `--autotest N`; el binario se verifica solo
en un segundo (`AUTOPRUEBA OK: 90 fotogramas` y código 0). Por eso puedo
afirmar que el `.exe` arranca sin que nadie mire la pantalla.

**Qué se hace:** el contrato de `build` exige que el artefacto generado exponga
un modo de autoprueba, y la fábrica lo ejecuta sobre el binario **ya
empaquetado**, no solo sobre el fuente. Verificar el fuente y entregar el
binario deja fuera justo lo que puede romperse al empaquetar.

## C10. Elegir la dependencia mínima es parte del encargo

**Evidencia:** los tres enfoques de Melchior eligieron **pygame** sin
discutirlo. Para «ejecutable único portable», tkinter (biblioteca estándar) da
**9,0 MB** sin SDL ni DLLs externas; pygame da 30-40 MB y más superficie de
fallo en la máquina destino.

**Qué se hace:** para encargos con `portable`, `exe` o `sin dependencias`, la
especificación incluye **presupuesto de dependencias**, y Balthasar tiene que
atacarlo explícitamente: «¿por qué esta biblioteca y no la estándar?». Una
decisión de dependencia sin justificar es un defecto, no un detalle.

---

## Orden actualizado

1. **C1** — dejar de mentir al aprobar. Todo lo demás depende de esto.
2. **C2 + C3** — que el trabajo llegue, y que el árbitro deje de morir.
3. **B1** (unir bloques antes de verificar) y **C7** — la verificación deja de
   producir falsos positivos por los dos lados.
4. **C4 + C9** — «hazme un exe» termina en un exe que se prueba solo.
5. **B4** (hedge en el bucle de herramientas) — el mayor ahorro de tiempo.
6. **C5 + C6** — usar lo que se sabe y distinguir roto de agotado.
7. El resto de las fases 1-4, y **C8 + C10** como criterio permanente.


---

# Fase C-bis — lo que enseñó la prueba del ping pong (C11-C16)

Evidencia: `docs/COMPARATIVA-C-pingpong-16bits.md`. Tercera muestra del mismo
patrón, con una agravante nueva y dos hallazgos que las pruebas A y B no
podían dar porque Naoko y Ritsuko no estaban bajo observación.

## C11. Un fallo que viene como texto sigue siendo un fallo  ⟵ **el arreglo de una línea que cierra media lista**

**Evidencia:** el sistema tiene DOS formas de devolver un error disfrazado de
respuesta normal, las dos son cadenas de texto corrientes:

| Origen | Texto | Marca máquina |
|---|---|---|
| `cloud.py:135` | `[Inferencia no disponible: …]` | `provider_id == "SYSTEM_ERROR"` |
| `agent_loop.py:116` | `[Tiempo de espera agotado tras 150s…]` | ninguna |

Quien no mire el `provider_id` se las traga. **Así se firma `APPROVED` sobre un
timeout** (pruebas A y B) y así el primer informe de Ritsuko traía el error como
veredicto (prueba C). Lo cometí yo mismo en Ritsuko y ya está corregido con
test; falta hacerlo en el resto del sistema.

**Qué se hace:**
1. Una función única —`es_degradada(texto, provider_id)`— en `magi/core/providers/base.py`,
   y **todo** el que consuma una respuesta la usa: agentes, orquestador, Naoko.
2. `agent_loop` devuelve también una marca máquina (`degraded=True` en
   `AgentTurn`), no solo un texto que empieza por corchete.

**Cómo se comprueba:** test que inyecta las dos cadenas y exige que ningún
camino produzca `APPROVED` ni las publique como contenido de agente.

## C12. Declarar éxito de algo que no se hizo

**Evidencia (prueba C):** «Se compiló **exitosamente** el binario ejecutable
único portable (`onefile`)» con **0** bloques de código, **0** llamadas a
`entregar_artefacto` y **0** artefactos en el bus.

Es peor que fallar: el informe parece perfecto y el usuario va a buscar un
fichero que no existe.

**Qué se hace:** el texto del árbitro no puede afirmar hechos que el sistema
puede comprobar. Antes de publicar la síntesis, se contrasta contra el registro
de la tarea: ¿hubo bloques?, ¿hubo verificación con rc=0?, ¿hubo artefacto? Si
la síntesis afirma «compilado/creado/entregado» y el registro dice que no, la
afirmación se sustituye por lo que de verdad pasó y el estado baja a
`INCOMPLETO`.

**Cómo se comprueba:** test con una síntesis que dice «se compiló» y un
registro vacío: el evento final debe contener «no se genero ningun artefacto» y
no `APPROVED`.

## C13. Naoko no puede diagnosticar con la cuota que ella misma está gastando

**Evidencia (prueba C):** 12 intervenciones, y cuatro «deriva detectada» —gpt,
gemini (dos veces), llama— **durante** una tarea que hacía 50 llamadas contra
esos proveedores. Los canarios fallan por cuota, no por deriva del modelo.

Es la tercera vez que este proyecto tropieza con lo mismo: la v5.5.1 ya corrigió
que medir la salud enfermara al sistema. Vuelve por otra puerta.

**Qué se hace:**
1. `_check_drift` no corre con tareas vivas (lo mismo que B8 pide para la sonda).
2. Un canario que falla por 429, timeout o respuesta trunca cuenta como **no
   concluyente**, nunca como deriva. Deriva es que el modelo conteste bien y
   distinto, no que no conteste.
3. Naoko declara deriva solo con **dos** medidas consecutivas concluyentes.

**Cómo se comprueba:** test que simula canarios con 429 y exige cero eventos de
deriva.

## C14. La familia de Ritsuko tiene que anclarse por familia, no por alias

**Evidencia (prueba C):** el fallo de Ritsuko mencionó la familia `deepseek`,
que no es ninguna de las suyas (`razonamiento`, `grok`, `perplexity`). Los
alias de modelo se resuelven a familia por una ruta que la auditora no
controla, así que su independencia —el requisito que la hace útil— depende hoy
de una tabla que puede cambiar sin que nadie se entere.

**Qué se hace:** `_pensar` pide **por familia** (`family=`), no por alias de
modelo, y el test `test_ritsuko_no_comparte_familia` pasa a comprobar la
familia efectivamente usada en la respuesta (`provider_id`), no solo la lista
declarada.

## C15. Cuando el enunciado es ambiguo, la ambigüedad se resuelve por escrito

**Evidencia:** el enjambre resolvió BIEN dos ambigüedades reales del encargo
—16 bits de color (65.536) frente a paleta retro, y binario de 16 bits frente a
color de 16 bits— pero esa resolución se quedó dentro del debate. El usuario no
vio ninguna de las dos.

**Qué se hace:** la síntesis empieza por «cómo he entendido el encargo» en dos
líneas, con las decisiones tomadas sobre lo ambiguo. Es barato y es lo que
separa una entrega de una sorpresa.

## C16. Lo que se pide medir se mide en el binario, no en el fuente

**De dónde sale:** mis dos entregas (`tetris_claude.exe`, `pong16_claude.exe`)
se verifican **ellas mismas**: `--autotest` juega N fotogramas y `--paleta`
comprueba que los doce colores existen en RGB565. Por eso puedo afirmar que
«16 bits» es cierto en vez de decirlo.

**Qué se hace:** cuando el encargo incluye una propiedad comprobable (formato
de color, tamaño, resolución, dependencias), el contrato de `build` exige un
modo de autoprueba que **la compruebe**, y la fábrica lo ejecuta sobre el
binario ya empaquetado. Una propiedad afirmada y no comprobada cuenta como no
cumplida.

---

## Apéndice — dónde se toca cada cosa

Para que este plan sea ejecutable sin volver a razonarlo. Un bloque sin fichero
y sin test es una intención, no una tarea.

| Bloque | Fichero(s) | Test que lo demuestra |
|---|---|---|
| C1 | `magi/modules/swarm/orchestrator.py` (`_orchestrate_loop`, publicación del veredicto) | `tests/test_arbitro_no_aprueba_a_ciegas.py` |
| C2 | `orchestrator.py` (`_publish_approval`) | mismo test: la propuesta viaja en el mensaje |
| C3 | `agents.py::_ask_with_tools`, `agent_loop.py::run_agent` (`iteration_timeout_s`) | `tests/test_presupuesto_tarea.py` (ampliar) |
| C4 | `orchestrator.py` + `magi/modules/swarm/intencion.py` | `tests/test_contrato_de_entregable.py` |
| C5 | `magi/core/tools/__init__.py::registry_for_role`, prompts de `agents.py` | `tests/test_wiring.py` (ampliar: herramientas ofrecidas vs usadas) |
| C6 | `magi/core/providers/backends/g4f_backend.py` (adaptador HuggingSpace) | test con respuesta `None` del proveedor |
| C7 | `magi/core/verification.py::ProposalVerifier.verify` | `tests/test_verificacion_vacia.py` |
| C8 | `scripts/auditar_sistema.py` + `ritsuko.evidencia()` | el propio informe de auditoría |
| C9 / C16 | `magi/modules/studio/entrega.py`, `packager.py` | `tests/test_entrega_artefactos.py` (ampliar) |
| C10 | prompts de `agents.py` (especificación y crítica) | revisión del prompt en `tests/test_prompts.py` |
| C11 | `magi/core/providers/base.py` (nueva `es_degradada`), `agent_loop.py` | `tests/test_ritsuko.py` (ya) + uno en el orquestador |
| C12 | `orchestrator.py` (contraste síntesis ↔ registro) | `tests/test_contrato_de_entregable.py` |
| C13 | `magi/modules/infrastructure/naoko.py::_check_drift` | `tests/test_sonda_no_envenena.py` (ampliar) |
| C14 | `magi/modules/infrastructure/ritsuko.py::_pensar` | `tests/test_ritsuko.py::test_ritsuko_no_comparte_familia` |
| C15 | prompt de Casper en `agents.py` | revisión del prompt |

## Orden final, con las tres pruebas encima de la mesa

1. **C11** — una función y su uso en tres sitios. Cierra la puerta por la que
   entran C1, C12 y el fallo que cometí en Ritsuko.
2. **C1 + C12** — dejar de firmar éxitos: ni sobre un error, ni sobre un
   artefacto que no existe.
3. **C2** — que el trabajo bueno llegue aunque el último paso falle.
4. **C4 + C7 + C9/C16** — «hazme un exe» termina en un exe que se prueba solo.
5. **C13 + B8** — que medir deje de envenenar lo medido.
6. **B1 + B4** — velocidad: unir bloques antes de verificar y cubrir la puerta
   de las herramientas.
7. **C5, C10, C14, C15** — usar lo que se sabe, justificar dependencias, anclar
   la independencia de la auditora y decir cómo se entendió el encargo.
