# Auditoría en caliente de la v5.5.2

**Fecha:** 2026-08-20 · **Método:** `python scripts/auditar_sistema.py`
**Entorno:** `.venv-lock` (coincide con `requirements.lock`) · Windows · Python 3.10.11

Tres pasadas reales contra los proveedores gratuitos, con el kernel arrancado
de verdad y una petición representativa: *«Escribe una función python que sume
dos números y su test con pytest»*, motor `fast`, 1 ronda.

No hay ninguna opinión en este informe que no tenga un número detrás.

---

## 1. Veredicto: el sistema funciona

La tarea recorrió el camino completo y terminó bien:

| Etapa | Evidencia |
|---|---|
| Melchior propone | `AGENT_POST` a los 97,9 s |
| Verificación real | rechaza el primer intento y lo devuelve con motivo |
| Melchior reconstruye | rebuild 1/2, con 1 sola variante (lo correcto) |
| Balthasar critica | `AGENT_POST` a los 116,9 s, con evidencia ejecutada |
| Casper arbitra | `APPROVED` a los 200,8 s |
| Aprobación | se pide al usuario, no se autoaprueba |

Casper cerró con «pasando los 4 casos de prueba en 0.22 segundos»: el sistema
**ejecutó el código de verdad** antes de aprobarlo. Eso es lo que separa este
proyecto de un generador de texto con tres personajes.

---

## 2. Dónde se va el tiempo (lo medido, no lo supuesto)

Tarea completa: **206,2 s de pared**.

```
ProviderRegistry.complete       14 llamadas    269,2 s acumulados   (19,2 s de media)
SwarmAgentBase._ask_with_tools   7 turnos      224,4 s
SwarmAgentBase._ask              2 llamadas     24,7 s
ProposalVerifier.verify          4 pasadas       3,2 s
arranque (imports + kernel)                      0,5 s
```

**El 98 % del tiempo es esperar a proveedores gratuitos.** La maquinaria propia
—verificar, ejecutar herramientas, arrancar— suma menos de 4 segundos.

Consecuencia para cualquier plan de velocidad: optimizar Python aquí no sirve
de nada. Solo hay tres palancas reales, y son **menos llamadas**, **llamadas
más cortas** y **más solape entre ellas**.

Tres números que lo concretan:

1. **19,2 s de media por llamada.** Con 16 llamadas para sumar dos números.
2. **Factor de solape 1,4×** (294 s de espera acumulada en 206 s de pared).
   Con las tres variantes de Melchior y los dos ejes de Balthasar corriendo en
   paralelo, debería acercarse a 3×.
3. **Verificación: 0,8 s por pasada.** No es el cuello de botella y no hay que
   tocarla — salvo por el bug de la sección 3.1, que provoca llamadas de más.

### La segunda puerta al modelo

Hay **dos caminos** distintos hasta el proveedor y no se comportan igual:

- `FreeCloudLLM.generate` → lo usan `_ask`, Naoko y la sonda. Lleva hedge
  (cubrir una llamada lenta con otro candidato), etiqueta de rama y cobro al
  presupuesto.
- `ProviderRegistry.complete` → lo usa `run_agent`, el bucle de herramientas,
  que es **el camino principal de Melchior y Casper**. Cobra al presupuesto
  (`agents.py:401`, correcto), pero **no lleva hedge**.

Las 14 llamadas más lentas del sistema son justo las que van sin cubrir.

---

## 3. Fallos encontrados

### 3.1 La verificación evalúa cada bloque por separado (coste: un ciclo entero)

Medido: `[VERIFICACIÓN] El código propuesto no arranca. Devuelto a Melchior
(rebuild 1/2)`. El motivo, en palabras de Melchior al reintentar:

> `ModuleNotFoundError: No module named 'suma'`

El modelo hizo lo natural —función en un bloque, test en otro— y el verificador
ejecutó cada bloque como un fichero suelto, así que el test no encontró a la
función. No es un fallo del modelo: es que se le está pidiendo algo distinto de
lo que se le dice.

Curioso y significativo: `entrega.py` ya resuelve esto con `_unir_bloques()`
para empaquetar. La verificación no lo usa.

**Coste medido:** un rebuild completo ≈ 4 llamadas al modelo ≈ **60-80 s de los
206**, en la tarea más simple posible.

### 3.2 Una tarea reanudada con las rondas agotadas se queda muda para siempre

Reproducido sin querer, que es la mejor forma. La segunda pasada de la
auditoría reutilizó el id `auditoria`, que estaba en la base esperando
aprobación. El sistema lo tomó por feedback y respondió:

> `[SWARM] Feedback del usuario recibido. Reanudando debate (Ronda 2)`

Y después, **300 s sin una sola llamada al modelo**. El bucle se relanza con
`round` ya por encima de `max_rounds`, no entra en ninguna iteración y termina
en silencio. Para el usuario: escribes, el sistema dice «reanudando» y no
vuelve a hablar nunca.

### 3.3 La sonda y el detector de deriva compiten con la tarea por la misma cuota

Medido en la segunda pasada, con el sistema recién usado:

> `Deriva detectada en g4f-gpt: solo 0/3 respuestas canarias correctas`
> `Deriva detectada en g4f-gemini: solo 0/3 respuestas canarias correctas`

Dos familias declaradas «a la deriva» inmediatamente después de una tarea real.
La explicación más probable no es que los proveedores se hayan roto, sino que
acaban de atender 16 llamadas y están limitando el ritmo. Es la misma clase de
error que la v5.5.1 ya corrigió una vez (*medir la salud no puede enfermar al
sistema*), reaparecida por otra puerta: ahora el que enferma al paciente es el
detector de deriva, no el filtro de basura.

También se observó `sonda.actualizada` **a mitad de la tarea** (t=51,6 s).

### 3.4 Los registros del arranque se perdían en silencio

`bus_log_handler.py:101` hacía:

```python
asyncio.create_task(self.bus.publish(BusEvent(...)))   # dentro de try/except RuntimeError
```

Python evalúa los argumentos primero, así que la corrutina ya estaba creada
cuando `create_task` fallaba por no haber bucle: el `except` se la tragaba sin
awaitarla. Síntoma visible: `RuntimeWarning: coroutine 'MagiBus.publish' was
never awaited` en cada arranque. Síntoma invisible y peor: **los registros
anteriores al bucle —los del arranque— no llegaban a ninguna parte.**

**Ya corregido** en esta misma sesión.

### 3.5 Ruido de arranque con causa real

```
[AASLoader] Repositorio ...\workspace\agentic-awesome-skills no encontrado.
```

Un cargador de skills busca un repositorio que nadie clona. O se clona, o se
degrada en silencio con una línea de debug; lo que no puede es gritar un error
que no lo es en cada arranque.

### 3.6 Un proveedor sigue intentando abrir el navegador

```
Aviso: cortafuegos íntegro; 1 intento(s) de abrir navegador BLOQUEADOS
(origen: SyncCDPSession.start_chrome).
```

El cortafuegos hizo su trabajo. Pero el intento existe, y cada uno cuesta
tiempo dentro de una llamada que después falla.

---

## 4. Lo que está bien y no hay que tocar

- **Arranque: 0,5 s** (0,11 s de imports + 0,39 s de kernel). Nada que ganar.
- **Verificación: 0,8 s por pasada.** Barata y devuelve evidencia real.
- **Presupuesto por tarea:** cobra las dos puertas, incluidas las iteraciones
  del bucle de herramientas. La contabilidad es honesta.
- **El hedge selectivo** hace lo que promete donde llega: las llamadas de
  `_ask` salieron con `hedge=False` y etiqueta de rama, sin multiplicar.
- **Suite:** 1.297 tests en verde, incluidos los que compilan un .exe real.
