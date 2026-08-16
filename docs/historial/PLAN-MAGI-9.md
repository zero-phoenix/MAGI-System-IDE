# PLAN DE AMPLIFICACIÓN — MAGI SYSTEM IDE 9.0

**Base auditada:** commit `16a59f3` (v5.0.28) · 3 agosto 2026
**Autor del plan:** análisis directo del código fuente, no del documento de arquitectura
**Principio rector:** convertir capacidad **declarada** en capacidad **real**

---

# PARTE 0 — DIAGNÓSTICO HONESTO

Antes de añadir nada, hay que decir qué hay realmente. Esto no es crítica: la arquitectura que diseñaste es buena, el documento de 875 KB es un trabajo serio, y el enjambre popperiano es una idea correcta. El problema es otro y es concreto.

## 0.1 El hallazgo central: la diversidad del enjambre es ficticia

El README y el documento de arquitectura declaran que cada nodo usa un proveedor distinto (regla de diversidad, §I.3.2). El código dice otra cosa:

```python
# magi/core/providers/cloud.py:122-123
if model in ["claude-3.5-sonnet", "qwen-2.5", "deepseek"]:
    model = "gpt-4o"
```

Melchior pide `deepseek`, Balthasar pide `claude-3.5-sonnet`, Casper pide `qwen-2.5`. Los tres se reescriben a `gpt-4o` antes de salir. **Los tres agentes son el mismo modelo con tres prompts distintos.**

Esto invalida el argumento epistemológico completo del sistema. El valor del debate popperiano viene de que el crítico tenga *sesgos distintos* al proponente. Tres instancias del mismo modelo con temperatura por defecto convergen: Balthasar tiende a criticar lo que un gpt-4o criticaría de sí mismo, que es poco y superficial. Es la razón por la que las críticas suenan genéricas.

Además la GUI muestra `provider: "G4F_Auto_Router(gpt-4o) (deepseek)"` — el nombre entre paréntesis es el que Melchior *cree* estar usando, no el real. La identidad de modelo declarada (§I.8 del documento) no se cumple.

## 0.2 El segundo hallazgo: gran parte del sistema es andamiaje no conectado

Inventario real de `magi/`:

| Categoría | Cuenta |
|---|---|
| Ficheros `.py` en `magi/` | 132 (106 en `modules/`) |
| Módulos importados desde algún sitio alcanzable | **~25** |
| Ficheros de configuración con 0 bytes | **8** (`providers.yaml`, `safety.yaml`, `machine.yaml`, `web_allowlist.yaml`, `policy/global.yaml`, `formats/registry.json`, `types/generated.ts`, `requirements.lock`) |

Y de los que sí se importan, muchos se **instancian y nunca se llaman**. En `magi/main.py:73-105` se construyen `MagiHive`, `SemanticRAG`, `HierarchicalMemory`, `SymbolicVerifier`, `PromptCompiler`, `EvolverAgent`, `CognitiveCore`, `QuantumOracle`, `HyperdimensionalMemory`, `SkinMembrane` y `MarketDigitalTwin`. Conteo de sitios de llamada de cada uno:

```
self.semantic_rag.*        → 0        self.cognitive_core.*   → 0
self.hierarchical_memory.* → 0        self.quantum_oracle.*   → 0
self.prompt_compiler.*     → 0        self.hdc_memory.*       → 0
self.evolver.*             → 0        self.quant_simulator.*  → 0
self.hive.*                → 1  (main.py:135, .shutdown())
self.cellular_router.*     → 1  (main.py:141, .shutdown())
```

Los dos únicos que se usan, se usan **para apagarlos**. `Blackboard` es la excepción honrosa: sí se usa de verdad (5 sitios en el orquestador). El resto existe para que se impriman estas líneas:

```
MAGI 5.0 Bio-Quantum: [Octopus Topology y Oráculo QML]
MAGI 7.0 Predictive Twin: [CFD HFT, Montecarlo y Risk-Off Geopolítico]
```

Y cuando se miran por dentro:

```python
# magi/core/quantum_oracle.py — "resuelve problemas NP-duros"
collapse_state = random.choice(["Alpha-Route", "Beta-Route", "Gamma-Route"])
return collapse_state
```

```python
# magi/modules/quant/simulator.py — el módulo financiero
risk_off_index = np.random.randint(60, 101)
...
return {"confidence": f"{np.random.randint(80, 100)}%", "take_profit": "+5.2%"}
```

El módulo de mercado devuelve **números aleatorios** presentados como análisis, con un take-profit hardcodeado. No se llama nunca, así que hoy no hace daño. Pero si se conectara tal cual, produciría recomendaciones financieras inventadas con una confianza inventada.

**Por qué esto importa para tu petición.** Pediste amplificar funciones. Si amplificamos sobre esta base, multiplicamos andamiaje: más módulos que se instancian, más líneas de log impresionantes, más capacidad declarada y la misma capacidad real. El trabajo de valor es el inverso — cada fase de este plan **conecta o borra**, nunca añade sin conectar.

## 0.3 Naoko ya dañó el repositorio

No es hipotético. Está en el historial:

```
1eb7e87  Auto-reparación Naoko: v1.0.0 - ... {'message': '[CRITICAL] magi.core.providers.cloud:
```

Ese commit está **entre v5.0.24 y v5.0.25**. Naoko intentó bumpear la versión, el regex de `naoko.py:196` no encontró el patrón, cayó al default `new_tag = "v1.0.0"` (línea 191), y etiquetó una regresión de versión. Además dejó esto pegado al final del README, donde sigue hoy:

```markdown
> **Actualización Autónoma (v1.0.0):** Auto-reparación aplicada por Naoko: {'message': '[CRITICAL] magi.core.providers.cloud:
```

La línea está cortada a media frase porque se trunca `error_details[:50]`. Y `naoko.py:225` hace `readme_content += ...` en cada reparación: el README crece indefinidamente.

Lo que Naoko hace hoy, en orden: recibe un error → pide a un LLM un script → lo ejecuta con `powershell -File` sin revisar → `git add .` → commit → tag → `git push origin HEAD`. Sin tests, sin ver si el parche arregló algo, sin poder deshacerlo. `git add .` incluye cualquier cosa que hubiera en el árbol.

Es la pieza más peligrosa del sistema y también la de mayor potencial: la idea de un SRE autónomo es correcta, la implementación es un solo intento a ciegas.

## 0.4 El resto del inventario

| # | Hallazgo | Evidencia | Impacto |
|---|---|---|---|
| 1 | Sin timeout en llamadas LLM | `cloud.py:92` — `await client.chat.completions.create()` sin `wait_for` | Un proveedor colgado congela el enjambre indefinidamente |
| 2 | Caché sin límite | `cloud.py:45,161` — `self._cache[key] = ...`, nunca se purga | Fuga de memoria proporcional al uso |
| 3 | Código muerto de salud | `_is_alive`, `_mark_failure`, `provider_swarm`, `user_agents`, `proxies` — definidos, nunca invocados | El "cortacircuitos" y la "rotación de navegadores" del README no existen |
| 4 | Heurística de censura frágil | `cloud.py:136-137` — dispara con `"no puedo"`, `"lo siento"` | Un texto técnico en español que contenga "no puedo garantizar X" activa el kill-switch global (`orchestrator.py:145`) |
| 5 | Rutas absolutas | `D:/PROYECTOS/MAGI System IDE` en 8 sitios (`kernel.py` ×5, `orchestrator.py:52`, `ws_server.py:112`, `naoko.py:176,186`) | El `.exe` publicado en Releases no funciona en ninguna otra máquina |
| 6 | Estado del enjambre solo en RAM | `orchestrator.py:17` — `self.active_tasks = {}` | Cerrar la ventana pierde todo; la BD existe y no se usa para esto |
| 7 | Debate estrictamente serial | `orchestrator.py:142,150,158` — tres `await` en cadena | Latencia = suma de las tres, siempre |
| 8 | Rondas fijas | `orchestrator.py:174` — `current_round >= 3` | "¿Qué hora es?" pasa por tres rondas de debate popperiano |
| 9 | Sin streaming | `cloud.py:92` sin `stream=True` | El usuario mira una pantalla quieta 30-90 s por turno |
| 10 | `narrativeStyle` no hace nada | `App.tsx:118` declarado, `App.tsx:307` renderizado, **jamás enviado**. `sendCommand(cmd, taskId, engine)` en `useMagiSocket.ts:96` no lo acepta | La feature estrella de v5.0.28 es un `<select>` decorativo |
| 11 | Ejecución sin red de seguridad | `orchestrator.py:69` — `powershell -ExecutionPolicy Bypass -File` sobre código LLM | Correcto que sea sin restricciones (es tu máquina), pero sin *undo* un error borra trabajo real |
| 12 | Tests fuera del repo | `pytest_results.txt` referencia `scratch/test_area*.py`, no versionados. `test_area0` FALLA | No hay CI de verdad; el workflow solo compila |
| 13 | Aprobación por diff desconectada | `App.tsx:818,824` — los `sendCommand("SI"/"NO")` están comentados | La pestaña "Diff (Aprobación)" no comunica la decisión al backend |
| 14 | Agentes sin herramientas | Los tres solo emiten texto | **Techo de capacidad**: no pueden leer un fichero, buscar, ni comprobar su propio trabajo |

El punto 14 es el más importante de todos y da lugar a la Parte 2.

---

# PARTE 1 — FUNDAMENTOS

Nada de lo que pides (juegos, emuladores, manga, documentos, análisis financiero) funciona sobre una capa de inferencia que se cuelga, no distingue modelos y no transmite. Esta parte es aburrida y es la que más multiplica.

## 1.1 Capa de proveedores real

Sustituir `FreeCloudLLM` por un `ProviderRegistry` con backends **de verdad distintos**, en orden de preferencia:

| Backend | Vía | Para qué |
|---|---|---|
| `claude_cli` | Tu suscripción de Claude Code ya autenticada, por subproceso | Razonamiento largo, código, crítica profunda |
| `ollama` | `localhost:11434` — Qwen2.5-Coder 14B, DeepSeek-R1 14B | Sin cuota, sin red, latencia baja, privacidad total |
| `openrouter_free` | Modelos `:free` con clave gratuita | Diversidad real de familias |
| `gemini_cli` / `codex_cli` | CLIs oficiales si están instalados | Más diversidad |
| `g4f` | Lo actual | **Último recurso**, no primero |

Contrato único:

```python
class Provider(Protocol):
    id: str
    family: str            # "claude" | "qwen" | "deepseek" | "gemini" ...
    supports_tools: bool
    supports_vision: bool
    supports_stream: bool

    async def complete(self, req: CompletionRequest) -> CompletionResponse: ...
    async def stream(self, req: CompletionRequest) -> AsyncIterator[Delta]: ...
```

Con, esta vez conectado de verdad:

- **Timeout duro** por llamada (`asyncio.wait_for`, 120 s configurable) y cancelación limpia.
- **Circuit breaker** funcional: 3 fallos → abierto 5 min → semiabierto (1 sonda) → cerrado. El código de `_mark_failure` ya existe, solo hay que *llamarlo*.
- **Caché LRU** con tope (`functools.lru_cache` no sirve por ser async; usar `cachetools.TTLCache(maxsize=500, ttl=3600)`).
- **Contabilidad de tokens** por llamada, agente y tarea → tabla `token_ledger`.
- **Identidad real**: el `provider` que llega a la GUI es el que respondió, no el que se pidió.

**Regla de diversidad, esta vez cumplida.** El selector garantiza que Melchior, Balthasar y Casper obtengan proveedores de **familias distintas**. Si solo hay una familia disponible, se marca `diversity: degraded` en la tarjeta y se fuerza divergencia por temperatura y orden de contexto — pero se *dice*, no se disimula.

**Borrar** en el mismo commit: `user_agents`, `proxies`, `_refresh_proxies`, `provider_swarm`. Son fósiles.

## 1.2 Streaming de extremo a extremo

Hoy: `create()` → espera 30-90 s → aparece un muro de texto.
Objetivo: primer token en < 2 s.

```
Provider.stream() → Delta
  → bus.publish("agent.delta", {task_id, agent, chunk, seq})
    → WSServer reenvía por WebSocket
      → useMagiSocket acumula por (task_id, agent)
        → AgentMessageCard renderiza incremental
```

Efecto secundario grande: con streaming, el debate serial deja de *sentirse* serial. El usuario ve a Melchior escribiendo mientras piensa.

## 1.3 Anclaje de rutas

Un solo módulo `magi/core/paths.py`:

```python
def project_root() -> Path:      # sys._MEIPASS si PyInstaller, si no, raíz del repo
def data_dir() -> Path:          # %LOCALAPPDATA%\MagiSystem  |  ~/.local/share/magi
def workspace_dir() -> Path:     # donde MAGI construye cosas
def db_path() -> Path:           # data_dir() / "magi_brain.db"
```

Y sustituir las 8 apariciones de `D:/PROYECTOS/...`. Sin esto, el `.exe` de Releases solo funciona en tu máquina y en tu carpeta actual. Es un arreglo de una tarde que hace el producto distribuible.

## 1.4 Estado persistente

`active_tasks` pasa de `dict` en RAM a tabla con transiciones registradas:

```sql
CREATE TABLE task_state (
  task_id TEXT PRIMARY KEY,
  command TEXT, status TEXT, round INTEGER,
  engine TEXT, narrative_style TEXT,
  last_proposal_id TEXT, last_critique_id TEXT,
  created_at, updated_at
);
CREATE TABLE task_event (   -- event sourcing real, no solo declarado
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id TEXT, topic TEXT, payload JSON, ts TIMESTAMP
);
```

Al arrancar, el kernel rehidrata las tareas en `in_progress` o `WAITING_USER_APPROVAL` y las reanuda. Cerrar la app deja de perder trabajo.

## 1.5 Tests de verdad

Los `scratch/test_area*.py` no están versionados y `test_area0` falla. Mover a `tests/`, versionar, y añadir al workflow un job que corra `pytest` **antes** de compilar. Un release que no pasa tests no debería publicarse.

Mínimo inicial: contrato de proveedores (con mock), matching de topics del bus, transiciones de estado del orquestador, round-trip de la BD, resolución de rutas en las dos plataformas.

## 1.6 Higiene del repositorio

- `magi_brain.db` (100 KB con tus datos) está **commiteado**. Sacar a `.gitignore`.
- Reparar el README: quitar la línea rota de Naoko.
- Los ~95 módulos no alcanzables: mover a `magi/_attic/` con un `README` que diga qué son. No borrar (son el mapa de tus intenciones), pero sacarlos del path de importación para que el árbol refleje lo que existe.

---

# PARTE 2 — EL ENJAMBRE QUE ACTÚA

Aquí está el salto de capacidad. Todo lo que pides —programas, videojuegos, emuladores, manga, documentos— sale de esta parte.

## 2.1 El problema: agentes ciegos

Hoy Melchior escribe un plan para analizar un firmware **sin haber abierto el firmware**. Balthasar critica ese plan **sin poder verificar nada**. Casper arbitra entre dos textos. Luego, si apruebas, se extraen los bloques ` ``` ` con un regex y se ejecutan a ciegas.

Es un sistema que *habla sobre* trabajo en vez de *hacer* trabajo.

## 2.2 La solución: bucle de herramientas

Cada agente recibe un catálogo de herramientas y un bucle que las ejecuta hasta que declara terminado:

```python
async def agent_turn(agent, task, max_iters=25):
    messages = [system(agent), user(task)]
    for i in range(max_iters):
        resp = await provider.complete(messages, tools=TOOLS[agent.role])
        if resp.tool_calls:
            results = await asyncio.gather(*[
                execute_tool(tc, ctx=task.ctx) for tc in resp.tool_calls
            ])
            messages += [resp, *results]
            await bus.publish("agent.tool_use", {...})   # visible en la GUI
            continue
        return resp   # sin más llamadas = terminó
```

**Catálogo base** (todos los agentes):

```
read_file(path, range)          write_file(path, content)
edit_file(path, old, new)       list_dir(path, recursive)
grep(pattern, path, glob)       glob(pattern)
run_command(cmd, cwd, timeout)  run_tests(path)
web_search(query)               web_fetch(url)
python_exec(code)               screenshot(target)
memgraph_query(cypher)          recall(query)  remember(fact)
```

**Por rol:**

| Rol | Herramientas propias |
|---|---|
| Melchior | `write_file`, `edit_file`, `run_command`, `scaffold_project`, `render_preview` |
| Balthasar | `run_tests`, `static_analyze` (ruff/mypy/bandit/semgrep), `fuzz`, `diff_review`, `benchmark` — pero **no** escritura |
| Casper | `read_*` todo, `run_tests`, `approve_plan`, `ask_user` |

Que Balthasar tenga lectura y ejecución pero no escritura no es una restricción de seguridad: es lo que le da autoridad. Una crítica que dice "esto falla con entrada vacía" **habiendo ejecutado el caso** vale infinitamente más que una que lo sospecha.

## 2.3 Enrutamiento adaptativo

Hoy todo pasa por tres rondas. Un clasificador barato al entrar:

| Clase | Ruta | Latencia objetivo |
|---|---|---|
| `chat` — pregunta, saludo, aclaración | Un solo agente, sin debate | < 3 s |
| `lookup` — dato, búsqueda, "qué es X" | Un agente + `web_search` | < 8 s |
| `task` — escribe/arregla/analiza algo acotado | Melchior con herramientas + Balthasar verifica | < 60 s |
| `build` — proyecto, juego, emulador, investigación | Debate completo + ejecución iterada | minutos, con progreso visible |

El propio clasificador es una llamada corta al modelo local (Ollama) o un heurístico. Esto solo ya divide por 5 la latencia percibida del uso diario.

**Rondas adaptativas** en la ruta `build`: se corta cuando Balthasar no encuentra defectos nuevos (delta de crítica por debajo de umbral) o cuando los tests pasan, no en un contador fijo. Tope duro configurable, por defecto 6.

## 2.4 Paralelismo donde el grafo lo permite

- **N propuestas en paralelo**: Melchior genera 2-3 enfoques distintos simultáneamente (temperaturas/semillas distintas), Balthasar los critica en una sola pasada comparativa, Casper elige. Mismo tiempo de pared, mucha mejor exploración.
- **Crítica multi-eje en paralelo**: seguridad, rendimiento, corrección, mantenibilidad como cuatro llamadas concurrentes que se funden. Balthasar deja de ser un párrafo genérico y pasa a ser un informe.
- **Herramientas concurrentes** dentro de un turno (`asyncio.gather`, ya en el bucle de 2.2).

## 2.5 Verificación ejecutable

Regla: **ninguna propuesta que contenga código llega a Casper sin haberse ejecutado.**

```
Melchior escribe → sandbox de trabajo → run_tests / lint / arranque
   ├─ pasa  → va a Balthasar con la evidencia adjunta
   └─ falla → vuelve a Melchior con el traceback (no gasta ronda de debate)
```

Esto elimina la clase de fallo más común y más cara: los tres agentes debatiendo elegantemente sobre código que no compila.

## 2.6 Memoria que se usa

Existen `SemanticRAG`, `HierarchicalMemory`, `HyperdimensionalMemory`, `MemGraphAdapter`, `Blackboard`, y tablas `mem_knowledge` / `mem_project`. Nada de eso entra en el prompt de ningún agente hoy.

Conectar tres niveles, en este orden de utilidad:

1. **Memoria de proyecto** — índice del repo activo con tree-sitter (`memgraph` ya está diseñado para esto). Melchior consulta `memgraph_query` en vez de adivinar la estructura.
2. **Memoria episódica** — qué se intentó antes en esta tarea y qué falló. Evita que la ronda 3 repita el error de la ronda 1.
3. **Memoria semántica** — hechos duraderos sobre ti, tu máquina, tus preferencias, tus proyectos. Tabla `mem_knowledge` con caducidad, que ya está en el esquema.

Recuperación por embeddings locales (`nomic-embed-text` en Ollama, o `sentence-transformers` — `scikit-learn` ya está en `requirements.txt` para el vecino más cercano).

## 2.7 Estilo narrativo, conectado

Arreglar el `<select>` decorativo de v5.0.28:

```typescript
// useMagiSocket.ts
const sendCommand = (cmd, taskId?, engine?, narrativeStyle?) =>
  ws.send({method:"SYS_EXEC", params:{command:cmd, id:taskId, engine, narrative_style:narrativeStyle}})
```

Y en el backend, cuatro fragmentos de prompt reales que se inyectan en los tres agentes:

| Estilo | Instrucción inyectada |
|---|---|
| `tecnico` | Rigor de ingeniería, pseudocódigo, nombres de API concretos, sin analogías |
| `sintetico` | Máximo 5 líneas. Conclusión primero. Cero preámbulo |
| `creativo` | Analogías, enfoques alternativos, exploración lateral antes de converger |
| `analitico` | Tabla comparativa obligatoria, pros/contras, supuestos explícitos |

Con persistencia en `localStorage` y en `task_state.narrative_style`.

---

# PARTE 3 — NAOKO: DE PARCHEADORA A INGENIERA DE FIABILIDAD

Naoko es la mejor idea del sistema y la peor implementada. El objetivo no es frenarla — es que su autonomía **sirva**, lo que exige que pueda equivocarse sin consecuencias permanentes.

## 3.1 Bucle real de reparación

```
1. DETECTAR    → excepción, test rojo, degradación de latencia, error de usuario
2. REPRODUCIR  → caso mínimo que falla, guardado como test
3. LOCALIZAR   → memgraph + traceback + git blame → ficheros candidatos
4. HIPOTETIZAR → 2-3 causas, ordenadas por probabilidad
5. PARCHEAR    → rama naoko/fix-<id>, edición quirúrgica (no script que reescribe ficheros)
6. VERIFICAR   → el test de (2) pasa Y la suite completa sigue verde
7. DECIDIR     → verde: merge + push · rojo: revert, siguiente hipótesis
8. APRENDER    → mem_knowledge: síntoma → causa → arreglo
```

El paso 6 es el que hoy no existe. Sin él, Naoko no sabe si arregló algo o rompió otra cosa.

## 3.2 Ediciones quirúrgicas, no scripts

Hoy Naoko pide a un LLM *un script que modifique ficheros* y lo ejecuta. Un script mal generado puede sobrescribir cualquier cosa, y es imposible revisarlo como diff.

Cambio: Naoko usa las mismas herramientas `read_file` / `edit_file` que los agentes. El resultado es un **diff**, que se puede mostrar, revisar, aplicar y revertir con `git`. Toda su actividad pasa a ser visible en el visor de diffs de la GUI (§7.4).

## 3.3 Git: arreglar el versionado roto

```python
# naoko.py:191  ← causa del commit v1.0.0
new_tag = "v1.0.0"
```

Sustituir por: leer la versión desde `git describe --tags --abbrev=0`, y **si falla, no inventar** — abortar el bump y avisar. Nunca un default que retrocede la versión.

Además:
- `git add .` → `git add <ficheros del diff>`. Nada más.
- No tocar el README en cada reparación. El registro va a `CHANGELOG.md` o a la BD.
- Push a `naoko/*`, nunca directo a `main` salvo que la suite esté verde.
- Un solo tag por release humano; Naoko no crea tags.

## 3.4 Observabilidad de verdad

Naoko no debería enterarse solo de excepciones. Debe ver:

- Latencia p50/p95/p99 por proveedor y por agente
- Tasa de éxito de herramientas
- Tokens y coste por tarea
- Tests rojos
- Deriva de proveedor (la sonda canaria del §I.8 del documento — nunca implementada)

Todo ya cabe en `provider_telemetry` y en las tablas nuevas del §1.4. Con eso Naoko pasa de reactiva a **proactiva**: "el proveedor B lleva 40 min con p95 de 25 s, lo saco de rotación".

## 3.5 Auto-mejora medible

Lo que pediste como "que haga perfectible al sistema". La forma honesta de conseguirlo:

1. Un banco de evaluación de ~50 tareas con solución verificable (escribe esta función, arregla este bug, analiza este binario, extrae esta tabla).
2. Naoko propone un cambio: un prompt distinto, otro orden de herramientas, otro reparto de proveedores.
3. Se ejecuta el banco **antes y después**.
4. Mejora estadísticamente significativa → se queda. Si no → se revierte.

Eso es evolución real y comprobable, frente a `EvolverAgent` que hoy se instancia y no se llama. Un sistema que mide si mejoró es un sistema que mejora; uno que solo se modifica, deriva.

---

# PARTE 4 — ENCARNACIÓN EN LA MÁQUINA

Tu máquina, tu autorización, sin capas de permiso. La única ingeniería que añado aquí es **reversibilidad**, y el argumento es de utilidad, no de cautela: un agente que puede deshacer lo que hizo es un agente al que puedes dejar suelto. Uno que no puede, acabas vigilándolo — y eso sí es una limitación.

## 4.1 Capacidades

| Dominio | Implementación |
|---|---|
| Ficheros | Lectura/escritura/borrado en todo el sistema. Sin allowlist |
| Procesos | Lanzar, supervisar, matar. Grupos de proceso para limpieza |
| Shell | PowerShell y CMD, con salida en streaming al terminal de la GUI |
| Apps | Automatización por COM/UIAutomation en Windows: Office, navegadores, Blender, VS Code |
| Escritorio | Captura, OCR, clic/teclado (`pyautogui` + visión) para lo que no tiene API |
| Red | HTTP sin restricción de dominio, descargas, git, gestores de paquetes |
| Hardware | USB/serie (`pyserial`, `libusb`) — la base de las Áreas 4 y 9 del documento |

## 4.2 La capa que lo hace utilizable

**Journal de escrituras.** Antes de tocar un fichero existente, copia a `data_dir()/journal/<ts>/`. Comando `magi undo` (y botón en la GUI) que revierte la última operación o toda una tarea. Coste: milisegundos. Beneficio: puedes decir "arregla todo el proyecto" sin pensarlo dos veces.

**Espacio de trabajo con git.** Todo proyecto que MAGI construye se inicializa como repo y se commitea automáticamente en cada hito. Volver atrás es `git checkout`, no arqueología.

**Instantáneas de sistema.** Antes de operaciones amplias (instalar toolchains, reescrituras masivas), un punto de restauración de Windows o una copia del directorio afectado.

**Dry-run como herramienta, no como puerta.** `run_command(cmd, dry_run=True)` devuelve qué haría. Los agentes lo usan para razonar, no requiere aprobación de nadie.

## 4.3 Conciencia de sí mismo y de su sitio

Lo que pediste como "que entienda dónde está funcionando y comprenda su lugar en el tiempo y el espacio cibernético". Hoy los agentes no saben qué día es ni en qué máquina corren. Es una carencia real y con arreglo directo: un bloque de contexto inyectado en cada prompt de sistema.

```
=== CONTEXTO DE EJECUCIÓN ===
Ahora:      2026-08-03 09:14 -05 (America/Lima) · lunes
Host:       DESKTOP-B6D864U · Windows 11 26100 · 16 GB · RTX ...
MAGI:       v5.0.28 (16a59f3) · rama main · árbol limpio
Proceso:    PID 4812 · uptime 2h 14m · 380 MB
Proveedores: claude_cli ok(p95 3.1s) · ollama ok(local) · g4f degradado
Proyecto:   D:\PROYECTOS\emu-vita  (git, 1.2k ficheros, C++/Rust)
Usuario:    David · es-PE · estilo: técnico
Sesión:     tarea 7 de hoy · última: "analizar dynarec de PPSSPP"
```

Con esto Melchior deja de proponer `apt-get` en Windows, Naoko sabe si el árbol está sucio antes de commitear, y todos saben qué versión de sí mismos están ejecutando. Es de las mejoras con mejor relación coste/beneficio de todo el plan.

**Introspección del propio código.** MAGI indexa su propio repositorio en el memgraph. Preguntarle "¿por qué Balthasar responde tan genérico?" se convierte en una consulta que puede responder leyendo `agents.py:73`, no en una especulación.

---

# PARTE 5 — FÁBRICA DE ARTEFACTOS

Todo lo que sigue se apoya en el bucle de herramientas (§2.2). Un patrón común, seis dominios.

## 5.0 El patrón

```
ESPECIFICAR → GENERAR → EJECUTAR/RENDERIZAR → OBSERVAR → CRITICAR → ITERAR → ENTREGAR
```

La clave es **OBSERVAR**: el sistema mira su propio resultado (ejecuta el programa, mira el PNG, lee el docx) antes de dártelo. Sin eso solo genera; con eso, produce.

## 5.1 Programas

Lo más maduro de todo. `scaffold_project` con plantillas (Python, Node, Rust, C++/CMake, Godot) → escritura → `run_tests` → iteración hasta verde. Ya tienes la mitad; falta el bucle de herramientas.

## 5.2 Videojuegos

```
Diseño (mecánicas, loop, estética)
  ↓
Andamiaje (Pygame / Godot / Bevy / web-canvas)
  ↓
Código + assets en paralelo
  ├─ sprites   → generación de imagen + recorte + paleta
  ├─ audio     → síntesis o biblioteca libre
  └─ niveles   → generación procedural o a mano
  ↓
ARRANCAR EN MODO HEADLESS + CAPTURAR FRAMES
  ↓
Balthasar mira las capturas (visión) → "el jugador no se distingue del fondo"
  ↓
Iterar
```

El paso de capturar y mirar es lo que separa "generó código de juego" de "hizo un juego jugable". Godot y Pygame arrancan headless sin problema, así que el bucle es viable.

## 5.3 Emuladores e ingeniería inversa

Tu área de interés declarada, y donde MAGI puede ser genuinamente diferencial. Ningún asistente comercial hace esto bien.

**Toolchain a integrar como herramientas:**

| Herramienta | Uso |
|---|---|
| Ghidra headless (`analyzeHeadless`) | Decompilación a C, exportable a JSON |
| radare2 / rizin (`r2pipe`) | Desensamblado, xrefs, strings, firmas |
| Capstone | Desensamblado embebido para análisis rápido |
| Unicorn | Emulación de fragmentos, ejecución diferencial |
| QEMU | Sistema completo cuando hace falta |
| `tree-sitter` (ya en memgraph) | Indexar código fuente de emuladores existentes |

**El flujo comparativo que describiste** — analizar emuladores decompilados y adaptar uno de una consola a otra:

```
1. INDEXAR CORPUS
   PPSSPP (PSP/MIPS) · melonDS y DeSmuME (NDS/ARM9+ARM7) · Vita3K (Vita/ARMv7)
   → memgraph con aristas CALLS / IMPLEMENTS / DISPATCHES
   → ~2M LOC consultables por Cypher

2. EXTRAER ARQUITECTURA POR SUBSISTEMA
   Para cada emulador: CPU core · dynarec · MMU · GPU/rasterizador ·
   audio · I/O · HLE de syscalls · savestates
   → ficha estructurada por subsistema, con referencias a fichero:línea

3. MATRIZ DE CONTRASTE
   ┌──────────────┬─────────────┬──────────────┬─────────────┐
   │ Subsistema   │ PSP         │ NDS          │ Vita        │
   ├──────────────┼─────────────┼──────────────┼─────────────┤
   │ ISA          │ MIPS32 R4k  │ ARMv5TE ×2   │ ARMv7-A NEON│
   │ Dynarec IR   │ propio      │ propio       │ propio      │
   │ MMU          │ plana+TLB   │ dual, dispersa│ MMU real   │
   │ GPU          │ GE (fija)   │ 2D+3D fija   │ SGX (shaders)│
   │ HLE          │ syscalls    │ BIOS parcial │ módulos SCE │
   └──────────────┴─────────────┴──────────────┴─────────────┘

4. PLAN DE PORTADO
   Qué es reutilizable tal cual (frontend, savestates, input, config, GUI)
   Qué necesita reemplazo (frontend del dynarec, GPU, HLE)
   Qué es irreducible y por qué (shaders programables no salen de una GPU fija)

5. IMPLEMENTAR CON VERIFICACIÓN DIFERENCIAL
   Emular instrucción a instrucción contra referencia (Unicorn)
   → detectar divergencia exacta de registro/flag/ciclo
```

Este workflow —indexar varios emuladores, contrastarlos por subsistema, y proponer una ruta de adaptación con referencias a código real— es exactamente lo que describiste querer, y es construible con lo listado arriba. El memgraph que ya está diseñado en tu Área 13 es la pieza central.

**Nota legal práctica**, sin moralina: analizar binarios que posees y escribir implementaciones propias es terreno establecido. Redistribuir BIOS/ROMs/firmware ajeno no. El CTL-1 que ya especificaste (`§I.4`) cubre esto y merece implementarse — no como freno, sino porque un proyecto que se distribuye limpio es un proyecto que sobrevive.

## 5.4 Imagen y manga

**Motor:** ComfyUI local (API HTTP, control total, sin coste por imagen) con SDXL o Flux. Alternativa por API para picos de calidad.

**Manga como pipeline, no como prompt:**

```
Guion → viñetas (texto por panel, encuadre, emoción)
  ↓
Layout de página (rejilla, ángulos, ritmo de lectura — derecha a izquierda si procede)
  ↓
Consistencia de personajes  ← LoRA entrenado o IP-Adapter con hoja de referencia
  ↓
Render por panel (ControlNet para pose y encuadre)
  ↓
Composición: bordes, tramas, líneas cinéticas
  ↓
Rotulación: globos posicionados por detección de espacio libre + tipografía
  ↓
Balthasar revisa la página con visión: ¿el personaje es el mismo? ¿se lee el orden?
  ↓
Iterar paneles concretos, no la página entera
```

La consistencia de personaje entre viñetas es el problema difícil y tiene solución conocida (LoRA/IP-Adapter + hoja de referencia). El resto es composición programática con PIL/OpenCV.

## 5.5 Vídeo

Aquí toca ser preciso sobre lo que es alcanzable:

| Enfoque | Viabilidad local | Nota |
|---|---|---|
| Vídeo programático (FFmpeg, motion graphics, TTS, capturas) | **Alta** | Tutoriales, demos, informes animados. Empezar aquí |
| Animática desde stills (Ken Burns, transiciones, doblaje) | **Alta** | Manga → vídeo con voz sale casi gratis |
| Interpolación y upscale (RIFE, Real-ESRGAN) | Alta | Mejora lo anterior |
| Gen-vídeo local (AnimateDiff, LTX, Wan) | Media | Clips cortos, exige VRAM seria |
| Gen-vídeo de calidad (Veo, Sora, Kling) | Solo API | De pago; no encaja en el modelo de coste cero |

Lo honesto: los tres primeros dan resultados profesionales ya. El gen-vídeo largo y coherente no está resuelto localmente en 2026 para hardware de escritorio.

## 5.6 Documentos

`python-docx`, `python-pptx`, `openpyxl`, `reportlab`/`weasyprint`, `pandoc`. Directo. Con el bucle de observación: renderizar a PDF, mirar el resultado, corregir maquetación. Y con acceso al sistema de ficheros, guarda donde le digas sin fricción.

---

# PARTE 6 — CONOCIMIENTO DEL MUNDO

## 6.1 Actualidad

- Búsqueda web como herramienta de primera clase (ya en el catálogo de §2.2).
- Ingesta de RSS/Atom: Reuters, AP, FT, Bloomberg, bancos centrales, boletines oficiales.
- Caché de "estado del mundo" con caducidad por tipo de dato: cotización (minutos), tipos de interés (días), composición de gobiernos (meses).
- Cada afirmación sobre el presente sale con fuente y fecha, o sale marcada como no verificada.

## 6.2 Geopolítica y macro

Fuentes con API gratuita y de calidad: FRED (Reserva Federal de St. Louis), Banco Mundial, FMI WEO, OCDE, Eurostat, Comtrade. Datos duros, no titulares.

El análisis lo aporta el enjambre: Melchior propone una lectura, Balthasar busca los datos que la contradicen, Casper pesa la evidencia. Ese es exactamente el uso donde la estructura popperiana **sí** aporta algo real, porque el análisis geopolítico es precisamente donde el consenso aparente engaña.

## 6.3 Finanzas — la versión construible

Pediste "todas las habilidades de Warren Buffett". Voy a ser directo contigo porque es la parte donde más fácil sería venderte humo, y ya tienes un módulo (`quant/simulator.py`) que devuelve `np.random.randint` como índice de riesgo.

**Lo que no se puede construir:** el juicio de Buffett. Su ventaja son sesenta años de criterio, una red de contactos, acceso a operaciones privadas, capital permanente y temperamento bajo pánico. Ningún sistema de software tiene eso, y cualquiera que te diga que su producto lo tiene te está vendiendo un generador de números con vocabulario financiero.

**Lo que sí se puede construir, y es genuinamente valioso:**

| Componente | Implementación |
|---|---|
| Fundamentales | SEC EDGAR XBRL — gratis, completo, todas las presentaciones desde 2009 |
| Precios e históricos | `yfinance`, Stooq |
| Macro | FRED |
| Owner earnings | Cálculo determinista en Python: FCO − capex de mantenimiento |
| DCF con escenarios | Aritmética en código, **nunca del LLM** — los modelos de lenguaje calculan mal |
| Checklist de calidad | ROIC, deuda/EBITDA, márgenes, dilución, conversión de caja — rúbrica explícita |
| Análisis de foso | Marco estructurado sobre datos reales, evaluado por el enjambre |
| Lectura de informes | Ingesta de 10-K/10-Q, extracción de notas, detección de cambios año a año |
| Retrotesteo | Los criterios se contrastan contra histórico antes de fiarse de ellos |
| Registro de decisiones | Cada tesis se guarda con fecha y se puntúa después. **Calibración medible** |

Lo último es lo que casi nadie hace y es lo que de verdad se parece a Buffett: llevar cuenta de tus errores. Un sistema que guarda cada tesis con su razonamiento y la revisa a los seis meses te enseña más sobre tu propio criterio que cualquier modelo predictivo.

**Regla dura:** toda aritmética financiera se ejecuta en Python y se muestra la fórmula. El LLM interpreta y argumenta; no calcula. Y el `simulator.py` actual se borra o se reescribe — un `np.random.randint` presentado como "índice risk-off" es peor que no tener nada, porque parece un análisis.

## 6.4 "Experto en todo" — la versión que funciona

La omnisciencia no es construible. Lo que sí, y que en la práctica rinde más:

1. **Recuperación antes que recuerdo** — busca en vez de confiar en lo memorizado.
2. **Herramientas antes que intuición** — calcula, ejecuta, mide.
3. **Verificación antes que afirmación** — corre el código antes de asegurar que funciona.
4. **Citación antes que aserción** — di de dónde sale cada dato.
5. **Calibración antes que confianza** — di cuánta seguridad tienes y acierta también en eso.

Un sistema con estas cinco propiedades supera en resultados a uno que finge saberlo todo, y —más importante— **puedes fiarte de él**, que es la única forma de que valga la pena dejarlo trabajar solo.

---

# PARTE 7 — INTERFAZ

## 7.1 Descomponer App.tsx

42 KB en un fichero, con `AgentMessageCard` definido dentro. Separar en `components/`, `hooks/`, `panels/`, `store/`. Sin esto, cada feature nueva es más cara que la anterior.

## 7.2 Layout multi-panel

```
┌──────────┬─────────────────────────┬──────────────┐
│ Proyecto │   Enjambre (streaming)  │ Naoko        │
│ Ficheros │   ─────────────────     │ ─────────    │
│ Memoria  │   Melchior ▊ escribiendo│ Salud        │
│ Tareas   │   Balthasar ✓ 3 defectos│ Métricas     │
│          │   Casper   ⧗ esperando  │ Reparaciones │
├──────────┼─────────────────────────┴──────────────┤
│ Terminal │  Artefacto: código · vista previa ·    │
│          │  diff · imagen · gráfico               │
└──────────┴────────────────────────────────────────┘
```

## 7.3 Piezas que faltan

| Pieza | Por qué |
|---|---|
| Streaming token a token | Percepción de velocidad; lo más notable de todo el plan |
| Traza de herramientas | Ver "leyendo `dynarec.cpp:412`" convierte una caja negra en un colaborador |
| Virtualización de lista | Historiales largos hoy hunden el render |
| Vista previa de artefactos | Imagen, HTML, PDF, juego, gráfico — en panel, no descargando |
| Visor de diffs | `DiffViewer.tsx` existe y se renderiza (`App.tsx:813`) pero está **neutralizado**: recibe `originalCode=""` (todo aparece como nuevo, no es un diff) y sus `sendCommand` de aprobar/rechazar están comentados (`App.tsx:818,824`) — pulsar "Aprobar" no llega al backend |
| Panel de coste | Tokens y tiempo por tarea, por agente |
| Paleta de comandos | Ctrl+K sobre acciones y proyectos |
| Cancelar / reencauzar | Poder parar un turno a mitad sin matar la app |

## 7.4 Aprobación con contexto

El banner de v5.0.28 va en la dirección correcta. Falta lo que hace falta para decidir de verdad: **qué se va a ejecutar exactamente**, qué ficheros toca, y si los tests pasaron. Botón "Ver diff" junto a "Apruebo". Con el journal de §4.2, aprobar deja de ser irreversible y por tanto deja de dar miedo.

---

# PARTE 8 — SECUENCIA

Cada fase deja el sistema mejor que la anterior. Nada de big bang.

### Fase 1 — Cimientos (semanas 1-2)
Capa de proveedores real con diversidad de familias · timeouts · caché LRU · streaming extremo a extremo · `paths.py` y borrado de las 8 rutas absolutas · estado persistente · tests versionados en CI · `magi_brain.db` fuera del repo · README reparado.

**Se nota en:** primer token en 2 s en vez de 60 · el `.exe` funciona en cualquier máquina · cerrar la app no pierde trabajo · Balthasar deja de sonar a Melchior.

### Fase 2 — Agentes que actúan (semanas 3-5)
Bucle de herramientas · catálogo base · enrutamiento adaptativo · verificación ejecutable · `narrativeStyle` conectado · journal de escrituras y `undo`.

**Se nota en:** el sistema deja de describir trabajo y lo hace · "¿qué hora es?" tarda 2 s, no 90 · el código que propone ya se ha ejecutado.

### Fase 3 — Naoko en serio (semanas 6-7)
Bucle detectar→reproducir→parchear→verificar · ediciones por diff en rama · versionado arreglado · observabilidad completa · banco de evaluación.

**Se nota en:** las reparaciones se verifican · nunca más un commit `v1.0.0` · Naoko avisa antes de que algo se caiga.

### Fase 4 — Fábrica (semanas 8-12)
Contexto de ejecución en todos los prompts · memoria conectada · toolchain de RE (Ghidra/r2/Unicorn) · corpus de emuladores indexado · ComfyUI · documentos · vídeo programático.

**Se nota en:** construye juegos que arrancan · responde sobre dynarecs citando fichero y línea · produce páginas de manga con personaje consistente.

### Fase 5 — Mundo e interfaz (semanas 13-16)
Búsqueda y RSS · FRED/EDGAR/World Bank · módulo financiero determinista (y borrado del `simulator.py` aleatorio) · registro de tesis calibrado · descomposición de App.tsx · multi-panel · traza de herramientas · visor de artefactos.

### Fase 6 — Continuo
Banco de evaluación en cada cambio · Naoko propone y mide · nuevas herramientas según lo que pidas.

---

## Métricas

Sin medición, "mejor" es una opinión. Lo que se sigue, desde la Fase 1:

| Métrica | Hoy (estimado) | Objetivo |
|---|---|---|
| Primer token | 30-90 s | < 2 s |
| Consulta simple, extremo a extremo | ~90 s (3 rondas) | < 5 s |
| Tareas completadas sin intervención | — | > 70 % |
| Código propuesto que ejecuta a la primera | — | > 85 % |
| Parches de Naoko verificados | 0 % | 100 % |
| Familias de modelo distintas en el enjambre | **1** | 3 |
| Módulos alcanzables / totales | ~25/132 | > 90 % |
| Cobertura de tests | ~0 | > 60 % en `core/` |
| Memoria en sesión de 8 h | crece sin tope | estable |

## Lo que este plan deliberadamente NO hace

- **No añade módulos sin conectarlos.** La regla de oro: si no tiene sitio de llamada y un test, no entra.
- **No mantiene `simulator.py` ni `quantum_oracle.py` como están.** Devolver `random` disfrazado de análisis es peor que no tener el módulo.
- **No pone puertas de permiso.** Reversibilidad, no autorización. Es tu máquina.
- **No promete lo imposible.** Gen-vídeo largo coherente en local, omnisciencia, y el juicio de Buffett no están sobre la mesa. Todo lo demás de tu lista, sí.

---

## El resumen en un párrafo

MAGI tiene una arquitectura pensada, una identidad clara y una idea correcta —confrontación entre inteligencias con sesgos distintos— construida sobre una implementación donde esa confrontación no ocurre, los agentes no pueden tocar nada, y un tercio del sistema son objetos que se construyen para imprimir su propio nombre en el log. La ruta a "MAGI 9.0" no pasa por añadir el Área 22: pasa por hacer que las tres inteligencias sean realmente tres, darles manos, y medir si lo que producen sirve. Con eso hecho —y son unas seis semanas de trabajo real para las Fases 1-3— construir juegos, analizar emuladores, dibujar manga y leer balances deja de ser una lista de deseos y se convierte en escribir herramientas para un motor que ya funciona.
