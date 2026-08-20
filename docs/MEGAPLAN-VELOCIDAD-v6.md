# MEGAPLAN v6 — que el sistema vaya rápido sin dejar de ser honesto

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
