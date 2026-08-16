# MAGI System IDE — Plan de Arquitectura Técnica Integral
### Espacio de Trabajo de Escritorio Independiente y Motor Autónomo de Síntesis y Análisis

**Producto:** **MAGI System IDE**. **Núcleo de ingeniería y síntesis:** `ATLAS-FORGE` (el motor que MAGI System IDE gobierna). **Deliberación:** los tres agentes **MELCHIOR • 1**, **BALTHASAR • 2** y **CASPER • 3**.
**Versión del plan:** 1.0. **Idioma normativo:** español. **Formato:** documento único de arquitectura interna.

---

## Tabla de contenidos

- [Parte I — Marco normativo del plan](#parte-i--marco-normativo-del-plan)
  - [I.1 Entorno objetivo fijado y Capa de Abstracción de Sistema (HAL)](#i1-entorno-objetivo-fijado-y-capa-de-abstracción-de-sistema-hal)
  - [I.2 Glosario normativo operativo](#i2-glosario-normativo-operativo)
  - [I.3 Jerarquía de coste cero real (Niveles 1/2/3)](#i3-jerarquía-de-coste-cero-real-niveles-123)
  - [I.4 Fronteras legales codificadas como controles técnicos](#i4-fronteras-legales-codificadas-como-controles-técnicos)
  - [I.5 Convención de pasos y subpasos con puertas de verificación](#i5-convención-de-pasos-y-subpasos-con-puertas-de-verificación)
  - [I.6 Identidad MAGI: los tres nodos, el núcleo ATLAS-FORGE y la nomenclatura](#i6-identidad-magi-los-tres-nodos-el-núcleo-atlas-forge-y-la-nomenclatura)
  - [I.7 Integración de tecnologías externas: MAGI-MEM y MAGI-ROUTE](#i7-integración-de-tecnologías-externas-magi-mem-y-magi-route)
  - [I.8 Identidad de modelo declarada](#i8-identidad-de-modelo-declarada-cada-nodo-dice-siempre-qué-inteligencia-está-usando)
- [Parte II — Desarrollo por áreas](#parte-ii--desarrollo-por-áreas)
  - [ÁREA 0 — Arquitectura global, modelo de datos y fundaciones](#área-0--arquitectura-global-modelo-de-datos-y-fundaciones)
  - [ÁREA 1 — Enrutador multimodal y análisis forense topográfico](#área-1--enrutador-multimodal-y-análisis-forense-topográfico)
  - [ÁREA 2 — Motor de razonamiento contrastivo (legal y técnico)](#área-2--motor-de-razonamiento-contrastivo-legal-y-técnico)
  - [ÁREA 3 — Motor de debate popperiano (cognición hostil)](#área-3--motor-de-debate-popperiano-cognición-hostil)
  - [ÁREA 4 — Interacción en tiempo real con dispositivos (live device telemetry)](#área-4--interacción-en-tiempo-real-con-dispositivos-live-device-telemetry)
  - [ÁREA 5 — Ingeniería inversa y síntesis de software](#área-5--ingeniería-inversa-y-síntesis-de-software)
  - [ÁREA 6 — Resiliencia y rotación dinámica (failover)](#área-6--resiliencia-y-rotación-dinámica-failover)
  - [ÁREA 7 — Especificación de prompts de sistema (modo Forensic Engineer)](#área-7--especificación-de-prompts-de-sistema-modo-forensic-engineer)
  - [ÁREA 8 — Motor de ejecución multi-paso autónomo en vivo](#área-8--motor-de-ejecución-multi-paso-autónomo-en-vivo)
  - [ÁREA 9 — Fabricación física y diseño electrónico (USB Fabrication Lab)](#área-9--fabricación-física-y-diseño-electrónico-usb-fabrication-lab)
  - [ÁREA 10 — Interfaz gráfica agentic y control total del sistema](#área-10--interfaz-gráfica-agentic-y-control-total-del-sistema)
  - [ÁREA 11 — Creatividad inventiva (motor de invención y explotación)](#área-11--creatividad-inventiva-motor-de-invención-y-explotación)
  - [ÁREA 12 — Núcleo cognitivo de capacidades de élite (C01–C39)](#área-12--núcleo-cognitivo-de-capacidades-de-élite-c01c39)
  - [ÁREA 13 — MAGI-MEM: grafo de memoria de código persistente](#área-13--magi-mem-grafo-de-memoria-de-código-persistente)
  - [ÁREA 14 — MAGI-ROUTE: pasarela universal de inferencia y economía de tokens](#área-14--magi-route-pasarela-universal-de-inferencia-y-economía-de-tokens)
  - [ÁREA 15 — Ingesta universal de documentos: cualquier formato, de cualquier época](#área-15--ingesta-universal-de-documentos-cualquier-formato-de-cualquier-época)
  - [ÁREA 16 — Sistemas operativos portables y entornos de época](#área-16--sistemas-operativos-portables-y-entornos-de-época)
  - [ÁREA 17 — Centro de Configuración y Calibración](#área-17--centro-de-configuración-y-calibración)
  - [ÁREA 18 — MAGI-KEEP: memoria íntegra y transferencia entre inteligencias](#área-18--magi-keep-memoria-íntegra-y-transferencia-entre-inteligencias)
  - [ÁREA 19 — MAGI-WEB: navegación robusta y captura de evidencia](#área-19--magi-web-navegación-robusta-y-captura-de-evidencia)
  - [ÁREA 20 — MAGI-STUDIO: videojuegos, música, imagen y vídeo con autocorrección](#área-20--magi-studio-creación-de-videojuegos-música-imagen-y-vídeo-con-autocorrección)
  - [ÁREA 21 — MAGI-SHELL: aplicación, extensión de navegador y proyectos con repositorio](#área-21--magi-shell-aplicación-de-escritorio-extensión-de-navegador-y-proyectos-con-repositorio)
- [Parte III — Artefactos transversales](#parte-iii--artefactos-transversales)
  - [T1 Árbol de directorios completo](#t1-árbol-de-directorios-completo)
  - [T2 Catálogo maestro de eventos del bus](#t2-catálogo-maestro-de-eventos-del-bus)
  - [T3 Esquema completo de la base de datos](#t3-esquema-completo-de-la-base-de-datos)
  - [T4 Matriz de trazabilidad Áreas ↔ Capacidades C01–C39](#t4-matriz-de-trazabilidad-áreas--capacidades-c01c39)
  - [T5 Matriz de dependencias entre módulos y orden topológico](#t5-matriz-de-dependencias-entre-módulos-y-orden-topológico)
  - [T6 Tabla maestra de dependencias externas](#t6-tabla-maestra-de-dependencias-externas)
  - [T7 Presupuesto global de recursos por escenario](#t7-presupuesto-global-de-recursos-por-escenario)
  - [T8 Hoja de ruta global en cuatro fases](#t8-hoja-de-ruta-global-en-cuatro-fases)
  - [T9 Diez riesgos principales del proyecto](#t9-diez-riesgos-principales-del-proyecto)
  - [T10 Glosario final](#t10-glosario-final)
  - [T11 Plan maestro de construcción por pasos y subpasos con puertas de verificación](#t11-plan-maestro-de-construcción-por-pasos-y-subpasos-con-puertas-de-verificación)
  - [T12 Sistema de diseño visual MAGI (tokens, componentes y accesibilidad)](#t12-sistema-de-diseño-visual-magi-tokens-componentes-y-accesibilidad)
  - [T13 Addenda de integración: cambios que MAGI-MEM y MAGI-ROUTE introducen en T1–T11](#t13-addenda-de-integración-cambios-que-magi-mem-y-magi-route-introducen-en-t1t11)
  - [T14 Addenda de las Áreas 15 y 16: ingesta universal y sistemas portables](#t14-addenda-de-las-áreas-15-y-16-ingesta-universal-y-sistemas-portables)
  - [T15 Addenda de la interfaz conversacional, el Área 17 y la deliberación multi-ronda](#t15-addenda-de-la-interfaz-conversacional-el-área-17-y-la-deliberación-multi-ronda)
  - [T16 Addenda de las Áreas 18 y 19: memoria íntegra y navegación gobernada](#t16-addenda-de-las-áreas-18-y-19-memoria-íntegra-y-navegación-gobernada)
  - [T17 Addenda de la inferencia en nube y de las Áreas 20 y 21](#t17-addenda-de-la-inferencia-en-nube-y-de-las-áreas-20-y-21)
- [Parte IV — Auto-verificación final](#parte-iv--auto-verificación-final)
  - [6.1 Tabla de cobertura](#61-tabla-de-cobertura)
  - [6.2 Tabla de trazabilidad contra el encargo](#62-tabla-de-trazabilidad-contra-el-encargo)
  - [6.3 Declaración de omisiones](#63-declaración-de-omisiones)
  - [6.4 Las cinco afirmaciones más débiles del propio plan](#64-las-cinco-afirmaciones-más-débiles-del-propio-plan)

---

# Parte I — Marco normativo del plan

## I.1 Entorno objetivo fijado y Capa de Abstracción de Sistema (HAL)

**Decisión:** paridad real Windows 10/11 (build ≥ 19045) ↔ Linux (glibc ≥ 2.35, kernel ≥ 6.1), mediante una HAL única en `core/hal/` que expone diez interfaces y dos implementaciones — porque cada módulo que toca el SO debe tener un único punto de divergencia auditable en vez de `if sys.platform` disperso.
*Descartado:* soportar únicamente Linux y usar WSL2 en Windows como capa completa — degrada el acceso USB nativo, que es el corazón de las Áreas 4 y 9.

Interfaces de la HAL (exhaustivas, con su fichero):

| Interfaz | Fichero | Responsabilidad | Impl. Windows | Impl. Linux |
|---|---|---|---|---|
| `PathsHAL` | `core/hal/paths.py` | Rutas de datos, caché, logs, modelos | `%LOCALAPPDATA%\MagiSystem\` | `~/.local/share/magi/` |
| `UsbHAL` | `core/hal/usb.py` | Enumeración y claim de dispositivos USB | `SetupAPI`/`CfgMgr32` + `libusb-1.0` (backend WinUSB/libusbK) | `pyudev` + `libusb-1.0` |
| `SerialHAL` | `core/hal/serial.py` | Puertos serie, DTR/RTS, baudios no estándar | `COM*` vía `pyserial` (`win32` backend) | `/dev/ttyACM*`, `/dev/ttyUSB*` |
| `HotplugHAL` | `core/hal/hotplug.py` | Eventos de conexión/desconexión en caliente | `CM_Register_Notification` + bomba `WM_DEVICECHANGE` en hilo dedicado | `pyudev.MonitorObserver` sobre netlink |
| `ElevationHAL` | `core/hal/elevation.py` | Elevación granular de privilegios | Broker `magibroker.exe` con manifiesto `requireAdministrator` | `polkit` (`pkexec`) + grupos `dialout`/`plugdev` |
| `ProcessHAL` | `core/hal/process.py` | Lanzar, supervisar y matar árboles de procesos | Job Objects (`CreateJobObject`) | `setsid` + grupos de proceso + `SIGTERM`/`SIGKILL` |
| `ServiceHAL` | `core/hal/service.py` | Trabajos de fondo persistentes | Tarea programada / servicio de Windows | unidad `systemd --user` |
| `FsSnapshotHAL` | `core/hal/fssnap.py` | Instantáneas del espacio de trabajo | `git` embebido + copia dura (`CopyFileEx`) | `git` embebido + `cp --reflink=auto` |
| `InputHAL` | `core/hal/input.py` | Automatización de escritorio | `SendInput` (user32) | `libei`/`XTEST` según sesión (Wayland/X11) |
| `ToolchainHAL` | `core/hal/toolchain.py` | Localización de toolchains externas | nativo, y `wsl.exe -d MagiSystem -- <cmd>` para OpenLane/Magic/netgen | nativo o `podman`/`docker` |

**Decisión:** las toolchains sin build nativo Windows decente (OpenLane 2, Magic 8.3.x, netgen 1.5.x, KLayout en modo batch para LVS) se ejecutan bajo WSL2 con una distro dedicada `MagiSystem` (Ubuntu 24.04) — porque duplicar esos flujos en Windows nativo cuesta más que mantener una distro reproducible.
*Descartado:* MSYS2 para esas herramientas — el flujo OpenLane no está soportado y rompe en cada actualización.

**Decisión:** stack fijo: núcleo Python 3.12.x (asyncio, `pydantic` 2.8+, `structlog` 24.x, `pyserial` 3.5, `libusb1` 3.1.0, `playwright` 1.4x), GUI Tauri 2.x (Rust 1.79+) + React 18.3 + TypeScript 5.5, Monaco Editor 0.50+, xterm.js 5.5, uPlot 1.6, React Flow 12, Zustand 4.5, TanStack Virtual 3 — porque es exactamente el conjunto declarado como no negociable en el encargo y ya cubre editor, terminal, telemetría de alta frecuencia y grafos.

**Topología del puente GUI↔núcleo (justificación en una línea):** el núcleo Python corre como *sidecar* de Tauri y habla WebSocket local en `127.0.0.1` con mensajes JSON tipados, porque así el trabajo largo (impresión, decompilación, flasheo) vive en un proceso que sobrevive al cierre de la ventana y la GUI queda como cliente reemplazable.

Ciclo de vida del sidecar (detallado en §0.4.4 y §0.2):
1. Tauri arranca `magi-core` con `--port 0 --token <aleatorio-32B>`; el núcleo imprime en stdout una línea JSON `{"event":"ready","port":N,"token":"..."}`.
2. Health check: `GET http://127.0.0.1:N/healthz` cada 2 s; tres fallos consecutivos ⇒ estado `DEGRADED` en la GUI.
3. Reinicio: la GUI **no** mata el núcleo; si el núcleo muere, Tauri lo relanza con `--recover <ruta_proyecto>` y el núcleo reconstruye estado desde SQLite + WAL de trabajos.
4. Apagado limpio: `POST /shutdown` ⇒ el núcleo rechaza si hay trabajos `non_cancellable` en curso (flasheo, impresión) y devuelve `409` con la lista; la GUI muestra el diálogo "hay trabajo físico en curso".
5. Sincronía de tipos: los modelos `pydantic` exportan JSON Schema con `model_json_schema()` y `scripts/gen_types.py` los convierte con `json-schema-to-typescript` 15.x a `gui/src/types/generated.ts`; el CI falla si el fichero generado difiere del comiteado.

**Perfil de máquina asumido:** x86-64, 8 hilos, 16 GB RAM, GPU opcional de 8 GB VRAM, 100 GB libres. Todo módulo que exceda esto lo declara en su subsección 11.

**Autonomía local parcial (sustituye al antiguo «offline-first»):** el sistema arranca, abre proyectos, ingiere documentos de cualquier época, decompila, consulta el grafo de código, genera CAD, rebana, habla por USB, imprime, flashea, construye sistemas portables y ejecuta **todas** sus puertas de verificación **sin conexión**. Lo que exige conexión es exclusivamente la deliberación de los tres nodos, porque las inteligencias son de nube (§I.3). Cada área declara en su subsección 9 qué se degrada sin red, y la respuesta ha cambiado en todas: antes «nada»; ahora «lo que necesita una inteligencia».

## I.2 Glosario normativo operativo

Se adoptan íntegramente los términos del encargo (Núcleo, Agente, Modelo, Ronda, Acta, Artefacto, Evidencia, Afirmación, Refutación, Veredicto, Acción, Radio de impacto, HAL) con el significado allí definido. Se añaden cuatro términos operativos que el plan usa de forma recurrente:

| Término | Significado |
|---|---|
| **Unidad reanudable (UR)** | Fragmento idempotente de un trabajo largo, con `unit_id` estable, entrada hasheada y salida persistida en el WAL de trabajos (§Área 6) |
| **Puerta de verificación (PV)** | Comprobación automatizada con criterio numérico que cierra un subpaso de construcción; si falla, el subpaso no se da por terminado (§I.5) |
| **Postcondición física** | Medición del mundo real que confirma que una acción R2/R3 logró su efecto (§Área 9.E) |
| **Perfil de máquina (PM)** | Estructura derivada de `M115`/`M503` que determina el dialecto de G-Code y los límites duros de una impresora (§Área 9.A) |

## I.3 Inferencia en la nube, sin clave de API y sin modelos locales

*Decisión:* **las tres inteligencias son servicios de nube, gratuitos, sin clave de API y sin instalación en el equipo**; MAGI System IDE no descarga pesos, no ejecuta un servidor de inferencia local y no ocupa memoria de vídeo — porque es el requisito del encargo y porque elimina de un golpe los 12–35 GB de descarga, el requisito de GPU y la conmutación de modelos que lastraba el Perfil A.
*Descartado:* la jerarquía de tres niveles de las revisiones anteriores, con `llama.cpp` local como suelo obligatorio. Queda **derogada por completo**. Lo que aquella arquitectura garantizaba —disponibilidad incondicional y funcionamiento sin conexión— **se pierde**, y el §I.3.4 dice exactamente qué se pierde y qué no.

### I.3.1 Qué significa «sin clave de API»

Se accede a cada proveedor **por su vía oficial documentada que no exige una clave de servicio de pago**. Las tres formas admitidas, en orden de preferencia:

| Forma | Cómo autentica | Ejemplo de uso en el sistema |
|---|---|---|
| **Cliente oficial con sesión de usuario** | El usuario inicia sesión una vez en la herramienta oficial del proveedor (flujo de dispositivo o navegador); el token de sesión lo guarda esa herramienta, no MAGI | La CLI oficial que el usuario ya tenga instalada y autenticada con su cuenta personal |
| **Punto final público documentado sin credencial** | El proveedor publica un endpoint abierto con límite por dirección o por sesión anónima | Servicios de inferencia con nivel abierto documentado |
| **Sesión propia del usuario en un portal del proveedor** | El usuario inicia sesión él mismo, una vez, en el navegador gobernado del Área 19, y el sistema reutiliza esa sesión **sólo** donde el proveedor ofrece un punto final programático para clientes de sesión | Portales que documentan acceso programático con sesión |

**Regla dura, sin excepción:** cuando un proveedor **sólo** ofrece una interfaz conversacional para personas y **no** publica ninguna vía programática, ese proveedor **no se integra**. No se simula a un usuario tecleando en un chat. Esto ya estaba en la restricción del §I.3 de la primera revisión y **se mantiene intacto** ahora que no hay suelo local: la tentación es mayor y la respuesta es la misma. La lista negra permanente del **CTL-7** (§19.4) es la que lo hace cumplir.

**Lo que el sistema nunca guarda:** claves de servicio. `config` rechaza cualquier campo que parezca una clave de API con `CredentialRefused`, y la interfaz explica por qué: si un día hace falta una, el diseño ha cambiado y debe discutirse, no colarse en un fichero de configuración.

### I.3.2 Registro de proveedores de nube y asignación a los nodos

`config/providers.yaml` — declarativo, sin secretos, y **con la ventana de recuperación como campo de primera clase**:

```yaml
providers:
  - id: prov-a
    access: official_cli            # official_cli | open_endpoint | session_portal
    auth: user_login                # nunca api_key
    models: [{name: "…", ctx: 200000, vision: true, tools: true, structured: "schema+retry"}]
    quota: {unit: requests, limit: 50, window_hours: 5, recovery: rolling}
    observed: {limit_seen: 47, window_hours_seen: 5.2, last_exhausted_at: null}
    health: {latency_ms_ewma: 3100, error_rate_ewma: 0.02, circuit: closed}
  - id: prov-b
    access: open_endpoint
    auth: none
    models: [{name: "…", ctx: 32768, vision: false, tools: false, structured: "schema+retry"}]
    quota: {unit: tokens, limit: 1000000, window_hours: 24, recovery: fixed_utc_midnight}
```

**Asignación a los tres nodos.** La regla de diversidad del sistema deja de ser «familias de pesos distintas» y pasa a ser **proveedores distintos**: MELCHIOR • 1, BALTHASAR • 2 y CASPER • 3 se sirven, siempre que haya al menos tres proveedores sanos, desde **tres proveedores distintos**. Con dos, el juez CASPER • 3 se aísla en el suyo y los otros dos comparten, marcando `diversity: partial`. Con uno solo, `diversity: degraded` y se fuerza la divergencia por temperatura, semilla y orden de contexto, exactamente como antes. La identidad completa de cada uno se declara siempre (§I.8), y ahora incluye el proveedor y la cuota restante.

### I.3.3 La cuota es un recurso planificable, no un accidente

Ésta es la parte que la arquitectura anterior no necesitaba y ahora es esencial. Un trabajo largo **atravesará varias ventanas de cuota**, y eso deja de ser un fallo para convertirse en una condición normal de operación.

- **Libro de cuotas** (`quota_ledger`): por proveedor, unidad (peticiones o tokens), límite **declarado** y límite **observado**, consumo en la ventana actual, instante de agotamiento y **hora prevista de recuperación**. El observado manda sobre el declarado en cuanto difieren: el sistema aprende el límite real chocando **una vez**, no repetidamente.
- **Reserva antes de gastar.** Antes de cada llamada se reserva la cuota estimada; si no alcanza, no se llama. El sistema no descubre su límite por error.
- **Suspensión y reanudación por ventana.** Cuando todos los proveedores capaces están agotados, el trabajo **no falla: se suspende** con estado `WAITING_QUOTA`, con la hora prevista de reanudación visible en la interfaz («continúa a las 19:40, dentro de 2 h 12 min»), y se reanuda solo. Esto sólo es tolerable porque el **Área 18** garantiza que la memoria sobrevive íntegra a la suspensión: se retoma exactamente donde se dejó, sin resumir nada.
- **Planificación de deliberaciones.** El planificador estima el coste de una deliberación completa (§T7) y **no la inicia** si no hay cuota para al menos las tres rondas mínimas; prefiere esperar a empezar y quedarse a medias.
- **Reparto entre nodos.** Cuando la cuota escasea, se prioriza en este orden: CASPER • 3 (sin juez no hay veredicto), luego MELCHIOR • 1, luego BALTHASAR • 2 — y si sólo alcanza para dos, se ejecuta una ronda con crítica diferida que se completa al recuperarse la cuota, marcándolo en el acta.

### I.3.4 Qué se pierde y qué no al no haber modelos locales (dicho sin adornos)

**Se pierde:** el funcionamiento sin conexión de todo lo que necesita una inteligencia; la disponibilidad garantizada (ahora depende de cuotas ajenas); la reproducibilidad exacta (un proveedor puede cambiar su modelo sin avisar, y por eso `weights_sha256` se sustituye por `provider_model_version` **observada y registrada**, con detección de cambio); y la garantía de privacidad por construcción, que era el argumento más fuerte del diseño anterior.

**Se conserva íntegro, y no es poco:** todo lo determinista. Ghidra, Rizin, Unicorn, QEMU, las pruebas diferenciales, KiCad, Yosys, OpenLane, el rebanador, el control de la impresora, el flasheo, la cascada de ingesta del Área 15, los sistemas portables del Área 16, el grafo de código del Área 13, el recálculo numérico del Área 2, la validación de citas y **todas las puertas de verificación**. Es decir: **la mitad del sistema que produce evidencia sigue funcionando sin conexión**; la que delibera, no.

**La consecuencia sobre la privacidad, que es la más grave.** Sin modelo local, la clase `local_only` del §14.3 —fotogramas de la pantalla del usuario, páginas de un expediente, volcados de firmware, corpus normativo— **ya no puede analizarse con una inteligencia sin salir del equipo**. La respuesta del plan es no fingir que el problema no existe: esa clase pasa a llamarse **`no_enviar`** y su contenido **no se envía a ningún proveedor**; lo que se hace con ella es (a) procesarla con las herramientas deterministas, que siguen siendo locales, y (b) **pedir permiso explícito por unidad de contenido** si el usuario quiere que una inteligencia la vea, con el proveedor concreto nombrado en el diálogo. Si el usuario no da permiso, el sistema entrega el análisis determinista y **declara qué no ha podido analizar**. Es peor que antes. Es lo que hay, y se dice.
## I.4 Fronteras legales codificadas como controles técnicos

Tres controles, con su punto exacto de aplicación (no son advertencias en prosa; son código especificado):

- **CTL-1 `no_redistribute_proprietary`** — Punto de aplicación: `core/artifacts/packager.py::pack_artifact()`, antes de escribir cualquier `.zip`/`.tar.zst` de salida. Regla: todo blob cuyo registro `Evidence.origin_class` sea `device_dump`, `bios`, `firmware` o `rom` se rechaza con `PackagingRefused(code="CTL1")`. Se permite leerlos del dispositivo del usuario y trabajar con ellos **localmente**; nunca empaquetarlos.
- **CTL-2 `derivative_risk_tagging`** — Punto de aplicación: `modules/re/decompile/pipeline.py::emit_artifact()`. Todo artefacto generado a partir de C decompilado propietario recibe `Artifact.derivative_risk = "high"` y su registro de procedencia enlaza el binario origen (hash, dispositivo, fecha). La GUI muestra ese distintivo en rojo en el Inspector de Procedencia.
- **CTL-3 `provenance_isolation`** — Punto de aplicación: `modules/re/synth/clean_room.py`. Cuando el objetivo es reimplementar, el pipeline separa físicamente dos espacios: `analysis/` (ve el binario; produce `spec.intermediate.json`, sin código) e `impl/` (ve sólo `spec.intermediate.json`). El registro `clean_room_ledger` guarda, por sesión de agente, qué hashes de entrada vio cada espacio. Cualquier intento de que un agente con rol `impl` lea un blob marcado `analysis-only` se rechaza en la capa de capacidades (`fs.read` restringido por prefijo).

## I.5 Convención de pasos y subpasos con puertas de verificación

Todo el plan usa una numeración de construcción común, exigida por el encargo del usuario para poder verificar cada parte antes de seguir:

- **Paso** `Pn` — unidad de construcción de un área (n = número de área, con letra de secuencia: `P0.a`, `P0.b`, …).
- **Subpaso** `Pn.x.y` — tarea concreta de un paso.
- **Puerta de verificación** `PV-n.x.y` — comprobación automatizada, con **criterio numérico o binario explícito**, que cierra el subpaso. Se implementa como test en `tests/gates/test_gate_<n_x_y>.py` y se ejecuta con `pytest -m gate -k gate_<n_x_y>`.
- **Regla dura:** ningún paso se declara terminado con una PV en rojo; ningún área avanza a la siguiente fase de la hoja de ruta con PV pendientes. El CI local (`make gates`) ejecuta todas las PV acumuladas y publica `reports/gates.json`. Esta es la defensa estructural contra "descubrir los bugs al final".

## I.6 Identidad MAGI: los tres nodos, el núcleo ATLAS-FORGE y la nomenclatura

**Decisión:** el producto se llama **MAGI System IDE**; su motor de ingeniería y síntesis se llama **ATLAS-FORGE**; y la deliberación la ejecutan tres nodos con nombre propio — **MELCHIOR • 1**, **BALTHASAR • 2** y **CASPER • 3** — porque un sistema que decide por confrontación necesita que cada voz tenga identidad estable, visible y auditable, no una etiqueta genérica intercambiable.
*Descartado:* mantener los nombres genéricos «A / B / C» — funcionan en un diagrama, pero en una interfaz donde el usuario arbitra disputas a las tres de la mañana, la identidad estable de cada nodo (su modelo, su historial de aciertos, su sesgo conocido) es información operativa.

| Nodo | Rol funcional | Enfoque | Rol popperiano | Prompt |
|---|---|---|---|---|
| **MELCHIOR • 1** | Arquitecto e Ingeniero de Sistemas | Diseño de arquitectura, síntesis de código, construcción de modelos, optimización técnica y avance del conocimiento del sistema | **Creador / Sintetizador** | `prompts/roles/melchior.md.j2` |
| **BALTHASAR • 2** | Auditor de Seguridad y Falsacionista | Cognición hostil, pruebas de estrés, búsqueda de vulnerabilidades, refutación popperiana, auditoría de límites HAL y legales, detección de modos de fallo | **Crítico Hostil / Falsacionista** | `prompts/roles/balthasar.md.j2` |
| **CASPER • 3** | Juez Operativo y Árbitro de Concordia | Evaluación de evidencia empírica frente a refutaciones, resolución de discrepancias, arbitraje de consenso, cumplimiento de políticas y emisión de veredictos vinculantes | **Juez / Árbitro de Concordia** | `prompts/roles/casper.md.j2` |

**Ampliación del mandato respecto de la versión anterior del plan.** Los tres roles conservan íntegramente lo definido en el Área 3, y se les añade el enfoque declarado arriba:
- **MELCHIOR • 1** asume además la *responsabilidad de avance del conocimiento del sistema*: cuando su propuesta sobrevive, debe emitir el **delta de conocimiento** — qué hecho nuevo queda establecido, con qué evidencia y con qué caducidad — que se escribe en el grafo de MAGI-MEM (Área 13) como nodo `Knowledge` y queda disponible para las rondas siguientes. Una propuesta que sobrevive y no deja delta de conocimiento es trabajo perdido.
- **BALTHASAR • 2** amplía su taxonomía con dos frentes obligatorios de auditoría en toda acción R2/R3: **límites del HAL** (¿esta acción asume una capacidad que la política no concede, o un comportamiento del SO que sólo se da en una de las dos plataformas?) y **límites legales** (¿esta acción viola CTL-1, CTL-2 o CTL-3, o los términos de un proveedor?). Ambos frentes producen refutaciones de tipo `suposicion` y `normativa` respectivamente, y su ausencia en un turno de BALTHASAR sobre una acción R2/R3 invalida el turno.
- **CASPER • 3** emite **veredictos vinculantes**: su salida no es una opinión que el ejecutor pueda ignorar, sino la condición de entrada del Área 8. Se añade a su mandato el **arbitraje de concordia**: cuando MELCHIOR y BALTHASAR coinciden pero la evidencia no sostiene la coincidencia, CASPER debe declarar `undecided` con acción — la concordancia entre dos modelos **no** es evidencia, y confundirlas es el modo de fallo que más barato sale y más caro cuesta.

**Nomenclatura de código (normativa).** Producto y binarios: `magi` (Linux), `MagiSystem` (directorios de datos), `magi-core` (núcleo Python), `magi-mcp` (servidor MCP), `magibroker.exe` (broker elevado en Windows), `magi-estop` (binario auxiliar de parada). Bus de eventos: `MagiBus`. Comandos Tauri: `magi_*`. El identificador de rol en todos los esquemas JSON, tablas y métricas es la cadena `MELCHIOR`, `BALTHASAR` o `CASPER` — nunca `A`, `B` ni `C`, para que un acta sea legible sin diccionario.

## I.7 Integración de tecnologías externas: MAGI-MEM y MAGI-ROUTE

El plan incorpora dos proyectos libres analizados y adoptados como sustrato de dos capacidades que antes estaban resueltas de forma más pobre.

**MAGI-MEM ← `DeusData/codebase-memory-mcp`** (servidor MCP en C, binario estático, licencia y versión a fijar en el commit adoptado). Aporta un **grafo de conocimiento persistente del código** construido con 155+ gramáticas *tree-sitter* vendorizadas, almacenado en SQLite WAL, consultable con un subconjunto de openCypher de sólo lectura, con embeddings `nomic-embed-code` (768 dimensiones, int8) compilados dentro del binario, procesamiento 100 % local y sin telemetría. Sustituye en el Área 5 la exploración fichero a fichero y el `index.jsonl` plano por una estructura navegable con aristas `CALLS`, `IMPORTS`, `IMPLEMENTS`, `HTTP_CALLS` y demás. Se desarrolla íntegramente en el **Área 13**.

**MAGI-ROUTE ← `diegosouzapw/OmniRoute`** (pasarela de IA, licencia MIT, Node/Electron). Aporta un **endpoint único compatible con OpenAI** en `http://127.0.0.1:20128/v1` que agrega proveedores por sus **interfaces oficiales**, con múltiples estrategias de enrutado, tres capas independientes de resiliencia, compresión de prompts y telemetría de coste por petición. Sustituye en el Área 6 la implementación propia de registro de proveedores, cortacircuitos y cubo de fichas por un sustrato probado, dejando al Área 6 el papel de **contrato de política** (qué capacidad exige cada tarea, qué se degrada, cómo se marca el acta). Se desarrolla íntegramente en el **Área 14**.

**Decisión:** ambos se adoptan **como procesos separados con interfaz declarada** (MCP por stdio en el caso de MAGI-MEM; HTTP compatible con OpenAI en el de MAGI-ROUTE), nunca como librerías enlazadas ni como forks — porque así el sistema conserva su capacidad de funcionar sin ellos (suelo local del §I.3 intacto), la actualización de cualquiera de los dos no obliga a recompilar MAGI System IDE, y las licencias de ambos quedan limpiamente aisladas de la del producto.
*Descartado:* reimplementar sus funciones dentro del núcleo — habría costado meses y habría producido una versión peor de dos cosas que ya existen, probadas y libres.

**Regla de honestidad sobre las cifras de ambos proyectos.** Sus README declaran métricas llamativas (indexar el núcleo de Linux en 3 minutos, 99,2 % de reducción de tokens, ~1,53 · 10⁹ tokens gratuitos mensuales agregados, 15–95 % de compresión de prompt). **Ninguna de esas cifras se da por buena en este plan**: cada una entra como **afirmación falsable** con su banco de medición propio en el Área 13 (§13.8) y el Área 14 (§14.8), y el plan fija umbrales de aceptación propios, más conservadores, por debajo de los cuales la integración se revierte al camino anterior. Las discrepancias detectadas entre distintas partes de su documentación (14 frente a 15 herramientas MCP; 155 frente a 158 lenguajes; 14 frente a 19 estrategias de enrutado; 37 frente a 104 herramientas MCP en la pasarela) se resuelven de una única manera: **se fija un commit concreto, se enumera lo que ese commit expone realmente con `list_projects`/`GET /v1/models` y la enumeración de herramientas MCP, y esa enumeración —no el README— es la que entra en el contrato del sistema** (PV-13.a.1 y PV-14.a.1).


## I.8 Identidad de modelo declarada: cada nodo dice siempre qué inteligencia está usando

*Decisión:* **ninguna salida de un nodo MAGI es válida sin su bloque `model_identity` completo**, y ese bloque se muestra en la interfaz junto a cada intervención, se persiste en el acta y en `model_run`, y viaja con todo artefacto — porque en un sistema donde tres modelos discuten, cambian de proveedor a mitad de trabajo y se degradan cuando falta memoria, saber **quién dijo qué y con qué cerebro** no es un detalle de auditoría: es la condición para poder confiar en la conclusión.
*Descartado:* mostrar sólo un nombre corto («modelo local») — es lo que hace imposible explicar después por qué dos ejecuciones dieron resultados distintos.

**Campos obligatorios del bloque, todos, en cada turno:**

| Campo | Ejemplo | Por qué es obligatorio |
|---|---|---|
| `display` | `Qwen2.5-Coder 7B Instruct · Q5_K_M · local` | Es lo que ve el usuario; una sola línea legible |
| `family` | `qwen2.5-coder` | Sostiene la regla de diversidad (§I.3): dos nodos no comparten familia |
| `params_b` | `7.6` | El tamaño explica la calidad esperable |
| `quant` | `Q5_K_M` | Dos cuantizaciones del mismo modelo no son el mismo modelo |
| `ctx` | `32768` | Determina qué se podó del contexto |
| `provider` | `prov-a` \| `claude-code-cli` \| `magi-route:<id>` | Local o remoto, y cuál |
| `endpoint` | `127.0.0.1:8081` | Prueba de que no salió del equipo |
| `provider_model_version` | `2026-07-11` | **Sustituye al hash de pesos**, que en la nube no existe: es la versión que el proveedor declara, **observada y registrada**, con detección de cambio (§14.4b) |
| `quota_left` | `31 de 50 · repone a las 19:40` | Cuánta cuota queda en la ventana actual y cuándo vuelve; sin esto no se puede planificar |
| `temperature`, `top_p`, `seed` | `0.25`, `0.9`, `20260802` | Reproducibilidad y diversidad forzada en modo degradado |
| `grammar` | `claims.gbnf` | Qué gramática restringió la salida |
| `runtime`, `accel` | `llama.cpp b3600`, `CUDA` | Explica latencia y diferencias numéricas |
| `degraded` | `false` \| `"misma familia que MELCHIOR"` | Si la diversidad se rompió, se dice |

**Dónde aparece, sin excepción:** (1) bajo el nombre de cada nodo en la cabecera de la interfaz, en una línea; (2) en cada mensaje de la conversación, en su cabecera plegable; (3) en el acta, en `model_identity` y en cada `model_used` de cada fase de cada ronda; (4) en la tabla `model_run`; (5) en el pie de todo informe exportado, con la tabla completa de qué modelo produjo qué tramo (esto ya lo exigía §6.5 y ahora se refuerza); y (6) en el panel de configuración, donde además se puede cambiar.

**Regla de cambio a mitad de deliberación:** si un nodo cambia de modelo entre rondas —por caída de proveedor, por cuota agotada o por decisión del usuario— la interfaz lo marca **en la propia línea temporal de la conversación** con una franja y el texto «a partir de aquí, BALTHASAR • 2 pasa a usar …», y el acta registra ambas identidades con el número de ronda en que ocurrió el cambio. El validador rechaza un acta donde `model_used` cambie sin que exista el registro de cambio correspondiente.

**Deriva silenciosa del proveedor (riesgo propio de la nube).** Un proveedor puede cambiar el modelo detrás del mismo nombre sin avisar, y eso rompería en silencio la comparabilidad entre dos ejecuciones. Contramedida: una **sonda canaria** —tres instrucciones fijas con respuesta conocida y temperatura cero— se ejecuta al primer uso de cada ventana de cuota; si la respuesta difiere de la registrada más allá de un umbral, se emite `provider.model_drift`, se anota en el acta de toda deliberación en curso y **las comparaciones con resultados anteriores dejan de ser válidas** hasta recalibrar. Coste: tres llamadas cortas por ventana, que se reservan en el libro de cuotas como cualquier otra.

**Verificación:** `PV-3.a.4` — sobre 200 turnos, el 100 % lleva bloque completo; se corrompe un campo en 20 de ellos y los 20 turnos se rechazan. `PV-10.b.4` — sobre 50 mensajes en pantalla, el 100 % muestra la línea de identidad sin necesidad de abrir nada.


---

# Parte II — Desarrollo por áreas

## ÁREA 0 — Arquitectura global, modelo de datos y fundaciones

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA** (sólo software libre y la computadora).

### 0.1 Propósito y alcance

Resuelve la existencia misma del sistema como sistema: define quién es dueño del estado, cómo se comunican los procesos, cómo se persiste todo lo que ocurre, cómo se demuestra de dónde salió cada conclusión y cómo se conceden capacidades peligrosas. Sin esta área, las doce restantes son doce programas sueltos que comparten carpeta.

Queda **explícitamente fuera**: la lógica de dominio de cualquier área (forense, RE, fabricación), la interfaz gráfica (Área 10), y las políticas de selección de proveedor (Área 6, que consume la infraestructura definida aquí).

**Consume:** nada (es la raíz). **Alimenta:** las trece áreas restantes, sin excepción — todas persisten en su modelo de datos, emiten en su bus, declaran capacidades en su política y publican procedencia en su grafo.

### 0.2 Arquitectura

Componentes con responsabilidad única:

- `core/kernel.py` — **Núcleo**: único dueño del estado y del bucle asyncio principal. No hace trabajo de dominio; supervisa.
- `core/bus.py` — **Bus de eventos** `MagiBus`: publicación/suscripción tipada en proceso.
- `core/store/` — **Persistencia**: `sqlite_store.py` (estado transaccional), `cas.py` (blobs), `duck.py` (analítica), `vector.py` (índice vectorial).
- `core/prov/graph.py` — **Grafo de procedencia**.
- `core/policy/engine.py` — **Motor de capacidades**.
- `core/sched/scheduler.py` — **Planificador de trabajos** con prioridades y presupuesto de recursos.
- `core/jobs/wal.py` — **WAL de trabajos** (unidades reanudables).
- `core/obs/` — **Observabilidad**: `log.py` (structlog→JSONL), `trace.py` (OpenTelemetry a fichero), `metrics.py`.
- `core/rpc/ws_server.py` — **Servidor WebSocket** para la GUI.
- `core/supervisor/procman.py` — **Supervisor de procesos efímeros** (Ghidra, KiCad, slicer, Yosys, OpenLane).

Diagrama maestro del sistema (flechas etiquetadas por tipo de dato):

```
                         ┌───────────────────────────────────────────────┐
                         │      SHELL TAURI 2.x  (Rust + React 18)       │
                         │  paneles §10.A · debate §10.B · política §10.C│
                         └───────┬───────────────────────────▲───────────┘
                        JSON tipado│ (comandos, aprobaciones) │ eventos del bus (JSON)
                                   ▼                          │
┌──────────────────────────────────────────────────────────────────────────────┐
│  NÚCLEO PYTHON 3.12  (sidecar; ÚNICO DUEÑO DEL ESTADO)                        │
│  ┌────────────┐   evento tipado   ┌──────────────┐   trabajo   ┌───────────┐ │
│  │  MagiBus     │◄─────────────────►│ Planificador │────────────►│ WAL jobs  │ │
│  └─────┬──────┘                   └──────┬───────┘             └─────┬─────┘ │
│        │ evento                          │ spawn supervisado         │ UR    │
│        │                                 ▼                           ▼       │
│        │                         ┌──────────────┐            ┌──────────────┐│
│        │                         │  procman     │            │  SQLite WAL  ││
│        │                         └──────┬───────┘            │  CAS  DuckDB ││
│        │                                │ argv+env           │  sqlite-vec  ││
│        ▼                                ▼                    └──────▲───────┘│
│  ┌──────────────┐   capacidad     ┌──────────────────────────┐      │        │
│  │ policy/engine│◄───solicitud────│  MÓDULOS DE DOMINIO 1–12 │──────┘ filas  │
│  └──────┬───────┘   concede/niega └───┬───────┬───────┬──────┘               │
│         │ DENY→action.failed          │       │       │                      │
└─────────┼─────────────────────────────┼───────┼───────┼──────────────────────┘
          │                    llamada  │       │ USB   │ argv
          ▼                    HTTP     ▼       ▼       ▼
   ┌─────────────┐        ┌───────────────┐ ┌────────┐ ┌───────────────────────┐
   │ AUDITORÍA   │        │ proveedor de nube  │ │ HAL USB│ │ TOOLCHAINS EFÍMERAS   │
   │ append-only │        │ (local, GBNF) │ │ serie  │ │ Ghidra·KiCad·Slicer   │
   │ hash-chain  │        └───────┬───────┘ └───┬────┘ │ Yosys·OpenLane·PIO    │
   └─────────────┘   tokens       │             │trama └───────────┬───────────┘
                                  ▼             ▼                  │ stdout/artefacto
                          ┌───────────────────────────────────────▼───────────┐
                          │  PUNTO DE FALLO CRÍTICO: verificación de resultado │
                          │  (postcondición §8.5) — sin ella no hay artefacto  │
                          └────────────────────────────────────────────────────┘
```

Puntos de decisión visibles en el diagrama: (a) el motor de política decide antes de cualquier efecto; (b) el planificador decide si hay presupuesto de RAM/VRAM antes de lanzar; (c) la verificación de postcondición decide si el resultado se convierte en artefacto o en refutación.

**Topología de procesos (exacta).** Cinco clases: (1) `magi.exe`/`magi` — shell Tauri, 1 instancia; (2) `magi-core` — núcleo Python, 1 instancia, dueño del trabajo; (3) el proveedor de nube asignado — 0..2 instancias (una de texto, una de visión) gestionadas por el núcleo; (4) procesos efímeros de toolchain — 0..N, siempre hijos de `procman` dentro de un Job Object (Windows) o grupo de proceso (Linux); (5) `magibroker` — 0..1, proceso elevado de catálogo cerrado (§10.C).

**La GUI no es dueña del trabajo.** Si el usuario cierra la ventana con una impresión 3D en curso o un flasheo a medias: el núcleo sigue vivo (en Windows sobrevive porque no es hijo del Job Object de la GUI; en Linux porque se lanza con `setsid`), la impresión continúa, la GUI al reabrir se reconecta por WebSocket, lee `job.progress` y reconstruye la vista desde SQLite. Si el usuario intenta cerrar el núcleo, `POST /shutdown` devuelve `409` mientras existan trabajos `non_cancellable`. Procesos huérfanos: cada proceso hijo hereda `MAGI_PARENT_PID`; un barrido en el arranque mata los que apunten a un PID inexistente y registra `orphan.reaped`.

### 0.3 Contratos e interfaces

**Bus de eventos.** *Decisión:* `MagiBus` sobre `asyncio.Queue` tipadas con modelos pydantic v2, in-process, con difusión a la GUI por WebSocket — porque un broker externo (Redis/NATS) añade una dependencia de instalación y un modo de fallo para cero beneficio en un monolito de escritorio.
*Descartado:* NATS embebido — sobra para un único proceso dueño del estado.

Semántica de entrega: **at-most-once en memoria, at-least-once en disco** — todo evento con `critical=True` se persiste en `event_log` antes de difundirse, de modo que un reinicio replica lo perdido. Backpressure: cada suscriptor tiene cola acotada (`maxsize=1024`); al llenarse, los eventos de clase `telemetry.*` e `inference.token` se **descartan por el más antiguo** con contador `bus.dropped{topic}`, y los de clase `action.*`, `print.*`, `flash.*` **bloquean al productor** (nunca se pierden).

Catálogo completo de eventos (payload en §T2): `device.attached`, `device.detached`, `telemetry.sample`, `debate.turn`, `debate.verdict`, `action.proposed`, `action.approved`, `action.executed`, `action.failed`, `artifact.created`, `job.progress`, `provider.degraded`, `print.layer`, `print.fault`, `flash.progress`, `inference.token`. Se añaden nueve eventos propios del sistema, también normativos: `orphan.reaped`, `policy.denied`, `gate.result`, `measurement.recorded`, `corpus.updated`, `invention.derived`, `capability.requested`, `snapshot.created`, `estop.triggered`.

Firmas públicas del núcleo (`core/kernel.py`):

```python
async def publish(event: BusEvent) -> None: ...
def subscribe(topic_glob: str, handler: Callable[[BusEvent], Awaitable[None]], *, maxsize: int = 1024) -> SubscriptionId: ...
async def submit_job(spec: JobSpec, *, priority: Priority = Priority.BATCH) -> JobId: ...
async def cancel_job(job_id: JobId, *, reason: str) -> CancelResult: ...
def request_capability(module: str, cap: Capability, ctx: CapContext) -> Grant | Denial: ...
async def record_artifact(path: Path, meta: ArtifactMeta) -> ArtifactId: ...
async def provenance_of(artifact_id: ArtifactId, depth: int = -1) -> ProvenanceGraph: ...
```

Endpoints IPC (WebSocket `ws://127.0.0.1:<port>/rpc`, autenticado por token de arranque): `rpc.hello`, `rpc.subscribe`, `rpc.unsubscribe`, `rpc.job.submit`, `rpc.job.cancel`, `rpc.action.approve`, `rpc.action.reject`, `rpc.policy.get`, `rpc.policy.set`, `rpc.provenance.get`, `rpc.estop`, `rpc.project.open`, `rpc.project.close`, `rpc.snapshot.create`, `rpc.snapshot.restore`. Cada uno con `request_id`, `payload` validado por esquema y respuesta `{ok, result|error{code,message,details}}`.

**Modelo canónico de datos.** DDL completo en §T3; entidades: `project`, `artifact`, `evidence`, `claim`, `refutation`, `verdict`, `debate_round`, `action`, `measurement`, `device`, `job`, `provider_quota`, `invention`, `prompt`, `model_run`, más las auxiliares `event_log`, `audit_log`, `provenance_edge`, `capability_grant`, `corpus_doc`, `corpus_chunk`, `job_unit`, `clean_room_ledger`, `machine_profile`, `gate_result`.

**Almacenamiento (decisiones).**
*Decisión:* SQLite 3.45+ en modo WAL (`journal_mode=WAL`, `synchronous=NORMAL`, `busy_timeout=5000`) para estado transaccional — porque un único escritor con lecturas concurrentes es exactamente el patrón del núcleo.
*Decisión:* almacén de blobs direccionado por contenido (CAS) SHA-256 con fan-out de 2 niveles (`ab/cd/abcd…`) — porque deduplica dumps de firmware y escaneos, y hace inmutable la evidencia por construcción.
*Decisión:* DuckDB 1.0.x para consultas analíticas sobre telemetría y resultados, con particiones Parquet por día y dispositivo — porque un `SELECT` sobre 50 millones de muestras en SQLite es inviable y DuckDB lo resuelve en memoria del proceso.
*Decisión:* `sqlite-vec` 0.1.x como índice vectorial (con FAISS 1.8 como motor alternativo activable si el corpus supera 2 millones de fragmentos) — porque mantiene un único fichero de proyecto y evita un servicio extra.

Árbol en disco (rutas concretas):

```
Windows: %LOCALAPPDATA%\MagiSystem\        Linux: ~/.local/share/magi/
├── models/                 pesos GGUF y mmproj
├── tools/                  toolchains descargadas y verificadas
├── projects/<slug>/
│   ├── project.db          SQLite (estado)
│   ├── analytics.duckdb    DuckDB
│   ├── vectors.db          sqlite-vec
│   ├── cas/ab/cd/<sha256>  blobs inmutables
│   ├── workspace/          espacio de trabajo editable (git embebido)
│   ├── artifacts/          salidas versionadas
│   ├── _quarantine/        zona de cuarentena (nada se borra)
│   └── logs/*.jsonl        logs estructurados y trazas OTel
└── policy/global.yaml      política de capacidades por defecto
```

**Procedencia y reproducibilidad.** Todo artefacto lleva: `inputs_hash` (Merkle de los hashes de entrada), `tool_id`+`tool_version`, `seed`, `prompt_hash`, `model_id`+`model_hash` (SHA-256 del GGUF), `params_hash` (temperatura, top_p, gramática), `created_at`, `host_fingerprint`. El grafo es una tabla de aristas `provenance_edge(src_kind, src_id, dst_kind, dst_id, relation)` con `relation ∈ {derives_from, cites, measured_by, approved_by, refuted_by, produced_by}`. La consulta "¿de dónde salió esta conclusión?" es un CTE recursivo sobre esa tabla, expuesto en `rpc.provenance.get` y renderizado en el Inspector de Procedencia con un clic.

**Observabilidad.** `structlog` 24.x con procesador JSON a `logs/core.jsonl`; esquema mínimo obligatorio por línea: `{ts, level, event, module, project_id, job_id?, round_id?, device_id?, duration_ms?, ok?, err_code?, extra{}}`. Trazas OpenTelemetry (SDK Python 1.26+) con exportador **a fichero local** `logs/otel.jsonl` — sin telemetría remota, nunca. Métricas obligatorias: `tokens_in/out{model,role}`, `latency_ms{model,stage}`, `refutation_success_rate{area}`, `print_time_s`, `flash_fail_rate{programmer}`, `gate_pass_rate{phase}`, `bus.dropped{topic}`.

**Modelo de seguridad y capacidades.** Capacidades atómicas: `fs.read`, `fs.write`, `net.out`, `usb.claim`, `serial.write`, `proc.spawn`, `proc.elevate`, `input.synthesize`, `registry.write`. Cada módulo declara las suyas en `module.yaml`; el núcleo concede según `policy/global.yaml` + `projects/<slug>/policy.yaml` (formato completo en §10.C). Toda concesión y toda denegación se escriben en `capability_grant` y en `audit_log`.

**Concurrencia y presupuesto de recursos.** Semáforos globales: `INFER_TEXT=1`, `INFER_VLM=1`, `TOOLCHAIN_HEAVY=1` (OpenLane, Ghidra analyze, Verilator build), `TOOLCHAIN_LIGHT=3`, `DEVICE_IO=∞` (limitado por dispositivo). El planificador mantiene un presupuesto declarado: cada `JobSpec` incluye `req_ram_mb`, `req_vram_mb`, `req_disk_mb`; no se admite un trabajo si `Σ(reservado)+req > 0,85 × total`. Prioridades: `INTERACTIVE(0) > PHYSICAL_SAFETY(1) > BATCH(2)`. Un OpenLane (`req_ram_mb=8192`) nunca se lanza mientras el VLM está residente en RAM en el Perfil B: el planificador lo encola y lo indica en la GUI.

**Cancelación.** Protocolo cooperativo: cada trabajo largo implementa `async def step()` y consulta `ctx.cancel_requested` entre unidades reanudables; al cancelar, escribe punto de control y sale con estado `CANCELLED_AT_UNIT=<n>`. Trabajos **no cancelables** (lista cerrada): flasheo en curso (`flash.*` entre `erase` y `verify`), escritura de bootloader, y el bloque de comandos G-Code ya enviado a la impresora hasta el siguiente `ok` — un flasheo a medias no se aborta: se completa o se entra en la rutina de rescate (§9.D).

**Empaquetado, instalación y actualización.** Windows: instalador NSIS generado por `tauri build` (`--target nsis`), sin requerir administrador para instalar en `%LOCALAPPDATA%`. Linux: AppImage + `.deb` (`tauri build --bundles deb,appimage`). Modelos: **no** se empaquetan; en el primer arranque el asistente descarga los GGUF elegidos según el perfil detectado y verifica SHA-256 contra `models/manifest.json` firmado con `minisign`. Actualización: descarga a `tools/staging/`, verificación, y aplicación **sólo** al cerrar sin trabajos activos; un proyecto abierto nunca se migra en caliente. Migraciones de esquema con `alembic` 1.13 y `schema_version` en `project.db`.

**Requisitos no funcionales cuantificados.**

| Requisito | Objetivo | Cómo se mide |
|---|---|---|
| Arranque en frío hasta ventana usable | ≤ 4,0 s (sin cargar modelos) | `gate_0_a_1`: media de 10 arranques |
| Carga del modelo de texto (Perfil A) | ≤ 25 s | log `model.loaded` |
| Latencia de eco de la terminal integrada | ≤ 30 ms p95 | test de 1 000 pulsaciones |
| Telemetría sostenible sin pérdida | ≥ 2 000 muestras/s agregadas | contador `bus.dropped{telemetry.sample} == 0` durante 10 min |
| RAM en reposo (sin modelos) | ≤ 450 MB (núcleo) + ≤ 320 MB (GUI) | RSS medido |
| RAM bajo debate con VLM cargado (Perfil B) | ≤ 13,5 GB | RSS agregado |
| Tamaño del instalador (sin modelos) | ≤ 120 MB | tamaño del artefacto |

### 0.4 Implementación

Estructura de carpetas: ver §T1. Comandos exactos de bootstrap:

```bash
# Linux
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.lock          # hashes fijados con pip-compile --generate-hashes
npm ci --prefix gui
cargo tauri build --bundles deb,appimage
# Windows (PowerShell)
py -3.12 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.lock
npm ci --prefix gui
cargo tauri build --target nsis
```

Tabla de paridad para lo que toca el SO en esta área:

| Elemento | Impl. Windows | Impl. Linux |
|---|---|---|
| Directorio de datos | `%LOCALAPPDATA%\MagiSystem` | `~/.local/share/magi` |
| Supervivencia del núcleo al cerrar la GUI | proceso fuera del Job Object de la GUI + `CREATE_BREAKAWAY_FROM_JOB` | `setsid()` + `start_new_session=True` |
| Matar árbol de procesos | `TerminateJobObject` | `killpg(pgid, SIGTERM)` → `SIGKILL` a 5 s |
| Trabajo persistente en segundo plano | Tarea programada `MagiSystemCore` | unidad `systemd --user` `magi-core.service` |
| Instantánea del espacio de trabajo | `git commit` embebido + copia dura | `git commit` embebido + `cp --reflink=auto` |
| Notificación de eventos críticos | `ToastNotification` (WinRT) | `notify-send` / D-Bus `org.freedesktop.Notifications` |
| Bloqueo de instancia única | mutex nombrado `Global\MagiSystem` | `flock` sobre `~/.local/state/magi/lock` |

### 0.5 Algoritmos

**A0-1 — Admisión de trabajo con presupuesto de recursos.** Complejidad O(log n) por inserción en heap.

```
1.  recibir JobSpec S con prioridad P y requisitos (ram, vram, disk)
2.  validar S contra esquema; si falla → rechazar(code=SCHEMA)
3.  si S.caps ⊄ política_efectiva(proyecto) → rechazar(code=POLICY) y emitir policy.denied
4.  calcular libre_ram = total_ram*0,85 − reservado_ram   (idem vram, disk)
5.  si S.ram ≤ libre_ram ∧ S.vram ≤ libre_vram ∧ S.disk ≤ libre_disk:
6.       reservar; estado=RUNNING; lanzar corrutina; emitir job.progress(0.0)
7.  si no: encolar en heap[P] ordenado por (P, llegada); emitir job.progress(estado=QUEUED)
8.  al terminar/cancelar cualquier trabajo: liberar reservas y reintentar el tope de heap[0], luego heap[1], heap[2]
9.  caso límite: trabajo cuya reserva excede el 85 % del total aun estando el sistema vacío
       → se admite en modo exclusivo (drena todo lo demás antes de arrancar) y se marca exclusive=true
```

**A0-2 — Consulta de procedencia (CTE recursivo).**

```
1.  entrada: artifact_id A, profundidad d
2.  frontera = {(artifact, A)}; visitados = ∅; aristas = ∅
3.  mientras frontera ≠ ∅ ∧ nivel < d:
4.       para cada nodo n en frontera: SELECT * FROM provenance_edge WHERE dst_kind=n.kind AND dst_id=n.id
5.       añadir aristas; nueva_frontera = orígenes no visitados
6.  detectar ciclos por conjunto visitados (un ciclo indica corrupción → emitir gate.result(fail))
7.  devolver grafo con nodos anotados (tool_version, model_hash, seed, prompt_hash)
```

**A0-3 — Cancelación cooperativa con punto de control.**

```
1.  rpc.job.cancel(job_id) → ctx.cancel_requested = True; emitir job.progress(estado=CANCELLING)
2.  el trabajo, entre unidades: si ctx.cancel_requested ∧ tipo ∉ NO_CANCELABLES:
3.       persistir checkpoint {unit_id, salida_parcial, hash_entrada}
4.       liberar recursos (cerrar handles USB, cerrar procesos hijos)
5.       estado = CANCELLED; emitir job.progress(estado=CANCELLED)
6.  si tipo ∈ NO_CANCELABLES: responder 409 con motivo y ETA; continuar
7.  timeout duro de 30 s sin atender la cancelación → escalada: matar árbol de procesos y marcar job.integrity=UNKNOWN
```

### 0.6 Integración con el debate popperiano

El Área 0 no emite afirmaciones de dominio, pero sí tres afirmaciones falsables sobre sí misma, que se someten al Área 3 en cada versión: **(C0-1)** "ningún evento crítico se pierde ante un reinicio duro" — refutable con una prueba de matar el proceso con `SIGKILL` durante 1 000 eventos críticos y comparar `event_log` con el emisor; **(C0-2)** "toda conclusión tiene procedencia completa hasta sus entradas primarias" — refutable buscando artefactos con `provenance_edge` huérfanas (`SELECT` de comprobación); **(C0-3)** "el presupuesto de recursos impide el OOM" — refutable lanzando simultáneamente OpenLane + VLM + Verilator en Perfil B y observando el `oom_kill`. Evidencia admisible: ejecución determinista y medición del sistema, ambas por encima de cualquier argumento (precedencia §3.10). El debate se invoca al cerrar cada fase de la hoja de ruta, no en cada operación: el Área 0 es infraestructura y sus operaciones son R0/R1 deterministas.

### 0.7 Costos, latencia y recursos

Presupuesto de tokens: el Área 0 sólo consume tokens en las tres afirmaciones anteriores, una vez por fase: ≤ 12 000 tokens de entrada y ≤ 4 000 de salida por ronda, con máximo 3 rondas ⇒ ≤ 48 000 tokens por fase. Latencia por etapa: publicación en el bus ≤ 0,2 ms; escritura de evento crítico ≤ 1,5 ms (SQLite WAL, `synchronous=NORMAL`); consulta de procedencia de profundidad 6 ≤ 40 ms; inserción de 10 000 muestras en DuckDB por lote ≤ 120 ms. Recursos: núcleo en reposo ≤ 450 MB RSS; `project.db` crece ≈ 3 MB por 10 000 rondas; el CAS domina el disco (un dump de firmware de PS Vita ronda cientos de MB).

**Regla de salto del debate:** operaciones R0 (lectura pura), deterministas y con salida verificable por hash **no** pasan por debate. Criterio concreto: se salta el debate si `radio ∈ {R0,R1} ∧ determinista == true ∧ coste_verificación < coste_debate`, donde `coste_debate` se estima en 30 s y 20 000 tokens.

**Caché.** Se cachea: resultado de análisis de Ghidra por binario (`clave = sha256(binario) + ghidra_version + script_hash`), embeddings por fragmento (`clave = sha256(texto_normalizado) + modelo_embed`), respuestas de modelo con temperatura 0 (`clave = sha256(prompt_render) + model_hash + params_hash`), y renders de teselas del Área 1 (`clave = sha256(imagen) + parámetros_de_normalización`). Política de invalidación: por cambio de cualquier componente de la clave, y purga LRU cuando `cache/` supera 20 GB. Nunca se cachea con temperatura > 0 salvo que la semilla forme parte de la clave.

### 0.8 Calidad y pruebas

| Caso | Procedimiento | Criterio de éxito |
|---|---|---|
| Camino feliz | Abrir proyecto, emitir 10 000 eventos, cerrar limpio | 0 eventos perdidos; cierre < 2 s |
| Consenso entre agentes | Someter C0-2 al debate con evidencia limpia | Veredicto `survives` con puntuación ≥ 75/100 |
| Desacuerdo total | Someter C0-3 con evidencia contradictoria inyectada | El Juez emite `undecided` y exige acción `medir de nuevo`; no inventa desempate |
| Reinicio duro | `SIGKILL` durante escritura de 1 000 eventos críticos | Tras reinicio, `event_log` contiene ≥ 999 y ningún registro corrupto |
| Presión de memoria | OpenLane + VLM + Verilator en Perfil B | 0 `oom_kill`; ≥ 1 trabajo en cola con motivo visible |
| Procedencia | Generar 200 artefactos encadenados y consultar el más profundo | 100 % con cadena completa; consulta ≤ 40 ms |
| Cancelación | Cancelar decompilación de 6 h al minuto 40 | Punto de control válido; reanudación reprocesa ≤ 1 unidad |
| GUI bajo estrés | 10 000 líneas de log/s + impresión simulada en curso | GUI ≥ 30 fps; `bus.dropped{action.*} == 0` |

El Juez evalúa cada caso con la rúbrica de §3.7, exigiendo evidencia de ejecución (log + medición) y no descripción.

### 0.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta automática | Estado final |
|---|---|---|---|---|
| Núcleo muere | Health check 3× fallido | GUI sin datos | Tauri relanza con `--recover`; reconstrucción desde SQLite+WAL | Operativo, trabajos reanudados |
| SQLite corrupto | `PRAGMA integrity_check` al abrir | Proyecto inusable | Restaurar desde `project.db.bak` rotatorio (3 copias) y replicar `event_log` | Operativo con pérdida ≤ última transacción |
| Disco lleno | Umbral 2 GB libres | Escrituras fallan | Pausar trabajos `BATCH`, purgar caché LRU, avisar | Degradado, sin pérdida |
| WebSocket caído | Ping/pong 10 s | GUI congelada | Reintento con backoff; el trabajo sigue | Núcleo operativo, GUI reconecta |
| Fallo parcial (peor caso): artefacto escrito sin fila en BD | Barrido de reconciliación CAS↔BD al abrir | Artefacto fantasma | Cuarentena del blob + evento `gate.result(fail)` y ticket en GUI | Consistente, con incidencia visible |
| Reloj del sistema retrocede | Comparación con monotónico | Marcas de tiempo incoherentes | Usar `time.monotonic_ns()` para duraciones y marcar `clock_anomaly` | Operativo |

Sin red: el Área 0 no se degrada en absoluto; sólo se desactiva la descarga de modelos y de toolchains.

### 0.10 Riesgos y mitigaciones

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Deriva de tipos GUI↔núcleo | Alta | Medio | Generación automática de TS desde JSON Schema + fallo de CI si difiere |
| Contención del único escritor SQLite | Media | Medio | Escrituras por cola serializada en el núcleo; lecturas por conexiones separadas |
| Crecimiento sin control del CAS | Alta | Medio | Recolección por referencia (blob sin `provenance_edge` durante 30 días → cuarentena) |
| Sobre-ingeniería del bus | Media | Bajo | Catálogo cerrado de eventos; añadir uno requiere fila en §T2 y prueba |
| Elevación mal delimitada | Baja | Alto | Broker con catálogo cerrado (§10.C) y auditoría encadenada por hash |
| Pérdida de trabajo físico por cierre | Media | Alto | Núcleo desacoplado de la GUI + trabajos no cancelables |

### 0.11 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA.** Requiere: Python 3.12.x, Node.js 20 LTS, Rust 1.79+ con `tauri-cli` 2.x, SQLite 3.45+, DuckDB 1.0.x, y 100 GB de disco. Todo es software libre. No hay prerrequisito de hardware ni cuenta de pago.

### 0.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (bus + SQLite + CAS + WebSocket + un evento extremo a extremo) → v1 (planificador, WAL de trabajos, procedencia, política) → completo (DuckDB, vectores, OTel, instalador, actualización).

Pasos y subpasos con puertas de verificación:

- **P0.a Esqueleto de proceso.** P0.a.1 crear venv y árbol de carpetas — **PV-0.a.1**: `pytest tests/gates/test_gate_0_a_1.py` comprueba que existen las 27 carpetas de §T1 y que `import core` funciona. P0.a.2 arrancar el núcleo y responder `/healthz` — **PV-0.a.2**: 10 arranques, `healthz` 200 en ≤ 4,0 s de media. P0.a.3 sidecar desde Tauri con token — **PV-0.a.3**: la GUI recibe `ready` y rechaza una conexión sin token (401).
- **P0.b Bus.** P0.b.1 publicar/suscribir tipado — **PV-0.b.1**: 100 000 eventos, 0 pérdidas en suscriptor no acotado. P0.b.2 backpressure — **PV-0.b.2**: inundar `telemetry.sample` a 20 000/s ⇒ se descartan sólo los de esa clase y `action.*` llega íntegro. P0.b.3 persistencia de críticos — **PV-0.b.3**: prueba de `SIGKILL` con ≥ 999/1 000 recuperados.
- **P0.c Persistencia.** P0.c.1 DDL y migraciones alembic — **PV-0.c.1**: `alembic upgrade head` + `downgrade base` sin error sobre BD con 10 000 filas. P0.c.2 CAS — **PV-0.c.2**: 1 000 blobs, deduplicación ≥ 99 % con entradas repetidas y verificación de hash al leer. P0.c.3 DuckDB — **PV-0.c.3**: inserción de 5 M de muestras y agregación por minuto en ≤ 2 s.
- **P0.d Procedencia y política.** P0.d.1 aristas y consulta recursiva — **PV-0.d.1**: cadena de 200 artefactos resuelta ≤ 40 ms y 0 huérfanos. P0.d.2 motor de capacidades — **PV-0.d.2**: 20 solicitudes, 10 denegadas por política, todas en `audit_log` con hash encadenado válido.
- **P0.e Planificador y cancelación.** P0.e.1 admisión con presupuesto — **PV-0.e.1**: escenario de presión sin `oom_kill`. P0.e.2 cancelación cooperativa — **PV-0.e.2**: reanudación reprocesa ≤ 1 unidad. P0.e.3 no cancelables — **PV-0.e.3**: `shutdown` devuelve 409 con flasheo simulado activo.
- **P0.f Empaquetado.** P0.f.1 instaladores — **PV-0.f.1**: NSIS y AppImage instalan y arrancan en máquina limpia; tamaño ≤ 120 MB. P0.f.2 descarga y verificación de modelos — **PV-0.f.2**: hash incorrecto ⇒ descarga rechazada y mensaje claro.

Métricas de salida del área: 100 % de PV en verde, cobertura de tests ≥ 80 % en `core/`, y el escenario "cerrar la ventana durante una impresión simulada de 40 min" sin pérdida de trabajo.

---

## ÁREA 1 — Enrutador multimodal y análisis forense topográfico

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA** (software libre + VLM local; un escáner es opcional, no requisito).

### 1.1 Propósito y alcance

Convierte cualquier imagen o PDF en una descripción estructurada, medida y falsable de su **topografía visual**: qué tipografía, qué tamaños, qué interlineado, qué márgenes, qué densidad de tinta, qué ruido de sensor, y qué de todo eso es incoherente con el resto del expediente. Su salida es evidencia, no opinión: cada rasgo tiene unidad, coordenada y confianza.

Queda fuera: la interpretación jurídica del contenido (Área 2), la decisión sobre si el documento es válido (eso es dictamen, no medición), y la firma pericial — el sistema produce indicios reproducibles, no peritajes.

**Consume:** Área 0 (bus, CAS, procedencia), Área 7 (prompt del especialista en topografía). **Alimenta:** Área 2 (afirmaciones y citas localizadas), Área 3 (afirmaciones falsables), Área 10 (visor forense), Área 11 (lectura de documentación técnica y de patentes).

### 1.2 Arquitectura

```
 entrada (PDF/JPEG/PNG/TIFF/foto/captura)
        │ bytes + sha256
        ▼
 ┌──────────────────┐  perfil de entrada  ┌────────────────────────┐
 │ CLASIFICADOR DE  │────────────────────►│  ENRUTADOR (tabla 1.4) │
 │ ENTRADA (magic,  │                     └───────┬────────────────┘
 │ pdfinfo, EXIF)   │                             │ pipeline elegido
 └──────────────────┘                             ▼
   ┌───────────────────────────────────────────────────────────────┐
   │ NORMALIZACIÓN: DPI → deskew → perspectiva → iluminación       │
   │  ⚠ punto de fallo: deskew erróneo contamina TODOS los rasgos  │
   └───────┬───────────────────────────────────────┬───────────────┘
    imagen │ normalizada (PNG 16-bit gris + color) │ matriz homográfica H
           ▼                                       ▼
   ┌────────────────┐   cajas baratas   ┌───────────────────────────┐
   │ LAYOUT ENGINE  │──────────────────►│ TESELADOR (solape 12 %)   │
   │ (Tesseract 5.4 │  bbox+baseline    │ respeta líneas base       │
   │  modo layout)  │                   └──────────┬────────────────┘
   └───────┬────────┘                              │ teselas + mapa de coords
           │ geometría                             ▼
           │                              ┌────────────────────┐
           │                              │  VLM LOCAL (Qwen2- │
           │                              │  VL-7B, GBNF JSON) │
           │                              └─────────┬──────────┘
           ▼                                        │ juicio por tesela
   ┌──────────────────────────────────────────────────────────────┐
   │ FUSIÓN GEOMETRÍA↔JUICIO → vector de rasgos de página (128 d)  │
   │  ⚠ decisión: si IoU(caja_layout, caja_VLM) < 0,5 → conflicto  │
   └───────┬──────────────────────────────────────────────────────┘
           │ page_features.json
           ▼
   ┌────────────────────┐  z-scores  ┌────────────────────────────┐
   │ DETECTORES D1..D9  │───────────►│ EVIDENCIA + AFIRMACIONES   │
   │ (§1.5)             │            │ falsables → Área 3         │
   └────────────────────┘            └────────────────────────────┘
```

### 1.3 Contratos e interfaces

Firmas públicas (`modules/forensic/api.py`):

```python
def route_input(path: Path) -> RoutingDecision: ...
def normalize_page(img: np.ndarray, dpi_hint: int | None) -> NormalizedPage: ...
def tile_page(page: NormalizedPage, max_side_px: int, overlap: float = 0.12) -> list[Tile]: ...
def extract_topography(page: NormalizedPage, tiles: list[Tile]) -> PageTopography: ...
def detect_anomalies(dossier: list[PageTopography]) -> list[AnomalyFinding]: ...
def render_overlay(page_id: str, findings: list[AnomalyFinding]) -> Path: ...
```

Sistema de coordenadas canónico: origen en la esquina superior izquierda de la página **normalizada**, eje x a la derecha, eje y hacia abajo, unidad **milímetro con tres decimales** (convertida desde píxeles con el DPI efectivo tras normalización). Toda caja se expresa `{x_mm, y_mm, w_mm, h_mm}` y arrastra `tile_id` y `H` (homografía aplicada) para poder retroproyectar al píxel original del escaneo: `p_orig = H⁻¹ · p_norm`.

Esquema JSON de salida (completo, abreviado sólo en repeticiones de la misma forma):

```json
{
  "page_id": "sha256:...#p3",
  "source_sha256": "…",
  "dpi_effective": 300.0,
  "size_mm": {"w": 210.0, "h": 297.0},
  "normalization": {"deskew_deg": -0.42, "homography": [[1,0,0],[0,1,0],[0,0,1]], "illum_method": "rolling_ball_r=50px"},
  "margins_mm": {"top": 25.1, "bottom": 24.7, "left": 30.2, "right": 20.0},
  "blocks": [
    {
      "block_id": "b1", "role": "body|header|footer|table|signature|stamp|figure",
      "bbox_mm": {"x": 30.2, "y": 25.1, "w": 159.6, "h": 40.3},
      "alignment": "left|right|center|justified", "ink_density": 0.0731,
      "lines": [
        {"line_id": "b1l1", "baseline_y_mm": 28.44, "bbox_mm": {"x":30.2,"y":25.3,"w":159.6,"h":4.1},
         "indent_mm": 0.0, "leading_mm": 5.29, "text_hint": "CLÁUSULA DÉCIMA…",
         "font": {"family_class": "serif_transitional", "family_conf": 0.81,
                  "x_height_px": 9.4, "cap_height_px": 13.1, "size_pt": 11.02,
                  "weight": "bold", "weight_score": 0.71, "italic_angle_deg": 0.3},
         "evidence": [{"kind":"measure","name":"x_height_px","value":9.4,"method":"projection_profile"}]}
      ]
    }
  ],
  "halftone": {"screen_angle_deg": 45.2, "screen_lpi": 85.0, "confidence": 0.62},
  "sensor_noise": {"sigma_flat": 1.83, "prnu_corr": 0.41, "jpeg_qtable_hash": "…"},
  "page_vector": {"dim": 128, "values": [0.021, -0.114, "…"], "schema": "pv-1.0"},
  "conflicts": [{"kind":"layout_vs_vlm","block_id":"b1","iou":0.41,"resolution":"layout_wins"}]
}
```

Eventos emitidos: `artifact.created` (informe y overlays), `job.progress`, `debate.turn` (indirecto vía Área 3). Consume: `job.progress` de sus propios lotes. Tablas propias: `forensic_page`, `forensic_block`, `forensic_line`, `forensic_finding`, `forensic_dossier` (DDL en §T3).

### 1.4 Implementación y enrutado

*Decisión:* PyMuPDF 1.24 para rasterizar y leer la estructura interna del PDF; OpenCV 4.10 para toda la geometría; `pikepdf` 9.x para el análisis de objetos incrementales; `exiftool` 12.x para metadatos; Qwen2-VL-7B-Instruct GGUF en el proveedor de nube asignado con proyector multimodal para el juicio visual — porque cubre rasterizado fiel, geometría, estructura PDF y visión con software libre y sin servicios.
*Descartado:* pdfplumber como base — extrae texto de PDFs nativos pero no da acceso a la capa de píxeles ni a los objetos incrementales.

**Por qué se descarta el OCR tradicional y qué se conserva.** *Decisión:* el OCR se descarta como fuente de verdad semántica (su transcripción no es evidencia del contenido visual y su corrección de errores destruye precisamente las anomalías que buscamos), pero **se conserva Tesseract 5.4 en modo sólo-layout** (`--psm 11` y la API `GetComponentImages` a nivel de línea/palabra) como fuente barata de cajas delimitadoras y líneas base — porque el VLM es caro y ruidoso para geometría fina, y Tesseract da bbox con error típico < 1 px en escaneos limpios. El cruce: para cada bloque, se calcula IoU entre la caja del layout y la caja que el VLM afirma; `IoU ≥ 0,5` ⇒ se fusiona (geometría del layout, semántica del VLM); `IoU < 0,5` ⇒ se registra en `conflicts` y **gana la geometría** (medida) sobre el juicio (modelo), coherente con la precedencia de evidencia de §3.10.
*Descartado:* PaddleOCR — mejor detección en escenas, pero añade una dependencia pesada y su beneficio sobre documentos A4 escaneados no compensa.

Tabla de enrutado completa:

| Entrada | Detección | Pipeline | Modelo invocado |
|---|---|---|---|
| PDF nativo (texto vectorial) | `pikepdf`: fuentes incrustadas + `/Contents` con operadores `Tj` | Extracción vectorial exacta + render 300 dpi para rasgos + análisis de objetos incrementales | VLM sólo para bloques marcados como firma/sello |
| PDF escaneado (imagen por página) | páginas con un solo `XObject` imagen ≥ 90 % del área | Normalización → layout → teselado → VLM | VLM completo |
| PDF mixto | proporción por página | Enrutado por página | Mixto |
| JPEG | magic `FFD8` | Normalización + ELA + tabla de cuantización | VLM completo |
| PNG | magic `89504E47` | Normalización (sin ELA; se anota "sin JPEG, ELA no aplicable") | VLM completo |
| TIFF multipágina | magic `II*\0`/`MM\0*` | Iteración por página; conserva compresión (G4/LZW) como señal | VLM completo |
| Foto de móvil | EXIF con `Make/Model` y sin `Software` de escáner | Corrección de perspectiva obligatoria (4 esquinas por contorno) + normalización de iluminación agresiva | VLM completo, con `confidence_penalty=0,15` |
| Captura de pantalla | EXIF ausente + dimensiones ≈ resolución de pantalla + ruido ≈ 0 | Sin deskew; se marca `native_digital=true` | VLM completo |
| Plano CAD escaneado | densidad de líneas rectas (Hough) > umbral y texto < 5 % del área | Pipeline de líneas: vectorización con `cv2.HoughLinesP` + detección de cotas | VLM técnico + Área 2 |
| Fotografía de PCB | detección de color verde/azul dominante + patrón de rejilla | Pipeline de inspección: segmentación de pistas y componentes | VLM + Área 9.D |

Paridad Windows/Linux: el único elemento que toca el SO es la localización de binarios (`tesseract`, `exiftool`, el proveedor de nube asignado): en Windows se resuelven desde `%LOCALAPPDATA%\MagiSystem\tools\`; en Linux desde `~/.local/share/magi/tools/` con fallback a `PATH`. El resto es puro cómputo.

### 1.5 Algoritmos

**A1-1 — Normalización.**
```
1.  dpi := dpi_declarado(PDF/EXIF) si existe; si no, estimar por altura-x mediana: dpi ≈ 300 · (x_height_px / 9,3)
2.  convertir a gris 16-bit; guardar copia en color para análisis de ruido
3.  deskew: (a) perfil de proyección horizontal para ángulos en [−5°, +5°] paso 0,05°, maximizando la varianza
       del perfil; (b) si |ángulo| > 5°, Hough probabilístico sobre bordes Canny y mediana de las pendientes
4.  perspectiva: si el contorno de página no es rectángulo (razón de lados fuera de ±3 %), detectar 4 esquinas
       (approxPolyDP sobre el mayor contorno) y aplicar getPerspectiveTransform → H
5.  iluminación: rolling-ball radio 50 px sobre el gris (morfología de apertura) y división; normalizar a p2–p98
6.  caso límite: página en blanco (varianza < 1e-4) → devolver PageTopography vacía con flag blank=true
7.  complejidad O(W·H) salvo Hough O(W·H·θ)
```

**A1-2 — Teselado que no corta líneas.**
```
1.  obtener líneas base del layout engine, ordenadas por y
2.  altura útil de tesela h = max_side_px del VLM (1280 en Perfil A) menos margen de solape (12 %)
3.  cortar en el hueco inter-línea más cercano al límite teórico: y_corte := argmax de la separación entre
       baselines consecutivas dentro de ±0,08·h del límite; si no hay hueco (tabla densa) → cortar en el
       límite y marcar tile.split_risk = true
4.  solape horizontal fijo del 12 % para bloques a dos columnas
5.  registrar por tesela el offset (dx,dy) y el factor de escala s para reensamblar: p_pag = (p_tile/s) + (dx,dy)
6.  caso límite: página con una sola línea gigante (cartel) → una tesela, sin corte
```

**A1-3 — Medición de rasgos tipográficos.**
```
1.  altura-x: mediana de la altura de los componentes conexos sin ascendente ni descendente dentro de la línea
2.  altura de mayúsculas: percentil 90 de la altura de componentes cuyo bbox toca la línea base
3.  tamaño en puntos: size_pt = (cap_height_px / dpi) · 72 / k_familia, con k_familia ∈ [0,68; 0,74] por clase
       tipográfica (serif transicional 0,70; grotesca 0,72; humanista 0,71; egipcia 0,69; monoespaciada 0,68)
4.  peso: densidad de trazo = (píxeles de tinta) / (longitud del esqueleto, skeletonize); negrita si el valor
       supera en ≥ 22 % la mediana de la página
5.  cursiva: ángulo dominante del esqueleto por transformada de Hough restringida a [−25°, +25°]; cursiva si |α| ≥ 6°
6.  interlineado: diferencia entre baselines consecutivas (mm), mediana y desviación por bloque
7.  sangría: histograma de x de inicio de línea con anchura de bin 1 mm; los modos son los niveles de sangría
8.  márgenes: distancia del bbox de tinta al borde de página, los cuatro, en mm
9.  densidad de tinta por bloque: fracción de píxeles bajo el umbral de Otsu local
10. ángulo de trama: FFT 2D del bloque; pico dominante fuera del eje ⇒ ángulo y frecuencia (lpi)
11. clasificación de familia: descriptores (contraste de trazo, presencia de serifas por análisis de terminales,
       relación anchura/altura, uniformidad de avance) → clasificador k-NN sobre 24 clases con prototipos
       generados sintéticamente a partir de fuentes libres (DejaVu, Liberation, EB Garamond, Inter, Roboto Mono…)
12. vector de rasgos de página (128 dimensiones, longitud fija): 12 estadísticos de tamaño, 8 de peso, 8 de
       interlineado, 8 de sangría, 4 de márgenes, 8 de densidad, 6 de trama, 24 de histograma de clase
       tipográfica, 12 de ruido, 16 de distribución espacial de tinta (rejilla 4×4), 22 de reserva a cero.
```

**A1-4 — Detectores de anomalía (señal, estadístico, umbral inicial).**

| ID | Anomalía | Señal | Estadístico | Umbral inicial | Evidencia producida |
|---|---|---|---|---|---|
| D1 | Página alterada en el expediente | vector de rasgos de página | distancia de Mahalanobis robusta a la mediana del expediente (MCD) | `d > 3,5` ⇒ indicio; `d > 5,0` ⇒ indicio fuerte | `{page_id, d, rasgos con \|z\|>3}` |
| D2 | Cláusula añadida con otra fuente | cambio de `family_class`/`size_pt`/`weight` dentro de un bloque semántico | z-score del tamaño intra-bloque | `\|z\| > 2,5` **y** cambio de clase tipográfica | recorte de imagen + medidas de ambas líneas |
| D3 | Interlineado/márgenes inconsistentes | `leading_mm`, márgenes | desviación relativa frente a la mediana del expediente | `> 6 %` en interlineado, `> 3 mm` en margen | tabla comparativa por página |
| D4 | Reimpresión/reescaneo parcial | σ del ruido en zonas planas, ángulo de trama, hash de tabla de cuantización | prueba de dos muestras (Kolmogórov-Smirnov) entre regiones | `p < 0,01` | mapa de regiones + histogramas |
| D5 | Empalme digital (splicing) | discontinuidad de ruido, nivel de negro, rejilla de bloques JPEG 8×8, ELA | mapa de residuo ELA + detección de desalineación de rejilla | bloque con residuo ELA > μ+4σ y desalineación ≥ 1 px | mapa de calor + coordenadas |
| D6 | Numeración de páginas incoherente | número leído en pie/encabezado vs. orden físico | comparación de secuencia | cualquier salto o repetición | lista de discordancias |
| D7 | Firma/sello clonado | correlación cruzada normalizada (NCC) entre regiones de firma | máx. NCC tras alineación por fase | `NCC > 0,97` ⇒ clon digital casi seguro | par de recortes + valor NCC |
| D8 | Nativo digital presentado como escaneo | σ del ruido, ángulo residual, bordes | `σ_flat < 0,4` **y** `\|deskew\| < 0,02°` **y** sin sombra de borde | conjunción de las tres | métricas + recorte de borde |
| D9 | Metadatos/estructura PDF alterada | objetos incrementales, `/Prev` en xref, fuentes divergentes, `ModDate` < `CreationDate` | conteo de revisiones y divergencias | ≥ 1 revisión incremental con cambio en páginas | volcado de objetos + diff |

Cada detector emite una **Afirmación falsable** hacia el Área 3 con esta forma: *"La página p7 fue sustituida respecto del resto del expediente"* con `falsifier`: *"si la distancia de Mahalanobis de p7 cae bajo 3,5 al recalcular con el expediente completo tras corregir el DPI efectivo, la afirmación queda refutada"*.

**A1-5 — Calibración de umbrales sin dataset etiquetado.**
```
1.  auto-referencia: la línea base es el propio expediente (mediana robusta y MCD sobre ≥ 5 páginas);
       con < 5 páginas se marca baseline_weak=true y los umbrales se relajan un 30 %
2.  generador de corpus sintético (scripts/forensic/make_tampered.py):
    2.1 tomar N documentos limpios del usuario (o generados con LaTeX/LibreOffice headless)
    2.2 aplicar alteraciones conocidas y parametrizadas: sustituir párrafo con otra fuente (ΔF),
        reescanear simulado (ruido gaussiano σ, recompresión JPEG Q), empalmar región (pegado con feathering),
        clonar firma (copia exacta y copia con jitter ±0,5 px), reordenar páginas, editar PDF incrementalmente
    2.3 registrar la verdad de terreno en tampered_manifest.json
3.  barrer umbrales y construir curvas ROC por detector; fijar el umbral en el punto de
       falsos positivos ≤ 2 % (prioridad: no acusar en falso), reportando la sensibilidad resultante
4.  criterio de aceptación del módulo: FPR ≤ 2 % y TPR ≥ 85 % en D1, D2, D5, D7 sobre 200 documentos sintéticos
```

**Cadena de custodia.** Al ingerir: `sha256` del fichero original, copia inmutable al CAS, `custody_log` con `{ts, actor, action, params_hash, output_sha256}` por cada transformación (normalización, teselado, detección). El informe incluye un apéndice con la lista ordenada de transformaciones y el comando exacto para reproducirlas: `magi forensic replay --dossier <id> --out <dir>`, que debe regenerar bit a bit los mismos `page_features.json` (semilla fija, sin operaciones no deterministas).

**Decisiones formalizadas adicionales de esta área.**
**Decisión:** el sistema de coordenadas canónico es el milímetro sobre la página normalizada, con retroproyección por homografía inversa al píxel original — porque un rasgo medido en píxeles no es comparable entre escaneos de distinto DPI y el expediente es precisamente una comparación entre páginas.
*Descartado:* trabajar en píxeles y normalizar al comparar — arrastra el error de DPI a todos los detectores.
**Decisión:** ante conflicto entre la geometría medida y el juicio del VLM, gana la geometría y el conflicto se registra en `conflicts[]` — porque la medida es evidencia de rango superior al razonamiento del modelo (§3.10).

### 1.6 Integración con el debate popperiano

Afirmaciones emitidas: una por hallazgo (D1–D9) y una agregada por expediente ("el expediente presenta k alteraciones"). Evidencia admisible: medidas numéricas con su método, recortes de imagen con coordenadas, y resultados del generador sintético. Refutación más potente disponible: **la explicación alternativa benigna verificada** — por ejemplo, el BALTHASAR demuestra que la diferencia de interlineado de D3 se explica por un cambio de DPI del escáner entre lotes, y lo prueba recalculando los rasgos con el DPI corregido y viendo caer la distancia bajo umbral. Segunda más potente: reproducir la anomalía en un documento **no alterado** (falso positivo demostrado). Punto de invocación exacto: `detect_anomalies()` no publica hallazgos directamente; los encola en `pending_claims` y el Área 3 se invoca antes de que ningún hallazgo llegue al informe.

### 1.7 Costos, latencia y recursos

Por página A4 a 300 dpi (Perfil A): normalización 180 ms; layout Tesseract 420 ms; teselado 15 ms; VLM 6 teselas × 2,8 s = 16,8 s; detectores 240 ms. Total ≈ 17,7 s/página. Un expediente de 300 páginas ≈ 1 h 28 min, ejecutable como trabajo por lotes reanudable. Tokens por página: entrada ≈ 1 400 (prompt + teselas codificadas) y salida ≈ 900 con gramática GBNF; el debate añade ≤ 25 000 tokens por hallazgo disputado. VRAM: 5,9 GB (VLM) + 0,7 GB (embeddings) en Perfil A. **Salto del debate:** los rasgos medidos (R0, deterministas) no se debaten; sólo se debaten los *hallazgos*. Caché: por página, `clave = sha256(imagen_normalizada) + versión_normalizador + modelo_vlm_hash + prompt_hash`; invalidación al cambiar cualquier componente; los `page_features.json` se conservan indefinidamente porque son baratos y son evidencia.

### 1.8 Calidad y pruebas

| Caso | Criterio de éxito |
|---|---|
| Camino feliz: contrato de 12 páginas limpio | 0 hallazgos con `d > 3,5`; informe generado ≤ 4 min |
| Documento alterado vs. original (par controlado) | D2 detecta la cláusula insertada con confianza ≥ 0,8 y coordenadas dentro de ±2 mm |
| Firma clonada | D7 con NCC ≥ 0,97 en el par clonado y < 0,85 en dos firmas auténticas del mismo firmante |
| Consenso entre agentes | A afirma alteración, B no encuentra explicación benigna, C otorga `survives` con ≥ 75/100 |
| Desacuerdo total | B demuestra cambio de DPI entre lotes; C emite `falsified` y el hallazgo **no** llega al informe |
| Falsos positivos | Sobre 200 documentos limpios: FPR global ≤ 2 % |
| Foto de móvil torcida 12° con sombra | Deskew residual ≤ 0,3°; márgenes con error ≤ 2 mm |
| Reproducibilidad | `forensic replay` produce `page_features.json` idénticos (hash igual) en 100/100 páginas |

### 1.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta automática | Estado |
|---|---|---|---|---|
| VLM no disponible | health check del el proveedor de nube asignado de visión | Sin juicio semántico | Continuar con geometría pura, marcar `vlm_absent=true`, reducir confianza 0,3 | Degradado, informe con limitación explícita |
| DPI desconocido y sin texto | estimador falla | Rasgos en unidades absolutas erróneas | Reportar en píxeles y marcar `dpi_unknown` | Degradado |
| PDF cifrado | `pikepdf` lanza `PasswordError` | Sin acceso | Pedir contraseña al usuario; si no, abortar con motivo | Bloqueado, explicado |
| Deskew erróneo (fallo parcial, el peor) | varianza del perfil tras deskew menor que antes | Todos los rasgos contaminados | Revertir deskew, marcar `deskew_failed`, rebajar todos los hallazgos a `indicio_debil` | Degradado, sin falsos positivos silenciosos |
| Sin red | — | Ninguno | Nada: el área es 100 % local | Operativo |

### 1.10 Riesgos y mitigaciones

Falsos positivos que dañen a un tercero (prob. media, impacto alto): umbral calibrado a FPR ≤ 2 %, debate obligatorio antes del informe y redacción normalizada de límites. Sesgo de arrastre en el debate documental (media/medio): resumen neutralizado entre rondas y reinicio ciego cada 3 rondas. Escáneres heterogéneos dentro del mismo expediente (alta/medio): agrupar por `sensor_noise` y calcular la línea base por grupo. Documentos con marcas de agua o fondos de seguridad (media/medio): máscara de fondo por apertura morfológica antes de medir densidad. Sobreconfianza del VLM (alta/alto): la geometría medida gana siempre sobre el juicio del modelo, y el conflicto se registra.

**Límites honestos, tal como se redactan en el informe (texto normativo del módulo):** *"Los hallazgos de este informe son indicios técnicos reproducibles obtenidos por medición automatizada sobre las imágenes aportadas. No constituyen prueba pericial ni dictamen de falsedad documental. Cada indicio incluye su método, su umbral y su procedimiento de reproducción para que un tercero pueda verificarlo o refutarlo. La ausencia de indicios no acredita autenticidad."*

### 1.11 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA**: Python 3.12, OpenCV 4.10, PyMuPDF 1.24, pikepdf 9.x, Tesseract 5.4 (binario libre), exiftool 12.x, VLM GGUF local. **🟡 REQUIERE-PRERREQUISITO** sólo para el flujo de digitalización propia: un escáner plano o un teléfono con cámara (que el usuario ya posee; no se compra nada). El módulo funciona íntegramente con imágenes aportadas.

### 1.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (normalización + layout + rasgos + D1/D2 sobre un expediente) → v1 (VLM, teselado, D3–D7, informe) → completo (D8/D9, generador sintético, calibración ROC, replay bit a bit).

- **P1.a Normalización.** P1.a.1 lector multi-formato — **PV-1.a.1**: 10 formatos de §1.4 abren y producen imagen y `dpi_effective`. P1.a.2 deskew — **PV-1.a.2**: sobre 100 páginas rotadas sintéticamente en [−12°,12°], error residual ≤ 0,3° en ≥ 95 %. P1.a.3 perspectiva — **PV-1.a.3**: sobre 50 fotos con inclinación, márgenes con error ≤ 2 mm.
- **P1.b Geometría.** P1.b.1 Tesseract modo layout — **PV-1.b.1**: IoU medio ≥ 0,85 contra cajas anotadas de 20 páginas. P1.b.2 teselado — **PV-1.b.2**: 0 líneas base cortadas en 200 páginas; reensamblado con error ≤ 0,2 mm.
- **P1.c Rasgos.** P1.c.1 tamaño/peso/cursiva — **PV-1.c.1**: sobre PDFs generados con tamaños conocidos (8–18 pt), error ≤ 0,4 pt en ≥ 95 % de líneas. P1.c.2 vector de página — **PV-1.c.2**: 128 dimensiones, sin NaN, y separación medible: la distancia entre páginas de distinto documento supera la intra-documento en ≥ 3σ.
- **P1.d Detectores.** P1.d.1 D1–D3 — **PV-1.d.1**: TPR ≥ 85 %, FPR ≤ 2 % en el corpus sintético. P1.d.2 D4–D7 — **PV-1.d.2**: D7 separa clon (NCC ≥ 0,97) de firma auténtica (< 0,85) en 100 pares. P1.d.3 D8–D9 — **PV-1.d.3**: 100 % de detección de revisión incremental en 30 PDFs editados.
- **P1.e Integración.** P1.e.1 informe + cadena de custodia — **PV-1.e.1**: `forensic replay` reproduce hashes idénticos. P1.e.2 conexión al debate — **PV-1.e.2**: ningún hallazgo aparece en el informe sin `verdict` asociado en la base.

Métricas de salida: FPR ≤ 2 %, TPR ≥ 85 % en D1/D2/D5/D7, ≤ 20 s/página en Perfil A, 100 % de reproducibilidad.

---

## ÁREA 2 — Motor de razonamiento contrastivo (legal y técnico)

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA** (requiere que el usuario aporte los textos normativos que quiera usar como corpus).

### 2.1 Propósito y alcance

El sistema no resume: **cruza**. Este módulo toma un documento bajo análisis (normalmente salido del Área 1) y lo confronta, proposición a proposición, contra un corpus de referencia local — normas jurídicas, normas técnicas, manuales de ingeniería, hojas de datos — y emite un dictamen donde **cada conclusión lleva cita literal localizable en ambos lados**.

Queda fuera: la medición visual (Área 1), la generación de la norma (el usuario aporta el corpus), y el asesoramiento legal o de inversión — la salida es análisis técnico documentado, y así se etiqueta.

**Consume:** Área 1 (documento estructurado con coordenadas), Área 0 (índice vectorial, CAS), Área 7 (prompt de contraste normativo). **Alimenta:** Área 3 (afirmaciones y refutaciones normativas), Área 11 (validación técnica y arte previo), Área 12 (capacidades C16–C19).

### 2.2 Arquitectura

```
 corpus del usuario (PDF/DOCX/HTML/TXT)      documento bajo análisis (Área 1)
        │ ingesta                                     │ blocks/lines + coords
        ▼                                             ▼
 ┌────────────────────────┐                 ┌─────────────────────────┐
 │ SEGMENTADOR ESTRUCTURAL│                 │ EXTRACTOR DE            │
 │ jurídico | técnico     │                 │ AFIRMACIONES (claims)   │
 └──────────┬─────────────┘                 └───────────┬─────────────┘
   chunk+metadata (norma,art,vigencia,hash)             │ claim{texto,cita,coord}
            ▼                                           │
 ┌────────────────────────┐  vector+bm25                │
 │ INDEXADOR HÍBRIDO      │◄────────────────────────────┤ consulta dirigida
 │ BM25(rank_bm25) +      │                             │
 │ denso(bge-m3, sqlite-vec)                            │
 └──────────┬─────────────┘                             │
            │ top-50 candidatos                         │
            ▼                                           │
 ┌────────────────────────┐                             │
 │ REORDENADOR cross-enc. │ top-8 ──────────────────────┤
 └──────────┬─────────────┘                             │
            ▼                                           ▼
 ┌────────────────────────────────────────────────────────────────┐
 │ ALINEACIÓN claim ↔ referencia → JUICIO DE COMPATIBILIDAD       │
 │  ⚠ punto de decisión: ¿la afirmación es numérica?              │
 │      sí → RECALCULADOR DETERMINISTA (sympy/numpy, sandbox)     │
 │      no → juicio del modelo con salida GBNF                    │
 └───────────┬──────────────────────────────────┬─────────────────┘
             │ relación + gravedad              │ divergencia numérica
             ▼                                  ▼
 ┌────────────────────────┐        ┌────────────────────────────────┐
 │ VALIDADOR DE CITAS     │        │  EVIDENCIA para Área 3         │
 │ (subcadena normalizada │        │  (el cálculo gana al modelo)   │
 │  + hash de fragmento)  │        └────────────────────────────────┘
 │  ⚠ punto de fallo: cita│
 │   no hallada → DESCARTE│
 └───────────┬────────────┘
             ▼  dictamen.json + dictamen.md
```

### 2.3 Contratos e interfaces

```python
def ingest_corpus(paths: list[Path], kind: Literal["legal","technical"], project: ProjectId) -> CorpusVersion: ...
def segment_legal(doc: RawDoc) -> list[Chunk]: ...
def segment_technical(doc: RawDoc) -> list[Chunk]: ...
def index_corpus(version: CorpusVersion) -> IndexStats: ...
def extract_claims(doc: PageTopography | list[PageTopography]) -> list[DocClaim]: ...
def retrieve(claim: DocClaim, k_dense: int = 50, k_lex: int = 50, k_final: int = 8) -> list[Reference]: ...
def judge_compatibility(claim: DocClaim, refs: list[Reference]) -> Alignment: ...
def recompute_numeric(claim: DocClaim) -> NumericCheck: ...
def emit_opinion(alignments: list[Alignment]) -> OpinionReport: ...
```

Esquema de afirmación del documento:

```json
{
  "claim_id": "dc-0007",
  "type": "normative|numeric|factual|definitional",
  "statement": "Las controversias se someterán a arbitraje de derecho ante un árbitro único designado por la parte contratante.",
  "verbatim": "…texto literal exacto tal como aparece…",
  "location": {"page_id": "sha256:…#p4", "block_id": "b3", "line_ids": ["b3l7","b3l8"],
               "bbox_mm": {"x":30.2,"y":142.5,"w":149.0,"h":9.4}},
  "extracted_by": {"model": "qwen2.5-coder-7b-q5km", "prompt_hash": "…", "seed": 20260801},
  "numeric": null
}
```

Esquema de alineación:

```json
{
  "claim_id": "dc-0007",
  "relation": "conforme|conforme-con-observacion|insuficiente|excesivo|contradictorio|nulo-de-pleno-derecho|ambiguo|no-aplicable|sin-referencia-en-corpus",
  "severity": "critica|alta|media|baja|informativa",
  "references": [{"corpus_doc_id":"dl1071@2024-05-01","chunk_id":"art-13","verbatim":"…","locator":"Artículo 13","hash":"…","similarity":0.83,"rerank":0.91}],
  "reasoning": "…",
  "numeric_check": {"performed": false},
  "citation_validation": {"doc_verbatim_found": true, "ref_verbatim_found": true, "method": "normalized_substring+sha256"},
  "recommendation": "…"
}
```

Taxonomía de relaciones — definición operativa y exigencia probatoria:

| Relación | Definición operativa | Qué exige el sistema para asignarla |
|---|---|---|
| `conforme` | La afirmación satisface todos los requisitos de la referencia aplicable | ≥ 1 referencia con `rerank ≥ 0,75` y ningún requisito de la referencia sin correspondencia en la afirmación |
| `conforme-con-observacion` | Satisface el requisito pero con redacción o práctica desaconsejada | Igual que `conforme` + al menos una observación con cita de la referencia |
| `insuficiente` | Falta un requisito exigido por la referencia | Enumeración explícita del requisito faltante con su cita literal |
| `excesivo` | Impone más de lo que la referencia permite | Cita del límite superado + cuantificación cuando sea numérico |
| `contradictorio` | Afirma lo opuesto a la referencia | Par de citas literales opuestas, ambas verificadas |
| `nulo-de-pleno-derecho` | La referencia declara nula la estipulación | Cita del precepto que establece la nulidad, textual |
| `ambiguo` | Admite dos lecturas incompatibles con consecuencias distintas | Enunciado explícito de las dos lecturas y de su consecuencia |
| `no-aplicable` | La referencia recuperada no rige el supuesto | Motivo de inaplicabilidad citado (ámbito, vigencia, materia) |
| `sin-referencia-en-corpus` | No hay soporte en el corpus indexado | Constancia de la consulta realizada (query, k, mejor `rerank` obtenido) |

Tablas propias: `corpus_doc`, `corpus_chunk`, `corpus_version`, `doc_claim`, `alignment`, `opinion_report` (DDL en §T3). Eventos: `corpus.updated`, `artifact.created`, `job.progress`.

### 2.4 Implementación

*Decisión:* índice híbrido BM25 (`rank_bm25` 0.2.2 con Okapi BM25, k1=1,2 b=0,75) + denso (`bge-m3` sobre `sqlite-vec` 0.1.x, coseno) fusionados con **Reciprocal Rank Fusion** con `k=60` y pesos `w_lex=0,45 / w_dense=0,55`, y reordenamiento final con `bge-reranker-v2-m3` sobre los 50 primeros — porque el caso real del encargo ("resolución de disputas" en el contrato frente a "convenio arbitral" en la norma) es exactamente donde el léxico solo falla y el denso solo alucina vecinos plausibles.
*Descartado:* sólo denso con un modelo mayor — más caro y sigue perdiendo la coincidencia exacta de numerales y citas legales, que es donde el léxico es insustituible.

Ingesta: `PyMuPDF` para PDF, `python-docx` 1.1 para DOCX, `trafilatura` 1.12 para HTML público descargado con Playwright (con hash y marca de tiempo, §I.3). Normalización de texto: NFKC, colapso de espacios, conservación de numerales y de mayúsculas iniciales de artículo.

Segmentador jurídico (`segment_legal`): trocea por **unidad normativa**, no por longitud. Gramática de reconocimiento por expresiones regulares jerarquizadas: `LIBRO`, `TÍTULO`, `CAPÍTULO`, `SUBCAPÍTULO`, `Artículo N[º°]?`, `N.` (numeral), `literal a)`, `Disposición Complementaria (Final|Transitoria|Modificatoria|Derogatoria)`. Cada fragmento arrastra: `{norma_id, jerarquia:[libro,titulo,capitulo], locator:"Artículo 13", numeral, literal, vigencia_desde, vigencia_hasta, fuente_url, fuente_sha256, texto_hash}`. Un artículo que supere 1 200 tokens se sub-trocea por numeral, nunca a ciegas.

Segmentador técnico (`segment_technical`): trocea por sección normativa (`E.030 Artículo 12`, `4.2.1`), **tabla completa como unidad indivisible** (una tabla partida es una fuente de error garantizada) y **ecuación con su contexto** (párrafo anterior + definición de variables). Metadatos: `{norma_tecnica, capitulo, tabla_id?, ecuacion_id?, unidades, vigencia}`.

Paridad Windows/Linux: sólo afecta a las rutas del índice y al binario de Playwright; ambos resueltos por `PathsHAL` y `ToolchainHAL`. El cómputo es idéntico.

### 2.5 Algoritmos

**A2-1 — Flujo legal completo (caso exigido: cláusula de resolución de disputas vs. Decreto Legislativo N.º 1071, Ley de Arbitraje del Perú).**

```
 1. ingerir DL 1071 (texto oficial aportado por el usuario en PDF/HTML) → segment_legal
 2. registrar CorpusVersion{norma_id:"DL-1071", vigencia_desde, sha256, modificatorias:[...]}
 3. del Área 1: obtener bloques del contrato; extract_claims sobre los bloques cuyo encabezado o
       contenido coincida con el patrón de cláusula compromisoria (regex + juicio del modelo)
 4. claim := "Las controversias se someterán a arbitraje …" con verbatim y coordenadas
 5. construir 5 consultas dirigidas, una por requisito a verificar:
       q1 forma del convenio arbitral        q2 designación y número de árbitros
       q3 sede del arbitraje                 q4 idioma del arbitraje
       q5 renuncias y estipulaciones nulas / arbitraje de derecho vs. de conciencia
 6. para cada qi: retrieve(qi) → BM25 ∪ denso → RRF → rerank → top-8 fragmentos con su locator real
       REGLA DURA: el locator (p. ej. "Artículo 13") se lee del corpus indexado, NUNCA de la memoria
       del modelo; una cita cuyo locator no exista en corpus_chunk se descarta antes del dictamen
 7. juicio por requisito con el prompt de contraste (salida GBNF, esquema Alignment)
 8. verificación mecánica de citas (A2-3); las que no pasan se eliminan y el requisito baja a
       'sin-referencia-en-corpus'
 9. agregación: la cláusula es 'patológica' si algún requisito resulta insuficiente, contradictorio o
       nulo-de-pleno-derecho; la gravedad del dictamen es el máximo de las gravedades por requisito
10. emitir dictamen con: resumen ejecutivo, tabla de hallazgos por gravedad, cada hallazgo con
       (cita del contrato + coordenada de página) y (cita de la norma + locator + hash), relación,
       gravedad, recomendación; y anexo de trazabilidad con las consultas ejecutadas
11. someter cada hallazgo al Área 3 antes de publicarlo
12. caso límite: norma modificada. Si CorpusVersion tiene modificatorias que afectan al locator citado,
       el dictamen debe citar el texto vigente a la fecha del contrato y, además, el texto vigente hoy,
       marcando el hallazgo con temporal_conflict=true
```

Gestión de vigencia: cada `corpus_chunk` lleva `vigencia_desde`/`vigencia_hasta`. Al ingerir una norma modificatoria, el sistema **no** reescribe el texto: crea una nueva `CorpusVersion` y marca la anterior con `vigencia_hasta`. Una consulta siempre se hace con una fecha de referencia (`as_of`), por defecto la fecha del documento analizado. La derogación se detecta por: (a) declaración expresa en una disposición derogatoria ingerida; (b) ausencia del artículo en una versión posterior del mismo `norma_id` (diff estructural), que genera `corpus.updated{kind:"possible_derogation"}` y exige confirmación humana antes de aplicarse.

**A2-2 — Flujo técnico completo (memoria de cálculo / plano vs. Normas Técnicas E.020 cargas, E.030 diseño sismorresistente, E.060 concreto armado del RNE).**

```
 1. del Área 1: extraer tablas, ecuaciones y valores declarados (factores, combinaciones, cuantías, derivas)
       con sus unidades y su coordenada
 2. normalizar unidades con `pint` 0.24 (kgf/cm², MPa, tonf, kN, ‰) y rechazar toda magnitud sin unidad
 3. mapear cada valor declarado a su requisito normativo mediante retrieve() sobre el corpus técnico
       (E.020 / E.030 / E.060 aportadas por el usuario)
 4. para cada valor: construir el CHEQUEO DETERMINISTA
       4.1 combinación de cargas: reconstruir la combinación declarada como expresión simbólica y
            compararla término a término con la combinación de la tabla normativa recuperada
       4.2 deriva: comparar la deriva declarada con el límite de la tabla correspondiente al sistema
            estructural y material declarados en la memoria
       4.3 cuantía: recalcular ρ = As/(b·d) con las dimensiones y el acero declarados y compararla
            con los límites mínimo y máximo recuperados del corpus
       4.4 parámetros sísmicos: verificar la coherencia interna del cortante basal declarado
            V = (Z·U·C·S/R)·P recomponiendo el producto con los factores declarados en la propia memoria
 5. TODA comparación numérica se ejecuta con sympy 1.13 / numpy 2.0 en el sandbox (A2-4), nunca por el modelo
 6. divergencia > tolerancia (por defecto 1 % relativo, o el redondeo declarado en la norma citada)
       ⇒ hallazgo 'contradictorio' con el cálculo adjunto como evidencia
 7. valor no verificable por falta de dato ⇒ 'insuficiente' con el dato faltante nombrado
 8. caso límite: la memoria cita una norma que NO está en el corpus ⇒ 'sin-referencia-en-corpus' y
       solicitud explícita al usuario de cargar ese documento; jamás se juzga de memoria
```

**A2-3 — Validador anti-alucinación de citas (regla de oro).**
```
1. para cada cita c producida por el modelo (lado documento y lado corpus):
2.    t := normalizar(c.verbatim)   # NFKC, minúsculas, colapso de espacios, sin guiones de corte de línea
3.    buscar t como subcadena en normalizar(chunk.texto) del chunk_id declarado
4.    si no aparece: buscar en TODO el corpus con índice de subcadenas (suffix automaton) — si aparece en
        otro chunk, corregir el chunk_id y anotar 'cita_reubicada'; si no aparece en ninguno → RECHAZO
5.    verificar sha256(chunk.texto) == chunk.hash almacenado (integridad del corpus)
6.    tolerancia: 0 caracteres de diferencia tras normalización; NO se admite similitud aproximada
7. si el número de citas rechazadas de una respuesta ≥ 1 → devolver al modelo el error exacto y reintentar
        (máx. 2 reintentos); a la tercera, la relación se fuerza a 'sin-referencia-en-corpus'
8. complejidad O(|t| + |corpus|) amortizado con el autómata construido una vez por CorpusVersion
```

**A2-4 — Puente "afirmación numérica → código de verificación → resultado".**
```
1. detectar afirmación numérica: contiene magnitud + unidad + relación (=, ≤, ≥, <, >) o fórmula
2. el modelo NO da el resultado: emite un plan de cálculo en JSON {variables:{nombre:{valor,unidad,origen}},
      expresion:"…", tolerancia:0.01, referencia_normativa:"chunk_id"}
3. validar que TODA variable tiene origen: 'documento' (con coordenada) o 'corpus' (con chunk_id).
      Una variable sin origen invalida el plan (no se permiten constantes inventadas)
4. ejecutar en sandbox: subproceso Python 3.12 sin red (capacidad net.out denegada), sin fs.write salvo
      un tmpdir, límite de 5 s de CPU y 512 MB (RLIMIT_AS en Linux; Job Object con límite de memoria en
      Windows), sólo sympy/numpy/pint importables mediante lista blanca de módulos
5. comparar resultado con el valor declarado: |calc − decl| / max(|decl|, ε) ≤ tolerancia
6. DIVERGENCIA: el resultado del cálculo gana siempre sobre el juicio del modelo (§3.10). Se genera
      Evidencia{kind:"computation", code_hash, inputs, output} y el hallazgo pasa a 'contradictorio'
7. si el sandbox falla (excepción, timeout) → el hallazgo se marca 'ambiguo' con motivo técnico, nunca
      se resuelve por el modelo
```

**Gestión del corpus.** El usuario carga documentos por arrastre en la GUI o `magi corpus add --kind legal --path <dir> --norma-id DL-1071 --vigencia-desde 2008-09-01`. Se versiona por `CorpusVersion(norma_id, sha256, fecha_ingesta, as_of)`. Aislamiento por proyecto: cada proyecto tiene su propio `vectors.db` y su propia tabla `corpus_doc`; un corpus puede **enlazarse** entre proyectos por referencia al CAS (sin duplicar bytes) pero nunca se comparte índice mutable.

**Decisiones formalizadas adicionales de esta área.**
**Decisión:** el `locator` de toda cita (por ejemplo "Artículo 13") se lee siempre del corpus indexado y nunca de la memoria del modelo — porque la numeración de artículos es exactamente el dato que un modelo alucina con más facilidad y con peores consecuencias.
*Descartado:* aceptar el locator del modelo y verificarlo después — el coste de un falso positivo en un dictamen es demasiado alto para una verificación posterior.
**Decisión:** toda consulta al corpus lleva una fecha de referencia `as_of` obligatoria, por defecto la fecha del documento analizado — porque juzgar un contrato de 2010 con el texto vigente hoy es un error de método, no de detalle.
**Decisión:** la tolerancia por defecto de las comparaciones numéricas es el 1 % relativo, salvo que la norma citada declare su propio redondeo, que entonces prevalece — porque la norma manda sobre la convención del sistema.

### 2.6 Integración con el debate popperiano

Afirmaciones emitidas: una por `Alignment` con relación distinta de `conforme`. Evidencia admisible: cita literal verificada por A2-3, resultado del recálculo determinista (A2-4), y metadatos de vigencia. Refutación más potente: **la referencia mejor** — B recupera un fragmento del mismo corpus, con locator real, que hace inaplicable o desplaza a la referencia usada por A (por especialidad, jerarquía normativa o vigencia). Segunda: demostrar que la cita de A no existe literalmente (A2-3 lo hace mecánicamente antes, así que en el debate esto sólo aparece si el corpus cambió). Punto de invocación: tras `judge_compatibility` y antes de `emit_opinion`; ningún hallazgo entra en el dictamen sin `verdict`.

### 2.7 Costos, latencia y recursos

Indexación: ≈ 1 800 fragmentos/min con `bge-m3` en CPU (Perfil B) y ≈ 9 000/min con GPU de 8 GB. Consulta: BM25 ≤ 15 ms; denso ≤ 25 ms sobre 200 000 fragmentos; reordenador 8 pares ≤ 900 ms (CPU) / 120 ms (GPU). Juicio por afirmación: ≈ 2 100 tokens de entrada, 700 de salida, latencia 4–11 s según perfil. Un contrato de 40 cláusulas ⇒ ≈ 40 × (5 consultas + 1 juicio) ≈ 12 min en Perfil A. Debate: ≤ 30 000 tokens por hallazgo disputado. Disco: índice ≈ 1,1 KB/fragmento (vector f32 de 1 024 d comprimido a f16) + texto.

**Salto del debate:** las relaciones `conforme` con `rerank ≥ 0,85` y sin observaciones no se debaten (R0, y su coste supera el beneficio); todo lo demás sí. **Caché:** embeddings por fragmento (`clave = sha256(texto_normalizado)+modelo`), resultados de `retrieve` (`clave = sha256(query)+corpus_version+k`), y juicios con temperatura 0 (`clave = sha256(claim+refs+prompt)+model_hash`). Invalidación: cualquier `corpus.updated` invalida las claves que incluyan esa `corpus_version`.

### 2.8 Calidad y pruebas

| Caso | Criterio de éxito |
|---|---|
| Camino feliz: contrato con convenio arbitral correcto | Los 5 requisitos `conforme`; 0 citas rechazadas por A2-3 |
| Cláusula patológica sembrada (árbitro designado unilateralmente) | Relación `insuficiente` o `nulo-de-pleno-derecho` con cita literal del corpus; detección en 10/10 variantes |
| Alucinación de cita | Sobre 200 respuestas del modelo con citas inyectadas falsas, 100 % rechazadas por A2-3 |
| Memoria de cálculo con error de combinación de cargas | `contradictorio` con el cálculo adjunto; divergencia numérica reportada con ≤ 1 % de tolerancia |
| Norma no cargada | `sin-referencia-en-corpus` en 100 % de los casos; 0 inferencias plausibles |
| Consenso entre agentes | A y B coinciden en `insuficiente`; C otorga ≥ 80/100 |
| Desacuerdo total | B aporta artículo de especialidad que desplaza al de A; C resuelve `amended` y el dictamen cambia de referencia |
| Vigencia | Contrato de 2010 juzgado con el texto vigente en 2010 y anotación del texto actual; 100 % de los hallazgos con `as_of` correcto |

### 2.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta | Estado |
|---|---|---|---|---|
| Corpus vacío o insuficiente | `retrieve` devuelve `rerank < 0,4` en todos los candidatos | Sin base para juzgar | Forzar `sin-referencia-en-corpus` + solicitud de carga | Degradado, honesto |
| Segmentador falla (norma con formato atípico) | fragmentos > 1 200 tokens o sin `locator` en > 20 % | Citas imprecisas | Cambiar a segmentación por párrafo con aviso `locator_weak` | Degradado |
| Reordenador no disponible | health check | Precisión menor | Fusión RRF sin reordenar y umbral elevado a 0,80 | Degradado |
| Sandbox de cálculo caído | excepción al lanzar | Sin verificación numérica | Hallazgos numéricos a `ambiguo`, nunca resueltos por el modelo | Degradado, sin riesgo |
| Fallo parcial: índice denso desincronizado del texto | comprobación de hash al recuperar | Citas apuntando a texto viejo | Reindexado incremental automático + invalidación de caché | Consistente |
| Sin red | — | Sin descarga de normas nuevas | Todo lo demás intacto | Operativo |

### 2.10 Riesgos y mitigaciones

Alucinación de artículos inexistentes (prob. alta sin control, impacto crítico): validador A2-3 mecánico, no opcional. Corpus desactualizado (alta/alto): `as_of` obligatorio, detección de derogación y aviso. Sesgo de recuperación hacia el léxico del contrato (media/medio): consultas dirigidas por requisito, no por copia de la cláusula. Sobreajuste del reordenador a fraseología jurídica peruana (media/bajo): umbrales por tipo de corpus y evaluación separada. Uso indebido como asesoría legal (media/alto): etiqueta obligatoria en la cabecera del dictamen — *"Análisis técnico documentado. No constituye asesoría legal; debe ser revisado por un profesional habilitado"* — y bloqueo de la exportación sin esa cabecera. Tablas partidas en el segmentador técnico (media/alto): unidad indivisible y prueba dedicada.

### 2.11 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA**: `bge-m3` y `bge-reranker-v2-m3` (pesos abiertos), `rank_bm25`, `sqlite-vec`, `sympy` 1.13, `numpy` 2.0, `pint` 0.24, `python-docx` 1.1, `trafilatura` 1.12. **🟡 REQUIERE-PRERREQUISITO**: el usuario debe aportar los textos normativos que quiera usar (DL 1071, E.020, E.030, E.060 u otros) — el plan no los redistribuye, los ingiere desde la fuente que el usuario proporcione; y conexión puntual a Internet si desea descargarlos de fuentes públicas oficiales.

### 2.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (ingesta + segmentador jurídico + BM25 + validador de citas sobre un contrato) → v1 (híbrido + reordenador + taxonomía completa + dictamen) → completo (flujo técnico, recálculo determinista, vigencia y modificatorias).

- **P2.a Ingesta y segmentación.** P2.a.1 lectores — **PV-2.a.1**: 4 formatos ingeridos con hash y sin pérdida de texto (comparación de longitud ±0,5 %). P2.a.2 segmentador jurídico — **PV-2.a.2**: sobre un texto normativo con 100 artículos, 100 % de artículos detectados con su `locator` correcto. P2.a.3 segmentador técnico — **PV-2.a.3**: 0 tablas partidas en 50 tablas de prueba.
- **P2.b Índice.** P2.b.1 BM25 — **PV-2.b.1**: recall@50 ≥ 0,90 sobre 100 consultas con respuesta conocida. P2.b.2 denso — **PV-2.b.2**: recall@50 ≥ 0,88 en las mismas consultas. P2.b.3 fusión + reordenador — **PV-2.b.3**: precisión@1 ≥ 0,80 y ≥ 12 puntos sobre el mejor individual.
- **P2.c Afirmaciones y validación.** P2.c.1 extractor — **PV-2.c.1**: sobre 20 contratos anotados, F1 ≥ 0,85 en extracción de cláusulas con coordenada correcta. P2.c.2 validador de citas — **PV-2.c.2**: 100 % de rechazo de 200 citas falsas inyectadas, 0 % de rechazo de 200 citas verdaderas.
- **P2.d Juicio y recálculo.** P2.d.1 taxonomía — **PV-2.d.1**: acuerdo ≥ 0,85 (kappa) contra 100 alineaciones anotadas manualmente por el usuario. P2.d.2 sandbox — **PV-2.d.2**: 50 cálculos, 100 % ejecutados sin red y con límite de 5 s; divergencias detectadas en los 10 casos sembrados.
- **P2.e Dictamen.** P2.e.1 informe — **PV-2.e.1**: ningún hallazgo sin cita verificada ni sin veredicto del Área 3 (consulta SQL de integridad devuelve 0 filas). P2.e.2 vigencia — **PV-2.e.2**: 10 casos con `as_of` distinto producen la referencia correcta en 10/10.

Métricas de salida: 0 citas no verificadas en el dictamen, precisión@1 ≥ 0,80, kappa ≥ 0,85 en la taxonomía, y 100 % de afirmaciones numéricas recalculadas por código.

---

## ÁREA 3 — Motor de debate popperiano (cognición hostil)

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA.**

### 3.1 Propósito y alcance

Es la ley del sistema: ninguna conclusión, binario, dictamen, diseño físico ni idea inventiva sale sin haber sobrevivido a un intento serio y **registrado** de refutación. Este módulo no sabe de dominios; sabe de procedimiento: emitir afirmaciones falsables, atacarlas con mecanismo, y arbitrar con rúbrica numérica.

Queda fuera: producir el contenido (lo hacen las áreas de dominio), ejecutar acciones (Área 8) y decidir sobre el mundo físico sin medición (la medición manda, §3.10).

**Consume:** todas las áreas de dominio (1, 2, 4, 5, 8, 9, 10, 11), Área 7 (prompts A/B/C), Área 6 (asignación de modelo por rol). **Alimenta:** Área 8 (aprobación de acciones), Área 0 (persistencia del acta), Área 10 (visualización).

### 3.2 Arquitectura

```
   tema + contexto de dominio (evidencia inicial)
              │
              ▼
   ┌────────────────────────────────────────────────────────────┐
   │ ORQUESTADOR DE RONDA (modules/debate/orchestrator.py)      │
   │  ┌──────────┐   claims[]   ┌──────────┐  refutations[]     │
   │  │ AGENTE A │─────────────►│ AGENTE B │──────────────┐     │
   │  │ modelo M1│              │ modelo M2│              │     │
   │  └────▲─────┘              └──────────┘              ▼     │
   │       │ rebuttals[]  ⚠ B NO ve el razonamiento de A ┌────────────┐
   │       └────────────────────────────────────────────►│ AGENTE C   │
   │                                                     │ modelo M3  │
   │  ┌─────────────────────────────────────────────┐    └─────┬──────┘
   │  │ GUARDAS: sicofancia · vacío · bucle ·       │          │ verdicts[]
   │  │ arrastre · colusión · deriva  (§3.8)        │◄─────────┤
   │  └─────────────────────────────────────────────┘          │
   └───────────────────────┬───────────────────────────────────┘
                           │ acta.json (ÚNICO artefacto persistido)
                           ▼
      ┌──────────────────────────────────────────────────────────┐
      │ ¿parada? convergencia | estancamiento | presupuesto | R3  │
      │  no → nueva ronda con contexto comprimido y neutralizado  │
      │  sí → veredicto final → Área 8 (acción) / Área 10 (GUI)   │
      │  ⚠ punto de fallo: prueba ejecutable disponible ⇒ su      │
      │    resultado SUSTITUYE al argumento de los tres agentes   │
      └──────────────────────────────────────────────────────────┘
```

### 3.3 Contratos e interfaces

```python
async def run_round(topic: Topic, ctx: DebateContext, *, parent: RoundId | None = None) -> Acta: ...
async def run_debate(topic: Topic, ctx: DebateContext, budget: DebateBudget) -> DebateResult: ...
def validate_refutation(r: RefutationDraft) -> ValidationResult: ...
def score_claim(claim: Claim, refs: list[Refutation], rebs: list[Rebuttal]) -> Verdict: ...
def compress_history(actas: list[Acta], role: Role, max_tokens: int) -> str: ...
def inject_human_refutation(round_id: RoundId, r: RefutationDraft) -> RefutationId: ...
```

**Esquema JSON completo del acta** (único artefacto que consume el Juez y único que se persiste). Una **deliberación** contiene **varias rondas** y varias **versiones de la propuesta**; el acta las guarda todas, porque el mejor resultado no siempre es el último:

```json
{
  "schema": "acta-2.0",
  "deliberation_id": "dlb_01J8X…",
  "topic": {"id":"tpc_…","area":5,"title":"Portabilidad del módulo de temporización","domain":"binary"},
  "conversation_turn_id": "cnv_…#t7",
  "started_at": "2026-08-02T10:04:11-05:00",
  "ended_at": "2026-08-02T10:23:48-05:00",
  "rounds_planned": {"min": 3, "max": 7},
  "rounds_executed": 5,
  "diversity": "full",

  "model_identity": {
    "MELCHIOR": {"display":"Qwen2.5-Coder 7B Instruct · Q5_K_M · local",
                 "family":"qwen2.5-coder","params_b":7.6,"quant":"Q5_K_M","ctx":32768,
                 "provider":"local-llamacpp","endpoint":"127.0.0.1:8081","weights_sha256":"…",
                 "temperature":0.25,"top_p":0.9,"seed":20260802,"grammar":"claims.gbnf",
                 "runtime":"llama.cpp b3600","accel":"CUDA"},
    "BALTHASAR": {"display":"DeepSeek-R1-Distill-Qwen 7B · Q4_K_M · local","…":"…"},
    "CASPER":   {"display":"Llama 3.1 8B Instruct · Q4_K_M · local","…":"…"}
  },

  "rounds": [
    {
      "round_index": 1,
      "proposal": {
        "version": 1, "author": "MELCHIOR",
        "model_used": "Qwen2.5-Coder 7B Instruct · Q5_K_M · local",
        "plain_summary": "Propongo reutilizar el módulo cambiando sólo tres parámetros.",
        "claims": [{"id":"c1.1","statement":"…","falsifier":"…","evidence":[…],"confidence":0.71,
                    "assumptions":["…"],"changed_from_previous":null}]
      },
      "critique": {
        "author": "BALTHASAR",
        "model_used": "DeepSeek-R1-Distill-Qwen 7B · Q4_K_M · local",
        "plain_summary": "No se sostiene: hay siete llamadas a código específico de la consola.",
        "new_refutations": [{"id":"r1.1","target_claim_id":"c1.1","type":"empirica",
                             "mechanism":"…","reproduction_steps":["…"],"evidence":[…],
                             "severity":"alta","admissible":true}],
        "refined_refutations": [],
        "still_open_from_previous": []
      },
      "arbitration": {
        "author": "CASPER",
        "model_used": "Llama 3.1 8B Instruct · Q4_K_M · local",
        "kind": "analysis",
        "plain_summary": "La objeción es sólida. Falta decidir qué hacer con esas siete llamadas.",
        "full_analysis": "…análisis completo, por criterio de la rúbrica, de la propuesta y de la crítica…",
        "provisional_score": 41,
        "rubric": {"soporte_empirico":9,"consistencia_logica":14,"casos_limite":6,
                   "falsabilidad":10,"reproducibilidad":2,"parsimonia":0,"normativa":0},
        "refutations_upheld": ["r1.1"],
        "refutations_dismissed": [],
        "guidance_for_next_round": {
          "to_MELCHIOR": ["Aborda las siete llamadas: o las aíslas tras una interfaz o cambias de veredicto",
                          "Declara el supuesto de temporización que BALTHASAR ha señalado"],
          "to_BALTHASAR": ["Comprueba si el acoplamiento es sintáctico o también semántico",
                           "Busca casos límite en el manejo de interrupciones, que nadie ha mirado"]
        },
        "best_so_far": {"proposal_version": 1, "score": 41},
        "continue": true, "continue_reason": "puntuación muy por debajo del umbral y mejora plausible"
      },
      "metrics": {"tokens":{"MELCHIOR":{"in":8421,"out":1930},"BALTHASAR":{"in":6110,"out":1502},
                            "CASPER":{"in":9880,"out":2140}},
                  "latency_ms":{"MELCHIOR":21840,"BALTHASAR":17210,"CASPER":24960}}
    }
  ],

  "final": {
    "author": "CASPER", "kind": "final_verdict",
    "selected_proposal_version": 4,
    "why_this_version": "La 4 resuelve las siete llamadas y no reintroduce el problema de la 3.",
    "outcome": "survives|falsified|amended|unfalsifiable|undecided",
    "score": 84,
    "rubric": {"…":"…"},
    "unresolved": [{"refutation_id":"r3.2","reason":"exige una medición en hardware que no hay"}],
    "required_action": {"kind":"none|run_test|measure|amend_claim|escalate_human","spec":{}},
    "plain_summary": "Acepto la cuarta versión: aísla las llamadas y no rompe la temporización."
  },

  "trajectory": [{"round":1,"score":41},{"round":2,"score":58},{"round":3,"score":55},
                 {"round":4,"score":84},{"round":5,"score":84}],
  "stop_reason": "convergence|no_new_refutations|budget_rounds|budget_tokens|budget_time|human_stop|r3_gate",
  "hashes": {"prompt_MELCHIOR":"…","prompt_BALTHASAR":"…","prompt_CASPER":"…","acta_self":"…"}
}
```

Nótese lo que el esquema hace imposible: **una deliberación de una sola ronda** (`rounds_executed ≥ rounds_planned.min`, y el mínimo no puede bajar de 3), **un turno de CASPER • 3 sin análisis completo** (`full_analysis` es obligatorio en cada ronda, no sólo al final) y **cualquier salida sin identidad de modelo declarada** (§I.8).

Eventos: emite `debate.turn` (por turno, con `role`, `round_id`, tokens acumulados), `debate.verdict`, `action.proposed` (cuando un veredicto exige acción). Consume: `action.executed`, `action.failed`, `measurement.recorded` (que entran como evidencia empírica en la ronda siguiente). Tablas: `debate_round`, `claim`, `refutation`, `rebuttal`, `verdict` (DDL en §T3).

**Decisiones formalizadas de esta área.**
**Decisión:** el acta JSON es el único artefacto persistido del debate y la única memoria canónica; los historiales conversacionales de los proveedores se consideran caché desechable — porque así el debate sobrevive a cambios de proveedor, reinicios y expiración de sesiones.
*Descartado:* mantener el hilo conversacional del proveedor como memoria — ata el sistema a un proveedor concreto y se pierde en cualquier reinicio.
**Decisión:** el umbral de aprobación es 70/100 y la franja 60–69 obliga a `amended` con enmienda concreta — porque un umbral único convierte todo desacuerdo en un rechazo y desperdicia trabajo casi válido.
**Decisión:** el BALTHASAR recibe la afirmación y la evidencia de A, pero nunca su razonamiento interno — porque un B que ve el camino de A tiende a imitarlo y a criticar el detalle en vez de atacar el resultado.
**Decisión:** las refutaciones sin mecanismo se rechazan mecánicamente antes de llegar al Juez, no se puntúan bajo — porque puntuarlas bajo aún consume contexto del Juez y le sesga con ruido.

### 3.4 Implementación: los tres roles

**MELCHIOR • 1 — Arquitecto e Ingeniero de Sistemas.** Mandato: producir la propuesta, el código, la decompilación interpretada, el dictamen o el diseño, y expresarla como afirmaciones falsables, **cada una con su `falsifier` explícito**. Prohibiciones codificadas en el validador: sin `falsifier` no hay `claim` (rechazo de esquema); vocabulario de cobertura (`podría`, `quizá`, `en general`, `depende`) detectado por lista de patrones y devuelto para reescritura; `confidence` obligatoria en [0,1]. Formato de salida: JSON `claims[]` bajo gramática GBNF.

**BALTHASAR • 2 — Auditor de Seguridad y Falsacionista.** Mandato: derribar. No propone alternativas amables. Construye el contraejemplo, el caso límite, la entrada maliciosa, la condición de carrera, el modo de fallo físico, la laguna normativa. Obligación: `mechanism` no vacío y `reproduction_steps` con al menos un paso ejecutable o verificable. Formato: JSON `refutations[]` bajo GBNF. **Lo que ve**: `topic`, `claims[]` con su `evidence[]`, y el contexto de dominio — **nunca** el razonamiento interno de A ni sus borradores (aislamiento por construcción del contexto en `compress_history(role="B")`), para que ataque el resultado y no imite el camino.

**CASPER • 3 — Juez Operativo y Árbitro de Concordia.** Mandato: arbitrar el procedimiento, no opinar del tema. Evalúa si la refutación se sostiene, si A la respondió, y puntúa. Obligación: decidir. El esquema **no admite** un veredicto sin `outcome` de la enumeración; `undecided` sólo es válido si `required_action != none` (es decir, si el Juez ordena obtener el dato que falta). "Ambas partes tienen razón" es inexpresable en el esquema.

**Taxonomía de refutaciones y criterio de admisión:**

| Tipo | Qué afirma | Criterio de admisión (verificado mecánicamente antes de llegar a C) |
|---|---|---|
| `empirica` | Existe una ejecución o medición que contradice | `evidence[].kind ∈ {execution, measurement}` con `locator` resoluble en la base |
| `logica` | Contradicción interna o falacia formal | Cita de las dos proposiciones incompatibles de A, ambas presentes en `claims[]` |
| `completitud` | Falta un caso | Enunciado del caso faltante en forma de entrada concreta |
| `suposicion` | A asumió algo no declarado | Identificación textual de la suposición + por qué no está en `claims[].statement` |
| `normativa` | Viola una norma del corpus | `chunk_id` real del Área 2 y cita verificada por A2-3 |
| `reproducibilidad` | No se puede repetir | Registro de ≥ 2 intentos con resultados distintos y sus `run_id` |
| `coste` | No cabe en el presupuesto de recursos declarado | Cifra del presupuesto declarado + estimación con su método |
| `falsabilidad` | La afirmación de A no es falsable en absoluto | Demostración de que ningún experimento posible la contradiría; **puntúa como la más grave** |

**Carga de la prueba (regla explícita).** A afirma; B refuta; **B debe aportar el mecanismo**. Una refutación sin `mechanism` o sin `reproduction_steps` es inadmisible: el validador la marca `admissible=false` y **no llega a C**. Sin esta regla, B degenera en generador de dudas y el debate no converge. Simétricamente, A no puede responder a una refutación admisible con negación: la réplica exige `evidence[]` o `concedes=true`.

**Protocolo de deliberación en varias rondas (nunca una sola).**

*Decisión:* toda deliberación ejecuta **como mínimo 3 rondas completas** y por defecto hasta 7, y en **cada** ronda CASPER • 3 emite su **análisis completo** —no sólo una puntuación— con instrucciones concretas para los otros dos; MELCHIOR • 1 produce entonces una **versión mejorada** de su propuesta y BALTHASAR • 2 **afina sus críticas y busca nuevas** sobre esa versión nueva; y así hasta que CASPER • 3 arbitra cuál de todas las versiones es el mejor resultado posible — porque un veredicto de una sola pasada premia a quien acierta a la primera y desperdicia la única ventaja real de un sistema con tres cabezas: que la propuesta mejore por presión.
*Descartado:* el esquema anterior de una ronda con veredicto inmediato y rondas adicionales sólo si algo fallaba — producía deliberaciones de una sola pasada en la mayoría de los casos, que es exactamente lo que este sistema no debe hacer.

**Ciclo de una ronda `n`:**

| Fase | Quién | Qué produce | Qué ve |
|---|---|---|---|
| 1 | **MELCHIOR • 1** | Propuesta versión `n`: en la ronda 1 es original; a partir de la 2 es una **revisión** que debe responder, una por una, a las refutaciones mantenidas y a las instrucciones de CASPER, marcando en `changed_from_previous` qué ha cambiado y por qué | Tema, evidencia, su propia versión anterior, las refutaciones **mantenidas** y las instrucciones de CASPER dirigidas a él |
| 2 | **BALTHASAR • 2** | Crítica de la versión `n`, separada en **`new_refutations`** (fallos que la versión nueva introduce o que nadie había visto) y **`refined_refutations`** (las anteriores, ahora con mecanismo más fuerte o caso límite más ajustado), más la lista de las que da por resueltas | Tema, evidencia, la propuesta versión `n`, sus propias críticas anteriores y las instrucciones de CASPER dirigidas a él. **Nunca** el razonamiento interno de MELCHIOR |
| 3 | **CASPER • 3** | **Análisis completo** de la ronda: examina propuesta y crítica criterio por criterio, decide qué refutaciones se sostienen y cuáles descarta, emite `provisional_score`, actualiza `best_so_far` y escribe **instrucciones separadas para cada uno** de los otros dos | Todo el acta de la deliberación hasta ese momento |

**Reglas duras del ciclo, todas verificadas por el validador antes de aceptar el turno:**
1. **Mínimo 3 rondas.** Ni siquiera la unanimidad en la ronda 1 termina la deliberación: si nadie objeta, CASPER debe **ordenar a BALTHASAR** un ángulo de ataque no explorado (la lista de ángulos por dominio está en §3.6) y la deliberación continúa. Una propuesta que nadie ha intentado romper tres veces no está probada, está sin probar.
2. **CASPER analiza en todas las rondas.** `full_analysis` no puede estar vacío ni ser una repetición del anterior (huella semántica con umbral 0,90); su función en las rondas intermedias es **dirigir**, no juzgar, y su veredicto vinculante llega sólo en `final`.
3. **MELCHIOR debe cambiar algo o conceder.** Una versión `n+1` idéntica a la `n` (similitud > 0,95) es inadmisible: o hay revisión sustantiva, o MELCHIOR concede explícitamente la refutación y lo declara. La deliberación no avanza por repetición.
4. **BALTHASAR debe atacar lo nuevo.** Al menos una refutación por ronda debe apuntar a algo introducido o modificado en la versión actual; repetir la crítica anterior sin refinarla se rechaza por duplicado. Si tras un análisis serio no encuentra nada nuevo, debe declararlo con `no_new_findings` y **justificar qué atacó y por qué resistió** — declaración que cuenta como evidencia a favor de la propuesta y que CASPER pondera.
5. **El mejor resultado no es el último.** CASPER selecciona en `final.selected_proposal_version` la versión con mejor puntuación entre **todas** las de la deliberación, y debe justificar la elección. Una versión 4 peor que la 2 no se acepta por ser la más reciente: la trayectoria de puntuación queda en el acta precisamente para que esto sea auditable.

**Condiciones de parada** (se evalúan sólo a partir de la ronda 3): **convergencia** — dos rondas consecutivas sin refutación admisible nueva **y** puntuación provisional ≥ umbral **y** CASPER declara `continue:false`; **meseta** — la puntuación no mejora más de 3 puntos en tres rondas consecutivas, se detiene y se selecciona la mejor versión; **oscilación** — la trayectoria alterna entre dos valores con amplitud < 5 puntos, se detiene y CASPER debe justificar cuál de los dos estados elige; **presupuesto** — rondas, tokens o tiempo agotados, con parada y selección de la mejor versión hasta ese punto; **escalada a humano** — `unfalsifiable` en la afirmación principal, acción R3 pendiente, o desacuerdo abierto con presupuesto agotado.

**Mínimos por área** (configurables en el Centro de Configuración, §Área 17, nunca por debajo de 3): dictamen legal y forense **4**, ingeniería inversa y HDL **5**, fabricación física **3**, invención **5**, infraestructura **3**.

**Ampliación por el Área 13.** Todo veredicto `survives` con puntuación ≥ 70 sobre una afirmación estructural o de comportamiento obliga a MELCHIOR • 1 a emitir un **delta de conocimiento** (§13.3) que se persiste y se reinyecta como contexto fijado en las rondas siguientes. Un veredicto favorable sin delta queda **incompleto** y no cierra la ronda: es la diferencia entre un sistema que discute y uno que aprende.

### 3.5 Algoritmos

**A3-1 — Bucle de deliberación en varias rondas.**
```
 1. n := 1; mejor := {version:0, score:-1}; trayectoria := []
 2. MIENTRAS n ≤ max_rondas:
 3.   ── FASE MELCHIOR • 1 ──────────────────────────────────────────────────────────
 3.1   contexto := tema + evidencia + (si n>1: propuesta v(n-1) + refutaciones MANTENIDAS
                                              + instrucciones de CASPER dirigidas a MELCHIOR)
 3.2   propuesta_n := generar(contexto)   [con identidad de modelo declarada, §I.8]
 3.3   validar: ¿claims con falsifier? ¿plain_summary ≤ 140? ¿si n>1, changed_from_previous no vacío
              o concesión explícita? ¿similitud con v(n-1) < 0,95?  → si falla, reintento dirigido (máx 2)
 4.   ── FASE BALTHASAR • 2 ─────────────────────────────────────────────────────────
 4.1   contexto := tema + evidencia + propuesta_n + sus críticas previas
                   + instrucciones de CASPER dirigidas a BALTHASAR   [SIN razonamiento de MELCHIOR]
 4.2   crítica_n := {new_refutations, refined_refutations, resolved}
 4.3   validar cada refutación: mecanismo presente · pasos reproducibles · evidencia del tipo exigido
              · no duplicada (coseno < 0,88 con toda refutación previa)
 4.4   si new_refutations = ∅ y refined_refutations = ∅:
              exigir declaración no_new_findings con la lista de ángulos atacados; si tampoco la da,
              turno inválido y se repite con mandato de ataque forzado
 5.   ── FASE CASPER • 3 ────────────────────────────────────────────────────────────
 5.1   contexto := acta completa de la deliberación hasta aquí
 5.2   análisis_n := {full_analysis, rubric, provisional_score, refutations_upheld,
                      refutations_dismissed, guidance_for_next_round{to_MELCHIOR[], to_BALTHASAR[]},
                      best_so_far, continue, continue_reason}
 5.3   validar: full_analysis no vacío ni repetido (coseno < 0,90 con el de la ronda anterior);
              guidance con ≥ 1 instrucción para cada uno mientras continue = true;
              precedencia de evidencia respetada (§3.10) → si no, turno rechazado
 5.4   trayectoria += {n, provisional_score};  si provisional_score > mejor.score → mejor := {n, score}
 6.   ── PARADA ────────────────────────────────────────────────────────────────────
 6.1   si n < 3 → n := n+1; continuar   [NUNCA se para antes de la tercera ronda]
 6.2   si convergencia ∨ meseta ∨ oscilación ∨ presupuesto ∨ CASPER.continue = false → salir
 6.3   n := n+1
 7. ── VEREDICTO FINAL (CASPER • 3) ──────────────────────────────────────────────────
 7.1   seleccionar mejor versión sobre TODA la trayectoria, no la última
 7.2   emitir final{selected_proposal_version, why_this_version, outcome, score, rubric,
                    unresolved[], required_action, plain_summary}
 7.3   si outcome ∈ {survives, amended} y la afirmación es estructural → exigir delta de conocimiento (§13.3)
 8. casos límite:
 8.1   MELCHIOR no produce propuesta válida en 3 intentos → deliberación abortada, outcome unfalsifiable
 8.2   BALTHASAR declara no_new_findings tres rondas seguidas → se acepta como evidencia de solidez,
         CASPER lo pondera al alza y puede cerrar en la ronda 3 con puntuación alta
 8.3   la puntuación EMPEORA de forma sostenida (3 rondas a la baja) → se detiene y se selecciona la
         mejor versión anterior; se registra regression_detected para el banco de prompts
 9. complejidad: O(rondas × 3) llamadas; el coste está acotado por el presupuesto de §3.7
```

**A3-1b — Selección del mejor resultado (el arbitraje que da sentido a las rondas).**
```
1. candidatas := todas las versiones de propuesta con su puntuación provisional
2. descartar las que tengan alguna refutación mantenida de severidad alta sin resolver
3. entre las restantes, elegir la de mayor puntuación; empate → la de menos suposiciones no declaradas
4. si la elegida NO es la última, CASPER debe explicar qué introdujo la última que la empeoró
5. si ninguna candidata sobrevive al filtro del paso 2 → outcome = falsified, y el acta conserva
     igualmente toda la trayectoria: saber por qué fracasaron cuatro versiones vale más que un "no"
```

**A3-2 — Rúbrica híbrida: 60 puntos los calcula la máquina, 40 los juzga el modelo.**

*Decisión:* la puntuación se parte en una **mitad mecánica**, calculada por reglas deterministas sobre hechos verificables, y una **mitad de juicio**, que sólo el modelo puede emitir; la mecánica pesa **60 de 100** y CASPER • 3 **no puede alterarla** — porque pedirle a un modelo de ocho mil millones de parámetros que evalúe la calidad de un razonamiento es pedirle justo aquello en lo que los modelos pequeños son peores, y dejar que además ponga los puntos del soporte empírico convierte la puntuación en una opinión sobre una opinión.
*Descartado:* la rúbrica íntegramente juzgada por el modelo de las revisiones anteriores — era el punto más frágil del sistema y la debilidad D1 lo señalaba sin corregirlo.

| Criterio | Peso | Quién lo puntúa | Cómo |
|---|---|---|---|
| **Soporte empírico** | 30 | **Máquina** | 30 si existe evidencia de rango 1 o 2 (medición o ejecución determinista) enlazada y verificada; 15 si sólo hay rango 3 (análisis estático, consulta al grafo); 5 si sólo rango 4 (cita); **0 si sólo hay razonamiento**. Se lee de la tabla `evidence`, no del texto |
| **Reproducibilidad** | 10 | **Máquina** | 10 si los pasos declarados se ejecutaron y volvieron a dar el mismo resultado; 5 si son ejecutables pero no se han ejecutado; 0 si no lo son |
| **Falsabilidad** | 12 | **Máquina** | 12 si toda afirmación tiene `falsifier` que menciona una observación concreta (verificado con reglas léxicas y con la existencia de una prueba asociada); 0 si prosperó una refutación de tipo `falsabilidad` |
| **Cumplimiento normativo** | 5 | **Máquina** | 5 con cita validada por el §A2-3; 0 ante violación acreditada; se redistribuye si no aplica |
| **Resolución de refutaciones** | 3 | **Máquina** | Proporción de refutaciones mantenidas que la versión actual **resuelve de forma comprobada** (prueba, consulta o medición), no de forma declarada |
| *Subtotal mecánico* | **60** | | |
| **Consistencia lógica** | 20 | Modelo | Descuento de 5 por contradicción interna acreditada; CASPER debe citar ambas proposiciones |
| **Cobertura de casos límite** | 12 | Modelo | Proporción de casos planteados por BALTHASAR • 2 que la propuesta aborda |
| **Parsimonia** | 8 | Modelo | Descuento de 2 por suposición no declarada identificada |
| *Subtotal de juicio* | **40** | | |

**Umbral de aprobación: 70/100.** Consecuencia directa e intencionada del reparto: **una propuesta sin evidencia dura no puede aprobarse**, porque el máximo alcanzable sin ejecución ni medición es 30 (mecánico parcial) + 40 (juicio perfecto) = 70 sólo en el caso imposible de que todo lo demás sea perfecto y el soporte empírico sea de rango 3; con sólo razonamiento, el techo real es 55. Franja 60–69 → `amended` con enmienda concreta. Por debajo de 60 → `falsified`.

**Puntuación ciega (contra el sesgo de novedad).** CASPER • 3 puntúa las versiones **sin saber cuál es más reciente**: se le presentan con etiquetas neutras barajadas (`propuesta-α`, `propuesta-β`…) y el orden se aleatoriza con una semilla registrada. La correspondencia se restablece después, fuera del modelo. Verificación: sobre un conjunto de control donde la mejor versión se coloca al azar, la posición no debe correlacionar con la puntuación (|ρ| ≤ 0,15).

**Regla de trinquete (contra la mejora cosmética).** La puntuación de la versión `n` **no puede superar la mejor anterior** salvo que la versión `n` resuelva **de forma comprobada mecánicamente** al menos una refutación mantenida — resuelta significa que una prueba, una consulta al grafo o una medición lo confirma, no que MELCHIOR • 1 lo afirme. Si no hay resolución comprobada, la puntuación queda acotada al máximo anterior y CASPER debe decirlo. Una reescritura más elegante no sube la nota.

**Repuntuación en contexto limpio (contra el artefacto de procedimiento).** Al terminar, las **dos mejores versiones** se vuelven a puntuar en una sesión **sin historial**: sólo el enunciado del problema, la versión y su evidencia. Se calcula `inflación_procedimental = puntuación_en_deliberación − puntuación_en_contexto_limpio`. Si supera **10 puntos**, la deliberación se marca `procedural_inflation` y la puntuación válida es la del contexto limpio. Es la prueba directa de que la trayectoria ascendente no es un efecto de haber leído mucho texto.

**A3-3 — Guardas anti-degeneración (detector y respuesta).**

| Guarda | Detector | Umbral | Respuesta |
|---|---|---|---|
| Sicofancia | `refutation_substantive_rate` = admisibles / total emitidas por B | < 0,35 durante 2 rondas | Inyectar mandato de refutación forzada ("emite al menos 2 refutaciones admisibles de tipos distintos") y, si persiste, rotar el modelo de B según §6.2 |
| Debate vacío | `validate_refutation` | cualquier refutación sin mecanismo | Rechazo antes de C, con motivo devuelto a B |
| Bucle | huella semántica del `mechanism`, y además huella del `full_analysis` de CASPER y de cada versión de propuesta | coseno ≥ 0,88 (refutación), ≥ 0,90 (análisis de CASPER), ≥ 0,95 (propuesta de MELCHIOR) | Rechazo por duplicado; a la tercera repetición, parada por estancamiento |
| Sesgo de arrastre | Similitud entre la propuesta de la ronda n y la n−1 | coseno ≥ 0,95 ⇒ turno inválido; ≥ 0,88 ⇒ aviso a CASPER para que endurezca sus instrucciones | Ronda de **reinicio ciego** cada 3 rondas: A vuelve a proponer viendo sólo `topic` + evidencia, sin su propuesta anterior |
| Colusión de modelo | Regla de diversidad §I.3 + `divergencia_léxica` | < 0,35 dos rondas | Forzar modo degradado explícito (temperatura, semilla, orden de contexto) y marcar `diversity: degraded` |
| Deriva de tema | Similitud del contenido del turno con `topic.title` + `topic.description` | coseno < 0,45 | Penalización de 10 puntos en la rúbrica y reinyección del anclaje al tema en el prompt |
| **Complacencia del juez** (control de crítica simulada) | Con probabilidad `p = 1/20` (configurable, nunca 0) se ejecuta una **ronda sombra**: se le entrega a CASPER • 3 la misma propuesta con las críticas de BALTHASAR • 2 **sustituidas por críticas perturbadas o tomadas de otro tema**, y se compara su puntuación con la de la ronda real | Si la puntuación de la ronda sombra **no baja al menos 15 puntos**, el juez está puntuando el texto y no el contenido | Marcar `judge_complacency` en el acta, invalidar la puntuación de juicio de esa deliberación (se conserva la mecánica), abrir hallazgo de calidad de prompt y, si ocurre en 3 de 20 deliberaciones, **rotar el modelo de CASPER • 3** |
| **Inflación procedimental** | `inflación = puntuación_en_deliberación − puntuación_en_contexto_limpio` sobre las dos mejores versiones | > 10 puntos | La puntuación válida pasa a ser la del contexto limpio; se registra y alimenta el banco |

### 3.6 Integración con el debate popperiano (aplicación por dominio)

Esta subsección es, en esta área, la especificación de cómo cambia el debate según el objeto:

| Objeto | Evidencia admisible | Refutación más potente disponible |
|---|---|---|
| Código fuente | Ejecución de test unitario, salida del compilador, análisis estático (ruff/mypy/clang-tidy) | Test que falla, escrito por B y ejecutado por el Área 8 |
| Binario decompilado | Traza de ejecución en QEMU/Unicorn, comparación de registros, hash de fotograma | **Prueba diferencial** contra el emulador de referencia: el primer punto de divergencia (§5.5) |
| Dictamen legal | Cita verificada del corpus con locator real y vigencia | Referencia de especialidad, jerarquía superior o vigencia posterior que desplaza la de A |
| Análisis forense documental | Medición de rasgos, corpus sintético con verdad de terreno | Explicación benigna verificada que hace caer la métrica bajo umbral |
| Diseño mecánico | Verificación geométrica (manifold, voladizos), medición dimensional de la pieza impresa | Medición física de la pieza fabricada fuera de tolerancia |
| Diseño de PCB | ERC/DRC, simulación, medición con multímetro o analizador lógico | DRC que falla o medición eléctrica que contradice el diseño |
| Módulo HDL | Simulación (iverilog/Verilator), co-simulación contra el modelo de referencia, prueba formal | **Contraejemplo de SymbiYosys**: el probador formal encuentra la traza que viola la propiedad |
| Idea inventiva | Cálculo por primeros principios, arte previo hallado, coste de materiales | Violación de un límite físico demostrada por cálculo, o patente anterior con reivindicación equivalente |

### 3.7 Costos, latencia y recursos

Presupuesto por ronda (Perfil A, modelos de 7B): A ≈ 8 400 tokens de entrada / 1 900 de salida (22 s); B ≈ 6 100 / 1 500 (17 s); C ≈ 5 000 / 850 (9 s). Ronda completa ≈ 22 750 tokens y ≈ 48 s. Debate típico de 3 rondas ≈ 68 000 tokens y ≈ 2 min 30 s. Presupuesto duro por defecto: `max_rounds=5`, `max_tokens=150000`, `max_wall_s=900`. VRAM: si los tres modelos no caben simultáneamente (Perfil A), se cargan y descargan por turno con `proveedor de nube --model-alias` y caché de KV en disco; coste de conmutación ≈ 4,5 s por cambio, presupuestado. **Salto del debate:** operaciones R0 deterministas y con verificación mecánica más barata que el debate (criterio de §0.7). **Caché:** el turno de C con temperatura 0 se cachea por `sha256(acta_sin_verdicts)+model_hash+prompt_hash`; los turnos de A y B **no** se cachean entre rondas distintas (el contexto cambia por diseño), pero sí en reejecución idéntica de una ronda revertida desde la GUI.

### 3.8 Calidad y pruebas

| Caso | Criterio de éxito |
|---|---|
| Camino feliz | Afirmación verdadera con evidencia sólida: `survives` con score ≥ 75 en ≤ 2 rondas |
| Afirmación falsa sembrada | `falsified` en ≤ 3 rondas en ≥ 90 % de 50 casos sembrados con error conocido |
| Consenso entre agentes | A y B coinciden; C no eleva la puntuación por encima de la evidencia disponible (score ≤ 60 si sólo hay razonamiento) |
| Desacuerdo total | 20 casos con evidencia contradictoria: C emite `undecided` con `required_action` concreta en 20/20; 0 empates sin desempate |
| Refutación sin mecanismo | 100 % rechazadas por el validador; nunca llegan a C |
| Bucle | Inyectar 10 reformulaciones de la misma refutación: ≥ 9 rechazadas por duplicado |
| Sicofancia inducida (A y B mismo modelo) | La guarda dispara en ≤ 2 rondas y el acta queda marcada `diversity: degraded` |
| Precedencia de evidencia | Caso donde el modelo argumenta contra una medición real: el veredicto sigue a la medición en 20/20 |
| Reproducibilidad del acta | Reejecución con misma semilla y contexto ⇒ `acta_self` idéntico en ≥ 95 % (los modelos deterministas con temperatura 0) |

### 3.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta | Estado |
|---|---|---|---|---|
| Un rol sin modelo disponible | health check + registro de proveedores | Debate imposible | Reasignar según §6.2; si sólo hay un modelo, modo degradado con diversidad forzada | Degradado, marcado en acta |
| Salida no válida contra el esquema | validación pydantic/GBNF | Turno perdido | Bucle de reparación (§7.4): error exacto al modelo, máx. 3 intentos, luego turno vacío registrado | Degradado |
| Contexto desbordado | conteo de tokens antes de enviar | Truncamiento silencioso | Poda jerárquica con fijación de contrato de salida y evidencia citada (§7.5) | Operativo |
| Fallo parcial: C emite veredicto para un `claim_id` inexistente | validación referencial | Acta inconsistente | Rechazo y reintento; si persiste, `undecided` + escalada | Consistente |
| Presupuesto agotado con desacuerdo | contadores | Sin conclusión | `stop_reason=budget_*`, escalada a humano con informe del punto de bloqueo | Explicado |
| Sin red | — | Ninguno con modelos locales | Nada | Operativo |

### 3.10 Riesgos y mitigaciones — y la precedencia de evidencia

Riesgos: teatro de debate por colusión de modelos (alta/alto → regla de diversidad y métrica de divergencia); Juez complaciente (media/alto → rúbrica con techo por tipo de evidencia: sin ejecución, máximo 15/30 en soporte empírico, luego el score no puede llegar a 70 sin evidencia dura salvo con puntuaciones perfectas en el resto, lo que se audita); coste de tokens desbordado (media/medio → presupuesto duro y salto del debate en R0); dependencia del orden MELCHIOR→BALTHASAR→CASPER (baja/medio → reinicio ciego periódico); antropomorfización del acta en la GUI (media/bajo → el acta cruda siempre visible).

**Puente a la realidad — precedencia de evidencia (regla normativa del sistema entero):**

```
medición física  >  ejecución determinista  >  análisis estático  >  cita normativa  >  razonamiento del modelo
```

Implementación: cada `Evidence` lleva `tier ∈ {1..5}` según esa escala. El Juez **no puede** emitir un veredicto que contradiga la evidencia de mayor `tier` disponible; el validador de veredictos comprueba esta condición y rechaza el turno con `code=EVIDENCE_PRECEDENCE`. Cuando existe una prueba ejecutable o una medición, el resultado real gana siempre sobre el argumento de cualquier agente, incluido C.

### 3.11 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA**: sólo requiere el motor de inferencia local del §I.3 y `bge-m3` para las huellas semánticas de las guardas. Ningún hardware, ninguna cuenta.

### 3.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (una ronda MELCHIOR→BALTHASAR→CASPER con acta válida y rúbrica) → v1 (guardas, presupuesto, parada por convergencia, acción propuesta) → completo (aplicación por dominio, reinicio ciego, precedencia de evidencia verificada, visualización del grafo).

- **P3.a Esquema y validadores.** P3.a.1 modelos pydantic del acta — **PV-3.a.1**: 200 actas sintéticas válidas y 200 inválidas clasificadas correctamente al 100 %. P3.a.2 GBNF por rol — **PV-3.a.2**: 500 generaciones locales, 100 % JSON válido sin reintentos. P3.a.3 validador de refutaciones — **PV-3.a.3**: 100 % de rechazo de refutaciones sin mecanismo.
- **P3.b Ronda básica.** P3.b.1 orquestador MELCHIOR→BALTHASAR→CASPER — **PV-3.b.1**: 20 rondas completas sin excepción, acta persistida y hash estable. P3.b.2 aislamiento de contexto de B — **PV-3.b.2**: auditoría automática del prompt de B: 0 apariciones del razonamiento interno de A (comprobación por hash de fragmentos).
- **P3.c Rúbrica y veredictos.** P3.c.1 puntuación — **PV-3.c.1**: sobre 100 casos anotados, correlación de Spearman ≥ 0,8 entre el score y la anotación humana del usuario. P3.c.2 precedencia de evidencia — **PV-3.c.2**: 20/20 veredictos siguen la medición; 0 rechazos falsos.
- **P3.d Guardas.** P3.d.1 sicofancia y bucle — **PV-3.d.1**: disparo en ≤ 2 rondas en los escenarios inducidos; 0 falsos disparos en 20 debates sanos. P3.d.2 arrastre y deriva — **PV-3.d.2**: reinicio ciego ejecutado cada 3 rondas y similitud entre propuestas < 0,93 tras el reinicio.
- **P3.e Integración.** P3.e.1 acción propuesta y realimentación — **PV-3.e.1**: un fallo real de ejecución aparece como refutación `empirica` en la ronda siguiente en 10/10 casos. P3.e.2 presupuesto y parada — **PV-3.e.2**: ningún debate excede `max_tokens` ni `max_wall_s` en 50 ejecuciones.

Métricas de salida: 100 % de actas válidas contra esquema, ≥ 90 % de detección de afirmaciones falsas sembradas, correlación ≥ 0,8 con la anotación humana, y 0 veredictos que contradigan evidencia de mayor `tier`.

---

## ÁREA 4 — Interacción en tiempo real con dispositivos (live device telemetry)

**Estado de construibilidad del módulo: 🟡 REQUIERE-PRERREQUISITO** — el software es libre y 🟢; validar cada perfil exige poseer el dispositivo correspondiente (teléfono Android, PSP, DS, Vita, impresora, MCU), que el usuario ya tenga o no. Coste cero de software; hardware sólo el que ya se posee.

### 4.1 Propósito y alcance

Convierte el puerto USB en un sentido del sistema: enumera lo que se conecta, lo identifica, abre el canal adecuado (almacenamiento, MTP, ADB, DFU, CDC-ACM serie, HID, UVC), y transporta datos y vídeo en vivo hacia el motor de IA con presupuesto de recursos, backpressure y privacidad.

Queda fuera: el análisis del contenido extraído (Área 5), el control de la impresora (Área 9.A, que consume este módulo para el transporte serie) y el flasheo (Área 9.D, ídem).

**Consume:** Área 0 (HAL USB/serie, bus, DuckDB). **Alimenta:** Área 1 (fotogramas para el VLM), Área 5 (binarios extraídos), Área 9 (transporte a impresora y programadores), Área 10 (gráficas y monitores).

### 4.2 Arquitectura

```
   ┌───────────────┐  hotplug   ┌───────────────────┐  descriptores  ┌──────────────┐
   │ HotplugHAL    │───────────►│ IDENTIFICADOR     │───────────────►│ PERFILADOR   │
   │ udev / WM_DEV │ evento     │ (VID/PID, clase,  │  desconocido→  │ (interrogación
   └───────────────┘            │  endpoints)       │  seguro        │  de firmware)│
                                └─────────┬─────────┘                └──────┬───────┘
                                          │ device_profile                  │
                                          ▼                                 ▼
   ┌──────────────────────────────────────────────────────────────────────────────┐
   │ SELECTOR DE MODO   msc │ mtp │ adb │ fastboot │ dfu │ cdc-acm │ hid │ uvc     │
   │  ⚠ decisión: modo compuesto → se elige por prioridad declarada en el perfil   │
   └───┬───────┬────────┬───────────┬──────────┬───────────┬────────────┬─────────┘
       │ files │ files  │ shell     │ flash    │ frames    │ bytes      │ frames
       ▼       ▼        ▼           ▼          ▼           ▼            ▼
   ┌────────┐ ┌────┐ ┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
   │ montaje│ │MTP │ │ADB srv │ │fastboot│ │ scrcpy   │ │ serie    │ │ UVC      │
   │ RO     │ │    │ │ propio │ │ /DFU   │ │ H.264    │ │ ring buf │ │ (Vita)   │
   └───┬────┘ └─┬──┘ └───┬────┘ └───┬────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
       └────────┴────────┴──────────┘           │            │            │
                    │ artefactos al CAS          │ PyAV       │ muestras   │
                    ▼                            ▼            ▼            ▼
              ┌──────────┐          ┌──────────────────────────────────────────┐
              │ Área 5   │          │ MUESTREADOR ADAPTATIVO (§4.5)            │
              │ triaje   │          │  ⚠ punto de fallo: un VLM no come 60 fps │
              └──────────┘          │  drop-oldest + escena + presupuesto/min  │
                                    └──────────────────┬───────────────────────┘
                                                       ▼ fotogramas seleccionados → Área 1 (VLM local)
```

### 4.3 Contratos e interfaces

```python
def enumerate_devices() -> list[DeviceInfo]: ...
def watch_hotplug(cb: Callable[[HotplugEvent], None]) -> WatcherHandle: ...
def identify(dev: DeviceInfo) -> DeviceProfile: ...
def open_mode(dev: DeviceInfo, mode: DeviceMode, opts: dict) -> DeviceSession: ...
async def stream_frames(sess: DeviceSession, budget: FrameBudget) -> AsyncIterator[Frame]: ...
async def stream_serial(sess: DeviceSession, parser: LineParser) -> AsyncIterator[TelemetrySample]: ...
def pull_files(sess: DeviceSession, remote: str, local: Path, *, filter: FileFilter) -> PullReport: ...
```

`telemetry.sample` (contrato del evento): `{device_id, channel, value: float, unit: str, t_mono_ns: int, t_wall: str, seq: int, quality: "ok|interpolated|lost"}`. La pérdida se detecta por hueco en `seq` y se emite una muestra `lost` con el número de muestras ausentes, en lugar de silenciar el hueco. Tablas: `device`, `device_session`, `measurement` (DDL en §T3); la telemetría de alta frecuencia va a DuckDB/Parquet, no a SQLite.

### 4.4 Implementación

**Enumeración e identificación.** Linux: `pyudev` 0.24 con `MonitorObserver` sobre el subsistema `usb` y `tty`; reglas udev escritas literalmente en `packaging/linux/udev/99-magi.rules`:

```
# 99-magi.rules — acceso sin root para el grupo plugdev; instalar en /etc/udev/rules.d/
# Sony (PSP, PS Vita, dispositivos DualShock)
SUBSYSTEM=="usb", ATTR{idVendor}=="054c", MODE="0660", GROUP="plugdev", TAG+="uaccess"
# Nintendo (consolas y accesorios)
SUBSYSTEM=="usb", ATTR{idVendor}=="057e", MODE="0660", GROUP="plugdev", TAG+="uaccess"
# Puentes USB-serie habituales en impresoras 3D y placas de desarrollo
SUBSYSTEM=="usb", ATTR{idVendor}=="1a86", MODE="0660", GROUP="dialout", TAG+="uaccess"  # QinHeng CH340/CH341
SUBSYSTEM=="usb", ATTR{idVendor}=="10c4", MODE="0660", GROUP="dialout", TAG+="uaccess"  # Silicon Labs CP210x
SUBSYSTEM=="usb", ATTR{idVendor}=="0403", MODE="0660", GROUP="dialout", TAG+="uaccess"  # FTDI
SUBSYSTEM=="usb", ATTR{idVendor}=="2341", MODE="0660", GROUP="dialout", TAG+="uaccess"  # Arduino
SUBSYSTEM=="usb", ATTR{idVendor}=="1eaf", MODE="0660", GROUP="dialout", TAG+="uaccess"  # Leaflabs Maple
# Microcontroladores y programadores
SUBSYSTEM=="usb", ATTR{idVendor}=="0483", MODE="0660", GROUP="plugdev", TAG+="uaccess"  # STMicroelectronics (ST-Link, DFU)
SUBSYSTEM=="usb", ATTR{idVendor}=="1366", MODE="0660", GROUP="plugdev", TAG+="uaccess"  # SEGGER J-Link
SUBSYSTEM=="usb", ATTR{idVendor}=="03eb", MODE="0660", GROUP="plugdev", TAG+="uaccess"  # Microchip/Atmel
SUBSYSTEM=="usb", ATTR{idVendor}=="1d50", MODE="0660", GROUP="plugdev", TAG+="uaccess"  # OpenMoko (proyectos libres)
SUBSYSTEM=="usb", ATTR{idVendor}=="0d28", MODE="0660", GROUP="plugdev", TAG+="uaccess"  # ARM mbed / CMSIS-DAP
SUBSYSTEM=="usb", ATTR{idVendor}=="303a", MODE="0660", GROUP="plugdev", TAG+="uaccess"  # Espressif
# Puertos serie: acceso por grupo dialout
KERNEL=="ttyACM[0-9]*", MODE="0660", GROUP="dialout", TAG+="uaccess"
KERNEL=="ttyUSB[0-9]*", MODE="0660", GROUP="dialout", TAG+="uaccess"
# Regla de identificación para el núcleo: exporta una propiedad consumible por pyudev
SUBSYSTEM=="usb", ENV{ID_MAGI}="1"
```

Windows: registro de notificaciones con `CM_Register_Notification` (CfgMgr32) y ventana oculta que atiende `WM_DEVICECHANGE` en un hilo dedicado, más `SetupDiGetClassDevs`/`SetupDiEnumDeviceInterfaces` (SetupAPI) para enumerar. **Prerrequisito documentado para el usuario 🟡:** los dispositivos que requieran acceso genérico (no CDC ni MSC) necesitan el controlador WinUSB o libusbK, instalado con Zadig 2.9; el sistema detecta la ausencia del controlador (`libusb` devuelve `LIBUSB_ERROR_NOT_SUPPORTED`) y muestra la instrucción exacta en la GUI en vez de fallar en silencio.

Tabla VID/PID→perfil (extracto normativo; el fichero completo vive en `profiles/devices/*.yaml`):

| VID:PID | Dispositivo | Modos ofrecidos | Prioridad |
|---|---|---|---|
| `054c:01c8` | PSP (modo almacenamiento masivo) | `msc` | msc |
| `054c:0*` (clase 08) | Familia Sony almacenamiento | `msc` | msc |
| `054c:06f*` | PS Vita (modos USB) | `msc`, `mtp` | mtp si el descriptor anuncia PTP/MTP |
| `057e:*` | Nintendo (según modelo y accesorio) | `msc` (flashcart como lector), `hid` | msc |
| `18d1:4ee*` | Android (Google, modos ADB/MTP) | `mtp`, `adb`, `fastboot` | adb si `interface class=ff subclass=42 protocol=1` |
| `1a86:7523` | CH340 | `cdc-acm` | serie |
| `10c4:ea60` | CP210x | `cdc-acm` | serie |
| `0403:6001` | FT232 | `cdc-acm` | serie |
| `0483:df11` | STM32 en DFU | `dfu` | dfu |
| `2341:0043` | Arduino Uno R3 | `cdc-acm` | serie |
| `0d28:0204` | CMSIS-DAP | `hid`/`swd` | swd |

**Dispositivo desconocido:** interrogación segura y sin escritura — leer descriptor de dispositivo, configuración, interfaces y endpoints (`libusb_get_*_descriptor`), leer cadenas iManufacturer/iProduct/iSerial, clasificar por `bDeviceClass`/`bInterfaceClass` (08 = almacenamiento, 02/0a = CDC, 03 = HID, 0e = vídeo, ff = específico del fabricante), y proponer un perfil tentativo con `confidence`. Nunca se envía un comando de clase específica a un dispositivo no identificado.

**Integración de ADB y scrcpy (detallada).** *Decisión:* el núcleo gestiona su **propio** servidor ADB (binario en `tools/platform-tools/`, arrancado con `adb -P 5038 start-server` en un puerto no estándar) — porque el `adb` del sistema puede ser de otra versión y reiniciar el servidor ajeno mataría las sesiones del usuario.
Secuencia: (1) `adb -P 5038 devices -l` para estado; (2) si `unauthorized`, mostrar en la GUI la instrucción de aceptar la huella RSA en el teléfono y esperar; (3) `adb shell`, `adb push/pull`, `adb forward tcp:<local> localabstract:scrcpy`, `adb reverse` según necesidad; (4) capacidades requeridas `usb.claim` + `proc.spawn`.
Vídeo: **scrcpy 2.x se usa como fuente de vídeo, no como ventana.** Se sube `scrcpy-server.jar` con `adb push`, se lanza con `adb shell CLASSPATH=/data/local/tmp/scrcpy-server app_process / com.genymobile.scrcpy.Server <ver> video_bit_rate=4000000 max_size=1280 max_fps=15 audio=false control=false tunnel_forward=true`, y el núcleo conecta al socket reenviado (`localabstract:scrcpy`) leyendo el **flujo H.264 crudo** (cabecera de dispositivo + paquetes con PTS). Decodificación con PyAV 12.x (`av.CodecContext.create('h264','r')`) a fotogramas `ndarray`. Alternativa equivalente soportada: `scrcpy --no-playback --record=- --record-format=mkv` leyendo de stdout con PyAV. *Descartado:* capturar la ventana de scrcpy con captura de pantalla — introduce recompresión, latencia y dependencia del gestor de ventanas.
Casos de uso exigidos: **(a) abrir un navegador y navegar por control remoto** — `adb shell am start -a android.intent.action.VIEW -d <url>`, y la navegación por `adb shell input tap X Y` / `input swipe` / `input text`, con las coordenadas propuestas por el VLM a partir del fotograma y **validadas** con una captura posterior (postcondición: el fotograma cambia y contiene el elemento esperado); **(b) reproducir multimedia y analizarlo** — lanzar el reproductor por intent y muestrear fotogramas + `adb shell dumpsys media.metrics` como telemetría; **(c) extraer el flujo en vivo hacia el motor de IA** — §4.5.

**Perfiles de consola (honestos).**

| Consola | Vía real | Con consola de fábrica | Con firmware personalizado (prerrequisito del usuario) |
|---|---|---|---|
| PSP | Modo USB de almacenamiento masivo (Memory Stick) | Leer/escribir la Memory Stick; nada del sistema | `USBHostFS` con PSPLink (host `usbhostfs_pc`) para sistema de ficheros remoto y consola de depuración; volcado de la UMD **del propio usuario** a ISO para uso local |
| Nintendo DS / 3DS | Flashcart como lector de tarjetas (MSC) | Acceso a la microSD del flashcart | 3DS: servicios homebrew por red/USB (`ftpd`, `3dslink` sobre USB o Wi-Fi) para transferir y depurar |
| PS Vita | VitaShell en modo USB (almacenamiento masivo) o MTP | Copia de contenido por el gestor oficial; muy limitado | VitaShell (MSC/MTP), `psvimgtools` para copias de seguridad del propio usuario, y **`udcd_uvc`** que expone la pantalla de la Vita como cámara web UVC — la vía real para meter su vídeo en el motor de IA |

Todo dump de firmware/BIOS/ROM leído del dispositivo del usuario queda sujeto a **CTL-1** (§I.4): se trabaja localmente, jamás se empaqueta en un artefacto de salida.

**Telemetría serie genérica.** Búfer circular de 1 MiB por dispositivo (`collections.deque` sobre `bytearray` con vista), marcado con `time.monotonic_ns()` en el instante de lectura del kernel, tasa configurable, detección de pérdida por `seq` cuando el firmware la provee o por hueco temporal > 2,5 × período nominal cuando no. Serialización por lotes de 5 000 muestras a Parquet/DuckDB.

Tabla de paridad:

| Elemento | Impl. Windows | Impl. Linux |
|---|---|---|
| Hotplug | `CM_Register_Notification` + `WM_DEVICECHANGE` | `pyudev.MonitorObserver` (netlink) |
| Enumeración | SetupAPI/CfgMgr32 + `libusb-1.0` | `pyudev` + `libusb-1.0` |
| Acceso genérico USB | WinUSB/libusbK (Zadig 2.9 como prerrequisito 🟡) | permisos por udev/`uaccess`, sin driver extra |
| Serie | `COM*`, apertura con `pyserial` y control explícito de DTR/RTS | `/dev/ttyACM*`, `/dev/ttyUSB*`, grupo `dialout` |
| Montaje MSC | letra de unidad asignada por el SO; lectura por ruta | montaje en `/run/media/...` o `udisksctl mount -b /dev/sdX1` |
| MTP | Shell API / WPD | `libmtp` (`mtp-*`) o `gio mount mtp://` |
| UVC (Vita con `udcd_uvc`) | Media Foundation vía OpenCV `CAP_MSMF` | V4L2 `/dev/video*` vía OpenCV `CAP_V4L2` |
| ADB | binario `adb.exe` propio en `tools\platform-tools` | binario `adb` propio en `tools/platform-tools` |

**Decisiones formalizadas adicionales de esta área.**
**Decisión:** el núcleo gestiona su propio servidor ADB en el puerto 5038 y su propio binario de `platform-tools` — porque reiniciar el servidor del sistema mataría las sesiones del usuario y una versión distinta rompe el protocolo en silencio.
*Descartado:* usar el `adb` del sistema — más simple, pero introduce un modo de fallo ajeno e invisible.
**Decisión:** los flujos de pantalla del dispositivo del usuario se analizan por defecto **sólo** con el VLM local, y su envío a cualquier proveedor remoto exige consentimiento explícito por sesión sin opción de recordarlo — porque la pantalla de un teléfono es el dato más sensible que este sistema puede llegar a ver.

### 4.5 Algoritmos

**A4-1 — Muestreador adaptativo de fotogramas (el punto crítico: un VLM no consume 60 fps).**
```
 1. presupuesto: FrameBudget{max_frames_per_min: 12 (Perfil A) | 6 (Perfil B), min_interval_ms: 900}
 2. cola de fotogramas decodificados con maxlen=4 y política DROP-OLDEST (nunca bloquea al decodificador)
 3. por cada fotograma f llegado:
    3.1 reducir a 320×180 en gris (barato) → f'
    3.2 d_hist := distancia de Bhattacharyya entre histograma(f') y histograma(último enviado)
    3.3 d_ssim := 1 − SSIM(f', último enviado)   [sólo si d_hist supera 0,08, para ahorrar CPU]
    3.4 puntuación de novedad s := 0,4·d_hist + 0,6·d_ssim
 4. enviar al VLM si  s ≥ 0,18  Y  (ahora − último_envío) ≥ min_interval_ms  Y  cuota del minuto > 0
 5. si la cuota se agota: conservar el fotograma de mayor s del minuto y enviarlo al reponerse la cuota
 6. eventos de escena forzada (siempre se envía, ignorando s): tras un tap/swipe sintético, tras
       cambio de actividad detectado por `adb shell dumpsys activity | grep mResumedActivity`, y al inicio
 7. latencia extremo a extremo objetivo: captura→decodificación ≤ 120 ms; decodificación→decisión ≤ 25 ms;
       decisión→respuesta del VLM ≤ 3,5 s (Perfil A). Objetivo total ≤ 4,0 s p95
 8. caso límite: vídeo estático (menú fijo) ⇒ 1 fotograma/min como latido, para detectar congelación
```

**A4-2 — Handshake genérico de puerto serie (usado también por el Área 9.A).**
```
 1. abrir puerto con DTR=False, RTS=False para NO reiniciar el MCU al abrir (trampa clásica de Marlin)
 2. si el perfil exige reinicio (bootloader Arduino): pulsar DTR 100 ms, esperar 2,0 s
 3. autodetección de baudios: probar [115200, 250000, 57600, 230400, 500000] en ese orden;
       criterio: recibir ≥ 1 línea con ≥ 90 % de bytes imprimibles en 3,0 s
 4. drenar el búfer de entrada; enviar el comando de identidad del perfil (p. ej. M115 en impresoras)
 5. parsear respuesta; construir DeviceProfile; si no responde en 3 intentos → clasificar como
       'serie genérica' y ofrecer sólo lectura cruda
 6. caso límite: dispositivo que emite continuamente sin ser interrogado (loggers) → detectar tráfico
       espontáneo y saltar directo a modo lectura
```

**A4-3 — Backpressure y aislamiento de fallos.**
```
 1. límite por dispositivo: 2 MiB/s de entrada y 5 000 muestras/s
 2. al superarlo durante 3 s: emitir provider.degraded{kind:"device_flood"}, reducir tasa de sondeo
       a la mitad y activar submuestreo por decimación (conservando mín/máx por ventana para no perder picos)
 3. al superar el doble del límite: cerrar el canal de datos, mantener el de control, emitir device.detached
       lógico con motivo 'flood_protection'; el resto del sistema no se ve afectado
 4. cada dispositivo corre en su propia tarea asyncio con supervisión; una excepción no propaga al núcleo
 5. desconexión en caliente (por modo):
       transferencia → abortar, marcar artefacto parcial en cuarentena, hash de lo transferido
       captura      → cerrar decodificador, conservar fotogramas ya enviados, marcar sesión incompleta
       flasheo      → NO se aborta lógicamente: se marca integrity=UNKNOWN y se dispara la rutina de
                      rescate del §9.D en cuanto el dispositivo reaparezca
       impresión    → la impresora sigue imprimiendo sin nosotros: al reconectar, M114/M105 para
                      recuperar estado y decidir entre reanudar el streaming o abortar con M112
```

**Puerta de privacidad.** Por defecto: los flujos de pantalla del teléfono **sólo** se analizan con el VLM local; el envío a cualquier proveedor remoto requiere consentimiento explícito por sesión, con diálogo que enumera qué se enviaría y a quién, y caduca al cerrar la sesión (no hay "recordar"). Se persisten: los fotogramas efectivamente enviados al modelo (para procedencia) y sus hashes; **no** se persiste el flujo completo salvo que el usuario active la grabación. La GUI muestra un indicador rojo permanente y un contador de fotogramas mientras haya captura activa, y el evento `capability.requested{input.capture}` queda en la auditoría.

### 4.6 Integración con el debate popperiano

Afirmaciones: identificación tentativa de dispositivo desconocido ("este dispositivo es una controladora Marlin sobre CH340"), interpretación de una pantalla capturada ("el diálogo pide confirmar la depuración USB"), y diagnóstico de telemetría ("la caída de tensión coincide con el arranque del motor"). Evidencia admisible: descriptores USB leídos, respuesta a un comando de identidad, muestras con marca temporal monotónica, fotogramas hasheados. Refutación más potente: **la interrogación directa** — B exige enviar el comando de identidad y comparar la respuesta con la afirmación; para telemetría, exigir una segunda medición con instrumento independiente (Área 9.E). Invocación: antes de cualquier acción R2+ sobre el dispositivo (nunca antes de una lectura).

### 4.7 Costos, latencia y recursos

Sin tokens salvo cuando se invoca el VLM: 12 fotogramas/min × ≈ 1 100 tokens de entrada = 13 200 tokens/min como techo en Perfil A; se declara en el presupuesto de la sesión y se corta al alcanzarlo. CPU: decodificación H.264 720p a 15 fps ≈ 12 % de un núcleo con PyAV; SSIM en 320×180 ≈ 0,8 ms/fotograma. RAM: 60 MB por sesión de vídeo, 4 MB por dispositivo serie. Disco: Parquet de telemetría ≈ 9 bytes/muestra comprimido. **Salto del debate:** enumeración, lectura de descriptores y lectura de ficheros son R0 y no se debaten. **Caché:** perfiles de dispositivo por `VID:PID:bcdDevice:serial_hash` (invalidación manual o por cambio de firmware detectado); fotogramas y sus juicios por `sha256(frame)+modelo+prompt`.

### 4.8 Calidad y pruebas

| Caso | Criterio de éxito |
|---|---|
| Camino feliz: teléfono Android | `adb devices` en estado `device` ≤ 5 s tras conectar; `pull` de 100 MB con hash correcto |
| Hotplug | 50 ciclos conectar/desconectar: 50 `device.attached` y 50 `device.detached`, 0 duplicados, 0 perdidos |
| Dispositivo desconocido | Descriptores leídos y perfil tentativo emitido sin enviar comandos de clase; 0 escrituras |
| Muestreador adaptativo | En un vídeo con 6 cambios de escena en 2 min: ≥ 6 fotogramas enviados y ≤ 24 en total; latencia p95 ≤ 4,0 s |
| Inundación del bus | Dispositivo que emite 10 MiB/s: el sistema sigue respondiendo (GUI ≥ 30 fps) y aísla el canal en ≤ 3 s |
| Desconexión en caliente durante transferencia | Artefacto parcial en cuarentena con hash; 0 artefactos corruptos aceptados |
| Consenso entre agentes | Identificación de controladora: A y B coinciden tras M115; C otorga ≥ 80 |
| Desacuerdo total | Dispositivo con VID clonado: A dice Arduino, B demuestra por M115 que es una impresora; C resuelve `falsified` y el perfil cambia |
| Privacidad | Con consentimiento no otorgado: 0 bytes de fotograma salen hacia un proveedor remoto (verificado por captura de tráfico local) |

### 4.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta | Estado |
|---|---|---|---|---|
| Permisos insuficientes (Linux) | `LIBUSB_ERROR_ACCESS` | Sin acceso | Instrucción exacta: instalar reglas udev y añadir al grupo; enlace en la GUI | Bloqueado, explicado |
| Driver ausente (Windows) | `LIBUSB_ERROR_NOT_SUPPORTED` | Sin acceso | Instrucción Zadig 2.9 con el VID/PID concreto | Bloqueado, explicado |
| ADB no autorizado | estado `unauthorized` | Sin shell | Espera activa + instrucción en pantalla; reintento cada 3 s durante 120 s | Degradado |
| scrcpy incompatible con la versión de Android | error al lanzar el servidor | Sin vídeo | Degradar a capturas periódicas `adb exec-out screencap -p` (1 cada 3 s) | Degradado, funcional |
| Fallo parcial: vídeo llega pero decodificador se desincroniza | PTS no monótono o fotogramas verdes | Análisis erróneo | Reiniciar decodificador, descartar GOP, marcar `frames_lost` | Consistente |
| Cable suelto | `LIBUSB_ERROR_NO_DEVICE` | Sesión rota | Rutina de §A4-3 según modo | Según modo |
| Sin red | — | Ninguno | Todo local | Operativo |

### 4.10 Riesgos y mitigaciones

Brickear un dispositivo por enviar comandos a un perfil equivocado (baja/crítico → nunca se envían comandos de clase a dispositivos no identificados; escritura sólo en R2+ con volcado previo). Fuga de pantalla del usuario a un tercero (baja/alto → puerta de privacidad por sesión, VLM local por defecto). Saturación del bus USB compartido (media/medio → límites por dispositivo y aislamiento). Dependencia de la versión de scrcpy (alta/medio → binario propio versionado en `tools/`, prueba de compatibilidad al arrancar la sesión). Falsa identificación por VID/PID clonado (alta/medio → identificación por interrogación de firmware, no por tabla). Consolas con firmware de fábrica que prometen más de lo posible (alta/bajo → tabla de honestidad §4.4 mostrada en la GUI antes de intentar nada).

### 4.11 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA** (software): `libusb-1.0`, `pyusb`/`libusb1`, `pyserial`, `pyudev` (Linux), `PyAV` 12.x, `platform-tools` (adb/fastboot), `scrcpy` 2.x, `libmtp`, OpenCV. **🟡 REQUIERE-PRERREQUISITO**: en Windows, controlador WinUSB/libusbK vía Zadig 2.9 para acceso genérico; en Linux, pertenecer a `plugdev`/`dialout`; teléfono Android con depuración USB activada; para PSP/DS/Vita, el dispositivo físico y, para las funciones avanzadas, firmware personalizado instalado por el usuario bajo su responsabilidad. **🔴 BLOQUEADO-SIN-HARDWARE**: la validación de cada perfil de consola exige la consola (PSP ≈ 40–70 USD, DS ≈ 40–80 USD, PS Vita ≈ 90–150 USD en mercado de segunda mano; ninguno es necesario para construir el resto del sistema).

### 4.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (enumeración + hotplug + serie + telemetría) → v1 (ADB, MSC, MTP, perfiles de consola) → completo (scrcpy con muestreador adaptativo, UVC de Vita, privacidad, backpressure).

- **P4.a Enumeración.** P4.a.1 HAL USB en ambos SO — **PV-4.a.1**: la lista de dispositivos coincide con `lsusb`/`pnputil` al 100 % en 10 ejecuciones. P4.a.2 hotplug — **PV-4.a.2**: 50 ciclos sin eventos perdidos ni duplicados. P4.a.3 reglas udev — **PV-4.a.3**: tras instalarlas, acceso sin root a un CH340 verificado por apertura del puerto.
- **P4.b Serie y telemetría.** P4.b.1 handshake A4-2 — **PV-4.b.1**: detección de baudios correcta en 20/20 con 3 dispositivos. P4.b.2 búfer y pérdidas — **PV-4.b.2**: 2 000 muestras/s durante 10 min con 0 huecos no reportados. P4.b.3 persistencia — **PV-4.b.3**: consulta DuckDB de agregación por segundo ≤ 300 ms sobre 1,2 M de muestras.
- **P4.c Android.** P4.c.1 servidor ADB propio — **PV-4.c.1**: no interfiere con un `adb` del sistema en ejecución (comprobado por PID y puerto). P4.c.2 pull/push — **PV-4.c.2**: 1 GB transferido con hash idéntico. P4.c.3 control remoto — **PV-4.c.3**: abrir una URL y confirmar por fotograma que la página cargó, 10/10.
- **P4.d Vídeo.** P4.d.1 flujo H.264 por socket — **PV-4.d.1**: 60 s sin errores de decodificación y PTS monótono. P4.d.2 muestreador — **PV-4.d.2**: criterios de §4.8 cumplidos. P4.d.3 privacidad — **PV-4.d.3**: 0 bytes salientes sin consentimiento, verificado con captura de tráfico.
- **P4.e Consolas.** P4.e.1 perfiles MSC/MTP — **PV-4.e.1**: montaje y listado correcto en el hardware disponible; si no se posee, la PV queda marcada 🔴 y bloquea sólo esa fila. P4.e.2 UVC de Vita — **PV-4.e.2**: fotogramas a ≥ 10 fps por V4L2/MSMF.

Métricas de salida: 0 eventos de hotplug perdidos en 50 ciclos, latencia de vídeo p95 ≤ 4,0 s, 2 000 muestras/s sostenidas sin pérdida, y 100 % de dispositivos desconocidos identificados sin escritura.

---

## ÁREA 5 — Ingeniería inversa y síntesis de software

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA** para todo el análisis, la decompilación, la comparación de arquitecturas y la síntesis; **🟡 REQUIERE-PRERREQUISITO** para las pruebas diferenciales contra hardware real (exige poseer la consola y, en su caso, firmware personalizado instalado por el usuario).

### 5.1 Propósito y alcance

Es el área que el usuario pone en el centro: **analizar emuladores decompilados de PSP, Nintendo DS y PS Vita, entender cómo se modifica un emulador de una consola para adaptarlo a otra, y hacerlo por análisis y comparación sistemática, no por intuición.** Para eso hace falta, en este orden: una infraestructura de análisis automatizada, un pipeline que convierta el C ilegible de Ghidra en algo comprensible y falsable, una matriz de arquitecturas que sea el activo comparativo central, una taxonomía de portabilidad, un libro mayor de adaptación módulo a módulo, y un método de refutación empírico (pruebas diferenciales).

*Nota de estructura:* esta área usa trece subsecciones en lugar de doce porque la subsección obligatoria «Algoritmos» se despliega en dos (§5.5, matriz de arquitecturas, clasificación de capas, libro mayor, HLE/LLE, JIT y pruebas diferenciales; y §5.6, síntesis y clean room) por su peso en el encargo. Las doce subsecciones obligatorias están todas presentes y en orden: 5.1 propósito, 5.2 arquitectura, 5.3 contratos, 5.4 implementación, 5.5+5.6 algoritmos, 5.7 debate, 5.8 costes, 5.9 calidad, 5.10 fallos, 5.11 riesgos, 5.12 prerrequisitos, 5.13 hoja de ruta.

Queda fuera: la ejecución de acciones sobre el sistema (Área 8), el acceso físico al dispositivo (Área 4, que le entrega los binarios), y la redistribución de cualquier material propietario (prohibida por CTL-1).

**Consume:** Área 4 (dispositivos montados y dumps), Área 0 (cola de trabajos, CAS, procedencia), Área 3 (refutación), Área 7 (prompt de lectura de C decompilado). **Alimenta:** Área 3 (afirmaciones sobre funciones y sobre portabilidad), Área 8 (compilar/ejecutar/probar), Área 11 (invención de software), Área 12 (C01, C03, C16, C17).

### 5.2 Arquitectura

```
 dispositivo (Área 4) │ fichero local │ repositorio de código de emulador
        │ bytes+sha256 │              │ árbol de fuentes
        ▼              ▼              ▼
 ┌──────────────────────────┐   ┌───────────────────────────────────┐
 │ TRIAJE (magic, entropía, │   │ ANALIZADOR DE CÓDIGO FUENTE       │
 │ binwalk/unblob, firmas)  │   │ (grafo de dependencias, clang/AST)│
 └────────┬─────────────────┘   └──────────────┬────────────────────┘
   interés│ score                              │ módulos + aristas
          ▼                                    ▼
 ┌────────────────────────┐          ┌──────────────────────────────┐
 │ COLA DE DECOMPILACIÓN  │          │ CLASIFICADOR DE CAPAS        │
 │ Ghidra headless (lotes,│          │ agnóstica/semi/específica    │
 │ checkpoint por función)│          └──────────────┬───────────────┘
 └────────┬───────────────┘                         │ etiqueta+confianza
   C crudo│ + listado + xrefs                       ▼
          ▼                            ┌────────────────────────────┐
 ┌────────────────────────────┐        │ MATRIZ DE ARQUITECTURAS    │
 │ REFINAMIENTO ASISTIDO IA   │◄───────│ (PSP / DS / Vita) §5.5     │
 │ renombrado·tipos·FSM·notas │        └──────────────┬─────────────┘
 └────────┬───────────────────┘                       ▼
          │ hipótesis = AFIRMACIÓN falsable  ┌──────────────────────────┐
          ▼                                  │ LIBRO MAYOR DE ADAPTACIÓN│
 ┌───────────────────────────────────┐       │ (adaptation ledger)      │
 │ PRUEBA DIFERENCIAL (§5.5)         │       └──────────────┬───────────┘
 │ referencia vs. construido         │                      ▼
 │  ⚠ PRIMER PUNTO DE DIVERGENCIA    │            ┌────────────────────┐
 │    ⇒ refutación automática de B   │            │ SÍNTESIS: spec →   │
 └───────────────┬───────────────────┘            │ clean room → build │
                 ▼                                └────────────────────┘
        Área 3 (debate) ──► Área 8 (compilar/ejecutar) ──► artefacto verificado
```

### 5.3 Contratos e interfaces

```python
def triage_tree(root: Path) -> list[TriageItem]: ...
def submit_decompile(binary: BinaryRef, opts: GhidraOpts) -> JobId: ...
def refine_function(fn: DecompiledFunction, ctx: BinaryContext) -> RefinementProposal: ...
def build_arch_matrix(consoles: list[str]) -> ArchMatrix: ...
def classify_modules(src_root: Path) -> list[ModuleClassification]: ...
def build_adaptation_ledger(src: EmulatorRef, target: ConsoleId) -> AdaptationLedger: ...
def run_differential(ref: RunnerRef, cand: RunnerRef, prog: TestProgram) -> DivergenceReport: ...
def emit_intermediate_spec(binary: BinaryRef, scope: SpecScope) -> IntermediateSpec: ...
def synthesize_from_spec(spec: IntermediateSpec, target: BuildTarget) -> SynthesisJob: ...
```

Esquema de la propuesta de refinamiento (cada hipótesis es una afirmación falsable):

```json
{
  "function": {"addr": "0x00801a40", "binary_sha256": "…", "arch": "MIPS:LE:32:default"},
  "hypotheses": [
    {"id":"h1","kind":"identity","statement":"FUN_00801a40 es memcpy con soporte de solape (memmove)",
     "falsifier":"si al ejecutar con src<dst solapados el resultado difiere de memmove, la hipótesis cae",
     "evidence":[{"kind":"static_analysis","locator":"0x801a58","value":"bucle con lw/sw y contador decreciente"}],
     "confidence":0.68},
    {"id":"h2","kind":"type","statement":"param_1 es char* de destino y param_2 char* de origen","…":"…"},
    {"id":"h3","kind":"rename","from":"uVar3","to":"remaining_bytes","…":"…"}
  ],
  "proposed_patch": {"renames":{"FUN_00801a40":"af_memmove"},"types":{"param_1":"char *"},
                     "comments":{"0x801a58":"bucle de copia descendente"}}
}
```

Esquema del libro mayor de adaptación:

```json
{
  "source_emulator": {"name":"<emulador de origen>","commit":"…","console":"PSP"},
  "target_console": "PSVita",
  "rows": [
    {"module":"core/HLE/sceKernelThread","layer":"console_specific",
     "verdict":"reescribir-de-cero",
     "rationale":"el modelo de hilos del firmware destino difiere en planificador y prioridades (ver matriz §5.5, fila 'SO/firmware')",
     "effort_pd": 22, "risk":"alto", "evidence_refs":["arch-matrix#os","src-graph#node-412"]}
  ],
  "totals": {"reutilizable-tal-cual": 41, "reutilizable-con-parametros": 18,
             "reescribir-con-la-misma-forma": 26, "reescribir-de-cero": 33, "no-aplica": 12,
             "effort_pd_total": 940}
}
```

Tablas: `binary`, `decompiled_function`, `refinement`, `arch_fact`, `module_classification`, `ledger_row`, `divergence`, `intermediate_spec`, `clean_room_ledger` (DDL en §T3). Eventos: `job.progress`, `artifact.created`, `action.proposed` (compilar/ejecutar), `debate.turn`.

### 5.4 Implementación: infraestructura local de análisis

*Decisión:* **Ghidra 11.x** en modo headless (`analyzeHeadless`) como analizador principal, con scripts propios en Python vía **PyGhidra** (y Jython 2.7 como ruta compatible para scripts heredados) — porque su decompilador multi-arquitectura cubre MIPS (PSP), ARM/Thumb (DS, Vita) y su modo headless es guionizable por lotes sin interfaz.
*Descartado:* IDA Pro — es de pago y el encargo exige coste cero real.

Línea de comandos exacta:

```bash
"$GHIDRA_HOME/support/analyzeHeadless" \
  "$PROJDIR/ghidra" MagiSystem \
  -import "$BIN" \
  -processor "MIPS:LE:32:default" \
  -scriptPath "$REPO/modules/re/ghidra_scripts" \
  -preScript MagiPreConfig.java "$OPTS_JSON" \
  -postScript MagiExportDecompiled.py "$OUTDIR" \
  -analysisTimeoutPerFile 7200 \
  -max-cpu 6 \
  -log "$OUTDIR/ghidra.log" -scriptlog "$OUTDIR/script.log" \
  -okToDelete -noanalysis=false
```

Formato de salida de `MagiExportDecompiled.py`: un fichero por función en `$OUTDIR/functions/<addr>.c`, más `index.jsonl` con `{addr, name, size, cc, params, callers[], callees[], stack_frame, decompile_ms, c_sha256}`, más `strings.jsonl`, `xrefs.jsonl` y `symbols.jsonl`. La base de proyecto Ghidra es compartida por binario (`-import` incremental) para no reanalizar.

Herramientas complementarias y su papel exacto:

| Herramienta | Versión | Uso concreto en el sistema |
|---|---|---|
| Rizin | 0.7.x (con `rz-pipe` Python) | Análisis rápido interactivo: `izz` (cadenas), `afl` (funciones), `agf` (grafo de flujo), y **`rz-diff`** para diffing binario entre versiones — el trabajo barato que no justifica arrancar Ghidra |
| Radare2 | 5.9.x (`r2pipe`) | Ruta alternativa equivalente cuando un script de la comunidad sólo existe para r2; `radiff2 -C` para diffing por función |
| Capstone | 5.0.x | Desensamblado embebido dentro del núcleo, sin lanzar procesos (inspección puntual, decodificación de una instrucción en una traza) |
| LIEF | 0.14.x | Parseo y manipulación de ELF/PE/Mach-O: secciones, símbolos, reubicaciones, y construcción de binarios de prueba |
| angr | 9.2.x | Ejecución simbólica para casos concretos: recuperar la condición de un `switch` no resuelto, o probar alcanzabilidad de una rama |
| Frida | 16.x | Instrumentación dinámica cuando el objetivo se puede ejecutar en el anfitrión o en el dispositivo del usuario |
| QEMU user-mode | 9.0.x | Ejecutar binarios de otra arquitectura (`qemu-mipsel`, `qemu-arm`) para pruebas diferenciales de funciones puras |
| Unicorn | 2.0.x | Emular fragmentos aislados con estado de registros controlado — la base del oráculo de función (A5-3) |
| binwalk | 2.3.x | Extracción de firmware por firmas |
| unblob | 24.x | Extracción recursiva más robusta que binwalk para contenedores anidados |

**Cola de trabajos.** La decompilación de un binario grande tarda horas: se modela como trabajo por lotes con unidades reanudables por **función** (`unit_id = f"{binary_sha256}:{addr}"`). Punto de control tras cada 50 funciones exportadas (escritura atómica de `index.jsonl` por append + `fsync`). Reanudación: al reiniciar, se leen las direcciones ya presentes en `index.jsonl` y se pasan a Ghidra por `-preScript` como lista de exclusión. Prioridad `BATCH`; ocupa el semáforo `TOOLCHAIN_HEAVY`.

**Pipeline de escaneo desde dispositivos USB.**
```
1. recorrer el sistema de ficheros montado (Área 4) con límite de profundidad y lista de exclusión
2. por fichero: magic bytes (LIEF/`file`), entropía de Shannon por bloques de 4 KiB
3. clasificar: ejecutable (ELF/PE/PRX/SELF/NRO/…), archivo contenedor, recurso, dato
4. detectar empaquetado/cifrado: entropía media > 7,4 y ausencia de cadenas legibles ⇒ candidato
5. extracción de firmware: unblob primero; binwalk como segunda pasada sobre lo no reconocido
6. TRIAJE por score de interés:
     score = 0,30·(es_ejecutable) + 0,20·(tiene_símbolos) + 0,15·(cadenas_interesantes/KB)
           + 0,15·(referencias_a_syscalls) + 0,10·(tamaño_normalizado) + 0,10·(es_único_por_hash)
     encolar a decompilación los de score ≥ 0,55, hasta el presupuesto declarado del trabajo
7. TODO artefacto derivado queda bajo CTL-1 y CTL-2 (§I.4)
```

**Comprensión asistida por IA del decompilado.** El C de Ghidra es ilegible por diseño (`FUN_`, `DAT_`, `undefined4`, `uVar`). Pipeline de refinamiento en cinco pasadas, cada una con su verificación:
1. **Identificación de librería estándar** — firmas propias tipo FLIRT: se compilan las libc/newlib/SDK relevantes disponibles y se genera un catálogo de hashes de función normalizados (hash del CFG + constantes + tamaño); coincidencia ⇒ nombre y firma conocidos, sin gastar tokens. Verificación: la coincidencia se confirma ejecutando el oráculo de función (A5-3).
2. **Recuperación de tipos** — propagación desde llamadas identificadas y desde accesos a memoria (patrón de `lw/sw` con desplazamiento constante ⇒ campo de estructura); el modelo propone la `struct`, y la verificación es que el decompilador **reanalice** con ese tipo aplicado y el C resultante reduzca su número de `undefined` y de casts (métrica objetiva: `readability_score`).
3. **Renombrado semántico** — el modelo propone nombres; se aplican en Ghidra vía script y se recalcula `readability_score = 1 − (undefined_count + cast_count + FUN_refs)/tokens`. Sólo se conserva si mejora.
4. **Reconstrucción de máquina de estados** — para funciones con `switch` sobre un campo persistente: extracción del grafo de estados (`networkx` 3.3) con nodos = valores del selector y aristas = transiciones observadas estáticamente; se emite un `.dot` y una hipótesis falsable.
5. **Anotación** — comentarios en el listado con la procedencia (`model_id`, `prompt_hash`, `confidence`).

Cada hipótesis del modelo sobre una función es una **afirmación falsable** que pasa al Área 3, y su refutación natural es una **prueba diferencial** (A5-3).

### 5.5 Algoritmos — núcleo del encargo: análisis, adaptación y portado de emuladores

#### 5.5.1 Matriz de arquitecturas de consola (el activo central)

| Rasgo | PSP (PlayStation Portable) | Nintendo DS | PlayStation Vita |
|---|---|---|---|
| CPU principal | "Allegrex", núcleo MIPS32 de linaje R4000, 32 bits, little-endian, reloj escalable típicamente 222–333 MHz | ARM946E-S (ARMv5TE) a ≈ 67 MHz | ARM Cortex-A9 MPCore de cuatro núcleos (ARMv7-A), hasta ≈ 444 MHz |
| CPU secundaria | Segundo núcleo Allegrex dedicado a medios ("Media Engine") | ARM7TDMI (ARMv4T) a ≈ 33 MHz, gestiona audio, entrada y compatibilidad GBA | Núcleo(s) de sistema y seguridad separados del área de aplicación |
| Coprocesadores | VFPU (unidad vectorial de coma flotante, registros matriciales 4×4), FPU escalar (COP1), COP0 de sistema | Sin FPU en ninguno de los dos núcleos: aritmética de punto fijo; unidad de división y raíz cuadrada por hardware; DMA | NEON (SIMD), VFPv3, MMU con TrustZone |
| Palabra/endianness | 32 bits, LE | 32 bits, LE | 32 bits, LE |
| Memoria principal | 32 MB (modelos 1000) / 64 MB (modelos posteriores), más 2 MB de eDRAM asociada al vídeo, y memoria rápida interna del núcleo (scratchpad) | 4 MB de RAM principal; WRAM compartida y bancos de VRAM conmutables (≈ 656 KB en total para vídeo) | 512 MB de RAM de sistema y 128 MB de memoria de vídeo |
| MMU / MPU | TLB del linaje MIPS gestionada por software (COP0), segmentos kuseg/kseg0/kseg1 | **MPU** del ARM946E-S (regiones protegidas, sin traducción de páginas); el ARM7 sin protección | **MMU** ARMv7 completa con paginación, dominios y TrustZone |
| GPU y modelo de comandos | "Graphics Engine" (GE): listas de display con paquetes de comandos ejecutadas por DMA; pipeline de función fija con etapas configurables | Dos motores 2D independientes (A y B) con capas de fondo y sprites, más un motor 3D de función fija con FIFO de comandos de geometría y rasterizado por línea | PowerVR SGX543MP4+ (arquitectura de renderizado por teselas, diferido), API gráfica del sistema **GXM** con shaders programables |
| Modelo de shading | Sin shaders programables (función fija) | Sin shaders (función fija) | Shaders programables compilados a un formato específico del proveedor |
| Audio | Hardware de reproducción con canales dedicados y decodificación asistida en el Media Engine (ATRAC3/ATRAC3+) | 16 canales de audio gestionados por el ARM7 (PCM, ADPCM, ruido/onda) | Puertos de audio del sistema con mezcla por software y códecs del firmware |
| Temporizadores | Contador de ciclos del COP0 y temporizadores del sistema | Cuatro temporizadores por CPU, con encadenado; contador de línea de vídeo (V-count) como base temporal | Temporizadores del sistema operativo y contador global ARM |
| Interrupciones | Controlador de interrupciones del sistema, con IRQ por periférico y por DMA | IRQ por periférico con registros IE/IF/IME por CPU; sincronización entre CPU por FIFO e IPC | GIC (controlador genérico de interrupciones ARM) |
| Medio de almacenamiento | UMD (disco óptico) y Memory Stick Pro Duo; ejecutables `.PBP`/`PRX`/`SELF` | Cartucho de tarjeta DS (ROM con guardado por EEPROM/FLASH), formato `.nds` con cabecera y dos binarios ARM9/ARM7 | Tarjeta de juego propietaria y descarga digital; paquetes de aplicación firmados |
| Firmware / SO | Sistema operativo propietario basado en módulos PRX, con llamadas al sistema `sce*` | Sin SO: BIOS mínima por CPU y "firmware" con parámetros de usuario; el juego es dueño de la máquina | Sistema operativo propietario multitarea, con módulos, permisos y aislamiento |
| Superficie de emulación crítica | VFPU y GE (listas de display) | Sincronía exacta entre ARM9/ARM7 y el temporizado por línea de vídeo | GXM (traducción de shaders) y el SO multitarea |
| Emuladores de referencia libres | PPSSPP | melonDS, DeSmuME | Vita3K |

**Cómo se construye y se mantiene esta matriz dentro del sistema:** cada celda es una fila de `arch_fact(console, dimension, value, source_kind, source_ref, confidence, verified_by)`. `source_kind ∈ {documentacion_publica, codigo_emulador_libre, medicion_en_hardware, decompilacion}`. Ninguna celda se acepta con `source_kind = modelo`: la matriz no se rellena de memoria, se rellena con referencia. Las celdas con `confidence < 0,8` se marcan en la GUI y son candidatas prioritarias a verificación empírica (test ROM en hardware del usuario o lectura del código del emulador de referencia).

#### 5.5.2 Descomposición de un emulador en capas de portabilidad

| Capa | Contenido | Qué ocurre al cambiar de consola |
|---|---|---|
| **Agnóstica de consola** | Frontend y GUI, gestión de entrada (mapeo de mandos), salida de audio (backend del anfitrión), configuración, guardado y carga de estado (serialización), rebobinado, red/netplay, shaders de post-proceso, capturas, traducción de la interfaz | Se reutiliza tal cual salvo la **forma** del estado guardado, que es específica |
| **Semi-agnóstica** | Recompilador dinámico (infraestructura de bloques, caché, invalidación, enlace de bloques), planificador de ciclos y cola de eventos, abstracción de GPU del anfitrión (contexto, texturas, búferes), abstracción de sistema de ficheros virtual, depurador | Se reutiliza la **arquitectura** y se reescribe el backend concreto (frontend de ISA, decodificador, generador de código) |
| **Específica de consola** | Núcleo de CPU (semántica de instrucciones), MMU/MPU y mapa de memoria, HLE de llamadas al sistema del firmware, GPU específica y su lenguaje de comandos, formatos de medios y de ejecutables, criptografía y verificación de firmas del firmware | Se reescribe casi por completo |

**Algoritmo de clasificación automática de módulos (A5-1).** *Nota de versión:* desde la incorporación del Área 13, este algoritmo queda como **camino de reserva**; el camino principal es **A13-2**, que sustituye las heurísticas de nombres por acoplamiento estructural medido sobre el grafo de MAGI-MEM y eleva la exactitud exigida de 0,85 a 0,92. A5-1 se conserva íntegro y se usa cuando el binario de MAGI-MEM no está disponible.

```
 1. construir el grafo de dependencias del código fuente:
    1.1 C/C++: `clang -MMD` para inclusiones + índice de símbolos con `clangd --index` o `ctags`/`cscope`
    1.2 nodo = fichero de traducción; arista = inclusión o referencia a símbolo definido en otro nodo
 2. calcular por nodo: grado de entrada/salida, centralidad de intermediación (networkx), y el conjunto
       de "términos ancla" que aparecen en nombres de símbolos y rutas
 3. heurística de nombres (pesos iniciales, ajustables por proyecto):
       específica: {sce, kernel, hle, bios, syscall, gpu_<consola>, gxm, ge_, dma, mpu, cartridge, umd}
       semi:       {jit, recompiler, ir, block, dispatcher, scheduler, timing, backend, glsl, vulkan}
       agnóstica:  {ui, frontend, config, input, audio_out, savestate, netplay, i18n, screenshot}
 4. propagación por el grafo: un nodo hereda la etiqueta mayoritaria ponderada de sus vecinos si su
       evidencia propia es débil (etiquetado por consenso, 3 iteraciones tipo label propagation)
 5. juicio del modelo sobre los nodos ambiguos (confianza < 0,7), con el contenido del fichero y sus
       vecinos como contexto; salida GBNF {module, layer, confidence, rationale}
 6. TODA etiqueta con confianza < 0,85 pasa por el Área 3 antes de entrar en el libro mayor
 7. verificación objetiva de la etiqueta 'agnóstica': el módulo debe compilar aislado sustituyendo la
       capa específica por una implementación vacía (stub). Si no compila, la etiqueta era falsa.
       Esta es la refutación mecánica más barata y se ejecuta automáticamente.
 8. complejidad O(V+E) por iteración; para 3 000 ficheros, < 20 s
```

#### 5.5.3 Libro mayor de adaptación (adaptation ledger)

Dado un emulador origen (por ejemplo uno de PSP) y una consola destino (por ejemplo PS Vita), se produce una tabla módulo a módulo con cinco veredictos posibles. Regla de asignación, derivada de la matriz §5.5.1:

| Veredicto | Condición de asignación |
|---|---|
| `reutilizable-tal-cual` | Capa agnóstica **y** no depende de ninguna dimensión de la matriz que difiera entre origen y destino |
| `reutilizable-con-parámetros` | Capa agnóstica o semi-agnóstica cuya única dependencia divergente es un valor configurable (resolución, tasa de refresco, tamaño de memoria, número de mandos) |
| `reescribir-con-la-misma-forma` | Capa semi-agnóstica cuya interfaz se conserva pero cuya implementación depende de una dimensión divergente (ISA, modelo de GPU, modelo de memoria). Se conserva el diseño, cambia el cuerpo |
| `reescribir-de-cero` | Capa específica sobre una dimensión que difiere estructuralmente (p. ej. MPU sin traducción → MMU con paginación; función fija → shaders programables; sin SO → SO multitarea) |
| `no-aplica` | El destino carece del subsistema (p. ej. no hay VFPU fuera de PSP; no hay pantalla dual fuera de DS) |

Estimación de esfuerzo: `effort_pd = base(veredicto) × tamaño_normalizado × factor_riesgo`, con `base` = {tal-cual: 0,2; con-parámetros: 1; misma-forma: 4; de-cero: 12; no-aplica: 0} días-persona por cada 1 000 líneas efectivas, `factor_riesgo ∈ [1,0; 2,5]` según la confianza de la celda de la matriz implicada. La estimación es una **afirmación falsable**: se contrasta contra el esfuerzo real registrado en los primeros módulos y se recalibra (el sistema guarda `effort_actual_pd` y ajusta `base` por regresión).

#### 5.5.4 HLE frente a LLE

| Criterio | HLE (interceptar llamadas del firmware) | LLE (ejecutar el firmware real) |
|---|---|---|
| Precisión | Depende de la fidelidad de la reimplementación; falla en usos no documentados | Alta por construcción |
| Rendimiento | Mucho mayor: una llamada nativa sustituye a miles de instrucciones emuladas | Menor: hay que emular también el SO |
| Prerrequisitos legales | Ninguno: se reimplementa el comportamiento observado | Requiere el firmware **del propio dispositivo del usuario**, que nunca se redistribuye (CTL-1) |
| Coste de desarrollo | Alto y continuo (una función por llamada) | Alto al principio (fidelidad de hardware), luego se amortiza |

**Regla de decisión por subsistema, implementada en el sistema:** se elige LLE cuando (a) el subsistema es pequeño y bien acotado, (b) su semántica es difícil de inferir, y (c) el usuario dispone del firmware volcado de su propio equipo; se elige HLE cuando el subsistema es amplio, está documentado por la comunidad y su coste de emulación de bajo nivel domina el presupuesto de rendimiento. El sistema calcula un índice `lle_score = 0,4·(1 − cobertura_documental) + 0,3·(1 − tamaño_normalizado) + 0,3·(firmware_disponible)` y propone LLE si `lle_score ≥ 0,6`; la propuesta pasa por el Área 3 con la evidencia de ambos lados.

#### 5.5.5 Recompilación dinámica

Estructura de un JIT portable en tres etapas: **frontend de ISA** (decodifica instrucciones a una representación intermedia propia), **optimizador de bloque** (propagación de constantes, eliminación de código muerto, fusión de banderas), **backend de código nativo** (emite x86-64). Lo que **se comparte** entre un JIT MIPS→x86-64 y uno ARM→x86-64: el gestor de caché de bloques y su invalidación por escritura en memoria de código, el enlace de bloques (block linking) y el despachador, la asignación de registros, la representación intermedia y sus optimizaciones, el manejo de excepciones y de puntos de interrupción, y la instrumentación de trazas. Lo que **no se comparte**: el decodificador y la semántica de cada instrucción, el modelo de banderas (MIPS no tiene registro de banderas; ARM sí, y su actualización condicional es una fuente sistemática de errores), la ejecución condicional (ARM clásico), el manejo de coprocesadores (VFPU del PSP frente a NEON/VFP de ARM), y las reglas de sincronía de memoria. Consecuencia práctica para el libro mayor: el JIT es `reescribir-con-la-misma-forma`, con el gestor de caché y el despachador como `reutilizable-tal-cual`.

#### 5.5.6 Pruebas diferenciales como método de refutación (lo que convierte esto en ciencia)

```
 1. seleccionar programa de prueba T: (a) homebrew de conformidad ("test ROMs") de dominio público,
       (b) programa propio compilado con el SDK libre correspondiente, (c) fragmento sintético generado
 2. ejecutar T en el emulador de REFERENCIA (PPSSPP para PSP; melonDS o DeSmuME para DS; Vita3K para
       Vita) con la instrumentación de traza activada, y en el emulador CONSTRUIDO
 3. formato de traza (JSONL comprimido con zstd, un registro por evento observable):
       {"i": 91823, "pc": "0x08804a1c", "op": "addiu", "regs_delta": {"t0": "0x0000ff02"},
        "mem_w": [{"addr":"0x09000010","size":4,"val":"0xdeadbeef"}],
        "gpu_cmd": null, "frame_hash": null, "cycles": 918230}
       y, en los límites de fotograma: {"i":…, "frame_hash":"sha256 de la superficie RGBA8888"}
 4. la comparación es sobre eventos observables, no sobre implementación: registros arquitectónicos,
       escrituras a memoria visibles, comandos de GPU emitidos y hash de fotograma
 5. PRIMER PUNTO DE DIVERGENCIA: índice mínimo i* donde los registros difieren. Se extrae la ventana
       [i*−64, i*+8] de ambas trazas, el desensamblado de esa ventana y el estado completo en i*−1
 6. ese paquete se convierte AUTOMÁTICAMENTE en una refutación del BALTHASAR, de tipo 'empirica', con
       mechanism = "divergencia en i* tras <instrucción>" y reproduction_steps = comandos exactos
 7. tolerancias declaradas: los hashes de fotograma admiten una comparación perceptual (SSIM ≥ 0,995)
       cuando el filtrado de texturas del anfitrión introduce diferencias legítimas; los registros NO
       admiten tolerancia: la igualdad es exacta
 8. caso límite: la referencia también está mal. Por eso el oráculo primario es el hardware real cuando
       el usuario lo tiene (Área 4), y la referencia es un oráculo secundario declarado como tal
 9. complejidad: comparación O(n) con dos punteros; el coste real es generar la traza (5–20× más lento)
```

**Suites de conformidad como oráculo objetivo.** Se mantiene un catálogo `profiles/conformance/<consola>.yaml` con cada programa de prueba de dominio público, qué subsistema cubre (CPU aritmética, temporizadores, DMA, 2D, 3D, audio, entrada) y cuál es su salida esperada (texto en pantalla, hash de fotograma, o código de salida). **Puntuación de conformidad** = `Σ(peso_subsistema × pruebas_pasadas/total)` normalizada a 100, con pesos por defecto: CPU 30, memoria/MMU 15, temporizadores/IRQ 15, GPU 25, audio 10, entrada/medios 5. Esta cifra es el criterio de éxito numérico del área.

**A5-3 — Oráculo de función con Unicorn (refutación barata sin ejecutar el sistema completo).**
```
1. dada la hipótesis "FUN_X es memmove", generar 200 casos de prueba (tamaños 0..4096, solapes
      positivos, negativos y nulos, alineaciones 1/2/4/8, patrones de relleno)
2. montar en Unicorn: mapear la sección de código del binario, colocar entradas en memoria, fijar
      registros según la convención de llamada de la arquitectura, ejecutar hasta el retorno
3. comparar la memoria de salida con la de la implementación de referencia en el anfitrión
4. criterio: 200/200 idénticos ⇒ evidencia fuerte (tier 2); ≥ 1 divergencia ⇒ refutación empírica
      con el caso mínimo (reducción por bisección sobre el tamaño y el solape)
5. coste: < 2 s por función, frente a minutos de un debate; por eso se ejecuta ANTES de gastar tokens
```

### 5.6 Algoritmos (continuación) — Síntesis de software: clonar, portear, recrear

1. **Especificación intermedia** (`emit_intermediate_spec`): documento JSON+Markdown que describe **qué hace** el binario — interfaces, formatos de datos, máquinas de estado, invariantes, protocolos, tiempos — **sin incluir su código**. Se genera desde el análisis y se somete al debate; su criterio de aceptación es que un tercero pueda implementar desde ella sin ver el original.
2. **Aislamiento de procedencia (CTL-3)**: `analysis/` produce la especificación; `impl/` sólo ve la especificación. `clean_room_ledger` registra por sesión qué hashes vio cada espacio, y la capa de capacidades impide a un agente `impl` leer blobs `analysis-only`.
3. **Generación del nuevo código** a partir de la especificación, con el MELCHIOR, contra una batería de pruebas derivada de la propia especificación (cada invariante es un test).
4. **Sistema de construcción:** *Decisión:* CMake 3.28+ con generador Ninja 1.11 como estándar del proyecto — porque es el denominador común de las toolchains de C/C++ implicadas y soporta compilación cruzada por fichero de toolchain.
   *Descartado:* Meson — igualmente válido, pero CMake tiene mejor interoperación con los ficheros de toolchain de `arm-none-eabi` y con los SDK libres implicados.
   Compilación cruzada con ficheros `cmake/toolchains/{mipsel-linux.cmake, arm-none-eabi.cmake, aarch64-linux.cmake}`.
5. **Validación por equivalencia de comportamiento:** pruebas diferenciales (§5.5.6) más el oráculo de función (A5-3) más la suite de conformidad.

**Clientes de cloud gaming (caso nombrado por el encargo).** Alcance realista y sus límites, declarados sin adorno: se analiza el **protocolo observable** de un cliente que el usuario posee legítimamente — captura de tráfico local con permiso del propio usuario sobre su propia sesión, reconstrucción de la máquina de estados de sesión (descubrimiento, autenticación, negociación de códec y de latencia, control de entrada, keep-alive, reconexión, terminación), y documentación de los formatos de paquete observados. **Límites duros:** (a) no se elude DRM ni cifrado de transporte ni se extraen claves — el sistema rechaza por diseño cualquier tarea cuyo objetivo declarado sea eso (comprobación en `synthesize_from_spec` contra una lista de objetivos prohibidos, con `PolicyRefused(code="CTL-DRM")`); (b) no se redistribuye ningún binario ni recurso del cliente original (CTL-1); (c) un cliente reimplementado sólo es útil contra un servicio al que el usuario tenga acceso legítimo, y los términos de ese servicio pueden prohibir clientes no oficiales — el sistema lo advierte en el artefacto y marca `derivative_risk: high`.

**Prueba de que el resultado funciona (umbrales numerados).** Un artefacto de síntesis o de portado se declara válido si y sólo si: **(U1)** compila sin errores y con 0 advertencias de la clase `-Wall -Wextra` que estén en la lista de bloqueantes del proyecto; **(U2)** la puntuación de conformidad ≥ **85/100** para un portado declarado "jugable", y ≥ **95/100** para uno declarado "preciso"; **(U3)** la traza diferencial converge: 0 divergencias de registro en las 10 primeras pruebas de conformidad de CPU, y SSIM medio de fotograma ≥ 0,995 en las pruebas gráficas; **(U4)** el rendimiento está dentro del **130 %** del tiempo de la referencia en el mismo anfitrión (es decir, no más de 1,3× más lento) para el conjunto de pruebas de rendimiento declarado; **(U5)** 100 % de los invariantes de la especificación intermedia cubiertos por al menos un test.

### 5.7 Integración con el debate popperiano

Afirmaciones emitidas: identidad y semántica de cada función refinada, etiqueta de capa de cada módulo, cada fila del libro mayor, la decisión HLE/LLE por subsistema, y las cinco condiciones U1–U5. Evidencia admisible: salida de Ghidra con su versión, oráculo de función con Unicorn, traza diferencial, puntuación de conformidad, medición de rendimiento. Refutación más potente: **el primer punto de divergencia** de la prueba diferencial, que es automática, reproducible y no admite retórica; en su defecto, el caso mínimo del oráculo de función. Punto de invocación: (a) tras el refinamiento, antes de fijar nombres y tipos; (b) tras la clasificación de módulos con confianza < 0,85; (c) antes de cerrar cada fila del libro mayor; (d) antes de aceptar un artefacto sintetizado.

### 5.8 Costos, latencia y recursos

Ghidra headless: ≈ 6–20 min para un binario de 8 MB con símbolos en 6 hilos; hasta 6 h para firmware grande sin símbolos (por eso la cola con checkpoint). RAM de Ghidra: 4–8 GB con `-Xmx6G`; ocupa `TOOLCHAIN_HEAVY`, incompatible con VLM residente en Perfil B. Refinamiento por función: ≈ 3 400 tokens de entrada (C + contexto de llamadas) y 800 de salida; 1 000 funciones ⇒ 4,2 M de tokens, inviable en un solo lote: por eso el triaje limita a las funciones con score ≥ 0,55 y la identificación por firmas resuelve las de librería sin gastar tokens (reducción típica del 35–60 % del volumen). Traza diferencial: 5–20× más lenta que la ejecución normal; 60 s de juego ⇒ ≈ 4 GB de traza sin comprimir, ≈ 260 MB con zstd nivel 10; se conservan sólo las ventanas alrededor de las divergencias más el resumen.

**Salto del debate:** identificación por firma con coincidencia exacta, extracción de cadenas, y cualquier resultado del oráculo de función con 200/200 (evidencia tier 2 concluyente) no se debaten. **Caché:** análisis de Ghidra por `sha256(binario)+ghidra_version+script_hash+opts_hash`; refinamiento por `sha256(C_crudo)+model_hash+prompt_hash`; trazas por `sha256(binario)+programa_prueba+emulador+versión`. Invalidación por cambio de cualquier componente; las trazas se purgan por LRU con límite de 30 GB.

### 5.9 Calidad y pruebas

| Caso | Criterio de éxito |
|---|---|
| Camino feliz | Binario ELF MIPS con símbolos: 100 % de funciones exportadas, `index.jsonl` consistente, reanudación tras corte reprocesa ≤ 50 funciones |
| Binario que no compila (síntesis) | El error del compilador se clasifica y vuelve a B como refutación en ≤ 1 iteración en 20/20 casos |
| Identificación de librería | Sobre 300 funciones de libc conocidas: precisión ≥ 0,95, recall ≥ 0,85 |
| Oráculo de función | 50 hipótesis (25 correctas, 25 falsas): 100 % de las falsas refutadas con caso mínimo |
| Clasificación de capas | Sobre un emulador libre con etiquetado manual de 200 módulos: exactitud ≥ 0,85; la prueba de compilación aislada refuta ≥ 90 % de las etiquetas 'agnóstica' erróneas |
| Prueba diferencial | Divergencia sembrada artificialmente (un bit en el resultado de una instrucción): detectada en el índice exacto en 20/20 |
| Conformidad | El emulador construido alcanza ≥ 85/100 en su suite antes de declararse "jugable" |
| Consenso entre agentes | Hipótesis de función con oráculo 200/200: A y B coinciden, C otorga ≥ 85 |
| Desacuerdo total | Hipótesis con oráculo 199/200: B refuta con el caso mínimo, C emite `falsified` pese a la alta confianza de A |
| Controles legales | CTL-1: intento de empaquetar un dump de firmware ⇒ rechazo en 10/10; CTL-3: agente `impl` intenta leer el binario ⇒ denegado en 10/10 |

### 5.10 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta | Estado |
|---|---|---|---|---|
| Ghidra agota memoria | código de salida + log | Sin decompilación | Reintento con `-Xmx` mayor y `-analysisTimeoutPerFile` reducido; si falla, trocear por sección | Degradado |
| Decompilación de una función falla | excepción en el script | Hueco en el índice | Marcar `decompile_failed`, continuar con el resto, exponer el desensamblado crudo | Parcial, visible |
| Arquitectura mal detectada | tasa de instrucciones inválidas > 5 % | Análisis basura | Probar la lista de procesadores candidatos y elegir por menor tasa de inválidas | Recuperado |
| Traza gigantesca | tamaño > presupuesto | Disco lleno | Traza por ventanas con muestreo y activación completa sólo alrededor de la divergencia | Degradado |
| Fallo parcial (el peor): refinamiento renombra mal y el usuario lo cree | `readability_score` mejora pero el oráculo falla | Nombres engañosos | Todo renombrado sin verificación queda marcado `unverified` en la GUI y en el C exportado | Consistente |
| Emulador de referencia no disponible | binario ausente | Sin oráculo secundario | Degradar a oráculo por suite de conformidad y por hardware del usuario | Degradado |
| Sin red | — | No se descargan suites ni fuentes | Todo el análisis local intacto | Operativo |

### 5.11 Riesgos y mitigaciones

Contaminación de procedencia al reimplementar (media/crítico → CTL-3 con separación física y registro por sesión). Redistribución accidental de material propietario (media/crítico → CTL-1 en el empaquetador, con prueba dedicada). Confianza excesiva en el refinamiento del modelo (alta/alto → nada se fija sin oráculo; marca `unverified`). Explosión de coste de tokens (alta/medio → triaje, firmas y caché). Emulador de referencia con errores propios (media/medio → hardware real como oráculo primario cuando exista, y declaración explícita del oráculo usado en cada afirmación). Expectativa irreal de "convertir un emulador de PSP en uno de Vita cambiando parámetros" (alta/alto → el libro mayor cuantifica desde el principio cuántos módulos son `reescribir-de-cero`, que es la respuesta honesta y el principal valor del área). Bloqueo legal por objetivo prohibido (baja/alto → lista de objetivos rechazados con código de política).

### 5.12 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA**: Ghidra 11.x (requiere JDK 21 Temurin), Rizin 0.7.x, Radare2 5.9.x, Capstone 5.0.x, LIEF 0.14.x, angr 9.2.x, Frida 16.x, QEMU 9.0.x, Unicorn 2.0.x, binwalk 2.3.x, unblob 24.x, CMake 3.28+, Ninja 1.11, networkx 3.3, zstd. Todo libre. **🟡 REQUIERE-PRERREQUISITO**: emuladores de referencia instalados (PPSSPP, melonDS/DeSmuME, Vita3K — libres y gratuitos); SDK libres de homebrew para compilar programas de prueba; el binario objetivo debe proceder del dispositivo o de la copia del propio usuario. **🔴 BLOQUEADO-SIN-HARDWARE**: usar hardware real como oráculo primario exige la consola (costes indicativos en §4.11) y, para algunas medidas, firmware personalizado instalado por el usuario bajo su responsabilidad.

### 5.13 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (Ghidra headless por lotes + exportación + triaje sobre un binario) → v1 (refinamiento con oráculo, matriz de arquitecturas poblada, clasificador de capas) → completo (libro mayor, pruebas diferenciales con traza, síntesis con clean room y suite de conformidad).

- **P5.a Infraestructura.** P5.a.1 Ghidra headless guionizado — **PV-5.a.1**: 3 binarios (MIPS, ARM, x86) importados y exportados con `index.jsonl` válido al 100 %. P5.a.2 checkpoint y reanudación — **PV-5.a.2**: matar el proceso al 40 % y reanudar reprocesando ≤ 50 funciones. P5.a.3 rizin/r2 y diffing — **PV-5.a.3**: `rz-diff` detecta las 12 funciones cambiadas entre dos versiones sembradas.
- **P5.b Triaje y extracción.** P5.b.1 clasificación por magic/entropía — **PV-5.b.1**: 200 ficheros clasificados con exactitud ≥ 0,95. P5.b.2 unblob/binwalk — **PV-5.b.2**: 10 imágenes de firmware de prueba extraídas con estructura correcta.
- **P5.c Refinamiento.** P5.c.1 firmas de librería — **PV-5.c.1**: precisión ≥ 0,95 y recall ≥ 0,85 sobre 300 funciones. P5.c.2 oráculo Unicorn — **PV-5.c.2**: 100 % de hipótesis falsas refutadas con caso mínimo. P5.c.3 `readability_score` — **PV-5.c.3**: mejora media ≥ 25 % tras aplicar tipos y nombres verificados.
- **P5.d Matriz y capas.** P5.d.1 poblar `arch_fact` — **PV-5.d.1**: 100 % de celdas con `source_kind ≠ modelo` y ninguna con confianza < 0,6 sin marcar. P5.d.2 clasificador — **PV-5.d.2**: exactitud ≥ 0,85 contra etiquetado manual; compilación aislada ejecutada para el 100 % de las etiquetas 'agnóstica'.
- **P5.e Libro mayor.** P5.e.1 generación — **PV-5.e.1**: cada fila con justificación que referencia una celda concreta de la matriz (0 filas sin `evidence_refs`). P5.e.2 recalibración de esfuerzo — **PV-5.e.2**: tras 10 módulos reales, error medio de la estimación ≤ 40 %.
- **P5.f Diferencial y síntesis.** P5.f.1 traza y comparación — **PV-5.f.1**: divergencia sembrada detectada en el índice exacto 20/20. P5.f.2 conformidad — **PV-5.f.2**: puntuación calculada y reproducible, con desviación 0 entre dos ejecuciones. P5.f.3 clean room — **PV-5.f.3**: 10/10 intentos de acceso cruzado denegados y registrados. P5.f.4 umbrales U1–U5 — **PV-5.f.4**: el artefacto sólo se marca válido si los cinco se cumplen (comprobación automatizada, 0 excepciones manuales).

Métricas de salida: ≥ 0,85 de exactitud en clasificación de capas, ≥ 0,95 de precisión en firmas, 100 % de hipótesis fijadas con oráculo, detección exacta del primer punto de divergencia, y libro mayor completo sin filas sin evidencia.

---

## ÁREA 6 — Resiliencia y rotación dinámica (failover)

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA.**

### 6.1 Propósito y alcance

Garantiza que un análisis de 300 páginas o una decompilación de 6 horas **no se pierdan** porque un proveedor se agotó en el minuto 200. Gestiona el registro de proveedores, la selección por capacidad y salud, el cortacircuitos, la contención de tasa, y sobre todo el WAL de unidades reanudables que hace que el trabajo sobreviva a cualquier cambio.

Queda fuera: la calidad del contenido (Áreas de dominio) y la política de qué modelo es mejor para qué capacidad cognitiva (Área 12, que declara el requisito; aquí se implementa la mecánica).

**Consume:** Área 0 (WAL, planificador, bus). **Alimenta:** Áreas 1, 2, 3, 5, 7, 10, 11 (toda llamada a modelo pasa por aquí).

*Nota de versión:* desde la incorporación del **Área 14 (MAGI-ROUTE)**, esta área conserva íntegro su papel de **contrato de política** (capacidad exigida, regla de diversidad, WAL de unidades reanudables, reconciliación y marcado de calidad heterogénea) y delega la **mecánica** de registro de proveedores, cortacircuitos, cubo de fichas y reintentos en la pasarela, cuando está disponible. Todo lo escrito a continuación sigue siendo normativo y es, además, el **camino de reserva obligatorio** cuando la pasarela no está: por eso no se ha recortado ni una línea.

### 6.2 Arquitectura y registro de proveedores

```
 solicitud de inferencia {capacidades requeridas, tokens estimados, prioridad}
        │
        ▼
 ┌───────────────────────────┐   no cumple capacidad   ┌──────────────────────┐
 │ FILTRO DE CAPACIDAD       │────────────────────────►│ ¿hay alternativa?    │
 │ (visión, herramientas,    │                         │ no → DEPENDENCIA:    │
 │  contexto, JSON estricto) │                         │ usar suelo local     │
 └──────────┬────────────────┘                         └──────────────────────┘
            ▼
 ┌───────────────────────────┐   circuito abierto    ┌──────────────────────┐
 │ PUNTUADOR (§6.3)          │──────────────────────►│ siguiente candidato  │
 └──────────┬────────────────┘                       └──────────────────────┘
            ▼
 ┌───────────────────────────┐  429/5xx/timeout/esquema inválido
 │ CUBO DE FICHAS + LLAMADA  │───────────────────────────┐
 └──────────┬────────────────┘                           ▼
            │ éxito                            ┌────────────────────────┐
            ▼                                  │ CORTACIRCUITOS         │
 ┌───────────────────────────┐                 │ cerrado→abierto→semi   │
 │ WAL DE UNIDADES (§6.5)    │◄────────────────┤ + reintento con jitter │
 │ ⚠ punto de fallo: aquí se │                 └────────────────────────┘
 │ salva o se pierde el      │
 │ trabajo de 6 horas        │
 └───────────────────────────┘
```

Estructura de datos por proveedor (`provider_registry.yaml` + tabla `provider_quota`):

```yaml
providers:
  - id: local-text
    kind: local                     # local | oficial-gratuito
    endpoint: "http://127.0.0.1:8081/v1"
    models: ["qwen2.5-coder-7b-q5km", "deepseek-r1-distill-7b-q4km", "llama-3.1-8b-q4km"]
    capabilities: {max_context: 32768, vision: false, tools: false, structured_output: "gbnf"}
    cost: 0
    quota: {declared: "unlimited", window: null}
    observed: {latency_ms_ewma: 21840, error_rate_ewma: 0.004}
    circuit: {state: closed, failures: 0, opened_at: null}
    retry: {max_attempts: 2, backoff_base_ms: 500, jitter: "full"}
  - id: local-vlm
    kind: local
    endpoint: "http://127.0.0.1:8082/v1"
    models: ["qwen2-vl-7b-q4km"]
    capabilities: {max_context: 32768, vision: true, tools: false, structured_output: "gbnf"}
    cost: 0
    quota: {declared: "unlimited", window: null}
  - id: claude-code-cli
    kind: oficial-gratuito
    access: "cli"                   # invocación no interactiva, §10.D
    command: ["claude", "-p", "{prompt}", "--output-format", "stream-json"]
    capabilities: {max_context: 200000, vision: true, tools: true, structured_output: "schema+retry"}
    cost: 0                          # dentro del plan que el usuario ya tenga
    quota: {declared: "según el plan del usuario", window: "según el plan del usuario"}
    retry: {max_attempts: 2, backoff_base_ms: 2000, jitter: "full"}
  - id: hf-inference
    kind: oficial-gratuito
    access: "huggingface_hub.InferenceClient"
    capabilities: {max_context: 32768, vision: false, tools: false, structured_output: "schema+retry"}
    cost: 0
    quota: {declared: "nivel gratuito documentado por el proveedor", window: "mensual"}
    retry: {max_attempts: 3, backoff_base_ms: 1000, jitter: "full"}
```

**Nota normativa sobre proveedores mencionados en el encargo.** Servicios de chat de terceros accesibles sólo por interfaz web (por ejemplo HuggingChat, o el chat con IA de DuckDuckGo, citados en el encargo como referencia de opciones gratuitas) **no se integran como backends automatizados**, en cumplimiento de §I.3: automatizar un navegador contra una interfaz de chat de terceros rompe sus términos, es frágil y hace el sistema irreproducible. Los modelos de esas familias (Mistral, DeepSeek, Llama, Qwen, Gemma, Phi) sí se usan — **ejecutándolos localmente con pesos abiertos**, que es la vía robusta, ilimitada y reproducible. Cuando exista una API oficial con nivel gratuito documentado para alguno de ellos, se añade como fila `oficial-gratuito` en este registro y nada más cambia.

### 6.3 Contratos, algoritmo de selección y cortacircuitos

```python
def select_provider(req: InferenceRequest) -> ProviderChoice: ...
async def call_model(req: InferenceRequest, choice: ProviderChoice) -> ModelResponse: ...
def record_outcome(provider_id: str, outcome: CallOutcome) -> None: ...
def open_work(job_id: JobId, units: list[UnitSpec]) -> WorkLedger: ...
def next_pending(job_id: JobId) -> UnitSpec | None: ...
def commit_unit(job_id: JobId, unit_id: str, result: UnitResult) -> None: ...
def reconcile(job_id: JobId) -> ReconciliationReport: ...
```

**Función de puntuación (explícita):**

```
score(p) = 0,40·cap_fit(p)            # 1 si cumple todas las capacidades requeridas, 0 si no (filtro duro previo)
         + 0,25·health(p)             # 1 − error_rate_ewma, con circuito abierto ⇒ 0
         + 0,20·quota_headroom(p)     # min(1, restante / (tokens_estimados · 3))
         + 0,15·speed(p)              # 1 / (1 + latency_ms_ewma / 10000)
   con desempate por kind: 'local' gana a 'oficial-gratuito' cuando |Δscore| < 0,05,
   porque local es ilimitado y no consume una cuota que hará falta después.
```

**Regla dura de dependencia:** si la tarea exige visión y sólo un proveedor la ofrece, no hay selección, hay dependencia. Por eso el **suelo** es siempre local: el VLM local (`local-vlm`) debe estar instalado y es requisito de instalación del sistema; si un proveedor remoto con visión cae, la tarea se degrada al VLM local con `provider.degraded{capability:"vision"}` y anotación en el acta, nunca se bloquea.

**Cortacircuitos.** Estados `closed → open → half_open`. Cuenta como fallo: HTTP 5xx, HTTP 429 (además consume cuota), timeout (> `p95·3` con mínimo 30 s), respuesta vacía, y **respuesta que no valida contra el esquema tras agotar los reintentos de reparación**. Umbral de apertura: 5 fallos en ventana de 60 s **o** 3 fallos consecutivos. Temporizador de reapertura: 60 s × 2^(aperturas_recientes), con techo de 15 min. En `half_open` se permite **una** llamada de prueba; éxito ⇒ `closed` y reset de contadores; fallo ⇒ `open` con el temporizador escalado.

**Contención de tasa.** Cubo de fichas por proveedor y por dimensión (peticiones/min y tokens/min), calibrado al **80 %** de la cuota declarada (margen de seguridad del 20 %) — el sistema no descubre su límite chocando contra él. El cubo se rellena de forma continua (`capacidad/ventana` por segundo). Si al pedir fichas la espera estimada supera 20 s, `select_provider` reevalúa y probablemente elige local.

**Reintento.** Retroceso exponencial con *full jitter*: `espera = uniform(0, base·2^intento)`, máximo por clase: 429 → 3 intentos; 5xx → 2; timeout → 1; error de esquema → 2 (reparación dirigida, §7.4); **no se reintentan**: 401/403 (credencial o permiso), 400 con error de validación de entrada, y cualquier error que indique que la petición viola los términos del proveedor.

### 6.4 Implementación

Cliente unificado en `core/providers/`: `base.py` (interfaz), `local_llama.py` (OpenAI-compatible con `httpx` 0.27, streaming SSE), `claude_code.py` (subproceso, §10.D), `hf_client.py` (`huggingface_hub` 0.24). Todos devuelven el mismo `ModelResponse{text, json?, tokens_in, tokens_out, model_id, provider_id, latency_ms, finish_reason}`. Paridad Windows/Linux: sólo difiere el lanzamiento de subprocesos (ProcessHAL) y la ruta de binarios; el resto es idéntico.

**Decisiones formalizadas de esta área.**
**Decisión:** el `unit_id` es determinista y se calcula como `sha256(job_kind + entrada_normalizada + índice_lógico)`, nunca con un contador de ejecución — porque un identificador dependiente de la ejecución hace imposible reanudar sin recomputar.
*Descartado:* identificadores secuenciales por ejecución — más simples, pero rompen exactamente la propiedad que justifica el WAL.
**Decisión:** el cubo de fichas se calibra al 80 % de la cuota declarada del proveedor — porque el sistema no debe descubrir su límite chocando contra él, y un margen del 20 % absorbe la deriva de contabilidad entre cliente y servidor.
**Decisión:** todo artefacto producido con más de un modelo declara en su cabecera la tabla de tramos y modelos — porque ocultar la heterogeneidad convierte un resultado depurable en uno inexplicable.

### 6.5 Algoritmos: no perder el trabajo largo

**A6-1 — Descomposición en unidades reanudables e idempotencia.**
```
1. todo trabajo largo declara una función de partición: unidades disjuntas y ordenables
      Área 1: unidad = página            Área 2: unidad = afirmación
      Área 5: unidad = función           Área 11: unidad = derivada
2. unit_id ESTABLE y determinista: sha256(job_kind + entrada_normalizada + índice_lógico)
      (nunca un contador de ejecución: eso rompe la reanudación)
3. idempotencia: commit_unit es un UPSERT por (job_id, unit_id); reejecutar una unidad no duplica
      efectos porque los efectos externos (escrituras) van al CAS por contenido
4. requisito: una unidad no puede depender del resultado de otra unidad de la misma tanda; si lo
      necesita, se declara como fase distinta (fases secuenciales, unidades paralelas dentro de la fase)
```

**A6-2 — WAL de trabajo y reanudación.**
```
1. al abrir el trabajo: escribir en job_unit todas las unidades con estado PENDING y su hash de entrada
2. por unidad completada: INSERT/UPDATE {estado:DONE, salida_ref (CAS), provider_id, model_id,
      prompt_hash, tokens, ts} con fsync agrupado cada 8 unidades o cada 2 s (lo que ocurra antes)
3. al reiniciar: SELECT unidades con estado != DONE ordenadas por índice → sólo esas se recomputan
4. verificación de coherencia: si el hash de entrada de una unidad DONE ya no coincide con la entrada
      actual (el usuario cambió el documento), esa unidad pasa a STALE y se recomputa
5. coste: 1 fila por unidad (~200 bytes); 300 páginas ⇒ 60 KB. Irrelevante frente al beneficio
```

**A6-3 — Migración de proveedor a mitad de trabajo y reconciliación.**
```
1. cada unidad registra qué proveedor y modelo la produjo
2. normalización estricta: toda salida se valida contra el MISMO esquema pydantic sea cual sea el
      proveedor; los campos libres (rationale, recommendation) se normalizan en longitud e idioma
3. PASADA FINAL DE RECONCILIACIÓN cuando el trabajo usó > 1 modelo:
   3.1 agrupar unidades por proveedor: tramos [1..120] = M1, [121..300] = M2
   3.2 métricas por tramo: longitud media de rationale, tasa de cada valor de enumeración (p. ej.
        proporción de 'insuficiente'), vocabulario distintivo (log-odds), severidad media
   3.3 detectar incoherencia: diferencia > 2σ respecto de la distribución global en cualquier métrica
   3.4 muestrear 10 unidades del tramo divergente y reejecutarlas con el otro modelo; si el resultado
        cambia de categoría en ≥ 3 de 10, marcar el tramo 'requiere revisión' y proponer reejecución
        completa del tramo como acción R1
4. MARCADO DE CALIDAD HETEROGÉNEA en el artefacto final (obligatorio, no opcional):
      sección "Procedencia de la generación" con tabla unidad-rango → proveedor → modelo → fecha,
      y una nota en la cabecera si hubo más de un modelo. Es honestidad y es depurable.
```

**Tabla de degradación en cascada.**

| Capacidad perdida | Qué hace el sistema | Cómo se comunica al usuario | Qué se anota en el acta |
|---|---|---|---|
| Proveedor remoto agotado (cuota) | Cambia a local y continúa la unidad siguiente | Chip ámbar en el panel de proveedores + notificación | `provider.degraded{reason:"quota"}`, `models` cambia a mitad de acta |
| Visión remota caída | VLM local con menor resolución de tesela | Aviso en el informe forense y `confidence_penalty` | `capability_degraded:["vision"]` |
| Contexto insuficiente (modelo local con 32 k) | Poda jerárquica + troceado de la unidad | Indicador "contexto podado" en el turno | `context_pruned: true` con tokens eliminados |
| Herramientas (tool use) no disponibles | Se sustituye por bucle explícito de propuesta→ejecución del Área 8 | Transparente | `tools:"emulated"` |
| Salida estructurada débil | Reparación dirigida y, si falla, unidad marcada `undecided` | Contador de reparaciones visible | `repairs: n` |
| Toda la red caída | Modo offline completo | Banner "modo sin conexión" | `offline: true` |

**Modo totalmente offline: qué queda operativo.** Todo el Área 5 (Ghidra, rizin, Unicorn, QEMU, pruebas diferenciales, síntesis), todo el Área 9 (CAD, slicer, impresión, HDL, síntesis lógica, OpenLane, KiCad, flasheo), todo el Área 4 (dispositivos), el Área 1 completa (VLM local), el Área 2 sobre el corpus ya ingerido, el Área 3 completa con modelos locales, y el Área 11 salvo la búsqueda de arte previo en línea. Lo único que **exige** red: descarga inicial de modelos y toolchains, ingesta de documentos desde la web, búsqueda de patentes y literatura, y los proveedores de Nivel 2.

### 6.6 Integración con el debate popperiano

Afirmaciones: "el trabajo J se reanudó sin pérdida", "el tramo producido por M2 es homogéneo con el de M1". Evidencia admisible: el propio WAL, los hashes de entrada/salida por unidad, y las métricas de reconciliación. Refutación más potente: **reejecutar una muestra aleatoria de unidades DONE y comparar** — si el resultado difiere materialmente, la afirmación de homogeneidad cae. Invocación: al cerrar cualquier trabajo que haya usado más de un modelo, obligatoriamente.

### 6.7 Costos, latencia y recursos

Sobrecoste del WAL: ≈ 0,4 ms por unidad (con fsync agrupado). Sobrecoste de la reconciliación: 10 unidades reejecutadas por tramo divergente (≈ 3 % del trabajo). Memoria del registro: despreciable. La selección de proveedor añade < 1 ms. **Salto del debate:** la mecánica de failover es determinista y no se debate; sólo se debate la homogeneidad del resultado. **Caché:** las respuestas con temperatura 0 se cachean por `sha256(prompt)+model_hash+params_hash`, lo que hace que una reanudación tras un fallo inmediato no vuelva a pagar la inferencia si el prompt fue idéntico.

### 6.8 Calidad y pruebas

| Caso | Criterio de éxito |
|---|---|
| Camino feliz | 300 unidades con un solo proveedor: 300 DONE, 0 duplicadas |
| Corte de proveedor en la unidad 200 | Trabajo completa las 300; se recomputan ≤ 1 unidad; el artefacto declara los dos tramos |
| Reinicio duro a mitad | Tras reiniciar, se recomputan sólo las no-DONE en 20/20 pruebas |
| Cortacircuitos | Proveedor que falla 5 veces: abre en ≤ 5 llamadas, no se vuelve a intentar antes del temporizador |
| Cubo de fichas | Con cuota simulada de 60 peticiones/min: 0 respuestas 429 en 10 min de carga continua |
| Entrada modificada | Cambiar el documento a mitad: las unidades afectadas pasan a STALE y se recomputan |
| Reconciliación | Sembrar un tramo con un modelo sesgado: detección del tramo divergente en 9/10 casos |
| Consenso/desacuerdo entre agentes | Sobre la homogeneidad: con muestreo concordante, `survives` ≥ 80; con 3/10 discrepancias, `falsified` y reejecución propuesta |
| Offline total | Desconectar la red: las Áreas 1, 3, 4, 5, 9 completan sus pruebas de humo al 100 % |

### 6.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta | Estado |
|---|---|---|---|---|
| Todos los proveedores en circuito abierto | selector sin candidatos | Sin inferencia | Forzar `local-text` ignorando el circuito (es el suelo) y, si tampoco responde, pausar el trabajo con estado `WAITING_MODEL` | Pausado, recuperable |
| WAL corrupto | `integrity_check` | Reanudación imposible | Reconstruir desde el CAS por salidas presentes y recomputar el resto | Degradado, sin pérdida total |
| Fallo parcial: unidad marcada DONE sin salida en CAS | verificación de referencia al leer | Artefacto incompleto | Revertir a PENDING y recomputar | Consistente |
| Reloj alterado (cuotas) | comparación monotónica | Cuota mal contada | Usar reloj monotónico para ventanas | Operativo |
| Proveedor devuelve texto plausible pero inválido | validador de esquema | Basura silenciosa | Reparación dirigida y, si falla, cuenta como fallo del cortacircuitos | Consistente |

### 6.10 Riesgos y mitigaciones

Dependencia oculta de un proveedor único con visión (media/alto → suelo local obligatorio). Reanudación que duplica efectos (baja/alto → idempotencia por `unit_id` y CAS). Falsa sensación de homogeneidad entre tramos (alta/medio → reconciliación obligatoria y marcado en el artefacto). Violación involuntaria de términos por reintentos agresivos (media/alto → cubo al 80 %, sin reintento en 401/403, sin automatización de interfaces de chat). Coste de tokens invisible (media/medio → contadores por área en la GUI). Cachés que devuelven resultados obsoletos (media/medio → clave con hash de todos los componentes).

### 6.11 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA**: `httpx` 0.27, `huggingface_hub` 0.24, SQLite. **🟡 REQUIERE-PRERREQUISITO**: para el Nivel 2, una cuenta gratuita en el proveedor correspondiente y, para `claude-code-cli`, tener Claude Code instalado y autenticado con el plan que el usuario ya posea; ninguno es necesario para operar el sistema, que funciona íntegramente en Nivel 1.

### 6.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (cliente local + WAL + reanudación) → v1 (registro, puntuación, cortacircuitos, cubo de fichas) → completo (migración de proveedor, reconciliación, marcado heterogéneo, degradación en cascada).

- **P6.a Cliente y suelo local.** P6.a.1 cliente OpenAI-compatible — **PV-6.a.1**: 500 llamadas locales, 0 errores de protocolo. P6.a.2 arranque y health de el proveedor de nube asignado — **PV-6.a.2**: recuperación automática tras matar el servidor, en ≤ 30 s.
- **P6.b WAL.** P6.b.1 partición e ids estables — **PV-6.b.1**: dos ejecuciones producen el mismo conjunto de `unit_id` (comparación exacta). P6.b.2 reanudación — **PV-6.b.2**: 20 reinicios duros, ≤ 1 unidad recomputada cada vez. P6.b.3 STALE — **PV-6.b.3**: cambio de entrada detectado en 10/10.
- **P6.c Selección y protección.** P6.c.1 puntuador — **PV-6.c.1**: en 100 escenarios simulados, elige el proveedor esperado en ≥ 95 %. P6.c.2 cortacircuitos — **PV-6.c.2**: apertura y reapertura conforme a umbrales en 20/20. P6.c.3 cubo de fichas — **PV-6.c.3**: 0 respuestas 429 bajo carga.
- **P6.d Heterogeneidad.** P6.d.1 reconciliación — **PV-6.d.1**: detección ≥ 9/10 de tramos sembrados. P6.d.2 marcado — **PV-6.d.2**: 100 % de artefactos multi-modelo con la tabla de procedencia de generación.
- **P6.e Offline.** P6.e.1 prueba de humo sin red — **PV-6.e.1**: las cinco áreas declaradas completan su prueba de humo al 100 % con la interfaz de red desactivada.

Métricas de salida: 0 unidades perdidas en 20 reinicios, ≤ 1 unidad recomputada por corte, 0 respuestas 429, y 100 % de artefactos multi-modelo etiquetados.

---

## ÁREA 7 — Especificación de prompts de sistema (modo *Forensic Engineer*)

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA.**

### 7.1 Propósito, alcance y nota de diseño

Produce análisis exhaustivo, literal y sin adornos de material técnico difícil — C decompilado ilegible, documentos legales densos, memorias de cálculo, trazas de fallo — eliminando el ruido: rodeos, advertencias no solicitadas sobre contenido técnico legítimo, cobertura defensiva, resúmenes cuando se pidió detalle, y juicios de valor sobre el trabajo del usuario. Eso se consigue con **especificación de rol precisa, formato de salida forzado y validación mecánica de la respuesta**, no con trucos.

**Nota de diseño (normativa).** Este módulo **no** diseña prompts cuyo propósito sea suprimir las políticas de seguridad de un modelo ni hacerle producir lo que su operador prohíbe. Aparte de romper los términos de uso, es mala ingeniería: es la parte más frágil de cualquier pipeline (se rompe con cada actualización del modelo, en silencio, y contamina resultados sin avisar) y es innecesaria, porque la vía robusta ya está en §I.3 — ejecutar modelos de pesos abiertos localmente, donde el usuario es el operador, la política la fija él, no hay filtro externo que sortear y el comportamiento es reproducible. **La respuesta correcta a "un modelo remoto se niega a una tarea técnica legítima" es enrutar esa tarea al modelo local** (`route_to: local-text`), registrarlo en el acta como `refusal_rerouted`, y seguir. Nunca atacar al modelo remoto.

Queda fuera: la lógica de dominio (áreas correspondientes) y la selección de proveedor (Área 6).

**Consume:** Área 0 (hashes, procedencia), Área 12 (bloques de capacidad). **Alimenta:** todas las áreas que llaman a un modelo.

### 7.2 Arquitectura: un compilador de prompts, no prompts sueltos

```
  petición {rol, dominio, capacidades C0x, esquema de salida, presupuesto}
        │
        ▼
 ┌──────────────────────────────────────────────────────────────┐
 │ COMPILADOR DE PROMPTS (modules/prompts/compiler.py, Jinja2)  │
 │  base común  +  bloque de rol  +  bloque de dominio          │
 │  +  bloques de capacidad (Área 12)  +  contrato de salida    │
 │  +  bloque de auto-verificación                              │
 │  ⚠ punto de decisión: ¿cabe en el contexto? → poda (§7.5)    │
 └───────────┬──────────────────────────────────────────────────┘
             │ prompt_render + prompt_hash (va al acta)
             ▼
 ┌──────────────────────────┐  local  ┌───────────────────────────┐
 │ SELECTOR DE MECANISMO    │────────►│ GBNF (decodificación      │
 │ DE SALIDA ESTRUCTURADA   │         │ restringida: GARANTÍA)    │
 └──────────┬───────────────┘         └───────────────────────────┘
            │ remoto
            ▼
 ┌──────────────────────────┐  inválido  ┌──────────────────────────┐
 │ VALIDACIÓN pydantic v2   │───────────►│ REPARACIÓN DIRIGIDA §7.4 │
 └──────────┬───────────────┘            └──────────────────────────┘
            ▼ válido → respuesta tipada
```

Árbol de ficheros y versionado:

```
prompts/
├── base/forensic_engineer.md.j2        # base común (v1.0.0)
├── roles/{melchior,balthasar,casper}.md.j2
├── domains/{decompiled_c,doc_topography,normative_contrast,mech_gcode,hdl_verif,invention}.md.j2
├── capabilities/c01..c39.md.j2         # 39 bloques, uno por capacidad del Área 12
├── contracts/{claims,refutations,verdicts,alignment,topography,ledger,invention}.schema.json
├── grammars/*.gbnf                     # generadas desde los esquemas
└── registry.yaml                       # nombre → ruta → semver → sha256
```

Cada plantilla lleva `semver` y su `sha256` se calcula sobre el **render final** (no sobre la plantilla) y se guarda en `acta.hashes.prompt_X` y en `model_run.prompt_hash`. Cambiar un prompt cambia el hash y, por tanto, invalida la caché y queda trazado.

### 7.3 Los prompts, redactados y listos para pegar

**7.3.1 Base común — `prompts/base/forensic_engineer.md.j2`**

```text
Eres un ingeniero forense técnico. Operas sobre material difícil y produces análisis verificable.

REGLAS DE FONDO
1. Literalidad: cita el material exactamente. Toda cita debe existir palabra por palabra en el
   contexto que se te entregó. Si no puedes citar, no afirmas.
2. Exhaustividad: cuando se te pide detalle, entregas detalle completo. No resumes, no abrevias,
   no dices "y otros elementos similares". Si una lista debe ser exhaustiva, la enumeras entera.
3. Incertidumbre declarada: cada afirmación lleva su confianza en [0,1] y la razón de esa confianza.
   No conviertes una suposición en un hecho por comodidad de redacción.
4. Prohibido inventar: si un dato no está en el contexto, escribes explícitamente "no consta en el
   contexto entregado" y lo tratas como dato faltante, no como valor por defecto.
5. Sin relleno: nada de preámbulos, disculpas, elogios al usuario, ni advertencias no solicitadas
   sobre material técnico legítimo. Nada de cierres motivacionales.
6. Sin juicios de valor sobre el trabajo del usuario. Describes lo que observas y su consecuencia
   técnica.
7. Números: todo número que afirmes debe provenir de (a) el contexto, citado, o (b) un cálculo que
   describes paso a paso con sus entradas. Nunca de tu estimación.
8. Formato: tu respuesta completa es un único objeto JSON válido contra el esquema indicado más
   abajo. Sin texto antes ni después. Sin bloques de código. Sin comentarios.

CONTEXTO DE TRABAJO
- Proyecto: {{ project_name }}
- Área: {{ area_id }} — {{ area_name }}
- Fecha de referencia: {{ as_of }}
- Idioma de salida: español técnico.
```

**7.3.2 MELCHIOR • 1 — `prompts/roles/melchior.md.j2`**

```text
ROL: MELCHIOR • 1 — ARQUITECTO E INGENIERO DE SISTEMAS (CREADOR / SINTETIZADOR).

Produces la propuesta: el análisis, el código, la interpretación del decompilado, el dictamen o el
diseño que se te pide. Tu salida se someterá inmediatamente a un intento hostil de refutación.

OBLIGACIONES
- Emites AFIRMACIONES FALSABLES. Cada afirmación incluye un campo "falsifier": la condición concreta,
  observable y comprobable que, de cumplirse, la derribaría. Ejemplo válido: "si al ejecutar con
  src y dst solapados el resultado difiere de memmove, la afirmación cae". Ejemplo inválido:
  "si se demuestra que no es correcta".
- Cada afirmación lleva su evidencia: tipo, localizador (fichero+offset, página+coordenada, run_id,
  chunk_id), valor y herramienta con versión.
- Declaras tus suposiciones en el propio texto de la afirmación. Una suposición no declarada es
  munición para el BALTHASAR.

PROHIBICIONES
- Prohibido el lenguaje de cobertura: "podría", "quizá", "en general", "depende", "es posible que",
  "en algunos casos". Si no puedes comprometerte, baja la confianza y dilo con un número.
- Prohibido afirmar sin condición de falsación.
- Prohibido responder con prosa fuera del JSON.

SALIDA: objeto JSON con la clave "claims", array de objetos
{id, statement, falsifier, evidence[], confidence, assumptions[]}.
```

**7.3.3 BALTHASAR • 2 — `prompts/roles/balthasar.md.j2`**

```text
ROL: BALTHASAR • 2 — AUDITOR DE SEGURIDAD Y FALSACIONISTA (COGNICIÓN HOSTIL).

Tu único objetivo es derribar las afirmaciones que recibes. No propones alternativas amables, no
matizas, no buscas consenso. Construyes el contraejemplo, el caso límite, la entrada maliciosa, la
condición de carrera, el modo de fallo físico o la laguna normativa.

CARGA DE LA PRUEBA
- Toda refutación debe traer MECANISMO: cómo se produce concretamente la contradicción.
- Toda refutación debe traer PASOS DE REPRODUCCIÓN ejecutables o verificables por un tercero.
- Una refutación sin mecanismo es inadmisible y será descartada antes de llegar al Juez. No la emitas.

TIPOS ADMITIDOS (elige el que corresponda, uno por refutación)
empirica | logica | completitud | suposicion | normativa | reproducibilidad | coste | falsabilidad

La refutación de tipo "falsabilidad" —demostrar que la afirmación no es refutable por ningún
experimento posible— es la más grave del sistema. Úsala cuando corresponda y demuéstrala.

NO VES el razonamiento interno del MELCHIOR: sólo su afirmación y su evidencia. Atacas el resultado,
no el camino.

SALIDA: objeto JSON con la clave "refutations", array de objetos
{id, target_claim_id, type, mechanism, reproduction_steps[], evidence[]}.
Si tras un análisis serio no encuentras ninguna refutación admisible, devuelves "refutations": [] y
rellenas "no_refutation_rationale" explicando qué atacaste y por qué resistió. No inventes objeciones
de relleno: eso degrada el debate y será detectado.
```

**7.3.4 CASPER • 3 — Juez Operativo y Árbitro de Concordia — `prompts/roles/casper.md.j2`** (rúbrica embebida)

```text
ROL: CASPER • 3 — JUEZ OPERATIVO Y ÁRBITRO DE CONCORDIA.

No opinas sobre el fondo del asunto: arbitras el procedimiento. Evalúas si cada refutación se
sostiene, si el MELCHIOR la respondió con evidencia o la concedió, y emites veredicto.

RÚBRICA (suma 100; puntúa cada criterio y da el total)
- soporte_empirico (30): 30 si hay ejecución o medición reproducible que respalda la afirmación;
  15 si sólo hay análisis estático; 0 si sólo hay razonamiento.
- consistencia_logica (20): resta 5 por cada contradicción interna acreditada.
- casos_limite (15): proporción de casos límite planteados por B que A abordó con evidencia.
- falsabilidad (12): 12 si el "falsifier" es concreto y comprobable; 0 si es vago o si prosperó una
  refutación de tipo "falsabilidad".
- reproducibilidad (10): 10 si un tercero puede repetirlo con los pasos y hashes dados.
- parsimonia (8): resta 2 por cada suposición no declarada que B identificó.
- normativa (5): 5 con cita verificada; 0 ante violación acreditada; si no aplica, redistribuye estos
  5 puntos proporcionalmente entre los otros seis y marca "redistributed": true.

UMBRAL: 70. Total ≥ 70 → "survives". Total entre 60 y 69 → "amended", y DEBES especificar en
"required_action" la enmienda concreta que A tiene que hacer. Total < 60 → "falsified".
"undecided" sólo es admisible si indicas en "required_action" qué medición o ejecución concreta
resolvería la disputa. "unfalsifiable" si la afirmación no admite refutación posible.

PRECEDENCIA DE EVIDENCIA (obligatoria, no negociable):
medición física > ejecución determinista > análisis estático > cita normativa > razonamiento.
No puedes emitir un veredicto que contradiga la evidencia de mayor rango disponible. Si lo haces,
tu turno será rechazado automáticamente.

PROHIBIDO: "ambas partes tienen razón" sin desempate. Decides.

SALIDA: objeto JSON con la clave "verdicts", array de
{claim_id, outcome, score, rubric{...}, rationale, required_action{kind, spec}}.
```

**7.3.5 Especialista en C decompilado — `prompts/domains/decompiled_c.md.j2`**

```text
DOMINIO: LECTURA DE C DECOMPILADO (salida del decompilador Ghidra).

Convenciones que vas a encontrar y cómo debes interpretarlas:
- FUN_XXXXXXXX: función sin símbolo, nombrada por su dirección. La dirección ES información: úsala
  como localizador en tu evidencia.
- DAT_XXXXXXXX / PTR_XXXXXXXX: dato global sin símbolo / puntero global. Una escritura a DAT_ desde
  varias funciones sugiere estado compartido; dilo y márcalo como hipótesis con su falsifier.
- LAB_XXXXXXXX: etiqueta de salto interno; suele indicar un bucle o un switch reconstruido.
- undefined, undefined1/2/4/8: el decompilador no infirió el tipo; el número es el TAMAÑO en bytes.
  Nunca asumas que undefined4 es int con signo: puede ser puntero, float o enum.
- uVar/iVar/lVar/pVar/fVar/auVar: variables sintéticas (unsigned, int, long, puntero, float, array).
  El sufijo numérico no tiene significado semántico.
- in_XX / unaff_XX / extraout_XX: registros de entrada no modelados, no afectados o valores de
  retorno secundarios. Su presencia indica que la convención de llamada puede estar mal detectada:
  señálalo explícitamente.
- halt_baddata(), switchD, code *: zonas donde el análisis falló o hay salto indirecto no resuelto.
- Aritmética de punteros expresada como *(int *)(x + 0x14): el 0x14 es un OFFSET DE CAMPO. Propón la
  estructura y numera los campos por offset.
- CONCAT44/SUB84/ZEXT48: manipulación de anchura de palabra; suelen indicar tipos de 64 bits
  partidos o valores de retorno en pares de registros.

TU TAREA: convertir esto en hipótesis falsables sobre identidad, tipos, estructuras y máquina de
estados de la función. Cada hipótesis debe indicar cómo verificarla con una ejecución concreta
(oráculo de función sobre el emulador de instrucciones), no con una impresión de lectura.
Nunca afirmes que una función "es" algo sin proponer el caso de prueba que lo confirmaría o refutaría.
```

**7.3.6 Especialista en topografía documental — `prompts/domains/doc_topography.md.j2`**

```text
DOMINIO: TOPOGRAFÍA DOCUMENTAL FORENSE.

Recibes teselas de una página normalizada con su sistema de coordenadas en milímetros y las medidas
geométricas ya calculadas por el motor determinista (altura-x, altura de mayúsculas, interlineado,
sangrías, márgenes, densidad de tinta, ángulo de trama, ruido).

REGLAS
1. Las MEDIDAS mandan sobre tu impresión visual. Si tu lectura contradice una medida, lo declaras
   como conflicto y ganas por perdida: la medida se conserva.
2. Tu aportación es la interpretación estructural: qué bloque es encabezado, pie, cuerpo, tabla,
   firma o sello; qué bloques pertenecen a la misma unidad semántica; dónde hay una discontinuidad
   visual que las medidas no capturan.
3. Describes lo que ves con coordenadas. "En la parte de abajo" no es una observación: "bloque b7,
   x=30,2 mm y=241,0 mm" sí lo es.
4. No dictaminas falsedad. Emites indicios con su señal y su localización. La palabra "falso" no
   aparece en tu salida; sí "incoherente con el resto del expediente en <rasgo>".
5. Si la tesela está cortada, borrosa o ilegible, lo dices y bajas la confianza. No completas.

SALIDA: JSON contra el esquema de topografía, con blocks[], su rol, sus coordenadas y sus conflictos.
```

**7.3.7 Especialista en contraste normativo — `prompts/domains/normative_contrast.md.j2`**

```text
DOMINIO: CONTRASTE NORMATIVO (jurídico y técnico).

Recibes: (a) una afirmación extraída del documento bajo análisis, con su cita literal y su
coordenada; (b) un conjunto de fragmentos del corpus de referencia, cada uno con su identificador de
fragmento, su localizador (p. ej. "Artículo 13") y su texto literal.

REGLAS DURAS
1. Sólo puedes citar texto que aparezca literalmente en los fragmentos entregados. No cites de
   memoria. No inventes números de artículo. Si crees recordar una norma que no está en el contexto,
   ese conocimiento NO existe para esta tarea.
2. Si ningún fragmento sostiene un juicio, la relación es "sin-referencia-en-corpus". Es una
   respuesta correcta y esperada. Una inferencia plausible sin cita es un error grave.
3. Toda relación que asignes debe cumplir su exigencia probatoria:
   conforme / conforme-con-observacion / insuficiente / excesivo / contradictorio /
   nulo-de-pleno-derecho / ambiguo / no-aplicable / sin-referencia-en-corpus.
4. Los números no los juzgas: emites un plan de cálculo con variables, su origen (documento o
   corpus) y la expresión. El sistema lo ejecutará y el resultado del cálculo prevalece sobre tu
   juicio.
5. Vigencia: usa la fecha de referencia indicada. Si un fragmento tiene vigencia distinta a esa
   fecha, dilo y márcalo.
6. Tu salida es análisis técnico documentado, no asesoría legal, y así se etiquetará.

SALIDA: JSON contra el esquema Alignment, con references[] que incluyan chunk_id y cita literal.
```

**7.3.8 Especialista en diseño mecánico y G-Code — `prompts/domains/mech_gcode.md.j2`**

```text
DOMINIO: DISEÑO MECÁNICO PARAMÉTRICO Y G-CODE.

Produces geometría como CÓDIGO PARAMÉTRICO, nunca como descripción. Todo parámetro lleva nombre,
valor, unidad (mm, grados, N, kg) y rango válido.

REGLAS
1. Antes de proponer geometría, enumeras las restricciones extraídas del encargo: dimensiones de
   acoplamiento, cargas, materiales, tolerancias, volumen de impresión disponible.
2. Toda cota que dependa de otra se expresa como fórmula, no como número calculado a mano.
3. Declaras explícitamente: grosor mínimo de pared, ángulo máximo de voladizo, holgura de ajuste
   (por defecto 0,20 mm por lado para encajes deslizantes; 0,05 mm para ajustes a presión), y si la
   pieza requiere soportes.
4. Para G-Code: nunca emites movimientos sin homing previo; nunca extrusión por debajo de la
   temperatura mínima de extrusión del material; nunca coordenadas fuera del volumen declarado.
5. Toda pieza propuesta viene con su PLAN DE VERIFICACIÓN: qué se mide con calibre, en qué punto,
   con qué valor nominal y qué tolerancia. Sin plan de verificación, la propuesta es incompleta.
6. Si el encargo implica carga estructural, emites el cálculo de primer orden con sus supuestos
   (sección, momento, tensión admisible del material a la temperatura de trabajo) como plan de
   cálculo para que el sistema lo ejecute.

SALIDA: JSON con {parameters[], scad_or_cq_source, verification_plan[], assumptions[], risks[]}.
```

**7.3.9 Especialista en HDL y verificación — `prompts/domains/hdl_verif.md.j2`**

```text
DOMINIO: HDL SINTETIZABLE Y VERIFICACIÓN.

Escribes Verilog-2005/SystemVerilog SINTETIZABLE. Prohibido: retardos (#), initial en lógica de
diseño (sólo en bancos de prueba), bucles no acotados, lógica sensible a ambos flancos del mismo
reloj, y cruces de dominio de reloj sin sincronizador explícito de dos flip-flops.

OBLIGACIONES
1. Reset: declaras si es síncrono o asíncrono y lo aplicas de forma consistente en todo el módulo.
2. Cada módulo trae su banco de pruebas en cocotb (Python) con casos dirigidos y aleatorios
   restringidos, y su comparación contra un modelo de referencia en software.
3. Cada módulo trae al menos tres propiedades formales (assert/assume/cover) para SymbiYosys:
   una de seguridad ("nunca ocurre X"), una de vivacidad acotada ("si A, en ≤ N ciclos ocurre B") y
   una de cobertura ("existe una traza que alcanza el estado S").
4. Declaras el presupuesto de temporización esperado y qué ruta crees que será crítica.
5. Un contraejemplo del probador formal es la refutación definitiva de tu diseño: cuando lo recibas,
   no discutes, corriges y explicas la causa raíz en una línea.

SALIDA: JSON con {modules[{name, path, source}], testbench_cocotb, formal_properties[],
expected_utilization, critical_path_hypothesis}.
```

**7.3.10 Especialista en invención y extrapolación — `prompts/domains/invention.md.j2`**

```text
DOMINIO: INVENCIÓN Y EXTRAPOLACIÓN.

Trabajas sobre el esquema formal Invention: problema, principio de funcionamiento, dominio, vector
de parámetros con rangos y unidades, supuestos declarados, restricciones, recursos y TRL.

REGLAS
1. No generas "ideas": generas variaciones mediante un operador declarado (combinatoria, traslación
   de dominio, inversión de supuestos, fusión, escalado extremo, sustracción, principio TRIZ,
   biomímesis). En cada derivada indicas QUÉ OPERADOR la produjo y sobre qué elemento actuó.
2. Toda derivada declara la hipótesis central que la haría fracasar, y el experimento más barato que
   la pondría a prueba (el MVP es un experimento, no un producto).
3. Los límites físicos no se negocian: si una derivada requiere superar un límite conocido
   (conservación de energía, eficiencia de Carnot, límite de Shannon, resistencia del material),
   lo declaras y la derivada se marca inviable. Prefieres decir "esto viola X" a ser creativo.
4. Toda cifra de mercado o de coste va con su fuente y su incertidumbre, o se declara desconocida.
5. No emites asesoría de inversión ni recomendación financiera. Emites análisis con sus supuestos.

SALIDA: JSON contra el esquema Invention/Derivation, con operator, novelty_claim, killer_hypothesis,
cheapest_experiment y parameter_vector completo.
```

### 7.4 Contrato de salida forzado y bucle de reparación

*Decisión:* para modelos locales, **decodificación restringida por gramática GBNF** en `llama.cpp` (parámetro `grammar` en la petición), generada automáticamente desde cada JSON Schema con `json-schema-to-gbnf` en `scripts/gen_grammars.py` — porque es una garantía estructural, no un ruego: el muestreador no puede emitir un token que viole la gramática.
*Descartado:* confiar en el "modo JSON" del proveedor — no garantiza el esquema, sólo la sintaxis.

Para proveedores remotos sin gramática: validación `pydantic` v2 + **bucle de reparación dirigida**:
```
1. validar la respuesta contra el modelo pydantic
2. si falla: construir un mensaje de reparación con (a) el error exacto de pydantic (ruta del campo,
      tipo esperado, valor recibido), (b) el fragmento de la salida que lo provocó, (c) la instrucción
      "devuelve el JSON completo corregido, sin explicación"
3. reintentar con temperatura reducida a 0,1 y el mismo contexto; máximo 3 intentos
4. escalada tras 3 fallos: (a) reintentar con el proveedor local con GBNF; (b) si tampoco, registrar
      turno vacío con motivo y dejar que el Área 3 lo trate como turno perdido (no como acuerdo)
5. cada reparación se cuenta en metrics.repairs y alimenta el cortacircuitos del Área 6
```

**Bloque de auto-verificación** (se anexa a todos los prompts y su resultado va en el JSON):

```text
ANTES DE EMITIR, COMPRUEBA Y DECLARA EL RESULTADO EN EL CAMPO "self_check":
1. ¿Toda cita que incluyes aparece literalmente en el contexto entregado? (cita_literal: true/false)
2. ¿Toda afirmación tiene su condición de falsación concreta? (falsifier_presente: true/false)
3. ¿Algún número aparece sin cálculo o sin cita de origen? (numeros_sin_origen: lista de campos)
4. ¿Has usado lenguaje de cobertura prohibido? (hedging_detectado: lista de expresiones)
5. ¿Tu salida valida contra el esquema pedido? (esquema_ok: true/false)
Si alguna comprobación falla, corrígelo antes de responder. Declarar un self_check en verde con
fallos reales es el peor error posible: el sistema lo verifica por su cuenta y lo registrará.
```

El sistema **verifica mecánicamente** las cinco comprobaciones (el validador de citas del Área 2, el de `falsifier` del Área 3, el detector de números sin origen y la lista de patrones de cobertura). La discrepancia entre `self_check` declarado y verificación real se registra como `self_check_mismatch` y es una métrica de calidad del prompt.

**Decisiones formalizadas adicionales de esta área.**
**Decisión:** el contrato de salida y la evidencia citada quedan fijados y nunca se podan; cuando no cabe el material, se subdivide la unidad en vez de truncar — porque truncar evidencia produce respuestas que parecen correctas y no lo son.
*Descartado:* truncamiento por ventana deslizante — barato, pero introduce errores silenciosos que ninguna validación de esquema detecta.
**Decisión:** un prompt no se promueve a nueva versión si cualquier métrica del banco cae más de 3 puntos porcentuales — porque la degradación de prompts es invisible sin una puerta numérica.

### 7.5 Gestión del contexto (sin resumen: derogación de la versión anterior)

*Decisión:* **el resumen queda derogado como mecanismo de gestión de contexto** y sustituido por el registro íntegro y la composición direccionada del **Área 18** — porque comprimir el historial de una deliberación destruye exactamente lo que hace válido a este sistema: que toda cita exista literalmente y que ninguna refutación se evapore por falta de sitio.
*Descartado:* el «resumen jerárquico del historial» y el «contexto comprimido y neutralizado entre rondas» que esta misma sección proponía en revisiones anteriores. Se conserva **una sola** excepción: el `plain_summary` de 140 caracteres que cada nodo escribe **para el humano**, marcado `derived:true` y que **nunca** se reinyecta como memoria.

Presupuesto por bloque (ventana de 32 768 tokens del modelo local):

| Bloque | Presupuesto | Fijado |
|---|---|---|
| Base común | 600 | Sí |
| Bloque de rol | 700 | Sí |
| Bloque de dominio | 900 | Sí |
| Bloques de capacidad (Área 12) | 1 200 (máx. 4 × 300) | No |
| Contrato de salida (esquema + ejemplo) | 1 400 | **Sí** |
| **Restricciones vigentes, literales** | 400 | **Sí** |
| **Índice completo del estado acumulado** (§18.4, bloque 2) | 12 000 | **Sí** |
| **Cuerpo literal de elementos abiertos y de la versión anterior** | 8 000 | **Sí** |
| Cuerpo literal del resto, por pertinencia | 6 500 | No |
| Margen para la respuesta | 1 000 | — |

**Orden de poda cuando no cabe** — y nótese que ninguna de las cuatro salidas es resumir: (1) se recorta el bloque de cuerpo literal por pertinencia, que es recuperable con `memory.fetch`; (2) se retiran los bloques de capacidad menos relevantes; (3) se pasa a **modo direccionado puro** (restricciones + índice completo + herramienta de recuperación); (4) si el índice completo por sí solo no cabe, se **escala a un modelo de mayor ventana** mediante el traspaso del §A18-1 o se **trocea el trabajo** en unidades reanudables. Si nada de eso es posible, el sistema **se detiene y lo declara**. El contrato de salida, las restricciones y el índice completo **no se podan nunca**.

**Verificación mecánica.** Todo fragmento que el compilador inserte como memoria pasa por `assert_verbatim` (§18.4) contra el registro íntegro, con tolerancia de **cero caracteres**. Una paráfrasis aborta la composición con `SummaryDetected`, que es un fallo de programación y no una advertencia. Es lo que convierte «aquí no se resume» en una propiedad comprobable en lugar de una intención.

### 7.6 Integración con el debate popperiano

Afirmaciones: "el prompt P produce salida válida al primer intento en ≥ X % de los casos" y "el prompt P no induce alucinación de citas por encima de Y %". Evidencia admisible: resultados del banco de evaluación (§7.8). Refutación más potente: **un caso del banco donde el prompt falla de forma reproducible**, aportado por B con el `prompt_hash` exacto. Invocación: en cada cambio de versión de un prompt (regresión obligatoria antes de promover la versión).

### 7.7 Costos, latencia y recursos

El compilador de prompts es puro cómputo local: < 8 ms por render. Sobrecoste de contexto de los bloques fijos: ≈ 3 600 tokens por llamada (11 % de una ventana de 32 k). GBNF añade ≈ 4–9 % de latencia de generación y elimina el 100 % de los reintentos por sintaxis: el balance es netamente favorable. Bucle de reparación: coste medio observado objetivo ≤ 0,15 reintentos por llamada remota. **Salto del debate:** el renderizado no se debata; sí las versiones de prompt. **Caché:** los renders se cachean por `sha256(plantillas+variables)`; las gramáticas GBNF se compilan una vez por esquema y se cachean por `sha256(schema)`.

### 7.8 Calidad y pruebas: el banco de evaluación de prompts

Sin esto, los prompts se degradan sin que nadie lo note. `tests/prompts/bench/` contiene 120 casos con salida esperada: 30 de C decompilado (con la identidad real de la función conocida), 25 de topografía (con verdad de terreno del generador sintético), 25 de contraste normativo (con la relación anotada), 20 de HDL (con el contraejemplo formal conocido) y 20 de invención (con arte previo conocido).

| Métrica | Definición | Umbral |
|---|---|---|
| Adherencia al formato | % de respuestas válidas contra esquema **al primer intento** | ≥ 98 % local (GBNF), ≥ 90 % remoto |
| Tasa de alucinación de citas | % de citas que no existen literalmente | ≤ 0,5 % |
| Cobertura de `falsifier` | % de afirmaciones con condición de falsación concreta (evaluada por regla + juez) | ≥ 95 % |
| Detección de cobertura verbal | % de respuestas con lenguaje prohibido | ≤ 2 % |
| Exactitud de dominio | % de casos del banco resueltos correctamente | ≥ 80 % |
| `self_check_mismatch` | % de auto-verificaciones falsamente en verde | ≤ 3 % |

**Procedimiento de regresión:** se ejecuta `make prompt-bench` automáticamente cuando cambia cualquier fichero bajo `prompts/` o cuando cambia el modelo asignado a un rol. Si alguna métrica empeora más de 3 puntos porcentuales respecto de la versión anterior, la promoción se bloquea y se abre un hallazgo. Casos obligatorios adicionales: camino feliz, consenso entre agentes (los tres prompts sobre el mismo caso trivial deben converger), desacuerdo total (caso ambiguo diseñado: el Juez debe emitir `undecided` con acción, no un empate), y GUI bajo estrés (renderizado de 500 prompts en lote sin bloquear el bucle asyncio: ≤ 4 s).

### 7.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta | Estado |
|---|---|---|---|---|
| Plantilla con variable ausente | `jinja2.UndefinedError` (modo `StrictUndefined`) | Prompt roto | Fallo inmediato en compilación, nunca se envía | Seguro |
| Gramática GBNF inválida | error al cargar en `llama.cpp` | Sin restricción | Degradar a validación+reparación y registrar | Degradado |
| Modelo remoto se niega a una tarea técnica legítima | patrón de negativa + esquema no cumplido | Turno perdido | **Reenrutar a modelo local** y anotar `refusal_rerouted` | Operativo |
| Contexto desbordado pese a la poda | conteo previo | Truncamiento | Subdividir la unidad; nunca truncar evidencia citada | Operativo |
| Fallo parcial: `self_check` en verde con fallos reales | verificación mecánica | Confianza falsa | Registrar `self_check_mismatch`, bajar confianza y abrir hallazgo de calidad del prompt | Consistente |

### 7.10 Riesgos y mitigaciones

Degradación silenciosa de prompts al cambiar de modelo (alta/alto → banco de regresión obligatorio). Prompts demasiado largos que desplazan la evidencia (media/alto → presupuesto por bloque y fijación). Sobreajuste del banco (media/medio → 20 % de casos ocultos rotados cada versión). Tentación de escribir prompts para eludir políticas (media/alto → prohibido por §7.1, con revisión en el propio banco: un caso comprueba que ningún prompt del repositorio contiene instrucciones de elusión, mediante lista de patrones). Divergencia entre esquema y gramática (media/alto → ambas generadas del mismo JSON Schema, con prueba de equivalencia).

### 7.11 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA**: Jinja2 3.1, pydantic 2.8, `llama.cpp` con soporte GBNF, generador de gramáticas. Sin hardware ni cuentas.

### 7.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (base + tres roles + un dominio + validación) → v1 (los seis dominios, GBNF, reparación, auto-verificación) → completo (bloques de capacidad C01–C39, banco de 120 casos, regresión automática).

- **P7.a Compilador.** P7.a.1 plantillas y registro — **PV-7.a.1**: 100 % de renders con `StrictUndefined` sin error y `prompt_hash` estable entre ejecuciones. P7.a.2 presupuesto y poda — **PV-7.a.2**: con contexto artificialmente reducido, la evidencia citada y el contrato nunca se podan (100 casos).
- **P7.b Contrato de salida.** P7.b.1 generación de GBNF — **PV-7.b.1**: para los 7 esquemas, 500 generaciones locales con 100 % de validez sintáctica y de esquema. P7.b.2 reparación — **PV-7.b.2**: con salidas corruptas inyectadas, ≥ 90 % reparadas en ≤ 2 intentos.
- **P7.c Prompts de rol y dominio.** P7.c.1 los diez prompts — **PV-7.c.1**: cada uno pasa su subconjunto del banco con los umbrales de §7.8. P7.c.2 auto-verificación — **PV-7.c.2**: `self_check_mismatch` ≤ 3 %.
- **P7.d Regresión.** P7.d.1 `make prompt-bench` — **PV-7.d.1**: ejecuta los 120 casos en ≤ 25 min en Perfil A y bloquea la promoción ante caída > 3 puntos. P7.d.2 comprobación anti-elusión — **PV-7.d.2**: 0 coincidencias de patrones de elusión en todo `prompts/`.

Métricas de salida: adherencia ≥ 98 % local, alucinación de citas ≤ 0,5 %, cobertura de `falsifier` ≥ 95 %, y regresión ejecutándose en cada cambio.

---

## ÁREA 8 — Motor de ejecución multi-paso autónomo en vivo

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA** para acciones de software; **🟡/🔴** para las acciones físicas, que heredan los prerrequisitos del Área 9.

### 8.1 Propósito y alcance

Convierte veredictos en efectos sobre el mundo y, sobre todo, **verifica que el efecto ocurrió**. Es lo que separa este motor de un script: ninguna acción se da por buena porque "salió sin error"; cada una declara su postcondición y se comprueba. Cuando falla, el fallo real se clasifica y vuelve al BALTHASAR convertido en refutación formal, cerrando el bucle.

Queda fuera: qué hay que hacer (lo deciden las áreas de dominio y el Juez) y los protocolos de bajo nivel del hardware (Área 9).

**Consume:** Área 3 (aprobación), Área 0 (política de capacidades, instantáneas, planificador). **Alimenta:** Área 3 (evidencia empírica), Área 9 (ejecución física), Área 10 (aprobaciones y parada de emergencia).

### 8.2 Arquitectura

```
  acción propuesta (área de dominio)  ──► action.proposed
        │
        ▼
 ┌─────────────────────────┐  rechazo  ┌───────────────────────────┐
 │ JUEZ (CASPER) evalúa  │──────────►│ vuelve a B con motivo     │
 │ contra el acta y el R   │           └───────────────────────────┘
 └──────────┬──────────────┘
            │ aprobada  (R3 ⇒ además CONFIRMACIÓN HUMANA obligatoria)
            ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ PREFLIGHT: esquema · precondiciones · dry-run · espacio ·    │
 │ energía · análisis estático del artefacto · copia de seguridad│
 │  ⚠ punto de fallo: preflight falla ⇒ NO se ejecuta, vuelve a B│
 └──────────┬──────────────────────────────────────────────────┘
            ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ EJECUTOR AISLADO: stdout/stderr/exit/duración/artefactos     │
 │ + telemetría física durante la ejecución (Área 4/9)          │
 └──────────┬──────────────────────────────────────────────────┘
            ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ VERIFICACIÓN DE POSTCONDICIÓN (lógica Y física)              │
 │  ⚠ "exit=0" NO es verificación                               │
 └──────┬────────────────────────────────────┬─────────────────┘
     ok │                                fallo│
        ▼                                     ▼
 ┌──────────────┐                    ┌───────────────────────────┐
 │ artifact.    │                    │ CLASIFICADOR DE ERROR     │
 │ created      │                    │ sintaxis|compilación|link │
 └──────────────┘                    │ runtime|lógico|entorno|   │
                                     │ dispositivo|físico        │
                                     └────────────┬──────────────┘
                                                  ▼
                                     ┌───────────────────────────┐
                                     │ B convierte el fallo en   │
                                     │ REFUTACIÓN formal → ronda │
                                     └────────────┬──────────────┘
                                                  ▼
                                     ┌───────────────────────────┐
                                     │ ROMPEDOR DE BUCLES §8.5   │
                                     │ escala a humano con informe│
                                     └───────────────────────────┘
```

### 8.3 Ontología de acciones y radio de impacto

Enumeración exhaustiva de tipos de acción, agrupados, con su esquema de parámetros:

**Sobre archivos:** `fs.read{path, offset?, length?}` · `fs.write{path, content_ref, mode}` · `fs.move{src, dst}` · `fs.copy{src, dst}` · `fs.quarantine{path}` (sustituye a borrar) · `fs.mkdir{path}` · `fs.chmod{path, mode}` · `fs.archive{paths[], out}` · `fs.extract{archive, out}` · `fs.hash{path, algo}`.
**Sobre procesos:** `proc.spawn{argv[], cwd, env, timeout_s, capture}` · `proc.signal{pid, sig}` · `proc.wait{pid, timeout_s}` · `proc.elevate{catalog_op, args}` (sólo catálogo cerrado del broker).
**Sobre la red:** `net.http_get{url, headers, out}` · `net.download{url, out, expected_sha256?}` · `net.browser_capture{url, out, evidence:true}` · `net.socket_connect{host, port}` (sólo a `127.0.0.1` salvo política explícita).
**Sobre dispositivos USB/serie:** `usb.claim{vid, pid, iface}` · `usb.control{req...}` · `serial.open{port, baud, dtr, rts}` · `serial.write{handle, bytes}` · `serial.query{handle, cmd, expect_regex, timeout_ms}` · `adb.shell{cmd}` · `adb.push{local, remote}` · `adb.pull{remote, local}` · `mtp.copy{src, dst}`.
**Sobre el hardware físico:** `printer.stream_gcode{file, profile_id}` · `printer.command{gcode}` · `printer.pause{}` · `printer.resume{}` · `printer.abort{}` · `printer.estop{}` · `printer.set_temp{tool, celsius}` · `mcu.erase{target}` · `mcu.flash{image, programmer, verify:true}` · `mcu.dump{target, out}` · `mcu.reset{target}` · `fpga.load{bitstream, board}` · `motion.jog{axis, mm, feed}`.
**Sobre el escritorio:** `input.key{keys}` · `input.type{text}` · `input.click{x, y, button}` · `input.move{x, y}` · `window.focus{title_regex}` · `screen.capture{region?}`.
**Sobre el propio sistema:** `pkg.install{manager, name, version}` · `pkg.uninstall{...}` · `svc.create{...}` · `svc.start/stop{...}` · `registry.write{hive, key, value}` (Windows) · `sysconf.write{path, content}` (Linux) · `policy.modify{capability, scope, value}` · `app.update{channel}`.

Clasificación por radio de impacto:

| Radio | Definición | Ejemplos | Política de aprobación | Mecanismo de reversión |
|---|---|---|---|---|
| **R0 — Inerte** | Lectura pura, sin efectos | `fs.read`, `fs.hash`, `usb` descriptores, `screen.capture`, `serial.query` de sólo lectura (M105, M115) | Autónomo, sin registro individual (sólo agregado) | No necesita |
| **R1 — Reversible** | Escribe en el espacio de trabajo | `fs.write` bajo `workspace/`, `proc.spawn` de compilador, `net.download` a caché | Autónomo **con registro** | Instantánea previa (git embebido) + `snapshot.restore` |
| **R2 — Semi-reversible** | Modifica el sistema o el dispositivo, con copia de seguridad previa **verificada** | `mcu.flash` con dump previo válido, `pkg.install`, `registry.write`, `sysconf.write`, `svc.create`, `fpga.load` | Veredicto favorable del Juez **y** confirmación de que la copia existe y su hash valida | Restauración desde el dump/copia + comando de reversión registrado |
| **R3 — Irreversible o físicamente peligroso** | Borrado sin copia, OTP, fusibles, calentamiento, movimiento de ejes, alto voltaje, formateo, escritura de gestor de arranque | `printer.set_temp`, `motion.jog`, `printer.stream_gcode`, `mcu.erase` sin dump, escritura de fusibles, `fs` fuera del espacio de trabajo en rutas del sistema | **Confirmación humana explícita siempre.** Sin excepción y **sin modo "no volver a preguntar"** | No hay reversión: por eso exige humano |

### 8.4 Contratos e interfaces

```python
def propose(action: ActionSpec, *, round_id: RoundId, rationale: str) -> ActionId: ...
def judge_action(action_id: ActionId) -> ActionVerdict: ...
def preflight(action_id: ActionId) -> PreflightReport: ...
async def execute(action_id: ActionId) -> ExecutionRecord: ...
def verify_postcondition(action_id: ActionId, rec: ExecutionRecord) -> PostconditionResult: ...
def classify_error(rec: ExecutionRecord) -> ErrorClass: ...
def revert(action_id: ActionId) -> RevertResult: ...
def emergency_stop(reason: str) -> None: ...
```

Esquema de acción:

```json
{
  "action_id":"act_01J9…","kind":"mcu.flash","radius":"R2",
  "params":{"image":"cas://sha256:…","programmer":"stlink","target":"stm32f103c8","verify":true},
  "origin":{"area":9,"round_id":"rnd_…","claim_id":"clm3"},
  "preconditions":[{"kind":"backup_exists","ref":"cas://sha256:…"},
                   {"kind":"device_present","selector":"0483:3748"},
                   {"kind":"disk_free_mb","min":200}],
  "postconditions":[{"kind":"readback_hash_matches","ref":"cas://sha256:…"},
                    {"kind":"device_responds","probe":"swd_idcode","expect":"0x1ba01477"}],
  "revert":{"kind":"mcu.flash","params":{"image":"cas://sha256:<dump previo>"}},
  "budget":{"timeout_s":180,"max_retries":0}
}
```

Eventos: `action.proposed`, `action.approved`, `action.executed`, `action.failed`, `snapshot.created`, `estop.triggered`. Tablas: `action`, `execution_record`, `snapshot`, `revert_log` (DDL en §T3).

### 8.5 Algoritmos: el bucle cerrado, paso a paso

**A8-1 — Bucle cerrado completo.**
```
 1. El área de dominio propone una acción → evento action.proposed (con round_id y claim que la motiva)
 2. El Juez evalúa la acción contra el acta y su radio:
    2.1 ¿el claim que la motiva tiene outcome ∈ {survives, amended} con score ≥ 70? si no → rechazo
    2.2 ¿el radio declarado coincide con el que el clasificador calcula? si no → rechazo por
         'radio_infravalorado' (defensa contra una acción R3 disfrazada de R1)
    2.3 R2 ⇒ exigir precondición backup_exists verificada; R3 ⇒ marcar 'awaiting_human'
    2.4 emitir action.approved|action.failed{reason}
 3. PREFLIGHT (§8.6). Fallo → NO se ejecuta; el motivo vuelve a B como refutación de tipo 'completitud'
      o 'suposicion' según corresponda
 4. EJECUCIÓN en el ejecutor aislado:
    4.1 instantánea previa si R1/R2 (git embebido: commit del workspace + registro del hash)
    4.2 lanzar con ProcessHAL, límites de CPU/RAM/tiempo, cwd controlado, entorno mínimo
    4.3 capturar stdout, stderr, código de salida, duración, y la lista de artefactos nuevos por
         comparación de árbol antes/después
    4.4 si hay hardware implicado: registrar la telemetría física durante toda la ejecución
         (temperaturas, corriente, posición, progreso de capa) y adjuntarla al ExecutionRecord
 5. VERIFICACIÓN DE POSTCONDICIÓN — no basta "salió sin error":
      binario   → existe, tiene el formato esperado y ARRANCA (ejecución de humo con timeout)
      pieza     → la medición dimensional cae dentro de la tolerancia declarada
      MCU       → responde al ping tras el flasheo Y la lectura de vuelta coincide con el hash
      dictamen  → todas sus citas existen en el corpus (validador del Área 2)
      HDL       → la simulación pasa y la síntesis cierra la temporización declarada
      documento → el hash del artefacto coincide con el registrado y el visor lo abre
 6. FALLO ⇒ CLASIFICACIÓN (A8-2) ⇒ realimentación a B con: clase de error, mensaje recortado a lo
      relevante (primeras 40 líneas del error + las 10 líneas de contexto del fichero implicado),
      comando exacto, y traza; B formula la refutación formal contra la afirmación original de A
 7. nueva ronda (Área 3) y, si procede, nueva acción. Iterar hasta convergencia, presupuesto o
      rompedor de bucles
 8. caso límite: éxito lógico con fallo físico (flasheo "correcto" cuyo MCU no responde) ⇒ se trata
      como FALLO de clase 'físico', nunca como éxito
```

**A8-2 — Clasificador de error y enrutado.**

| Clase | Señal de detección | A dónde se enruta |
|---|---|---|
| `sintaxis` | El compilador/intérprete reporta error de parseo con fichero:línea | A (corrección directa, sin debate: R0 determinista) |
| `compilacion` | Error semántico del compilador (tipos, símbolos no declarados) | A con el fragmento de código y el error |
| `enlazado` | Símbolo indefinido, librería no encontrada | A + comprobación de dependencias del entorno |
| `runtime` | Excepción, señal (SIGSEGV=139), código de salida no nulo | B (refutación empírica) |
| `logico` | Compila y corre, pero la postcondición de resultado falla | B (la refutación más valiosa: la afirmación era falsa) |
| `entorno` | Herramienta ausente, versión incompatible, permiso denegado | Autorreparación: instalar/localizar la herramienta (acción R2) y reintentar una vez |
| `dispositivo` | Error USB/serie, dispositivo ausente, timeout de respuesta | Área 4 (rutina de reconexión) y luego B |
| `fisico` | Medición fuera de tolerancia, MCU sin responder, impresión fallida | B con la Evidencia física (tier 1, precedencia máxima) |

**A8-3 — Rompedor de bucles.**
```
1. huella de error: sha256(clase + fichero + línea + primeras 200 chars normalizadas del mensaje)
2. huella de corrección: sha256(diff normalizado aplicado por A)
3. disparadores (cualquiera):
   3.1 misma huella de error N=3 veces
   3.2 misma huella de corrección N=2 veces
   3.3 oscilación: la secuencia de huellas de estado contiene un ciclo de longitud ≤ 4 repetido 2 veces
   3.4 progreso nulo: la métrica objetiva no mejora en 3 iteraciones consecutivas
        métrica por dominio: nº de errores del compilador · nº de tests que pasan · desviación
        dimensional en mm · nº de divergencias en la traza · puntuación de conformidad
4. al dispararse: NO se reintenta una vez más. Se genera un informe de atasco con:
      historial de intentos, huellas, métrica por iteración, hipótesis descartadas, y la pregunta
      concreta que el humano debe responder para desbloquear
5. estado del trabajo: BLOCKED_ESCALATED; se libera el hardware y se conservan las instantáneas
```

**Presupuesto del bucle (valores por defecto, configurables por proyecto):** `max_iterations=8`, `max_wall_s=3600`, `max_tokens=400000`, `max_R2_actions=6`, `max_R3_actions=2` (y cada una exige humano). Al agotarse cualquiera: parada con informe, nunca continuación silenciosa.

**Decisiones formalizadas adicionales de esta área.**
**Decisión:** el borrado no existe como operación del sistema: `fs.quarantine` mueve a una zona de cuarentena con manifiesto — porque la irreversibilidad es el único error que no se puede corregir iterando.
*Descartado:* borrado con papelera del sistema operativo — depende del entorno y no deja registro consultable por el propio sistema.
**Decisión:** el radio declarado por el módulo se contrasta siempre con el que calcula el clasificador, y la discrepancia es motivo de rechazo — porque una acción R3 mal etiquetada como R1 es el vector de fallo más peligroso del motor.

### 8.6 Comprobaciones previas (preflight) por tipo de acción

| Tipo | Comprobaciones obligatorias antes de ejecutar |
|---|---|
| `fs.*` | Ruta dentro del espacio permitido; no coincide con la lista negra dura; espacio libre ≥ tamaño × 1,2; el destino no existe o su sobrescritura está declarada |
| `proc.spawn` | Binario existe, hash conocido o firmado por el instalador; argv sin metacaracteres no escapados; cwd dentro del proyecto; timeout declarado |
| `net.*` | URL en política; TLS válido; `expected_sha256` presente para descargas de binarios |
| `usb/serial` | Dispositivo presente y reclamado; ningún otro trabajo usa el handle; velocidad y paridad del perfil |
| `printer.stream_gcode` | **Análisis estático completo del G-Code (§9.B)**; perfil de máquina cargado; temperatura objetivo dentro del rango del perfil; filamento suficiente declarado; homing presente |
| `mcu.flash` | **Dump previo existente y con hash válido**; imagen verificada (formato, tamaño, checksum); programador presente; tensión de alimentación correcta si es medible |
| `input.*` | Ventana objetivo enfocada y con título esperado; captura previa para verificar el estado; capacidad `input.synthesize` concedida |
| `pkg.install` / `registry.write` / `sysconf.write` | Copia previa del estado (exportación de la clave, copia del fichero); broker disponible; comando de reversión construido y almacenado **antes** de ejecutar |
| Todas | Validación de esquema; simulación en seco cuando la herramienta la soporte (`--dry-run`, `-n`, `M111`/simulación de slicer); comprobación de energía cuando aplique (impresión larga: aviso si no hay SAI declarado) |

### 8.7 Registro de transacciones, reversión y parada de emergencia

**Diario de transacciones:** cada ejecución escribe `execution_record` con `{action_id, snapshot_before, argv, env_hash, stdout_ref, stderr_ref, exit_code, duration_ms, artifacts[], telemetry_ref, postcondition_result, revert_cmd}`. **Mecanismo de instantánea:** *Decisión:* control de versiones interno con `git` embebido (`pygit2` 1.15 sobre un repositorio propio en `workspace/.magigit/`, separado del git del usuario) — porque da diffs, restauración selectiva y coste incremental, y no interfiere con el repositorio que el usuario pueda tener.
*Descartado:* copia completa del directorio por acción — inviable con espacios de trabajo de decenas de GB.

**Interruptor de parada (E-STOP).** Atajo global `Ctrl+Alt+Shift+K` (registrado a nivel de SO por la GUI) **y** botón siempre visible en la barra superior. Ruta de código: `gui/src/estop.ts` → canal Tauri dedicado → `core/rpc/estop_channel.py`, que es un **hilo separado con su propio socket y su propia cola**, no el bucle asyncio principal — de modo que no depende de que el núcleo esté sano. Secuencia: (1) enviar `M112` por el puerto serie de toda impresora activa (escritura directa al descriptor, sin pasar por la cola de G-Code) y cortar calentadores con `M104 S0`/`M140 S0`; (2) matar el árbol de procesos de toolchain; (3) liberar todos los handles USB (`libusb_release_interface` + `libusb_close`); (4) cancelar inferencias en curso; (5) escribir `estop.triggered` en la auditoría con el motivo; (6) dejar el sistema en estado `SAFE` que exige confirmación humana para reanudar. **Garantía adicional:** si el proceso del núcleo no responde en 1,5 s, la GUI ejecuta directamente el corte serie a través de un binario auxiliar mínimo (`magi-estop`) que sólo sabe abrir puertos y enviar `M112`.

### 8.8 Integración con el debate popperiano

Afirmaciones: cada postcondición declarada es una afirmación falsable ("tras esta acción, el MCU responderá con IDCODE 0x1ba01477"). Evidencia admisible: `ExecutionRecord` completo, telemetría física, lectura de vuelta. Refutación más potente: **la ejecución misma** — es la refutación definitiva y automática; por eso el motor está diseñado para que el fallo real se convierta en refutación sin intervención. Invocación: obligatoria antes de toda acción R2/R3, y tras todo fallo.

### 8.9 Costos, latencia y recursos

Sobrecoste del preflight: 20–400 ms según tipo (el análisis estático de G-Code de 50 MB tarda ≈ 3,5 s). Instantánea git de un espacio de trabajo de 2 GB con pocos cambios: ≈ 300 ms. Verificación de postcondición: variable (una lectura de vuelta de 128 KB por SWD ≈ 6 s). Tokens: la clasificación de error es determinista (0 tokens); la formulación de la refutación por B cuesta ≈ 4 200 tokens. **Salto del debate:** acciones R0 y R1 con postcondición verificable mecánicamente y sin efecto fuera del espacio de trabajo (compilar, ejecutar un test) no pasan por el Juez; se ejecutan y sólo su resultado entra en el debate. **Caché:** los resultados de `proc.spawn` deterministas (compilación con las mismas entradas) se cachean por `sha256(argv+entradas+toolchain_version)`, lo que ahorra recompilaciones completas en el bucle.

### 8.10 Calidad y pruebas

| Caso | Criterio de éxito |
|---|---|
| Camino feliz | Compilar → ejecutar → postcondición verificada: 20/20 sin intervención |
| Binario que no compila | Error clasificado como `compilacion` y convertido en refutación en ≤ 1 iteración, 20/20 |
| Éxito lógico con fallo físico | Flasheo con lectura de vuelta divergente: clasificado `fisico` y tratado como fallo, 10/10 |
| Radio infravalorado | Acción R3 declarada como R1: rechazada por el Juez en 10/10 |
| R3 sin humano | Sin confirmación humana, la acción **nunca** se ejecuta, ni tras 24 h de espera, 10/10 |
| Bucle | Error idéntico 3 veces: escalada con informe, 0 reintentos adicionales, 10/10 |
| Reversión | 20 acciones R1/R2 revertidas: estado idéntico al previo por hash de árbol, 20/20 |
| E-STOP | Con impresión activa y 3 procesos pesados: todo detenido en ≤ 1,5 s; `M112` confirmado en el log serie, 10/10 |
| E-STOP con núcleo colgado | Núcleo bloqueado artificialmente: `magi-estop` corta igualmente en ≤ 2,5 s |
| Consenso/desacuerdo | Postcondición ambigua: C exige medición adicional (`undecided` + `required_action`), 10/10 |

### 8.11 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta | Estado |
|---|---|---|---|---|
| Preflight con falso negativo | acción segura rechazada | Trabajo detenido | Informe con la comprobación que falló y opción de anular manualmente (queda auditado) | Bloqueado, explicado |
| Instantánea imposible (disco lleno) | error de `pygit2` | Sin reversión | La acción R1/R2 **no se ejecuta** | Seguro |
| Proceso hijo zombi | supervisión | Recursos retenidos | Matar árbol; barrido de huérfanos | Recuperado |
| Postcondición no verificable (sin instrumento) | falta de sonda | Sin confirmación | La acción queda `unverified` y NO produce artefacto válido; se pide medición manual | Consistente |
| Fallo parcial: acción ejecutada, registro no escrito | reconciliación al abrir | Auditoría incompleta | Reconstruir desde el diario de proceso y marcar `audit_gap` | Consistente, señalado |
| E-STOP durante flasheo | evento | Dispositivo en estado desconocido | Marcar `integrity=UNKNOWN` y activar rutina de rescate del §9.D | Recuperable |

### 8.12 Riesgos, prerrequisitos y pasos verificables

**Riesgos:** acción destructiva por error del agente (media/crítico → radio, cuarentena en vez de borrado, lista negra dura, humano en R3); bucle infinito consumiendo recursos (alta/medio → rompedor de bucles y presupuesto); falsa confianza en `exit=0` (alta/alto → postcondiciones obligatorias); E-STOP que no funciona cuando hace falta (baja/crítico → ruta independiente del núcleo y prueba mensual automatizada); autorreparación de entorno que instala algo indeseado (media/medio → `pkg.install` es R2 con reversión y confirmación de la fuente).

**Prerrequisitos: 🟢 CONSTRUIBLE-YA** para todo lo de software (`pygit2` 1.15, ProcessHAL); **🟡/🔴** heredados del Área 9 para las acciones físicas.

- **P8.a Ontología y radio.** P8.a.1 catálogo de acciones — **PV-8.a.1**: las 60 acciones del §8.3 con esquema válido y clasificador de radio que coincide con la tabla en 60/60. P8.a.2 detección de radio infravalorado — **PV-8.a.2**: 20 intentos disfrazados, 20 rechazos.
- **P8.b Preflight.** P8.b.1 comprobaciones por tipo — **PV-8.b.1**: cada fila de §8.6 con al menos un test que falla cuando debe. P8.b.2 dry-run — **PV-8.b.2**: en las herramientas que lo soportan, se ejecuta y su fallo bloquea, 10/10.
- **P8.c Ejecución y verificación.** P8.c.1 captura completa — **PV-8.c.1**: stdout/stderr/exit/duración/artefactos registrados en 50/50 ejecuciones. P8.c.2 postcondiciones — **PV-8.c.2**: 0 artefactos válidos sin postcondición verificada (consulta SQL devuelve 0 filas).
- **P8.d Bucle.** P8.d.1 clasificador — **PV-8.d.1**: 8 clases, exactitud ≥ 0,95 sobre 200 fallos sembrados. P8.d.2 realimentación a B — **PV-8.d.2**: 20/20 fallos convertidos en refutación con mecanismo. P8.d.3 rompedor — **PV-8.d.3**: los 4 disparadores probados, 0 falsos negativos.
- **P8.e Seguridad.** P8.e.1 instantáneas y reversión — **PV-8.e.1**: 20/20 restauraciones con hash de árbol idéntico. P8.e.2 E-STOP — **PV-8.e.2**: ≤ 1,5 s con núcleo sano, ≤ 2,5 s con núcleo colgado, 10/10 cada escenario. P8.e.3 R3 — **PV-8.e.3**: 0 ejecuciones R3 sin confirmación humana registrada en auditoría.

**Hoja de ruta:** MVP (acciones de archivo y proceso + postcondiciones + reversión) → v1 (radio completo, preflight, clasificador, rompedor de bucles) → completo (acciones físicas, E-STOP redundante, auditoría encadenada). **Métricas de salida:** 0 artefactos sin postcondición, 100 % de R3 con humano, exactitud de clasificación ≥ 0,95, E-STOP dentro de plazo en ambos escenarios.

---

## ÁREA 9 — Fabricación física y diseño electrónico (USB Fabrication Lab)

**Estado de construibilidad del módulo: mixto y declarado por subárea** — 9.B (CAD y rebanado) y 9.C hasta GDSII: **🟢 CONSTRUIBLE-YA**; 9.A (impresora), 9.D (flasheo) y 9.E (instrumentación): **🟡 REQUIERE-PRERREQUISITO**; fabricación de ASIC real y PCB fabricada: **🔴 BLOQUEADO-SIN-HARDWARE**.

### 9.1 Propósito y alcance

Aquí el sistema toca el mundo real y los errores queman cosas. El nivel de detalle de protocolo es el de un firmware, no el de un diagrama de bloques: tramas, temporizaciones, control de flujo y recuperación. Cubre cinco frentes: control de impresora 3D por USB (9.A), generación programática de geometría y rebanado (9.B), diseño digital de procesadores hasta GDSII y validación en FPGA (9.C), dispositivos electrónicos completos con su firmware (9.D), y medición e iteración física (9.E).

Queda fuera: la decisión de qué fabricar (Áreas 3 y 11), el transporte USB de bajo nivel (Área 4, del que este módulo es cliente) y la aprobación de acciones (Área 8).

**Consume:** Área 4 (serie/USB), Área 8 (ejecución y radio), Área 3 (aprobación), Área 7 (prompts mecánico y HDL). **Alimenta:** Área 3 (evidencia física, la de mayor precedencia), Área 11 (prototipos), Área 10 (monitores).

### 9.2 Arquitectura

```
        intención (Área 3/11)                     especificación de ISA / circuito
              │                                              │
              ▼                                              ▼
 ┌─────────────────────────┐                    ┌──────────────────────────────┐
 │ 9.B CAD PARAMÉTRICO     │                    │ 9.C HDL  ·  9.D ESQUEMÁTICO  │
 │ CadQuery/OpenSCAD       │                    │ Verilog     KiCad/SKiDL      │
 └───────────┬─────────────┘                    └───────────┬──────────────────┘
   STEP/STL  │                                    RTL/netlist│
             ▼                                               ▼
 ┌─────────────────────────┐                    ┌──────────────────────────────┐
 │ VERIFICACIÓN GEOMÉTRICA │                    │ VERIFICACIÓN: sim · formal · │
 │ manifold·voladizos·caja │                    │ ERC · DRC · STA              │
 │ ⚠ falla ⇒ NO se imprime │                    │ ⚠ falla ⇒ NO se fabrica      │
 └───────────┬─────────────┘                    └───────────┬──────────────────┘
             ▼ G-Code                                       ▼ bitstream / GDSII / Gerber / .hex
 ┌─────────────────────────┐                    ┌──────────────────────────────┐
 │ ANÁLISIS ESTÁTICO GCODE │                    │ 9.D FLASHEO con DUMP PREVIO  │
 │ temp·volumen·velocidad  │                    │ y verificación por hash      │
 └───────────┬─────────────┘                    └───────────┬──────────────────┘
             ▼                                               ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ 9.A EMISOR DE G-CODE (máquina de estados, N+checksum, crédito por 'ok')    │
 │  ⚠ puntos de fallo: reinicio por DTR · desbordamiento de búfer · Resend    │
 └───────────┬───────────────────────────────────────────────────────────────┘
             ▼ telemetría (M105/M119) + progreso de capa
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ 9.E MEDICIÓN: calibre · sigrok · multímetro · INA226 · VLM con escala      │
 │  ⚠ la medición es EVIDENCIA tier 1: gana a todo argumento                  │
 └───────────┬───────────────────────────────────────────────────────────────┘
             ▼  desviación empaquetada como Measurement → BALTHASAR → nueva iteración
```

### 9.3 Contratos e interfaces

```python
# 9.A
def discover_printers() -> list[PrinterCandidate]: ...
def probe_printer(port: str) -> MachineProfile: ...
async def stream_gcode(profile: MachineProfile, path: Path, *, job: JobId) -> PrintResult: ...
def printer_command(profile: MachineProfile, gcode: str, *, expect: str | None) -> str: ...
async def monitor_printer(profile: MachineProfile) -> AsyncIterator[PrinterState]: ...
# 9.B
def solve_parameters(constraints: list[Constraint], template: CadTemplate) -> ParamSet: ...
def build_geometry(params: ParamSet, template: CadTemplate) -> GeometryArtifact: ...
def verify_geometry(g: GeometryArtifact, machine: MachineProfile) -> GeometryReport: ...
def slice_model(g: GeometryArtifact, profile_id: str) -> SliceResult: ...
def analyze_gcode(path: Path, machine: MachineProfile) -> GcodeReport: ...
# 9.C
def synthesize_hdl(src: HdlProject, target: SynthTarget) -> SynthReport: ...
def simulate(src: HdlProject, tb: TestbenchRef) -> SimReport: ...
def prove(src: HdlProject, props: list[Property]) -> FormalReport: ...
def place_and_route(netlist: Path, board: FpgaBoard) -> PnrReport: ...
def run_openlane(design: OpenlaneDesign) -> AsicReport: ...
# 9.D
def build_schematic(desc: CircuitDesc) -> KicadProject: ...
def export_fab(project: KicadProject) -> FabPackage: ...
def build_firmware(proj: FirmwareProject, target: McuTarget) -> BuildReport: ...
def dump_mcu(target: McuTarget, programmer: Programmer) -> DumpRef: ...
def flash_mcu(image: Path, target: McuTarget, programmer: Programmer) -> FlashReport: ...
# 9.E
def measure(instrument: InstrumentRef, channel: str, opts: dict) -> Measurement: ...
def compare_to_spec(m: list[Measurement], spec: SpecRef) -> DeviationReport: ...
```

Contrato de `Measurement` (evidencia física, tier 1): `{id, magnitude, value, unit, uncertainty, instrument{model, serial, calibration_date?}, method, timestamp_rfc3339, conditions{temp_c?, humidity?, supply_v?}, artifact_ref, operator: "system"|"human"}`. Una medición **sin** `uncertainty` e `instrument` es inadmisible como evidencia tier 1 y baja a tier 3.

Eventos propios: `print.layer{job, layer, total, z_mm, eta_s}`, `print.fault{job, kind, detail}`, `flash.progress{target, phase, pct}`, `measurement.recorded`. Tablas: `machine_profile`, `print_job`, `print_sample`, `geometry_artifact`, `hdl_run`, `fab_package`, `flash_record`, `measurement` (DDL en §T3).

### 9.4 Implementación

#### 9.A Control de impresora 3D por USB

**Detección e identificación.** Los VID/PID de las controladoras habituales (`1a86:7523` CH340, `10c4:ea60` CP2102, `0403:6001` FTDI, `2341:*` ATmega32U4 nativo, `0483:5740` STM32 CDC) son **ambiguos por naturaleza**: el mismo CH340 aparece en una impresora y en un Arduino cualquiera. *Decisión:* la identificación se resuelve **por interrogación de firmware, nunca por VID/PID** — se abre el puerto según A4-2, se envía `M115` y se clasifica por la respuesta.
*Descartado:* base de datos de VID/PID como fuente de verdad — produce falsos positivos peligrosos (enviar G-Code a un Arduino que controla otra cosa).

**Handshake serial completo (secuencia exacta).**
1. Abrir el puerto con `dtr=False, rts=False` **antes** de que el driver los active (en `pyserial`: `Serial(port, baudrate, dsrdtr=False, rtscts=False)` y, en Linux, `termios` con `HUPCL` desactivado). Motivo: en placas con ATmega y en muchas con STM32, la activación de DTR **reinicia el microcontrolador**; si no se controla, Marlin se reinicia al conectar y se pierden los primeros comandos. Ésta es la trampa clásica.
2. Si el perfil indica que el reinicio es necesario (bootloader tipo Arduino), pulsar DTR 100 ms y esperar 2,0 s.
3. Autodetección de baudios: probar `[115200, 250000, 57600, 230400, 500000]`; criterio de éxito: recibir en 3,0 s una línea con ≥ 90 % de caracteres imprimibles.
4. Esperar el banner `start` durante 10 s. Si no llega, enviar `\nM115\n` y esperar respuesta (algunas placas ya estaban arrancadas).
5. `M115` → parsear `FIRMWARE_NAME:`, `MACHINE_TYPE:`, `EXTRUDER_COUNT:` y el bloque `Cap:` (`Cap:EEPROM:1`, `Cap:AUTOREPORT_TEMP:1`, `Cap:EMERGENCY_PARSER:1`, etc.).
6. `M503` → leer la configuración (pasos/mm `M92`, aceleraciones `M201/M204`, velocidades máximas `M203`, offsets `M206`, PID `M301`, dimensiones si el firmware las reporta).
7. Construir el **Perfil de máquina (PM)**: `{firmware_family, version, dialect, volume_mm{x,y,z}, max_temp_hotend, max_temp_bed, max_feedrate, steps_per_mm, has_emergency_parser, has_autoreport, has_line_numbers, materials_allowed[]}`. El volumen, si el firmware no lo reporta, se pide al usuario una vez y se persiste.

**Dialectos y familias de firmware.**

| Rasgo | Marlin 2.x | Linaje RepRap (RepRapFirmware/Duet, Repetier, Smoothieware) | Klipper |
|---|---|---|---|
| Dialecto de G-Code | Marlin (superset de RS-274 con M-codes propios) | RepRap/RRF (M-codes propios, `M408` para estado en RRF; Repetier y Smoothieware con sus variantes) | Se controla por macros y comandos de host; el G-Code lo interpreta el host, no el MCU |
| Comando de identidad | `M115` | `M115` | `M115` (respondido por el host Klipper) |
| Estado y temperaturas | `M105` → `ok T:210.00 /210.00 B:60.00 /60.00 @:127 B@:80` | `M105` similar; en RRF además `M408 S0` devuelve JSON | Consulta de objetos por API, no por `M105` |
| Finales de carrera | `M119` → `x_min: open` … | `M119` equivalente | Consulta del objeto de estado |
| Numeración de línea y checksum | Sí (`Nnnn ... *chk`), con `Resend: N` | Sí | No aplica (transporte distinto) |
| Vía de control preferente | **Serie** | **Serie** (RRF también HTTP) | **HTTP/WebSocket vía Moonraker** |
| Parada de emergencia | `M112` (inmediata si `EMERGENCY_PARSER` está activo) | `M112` | `emergency_stop` por API |

*Decisión:* el PM detectado por `M115` selecciona el dialecto mediante una tabla de mapeo `firmware_family → dialect_module` en `profiles/printers/dialects/*.yaml`, y cada dialecto define: comando de estado, expresión regular de parseo, comandos bloqueantes, soporte de checksum y comando de parada — porque la diferencia entre familias no es cosmética y un `M105` mal parseado apaga la protección térmica.
*Descartado:* asumir Marlin siempre y "adaptarse sobre la marcha" — falla en silencio justo en los comandos de seguridad.

**Protocolo de streaming de G-Code (detalle de firmware).**
- Cada línea se envía como `N<n> <comando>*<checksum>\n`, donde el checksum es el **XOR byte a byte** de todos los caracteres desde `N` hasta el carácter anterior a `*` (inclusive el espacio), es decir `chk = 0; for c in linea: chk ^= ord(c)`.
- **Flujo de crédito basado en `ok`:** el firmware confirma cada línea con `ok` (a veces `ok N<n>` o con datos de temperatura si el auto-reporte está activo). El emisor mantiene una **ventana de comandos en vuelo** de tamaño `W`. Enviar sin esperar `ok` desborda el búfer de recepción de Marlin (típicamente 4 líneas de `MAX_CMD_SIZE`, configurable; el búfer de planificación de movimientos es otra cosa y no debe confundirse). *Decisión:* `W = 4` por defecto, elevable a 8 sólo si `M115` declara `Cap:BUFFER_SIZE` con valor mayor y una prueba de estrés lo confirma — porque un `W` alto mejora poco y arriesga corrupción.
- **`Resend: N`:** el firmware pide retransmitir desde la línea `N`. El emisor **debe** conservar un historial circular de al menos 64 líneas enviadas y reenviar desde `N` en orden, descartando el resto de la ventana. Tras 5 `Resend` en 100 líneas, se considera línea serie degradada y se baja el baudio al siguiente de la lista.
- **`busy: processing`:** el firmware avisa de que sigue vivo durante una operación larga; **reinicia el temporizador de inactividad** del emisor pero no cuenta como `ok`.
- **`echo:`** — mensajes informativos; se registran, no consumen crédito.
- **Comandos bloqueantes** (no siguen el flujo normal porque el firmware no responde `ok` hasta terminar): `M109` (esperar hotend), `M190` (esperar cama), `G28` (homing), `G29` (nivelado), `M600` (cambio de filamento), `M400` (esperar a vaciar la cola). Para ellos: vaciar la ventana (esperar todos los `ok` pendientes), enviar en solitario, y esperar con un timeout específico (por defecto 600 s para `M109`/`M190`, 300 s para `G28`/`G29`, y **sin timeout** para `M600`, que espera al humano) atendiendo `busy:` como latido.

**Máquina de estados del emisor:**

```
   [IDLE] --start--> [HANDSHAKE] --profile ok--> [READY]
                          |  fallo                    |  stream_gcode
                          v                           v
                      [FAILED]                  [STREAMING] --línea bloqueante--> [BLOCKING]
                                                  |   ^  |                            |
                              ok recibido ────────┘   |  | Resend:N                   | ok
                                                      |  v                            v
                                                 [RESENDING] ─────────────────────► [STREAMING]
                          [STREAMING] --M25/pausa--> [PAUSED] --M24/reanudar--> [STREAMING]
                          [cualquiera] --fallo térmico/M112--> [EMERGENCY] --confirmación humana--> [IDLE]
                          [STREAMING] --fin de fichero + M400 + ok--> [FINISHING] --> [DONE]
```

**Monitorización.** *Decisión:* si `M115` declara `Cap:AUTOREPORT_TEMP:1`, se activa `M155 S2` (auto-reporte cada 2 s) en vez de sondear — porque el sondeo compite con el streaming por la ventana de crédito. Si no lo declara, se sondea `M105` cada 2,0 s **intercalado sólo cuando la ventana tiene crédito libre**, y `M119` cada 30 s o antes/después de un homing. Expresiones regulares concretas:

```python
RE_TEMP = re.compile(r"T:(?P<t>-?\d+\.?\d*)\s*/(?P<tset>-?\d+\.?\d*)"
                     r"(?:\s*B:(?P<b>-?\d+\.?\d*)\s*/(?P<bset>-?\d+\.?\d*))?"
                     r"(?:.*?@:(?P<pwm>\d+))?(?:.*?B@:(?P<bpwm>\d+))?")
RE_OK      = re.compile(r"^ok(?:\s+N(?P<n>\d+))?")
RE_RESEND  = re.compile(r"^(?:Resend|rs):\s*N?(?P<n>\d+)", re.I)
RE_BUSY    = re.compile(r"^echo:busy:\s*(?P<what>\w+)")
RE_ERROR   = re.compile(r"^(?:Error|!!)\s*:?\s*(?P<msg>.*)")
RE_ENDSTOP = re.compile(r"^(?P<name>[xyz]_(?:min|max)|filament):\s*(?P<state>open|TRIGGERED)", re.I)
RE_POS     = re.compile(r"X:(?P<x>-?\d+\.?\d*)\s*Y:(?P<y>-?\d+\.?\d*)\s*Z:(?P<z>-?\d+\.?\d*)\s*E:(?P<e>-?\d+\.?\d*)")
```

Cada muestra alimenta `telemetry.sample` (canales `hotend_t`, `hotend_target`, `bed_t`, `bed_target`, `hotend_pwm`, `bed_pwm`, `z_pos`, `layer`) y se persiste en DuckDB para la gráfica de la GUI.

**Seguridad térmica y mecánica (detectores, umbral, acción escalonada).**

| Detector | Señal | Umbral | Acción |
|---|---|---|---|
| Descontrol térmico ascendente | `T` sube mientras `pwm=0` | +2,0 °C en 20 s con PWM nulo | Nivel 3 |
| Descontrol térmico por no calentar | PWM = 255 sostenido y `T` no sube | < +2,0 °C en 40 s con PWM ≥ 250 | Nivel 2 |
| Termistor desconectado | Lectura absurda | `T < 0 °C` o `T > 400 °C` o `T` constante bit a bit durante 30 s con PWM > 0 | Nivel 3 |
| Sobrepaso excesivo | `T > Tset + 15 °C` | 15 °C durante 5 s | Nivel 2 |
| Cama que no alcanza consigna | Tiempo | `> 600 s` sin llegar a `Tset − 2 °C` | Nivel 1 + aviso |
| Final de carrera que no dispara | `M119` tras `G28` | Eje sin `TRIGGERED` esperado | Nivel 3 antes de mover |
| Pérdida de comunicación | Sin `ok` ni `busy:` | > 15 s (o > 620 s en bloqueante) | Nivel 3 |
| Temperatura fuera del rango del material | Perfil | `T > max_temp_material + 10 °C` | Nivel 2 |

Acción escalonada: **Nivel 1** = pausa (`M25` si imprime desde SD, o parada de la cola del emisor) y aviso; **Nivel 2** = pausa + enfriado (`M104 S0`, `M140 S0`) + notificación; **Nivel 3** = **`M112`** (parada de emergencia) + corte de calentadores + registro del incidente + estado `EMERGENCY` que exige confirmación humana. En todos los casos se persiste un `print.fault` con la ventana de telemetría de los 60 s previos.

**Pausa, reanudación y aborto con estado preservado.** Al pausar: `M400` (vaciar cola), leer `M114` (posición), guardar `{x,y,z,e, feedrate, temps, línea_actual, N}`, elevar Z 5 mm (`G91 G1 Z5 F600 G90`), retraer 2 mm, y mantener temperaturas salvo pausa larga (> 10 min ⇒ bajar hotend 40 °C para evitar degradación). Al reanudar: restaurar temperaturas con `M109`/`M190`, volver a XY con `G1 F3000`, bajar Z, purgar (`G1 E2 F300`), y continuar desde `línea_actual`. **Corte de energía:** el estado se persiste por línea en `print_job.progress` con `fsync` cada 200 líneas; al volver, el sistema ofrece reanudación desde la capa registrada, advirtiendo explícitamente de que el éxito depende de que la pieza siga adherida y de que Marlin tenga `POWER_LOSS_RECOVERY` — si no lo tiene, se declara sin rodeos que la reanudación puede fallar. **`M600`:** se trata como bloqueante sin timeout, con estado `PAUSED_USER` y notificación del SO.

**Klipper — ruta alternativa.** *Decisión:* si `M115` (o el descubrimiento en red) indica Klipper, **no se habla serie**: el MCU está bajo control exclusivo del host Klipper y competir por el puerto es una fuente de fallos. Se usa **Moonraker** por HTTP/WebSocket — porque es la interfaz diseñada para eso, ofrece estado estructurado y evita el parseo frágil de texto.
Endpoints usados: `GET /printer/info`, `GET /printer/objects/list`, `GET /printer/objects/query?extruder&heater_bed&toolhead&print_stats&display_status`, `POST /printer/gcode/script?script=<gcode>`, `POST /printer/print/start?filename=`, `POST /printer/print/pause|resume|cancel`, `POST /printer/emergency_stop`, `POST /server/files/upload`. Suscripción por WebSocket JSON-RPC: método `printer.objects.subscribe` con `{objects:{extruder:["temperature","target","power"], heater_bed:[...], toolhead:["position","homed_axes"], print_stats:["state","filename","print_duration"], virtual_sdcard:["progress"]}}`, recibiendo `notify_status_update`. Esta ruta es preferible cuando existe porque entrega estado tipado, progreso real y parada de emergencia sin depender de expresiones regulares.

#### 9.B Generación programática de modelos 3D y rebanado

*Decisión:* **CadQuery 2.4 / build123d 0.5 (kernel OCCT)** como generador principal de geometría, y **OpenSCAD 2021.01** como generador secundario para piezas puramente constructivas — porque CadQuery da filetes y chaflanes reales y exporta STEP (indispensable para reutilizar la pieza en cualquier CAD y para el ensamblaje), mientras que OpenSCAD es trivial de generar por un modelo de lenguaje y basta para plantillas simples; se usa OpenSCAD cuando la pieza es unión/diferencia de primitivas sin redondeos, y CadQuery en todo lo demás.
*Descartado:* FreeCAD headless (`freecadcmd`) como generador principal — se conserva únicamente como **conversor y verificador** (importar STEP, medir volumen y masa, exportar mallas), porque su API de scripting es más pesada y menos estable entre versiones.

**De la intención a la geometría (pipeline).**
1. **Extracción de restricciones**: del encargo ("un soporte que aguante 2 kg y encaje en un perfil de 20×20") se extraen `{interface: perfil_aluminio_20x20, carga_N: 19.6, direccion: vertical, material: PLA|PETG, tolerancia_ajuste_mm: 0.20}` como JSON validado; toda restricción sin unidad se rechaza.
2. **Plantilla paramétrica**: selección de la plantilla de `cad/templates/` (p. ej. `bracket_l_profile.py`) cuyos parámetros cubren las restricciones.
3. **Resolución de parámetros**: cálculo de primer orden ejecutado en el sandbox del Área 2 — sección resistente mínima a partir de `σ_adm` del material (con factor de seguridad 2,0 por defecto y la reducción por anisotropía de impresión FDM declarada explícitamente, factor 0,6 en dirección Z), grosor de pared ≥ 3 perímetros × ancho de extrusión, y holguras.
4. **Verificación geométrica antes de imprimir** (`verify_geometry`, todas obligatorias): malla *manifold* (aristas con exactamente 2 caras), ausencia de auto-intersecciones, ausencia de triángulos degenerados, volumen > 0 y coherente con la densidad esperada, caja envolvente dentro del volumen de impresión del PM, grosor mínimo de pared ≥ 0,8 mm (medido por transformada de distancia sobre vóxeles de 0,2 mm), voladizos por encima del ángulo crítico (45° por defecto) cuantificados como porcentaje de área, y área de contacto con la cama ≥ 150 mm² o aviso de adhesión.
   Herramientas: `trimesh` 4.4 (topología, `is_watertight`, booleanas), `manifold3d` 2.x (booleanas robustas y reparación), `admesh` 0.98 (reparación de STL clásica), `numpy-stl` para E/S rápida.
5. **Rebanado por línea de comandos.** *Decisión:* **PrusaSlicer 2.8 en modo CLI** como rebanador principal y **CuraEngine 5.x** como secundario — porque PrusaSlicer acepta un `.ini` completo de perfil y sobrescrituras por CLI, y su informe de salida es fácil de parsear; CuraEngine se conserva para perfiles Cura que el usuario ya tenga.
   Comandos exactos:
   ```bash
   prusa-slicer --export-gcode --load "profiles/slicer/prusa/<perfil>.ini" \
                --nozzle-diameter 0.4 --filament-type PETG --temperature 240 --bed-temperature 80 \
                --layer-height 0.2 --fill-density 25% --perimeters 3 --support-material \
                --output "out/pieza.gcode" "out/pieza.stl"
   CuraEngine slice -v -j "profiles/slicer/cura/fdmprinter.def.json" \
                -s layer_height=0.2 -s infill_sparse_density=25 -s material_print_temperature=240 \
                -l "out/pieza.stl" -o "out/pieza.gcode"
   ```
   Parseo del informe: PrusaSlicer emite en el propio G-Code comentarios `; estimated printing time (normal mode) = 1h 12m 34s`, `; filament used [mm] = 3421.5`, `; filament used [g] = 10.21`, `; layer_height = 0.2`, y el número de capas se cuenta por `;LAYER_CHANGE` / `;LAYER:`. Todo ello va al `SliceResult` y a la estimación mostrada en la GUI.
6. **Análisis estático del G-Code antes de enviarlo** (`analyze_gcode`, bloqueante): temperaturas dentro del rango del PM y del material; todos los movimientos dentro del volumen (simulando la posición acumulada con soporte de `G90/G91`, `M82/M83`, `G92`); **ausencia de extrusión en frío** (ningún `E` positivo antes de que la temperatura objetivo se haya establecido con `M109`); velocidad de avance ≤ `max_feedrate` del PM; longitud total de filamento ≤ disponible declarado; presencia del preámbulo de homing (`G28` antes del primer movimiento XY); ausencia de `M302` (permitir extrusión en frío) salvo autorización explícita; y coherencia del `M104/M140` con el perfil. **Un G-Code que no pasa esto no se envía**: la acción es rechazada en el preflight del Área 8.
7. **Cola de impresión autónoma:** trabajos encolados con prioridad `PHYSICAL_SAFETY`, estimación de tiempo, ejecución desatendida con notificación por `print.layer`/`print.fault`, y entre impresiones: enfriado a temperatura de reposo, `G28 X Y` para liberar la zona, y espera de la confirmación de retirada de la pieza (que es humana y no se automatiza: el sistema **no** intenta expulsar piezas).

#### 9.C Procesadores y microprocesadores desde cero (flujo digital)

*Decisión:* **Verilog-2005 / SystemVerilog sintetizable** como lenguaje principal, con **GHDL 4.x** como ruta secundaria para VHDL — porque el conjunto de herramientas libres (Yosys, nextpnr, Verilator, Icarus) tiene su mejor soporte en Verilog, y GHDL cubre el caso de que el usuario aporte IP en VHDL (con `ghdl --synth` o el plugin `ghdl-yosys-plugin` para integrarlo en el mismo flujo).
*Descartado:* Chisel/SpinalHDL como lenguaje principal — potentes, pero añaden una cadena JVM/Scala y alejan el código del flujo de verificación formal directo.

Estructura del proyecto HDL:

```
hw/<diseño>/
├── rtl/            módulos sintetizables (.v/.sv), un módulo por fichero, mismo nombre
├── tb/             bancos de prueba cocotb (Python) y wrappers Verilog mínimos
├── formal/         propiedades SVA y ficheros .sby de SymbiYosys
├── model/          modelo de referencia en software (simulador de la ISA en Python)
├── synth/          scripts .ys de Yosys por objetivo
├── pnr/            restricciones (.pcf/.lpf/.xdc) y scripts de nextpnr
├── openlane/       config.json del diseño para el flujo ASIC
└── Makefile        objetivos: sim, lint, formal, synth, pnr, bit, prog, asic
```

Convenciones de nombres obligatorias: señales `snake_case`; sufijos `_i`/`_o`/`_io` para puertos; `_n` para activo-bajo; `clk`/`rst_n` para reloj y reset; registros con prefijo `r_`, combinacional con `c_`; parámetros en `MAYÚSCULAS`. Regla dura: un módulo, un fichero, un dominio de reloj declarado; los cruces de dominio requieren un sincronizador de dos biestables instanciado explícitamente y marcado con un comentario `// CDC`.

**Cómo el agente genera RTL a partir de una especificación de ISA:** la especificación (formato JSON: instrucciones con su codificación de bits, semántica en pseudocódigo, efectos sobre banderas, excepciones) se convierte en (1) un **modelo de referencia en Python** (intérprete instrucción a instrucción), (2) el **decodificador** generado a partir de la tabla de codificación, y (3) las **unidades funcionales**. El modelo de referencia se escribe **primero**, porque es el oráculo.

**Simulación y verificación.**

| Herramienta | Versión | Uso |
|---|---|---|
| Icarus Verilog | 12.0 | Simulación funcional rápida: `iverilog -g2012 -o sim.vvp rtl/*.v tb/tb_top.v && vvp sim.vvp` |
| Verilator | 5.0xx | Linting estricto (`verilator --lint-only -Wall -Wno-fatal`) y simulación en C++ de alto rendimiento para regresiones largas |
| cocotb | 1.9 | Bancos de prueba en Python — lo que permite al agente escribir pruebas potentes sin pelear con SystemVerilog: `make SIM=icarus TOPLEVEL=cpu MODULE=tb_cpu` |
| GTKWave 3.3 / Surfer 0.2 | — | Inspección de ondas (`.vcd`/`.fst`) cuando hay divergencia |
| SymbiYosys (sby) | 0.4x con Yices 2.6 / Boolector | Verificación formal: `sby -f formal/cpu.sby` con modos `bmc` (inducción acotada), `prove` (k-inducción) y `cover` |

Las tres clases de propiedad obligatorias por módulo: **seguridad** (`assert property (@(posedge clk) disable iff(!rst_n) !(wr_en && rd_en));`), **vivacidad acotada** (`assert property (@(posedge clk) req |-> ##[1:16] ack);`) y **cobertura** (`cover property (@(posedge clk) state == ST_DONE);`). La verificación formal es la forma más popperiana de refutar un diseño: el probador **busca activamente el contraejemplo**, y cuando lo encuentra devuelve la traza exacta, que entra en el debate como refutación empírica de máxima calidad.

**Cobertura y oráculo.** Co-simulación instrucción a instrucción: cocotb ejecuta el RTL y el modelo de referencia en paralelo, comparando el archivo de registros y las escrituras a memoria **tras cada instrucción retirada**. El primer punto de divergencia es la refutación (mismo mecanismo que el §5.5.6, deliberadamente). Cobertura funcional declarada por conjuntos: cada instrucción ejecutada al menos una vez, cada bandera puesta y borrada, cada excepción disparada, cada camino de bypass del pipeline ejercitado. Criterio: **cobertura funcional ≥ 95 %** y **0 divergencias en 10⁶ instrucciones aleatorias restringidas** antes de pasar a síntesis.

**Síntesis lógica.** Yosys 0.4x, con scripts concretos por objetivo:

```tcl
# synth/ice40.ys
read_verilog -sv rtl/*.v
hierarchy -check -top cpu_top
synth_ice40 -top cpu_top -json build/cpu.json
stat
tee -o build/timing_pre.txt ltp
```

Lectura del informe: `stat` da la utilización (LUTs, DFFs, BRAM, DSP); `ltp`/el informe de nextpnr da la ruta crítica y la frecuencia máxima estimada. **Qué hace el agente cuando no cierra la temporización** (procedimiento fijo, en este orden): (1) identificar la ruta crítica en el informe; (2) si es lógica combinacional larga, insertar registro de segmentación (pipeline) y ajustar el modelo de referencia y las pruebas; (3) si es un multiplexor ancho, rehacer como árbol balanceado; (4) si es memoria, mover a BRAM con registro de salida; (5) si nada de lo anterior, bajar la frecuencia objetivo y **declararlo** como resultado, no ocultarlo. Cada intento es una acción del Área 8 con su medición (frecuencia alcanzada) como postcondición.

**Emplazamiento y rutado / flujo ASIC.**
- **FPGA:** `nextpnr-ice40 --up5k --package sg48 --json build/cpu.json --pcf pnr/board.pcf --asc build/cpu.asc --freq 24 && icepack build/cpu.asc build/cpu.bin` (ECP5: `nextpnr-ecp5 ... --textcfg && ecppack`). Carga: `openFPGALoader -b <placa> build/cpu.bin`.
- **ASIC:** *Decisión:* **OpenLane 2** con **PDK Sky130A** como flujo principal y **GF180MCU** como segunda opción — porque Sky130A es el PDK abierto con más soporte, documentación y ejemplos reproducibles.
  Etapas nombradas y el informe que se lee en cada una: **síntesis** (Yosys → `synthesis/…stat.rpt`: área en µm², conteo de celdas); **floorplan** (`floorplan/…`: utilización objetivo, relación de aspecto, anillo de alimentación); **emplazamiento** (global y detallado → `placement/…: densidad, desplazamiento legalizado`); **árbol de reloj (CTS)** (`cts/…: skew, latencia de inserción`); **rutado** (global y detallado → `routing/…: violaciones de DRC de rutado, congestión`); **extracción parásita** (SPEF); **STA** (`signoff/…sta.rpt`: slack de setup y hold, WNS/TNS — criterio: WNS ≥ 0); **DRC** con **Magic 8.3.x** y **KLayout 0.29** (criterio: 0 violaciones); **LVS** con **netgen 1.5.x** (criterio: netlists equivalentes, 0 discrepancias); salida **GDSII**.

**Validación en FPGA antes de fabricación.** Placas objetivo concretas y baratas: **iCEBreaker (iCE40 UP5K)** ≈ 70 USD; **ULX3S (ECP5 85F)** ≈ 100–150 USD; **Colorlight i5/i9 (ECP5)** ≈ 25–40 USD como opción más económica; **Tang Nano 9K (GOWIN GW1NR-9)** ≈ 20 USD. Cadena completa: `yosys → nextpnr → icepack/ecppack/gowin_pack → openFPGALoader`. Instrumentación en placa para que la telemetría real vuelva al debate: (a) **analizador lógico integrado** — un módulo `magi_ila.v` propio con búfer circular en BRAM, disparo por condición y volcado por UART; (b) **UART de depuración** a 1 Mbaud con protocolo de tramas `[0xA5][len][payload][crc16]`; (c) contadores de rendimiento (ciclos, instrucciones, fallos de caché) leídos periódicamente. Esos datos entran como `telemetry.sample` y como `Measurement`.

**Marca de realidad (explícita).** Todo el flujo **hasta GDSII y su validación en FPGA es 🟢 CONSTRUIBLE-YA**: síntesis, emplazamiento, rutado, CTS, STA, DRC, LVS y el GDSII final se producen y se verifican con software libre en la máquina del usuario, sin gastar un céntimo. **El tape-out real es 🔴 BLOQUEADO-SIN-HARDWARE/SIN-DINERO**: fabricar silicio cuesta miles de dólares y meses de espera incluso por lanzaderas multiproyecto; el plan no lo incluye en ninguna fase y lo declara como frontera. La validación sustitutiva es la FPGA, cuyo coste está en el rango de decenas de dólares y es opcional.

#### 9.D Dispositivos electrónicos completos con su software

**Diseño de PCB por código.** *Decisión:* **KiCad 8.x** con su CLI, y **SKiDL 1.2** para describir el netlist en Python — porque permite generar el esquemático de forma programática y determinista, y KiCad 8 expone `kicad-cli` para todo el flujo de salida sin abrir la interfaz.
*Descartado:* manipular directamente los ficheros s-expression con `kicad-skip` como vía principal — se conserva sólo para retoques puntuales (mover una huella, cambiar un valor) porque es frágil ante cambios de formato.

Flujo completo y comandos:
```bash
python3 hw/pcb/<diseño>/netlist.py           # SKiDL: genera <diseño>.net y el ERC de SKiDL
kicad-cli sch export netlist  --output build/<d>.net  hw/pcb/<d>/<d>.kicad_sch
kicad-cli sch export pdf      --output build/<d>-sch.pdf hw/pcb/<d>/<d>.kicad_sch
kicad-cli sch erc             --output build/<d>-erc.rpt --severity-error hw/pcb/<d>/<d>.kicad_sch
# emplazamiento: script propio de colocación por grupos funcionales + revisión humana (🟡)
java -jar tools/freerouting.jar -de build/<d>.dsn -do build/<d>.ses -mp 100   # autorouter por CLI
kicad-cli pcb drc             --output build/<d>-drc.rpt --severity-error hw/pcb/<d>/<d>.kicad_pcb
kicad-cli pcb export gerbers  --output build/gerbers/ --layers F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts hw/pcb/<d>/<d>.kicad_pcb
kicad-cli pcb export drill    --output build/gerbers/ --format excellon --excellon-separate-th hw/pcb/<d>/<d>.kicad_pcb
kicad-cli pcb export pos      --output build/<d>-cpl.csv --format csv --units mm --side both hw/pcb/<d>/<d>.kicad_pcb
kicad-cli pcb export step     --output build/<d>.step hw/pcb/<d>/<d>.kicad_pcb
kicad-cli sch export bom      --output build/<d>-bom.csv --fields "Reference,Value,Footprint,MPN,Supplier,SupplierPN" hw/pcb/<d>/<d>.kicad_sch
```
Salidas de fabricación empaquetadas: **Gerber X2** (con atributos), **taladro Excellon** (metalizados y no metalizados separados), **posiciones de componentes (CPL)** en mm con lado, **BOM** con referencia de proveedor, y `README-fab.txt` con espesor, número de capas, acabado y color; todo en un `.zip` listo para un fabricante. Verificación previa obligatoria con `gerbv` 2.10 (render de cada capa a PNG para inspección visual automatizada: comparación de la capa de cobre con la esperada por área) y el DRC de KiCad en modo comprobación (0 errores para poder empaquetar).

**Firmware desde cero.** Toolchains por familia, con versión:

| Familia | Toolchain | Ejemplo de invocación |
|---|---|---|
| AVR (ATmega/ATtiny) | `avr-gcc` 14.x + `avr-libc` 2.2 | `avr-gcc -mmcu=atmega328p -Os -DF_CPU=16000000UL -o fw.elf main.c && avr-objcopy -O ihex fw.elf fw.hex` |
| ARM Cortex-M | `arm-none-eabi-gcc` 13.x (Arm GNU Toolchain) | `arm-none-eabi-gcc -mcpu=cortex-m3 -mthumb -T stm32f103.ld -o fw.elf ...` |
| 8051 / STM8 | SDCC 4.4 | `sdcc -mmcs51 --code-size 8192 main.c` |
| RISC-V | `riscv64-unknown-elf-gcc` 13.x | `riscv64-unknown-elf-gcc -march=rv32imc -mabi=ilp32 -T link.ld -o fw.elf ...` |
| Capa unificada | **PlatformIO Core 6.x** | `pio run -e nucleo_f103rb`, `pio run -t upload`, `pio pkg install` |

*Decisión:* PlatformIO Core 6.x como capa de gestión unificada de proyectos, dependencias y placas, con los toolchains anteriores accesibles también de forma directa — porque resuelve la instalación reproducible de cadenas y placas sin que el usuario configure nada, y su `platformio.ini` es un contrato versionable.

Estructura del proyecto de firmware: `fw/<proyecto>/{src/, include/, lib/, test/, platformio.ini, linker/*.ld, Makefile}`. Mapa de memoria: el script de enlazado se genera desde el `McuTarget` (FLASH origen/tamaño, RAM origen/tamaño, tamaño de pila y de montículo declarados) y el sistema **verifica tras compilar** con `arm-none-eabi-size` que `.text+.rodata+.data ≤ FLASH` y `.data+.bss+pila+montículo ≤ RAM`, con un margen mínimo del 10 % — un firmware que no deja margen se rechaza. **Pruebas unitarias en el anfitrión:** la lógica pura (protocolos, máquinas de estado, cálculos) se compila nativamente con **Unity 2.6 / Ceedling 1.0** y se ejecuta en el PC (`pio test -e native`), separando la lógica del acceso a registros mediante una capa HAL de firmware; criterio: cobertura de la lógica pura ≥ 80 % antes de flashear.

**Flasheo por USB.** Para cada programador: comando exacto, verificación posterior **obligatoria** (lectura de vuelta y comparación de hash) y rescate.

| Programador | Comando de volcado previo | Comando de escritura | Verificación | Rescate |
|---|---|---|---|---|
| `avrdude` 7.3 (AVR/Arduino) | `avrdude -c arduino -p m328p -P <port> -b 115200 -U flash:r:dump.hex:i` | `avrdude -c arduino -p m328p -P <port> -b 115200 -U flash:w:fw.hex:i` | `-U flash:r:back.hex:i` + comparación de hash del binario normalizado | Reflashear el bootloader con un programador ISP (USBasp/Arduino as ISP) — **prerrequisito 🟡** |
| `dfu-util` 0.11 (DFU) | `dfu-util -a 0 -s 0x08000000:0x10000 -U dump.bin` | `dfu-util -a 0 -s 0x08000000:leave -D fw.bin` | `-U back.bin` + hash | Entrar a DFU por BOOT0/pines o por comando; si el bootloader se dañó, recuperación por SWD |
| `OpenOCD` 0.12 (SWD/JTAG: ST-Link, CMSIS-DAP, FT2232) | `openocd -f interface/stlink.cfg -f target/stm32f1x.cfg -c "init; halt; dump_image dump.bin 0x08000000 0x10000; exit"` | `... -c "program fw.elf verify reset exit"` | `verify` integrado + `dump_image` y hash | Reconexión bajo reset (`connect_assert_srst`), borrado de masa, y desbloqueo si hay protección de lectura |
| `esptool.py` 4.8 (ESP32/ESP8266) | `esptool.py --port <p> read_flash 0 0x400000 dump.bin` | `esptool.py --port <p> --baud 460800 write_flash 0x1000 fw.bin` | `verify_flash 0x1000 fw.bin` | Modo descarga por GPIO0 a masa durante el reset |
| `stm32flash` 0.7 (bootloader serie) | `stm32flash -r dump.bin -S 0x08000000:65536 <port>` | `stm32flash -w fw.bin -v -g 0x0 <port>` | `-v` integrado + hash | BOOT0 alto y reset |
| `openFPGALoader` 0.12 | `openFPGALoader -b <placa> --dump-flash -o dump.bin` | `openFPGALoader -b <placa> -f build/cpu.bin` | Lectura de vuelta y hash | Carga volátil a SRAM (`-m`) para recuperar sin tocar la flash |

**Volcado previo (regla dura).** Antes de escribir, se lee y se guarda el contenido original con su hash en el CAS. **Sin volcado válido, la acción es R3** y exige confirmación humana explícita, con el texto llano: *"No se ha podido leer el contenido actual del dispositivo. Si esta escritura falla, no habrá forma de restaurar el estado anterior."* Con volcado válido, la acción es R2 y se aprueba por el Juez con la precondición `backup_exists` verificada por hash.

#### 9.E Medición, instrumentación y el bucle de iteración física

**El "multímetro virtual", hecho real — tres vías, todas especificadas:**
1. **Multímetro USB/serie real con protocolo conocido.** Familias soportadas: UNI-T UT61E (protocolo de 14 bytes por lectura sobre puente HID/serie), Owon (serie a 19200 8N1 con trama de texto), y cualquier instrumento con salida serie documentada. Implementación: parser por perfil en `profiles/instruments/*.yaml` con `{trama, longitud, campos, escala, unidades, tasa}`; cada lectura produce un `Measurement` con `uncertainty` tomada de la especificación de exactitud del instrumento (por ejemplo ±(0,1 % + 2 dígitos)). **🟡 Prerrequisito: poseer el multímetro con interfaz** (≈ 40–70 USD si se compra; no es necesario para el resto del sistema).
2. **`sigrok` 0.5.x / `sigrok-cli` 0.7.2 como capa universal** para analizadores lógicos y osciloscopios económicos (clones de Saleae con `fx2lafw`, DSLogic, Hantek). Captura por CLI: `sigrok-cli -d fx2lafw --config samplerate=8m --samples 8m -o cap.sr`, y **decodificadores de protocolo invocados automáticamente**: `sigrok-cli -i cap.sr -P uart:rx=D0:baudrate=115200 -A uart=rx-data`, `-P i2c:scl=D0:sda=D1 -A i2c=address-read:data-read:data-write`, `-P spi:clk=D0:mosi=D1:miso=D2:cs=D3`, `-P can:can_rx=D0:bitrate=500000`. La salida decodificada se convierte en `Evidence` con marca de tiempo. **🟡 Prerrequisito: un analizador lógico** (clon de 8 canales ≈ 8–15 USD; DSLogic ≈ 100 USD).
3. **Telemetría del propio circuito** (la vía **🟢 sin instrumento externo** cuando el diseño la incorpora): sensor **INA219/INA226** de corriente y tensión por I²C, termistores NTC leídos por ADC, y encoders; el firmware los reporta por serie con el protocolo de tramas de §9.C, y el núcleo los convierte en `telemetry.sample` y `Measurement`. Es la vía preferida porque no exige comprar nada más allá del propio circuito que se está construyendo.

**Medición dimensional de la pieza impresa.** (a) **Entrada manual del calibre** — el sistema presenta el plan de verificación (qué cota, dónde, valor nominal, tolerancia) y el usuario introduce el valor; incertidumbre por defecto ±0,02 mm para un calibre digital de 0,01 mm de resolución. (b) **Vía automatizable**: fotografía cenital de la pieza junto a una **referencia de escala** impresa por el propio sistema (un patrón de calibración de 40,00 mm con marcas fiduciales), analizada por el VLM y por el detector de bordes del Área 1; la escala se obtiene de la referencia y la cota del contorno segmentado. **Precisión honesta declarada:** con una cámara de teléfono a 25 cm y la referencia en el mismo plano, el error típico es de **±0,3 mm**, dominado por la distorsión y por la determinación del borde; es útil para detectar desviaciones groseras (encogimiento, elephant's foot, error de escala) y **no sustituye al calibre** para tolerancias de ±0,1 mm. El sistema lo declara en el informe y nunca marca una cota como conforme por foto si la tolerancia es menor que ±0,5 mm.

**El bucle de iteración física, completo:**
```
 diseñar (9.B/9.C/9.D)
   → verificar (geometría · ERC · DRC · simulación · formal · análisis de G-Code)
     → fabricar (imprimir | compilar+flashear | cargar bitstream)
       → medir (dimensional · eléctrica · funcional · térmica)
         → comparar contra la especificación
           → si desvía: empaquetar la desviación como EVIDENCIA FÍSICA (Measurement, tier 1)
             → BALTHASAR formula la refutación ('empirica', con el mecanismo físico)
               → MELCHIOR corrige el diseño PARAMÉTRICO (no la pieza: el parámetro)
                 → CASPER aprueba la reejecución (R2/R3 según el caso)
                   → repetir
```
**Criterio de convergencia:** (a) todas las cotas del plan de verificación dentro de tolerancia ⇒ éxito; (b) **N=3 iteraciones sin mejora** de la métrica objetiva (suma de desviaciones absolutas normalizadas por tolerancia) ⇒ escalada a humano con el historial completo; (c) presupuesto de material o de tiempo agotado ⇒ parada con informe. Cada iteración registra `{iteration, params, deviations[], cost_material_g, cost_time_s}` para que la tendencia sea visible en la GUI.

**Integración explícita con el Área 8 — postcondición física de cada acción del catálogo:**

| Acción | Postcondición **física** verificada |
|---|---|
| `printer.stream_gcode` | La impresión termina sin `print.fault`, el peso estimado coincide con el filamento consumido ±8 %, y **la pieza pasa su plan de verificación dimensional** |
| `printer.set_temp` | La temperatura medida alcanza la consigna ±3 °C en el tiempo esperado |
| `mcu.flash` | Lectura de vuelta con hash idéntico **y** el MCU responde al ping/IDCODE **y** el firmware emite su banner por UART en ≤ 3 s |
| `mcu.erase` | Lectura devuelve el patrón de borrado (0xFF) en el 100 % del rango |
| `fpga.load` | El diseño responde por su UART de depuración y los contadores avanzan |
| `motion.jog` | `M114` reporta la posición esperada ±0,1 mm y ningún final de carrera se disparó inesperadamente |
| `mcu.dump` | El dump tiene el tamaño exacto del rango y su relectura produce el mismo hash |

Un flasheo "exitoso" cuyo MCU no responde **es un fallo**; una impresión "completada" cuya pieza no encaja **es un fallo**. Esta regla está codificada en `verify_postcondition` y no admite excepción.

**Seguridad física.**
- **Acciones que nunca se ejecutan sin humano presente y confirmando (lista cerrada):** primera puesta en marcha de una impresora recién perfilada; cualquier `printer.set_temp` por encima de 260 °C; `G29`/nivelado en una máquina sin `PROBE` verificado; escritura de fusibles de un MCU; carga de bitstream a una FPGA que controle potencia; cualquier acción sobre un circuito con tensión de red; `mcu.erase` sin dump previo; y la reanudación tras un `EMERGENCY`.
- **Límites duros cableados en la configuración** (`config/safety.yaml`, no editables por el agente, sólo por el usuario y con confirmación): `max_hotend_c: 260`, `max_bed_c: 110`, `max_chamber_c: 60`, `max_current_a: 5.0`, `max_heater_on_without_progress_s: 300`, `max_print_hours: 24`, `max_jog_mm: 50`. El agente puede pedir menos, nunca más; una petición por encima se rechaza en preflight con `SAFETY_LIMIT`.
- **Temporizador de hombre muerto:** el núcleo envía a la impresora un `M105` (o el auto-reporte) cada 2 s; el emisor mantiene además un vigilante independiente que, si no ve actividad del núcleo durante 20 s con calentadores encendidos, ejecuta directamente `M104 S0`/`M140 S0` y luego `M112`. Se implementa en el mismo binario auxiliar `magi-estop` del §8.7, que corre como proceso hermano y comparte sólo el descriptor del puerto y un latido por memoria compartida — de modo que **no depende de que el núcleo esté sano**.

### 9.5 Algoritmos

**A9-1 — Emisor de G-Code con crédito y retransmisión.**
```
 1. estado: N=1, ventana=[], historial=deque(maxlen=64), credito=W(=4)
 2. mientras queden líneas o ventana no vacía:
 3.   mientras credito>0 y hay línea siguiente L y L no es bloqueante:
 3.1     s := f"N{N} {L}"; chk := XOR de todos los bytes de s; enviar s+f"*{chk}\n"
 3.2     historial.append((N,s)); ventana.append(N); N+=1; credito-=1
 4.   si la línea siguiente es bloqueante: esperar a que ventana esté vacía, enviar sola con su
        timeout específico, atendiendo 'busy:' como latido
 5.   leer línea de respuesta r con timeout de 15 s:
 5.1     r ~ '^ok'          → ventana.popleft(); credito+=1
 5.2     r ~ 'Resend: N(k)' → descartar ventana; reenviar desde k usando historial; N:=k+…;
                              contador_resend+=1; si contador_resend>5 en 100 líneas → bajar baudio
 5.3     r ~ 'busy:'        → reiniciar temporizador, no tocar crédito
 5.4     r ~ 'echo:'        → registrar
 5.5     r ~ 'Error|!!'     → clasificar; si es térmico o de endstop → nivel de seguridad y M112
 5.6     timeout            → 3 reintentos de sondeo con M105; luego fallo de comunicación (Nivel 3)
 6. al terminar: enviar M400 y esperar 'ok'; luego secuencia de fin (apagar calentadores, home XY)
 7. caso límite: el firmware responde 'ok' de más (algunas versiones) → tolerar crédito > W sin
        superar W en el envío; nunca aumentar la ventana por encima de W
 8. complejidad O(n) en líneas; memoria O(64) líneas de historial
```

**A9-2 — Análisis estático de G-Code (bloqueante antes de enviar).**
```
 1. estado: pos={x:0,y:0,z:0,e:0}, absoluto=True, e_absoluto=True, temp_objetivo={hotend:0,bed:0},
       homed={x:False,y:False,z:False}, filamento_total=0, max_feed=0
 2. por cada línea (ignorando comentarios):
 2.1  G90/G91 → absoluto; M82/M83 → e_absoluto; G92 → redefinir origen (¡también de E!)
 2.2  G28 → homed[ejes]=True y pos=origen del PM
 2.3  G0/G1 → calcular destino; SI extruye (ΔE>0):
         - comprobar temp_objetivo.hotend ≥ min_extrusion_temp del material  → si no: ERROR extrusión en frío
         - acumular filamento_total += ΔE
      comprobar destino dentro de volumen del PM (con margen 0,5 mm) → si no: ERROR fuera de volumen
      comprobar F ≤ max_feedrate → si no: ERROR velocidad
      si no homed[eje] y hay movimiento en ese eje → ERROR movimiento sin homing
 2.4  M104/M109/M140/M190 → actualizar objetivo; comprobar contra max_temp del PM y del material
 2.5  M302 (permitir extrusión en frío) → ERROR salvo autorización explícita registrada
 3. al final: filamento_total ≤ disponible_declarado → si no: ADVERTENCIA bloqueante
 4. salida: GcodeReport{errores[], advertencias[], estadísticas{capas, altura_max, filamento_mm,
       tiempo_estimado_s, temp_max}}; UN SOLO error impide el envío
 5. complejidad O(n) sobre las líneas; 50 MB de G-Code ≈ 3,5 s
```

**A9-3 — Bucle de convergencia dimensional.**
```
1. spec := plan de verificación {cota_i, nominal_i, tol_i, método_i}
2. medir → d_i := (medido_i − nominal_i); métrica J := Σ |d_i| / tol_i
3. si todas |d_i| ≤ tol_i → CONVERGE
4. si no: diagnóstico por patrón (regla determinista antes de gastar tokens):
     todas las cotas externas grandes por igual  → escala/expansión térmica → corregir factor de escala
     agujeros pequeños por igual                 → compensación de holgura → aumentar diámetro nominal
     primera capa ancha                          → 'pata de elefante' → chaflán inferior 0,3 mm
     una sola cota fuera                         → error de modelado → revisar la fórmula de ese parámetro
     dispersión aleatoria                        → problema de proceso (mecánica) → calibrar, no rediseñar
5. aplicar la corrección al PARÁMETRO, regenerar geometría, verificar, reimprimir
6. si J no mejora ≥ 10 % en 3 iteraciones → ESCALAR a humano con el historial y el diagnóstico
```

### 9.6 Integración con el debate popperiano

Afirmaciones emitidas: "esta pieza soporta 2 kg con factor de seguridad 2", "este G-Code es seguro para esta máquina", "este módulo HDL cumple la propiedad P", "este firmware cabe en la memoria y arranca", "la corriente de reposo será < 5 mA". Evidencia admisible: verificación geométrica, informe del rebanador, informe de STA/DRC/LVS, contraejemplo o prueba de SymbiYosys, y **medición física con instrumento e incertidumbre** (tier 1). Refutación más potente: **la medición que contradice** — la pieza que no encaja, el contraejemplo formal, la lectura de vuelta que no coincide, la corriente medida que triplica la estimada. Invocación: antes de toda acción R2/R3 (imprimir, flashear, cargar bitstream, calentar) y después de cada medición que se desvíe.

### 9.7 Costos, latencia y recursos

Generación CAD: 0,3–4 s (CadQuery) por pieza. Verificación geométrica: 0,5–6 s según densidad de malla. Rebanado: 3–40 s. Análisis estático de G-Code: ≈ 70 ms/MB. Impresión: horas (trabajo desatendido, `PHYSICAL_SAFETY`). Simulación cocotb de 10⁶ instrucciones: 4–25 min con Verilator, 1–6 h con Icarus (por eso Verilator para regresiones). SymbiYosys `prove` con k-inducción: segundos a horas según el diseño; presupuesto por defecto 900 s con `--timeout`. Yosys+nextpnr en iCE40 UP5K: 20 s–4 min. **OpenLane 2 sobre Sky130A: 30 min–6 h y 8–16 GB de RAM** — ocupa `TOOLCHAIN_HEAVY` en exclusiva y en Perfil B exige descargar el VLM. KiCad CLI: segundos; freerouting: 1–20 min. Compilación de firmware: 2–30 s. Flasheo: 2–60 s; lectura de vuelta de 128 KB por SWD ≈ 6 s. Tokens: el diseño paramétrico consume ≈ 5 000 de entrada y 2 500 de salida por iteración; el debate físico ≈ 25 000 por ronda. **Salto del debate:** verificaciones deterministas (DRC, ERC, análisis de G-Code, `size`) no se debaten: se ejecutan y su resultado es evidencia. **Caché:** geometría por `sha256(params+plantilla+versión_cadquery)`; G-Code por `sha256(STL+perfil+versión_slicer)`; síntesis por `sha256(RTL+script+versión_yosys)`; nada relacionado con hardware físico se cachea (el mundo cambia).

### 9.8 Calidad y pruebas

| Caso | Criterio de éxito |
|---|---|
| Camino feliz de impresión | Pieza de calibración de 20×20×20 mm: cotas dentro de ±0,3 mm, 0 `print.fault` |
| Impresión fallida vs. correcta | Con desprendimiento inducido: detección por `print.fault` térmico/mecánico o por medición final; el sistema **no** declara éxito, 10/10 |
| Handshake sin reinicio | Abrir el puerto 50 veces sin que el MCU se reinicie (verificado por ausencia de banner `start`), 50/50 |
| Desbordamiento de búfer | Enviar 10 000 líneas con W=4: 0 `Resend` en línea serie sana; con ruido inducido, retransmisión correcta 20/20 |
| Análisis estático de G-Code | 30 ficheros con defectos sembrados (extrusión en frío, fuera de volumen, sin homing, temperatura excesiva): 30/30 bloqueados; 30 ficheros sanos: 0 falsos bloqueos |
| Seguridad térmica | Simulación de termistor desconectado (inyección en el flujo serie): `M112` en ≤ 2 s, 20/20 |
| Verificación geométrica | 50 mallas defectuosas (no manifold, auto-intersecciones): 50/50 detectadas antes de rebanar |
| HDL: co-simulación | 10⁶ instrucciones aleatorias restringidas: 0 divergencias; con un bit sembrado en el ALU: divergencia detectada en la instrucción exacta, 20/20 |
| HDL: formal | Propiedad violada sembrada: SymbiYosys devuelve contraejemplo y éste entra como refutación, 10/10 |
| ASIC hasta GDSII | Diseño de referencia: WNS ≥ 0, 0 DRC, LVS limpio, GDSII generado; reproducible bit a bit entre dos ejecuciones con la misma semilla |
| PCB | 0 errores de ERC y DRC antes de empaquetar; paquete con las 6 salidas obligatorias, 10/10 |
| Flasheo | 20 ciclos dump→flash→verify: 20/20 con hash idéntico; con corrupción inducida, detectada 10/10 y rescate ejecutado |
| Binario que no compila | Firmware con error sembrado: clasificado y devuelto a B en ≤ 1 iteración, 20/20 |
| Consenso entre agentes | Diseño verificado por simulación y formal: `survives` ≥ 85 |
| Desacuerdo total | A afirma que la pieza encaja, la medición dice lo contrario: la medición gana, 10/10 |
| E-STOP con impresión en curso | `M112` confirmado en ≤ 1,5 s y calentadores a 0, 10/10 |

### 9.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta automática | Estado |
|---|---|---|---|---|
| Reinicio del MCU al abrir el puerto | banner `start` inesperado | Comandos perdidos | Reiniciar handshake con DTR controlado y reenviar desde el inicio del trabajo | Recuperado |
| Desbordamiento de búfer | `Resend` repetidos | Corrupción de líneas | Reducir W a 2, bajar baudio, retransmitir | Degradado, seguro |
| Descontrol térmico | detectores §9.A | Riesgo de incendio | `M112` + corte + estado `EMERGENCY` | Seguro, requiere humano |
| Corte de energía | ausencia de puerto al volver | Impresión perdida | Ofrecer reanudación con advertencia explícita | Explicado |
| Fallo parcial (el peor): impresión "completada" con pieza inservible | medición dimensional | Falso éxito | La postcondición física falla ⇒ acción marcada fallida ⇒ refutación | Consistente |
| Flasheo interrumpido | pérdida de dispositivo entre `erase` y `verify` | MCU inutilizable | `integrity=UNKNOWN` + rutina de rescate al reaparecer; si requiere programador externo, se declara 🟡 | Recuperable con prerrequisito |
| OpenLane agota RAM | `oom` o error de etapa | Sin GDSII | Reintento con `SYNTH_STRATEGY` menor y utilización objetivo más baja; si falla, declarar la limitación de la máquina | Degradado |
| Autorouter no cierra el rutado | freerouting termina con pistas sin rutar | PCB incompleta | Informe con las conexiones pendientes y solicitud de intervención humana en el emplazamiento | Bloqueado, explicado |
| Instrumento ausente | enumeración | Sin medición eléctrica | Degradar a telemetría del propio circuito (INA226) o a entrada manual; nunca se da por buena una postcondición no medida | Consistente |
| Sin red | — | Ninguno | Todo el área es local | Operativo |

### 9.10 Riesgos y mitigaciones

Incendio o daño por descontrol térmico (baja/crítico → detectores, límites duros, hombre muerto independiente, `M112` redundante). Brickear un MCU (media/alto → volcado previo obligatorio, R3 sin él, rutina de rescate documentada). Enviar G-Code de otra máquina (media/alto → PM obligatorio y análisis estático que valida contra el PM). Colisión de ejes (media/medio → verificación de homing y límites de volumen). Pieza que parece bien y no cumple (alta/medio → plan de verificación obligatorio y postcondición física). PCB fabricada con error (media/alto → ERC+DRC bloqueantes, render de capas, revisión humana del emplazamiento como paso 🟡 explícito). Expectativa de fabricar un ASIC (alta/medio → frontera 🔴 declarada desde el principio). Autorouter que produce rutados de mala calidad (alta/medio → se declara que el emplazamiento y el rutado crítico son tareas con revisión humana; el autorouter sólo cierra lo no crítico). Falsa precisión de la medición por foto (alta/medio → ±0,3 mm declarados y prohibición de validar tolerancias menores de ±0,5 mm por ese método).

### 9.11 Prerrequisitos y estado de construibilidad

- **🟢 CONSTRUIBLE-YA (sin comprar nada):** CadQuery 2.4/build123d 0.5, OpenSCAD 2021.01, FreeCAD 1.0 (`freecadcmd`), trimesh 4.4, manifold3d, admesh 0.98, PrusaSlicer 2.8, CuraEngine 5.x, Icarus Verilog 12.0, Verilator 5.0xx, cocotb 1.9, GTKWave 3.3/Surfer, SymbiYosys 0.4x + Yices 2.6, Yosys 0.4x, nextpnr, OpenLane 2 + Sky130A + GF180MCU, Magic 8.3.x, KLayout 0.29, netgen 1.5.x, KiCad 8.x + `kicad-cli`, SKiDL 1.2, freerouting 1.9 (Java), gerbv 2.10, avr-gcc 14.x, arm-none-eabi-gcc 13.x, SDCC 4.4, riscv64-unknown-elf-gcc 13.x, PlatformIO Core 6.x, Unity/Ceedling, avrdude 7.3, dfu-util 0.11, OpenOCD 0.12, esptool.py 4.8, stm32flash 0.7, openFPGALoader 0.12, sigrok/sigrok-cli.
- **🟡 REQUIERE-PRERREQUISITO (hardware que el usuario probablemente ya tiene o que es opcional):** impresora 3D con firmware Marlin/RepRap/Klipper y cable USB; en Windows, driver del puente USB-serie; placa MCU objetivo; programador externo para rescate (USBasp ≈ 5 USD, ST-Link V2 clon ≈ 4 USD, CMSIS-DAP ≈ 10 USD); analizador lógico (clon 8 canales ≈ 8–15 USD); multímetro con interfaz (≈ 40–70 USD); calibre digital (≈ 10–25 USD); FPGA de validación (Tang Nano 9K ≈ 20 USD, Colorlight ≈ 25–40 USD, iCEBreaker ≈ 70 USD, ULX3S ≈ 100–150 USD). **Ninguno es necesario para construir y verificar el software del sistema.**
- **🔴 BLOQUEADO-SIN-HARDWARE:** fabricación real de PCB (lote de 5 unidades de 2 capas ≈ 5–30 USD más envío, en el rango de decenas de dólares) y **tape-out de ASIC** (miles de dólares y meses; queda fuera de todas las fases del plan). La validación sustitutiva es, respectivamente, la simulación y el render de capas, y la FPGA.

### 9.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (9.B completo en simulación + 9.A con impresora simulada) → v1 (9.A real con seguridad térmica, 9.D firmware y flasheo con verificación) → completo (9.C hasta GDSII y FPGA, 9.E instrumentación y bucle de convergencia).

- **P9.a Impresora — simulador primero.** P9.a.1 **simulador de firmware Marlin** en `tests/fakes/marlin_sim.py` (responde `M115`, `M105`, `ok`, genera `Resend` y fallos térmicos a demanda) — **PV-9.a.1**: el emisor completa un G-Code de 100 000 líneas contra el simulador con 0 pérdidas y retransmite correctamente ante `Resend` inyectado. *Este subpaso es la clave para no descubrir bugs con una impresora real ardiendo.* P9.a.2 handshake real — **PV-9.a.2**: 50 aperturas sin reinicio no deseado. P9.a.3 detectores térmicos — **PV-9.a.3**: 20/20 inyecciones producen la acción de nivel correcta en ≤ 2 s. P9.a.4 Klipper/Moonraker — **PV-9.a.4**: suscripción a objetos y `emergency_stop` verificados contra una instancia de Moonraker de prueba.
- **P9.b CAD y rebanado.** P9.b.1 plantillas paramétricas — **PV-9.b.1**: 10 plantillas generan STEP y STL válidos con parámetros aleatorios en rango, 100/100 sin excepción. P9.b.2 verificación geométrica — **PV-9.b.2**: 50/50 mallas defectuosas detectadas, 0 falsos positivos en 50 sanas. P9.b.3 rebanado y parseo — **PV-9.b.3**: informe extraído correctamente en 20/20 ficheros. P9.b.4 análisis estático — **PV-9.b.4**: 30/30 defectos bloqueados, 0 falsos bloqueos.
- **P9.c HDL.** P9.c.1 lint y simulación — **PV-9.c.1**: `verilator --lint-only -Wall` sin advertencias en todo `rtl/`. P9.c.2 co-simulación — **PV-9.c.2**: 10⁶ instrucciones sin divergencia; bit sembrado detectado en la instrucción exacta. P9.c.3 formal — **PV-9.c.3**: las 3 clases de propiedad por módulo, con contraejemplo reproducible cuando se siembra un fallo. P9.c.4 síntesis y P&R — **PV-9.c.4**: bitstream generado y cargado; contadores leídos por UART coinciden con el modelo. P9.c.5 OpenLane — **PV-9.c.5**: WNS ≥ 0, 0 DRC, LVS limpio y GDSII reproducible.
- **P9.d PCB y firmware.** P9.d.1 netlist por código — **PV-9.d.1**: ERC sin errores en 5 diseños de prueba. P9.d.2 paquete de fabricación — **PV-9.d.2**: las 6 salidas presentes y los Gerber renderizados sin capas vacías. P9.d.3 firmware y mapa de memoria — **PV-9.d.3**: margen ≥ 10 % en FLASH y RAM, verificado tras compilar. P9.d.4 dump→flash→verify — **PV-9.d.4**: 20/20 con hash idéntico y rescate probado.
- **P9.e Medición y bucle.** P9.e.1 instrumentos — **PV-9.e.1**: 3 vías de medición producen `Measurement` con incertidumbre e instrumento en 100 % de las lecturas. P9.e.2 postcondiciones físicas — **PV-9.e.2**: 0 acciones marcadas exitosas sin su postcondición física verificada. P9.e.3 convergencia — **PV-9.e.3**: en 5 casos con desviación sembrada, el diagnóstico determinista acierta el patrón en ≥ 4 y converge en ≤ 3 iteraciones. P9.e.4 hombre muerto — **PV-9.e.4**: matando el núcleo con calentadores encendidos, `magi-estop` corta en ≤ 20 s, 10/10.

Métricas de salida: 0 impresiones iniciadas con G-Code que no pasó el análisis estático, `M112` en ≤ 2 s ante fallo térmico simulado, 0 divergencias en 10⁶ instrucciones, GDSII con LVS limpio, y 100 % de flasheos verificados por lectura de vuelta.

---

## ÁREA 10 — Interfaz gráfica agentic y control total del sistema (IDE tipo ZCode)

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA**, salvo 10.D que es **🟡 REQUIERE-PRERREQUISITO** (Node.js y Claude Code instalado y autenticado con el plan que el usuario ya posea).

### 10.1 Propósito y alcance

Da al humano visibilidad y control sobre un sistema que trabaja solo: ver el debate mientras ocurre, ver la telemetría a 10 Hz sin que la interfaz se atragante, aprobar o rechazar acciones con su radio de impacto visible, editar la política de capacidades sin tocar código, y parar todo con un atajo. Y da al sistema **control total de la computadora mediante arquitectura, no mediante `sudo`**.

Queda fuera: la lógica de negocio (vive en el núcleo; la GUI es un cliente), la propiedad del trabajo (§0.2) y la ejecución de acciones (Área 8).

**Consume:** todos los eventos del bus, `rpc.*` del núcleo. **Alimenta:** aprobaciones humanas al Área 8, refutaciones humanas al Área 3, y la política de capacidades al Área 0.

### 10.2 Arquitectura

```
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ TAURI 2.x (Rust)  ── ventana, atajos globales, notificaciones del SO,      │
 │                      ciclo de vida del sidecar, canal E-STOP independiente │
 └────────────┬──────────────────────────────────────────────┬───────────────┘
              │ IPC Tauri                                     │ canal E-STOP
              ▼                                               ▼ (no pasa por React)
 ┌──────────────────────────────────────────────┐    ┌──────────────────────┐
 │ REACT 18 + TS 5                              │    │ magi-estop (binario aux)│
 │  ┌────────────┐  ┌───────────────┐           │    └──────────────────────┘
 │  │ WS CLIENT  │─►│ ZUSTAND STORE │──► paneles│
 │  │ (JSON tip.)│  │ (slices por   │           │
 │  └─────▲──────┘  │  dominio)     │           │
 │        │         └───────┬───────┘           │
 │        │   ⚠ DESACOPLE: la telemetría NO pasa │
 │        │   por el store de React: va a un     │
 │        │   ring buffer y uPlot lo lee en rAF  │
 │        │                                      │
 │  Monaco · xterm.js · uPlot · React Flow · TanStack Virtual                │
 └────────┼──────────────────────────────────────────────────────────────────┘
          │ ws://127.0.0.1:<port>/rpc  (token de arranque)
          ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ NÚCLEO PYTHON — dueño del estado · política · auditoría · broker elevado  │
 └───────────────────────────────────────────────────────────────────────────┘
```

### 10.3 Contratos e interfaces

Comandos Tauri (Rust→núcleo): `magi_connect`, `magi_estop`, `magi_open_project`, `magi_pick_folder`, `magi_register_hotkey`, `magi_notify`. Mensajes WebSocket: los `rpc.*` de §0.3 más el flujo de eventos. Tipos TypeScript generados desde los esquemas pydantic (§I.1), sin escritura manual. Estado de la GUI en Zustand con *slices*: `debateSlice`, `deviceSlice`, `jobSlice`, `printSlice`, `providerSlice`, `policySlice`, `forensicSlice`, `inventionSlice`, `logSlice`.

### 10.4 La interfaz (10.A)

**Estética, disposición y modelo de interacción.**

*Decisión:* la ventana es **horizontal, de tres columnas, y nunca excede el tamaño de la pantalla**; el crecimiento del contenido **jamás** ensancha la interfaz ni la alarga: cada columna tiene su propio desplazamiento vertical con la rueda del ratón, y el marco exterior es fijo — porque una conversación larga que estira la ventana convierte el trabajo en una persecución de la barra de desplazamiento, y una interfaz vertical desaprovecha exactamente la forma que tiene un monitor.
*Descartado:* el desplazamiento de página completa y el diseño de columna única alta de las revisiones anteriores.

**Regla de encuadre (normativa, verificada por prueba).** La ventana se abre a `min(1440, ancho_pantalla − 80) × min(900, alto_pantalla − 80)` y **nunca** solicita más. `overflow` del documento raíz fijado a `hidden`; **todo** desplazamiento ocurre dentro de regiones con `overflow-y: auto` y `overflow-x: hidden`. El texto se ajusta por palabra y las cadenas largas —rutas, hashes, líneas de código— se cortan con `overflow-wrap: anywhere` o se desplazan **dentro de su propia caja**, nunca ensanchando la columna. Ningún elemento usa anchura mínima que pueda empujar el diseño: el CI ejecuta la comprobación a 1280×720, 1366×768, 1600×900 y 1920×1080, y **falla si aparece una barra horizontal en cualquier nivel** o si el alto del documento supera el de la ventana.

**Las tres columnas:**

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ MAGI SYSTEM IDE   ·  Conversación | Proyectos          ·  proveedores  ·  ⚙  ·  PARAR TODO│
├────────────┬──────────────────────────────────┬──────────────────────────────────────────┤
│ CARRIL     │ CONVERSACIÓN                     │ LIENZO  (se abre y se cierra con Ctrl+L) │
│ 220 px     │ flexible, mínimo 520 px          │ 30–55 % arrastrable, plegable a 0        │
│            │                                  │                                          │
│ Conversa-  │ ┌─ cabecera MAGI compacta ─────┐ │ ┌ pestañas ──────────────────────────┐  │
│ ción /     │ │ BALTHASAR·2  ronda 3 / 3–7   │ │ │ Plan │ Código │ Imagen │ Gráfico │ │  │
│ Proyectos  │ │ CASPER·3      MELCHIOR·1     │ │ └────────────────────────────────────┘  │
│            │ └──────────────────────────────┘ │                                          │
│ hilos      │ ▲ rueda del ratón                │  contenido del artefacto en curso        │
│ recientes  │ │ turnos y tarjetas              │  con su propia rueda                     │
│ búsqueda   │ ▼ desplazamiento propio          │                                          │
│            │                                  │                                          │
│ ⚙ Config.  │ ┌ barra de instrucción fija ───┐ │  [abrir aparte] [guardar] [reejecutar]   │
│            │ └──────────────────────────────┘ │                                          │
└────────────┴──────────────────────────────────┴──────────────────────────────────────────┘
  fijo          scroll propio, nunca horizontal    scroll propio, nunca horizontal
```

Cada columna es una región de desplazamiento independiente: la rueda del ratón actúa sobre la que tiene el puntero encima, sin encadenarse a las vecinas (`overscroll-behavior: contain`). La barra de instrucción está **anclada abajo** en la columna central y no se desplaza. En pantallas estrechas (< 1200 px) el lienzo se superpone en lugar de comprimir la conversación por debajo de 520 px, y por debajo de 900 px de ancho el carril se colapsa a iconos. La interfaz **nunca** cambia a disposición vertical.

**La columna de lienzo — el añadido de esta revisión.** Es donde se ve lo que el sistema está produciendo, con pestañas y sin sacar al usuario de la conversación:

| Pestaña | Qué muestra | Interacciones |
|---|---|---|
| **Plan** | El **plan de ejecución de la instrucción** antes y durante: pasos, qué área hace cada uno, qué necesita, coste estimado en cuota y tiempo, y en cuál va | Aprobar el plan, quitar pasos, reordenar, ejecutar paso a paso |
| **Código** | Fichero generado o modificado, con resaltado, comparación con la versión anterior y errores del compilador anclados a su línea | Editar, aceptar, rechazar, ejecutar, volver a una versión |
| **Imagen** | La imagen solicitada, con su historial de versiones y la crítica de cada iteración de autocorrección (§Área 20) | Comparar versiones, pedir cambio concreto, exportar |
| **Gráfico** | Series de telemetría, trayectoria de puntuación de la deliberación, grafos de código o de afirmaciones | Zoom, exportar, fijar |
| **Vista previa** | Videojuego, animación, pieza musical o vídeo en ejecución, dentro del panel | Reproducir, pausar, capturar fotograma, medir |
| **Documento** | Informe, dictamen o página web capturada, con sus citas resaltadas y enlazadas a su fuente | Ir a la cita, exportar, imprimir a PDF |

El lienzo se abre solo cuando hay algo que enseñar y **nunca roba el foco del campo de instrucción**. `Ctrl+L` lo abre y cierra; `Ctrl+Mayús+L` lo desprende a una ventana propia para un segundo monitor. Su contenido siempre corresponde al turno seleccionado en la conversación: al subir por el hilo con la rueda, el lienzo sigue al turno visible salvo que se fije con el candado.

**La cabecera MAGI, ahora compacta.** Ocupa 96 px en vez de 148 y mantiene la disposición canónica —BALTHASAR • 2 arriba, CASPER • 3 abajo izquierda, MELCHIOR • 1 abajo derecha, con el rombo central—, cada trapecio con su nombre, su función en tres palabras, **el proveedor y el modelo en uso**, su estado y su última frase. El rombo muestra la ronda actual sobre el mínimo y el máximo, y ahora también **el estado de cuota** del conjunto: verde si hay margen, ámbar si queda menos del 25 %, y con el reloj de recuperación cuando algún proveedor está agotado.

**Anatomía de un mensaje** (sin cambios respecto de la revisión anterior salvo el bloque de identidad, que ahora nombra proveedor y ventana de cuota): cabecera con nodo, función, ronda y versión; **bloque de identidad siempre visible** con proveedor, modelo, versión observada, contexto, temperatura, semilla y cuota restante; resumen en español llano entre comillas; secciones plegadas con el detalle técnico completo; y pie con tokens, tiempo y consumo de cuota.

**Paleta normativa (`gui/src/theme/magi.css`):** `--magi-bg` `#000000` · `--magi-surface` `#0A0E0E` · `--magi-node` `#5BC5E0` · `--magi-node-dim` `#2E6D7D` · `--magi-accent` `#F08000` · `--magi-accent-hi` `#FFA733` · `--magi-ink` `#000000` · `--magi-text` `#F5A65B` · `--magi-ok` `#39FF7A` · `--magi-warn` `#FFC400` · `--magi-danger` `#FF2D2D` · `--magi-undecided` `#8A8F98` · `--magi-grid` `#1A2A2E`. Tipografía `Inter` para prosa, `JetBrains Mono` para código y registros. Alfabeto latino exclusivamente, verificado por test.

**La barra de instrucción.** Campo llamado **Instrucción** (`prompt`), anclado al fondo de la columna central, que crece hasta 5 renglones y **después desplaza internamente** en vez de empujar la conversación. `Enter` envía, `Mayús+Enter` salta línea, `↑` recupera la anterior. A la izquierda, el preajuste de deliberación (`Rápida 3 rondas` · `Estándar 5` · `Exhaustiva 7`); a la derecha, adjuntar y ejecutar. Debajo, la tira de adjuntos en una sola línea con desplazamiento propio. Adjuntos **sin filtro de formato**: toda la ventana es zona de arrastre y el Área 15 resuelve qué hacer con cada fichero.

**Permisos en el momento**, en el hilo, con el efecto en lenguaje llano y dos botones; las acciones irreversibles esperan indefinidamente mientras el resto continúa. **Sin campo de código de acceso.**

**Ergonomía de escritorio.** Paleta de comandos `Ctrl+K`; búsqueda global `Ctrl+Mayús+F`; ajustes `Ctrl+,` (Área 17); atajos reasignables; y tres disposiciones guardadas para la sección Proyectos: **Análisis**, **Ingeniería inversa** y **Fabricación**, que cambian qué pestaña del lienzo se abre por defecto y qué paneles hay en el carril.

**Catálogo completo de paneles** (contenido · interacciones · eventos que consume · comportamiento bajo carga):

| Panel | Contenido | Interacciones | Eventos que consume | Bajo carga |
|---|---|---|---|---|
| **Chat MAGI (MELCHIOR / BALTHASAR / CASPER)** | Tres columnas (o pestañas en pantallas < 1600 px) con transmisión token a token simultánea, cabecera con el modelo que sirve al rol, y por turno: tokens, latencia, coste (0) y proveedor | Pausar rol, copiar JSON crudo, reejecutar turno | `debate.turn`, `inference.token` | Coalescencia de tokens cada 50 ms; si el ritmo supera 200 tok/s por rol, se muestra el texto en bloques |
| **Estructura del proyecto** | Árbol de ficheros y artefactos con estado por fichero (sin analizar / en cola / analizado / con hallazgos) | Abrir, encolar análisis, ver procedencia | `artifact.created`, `job.progress` | Virtualizado (TanStack Virtual) |
| **Terminal integrada** | xterm.js 5.5 sobre `node-pty`/`ptyprocess`, múltiples sesiones en pestañas, con las ejecuciones del agente visibles en vivo | Escribir, `Ctrl+C`, abrir nueva sesión, adjuntar a un trabajo | salida de `proc.spawn` | Búfer de 10 000 líneas con `scrollback` recortado; escritura por lotes de 16 ms |
| **Editor / visor de diff** | Monaco 0.50 con resaltado para C decompilado, Verilog, G-Code, Python, JSON, YAML; vista lado a lado original↔refinado | Editar, aceptar/rechazar refinamiento, ir a definición (por `index.jsonl`) | `artifact.created` | Modelos Monaco descargados al cerrar pestaña; ficheros > 5 MB en modo sólo lectura sin *minimap* |
| **Telemetría USB** | uPlot 1.6, múltiples series, ventana deslizante configurable (10 s–30 min), marcadores de evento verticales | Zoom, fijar escala, exportar CSV | `telemetry.sample` | Ring buffer fuera de React; redibujo en `requestAnimationFrame`, máximo 30 fps; decimación mín/máx al superar 2 px por muestra |
| **Debate MAGI** | Ver 10.B | — | `debate.turn`, `debate.verdict` | — |
| **Monitor de impresión 3D** | Progreso por capa, temperaturas con sus consignas (gráfica dual), posición de ejes, previsualización de la capa actual renderizada desde el G-Code, y botones **Pausar / Reanudar / Abortar / M112** | Controles directos (cada uno es una acción con su radio) | `print.layer`, `print.fault`, `telemetry.sample` | Previsualización de capa cacheada y renderizada en `OffscreenCanvas` |
| **Monitor de flasheo** | Barra por fase (borrar / escribir / verificar), log del programador, hash esperado vs. leído | Abortar sólo antes de `erase` | `flash.progress` | Log virtualizado |
| **Visor forense** | Página con superposición de cajas detectadas, mapa de calor de anomalías, panel de rasgos por bloque, y comparación página↔mediana del expediente | Alternar capas, clic en caja → rasgos, ir al hallazgo | `artifact.created` | Imagen en mosaico con niveles de zoom precalculados |
| **Cola de trabajos y acciones pendientes** | Trabajos con estado y ETA; acciones esperando aprobación **con su radio de impacto en color y texto llano** | Aprobar / Rechazar / Ver acta que la motiva | `action.proposed`, `job.progress` | Ordenado por radio descendente; R3 siempre arriba |
| **Proveedores y cuotas** | Estado del circuito, cuota restante, latencia media, modelo por rol | Forzar proveedor, abrir/cerrar circuito manualmente | `provider.degraded` | Actualización cada 2 s |
| **Inspector de procedencia** | Grafo de cómo se produjo cualquier resultado, con herramienta, versión, semilla, prompt y modelo | Clic en nodo → abrir artefacto; exportar subgrafo | consulta `rpc.provenance.get` | Grafo podado a 200 nodos con expansión bajo demanda |
| **Banco de invenciones** | Ideas, derivadas, operador que las generó, puntuaciones y estado | Filtrar por nicho, reactivar, prototipar | `invention.derived` | Virtualizado |
| **Grafo de código (MAGI-MEM)** | Vista del grafo de conocimiento del código: nodos por etiqueta, aristas por tipo, cobertura por lenguaje, y consola Cypher con autocompletado del esquema | Consultar, ir al símbolo, abrir fragmento, exportar subgrafo como evidencia | `memgraph.indexed`, `memgraph.stale` | Grafo podado a 300 nodos con expansión bajo demanda; consola con límite de 5 000 filas |
| **Ruta e inferencia (MAGI-ROUTE)** | Proveedor y modelo servidos por unidad, estrategia aplicada, estado de las tres capas de resiliencia, cuota **observada** frente a la declarada, coste acumulado (que debe ser 0) y sobrecoste de la pasarela | Fijar modelo por rol, abrir/cerrar circuito, forzar camino de reserva, revocar un proveedor | `route.selected`, `route.tripped`, `route.degraded`, `route.blocked` | Agregación cada 2 s; `route.selected` se muestrea 1:10 en la tabla y completo en el gráfico |
| **Conocimiento establecido** | Deltas vigentes e invalidados por símbolo, con el veredicto que los estableció y su condición de caducidad | Filtrar por símbolo, ir al acta, marcar como obsoleto manualmente | `knowledge.recorded`, `knowledge.invalidated` | Virtualizado |
| **Hilos y proyectos** | Barra lateral con las dos secciones, lista de hilos o proyectos con búsqueda, y acceso a Configuración | Cambiar de sección, abrir, renombrar, convertir hilo en proyecto, archivar | `conversation.*`, `job.progress` | Virtualizado |
| **Conversación** | Hilo de turnos: instrucción del usuario, tarjetas de las tres inteligencias con su identidad de modelo, resultados y tarjetas de permiso; ramas visibles | Escribir, reejecutar con cambios, pedir más rondas, interpelar a un nodo, corregir el rumbo, plegar y desplegar detalle | `debate.turn`, `debate.round`, `debate.verdict`, `inference.token`, `action.proposed` | Virtualizado por turnos; los tokens se coalescen cada 50 ms |
| **Trayectoria de la deliberación** | Puntuación por ronda, versiones de propuesta, refutaciones nuevas frente a resueltas, y qué versión eligió CASPER • 3 | Ir a la ronda, comparar dos versiones, exportar el acta | `debate.round` | Gráfico ligero, ≤ 30 fps |
| **Adjuntos e ingesta** | Lista de ficheros soltados con su formato detectado, el nivel de la cascada que los resolvió, la fidelidad y lo que se perdió; botón *Intentar de otra forma* por fichero | Arrastrar, pegar, quitar, reintentar, abrir en entorno de época | `ingest.started`, `ingest.level`, `ingest.finished` | Virtualizado; miniaturas perezosas |
| **Sistema portable (ventana de máquina)** | Pantalla del sistema operativo construido o del entorno de época, con barra de estado que dice si hay red (normalmente «sin red»), si hay carpeta compartida y qué motor se usa | Capturar teclado y ratón (`Ctrl+Alt` libera), instantánea, restaurar, capturar pantalla, apagar | `vm.started`, `vm.stopped`, `vm.snapshot`, `vm.escape_attempt` | Lienzo a 30 fps; se pausa al perder el foco si la receta lo permite |
| **Registro de auditoría** | Toda acción privilegiada, encadenada por hash, con verificación de la cadena visible | Filtrar, exportar, verificar cadena | `action.executed`, `policy.denied`, `estop.triggered` | Virtualizado; verificación de cadena en *worker* |

**Rendimiento de la GUI.** Virtualización obligatoria en las cuatro listas largas (logs, resultados de decompilación, hallazgos forenses, auditoría). Límite de fotogramas de las gráficas a 30 fps. **Desacople del hilo de render de la llegada de telemetría:** el cliente WebSocket corre en un *Web Worker* que escribe en un `SharedArrayBuffer` circular; uPlot lee de ahí en `requestAnimationFrame`; React nunca ve una muestra individual. Objetivo numérico: **interacción fluida (≥ 30 fps y latencia de entrada ≤ 50 ms) con 10 000 líneas de log por segundo entrando y una impresión en curso**.

**Accesibilidad y modo desatendido.** Navegación completa por teclado con anillo de foco visible; contraste mínimo 4,5:1 en texto; `aria-live` en las notificaciones de fallo. Notificaciones del SO (ToastNotification en Windows, D-Bus en Linux) en: `print.fault`, `action.proposed` con radio R3, `job` terminado, `estop.triggered`, y bloqueo por rompedor de bucles. Al volver tras horas, la GUI muestra una **"cinta de lo ocurrido"**: resumen cronológico de hitos (trabajos terminados, fallos, acciones pendientes, hallazgos nuevos) con enlaces directos, en vez de obligar a reconstruirlo del log.

### 10.5 Visualización de la deliberación en varias rondas (10.B)

La conversación **es** la visualización. Cada deliberación aparece en el hilo como un bloque plegable con una ronda por fila, y sobre él, tres vistas que se abren desde el mismo sitio.

**Vista de rondas (por defecto, dentro del hilo).** Una fila por ronda, cada una con las tres tarjetas del §10.4 en orden MELCHIOR → BALTHASAR → CASPER, plegadas al resumen y expandibles al detalle. En la cabecera de cada fila: número de ronda, versión de la propuesta, puntuación provisional con su variación respecto de la anterior (`58 ▲ +17`), y el recuento de refutaciones nuevas, afinadas y resueltas. **La franja de cambio de modelo** aparece aquí cuando un nodo cambia de inteligencia a mitad de deliberación, con el texto completo del cambio (§I.8).

**Vista de trayectoria.** Gráfico de la puntuación ronda a ronda con las versiones de propuesta marcadas, la versión que CASPER • 3 acabó eligiendo destacada, y bandas de color por criterio de la rúbrica para ver **dónde** se ganó o se perdió. Es donde se detecta a simple vista una meseta (presupuesto que se está tirando) o una oscilación (dos soluciones que se turnan sin converger).

**Vista de grafo.** React Flow 12: nodos = afirmaciones por versión, aristas = refutaciones, color por resultado —verde sobrevive, ámbar enmendada, rojo falsada, violeta no falsable, gris indecisa— y grosor por puntuación. Las versiones se disponen en columnas de izquierda a derecha, de modo que se ve **cómo una afirmación de la versión 1 sobrevive hasta la 4 o muere en la 2**. Es el mapa de por qué el sistema cree lo que cree.

**Marcador de CASPER • 3.** Puntuación por criterio, ronda a ronda, con la tendencia etiquetada en palabras: «mejorando», «estancado» o «empeorando». Junto a él, sus **instrucciones vigentes** para cada uno de los otros dos nodos, que son el mejor resumen posible de en qué punto está la discusión.

**Intervención humana sin romper la autonomía.** Desde el propio hilo: **pausar entre rondas**; **pedir más rondas** con presupuesto ampliado; **inyectar una refutación propia**, que pasa por el mismo validador que BALTHASAR • 2 y sin privilegios; **forzar el veredicto** con motivo obligatorio, registrado como `human_override` en el acta y en la auditoría; **volver a una ronda anterior y reejecutar desde ahí**, lo que crea una rama sin borrar la original; **cambiar el modelo de un nodo** a mitad de deliberación, con el cambio registrado; y **aprobar o rechazar** una acción pendiente. Regla de diseño intacta: si no hay humano, se aplica la política por defecto del radio de impacto y la deliberación continúa; **sólo R3 espera indefinidamente**.

### 10.6 Control total del sistema, con arquitectura y no con `sudo` (10.C)

**Modelo de capacidades.** Cada módulo declara en su `module.yaml` las capacidades que necesita; el núcleo mantiene una política por proyecto y por sesión. Formato del fichero de política (YAML), con ejemplo completo:

```yaml
# policy/global.yaml  (y projects/<slug>/policy.yaml, que lo sobrescribe por clave)
version: 1
defaults:
  fs.read:   {allow: ["${PROJECT}/**", "${HOME}/Documents/**"], deny: ["${HOME}/.ssh/**", "${HOME}/.gnupg/**"]}
  fs.write:  {allow: ["${PROJECT}/workspace/**", "${PROJECT}/artifacts/**"], deny: ["${SYSTEM}/**"]}
  net.out:   {allow: ["https://*.kicad.org", "https://huggingface.co", "https://api.github.com"], deny: ["*"]}
  proc.spawn:{allow_binaries: ["ghidra", "kicad-cli", "prusa-slicer", "yosys", "nextpnr-*", "openocd",
                               "avrdude", "dfu-util", "esptool.py", "iverilog", "verilator", "pio",
                               "adb", "scrcpy", "sigrok-cli", "git", "cmake", "ninja"],
              deny_shell: true}          # nunca se invoca a través de un intérprete de comandos
  usb.claim: {allow_vid_pid: ["1a86:*", "10c4:*", "0483:*", "0d28:*", "18d1:*", "054c:*", "057e:*"]}
  serial.write: {allow_ports: ["auto-detected-printers", "auto-detected-mcus"], max_baud: 500000}
  proc.elevate: {enabled: false, catalog: []}      # desactivado por defecto
  input.synthesize: {enabled: false}               # desactivado por defecto
  registry.write: {enabled: false}
radius_policy:
  R0: auto
  R1: auto_with_log
  R2: judge_approval_and_backup
  R3: human_always                                  # no configurable a otro valor
limits:
  max_R2_per_hour: 20
  max_concurrent_devices: 4
  quarantine_instead_of_delete: true                 # no configurable a false
audit:
  chain: sha256
  export_path: "${PROJECT}/artifacts/audit/"
overrides:
  - module: "modules/fabrication"
    grant: ["serial.write", "usb.claim"]
    reason: "control de impresora y programadores"
  - module: "modules/re"
    grant: ["proc.spawn"]
    deny:  ["net.out"]
    reason: "el análisis de binarios no necesita red"
```

**Elevación de privilegios.**
- **Windows:** *Decisión:* patrón de **broker elevado** — un proceso auxiliar pequeño y auditado (`magibroker.exe`, con manifiesto `requireAdministrator`, firmado por el instalador) que corre elevado y ejecuta **sólo** operaciones de un catálogo cerrado, en lugar de correr toda la aplicación como administrador. Catálogo cerrado (lista exhaustiva): `install_driver_inf`, `create_service`, `delete_service`, `write_registry_key` (limitado a `HKLM\SOFTWARE\MagiSystem`), `set_firewall_rule` (limitado a `127.0.0.1`), `mount_vhd`, `read_smart_data`. Comunicación por tubería con nombre con descriptor de seguridad restringido al usuario que lanzó la aplicación, mensajes firmados con un secreto por sesión, y **todo** lo que pasa por el broker se escribe en la auditoría antes de ejecutarse.
- **Linux:** *Decisión:* `polkit` con acciones y reglas propias, y **grupos (`dialout`, `plugdev`) como alternativa preferible** para USB/serie porque evita la elevación por completo. Fichero de acción `/usr/share/polkit-1/actions/org.magisystem.policy` con acciones `org.magisystem.install-udev-rules`, `org.magisystem.manage-service`, `org.magisystem.write-sysconf`, cada una con `<allow_active>auth_admin_keep</allow_active>`. `sudo` con `NOPASSWD` acotado a comandos concretos **sólo** cuando no hay otra vía, y siempre con la ruta absoluta del binario y argumentos fijos en `/etc/sudoers.d/magi`.
- **Por qué el broker es superior a "ejecutar todo como root":** reduce la superficie de ataque de "toda la aplicación, incluidos el intérprete de plantillas, el parser de PDF y el motor de inferencia" a "siete operaciones con parámetros validados"; hace la auditoría significativa (cada operación privilegiada tiene un nombre, no es "el proceso hizo algo"); permite denegar por política sin recompilar; y evita que un error del agente —o una entrada maliciosa en un PDF o en un binario analizado— se convierta en compromiso total de la máquina.

**Alcance del control (API concreta por SO y capacidad que lo cubre):**

| Dominio | Windows | Linux | Capacidad |
|---|---|---|---|
| Sistema de archivos completo | Win32 `CreateFileW`, `SetFileAttributes`, VSS para copias | POSIX + `xattr`, `statx` | `fs.read`/`fs.write` |
| Red | WinHTTP / sockets, `INetFwPolicy2` para reglas | sockets, `nftables` sólo vía polkit | `net.out` |
| Procesos | `CreateProcessW`, Job Objects, `EnumProcesses` | `fork/exec`, cgroups v2, `/proc` | `proc.spawn` |
| Registro / configuración | `RegCreateKeyEx`, `RegSetValueEx` (vía broker) | ficheros bajo `/etc` (vía polkit) | `registry.write` / `sysconf.write` |
| Dispositivos | SetupAPI, WinUSB, `COM*` | udev, libusb, `/dev/tty*` | `usb.claim`, `serial.write` |
| Automatización de escritorio | `SendInput`, `SetForegroundWindow`, `EnumWindows` | `libei` (Wayland) / `XTEST` (X11), `wmctrl` | `input.synthesize` |
| Servicios y tareas programadas | SCM (`CreateService`), Task Scheduler (vía broker) | `systemd --user`, `systemd` de sistema vía polkit | `proc.elevate` |
| Gestión de paquetes | `winget`/`choco` (vía broker) | `apt`/`dnf`/`pacman` (vía polkit), `pip`/`npm` sin elevación | `proc.elevate` |

**Autorización en la instalación.** El instalador pregunta exactamente cuatro cosas, cada una con su explicación en lenguaje llano y todas **opcionales**: (1) acceso a dispositivos USB/serie — "para hablar con impresoras, microcontroladores y consolas"; en Linux instala las reglas udev y añade al grupo; en Windows sólo informa de Zadig si hace falta. (2) Broker elevado — "para instalar controladores y servicios cuando lo pidas"; si se rechaza, esas funciones quedan deshabilitadas y visibles como tales. (3) Automatización de escritorio — "para que el sistema pueda mover el ratón y teclear por ti"; desactivada por defecto. (4) Red saliente — "para descargar modelos, documentación y hojas de datos"; con lista blanca inicial. **Revocación:** panel "Política" en la GUI que edita el YAML con validación en vivo, muestra el efecto de cada cambio ("esto impedirá que el módulo de fabricación abra el puerto serie") y permite volver a los valores por defecto; el usuario **debe** poder verla y editarla sin tocar código.

**Sandbox de acciones destructivas.**
- **Lista negra dura** (no anulable por política): raíz del sistema (`C:\Windows`, `C:\Program Files`, `/boot`, `/etc`, `/usr`, `/bin`, `/sbin`, `/lib`), el directorio de instalación de la propia aplicación, el almacén de artefactos y el CAS, los directorios de credenciales (`~/.ssh`, `~/.gnupg`, `%APPDATA%\Microsoft\Crypto`), y los dispositivos de bloque en crudo.
- **Zona de cuarentena en vez de borrado:** `fs.quarantine` mueve a `projects/<slug>/_quarantine/<ts>/<ruta_original>` con un `manifest.json` que registra origen, motivo, acta que lo ordenó y hash. **Nada se borra nunca**; la purga de cuarentena es una acción del usuario, no del sistema.
- **Instantánea previa obligatoria** para R1/R2 (§8.7).
- **Confirmación explícita por acción R3**, con el efecto descrito en lenguaje llano ("esto calentará el extrusor a 240 °C durante aproximadamente 3 horas y moverá los ejes; asegúrate de que la máquina está despejada y de que hay alguien en casa") y **ninguna opción de "recordar mi respuesta"**.

**Auditoría.** Registro *append-only* encadenado por hash: cada entrada `{seq, ts, actor{agent|human|system}, action_id, kind, params_hash, radius, reason_ref (acta), result, prev_hash, entry_hash=sha256(prev_hash||canonical_json(entry))}`. Se escribe en `audit_log` (SQLite, con disparador que impide `UPDATE`/`DELETE`) y se replica en `artifacts/audit/audit-<fecha>.jsonl`. Verificación de la cadena en un clic desde la GUI y en el arranque; una rotura se muestra en rojo y se registra como incidencia (no se "repara" silenciosamente). Exportable en JSONL y CSV.

**Principio rector (enunciado normativo del plan):** *el objetivo es que ninguna tarea esté bloqueada por diseño, y eso se consigue con una política configurable por el usuario que puede abrirse hasta el máximo — no eliminando el control, que sólo garantiza que el primer error destructivo sea el último.*

### 10.7 Capa de integración con Claude Code como orquestador (10.D)

**Instalación y detección.** El sistema comprueba, en este orden: (1) `claude --version` en `PATH`; (2) rutas conocidas de instalación por SO; (3) `node --version` (requiere Node.js 18+). Si falta Node.js, la GUI guía su instalación (enlace oficial y verificación posterior); si falta la CLI, muestra el comando de instalación del paquete y verifica al terminar. Autenticación: se ejecuta `claude -p "ping" --output-format json` con timeout de 30 s; una respuesta válida confirma sesión activa; un error de autenticación muestra la instrucción de iniciar sesión en la terminal integrada. **Si no está disponible, se degrada al orquestador propio con modelos locales** — Claude Code es un acelerador, no una dependencia dura, coherente con el principio offline-first.

**Modo de invocación.** Ejecución no interactiva desde el núcleo:

```bash
claude -p "<prompt>" --output-format stream-json --append-system-prompt "<bloque de rol>" \
       --session-id "<uuid del rol>" --allowedTools "mcp__magi__*" --max-turns 12
# continuación:
claude -p "<siguiente turno>" --output-format stream-json --resume "<uuid>"
```

El núcleo lee el flujo línea a línea (JSON por línea), distingue los tipos de mensaje (inicio de sesión, bloques de contenido de texto, bloques de uso de herramienta y sus resultados, mensaje final con métricas de uso), y **reenvía cada fragmento al bus como `inference.token`** para que la GUI lo muestre en vivo igual que un modelo local. Manejo de errores: código de salida ≠ 0 ⇒ leer `stderr` y clasificar (autenticación, límite de uso, red, argumento inválido); límite de uso ⇒ el Área 6 abre el circuito de este proveedor y reenruta a local **sin perder el turno** (la unidad reanudable se reintenta con otro proveedor). Timeout duro por turno: 180 s con `busy` detectado por la llegada de cualquier fragmento.

**Sesión por agente.** Tres sesiones persistentes e independientes (A, B, C), cada una con su `--session-id` propio (UUID estable guardado en `debate_session`), su propio prompt de sistema anexado (`--append-system-prompt` con el bloque de rol del Área 7) y su propio historial gestionado por la CLI. **Aislamiento:** el prompt de B se construye **desde el acta**, no desde la conversación de A; además, las tres sesiones son procesos distintos con directorios de trabajo distintos (`sessions/{melchior,balthasar,casper}/`), de modo que B no puede leer artefactos intermedios de A salvo los que el orquestador copie explícitamente (afirmaciones y evidencia). Se comprueba automáticamente (PV-3.b.2).

**Exposición de las herramientas del sistema vía MCP — la decisión de diseño más potente del área.** *Decisión:* el núcleo levanta un **servidor MCP local por transporte stdio** (`modules/mcp/server.py`, lanzado como `magi-mcp` y declarado en la configuración de proyecto de Claude Code) que expone como herramientas las capacidades del laboratorio — porque así Claude Code no sólo conversa: **opera el laboratorio**, con el mismo control de radio y auditoría que cualquier otro actor.
*Descartado:* transporte HTTP/SSE — innecesario para un servidor local y añade superficie de red.

Herramientas registradas, con su esquema de entrada resumido y su radio:

| Herramienta MCP | Entrada | Radio | Comportamiento |
|---|---|---|---|
| `decompile_binary` | `{path|cas_ref, arch?, timeout_s?}` | R1 | Encola trabajo, devuelve `job_id`; el resultado se consulta con `get_job` |
| `read_document_topography` | `{doc_ref, pages?}` | R0 | Devuelve `PageTopography` resumida y el enlace al JSON completo |
| `query_corpus` | `{query, k?, as_of?, corpus?}` | R0 | Devuelve fragmentos con `chunk_id`, locator y cita literal |
| `list_devices` | `{}` | R0 | Dispositivos con su perfil y modos disponibles |
| `read_telemetry` | `{device_id, channel, since, until, agg?}` | R0 | Serie temporal agregada desde DuckDB |
| `slice_and_print` | `{geometry_ref, profile_id, printer_id, dry_run?}` | **R3** | **Emite `action.proposed`; nunca imprime directamente** |
| `synthesize_hdl` | `{project_ref, target}` | R1 | Ejecuta Yosys y devuelve utilización y ruta crítica |
| `flash_firmware` | `{image_ref, target, programmer}` | **R2/R3** | **Emite `action.proposed`; exige dump previo** |
| `run_debate_round` | `{topic, context_refs[], budget?}` | R1 | Ejecuta una ronda y devuelve el acta |
| `query_code_graph` | `{cypher, project}` | R0 | Consulta validada por A13-1 sobre el grafo de MAGI-MEM; devuelve filas y la consulta como evidencia |
| `impact_of_change` | `{diff_ref, project}` | R0 | Superficie afectada y clasificación de riesgo (A13-3) |
| `record_measurement` | `{magnitude, value, unit, uncertainty, instrument, method}` | R1 | Inserta `Measurement` con procedencia `human|instrument` |

**Puerta de permisos (regla dura):** toda herramienta que produzca una acción R2/R3 **no se ejecuta directamente**; emite `action.proposed` y espera la vía del Área 8 (Juez, preflight, y humano si es R3). El servidor MCP devuelve en ese caso `{status:"pending_approval", action_id}` y la conversación continúa; nunca miente diciendo que hizo algo que está pendiente.

**Cadena de reserva entre modelos (tabla completa).**

| Rol / tipo de tarea | 1.ª opción | 2.ª opción | 3.ª opción | Disparador del cambio |
|---|---|---|---|---|
| MELCHIOR • 1, razonamiento largo con herramientas | `claude-code-cli` | otro proveedor de nube declarado | `hf-inference` | Cuota agotada, error de autenticación, requisito offline |
| BALTHASAR • 2, falsación | proveedor de nube distinto al de MELCHIOR • 1 | `claude-code-cli` | local-text con temperatura alta | Regla de diversidad: B nunca comparte proveedor **y** familia con A si hay alternativa |
| CASPER • 3, arbitraje | proveedor de nube distinto a los otros dos | `claude-code-cli` | el proveedor con más cuota restante | Diversidad y coste; el Juez es el rol más barato |
| Visión (Área 1) | el proveedor con visión y cuota disponible | `claude-code-cli` si el usuario consintió enviar imágenes | — | Consentimiento explícito por sesión; por defecto **nunca** sale del equipo |
| Tareas de código largas (síntesis, refactor) | `claude-code-cli` | el proveedor con mayor contexto disponible | troceado en unidades reanudables | Longitud de contexto necesaria > 32 k |
| Embeddings y reordenamiento | local siempre | — | — | Nunca sale del equipo |
| Tarea rechazada por un proveedor remoto | **reenrutar a local** | — | — | Detección de negativa (§7.9) |

**Persistencia del contexto de debate entre llamadas.** *El acta JSON es la memoria canónica, no el historial conversacional del proveedor.* Proceso de **rehidratación** al iniciar un turno: (1) leer las actas de la rama actual (`round_id` y sus antecesores por `parent_round_id`); (2) filtrar por rol — A recibe sus afirmaciones vigentes, las refutaciones admitidas y los veredictos; B recibe afirmaciones y evidencia, **sin** el razonamiento de A; C recibe todo el acta de la ronda; (3) comprimir según el nivel jerárquico de §7.5; (4) renderizar con el compilador de prompts y enviar. Consecuencia: el debate **sobrevive** a un cambio de proveedor a mitad, a un reinicio de la aplicación y a la expiración de una sesión de la CLI — basta con crear una sesión nueva y rehidratar. Ésta es la propiedad que hace el sistema robusto, y se prueba explícitamente (PV-10.d.3).

**Paridad o superioridad de resultado — de dónde sale y cómo se mide.** La ventaja no está en el modelo aislado, sino en la arquitectura: **(1)** verificación mecánica en lugar de confianza (citas validadas por subcadena, esquemas por gramática, postcondiciones comprobadas); **(2)** debate adversarial con **modelos distintos** y guardas anti-degeneración; **(3)** evidencia física por encima del argumento (precedencia §3.10); **(4)** recálculo determinista de todo número en un sandbox; **(5)** oráculos ejecutables (Unicorn, co-simulación, pruebas diferenciales, formal); **(6)** bucles de iteración con realimentación real del mundo. **Cómo se mide** — banco de tareas con solución conocida (`bench/superiority/`, 60 tareas: 20 de RE con la respuesta verificable por oráculo, 20 de contraste normativo con la relación anotada, 10 de diseño paramétrico con cotas objetivo, 10 de HDL con contraejemplo conocido), comparando tres condiciones: **(a)** una sola llamada a un modelo frontera sin arquitectura alrededor, **(b)** el sistema completo con modelos locales, **(c)** el sistema completo usando Claude Code como MELCHIOR. Métricas: tasa de error (respuesta incorrecta), **tasa de alucinación** (afirmación con cita o número inexistente), tasa de afirmaciones no falsables, y coste en tiempo. **Criterio de la afirmación de superioridad:** la condición (b) debe reducir la tasa de alucinación en ≥ 70 % respecto de (a) y la tasa de error en ≥ 25 %; si no lo consigue, la afirmación "igual o superior a los modelos frontera" queda **refutada** y así se declara en la documentación. Una afirmación de superioridad sin banco de pruebas es exactamente el tipo de afirmación no falsable que el BALTHASAR debe destruir — y por eso este banco es obligatorio antes de que el proyecto pueda afirmar nada.

### 10.8 Integración con el debate popperiano

Afirmaciones: "la GUI mantiene 30 fps bajo la carga declarada", "ninguna acción R3 se ejecutó sin humano", "el contexto de debate sobrevive a un cambio de proveedor", y las tres condiciones del banco de superioridad. Evidencia admisible: trazas de rendimiento del navegador (`performance.measure`), consultas SQL sobre la auditoría, y resultados del banco. Refutación más potente: **la ejecución del escenario de estrés** y **la consulta SQL que encuentra una excepción** (una sola fila con R3 sin humano refuta la afirmación entera). Invocación: al cerrar cada fase y ante cualquier cambio en el modelo de capacidades.

### 10.9 Costos, latencia y recursos

RAM de la GUI: ≤ 320 MB en reposo, ≤ 600 MB con 10 000 líneas de log y tres gráficas activas. CPU: ≤ 8 % de un núcleo en reposo con telemetría a 10 Hz. Latencia de eco de la terminal ≤ 30 ms p95. Tokens: la GUI no consume; Claude Code consume según el plan del usuario y se contabiliza por sesión y por rol en el panel de proveedores. **Salto del debate:** las interacciones de interfaz son R0/R1 y no se debaten. **Caché:** previsualizaciones de capa de G-Code por `sha256(gcode)+capa`; mosaicos del visor forense por `sha256(imagen)+zoom`; grafos de procedencia por `artifact_id+profundidad` con invalidación al crear aristas nuevas.

### 10.10 Calidad y pruebas

| Caso | Criterio de éxito |
|---|---|
| Camino feliz | Abrir proyecto, lanzar debate, ver los tres roles transmitir, aprobar una acción R1: sin errores de consola, 20/20 |
| GUI bajo estrés | 10 000 líneas/s de log + telemetría a 10 Hz + impresión en curso durante 10 min: ≥ 30 fps, latencia de entrada ≤ 50 ms, sin fugas (RSS estable ±5 %) |
| Consenso entre agentes | El grafo muestra 1 nodo verde sin aristas rojas y el marcador converge, 10/10 |
| Desacuerdo total | El grafo muestra nodos grises con aristas y el marcador marca "estancado"; el sistema propone la medición que resolvería, 10/10 |
| Documento alterado (integración Área 1) | El visor forense superpone el hallazgo en las coordenadas correctas ±2 mm, 20/20 |
| Impresión fallida (integración Área 9) | El monitor muestra `print.fault` y el botón M112 responde en ≤ 1,5 s, 10/10 |
| Idea inventiva validada (integración Área 11) | El banco muestra la derivada, su operador y su veredicto con enlace al acta, 10/10 |
| R3 sin humano | Consulta SQL sobre `audit_log`: 0 filas con `radius=R3` y `actor≠human`, en 30 días de uso simulado |
| Auditoría | Cadena de 10 000 entradas verificada en ≤ 3 s; alteración de una entrada detectada, 10/10 |
| Claude Code ausente | Con la CLI desinstalada, el sistema arranca y ejecuta un debate completo con modelos locales, 10/10 |
| Cambio de proveedor a mitad de debate | Matar la sesión de la CLI en la ronda 2: la ronda 3 continúa con local y el acta es coherente, 10/10 |
| MCP con radio R3 | `slice_and_print` invocada desde Claude Code: devuelve `pending_approval` y **no** imprime, 10/10 |
| Política | Editar la política para denegar `serial.write` y comprobar que el módulo de fabricación es rechazado con mensaje claro, 10/10 |

### 10.11 Modos de fallo, riesgos y prerrequisitos

| Fallo | Detección | Efecto | Respuesta | Estado |
|---|---|---|---|---|
| WebSocket caído | ping/pong | GUI sin datos | Reconexión con backoff; banner "reconectando"; el trabajo sigue | Núcleo operativo |
| Fuga de memoria en la GUI | RSS creciente monótono | Congelación | Recorte forzado de búferes y aviso; recarga de la ventana sin matar el núcleo | Recuperado |
| Atajo global no registrable | error de Tauri | Sin E-STOP por teclado | Botón visible + `magi-estop` como vía alternativa; aviso explícito al usuario | Degradado, explicado |
| Broker no autorizado | rechazo en instalación | Sin operaciones elevadas | Funciones deshabilitadas y marcadas en la interfaz; nunca se intenta por otra vía | Consistente |
| Fallo parcial: acción ejecutada sin entrada en auditoría | verificación de cadena | Trazabilidad rota | Marcar `audit_gap`, bloquear nuevas acciones R2+ hasta revisión humana | Seguro |
| Claude Code devuelve JSON malformado | parser de flujo | Turno perdido | Reparación (§7.4) y luego reenrutado a local | Operativo |

**Riesgos:** control total mal delimitado (media/crítico → broker con catálogo cerrado, lista negra dura, cuarentena, auditoría encadenada); GUI que se convierte en el dueño del trabajo (media/alto → arquitectura de sidecar y pruebas de cierre de ventana); dependencia de Claude Code (media/medio → degradación probada); sobrecarga cognitiva de la interfaz (alta/medio → tres workspaces y paleta de comandos); afirmación de superioridad no sostenida (alta/alto → banco obligatorio con criterio numérico y disposición a declararla refutada).

**Prerrequisitos: 🟢 CONSTRUIBLE-YA** para 10.A/10.B/10.C (Rust 1.79+, Node.js 20 LTS, Tauri 2.x y las librerías citadas). **🟡 REQUIERE-PRERREQUISITO** para 10.D: Node.js 18+ y Claude Code instalado y autenticado con el plan que el usuario ya tenga (coste cero adicional; si no lo tiene, el sistema funciona igual con modelos locales).

### 10.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (ventana, WS, chat A/B/C, terminal, árbol, E-STOP) → v1 (todos los paneles, política editable, auditoría, monitores) → completo (grafo de debate, inspector de procedencia, MCP, banco de superioridad).

- **P10.a Cascarón.** P10.a.1 Tauri + sidecar + WS — **PV-10.a.1**: la GUI arranca, conecta con token y sobrevive a un reinicio del núcleo, 20/20. P10.a.2 tipos generados — **PV-10.a.2**: el CI falla si `generated.ts` difiere del esquema. P10.a.3 E-STOP — **PV-10.a.3**: ≤ 1,5 s con núcleo sano y ≤ 2,5 s con núcleo colgado.
- **P10.b Paneles.** P10.b.1 los 13 paneles — **PV-10.b.1**: cada panel renderiza con datos sintéticos y consume exactamente los eventos declarados (prueba de contrato). P10.b.2 rendimiento — **PV-10.b.2**: escenario de estrés cumplido. P10.b.3 layouts — **PV-10.b.3**: los tres workspaces se guardan y restauran, 10/10.
- **P10.c Debate visual.** P10.c.1 turnos y JSON crudo — **PV-10.c.1**: el JSON mostrado es idéntico byte a byte al acta persistida. P10.c.2 grafo — **PV-10.c.2**: 200 nodos renderizados en ≤ 800 ms, colores correctos al 100 %. P10.c.3 intervención humana — **PV-10.c.3**: refutación inyectada pasa el mismo validador y queda registrada como `human`, 10/10.
- **P10.d Control y Claude Code.** P10.d.1 política y capacidades — **PV-10.d.1**: 20 escenarios de denegación producen mensaje claro y entrada de auditoría. P10.d.2 broker/polkit — **PV-10.d.2**: sólo las 7 operaciones del catálogo se ejecutan; cualquier otra es rechazada, 20/20. P10.d.3 rehidratación — **PV-10.d.3**: matar la sesión a mitad y continuar el debate con acta coherente, 10/10. P10.d.4 MCP — **PV-10.d.4**: las 10 herramientas responden con esquema válido y las R2/R3 devuelven `pending_approval`, 10/10 cada una. P10.d.5 banco de superioridad — **PV-10.d.5**: ejecutado y publicado con sus tres condiciones y su criterio numérico, con resultado honesto sea cual sea.

Métricas de salida: ≥ 30 fps bajo estrés, 0 acciones R3 sin humano, cadena de auditoría íntegra, y banco de superioridad ejecutado con resultado publicado.

---

## ÁREA 11 — Creatividad inventiva (motor de invención y explotación)

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA** para representación, extrapolación, validación y cribado; **🟡** para arte previo en línea (requiere red) y para el prototipado físico (hereda los prerrequisitos del Área 9).

### 11.1 Propósito y alcance

Convierte una idea del usuario en un objeto formal manipulable por algoritmos, la valida contra la física y contra el arte previo, genera derivadas por operadores declarados (no por ocurrencia), las somete al debate, y prototipa la ganadora para que el fallo real realimente el proceso. Lo que separa un motor de invención de un generador de ocurrencias es exactamente ese último bucle.

Queda fuera: la asesoría legal de propiedad industrial (se produce orientación técnica documentada, y así se etiqueta), la asesoría de inversión, y la fabricación en sí (Área 9).

**Consume:** Área 2 (literatura técnica y normativa), Área 9 (prototipo físico), Área 5 (prototipo software), Área 3 (debate), Área 7 (prompt de invención). **Alimenta:** Área 9 y Área 5 (encargos de prototipo), Área 10 (banco de invenciones).

### 11.2 Arquitectura

```
 descripción libre del usuario
        │
        ▼
 ┌──────────────────────┐  huecos  ┌───────────────────────────┐
 │ ESTRUCTURACIÓN       │─────────►│ INTERROGATORIO DIRIGIDO   │
 │ → esquema Invention  │◄─────────│ (preguntas mínimas)       │
 └──────────┬───────────┘          └───────────────────────────┘
            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │ VALIDACIÓN TÉCNICA por primeros principios (sandbox §2.5)     │
 │  ⚠ punto de corte: si viola un límite físico ⇒ INVIABLE       │
 └──────────┬───────────────────────────────────────────────────┘
            ▼
 ┌──────────────────────┐   patentes/literatura   ┌──────────────────────┐
 │ ARTE PREVIO          │◄───────────────────────►│ Playwright legítimo  │
 │ (reivindicaciones)   │                          │ + hash + timestamp  │
 └──────────┬───────────┘                          └──────────────────────┘
            ▼
 ┌──────────────────────┐        ┌───────────────────────────────────────┐
 │ CRIBADO DE           │        │ EXTRAPOLACIÓN: 8 operadores (§11.5)   │
 │ PATENTABILIDAD       │        │ → métrica de novedad → MAP-Elites     │
 └──────────┬───────────┘        └──────────────────┬────────────────────┘
            ▼                                        ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │ DEBATE POPPERIANO con rúbrica de invención (§11.6)                   │
 └──────────┬───────────────────────────────────────────────────────────┘
            ▼
 ┌──────────────────────┐   fallo real   ┌───────────────────────────────┐
 │ MVP = EXPERIMENTO    │───────────────►│ actualiza vector de parámetros│
 │ (Área 9 o Área 5)    │                │ y REACTIVA los operadores     │
 └──────────────────────┘                └───────────────────────────────┘
```

### 11.3 Representación formal (va primero: sin ella no hay algoritmo)

```json
{
  "invention_id": "inv_01J9…", "version": 3,
  "title": "…",
  "problem": {"statement":"…","who_has_it":"…","current_alternatives":[{"name":"…","limitation":"…"}]},
  "operating_principle": {"summary":"…","physical_domain":["mecánico","térmico"],
                          "governing_equations":["Q = m·c·ΔT"],"key_phenomena":["conducción"]},
  "domain": "mecánico|eléctrico|hidráulico|térmico|informacional|biológico|químico|óptico",
  "parameter_vector": [
    {"name":"diametro_tubo","value":12.0,"unit":"mm","range":[6.0,25.0],"sensitivity":"alta"},
    {"name":"caudal","value":2.5,"unit":"L/min","range":[0.5,8.0],"sensitivity":"media"}
  ],
  "assumptions": [{"id":"a1","statement":"el fluido es incompresible","declared_by":"user|system"}],
  "constraints": [{"kind":"physical|economic|regulatory|manufacturing","statement":"…","source":"…"}],
  "resource_requirements": {"materials":[{"item":"…","qty":1,"unit":"ud","cost_usd":0}],
                            "tools_required":["impresora 3D"],"skills":["…"],"time_h":6},
  "trl": 2,
  "prototype_artifacts": [{"kind":"stl|gcode|firmware|pcb|code","artifact_id":"…"}],
  "provenance": {"derived_from":"inv_…|null","operator":"inversion_supuestos|null","generation":2},
  "killer_hypothesis": "…la hipótesis central cuyo fracaso mata la idea…",
  "cheapest_experiment": {"description":"…","cost_usd":0,"time_h":2,"decides":"killer_hypothesis"}
}
```

Tablas: `invention`, `invention_param`, `invention_derivation`, `prior_art_ref`, `patentability_screen`, `invention_score` (DDL en §T3). Eventos: `invention.derived`, `artifact.created`.

### 11.4 Pipeline de explotación, etapa a etapa

1. **Estructuración.** Entrada: texto libre. Salida: `Invention` válido. El interrogatorio dirigido pregunta **sólo** por los campos obligatorios ausentes, en bloques de máximo 4 preguntas, con opciones concretas cuando existan. Criterio de salida: esquema válido y `killer_hypothesis` no vacía.
2. **Validación técnica por primeros principios.** Comprobaciones deterministas en el sandbox (§A2-4): balance de energía, balance de masa, conservación de momento, límite de Carnot para máquinas térmicas, límite de Betz para captación eólica, límite de Shannon para capacidad de canal, resistencia y fatiga del material, escalado (cómo varía el efecto con el tamaño: ley cuadrado-cubo), y densidad energética de la fuente declarada. Herramientas: `sympy` 1.13, `numpy` 2.0, `scipy` 1.14, `pint` 0.24 (obligatorio: sin unidades no se calcula). Conectado al Área 2 para contrastar contra literatura técnica local. Salida: `feasibility_report` con `viable | viable_con_condiciones | inviable` y, si es inviable, **la desigualdad concreta que se viola** con sus números.
3. **Búsqueda de arte previo.** Fuentes consultadas por el módulo de navegación legítimo (§I.3): Espacenet, Google Patents, USPTO Patent Full-Text Search, **INDECOPI** para Perú, y repositorios académicos abiertos. Procedimiento: generar 6–12 consultas (términos del principio de funcionamiento + sinónimos por dominio + clasificación CPC/IPC estimada), recuperar hasta 50 documentos, extraer **reivindicaciones independientes** (parseo por el patrón "1. Un/Una ... caracterizado por"), embeber y comparar semánticamente con el principio de funcionamiento de la invención, y ordenar por similitud. Cada documento se guarda con su URL, su hash y su marca de tiempo como evidencia. Salida: **informe de novedad** con las 10 referencias más cercanas, su similitud, y para cada una un análisis de qué elemento de la reivindicación coincide y cuál no.
4. **Cribado de patentabilidad.** Evaluación explícita de los tres requisitos frente a las referencias halladas: **novedad** (¿existe una sola referencia que divulgue todos los elementos?), **nivel inventivo** (¿la combinación de dos o más referencias resultaría obvia para un experto en la materia? — se examina explícitamente la motivación para combinarlas), y **aplicación industrial** (¿puede fabricarse o usarse en la industria?). Rutas de protección concretas: **patente de invención** (protección más fuerte, examen más exigente, plazo largo), **modelo de utilidad** (que en Perú, ante INDECOPI, tiene requisitos y plazos distintos de la patente de invención y suele ser la vía correcta para mejoras mecánicas de forma o configuración que aporten una ventaja técnica), **secreto industrial** (cuando el producto no revela el método al comercializarse y no es fácilmente aplicable por ingeniería inversa) y **publicación defensiva** (cuando no se quiere patentar pero sí impedir que otro lo patente). Se incluye la **vía PCT** para internacionalizar y los **plazos de prioridad** aplicables, que el sistema recupera del corpus normativo cargado por el usuario, **no de memoria del modelo**. **Etiqueta obligatoria en la salida:** *"Orientación técnica documentada. No constituye asesoría legal. La presentación debe ser revisada por un agente de la propiedad industrial."*
5. **MVP mínimo construible.** Descomposición en **el prototipo más pequeño que falsa o confirma la `killer_hypothesis`** — no el producto: el experimento. Regla: si el MVP propuesto cuesta más de 50 USD o más de 8 h, se exige justificar por qué no existe uno más barato. Ruta: Área 9 si es físico, Área 5 si es software. Salida: presupuesto, tiempo, lista de materiales y **el criterio de decisión** escrito antes de ejecutar ("si la deflexión supera 2 mm con 2 kg, la hipótesis cae").
6. **Mercado y monetización.** Problema, usuario concreto, alternativas actuales con su precio, dimensionamiento razonado **con fuentes citadas e incertidumbre declarada** (y "desconocido" cuando no haya fuente: prohibido inventar cifras de mercado), modelo de ingresos, estructura de costes con la lista de materiales real del MVP, y **punto de equilibrio calculado** por código determinista. Etiqueta: análisis, no recomendación de inversión.
7. **Hoja de lanzamiento.** Hitos con fecha relativa, dependencias, riesgos, y **condiciones de abandono definidas por adelantado**: qué resultado mataría el proyecto (por ejemplo, "si el coste unitario a 1 000 unidades supera 18 USD, se abandona"). Es la disciplina popperiana aplicada al negocio, y se escribe **antes** de empezar, no después.

**Decisiones formalizadas adicionales de esta área.**
**Decisión:** la derivación se produce siempre por un **operador declarado** de la lista de ocho, y la derivada registra cuál fue y sobre qué elemento actuó — porque "el modelo pensó variantes" no es un procedimiento reproducible y no se puede auditar ni mejorar.
*Descartado:* generación libre con temperatura alta — produce variedad aparente y concentración real en torno a lo que el modelo ya conoce.
**Decisión:** el MVP es siempre el experimento más barato que decide la `killer_hypothesis`, con su criterio escrito antes de ejecutarlo — porque escribir el criterio después convierte cualquier resultado en confirmación.

### 11.5 Algoritmo de extrapolación inventiva

**A11-1 — Operadores de variación (los ocho, cada uno con su implementación).**

| ID | Operador | Implementación concreta |
|---|---|---|
| O-a | **Combinatoria de parámetros** | Caja morfológica de Zwicky: se discretiza cada parámetro en 3–5 niveles y se muestrea con **muestreo por hipercubo latino** (`scipy.stats.qmc.LatinHypercube`) más muestreo dirigido por sensibilidad (los parámetros marcados `sensitivity: alta` reciben el doble de niveles). Nunca exhaustivo: `N` muestras declaradas |
| O-b | **Traslación de dominio** | Tabla de correspondencias entre dominios aplicada al principio de funcionamiento: mecánico↔eléctrico↔hidráulico↔térmico↔informacional↔biológico (fuerza↔tensión↔presión↔ΔT↔gradiente de información; masa↔inductancia↔inertancia; amortiguador↔resistencia↔restricción↔conductancia térmica; muelle↔capacitancia↔capacitancia hidráulica↔capacidad calorífica; caudal↔corriente↔caudal↔flujo de calor↔ancho de banda). El sistema aplica la tabla mecánicamente y el modelo redacta la analogía resultante |
| O-c | **Inversión de supuestos** | Se enumeran los `assumptions[]` declarados y se niega cada uno, generando la idea que resulta ("¿y si el fluido **es** compresible?"). Implementación determinista: una derivada por supuesto |
| O-d | **Fusión con ideas no relacionadas** | Muestreo aleatorio de conceptos de un **banco semántico local** (`data/concept_bank.jsonl`: 5 000 conceptos técnicos con su embedding, construido desde los índices de manuales y normas que el usuario cargó) restringido a distancia coseno ∈ [0,55; 0,80] del concepto base — ni idéntico ni absurdo —, y forzado de la síntesis |
| O-e | **Escalado extremo** | Se lleva el parámetro clave dos órdenes de magnitud arriba y dos abajo, y se recalculan los efectos dominantes por análisis dimensional (qué término de la ecuación gobernante pasa a dominar), lo que suele revelar un régimen distinto |
| O-f | **Sustracción** | Se elimina el componente de mayor coste o mayor complejidad de la lista de recursos y se exige resolver la función sin él |
| O-g | **Principios TRIZ** | Identificación de la **contradicción técnica** (parámetro que mejora vs. parámetro que empeora, mapeados a los 39 parámetros de ingeniería), consulta de la **matriz de contradicciones** (tabla local `data/triz_matrix.json`) y aplicación de los principios inventivos sugeridos (de los 40) al caso concreto |
| O-h | **Biomímesis** | Consulta a un índice local de estrategias biológicas (`data/biomimicry.jsonl`, construido desde literatura abierta que el usuario cargue) por función requerida (adherir, filtrar, aislar, disipar, autolimpiar, autorrepararse), y transferencia de la estrategia al dominio técnico |

**A11-2 — Métrica de novedad y diversidad.**
```
1. embeber cada idea con bge-m3 sobre un texto canónico: problema + principio + parámetros clave
2. novedad_vs_base := 1 − cos(e_derivada, e_base)
3. novedad_vs_conjunto := min sobre todas las derivadas ya aceptadas de (1 − cos(e_i, e_derivada))
4. UMBRALES: se descarta la derivada si novedad_vs_base < 0,15 (es una reformulación de la base)
      o si novedad_vs_conjunto < 0,12 (es una reformulación de otra derivada)
5. además, comprobación léxica: si el solape de trigramas con otra derivada supera 0,6, se descarta
```

**A11-3 — Selección con preservación de diversidad.** *Decisión:* esquema de **calidad-diversidad tipo MAP-Elites** sobre una rejilla de descriptores, conservando la mejor idea de cada nicho en lugar de las N mejores globales — porque las N mejores globales son siempre variaciones de la misma idea, y lo valioso de un motor de invención es cubrir el espacio.
*Descartado:* algoritmo genético con selección por torneo — converge a un óptimo local y colapsa la diversidad, que es justo lo que aquí hay que preservar.

Rejilla (4 descriptores, 4×4×3×8 = 384 nichos):
- **Coste de validación** (USD del `cheapest_experiment`): [0–10), [10–50), [50–200), [200–∞)
- **Complejidad** (número de componentes distintos): [1–2], [3–5], [6–10], [11–∞)
- **TRL**: 1–2, 3–4, 5+
- **Dominio físico principal**: los 8 del esquema

Cada nicho guarda un único elite (la de mayor puntuación de la rúbrica de invención). Una derivada nueva sustituye al elite de su nicho sólo si su puntuación es mayor; si el nicho está vacío, entra directamente aunque su puntuación sea baja — así se exploran regiones poco pobladas.

**A11-4 — Rúbrica específica de invención (pesos que suman 100).**

| Criterio | Peso | Cómo se puntúa |
|---|---|---|
| Impacto | 25 | Magnitud de la mejora sobre la mejor alternativa actual, cuantificada y con fuente |
| Viabilidad técnica | 25 | 25 si la validación por primeros principios es `viable`; 12 si `viable_con_condiciones`; 0 si `inviable` |
| Novedad | 20 | Combinación de `novedad_vs_base` y del informe de arte previo (0 si una referencia divulga todos los elementos) |
| Coste de validación | 15 | Inverso normalizado del coste del experimento decisivo (barato puntúa alto) |
| Riesgo regulatorio | 15 | 15 si no hay requisito de certificación; descuentos por cada requisito identificado en el corpus |

**Parámetro N y presupuesto:** por defecto **12 derivadas por ronda** (dos por operador para O-a…O-f y una para O-g y O-h), **3 rondas**, y criterio de corte: se detiene si en una ronda completa ninguna derivada supera 60/100 en la rúbrica **o** si la mejor puntuación no mejora ≥ 5 puntos respecto de la ronda anterior. Presupuesto de tokens: ≈ 9 000 por derivada (generación + debate abreviado) ⇒ ≈ 108 000 por ronda.

**A11-5 — Bucle de demostración empírica (lo que separa un motor de invención de un generador de ocurrencias).**
```
1. la idea ganadora del nicho más prometedor se prototipa: Área 9 (pieza física) o Área 5 (software)
2. se ejecuta el cheapest_experiment con su criterio de decisión escrito de antemano
3. resultado → Measurement (tier 1) o ExecutionRecord (tier 2)
4. SI FALLA:
   4.1 identificar qué parámetro o supuesto quedó refutado (el experimento se diseñó para eso)
   4.2 ACTUALIZAR el vector de parámetros: estrechar el rango del parámetro implicado a la región
        no refutada, o marcar el supuesto como falso y moverlo a constraints
   4.3 REACTIVAR los operadores con esa restricción nueva incorporada: O-c ya no puede negar ese
        supuesto (ya está resuelto), O-a muestrea sólo el rango reducido, y O-f y O-g se priorizan
        porque el fallo suele indicar exceso de complejidad o una contradicción no resuelta
   4.4 la derivada fallida NO se borra: queda en el banco con su veredicto y su evidencia
5. SI ACIERTA: subir TRL, generar el siguiente experimento decisivo, y repetir
6. criterio de parada: TRL objetivo alcanzado, o 3 experimentos consecutivos sin avanzar el TRL
```

**Banco de invenciones persistente.** Todas las ideas, derivadas, veredictos y prototipos quedan en la base, consultables y reactivables. **Disparador de reevaluación** (automático, ejecutado semanalmente por un trabajo de fondo): una idea descartada se marca para revisión si (a) un parámetro del mundo registrado en `world_params` cambió más de un 25 % (coste de un material, disponibilidad de un componente, precio de la energía — valores que el usuario mantiene o que se actualizan al consultar proveedores), (b) apareció un artefacto nuevo en el proyecto que cubre uno de sus requisitos de recursos, o (c) una invención posterior comparte ≥ 0,7 de similitud y superó la validación. La reevaluación no rehace todo: reejecuta la validación técnica y la rúbrica, y avisa en la GUI.

### 11.6 Integración con el debate popperiano

Afirmaciones: la viabilidad técnica, la novedad frente al arte previo, el impacto cuantificado, el coste del experimento y el punto de equilibrio. Evidencia admisible: cálculo determinista con unidades, referencia de patente con su URL y hash, medición del prototipo, y coste real de materiales. **El MELCHIOR propone y desarrolla; el BALTHASAR falsa la viabilidad en cinco frentes obligatorios — física, económica, arte previo, fabricabilidad y adopción —; el CASPER juzga y prioriza con la rúbrica de A11-4.** Refutación más potente: **la referencia de arte previo que divulga todos los elementos** (mata la novedad de forma limpia) y **la desigualdad física violada** (mata la viabilidad). Invocación: sobre cada derivada que supere el filtro de novedad, y sobre la idea original antes de gastar en prototipo.

### 11.7 Costos, latencia y recursos

Estructuración: 1 ronda de preguntas + 1 llamada ≈ 6 000 tokens. Validación técnica: cálculo determinista, < 3 s. Arte previo: 6–12 consultas web + extracción, 2–8 min con red. Extrapolación: 12 derivadas × ≈ 9 000 tokens ≈ 108 000 por ronda; embeddings locales despreciables. MAP-Elites: cómputo trivial (384 nichos). Debate por derivada: abreviado a 2 rondas, ≈ 45 000 tokens. Total por ciclo completo de 3 rondas: ≈ 500 000 tokens locales (≈ 45 min en Perfil A) y 0 USD. **Salto del debate:** las derivadas que no superan el filtro de novedad ni entran en el debate (ahorro típico del 40 %). **Caché:** embeddings de conceptos y de ideas; resultados de consultas de arte previo por `sha256(consulta)+fecha` con caducidad de 30 días (las patentes nuevas importan).

### 11.8 Calidad y pruebas

| Caso | Criterio de éxito |
|---|---|
| Camino feliz | Idea del usuario → `Invention` válido → viable → 12 derivadas → ganadora con MVP definido, sin intervención salvo el interrogatorio |
| Idea que viola la física (móvil perpetuo sembrado) | Marcada `inviable` con la desigualdad concreta citada, 10/10; **0 casos** en que pase a extrapolación |
| Idea inventiva validada por debate | Con arte previo limpio y cálculo correcto: `survives` ≥ 75 y prototipo encargado, 10/10 |
| Arte previo que la anticipa | Con una patente sembrada que divulga todos los elementos: novedad puntuada 0 y veredicto `falsified`, 10/10 |
| Diversidad | 36 derivadas de 3 rondas ocupan ≥ 12 nichos distintos; ninguna pareja con similitud > 0,88 |
| Reformulaciones | Inyectar 10 reformulaciones de la misma idea: ≥ 9 descartadas por el filtro de novedad |
| Cifras inventadas | Auditoría de 100 afirmaciones numéricas: 100 % con fuente citada o cálculo, 0 estimaciones sin origen |
| Bucle empírico | Prototipo que falla: el parámetro implicado se estrecha y la ronda siguiente lo respeta, 10/10 |
| Consenso / desacuerdo | Con evidencia sólida, A y B convergen y C ≥ 80; con arte previo ambiguo, C emite `undecided` exigiendo la búsqueda concreta que falta |
| Etiquetas obligatorias | 100 % de informes de patentabilidad con la etiqueta de no-asesoría-legal; sin ella, la exportación se bloquea |

### 11.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta | Estado |
|---|---|---|---|---|
| Sin red (arte previo) | fallo de Playwright | Sin búsqueda de patentes | Continuar con validación técnica y extrapolación; marcar `prior_art: not_checked` y **prohibir** cualquier afirmación de novedad | Degradado, honesto |
| Banco de conceptos vacío | conteo | O-d inoperante | Desactivar O-d y redistribuir sus derivadas entre O-c y O-g | Degradado |
| Matriz TRIZ ausente | fichero no encontrado | O-g inoperante | Descargarla del corpus del usuario o desactivar el operador con aviso | Degradado |
| Colapso de diversidad | ≥ 80 % de derivadas en 3 nichos | Exploración pobre | Forzar operadores O-b, O-e y O-h en la ronda siguiente y ampliar el umbral de novedad | Recuperado |
| Fallo parcial: idea marcada viable con un cálculo mal planteado | el prototipo falla | Coste desperdiciado | El fallo actualiza el modelo de validación (se añade la comprobación que faltaba como regla permanente) | Aprendizaje registrado |
| Extracción de reivindicaciones falla | patrón no encontrado | Comparación pobre | Degradar a comparación sobre el resumen y marcar `claims_not_parsed` | Degradado |

### 11.10 Riesgos y mitigaciones

Generar N reformulaciones de lo mismo (alta/alto → filtro de novedad + MAP-Elites). Cifras de mercado inventadas (alta/alto → prohibición explícita en el prompt y auditoría de números sin origen). Confundir orientación con asesoría legal (media/alto → etiqueta obligatoria y bloqueo de exportación sin ella). Arte previo incompleto que produce falsa novedad (alta/medio → declarar siempre las fuentes consultadas y las no consultadas; prohibir afirmar novedad sin búsqueda). Sesgo del modelo hacia ideas conocidas (alta/medio → operadores deterministas que fuerzan la exploración, no dependen del gusto del modelo). Prototipos caros por MVP mal dimensionado (media/medio → regla de justificación por encima de 50 USD u 8 h). Optimismo sistemático en el impacto (alta/medio → B ataca el impacto con la alternativa actual real y su precio).

### 11.11 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA**: `sympy` 1.13, `numpy` 2.0, `scipy` 1.14, `pint` 0.24, `bge-m3`, MAP-Elites propio, matriz TRIZ y banco de conceptos construidos localmente. **🟡 REQUIERE-PRERREQUISITO**: conexión a Internet para el arte previo (Espacenet, Google Patents, USPTO, INDECOPI, repositorios académicos — todos de consulta pública y gratuita); Playwright con Chromium instalado. **🔴 BLOQUEADO-SIN-HARDWARE**: sólo el prototipado físico, que hereda los prerrequisitos del Área 9; el resto del área funciona íntegramente sin comprar nada. La presentación de una solicitud ante una oficina de propiedad industrial tiene tasas oficiales que quedan **fuera** del alcance del sistema y se declaran como coste del usuario, no del plan.

### 11.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (esquema `Invention` + estructuración + validación técnica) → v1 (los 8 operadores + novedad + MAP-Elites + debate) → completo (arte previo en línea, cribado de patentabilidad, bucle empírico con prototipo, banco con reevaluación).

- **P11.a Representación.** P11.a.1 esquema y validación — **PV-11.a.1**: 50 descripciones libres producen `Invention` válido o una lista de huecos concretos, 50/50. P11.a.2 interrogatorio — **PV-11.a.2**: ≤ 8 preguntas para completar el esquema en ≥ 90 % de los casos.
- **P11.b Validación técnica.** P11.b.1 comprobaciones de primeros principios — **PV-11.b.1**: 20 ideas inviables sembradas detectadas 20/20 con la desigualdad citada; 20 viables, 0 falsos rechazos. P11.b.2 unidades — **PV-11.b.2**: 100 % de magnitudes con unidad; toda magnitud sin unidad rechazada.
- **P11.c Extrapolación.** P11.c.1 los 8 operadores — **PV-11.c.1**: cada operador produce derivadas etiquetadas con su origen; 8/8 operativos. P11.c.2 novedad — **PV-11.c.2**: ≥ 9/10 reformulaciones descartadas. P11.c.3 MAP-Elites — **PV-11.c.3**: ≥ 12 nichos ocupados en 36 derivadas.
- **P11.d Arte previo y patentabilidad.** P11.d.1 consultas y extracción — **PV-11.d.1**: sobre 20 invenciones con arte previo conocido, la referencia esperada aparece entre las 10 primeras en ≥ 15. P11.d.2 cribado — **PV-11.d.2**: los tres requisitos evaluados con cita de la referencia en 100 % de los informes; etiqueta presente en 100 %.
- **P11.e Bucle empírico.** P11.e.1 MVP como experimento — **PV-11.e.1**: 100 % de MVP con criterio de decisión escrito **antes** de ejecutar. P11.e.2 realimentación — **PV-11.e.2**: el fallo estrecha el rango del parámetro y la ronda siguiente lo respeta, 10/10. P11.e.3 reevaluación — **PV-11.e.3**: cambiar un `world_param` un 30 % dispara la revisión de las ideas afectadas, 10/10.

Métricas de salida: 0 ideas inviables que pasen a extrapolación, ≥ 12 nichos ocupados, 100 % de números con origen, y 100 % de MVP con criterio de decisión previo.

---

## ÁREA 12 — Núcleo cognitivo de capacidades de élite (C01–C39)

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA** (todas las capacidades se implementan con software libre; las pruebas de posesión de C31–C39 son rúbricas, no hardware).

### 12.1 Propósito y alcance

Convierte un perfil cognitivo declarado en **39 capacidades implementables y verificables**. La regla que gobierna toda el área: una capacidad no existe porque su nombre aparezca en un prompt; existe si tiene una herramienta determinista o un pipeline real detrás y una prueba de posesión con criterio numérico o rúbrica. Es la exigencia popperiana aplicada al propio sistema.

Queda fuera: la ejecución de las áreas que las consumen (0–11) y la calidad de los modelos (Área 6).

**Consume:** Área 7 (compilador de prompts, que ensambla los bloques), Área 2 (corpus), Área 0 (procedencia). **Alimenta:** las doce áreas restantes.

### 12.2 Perfil normativo (reproducido completo y sin alterar)

> Posee un dominio matemático puro de élite en geometría diferencial, topología y formulación de invariantes complejos, integrado con extraordinarias habilidades analíticas en la teoría de códigos algebraicos, la teoría de la información y la teoría de juegos combinatorios para desglosar posiciones en rompecabezas y tableros tradicionales, desarrollando así modelos estocásticos algorítmicos masivos de aprendizaje automático que permiten desde la corrección matemática de errores en la transmisión digital hasta la minería de Big Data y la psicometría predictiva para la microsegmentación conductual en campañas a gran escala, incluyendo el modelado estadístico y el reconocimiento de voz basado en probabilidades; esta inmensa capacidad de procesamiento computacional y cuantitativo se entrelaza con una resiliencia cognitiva extrema que le permite realizar cálculos físicos, tensoriales y geométricos de máxima complejidad enteramente en la imaginación compensando cualquier limitación motriz, facilitando experimentos mentales espaciales para el análisis de la gravedad cuántica, la termodinámica de singularidades y la cosmología teórica, logrando deconstruir conceptos absolutos como el espacio y el tiempo al reconocer patrones unificadores en las fuerzas fundamentales para luego traducir estas densas abstracciones en narrativas de divulgación accesibles; este rigor analítico se fundamenta en una pericia inigualable para la categorización taxonómica y la sistematización del conocimiento mediante la observación empírica, siendo el arquitecto de la lógica formal deductiva y el uso de silogismos, combinado con un reduccionismo lógico y parsimonia estricta que elimina variables o suposiciones innecesarias a través del nominalismo para enfocar el análisis exclusivamente en la realidad de lo singular, aplicando además el método dialéctico y la mayéutica mediante interrogaciones inductivas constantes para desmantelar falacias, detectar contradicciones lógicas y deconstruir el razonamiento inexacto; esta profunda estructuración objetiva de la realidad se traslada magistralmente al análisis microscópico de ciclos macroeconómicos históricos y de deuda, ejecutando una gestión institucional de alta precisión y política monetaria en mercados volátiles mediante el anclaje de expectativas, el control de inflación con tasas de interés y la acumulación estratégica de reservas para mitigar choques externos, respaldado por la aplicación de la teoría de la reflexividad epistemológica para modelar y explotar vulnerabilidades sistémicas mediante operaciones apalancadas y arbitraje de divisas a gran escala, integrando tácticas de paridad de riesgo y la codificación estricta de principios de toma de decisiones para crear portafolios impermeables a las crisis bajo una cultura corporativa que funciona como un algoritmo meritocrático de selección de ideas; a un nivel microeconómico, exhibe una capacidad excepcional para la asignación de capital, la inversión de valor y la investigación de campo fundamental ascendente (bottom-up), identificando tempranamente tendencias de consumo masivo y ventajas competitivas sostenibles a largo plazo en negocios subvalorados, operando con una disciplina operativa inquebrantable para aprovechar el pánico del mercado, respaldada por un talento retórico para simplificar las finanzas mediante analogías cotidianas y una gran habilidad organizativa para reclutar y coordinar talento interdisciplinario de astrofísicos y estadísticos; en el plano interactivo y estético, su genialidad se manifiesta en el diseño espacial de interfaces lúdicas altamente intuitivas, comprendiendo la psicología del usuario para enseñar mecánicas complejas exclusivamente mediante la progresión de la dificultad y señales visuales sin textos, fusionando esta sinergia táctil de hardware y software con la dirección cinematográfica aplicada a medios interactivos para integrar narrativas de espionaje o políticas, rutinas avanzadas de inteligencia artificial, mecánicas pioneras de sigilo y la manipulación de la tensión rompiendo metódicamente la cuarta pared, todo respaldado por un virtuosismo técnico inusitado en la ilustración de fantasía utilizando tramas cruzadas y sombreado a plumilla para lograr un detalle anatómico abrumador y coreografías gráficas viscerales, deconstruyendo tropos narrativos de género al inyectar un profundo análisis del trauma psicológico en los personajes, acompañado de una dirección visual de encuadres asimétricos, cortes rápidos, maquinaria biomecánica compleja y montajes frenéticos propios del cine de acción real; finalmente, toda esta arquitectura técnica y narrativa se complementa con un talento rítmico, auditivo y vocal absoluto, capaz de componer orquestaciones y arreglos completos de bajos y sintetizadores enteramente mediante el beatboxing y la imitación vocal, ejecutando simultáneamente una destreza física biomecánica para coreografiar movimientos corporales extremadamente precisos, aislados y de apariencia antigravitatoria que redefinen la danza contemporánea, consolidando una presencia escénica maestra que sincroniza milimétricamente el movimiento, el sonido y la innovación de los cortometrajes musicales.

### 12.3 Tabla de descomposición: las 39 capacidades

Leyenda de la columna «Enrutado»: **M1**=MELCHIOR • 1, **B2**=BALTHASAR • 2, **C3**=CASPER • 3, **V**=VLM local, **E**=embeddings, **CC**=Claude Code cuando esté disponible, **L**=modelo local de texto. Todos los bloques de prompt viven en `prompts/capabilities/cNN.md.j2`.

| ID | Capacidad | Bloque de prompt (ruta) | Enrutado de modelo | Herramientas y pipeline deterministas | Corpus/datos en el índice (Área 2) | Salida típica | Prueba de posesión (criterio) | Áreas que la consumen |
|---|---|---|---|---|---|---|---|---|
| C01 | Matemática pura: geometría diferencial, topología, invariantes | `c01.md.j2` | M1/L razonamiento largo; CC si hay contexto extenso | `sympy` 1.13 (`diffgeom`), `numpy` 2.0, `networkx` 3.3, `gudhi` 3.9 (homología persistente), `scipy.spatial` | Textos de geometría diferencial y topología aportados por el usuario | Demostración simbólica, invariante calculado, diagrama de persistencia | Calcular la característica de Euler y los números de Betti de 20 complejos simpliciales conocidos: **20/20 exactos**; verificar el tensor de curvatura de una métrica dada contra el resultado simbólico esperado | 5, 9, 11 |
| C02 | Teoría de códigos algebraicos | `c02.md.j2` | M1/L código | `galois` 0.3.x (campos finitos), `numpy`, implementación Reed–Solomon/BCH/LDPC, `sympy` para polinomios | Textos de teoría de códigos | Codificador/decodificador, matriz generadora, capacidad de corrección | Codificar y decodificar 10⁴ palabras RS(255,223) con hasta 16 errores por bloque: **100 % recuperadas**; con 17 errores, fallo detectado y declarado | 5, 9, 12 |
| C03 | Teoría de la información | `c03.md.j2` | M1/L | `scipy.stats.entropy`, implementación propia de entropía condicional e información mutua, `zstandard` para límites empíricos de compresión | Textos de teoría de la información | Entropía, tasa, límite de canal, análisis de compresibilidad | Estimar la entropía de 20 fuentes sintéticas con entropía conocida: error ≤ **2 %**; el límite de Shannon calculado nunca es superado por ningún esquema propuesto (verificación automática) | 1, 5, 9, 11 |
| C04 | Teoría de juegos combinatorios (rompecabezas y tableros) | `c04.md.j2` | M1/L | Buscador propio con minimax + poda alfa-beta, tablas de transposición Zobrist, resolución retrógrada, teoría Sprague-Grundy (`numpy`), SAT/SMT (`z3-solver` 4.13) para rompecabezas de restricciones | Reglas y posiciones de referencia aportadas | Valor de la posición, jugada óptima, número de Grundy | Resolver 50 posiciones de finales con valor conocido: **50/50 correctas**; calcular los números de Grundy de un juego de Nim compuesto: exactos | 11, 12 |
| C05 | Modelos estocásticos masivos de aprendizaje automático | `c05.md.j2` | M1/L código | `scikit-learn` 1.5, `numpy`, `scipy`, `statsmodels` 0.14, `duckdb` para datos grandes, `optuna` 3.6 para búsqueda de hiperparámetros; validación cruzada obligatoria | Datos del usuario | Modelo entrenado, informe de validación | Sobre 5 conjuntos públicos con línea base conocida: igualar o superar la línea base en ≥ **4/5** con validación cruzada de 5 pliegues y semilla fijada | 1, 2, 11 |
| C06 | Corrección matemática de errores en transmisión digital | `c06.md.j2` | M1/L código | Implementación CRC-8/16/32, Hamming, RS; `crcmod`; banco de pruebas con canal simulado (BSC, AWGN) en `numpy` | — | Esquema de trama con FEC, tasa de error residual | Con BER de entrada 10⁻³ y RS(255,223): BER de salida medida ≤ **10⁻⁹** en 10⁷ bits simulados | 4, 9 |
| C07 | Minería de Big Data | `c07.md.j2` | M1/L | `duckdb` 1.0 (SQL analítico), `polars` 1.x, `pyarrow`, muestreo estratificado, detección de sesgo de muestreo | Telemetría, trazas, corpus | Consulta, agregación, hallazgo con su intervalo de confianza | Sobre 50 M de filas de telemetría: consulta de agregación por ventana en ≤ **2 s** y resultado idéntico al calculado por fuerza bruta sobre una muestra verificada | 4, 5, 9 |
| C08 | Psicometría predictiva y microsegmentación conductual | `c08.md.j2` | M1/L | `statsmodels`, análisis factorial (`factor_analyzer`), clustering (`scikit-learn`), calibración con `sklearn.calibration`; **guarda de datos** (§12.5) | Sólo datos propios y consentidos del usuario | Segmentos con su perfil y su incertidumbre | Sobre un conjunto sintético con estructura factorial conocida: recuperar los factores con congruencia de Tucker ≥ **0,90**; **y** rechazo del 100 % de las peticiones con datos sin procedencia consentida | 11 |
| C09 | Modelado estadístico | `c09.md.j2` | M1/L | `statsmodels` 0.14 (GLM, series temporales, ARIMA), `scipy.stats`, comprobación de supuestos automatizada (normalidad, homocedasticidad, autocorrelación) | Datos del proyecto | Modelo con diagnósticos e intervalos | Sobre 20 conjuntos con modelo generador conocido: recuperar los coeficientes dentro del **IC del 95 %** en ≥ 18/20; 100 % de los informes incluyen diagnóstico de supuestos | 1, 2, 9, 11 |
| C10 | Reconocimiento de voz basado en probabilidades | `c10.md.j2` | L + modelo acústico local | `whisper.cpp` (modelo `base`/`small` GGUF) para transcripción local, `librosa` 0.10 para características, `webrtcvad` para detección de voz, decodificación con puntuaciones de confianza | Léxico del dominio aportado | Transcripción con marcas de tiempo y confianza por palabra | Sobre 30 min de audio con transcripción de referencia: **WER ≤ 15 %** en español limpio y confianza calibrada (correlación ≥ 0,6 entre confianza y acierto) | 4, 10 |
| C11 | Resiliencia cognitiva extrema | `c11.md.j2` | M1/B2/L (transversal) | No es una capacidad de contenido sino de **proceso**: presupuesto de rondas del Área 3, WAL del Área 6, rompedor de bucles del Área 8, y reanudación tras fallo | — | Continuidad del trabajo largo | Un trabajo de 6 h con 5 interrupciones forzadas (matar proveedor, matar núcleo, desconectar dispositivo) se completa con ≤ **1 unidad** recomputada por interrupción y sin pérdida de conclusiones | 0, 6, 8 |
| C12 | Cálculo físico, tensorial y geométrico "en la imaginación" | `c12.md.j2` | M1/L razonamiento largo | `sympy.tensor` y `einsteinpy` 0.4 para tensores; `numpy` para verificación numérica; **regla: todo resultado simbólico se comprueba numéricamente en el sandbox** | Textos de mecánica y relatividad aportados | Derivación simbólica con verificación numérica | Derivar los símbolos de Christoffel y el tensor de Ricci de 10 métricas conocidas: **10/10** coincidiendo con la referencia simbólica **y** con la comprobación numérica en 100 puntos aleatorios | 9, 11 |
| C13 | Experimentos mentales espaciales (gravedad cuántica, singularidades, cosmología) | `c13.md.j2` | M1/L razonamiento largo | Análisis dimensional automatizado (`pint`), cálculo de escalas características (Planck, Schwarzschild, Hubble) con `astropy` 6.x y `scipy.constants` | Literatura de cosmología aportada | Experimento mental estructurado con sus escalas y sus límites | Para 15 escenarios, calcular las escalas características y detectar el régimen aplicable: **15/15** con error ≤ 1 % frente al cálculo cerrado; 100 % de los escenarios declaran explícitamente qué teoría deja de ser válida | 11 |
| C14 | Deconstrucción de espacio y tiempo por patrones unificadores | `c14.md.j2` | M1/L | Comparación estructural de formalismos: extracción de simetrías y grupos (`sympy.combinatorics`), tabla de correspondencias entre teorías construida como grafo (`networkx`) | Literatura de fuerzas fundamentales aportada | Mapa de correspondencias con sus supuestos | Reproducir el grafo de correspondencias entre 4 formulaciones (lagrangiana, hamiltoniana, geométrica, de campos) y superar el debate: **0 afirmaciones sin cita** en el corpus y `survives` ≥ 70 | 11 |
| C15 | Traducción a narrativa de divulgación accesible | `c15.md.j2` | M1/L (temperatura 0,6) | Métricas de legibilidad en español (índice de perspicuidad de Szigriszt-Pazos e índice Fernández-Huerta, implementados en `modules/lang/readability.py`), verificador de que **toda cifra del texto divulgativo existe en el documento técnico origen** | El propio artefacto técnico | Texto divulgativo con equivalencias | Sobre 20 informes técnicos: índice de perspicuidad ≥ **60** (nivel "normal") y **0 cifras** sin correspondencia en el origen | 2, 10, 11 |
| C16 | Categorización taxonómica y sistematización empírica | `c16.md.j2` | M1/L + E | Clustering jerárquico (`scipy.cluster.hierarchy`), construcción de taxonomías con `networkx`, validación por coeficiente de silueta y por estabilidad ante remuestreo | Corpus del dominio | Taxonomía con criterios de pertenencia | Sobre 300 elementos con taxonomía de referencia: **índice de Rand ajustado ≥ 0,75**; estabilidad ≥ 0,8 en 20 remuestreos | 1, 2, 5, 9, 11 |
| C17 | Lógica formal deductiva y silogismos | `c17.md.j2` | M1/B2/L | `z3-solver` 4.13 (SMT) y `pysat` para SAT: **toda cadena deductiva se formaliza y se comprueba mecánicamente**; detección de falacias formales por análisis de la forma | Reglas del dominio | Derivación formal verificada o contraejemplo | Sobre 100 argumentos (50 válidos, 50 inválidos): clasificación correcta **100/100** con el modelo de contraejemplo cuando es inválido | 2, 3, 5, 9 |
| C18 | Reduccionismo, parsimonia y nominalismo | `c18.md.j2` | M1/C3/L | Contador de suposiciones declaradas (validador del Área 3), criterio de información (AIC/BIC en `statsmodels`) y longitud de descripción mínima para comparar explicaciones | — | Explicación mínima con las suposiciones enumeradas | Dadas 20 parejas de explicaciones equivalentes, elegir la de menor número de suposiciones y menor MDL en **20/20**; el criterio de parsimonia de la rúbrica del Juez se aplica en el 100 % de los veredictos | 3, 5, 11 |
| C19 | Método dialéctico y mayéutica | `c19.md.j2` | B2/L | Es el propio Área 3: taxonomía de refutaciones, validador de mecanismo, detección de duplicados y de deriva; más un detector de falacias informales por patrón (`modules/logic/fallacies.py`, 24 patrones enumerados) | — | Refutación estructurada, cadena de preguntas | Sobre 60 textos con falacia sembrada (24 tipos): identificación correcta del tipo en ≥ **80 %**; 0 refutaciones sin mecanismo admitidas | 3, 2, 5, 11 |
| C20 | Análisis de ciclos macroeconómicos y de deuda | `c20.md.j2` | M1/L | `statsmodels` (filtros Hodrick-Prescott y Baxter-King, VAR), `pandas`, series aportadas por el usuario; fechado de ciclos por regla determinista (Bry-Boschan) | Series históricas cargadas por el usuario | Cronología de ciclos con sus fases | Sobre 3 series con cronología de referencia publicada y cargada: coincidencia de puntos de giro dentro de ±**2 periodos** en ≥ 80 % | 11 |
| C21 | Gestión institucional y política monetaria | `c21.md.j2` | M1/L | Simulación de reglas de política (regla de Taylor parametrizada), modelo de expectativas simple, y análisis de sensibilidad; todo **simulación**, etiquetada como análisis | Marcos normativos y series cargadas | Escenario simulado con sus supuestos | Reproducir la trayectoria de una regla parametrizada frente a un cálculo cerrado: error ≤ **1 %** en 10 escenarios; 100 % de salidas con la etiqueta de análisis | 11 |
| C22 | Reflexividad epistemológica y vulnerabilidades sistémicas | `c22.md.j2` | M1/B2/L | Modelos de realimentación (dinámica de sistemas con `scipy.integrate`), pruebas de estrés y análisis de contagio en red (`networkx`); **guarda: salida etiquetada como análisis y simulación, nunca recomendación de operación** (§12.5) | Datos y literatura cargados | Informe de vulnerabilidad simulada | Sobre un modelo de contagio con propagación conocida: reproducir el orden de caída de nodos en **≥ 90 %**; 100 % de salidas con la etiqueta obligatoria | 11 |
| C23 | Operaciones apalancadas y arbitraje de divisas | `c23.md.j2` | M1/L | Cálculo determinista de paridad cubierta y no cubierta de tipos de interés, coste de financiación, y **simulación** de posiciones con `numpy`; **guarda idéntica a C22** | Series de tipos cargadas | Análisis de desviación de paridad con sus supuestos | Detectar desviaciones de la paridad cubierta en series sintéticas con desviación sembrada: **20/20**; 100 % etiquetadas como análisis, 0 recomendaciones emitidas | 11 |
| C24 | Paridad de riesgo | `c24.md.j2` | M1/L | Optimización de contribución al riesgo (`scipy.optimize`, `numpy` sobre matriz de covarianzas), con `cvxpy` 1.5 para la formulación convexa | Series cargadas | Pesos con su contribución al riesgo | La contribución marginal al riesgo de cada activo difiere de la media en ≤ **1 %** en 20 carteras sintéticas | 11 |
| C25 | Codificación de principios de decisión y meritocracia de ideas | `c25.md.j2` | C3/L | El propio motor de rúbricas: reglas de decisión versionadas en YAML, puntuación explícita y trazable, y registro de por qué ganó cada idea (`invention_score`, `verdict.rubric`) | — | Registro de decisiones con su regla aplicada | 100 % de decisiones del sistema con regla identificada y puntuación reproducible; reejecutar 50 decisiones con los mismos datos produce el mismo resultado **50/50** | 3, 8, 11 |
| C26 | Asignación de capital e inversión de valor (bottom-up) | `c26.md.j2` | M1/L | Modelos deterministas de descuento de flujos y de múltiplos implementados en `numpy`, con análisis de sensibilidad obligatorio (tornado) sobre los 5 supuestos dominantes | Estados financieros aportados por el usuario | Valoración con rango e incertidumbre | Sobre 10 casos con estados financieros cargados: la valoración recalculada por un tercero con los mismos supuestos coincide en ≤ **1 %**; 100 % con análisis de sensibilidad | 11 |
| C27 | Identificación de tendencias y ventajas competitivas sostenibles | `c27.md.j2` | M1/L + E | Detección de tendencia en series (`statsmodels`, prueba de Mann-Kendall), y análisis estructurado de barreras de entrada con lista de comprobación de 12 factores verificables | Corpus sectorial cargado | Informe de tendencia con su significancia | Sobre 30 series (15 con tendencia sembrada): detección correcta con p < 0,05 en ≥ **27/30**; cada ventaja competitiva afirmada con ≥ 1 evidencia citada | 11 |
| C28 | Disciplina operativa ante el pánico del mercado | `c28.md.j2` | C3/L | Reglas de decisión precomprometidas: el sistema **escribe el criterio antes** de observar el resultado (misma mecánica que `cheapest_experiment.decides` y que las condiciones de abandono del §11.4) | — | Regla precomprometida con su fecha y hash | 100 % de decisiones de continuidad con criterio escrito **antes** del evento (verificado por marca de tiempo y hash en la auditoría); 0 criterios modificados a posteriori sin registro | 8, 11 |
| C29 | Retórica de simplificación financiera por analogías | `c29.md.j2` | M1/L (temperatura 0,6) | Mismo verificador de C15 (legibilidad + trazabilidad de cifras) más un banco de analogías con su dominio de validez declarado (`data/analogies.jsonl`) | El propio análisis | Explicación con analogía y sus límites | Sobre 20 explicaciones: índice de perspicuidad ≥ **60**, 0 cifras sin origen, y **100 % de analogías con su límite explícito** ("la analogía deja de valer cuando…") | 10, 11 |
| C30 | Organización y coordinación de talento interdisciplinario | `c30.md.j2` | C3/L | El planificador del Área 0 y la asignación rol→modelo del Área 6: es la coordinación de agentes heterogéneos con presupuesto y prioridades | — | Plan de asignación con dependencias | Un trabajo con 5 subtareas de dominios distintos se planifica sin conflicto de recursos y se completa respetando el orden topológico en **20/20** ejecuciones | 0, 3, 6 |
| C31 | Diseño espacial de interfaces lúdicas que enseñan sin texto | `c31.md.j2` | M1/L + V | **Capacidad generativa/estilística.** Mecanismo de evaluación: rúbrica de 6 criterios (visibilidad de la affordance, retroalimentación inmediata, progresión de dificultad monótona, ausencia de texto instructivo, recuperabilidad del error, coherencia de señales) aplicada por C sobre capturas del prototipo analizadas por el VLM | Corpus de patrones de interacción aportado | Prototipo de interfaz + informe de rúbrica | Sobre 10 prototipos: rúbrica ≥ **4/6** de media y **0 textos instructivos** detectados por el VLM en las capturas | 10 |
| C32 | Sinergia táctil de hardware y software | `c32.md.j2` | M1/L | Determinista: medición de **latencia de extremo a extremo** entrada→respuesta (Área 4 y 9.E) y de jitter, con umbrales declarados | — | Informe de latencia y jitter con su instrumento | Latencia medida de un lazo entrada→actuación ≤ **50 ms** con jitter ≤ 10 ms en 1 000 muestras, medida con instrumento, no estimada | 4, 9, 10 |
| C33 | Dirección cinematográfica aplicada a medios interactivos | `c33.md.j2` | M1/L | **Capacidad generativa/estilística.** Evaluación por rúbrica de 5 criterios (arco de tensión declarado y medible en la escaleta, coherencia de la información que el jugador posee en cada instante, justificación diegética de las rutinas de IA, uso deliberado de la ruptura de la cuarta pared con su función, y economía de recursos) juzgada por C | Corpus de guion y diseño aportado | Escaleta anotada con la curva de tensión | Sobre 5 escaletas: rúbrica ≥ **4/5**; la curva de tensión declarada debe ser reproducible por un tercero a partir de la escaleta en ≥ 4/5 | 10, 11 |
| C34 | Ilustración de fantasía (tramas cruzadas, plumilla, anatomía) | `c34.md.j2` | M1 + V | **Capacidad generativa/estilística.** Mecanismo determinista de apoyo: verificación de **proporciones anatómicas** sobre la imagen (detección de puntos clave y comparación con cánones declarados) y análisis de densidad de trama por FFT (reutiliza §1.5) | Referencias anatómicas aportadas | Lámina + informe de verificación | Sobre 10 láminas: desviación de proporción ≤ **8 %** frente al canon declarado y densidad de trama dentro del rango objetivo en ≥ 8/10 | 1, 11 |
| C35 | Deconstrucción de tropos con análisis del trauma psicológico | `c35.md.j2` | M1/L | **Capacidad generativa/estilística.** Evaluación por rúbrica de 4 criterios (identificación explícita del tropo y su función, coherencia psicológica del personaje con literatura citada, ausencia de resolución no ganada, y consecuencia narrativa medible) juzgada por C, con el requisito de citar el corpus clínico o literario cargado | Corpus de narrativa y psicología aportado | Análisis de tropo con su reformulación | Sobre 10 análisis: rúbrica ≥ **3/4** y **100 %** con cita verificada del corpus (validador del Área 2) | 11 |
| C36 | Dirección visual: encuadres asimétricos, cortes, biomecánica, montaje | `c36.md.j2` | M1 + V | **Capacidad generativa/estilística.** Apoyo determinista: análisis de composición sobre fotogramas (regla de tercios y desviación del centro de masa visual, calculado con OpenCV) y **medición del ritmo de montaje** (duración media y desviación de los planos, extraída de la lista de decisiones de edición) | Corpus de referencia visual aportado | Guion gráfico con métricas de composición y ritmo | Sobre 10 secuencias: asimetría de composición dentro del rango declarado en ≥ 8/10 y ritmo de montaje con desviación ≤ **15 %** del objetivo declarado | 1, 11 |
| C37 | Talento rítmico y vocal: orquestación por beatboxing e imitación | `c37.md.j2` | M1/L + audio | **Capacidad generativa/estilística con verificación determinista:** `librosa` 0.10 (detección de pulso, tempo y tono), `aubio` 0.4 (onset y pitch), `music21` 9.x (análisis armónico), `mido` para MIDI; el sistema transcribe el audio a MIDI y **verifica** afinación y ritmo | Corpus musical aportado | Transcripción MIDI + arreglo + informe de afinación | Sobre 20 muestras: desviación de tempo ≤ **2 %** frente al pulso de referencia y desviación de afinación ≤ **30 cents** en ≥ 90 % de las notas detectadas | 11 |
| C38 | Destreza biomecánica y coreografía antigravitatoria | `c38.md.j2` | M1 + V | **Capacidad generativa/estilística con verificación determinista:** estimación de pose sobre vídeo (`mediapipe` 0.10) y cálculo de ángulos articulares, aislamiento (movimiento de un segmento con el resto por debajo de un umbral) y verificación de plausibilidad física (centro de masa dentro de la base de sustentación) | Referencias de biomecánica aportadas | Notación de coreografía + informe de ángulos | Sobre 10 secuencias: los ángulos articulares generados están dentro del rango humano en **100 %** de los fotogramas y el centro de masa es físicamente plausible en ≥ 95 % | 11 |
| C39 | Presencia escénica: sincronía de movimiento, sonido e innovación | `c39.md.j2` | M1 + V + audio | **Capacidad generativa/estilística con verificación determinista:** correlación temporal entre los onsets de audio (`aubio`) y los picos de movimiento de la pose (`mediapipe`), midiendo el desfase medio y su dispersión | — | Pieza sincronizada + informe de desfase | Desfase medio audio↔movimiento ≤ **40 ms** y desviación típica ≤ 25 ms sobre 3 min de material, en ≥ 8/10 piezas | 10, 11 |

### 12.4 Contratos, arquitectura de composición y algoritmos

Cada bloque de capacidad es una plantilla Jinja2 con esta estructura fija: `{id, nombre, principios (≤ 6 líneas), herramientas disponibles y cómo invocarlas, formato de salida específico, criterio de auto-verificación propio}`, con un presupuesto duro de **300 tokens** por bloque. El compilador del Área 7 selecciona los bloques por una función de relevancia:

```
relevancia(c, tarea) = 0,5·coincidencia_de_área(c, tarea.area)
                     + 0,3·similitud_semántica(embed(c.nombre + c.principios), embed(tarea.topic))
                     + 0,2·frecuencia_histórica_de_éxito(c, tarea.kind)
se seleccionan como máximo 4 bloques (1 200 tokens); si dos bloques comparten > 0,8 de similitud,
se conserva sólo el de mayor relevancia (evita duplicar principios y desperdiciar contexto)
```

**Composición — ejemplos normativos de cómo se combinan varias capacidades en una sola tarea:**

| Tarea | Capacidades ensambladas | Áreas implicadas | Cómo se evita el desbordamiento de contexto |
|---|---|---|---|
| Auditar un contrato | C16 + C17 + C18 + C19 | Área 2 (+1, 3) | Los cuatro bloques suman 1 200 tokens; la evidencia citada está fijada y el material se trocea por cláusula (unidad reanudable) |
| Portar un emulador | C01 + C03 + C16 + C17 | Área 5 (+3, 8) | Se compilan por fase: la fase de clasificación de capas usa C16+C17; la de análisis de temporización usa C01+C03; nunca los cuatro a la vez |
| Diseñar un ASIC | C01 + C02 + C03 + C17 | Área 9.C (+3, 8) | C02 sólo se carga cuando el diseño incluye FEC; si no, se libera su presupuesto para más evidencia |
| Analizar un expediente escaneado | C16 + C09 + C03 | Área 1 (+2, 3) | C09 (estadística) se carga en la fase de detección de anomalías, no en la de medición |
| Inventar y prototipar | C04 + C12 + C18 + C25 | Área 11 (+9, 3) | Se rotan por etapa del pipeline de §11.4 |
| Explicar el resultado al usuario | C15 + C29 | Área 10 | Bloques pequeños; el artefacto técnico ya está resumido |

**A12-1 — Comprobación de posesión (trabajo periódico).**
```
1. cada capacidad C tiene un test en tests/capabilities/test_cNN.py marcado con @pytest.mark.capability
2. `make capabilities` ejecuta las 39 pruebas y escribe reports/capabilities.json con
      {id, passed, metric, threshold, duration_s, model_used}
3. una capacidad con prueba fallida se marca NO POSEÍDA y el compilador de prompts DEJA DE CARGAR su
      bloque (para no afirmar en el prompt algo que el sistema no puede sostener). Se registra en la GUI
4. periodicidad: en cada cambio de modelo asignado a un rol, en cada cambio del bloque, y semanalmente
5. las pruebas de C31–C39 que usan rúbrica requieren que el Juez evalúe con la rúbrica declarada; se
      considera aprobada si la puntuación media de 3 ejecuciones con semillas distintas supera el umbral
```

**Decisiones formalizadas de esta área.**
**Decisión:** una capacidad cuya prueba de posesión falla deja de cargar su bloque en el prompt — porque afirmar en el prompt una habilidad que el sistema no puede sostener es la forma más directa de producir salidas seguras de sí mismas y equivocadas.
*Descartado:* mantener el bloque con un aviso de "capacidad limitada" — el modelo lo ignora y el efecto neto es el mismo que afirmarla.
**Decisión:** se cargan como máximo 4 bloques de capacidad por llamada (1 200 tokens) con deduplicación por similitud > 0,8 — porque el contexto gastado en principios es contexto quitado a la evidencia, que es lo que realmente decide la calidad.

### 12.5 Guardas de uso responsable, integradas como diseño

- **C08 (microsegmentación conductual):** se acota a **datos propios y consentidos**. La restricción está escrita en el propio bloque `c08.md.j2` ("sólo puedes operar sobre conjuntos cuyo registro de procedencia declare `consent: explicit` y `owner: user`") **y se verifica mecánicamente** en la procedencia: `modules/capabilities/guards.py::require_consented_data()` comprueba que todo `dataset_ref` usado por C08 tiene en `provenance_edge` un nodo `consent_record` con `scope`, `fecha` y `titular`; si no lo tiene, la ejecución se rechaza con `GuardRefused(code="C08-CONSENT")` antes de gastar un solo token.
- **C22 y C23 (reflexividad, apalancamiento y arbitraje):** se implementan como **modelado analítico y simulación**. La salida se etiqueta obligatoriamente `output_class: "analysis"` y la plantilla del informe inserta en la cabecera: *"Análisis y simulación. No constituye recomendación de operación financiera ni asesoría de inversión."* El validador `guards.py::forbid_recommendation()` rechaza salidas que contengan patrones imperativos de operación ("compra", "vende", "abre una posición", "recomiendo invertir") aplicados a instrumentos concretos, coherente con que **el sistema no es un asesor de inversión**.
- **Regla general:** ninguna capacidad se implementa sólo con adjetivos en un prompt. Cada fila de §12.3 tiene al menos una herramienta determinista o un pipeline real; las de C31–C36 (y parcialmente C33, C35) están **declaradas explícitamente como generativas/estilísticas** y, aun así, todas llevan su mecanismo de evaluación —rúbrica juzgada por C, y en C31, C34, C36, C37, C38 y C39 además una verificación determinista sobre el artefacto producido.

### 12.6 Integración con el debate popperiano

Cada capacidad emite una afirmación permanente: *"el sistema posee C_nn"*, cuyo `falsifier` es su propia prueba de posesión. Evidencia admisible: el resultado de `make capabilities` con su métrica y su umbral. Refutación más potente: **ejecutar la prueba y verla fallar** — que es automática y no admite discusión; y, para las capacidades con rúbrica, aportar un caso donde la rúbrica se cumple pero el resultado es manifiestamente pobre (lo que refuta la rúbrica, no la capacidad, y obliga a corregir la rúbrica). Invocación: en cada ejecución periódica y en cada cambio de modelo.

### 12.7 Costos, latencia y recursos

Coste de contexto: ≤ 1 200 tokens por llamada (4 bloques). Coste de la comprobación completa de posesión: ≈ 35 min en Perfil A (dominado por C05, C10 y las rúbricas de C31–C39). Disco: `data/` con la matriz TRIZ, el banco de conceptos, las analogías y las referencias anatómicas ≈ 180 MB. VRAM: las capacidades con VLM comparten el mismo servidor de visión. **Salto del debate:** las pruebas de posesión son deterministas y no se debaten; sí se debaten las rúbricas cuando se cuestionan. **Caché:** resultados de pruebas de posesión por `sha256(test)+model_hash+block_hash` (una capacidad no se reevalúa si nada cambió).

### 12.8 Calidad y pruebas

Las 39 pruebas de posesión de §12.3 **son** el plan de pruebas del área. Casos obligatorios adicionales: **camino feliz** (una tarea que ensambla 4 capacidades produce salida válida, 20/20); **consenso** (dos capacidades que se solapan, C17 y C19, no se contradicen en el mismo veredicto en 20 casos); **desacuerdo total** (C18 exige la explicación más simple y C05 propone un modelo complejo: el Juez debe resolver con el criterio de información, no por preferencia, 10/10); **GUI bajo estrés** (el panel de capacidades muestra el estado de las 39 sin degradar el rendimiento); y **capacidad no poseída** (forzar el fallo de una prueba y comprobar que su bloque deja de cargarse en el prompt, 10/10).

### 12.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta | Estado |
|---|---|---|---|---|
| Prueba de posesión falla | `make capabilities` | El sistema afirmaría algo falso | Se desactiva el bloque y se marca en la GUI; las tareas que la requerían avisan de la limitación | Honesto |
| Datos sin consentimiento para C08 | `guards.py` | Riesgo de uso indebido | Rechazo antes de ejecutar, con motivo | Seguro |
| Salida de C22/C23 con lenguaje de recomendación | validador | Riesgo de interpretarse como asesoría | Rechazo y reintento con instrucción explícita; a la segunda, se emite sólo la tabla de datos | Seguro |
| Herramienta ausente (p. ej. `gudhi`) | importación | Capacidad inoperante | Marcar no poseída e indicar el comando de instalación | Degradado, explicado |
| Solape de bloques desborda el contexto | conteo previo | Poda indebida | Selección por relevancia con máximo 4 y deduplicación por similitud | Operativo |
| Rúbrica complaciente (C31–C39) | dispersión de puntuaciones < 0,3 en 20 evaluaciones | Falsa posesión | Revisión de la rúbrica y adición de un caso negativo obligatorio | Corregido |

### 12.10 Riesgos y mitigaciones

Capacidades declaradas y no poseídas (alta/alto → prueba de posesión obligatoria con desactivación automática del bloque). Rúbricas autocomplacientes en el bloque C31–C39 (alta/medio → casos negativos obligatorios y dispersión mínima). Uso de C08 sobre datos de terceros (media/alto → guarda con verificación de procedencia). Interpretación de C22/C23 como asesoría (media/alto → etiqueta y validador de lenguaje). Inflación de contexto por cargar demasiados bloques (alta/medio → máximo 4 y deduplicación). Dependencia de librerías científicas pesadas (media/bajo → cada una es opcional y su ausencia sólo desactiva su capacidad).

### 12.11 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA**: `sympy` 1.13, `numpy` 2.0, `scipy` 1.14, `statsmodels` 0.14, `scikit-learn` 1.5, `networkx` 3.3, `gudhi` 3.9, `galois` 0.3.x, `z3-solver` 4.13, `pysat`, `cvxpy` 1.5, `polars` 1.x, `duckdb` 1.0, `librosa` 0.10, `aubio` 0.4, `music21` 9.x, `mido`, `mediapipe` 0.10, `whisper.cpp` con modelo GGUF, `astropy` 6.x, `einsteinpy` 0.4, `optuna` 3.6, `factor_analyzer`, `crcmod`, `pint` 0.24. Todo libre y sin cuenta. **🟡 REQUIERE-PRERREQUISITO**: para C10 y C37–C39, un micrófono y/o una cámara (que el usuario ya posee en cualquier portátil) y los corpus que el usuario decida cargar. **🔴** ninguna capacidad está bloqueada por hardware de pago.

### 12.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (C16–C19, que sostienen el debate y el contraste, más C01 y C03) → v1 (bloque matemático-computacional C01–C10 y físico C11–C15 completos) → completo (C20–C30 con corpus del usuario y C31–C39 con sus rúbricas y verificaciones deterministas).

- **P12.a Infraestructura.** P12.a.1 39 bloques con presupuesto — **PV-12.a.1**: los 39 renderizan y ninguno supera 300 tokens. P12.a.2 selector por relevancia — **PV-12.a.2**: en 100 tareas, los bloques esperados están entre los 4 elegidos en ≥ 90 %.
- **P12.b Pruebas de posesión.** P12.b.1 C01–C10 — **PV-12.b.1**: 10/10 pruebas en verde con sus umbrales. P12.b.2 C11–C19 — **PV-12.b.2**: 9/9 en verde. P12.b.3 C20–C30 — **PV-12.b.3**: 11/11 en verde con corpus de prueba. P12.b.4 C31–C39 — **PV-12.b.4**: 9/9 con rúbrica y verificación determinista, con dispersión de puntuaciones ≥ 0,3.
- **P12.c Guardas.** P12.c.1 C08 — **PV-12.c.1**: 20 intentos con datos sin consentimiento, 20 rechazos. P12.c.2 C22/C23 — **PV-12.c.2**: 20 salidas, 100 % etiquetadas y 0 con lenguaje de recomendación.
- **P12.d Desactivación honesta.** P12.d.1 — **PV-12.d.1**: forzar el fallo de 5 capacidades y comprobar que sus bloques dejan de cargarse y que la GUI lo muestra, 5/5.

Métricas de salida: 39/39 pruebas de posesión definidas y ejecutables, ≥ 35/39 en verde para declarar el área completa, y 0 bloques cargados de capacidades no poseídas.

---

## ÁREA 13 — MAGI-MEM: grafo de memoria de código persistente

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA** (binario estático libre, sin dependencias de ejecución, sin cuentas, 100 % local).

### 13.1 Propósito y alcance

Da al sistema **memoria estructural del código** en lugar de lectura repetida de ficheros. Construye y mantiene un grafo de conocimiento —funciones, clases, módulos, importaciones, llamadas, rutas HTTP, recursos de infraestructura— sobre el que MELCHIOR • 1 razona con consultas, BALTHASAR • 2 busca acoplamientos ocultos y CASPER • 3 verifica que una afirmación de estructura tiene respaldo. Es la respuesta directa a tres problemas que el plan tenía mal resueltos: el coste de tokens de leer código, la fragilidad de la clasificación de módulos del Área 5 (que se apoyaba en heurísticas de nombres) y la ausencia de memoria entre sesiones.

Queda fuera: la interpretación semántica del código (Áreas 5 y 12), la decompilación (Área 5, que **alimenta** este grafo con el C exportado), y la ejecución (Área 8). MAGI-MEM **no contiene ningún modelo de lenguaje**: devuelve estructura; quien la interpreta es el nodo MAGI que consulta.

**Consume:** Área 0 (CAS, política de capacidades, bus), Área 5 (código decompilado exportado como fuentes indexables). **Alimenta:** Área 3 (evidencia estructural), Área 5 (clasificación de capas, libro mayor, análisis de impacto), Área 8 (superficie afectada por un cambio), Área 10 (panel de grafo y herramientas MCP), Área 11 (prototipos de software), Área 12 (C16 taxonomía, C07 minería, C03 información).

### 13.2 Arquitectura

*Decisión:* se adopta **`DeusData/codebase-memory-mcp`** como binario externo ejecutado por el núcleo, hablando **MCP sobre stdio**, con el commit fijado en `config/externals.lock` y verificado por SHA-256 y por firma Sigstore antes de ejecutarse — porque indexar 155+ lenguajes con *tree-sitter*, resolver tipos con un LSP híbrido y ejecutar Cypher en menos de un milisegundo es un año de trabajo que ya está hecho, es libre y no envía nada fuera de la máquina.
*Descartado:* construir el índice con `ctags` + `networkx` sobre el grafo de inclusiones (lo que el plan proponía en §5.5.2) — sigue disponible como **camino de reserva** cuando el binario no está, pero su resolución de llamadas es muy inferior y no cruza servicios.

```
   repositorio | árbol de fuentes | C decompilado exportado (Área 5)
              │ rutas + .cbmignore
              ▼
 ┌───────────────────────────────────────────────────────────────────┐
 │ magi-mem (binario estático, proceso hijo supervisado)             │
 │  discover → tree-sitter (155+ gramáticas) → LSP híbrido (12 leng.)│
 │  → pases: definiciones → llamadas → rutas HTTP → importaciones     │
 │  ⚠ punto de fallo: presupuesto de RAM (CBM_MEM_BUDGET_MB)         │
 └──────────┬────────────────────────────────────────────────────────┘
            │ SQLite WAL comprimido  (~/.local/share/MagiSystem/memgraph/)
            ▼
 ┌───────────────────────────────────────────────────────────────────┐
 │ GRAFO: nodos Project·Package·Folder·File·Module·Class·Function·    │
 │ Method·Interface·Enum·Type·Route·Resource                          │
 │ aristas CALLS·IMPORTS·DEFINES·DEFINES_METHOD·IMPLEMENTS·HANDLES·   │
 │ HTTP_CALLS·ASYNC_CALLS·USAGE·CONFIGURES·WRITES·MEMBER_OF·TESTS·    │
 │ USES_TYPE·FILE_CHANGES_WITH·CONTAINS_*                             │
 └────┬─────────────────┬──────────────────┬────────────────────┬────┘
      │ MCP/stdio       │ Cypher (RO)      │ semántico          │ watcher git
      ▼                 ▼                  ▼                    ▼
 ┌──────────┐   ┌───────────────┐   ┌──────────────┐   ┌────────────────┐
 │ ADAPTADOR│   │ query_graph   │   │ nomic-embed- │   │ auto-sync      │
 │ magi-mem │   │ <1 ms         │   │ code 768 int8│   │ incremental    │
 │ (núcleo) │   └───────────────┘   └──────────────┘   └────────────────┘
 └────┬─────┘
      │ EVIDENCIA estructural tipada (tier 3: análisis estático)
      ▼
   Área 3 (debate) · Área 5 (capas y libro mayor) · Área 8 (impacto) · GUI
```

**Nodo `Knowledge` (extensión propia del plan).** El grafo del proyecto original describe código; MAGI System IDE añade una capa propia **en su propia base de datos**, no dentro del binario externo: la tabla `mem_knowledge` guarda los *deltas de conocimiento* que MELCHIOR • 1 emite al sobrevivir una afirmación (§I.6), enlazados por `qualified_name` a los nodos del grafo. Así el sistema recuerda no sólo *qué llama a qué*, sino *qué se estableció como cierto sobre esa función, con qué evidencia y cuándo caduca*.

### 13.3 Contratos e interfaces

Adaptador en `modules/memgraph/`:

```python
def ensure_binary() -> BinaryInfo: ...                     # verifica hash + firma del commit fijado
def index_repository(path: Path, *, project: str, watch: bool = True) -> IndexJob: ...
def index_status(project: str) -> IndexStatus: ...
def list_projects() -> list[ProjectStat]: ...
def delete_project(project: str) -> None: ...
def search_graph(*, label: str | None, name_pattern: str | None, file_pattern: str | None,
                 min_degree: int | None = None, limit: int = 100, offset: int = 0) -> list[GraphNode]: ...
def trace_call_path(function_name: str, *, depth: int = 3, direction: Literal["out","in"] = "out") -> CallPath: ...
def query_graph(cypher: str, *, timeout_ms: int = 2000) -> QueryResult: ...   # sólo lectura, validado
def get_graph_schema(project: str) -> GraphSchema: ...
def get_code_snippet(qualified_name: str) -> CodeSnippet: ...
def get_architecture(project: str) -> ArchitectureOverview: ...
def search_code(pattern: str, *, project: str, regex: bool = True) -> list[TextHit]: ...
def detect_changes(diff_ref: str, *, project: str) -> ImpactReport: ...
def manage_adr(op: Literal["list","get","create","update"], **kw) -> AdrResult: ...
def ingest_traces(traces: Path, *, project: str) -> TraceIngestReport: ...
def semantic_query(text: str, *, project: str, k: int = 20) -> list[SemanticHit]: ...
# extensión propia
def record_knowledge(qualified_name: str, delta: KnowledgeDelta) -> KnowledgeId: ...
def knowledge_for(qualified_name: str, *, as_of: str | None = None) -> list[KnowledgeDelta]: ...
```

Esquema del delta de conocimiento (extensión propia, va al acta y al grafo):

```json
{
  "knowledge_id": "kn_01J9…",
  "qualified_name": "atlasforge.modules.re.decompile.pipeline.emit_artifact",
  "statement": "emit_artifact marca derivative_risk=high para todo binario con origin_class=device_dump",
  "established_by": {"round_id": "rnd_…", "verdict_id": "vd_…", "score": 82},
  "evidence_refs": ["ev_…", "ev_…"],
  "evidence_tier_min": 2,
  "expires_when": "cambie el sha256 del fichero que define la función o su firma",
  "invalidated_by": null,
  "created_at": "2026-08-02T09:14:22-05:00"
}
```

Eventos nuevos en el bus: `memgraph.indexed{project, nodes, edges, duration_s, languages[]}`, `memgraph.stale{project, files_changed}`, `memgraph.query{kind, duration_ms, rows}` (no crítico, muestreado 1:50), `knowledge.recorded{knowledge_id, qualified_name}`, `knowledge.invalidated{knowledge_id, reason}`. Tablas propias: `mem_project`, `mem_query_log`, `mem_knowledge`, `mem_coverage` (DDL en §T13).

### 13.4 Implementación

Instalación: binario estático descargado de la publicación oficial del commit fijado, verificado por **SHA-256 publicado + firma Sigstore/cosign keyless + procedencia SLSA**, y colocado en `tools/magi-mem/<version>/`. **No se usa el instalador `curl | bash` del proyecto** — *Decisión:* la descarga y la verificación las hace el propio núcleo con `net.download{expected_sha256}` (acción R1 del Área 8) y la configuración de clientes MCP la escribe MAGI System IDE, porque un instalador que auto-detecta 43 superficies de cliente y edita sus configuraciones es exactamente el tipo de efecto lateral no auditado que el §10.6 prohíbe.
*Descartado:* `npm i -g` / Homebrew / Scoop — cómodos, pero el sistema perdería el control del hash exacto que ejecuta.

Arranque: proceso hijo bajo `procman` (Área 0) con el entorno acotado:

```bash
CBM_CACHE_DIR="${MAGI_DATA}/memgraph"      \
CBM_ALLOWED_ROOT="${PROJECT_ROOT}"          \
CBM_WORKERS=6                               \
CBM_MEM_BUDGET_MB=3072                      \
CBM_LOG_LEVEL=warn                          \
CBM_DIAGNOSTICS=false                       \
  tools/magi-mem/<version>/codebase-memory-mcp
```

`CBM_ALLOWED_ROOT` es **obligatorio** y se fija a la raíz del proyecto abierto: es el control que impide que el indexador recorra el disco del usuario, y su ausencia es motivo de rechazo en el preflight. Modo CLI para trabajos por lotes y comprobaciones desde `make gates`:

```bash
codebase-memory-mcp cli index_repository '{"repo_path":"'"$PROJECT_ROOT"'"}'
codebase-memory-mcp cli search_graph     '{"name_pattern":".*Timing.*","label":"Function"}'
codebase-memory-mcp cli trace_call_path  '{"function_name":"schedule_events","depth":4}'
codebase-memory-mcp cli query_graph      '{"query":"MATCH (f:Function)-[:CALLS]->(g:Function) WHERE f.file =~ \".*core.*\" RETURN g.name, count(*) AS n ORDER BY n DESC LIMIT 20"}'
codebase-memory-mcp cli list_projects
```

**Perfiles de consulta.** El proyecto define tres perfiles de uso (descubrimiento rápido, verificación dirigida y auditoría exhaustiva). Se mapean a los tres nodos: **MELCHIOR • 1 → perfil de verificación dirigida** (el equilibrado, por defecto), **BALTHASAR • 2 → perfil de auditoría exhaustiva** (necesita ver todo lo que puede romperse), **CASPER • 3 → perfil de descubrimiento rápido** (sólo comprueba que la evidencia citada existe, no explora). Esta asignación se declara en `config/memgraph.yaml` y es auditable.

**Artefacto compartible del grafo.** El grafo se exporta comprimido con zstd a `<proyecto>/artifacts/memgraph/graph.db.zst` y se registra en el CAS con su hash; al abrir el proyecto en otra máquina se descomprime y se ejecuta indexación incremental. **CTL-1 se aplica igual aquí**: un grafo construido sobre código decompilado propietario hereda `origin_class` y **no puede empaquetarse** en una salida distribuible; la comprobación se añade a `packager.py`.

Tabla de paridad:

| Elemento | Impl. Windows | Impl. Linux |
|---|---|---|
| Binario | `codebase-memory-mcp.exe` (amd64) en `tools\magi-mem\` | binario estático (amd64/arm64) en `tools/magi-mem/` |
| Caché del grafo | `%LOCALAPPDATA%\MagiSystem\memgraph\` | `~/.local/share/MagiSystem/memgraph/` |
| Vigilancia de cambios | sondeo de `git status` cada 15 s (el vigilante propio del binario) | ídem |
| Límite de raíz | `CBM_ALLOWED_ROOT` con ruta con letra de unidad | `CBM_ALLOWED_ROOT` con ruta POSIX |
| Verificación de firma | `cosign verify-blob` (binario propio en `tools\`) | ídem |
| Aislamiento de proceso | Job Object con límite de memoria = `CBM_MEM_BUDGET_MB` + 25 % | cgroup v2 `memory.max` equivalente |

### 13.5 Algoritmos

**A13-1 — Validación de consultas Cypher antes de ejecutarlas (defensa propia, no delegada).**
```
1. tokenizar la consulta; rechazar si aparece cualquier palabra clave de escritura:
      CREATE, MERGE, DELETE, DETACH, SET, REMOVE, LOAD CSV, CALL db., apoc.
2. exigir LIMIT explícito ≤ 5 000; si falta, añadirlo
3. exigir que toda consulta esté anclada a un `project` conocido (cláusula WHERE o etiqueta Project)
4. presupuesto: timeout de 2 000 ms; superarlo cancela y devuelve QueryTimeout, nunca un resultado parcial
5. registrar la consulta, su duración y sus filas en mem_query_log (para el banco de §13.8)
6. caso límite: el binario no soporta una construcción → error de sintaxis del motor; se devuelve al nodo
     que la emitió con el mensaje exacto y se cuenta como reparación (§7.4)
```

**A13-2 — Clasificación de capas de un emulador con evidencia de grafo (sustituye a A5-1).**
```
 1. indexar el árbol de fuentes del emulador: index_repository(watch=true)
 2. por cada módulo M, obtener del grafo:
      out_console := nº de aristas CALLS/USES_TYPE de M hacia símbolos cuyo fichero está en el
                     subárbol específico de consola (rutas y símbolos declarados en profiles/emulators/*.yaml)
      out_backend := ídem hacia el subárbol de backend de anfitrión (GPU, audio, entrada)
      in_degree, out_degree, betweenness  (con query_graph y agregados)
 3. señal ESTRUCTURAL (nueva, dura):  console_coupling := out_console / max(1, out_degree)
 4. etiqueta preliminar:
      console_coupling ≥ 0,25            → console_specific
      0,05 ≤ console_coupling < 0,25     → semi_agnostic
      console_coupling < 0,05 ∧ out_backend > 0 → semi_agnostic
      console_coupling < 0,05 ∧ out_backend = 0 → agnostic
 5. las heurísticas de nombres del A5-1 pasan de ser la señal principal a ser un DESEMPATE con peso 0,2
 6. verificación por compilación aislada (como antes) + NUEVA verificación de grafo: un módulo
      'agnostic' con cualquier arista a un símbolo de consola es una contradicción y refuta la etiqueta
      automáticamente, sin gastar un token
 7. complejidad: dominada por la indexación; la clasificación es O(V+E) sobre el grafo ya construido
```

**A13-3 — Análisis de impacto de un cambio (alimenta al Área 8 y a BALTHASAR • 2).**
```
1. entrada: diff de git (o conjunto de ficheros modificados por una acción propuesta)
2. detect_changes(diff) → símbolos definidos o modificados
3. expansión inversa: trace_call_path(direction="in", depth=3) sobre cada símbolo
4. superficie afectada := unión de los llamadores hasta profundidad 3, más los ficheros con arista
     FILE_CHANGES_WITH (co-cambio histórico) por encima de un umbral de coocurrencia
5. clasificación de riesgo: alto si toca símbolos con in_degree ≥ 20 o rutas HTTP; medio si toca
     ≥ 5 llamadores; bajo en el resto
6. salida: ImpactReport que (a) se adjunta a toda acción del Área 8 que modifique código, y
     (b) se entrega a BALTHASAR • 2 como material de refutación de completitud
     («la afirmación de MELCHIOR ignora estos 7 llamadores»)
7. caso límite: símbolo no indexado (lenguaje no soportado) → se marca coverage_gap y el riesgo se
     eleva a alto por desconocimiento, nunca se baja
```

**A13-4 — Ciclo de vida del conocimiento (deltas de MELCHIOR • 1).**
```
1. al emitirse un veredicto survives con score ≥ 70 sobre una afirmación estructural o de comportamiento,
     MELCHIOR debe producir un KnowledgeDelta o el veredicto queda incompleto
2. se guarda con su qualified_name y su condición de caducidad
3. invalidación automática: al reindexar, si el sha256 del fichero que define el símbolo cambió, o si
     cambió su firma (parámetros o tipo de retorno), el delta pasa a invalidated_by="reindex"
4. el compilador de prompts (§7.5) inyecta los deltas VIGENTES del símbolo en foco como contexto fijado,
     con presupuesto de 800 tokens y prioridad sobre el historial de debate comprimido
5. un delta invalidado NO se borra: queda como historia y como aviso («esto era cierto hasta el commit X»)
```

### 13.6 Integración con el debate popperiano

Afirmaciones que emite: la etiqueta de capa de cada módulo (ahora con evidencia estructural), la superficie afectada por un cambio, la existencia y la firma de un símbolo, la ausencia de llamadores (código muerto) y la cobertura del índice. Evidencia admisible: resultado de `query_graph` con la consulta exacta y su hash, `get_code_snippet` con el `qualified_name`, y el informe de cobertura. **Tier 3 (análisis estático)** en la escala de §3.10: gana a la cita normativa y al razonamiento, pierde ante la ejecución y la medición.

Refutación más potente disponible: **la consulta contradictoria** — BALTHASAR • 2 escribe una consulta Cypher que devuelve filas incompatibles con la afirmación de MELCHIOR • 1 (por ejemplo, aristas `CALLS` desde un módulo declarado agnóstico hacia un símbolo específico de consola). Es barata (< 1 ms), reproducible y no admite retórica; el plan la eleva a **refutación preferente en todo lo que sea estructura de código**, por delante del argumento. Punto de invocación: antes de fijar cualquier etiqueta de capa, antes de cerrar una fila del libro mayor y antes de aprobar una acción del Área 8 que modifique código.

**Guarda contra el falso confort.** Un grafo que no cubre un lenguaje devuelve «no hay llamadores», que es indistinguible de «es código muerto». Por eso `check_index_coverage` se ejecuta antes de cualquier afirmación de ausencia, y una afirmación de ausencia sobre un fichero no cubierto es **inadmisible** (rechazo del validador, no puntuación baja).

### 13.7 Costos, latencia y recursos

Indexación (objetivo propio, más conservador que el declarado por el proyecto): **≤ 45 s para 100 000 nodos** en el perfil de máquina del plan; el proyecto declara cifras muy superiores (núcleo de Linux en 3 minutos) y el banco de §13.8 las mide sin darlas por buenas. Consultas: Cypher ≤ 5 ms p95 (objetivo propio; el proyecto declara < 1 ms), búsqueda por nombre ≤ 20 ms, `semantic_query` ≤ 300 ms. RAM: acotada por `CBM_MEM_BUDGET_MB=3072` más el 25 % de margen del Job Object; liberada al terminar la indexación. Disco: grafo comprimido ≈ 8–13:1 sobre el SQLite crudo (declarado por el proyecto; se mide y se registra el valor real por proyecto).

**Ahorro de tokens — la razón económica de esta área.** El proyecto declara una reducción del 99,2 % frente a explorar fichero a fichero. El plan **no adopta esa cifra**: fija como criterio de aceptación **≥ 80 % de reducción de tokens de entrada** en el banco de 40 tareas de §13.8, medido como `tokens_in(con grafo) / tokens_in(sin grafo)`. Con el presupuesto del Área 5 (3 400 tokens de entrada por función refinada), una reducción del 80 % convierte 4,2 M de tokens en 840 k para un binario de 1 000 funciones: es la diferencia entre viable e inviable en Perfil A.

**Salto del debate:** las consultas de estructura son R0 deterministas y no se debaten; se ejecutan y su resultado es evidencia. **Caché:** resultados de `query_graph` por `sha256(cypher)+graph_version`, invalidados por `memgraph.indexed`; los `qualified_name` resueltos por `sha256(fichero)+símbolo`.

### 13.8 Calidad y pruebas

| Caso | Criterio de éxito |
|---|---|
| Camino feliz | Indexar el propio repositorio de MAGI System IDE: `list_projects` reporta > 0 nodos y `get_graph_schema` devuelve las 13 etiquetas de nodo esperadas |
| **Contrato real frente a README** | La enumeración efectiva de herramientas MCP del commit fijado se escribe en `config/externals.lock`; el sistema falla al arrancar si difiere de la esperada (defensa contra las discrepancias 14/15 herramientas y 155/158 lenguajes) |
| Rendimiento de indexación | 3 repositorios de 20 k, 100 k y 500 k nodos: ≤ 45 s, ≤ 4 min y ≤ 20 min respectivamente; si no se cumple, se rebaja el objetivo publicado y se declara |
| Latencia de consulta | 200 consultas Cypher representativas: p95 ≤ 5 ms, 0 timeouts |
| **Ahorro de tokens** | Banco de 40 tareas de comprensión de código resueltas con y sin grafo: reducción media de tokens de entrada ≥ 80 % **y** exactitud de la respuesta no inferior a la del camino sin grafo (medida contra respuesta conocida) |
| Clasificación de capas (A13-2) | Sobre el emulador libre con 200 módulos etiquetados a mano: exactitud ≥ **0,92** (frente a ≥ 0,85 del A5-1 sin grafo); 0 etiquetas `agnostic` con arista a consola |
| Análisis de impacto | 30 cambios sembrados: la superficie afectada contiene el 100 % de los llamadores reales; ≤ 25 % de falsos positivos |
| Inyección en Cypher | 50 consultas de escritura o con `CALL db.` inyectadas: 50/50 rechazadas por A13-1 antes de llegar al binario |
| Confinamiento de raíz | Intento de indexar fuera de `CBM_ALLOWED_ROOT`: rechazado 10/10, con entrada en la auditoría |
| Cobertura y falso vacío | Fichero en lenguaje no cubierto: toda afirmación de ausencia sobre él es rechazada, 10/10 |
| Consenso entre nodos | MELCHIOR afirma una etiqueta con respaldo de grafo, BALTHASAR consulta y confirma: CASPER ≥ 80 |
| Desacuerdo total | BALTHASAR devuelve filas contradictorias: CASPER emite `falsified` **aunque MELCHIOR tenga alta confianza**, 20/20 |
| Conocimiento | 50 deltas registrados; al modificar la firma de 20 símbolos, los 20 deltas correspondientes quedan invalidados automáticamente |
| Binario ausente | Sin `magi-mem` instalado, el sistema arranca y el Área 5 usa el camino de reserva `ctags`+`networkx`, con aviso visible |
| CTL-1 | Intento de empaquetar un grafo derivado de código propietario: rechazo 10/10 |

### 13.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta automática | Estado |
|---|---|---|---|---|
| Binario ausente o hash incorrecto | verificación previa al arranque | Sin grafo | Camino de reserva (`ctags`+`networkx`) con precisión declarada menor; banner en la GUI | Degradado, honesto |
| Indexación agota el presupuesto de RAM | Job Object / cgroup | Índice incompleto | Reintento con `CBM_WORKERS` reducido a la mitad y `CBM_MEM_BUDGET_MB` a 1536; si falla, indexar por subárboles | Degradado |
| Grafo obsoleto respecto del disco | `memgraph.stale` por el vigilante git | Respuestas desfasadas | Reindexación incremental automática; **toda consulta sobre un proyecto `stale` se marca así en la evidencia** | Consistente |
| **Fallo parcial (el peor): grafo parcial que parece completo** | `check_index_coverage` comparado con el recuento de ficheros del descubrimiento | Falsos negativos silenciosos | Cobertura por lenguaje visible en la GUI; afirmaciones de ausencia inadmisibles bajo cobertura < 95 % | Seguro |
| Consulta que cuelga el binario | timeout de 2 000 ms + latido | Bloqueo del adaptador | Matar y relanzar el proceso; la consulta se marca fallida, nunca parcial | Recuperado |
| Base de datos del grafo corrupta | `PRAGMA integrity_check` al abrir | Proyecto sin memoria | Borrar y reindexar desde cero (el grafo es derivado, nunca fuente) | Recuperado |
| Sin red | — | Ninguno | Todo local, incluidos los embeddings | Operativo |

### 13.10 Riesgos y mitigaciones

Confiar en un grafo incompleto (alta / alto → cobertura obligatoria y prohibición de afirmar ausencia). Dependencia de un binario de terceros en el camino crítico (media / alto → camino de reserva probado en PV-13.e.2 y verificación de firma). Ejecución de código de terceros con acceso al árbol de fuentes (media / alto → `CBM_ALLOWED_ROOT`, Job Object/cgroup con límite de memoria, sin capacidad `net.out` concedida al proceso hijo, y verificación SLSA/cosign). Inyección por consulta generada por un modelo (media / medio → validador A13-1 propio, sin delegar). Deriva entre el README y el binario real (alta / medio → `config/externals.lock` con la enumeración efectiva y fallo al arrancar si difiere). Sobreajuste del sistema al grafo, olvidando que el código decompilado tiene estructura degradada (media / medio → el grafo del C de Ghidra se marca `synthetic_source=true` y su `console_coupling` se pondera a la baja).

### 13.11 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA.** Requiere: el binario estático del commit fijado (macOS arm64/amd64, Linux arm64/amd64, Windows amd64), `cosign` para verificar la firma, y espacio en disco para el grafo (≈ 150 MB por cada 500 k nodos antes de comprimir). Sin cuentas, sin claves de API, sin red en tiempo de ejecución, sin telemetría. Licencia del proyecto a registrar en §T6 al fijar el commit; al ejecutarse como **proceso separado por MCP**, cualquier licencia copyleft queda aislada de la del producto.

### 13.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (indexar el propio repositorio, `search_graph` y `get_code_snippet` desde el núcleo) → v1 (Cypher validado, análisis de impacto, integración con el Área 5) → completo (deltas de conocimiento, artefacto compartible, panel de grafo en la GUI, banco de ahorro de tokens).

- **P13.a Adopción verificada.** P13.a.1 fijar commit, descargar y verificar — **PV-13.a.1**: hash y firma correctos, y la enumeración efectiva de herramientas y lenguajes escrita en `config/externals.lock` coincide con la esperada; el arranque falla si no. P13.a.2 arranque supervisado con entorno acotado — **PV-13.a.2**: 20 arranques con `CBM_ALLOWED_ROOT` respetado y límite de memoria aplicado.
- **P13.b Consulta segura.** P13.b.1 validador A13-1 — **PV-13.b.1**: 50/50 consultas de escritura rechazadas. P13.b.2 latencia — **PV-13.b.2**: p95 ≤ 5 ms sobre 200 consultas. P13.b.3 evidencia tipada — **PV-13.b.3**: 100 % de resultados convertidos en `Evidence` con `tier=3` y la consulta exacta como localizador.
- **P13.c Integración con el Área 5.** P13.c.1 clasificación con grafo — **PV-13.c.1**: exactitud ≥ 0,92 y 0 contradicciones `agnostic`↔consola. P13.c.2 libro mayor con evidencia de grafo — **PV-13.c.2**: 100 % de filas con al menos una consulta Cypher como `evidence_ref`. P13.c.3 impacto — **PV-13.c.3**: 100 % de llamadores reales cubiertos en 30 cambios sembrados.
- **P13.d Conocimiento.** P13.d.1 deltas — **PV-13.d.1**: ningún veredicto `survives` sobre afirmación estructural se cierra sin delta (consulta SQL devuelve 0 filas). P13.d.2 invalidación — **PV-13.d.2**: 20/20 deltas invalidados al cambiar la firma.
- **P13.e Economía y reserva.** P13.e.1 banco de ahorro — **PV-13.e.1**: reducción de tokens ≥ 80 % sin pérdida de exactitud. P13.e.2 camino de reserva — **PV-13.e.2**: con el binario ausente, el Área 5 completa su prueba de humo y la GUI lo declara.

Métricas de salida: exactitud de capas ≥ 0,92, ahorro de tokens ≥ 80 %, p95 de consulta ≤ 5 ms, 0 afirmaciones de ausencia bajo cobertura insuficiente, y camino de reserva verificado.

---

## ÁREA 14 — MAGI-ROUTE: pasarela universal de inferencia y economía de tokens

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA** en su modo local y de agregación de niveles gratuitos oficiales; **🟡 REQUIERE-PRERREQUISITO** para cada proveedor concreto (cuenta gratuita del propio usuario y su token, obtenidos por la vía oficial del proveedor).

### 14.1 Propósito y alcance

Convierte la jerarquía de coste cero del §I.3 —que el plan resolvía con un cliente propio y un registro de proveedores escrito a mano— en una **pasarela real**: un único endpoint compatible con OpenAI en `127.0.0.1:20128/v1` detrás del cual viven los proveedores de nube declarados en `config/providers.yaml`, todos gratuitos y sin clave de servicio (§I.3), con estrategias de enrutado, tres capas de resiliencia, compresión de prompts y telemetría de coste por petición.

Queda fuera: la **política** de qué capacidad exige cada tarea y cómo se degrada, que sigue siendo del Área 6; la asignación rol→modelo, que sigue siendo del §I.3 y del Área 6; y el contenido, que es de las áreas de dominio. MAGI-ROUTE es sustrato, no criterio.

**Consume:** Área 0 (supervisión de procesos, política de capacidades, bus), Área 6 (contrato de selección y degradación). **Alimenta:** todas las áreas que llaman a un modelo, y el Área 10 (panel de proveedores y telemetría de coste).

### 14.2 Arquitectura y relación con el Área 6

*Decisión:* se adopta **`diegosouzapw/OmniRoute`** (MIT) como pasarela local, ejecutada como proceso hijo supervisado y **enlazada exclusivamente a `127.0.0.1`**, y el Área 6 se reescribe como **capa de política sobre ella** en lugar de como implementación — porque cortacircuitos, cubos de fichas, reintentos con jitter y contabilidad de cuotas son infraestructura resuelta, mientras que la parte que sólo este plan puede aportar (qué se degrada, qué se anota en el acta, qué unidad se reanuda) es exactamente lo que queda en el Área 6.
*Descartado:* mantener la implementación propia de §6.2–§6.4 como camino principal — se conserva íntegra como **camino de reserva obligatorio**, porque el suelo local del §I.3 no puede depender de una pasarela de terceros para funcionar.

**Reparto de responsabilidades, sin solape:**

| Responsabilidad | Dueño | Nota |
|---|---|---|
| Registro de proveedores y sus credenciales | **MAGI-ROUTE** | El usuario las introduce en su panel o en el de MAGI System IDE, que las delega |
| Estrategia de enrutado entre proveedores | **MAGI-ROUTE** | Configurada por MAGI System IDE según §14.4 |
| Cortacircuitos, cooldown por clave, bloqueo por modelo | **MAGI-ROUTE** | Tres capas independientes (§14.4) |
| Compresión de prompt | **MAGI-ROUTE** | Desactivada por defecto en este plan; ver §14.5 |
| **Capacidad exigida por la tarea** (visión, contexto, salida estructurada) | **Área 6** | Filtro duro previo; MAGI-ROUTE no sabe qué necesita un análisis forense |
| **Suelo local garantizado** | **Área 6 + §I.3** | al menos un proveedor alcanzable también sin la pasarela |
| **Regla de diversidad MELCHIOR ≠ BALTHASAR** | **Área 6** | Se impone fijando `model` explícito por rol, no dejando que la pasarela elija |
| **WAL de unidades reanudables y reconciliación** | **Área 6** | Sobrevive a cualquier cambio de proveedor |
| **Marcado de calidad heterogénea en el artefacto** | **Área 6** | Alimentado por las cabeceras de telemetría de MAGI-ROUTE |
| Presupuesto de tokens por área y por ronda | **Área 6 + Área 0** | La pasarela informa; el planificador decide |

```
   petición de inferencia (cualquier área)
        │  {capacidades exigidas, rol, presupuesto, unit_id}
        ▼
 ┌──────────────────────────────────────────────────────────────┐
 │ ÁREA 6 — POLÍTICA (sigue siendo nuestra)                     │
 │  filtro de capacidad · rol→modelo · diversidad · WAL · acta   │
 │  ⚠ decisión: ¿la pasarela está sana?  no → cliente directo    │
 └───────────┬──────────────────────────────────┬───────────────┘
             │ HTTP OpenAI-compatible           │ camino de reserva
             ▼                                  ▼
 ┌────────────────────────────────────┐   ┌──────────────────────┐
 │ MAGI-ROUTE  127.0.0.1:20128/v1     │   │ core/providers/*     │
 │  ┌───────────────────────────────┐ │   │ (cliente propio      │
 │  │ estrategia (§14.4)            │ │   │  directo a           │
 │  ├───────────────────────────────┤ │   │  proveedor de nube)       │
 │  │ L1 cortacircuitos por proveedor│ │   └──────────┬───────────┘
 │  │ L2 cooldown por credencial     │ │              │
 │  │ L3 bloqueo por modelo          │ │              │
 │  └───────────────────────────────┘ │              │
 └──┬────────────┬──────────┬─────────┘              │
    │ local      │ oficial  │ oficial                │
    ▼            ▼          ▼                        ▼
 proveedor de nube  Claude Code  niveles gratuitos    proveedor de nube
 (SUELO)       CLI          documentados          (SUELO)
    │
    └──── cabeceras X-OmniRoute-* → telemetría de coste → acta y GUI
```

### 14.3 Contratos e interfaces

Adaptador en `modules/route/`:

```python
def ensure_gateway() -> GatewayInfo: ...           # verifica versión fijada, puerto y enlace a loopback
def gateway_health() -> HealthReport: ...          # GET /health; 3 fallos ⇒ camino de reserva
def list_models() -> list[RouteModel]: ...         # GET /v1/models, normalizado a nuestro esquema
async def complete(req: InferenceRequest, *, route: RouteDirective) -> ModelResponse: ...
def set_strategy(scope: Literal["role","task","global"], name: str, strategy: str) -> None: ...
def quota_snapshot() -> list[ProviderQuota]: ...   # alimenta el panel §10.4 y la tabla provider_quota
def cost_headers(resp: httpx.Response) -> CostTelemetry: ...
```

`RouteDirective` (lo que el Área 6 impone a la pasarela, y que la pasarela **no** puede sobrescribir):

```json
{
  "role": "MELCHIOR|BALTHASAR|CASPER|VLM|EMBED|RERANK",
  "pin_model": "qwen2.5-coder-7b-q5km",
  "allow_remote": false,
  "required_caps": {"vision": false, "min_context": 32768, "structured_output": "gbnf"},
  "strategy": "priority",
  "forbid_providers": ["*"],
  "max_tokens_in": 12000,
  "unit_id": "sha256:…",
  "privacy_class": "local_only|consented_remote"
}
```

**Regla dura de privacidad:** `privacy_class: "local_only"` es el valor por defecto de **toda** petición que contenga (a) fotogramas de pantalla del dispositivo del usuario, (b) páginas de un expediente documental, (c) contenido de un binario o de un dump de firmware, o (d) texto del corpus normativo del usuario. Con ese valor, el adaptador fija `allow_remote:false` y `forbid_providers:["*"]`, de modo que la petición **no puede** salir del equipo aunque la pasarela tenga cien proveedores configurados. El cambio a `consented_remote` exige consentimiento explícito por sesión (§4.4) y queda en la auditoría.

Eventos nuevos: `route.selected{unit_id, provider, model, strategy, latency_ms, tokens_in, tokens_out, cost_usd}`, `route.tripped{provider, layer, reason, reset_in_s}`, `route.quota{provider, remaining, window}`, `route.degraded{from, to, reason}`, `route.blocked{reason:"privacy"|"policy", provider}`. Tablas: se reutiliza `provider_quota` (§T3) y se añaden `route_call` y `route_event` (DDL en §T13).

### 14.4 Implementación

**Instalación y arranque.** Versión fijada en `config/externals.lock`, instalada en `tools/magi-route/<version>/` (NPM o contenedor; *Decisión:* **contenedor OCI cuando exista runtime disponible, e instalación NPM local en caso contrario** — porque el contenedor da un límite de memoria y una superficie de red controlada de forma trivial). Arranque con:

```bash
PORT=20128 HOST=127.0.0.1 REQUIRE_API_KEY=true DATA_DIR="${MAGI_DATA}/route" \
  node tools/magi-route/<version>/server.js
```

`HOST=127.0.0.1` y `REQUIRE_API_KEY=true` son **obligatorios y verificados en el preflight**: el adaptador comprueba con un `connect()` desde otra interfaz que el puerto **no** responde fuera de loopback, y aborta el arranque si responde. Una pasarela de inferencia escuchando en `0.0.0.0` dentro de la red del usuario es un incidente de seguridad, no una comodidad.

**Estrategias de enrutado: cuáles se usan y cuáles se prohíben.** El proyecto ofrece un catálogo amplio (prioridad, ponderada, rotación circular, coste mínimo, menos usado, potencia de dos opciones, último camino bueno conocido, puntuación automática multifactor, aleatoria, relevo de contexto, optimizada por caché, fusión de varios modelos con síntesis, encadenado en tubería, y otras). *Decisión:* MAGI System IDE fija la estrategia por rol y por clase de tarea, y **no** usa la selección automática global —

| Rol / tarea | Estrategia | Motivo (una línea) |
|---|---|---|
| MELCHIOR • 1, BALTHASAR • 2, CASPER • 3 | `priority` con `pin_model` | La regla de diversidad exige control total del modelo por rol; una estrategia adaptativa la rompería en silencio |
| VLM, embeddings, reordenador | `priority` con proveedor local único | Nunca salen del equipo |
| Tareas de código largas (síntesis, refactor) | `lkgp` (último camino bueno conocido) | Estabilidad de estilo dentro de un mismo trabajo, que es lo que la reconciliación del §6.5 premia |
| Trabajos por lotes tolerantes (resumen de documentación pública, arte previo) | `cost-optimized` | Es donde el ahorro importa y la heterogeneidad no daña |
| Reintento tras fallo de proveedor | `round-robin` acotado a los que cumplen la capacidad | Evita reintentar contra el mismo proveedor caído |

**Prohibidas por decisión y por qué:** `fusion` (panel de varios modelos con síntesis) — **duplicaría el debate MAGI con un mecanismo opaco y sin acta**, que es precisamente lo que el Área 3 hace de forma auditable; `pipeline` (encadenado de salidas) — el encadenado del sistema es el bucle del Área 8, con postcondiciones verificadas, y un encadenado paralelo dentro de la pasarela produciría artefactos sin procedencia; y toda estrategia que reparta entre cuentas agrupadas de terceros, por higiene de términos de servicio. Las prohibiciones se aplican en el adaptador (`RouteDirective.strategy` es una enumeración cerrada) y **también** en la configuración de la pasarela, para que un cambio manual del usuario no las reintroduzca sin darse cuenta.

**Resiliencia en tres capas (de la pasarela) y qué queda del Área 6.** La pasarela aporta: **L1** cortacircuitos por proveedor ante errores 408/5xx con ventanas de reapertura exponenciales; **L2** enfriamiento por credencial con retroceso exponencial y protección contra estampida; **L3** bloqueo del modelo concreto que falla sin arrastrar al resto de la conexión. El Área 6 conserva: la clasificación de «respuesta que no valida contra el esquema» como fallo (que una pasarela genérica no puede juzgar, porque no conoce nuestros esquemas), el WAL de unidades, la reconciliación entre tramos y el marcado del artefacto. *Decisión:* cuando una respuesta llega con HTTP 200 pero falla la validación pydantic/GBNF tras agotar reparaciones, el adaptador **informa el fallo a la pasarela** mediante una llamada explícita de marcado, para que su cortacircuitos lo contabilice; sin eso, un proveedor que devuelve basura sintácticamente válida nunca se abriría.

**Niveles gratuitos oficiales.** La pasarela agrega niveles gratuitos documentados de decenas de proveedores y publica su propio panel de uso. Condiciones que MAGI System IDE impone para activar cualquiera de ellos: (1) la cuenta y el token son **del usuario**, obtenidos por la vía oficial del proveedor; (2) se respeta el límite declarado con el margen del 20 % del §6.3; (3) **no** se usan grupos de cuentas compartidas ni rotación de identidades; (4) toda petición que salga lleva `privacy_class: consented_remote` y su consentimiento vigente. Las cifras agregadas que el proyecto publica (del orden de 10⁹ tokens gratuitos mensuales) se tratan como **dato de terceros, no como promesa del plan**: el panel de §10.4 muestra la cuota **observada** por el propio sistema, y la declarada aparece en gris como referencia.

**Compresión de prompt.** El proyecto incluye motores de compresión que declaran ahorros del 15 % al 95 %. *Decisión:* **desactivada por defecto en todas las rutas de MAGI System IDE, y activable sólo para la clase de tarea `bulk_summarize`** — porque comprimir el prompt destruye la propiedad que sostiene la mitad de este sistema: que **toda cita debe existir literalmente en el contexto entregado** (§A2-3) y que el hash del prompt es parte de la procedencia. Un prompt comprimido rompe el validador de citas y hace irreproducible el artefacto.
*Descartado:* activarla globalmente por el ahorro — el ahorro real ya viene del grafo de MAGI-MEM (≥ 80 % de tokens de entrada, §13.7), que reduce el contexto **sin alterarlo**.

Tabla de paridad:

| Elemento | Impl. Windows | Impl. Linux |
|---|---|---|
| Ejecución | Servicio de usuario o proceso hijo bajo Job Object | `systemd --user` o proceso hijo con `setsid` |
| Enlace de red | `127.0.0.1:20128`, regla de firewall de bloqueo entrante vía broker | `127.0.0.1:20128`, sin regla necesaria |
| Comprobación de no-exposición | `Test-NetConnection` desde la IP de la interfaz activa | `ss -ltnp` + `connect()` desde la IP de la interfaz activa |
| Almacén de credenciales | DPAPI (`CryptProtectData`) sobre `DATA_DIR` | `libsecret` si hay sesión de escritorio; si no, fichero `0600` con aviso |
| Contenedor (opción preferente) | Docker Desktop o Podman en WSL2 | Podman o Docker nativo |

### 14.5 Algoritmos

**A14-1 — Selección con política propia sobre pasarela.**
```
 1. la petición llega con capacidades exigidas, rol y privacy_class
 2. si privacy_class == local_only  →  RouteDirective{allow_remote:false, forbid_providers:["*"],
       pin_model = modelo local del rol}  y se llama a la pasarela (o al cliente directo) sin más
 3. si no: filtrar los modelos de list_models() que cumplen required_caps (filtro DURO, del Área 6)
 4. aplicar la regla de diversidad: si el rol es BALTHASAR y el modelo elegido comparte familia con el
       de MELCHIOR en esta ronda, se descarta y se toma el siguiente; si no queda ninguno, modo degradado
 5. fijar pin_model y strategy según la tabla de §14.4
 6. comprobar cuota observada: si remaining < tokens_estimados · 1,5 → preferir local
 7. llamar; leer cabeceras de telemetría; registrar route_call y emitir route.selected
 8. si HTTP 200 pero falla la validación tras N reparaciones → marcar fallo en la pasarela (§14.4) y
       reintentar según la política del Área 6, nunca en bucle abierto
 9. caso límite: la pasarela responde pero list_models() está vacío (aún cargando) → esperar 2 s,
       reintentar una vez, y si sigue vacío usar el camino de reserva
```

**A14-2 — Verificación de no-exposición de red (preflight obligatorio).**
```
1. obtener la lista de direcciones IP de las interfaces activas del equipo (sin loopback)
2. para cada una: intentar connect() a <ip>:20128 con timeout de 800 ms
3. cualquier conexión establecida ⇒ ABORTAR el arranque, emitir route.blocked{reason:"policy"},
     escribir en la auditoría y mostrar en la GUI la causa exacta
4. repetir la comprobación cada 10 min mientras la pasarela esté activa (la configuración puede cambiar)
5. además: verificar que REQUIRE_API_KEY está activo pidiendo /v1/models sin credencial y esperando 401
```

**A14-3 — Conciliación de telemetría de coste con el presupuesto propio.**
```
1. por cada respuesta, leer las cabeceras de coste y uso que la pasarela añade
2. normalizar a nuestro esquema {tokens_in, tokens_out, cost_usd, cache_hit, provider, model}
3. contrastar tokens_in con nuestro propio conteo previo al envío:
     divergencia > 15 % ⇒ anotar telemetry_mismatch en model_run y NO usar la cifra de la pasarela
     para el presupuesto (se usa la nuestra, que es la que el planificador puede auditar)
4. acumular por área, por rol y por trabajo; exponer en el panel de proveedores
5. cost_usd debe ser 0 en todas las rutas de este plan; cualquier valor > 0 dispara una alerta
     visible y detiene el uso de ese proveedor hasta confirmación humana (defensa contra que un
     proveedor "gratuito" empiece a cobrar sin que nadie lo note)
```

### 14.6 Integración con el debate popperiano

Afirmaciones: «esta ronda se ejecutó con tres modelos de familias distintas», «ninguna petición de clase `local_only` salió del equipo», «el coste acumulado del proyecto es 0 USD», «la pasarela no es alcanzable desde la red local». Evidencia admisible: `route_call` con proveedor y modelo por unidad, captura de tráfico local, resultado de A14-2, y la contabilidad de `cost_usd`. Refutación más potente: **la captura de tráfico** que muestra una petición saliente con contenido de clase `local_only`, y **la consulta SQL** que encuentra una ronda con dos roles servidos por la misma familia sin marca `diversity: degraded`. Punto de invocación: al cerrar cada trabajo que haya usado la pasarela y en cada cambio de su configuración.

### 14.7 Costos, latencia y recursos

Sobrecoste de la pasarela frente a llamar directo al servidor local: objetivo **≤ 25 ms p95** por petición (medido en §14.8); si se supera, las rutas puramente locales se envían por el cliente directo y la pasarela queda sólo para lo remoto. RAM del proceso: ≤ 400 MB, acotada por contenedor o Job Object. Disco: `DATA_DIR` con historial de peticiones; rotación a 2 GB. Tokens: la pasarela no consume; su valor es no gastarlos en proveedores caídos y no perder trabajo. **Salto del debate:** la selección de proveedor es determinista y no se debate; sí se debaten las cuatro afirmaciones de §14.6. **Caché:** la caché de respuestas sigue siendo la del Área 6 (clave con `prompt_hash+model_hash+params_hash`), **no** la de la pasarela — porque nuestra clave incluye la semilla y la gramática, y una caché que ignore eso devolvería resultados no reproducibles.

### 14.8 Calidad y pruebas

| Caso | Criterio de éxito |
|---|---|
| Camino feliz | 500 peticiones locales a través de la pasarela: 0 errores de protocolo, respuestas idénticas a las del cliente directo con la misma semilla |
| **Sobrecoste** | p95 de latencia añadida ≤ 25 ms sobre 500 peticiones; si se supera, la ruta local se desvía al cliente directo automáticamente |
| **No exposición** | A14-2 sobre todas las interfaces: 0 conexiones establecidas, 10/10 arranques; con `HOST=0.0.0.0` forzado, el arranque **aborta** 10/10 |
| **Privacidad** | 200 peticiones de clase `local_only` (fotogramas, páginas de expediente, dumps): 0 bytes salientes, verificado con captura de tráfico |
| Diversidad | 50 rondas: 0 con dos roles de la misma familia sin marca `degraded` |
| Cortacircuitos | Proveedor simulado que falla: L1 abre en ≤ 5 llamadas y no se reintenta antes del temporizador; el trabajo continúa en local |
| Basura sintácticamente válida | Proveedor que devuelve JSON válido pero fuera de esquema: tras las reparaciones, el fallo se marca en la pasarela y el proveedor acaba abierto, 10/10 |
| Coste cero | 10 000 peticiones: `cost_usd` acumulado = 0; con un proveedor que reporta coste > 0, alerta y detención, 10/10 |
| Telemetría | Divergencia de conteo de tokens > 15 % detectada y registrada en 10/10 casos sembrados |
| Pasarela ausente o caída | Matar el proceso a mitad de un trabajo de 300 unidades: continúa por el camino de reserva, ≤ 1 unidad recomputada, artefacto declara el cambio |
| Estrategias prohibidas | Intento de fijar `fusion` o `pipeline` desde la configuración: rechazado en el adaptador y revertido en la pasarela, 10/10 |
| Consenso / desacuerdo entre nodos | Sobre «el coste es cero»: con la contabilidad limpia, `survives` ≥ 85; con una fila de coste > 0, `falsified` inmediato |
| Compresión | Con compresión activada fuera de `bulk_summarize`: el validador de citas del Área 2 falla y la ruta se bloquea, 10/10 (prueba de que la decisión de §14.4 está implementada, no sólo escrita) |

### 14.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta automática | Estado |
|---|---|---|---|---|
| Pasarela no arranca | `gateway_health` 3 fallos | Sin agregación | Camino de reserva (cliente propio a el proveedor de nube asignado); banner en la GUI | Degradado, funcional |
| Pasarela escucha fuera de loopback | A14-2 | Riesgo de seguridad | **Aborto del arranque** y bloqueo hasta corregir | Seguro |
| Proveedor remoto agotado | L1 + cuota | Menos capacidad | Degradación en cascada del §6.5, con anotación en el acta | Degradado |
| **Fallo parcial: la pasarela responde con un modelo distinto al fijado** | Comparación de `model` devuelto con `pin_model` | Ronda con diversidad falsa | Descartar la respuesta, marcar el proveedor y reintentar con `pin_model` estricto; si reincide, prohibirlo | Consistente |
| Credenciales expuestas en `DATA_DIR` | Comprobación de permisos al arrancar | Riesgo | Corregir a `0600`/DPAPI y avisar; si no es posible, no arrancar con proveedores remotos | Seguro |
| Actualización automática de la pasarela | Cambio de versión detectado | Comportamiento distinto | Bloquear: sólo se ejecuta la versión de `config/externals.lock` | Determinista |
| Sin red | — | Sólo local | La pasarela sirve el proveedor local; todo el sistema sigue | Operativo |

### 14.10 Riesgos y mitigaciones

Superficie de red nueva en la máquina del usuario (media / **crítico** → loopback obligatorio, clave requerida, verificación activa cada 10 min, contenedor con red acotada). Fuga de material sensible a un proveedor remoto (media / crítico → `privacy_class` por defecto `local_only` en las cuatro clases de contenido, verificado con captura de tráfico). Dependencia de un proyecto de terceros en el camino de toda inferencia (media / alto → camino de reserva probado y obligatorio, PV-14.e.1). Deriva de comportamiento por actualización silenciosa (alta / medio → versión fijada y bloqueo de auto-actualización). Un «gratuito» que empieza a cobrar (media / alto → alerta por `cost_usd > 0` con detención). Violación involuntaria de términos por estrategias de reparto entre cuentas (media / alto → enumeración cerrada de estrategias y prohibición explícita). Compresión que rompe la trazabilidad de citas (alta si se activara / crítico → desactivada por defecto y prueba que lo verifica).

### 14.11 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA** en modo local puro: Node.js 20 LTS o un runtime OCI, y el servidor local de `llama.cpp` que el plan ya exige. **🟡 REQUIERE-PRERREQUISITO** para cada proveedor remoto: cuenta gratuita **del propio usuario** creada por la vía oficial del proveedor y su token; y, para Claude Code, el plan que el usuario ya tenga. **🔴** ninguno: el área no exige comprar nada, y su valor completo en modo offline es el de un endpoint unificado sobre el suelo local.

### 14.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (pasarela local con un único proveedor local + verificación de no exposición) → v1 (estrategias por rol, tres capas de resiliencia, telemetría conciliada, camino de reserva) → completo (niveles gratuitos oficiales del usuario, panel de cuotas, banco de sobrecoste y de privacidad).

- **P14.a Adopción segura.** P14.a.1 versión fijada y verificada — **PV-14.a.1**: la enumeración efectiva de estrategias y endpoints del build fijado se escribe en `config/externals.lock`; arranque bloqueado si difiere. P14.a.2 no exposición — **PV-14.a.2**: A14-2 en verde en 10/10 arranques y aborto forzado con `HOST=0.0.0.0`.
- **P14.b Política sobre pasarela.** P14.b.1 `RouteDirective` y filtro de capacidad — **PV-14.b.1**: 100 peticiones con capacidades exigidas, 0 servidas por un modelo que no las cumple. P14.b.2 diversidad — **PV-14.b.2**: 0 rondas con familias repetidas sin marca. P14.b.3 estrategias prohibidas — **PV-14.b.3**: `fusion`/`pipeline` rechazadas y revertidas.
- **P14.c Privacidad.** P14.c.1 clases de contenido — **PV-14.c.1**: las cuatro clases marcadas `local_only` automáticamente en 100 % de los casos. P14.c.2 captura de tráfico — **PV-14.c.2**: 0 bytes salientes en 200 peticiones sensibles.
- **P14.d Economía y telemetría.** P14.d.1 conciliación — **PV-14.d.1**: divergencias > 15 % detectadas 10/10. P14.d.2 coste cero — **PV-14.d.2**: acumulado 0 USD en 10 000 peticiones y alerta funcional. P14.d.3 sobrecoste — **PV-14.d.3**: p95 ≤ 25 ms o desvío automático al cliente directo.
- **P14.e Reserva.** P14.e.1 caída a mitad de trabajo — **PV-14.e.1**: 300 unidades completadas con ≤ 1 recomputada y declaración en el artefacto.

Métricas de salida: 0 exposiciones de red, 0 fugas de contenido sensible, coste acumulado 0 USD, sobrecoste p95 ≤ 25 ms, y camino de reserva verificado bajo caída real.

---

## ÁREA 15 — Ingesta universal de documentos: cualquier formato, de cualquier época

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA** hasta el nivel 5 de la cascada; el nivel 6 depende del Área 16, que también es 🟢.

### 15.1 Propósito y alcance

Garantiza que **el usuario pueda soltar cualquier fichero en la ventana y obtener algo utilizable**, sin filtros de extensión, sin listas de formatos admitidos y sin que importe que el fichero se creara en 1987 en un ordenador que ya no existe. Cubre procesadores de texto muertos, hojas de cálculo de los años ochenta, gráficos vectoriales de sistemas descontinuados, contenedores comprimidos con algoritmos que nadie usa, imágenes de disquete, bases de datos abandonadas, correo de programas extintos y ficheros sin extensión ni cabecera reconocible.

Queda fuera: la interpretación del contenido (Áreas 1, 2 y 5), la ejecución de programas antiguos (Área 16, a la que este módulo delega como último recurso) y la recuperación de soportes físicos dañados — leer un disquete requiere una disquetera y es 🔴; leer la **imagen** de ese disquete es 🟢 y sí está cubierto.

**Consume:** Área 0 (CAS, política, trabajos reanudables), Área 5 (análisis binario para formatos desconocidos), Área 16 (entornos de época). **Alimenta:** Área 1 (documentos normalizados), Área 2 (corpus y documentos bajo análisis), Área 11 (literatura y arte previo), Área 13 (fuentes indexables).

### 15.2 Arquitectura: una cascada de siete niveles que nunca dice «formato no soportado»

*Decisión:* la ingesta se organiza como **cascada de siete niveles con descenso automático**, donde cada nivel se intenta sólo si el anterior falla y **cada intento queda registrado con su resultado**, porque la alternativa —una tabla de formatos admitidos— garantiza que el fichero raro del usuario sea siempre el que falta.
*Descartado:* una única librería universal — no existe; las que lo prometen cubren bien los formatos vivos y mal los muertos, que son justamente los que nadie más abre.

```
   fichero soltado en la ventana (sin filtro de extensión)
        │
        ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │ N0 IDENTIFICACIÓN  magic bytes · estructura · bifurcación de recurso  │
 │    · extensión (última pista, nunca la primera) · entropía            │
 └───────┬──────────────────────────────────────────────────────────────┘
         ▼  perfil de formato + confianza
 ┌──────────────────────────────────────────────────────────────────────┐
 │ N1 LECTOR NATIVO         formatos vivos: PDF, DOCX, XLSX, PNG, CSV…   │
 ├──────────────────────────────────────────────────────────────────────┤
 │ N2 LIBRERÍA ESPECIALIZADA  WordPerfect, Lotus, ClarisWorks, dBase,    │
 │    CorelDraw, MOD/XM, Access, Outlook antiguo…                        │
 ├──────────────────────────────────────────────────────────────────────┤
 │ N3 CONVERSOR EXTERNO      LibreOffice · Gnumeric · ffmpeg ·           │
 │    ImageMagick · Ghostscript · pandoc · fontforge                     │
 ├──────────────────────────────────────────────────────────────────────┤
 │ N4 EXPANSIÓN DE CONTENEDOR  archivos comprimidos, imágenes de disco,  │
 │    firmware, instaladores → recursión sobre cada miembro              │
 ├──────────────────────────────────────────────────────────────────────┤
 │ N5 PARSEO DECLARATIVO     Kaitai Struct + análisis binario (Área 5):  │
 │    se ESCRIBE un lector para ese formato y se guarda para siempre     │
 ├──────────────────────────────────────────────────────────────────────┤
 │ N6 ENTORNO DE ÉPOCA (Área 16)  se arranca el sistema y la aplicación  │
 │    originales, se abre el fichero y se captura o se exporta           │
 ├──────────────────────────────────────────────────────────────────────┤
 │ N7 RESCATE PARCIAL        cadenas legibles, estructura inferida,      │
 │    mapa de bloques → se entrega lo que hay, declarado como parcial    │
 └───────┬──────────────────────────────────────────────────────────────┘
         ▼
   documento canónico + informe de ingesta (qué nivel lo resolvió, qué se perdió)
```

**Regla dura:** el proceso **nunca** termina con «formato no soportado». Termina en uno de cuatro estados, todos honestos: `leido_completo`, `leido_parcial` (con la lista de lo que falta), `abierto_en_entorno_de_epoca` (con la captura o la exportación obtenida) o `no_legible` (con el motivo técnico exacto, el volcado hexadecimal de la cabecera y el botón *Intentar de otra forma*).

### 15.3 Contratos e interfaces

```python
def identify(path: Path) -> FormatProfile: ...
def ingest(path: Path, *, budget: IngestBudget, allow_era_env: bool = True) -> IngestResult: ...
def expand_container(path: Path, *, max_depth: int = 6) -> list[MemberRef]: ...
def detect_encoding(data: bytes, *, hints: FormatProfile) -> EncodingGuess: ...
def build_kaitai_parser(samples: list[Path], hypothesis: StructHypothesis) -> ParserArtifact: ...
def open_in_era_environment(path: Path, profile: FormatProfile) -> EraOpenResult: ...
def salvage(path: Path) -> SalvageReport: ...
def register_format(profile: FormatProfile, reader: ReaderSpec) -> None: ...
```

Documento canónico de salida (lo que ven las demás áreas, sea cual sea el origen):

```json
{
  "ingest_id": "ing_01J9…",
  "source": {"sha256": "…", "bytes": 148992, "name": "MEMO.WP5", "mtime": "1993-04-17T00:00:00Z"},
  "format": {"family": "wordprocessor", "name": "WordPerfect 5.1", "confidence": 0.96,
             "evidence": ["magic FF 57 50 43", "estructura de prefijo de documento"],
             "era": "1989-1994", "endianness": "little"},
  "resolved_at_level": 3,
  "attempts": [{"level":1,"tool":"native","ok":false,"reason":"sin lector nativo"},
               {"level":2,"tool":"libwpd 0.10","ok":false,"reason":"versión anterior a la soportada"},
               {"level":3,"tool":"libreoffice 24.8 --convert-to odt","ok":true,"duration_ms":2410}],
  "encoding": {"detected": "CP437", "confidence": 0.88, "method": "histograma + marcas de dibujo de caja",
               "line_endings": "CRLF"},
  "content": {"text_ref": "cas://sha256:…", "layout_ref": "cas://sha256:…",
              "images": [{"ref":"cas://…","w":640,"h":480,"format_origen":"PCX"}],
              "tables": 3, "pages": 12},
  "fidelity": {"text": "completo", "formato": "aproximado", "imagenes": "completo",
               "perdido": ["macros", "campos de combinación de correspondencia"]},
  "status": "leido_completo",
  "custody": {"original_inmutable": true, "transformaciones": ["convert:libreoffice", "normalize:nfkc"]}
}
```

Eventos: `ingest.started`, `ingest.level{level, tool, ok}`, `ingest.finished{status, fidelity}`, `ingest.unknown_format{sha256}` (dispara el flujo del nivel 5), `format.registered{name}`. Tablas: `ingest_job`, `ingest_attempt`, `format_registry`, `format_sample` (DDL en §T14).

### 15.4 Implementación: el arsenal, por familia y por época

Todas las herramientas son libres y se invocan como **procesos separados dentro del trabajador confinado** de §6.3 C-2 (sin red, sin escritura fuera de su directorio temporal, sólo el descriptor del fichero de entrada), porque abrir un fichero de origen desconocido es la operación más expuesta de todo el sistema.

**N0 — Identificación.** `libmagic` 5.45 (`file`) como primera señal; **Apache Tika 3.x** en modo detección para el cruce; comprobación de **estructura** propia para los casos que ambos fallan (prefijos de longitud, tablas de sectores, cabeceras de registro); detección de **bifurcación de recurso** de Mac clásico (AppleDouble `._nombre`, MacBinary, BinHex `.hqx`); y la extensión **sólo como desempate**, nunca como fuente primaria — un `.doc` de 1991 no es un `.doc` de 2003 y confiar en la extensión produce el error más caro de esta área.

**N1/N2/N3 — Matriz de cobertura por familia** (herramienta principal → alternativa):

| Familia | Formatos representativos de época | Herramienta principal | Alternativa |
|---|---|---|---|
| Procesadores de texto DOS/Windows | WordStar, WordPerfect 4.2–6.x, Word 2/6/95/97, Works, AmiPro, DisplayWrite, Lotus WordPro, T602, ChiWriter | **LibreOffice 24.8 headless** (`--convert-to odt:writer8`), que integra `libwpd`, `libwps`, `libstaroffice` | `antiword` 0.37, `catdoc` 0.95, `unrtf` 0.21, `wpd2text` |
| Procesadores de texto Mac clásico | MacWrite, MacWrite II, ClarisWorks/AppleWorks, WriteNow, Nisus, DOCMaker, Mariner | **`libmwaw` 0.3.x** (vía LibreOffice) | Extracción de bifurcación de recurso + N5 |
| Hojas de cálculo | Lotus 1-2-3 (`.wk1/.wk3/.wk4/.123`), Quattro Pro, Multiplan (SYLK), VisiCalc, Excel 2–5/95/97, DIF | **Gnumeric 1.12 `ssconvert`** (la mejor cobertura de formatos muertos) | LibreOffice; `xls2csv` |
| Bases de datos | dBase III/IV/5 (`.dbf`), FoxPro, Paradox, Access `.mdb` antiguo, Btrieve | `dbfread` 2.x, **`mdbtools` 1.0** | N5 con esquema declarado |
| Presentaciones | Harvard Graphics, Freelance, PowerPoint 4/95/97 | LibreOffice | `catppt` |
| Gráficos vectoriales | CorelDraw (`.cdr` v1–v16), Micrografx, FreeHand, PageMaker, QuarkXPress, Visio antiguo, WMF/EMF, CGM, HPGL, DXF | **`libcdr`/`libfreehand`/`libpagemaker`/`libqxp`/`libvisio`/`libzmf`** vía LibreOffice | `uniconvertor`; ImageMagick para rasterizar |
| Imágenes raster antiguas | PCX, TGA, IFF/ILBM (Amiga), MacPaint, PICT, BMP OS/2 v1/v2, GIF87a, Sun Raster, Degas, XBM/XPM, PBM/PGM/PPM, JPEG antiguo | **ImageMagick 7.1** | `netpbm` 11.x para los muy raros; `libmwaw` para PICT incrustado |
| Sonido y música | MOD/S3M/XM/IT, MIDI, VOC, AU, AIFF, Shorten, RealAudio | **`libopenmpt` 0.7** (módulos), **`ffmpeg` 7.x** (resto) | `timidity` para renderizar MIDI |
| Vídeo antiguo | MPEG-1, Cinepak, Indeo, Sorenson, RealMedia, QuickTime antiguo, FLI/FLC | **`ffmpeg` 7.x** | N6 |
| Documentos de página | PostScript, PDF 1.0–1.3, DVI, Ghostscript-only | **Ghostscript 10.x**, `dvisvgm` | `pdftoppm` |
| Ayuda y libros | WinHelp `.hlp`, `.chm`, GEM, `.lit`, PalmDoc, Rocket eBook | `helpdeco`, `chmlib`/`archmage`, **`libe-book`** | N5 |
| Correo y agendas | `.pst` antiguo, `.dbx`, `.mbx`, Eudora, cc:Mail | `libpff` / `readpst` 0.6, `mbox` estándar | N5 |
| Tipografías | BDF, PCF, FON, PFB/PFM, maleta Mac | **`fontforge` 2024** | `fonttools` 4.x |
| CAD | DXF, DWG R12+, IGES | LibreCAD/`libdxfrw`, `dxfgrabber` | N6 con la aplicación de época |
| Contenedores comprimidos | ARC, ZOO, LZH/LHA, ARJ, PAK, SQZ, HA, StuffIt (`.sit`, `.sitx`), Compact Pro, ACE, RAR, ZIP con métodos *shrink/reduce/implode* | **`unar`/`lsar` 1.10** (la mejor cobertura de formatos muertos) | `p7zip` 17.05, `cabextract`, `unshield`, `msitools` |
| Codificación de transporte | uuencode, BinHex, MacBinary, AppleSingle/Double, Base64 en texto | `uudeview`, `macutils`, decodificador propio | — |
| Imágenes de disco | IMG/IMA (FAT12/16), ISO 9660, BIN/CUE, HFS y HFS+, ADF (Amiga), D64 (Commodore), imágenes CP/M, TD0, IMD | **`mtools` 4.0** (FAT), **`hfsutils`/`hfsplus`**, **`cpmtools` 2.2x**, `libdsk` 1.5, `bchunk` | N6 arrancando la imagen |
| Firmware y binarios opacos | Cualquiera | `unblob` 24.x, `binwalk` 2.3, y el Área 5 completa | N5 |

**Codificaciones de texto (el error silencioso más frecuente).** Detección con `uchardet` 0.0.8 más heurísticas propias que las librerías modernas no aplican: presencia de caracteres de **dibujo de caja** de CP437/CP850 (los antiguos menús de DOS), patrones de **EBCDIC** (CP037/CP500, de sistemas grandes), **Mac Roman** por su distribución de acentos, y fin de línea **sólo CR** (Mac clásico) frente a LF y CRLF. Conversión con `iconv`, conservando **siempre** el byte original en el CAS. Cuando la confianza baja de 0,7, el documento se marca `encoding_incierto` y se ofrecen al usuario las tres interpretaciones más probables con una muestra de 200 caracteres de cada una, para que elija mirando — que es más fiable que cualquier heurística.

**N4 — Expansión recursiva de contenedores.** Profundidad máxima 6, con detección de bombas de descompresión: se aborta si la razón de expansión supera 200:1 o si el total supera 4 GB, y se declara. Cada miembro entra en la cascada como fichero independiente, conservando su ruta lógica (`disco.img/DOCS/MEMO.WP5`) para que la procedencia sea navegable.

**N5 — Escribir el lector que no existe.** Cuando ninguna herramienta reconoce el formato y hay **al menos tres muestras** del mismo tipo, se dispara un flujo propio: análisis de estructura (entropía por bloques, detección de tablas de desplazamientos, longitudes repetidas, cadenas ancladas), hipótesis de estructura emitida por MELCHIOR • 1, **especificación en Kaitai Struct** (`.ksy`), generación del lector en Python, y validación contra las muestras. Cada campo de la hipótesis es una afirmación falsable y su refutación es directa: el lector aplicado a la muestra 3 debe producir valores coherentes con los de las muestras 1 y 2. El lector resultante se guarda en `formats/kaitai/<nombre>.ksy` y **queda disponible para siempre**: es la única parte del sistema donde el trabajo del usuario amplía permanentemente la capacidad del producto.

**N6 — Entorno de época.** Si el formato es propietario, cerrado y sin librería libre —el caso de bastantes programas de nicho de los noventa—, se delega en el **Área 16**: se arranca un sistema de la época con la aplicación original que el usuario posea, se abre el fichero, y se obtiene o bien una **exportación** a un formato abierto (la vía preferida, porque conserva el texto) o bien una **captura de pantalla** de la ventana (la vía de última instancia, que luego pasa por el Área 1 para recuperar el contenido visualmente). El sistema **no distribuye** ninguna aplicación propietaria: usa la que el usuario aporte, exactamente igual que con las normas del Área 2.

**N7 — Rescate.** Extracción de cadenas legibles con su desplazamiento, mapa de bloques por entropía, tablas de fechas plausibles, y cualquier estructura reconocible parcialmente. Se entrega como `leido_parcial` con la advertencia clara de que es un rescate, no una lectura.

Tabla de paridad:

| Elemento | Impl. Windows | Impl. Linux |
|---|---|---|
| Herramientas de conversión | Binarios en `tools\ingest\`; LibreOffice portable | Paquetes del sistema o `tools/ingest/`; LibreOffice del sistema |
| Trabajador confinado | Proceso de baja integridad en Job Object con límite de memoria y CPU | `seccomp` en lista blanca + `unshare` de red + montaje de sólo lectura |
| Montaje de imágenes de disco | `mtools`/`hfsutils` en modo fichero (sin montar en el SO) | ídem, sin `mount` privilegiado |
| Bifurcación de recurso Mac | Detección de `._nombre` y MacBinary en el propio fichero | ídem |
| Fin de línea y codificación | Idéntico (cómputo puro) | Idéntico |

### 15.5 Algoritmos

**A15-1 — Cascada de identificación e ingesta.**
```
 1. calcular sha256 y guardar el original inmutable en el CAS (nunca se modifica el fichero del usuario)
 2. N0: magic(libmagic) ∪ tika_detect ∪ estructura_propia ∪ bifurcación_de_recurso
    2.1 si dos fuentes coinciden → confianza 0,9; si sólo una → 0,6; si ninguna → 0,0 y se salta a N4/N5
    2.2 la extensión suma 0,05 y NUNCA decide sola
 3. para nivel en [1..4]:
    3.1 buscar en format_registry el lector del perfil; si no hay, siguiente nivel
    3.2 ejecutar en el trabajador confinado con presupuesto (30 s por defecto, 300 s para conversión de oficina)
    3.3 validar la salida: ¿texto no vacío? ¿tamaño coherente? ¿imágenes decodificables?
        una conversión que devuelve 0 bytes o texto de basura (>60 % de caracteres no imprimibles) es FALLO
    3.4 registrar el intento con su herramienta, resultado y duración
 4. si sigue sin resolverse y hay ≥ 3 muestras del mismo perfil → N5 (parseo declarativo)
 5. si no, y allow_era_env → N6 (Área 16)
 6. si no, N7 (rescate) y estado leido_parcial o no_legible
 7. caso límite: fichero de 0 bytes, o fichero que es sólo una bifurcación de recurso → se declara y se
      busca el fichero de datos hermano
 8. caso límite: el mismo fichero es válido como dos formatos (por ejemplo, un ZIP que también es un JAR
      y un DOCX) → se resuelve por estructura interna, no por magic, y se registra la ambigüedad
```

**A15-2 — Detección de codificación con heurísticas de época.**
```
1. si hay BOM → decidido
2. uchardet sobre la muestra completa → candidato y confianza
3. heurísticas propias, que suman evidencia:
   3.1 densidad de bytes 0xB0–0xDF con patrón de marco → CP437/CP850 (menús de DOS)
   3.2 ausencia total de 0x20 como byte más frecuente y presencia de 0x40 → EBCDIC
   3.3 0x8E/0x8F/0xA5 en posiciones de vocal acentuada → Mac Roman
   3.4 fin de línea sólo CR → Mac clásico, refuerza Mac Roman
   3.5 rango 0xA1–0xFE en pares → codificación de doble byte (se detecta y se convierte, sin que el
       usuario tenga que saberlo; la interfaz siempre muestra el resultado en español)
4. si la mejor confianza < 0,7 → estado encoding_incierto y se ofrecen 3 muestras al usuario para elegir
5. la elección del usuario se guarda por perfil de formato y se reutiliza en el resto del lote
```

**A15-3 — Aprendizaje de un formato nuevo (nivel 5), con debate.**
```
1. agrupar por sha256 de cabecera los ficheros no identificados; exigir ≥ 3 muestras
2. análisis estructural determinista: entropía por bloques de 512 B, búsqueda de tablas de
     desplazamientos (enteros crecientes que apuntan dentro del fichero), longitudes prefijadas,
     cadenas con terminador, marcas de fecha plausibles (1980–2000 en formatos DOS y Mac)
3. MELCHIOR • 1 emite una hipótesis de estructura como especificación Kaitai (.ksy) — afirmación falsable
4. BALTHASAR • 2 la refuta aplicándola a la muestra que MELCHIOR no vio: si produce longitudes fuera de
     rango, desplazamientos que salen del fichero o texto ilegible, la hipótesis cae con el caso mínimo
5. CASPER • 3 acepta cuando el lector reconstruye ≥ 90 % del contenido de las 3 muestras sin
     inconsistencias, y exige registro en format_registry con su nivel de confianza
6. el .ksy y su lector generado se versionan y se comparten como artefacto del proyecto
7. caso límite: formato comprimido con algoritmo propio → se declara y se pasa a N6, porque adivinar un
     compresor desde cero no cabe en el presupuesto y el entorno de época lo resuelve en minutos
```

### 15.6 Integración con el debate popperiano

Afirmaciones: la identificación del formato, la fidelidad declarada de la conversión, la codificación detectada y la estructura hipotética del nivel 5. Evidencia admisible: bytes de cabecera con su desplazamiento, resultado de la herramienta con su versión, comparación de la reconstrucción con las muestras, y la captura del entorno de época. Refutación más potente: **la reconstrucción fallida sobre una muestra no vista** (nivel 5) y **la comparación de la conversión con la apertura en el entorno de época** — si el texto convertido y el texto que muestra la aplicación original difieren, la fidelidad declarada es falsa, y eso se comprueba de forma automática cuando el Área 16 está disponible. Invocación: siempre en el nivel 5, y siempre que la fidelidad declarada sea distinta de «completo» en un documento que vaya a alimentar un dictamen del Área 2.

### 15.7 Costos, latencia y recursos

Identificación: ≤ 40 ms por fichero. Lectores nativos: ≤ 200 ms. Librerías especializadas: 0,1–2 s. Conversión con LibreOffice: 1,5–8 s por documento (el proceso se mantiene vivo entre conversiones con `--headless --accept=socket` para no pagar el arranque, que son 3 s). Expansión de contenedor: dominada por E/S. Nivel 5 con debate: ≈ 60 000 tokens y 4–15 min, pero **una sola vez por formato en la vida del sistema**. Nivel 6: el arranque del entorno de época, 8–40 s (Área 16). RAM: ≤ 1,2 GB con LibreOffice residente; el trabajador confinado se limita a 512 MB por fichero. **Salto del debate:** los niveles 1 a 4 con validación de salida correcta son R0 deterministas y no se debaten. **Caché:** por `sha256(fichero)+versión_de_la_cascada`, de modo que reingerir un expediente ya procesado es instantáneo; el `format_registry` se cachea en memoria.

### 15.8 Calidad y pruebas

El banco de esta área es un **corpus de época** de 400 ficheros reales o generados, distribuidos por familia y por década (1980-1989: 80; 1990-1999: 200; 2000-2009: 80; sin fecha o sin extensión: 40), con verdad de terreno sobre su contenido textual.

| Caso | Criterio de éxito |
|---|---|
| Camino feliz | 100 documentos vivos (PDF, DOCX, XLSX, PNG): 100/100 `leido_completo` en ≤ 2 s cada uno |
| **Cobertura de época** | Sobre los 400 del corpus: ≥ **92 %** en estado `leido_completo` o `leido_parcial` con texto recuperado, y **0 %** en «formato no soportado» (ese estado no existe) |
| Fidelidad de texto | Sobre los 200 con verdad de terreno textual: distancia de edición normalizada ≤ **0,05** frente al texto real |
| Sin filtro de extensión | 50 ficheros renombrados con extensión falsa: identificados correctamente 50/50 (la extensión no decide) |
| Sin extensión | 40 ficheros sin extensión: identificados o descendidos correctamente en la cascada, 0 rechazos |
| Codificación | 60 ficheros en CP437, CP850, Mac Roman, EBCDIC e ISO-8859-1: codificación correcta en ≥ 55; los 5 restantes marcados `encoding_incierto`, nunca convertidos mal en silencio |
| Contenedores anidados | Imagen de disquete → archivo comprimido → documento: los tres niveles expandidos y el documento leído, 20/20 |
| Bomba de descompresión | Fichero con razón 1000:1: abortado en ≤ 3 s, sin llenar el disco, con mensaje claro |
| Fichero malformado y hostil | Corpus de ficheros corruptos y construidos para romper analizadores: **0 caídas del núcleo, 0 escrituras fuera del temporal, 0 conexiones de red** (esto es también la prueba del confinamiento de §6.3 C-2) |
| Aprendizaje de formato (N5) | 5 formatos propietarios sintéticos con 3 muestras cada uno: lector generado y validado en ≥ 4 de 5 |
| Entorno de época (N6) | 10 ficheros que ninguna herramienta abre: ≥ 8 abiertos y exportados o capturados |
| Consenso / desacuerdo | Fidelidad declarada «completo» refutada por comparación con el entorno de época: el veredicto rebaja la fidelidad, 10/10 |
| Custodia | El fichero original nunca se modifica: hash idéntico antes y después en 400/400 |

### 15.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta automática | Estado |
|---|---|---|---|---|
| Conversor externo ausente | comprobación al arrancar | Menos cobertura | Descender al siguiente nivel y declarar qué herramienta falta con su comando de instalación | Degradado, explicado |
| Conversión que devuelve basura | validador de salida (>60 % no imprimible) | Texto inservible | Marcar el intento como fallo y descender, nunca aceptar la basura | Consistente |
| **Fallo parcial (el peor): conversión que parece buena y perdió la mitad** | Comparación de longitud con la estimación estructural y, si hay Área 16, con la apertura original | Pérdida silenciosa | Marcar `fidelidad: aproximado` y enumerar lo perdido; si la diferencia supera el 25 %, forzar N6 | Seguro |
| Codificación mal detectada | Confianza < 0,7 o alta densidad de reemplazos | Texto ilegible | Preguntar al usuario con tres muestras visibles | Consistente |
| Bomba de descompresión | Razón de expansión | Disco lleno | Aborto y cuarentena del contenedor | Seguro |
| Analizador que cuelga | Timeout del trabajador | Bloqueo | Matar el trabajador, marcar el intento y descender | Recuperado |
| Sin Área 16 disponible | Comprobación | Sin nivel 6 | Terminar en N7 con rescate parcial y decirlo | Degradado, honesto |
| Sin red | — | Ninguno | Toda la cascada es local | Operativo |

### 15.10 Riesgos y mitigaciones

Ejecución de código por un analizador vulnerable (media / **crítico** → trabajador confinado sin red ni escritura, corpus hostil en el banco, y el analizador nunca corre en el proceso del núcleo). Pérdida silenciosa de contenido en la conversión (alta / alto → validación de salida, fidelidad declarada por partes y contraste con el entorno de época). Extensión engañosa (alta / medio → la extensión no decide nunca). Bomba de descompresión (media / medio → límites duros). Falsa sensación de universalidad (alta / medio → el informe de ingesta dice siempre qué nivel resolvió el fichero y qué se perdió; «leído» y «leído del todo» no son lo mismo y la interfaz los distingue). Dependencia de aplicaciones propietarias en N6 (media / bajo → las aporta el usuario, no se distribuyen, y N7 siempre existe como suelo).

### 15.11 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA:** `libmagic` 5.45, Apache Tika 3.x (requiere Java 21), LibreOffice 24.8, Gnumeric 1.12, ImageMagick 7.1, `netpbm` 11.x, `ffmpeg` 7.x, `libopenmpt` 0.7, Ghostscript 10.x, `unar`/`lsar` 1.10, `p7zip` 17.05, `cabextract`, `msitools`, `mtools` 4.0, `hfsutils`, `cpmtools` 2.2x, `libdsk` 1.5, `mdbtools` 1.0, `dbfread` 2.x, `libpff`/`readpst` 0.6, `chmlib`, `helpdeco`, `fontforge` 2024, `uchardet`, `iconv`, Kaitai Struct 0.10, y las librerías del Document Liberation Project que LibreOffice ya trae. Todo libre, todo local. **🟡 REQUIERE-PRERREQUISITO:** para el nivel 6, el Área 16 y —si el formato es propietario— la aplicación original que el usuario posea legítimamente. **🔴 BLOQUEADO-SIN-HARDWARE:** leer un soporte físico antiguo (disquete, cinta, disco Zip) exige la unidad correspondiente; el sistema trabaja con la **imagen** del soporte, que es 🟢, y documenta cómo obtenerla.

### 15.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (N0 + N1 + N4 con el corpus vivo) → v1 (N2 y N3 completos, codificaciones de época, imágenes de disco) → completo (N5 con debate, N6 contra el Área 16, corpus de 400 y banco de fidelidad).

- **P15.a Identificación.** P15.a.1 fusión de señales — **PV-15.a.1**: 50/50 ficheros con extensión falsa identificados correctamente. P15.a.2 bifurcaciones y contenedores de transporte — **PV-15.a.2**: MacBinary, BinHex y AppleDouble reconocidos y decodificados, 20/20.
- **P15.b Lectores y conversores.** P15.b.1 matriz N2/N3 instalada y verificada — **PV-15.b.1**: cada familia de §15.4 con al menos un fichero leído correctamente. P15.b.2 validador de salida — **PV-15.b.2**: 30 conversiones basura sembradas, 30 detectadas y descendidas.
- **P15.c Codificación.** P15.c.1 heurísticas de época — **PV-15.c.1**: ≥ 55/60 correctas y el resto marcadas inciertas, 0 conversiones erróneas silenciosas.
- **P15.d Contenedores.** P15.d.1 recursión con límites — **PV-15.d.1**: anidamiento de 3 niveles resuelto 20/20 y bomba abortada en ≤ 3 s.
- **P15.e Formatos nuevos.** P15.e.1 flujo Kaitai con debate — **PV-15.e.1**: 4 de 5 formatos sintéticos aprendidos y registrados. P15.e.2 persistencia — **PV-15.e.2**: el lector aprendido resuelve el formato al primer intento en la siguiente sesión.
- **P15.f Confinamiento y corpus.** P15.f.1 corpus hostil — **PV-15.f.1**: 0 caídas, 0 escrituras fuera del temporal, 0 conexiones. P15.f.2 corpus de época — **PV-15.f.2**: ≥ 92 % de cobertura y distancia de edición ≤ 0,05 en los que tienen verdad de terreno.

Métricas de salida: cobertura ≥ 92 % sobre el corpus de época, 0 estados «no soportado», 0 modificaciones del fichero original, y confinamiento verificado con corpus hostil.

---

## ÁREA 16 — Sistemas operativos portables y entornos de época

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA** con sistemas de libre redistribución; **🟡** cuando el usuario aporta su propio soporte con licencia; **🔴** nada — el área completa se construye y se verifica sin comprar nada.

### 16.1 Propósito y alcance

Permite **construir un sistema operativo completo, empaquetarlo en un único ejecutable y abrirlo en una ventana dentro del ordenador donde está instalado MAGI System IDE**, sin instalar nada más, sin tocar el arranque de la máquina y sin privilegios de administrador. Ese mismo mecanismo da al sistema tres capacidades que hasta ahora le faltaban: un **entorno de época** para abrir con la aplicación original los ficheros que ninguna librería moderna lee (nivel 6 del Área 15), un **banco de pruebas desechable** donde ejecutar binarios de origen desconocido sin arriesgar la máquina (Área 5), y un **destino de despliegue** para el software que el propio sistema sintetiza.

Queda fuera: la virtualización de servidores o de cargas de producción; el arranque del sistema construido en hardware real (se documenta cómo escribir la imagen a un USB, pero hacerlo es una acción del usuario, no del sistema); y la distribución de sistemas operativos propietarios, que está expresamente prohibida por **CTL-4**.

**Consume:** Área 0 (procesos, política, CAS), Área 8 (radio de impacto de las acciones), Área 15 (peticiones de apertura en entorno de época). **Alimenta:** Área 15 (nivel 6), Área 5 (ejecución aislada de binarios y de emuladores construidos), Área 9 (pruebas de firmware con periféricos redirigidos), Área 11 (prototipos de software distribuibles).

### 16.2 Arquitectura

```
  receta declarativa (YAML)            imagen aportada por el usuario
        │ base · paquetes · ajustes            │ (ISO propia, licencia propia)
        ▼                                      ▼
 ┌──────────────────────────────────────────────────────────────────┐
 │ CONSTRUCTOR   Buildroot 2024.x | Alpine mkimage | receta FreeDOS  │
 │  salida: núcleo + sistema de ficheros raíz + configuración        │
 │  ⚠ reproducible: SOURCE_DATE_EPOCH fijo, orden estable, sin red   │
 └──────────┬───────────────────────────────────────────────────────┘
            │ imagen (qcow2 / raw) + manifiesto con hashes
            ▼
 ┌──────────────────────────────────────────────────────────────────┐
 │ EMPAQUETADOR  → EJECUTABLE ÚNICO                                  │
 │  lanzador en Rust con la imagen y el motor EMBEBIDOS              │
 │  Windows: .exe   ·   Linux: ELF estático / AppImage               │
 └──────────┬───────────────────────────────────────────────────────┘
            │ un solo fichero, sin instalación
            ▼
 ┌──────────────────────────────────────────────────────────────────┐
 │ EJECUTOR EN VENTANA                                               │
 │  ruta A: QEMU 9.x + virtio-gpu, pantalla por SPICE local,         │
 │          cliente embebido en la ventana de MAGI System IDE        │
 │  ruta B: emulador x86 en WebAssembly dentro del propio panel      │
 │          (sistemas muy ligeros, sin ningún binario externo)       │
 │  ruta C: DOSBox-X para MS-DOS y compatibles                       │
 │  ⚠ red DESACTIVADA y carpeta compartida AUSENTE por defecto       │
 └──────────┬───────────────────────────────────────────────────────┘
            ▼
   instantánea previa · captura de pantalla · exportación de ficheros · registro
```

*Decisión:* el motor principal es **QEMU 9.x**, con aceleración por el hipervisor del sistema cuando está disponible (KVM en Linux, la plataforma de hipervisor de Windows en Windows) y emulación pura cuando no, porque es la única pieza libre que cubre a la vez varias arquitecturas, dispositivos redirigidos por USB y una salida gráfica que se puede incrustar.
*Descartado:* usar la virtualización nativa de cada sistema operativo (dos implementaciones, dos conjuntos de fallos) y contenedores tipo Docker (comparten el núcleo del anfitrión: no sirven para arrancar otro sistema operativo ni para aislar de verdad un binario hostil).

*Decisión:* además de QEMU se incorpora una **ruta ligera basada en un emulador x86 compilado a WebAssembly**, que se ejecuta dentro del propio panel de la interfaz sin ningún binario externo, para sistemas pequeños (MS-DOS libre, Linux mínimo, sistemas de nicho) — porque cubre el caso «quiero enseñarle esto a alguien y que le funcione al primer intento» sin depender de que el anfitrión tenga virtualización.
*Descartado:* que la ruta ligera fuera la única — su rendimiento no sirve para compilar ni para emuladores de consola.

### 16.3 Contratos e interfaces

```python
def build_portable_os(recipe: Path, *, reproducible: bool = True) -> OsImage: ...
def package_single_executable(image: OsImage, target: Literal["windows","linux"],
                              *, engine: Literal["qemu","wasm","dosbox"]) -> Path: ...
def launch_in_window(image_or_exe: Path, *, net: bool = False, share: Path | None = None,
                     snapshot: bool = True) -> VmSession: ...
def snapshot(session: VmSession, name: str) -> SnapshotRef: ...
def restore(session: VmSession, snap: SnapshotRef) -> None: ...
def send_file(session: VmSession, src: Path) -> None: ...          # entrada por imagen ISO efímera
def collect_output(session: VmSession, glob: str) -> list[Path]: ...
def capture_screen(session: VmSession) -> Path: ...
def run_in_era(profile: EraProfile, doc: Path) -> EraOpenResult: ...
def verify_reproducible(recipe: Path, times: int = 2) -> ReproReport: ...
```

Receta declarativa (`os/recipes/*.yaml`), ejemplo completo:

```yaml
name: minimo-linux-analisis
base: buildroot-2024.11          # buildroot | alpine-3.20 | freedos-1.3 | reactos-0.4 | haiku-r1b5 | kolibri
arch: x86_64
kernel: 6.6.x-lts
init: busybox
packages: [python3.12, file, binutils, less, nano]
display: {mode: virtio-gpu, width: 1280, height: 800}
memory_mb: 1024
disk_mb: 2048
network: none                    # none | host-only | nat  (por defecto none, y cambiarlo es una decisión con radio)
shared_folder: none              # none | ro:<ruta> | rw:<ruta>
persistence: overlay             # none | overlay | full
autostart: /usr/bin/python3
reproducible:
  source_date_epoch: 1735689600
  lock: os/recipes/minimo-linux-analisis.lock   # hashes de todas las fuentes
output:
  single_executable: [windows, linux]
  max_size_mb: 180
```

Eventos: `os.build.started`, `os.build.progress{stage,pct}`, `os.build.finished{sha256,size,reproducible}`, `vm.started{session,engine,accel}`, `vm.stopped{session,reason}`, `vm.snapshot{session,name}`, `vm.escape_attempt{session,detail}` (crítico). Tablas: `os_recipe`, `os_image`, `vm_session`, `vm_snapshot`, `era_profile` (DDL en §T14).

### 16.4 Implementación

**Construcción.** *Decisión:* **Buildroot 2024.x** como constructor principal de sistemas Linux mínimos y **Alpine Linux 3.20** cuando se necesita gestor de paquetes en el sistema resultante — porque Buildroot produce imágenes de decenas de megabytes con dependencias fijadas y compilación cruzada, y Alpine da un sistema usable y actualizable en un tamaño todavía razonable.
*Descartado:* construir desde cero al estilo *Linux From Scratch* — didáctico, pero irreproducible en la práctica y sin ventaja frente a Buildroot.

Bases de libre redistribución soportadas, todas verificadas por hash y con su licencia registrada: **Buildroot/Linux** (GPL-2.0), **Alpine Linux 3.20** (mayormente MIT/BSD), **FreeDOS 1.3** (GPL, sistema compatible con MS-DOS), **ReactOS 0.4.x** (GPL, compatible con aplicaciones de Windows de la época), **Haiku R1 beta** (MIT, heredero de BeOS), **NetBSD 10** y **FreeBSD 14** (BSD), y **KolibriOS** (GPL, sistema completo en menos de 2 MB, ideal para demostraciones y para la ruta WebAssembly).

Reproducibilidad: `SOURCE_DATE_EPOCH` fijo, orden de construcción estable, construcción **sin red** a partir de un caché de fuentes con hashes en el fichero `.lock`, marcas de tiempo normalizadas en el sistema de ficheros y eliminación de rutas de construcción del binario. Criterio: **dos construcciones de la misma receta producen imágenes con el mismo SHA-256**.

**Empaquetado en un único ejecutable.** *Decisión:* un **lanzador escrito en Rust** (`os/launcher/`) que lleva **embebidos** el motor (QEMU estático o el emulador WebAssembly con su tiempo de ejecución), la imagen del sistema y el manifiesto, mediante inclusión de los bytes en tiempo de compilación; al ejecutarse extrae lo necesario a un directorio temporal propio (en Linux, preferentemente a un descriptor de memoria sin tocar el disco), arranca el sistema en una ventana y limpia al salir — porque es la única forma de tener **un fichero, doble clic, funciona**, que es exactamente lo que se pidió.
*Descartado:* un instalador o un archivo autoextraíble con guion — deja rastro, pide permisos y rompe la premisa de portabilidad.

Estructura del ejecutable resultante y sus garantías: firma opcional del artefacto, verificación del hash de la imagen antes de arrancar, código de salida del sistema huésped propagado al anfitrión, y modo `--headless` para usarlo desde un guion. Tamaños objetivo: **≤ 60 MB** para FreeDOS o KolibriOS, **≤ 180 MB** para un Linux mínimo con Python, **≤ 400 MB** para Alpine con entorno gráfico ligero. Si una receta excede su `max_size_mb`, la construcción falla y dice qué paquete es el responsable.

**Ejecución en ventana.** Tres rutas, elegidas automáticamente según el sistema y el anfitrión, con la elección siempre visible:

| Ruta | Cuándo se usa | Pantalla | Rendimiento |
|---|---|---|---|
| **A — QEMU** | Sistemas completos, compilación, emuladores, dispositivos redirigidos | `virtio-gpu` con servidor SPICE en el bucle local; el cliente va **embebido en un panel** de la interfaz (`GraphCanvas` hermano, `VmCanvas`), con teclado y ratón capturados y liberados con `Ctrl+Alt` | Cercano al nativo con aceleración; 5–20× más lento sin ella |
| **B — WebAssembly** | Sistemas pequeños, demostraciones, máquinas sin virtualización | Lienzo dentro del propio panel, sin proceso externo | Suficiente para MS-DOS y sistemas de nicho |
| **C — DOSBox-X** | MS-DOS y aplicaciones de esa época que necesitan hardware simulado fiel | Ventana embebida | Excelente para su caso |

**Seguridad por defecto, que aquí es lo que decide si el área es útil o peligrosa.** Red **desactivada**; carpeta compartida **ausente**; portapapeles compartido **desactivado**; redirección de dispositivos USB **desactivada**. Activar cualquiera de las cuatro es una acción con radio de impacto: `network: nat` y `shared_folder: rw:` son **R2** (el sistema huésped puede alcanzar la red del usuario o escribir en su disco) y exigen veredicto favorable de CASPER • 3 más confirmación explícita con el efecto descrito en lenguaje llano. La entrada de ficheros por defecto **no** usa carpeta compartida sino una **imagen ISO efímera de sólo lectura** generada al vuelo con los ficheros que se quieren meter, que es un canal de una sola dirección y sin sorpresas. La salida se recoge por una **segunda imagen** que el huésped escribe y el anfitrión lee tras apagar, o por el portapapeles cuando se habilita explícitamente.

**Detección de fuga (`vm.escape_attempt`).** Se vigilan y se registran: intentos de conexión de red desde el huésped cuando la red está desactivada (contador del cortafuegos del motor), accesos a rutas del anfitrión fuera de las imágenes montadas, y uso de canales del motor no declarados en la receta. Cualquiera de los tres es evento **crítico**, detiene la sesión y queda en la auditoría.

**Entornos de época (integración con el Área 15).** `os/era/*.yaml` describe perfiles listos: *MS-DOS 6 compatible* (FreeDOS 1.3 + intérprete y utilidades libres), *Windows de los noventa compatible* (ReactOS, para aplicaciones de esa era), *BeOS compatible* (Haiku), *Amiga*, *Commodore* y *CP/M* (con sus emuladores libres correspondientes). Cada perfil declara qué formatos sabe abrir y con qué aplicación; **las aplicaciones propietarias las aporta el usuario** desde su propio soporte y **nunca** se empaquetan en un artefacto de salida (CTL-4, mismo mecanismo que CTL-1). El flujo automático es: arrancar el perfil, montar la ISO efímera con el documento, lanzar la aplicación con el documento como argumento, esperar a que la ventana se estabilice, intentar **exportar** a un formato abierto mediante la automatización de teclado del propio huésped (secuencias declaradas por perfil, no adivinadas) y, si no hay exportación posible, **capturar la pantalla** y devolverla al Área 1.

**CTL-4 — control legal nuevo.** Punto de aplicación: `os/packager.py::package_single_executable()`. Regla: se rechaza el empaquetado si el manifiesto de la imagen contiene cualquier componente cuyo registro de licencia no permita redistribución (sistemas propietarios, aplicaciones aportadas por el usuario, fuentes con licencia restringida), con `PackagingRefused(code="CTL4")`. El usuario **puede** construir y ejecutar localmente una máquina con su propio soporte con licencia; lo que no puede es generar con ella un ejecutable distribuible, y el sistema se lo explica en una frase en vez de dejarle descubrirlo después.

Tabla de paridad:

| Elemento | Impl. Windows | Impl. Linux |
|---|---|---|
| Aceleración | Plataforma de hipervisor de Windows (requiere activarla, es un 🟡 documentado) | KVM (`/dev/kvm`, grupo `kvm`) |
| Sin aceleración | Emulación pura, funcional y más lenta; se avisa en la interfaz | ídem |
| Ejecutable único | `.exe` con los recursos embebidos | ELF estático o AppImage |
| Extracción temporal | Directorio temporal por sesión, borrado al salir | `memfd_create` cuando es posible; si no, directorio temporal |
| Pantalla embebida | Cliente SPICE en el panel; ventana secundaria como alternativa | ídem |
| Carpeta compartida (si se activa) | `virtiofs` o SMB local | `virtiofs` o `9p` |
| Aislamiento del proceso del motor | Job Object con límites | cgroup v2 + `seccomp` |

### 16.5 Algoritmos

**A16-1 — Construcción reproducible y verificada.**
```
1. leer receta; resolver todas las fuentes contra el .lock (hash por fuente); si falta alguna, abortar
2. construir con red DESACTIVADA a partir del caché de fuentes  (una construcción que necesita red no es reproducible)
3. normalizar: SOURCE_DATE_EPOCH, marcas de tiempo del sistema de ficheros, orden de directorios,
     eliminación de rutas de construcción y de identificadores aleatorios
4. calcular sha256 de la imagen y compararlo con la construcción anterior si existe
5. verify_reproducible: construir 2 veces en directorios distintos y exigir hashes idénticos
6. registrar el manifiesto: componente, versión, licencia, hash  → alimenta CTL-4
7. caso límite: un paquete introduce una marca de tiempo o un identificador aleatorio → se detecta por la
     diferencia entre las dos construcciones, se localiza el fichero culpable y se declara; si no se puede
     normalizar, la receta se marca no_reproducible y el artefacto lo dice
```

**A16-2 — Empaquetado en ejecutable único.**
```
1. seleccionar motor: qemu (por defecto) | wasm (si imagen ≤ 64 MB y el sistema está en la lista ligera) | dosbox
2. comprobar tamaño: motor + imagen comprimida ≤ max_size_mb; si no, informar qué paquete sobra
3. compilar el lanzador Rust con la imagen y el motor incluidos como bytes; sin dependencias dinámicas
4. incrustar el manifiesto (componentes, licencias, hashes) como recurso legible con `--manifest`
5. CTL-4: si algún componente no es redistribuible → PackagingRefused, con la lista exacta
6. firmar opcionalmente y publicar el sha256 junto al ejecutable
7. prueba obligatoria de humo: ejecutar el artefacto en una máquina limpia (contenedor sin nada instalado),
     comprobar que arranca hasta el indicador de sistema y que sale con código 0
8. caso límite: antivirus del anfitrión bloquea el autoextraíble → el lanzador evita patrones de
     autoextracción sospechosos (nada de escribir y ejecutar en el directorio de descargas) y se documenta
```

**A16-3 — Apertura de un documento en entorno de época (nivel 6 del Área 15).**
```
1. elegir perfil por la época y la familia del formato (era_profile)
2. crear ISO efímera de sólo lectura con el documento (canal de una dirección)
3. arrancar la sesión: red desactivada, sin carpeta compartida, instantánea previa tomada
4. lanzar la aplicación con el documento; esperar estabilidad de la pantalla (dos capturas consecutivas
     con diferencia < 1 % en 3 s) o el marcador declarado por el perfil
5. intentar EXPORTAR con la secuencia de teclas declarada en el perfil (nunca adivinada); recoger el
     resultado por la imagen de salida
6. si no hay exportación: capturar pantalla a resolución nativa y devolverla al Área 1 para recuperar el texto
7. apagar, restaurar la instantánea (la sesión es desechable por construcción) y registrar todo
8. criterio de éxito: la exportación contiene texto no vacío, o la captura contiene ≥ 50 caracteres
     reconocibles por el Área 1
9. caso límite: la aplicación pide licencia o registro → se declara y se devuelve al usuario con el motivo
```

### 16.6 Integración con el debate popperiano

Afirmaciones: «esta imagen es reproducible», «este ejecutable arranca en una máquina limpia sin instalar nada», «la sesión no tuvo acceso a la red», «el documento se abrió con fidelidad». Evidencia admisible: los dos hashes de la construcción doble, el registro de la prueba de humo en máquina limpia, el contador del cortafuegos del motor y la captura de tráfico del anfitrión, y la comparación entre la exportación del entorno de época y la conversión del Área 15. Refutación más potente: **ejecutar el artefacto en un contenedor sin nada instalado y ver que no arranca**, y **la captura de tráfico que muestra actividad de red con la red declarada desactivada** — ambas automáticas y sin margen de discusión. Invocación: antes de publicar cualquier artefacto portable y antes de activar red o carpeta compartida en una sesión.

### 16.7 Costos, latencia y recursos

Construcción con Buildroot: 8–35 min la primera vez (compilación cruzada completa), 1–4 min con caché caliente; ocupa `TOOLCHAIN_HEAVY`. Empaquetado: 20–90 s. Arranque de una sesión: FreeDOS ≈ 3 s, Linux mínimo 6–12 s con aceleración y 25–60 s sin ella, ReactOS 20–45 s. RAM: la declarada en la receta más ≈ 250 MB del motor. Disco: caché de fuentes de Buildroot 4–8 GB (se declara en §T7 y es lo más pesado del área), imágenes 30 MB–2 GB, artefactos según objetivo. Tokens: sólo en la redacción de recetas y en el debate de las cuatro afirmaciones, ≈ 30 000 por artefacto publicado. **Salto del debate:** arrancar una sesión desechable sin red ni carpeta compartida es R1 y no se debate; activar red o carpeta compartida es R2 y sí. **Caché:** imágenes por `sha256(receta + lock)`; artefactos por `sha256(imagen + motor + objetivo)`; el caché de fuentes de Buildroot se conserva entre proyectos porque es caro y es inmutable por hash.

### 16.8 Calidad y pruebas

| Caso | Criterio de éxito |
|---|---|
| Camino feliz | Receta `minimo-linux-analisis`: construye, empaqueta y arranca en ventana mostrando el indicador de sistema, 10/10 |
| **Reproducibilidad** | Dos construcciones en directorios distintos: **SHA-256 idéntico** en ≥ 9 de 10 recetas; la que falle debe identificar el fichero culpable |
| **Ejecutable único en máquina limpia** | Contenedor sin QEMU, sin Python y sin bibliotecas: el artefacto arranca hasta el indicador y sale con código 0, 10/10 en Linux y 10/10 en Windows |
| Tamaño | FreeDOS ≤ 60 MB, Linux mínimo ≤ 180 MB, Alpine gráfico ≤ 400 MB |
| **Aislamiento de red** | 20 sesiones con `network: none` y un huésped que intenta conectarse activamente: **0 paquetes salientes**, verificado con captura en el anfitrión; 20/20 `vm.escape_attempt` registrados |
| Aislamiento de disco | Huésped que intenta escribir en rutas del anfitrión: 0 escrituras fuera de las imágenes declaradas |
| Sin aceleración | Con la aceleración deshabilitada: arranca igualmente y la interfaz **avisa** de que será más lento, 10/10 |
| Entorno de época | 10 documentos que ninguna herramienta del Área 15 abre: ≥ 8 exportados o capturados con contenido reconocible |
| Instantáneas | 20 ciclos de instantánea, modificación y restauración: estado idéntico por hash, 20/20 |
| CTL-4 | Intento de empaquetar una imagen con un componente no redistribuible: rechazo 10/10 con la lista exacta |
| Consenso / desacuerdo | Sobre «arranca en máquina limpia»: con la prueba en verde, `survives` ≥ 85; con un fallo de arranque, `falsified` inmediato pese a que el artefacto funcione en la máquina del desarrollador |
| Interfaz | Crear un sistema portable requiere responder **como máximo 4 preguntas** en la conversación y produce el ejecutable sin que el usuario escriba una sola línea de configuración |

### 16.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta automática | Estado |
|---|---|---|---|---|
| Sin aceleración disponible | Comprobación al arrancar | Lentitud | Continuar en emulación pura y **avisar en lenguaje llano**; ofrecer la ruta WebAssembly si el sistema es ligero | Degradado, explicado |
| Construcción no reproducible | Doble construcción con hashes distintos | Artefacto no verificable | Localizar el fichero divergente, declarar `no_reproducible` y seguir, sin ocultarlo | Honesto |
| Artefacto que no arranca en máquina limpia | Prueba de humo en contenedor | Entrega inservible | **Bloquear la publicación**; el artefacto no se marca válido | Seguro |
| **Fallo parcial (el peor): arranca pero la aplicación de época falla en silencio** | Estabilidad de pantalla sin marcador esperado, o exportación vacía | Documento «abierto» sin contenido | Marcar el intento como fallo y descender a captura de pantalla; si también falla, devolver al Área 15 como `no_legible` con el motivo | Consistente |
| Antivirus bloquea el ejecutable | Código de salida y ausencia de ventana | Artefacto inutilizable en ese equipo | Documentar el patrón, ofrecer la variante sin extracción a disco, y publicar el hash para que el usuario lo excluya | Explicado |
| Huésped consume toda la memoria | Límite del motor | Anfitrión lento | Límite duro por sesión desde la receta; el motor no puede superarlo | Contenido |
| Sin red | — | Ninguno; de hecho es el estado por defecto | Nada | Operativo |

### 16.10 Riesgos y mitigaciones

Un sistema huésped hostil que escapa al anfitrión (baja / **crítico** → red y carpeta compartida desactivadas por defecto, entrada por imagen de sólo lectura, detección de fuga, instantánea previa, y el motor bajo cgroup/Job Object). Distribuir sin querer software propietario (media / alto → CTL-4 en el empaquetador con manifiesto de licencias). Falsa portabilidad (alta / alto → la prueba de humo en máquina limpia es obligatoria y bloquea la publicación). Caché de construcción que ocupa el disco (alta / medio → declarado en §T7, con purga por antigüedad y aviso). Expectativa de ejecutar sistemas propietarios modernos (media / medio → la interfaz lo dice desde la tarjeta de inicio: se pueden construir y ejecutar los sistemas libres listados, y usar el soporte propio del usuario sin poder empaquetarlo). Aceleración no disponible en portátiles con otras herramientas de virtualización activas (alta / bajo → detección y aviso, con la ruta WebAssembly como alternativa inmediata).

### 16.11 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA:** QEMU 9.x, Buildroot 2024.x, Alpine 3.20, FreeDOS 1.3, ReactOS 0.4.x, Haiku R1 beta, KolibriOS, NetBSD 10, FreeBSD 14, DOSBox-X, emulador x86 en WebAssembly, Rust 1.79+ para el lanzador, `xorriso` para las imágenes efímeras, `qemu-img` para las instantáneas. Todo libre y redistribuible. **🟡 REQUIERE-PRERREQUISITO:** activar la plataforma de hipervisor en Windows o pertenecer al grupo `kvm` en Linux para tener aceleración (sin ellas todo funciona, más despacio); y, para abrir formatos propietarios en entorno de época, la aplicación original que el usuario posea. **🔴** ninguno: no hace falta comprar nada; 4–8 GB de disco para el caché de construcción es el único coste real.

### 16.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (arrancar una imagen existente en ventana, sin red) → v1 (constructor Buildroot reproducible, empaquetado en ejecutable único, instantáneas) → completo (rutas WebAssembly y DOSBox-X, perfiles de época conectados al Área 15, detección de fuga, CTL-4).

- **P16.a Ejecución en ventana.** P16.a.1 QEMU embebido — **PV-16.a.1**: sesión arrancada y visible en el panel, teclado y ratón capturados y liberados, 20/20. P16.a.2 aislamiento por defecto — **PV-16.a.2**: 0 paquetes salientes y 0 escrituras fuera de las imágenes, en 20 sesiones con huésped hostil.
- **P16.b Construcción.** P16.b.1 receta y `.lock` — **PV-16.b.1**: construcción sin red a partir del caché, 10/10. P16.b.2 reproducibilidad — **PV-16.b.2**: hashes idénticos en ≥ 9 de 10 recetas, con diagnóstico del fichero culpable en la restante.
- **P16.c Ejecutable único.** P16.c.1 lanzador con recursos embebidos — **PV-16.c.1**: un solo fichero, sin dependencias dinámicas (verificado con el inspector de enlaces). P16.c.2 máquina limpia — **PV-16.c.2**: arranca y sale con código 0 en contenedor vacío, 10/10 por plataforma. P16.c.3 tamaños — **PV-16.c.3**: los tres objetivos cumplidos o construcción fallida con el paquete responsable señalado.
- **P16.d Época.** P16.d.1 perfiles — **PV-16.d.1**: los seis perfiles arrancan y su marcador de estabilidad se detecta. P16.d.2 apertura automática — **PV-16.d.2**: ≥ 8 de 10 documentos exportados o capturados con contenido reconocible.
- **P16.e Legalidad y simplicidad.** P16.e.1 CTL-4 — **PV-16.e.1**: 10/10 rechazos con lista exacta de componentes. P16.e.2 asistente conversacional — **PV-16.e.2**: 5 usuarios sin conocimientos de programación producen un ejecutable respondiendo ≤ 4 preguntas en el hilo, sin ayuda externa.

Métricas de salida: reproducibilidad ≥ 90 % de las recetas, 100 % de artefactos publicados con prueba de humo en máquina limpia superada, 0 fugas de red en sesiones aisladas, y el asistente conversacional validado con usuarios reales.

---

## ÁREA 17 — Centro de Configuración y Calibración

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA.**

### 17.1 Propósito y alcance

Reúne en un único lugar **todos los parámetros del sistema**, con su valor actual, su valor por defecto, su rango válido, el efecto que tiene cambiarlo y la puerta de verificación que lo respalda; y añade lo que ninguna pantalla de ajustes suele tener: **calibradores**, es decir, procedimientos que **miden** en la máquina y en el entorno del usuario para proponer el valor correcto en vez de dejarle adivinar. Un sistema con 400 parámetros y sin calibración es un sistema mal configurado por definición.

Queda fuera: la lógica que consume cada parámetro (vive en su área) y la política de capacidades en sí (§10.6, que este centro presenta y edita pero no redefine).

**Consume:** todas las áreas (cada una declara su esquema de configuración). **Alimenta:** todas las áreas, el acta (los parámetros efectivos de cada deliberación se registran) y la procedencia (un artefacto producido con otra configuración no es comparable).

### 17.2 Arquitectura

*Decisión:* la configuración es **un árbol de esquemas declarados por cada módulo**, fusionado en cuatro capas con precedencia explícita —valores de fábrica → perfil de máquina detectado → configuración global del usuario → configuración del proyecto → anulaciones del turno— y **validado con el mismo `pydantic` que valida los contratos**, de modo que la pantalla de ajustes se **genera** desde los esquemas en lugar de escribirse a mano, porque una pantalla escrita a mano siempre acaba desincronizada del código que lee el valor.
*Descartado:* un fichero de configuración monolítico editado a mano — imposible de validar por partes, imposible de explicar y garantía de que nadie toque nada por miedo.

```
   módulo declara config_schema.py  ──────────────┐
   (tipo · rango · defecto · efecto · PV asociada)│
                                                  ▼
 ┌───────────────────────────────────────────────────────────────────┐
 │ FUSIÓN POR CAPAS (precedencia de menor a mayor)                    │
 │  1 fábrica → 2 perfil de máquina → 3 usuario → 4 proyecto → 5 turno│
 │  ⚠ toda anulación muestra de qué capa viene y qué valor tapa       │
 └──────────┬────────────────────────────────────────────────────────┘
            ▼ configuración efectiva (validada, hasheada)
 ┌───────────────────────────────────────────────────────────────────┐
 │ PANTALLA GENERADA        búsqueda · diff contra defecto ·          │
 │ formulario ↔ YAML sincronizados · revertir por campo               │
 ├───────────────────────────────────────────────────────────────────┤
 │ CALIBRADORES             miden en esta máquina y proponen valor    │
 ├───────────────────────────────────────────────────────────────────┤
 │ SIMULACIÓN DE EFECTO     "esto hará que…" antes de guardar         │
 └──────────┬────────────────────────────────────────────────────────┘
            ▼ config_hash → acta · model_run · artefacto · procedencia
```

### 17.3 Contratos e interfaces

```python
def schema_tree() -> ConfigTree: ...                       # generado desde los módulos
def effective(scope: Scope) -> ConfigView: ...             # con origen por campo
def set_value(path: str, value: Any, *, scope: Scope, reason: str | None) -> SetResult: ...
def revert(path: str, *, scope: Scope) -> None: ...
def diff_vs_default(scope: Scope) -> list[ConfigDiff]: ...
def simulate(path: str, value: Any) -> EffectPreview: ...  # qué cambia y qué PV lo cubre
def run_calibrator(name: str, **kw) -> CalibrationReport: ...
def apply_calibration(report: CalibrationReport, *, accept: list[str]) -> None: ...
def export_config(scope: Scope) -> Path: ...
def import_config(path: Path, *, dry_run: bool = True) -> ImportReport: ...
def preset_apply(name: str) -> None: ...                   # perfiles completos
def config_hash(scope: Scope) -> str: ...
```

Cada campo declarado por un módulo tiene esta forma, y sin ella no aparece en la pantalla:

```python
ConfigField(
  path="debate.rounds.min", type=int, default=3, minimum=3, maximum=12,
  label="Rondas mínimas de deliberación",
  effect="Ninguna deliberación terminará antes de este número de rondas, aunque haya acuerdo.",
  consequence_if_lower="No se puede bajar de 3: una sola pasada no es deliberación.",
  cost_hint="Cada ronda adicional cuesta ~23 000 tokens y ~50 s en el perfil de esta máquina.",
  gate="PV-3.b.4", restart_required=False, scope_allowed=["global","project","turn"])
```

Eventos: `config.changed{path, from, to, scope, actor}`, `config.reverted`, `calibration.started`, `calibration.finished{name, proposals}`, `config.imported{count, rejected}`. Tablas: `config_value`, `config_history`, `calibration_run` (DDL en §T15).

### 17.4 Implementación: el árbol completo de lo que se puede calibrar

Doce grupos, con los parámetros de mayor impacto de cada uno. Todos con valor por defecto, rango y efecto declarado.

| Grupo | Parámetros principales |
|---|---|
| **Las tres inteligencias** | Modelo, cuantización y proveedor por nodo · temperatura, `top_p`, semilla · contexto máximo · gramática · **regla de diversidad** (activa/degradada y su umbral de divergencia léxica) · orden de carga y política de conmutación en máquinas con poca memoria |
| **Deliberación** | `rounds.min` (≥ 3) y `rounds.max` por área · umbral de aprobación (70) · franja de enmienda (60–69) · **pesos de los siete criterios de la rúbrica**, que deben sumar 100 y la pantalla lo impone · umbrales de convergencia, meseta y oscilación · presupuesto de tokens, tiempo y rondas · exigencia de `no_new_findings` justificado |
| **Guardas anti-degeneración** | Umbral de sicofancia · umbrales de duplicado (refutación 0,88 · análisis 0,90 · propuesta 0,95) · periodicidad del reinicio ciego · sensibilidad de la deriva de tema |
| **Ejecución y seguridad** | Política por radio (R0/R1 automáticos, R2 con juez y copia, **R3 siempre humano y no configurable**) · presupuesto del bucle · disparadores del rompedor de bucles · lista negra de rutas (ampliable, nunca reducible por debajo del mínimo) · cuarentena en vez de borrado (no desactivable) |
| **Seguridad física (Área 9)** | Temperaturas máximas · corriente máxima · tiempo máximo de calentador sin progreso · límites de recorrido · **tope duro que el agente no puede subir**, sólo el usuario y con confirmación |
| **Proveedores y ruta (Área 14)** | Alta y baja de proveedores · estrategia por rol y por tarea · márgenes de cuota · umbrales del cortacircuitos · **clases de privacidad** y qué contenido nunca sale del equipo (los cuatro por defecto no se pueden desmarcar sin confirmación explícita y registro) |
| **Ingesta (Área 15)** | Niveles de la cascada activos · tiempos máximos por nivel · profundidad de contenedores · umbral de bomba de descompresión · confianza mínima de codificación antes de preguntar · política del nivel 6 (entorno de época) |
| **Memoria de código (Área 13)** | Raíz permitida · trabajadores · presupuesto de memoria · frecuencia de reindexación · cobertura mínima para admitir afirmaciones de ausencia · caducidad de los deltas de conocimiento |
| **Documentos (Áreas 1 y 2)** | Umbrales de los nueve detectores forenses · pesos de fusión del índice híbrido · `k` de recuperación · tolerancia de recálculo numérico · fecha de referencia por defecto |
| **Fabricación (Área 9)** | Perfiles de máquina · dialecto y ventana de comandos en vuelo · frecuencia de sondeo · perfiles de rebanado · tolerancias del plan de verificación · factores de esfuerzo del libro mayor (Área 5) |
| **Sistemas portables (Área 16)** | Motor preferido · memoria y disco por receta · red y carpeta compartida (ambas desactivadas por defecto) · tamaño máximo del ejecutable |
| **Interfaz** | Tema · densidad · tamaño de fuente · qué secciones plegadas por defecto en las tarjetas · nivel de detalle del hilo · atajos · notificaciones · idioma |

**Presentación.** Pantalla generada desde los esquemas con **búsqueda incremental** que encuentra por nombre, por ruta y por efecto («escribe *temperatura* y salen las tres temperaturas del sistema, la del modelo y las dos del extrusor, cada una con su grupo»). Cada campo muestra: valor efectivo, **de qué capa viene**, valor por defecto, rango, efecto en una frase, coste estimado del cambio y la **puerta de verificación** que lo respalda. Un filtro **«sólo lo que he cambiado»** muestra el `diff` completo contra los valores de fábrica, que es la primera pregunta cuando algo se comporta raro. Edición en **formulario y en YAML crudo, sincronizados en vivo**; el YAML es la fuente para exportar, compartir y versionar.

**Simulación de efecto antes de guardar.** Al modificar un valor, un panel lateral dice qué implica en lenguaje llano y con números de esta máquina: *«Subir las rondas mínimas de 3 a 5 hará que cada deliberación tarde unos 100 segundos más y consuma unos 46 000 tokens más. Afecta a todas las áreas. Puerta que lo cubre: PV-3.b.4.»* Los cambios que exigen reiniciar un componente lo dicen y ofrecen hacerlo.

**Preajustes completos**, aplicables de una vez y siempre reversibles: **Equilibrado** (valores de fábrica), **Máquina modesta** (un solo modelo residente con diversidad forzada, rondas mínimas 3, contexto reducido, VLM a menor resolución), **Máxima calidad** (tres familias distintas, rondas mínimas 5, exhaustiva 9, todas las verificaciones activas), **Sin conexión** (proveedores remotos desactivados, todo local, red denegada por política), **Trabajo con hardware** (prioridad de seguridad física, sondeo alto, R2 con confirmación adicional) y **Análisis documental** (detectores forenses sensibles, corpus obligatorio, recálculo numérico estricto).

**Calibradores** — la parte que distingue este centro de una pantalla de ajustes:

| Calibrador | Qué mide | Qué propone | Duración |
|---|---|---|---|
| **Perfil de máquina** | Núcleos, memoria libre, memoria de vídeo, disco, presencia de aceleración de virtualización, velocidad de disco | Perfil (A/B/C), modelos y cuantizaciones por nodo, semáforos de concurrencia, presupuestos de memoria | 2–4 min |
| **Velocidad de los modelos** | Tokens por segundo de cada modelo cargado, tiempo de carga, coste de conmutación | Asignación modelo→nodo, si conviene conmutar o mantener residente, presupuesto de tiempo por ronda | 5–8 min |
| **Calidad de la deliberación** | Ejecuta 20 casos con solución conocida a 3, 5 y 7 rondas **más una cuarta condición con crítica simulada** (§A17-2) | **Número de rondas a partir del cual deja de mejorar**, y —antes que eso— **si el juez distingue una crítica real de una falsa**; si no la distingue, lo dice y bloquea el resto del análisis | 40–80 min |
| **Umbrales forenses** | Genera el corpus sintético del §A1-5 y traza las curvas | Umbrales de los nueve detectores para el objetivo de falsos positivos elegido | 20–40 min |
| **Cobertura de ingesta** | Pasa el corpus de época y el del propio usuario | Qué niveles activar, tiempos máximos por nivel, y qué herramientas faltan con su comando de instalación | 10–30 min |
| **Impresora 3D** | Secuencia guiada: identidad por `M115`, prueba de temperatura, cubo de calibración, medición con calibre | Pasos por milímetro, holguras, factor de escala, temperaturas, tolerancias del plan de verificación | 30–90 min (incluye impresión) |
| **Instrumentos** | Lectura de referencia conocida frente a la medida | Incertidumbre real del instrumento, que es lo que hace admisible una medición como evidencia de rango 1 | 5–15 min |
| **Factores de esfuerzo** | Compara estimaciones del libro mayor con el esfuerzo real registrado | Recalibra los factores base (0,2 / 1 / 4 / 12) por regresión — cierra la debilidad D3 | Continuo |

Cada calibrador produce un informe con **valor actual, valor propuesto, evidencia y ganancia esperada**, y el usuario acepta o rechaza **campo por campo**; nada se aplica en bloque sin verlo. Todo lo aplicado queda en `config_history` con su justificación.

**Configuración por turno.** Desde la barra de instrucción se pueden anular, sólo para ese turno, los parámetros más frecuentes: mínimo de rondas, modelos por nodo, presupuesto y si se permite salir a internet. La anulación se muestra como un distintivo en el turno y queda en el acta, de modo que dos turnos con resultados distintos siempre son comparables.

**Paridad Windows/Linux:** rutas de los ficheros de configuración por `PathsHAL`; el resto es idéntico. Ficheros: `config/factory.yaml` (fábrica, sólo lectura), `config/machine.yaml` (calibrado), `~/.../MagiSystem/config/user.yaml`, `projects/<slug>/config.yaml`, y `config/presets/*.yaml`.

### 17.5 Algoritmos

**A17-1 — Fusión por capas con trazabilidad de origen.**
```
1. cargar fábrica (validada contra los esquemas de todos los módulos)
2. aplicar capa perfil de máquina; luego usuario; luego proyecto; luego anulaciones del turno
3. por cada campo, guardar (valor, capa_de_origen, capa_que_tapa) para poder explicarlo en la pantalla
4. validar el resultado COMPLETO, no campo a campo: hay restricciones cruzadas
     4.1 los pesos de la rúbrica deben sumar 100
     4.2 rounds.min ≤ rounds.max y rounds.min ≥ 3
     4.3 la suma de memoria reservada por los modelos activos no puede superar el 85 % del total
     4.4 si la regla de diversidad está activa, debe haber al menos dos familias disponibles
     4.5 los topes de seguridad física no pueden superar los de fábrica
5. si la validación cruzada falla → NO se aplica nada, se explica qué restricción se viola y qué campos
     intervienen, y se ofrece el ajuste mínimo que la satisface
6. calcular config_hash sobre la configuración efectiva; ese hash va al acta y a cada artefacto
```

**A17-2 — Calibrador de calidad de la deliberación, con condición de control (el más valioso).**
```
 1. tomar 20 casos del banco con solución conocida y coste de evaluación bajo
 2. CUATRO condiciones, no tres:
      A · r=3 rondas, crítica real
      B · r=5 rondas, crítica real
      C · r=7 rondas, crítica real
      D · r=5 rondas, CRÍTICA SIMULADA — las refutaciones de BALTHASAR • 2 se sustituyen por
          refutaciones perturbadas o tomadas de otro tema, manteniendo forma y longitud
 3. medir en las cuatro: aciertos, tasa de alucinación de citas, puntuación final, tokens, tiempo
 4. LECTURA DE LOS RESULTADOS, en este orden y sin saltarse el primero:
    4.1 si la condición D obtiene una puntuación comparable a la B (diferencia < 15 puntos), el juez
        está premiando la FORMA de la deliberación y no su contenido:
          → la mitad de juicio de la rúbrica queda invalidada para esta configuración de modelos
          → se aumenta el peso mecánico o se cambia el modelo de CASPER • 3, y se REPITE el calibrador
          → este resultado se publica; es exactamente lo que la debilidad D1 predice y hay que saberlo
    4.2 sólo si D queda claramente por debajo, se comparan A, B y C entre sí
    4.3 ganancia marginal por ronda := Δaciertos / Δtokens
 5. proponer rounds.min := el menor r cuya ganancia marginal respecto de r−2 sea ≥ 5 puntos
      porcentuales de acierto; si ninguno lo alcanza, proponer 3 y DECLARAR que las rondas
      adicionales no aportan en esta configuración — resultado legítimo y valioso
 6. proponer rounds.max := el menor r a partir del cual la ganancia es < 1 punto
 7. guardar las cuatro curvas y el informe; es la evidencia con la que se juzga la afirmación D1
```

**A17-3 — Importación segura de configuración compartida.**
```
1. leer el YAML; validar contra los esquemas; rechazar campos desconocidos (no se ignoran en silencio)
2. simular la fusión y calcular el diff contra la configuración actual
3. RECHAZAR sin excepción: cambios que suban los topes de seguridad física, que desactiven la
     cuarentena, que reduzcan la lista negra por debajo del mínimo, que pongan R3 en automático o
     que desmarquen una clase de privacidad
4. mostrar el diff completo agrupado por grupo, con el efecto de cada cambio
5. aplicar sólo lo aceptado; registrar en config_history con la procedencia del fichero importado
```

### 17.6 Integración con el debate popperiano

Afirmaciones: «esta configuración es coherente», «el valor propuesto por el calibrador mejora el resultado», «ningún parámetro efectivo contradice un tope de seguridad». Evidencia admisible: los informes de calibración con sus medidas, el `config_hash` de las ejecuciones comparadas y el resultado del banco. Refutación más potente: **la comparación A/B** — BALTHASAR • 2 exige ejecutar el mismo banco con la configuración anterior y la nueva; si la nueva no mejora, la propuesta del calibrador cae. Invocación: al aplicar cualquier calibración y al importar configuración ajena.

### 17.7 Costos, latencia y recursos

La fusión y validación completas tardan ≤ 25 ms; la pantalla se genera desde los esquemas en ≤ 120 ms. Los calibradores tienen coste declarado en la tabla de §17.4 y **todos son cancelables y reanudables**. Almacenamiento: `config_history` crece ≈ 200 bytes por cambio. Tokens: sólo el calibrador de calidad de deliberación los consume (≈ 1,4 millones para las tres pasadas de 20 casos), y lo dice antes de empezar. **Salto del debate:** cambiar un parámetro es R1 y no se debate; aplicar una calibración completa sí. **Caché:** el árbol de esquemas se construye una vez por arranque.

### 17.8 Calidad y pruebas

| Caso | Criterio de éxito |
|---|---|
| Camino feliz | Cambiar 20 parámetros de grupos distintos, reiniciar y comprobar que persisten con su capa correcta, 20/20 |
| Generación desde esquemas | Todo campo declarado por un módulo aparece en la pantalla; **0 campos huérfanos y 0 campos en pantalla sin esquema** (prueba automática que recorre ambos lados) |
| Validación cruzada | 30 configuraciones inválidas sembradas (pesos que no suman 100, `rounds.min` = 1, memoria excedida): 30/30 rechazadas con la restricción y los campos nombrados |
| **Mínimo de rondas** | Intentar fijar `debate.rounds.min = 1` por pantalla, por YAML, por importación y por anulación de turno: **rechazado en las cuatro vías**, 10/10 cada una |
| Topes de seguridad | Intentar subir la temperatura máxima por encima del tope de fábrica: rechazado; hacerlo dentro del rango: exige confirmación y queda registrado |
| Trazabilidad de origen | Con las cinco capas activas, cada campo indica correctamente de dónde viene, 100 % |
| Simulación de efecto | 20 cambios: la previsión de coste está dentro del ±30 % de lo medido después |
| Calibrador de máquina | En tres máquinas distintas propone perfiles distintos y correctos, y el sistema arranca sin fallos de memoria tras aplicarlos |
| Calibrador de deliberación | Produce las tres curvas y una recomendación justificada; si no hay ganancia, **lo dice** en vez de recomendar más rondas |
| Importación hostil | Fichero que sube topes de seguridad, desactiva la cuarentena y pone R3 en automático: los tres cambios rechazados, el resto ofrecido, 10/10 |
| Reversión | Revertir campo a campo y por grupo devuelve exactamente el estado anterior por hash, 20/20 |
| `config_hash` en procedencia | 100 % de artefactos y actas llevan el hash de la configuración con que se produjeron |
| Consenso / desacuerdo | Sobre una calibración: con mejora medida, `survives` ≥ 80; sin mejora, `falsified` aunque el calibrador la proponga |

### 17.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta | Estado |
|---|---|---|---|---|
| Configuración de usuario corrupta | Validación al arrancar | No arranca | Arrancar con fábrica + perfil de máquina, avisar y conservar el fichero roto para inspección | Operativo |
| Restricción cruzada violada tras una actualización | Validación completa | Estado incoherente | Aplicar el ajuste mínimo automático y **decir cuál**; nunca arrancar en estado inválido | Consistente |
| Calibrador interrumpido | Punto de control | Informe parcial | Reanudar donde quedó; nunca aplicar una calibración incompleta | Seguro |
| **Fallo parcial (el peor): un cambio que parece inocuo degrada la calidad sin avisar** | El banco de prompts (§7.8) se ejecuta tras aplicar calibraciones | Peor calidad invisible | Comparación automática antes/después y aviso con el `config_hash` culpable | Detectable |
| Preajuste incompatible con la máquina | Validación cruzada de memoria | Sistema inarrancable | Rechazo con la explicación y el preajuste alternativo sugerido | Seguro |
| Sin red | — | Ninguno | Todo local | Operativo |

### 17.10 Riesgos y mitigaciones

Un usuario que se dispara en el pie (alta / alto → topes de fábrica no superables, simulación de efecto, diff siempre visible, reversión por campo). Configuración compartida maliciosa (media / alto → A17-3 con rechazos no negociables). Deriva silenciosa de calidad por acumulación de ajustes (alta / alto → `config_hash` en toda procedencia y banco de prompts tras calibrar). Pantalla que crece hasta ser inmanejable (alta / medio → generada desde esquemas, con búsqueda por efecto y filtro de «sólo lo cambiado»). Calibradores que proponen con poca evidencia (media / medio → cada propuesta lleva su medida y pasa por deliberación). Parámetros huérfanos tras una refactorización (media / bajo → prueba automática de correspondencia biunívoca esquema ↔ pantalla ↔ lector).

### 17.11 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA:** `pydantic` 2.8, `ruamel.yaml` 0.18 (conserva comentarios al editar), y los bancos y corpus que las demás áreas ya definen. Sin hardware ni cuentas. El calibrador de impresora es **🟡** (necesita la impresora y un calibre) y el de instrumentos **🟡** (necesita el instrumento y una referencia conocida).

### 17.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (esquemas, fusión por capas, pantalla generada, persistencia) → v1 (simulación de efecto, diff, preajustes, importación segura) → completo (los ocho calibradores, `config_hash` en toda la procedencia, anulaciones por turno).

- **P17.a Esquemas y fusión.** P17.a.1 declaración por módulo — **PV-17.a.1**: 0 campos huérfanos en ambos sentidos. P17.a.2 fusión por capas — **PV-17.a.2**: origen correcto por campo con las cinco capas, 100 %. P17.a.3 validación cruzada — **PV-17.a.3**: 30/30 configuraciones inválidas rechazadas con explicación.
- **P17.b Pantalla.** P17.b.1 generación y búsqueda — **PV-17.b.1**: todo campo alcanzable en ≤ 3 pulsaciones desde la búsqueda. P17.b.2 formulario ↔ YAML — **PV-17.b.2**: 100 ediciones cruzadas sin desincronización. P17.b.3 simulación — **PV-17.b.3**: previsión dentro del ±30 %.
- **P17.c Seguridad de la configuración.** P17.c.1 mínimo de rondas — **PV-17.c.1**: `rounds.min = 1` rechazado por las cuatro vías. P17.c.2 topes físicos y R3 — **PV-17.c.2**: no superables ni automatizables, 10/10. P17.c.3 importación — **PV-17.c.3**: los tres cambios prohibidos rechazados.
- **P17.d Calibradores.** P17.d.1 máquina y modelos — **PV-17.d.1**: perfiles correctos en tres máquinas. P17.d.2 calidad de deliberación — **PV-17.d.2**: tres curvas y recomendación justificada, incluido el caso «no aporta». P17.d.3 forense, ingesta e instrumentos — **PV-17.d.3**: cada uno produce propuestas con evidencia y ganancia declarada.
- **P17.e Procedencia.** P17.e.1 `config_hash` — **PV-17.e.1**: 100 % de actas y artefactos con el hash de su configuración.

Métricas de salida: 0 campos huérfanos, 0 configuraciones inválidas aplicadas, `rounds.min` nunca por debajo de 3, y los ocho calibradores produciendo propuestas con evidencia medida.

---

## ÁREA 18 — MAGI-KEEP: memoria íntegra y transferencia entre inteligencias

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA.**

### 18.1 Propósito y alcance

Garantiza que **cuando un nodo cambia de modelo, no se pierde absolutamente nada de lo dicho hasta ese momento, y nada se resume**. Es la corrección de un error de diseño de las revisiones anteriores: el §7.5 preveía un «resumen jerárquico del historial» que comprimía las rondas antiguas a una línea. Un resumen es una pérdida con buena prensa: elimina el matiz que refutaba una afirmación, borra el supuesto que alguien declaró en la ronda 2 y convierte la memoria en una versión de los hechos escrita por un modelo. En un sistema cuyo valor entero descansa en que **toda cita exista literalmente**, alimentar la memoria con paráfrasis es contradecirse.

*Decisión:* se **prohíbe el resumen en todo el camino de memoria**. Lo que no cabe en el contexto no se comprime: **se direcciona**. El registro es íntegro, literal e inmutable; el contexto de cada turno se compone de fragmentos **literales** del registro más un índice completo de todo lo demás, y cualquier fragmento no cargado es recuperable en el acto — porque una memoria que se resume deja de ser memoria y pasa a ser una opinión sobre el pasado.
*Descartado:* el resumen jerárquico del §7.5 y el «contexto comprimido y neutralizado» entre rondas del §3.4 — ambos quedan **derogados por esta área** y sustituidos por lo que sigue. Se mantiene una única forma de resumen: el `plain_summary` de 140 caracteres que cada nodo emite **para el humano**, que nunca se reinyecta como memoria y va marcado como derivado.

Queda fuera: la memoria de código (Área 13, que es estructura, no diálogo) y la caché de respuestas (Área 6, que es aceleración, no memoria).

**Consume:** Área 0 (CAS, hash, procedencia), Área 17 (presupuestos). **Alimenta:** Área 3 (deliberación), Área 6 (cambio de proveedor), Área 7 (composición de prompts), Área 10 (hilos), Área 14 (conmutación de modelo).

### 18.2 Arquitectura

```
  cada emisión: turno de usuario · intervención de un nodo · resultado de herramienta
        │ verbatim, sin tocar
        ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ REGISTRO ÍNTEGRO (RI)  append-only · encadenado por hash · en el CAS    │
 │  item = {id, tipo, autor, ronda, texto LITERAL, hash, prev_hash}        │
 │  ⚠ inmutable: no se edita, no se compacta, no se poda jamás             │
 └───────┬────────────────────────────────────────────────────────────────┘
         │ indexación sin reescritura
         ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ ESTADO ESTRUCTURADO ACUMULADO (EEA)                                     │
 │  TODAS las afirmaciones · TODAS las refutaciones · réplicas · veredictos│
 │  restricciones · decisiones · deltas de conocimiento — con su estado    │
 │  y su REFERENCIA al item del RI. Reorganiza; NO reescribe.              │
 └───────┬────────────────────────────────────────────────────────────────┘
         ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ COMPOSITOR DE CONTEXTO                                                  │
 │  (a) índice COMPLETO del EEA (todo elemento aparece)                    │
 │  (b) cuerpo LITERAL de lo pertinente al turno                           │
 │  (c) herramienta memory.fetch(ids) → literal, en mitad del turno        │
 │  ⚠ punto de decisión: ¿no cabe? → NO se resume: se direcciona,          │
 │     se trocea el trabajo, o se escala a un modelo de más contexto       │
 └───────┬────────────────────────────────────────────────────────────────┘
         ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ TRASPASO ENTRE MODELOS (handover)                                       │
 │  paquete completo → PRUEBA DE RECEPCIÓN → sólo entonces continúa        │
 │  ⚠ si el modelo entrante no supera la prueba, NO toma el relevo         │
 └────────────────────────────────────────────────────────────────────────┘
```

**La distinción que sostiene toda el área: reorganizar no es resumir.** El EEA contiene el texto **literal** de cada elemento, agrupado por tipo y estado. Un índice que dice «refutación r2.1 · mantenida · *«La función tick_sync llama a allegrex_cycles desde dentro de la interfaz…»*» no es un resumen de r2.1: es r2.1, con su primera línea literal y su identificador para traer el resto. La diferencia con un resumen es comprobable mecánicamente, y de hecho **se comprueba**: todo fragmento que entra en un prompt como memoria debe existir **literalmente** en el registro, verificado con el mismo validador de subcadena normalizada del §A2-3. Una paráfrasis no pasa ese filtro. Esa es la garantía técnica de que aquí no se resume nada, y no una promesa de redacción.

### 18.3 Contratos e interfaces

```python
def append(item: MemoryItem) -> ItemId: ...                  # verbatim, inmutable, encadenado
def state(deliberation_id: str) -> AccumulatedState: ...      # EEA completo, con referencias
def compose_context(turn: TurnSpec, budget: int) -> ComposedContext: ...
def fetch(ids: list[ItemId]) -> list[MemoryItem]: ...         # literal; expuesto al modelo como herramienta
def verify_chain(record_id: str) -> ChainReport: ...
def handover(node: Node, from_id: ModelIdentity, to_id: ModelIdentity,
             *, reason: str) -> HandoverResult: ...
def receipt_test(node: Node, to_id: ModelIdentity, k: int = 5) -> ReceiptReport: ...
def context_manifest(turn_id: str) -> Manifest: ...           # qué items exactos vio el modelo
```

Elemento del registro y paquete de traspaso:

```json
{ "item_id":"mi_000412", "record_id":"ri_dlb_01J8X", "seq":412,
  "kind":"user_turn|proposal|claim|refutation|rebuttal|arbitration|verdict|tool_result|constraint|knowledge_delta|handover_note",
  "author":"MELCHIOR|BALTHASAR|CASPER|USER|SYSTEM", "round_index":3, "proposal_version":3,
  "text":"…texto LITERAL, sin recortar, sin normalizar salvo NFKC…",
  "tokens":842, "model_identity_id":"mid_…", "created_at":"2026-08-02T11:14:02-05:00",
  "sha256":"…", "prev_hash":"…" }
```

```json
{ "handover_id":"hv_01J9…", "deliberation_id":"dlb_01J8X", "node":"BALTHASAR", "at_round":4,
  "from": {"display":"DeepSeek-R1-Distill-Qwen 7B · Q4_K_M · local","identity_id":"mid_a"},
  "to":   {"display":"Mistral 7B Instruct v0.3 · Q4_K_M · local","identity_id":"mid_b"},
  "reason":"diversidad de familia recuperada",
  "package": {"record_id":"ri_dlb_01J8X","items_total":412,"chain_head_sha256":"…",
              "state_ref":"cas://sha256:…","open_items":["r3.1","r3.2","r1.4"],
              "constraints":["presupuesto 20 EUR","sin internet"],
              "context_manifest_ref":"cas://sha256:…"},
  "receipt_test": {"questions":5,"passed":5,"verbatim_matches":5,"duration_ms":9120},
  "status":"verified", "loss_check":{"items_before":412,"items_after":412,"diff":0} }
```

Eventos: `memory.appended{item_id, kind, tokens}`, `memory.fetch{turn_id, ids, tokens}`, `handover.started`, `handover.verified`, `handover.failed{reason}` (**crítico**), `memory.chain_broken` (**crítico**), `memory.overflow{strategy}`. Tablas: `memory_record`, `memory_item`, `memory_state`, `context_manifest`, `memory_fetch_log`, `handover`, `handover_check` (DDL en §T16).

### 18.4 Implementación

**Registro.** Un `memory_record` por deliberación y otro por hilo de conversación. Cada `append` escribe el texto literal en el CAS, la fila en SQLite con `prev_hash`, y calcula `sha256(prev_hash || canonical(item))`. **No existe operación de borrado ni de edición**; el disparador de SQLite lo impide igual que en `audit_log`. Coste: un registro de deliberación de 7 rondas ronda 400–900 elementos y 120–260 kB de texto; comprimido con zstd, 25–60 kB. **Guardarlo todo es barato; perderlo es lo caro.**

**Composición del contexto (el corazón).** Dado un presupuesto de `B` tokens para memoria, el compositor arma, en este orden y sin excepción:

| Bloque | Contenido | Fijado |
|---|---|---|
| 1 | **Restricciones vigentes**, literales, todas | **Sí** |
| 2 | **Índice completo del EEA**: *todo* elemento con `id`, tipo, estado y sus **primeros 160 caracteres literales** | **Sí** |
| 3 | **Cuerpo literal** de: los elementos abiertos (refutaciones mantenidas), la versión de propuesta anterior íntegra, y las instrucciones de CASPER • 3 dirigidas a este nodo | **Sí** |
| 4 | Cuerpo literal de los elementos citados en el turno anterior | No |
| 5 | Cuerpo literal del resto, por orden de pertinencia hasta agotar `B` | No |

**El bloque 2 es completo por construcción**: si hay 300 elementos, aparecen los 300. A 40 tokens por entrada son 12 000 tokens, que caben en cualquier ventana de 32 k. Los 160 caracteres son **literales, no un resumen**, y llevan la marca `…` que indica que hay más, con su identificador para pedirlo.

**Regla de lectura obligatoria (la que impide que el truncado del índice se convierta en pérdida).** Ningún nodo puede afirmar nada *sobre* un elemento del registro sin haberlo recuperado **íntegro** en ese mismo turno. El validador cruza cada referencia a un `item_id` en la salida con el `memory_fetch_log` del turno; una referencia sin recuperación previa **invalida el turno** y se repite con la instrucción exacta. Así, el índice sirve para saber **qué existe**, nunca para pronunciarse sobre su contenido.

**Cuando no cabe: tres salidas, ninguna es resumir.**
1. **Direccionar** — es la vía normal: el modelo pide con `memory.fetch` lo que necesite mientras razona; el coste es una llamada más, no una pérdida.
2. **Trocear el trabajo** — si el turno necesita de verdad más contexto del que hay, se parte en unidades reanudables (Área 6) con estado explícito entre ellas.
3. **Escalar de modelo** — se conmuta a uno de mayor ventana (§I.3, Área 14) mediante el traspaso del §18.5, y se declara en el acta.
Si ninguna es posible, el sistema **se detiene y lo dice**: `memory.overflow{strategy:"none"}` con escalada a humano. Detenerse es aceptable; inventar una versión resumida del pasado, no.

**Traspaso entre modelos.** Al cambiar el modelo de un nodo —por caída de proveedor, cuota, decisión del usuario o regla de diversidad— se ejecuta el procedimiento del §18.5. Nunca se hereda el estado del proveedor: la conversación que la CLI o la pasarela mantengan en su lado es **caché desechable**, y el registro es la verdad. Esto ya estaba en el §10.7 como «rehidratación»; aquí se endurece con una prueba de recepción que puede **impedir el relevo**.

**Prohibición mecánica del resumen.** `modules/memory/nosummary.py::assert_verbatim(fragment, record_id)` se ejecuta sobre **todo** fragmento que el compositor inserte como memoria: normalización NFKC, minúsculas, colapso de espacios, y búsqueda como subcadena en el registro (autómata de sufijos construido una vez por registro). Tolerancia: **0 caracteres**. Un fragmento que no aparezca literalmente aborta la composición del prompt con `SummaryDetected`, que es un fallo de programación, no una advertencia. Excepción única y declarada: el `plain_summary` para el humano, que va marcado `derived:true` y **nunca** entra en el bloque de memoria.

Tabla de paridad: el área es cómputo y almacenamiento puros; sólo difieren las rutas (`PathsHAL`) y el tamaño de página del autómata de sufijos, que se ajusta a la memoria disponible. Idéntica en ambos sistemas.

### 18.5 Algoritmos

**A18-1 — Traspaso con prueba de recepción (ningún relevo a ciegas).**
```
 1. congelar el registro: chain_head := hash del último elemento; items_before := recuento
 2. el modelo SALIENTE emite una NOTA DE TRASPASO: no un resumen, sino una enumeración de
      elementos abiertos por identificador y una declaración de su propio estado interno
      («qué estaba a punto de comprobar»); se APPENDEA al registro como un elemento más
 3. componer el paquete: record_id · chain_head · EEA completo · elementos abiertos ·
      restricciones · manifiesto del último contexto · identidad de ambos modelos
 4. PRUEBA DE RECEPCIÓN sobre el modelo ENTRANTE, k=5 preguntas generadas de forma determinista
      a partir del registro (no por un modelo), de estos cinco tipos:
      4.1 «cita literalmente el mecanismo de la refutación <id>»          → coincidencia exacta
      4.2 «¿cuántas versiones de propuesta hay y cuál puntuó más alto?»   → número exacto
      4.3 «enumera los identificadores de las refutaciones mantenidas»     → conjunto exacto
      4.4 «¿qué restricción impuso el usuario en el turno <n>?»            → coincidencia exacta
      4.5 «¿qué te ha pedido CASPER • 3 para esta ronda?»                  → coincidencia exacta
      el modelo PUEDE y DEBE usar memory.fetch para responder: se evalúa la continuidad de la
      memoria, no la de su ventana
 5. criterio: 5/5 correctas → status=verified y el relevo se produce
      4/5 → segundo intento con las preguntas falladas; 3/5 o menos → status=failed
 6. si failed: NO se cambia de modelo. Se intenta el siguiente candidato; si no hay ninguno, se
      mantiene el modelo original aunque esté degradado, y si tampoco es posible, la deliberación
      se PAUSA con escalada a humano. Nunca se continúa con un nodo que no ha recibido la memoria
 7. verificación de no pérdida: items_after == items_before ∧ chain_head sin cambios ∧
      verify_chain(record_id).ok → si falla, memory.chain_broken (crítico) y parada
 8. registrar handover con su informe; la interfaz muestra la franja de cambio (§I.8)
 9. caso límite: el modelo entrante tiene ventana MENOR que el saliente → se permite, porque el
      contexto se direcciona; pero se marca `window_downgrade` y se eleva el presupuesto de fetch
10. caso límite: cambio a mitad de una emisión → la emisión parcial se appendea igualmente al
      registro marcada `partial:true`; no se descarta, porque puede contener el razonamiento útil
```

**A18-1b — Recuperación proactiva (corrección de la debilidad D5, promovida al diseño).**

*Por qué existe.* La revisión anterior dejaba el modo direccionado esperando a que el modelo pidiera lo que necesitaba, y declaraba como debilidad que **nada garantiza que se dé cuenta de que algo antiguo era pertinente**. Dejarlo en «debilidad declarada» era insuficiente: el fallo no es del modelo, es del compositor, que sabía qué elementos estaban relacionados y no los puso delante. Se corrige aquí.

```
1. antes de componer, calcular la PERTINENCIA de cada elemento del registro respecto del turno,
     con tres señales deterministas y una semántica, todas baratas:
   1.1 GRAFO DE REFERENCIAS: elementos citados por los que ya están en el contexto (cierre transitivo
        de profundidad 2) — si la refutación r3.1 está en contexto y menciona a c1.4, c1.4 entra
   1.2 CADENA DE VIDA: todo elemento con estado ABIERTO entra siempre, sin excepción
   1.3 REAPARICIÓN: elementos recuperados en los dos turnos anteriores del mismo nodo
   1.4 SIMILITUD: coseno del texto del elemento con el enunciado del turno (bge-m3 o el reordenador)
2. precargar por orden de pertinencia hasta agotar el bloque 5 del §18.4
3. AVISO EXPLÍCITO DE LO NO CARGADO: al final del índice se inserta, literalmente,
     «Hay N elementos relacionados con este turno que no están cargados: <ids>. Recupéralos con
      memory.fetch antes de pronunciarte sobre ellos.»  ← el modelo no tiene que adivinar que existen
4. MEDIDA DE ACIERTO: se registra qué elementos precargó el compositor y cuáles pidió después el
     modelo. Precisión := precargados_usados / precargados;  cobertura := precargados_usados /
     (precargados_usados + pedidos_después). Ambas van al banco de §18.8
5. AJUSTE: si la cobertura cae por debajo de 0,7 durante 20 turnos, se amplía el bloque de precarga a
     costa del bloque 4; si la precisión cae por debajo de 0,4, se reduce (se está cargando ruido)
6. caso límite: el turno es una pregunta directa sobre una ronda antigua concreta → detección por
     mención explícita de número de ronda o de identificador, y precarga íntegra de esa ronda
```

**A18-2 — Composición de contexto sin pérdida.**
```
1. B := presupuesto de memoria del turno (config, Área 17)
2. montar bloques fijos 1–3; si ya exceden B:
     2.1 NO se recorta el índice (bloque 2) — se recorta el bloque 5 hasta cero
     2.2 si aun así excede, se activa modo direccionado puro: bloques 1 y 2 + herramienta fetch
     2.3 si el bloque 2 solo no cabe, se escala de modelo (A18-1); si no hay, se trocea el trabajo
     2.4 si nada de lo anterior es posible → memory.overflow{strategy:"none"} y parada con escalada
3. rellenar bloques 4 y 5 por pertinencia (coseno con el tema del turno + prioridad de elementos
     abiertos), siempre con texto LITERAL
4. assert_verbatim sobre cada fragmento insertado  → 0 tolerancia
5. escribir context_manifest{turn_id, item_ids[], hashes[], tokens} — dos ejecuciones con el mismo
     manifiesto ven exactamente lo mismo, que es lo que hace reproducible una deliberación
```

**A18-3 — Verificación de integridad y de no pérdida.**
```
1. verify_chain: recorrer el registro recalculando sha256(prev_hash || item); coste O(n), ~90 ms
     para 100 000 elementos
2. comparación antes/después de cada traspaso: conjuntos de item_id idénticos (no basta el recuento)
3. auditoría periódica: para cada deliberación cerrada, comprobar que todo elemento referenciado en
     el acta existe en el registro y que todo elemento del registro está clasificado en el EEA
4. cualquier discrepancia → memory.chain_broken, la deliberación se marca integrity=UNKNOWN y sus
     conclusiones dejan de ser citables hasta revisión humana
```

### 18.6 Integración con el debate popperiano

Afirmaciones: «no se ha perdido nada en este cambio de modelo», «todo lo que el nodo afirmó sobre el elemento X lo había leído íntegro», «este contexto es reproducible». Evidencia admisible: la cadena de hashes, el `context_manifest`, el `memory_fetch_log` y el informe de prueba de recepción. Refutación más potente: **la consulta que encuentra una referencia sin recuperación** o **un fragmento de prompt que no existe literalmente en el registro** — ambas automáticas y sin margen de discusión. Invocación: tras cada traspaso y al cerrar cada deliberación.

### 18.7 Costos, latencia y recursos

`append`: ≤ 0,8 ms. Construcción del autómata de sufijos: ≈ 120 ms por 250 kB, una vez por registro. `assert_verbatim`: ≤ 0,4 ms por fragmento. Composición de contexto: ≤ 25 ms. Prueba de recepción: 5 preguntas ≈ 9–20 s y ≈ 6 000 tokens — **es el coste directo de no perder memoria, y se paga una vez por cambio de modelo**. Recuperaciones en mitad del turno: 2–6 llamadas típicas, ≈ 300 ms y 1 500–6 000 tokens adicionales por turno en modo direccionado. Disco: 25–60 kB comprimidos por deliberación; un año de uso intenso no llega a 2 GB. **Salto del debate:** la mecánica de memoria es determinista y no se debate; sí se debaten las tres afirmaciones de §18.6. **Caché:** el autómata de sufijos y el índice del EEA por `record_id + chain_head`; se invalidan al añadir elementos, lo que es correcto porque el registro sólo crece.

### 18.8 Calidad y pruebas

| Caso | Criterio de éxito |
|---|---|
| Camino feliz | Deliberación de 7 rondas: registro con todos los elementos, cadena válida, 0 discrepancias |
| **Cero pérdida en cambio de modelo** | 50 traspasos forzados en momentos aleatorios: conjuntos de `item_id` **idénticos** antes y después, 50/50; `chain_head` sin cambios |
| **Prohibición de resumen** | Se inyectan 200 fragmentos parafraseados en el compositor: **200/200 abortan** con `SummaryDetected`; 0 falsos positivos sobre 2 000 fragmentos literales |
| Prueba de recepción | 50 traspasos: el 100 % ejecuta las 5 preguntas; con un modelo al que se le oculta deliberadamente el paquete, **falla y el relevo no se produce**, 20/20 |
| Regla de lectura obligatoria | 200 turnos con referencias a elementos: 100 % respaldadas por recuperación; se siembran 20 referencias sin lectura y las 20 invalidan el turno |
| Modo direccionado | Registro de 250 k tokens con un modelo de 32 k: la deliberación **termina correctamente**, con ≥ 95 % de aciertos en un cuestionario de 40 preguntas sobre detalles de rondas antiguas |
| **Recuperación proactiva (A18-1b)** | Sobre 200 turnos: cobertura ≥ **0,70** (lo pertinente ya estaba cargado) y precisión ≥ **0,40** (no se carga ruido). Prueba decisiva: 40 turnos donde lo pertinente está en la ronda 1 y el turno no la menciona — el compositor debe precargarla en ≥ 32 |
| Comparación contra resumen (control) | El mismo caso resuelto con memoria íntegra frente a memoria resumida al 10 %: la versión resumida pierde ≥ 30 % de los detalles del cuestionario — **medición que justifica el área** |
| Integridad | Alterar un byte de un elemento: detectado por `verify_chain` en 10/10 |
| Reproducibilidad | Dos ejecuciones con el mismo `context_manifest` y temperatura 0: salida idéntica en ≥ 95 % |
| Desbordamiento | Registro que no cabe ni con índice: escala de modelo o trocea; **0 casos de resumen silencioso** |
| Ventana menor | Traspaso a un modelo con la mitad de contexto: marcado `window_downgrade`, presupuesto de fetch elevado, deliberación completada, 10/10 |
| Consenso / desacuerdo | Sobre «no se perdió nada»: con conjuntos idénticos, `survives` ≥ 90; con un solo elemento ausente, `falsified` inmediato |

### 18.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta | Estado |
|---|---|---|---|---|
| Cadena rota | `verify_chain` | Memoria no fiable | Parada, `integrity=UNKNOWN`, conclusiones no citables hasta revisión | Seguro |
| Modelo entrante no supera la recepción | Prueba de recepción | Relevo imposible | Siguiente candidato; si no hay, mantener el original degradado; si tampoco, pausar con escalada | Seguro |
| Registro no cabe de ninguna forma | Compositor | Turno imposible | Trocear o escalar; si no, parada declarada | Honesto |
| Herramienta `fetch` no disponible en el proveedor | Capacidad del modelo | Sin direccionado | Se prohíbe usar ese proveedor para turnos con registro grande; se declara | Consistente |
| **Fallo parcial (el peor): el modelo ignora la herramienta y responde de memoria vaga** | Regla de lectura obligatoria | Afirmaciones sin respaldo | Turno invalidado y repetido con instrucción explícita; a la tercera, cambio de modelo | Consistente |
| Disco lleno | Umbral | No se puede appendear | **Se detiene la deliberación**; nunca se continúa sin registrar | Seguro |
| Sin red | — | Ninguno | Todo local | Operativo |

### 18.10 Riesgos y mitigaciones

Creer que se conserva todo cuando el modelo no lee lo que tiene direccionado (alta / alto → regla de lectura obligatoria con validación cruzada). Crecimiento del registro (media / bajo → 25–60 kB comprimidos por deliberación; se declara y se mide). Coste de latencia del direccionado (alta / medio → medido en §18.7 y expuesto en la interfaz; el usuario puede subir el presupuesto de memoria en Configuración). Un traspaso que bloquea el trabajo porque ningún modelo supera la recepción (media / medio → mantener el original degradado es siempre preferible a continuar sin memoria, y así está ordenado). Falsa sensación de reproducibilidad (media / medio → el `context_manifest` es la única prueba y se compara por hash). Tentación futura de reintroducir resúmenes «sólo para lo antiguo» (alta / alto → prohibido mecánicamente, no por convención: `assert_verbatim` corre en el camino crítico).

### 18.11 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA:** SQLite con disparadores de inmutabilidad, CAS del Área 0, `zstandard` 0.22, autómata de sufijos propio o `pyahocorasick` 2.x, y el validador de subcadena del §A2-3 reutilizado. Sin hardware, sin cuentas, sin red.

### 18.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (registro íntegro encadenado + `assert_verbatim` + composición con índice completo) → v1 (herramienta `fetch`, regla de lectura obligatoria, manifiesto) → completo (traspaso con prueba de recepción, verificación de no pérdida, banco comparativo contra resumen).

- **P18.a Registro.** P18.a.1 `append` inmutable y encadenado — **PV-18.a.1**: 100 000 elementos, cadena válida, 0 ediciones posibles. P18.a.2 compresión y coste — **PV-18.a.2**: ≤ 60 kB por deliberación de 7 rondas.
- **P18.b Prohibición de resumen.** P18.b.1 `assert_verbatim` en el camino crítico — **PV-18.b.1**: 200/200 paráfrasis abortadas, 0 falsos positivos en 2 000 literales.
- **P18.c Contexto.** P18.c.1 índice completo del EEA — **PV-18.c.1**: con 300 elementos, los 300 presentes y ≤ 12 000 tokens. P18.c.2 direccionado — **PV-18.c.2**: registro de 250 k con modelo de 32 k, ≥ 95 % de aciertos en el cuestionario. P18.c.3 regla de lectura — **PV-18.c.3**: 20/20 referencias sin lectura invalidadas.
- **P18.d Traspaso.** P18.d.1 paquete y prueba de recepción — **PV-18.d.1**: 50/50 traspasos verificados y sin pérdida. P18.d.2 rechazo del relevo — **PV-18.d.2**: 20/20 modelos sin paquete rechazados. P18.d.3 ventana menor — **PV-18.d.3**: 10/10 completadas con `window_downgrade`.
- **P18.e Justificación medida.** P18.e.1 banco íntegro contra resumido — **PV-18.e.1**: la memoria resumida pierde ≥ 30 % de detalles; si perdiera menos del 10 %, el área se replantea y se declara.

Métricas de salida: 0 pérdidas en 50 traspasos, 0 resúmenes admitidos, ≥ 95 % de aciertos en direccionado puro, y la comparación contra memoria resumida publicada sea cual sea su resultado.

---

## ÁREA 19 — MAGI-WEB: navegación robusta y captura de evidencia

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA** en su modo local; **🟡** para las sesiones autenticadas del propio usuario.

### 19.1 Propósito y alcance

Sustituye la automatización de navegador improvisada de las Áreas 2 y 11 por un **servidor de navegación local, gobernado por política, optimizado para agentes y con captura de evidencia verificable**. Resuelve tres problemas concretos que el plan tenía mal cubiertos: el coste en tokens de leer páginas (el HTML crudo de una página de documentación técnica ronda 40 000 tokens), la fragilidad de los selectores basados en el árbol del documento, y la ausencia de un formato de evidencia web que un tercero pueda verificar.

Queda fuera, y con carácter normativo: **todo uso destinado a evadir límites de servicio, rotar identidades o suplantar usuarios humanos frente a interfaces que no publican una API**. La restricción del §I.3 sigue vigente sin matices; esta área **no** la relaja, y en §19.4 se explica qué funciones del componente adoptado quedan desactivadas por diseño y cómo se impide reactivarlas.

**Consume:** Área 0 (política de capacidades, CAS), Área 17 (configuración), Área 15 (lo descargado entra en la cascada de ingesta). **Alimenta:** Área 2 (documentación y normas públicas), Área 11 (arte previo y literatura), Área 5 (descarga de SDK y documentación técnica), Área 16 (imágenes base verificadas).

### 19.2 Arquitectura y la decisión difícil

*Decisión:* se adopta **`jo-inc/camofox-browser`** —servidor con API REST que envuelve el motor Camoufox, un derivado de Firefox— ejecutado en el bucle local, con la versión fijada en `config/externals.lock` — porque aporta tres cosas que el plan necesita y no tiene: **instantáneas de accesibilidad** con referencias estables de elemento (`e1`, `e2`…) que reducen alrededor de un 90 % los tokens frente al HTML crudo, una **API pensada para agentes** en lugar de para pruebas de interfaz, y un motor cuya coherencia interna evita que los sitios sirvan páginas degradadas a un navegador que parece roto.
*Descartado:* seguir con Playwright a pelo — funciona, pero obliga a leer HTML completo (coste de tokens prohibitivo en el Área 11, que consulta decenas de documentos por invención) y sus selectores se rompen con cada rediseño; se conserva como **camino de reserva obligatorio**.

**La parte incómoda, y por qué esta revisión la agrava.** El componente adoptado se presenta como navegador *anti-detección*: su rasgo distintivo es falsear la huella del navegador —concurrencia de hardware, WebGL, contexto de audio, geometría de pantalla, WebRTC— **en la implementación en C++**, antes de que ningún guion de la página pueda observarla, y ofrece además rotación de salidas de proxy con sesiones pegajosas.

Hasta esta revisión, el riesgo era teórico: había un suelo de inferencia local ilimitado, así que **nadie tenía motivo** para usar el navegador contra una interfaz de chat. Al pasar a inferencia exclusivamente de nube, gratuita y con cuota (§I.3), ese motivo aparece: cuando las cuotas se agotan y el trabajo se suspende dos horas, la tentación de «entrar por el chat» deja de ser abstracta. **La corrección no es endurecer el discurso, es reconocer que el incentivo cambió y responder en la arquitectura**, con cuatro medidas, tres que ya existían y una nueva:

- **CTL-5 · propósito declarado.** Enumeración cerrada; sin propósito no hay navegación. El propósito viaja a la evidencia y a la auditoría.
- **CTL-6 · rotación imposible.** El adaptador **no expone** parámetro de proxy ni de perfil de huella; el perfil es único por instalación, se genera una vez, se registra y se declara en cada evidencia. Un vigilante comprueba cada 10 minutos que sigue siendo el mismo y que la estrategia de proxy sigue vacía; una discrepancia detiene el servidor. Cambiarlo exige editar el código fuente, no la configuración, y el §17.5 rechaza toda configuración importada que lo intente.
- **CTL-7 · lista negra permanente.** Interfaces conversacionales de terceros y servicios cuyo acceso automatizado sustituiría a una vía de pago. Es **aditiva**: el usuario puede ampliarla, nunca reducirla, y vive en `config/factory.yaml` como sólo lectura.
- **CTL-10 · separación de caminos (nuevo en esta revisión).** El módulo de navegación **no puede ser fuente de inferencia**. Se implementa como una separación de tipos, no como una regla escrita: `modules/web` devuelve `EvidencePackage` e `IngestRef`, y **no existe ninguna función que devuelva un `ModelResponse`**; el registro de proveedores del §I.3.2 sólo admite `access ∈ {official_cli, open_endpoint, session_portal}` y para `session_portal` **exige que el proveedor documente un punto final programático**, campo obligatorio `programmatic_endpoint_doc` que se valida como URL presente. Un proveedor que sólo tenga chat **no se puede declarar**: el esquema lo rechaza antes de que nadie tenga que decidir nada.

Y una constatación que el plan asume: los tres primeros controles son código, y **quien haga una bifurcación del proyecto puede quitarlos**. Eso no los hace inútiles —definen qué es este sistema y qué no— pero conviene no confundir un control con una garantía. Lo que sí es garantía es CTL-10: sin una función que devuelva inferencia, no hay atajo que tomar sin reescribir el módulo entero.

```
   petición de navegación {url, propósito declarado, clase de privacidad}
        │
        ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │ PUERTA DE POLÍTICA (nuestra, no del componente)                       │
 │  · propósito ∈ {documentación, norma, datasheet, patente, repositorio,│
 │      evidencia, sesión propia del usuario}                            │
 │  · dominio en lista de permitidos del proyecto                        │
 │  · robots.txt consultado y respetado                                  │
 │  · ⛔ rotación de identidad DESACTIVADA · ⛔ interfaces de chat de      │
 │      terceros BLOQUEADAS por lista negra permanente                   │
 └───────┬──────────────────────────────────────────────────────────────┘
         ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │ magi-web (servidor local en 127.0.0.1:9377, proceso hijo supervisado) │
 │  instantánea de accesibilidad · referencias estables · extracción de  │
 │  enlaces e imágenes · captura de pantalla · descargas · sesiones      │
 └───────┬──────────────────────────────────────────────────────────────┘
         ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │ EMPAQUETADOR DE EVIDENCIA                                             │
 │  HTML original + instantánea + captura + cabeceras + traza + hash     │
 │  + marca de tiempo → CAS, inmutable, reproducible por un tercero      │
 └───────┬──────────────────────────────────────────────────────────────┘
         ▼  → Área 15 (ingesta de lo descargado) · Área 2 · Área 11
```

### 19.3 Contratos e interfaces

```python
def ensure_server() -> WebServerInfo: ...                  # versión fijada, loopback, sin telemetría
def open_page(url: str, *, purpose: Purpose, session: str | None = None) -> TabRef: ...
def snapshot(tab: TabRef) -> A11ySnapshot: ...             # elementos con referencia estable
def act(tab: TabRef, ref: str, action: Literal["click","type","scroll"], value: str | None) -> ActResult: ...
def extract(tab: TabRef, what: Literal["links","images","text","downloads"]) -> Extraction: ...
def capture_evidence(tab: TabRef) -> EvidencePackage: ...
def download(url: str, *, expected_sha256: str | None) -> Path: ...
def user_session(name: str, *, interactive_login: bool = False) -> SessionRef: ...
def close_session(name: str) -> None: ...
```

Paquete de evidencia web (lo que hace citable una página en un dictamen):

```json
{ "evidence_id":"wev_01J9…", "url":"https://…", "final_url":"https://…",
  "fetched_at":"2026-08-02T12:31:07-05:00", "http_status":200,
  "request_headers_ref":"cas://…", "response_headers_ref":"cas://…",
  "html_sha256":"…", "a11y_snapshot_ref":"cas://…", "screenshot_ref":"cas://…",
  "text_ref":"cas://…", "trace_ref":"cas://…",
  "purpose":"norma", "robots_allowed":true, "session":null,
  "engine":{"name":"camofox-browser","version":"…","fingerprint_profile":"estable-declarado"},
  "reproduce_cmd":"magi web capture --url … --profile estable-declarado" }
```

Eventos: `web.opened`, `web.snapshot{tokens_saved}`, `web.evidence{evidence_id}`, `web.blocked{reason:"policy"|"robots"|"blacklist"}` (**crítico**), `web.session_used{name}`. Tablas: `web_evidence`, `web_session`, `web_policy_log` (DDL en §T16).

### 19.4 Implementación: qué se activa, qué se apaga y cómo se impide reactivarlo

Arranque como proceso hijo supervisado, con el entorno fijado por el núcleo y **verificado en el preflight**:

```bash
CAMOFOX_PORT=9377  CAMOFOX_HOST=127.0.0.1  CAMOFOX_ACCESS_KEY="<token de sesión>" \
CAMOFOX_CRASH_REPORT_ENABLED=false          # telemetría APAGADA: requisito del §0.3
CAMOFOX_API_KEY=""                          # importación de cookies DESACTIVADA por defecto
PROXY_STRATEGY=""                           # rotación de salidas DESACTIVADA (cadena vacía)
MAX_SESSIONS=8  SESSION_TIMEOUT_MS=900000  BROWSER_IDLE_TIMEOUT_MS=300000 \
  node tools/magi-web/<version>/server.js
```

| Función del componente | Estado en MAGI System IDE | Motivo |
|---|---|---|
| Instantánea de accesibilidad con referencias estables | **Activada** | Es el motivo de adoptarlo: ≈ 90 % menos tokens y selectores que no se rompen |
| Extracción de enlaces, imágenes, texto y descargas | **Activada** | Alimenta las Áreas 2, 11 y 15 |
| Captura de pantalla y traza de sesión | **Activada** | Es la evidencia reproducible que el Área 2 exige para citar una página |
| Coherencia de huella del motor | **Activada, con perfil único y declarado** | Un navegador con huella incoherente recibe páginas degradadas; se usa **un** perfil estable, registrado en la evidencia, **no** una huella distinta por petición |
| Sesiones persistentes del usuario | **Activada bajo permiso** | Para portales de normas o repositorios donde el usuario **tiene cuenta propia**; requiere confirmación por sesión y queda en la auditoría |
| Importación de cookies | **Desactivada por defecto** | Sólo se habilita con permiso explícito y para una sesión del propio usuario |
| **Rotación de proxy / salidas pegajosas** | **Desactivada y bloqueada** | Es rotación de identidad: prohibida por §I.3 |
| **Uso contra interfaces de chat de terceros** | **Bloqueado por lista negra permanente** | Prohibido por §I.3; la lista no es editable por el agente ni por importación de configuración |
| Telemetría del componente | **Desactivada** | El sistema no envía nada fuera del equipo |
| **Uso como fuente de inferencia** | **Imposible por tipos (CTL-10)** | El módulo no expone ninguna función que devuelva una respuesta de modelo; no es una prohibición, es una ausencia |
| Macros de búsqueda en sitios populares | **Activadas sólo para las fuentes declaradas** | Patentes, repositorios y documentación; el resto se sirve por navegación normal |
| Extracción de transcripciones de vídeo | **Activada** | Fuente legítima de documentación técnica; sujeta a la política de dominios |

**Los tres controles que hacen que esto no dependa de la buena voluntad:**

1. **`CTL-5 · propósito declarado`.** Punto de aplicación: `modules/web/policy.py::gate()`. Toda petición lleva un `purpose` de una enumeración cerrada. Un propósito ausente o desconocido se rechaza. El propósito viaja a la evidencia y a la auditoría, de modo que después se puede responder «¿para qué entró el sistema aquí?».
2. **`CTL-6 · rotación imposible`.** El adaptador **no expone** parámetro de proxy ni de perfil de huella; el perfil es único por instalación, se genera una vez, se registra y se declara en cada evidencia. Además, un vigilante comprueba cada 10 minutos que `PROXY_STRATEGY` sigue vacío y que el perfil no ha cambiado; una discrepancia detiene el servidor y emite `web.blocked{reason:"policy"}`. Cambiar esto exige editar el código fuente, no la configuración — y el §17.5 rechaza la importación de cualquier configuración que lo intente.
3. **`CTL-7 · lista negra permanente`.** Dominios de interfaces conversacionales de terceros y de servicios cuyo acceso automatizado sustituiría a una API de pago. Es **aditiva**: el usuario puede ampliarla, nunca reducirla. Vive en `config/factory.yaml` como sólo lectura.

**Respeto de `robots.txt` y de los términos.** Se consulta y se respeta por defecto; una excepción exige permiso explícito por dominio, con motivo escrito, y queda en la auditoría. La interfaz lo dice con claridad: *«Este sitio pide que no se automatice el acceso. Puedo respetarlo o puedes autorizarme una excepción; la decisión y su motivo quedarán registrados.»* El plan no decide por el usuario lo que es lícito en su jurisdicción y con su relación contractual con el sitio; **sí** deja constancia de quién decidió qué.

**Ahorro de tokens, que es la razón económica.** Una página de documentación de referencia ocupa 35 000–60 000 tokens en HTML crudo. Su instantánea de accesibilidad ronda 3 000–6 000. Con el Área 11 consultando 12 documentos por invención, la diferencia entre 500 000 y 50 000 tokens por ciclo es la diferencia entre viable e inviable en el Perfil A. El plan **no adopta** el 90 % declarado por el proyecto: fija como criterio propio **≥ 75 % de reducción** medido sobre 40 páginas reales (§19.8).

Tabla de paridad:

| Elemento | Impl. Windows | Impl. Linux |
|---|---|---|
| Servidor | Node 20 en `tools\magi-web\`, o contenedor OCI | ídem |
| Motor | Descarga verificada por hash (~300 MB) en primer uso | ídem |
| Verificación de no exposición | `Test-NetConnection` desde la IP de la interfaz activa | `ss -ltnp` + `connect()` externo |
| Perfiles y sesiones | `%LOCALAPPDATA%\MagiSystem\web\profiles\` | `~/.local/share/MagiSystem/web/profiles/` |
| Aislamiento | Job Object con límite de memoria | cgroup v2 + `seccomp` |

### 19.5 Algoritmos

**A19-1 — Puerta de política antes de cada navegación.**
```
1. validar purpose ∈ enumeración cerrada; ausente o desconocido → rechazo
2. resolver dominio; si está en la lista negra permanente (CTL-7) → web.blocked, auditoría, fin
3. si no está en la lista de permitidos del proyecto → preguntar al usuario una vez, con el propósito
     declarado a la vista; la respuesta se guarda por dominio y proyecto
4. consultar robots.txt (con caché de 24 h); si prohíbe la ruta → rechazo salvo excepción autorizada
5. comprobar CTL-6: PROXY_STRATEGY vacío y perfil de huella igual al registrado → si no, detener servidor
6. abrir, capturar evidencia, y registrar {url, purpose, decisión, quién decidió} en web_policy_log
7. caso límite: redirección a un dominio distinto → se vuelve al paso 2 con el destino real; una
     redirección hacia la lista negra aborta y se registra
```

**A19-2 — Captura de evidencia reproducible.**
```
1. abrir con perfil declarado; esperar red inactiva 500 ms o 8 s de tope
2. guardar: HTML íntegro, instantánea de accesibilidad, texto extraído, captura de pantalla a
     resolución fija (1280×N completa), cabeceras de petición y respuesta, traza de sesión
3. calcular sha256 de cada pieza; escribir el paquete en el CAS; marca de tiempo RFC 3339 local
4. componer reproduce_cmd para que un tercero repita la captura con el mismo perfil
5. lo descargado (PDF, ZIP, lo que sea) entra en la cascada del Área 15 sin excepción
6. la evidencia web es tier 4 (cita) en la escala del §3.10: por encima del razonamiento, por debajo
     del análisis estático — porque una página puede cambiar mañana, y por eso se congela aquí
```

**A19-3 — Lectura eficiente para el agente.**
```
1. pedir instantánea de accesibilidad, no HTML
2. si el contenido principal no aparece (páginas que lo dibujan por guion): esperar y reintentar 2 veces
3. si sigue sin aparecer: extraer texto; si tampoco, capturar pantalla y pasarla al VLM del Área 1
4. medir y registrar tokens_html frente a tokens_snapshot → alimenta el banco de §19.8
5. paginar contenido largo por secciones de la instantánea, nunca truncando en medio de un elemento
```

### 19.6 Integración con el debate popperiano

Afirmaciones: «esta página dice X», «esta norma es la vigente», «no existe arte previo en estas fuentes». Evidencia admisible: el paquete de evidencia con sus hashes y su `reproduce_cmd`. Refutación más potente: **volver a capturar y comparar hashes** —si el contenido cambió, la afirmación pierde su base y hay que rehacerla— y, para las afirmaciones de ausencia, **la consulta que encuentra lo que se decía inexistente**. Regla heredada del §11.9 y ahora reforzada: **sin búsqueda registrada no se puede afirmar novedad**; el paquete de evidencia de cada consulta es lo que respalda esa afirmación.

### 19.7 Costos, latencia y recursos

Servidor en reposo ≈ 40 MB; con navegador activo, 250–500 MB. Apertura de página 0,8–4 s. Instantánea ≤ 300 ms. Paquete de evidencia completo ≈ 1,5 s y 0,4–3 MB en disco. Descarga del motor: ~300 MB una sola vez. Tokens: **es un ahorro neto**, no un coste. **Salto del debate:** abrir y capturar son R0/R1 y no se debaten; sí se debaten las afirmaciones sobre el contenido. **Caché:** evidencia por `sha256(url + perfil + día)`; las consultas de arte previo caducan a 30 días (§11.7).

### 19.8 Calidad y pruebas

| Caso | Criterio de éxito |
|---|---|
| Camino feliz | 40 páginas de documentación pública: 40/40 con paquete de evidencia completo y verificable |
| **Ahorro de tokens** | Sobre esas 40: reducción media ≥ **75 %** frente al HTML crudo **y** ninguna pérdida del contenido principal (comprobado con 10 preguntas por página) |
| **No exposición de red** | El puerto no responde desde ninguna interfaz que no sea loopback, 10/10 arranques; con `CAMOFOX_HOST=0.0.0.0` forzado, el arranque **aborta** |
| **Telemetría apagada** | Captura de tráfico durante 30 min de uso: **0 conexiones** a dominios del componente |
| **CTL-6 · rotación imposible** | Intentar fijar proxy rotatorio por configuración, por importación y por variable de entorno: rechazado en las tres vías, 10/10 cada una; el vigilante detiene el servidor si el perfil cambia |
| **CTL-7 · lista negra** | 20 intentos de navegar a interfaces de chat de terceros, incluidos 5 por redirección: 20/20 bloqueados y registrados |
| **CTL-10 · separación de caminos** | Análisis estático del módulo: **0 funciones** con tipo de retorno `ModelResponse` o compatible; 10 proveedores de sólo chat declarados en configuración: **10/10 rechazados por el esquema** por falta de `programmatic_endpoint_doc` |
| Propósito declarado | 100 % de peticiones con propósito válido; 20 peticiones sin propósito, 20 rechazos |
| `robots.txt` | 15 sitios con reglas restrictivas: respetadas 15/15; la excepción exige permiso y queda en auditoría |
| Reproducibilidad de evidencia | Recapturar 20 páginas estables: hashes idénticos en ≥ 18; las 2 restantes detectadas como contenido cambiado, no como fallo |
| Sesión propia del usuario | Inicio de sesión interactivo en un portal del usuario, persistencia entre reinicios y cierre limpio, 10/10 |
| Camino de reserva | Con el servidor ausente, las Áreas 2 y 11 completan su prueba de humo con Playwright y lo declaran |
| Consenso / desacuerdo | Sobre «esta norma es la vigente»: con evidencia fechada y hash, `survives` ≥ 85; si la recaptura difiere, `falsified` |

### 19.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta | Estado |
|---|---|---|---|---|
| Servidor ausente o versión distinta | Preflight y `externals.lock` | Sin navegación optimizada | Camino de reserva con Playwright; banner en la interfaz | Degradado |
| Escucha fuera de loopback | Comprobación activa | Riesgo de seguridad | **Aborto del arranque** | Seguro |
| Perfil de huella alterado | Vigilante cada 10 min | Posible uso indebido | Detener servidor, `web.blocked`, auditoría | Seguro |
| Sitio que no se renderiza | Contenido principal ausente | Sin datos | Escalonado del A19-3 hasta la captura de pantalla y el VLM | Degradado, funcional |
| **Fallo parcial (el peor): instantánea que omite el contenido principal sin avisar** | Comparación de longitud contra el texto extraído y 10 preguntas de control | Análisis sobre nada | Marcar `snapshot_incomplete`, usar el texto completo y registrar la página para revisión | Consistente |
| Descarga con hash distinto del esperado | Verificación | Artefacto no confiable | Rechazo y cuarentena | Seguro |
| Sin red | — | Área inoperante | El resto del sistema funciona; las afirmaciones de novedad quedan prohibidas (§11.9) | Honesto |

### 19.10 Riesgos y mitigaciones

**Uso del componente para lo que el plan prohíbe** (media / **crítico** → CTL-5, CTL-6 y CTL-7 en código, vigilante periódico, lista negra no reducible, y rechazo de configuración importada que los toque; y, sobre todo, la decisión de **no exponer** el parámetro de proxy en el adaptador). Responsabilidad sobre términos de terceros (alta / medio → `robots.txt` respetado por defecto, propósito declarado, excepciones con motivo y auditoría; el plan deja constancia, no absuelve). Dependencia de un componente joven en el camino de la investigación (media / medio → camino de reserva probado). Evidencia que caduca porque la página cambia (alta / bajo → congelación en el CAS con fecha y hash, y recaptura como refutación legítima). Sesiones autenticadas que se dejan abiertas (media / medio → tiempo de expiración de 15 minutos, cierre explícito y aviso en la interfaz cuando hay una sesión viva). Telemetría del componente activada por defecto (alta / medio → apagada por variable y verificada con captura de tráfico en el banco).

### 19.11 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA:** Node.js 20 LTS o runtime OCI, ~300 MB para el motor, y la política del Área 0. **🟡 REQUIERE-PRERREQUISITO:** para sesiones autenticadas, la cuenta **propia** del usuario en el sitio correspondiente y su consentimiento por sesión. **🔴** ninguno. Licencia del componente a registrar en §T6 al fijar la versión; se ejecuta como **proceso separado por HTTP**, de modo que su licencia queda aislada de la del producto.

### 19.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (servidor local, apertura, instantánea, captura de evidencia) → v1 (puerta de política con los tres controles, `robots.txt`, sesiones del usuario) → completo (macros de fuentes declaradas, transcripciones, banco de ahorro y camino de reserva verificado).

- **P19.a Adopción segura.** P19.a.1 versión fijada y verificada — **PV-19.a.1**: hash correcto y enumeración efectiva de puntos finales en `externals.lock`. P19.a.2 loopback y telemetría — **PV-19.a.2**: 0 respuestas fuera de loopback, 0 conexiones de telemetría en 30 min.
- **P19.b Controles.** P19.b.1 CTL-5 propósito — **PV-19.b.1**: 20/20 peticiones sin propósito rechazadas. P19.b.2 CTL-6 rotación — **PV-19.b.2**: rechazado por las tres vías; vigilante detiene ante cambio de perfil. P19.b.3 CTL-7 lista negra — **PV-19.b.3**: 20/20 bloqueos, incluidas redirecciones.
- **P19.c Eficiencia y evidencia.** P19.c.1 instantáneas — **PV-19.c.1**: ahorro ≥ 75 % sin pérdida de contenido principal. P19.c.2 paquete de evidencia — **PV-19.c.2**: reproducible por un tercero en ≥ 18 de 20.
- **P19.d Integración.** P19.d.1 descargas hacia el Área 15 — **PV-19.d.1**: 100 % de descargas pasan por la cascada de ingesta. P19.d.2 camino de reserva — **PV-19.d.2**: con el servidor ausente, Áreas 2 y 11 completan su prueba de humo.

Métricas de salida: ahorro de tokens ≥ 75 %, 0 usos fuera de propósito, 0 rotaciones de identidad posibles, 0 conexiones de telemetría, y evidencia web reproducible por terceros.

---

## ÁREA 20 — MAGI-STUDIO: creación de videojuegos, música, imagen y vídeo con autocorrección

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA** en todo lo que se genera como código y se verifica de forma determinista; **🟡** para lo que depende de un servicio de generación de imagen o vídeo en la nube, que sigue la política del §I.3.

### 20.1 Propósito y alcance

Añade al sistema la capacidad de **crear obra**: videojuegos jugables, música, imagen en cualquier estilo —desde arte de píxeles hasta ilustración fotorrealista, pasando por cómic, manga y animación— y vídeo. Y, sobre todo, añade lo que separa a un generador de un autor: **un bucle de autocorrección con criterios medibles**, donde lo producido se ejecuta, se mide, se critica y se rehace hasta cumplir una especificación que se escribió antes.

*Decisión rectora:* siempre que sea posible, **la obra se genera como código o como partitura, no como píxel opaco** — un arte de píxeles es una paleta y una rejilla; una animación es una lista de fotogramas con sus reglas; una pieza musical es una partitura simbólica; un videojuego es código fuente — porque lo que está escrito como código **se puede ejecutar, medir, comparar y corregir de forma automática**, mientras que un archivo de imagen devuelto por un servicio sólo se puede mirar. La generación por servicio de nube se usa donde aporta algo que el código no da (fotorrealismo, textura pictórica), y **también** entra en el bucle de crítica.
*Descartado:* apoyar toda el área en servicios generativos de nube — produce resultados vistosos, irreproducibles y no corregibles, y con la política de cuotas del §I.3 sería además la parte más frágil del sistema.

Queda fuera: la fabricación física de la obra (Área 9), la distribución en tiendas, y la generación de contenido que suplante la identidad de personas reales o infrinja derechos de terceros — controlado por **CTL-8** (§20.4).

**Consume:** Área 3 (deliberación), Área 8 (ejecución y postcondiciones), Área 15 (activos aportados por el usuario en cualquier formato), Área 16 (entorno aislado para ejecutar el juego), Área 17 (parámetros), Área 18 (memoria de las iteraciones). **Alimenta:** Área 10 (pestañas *Imagen* y *Vista previa* del lienzo), Área 11 (prototipos), Área 21 (proyecto y repositorio).

### 20.2 Arquitectura: el bucle de autocorrección es el módulo

```
   instrucción  ("un juego de plataformas de 8 bits", "un tema de 90 s", "un cómic de 6 viñetas")
        │
        ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ ESPECIFICACIÓN MEDIBLE (obligatoria, antes de generar nada)            │
 │  qué se produce · en qué estilo · con qué restricciones · y CÓMO SE    │
 │  MIDE que está bien: criterios numéricos o rúbrica con casos           │
 │  ⚠ sin criterios de medición no se genera: se pregunta                 │
 └──────────┬─────────────────────────────────────────────────────────────┘
            ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ GENERADOR      código · partitura · rejilla de píxeles · guion gráfico │
 │  (MELCHIOR • 1 propone; el resultado es un artefacto ejecutable)       │
 └──────────┬─────────────────────────────────────────────────────────────┘
            ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ MATERIALIZADOR  compila · renderiza · sintetiza · monta                │
 └──────────┬─────────────────────────────────────────────────────────────┘
            ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ MEDIDOR AUTOMÁTICO (determinista, sin modelo)                          │
 │  juego: ¿arranca? ¿el agente de prueba supera el nivel? ¿fotogramas?   │
 │  música: ¿tono, tempo, rango dinámico, disonancia, duración?           │
 │  imagen: ¿paleta, resolución, coherencia entre fotogramas, anatomía?   │
 │  vídeo: ¿continuidad, ritmo de corte, sincronía con el audio?          │
 └──────────┬─────────────────────────────────────────────────────────────┘
            ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ CRÍTICA  BALTHASAR • 2 sobre las MEDIDAS y sobre la obra renderizada   │
 │          CASPER • 3 decide si mejora, si empeora o si converge         │
 │  ⚠ regla de trinquete: no sube la nota sin resolver una medida         │
 └──────────┬─────────────────────────────────────────────────────────────┘
            ▼  si no converge → nueva versión (el generador ve las medidas, no una opinión)
   obra + informe de iteraciones + medidas por versión → lienzo (Área 10)
```

**La especificación medible es obligatoria.** Antes de generar, el sistema escribe —y muestra en el lienzo— qué va a producir y **cómo se comprobará**. «Un juego bonito» no es una especificación; «un juego de plataformas de una pantalla, 320×180, paleta de 16 colores, que un agente de prueba pueda terminar en menos de 90 segundos y que mantenga 60 fotogramas por segundo en el equipo del usuario» sí lo es. Si el usuario no da criterios, el sistema propone los suyos y **pide confirmación en una sola pregunta**.

### 20.3 Contratos e interfaces

```python
def spec_from_prompt(prompt: str, kind: MediaKind) -> MediaSpec: ...      # con criterios medibles
def generate(spec: MediaSpec, *, version: int, feedback: Measurements | None) -> MediaArtifact: ...
def materialize(artifact: MediaArtifact) -> RenderedMedia: ...
def measure(rendered: RenderedMedia, spec: MediaSpec) -> Measurements: ...
def critique(rendered: RenderedMedia, m: Measurements, spec: MediaSpec) -> Critique: ...
def iterate(spec: MediaSpec, *, max_versions: int = 6) -> IterationReport: ...
def playtest(game: GameArtifact, *, budget_s: int = 120) -> PlaytestReport: ...
def export(artifact: MediaArtifact, target: ExportTarget) -> Path: ...
```

`MediaSpec` (extracto; el esquema completo vive en `schemas/media_spec.json`):

```json
{ "spec_id":"msp_01J9…", "kind":"game|music|image|animation|comic|video",
  "brief":"…lo que pidió el usuario, literal…",
  "style":{"named":"pixel-8bit|manga|comic-us|acuarela|fotorrealista|linea-clara|…",
           "palette":["#0f380f","#306230","#8bac0f","#9bbc0f"], "resolution":[320,180],
           "references":["cas://…"]},
  "constraints":{"duration_s":90,"frames":24,"panels":6,"max_size_mb":8,"offline_ok":true},
  "acceptance":[
    {"id":"a1","metric":"playtest.completa_nivel","op":">=","value":1,"hard":true},
    {"id":"a2","metric":"render.fps_p05","op":">=","value":60,"hard":true},
    {"id":"a3","metric":"palette.colores_distintos","op":"<=","value":16,"hard":true},
    {"id":"a4","metric":"critique.rubrica_estilo","op":">=","value":4,"scale":5,"hard":false}],
  "rights":{"referencias_propias":true,"personas_reales":false,"marcas":false} }
```

Eventos: `studio.spec`, `studio.version{n, passed, failed}`, `studio.measured{metrics}`, `studio.converged{version}`, `studio.blocked{reason}`. Tablas: `media_spec`, `media_version`, `media_measurement`, `playtest_run` (DDL en §T17).

### 20.4 Implementación por tipo de obra

**Videojuegos.** *Decisión:* motor **Godot 4.x** con guiones en GDScript como camino principal y **HTML5 con lienzo** (juego de una sola página, sin dependencias) como camino ligero — porque Godot es libre, exporta a escritorio y a web, tiene modo sin ventana para pruebas automáticas, y su formato de escena es texto legible y modificable por el generador.
*Descartado:* motores propietarios y motores sin modo automatizable — sin ejecución sin ventana no hay autocorrección posible.
El **agente de prueba de juego** es lo que hace medible un videojuego: un guion que carga la escena en modo sin ventana, inyecta entradas (aleatorias acotadas, y luego dirigidas por una búsqueda simple sobre el estado del juego) y mide: si el juego arranca, si el nivel es completable, en cuántos segundos, cuántas muertes, si hay estados sin salida, si hay colisiones imposibles, fotogramas por segundo mínimo y en el percentil 5, y si algún objeto sale del mundo. Un juego que el agente **no puede terminar** no es un juego terminado, y esa medida es objetiva. Ejecución dentro de la caja del **Área 16** cuando el juego es código de origen desconocido.

**Música.** *Decisión:* **partitura simbólica primero** (`music21` 9.x → MIDI) y síntesis con **FluidSynth 2.3** más bancos de sonido de libre distribución; para sonido diseñado, **SuperCollider 3.13** o síntesis propia con `numpy`; mezcla y masterizado con `ffmpeg` 7.x y `pyloudnorm` — porque una partitura se puede analizar, transponer, corregir y volver a renderizar, y un archivo de audio sólo se puede recortar.
Medidas automáticas: tono y afinación (`librosa`, `aubio`), tempo y estabilidad del pulso, rango dinámico y sonoridad integrada, densidad armónica y proporción de disonancia no resuelta (`music21`), duración frente a la pedida, y silencio inicial y final. Para voz o percusión imitada, la comparación con la referencia usa los mismos descriptores del §12.3 (C37).

**Imagen.** Cuatro caminos según el estilo, todos con el mismo bucle:

| Estilo | Camino principal | Medidas automáticas |
|---|---|---|
| **Arte de píxeles** | Generación de **rejilla y paleta como datos** (JSON) y renderizado determinista con `Pillow` 10.x; escalado por vecino más próximo | Número de colores ≤ paleta, alineación a rejilla, ausencia de píxeles huérfanos, contraste entre figura y fondo, tamaño exacto |
| **Vectorial, línea clara, cómic y manga** | **SVG generado**, con capas de tinta, tramas y bocadillos; tipografía libre; rasterizado con `resvg`/`cairosvg` | Legibilidad de bocadillos (área y contraste), grosor de línea dentro de rango, número de viñetas, dirección de lectura, densidad de trama por FFT (§1.5) |
| **Pintura, acuarela, textura** | Composición programática de capas y filtros con `Pillow`/`scikit-image`, más referencia de estilo del usuario | Histograma dentro de la referencia, ausencia de bandas, resolución |
| **Fotorrealista** | Servicio de generación en la nube del §I.3 cuando hay cuota; si no, **se declara y se ofrece el camino vectorial o la composición** | Nitidez, artefactos, coherencia anatómica por puntos clave (`mediapipe`), coherencia entre imágenes de la misma serie |

**Animación y GIF.** Fotogramas generados por los caminos anteriores más **reglas de interpolación explícitas** (posición, escala, opacidad por fotograma en un fichero de animación legible); montaje con `Pillow` para GIF y `ffmpeg` para WebP animado y vídeo. Medidas: coherencia entre fotogramas (SSIM entre consecutivos dentro de una banda), tamaño del archivo, número de colores del GIF, cadencia real frente a la declarada, y ausencia de saltos.

**Vídeo.** Guion gráfico como datos → planos generados o compuestos → montaje con `ffmpeg` según una **lista de decisiones de edición** legible. Medidas: duración por plano frente a la declarada, ritmo de corte y su desviación, continuidad de color entre planos, sincronía audio-imagen (desfase medio ≤ 40 ms, reutilizando C39), y sonoridad integrada.

**CTL-8 — control de derechos y de identidad.** Punto de aplicación: `modules/studio/rights.py::gate()`. Reglas: (a) **no se generan retratos de personas reales identificables** ni voces que imiten a una persona concreta; la petición se rechaza con explicación y se ofrece la alternativa genérica; (b) las **referencias de estilo** deben ser del usuario o de dominio público declarado, y quedan en la procedencia; (c) toda obra exportada lleva un **manifiesto de procedencia** con las referencias usadas, los servicios que intervinieron y las versiones; (d) las marcas y personajes de terceros se rechazan en la especificación, no después de generar. El gate corre **antes** del generador, no después: rechazar cuando ya está hecho es la peor de las políticas.

### 20.5 Algoritmos

**A20-1 — Bucle de autocorrección con medidas (el núcleo del área).**
```
 1. spec := spec_from_prompt(...); si falta cualquier criterio 'hard', preguntar UNA vez y fijarlo
 2. CTL-8 sobre la especificación; rechazo temprano si procede
 3. v := 1; historial := []
 4. MIENTRAS v ≤ max_versions:
 4.1   artefacto := generate(spec, version=v, feedback = medidas de v-1)   ← ve NÚMEROS, no adjetivos
 4.2   render := materialize(artefacto)        # compila / renderiza / sintetiza / monta
 4.3   m := measure(render, spec)              # determinista, sin modelo
 4.4   duros_fallidos := criterios hard que m no cumple
 4.5   crítica := BALTHASAR • 2 sobre (render, m, spec)  → señala lo que la medida no capta
 4.6   veredicto := CASPER • 3 con la rúbrica híbrida del §A3-2:
         parte mecánica = proporción de criterios cumplidos y su margen
         parte de juicio = adecuación al estilo pedido y calidad percibida
 4.7   historial += {v, m, veredicto}; si duros_fallidos = ∅ y veredicto ≥ umbral → CONVERGE
 4.8   si el número de criterios cumplidos NO aumenta en dos versiones seguidas → PARADA por meseta:
         se entrega la mejor versión y se dice qué criterio no se logró y por qué
 4.9   v += 1
 5. selección final: mejor versión de TODO el historial, no la última (misma regla que §A3-1b)
 6. casos límite:
 6.1   el materializador falla (no compila, no renderiza) → es un fallo duro con mensaje del compilador
         devuelto al generador como refutación, sin gastar una versión completa
 6.2   criterio imposible por contradicción (16 colores y degradado suave) → se detecta al fijar la
         especificación y se avisa ANTES de generar
 6.3   sin cuota de nube → se generan y miden las versiones que el camino determinista permite y se
         declara qué parte quedó sin crítica de modelo
```

**A20-2 — Agente de prueba de juego.**
```
1. cargar la escena en modo sin ventana con el motor; fijar semilla
2. fase A (30 s): entradas aleatorias acotadas → mide arranque, caídas, fotogramas, objetos fuera del mundo
3. fase B (60 s): búsqueda dirigida sobre el estado (posición del jugador, objetivo) con retroceso al
     último punto seguro; mide completable, tiempo, muertes, estados sin salida
4. fase C (30 s): entradas adversarias (pulsaciones simultáneas, pausa en transición, salir del área)
     → mide robustez: cualquier bloqueo o caída es fallo duro
5. salida: PlaytestReport con vídeo del intento, que se muestra en la pestaña Vista previa del lienzo
6. criterio de éxito del área: el agente completa el nivel en ≥ 8 de 10 ejecuciones con semillas distintas
```

**A20-3 — Coherencia de una serie de imágenes (cómic, manga, animación).**
```
1. fijar una FICHA DE ESTILO como datos: paleta, grosor de línea, proporciones del personaje,
     tipografía y encuadres permitidos  → es lo que se pasa a cada generación, no una descripción libre
2. tras generar cada imagen: medir contra la ficha (paleta, grosor, proporciones por puntos clave)
3. medir coherencia entre imágenes consecutivas: distancia de histograma acotada y, en personajes,
     distancia entre proporciones ≤ 8 %
4. una imagen fuera de ficha se regenera SOLA, sin rehacer la serie entera
5. la ficha de estilo se guarda con la obra: es lo que permite continuar la serie meses después
```

### 20.6 Integración con el debate popperiano

Afirmaciones: «esta obra cumple la especificación», «este juego es completable», «esta serie es coherente». Evidencia admisible: las medidas deterministas con su método, el informe del agente de prueba con su vídeo, y los renderizados con su hash. Refutación más potente: **el agente de prueba que no termina el nivel** y **la medida fuera de rango** — ambas automáticas. Para lo estético, que no es medible, la refutación es la **rúbrica de estilo con casos**: BALTHASAR • 2 debe señalar el elemento concreto que se desvía de la ficha, no expresar disgusto. Invocación: en cada versión del bucle, con presupuesto reducido (2 rondas) porque la evidencia es barata y abundante; y con las 3 rondas completas sólo en la especificación inicial y en la selección final.

### 20.7 Costos, latencia y recursos

Generación de código de juego: 6 000–14 000 tokens por versión. Compilación y prueba en Godot sin ventana: 40–120 s. Renderizado de arte de píxeles: < 1 s. SVG a mapa de bits: 0,2–2 s. Síntesis de 90 s de música: 8–25 s. Montaje de vídeo de 60 s: 30–90 s. Servicio de imagen en la nube: según cuota del §I.3, y **cada llamada se reserva en el libro de cuotas** como cualquier otra. Un bucle típico de 4 versiones de un juego pequeño: ≈ 60 000 tokens y 12–20 min. RAM: Godot sin ventana 500 MB–1,2 GB. Disco: los artefactos de medios pesan; se declara y se purgan las versiones no seleccionadas salvo la mejor y la última. **Salto del debate:** las medidas deterministas no se debaten, se ejecutan. **Caché:** renderizados por `sha256(fuente + parámetros + versión de la herramienta)`.

### 20.8 Calidad y pruebas

| Caso | Criterio de éxito |
|---|---|
| Camino feliz: juego de plataformas | Arranca, el agente lo completa en ≥ 8 de 10 semillas, fotogramas p05 ≥ 60, converge en ≤ 4 versiones |
| **Autocorrección real** | Sobre 20 encargos con un criterio duro deliberadamente difícil: la proporción de criterios cumplidos **aumenta** entre la versión 1 y la final en ≥ 17 de 20; si no aumenta, el bucle no está funcionando y se declara |
| Juego no completable | Se siembra un nivel imposible: el agente lo detecta y el sistema **no lo declara terminado**, 10/10 |
| Arte de píxeles | 30 encargos con paleta y tamaño fijados: 30/30 cumplen colores y dimensiones exactos |
| Cómic y manga | 10 series de 6 viñetas: coherencia de personaje ≤ 8 % de desviación en ≥ 9; bocadillos legibles al 100 % |
| Animación GIF | 20 animaciones: cadencia real dentro del ±5 % de la declarada, tamaño bajo el máximo, 20/20 |
| Música | 20 piezas: tempo dentro del ±2 %, duración dentro del ±3 %, sonoridad integrada dentro de la banda pedida |
| Vídeo | 10 montajes: sincronía audio-imagen ≤ 40 ms, ritmo de corte dentro del ±15 % |
| Fotorrealista sin cuota | Con los servicios agotados: se ofrece el camino alternativo y **se declara**; 0 fallos silenciosos |
| CTL-8 | 20 peticiones de retrato de persona real o de marca ajena: 20/20 rechazadas **en la especificación**, con alternativa ofrecida |
| Meseta | Encargo con criterio contradictorio: parada por meseta con explicación del criterio imposible, 10/10 |
| Consenso / desacuerdo | Con todos los criterios duros cumplidos, `survives` ≥ 85; con uno incumplido, no converge aunque la crítica estética sea excelente |

### 20.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta | Estado |
|---|---|---|---|---|
| El motor de juego no está instalado | Preflight | Sin juegos de escritorio | Camino HTML5 con lienzo, que no necesita nada; se declara la diferencia | Degradado |
| El juego no compila | Salida del compilador | Versión perdida | Error devuelto al generador como refutación, sin contar como versión | Recuperado |
| El agente de prueba se atasca sin ser culpa del juego | Sin progreso con estado cambiante | Falso negativo | Tres semillas distintas antes de declarar no completable | Consistente |
| **Fallo parcial (el peor): la obra cumple todas las medidas y es mala** | Rúbrica de estilo baja con medidas altas | Entrega decepcionante | Se entrega **declarando** que cumple lo medible y no convence en lo estético, y se pide al usuario un criterio nuevo que capture lo que falta — que pasa a formar parte de la especificación | Honesto |
| Servicio de imagen agotado | Libro de cuotas | Sin fotorrealismo | Camino alternativo o espera a la recuperación, con reloj visible | Degradado |
| Artefactos que llenan el disco | Umbral | Sin espacio | Purga de versiones no seleccionadas con aviso | Contenido |
| Sin red | — | Sin crítica de modelo ni servicios de imagen | **Generación y medición deterministas siguen funcionando**: arte de píxeles, SVG, música simbólica, juegos y montaje | Degradado, muy funcional |

### 20.10 Riesgos y mitigaciones

Confundir «cumple las medidas» con «es bueno» (alta / alto → el modo de fallo está reconocido arriba y la respuesta es declararlo y ampliar la especificación, no fingir). Generación de contenido que infringe derechos o suplanta a personas (media / **crítico** → CTL-8 antes de generar, manifiesto de procedencia en cada exportación). Bucles caros que no convergen (alta / medio → parada por meseta y presupuesto de versiones). Dependencia de servicios de nube para el estilo fotorrealista (alta / medio → tres caminos deterministas cubren el resto, y la ausencia se declara). Juegos generados que se ejecutan en el equipo del usuario (media / alto → ejecución en la caja del Área 16 cuando el código no lo escribió el propio sistema). Sobreajuste del generador a las métricas (media / medio → la crítica de BALTHASAR • 2 existe precisamente para señalar lo que la medida no capta, y su ausencia de hallazgos se registra).

### 20.11 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA:** Godot 4.x (MIT), `Pillow` 10.x, `resvg`/`cairosvg`, `scikit-image`, `music21` 9.x, FluidSynth 2.3 con bancos libres, SuperCollider 3.13, `ffmpeg` 7.x, `librosa`, `aubio`, `pyloudnorm`, `mediapipe`, tipografías libres. **🟡 REQUIERE-PRERREQUISITO:** para el estilo fotorrealista, un servicio de generación de imagen o vídeo en la nube accesible según §I.3, con su cuota; sin él, el resto del área funciona. **🔴** ninguno.

### 20.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (especificación medible + arte de píxeles + música simbólica, con bucle completo) → v1 (juegos con agente de prueba, SVG, cómic y animación) → completo (vídeo, fotorrealista, ficha de estilo persistente, CTL-8).

- **P20.a Especificación.** P20.a.1 criterios medibles obligatorios — **PV-20.a.1**: 0 generaciones sin criterios duros; 20/20 encargos vagos producen una única pregunta. P20.a.2 contradicciones — **PV-20.a.2**: 10/10 criterios imposibles detectados antes de generar.
- **P20.b Bucle.** P20.b.1 medición determinista por tipo — **PV-20.b.1**: cada tipo con sus medidas implementadas y reproducibles. P20.b.2 autocorrección — **PV-20.b.2**: mejora en ≥ 17 de 20 encargos. P20.b.3 selección de la mejor versión — **PV-20.b.3**: 100 % de entregas con la mejor, no la última, y justificación si difieren.
- **P20.c Juegos.** P20.c.1 agente de prueba — **PV-20.c.1**: completa en ≥ 8 de 10 semillas; detecta el nivel imposible sembrado 10/10. P20.c.2 aislamiento — **PV-20.c.2**: código ajeno ejecutado sólo dentro de la caja del Área 16.
- **P20.d Imagen y serie.** P20.d.1 los cuatro caminos — **PV-20.d.1**: cada uno produce y mide. P20.d.2 ficha de estilo — **PV-20.d.2**: coherencia ≤ 8 % en series de 6.
- **P20.e Derechos.** P20.e.1 CTL-8 — **PV-20.e.1**: 20/20 rechazos en la especificación con alternativa. P20.e.2 manifiesto — **PV-20.e.2**: 100 % de exportaciones con procedencia completa.

Métricas de salida: mejora medible en ≥ 85 % de los encargos, juegos completables verificados por agente, 0 generaciones sin criterios, y 0 exportaciones sin manifiesto de procedencia.

---

## ÁREA 21 — MAGI-SHELL: aplicación de escritorio, extensión de navegador y proyectos con repositorio

**Estado de construibilidad del módulo: 🟢 CONSTRUIBLE-YA**; **🟡** para la publicación en las tiendas de extensiones y para la conexión con un repositorio remoto, que exige una cuenta del usuario.

### 21.1 Propósito y alcance

Resuelve tres cosas que hasta ahora estaban implícitas y mal atadas: **cómo se ejecuta el sistema** (un ejecutable, nunca una página web), **cómo se conecta al navegador del usuario** (una extensión que habla con el ejecutable, no un servidor que se abre en una pestaña) y **qué es exactamente un proyecto** (una carpeta real en el disco, versionada, que puede subirse a un repositorio y volver a bajarse en otro equipo con el sistema instalado).

Queda fuera: la navegación gobernada del propio sistema (Área 19, que es un navegador interno con otra finalidad) y la política de capacidades (§10.6).

**Consume:** Área 0 (procesos, política, CAS), Área 17 (configuración), Área 18 (memoria), Área 19 (evidencia web). **Alimenta:** Área 10 (la ventana es esto), todas las áreas que producen artefactos de proyecto.

### 21.2 Arquitectura: tres piezas y ningún servidor web

*Decisión:* MAGI System IDE es **una aplicación de escritorio nativa** —`MagiSystem.exe` en Windows y un binario o AppImage en Linux— cuya interfaz se dibuja en un componente de vista web **embebido en el proceso**, sin servir ninguna página, sin escuchar en ningún puerto para la interfaz y sin que exista una dirección que se pueda abrir en un navegador; el canal entre la interfaz y el núcleo pasa a ser **una tubería con nombre en Windows y un socket de dominio Unix en Linux**, no un WebSocket sobre TCP — porque «no se abre por la web» sólo es cierto si **no hay nada que abrir**, y el diseño anterior, con el núcleo escuchando en `127.0.0.1`, dejaba exactamente eso.
*Descartado:* el WebSocket local de las revisiones anteriores, que era cómodo y depurable pero contradecía el requisito y ampliaba la superficie.

```
 ┌───────────────────────────────────────────────────────────────────────────┐
 │  MagiSystem.exe   (proceso único, ventana nativa, sin puerto de interfaz)  │
 │  ┌──────────────────────┐   tubería con nombre / socket Unix              │
 │  │ INTERFAZ (vista web  │◄──────────────────────────────┐                 │
 │  │ embebida, sin URL)   │   marcos con longitud + CBOR   │                 │
 │  └──────────────────────┘                                │                 │
 │  ┌───────────────────────────────────────────────────────▼──────────────┐  │
 │  │ NÚCLEO  (mismo ejecutable, hilo/proceso hijo supervisado)            │  │
 │  └───────────────┬──────────────────────────────┬───────────────────────┘  │
 └──────────────────┼──────────────────────────────┼──────────────────────────┘
                    │ mensajería nativa            │ carpeta de proyecto
                    ▼                              ▼
      ┌──────────────────────────┐   ┌────────────────────────────────────────┐
      │ EXTENSIÓN DE NAVEGADOR   │   │ PROYECTO = CARPETA REAL EN EL DISCO     │
      │ Chrome · Firefox · Edge  │   │ con repositorio local y, si el usuario  │
      │ envía la página actual,  │   │ lo autoriza, remoto en su cuenta        │
      │ la selección, capturas   │   └────────────────────────────────────────┘
      └──────────────────────────┘
```

**Por qué la vista web embebida no contradice el requisito.** El componente de dibujo del sistema operativo —el mismo que usan los clientes de correo y de mensajería de escritorio— renderiza la interfaz **dentro** del proceso, desde ficheros incrustados en el ejecutable, con navegación a direcciones externas **deshabilitada** y sin devolver ninguna página a nadie. No hay servidor, no hay dirección, no hay pestaña. Se verifica: `PV-21.a.2` comprueba con un análisis de puertos que el ejecutable **no escucha en ninguno** para la interfaz, y `PV-21.a.3` que intentar abrir cualquier dirección del sistema en un navegador **no devuelve nada**.

### 21.3 Contratos e interfaces

```python
# Aplicación
def ipc_channel() -> ChannelInfo: ...           # nombre de tubería o ruta de socket, permisos del usuario
def single_instance_guard() -> bool: ...
# Extensión
def ext_handshake(origin: ExtensionOrigin) -> PairingResult: ...   # emparejamiento con confirmación
def ext_send_page(payload: PagePayload) -> IngestRef: ...          # entra por el Área 15
def ext_send_selection(text: str, url: str) -> IngestRef: ...
def ext_request_capture(url: str) -> EvidenceRef: ...              # delega en el Área 19
# Proyecto
def project_create(path: Path, template: str | None) -> ProjectRef: ...
def project_open(path: Path) -> ProjectRef: ...
def repo_init(project: ProjectRef) -> None: ...
def repo_connect(project: ProjectRef, remote_url: str, auth: RepoAuth) -> ConnectResult: ...
def repo_sync(project: ProjectRef, *, direction: Literal["push","pull","both"]) -> SyncReport: ...
def project_portability_check(project: ProjectRef) -> PortabilityReport: ...
```

Eventos: `app.started`, `app.ipc_ready`, `ext.paired{browser}`, `ext.page_sent`, `ext.blocked{reason}`, `project.created`, `repo.connected{remote}`, `repo.synced{ahead, behind, conflicts}`, `repo.secret_blocked` (**crítico**), `project.portability{ok, missing[]}`. Tablas: `app_instance`, `ext_pairing`, `project_repo`, `repo_sync_log` (DDL en §T17).

### 21.4 Implementación

#### 21.4.a El ejecutable

Windows: `MagiSystem.exe` producido por `tauri build --target nsis` y también en variante **portátil de un solo fichero** que no requiere instalación ni privilegios (usa `%LOCALAPPDATA%` para datos). Linux: AppImage y `.deb`. Instancia única mediante mutex nombrado o `flock`; al lanzar una segunda copia, se enfoca la ventana existente y se le pasa el argumento (por ejemplo, la carpeta de proyecto). Canal de interfaz: tubería `\\.\pipe\MagiSystem.<sid>` con descriptor de seguridad restringido al usuario, o socket `~/.local/state/MagiSystem/ipc.sock` con permisos `0600`; marcos con longitud prefijada y carga en CBOR. **La navegación externa de la vista embebida está deshabilitada**: cualquier enlace se abre en el navegador del sistema, nunca dentro.

#### 21.4.b La extensión de navegador

*Decisión:* la extensión se comunica con el ejecutable por **mensajería nativa** —el mecanismo que Chrome, Edge y Firefox ofrecen para que una extensión hable con un programa instalado— y **no** por una petición a `localhost` — porque la mensajería nativa no abre ningún puerto, sólo funciona con el manifiesto que el instalador registra y con los identificadores de extensión declarados, y por tanto ninguna página web puede suplantarla.
*Descartado:* que la extensión llame a un servidor local del sistema — reintroduciría el puerto que el §21.2 acaba de eliminar y sería alcanzable desde cualquier pestaña.

Manifiesto V3 con permisos mínimos: `activeTab`, `scripting` bajo acción del usuario, `nativeMessaging`, `contextMenus`, `storage`. **Sin `host_permissions` amplios**: la extensión no lee páginas por su cuenta, sólo cuando el usuario pulsa. Qué hace:

| Acción del usuario | Qué envía al ejecutable | Qué recibe |
|---|---|---|
| Botón «Enviar a MAGI» | Dirección, título, texto principal extraído y, opcionalmente, el HTML | La página entra por el Área 15 y aparece como adjunto en el hilo activo |
| Selección + menú contextual | El texto seleccionado con su dirección y su ubicación | Aparece como cita en el campo de instrucción |
| «Capturar como evidencia» | La dirección | El Área 19 hace la captura completa y devuelve el identificador de evidencia |
| «Continuar aquí» | La pestaña actual | El sistema abre el hilo relacionado con esa página, si existe |
| Indicador de estado | — | Si el ejecutable está abierto, con qué proyecto y si hay algo esperando permiso |

**Emparejamiento con confirmación.** La primera vez, el ejecutable muestra un diálogo con el navegador y el identificador de la extensión, y el usuario acepta. El emparejamiento se guarda en `ext_pairing` y se puede revocar desde Configuración. Una extensión no emparejada recibe `ext.blocked`. La extensión **nunca** recibe del ejecutable contenido del proyecto ni de la conversación: el flujo es de una sola dirección salvo el indicador de estado, que es un booleano y un nombre.

#### 21.4.c El proyecto es una carpeta

*Decisión:* un proyecto es **una carpeta elegida por el usuario en su disco**, con estructura declarada y **un repositorio Git local desde el minuto uno**; la base de datos del proyecto vive dentro de esa carpeta y **todo lo que hace falta para continuar el trabajo en otro equipo está ahí** — porque la diferencia real entre «conversación» y «proyecto» no es la persistencia, es que **el proyecto es un objeto que se puede coger y llevar**.
*Descartado:* proyectos guardados en un almacén interno del sistema — cómodo de programar, imposible de compartir, y convierte al sistema en un silo.

```
<carpeta del proyecto>/
├── .magi/
│   ├── project.yaml          nombre, plantilla, versión de esquema, áreas activas
│   ├── project.db            estado (SQLite): hilos, deliberaciones, acciones, artefactos
│   ├── memory/               registro íntegro del Área 18 (texto literal, comprimido)
│   ├── config.yaml           capa de configuración del proyecto (Área 17)
│   ├── externals.lock        versiones fijadas de los componentes externos
│   └── portability.json      qué hace falta para abrirlo en otro equipo
├── artifacts/                salidas versionadas (informes, medios, paquetes de fabricación)
├── workspace/                lo que el usuario y el sistema editan (código, CAD, HDL, escenas)
├── inputs/                   lo que el usuario aportó, intacto
├── cas/                      blobs direccionados por contenido  ← puede excluirse del remoto
├── _quarantine/              nada se borra
└── .gitignore                generado: excluye caché, binarios grandes y credenciales
```

**Conexión con un repositorio remoto.** Con **autorización explícita del usuario**, el proyecto se conecta a un repositorio en su cuenta. Autenticación: **flujo de dispositivo con inicio de sesión del usuario** o, si él prefiere, un testigo de acceso personal que **el sistema no almacena**: lo guarda el gestor de credenciales del sistema operativo (`libsecret`/`Credential Manager`) y el sistema lo pide por su nombre. Coherente con §I.3: aquí tampoco hay claves en ficheros.

Operaciones: crear el repositorio remoto si no existe, `push`, `pull`, ver el estado (`adelantado`/`atrasado`/`en conflicto`) en el carril, y resolver conflictos con una vista de comparación en el lienzo. **Regla dura:** el sistema **nunca** hace `push` automático; siempre lo propone como acción con su radio de impacto y su resumen de qué se va a subir.

**Tres controles antes de subir nada:**
1. **`CTL-9 · barrido de secretos`.** Antes de cada `push` se analiza lo que va a subirse buscando testigos, claves privadas, ficheros de credenciales y cadenas de conexión, con reglas de patrón y de entropía. Un hallazgo **bloquea** el `push`, marca el fichero y lo explica. No hay opción de «subir igualmente» sin escribir un motivo que queda en la auditoría.
2. **`CTL-1` sigue vigente** — nada de lo marcado como volcado de dispositivo, BIOS, firmware o ROM entra en el remoto, aunque esté en la carpeta; el `.gitignore` generado lo excluye y el barrido lo confirma.
3. **Tamaño y contenido.** El almacén de blobs se excluye por defecto (puede ser de gigabytes); lo que se sube es el estado, la memoria, la configuración y los artefactos. Si el usuario quiere llevarse los blobs, se le ofrece exportar un paquete aparte, no inflar el repositorio.

**Portabilidad verificada.** `project_portability_check` produce `portability.json` y responde a la única pregunta que importa: *¿esto se abre en otro equipo?* Comprueba que la versión de esquema es compatible, que todos los componentes externos fijados en `externals.lock` existen o se pueden obtener, que ninguna ruta absoluta del equipo de origen se ha colado en la configuración, y que los artefactos referenciados están presentes o marcados como excluidos a propósito. Al clonar en otro equipo, el sistema lee ese fichero y, si falta algo, **lo dice antes de abrir** con la lista y el comando de instalación de cada pieza.

**Lo que viaja y lo que no.** Viaja: los hilos, las deliberaciones íntegras con su memoria literal, la configuración del proyecto, los artefactos, el espacio de trabajo y las entradas. No viaja: las credenciales (están en el gestor del sistema operativo), las cuotas observadas (son del equipo y de la cuenta), el caché, los blobs grandes salvo petición, y las rutas locales de las herramientas. **La consecuencia práctica: al clonar en otro equipo, la conversación completa está ahí y se puede continuar en el turno siguiente**, con la salvedad de que las inteligencias son de nube y dependen de la cuenta y de la cuota de ese equipo.

Tabla de paridad:

| Elemento | Impl. Windows | Impl. Linux |
|---|---|---|
| Ejecutable | `MagiSystem.exe` (instalador y portátil) | AppImage y `.deb` |
| Canal de interfaz | Tubería con nombre, descriptor restringido al usuario | Socket Unix `0600` |
| Instancia única | Mutex nombrado | `flock` |
| Mensajería nativa | Manifiesto en el registro (`HKCU`) apuntando al ejecutable | Manifiesto en `~/.mozilla/native-messaging-hosts/` y `~/.config/google-chrome/NativeMessagingHosts/` |
| Credenciales del repositorio | Administrador de credenciales de Windows | `libsecret`; si no hay sesión de escritorio, fichero `0600` con aviso |
| Git | `pygit2` embebido; no depende del `git` del sistema | ídem |

### 21.5 Algoritmos

**A21-1 — Arranque sin puertos y con instancia única.**
```
1. adquirir mutex/flock; si ya existe → enviar argumentos a la instancia viva por el canal y salir
2. crear canal (tubería/socket) con permisos del usuario; generar testigo de sesión en memoria
3. lanzar el núcleo; la vista embebida se conecta al canal con el testigo
4. VERIFICACIÓN OBLIGATORIA: enumerar los puertos que escucha el proceso → debe ser CONJUNTO VACÍO
     para la interfaz; los únicos permitidos son los de componentes externos declarados (Área 19),
     y siempre en bucle local. Cualquier otro → abortar el arranque y registrar
5. deshabilitar la navegación externa de la vista y la apertura de ventanas emergentes
```

**A21-2 — Emparejamiento y mensaje de la extensión.**
```
1. la extensión abre el canal de mensajería nativa; el sistema lee su identificador de origen
2. si no está en ext_pairing → diálogo con navegador e identificador; el usuario acepta o rechaza
3. cada mensaje se valida contra su esquema; tamaño máximo 8 MB; se rechaza cualquier campo no previsto
4. el contenido entra SIEMPRE por la cascada del Área 15, nunca directo al modelo
5. el ejecutable responde únicamente: recibido, identificador del adjunto y estado (abierto/proyecto/espera)
6. caso límite: llega un mensaje sin ventana abierta → se encola y se muestra al abrir; no se procesa a ciegas
```

**A21-3 — Sincronización segura con el repositorio.**
```
1. calcular el conjunto de ficheros a subir según .gitignore generado
2. CTL-9: barrido de secretos por patrón y entropía sobre ese conjunto; hallazgo → BLOQUEO con lista
3. CTL-1: comprobar origin_class de todo artefacto incluido; volcados y firmware → excluidos
4. estimar tamaño; si supera 200 MB o el remoto tiene límite menor → proponer excluir blobs y explicar
5. proponer la acción con su resumen (ficheros, tamaño, mensaje del commit) → confirmación del usuario
6. push; registrar en repo_sync_log; actualizar portability.json
7. al clonar en otro equipo: leer portability.json ANTES de abrir; si falta algo, listarlo con su
     comando de instalación y permitir abrir en modo lectura mientras tanto
8. conflictos: nunca se resuelven solos; se muestran en el lienzo con comparación y el usuario decide
```

### 21.6 Integración con el debate popperiano

Afirmaciones: «el ejecutable no expone ningún puerto de interfaz», «este proyecto se abre en otro equipo», «no se ha subido ningún secreto». Evidencia admisible: el análisis de puertos, el resultado de clonar en una máquina limpia y abrir, y el informe del barrido de secretos. Refutación más potente: **clonar el proyecto en un contenedor limpio y no poder abrirlo** — automática y bloqueante; y **encontrar un secreto en el historial del repositorio**, que además obliga a rotarlo y a reescribir el historial, y por eso el barrido es previo y no posterior. Invocación: antes de cada publicación del ejecutable y antes del primer `push` de cada proyecto.

### 21.7 Costos, latencia y recursos

Arranque en frío hasta ventana usable ≤ 4,0 s (objetivo heredado del §0.3, ahora sin carga de modelos, lo que lo hace holgado). Canal de interfaz: latencia ≤ 1,5 ms por mensaje, muy por debajo del WebSocket que sustituye. Extensión: ≤ 12 MB de memoria, sin actividad hasta que el usuario pulsa. Instalador ≤ 120 MB. Proyecto en disco: `.magi/` ronda 5–40 MB sin blobs; el `cas/` es lo que crece y por eso se excluye del remoto. Barrido de secretos: ≈ 0,9 s por cada 100 MB. **Salto del debate:** las operaciones de proyecto son R1 salvo el `push`, que es **R2** (efecto fuera del equipo, reversible con esfuerzo) y por tanto exige veredicto y confirmación. **Caché:** el barrido de secretos por hash de fichero.

### 21.8 Calidad y pruebas

| Caso | Criterio de éxito |
|---|---|
| Camino feliz | Instalar, abrir, crear proyecto, trabajar, cerrar y reabrir: estado íntegro, 20/20 |
| **Ejecutable sin puertos de interfaz** | Análisis de puertos del proceso: **conjunto vacío** para la interfaz en 10/10 arranques; con un puerto forzado, el arranque **aborta** |
| **No se abre por la web** | Intentar abrir cualquier dirección local del sistema en tres navegadores: **nada responde**, 10/10 |
| Instancia única | Lanzar 5 copias: una sola ventana, argumentos entregados, 10/10 |
| Extensión: emparejamiento | Extensión no emparejada rechazada 10/10; emparejada tras confirmación, funcional |
| Extensión: superficie | Una página web maliciosa intenta hablar con el ejecutable: **imposible** (la mensajería nativa no es alcanzable desde una página), verificado con página de prueba |
| Extensión: flujo | Enviar página, selección y captura: los tres llegan y entran por el Área 15, 20/20 |
| **Portabilidad real** | Clonar el proyecto en un **contenedor limpio** con el sistema recién instalado y **continuar la conversación en el turno siguiente**: 10/10, con la memoria íntegra disponible |
| Portabilidad incompleta | Proyecto que depende de una herramienta ausente: se declara **antes de abrir**, con la lista y el comando, 10/10 |
| **CTL-9 secretos** | 30 ficheros con credenciales sembradas de 10 formatos distintos: 30/30 bloqueados; 0 falsos positivos sobre 300 ficheros limpios |
| CTL-1 en el repositorio | Volcado de firmware en la carpeta: excluido del `push` y detectado por el barrido, 10/10 |
| Sin `push` automático | 50 sesiones de trabajo: **0 publicaciones sin confirmación explícita** |
| Conflictos | Editar el mismo fichero en dos equipos: conflicto mostrado, nunca resuelto solo, 10/10 |
| Consenso / desacuerdo | Sobre «se abre en otro equipo»: con el clon funcionando, `survives` ≥ 90; con un fallo de apertura, `falsified` aunque funcione en el equipo de origen |

### 21.9 Modos de fallo y degradación

| Fallo | Detección | Efecto | Respuesta | Estado |
|---|---|---|---|---|
| Vista embebida ausente en el sistema | Preflight | No hay interfaz | Instalador la instala; si no puede, mensaje con el paquete exacto que falta | Bloqueado, explicado |
| Canal ocupado por una instancia zombi | Fallo al crear | No arranca | Detectar el proceso huérfano, ofrecer cerrarlo; nunca abrir un segundo canal | Recuperado |
| Mensajería nativa no registrada | La extensión no conecta | Sin extensión | Reparar el registro desde Configuración con un botón; se explica qué hace | Degradado |
| Repositorio remoto inaccesible | Error de red o de credencial | Sin sincronización | El trabajo local sigue; se acumulan cambios y se avisa de cuántos | Degradado |
| **Fallo parcial (el peor): el proyecto clona pero le falta memoria** | Comprobación de la cadena del Área 18 al abrir | Continuidad falsa | Se declara **al abrir**, se identifica qué elementos faltan, y las conclusiones afectadas dejan de ser citables | Seguro |
| Secreto ya subido en un commit anterior | Barrido histórico al conectar | Credencial expuesta | Aviso destacado con instrucciones de rotación; el sistema **no** reescribe el historial por su cuenta | Explicado |
| Sin red | — | Sin sincronización | Todo el trabajo local intacto | Operativo |

### 21.10 Riesgos y mitigaciones

Subir una credencial a un repositorio (media / **crítico** → CTL-9 previo, `.gitignore` generado, y aviso de rotación si ya ocurrió). Una página web que suplanta a la extensión (baja / alto → mensajería nativa con manifiesto e identificadores declarados; no hay puerto que atacar). Proyectos que sólo funcionan en el equipo donde nacieron (alta / alto → `portability.json` y la prueba de clonado en contenedor limpio, que es bloqueante). Repositorios que crecen sin control (alta / medio → blobs excluidos por defecto y aviso de tamaño). Confusión entre carpeta de proyecto y espacio de trabajo del usuario (media / medio → estructura declarada y `inputs/` intacto). Falsa sensación de que «no se abre por la web» (media / medio → verificado por análisis de puertos y por intento real en tres navegadores, no por afirmación).

### 21.11 Prerrequisitos y estado de construibilidad

**🟢 CONSTRUIBLE-YA:** Tauri 2.x con Rust 1.79+, componente de vista web del sistema, `pygit2` 1.15, gestor de credenciales del sistema operativo, y las API de mensajería nativa de los navegadores. **🟡 REQUIERE-PRERREQUISITO:** una cuenta del usuario en el servicio de repositorios para el remoto; y, si se quiere distribuir la extensión, alta en las tiendas correspondientes (la instalación manual en modo desarrollador no lo exige). **🔴** ninguno.

### 21.12 Hoja de ruta, métricas y pasos verificables

**Fases:** MVP (ejecutable con canal sin puertos, instancia única, proyecto como carpeta con repositorio local) → v1 (extensión con emparejamiento y los cuatro flujos, remoto con CTL-9) → completo (portabilidad verificada por clonado en limpio, resolución de conflictos en el lienzo, variante portátil).

- **P21.a Ejecutable.** P21.a.1 canal sin TCP — **PV-21.a.1**: latencia ≤ 1,5 ms y permisos correctos. P21.a.2 sin puertos de interfaz — **PV-21.a.2**: conjunto vacío, 10/10; aborto si se fuerza uno. P21.a.3 no abrible por navegador — **PV-21.a.3**: nada responde en tres navegadores.
- **P21.b Extensión.** P21.b.1 mensajería nativa y emparejamiento — **PV-21.b.1**: no emparejada rechazada 10/10. P21.b.2 los cuatro flujos — **PV-21.b.2**: 20/20 llegan y entran por el Área 15. P21.b.3 superficie — **PV-21.b.3**: página maliciosa no puede alcanzar el ejecutable.
- **P21.c Proyecto.** P21.c.1 estructura y repositorio local — **PV-21.c.1**: creación, commit inicial y `.gitignore` correcto. P21.c.2 CTL-9 — **PV-21.c.2**: 30/30 secretos bloqueados, 0 falsos positivos en 300. P21.c.3 sin publicación automática — **PV-21.c.3**: 0 en 50 sesiones.
- **P21.d Portabilidad.** P21.d.1 informe — **PV-21.d.1**: detecta 100 % de dependencias ausentes. P21.d.2 **clonado en limpio** — **PV-21.d.2**: 10/10 proyectos clonados continúan la conversación con memoria íntegra.

Métricas de salida: 0 puertos de interfaz, 0 secretos publicados, 0 publicaciones sin confirmación, y 100 % de proyectos que continúan en otro equipo tras clonar.

---

# Parte III — Artefactos transversales

## T1 Árbol de directorios completo

```
magi/
├── core/                          núcleo Python: único dueño del estado
│   ├── kernel.py                  bucle principal, supervisión, API pública
│   ├── bus.py                     bus de eventos tipado (MagiBus)
│   ├── hal/                       capa de abstracción de SO (10 interfaces, §I.1)
│   ├── store/                     persistencia: SQLite, CAS, DuckDB, índice vectorial
│   ├── prov/                      grafo de procedencia y consultas recursivas
│   ├── policy/                    motor de capacidades y carga de política YAML
│   ├── sched/                     planificador con prioridades y presupuesto de recursos
│   ├── jobs/                      WAL de trabajos y unidades reanudables
│   ├── providers/                 clientes de inferencia (local, Claude Code, HF)
│   ├── obs/                       logging estructurado, trazas OTel a fichero, métricas
│   ├── rpc/                       servidor WebSocket y canal E-STOP independiente
│   ├── supervisor/                gestión de procesos efímeros de toolchain
│   └── artifacts/                 registro y empaquetado de artefactos (CTL-1)
├── modules/                       módulos de dominio, uno por área
│   ├── forensic/                  Área 1: normalización, teselado, rasgos, detectores
│   ├── contrast/                  Área 2: corpus, índice híbrido, alineación, dictamen
│   ├── debate/                    Área 3: orquestador, validadores, rúbrica, guardas
│   ├── devices/                   Área 4: enumeración, modos, ADB/scrcpy, telemetría
│   ├── re/                        Área 5: Ghidra, triaje, refinamiento, emuladores, síntesis
│   │   ├── ghidra_scripts/        scripts Java/Python del analizador headless
│   │   ├── emulators/             matriz de arquitecturas, clasificador, libro mayor
│   │   └── synth/                 especificación intermedia y clean room (CTL-3)
│   ├── resilience/                Área 6: registro de proveedores, circuito, reconciliación
│   ├── prompts/                   Área 7: compilador Jinja2, gramáticas, reparación
│   ├── executor/                  Área 8: ontología de acciones, preflight, postcondiciones
│   ├── fabrication/               Área 9: impresora, CAD, HDL, PCB, firmware, medición
│   │   ├── printer/               emisor de G-Code, dialectos, seguridad térmica, Moonraker
│   │   ├── cad/                   plantillas paramétricas y verificación geométrica
│   │   ├── hdl/                   flujo Verilog, formal, síntesis, P&R, OpenLane
│   │   ├── pcb/                   SKiDL, kicad-cli, paquete de fabricación
│   │   ├── firmware/              toolchains, PlatformIO, flasheo y rescate
│   │   └── metrology/             instrumentos, sigrok, mediciones, convergencia
│   ├── invention/                 Área 11: esquema, operadores, MAP-Elites, arte previo
│   ├── capabilities/              Área 12: bloques C01–C39, guardas y pruebas de posesión
│   ├── mcp/                       servidor MCP local que expone las herramientas del laboratorio
│   ├── lang/                      legibilidad, detección de falacias, normalización de texto
│   └── logic/                     formalización SAT/SMT y verificación deductiva
├── gui/                           aplicación Tauri 2.x + React 18 + TypeScript 5
│   ├── src-tauri/                 shell Rust: ventana, atajos, sidecar, canal E-STOP
│   ├── src/                       componentes, paneles, slices de estado, workers
│   │   ├── panels/                los 13 paneles del catálogo §10.4
│   │   ├── debate/                vista de turnos, grafo React Flow, marcador
│   │   ├── policy/                editor de política de capacidades con validación en vivo
│   │   └── types/generated.ts     tipos generados desde los esquemas pydantic (no editar)
│   └── public/                    recursos estáticos
├── prompts/                       Área 7: base, roles, dominios, capacidades, contratos, gramáticas
├── schemas/                       JSON Schema canónicos compartidos núcleo↔GUI
├── profiles/                      perfiles versionados de dispositivos y procesos
│   ├── devices/                   VID/PID → perfil, modos y prioridades
│   ├── printers/                  perfiles de máquina y dialectos de G-Code
│   ├── slicer/                    configuraciones de PrusaSlicer y CuraEngine
│   ├── instruments/               tramas y escalas de multímetros y analizadores
│   └── conformance/               suites de conformidad por consola (Área 5)
├── cad/templates/                 plantillas paramétricas CadQuery y OpenSCAD
├── hw/                            diseños de hardware del usuario (HDL y PCB)
├── fw/                            proyectos de firmware (PlatformIO)
├── data/                          matriz TRIZ, banco de conceptos, analogías, referencias
├── scripts/                       generadores (tipos, gramáticas), utilidades, mantenimiento
├── packaging/                     instaladores, reglas udev, manifiestos, unidades systemd
│   ├── linux/udev/                99-magi.rules (§4.4)
│   ├── linux/polkit/              acciones y reglas de polkit
│   └── windows/                   manifiesto del broker, plantilla NSIS
├── tests/                         pruebas
│   ├── gates/                     puertas de verificación PV-n.x.y (§I.5)
│   ├── capabilities/              las 39 pruebas de posesión
│   ├── prompts/bench/             banco de evaluación de prompts (120 casos)
│   ├── fakes/                     simuladores: marlin_sim, device_sim, provider_sim
│   └── integration/               escenarios extremo a extremo
├── bench/superiority/             banco de tareas con solución conocida (§10.7)
├── docs/                          este plan, decisiones de arquitectura, manuales
├── config/                        safety.yaml (límites duros), defaults del sistema
├── policy/                        global.yaml (política de capacidades por defecto)
├── requirements.lock              dependencias Python fijadas con hashes
├── Makefile                       objetivos: gates, capabilities, prompt-bench, build, package
└── README.md                      arranque rápido y estado de construibilidad por módulo
```

## T2 Catálogo maestro de eventos del bus

| Evento | Emisor | Consumidores | Payload (campos) | Frecuencia esperada | Criticidad |
|---|---|---|---|---|---|
| `device.attached` | modules/devices | GUI, executor, fabrication | `{device_id, vid, pid, serial_hash, profile_id, modes[], ts}` | Esporádica | Alta (persistido) |
| `device.detached` | modules/devices | GUI, executor, fabrication, jobs | `{device_id, reason, ts}` | Esporádica | Alta (persistido) |
| `telemetry.sample` | devices, fabrication | GUI (worker), store/duck | `{device_id, channel, value, unit, t_mono_ns, t_wall, seq, quality}` | Hasta 2 000/s | Baja (descartable) |
| `debate.turn` | modules/debate | GUI, obs | `{round_id, role, model_id, provider_id, tokens_in, tokens_out, latency_ms, partial?}` | 3–15/min | Media (persistido) |
| `debate.verdict` | modules/debate | executor, GUI, store | `{round_id, claim_id, outcome, score, rubric{}, required_action}` | 1–10/ronda | Alta (persistido) |
| `action.proposed` | cualquier módulo | debate (Juez), GUI | `{action_id, kind, radius, params_hash, origin{area, round_id, claim_id}}` | Esporádica | Alta (bloqueante) |
| `action.approved` | modules/debate | executor, GUI, audit | `{action_id, approver: "judge"\|"human", reason_ref, ts}` | Esporádica | Alta (bloqueante) |
| `action.executed` | modules/executor | debate, GUI, audit, store | `{action_id, exit_code, duration_ms, artifacts[], postcondition_ok}` | Esporádica | Alta (bloqueante) |
| `action.failed` | modules/executor | debate, GUI, audit | `{action_id, error_class, message, stage}` | Esporádica | Alta (bloqueante) |
| `artifact.created` | cualquier módulo | GUI, prov, store | `{artifact_id, kind, sha256, size, derivative_risk, provenance_root}` | 1–100/min | Alta (persistido) |
| `job.progress` | core/sched | GUI, obs | `{job_id, state, done_units, total_units, eta_s, message?}` | 1/s por trabajo | Media |
| `provider.degraded` | modules/resilience | GUI, debate, obs | `{provider_id, reason, capability_lost?, fallback_id}` | Esporádica | Alta (persistido) |
| `print.layer` | fabrication/printer | GUI, store | `{job_id, layer, total_layers, z_mm, eta_s, filament_mm}` | 1 por capa | Media |
| `print.fault` | fabrication/printer | executor, GUI, audit | `{job_id, kind, detail, level, telemetry_window_ref}` | Rara | **Crítica** |
| `flash.progress` | fabrication/firmware | GUI, store | `{target, phase, pct, bytes_done, bytes_total}` | 2–10/s durante flasheo | Alta |
| `inference.token` | core/providers | GUI (worker) | `{round_id?, role?, provider_id, delta, index}` | Hasta 200/s por rol | Baja (descartable) |
| `orphan.reaped` | core/supervisor | obs, audit | `{pid, argv_hash, parent_pid, ts}` | Rara | Media |
| `policy.denied` | core/policy | GUI, audit | `{module, capability, ctx_hash, reason}` | Esporádica | Alta (persistido) |
| `gate.result` | tests/gates (CI local) | GUI, obs | `{gate_id, passed, metric, threshold, duration_s}` | Por ejecución | Media |
| `measurement.recorded` | fabrication/metrology | debate, GUI, store | `{measurement_id, magnitude, value, unit, uncertainty, instrument}` | Esporádica | **Alta (evidencia tier 1)** |
| `corpus.updated` | modules/contrast | GUI, cache | `{corpus_version, norma_id, kind, chunks_added, chunks_retired}` | Esporádica | Alta (persistido) |
| `invention.derived` | modules/invention | GUI, store | `{invention_id, parent_id, operator, novelty, niche}` | 12/ronda | Media |
| `capability.requested` | cualquier módulo | policy, GUI, audit | `{module, capability, scope, purpose}` | Esporádica | Alta |
| `snapshot.created` | modules/executor | GUI, store | `{snapshot_id, action_id, tree_hash, size_bytes}` | Por acción R1/R2 | Alta |
| `estop.triggered` | gui / core/rpc / magi-estop | todos | `{source, reason, ts, actions_aborted[]}` | Rara | **Crítica (nunca se descarta)** |

## T3 Esquema completo de la base de datos

```sql
-- ============ Núcleo (Área 0) ============
PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON; PRAGMA synchronous=NORMAL;

CREATE TABLE project (
  project_id   TEXT PRIMARY KEY, slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
  created_at   TEXT NOT NULL, schema_version INTEGER NOT NULL, settings_json TEXT NOT NULL);

CREATE TABLE artifact (
  artifact_id  TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES project(project_id),
  kind         TEXT NOT NULL, sha256 TEXT NOT NULL, size_bytes INTEGER NOT NULL,
  path_rel     TEXT, created_at TEXT NOT NULL,
  tool_id      TEXT, tool_version TEXT, seed INTEGER, prompt_hash TEXT,
  model_id     TEXT, model_hash TEXT, params_hash TEXT, inputs_hash TEXT,
  derivative_risk TEXT NOT NULL DEFAULT 'none'
    CHECK (derivative_risk IN ('none','low','high')),
  origin_class TEXT NOT NULL DEFAULT 'generated'
    CHECK (origin_class IN ('generated','user_supplied','device_dump','bios','firmware','rom','web_capture')),
  UNIQUE(project_id, sha256, kind));
CREATE INDEX ix_artifact_sha    ON artifact(sha256);
CREATE INDEX ix_artifact_kind   ON artifact(project_id, kind, created_at DESC);

CREATE TABLE evidence (
  evidence_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES project(project_id),
  kind        TEXT NOT NULL CHECK (kind IN ('file_offset','execution','measurement','citation','static_analysis','computation','web_capture')),
  tier        INTEGER NOT NULL CHECK (tier BETWEEN 1 AND 5),
  locator     TEXT NOT NULL, value_json TEXT NOT NULL, tool TEXT, tool_version TEXT,
  hash        TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE INDEX ix_evidence_tier ON evidence(project_id, tier);

CREATE TABLE provenance_edge (
  edge_id  INTEGER PRIMARY KEY AUTOINCREMENT,
  src_kind TEXT NOT NULL, src_id TEXT NOT NULL,
  dst_kind TEXT NOT NULL, dst_id TEXT NOT NULL,
  relation TEXT NOT NULL CHECK (relation IN ('derives_from','cites','measured_by','approved_by','refuted_by','produced_by')),
  created_at TEXT NOT NULL);
CREATE INDEX ix_prov_dst ON provenance_edge(dst_kind, dst_id);
CREATE INDEX ix_prov_src ON provenance_edge(src_kind, src_id);

CREATE TABLE event_log (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT NOT NULL, ts TEXT NOT NULL,
  payload_json TEXT NOT NULL, critical INTEGER NOT NULL DEFAULT 0);
CREATE INDEX ix_event_topic ON event_log(topic, seq DESC);

CREATE TABLE audit_log (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL,
  actor_kind TEXT NOT NULL CHECK (actor_kind IN ('agent','human','system')), actor_id TEXT,
  action_id TEXT, kind TEXT NOT NULL, radius TEXT, params_hash TEXT,
  reason_ref TEXT, result TEXT, prev_hash TEXT NOT NULL, entry_hash TEXT NOT NULL UNIQUE);
CREATE TRIGGER trg_audit_no_update BEFORE UPDATE ON audit_log
  BEGIN SELECT RAISE(ABORT,'audit_log es append-only'); END;
CREATE TRIGGER trg_audit_no_delete BEFORE DELETE ON audit_log
  BEGIN SELECT RAISE(ABORT,'audit_log es append-only'); END;

CREATE TABLE capability_grant (
  grant_id INTEGER PRIMARY KEY AUTOINCREMENT, module TEXT NOT NULL, capability TEXT NOT NULL,
  scope_json TEXT, granted INTEGER NOT NULL, reason TEXT, ts TEXT NOT NULL);

CREATE TABLE job (
  job_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES project(project_id),
  kind TEXT NOT NULL, priority INTEGER NOT NULL, state TEXT NOT NULL
    CHECK (state IN ('QUEUED','RUNNING','PAUSED','CANCELLING','CANCELLED','DONE','FAILED','BLOCKED_ESCALATED','WAITING_MODEL')),
  req_ram_mb INTEGER, req_vram_mb INTEGER, req_disk_mb INTEGER,
  total_units INTEGER, done_units INTEGER DEFAULT 0, exclusive INTEGER DEFAULT 0,
  created_at TEXT NOT NULL, started_at TEXT, ended_at TEXT, spec_json TEXT NOT NULL);
CREATE INDEX ix_job_state ON job(state, priority);

CREATE TABLE job_unit (
  job_id TEXT NOT NULL REFERENCES job(job_id), unit_id TEXT NOT NULL,
  idx INTEGER NOT NULL, state TEXT NOT NULL CHECK (state IN ('PENDING','RUNNING','DONE','STALE','FAILED')),
  input_hash TEXT NOT NULL, output_ref TEXT, provider_id TEXT, model_id TEXT,
  prompt_hash TEXT, tokens_in INTEGER, tokens_out INTEGER, ts TEXT,
  PRIMARY KEY (job_id, unit_id));
CREATE INDEX ix_unit_state ON job_unit(job_id, state, idx);

CREATE TABLE model_run (
  run_id TEXT PRIMARY KEY, provider_id TEXT NOT NULL, model_id TEXT NOT NULL, model_hash TEXT,
  role TEXT, prompt_hash TEXT NOT NULL, params_hash TEXT NOT NULL, seed INTEGER,
  tokens_in INTEGER, tokens_out INTEGER, latency_ms INTEGER, ok INTEGER, repairs INTEGER DEFAULT 0,
  ts TEXT NOT NULL);

CREATE TABLE prompt (
  prompt_id TEXT PRIMARY KEY, name TEXT NOT NULL, semver TEXT NOT NULL,
  template_path TEXT NOT NULL, render_sha256 TEXT NOT NULL, created_at TEXT NOT NULL,
  UNIQUE(name, semver, render_sha256));

CREATE TABLE provider_quota (
  provider_id TEXT PRIMARY KEY, kind TEXT NOT NULL, declared_quota TEXT, window TEXT,
  remaining REAL, resets_at TEXT, latency_ms_ewma REAL, error_rate_ewma REAL,
  circuit_state TEXT NOT NULL DEFAULT 'closed' CHECK (circuit_state IN ('closed','open','half_open')),
  failures INTEGER DEFAULT 0, opened_at TEXT, updated_at TEXT NOT NULL);

CREATE TABLE gate_result (
  gate_id TEXT NOT NULL, run_ts TEXT NOT NULL, passed INTEGER NOT NULL,
  metric REAL, threshold REAL, duration_s REAL, detail TEXT, PRIMARY KEY (gate_id, run_ts));

-- ============ Debate (Área 3) ============
CREATE TABLE debate_round (
  round_id TEXT PRIMARY KEY, parent_round_id TEXT REFERENCES debate_round(round_id),
  project_id TEXT NOT NULL REFERENCES project(project_id),
  topic_id TEXT NOT NULL, area INTEGER NOT NULL, domain TEXT NOT NULL,
  started_at TEXT NOT NULL, ended_at TEXT, diversity TEXT CHECK (diversity IN ('full','degraded')),
  stop_reason TEXT, acta_json TEXT NOT NULL, acta_sha256 TEXT NOT NULL);
CREATE INDEX ix_round_topic ON debate_round(topic_id, started_at);

CREATE TABLE claim (
  claim_id TEXT PRIMARY KEY, round_id TEXT NOT NULL REFERENCES debate_round(round_id),
  statement TEXT NOT NULL, falsifier TEXT NOT NULL, confidence REAL NOT NULL,
  author TEXT NOT NULL, amended_from TEXT REFERENCES claim(claim_id));

CREATE TABLE refutation (
  refutation_id TEXT PRIMARY KEY, round_id TEXT NOT NULL REFERENCES debate_round(round_id),
  target_claim_id TEXT NOT NULL REFERENCES claim(claim_id),
  type TEXT NOT NULL CHECK (type IN ('empirica','logica','completitud','suposicion','normativa','reproducibilidad','coste','falsabilidad')),
  mechanism TEXT NOT NULL, reproduction_steps_json TEXT NOT NULL,
  admissible INTEGER NOT NULL, admissibility_reason TEXT,
  fingerprint TEXT NOT NULL, author TEXT NOT NULL);
CREATE INDEX ix_ref_fp ON refutation(fingerprint);

CREATE TABLE rebuttal (
  rebuttal_id TEXT PRIMARY KEY, round_id TEXT NOT NULL REFERENCES debate_round(round_id),
  target_refutation_id TEXT NOT NULL REFERENCES refutation(refutation_id),
  statement TEXT NOT NULL, concedes INTEGER NOT NULL DEFAULT 0);

CREATE TABLE verdict (
  verdict_id TEXT PRIMARY KEY, round_id TEXT NOT NULL REFERENCES debate_round(round_id),
  claim_id TEXT NOT NULL REFERENCES claim(claim_id),
  outcome TEXT NOT NULL CHECK (outcome IN ('survives','falsified','amended','unfalsifiable','undecided')),
  score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100), rubric_json TEXT NOT NULL,
  rationale TEXT NOT NULL, required_action_json TEXT, human_override INTEGER DEFAULT 0);
CREATE INDEX ix_verdict_claim ON verdict(claim_id);

-- ============ Acciones y ejecución (Área 8) ============
CREATE TABLE action (
  action_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES project(project_id),
  kind TEXT NOT NULL, radius TEXT NOT NULL CHECK (radius IN ('R0','R1','R2','R3')),
  params_json TEXT NOT NULL, origin_round_id TEXT, origin_claim_id TEXT,
  state TEXT NOT NULL CHECK (state IN ('proposed','approved','rejected','awaiting_human','preflight_failed','running','executed','failed','reverted')),
  preconditions_json TEXT, postconditions_json TEXT, revert_json TEXT,
  approved_by TEXT, approved_at TEXT, created_at TEXT NOT NULL);
CREATE INDEX ix_action_state ON action(state, radius);

CREATE TABLE execution_record (
  exec_id TEXT PRIMARY KEY, action_id TEXT NOT NULL REFERENCES action(action_id),
  snapshot_before TEXT, argv_json TEXT, env_hash TEXT, stdout_ref TEXT, stderr_ref TEXT,
  exit_code INTEGER, duration_ms INTEGER, artifacts_json TEXT, telemetry_ref TEXT,
  postcondition_ok INTEGER, error_class TEXT, ts TEXT NOT NULL);

CREATE TABLE snapshot (
  snapshot_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, action_id TEXT,
  tree_hash TEXT NOT NULL, size_bytes INTEGER, created_at TEXT NOT NULL);

CREATE TABLE revert_log (
  revert_id INTEGER PRIMARY KEY AUTOINCREMENT, action_id TEXT NOT NULL REFERENCES action(action_id),
  ok INTEGER NOT NULL, detail TEXT, ts TEXT NOT NULL);

-- ============ Dispositivos y medición (Áreas 4 y 9) ============
CREATE TABLE device (
  device_id TEXT PRIMARY KEY, vid TEXT, pid TEXT, serial_hash TEXT, profile_id TEXT,
  class_code TEXT, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL, descriptors_json TEXT);

CREATE TABLE device_session (
  session_id TEXT PRIMARY KEY, device_id TEXT NOT NULL REFERENCES device(device_id),
  mode TEXT NOT NULL, opened_at TEXT NOT NULL, closed_at TEXT, close_reason TEXT);

CREATE TABLE machine_profile (
  profile_id TEXT PRIMARY KEY, device_id TEXT REFERENCES device(device_id),
  firmware_family TEXT NOT NULL, firmware_version TEXT, dialect TEXT NOT NULL,
  volume_x REAL, volume_y REAL, volume_z REAL, max_temp_hotend REAL, max_temp_bed REAL,
  max_feedrate REAL, caps_json TEXT, created_at TEXT NOT NULL);

CREATE TABLE print_job (
  print_job_id TEXT PRIMARY KEY, job_id TEXT REFERENCES job(job_id),
  profile_id TEXT NOT NULL REFERENCES machine_profile(profile_id),
  gcode_sha256 TEXT NOT NULL, total_lines INTEGER, current_line INTEGER, current_layer INTEGER,
  total_layers INTEGER, state TEXT NOT NULL, started_at TEXT, ended_at TEXT, fault_json TEXT);

CREATE TABLE flash_record (
  flash_id TEXT PRIMARY KEY, action_id TEXT REFERENCES action(action_id),
  target TEXT NOT NULL, programmer TEXT NOT NULL, dump_sha256 TEXT, image_sha256 TEXT NOT NULL,
  readback_sha256 TEXT, verified INTEGER, integrity TEXT DEFAULT 'ok'
    CHECK (integrity IN ('ok','unknown','corrupt')), ts TEXT NOT NULL);

CREATE TABLE measurement (
  measurement_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES project(project_id),
  magnitude TEXT NOT NULL, value REAL NOT NULL, unit TEXT NOT NULL, uncertainty REAL,
  instrument_json TEXT NOT NULL, method TEXT NOT NULL, conditions_json TEXT,
  artifact_ref TEXT, operator TEXT NOT NULL CHECK (operator IN ('system','human')),
  ts TEXT NOT NULL);
CREATE INDEX ix_meas_mag ON measurement(project_id, magnitude, ts DESC);

-- ============ Forense (Área 1) ============
CREATE TABLE forensic_dossier (
  dossier_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES project(project_id),
  source_sha256 TEXT NOT NULL, page_count INTEGER, baseline_weak INTEGER DEFAULT 0,
  custody_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE forensic_page (
  page_id TEXT PRIMARY KEY, dossier_id TEXT NOT NULL REFERENCES forensic_dossier(dossier_id),
  page_no INTEGER NOT NULL, dpi_effective REAL, deskew_deg REAL, margins_json TEXT,
  halftone_json TEXT, noise_json TEXT, page_vector BLOB, features_ref TEXT, flags_json TEXT);
CREATE TABLE forensic_block (
  block_id TEXT PRIMARY KEY, page_id TEXT NOT NULL REFERENCES forensic_page(page_id),
  role TEXT, bbox_json TEXT NOT NULL, alignment TEXT, ink_density REAL);
CREATE TABLE forensic_line (
  line_id TEXT PRIMARY KEY, block_id TEXT NOT NULL REFERENCES forensic_block(block_id),
  baseline_y REAL, bbox_json TEXT, indent_mm REAL, leading_mm REAL, font_json TEXT, text_hint TEXT);
CREATE TABLE forensic_finding (
  finding_id TEXT PRIMARY KEY, dossier_id TEXT NOT NULL REFERENCES forensic_dossier(dossier_id),
  detector TEXT NOT NULL CHECK (detector IN ('D1','D2','D3','D4','D5','D6','D7','D8','D9')),
  page_id TEXT, statistic REAL, threshold REAL, confidence REAL,
  evidence_json TEXT NOT NULL, claim_id TEXT REFERENCES claim(claim_id),
  verdict_id TEXT REFERENCES verdict(verdict_id));

-- ============ Contraste normativo (Área 2) ============
CREATE TABLE corpus_doc (
  corpus_doc_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES project(project_id),
  kind TEXT NOT NULL CHECK (kind IN ('legal','technical')), norma_id TEXT, title TEXT,
  source_ref TEXT, sha256 TEXT NOT NULL, ingested_at TEXT NOT NULL);
CREATE TABLE corpus_version (
  corpus_version TEXT PRIMARY KEY, corpus_doc_id TEXT NOT NULL REFERENCES corpus_doc(corpus_doc_id),
  vigencia_desde TEXT, vigencia_hasta TEXT, modificatorias_json TEXT, created_at TEXT NOT NULL);
CREATE TABLE corpus_chunk (
  chunk_id TEXT PRIMARY KEY, corpus_version TEXT NOT NULL REFERENCES corpus_version(corpus_version),
  locator TEXT NOT NULL, hierarchy_json TEXT, numeral TEXT, literal TEXT,
  text TEXT NOT NULL, text_hash TEXT NOT NULL, tokens INTEGER,
  unit_kind TEXT CHECK (unit_kind IN ('articulo','numeral','literal','disposicion','seccion','tabla','ecuacion','parrafo')));
CREATE INDEX ix_chunk_locator ON corpus_chunk(corpus_version, locator);
CREATE TABLE doc_claim (
  doc_claim_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, source_page_id TEXT,
  type TEXT NOT NULL, statement TEXT NOT NULL, verbatim TEXT NOT NULL,
  location_json TEXT NOT NULL, numeric_json TEXT);
CREATE TABLE alignment (
  alignment_id TEXT PRIMARY KEY, doc_claim_id TEXT NOT NULL REFERENCES doc_claim(doc_claim_id),
  relation TEXT NOT NULL CHECK (relation IN ('conforme','conforme-con-observacion','insuficiente','excesivo','contradictorio','nulo-de-pleno-derecho','ambiguo','no-aplicable','sin-referencia-en-corpus')),
  severity TEXT NOT NULL, references_json TEXT NOT NULL, reasoning TEXT,
  numeric_check_json TEXT, citation_validation_json TEXT NOT NULL,
  recommendation TEXT, verdict_id TEXT REFERENCES verdict(verdict_id));
CREATE TABLE opinion_report (
  report_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, artifact_id TEXT REFERENCES artifact(artifact_id),
  as_of TEXT NOT NULL, findings_count INTEGER, max_severity TEXT, created_at TEXT NOT NULL);

-- ============ Ingeniería inversa (Área 5) ============
CREATE TABLE binary (
  binary_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, sha256 TEXT NOT NULL UNIQUE,
  arch TEXT, format TEXT, size_bytes INTEGER, entropy REAL, source_device_id TEXT,
  triage_score REAL, packed INTEGER DEFAULT 0);
CREATE TABLE decompiled_function (
  func_id TEXT PRIMARY KEY, binary_id TEXT NOT NULL REFERENCES binary(binary_id),
  addr TEXT NOT NULL, name TEXT, size INTEGER, cc TEXT, c_sha256 TEXT,
  readability_score REAL, decompile_ms INTEGER, failed INTEGER DEFAULT 0,
  UNIQUE(binary_id, addr));
CREATE TABLE refinement (
  refinement_id TEXT PRIMARY KEY, func_id TEXT NOT NULL REFERENCES decompiled_function(func_id),
  hypothesis_kind TEXT NOT NULL, statement TEXT NOT NULL, falsifier TEXT NOT NULL,
  confidence REAL, verified INTEGER DEFAULT 0, oracle_ref TEXT, claim_id TEXT REFERENCES claim(claim_id));
CREATE TABLE arch_fact (
  fact_id TEXT PRIMARY KEY, console TEXT NOT NULL, dimension TEXT NOT NULL, value TEXT NOT NULL,
  source_kind TEXT NOT NULL CHECK (source_kind IN ('documentacion_publica','codigo_emulador_libre','medicion_en_hardware','decompilacion')),
  source_ref TEXT NOT NULL, confidence REAL NOT NULL, verified_by TEXT,
  UNIQUE(console, dimension));
CREATE TABLE module_classification (
  module_path TEXT NOT NULL, src_root TEXT NOT NULL,
  layer TEXT NOT NULL CHECK (layer IN ('agnostic','semi_agnostic','console_specific')),
  confidence REAL NOT NULL, isolated_build_ok INTEGER, rationale TEXT,
  PRIMARY KEY (src_root, module_path));
CREATE TABLE ledger_row (
  ledger_id TEXT NOT NULL, module TEXT NOT NULL, layer TEXT NOT NULL,
  verdict TEXT NOT NULL CHECK (verdict IN ('reutilizable-tal-cual','reutilizable-con-parametros','reescribir-con-la-misma-forma','reescribir-de-cero','no-aplica')),
  rationale TEXT NOT NULL, evidence_refs_json TEXT NOT NULL,
  effort_pd REAL, effort_actual_pd REAL, risk TEXT, PRIMARY KEY (ledger_id, module));
CREATE TABLE divergence (
  divergence_id TEXT PRIMARY KEY, run_ref TEXT NOT NULL, ref_emulator TEXT NOT NULL,
  cand_emulator TEXT NOT NULL, first_index INTEGER NOT NULL, pc TEXT, detail_json TEXT NOT NULL,
  refutation_id TEXT REFERENCES refutation(refutation_id));
CREATE TABLE intermediate_spec (
  spec_id TEXT PRIMARY KEY, binary_id TEXT REFERENCES binary(binary_id),
  scope TEXT NOT NULL, sha256 TEXT NOT NULL, invariants_count INTEGER, created_at TEXT NOT NULL);
CREATE TABLE clean_room_ledger (
  entry_id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
  space TEXT NOT NULL CHECK (space IN ('analysis','impl')), saw_hash TEXT NOT NULL, ts TEXT NOT NULL);

-- ============ Invención (Área 11) ============
CREATE TABLE invention (
  invention_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, version INTEGER NOT NULL,
  title TEXT NOT NULL, problem_json TEXT NOT NULL, principle_json TEXT NOT NULL,
  domain TEXT NOT NULL, assumptions_json TEXT, constraints_json TEXT, resources_json TEXT,
  trl INTEGER, killer_hypothesis TEXT NOT NULL, cheapest_experiment_json TEXT NOT NULL,
  niche TEXT, created_at TEXT NOT NULL);
CREATE TABLE invention_param (
  invention_id TEXT NOT NULL REFERENCES invention(invention_id), name TEXT NOT NULL,
  value REAL, unit TEXT NOT NULL, range_min REAL, range_max REAL, sensitivity TEXT,
  PRIMARY KEY (invention_id, name));
CREATE TABLE invention_derivation (
  derivation_id TEXT PRIMARY KEY, parent_id TEXT NOT NULL REFERENCES invention(invention_id),
  child_id TEXT NOT NULL REFERENCES invention(invention_id),
  operator TEXT NOT NULL CHECK (operator IN ('combinatoria','traslacion_dominio','inversion_supuestos','fusion','escalado','sustraccion','triz','biomimesis')),
  novelty_vs_base REAL, novelty_vs_set REAL, generation INTEGER);
CREATE TABLE prior_art_ref (
  ref_id TEXT PRIMARY KEY, invention_id TEXT NOT NULL REFERENCES invention(invention_id),
  source TEXT NOT NULL, identifier TEXT, url TEXT, captured_sha256 TEXT, captured_at TEXT,
  claim_text TEXT, similarity REAL);
CREATE TABLE patentability_screen (
  screen_id TEXT PRIMARY KEY, invention_id TEXT NOT NULL REFERENCES invention(invention_id),
  novelty TEXT, inventive_step TEXT, industrial_application TEXT, route TEXT,
  rationale TEXT NOT NULL, disclaimer_present INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL);
CREATE TABLE invention_score (
  invention_id TEXT PRIMARY KEY REFERENCES invention(invention_id),
  impacto INTEGER, viabilidad INTEGER, novedad INTEGER, coste_validacion INTEGER,
  riesgo_regulatorio INTEGER, total INTEGER, verdict_id TEXT REFERENCES verdict(verdict_id));

-- ============ Fabricación digital (Área 9) ============
CREATE TABLE geometry_artifact (
  geom_id TEXT PRIMARY KEY, artifact_id TEXT REFERENCES artifact(artifact_id),
  template TEXT NOT NULL, params_json TEXT NOT NULL, manifold INTEGER, volume_mm3 REAL,
  bbox_json TEXT, min_wall_mm REAL, overhang_pct REAL, bed_contact_mm2 REAL);
CREATE TABLE hdl_run (
  hdl_run_id TEXT PRIMARY KEY, design TEXT NOT NULL, stage TEXT NOT NULL,
  tool TEXT NOT NULL, tool_version TEXT NOT NULL, ok INTEGER, metrics_json TEXT,
  report_ref TEXT, ts TEXT NOT NULL);
CREATE TABLE fab_package (
  package_id TEXT PRIMARY KEY, design TEXT NOT NULL, artifact_id TEXT REFERENCES artifact(artifact_id),
  erc_ok INTEGER, drc_ok INTEGER, outputs_json TEXT NOT NULL, created_at TEXT NOT NULL);
```

Notas de integridad: toda tabla de dominio que produzca conclusiones enlaza a `claim`/`verdict`, lo que permite la consulta de control **"artefactos sin veredicto"** que se usa como puerta de calidad (`SELECT ... WHERE verdict_id IS NULL` debe devolver 0 filas antes de exportar cualquier informe). Las series de alta frecuencia (`telemetry.sample`, `print_sample`) **no** viven en SQLite: se escriben en Parquet particionado y se consultan con DuckDB.

## T4 Matriz de trazabilidad Áreas ↔ Capacidades C01–C39

| Capacidad | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C01 matemática pura | | | | | | ✔ | | | | ✔ | | ✔ |
| C02 códigos algebraicos | | | | | | ✔ | | | | ✔ | | |
| C03 teoría de la información | | ✔ | | | | ✔ | | | | ✔ | | ✔ |
| C04 juegos combinatorios | | | | | | | | | | | | ✔ |
| C05 aprendizaje automático | | ✔ | ✔ | | | | | | | | | ✔ |
| C06 corrección de errores | | | | | ✔ | | | | | ✔ | | |
| C07 minería de Big Data | | | | | ✔ | ✔ | | | | ✔ | | |
| C08 psicometría (con guarda) | | | | | | | | | | | | ✔ |
| C09 modelado estadístico | | ✔ | ✔ | | | | | | | ✔ | | ✔ |
| C10 reconocimiento de voz | | | | | ✔ | | | | | | ✔ | |
| C11 resiliencia cognitiva | ✔ | | | | | | ✔ | | ✔ | | | |
| C12 cálculo tensorial | | | | | | | | | | ✔ | | ✔ |
| C13 experimentos mentales | | | | | | | | | | | | ✔ |
| C14 patrones unificadores | | | | | | | | | | | | ✔ |
| C15 divulgación accesible | | | ✔ | | | | | | | | ✔ | ✔ |
| C16 taxonomía y sistematización | | ✔ | ✔ | | | ✔ | | | | ✔ | | ✔ |
| C17 lógica formal deductiva | | | ✔ | ✔ | | ✔ | | | | ✔ | | |
| C18 parsimonia y nominalismo | | | | ✔ | | ✔ | | | | | | ✔ |
| C19 dialéctica y mayéutica | | | ✔ | ✔ | | ✔ | | | | | | ✔ |
| C20 ciclos macroeconómicos | | | | | | | | | | | | ✔ |
| C21 política monetaria | | | | | | | | | | | | ✔ |
| C22 reflexividad (con guarda) | | | | | | | | | | | | ✔ |
| C23 arbitraje (con guarda) | | | | | | | | | | | | ✔ |
| C24 paridad de riesgo | | | | | | | | | | | | ✔ |
| C25 principios de decisión | | | | ✔ | | | | | ✔ | | | ✔ |
| C26 asignación de capital | | | | | | | | | | | | ✔ |
| C27 tendencias y ventajas | | | | | | | | | | | | ✔ |
| C28 disciplina operativa | | | | | | | | | ✔ | | | ✔ |
| C29 analogías financieras | | | | | | | | | | | ✔ | ✔ |
| C30 coordinación de talento | ✔ | | | ✔ | | | ✔ | | | | | |
| C31 interfaces lúdicas | | | | | | | | | | | ✔ | |
| C32 sinergia hardware/software | | | | | ✔ | | | | | ✔ | ✔ | |
| C33 dirección cinematográfica | | | | | | | | | | | ✔ | ✔ |
| C34 ilustración de fantasía | | ✔ | | | | | | | | | | ✔ |
| C35 tropos y trauma | | | | | | | | | | | | ✔ |
| C36 dirección visual y montaje | | ✔ | | | | | | | | | | ✔ |
| C37 talento rítmico y vocal | | | | | | | | | | | | ✔ |
| C38 biomecánica y coreografía | | | | | | | | | | | | ✔ |
| C39 presencia escénica | | | | | | | | | | ✔ | | ✔ |

**Lectura de la matriz:** el Área 7 no aparece como consumidora porque es la que **implanta** los bloques (los aloja), no la que los usa; el Área 6 consume C11 y C30 porque la resiliencia y la coordinación de agentes heterogéneos son exactamente su función. El bloque C20–C29 se concentra en el Área 11 por diseño: son capacidades analíticas cuyo uso legítimo en este sistema es el estudio de viabilidad económica de una invención, con las guardas de §12.5.

## T5 Matriz de dependencias entre módulos y orden topológico

| Módulo | Depende de | Es dependencia de |
|---|---|---|
| `core` (Área 0) | — | todos |
| `modules/prompts` (7) | core | debate, forensic, contrast, re, invention, capabilities |
| `modules/resilience` (6) | core, prompts | debate, forensic, contrast, re, invention |
| `modules/capabilities` (12) | core, prompts | prompts (bloques), todas las áreas de dominio |
| `modules/debate` (3) | core, prompts, resilience, capabilities | forensic, contrast, re, executor, fabrication, invention |
| `modules/executor` (8) | core, debate | fabrication, re, invention |
| `modules/devices` (4) | core | fabrication, re |
| `modules/forensic` (1) | core, prompts, resilience, debate | contrast, invention |
| `modules/contrast` (2) | core, prompts, resilience, debate, forensic | invention, re |
| `modules/re` (5) | core, debate, executor, devices, prompts | invention |
| `modules/fabrication` (9) | core, debate, executor, devices | invention |
| `modules/invention` (11) | core, debate, contrast, re, fabrication | — |
| `modules/mcp` (10.D) | core, executor, todas las de dominio | gui |
| `gui` (10) | core (por WebSocket), mcp | — |

**Orden topológico de construcción (único válido):**
`core` → `prompts` → `capabilities` → `resilience` → `debate` → `executor` → `devices` → `forensic` → `contrast` → `re` → `fabrication` → `invention` → `mcp` → `gui`.
Nota: la GUI se construye en paralelo desde el principio en su versión mínima (para poder ver lo que ocurre), pero su **catálogo completo de paneles** depende de que existan los módulos que alimentan cada panel; por eso figura al final del orden.

## T6 Tabla maestra de dependencias externas

| Herramienta | Versión | Licencia | Instalación Windows | Instalación Linux | Disco | Obligatoria |
|---|---|---|---|---|---|---|
| Python | 3.12.x | PSF | `winget install Python.Python.3.12` | `apt install python3.12 python3.12-venv` | 120 MB | **Sí** |
| Node.js | 20 LTS | MIT | `winget install OpenJS.NodeJS.LTS` | `apt install nodejs npm` (o nvm) | 90 MB | **Sí** |
| Rust + tauri-cli | 1.79+ / 2.x | MIT/Apache-2.0 | `winget install Rustlang.Rustup` + `cargo install tauri-cli` | `rustup` + `cargo install tauri-cli` | 1,5 GB | **Sí** (sólo para compilar) |
| SQLite | 3.45+ | Dominio público | incluido en Python | incluido / `apt install sqlite3` | 5 MB | **Sí** |
| DuckDB | 1.0.x | MIT | `pip install duckdb` | `pip install duckdb` | 60 MB | **Sí** |
| sqlite-vec | 0.1.x | Apache-2.0/MIT | `pip install sqlite-vec` | ídem | 3 MB | **Sí** |
| llama.cpp (el proveedor de nube asignado) | b3600+ | MIT | binario de la publicación oficial | compilar o binario | 40 MB | **Sí** |
| Ollama | 0.3.x | MIT | `winget install Ollama.Ollama` | `curl -fsSL https://ollama.com/install.sh \| sh` | 400 MB | No (gestor de modelos) |
| Modelos GGUF (texto + VLM + embeddings) | según §I.3 | Licencias de pesos abiertos (Apache-2.0, Llama Community, MIT según modelo) | descarga verificada en el primer arranque | ídem | 12–35 GB | **Sí** |
| Ghidra | 11.x | Apache-2.0 | ZIP oficial + JDK 21 Temurin | ídem | 1,5 GB + 300 MB JDK | Sí (Área 5) |
| Rizin | 0.7.x | LGPL-3.0 | binario oficial | `apt install rizin` | 90 MB | No |
| Radare2 | 5.9.x | LGPL-3.0 | instalador oficial | `apt install radare2` | 80 MB | No |
| Capstone | 5.0.x | BSD-3-Clause | `pip install capstone` | ídem | 20 MB | Sí (Área 5) |
| LIEF | 0.14.x | Apache-2.0 | `pip install lief` | ídem | 40 MB | Sí (Área 5) |
| angr | 9.2.x | BSD-2-Clause | `pip install angr` | ídem | 600 MB | No |
| Frida | 16.x | wxWindows Library Licence | `pip install frida-tools` | ídem | 90 MB | No |
| QEMU (user-mode) | 9.0.x | **GPL-2.0** (se invoca como proceso separado, no se enlaza) | binarios MSYS2/WSL2 | `apt install qemu-user` | 200 MB | No |
| Unicorn | 2.0.x | **GPL-2.0** (proceso separado) | `pip install unicorn` | ídem | 40 MB | Sí (oráculo A5-3) |
| binwalk / unblob | 2.3.x / 24.x | MIT / MIT | `pip install binwalk unblob` | ídem | 120 MB | No |
| OpenCV | 4.10 | Apache-2.0 | `pip install opencv-python-headless` | ídem | 90 MB | Sí (Área 1) |
| PyMuPDF | 1.24 | **AGPL-3.0** (⚠ si se distribuyera el sistema, obliga a liberar la fuente; es aceptable porque el proyecto se publica bajo licencia libre) | `pip install pymupdf` | ídem | 40 MB | Sí (Área 1) |
| pikepdf | 9.x | MPL-2.0 | `pip install pikepdf` | ídem | 30 MB | Sí (Área 1) |
| Tesseract | 5.4 | Apache-2.0 | `winget install UB-Mannheim.TesseractOCR` | `apt install tesseract-ocr tesseract-ocr-spa` | 120 MB | Sí (geometría, Área 1) |
| ExifTool | 12.x | Perl (Artistic/GPL) | ZIP oficial | `apt install libimage-exiftool-perl` | 25 MB | Sí (Área 1) |
| Playwright | 1.4x | Apache-2.0 | `pip install playwright && playwright install chromium` | ídem | 450 MB | No (Áreas 2 y 11) |
| adb / fastboot (platform-tools) | 35.x | Apache-2.0 | ZIP oficial de la plataforma | ídem | 15 MB | Sí (Área 4) |
| scrcpy | 2.x | Apache-2.0 | binario oficial | `apt install scrcpy` | 60 MB | No (Área 4) |
| libusb | 1.0.27 | LGPL-2.1 | incluido con `libusb1` | `apt install libusb-1.0-0` | 2 MB | Sí (Área 4) |
| PyAV | 12.x | BSD-3-Clause (FFmpeg **LGPL/GPL** según build: se usa build LGPL) | `pip install av` | ídem | 80 MB | No (Área 4) |
| CadQuery / build123d | 2.4 / 0.5 | Apache-2.0 | `pip install cadquery build123d` | ídem | 700 MB (OCCT) | Sí (Área 9.B) |
| OpenSCAD | 2021.01 | **GPL-2.0** (proceso separado) | `winget install OpenSCAD.OpenSCAD` | `apt install openscad` | 60 MB | No |
| FreeCAD | 1.0 | **LGPL-2.1** | instalador oficial | AppImage / `apt install freecad` | 1,2 GB | No |
| trimesh / manifold3d / admesh | 4.4 / 2.x / 0.98 | MIT / Apache-2.0 / GPL-2.0 | `pip install trimesh manifold3d` + binario admesh | ídem | 60 MB | Sí (Área 9.B) |
| PrusaSlicer | 2.8 | **AGPL-3.0** (proceso separado por CLI) | instalador oficial | AppImage | 250 MB | Sí (Área 9.B) |
| CuraEngine | 5.x | **AGPL-3.0** (proceso separado) | binario oficial | `apt install cura-engine` | 80 MB | No |
| Icarus Verilog | 12.0 | **GPL-2.0** (proceso separado) | instalador oficial | `apt install iverilog` | 40 MB | Sí (Área 9.C) |
| Verilator | 5.0xx | **LGPL-3.0 / Artistic-2.0** | `winget`/WSL2 | `apt install verilator` | 120 MB | Sí (Área 9.C) |
| cocotb | 1.9 | BSD-3-Clause | `pip install cocotb` | ídem | 15 MB | Sí (Área 9.C) |
| GTKWave / Surfer | 3.3 / 0.2 | GPL-2.0 / EUPL-1.2 | binario oficial | `apt install gtkwave` | 40 MB | No |
| Yosys | 0.4x | **ISC** | binarios OSS CAD Suite | OSS CAD Suite / `apt install yosys` | 200 MB | Sí (Área 9.C) |
| SymbiYosys + Yices | 0.4x / 2.6 | ISC / GPL-3.0 | OSS CAD Suite | ídem | 150 MB | Sí (Área 9.C) |
| nextpnr | 0.7 | ISC | OSS CAD Suite | ídem | 180 MB | Sí (Área 9.C) |
| openFPGALoader | 0.12 | Apache-2.0 | binario oficial | `apt install openfpgaloader` | 10 MB | No |
| OpenLane 2 + Sky130A + GF180MCU | 2.x / PDK actual | Apache-2.0 / Apache-2.0 | **vía WSL2 o contenedor** | `pip install openlane` + `volare` para el PDK | 12 GB | No (Área 9.C ASIC) |
| Magic / KLayout / netgen | 8.3.x / 0.29 / 1.5.x | Licencia Magic (BSD-like) / GPL-3.0 / GPL-2.0 | vía WSL2 | `apt`/compilar | 400 MB | No (firma del ASIC) |
| GHDL | 4.x | GPL-2.0 | binario oficial | `apt install ghdl` | 90 MB | No (VHDL) |
| KiCad + kicad-cli | 8.x | **GPL-3.0** (proceso separado) | `winget install KiCad.KiCad` | `apt install kicad` | 2,5 GB con librerías | Sí (Área 9.D) |
| SKiDL / kicad-skip | 1.2 / 0.2 | MIT / MIT | `pip install skidl kicad-skip` | ídem | 10 MB | Sí (Área 9.D) |
| freerouting | 1.9 | GPL-3.0 (Java, proceso separado) | JAR + JRE 21 | ídem | 60 MB + 200 MB JRE | No |
| gerbv | 2.10 | GPL-2.0 | binario oficial | `apt install gerbv` | 30 MB | No |
| avr-gcc + avr-libc | 14.x / 2.2 | GPL-3.0 / BSD | vía PlatformIO | vía PlatformIO / `apt install gcc-avr avr-libc` | 200 MB | No |
| arm-none-eabi-gcc | 13.x | GPL-3.0 | vía PlatformIO | `apt install gcc-arm-none-eabi` | 900 MB | No |
| SDCC | 4.4 | GPL-2.0 | instalador oficial | `apt install sdcc` | 120 MB | No |
| riscv64-unknown-elf-gcc | 13.x | GPL-3.0 | vía PlatformIO | vía PlatformIO | 900 MB | No |
| PlatformIO Core | 6.x | Apache-2.0 | `pip install platformio` | ídem | 150 MB + toolchains | Sí (Área 9.D) |
| Unity / Ceedling | 2.6 / 1.0 | MIT | vía PlatformIO / gem | ídem | 20 MB | No |
| avrdude | 7.3 | GPL-2.0 | binario oficial | `apt install avrdude` | 15 MB | No |
| dfu-util | 0.11 | GPL-2.0 | binario oficial | `apt install dfu-util` | 5 MB | No |
| OpenOCD | 0.12 | GPL-2.0 | binario oficial | `apt install openocd` | 40 MB | No |
| esptool.py | 4.8 | GPL-2.0 | `pip install esptool` | ídem | 10 MB | No |
| stm32flash | 0.7 | GPL-2.0 | binario oficial | `apt install stm32flash` | 3 MB | No |
| sigrok-cli + libsigrok | 0.7.2 / 0.5.x | GPL-3.0 | instalador oficial | `apt install sigrok-cli` | 60 MB | No (Área 9.E) |
| pygit2 | 1.15 | GPL-2.0 con excepción de enlazado | `pip install pygit2` | ídem | 30 MB | Sí (Área 8) |
| sympy / numpy / scipy / statsmodels / scikit-learn | 1.13 / 2.0 / 1.14 / 0.14 / 1.5 | BSD-3-Clause (todos) | `pip install` | ídem | 700 MB | **Sí** |
| pint / networkx / polars / z3-solver / cvxpy | 0.24 / 3.3 / 1.x / 4.13 / 1.5 | BSD / BSD / MIT / MIT / Apache-2.0 | `pip install` | ídem | 400 MB | **Sí** |
| gudhi / galois / einsteinpy / astropy / optuna | 3.9 / 0.3 / 0.4 / 6.x / 3.6 | MIT / MIT / MIT / BSD-3 / MIT | `pip install` | ídem | 350 MB | No (Área 12) |
| librosa / aubio / music21 / mido / mediapipe | 0.10 / 0.4 / 9.x / 1.3 / 0.10 | ISC / GPL-3.0 / BSD-3 / MIT / Apache-2.0 | `pip install` | ídem | 500 MB | No (Área 12) |
| whisper.cpp + modelo | reciente | MIT + pesos MIT | binario + GGUF | ídem | 500 MB | No (C10) |
| Claude Code CLI | actual | Términos del proveedor | `npm i -g` el paquete oficial | ídem | 100 MB | No (Área 10.D) |

**Nota de licencias (importa, y el plan la asume explícitamente):** varias herramientas centrales son **GPL/AGPL** (QEMU, Unicorn, OpenSCAD, PrusaSlicer, CuraEngine, KiCad, Icarus Verilog, avrdude, OpenOCD, sigrok, PyMuPDF). *Decisión:* **todas se invocan como procesos separados por su interfaz de línea de comandos, nunca se enlazan en el binario del sistema**, y el proyecto se publica bajo **AGPL-3.0** — porque PyMuPDF es AGPL y se usa como librería enlazada, lo que arrastra la licencia del conjunto; asumirlo desde el principio evita una reescritura posterior.
*Descartado:* sustituir PyMuPDF por `pypdfium2` (BSD/Apache) para poder publicar bajo licencia permisiva — es viable y se deja documentado como la vía si en el futuro se quiere relicenciar, pero PyMuPDF ofrece mejor acceso a la estructura interna del PDF, que es justo lo que el Área 1 necesita para D9.

## T7 Presupuesto global de recursos por escenario

| Escenario | RAM | VRAM | Disco (trabajo) | Tiempo | Modelos residentes | Notas |
|---|---|---|---|---|---|---|
| **Reposo** (núcleo + GUI, sin modelos) | 0,8 GB | 0 | — | — | ninguno | Objetivo de arranque ≤ 4 s |
| **Análisis documental** (expediente de 300 páginas) | 9,5 GB (Perfil B) / 4,5 GB + 6 GB VRAM (Perfil A) | 5,9 GB | 4 GB (imágenes normalizadas + teselas + informes) | 1 h 30 min | VLM + embeddings | Trabajo por lotes reanudable; CPU dominada por Tesseract y OpenCV |
| **Decompilación larga** (firmware de 40 MB) | 11 GB (Ghidra 6 GB + núcleo + modelo 4 GB) | 5,4 GB | 25 GB (proyecto Ghidra + C exportado + trazas) | 4–8 h | 1 modelo de texto | `TOOLCHAIN_HEAVY` exclusivo; VLM descargado |
| **Sesión de fabricación** (impresión + medición + firmware) | 5 GB | 0–5 GB | 3 GB | Duración de la impresión (horas) | opcional | Prioridad `PHYSICAL_SAFETY`; el debate se ejecuta entre capas |
| **Debate intensivo** (5 rondas, 3 modelos distintos, Perfil C) | 8 GB | 22 GB | 1 GB | 12 min | 3 modelos + embeddings | En Perfil A se conmutan modelos por turno (+4,5 s por cambio) |
| **Flujo ASIC** (OpenLane sobre Sky130A) | 14 GB | 0 | 30 GB | 30 min – 6 h | ninguno | Exclusivo: drena el resto de trabajos |
| **Todo instalado** (línea base de disco) | — | — | **≈ 55–80 GB** (modelos 12–35 GB + toolchains ≈ 25 GB + PDK 12 GB si se instala) | — | — | Encaja en los 100 GB declarados si el PDK del ASIC es opcional |

## T8 Hoja de ruta global en cuatro fases

| Fase | Módulos incluidos | Entregables concretos | Métricas de salida |
|---|---|---|---|
| **F1 — MVP vertical estrecho (no un esqueleto de todo)** | `core` mínimo (bus, SQLite, CAS, WS), `prompts` (base + 3 roles + dominio de contraste), `resilience` (cliente local + WAL), `debate` (1 ronda con rúbrica), `contrast` (ingesta + BM25 + validador de citas + dictamen), `gui` mínima (chat A/B/C + árbol + terminal + E-STOP) | **Un contrato escaneado entra y sale un dictamen con citas verificadas, habiendo pasado un debate real** — de punta a punta, sin atajos | 0 citas no verificadas; ≥ 1 debate completo con acta persistida; reanudación tras matar el núcleo sin pérdida; arranque ≤ 4 s |
| **F2 — Física y ejecución** | `executor` completo, `devices`, `fabrication/printer` + `cad`, `forensic` completo, paneles de telemetría y monitor de impresión | Imprimir una pieza diseñada por el sistema, medirla, y que la desviación se convierta en refutación e itere hasta converger; informe forense con FPR ≤ 2 % | Convergencia dimensional en ≤ 3 iteraciones; 0 G-Code enviado sin análisis estático; `M112` en ≤ 2 s; FPR ≤ 2 % |
| **F3 — Ingeniería inversa y síntesis** | `re` completo (Ghidra, triaje, refinamiento, matriz, clasificador, libro mayor, diferencial, clean room), `capabilities` C01–C19, MCP | Libro mayor de adaptación completo entre un emulador de origen y una consola destino, con pruebas diferenciales funcionando y el primer punto de divergencia convertido en refutación | Exactitud de capas ≥ 0,85; 100 % de hipótesis fijadas con oráculo; divergencia detectada en el índice exacto; 19/19 capacidades en verde |
| **F4 — Completo** | `fabrication/hdl` + `pcb` + `firmware` + `metrology`, `invention`, `capabilities` C20–C39, GUI completa (grafo, procedencia, política, auditoría), instaladores, banco de superioridad | Sistema completo empaquetado para Windows y Linux, con las 39 capacidades probadas y el banco de superioridad ejecutado y publicado | 39/39 pruebas definidas y ≥ 35 en verde; GDSII con LVS limpio; instaladores ≤ 120 MB; banco de superioridad publicado con su resultado, favorable o no |

## T9 Los diez riesgos principales del proyecto (ordenados por impacto × probabilidad)

| # | Riesgo | Prob. | Impacto | Mitigación | Señal temprana de alerta |
|---|---|---|---|---|---|
| 1 | **Alcance inabarcable**: 13 áreas es más de lo que un equipo pequeño termina; se queda todo a medias | Muy alta | Crítico | F1 es un vertical estrecho **completo**, no un esqueleto; ningún módulo avanza de fase con PV en rojo; el orden topológico de §T5 es obligatorio | En F1, más de 3 semanas sin que el dictamen de punta a punta funcione |
| 2 | **Daño físico** (incendio, MCU inutilizado, colisión de ejes) | Baja | Crítico | Límites duros en `config/safety.yaml`, detectores térmicos, `M112` redundante, hombre muerto independiente del núcleo, dump previo obligatorio, R3 siempre humano | Cualquier `print.fault` de nivel 3 en pruebas; cualquier flasheo con `integrity=UNKNOWN` |
| 3 | **Debate teatral** (A y B convergen y el sistema se autoconfirma) | Alta | Alto | Regla de diversidad de modelos, métrica de divergencia léxica, guarda de sicofancia, reinicio ciego, precedencia de evidencia | `refutation_substantive_rate` < 0,35 dos rondas seguidas |
| 4 | **Alucinación con apariencia de rigor** (citas y números inventados que pasan por análisis) | Alta | Alto | Validador de citas por subcadena exacta, recálculo determinista en sandbox, `sin-referencia-en-corpus` como salida legítima, banco de prompts con umbral de 0,5 % | Tasa de alucinación de citas > 0,5 % en el banco |
| 5 | **Control total mal delimitado** (un error destructivo irreversible) | Media | Crítico | Broker con catálogo cerrado de 7 operaciones, lista negra dura, cuarentena en vez de borrado, instantáneas, auditoría encadenada, R3 sin "recordar respuesta" | Cualquier fila de `audit_log` con `radius=R3` y `actor≠human` |
| 6 | **Deriva silenciosa de calidad** al cambiar modelo o prompt | Alta | Alto | Banco de regresión de prompts obligatorio en cada cambio, pruebas de posesión de capacidades, marcado de calidad heterogénea en artefactos | Caída > 3 puntos en cualquier métrica del banco |
| 7 | **Fragilidad de las toolchains externas** (versiones, rutas, WSL2) | Alta | Medio | Versiones fijadas en §T6, verificación de hash al instalar, `ToolchainHAL` con detección y mensaje exacto, contenedor para OpenLane | Cualquier fallo de clase `entorno` recurrente en el clasificador del Área 8 |
| 8 | **Expectativa irreal sobre el portado de emuladores** ("cambiar cuatro parámetros") | Alta | Medio | El libro mayor cuantifica desde el primer día cuántos módulos son `reescribir-de-cero`; la matriz de arquitecturas es el activo que sostiene esa cifra | Recuento de `reescribir-de-cero` > 30 % y aun así estimación optimista de esfuerzo |
| 9 | **Coste computacional que hace el sistema inusable** en la máquina declarada | Media | Alto | Presupuesto de recursos en el planificador, semáforos exclusivos, salto del debate en R0, caché con claves completas, perfiles A/B/C | Cualquier `oom_kill`, o un debate que supere 12 min en Perfil A |
| 10 | **Problema legal** (redistribución de material propietario o uso indebido de datos) | Media | Alto | CTL-1/CTL-2/CTL-3 aplicados en puntos concretos del código, guarda de consentimiento de C08, etiquetas obligatorias en dictámenes y análisis financieros | Cualquier `PackagingRefused` real en uso normal (indica que alguien lo intentó sin saberlo) |

## T10 Glosario final

**Acta** — registro JSON estructurado de una ronda de debate; único artefacto que consume el Juez y único que se persiste. · **ADB** — *Android Debug Bridge*, puente de depuración de Android. · **Afirmación (Claim)** — proposición falsable emitida por el MELCHIOR. · **Agente** — rol conversacional (MELCHIOR/BALTHASAR/CASPER) con su prompt, su modelo y su sesión. · **AGPL** — licencia pública general de Affero. · **angr** — plataforma de análisis binario con ejecución simbólica. · **Artefacto** — salida versionada y hasheada. · **BM25** — función de ranking léxico. · **CAS** — almacén direccionado por contenido. · **CDC-ACM** — clase USB de comunicaciones que expone un puerto serie. · **CPL** — fichero de posiciones de componentes para ensamblaje. · **CTS** — síntesis del árbol de reloj. · **cocotb** — marco de bancos de prueba HDL en Python. · **DFU** — *Device Firmware Upgrade*, clase USB de actualización de firmware. · **DRC** — comprobación de reglas de diseño. · **DuckDB** — motor analítico embebido. · **ELA** — análisis de nivel de error sobre imágenes JPEG. · **ERC** — comprobación de reglas eléctricas. · **Evidencia** — dato observado con su procedencia. · **Excellon** — formato de fichero de taladro. · **FLIRT** — técnica de identificación de funciones de librería por firma. · **FPGA** — matriz de puertas programable en campo. · **Frida** — instrumentación dinámica. · **GBNF** — formato de gramática de `llama.cpp` para decodificación restringida. · **GDSII** — formato de intercambio de geometría de circuito integrado. · **Gerber** — formato de fichero de fabricación de PCB. · **Ghidra** — plataforma libre de ingeniería inversa. · **GXM** — API gráfica de PlayStation Vita. · **HAL** — capa de abstracción de sistema operativo. · **HLE / LLE** — emulación de alto nivel / de bajo nivel. · **HID** — clase USB de dispositivos de interfaz humana. · **IoU** — intersección sobre unión. · **JIT** — compilación dinámica. · **KiCad** — suite libre de diseño electrónico. · **Klipper** — firmware de impresora 3D con el control en un host. · **LVS** — comparación de esquemático contra trazado. · **MAP-Elites** — algoritmo de calidad-diversidad. · **Marlin** — firmware de impresora 3D. · **MCP** — *Model Context Protocol*, protocolo de exposición de herramientas a modelos. · **MCU** — microcontrolador. · **Moonraker** — servidor de API para Klipper. · **MPU/MMU** — unidad de protección / de gestión de memoria. · **MSC** — clase USB de almacenamiento masivo. · **MTP** — protocolo de transferencia de medios. · **nextpnr** — emplazador y rutador libre para FPGA. · **OpenLane** — flujo libre RTL→GDSII. · **OpenOCD** — depurador y programador por JTAG/SWD. · **PDK** — kit de diseño de proceso de fabricación de silicio. · **PM (Perfil de máquina)** — estructura con dialecto y límites de una impresora. · **polkit** — marco de autorización de privilegios en Linux. · **PRNU** — no uniformidad de respuesta de fotositos, huella del sensor. · **Procedencia** — cadena de origen de un artefacto. · **PV (Puerta de verificación)** — comprobación automatizada que cierra un subpaso. · **QEMU** — emulador y virtualizador. · **R0/R1/R2/R3** — radios de impacto de una acción. · **Radio de impacto** — clasificación de reversibilidad de una acción. · **Refutación** — intento estructurado de falsar una afirmación. · **Rizin/Radare2** — marcos libres de ingeniería inversa. · **RRF** — fusión recíproca de rangos. · **Ronda** — ciclo MELCHIOR→BALTHASAR→CASPER con su acta. · **RTL** — nivel de transferencia entre registros. · **scrcpy** — herramienta de espejo de pantalla Android. · **sigrok** — suite libre de instrumentación. · **SKiDL** — descripción de esquemáticos en Python. · **SSIM** — índice de similitud estructural. · **STA** — análisis estático de temporización. · **SWD** — interfaz de depuración serie de ARM. · **SymbiYosys** — envoltorio de verificación formal sobre Yosys. · **Tape-out** — envío de un diseño a fabricación de silicio. · **Tesela (tile)** — fragmento de imagen enviado al VLM. · **TRIZ** — teoría para la resolución inventiva de problemas. · **TRL** — nivel de madurez tecnológica. · **UMD** — medio óptico de PSP. · **Unicorn** — emulador de conjuntos de instrucciones basado en QEMU. · **UR (Unidad reanudable)** — fragmento idempotente de un trabajo largo. · **UVC** — clase USB de vídeo. · **udev** — gestor de dispositivos de Linux. · **Veredicto** — resolución del CASPER con puntuación. · **Verilator** — simulador y linter de Verilog. · **VFPU** — unidad vectorial de coma flotante del PSP. · **VLM** — modelo de lenguaje con visión. · **WAL** — registro de escritura anticipada. · **WinUSB/libusbK** — controladores genéricos de USB en Windows. · **Yosys** — sintetizador lógico libre. · **Zadig** — utilidad de instalación de controladores USB en Windows. · **z3** — solucionador SMT.

## T11 Plan maestro de construcción por pasos y subpasos con puertas de verificación

Este artefacto reúne, en el orden topológico de §T5, todos los pasos `Pn.x` y sus puertas `PV-n.x.y` definidos en las subsecciones 12 de cada área, y añade las **puertas de integración** entre módulos, que son las que atrapan los errores que ninguna prueba unitaria ve. La regla operativa es una sola: **no se empieza el paso siguiente con una puerta en rojo**, y `make gates` los ejecuta todos de forma acumulativa (una puerta que pasó en la fase 1 debe seguir pasando en la fase 4; si deja de pasar, es una regresión y bloquea).

| Orden | Paso | Puertas propias | **Puerta de integración que lo cierra** |
|---|---|---|---|
| 1 | P0.a–P0.f (núcleo) | PV-0.a.1 … PV-0.f.2 | **PV-INT-1**: la GUI mínima recibe 10 000 eventos, se cierra la ventana con un trabajo simulado de 10 min en curso, y al reabrir el trabajo sigue y el progreso es correcto |
| 2 | P7.a–P7.d (prompts) | PV-7.a.1 … PV-7.d.2 | **PV-INT-2**: 500 generaciones locales con GBNF producen 100 % de JSON válido contra los 7 esquemas, y el `prompt_hash` aparece en el 100 % de los `model_run` |
| 3 | P12.a (bloques de capacidad) | PV-12.a.1, PV-12.a.2 | **PV-INT-3**: una tarea que ensambla 4 bloques no supera el presupuesto de contexto en 100 casos |
| 4 | P6.a–P6.e (resiliencia) | PV-6.a.1 … PV-6.e.1 | **PV-INT-4**: trabajo de 300 unidades con corte de proveedor en la 200 y reinicio duro en la 250: completa con ≤ 2 unidades recomputadas y el artefacto declara los tramos |
| 5 | P3.a–P3.e (debate) | PV-3.a.1 … PV-3.e.2 | **PV-INT-5**: 20 debates completos con actas válidas, aislamiento de contexto de B verificado por hash y 0 veredictos que contradigan evidencia de mayor rango |
| 6 | P8.a–P8.e (ejecutor) | PV-8.a.1 … PV-8.e.3 | **PV-INT-6**: un fallo real de compilación se convierte en refutación, produce una corrección, y el ciclo converge o escala en ≤ 8 iteraciones, 20/20 |
| 7 | P4.a–P4.e (dispositivos) | PV-4.a.1 … PV-4.e.2 | **PV-INT-7**: 50 ciclos de conexión/desconexión durante un debate activo sin pérdida de eventos críticos ni caída de la GUI |
| 8 | P1.a–P1.e (forense) | PV-1.a.1 … PV-1.e.2 | **PV-INT-8**: expediente de 300 páginas procesado por lotes con reanudación, informe con 0 hallazgos sin veredicto y `replay` con hashes idénticos |
| 9 | P2.a–P2.e (contraste) | PV-2.a.1 … PV-2.e.2 | **PV-INT-9**: contrato escaneado → topografía → afirmaciones → dictamen con 100 % de citas verificadas y 100 % de números recalculados — **éste es el hito de la Fase 1** |
| 10 | P5.a–P5.f (ingeniería inversa) | PV-5.a.1 … PV-5.f.4 | **PV-INT-10**: binario del dispositivo → triaje → decompilación reanudable → refinamiento con oráculo → libro mayor con evidencia en el 100 % de las filas |
| 11 | P9.a–P9.e (fabricación) | PV-9.a.1 … PV-9.e.4 | **PV-INT-11**: intención → CAD → verificación → G-Code → impresión → medición → refutación → corrección → convergencia, con el simulador primero y la máquina real después |
| 12 | P11.a–P11.e (invención) | PV-11.a.1 … PV-11.e.3 | **PV-INT-12**: idea → validación → 36 derivadas en ≥ 12 nichos → ganadora → MVP prototipado en el Área 9 → fallo real que estrecha un parámetro |
| 13 | P12.b–P12.d (capacidades) | PV-12.b.1 … PV-12.d.1 | **PV-INT-13**: `make capabilities` en verde para ≥ 35/39 y desactivación automática comprobada de las que fallan |
| 14 | P10.a–P10.d (GUI y control) | PV-10.a.1 … PV-10.d.5 | **PV-INT-14**: escenario de estrés completo (10 000 líneas/s + impresión + debate + decompilación) con ≥ 30 fps, 0 acciones R3 sin humano y cadena de auditoría íntegra |

**Puertas transversales que se ejecutan en cada fase, no una sola vez:**

| Puerta | Qué comprueba | Criterio |
|---|---|---|
| **PV-X-SEG** (seguridad) | Consulta SQL sobre `audit_log` y `action` | 0 filas con `radius='R3'` sin aprobación humana; 0 acciones ejecutadas sin entrada de auditoría |
| **PV-X-CIT** (citas) | Todo informe exportado | 0 citas no verificadas por A2-3 |
| **PV-X-POST** (postcondiciones) | Todo artefacto marcado válido | 0 artefactos con `postcondition_ok` nulo o falso |
| **PV-X-PROV** (procedencia) | Grafo de procedencia | 0 artefactos sin cadena hasta entradas primarias |
| **PV-X-LEG** (controles legales) | CTL-1/CTL-2/CTL-3 | 0 empaquetados con `origin_class` prohibido; 100 % de derivados de decompilación con `derivative_risk='high'`; 0 accesos cruzados en el clean room |
| **PV-X-REG** (regresión de prompts) | `make prompt-bench` | Ninguna métrica cae más de 3 puntos respecto de la versión anterior |
| **PV-X-OFF** (offline) | Prueba de humo sin red | Áreas 1, 3, 4, 5 y 9 completan su escenario al 100 % |

## T12 Sistema de diseño visual MAGI (tokens, componentes, lenguaje llano y accesibilidad)

Fuente única de verdad de la apariencia y del vocabulario. Vive en `gui/src/theme/` y `gui/src/help/`; el CI falla si un componente usa un color literal en vez de un token **o si introduce una sigla que no esté en el glosario**.

**Ficheros:** `magi.css` (variables), `magi.tokens.json` (los mismos valores para tests y capturas), `components/` (los 12 componentes propios), `help/glossary.es.json` (términos con definición de dos frases y ejemplo), `help/wording.es.json` (catálogo cerrado de rótulos y mensajes), `a11y.test.tsx` y `wording.test.ts`.

**Componentes propios, con su contrato:**

| Componente | Qué es | Props clave | Qué representa |
|---|---|---|---|
| `MagiNodePanel` | Trapecio de un nodo MAGI con su nombre, su función en tres palabras y su frase de pensamiento | `node`, `role_plain`, `state`, `plain_summary`, `tokens` | Esperando / Pensando / Propuesta lista / Buscando fallos / Decidiendo / Ha fallado |
| `MagiTriad` | Cabecera completa con los tres trapecios y el rombo | `round`, `verdict`, `needsPermission` | Estado global de la tarea |
| `MagiVerdictRhombus` | Rombo central | `outcome`, `shapeMode` | Aceptada / Aceptada con cambios / Rechazada / Sin decidir / Necesita tu permiso |
| `TaskStatusBlock` | Bloque de estado en español llano | `task`, `file`, `step`, `total`, `eta`, `network` | Sustituye al antiguo bloque de códigos |
| `AttachmentStrip` | Tira de adjuntos sin filtro de formato | `files`, `onRemove` | Leído / Leído parcialmente / Abierto en entorno de época / No se ha podido leer |
| `TaskCard` | Tarjeta de sugerencia de encargo en un hilo vacío | `verb`, `needs`, `typicalTime` | Ocho encargos frecuentes; nunca sustituye a la barra de instrucción |
| `ModelIdentityLine` | Línea siempre visible con la inteligencia en uso, expandible al detalle completo del §I.8 | `identity`, `expanded`, `changedAtRound` | Qué modelo, con qué cuantización, dónde corre y con qué semilla |
| `TurnCard` | Tarjeta de intervención de un nodo, con sus cinco partes fijas | `node`, `identity`, `round`, `version`, `plainSummary`, `sections[]` | Una intervención de MELCHIOR, BALTHASAR o CASPER |
| `RoundStrip` | Fila de una ronda con las tres tarjetas y su cabecera | `round`, `score`, `delta`, `counts` | Una ronda completa de la deliberación |
| `TrajectoryChart` | Puntuación por ronda con las versiones marcadas | `trajectory`, `selectedVersion` | Si la deliberación mejora, se estanca u oscila |
| `ThreadComposer` | Barra de instrucción con preajuste de rondas, adjuntar y ejecutar | `onSubmit`, `preset`, `overrides` | Entrada principal; permite anular parámetros sólo para ese turno |
| `SectionSwitch` | Conmutador Conversación / Proyectos | `section` | Las dos secciones hermanas |
| `PermissionDialog` | Diálogo de permiso puntual | `effectPlain`, `radius`, `reversible` | Sustituye al código de acceso |
| `RadiusBadge` | Distintivo de impacto, con etiqueta en palabras | `radius` | «Sólo lee» / «Se puede deshacer» / «Se puede deshacer con copia» / «No se puede deshacer» |
| `EvidenceTierChip` | Rango de la prueba, en palabras | `tier` | «Medido» / «Ejecutado» / «Analizado» / «Citado» / «Razonado» |
| `TelemetryStrip` | Franja de señales en vivo | `channels`, `window` | Series de alta frecuencia fuera de React |
| `GraphCanvas` | Lienzo de grafo | `mode: "debate" \| "code"` | Grafo de propuestas o de código |

**Reglas de lenguaje (verificadas en `wording.test.ts`, no son estilo sino contrato):**
1. **Alfabeto latino exclusivamente** en todo rótulo, mensaje, estado y nombre de panel. Ninguna cadena de la interfaz puede contener caracteres fuera de los rangos latinos; el test recorre `wording.es.json` y los literales de los componentes y falla si encuentra uno.
2. **Ninguna sigla sin glosario.** Toda sigla mostrada en la interfaz debe existir en `glossary.es.json`; el test lo comprueba. En el resumen en llano de cada tarjeta se prefiere siempre la forma desarrollada.
3. **Los estados se nombran con verbos**, no con códigos: `Pensando`, no `EX_MODE:ON`.
4. **Los errores usan la plantilla de tres partes** «Qué ha pasado / Por qué / Qué puedes hacer» y la tercera es un botón. El test verifica que ningún mensaje de error carece de acción.
5. **Las cifras llevan unidad y contexto**: «quedan unos 2 minutos», no «ETA 118».
6. **`plain_summary` obligatorio** en todo turno de un nodo MAGI: máximo 140 caracteres, sin jerga, sin siglas y sin cifras sin unidad; su ausencia es defecto de prompt y se cuenta en §7.8.

**Reglas de accesibilidad (verificadas en `a11y.test.tsx`):**
1. Contraste ≥ 4,5:1 en todo texto; `--magi-ink` sobre `--magi-node` alcanza 8,9:1 y `--magi-text` sobre negro 7,1:1.
2. **Ningún estado se comunica sólo por color**: el rombo lleva forma (círculo, triángulo, aspa, guion) y palabra; los trapecios llevan etiqueta de estado.
3. Foco de teclado visible en `--magi-accent-hi`, 2 px, nunca suprimido; toda la interfaz recorrible con tabulador en orden lógico.
4. Animaciones desactivadas con `prefers-reduced-motion`, sustituidas por indicador estático.
5. Tamaño de fuente escalable de 12 a 20 px sin romper la cabecera (probado al 200 % de zoom).
6. Toda imagen y todo icono con texto alternativo; los distintivos de adjunto se leen como frase completa.

**Modos de tema:** `magi-dark` (por defecto), `magi-high-contrast`, `magi-colorblind` (azul/amarillo más formas) y `sobrio` (los trapecios pasan a barras horizontales y la saturación baja al 40 %, conservando toda la información). Se cambia con `Ctrl+Mayús+T` y se persiste por proyecto.

**Regresión visual y de lenguaje:** `tests/gui/visual/` guarda una captura por componente y tema; un cambio superior al 2 % en un componente no tocado por el commit bloquea la promoción. `tests/gui/wording/` guarda el `wording.es.json` aprobado; cualquier rótulo nuevo exige revisión explícita. Es lo que impide que, a lo largo de cuatro fases, la interfaz vuelva a llenarse de siglas.

## T13 Addenda de integración: cambios que MAGI-MEM y MAGI-ROUTE introducen en T1–T11

Este artefacto no sustituye a T1–T11: los **enmienda de forma explícita y localizada**, para que la trazabilidad del documento no se pierda.

**Enmienda a T1 (árbol de directorios).** Se añaden:

```
modules/memgraph/          Área 13: adaptador de MAGI-MEM, validador Cypher, deltas de conocimiento
modules/route/             Área 14: adaptador de MAGI-ROUTE, RouteDirective, conciliación de telemetría
tools/magi-mem/<version>/  binario estático verificado por hash y firma
tools/magi-route/<version>/ pasarela (NPM o imagen OCI) en la versión fijada
config/externals.lock      commit/versión, hashes y ENUMERACIÓN EFECTIVA de capacidades de ambos externos
config/memgraph.yaml       perfiles de consulta por nodo MAGI, raíz permitida, presupuesto de RAM
config/route.yaml          estrategias por rol y por clase de tarea, enumeración cerrada, clases de privacidad
gui/src/theme/             T12: tokens, componentes MAGI, pruebas de accesibilidad y capturas de referencia
profiles/emulators/*.yaml  subárboles y símbolos específicos de consola usados por A13-2
tests/gui/visual/          capturas de referencia por componente y tema
```

**Enmienda a T2 (catálogo de eventos).** Se añaden nueve eventos, todos con emisor, consumidores y criticidad:

| Evento | Emisor | Consumidores | Payload | Frecuencia | Criticidad |
|---|---|---|---|---|---|
| `memgraph.indexed` | modules/memgraph | GUI, Área 5, caché | `{project, nodes, edges, duration_s, languages[], coverage_pct}` | Esporádica | Alta (persistido) |
| `memgraph.stale` | vigilante de MAGI-MEM | Área 5, GUI | `{project, files_changed}` | Esporádica | Media |
| `memgraph.query` | modules/memgraph | obs | `{kind, duration_ms, rows}` | Alta (muestreo 1:50) | Baja |
| `knowledge.recorded` | modules/debate | Área 13, GUI | `{knowledge_id, qualified_name, round_id}` | 1–5 por ronda | Alta (persistido) |
| `knowledge.invalidated` | modules/memgraph | GUI, prompts | `{knowledge_id, reason}` | Esporádica | Alta |
| `route.selected` | modules/route | obs, Área 6, GUI | `{unit_id, provider, model, strategy, latency_ms, tokens_in, tokens_out, cost_usd}` | 1 por llamada | Media |
| `route.tripped` | modules/route | Área 6, GUI | `{provider, layer, reason, reset_in_s}` | Esporádica | Alta |
| `route.blocked` | modules/route | audit, GUI | `{reason:"privacy"\|"policy", provider, unit_id}` | Rara | **Crítica** |
| `route.degraded` | modules/route | Área 6, GUI, acta | `{from, to, reason}` | Esporádica | Alta (persistido) |

**Enmienda a T3 (esquema de base de datos).** Se añaden seis tablas:

```sql
CREATE TABLE mem_project (
  project TEXT PRIMARY KEY, root_path TEXT NOT NULL, graph_version TEXT NOT NULL,
  nodes INTEGER, edges INTEGER, languages_json TEXT, coverage_pct REAL,
  synthetic_source INTEGER NOT NULL DEFAULT 0,          -- 1 si proviene de C decompilado
  origin_class TEXT NOT NULL DEFAULT 'user_supplied',   -- hereda CTL-1
  indexed_at TEXT NOT NULL, stale INTEGER NOT NULL DEFAULT 0);

CREATE TABLE mem_query_log (
  query_id INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT NOT NULL REFERENCES mem_project(project),
  kind TEXT NOT NULL CHECK (kind IN ('cypher','search','trace','semantic','snippet','impact')),
  query_hash TEXT NOT NULL, query_text TEXT NOT NULL, rows INTEGER, duration_ms REAL,
  asked_by TEXT CHECK (asked_by IN ('MELCHIOR','BALTHASAR','CASPER','system')), ts TEXT NOT NULL);
CREATE INDEX ix_memq_hash ON mem_query_log(query_hash);

CREATE TABLE mem_knowledge (
  knowledge_id TEXT PRIMARY KEY, project TEXT NOT NULL REFERENCES mem_project(project),
  qualified_name TEXT NOT NULL, statement TEXT NOT NULL,
  round_id TEXT, verdict_id TEXT, score INTEGER, evidence_tier_min INTEGER,
  expires_when TEXT NOT NULL, invalidated_by TEXT, invalidated_at TEXT, created_at TEXT NOT NULL);
CREATE INDEX ix_know_symbol ON mem_knowledge(project, qualified_name, invalidated_by);

CREATE TABLE mem_coverage (
  project TEXT NOT NULL REFERENCES mem_project(project), language TEXT NOT NULL,
  files_seen INTEGER, files_indexed INTEGER, pct REAL,
  PRIMARY KEY (project, language));

CREATE TABLE route_call (
  call_id TEXT PRIMARY KEY, unit_id TEXT, role TEXT NOT NULL, provider TEXT NOT NULL,
  model TEXT NOT NULL, pinned_model TEXT, strategy TEXT NOT NULL,
  privacy_class TEXT NOT NULL CHECK (privacy_class IN ('local_only','consented_remote')),
  tokens_in INTEGER, tokens_out INTEGER, tokens_in_local_count INTEGER,
  telemetry_mismatch INTEGER DEFAULT 0, cost_usd REAL NOT NULL DEFAULT 0,
  latency_ms INTEGER, gateway_overhead_ms INTEGER, ok INTEGER, ts TEXT NOT NULL);
CREATE INDEX ix_route_provider ON route_call(provider, ts DESC);

CREATE TABLE route_event (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, provider TEXT,
  layer TEXT, reason TEXT, detail_json TEXT, ts TEXT NOT NULL);
```

Consulta de control nueva, que se ejecuta en `PV-X-SEG`: `SELECT COUNT(*) FROM route_call WHERE privacy_class='local_only' AND provider NOT IN (SELECT id FROM local_providers)` debe devolver **0**; y `SELECT SUM(cost_usd) FROM route_call` debe devolver **0**.

**Enmienda a T4 (matriz Áreas ↔ capacidades).** Las columnas se extienden a 13 y 14: **C03** (teoría de la información) y **C07** (minería de datos) pasan a consumirse también en el Área 13, porque la métrica de ahorro de tokens y las consultas agregadas sobre el grafo son exactamente eso; **C16** (taxonomía) se consume en el Área 13 (clasificación de capas con evidencia estructural); **C11** (resiliencia) y **C30** (coordinación) se consumen en el Área 14.

**Enmienda a T5 (dependencias y orden topológico).** El orden pasa a ser:
`core` → `prompts` → `capabilities` → **`route`** → `resilience` → `debate` → `executor` → `devices` → `forensic` → `contrast` → **`memgraph`** → `re` → `fabrication` → `invention` → `mcp` → `gui`.
`route` se adelanta porque toda inferencia pasa por él; `memgraph` precede a `re` porque el Área 5 ya no clasifica capas sin grafo (con reserva).

**Enmienda a T6 (dependencias externas).** Dos filas nuevas, con la licencia a registrar al fijar el commit:

| Herramienta | Versión | Licencia | Instalación Windows | Instalación Linux | Disco | Obligatoria |
|---|---|---|---|---|---|---|
| MAGI-MEM (`codebase-memory-mcp`) | commit fijado en `externals.lock` | registrar del repositorio al fijar el commit; **proceso separado por MCP**, sin enlazado | binario amd64 verificado por hash + cosign | binario amd64/arm64 ídem | 60–120 MB + grafo | No (con camino de reserva) |
| MAGI-ROUTE (`OmniRoute`) | versión fijada en `externals.lock` | MIT (verificar en el tag adoptado) | NPM local o imagen OCI | ídem | 300–500 MB | No (con camino de reserva) |

**Enmienda a T7 (presupuesto de recursos).** Dos escenarios nuevos y un ajuste:

| Escenario | RAM | VRAM | Disco | Tiempo | Notas |
|---|---|---|---|---|---|
| Indexación de MAGI-MEM (500 k nodos) | 3,8 GB (acotada) | 0 | 1,5 GB | ≤ 20 min | Exclusivo con `TOOLCHAIN_HEAVY`; se libera al terminar |
| Pasarela MAGI-ROUTE en reposo | 0,4 GB | 0 | 2 GB (rotación) | — | Puede convivir con todo |
| **Ajuste al escenario «decompilación larga»** | **9,2 GB** (antes 11) | 5,4 GB | 25 GB + grafo | 3–6 h | El grafo reduce el contexto por función y permite bajar el modelo residente a Q4 sin perder calidad medible |

**Enmienda a T8 (hoja de ruta).** MAGI-ROUTE entra en **F1** (es el sustrato de toda inferencia y su camino de reserva es el cliente que F1 ya construye) y MAGI-MEM entra en **F3** junto al Área 5, salvo su MVP de indexación del propio repositorio, que se adelanta a **F2** para que el equipo lo use mientras construye. La identidad visual MAGI y el sistema de diseño T12 entran en **F1**, no al final: rehacer una interfaz completa en F4 es el error clásico.

**Enmienda a T9 (riesgos).** Dos riesgos nuevos que entran directamente en el top 10, desplazando a los puestos 9 y 10 anteriores a la cola:

| # | Riesgo | Prob. | Impacto | Mitigación | Señal temprana |
|---|---|---|---|---|---|
| 2-bis | **Superficie de red nueva por la pasarela** (puerto de inferencia alcanzable en la red del usuario) | Media | **Crítico** | Loopback obligatorio, clave requerida, verificación activa A14-2 cada 10 min, contenedor con red acotada | Cualquier `route.blocked{reason:"policy"}` |
| 4-bis | **Falso vacío del grafo** (el índice no cubre un lenguaje y «no hay llamadores» se lee como «código muerto») | Alta | Alto | Cobertura por lenguaje obligatoria; afirmación de ausencia inadmisible bajo cobertura < 95 % | `coverage_pct` < 95 en cualquier proyecto activo |

**Enmienda a T10 (glosario).** Se añaden: **MAGI System IDE** — nombre del producto. · **MELCHIOR • 1 / BALTHASAR • 2 / CASPER • 3** — los tres nodos deliberativos. · **ATLAS-FORGE** — núcleo de ingeniería y síntesis gobernado por MAGI System IDE. · **MAGI-MEM** — grafo de memoria de código (Área 13). · **MAGI-ROUTE** — pasarela de inferencia (Área 14). · **Cypher** — lenguaje de consulta de grafos; aquí, subconjunto de sólo lectura. · **tree-sitter** — generador de analizadores sintácticos incrementales. · **LSP híbrido** — resolución de tipos ligera, no un servidor de lenguaje completo. · **`qualified_name`** — identificador de un símbolo en el grafo, con formato `<proyecto>.<ruta>.<nombre>`. · **Delta de conocimiento** — hecho establecido por un veredicto, con evidencia y caducidad. · **`privacy_class`** — clasificación que decide si una petición puede salir del equipo. · **`RouteDirective`** — orden de la política al enrutador, no sobrescribible. · **lkgp** — último camino bueno conocido, estrategia de enrutado. · **Sigstore / cosign / SLSA** — firma y procedencia de artefactos de terceros.

**Enmienda a T11 (plan maestro de pasos).** Se insertan dos filas y una puerta transversal:

| Orden | Paso | Puertas propias | Puerta de integración |
|---|---|---|---|
| 3-bis | P14.a–P14.e (MAGI-ROUTE) | PV-14.a.1 … PV-14.e.1 | **PV-INT-15**: 300 unidades con la pasarela caída a mitad, ≤ 1 recomputada, 0 fugas de clase `local_only`, coste 0 |
| 9-bis | P13.a–P13.e (MAGI-MEM) | PV-13.a.1 … PV-13.e.2 | **PV-INT-16**: repositorio de emulador indexado → clasificación de capas con exactitud ≥ 0,92 → libro mayor con consulta Cypher como evidencia en el 100 % de las filas → binario ausente y camino de reserva funcionando |

| Puerta transversal nueva | Qué comprueba | Criterio |
|---|---|---|
| **PV-X-PRIV** (privacidad) | `route_call` y captura de tráfico | 0 peticiones `local_only` servidas por proveedor no local; 0 bytes de fotograma, página de expediente, dump o corpus saliendo sin consentimiento vigente |
| **PV-X-EXT** (externos) | `config/externals.lock` frente a la realidad | La enumeración efectiva de herramientas MCP, lenguajes y estrategias coincide con la fijada; cualquier deriva bloquea el arranque |


## T14 Addenda de las Áreas 15 y 16: ingesta universal y sistemas portables

**Enmienda a T1 (árbol de directorios).** Se añaden:

```
modules/ingest/            Área 15: cascada de 7 niveles, identificación, codificaciones, rescate
modules/portable/          Área 16: constructor, empaquetador, ejecutor en ventana, perfiles de época
formats/kaitai/            lectores declarativos aprendidos por el nivel 5 (crecen con el uso)
formats/registry.json      registro de formatos conocidos, su lector y su confianza
os/recipes/*.yaml          recetas de sistemas portables, con su .lock de fuentes
os/era/*.yaml              perfiles de entorno de época y sus secuencias de exportación
os/launcher/               lanzador Rust que produce el ejecutable único
tools/ingest/              conversores y lectores externos verificados por hash
gui/src/help/glossary.es.json   términos con definición de dos frases, usados en toda la interfaz
gui/src/help/wording.es.json    catálogo cerrado de rótulos y mensajes de la interfaz
tests/corpus/legacy/       corpus de 400 ficheros de época con verdad de terreno
tests/corpus/hostile/      ficheros malformados para probar el confinamiento
```

**Enmienda a T2 (eventos).** Se añaden: `ingest.started`, `ingest.level`, `ingest.finished`, `ingest.unknown_format`, `format.registered`, `os.build.started`, `os.build.progress`, `os.build.finished`, `vm.started`, `vm.stopped`, `vm.snapshot` y **`vm.escape_attempt`** (criticidad **crítica**, nunca se descarta, va directo a la auditoría).

**Enmienda a T3 (base de datos).** Se añaden nueve tablas:

```sql
CREATE TABLE ingest_job (
  ingest_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES project(project_id),
  source_sha256 TEXT NOT NULL, source_name TEXT, bytes INTEGER, source_mtime TEXT,
  format_name TEXT, format_family TEXT, format_confidence REAL, era TEXT,
  resolved_level INTEGER, status TEXT NOT NULL
    CHECK (status IN ('leido_completo','leido_parcial','abierto_en_entorno_de_epoca','no_legible')),
  encoding TEXT, encoding_confidence REAL, line_endings TEXT,
  fidelity_json TEXT, content_ref TEXT, created_at TEXT NOT NULL);
CREATE INDEX ix_ingest_status ON ingest_job(project_id, status);

CREATE TABLE ingest_attempt (
  attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
  ingest_id TEXT NOT NULL REFERENCES ingest_job(ingest_id),
  level INTEGER NOT NULL, tool TEXT NOT NULL, tool_version TEXT,
  ok INTEGER NOT NULL, reason TEXT, duration_ms INTEGER);

CREATE TABLE format_registry (
  format_name TEXT PRIMARY KEY, family TEXT NOT NULL, era TEXT,
  magic_json TEXT, reader_kind TEXT NOT NULL
    CHECK (reader_kind IN ('native','library','converter','kaitai','era_env','salvage')),
  reader_ref TEXT, confidence REAL, learned_from_round TEXT, registered_at TEXT NOT NULL);

CREATE TABLE format_sample (
  sample_id INTEGER PRIMARY KEY AUTOINCREMENT, format_name TEXT REFERENCES format_registry(format_name),
  sha256 TEXT NOT NULL, bytes INTEGER, header_hex TEXT, used_for_learning INTEGER DEFAULT 0);

CREATE TABLE os_recipe (
  recipe_id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, base TEXT NOT NULL, arch TEXT NOT NULL,
  yaml_ref TEXT NOT NULL, lock_sha256 TEXT NOT NULL, created_at TEXT NOT NULL);

CREATE TABLE os_image (
  image_id TEXT PRIMARY KEY, recipe_id TEXT NOT NULL REFERENCES os_recipe(recipe_id),
  sha256 TEXT NOT NULL, size_bytes INTEGER, reproducible INTEGER NOT NULL DEFAULT 0,
  divergent_file TEXT, manifest_json TEXT NOT NULL,      -- componentes, versiones, licencias, hashes
  redistributable INTEGER NOT NULL DEFAULT 1,            -- alimenta CTL-4
  built_at TEXT NOT NULL);

CREATE TABLE os_artifact (
  artifact_id TEXT PRIMARY KEY, image_id TEXT NOT NULL REFERENCES os_image(image_id),
  target TEXT NOT NULL CHECK (target IN ('windows','linux')),
  engine TEXT NOT NULL CHECK (engine IN ('qemu','wasm','dosbox')),
  sha256 TEXT NOT NULL, size_bytes INTEGER,
  clean_machine_test INTEGER NOT NULL DEFAULT 0,          -- 0 = no publicable
  built_at TEXT NOT NULL);

CREATE TABLE vm_session (
  session_id TEXT PRIMARY KEY, image_id TEXT REFERENCES os_image(image_id),
  engine TEXT NOT NULL, accel TEXT, network TEXT NOT NULL DEFAULT 'none',
  shared_folder TEXT, started_at TEXT NOT NULL, stopped_at TEXT, stop_reason TEXT,
  escape_attempts INTEGER NOT NULL DEFAULT 0);

CREATE TABLE era_profile (
  profile_id TEXT PRIMARY KEY, name TEXT NOT NULL, base_image TEXT NOT NULL,
  formats_json TEXT NOT NULL, app_supplied_by_user INTEGER NOT NULL DEFAULT 1,
  export_sequence_json TEXT, stability_marker TEXT);
```

Consultas de control nuevas para `PV-X-SEG`: `SELECT COUNT(*) FROM os_artifact WHERE clean_machine_test=0` debe ser **0** entre los publicados; `SELECT COUNT(*) FROM vm_session WHERE escape_attempts>0` debe ser **0**; y `SELECT COUNT(*) FROM ingest_job WHERE status='no_legible' AND NOT EXISTS (SELECT 1 FROM ingest_attempt a WHERE a.ingest_id=ingest_job.ingest_id AND a.level>=7)` debe ser **0** — nada se declara ilegible sin haber pasado por el rescate.

**Enmienda a T5 (orden topológico).** El orden final es:
`core` → `prompts` → `capabilities` → `route` → `resilience` → `debate` → `executor` → **`portable`** → **`ingest`** → `devices` → `forensic` → `contrast` → `memgraph` → `re` → `fabrication` → `invention` → `mcp` → `gui`.
`portable` precede a `ingest` porque el nivel 6 de la cascada lo necesita; ambos preceden a `forensic` y `contrast` porque son quienes les entregan los documentos.

**Enmienda a T6 (dependencias externas).** Filas nuevas, todas libres: LibreOffice 24.8 (MPL-2.0, proceso separado), Gnumeric 1.12 (GPL-2.0, proceso separado), Apache Tika 3.x (Apache-2.0, requiere Java 21), ImageMagick 7.1 (ImageMagick License), netpbm 11.x (varias libres), unar/lsar 1.10 (LGPL-2.1), p7zip 17.05 (LGPL), mtools 4.0 / hfsutils / cpmtools 2.2x / libdsk 1.5 (GPL), mdbtools 1.0 (GPL/LGPL), libpff y readpst 0.6 (LGPL/GPL), chmlib (LGPL), fontforge 2024 (GPL-3.0), uchardet (MPL), Kaitai Struct 0.10 (GPL/MIT según componente), QEMU 9.x (**GPL-2.0**, proceso separado), Buildroot 2024.x (GPL-2.0, sólo herramienta de construcción), DOSBox-X (GPL-2.0), emulador x86 en WebAssembly (BSD-2), xorriso (GPL-3.0). **Nota de licencia:** todas se invocan como procesos separados o son herramientas de construcción, de modo que ninguna altera la licencia AGPL-3.0 del producto ya decidida en §T6; **los sistemas operativos base empaquetados sí acompañan al artefacto**, y por eso el manifiesto de licencias y CTL-4 son obligatorios: un ejecutable con Buildroot/Linux dentro debe distribuirse cumpliendo la GPL, incluida la oferta de fuentes, y el empaquetador lo incluye automáticamente en `--manifest`.

**Enmienda a T7 (presupuesto de recursos).** Tres escenarios nuevos:

| Escenario | RAM | Disco | Tiempo | Notas |
|---|---|---|---|---|
| Ingesta de un lote de 500 ficheros de época | 1,2 GB (LibreOffice residente) | 3 GB | 25–60 min | Trabajo reanudable; el trabajador confinado se limita a 512 MB por fichero |
| Construcción de un sistema portable (Buildroot) | 3,5 GB | **4–8 GB de caché de fuentes** + 2 GB de salida | 8–35 min la primera vez | Exclusivo con `TOOLCHAIN_HEAVY`; el caché es lo más pesado de todo el sistema |
| Sesión de máquina en ventana | Lo declarado en la receta + 250 MB | Imagen + instantáneas | Continuo | Con aceleración es cómodo; sin ella, funcional y lento |

El total de disco «todo instalado» pasa de **≈ 55–80 GB** a **≈ 62–92 GB**, y sigue cabiendo en los 100 GB declarados si el kit de fabricación de silicio y el caché de Buildroot no se instalan a la vez; la interfaz lo dice antes de descargar nada.

**Enmienda a T8 (hoja de ruta).** El **Área 15 entra en F1** en sus niveles 0 a 4 —porque el primer hito de F1 es «un contrato escaneado entra y sale un dictamen», y ese contrato puede venir en cualquier formato— y se completa en F3 con los niveles 5 a 7. El **Área 16 entra en F2** con la ejecución en ventana y el ejecutable único, y se completa en F4 con los perfiles de época. La **interfaz conversacional con sus dos secciones, la barra de instrucción y el sistema de diseño T12 entran en F1**: son la diferencia entre un producto y una demostración.

**Enmienda a T9 (riesgos).** Dos riesgos nuevos en el top:

| # | Riesgo | Prob. | Impacto | Mitigación | Señal temprana |
|---|---|---|---|---|---|
| 2-ter | **Ejecución de código por un analizador de formato antiguo vulnerable** — el sistema abre por diseño ficheros de origen desconocido | Media | **Crítico** | Trabajador confinado sin red ni escritura (§6.3 C-2), corpus hostil obligatorio en el banco, y ningún analizador en el proceso del núcleo | Cualquier caída del trabajador con el corpus hostil |
| 5-bis | **Falsa portabilidad** — el ejecutable único funciona en la máquina de quien lo construyó y en ninguna otra | Alta | Alto | Prueba de humo obligatoria en contenedor vacío que **bloquea la publicación**; `clean_machine_test` en la base de datos | Cualquier `os_artifact` con `clean_machine_test=0` |

**Enmienda a T11 (plan maestro).** Dos filas y una puerta transversal nuevas:

| Orden | Paso | Puertas propias | Puerta de integración |
|---|---|---|---|
| 7-bis | P16.a–P16.e (sistemas portables) | PV-16.a.1 … PV-16.e.2 | **PV-INT-17**: receta → construcción reproducible → ejecutable único → arranque en contenedor vacío → sesión sin red verificada con captura de tráfico |
| 8-bis | P15.a–P15.f (ingesta universal) | PV-15.a.1 … PV-15.f.2 | **PV-INT-18**: corpus de 400 ficheros de época → ≥ 92 % legibles → los no legibles descienden al entorno de época → informe de fidelidad por fichero, con el original intacto |

| Puerta transversal nueva | Qué comprueba | Criterio |
|---|---|---|
| **PV-X-SBX** (confinamiento) | Corpus hostil de `tests/corpus/hostile/` procesado por las Áreas 1, 5 y 15 | 0 caídas del núcleo, 0 escrituras fuera del temporal del trabajador, 0 conexiones de red, 10/10 ejecuciones |

**Enmienda a T10 (glosario).** Se añaden: **Cascada de ingesta** — los siete niveles del Área 15. · **Entorno de época** — sistema y aplicación originales arrancados para abrir un fichero antiguo. · **Ejecutable único** — un solo fichero que lleva dentro el sistema y su motor y arranca con doble clic. · **Instantánea de máquina** — copia del estado de una sesión que permite volver atrás. · **Kaitai Struct** — lenguaje para describir formatos binarios y generar lectores. · **Bifurcación de recurso** — segunda parte de un fichero en los Mac clásicos, donde a veces está el contenido de verdad. · **Conversación / Proyectos** — las dos secciones de la interfaz. · **Instrucción (`prompt`)** — lo que el usuario pide al sistema. · **Fidelidad** — cuánto del documento original se ha conservado al leerlo. · **CTL-4** — control que impide empaquetar software no redistribuible.


## T15 Addenda de la interfaz conversacional, el Área 17 y la deliberación multi-ronda

**Enmienda a T1 (árbol de directorios).** Se añaden:

```
modules/conversation/      hilos, turnos, ramas, herencia de contexto, promoción a proyecto
modules/config/            Área 17: árbol de esquemas, fusión por capas, calibradores
config/factory.yaml        valores de fábrica (sólo lectura)
config/machine.yaml        resultado del calibrador de perfil de máquina
config/presets/*.yaml      los seis preajustes completos
gui/src/conversation/      hilo, tarjetas de turno, trayectoria, composer
gui/src/settings/          pantalla generada desde los esquemas y asistentes de calibración
```

**Enmienda a T2 (eventos).** Se añaden: `conversation.created`, `conversation.turn`, `conversation.branch`, `conversation.promoted`, `debate.round{deliberation_id, round_index, provisional_score, new_refutations, refined, resolved}`, `debate.model_switch{node, from, to, round}` (**crítico**: alimenta §I.8), `config.changed`, `config.reverted`, `calibration.started`, `calibration.finished`.

**Enmienda a T3 (base de datos).** Ocho tablas nuevas:

```sql
CREATE TABLE conversation (
  conversation_id TEXT PRIMARY KEY, project_id TEXT REFERENCES project(project_id),  -- NULL = sección Conversación
  title TEXT NOT NULL, created_at TEXT NOT NULL, last_turn_at TEXT, archived INTEGER DEFAULT 0);

CREATE TABLE conversation_turn (
  turn_id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES conversation(conversation_id),
  parent_turn_id TEXT REFERENCES conversation_turn(turn_id),   -- ramas
  idx INTEGER NOT NULL, prompt TEXT NOT NULL, attachments_json TEXT,
  kind TEXT NOT NULL CHECK (kind IN ('nuevo','continuar','reejecutar','mas_rondas','interpelar','restriccion')),
  target_node TEXT CHECK (target_node IN ('MELCHIOR','BALTHASAR','CASPER',NULL)),
  deliberation_id TEXT, config_hash TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE INDEX ix_turn_conv ON conversation_turn(conversation_id, idx);

CREATE TABLE deliberation (
  deliberation_id TEXT PRIMARY KEY, topic_id TEXT NOT NULL, area INTEGER NOT NULL,
  rounds_min INTEGER NOT NULL CHECK (rounds_min >= 3), rounds_max INTEGER NOT NULL,
  rounds_executed INTEGER NOT NULL, selected_proposal_version INTEGER,
  final_outcome TEXT, final_score INTEGER, stop_reason TEXT,
  config_hash TEXT NOT NULL, acta_json TEXT NOT NULL, acta_sha256 TEXT NOT NULL,
  started_at TEXT NOT NULL, ended_at TEXT,
  CHECK (rounds_executed >= rounds_min));

CREATE TABLE deliberation_round (
  deliberation_id TEXT NOT NULL REFERENCES deliberation(deliberation_id),
  round_index INTEGER NOT NULL, proposal_version INTEGER NOT NULL,
  provisional_score INTEGER, new_refutations INTEGER, refined_refutations INTEGER, resolved INTEGER,
  casper_analysis_hash TEXT NOT NULL, guidance_json TEXT NOT NULL,
  continue_flag INTEGER NOT NULL, PRIMARY KEY (deliberation_id, round_index));

CREATE TABLE model_identity (
  identity_id TEXT PRIMARY KEY, node TEXT NOT NULL CHECK (node IN ('MELCHIOR','BALTHASAR','CASPER','VLM','EMBED','RERANK')),
  display TEXT NOT NULL, family TEXT NOT NULL, params_b REAL, quant TEXT, ctx INTEGER,
  provider TEXT NOT NULL, endpoint TEXT, weights_sha256 TEXT,
  temperature REAL, top_p REAL, seed INTEGER, grammar TEXT, runtime TEXT, accel TEXT,
  degraded TEXT);

CREATE TABLE model_switch (
  switch_id INTEGER PRIMARY KEY AUTOINCREMENT, deliberation_id TEXT NOT NULL,
  round_index INTEGER NOT NULL, node TEXT NOT NULL,
  from_identity TEXT NOT NULL REFERENCES model_identity(identity_id),
  to_identity TEXT NOT NULL REFERENCES model_identity(identity_id),
  reason TEXT NOT NULL, ts TEXT NOT NULL);

CREATE TABLE config_value (
  scope TEXT NOT NULL CHECK (scope IN ('factory','machine','user','project','turn')),
  scope_ref TEXT, path TEXT NOT NULL, value_json TEXT NOT NULL, set_at TEXT NOT NULL,
  PRIMARY KEY (scope, scope_ref, path));

CREATE TABLE config_history (
  change_id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT NOT NULL, scope TEXT NOT NULL,
  from_json TEXT, to_json TEXT NOT NULL, actor TEXT NOT NULL, reason TEXT,
  calibration_run_id TEXT, ts TEXT NOT NULL);

CREATE TABLE calibration_run (
  run_id TEXT PRIMARY KEY, calibrator TEXT NOT NULL, started_at TEXT NOT NULL, ended_at TEXT,
  measurements_json TEXT, proposals_json TEXT, accepted_json TEXT, report_ref TEXT);
```

Consultas de control nuevas para `PV-X-SEG`: `SELECT COUNT(*) FROM deliberation WHERE rounds_executed < 3` debe ser **0**; `SELECT COUNT(*) FROM deliberation_round WHERE casper_analysis_hash IS NULL` debe ser **0**; y `SELECT COUNT(*) FROM model_run WHERE identity_id IS NULL` debe ser **0** (§I.8).

**Enmienda a T5 (orden topológico).** Se inserta `config` justo después de `core` —porque todo lo demás lee configuración— y `conversation` antes de `gui`:
`core` → **`config`** → `prompts` → `capabilities` → `route` → `resilience` → `debate` → `executor` → `portable` → `ingest` → `devices` → `forensic` → `contrast` → `memgraph` → `re` → `fabrication` → `invention` → **`conversation`** → `mcp` → `gui`.

**Enmienda a T7 (presupuesto).** La deliberación pasa de una media de 3 rondas a un mínimo de 3 y una media de 5: el escenario «debate intensivo» sube de **≈ 68 000 a ≈ 114 000 tokens** y de 2 min 30 s a **≈ 4 min 10 s** en Perfil A. Es el coste directo de la exigencia de varias rondas, se declara sin adornos, y el calibrador de calidad de deliberación (§17.4) existe precisamente para saber si ese gasto compra algo en cada configuración concreta.

**Enmienda a T8 (hoja de ruta).** El **Área 17 entra en F1** en su núcleo (esquemas, fusión, pantalla generada, persistencia): sin ella, cada área inventa su propia forma de configurarse y luego es irreparable. Los calibradores llegan en F2 (máquina, modelos), F3 (deliberación, ingesta) y F4 (forense, impresora, instrumentos, esfuerzo). La **interfaz conversacional con las dos secciones entra en F1** y la deliberación multi-ronda **también en F1**, porque es el corazón del sistema y retroencajarla después obligaría a rehacer el acta.

**Enmienda a T9 (riesgos).** Un riesgo nuevo:

| # | Riesgo | Prob. | Impacto | Mitigación | Señal temprana |
|---|---|---|---|---|---|
| 3-bis | **Las rondas adicionales no mejoran nada y sólo multiplican el coste** — el sistema gasta cinco veces más para el mismo resultado | Media | Alto | Calibrador de calidad de deliberación (§A17-2) que **mide** la ganancia marginal por ronda y puede recomendar el mínimo de 3; trayectoria visible en la interfaz; detección de meseta que corta | Trayectorias planas en el panel: la puntuación de la ronda 5 igual a la de la 3 |

**Enmienda a T11 (plan maestro).** Dos filas y una puerta transversal:

| Orden | Paso | Puertas propias | Puerta de integración |
|---|---|---|---|
| 1-bis | P17.a–P17.e (configuración) | PV-17.a.1 … PV-17.e.1 | **PV-INT-19**: 0 campos huérfanos, `rounds.min` no bajable de 3 por ninguna vía, `config_hash` en el 100 % de actas y artefactos |
| 14-bis | Conversación e interfaz | PV-10.a.1 … PV-10.d.5 | **PV-INT-20**: hilo con 6 turnos encadenados, uno de ellos «pedir más rondas» y otro «reejecutar con cambios», con ramas visibles, identidad de modelo en el 100 % de los mensajes y promoción a proyecto sin pérdida |

| Puerta transversal nueva | Qué comprueba | Criterio |
|---|---|---|
| **PV-X-RND** (deliberación) | Toda deliberación registrada | `rounds_executed ≥ 3` en el 100 %; `full_analysis` de CASPER presente en todas las rondas; `selected_proposal_version` justificada cuando no es la última |
| **PV-X-MID** (identidad de modelo) | Todo turno y todo artefacto | Bloque `model_identity` completo en el 100 %; todo cambio de modelo con su registro en `model_switch` |

**Enmienda a T10 (glosario).** Se añaden: **Deliberación** — conjunto de rondas sobre un mismo tema; nunca menos de tres. · **Ronda** — ciclo MELCHIOR → BALTHASAR → CASPER dentro de una deliberación. · **Versión de propuesta** — cada revisión que MELCHIOR • 1 produce en una ronda. · **Análisis de ronda** — informe completo que CASPER • 3 emite en cada ronda, con instrucciones para los otros dos. · **Trayectoria** — evolución de la puntuación ronda a ronda. · **Hilo** — conversación con sus turnos y ramas. · **Turno** — una instrucción del usuario y todo lo que desencadena. · **Rama** — reejecución de un turno que conserva la anterior. · **Identidad de modelo** — bloque que declara qué inteligencia produjo cada salida. · **Capa de configuración** — fábrica, máquina, usuario, proyecto o turno. · **Calibrador** — procedimiento que mide en esta máquina y propone valores. · **`config_hash`** — huella de la configuración con que se produjo un resultado.


## T16 Addenda de las Áreas 18 y 19: memoria íntegra y navegación gobernada

**Enmienda a T1 (árbol de directorios).**

```
modules/memory/            Área 18: registro íntegro, estado acumulado, compositor, traspaso
modules/memory/nosummary.py   assert_verbatim: prohibición mecánica del resumen
modules/web/               Área 19: adaptador, puerta de política, empaquetador de evidencia
modules/web/policy.py      CTL-5 propósito · CTL-6 rotación imposible · CTL-7 lista negra
tools/magi-web/<version>/  servidor de navegación en la versión fijada
config/web_allowlist.yaml  dominios permitidos por proyecto, con su propósito
config/factory.yaml        (ampliado) lista negra permanente de CTL-7, sólo lectura
tests/memory/handover/     50 escenarios de traspaso con verificación de no pérdida
tests/web/evidence/        40 páginas de referencia para el banco de ahorro y reproducibilidad
```

**Enmienda a T2 (eventos).** Se añaden: `memory.appended`, `memory.fetch`, `memory.overflow`, `memory.chain_broken` (**crítico**), `handover.started`, `handover.verified`, `handover.failed` (**crítico**), `web.opened`, `web.snapshot`, `web.evidence`, `web.blocked` (**crítico**), `web.session_used`.

**Enmienda a T3 (base de datos).** Diez tablas nuevas:

```sql
CREATE TABLE memory_record (
  record_id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK (kind IN ('deliberation','conversation')),
  ref_id TEXT NOT NULL, chain_head_sha256 TEXT NOT NULL, items INTEGER NOT NULL DEFAULT 0,
  bytes_text INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);

CREATE TABLE memory_item (
  item_id TEXT PRIMARY KEY, record_id TEXT NOT NULL REFERENCES memory_record(record_id),
  seq INTEGER NOT NULL, kind TEXT NOT NULL, author TEXT NOT NULL,
  round_index INTEGER, proposal_version INTEGER,
  text_ref TEXT NOT NULL,                     -- CAS: texto LITERAL, jamás reescrito
  tokens INTEGER, model_identity_id TEXT REFERENCES model_identity(identity_id),
  partial INTEGER NOT NULL DEFAULT 0,
  sha256 TEXT NOT NULL, prev_hash TEXT NOT NULL, created_at TEXT NOT NULL,
  UNIQUE(record_id, seq));
CREATE TRIGGER trg_mem_no_update BEFORE UPDATE ON memory_item
  BEGIN SELECT RAISE(ABORT,'memory_item es inmutable'); END;
CREATE TRIGGER trg_mem_no_delete BEFORE DELETE ON memory_item
  BEGIN SELECT RAISE(ABORT,'memory_item es inmutable'); END;

CREATE TABLE memory_state (
  record_id TEXT NOT NULL REFERENCES memory_record(record_id), element_id TEXT NOT NULL,
  element_kind TEXT NOT NULL, status TEXT NOT NULL, item_id TEXT NOT NULL REFERENCES memory_item(item_id),
  PRIMARY KEY (record_id, element_id));

CREATE TABLE context_manifest (
  turn_id TEXT PRIMARY KEY, record_id TEXT NOT NULL, item_ids_json TEXT NOT NULL,
  hashes_json TEXT NOT NULL, tokens INTEGER NOT NULL, mode TEXT NOT NULL
    CHECK (mode IN ('completo','direccionado','direccionado_puro')), created_at TEXT NOT NULL);

CREATE TABLE memory_fetch_log (
  fetch_id INTEGER PRIMARY KEY AUTOINCREMENT, turn_id TEXT NOT NULL, item_id TEXT NOT NULL,
  tokens INTEGER, ts TEXT NOT NULL);
CREATE INDEX ix_fetch_turn ON memory_fetch_log(turn_id);

CREATE TABLE handover (
  handover_id TEXT PRIMARY KEY, deliberation_id TEXT, conversation_id TEXT, node TEXT NOT NULL,
  at_round INTEGER, from_identity TEXT NOT NULL REFERENCES model_identity(identity_id),
  to_identity TEXT NOT NULL REFERENCES model_identity(identity_id), reason TEXT NOT NULL,
  items_before INTEGER NOT NULL, items_after INTEGER NOT NULL, chain_head_sha256 TEXT NOT NULL,
  window_downgrade INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL CHECK (status IN ('verified','failed','pending')), ts TEXT NOT NULL,
  CHECK (items_after >= items_before));

CREATE TABLE handover_check (
  check_id INTEGER PRIMARY KEY AUTOINCREMENT, handover_id TEXT NOT NULL REFERENCES handover(handover_id),
  question_kind TEXT NOT NULL, expected TEXT NOT NULL, answered TEXT, exact_match INTEGER NOT NULL);

CREATE TABLE web_evidence (
  evidence_id TEXT PRIMARY KEY, project_id TEXT, url TEXT NOT NULL, final_url TEXT,
  fetched_at TEXT NOT NULL, http_status INTEGER, purpose TEXT NOT NULL,
  robots_allowed INTEGER NOT NULL, session_name TEXT,
  html_sha256 TEXT, snapshot_ref TEXT, screenshot_ref TEXT, text_ref TEXT, trace_ref TEXT,
  headers_ref TEXT, engine_json TEXT NOT NULL, reproduce_cmd TEXT NOT NULL,
  tokens_html INTEGER, tokens_snapshot INTEGER);
CREATE INDEX ix_webev_url ON web_evidence(url, fetched_at DESC);

CREATE TABLE web_session (
  session_name TEXT PRIMARY KEY, owner TEXT NOT NULL DEFAULT 'user', domain TEXT NOT NULL,
  consented_at TEXT NOT NULL, expires_at TEXT, closed_at TEXT);

CREATE TABLE web_policy_log (
  log_id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT NOT NULL, domain TEXT NOT NULL,
  purpose TEXT, decision TEXT NOT NULL CHECK (decision IN ('permitido','bloqueado','excepcion_autorizada')),
  reason TEXT, decided_by TEXT NOT NULL, ts TEXT NOT NULL);
```

Consultas de control nuevas para `PV-X-SEG`:
`SELECT COUNT(*) FROM handover WHERE items_after <> items_before` debe ser **0** — ninguna pérdida en un traspaso.
`SELECT COUNT(*) FROM handover WHERE status <> 'verified'` entre los aplicados debe ser **0** — ningún relevo sin prueba de recepción superada.
`SELECT COUNT(*) FROM web_policy_log WHERE decision='permitido' AND purpose IS NULL` debe ser **0** — ninguna navegación sin propósito declarado.

**Enmienda a T5 (orden topológico).** `memory` entra justo después de `config`, porque el compositor de contexto es prerrequisito de `prompts` y de `debate`; `web` entra antes de `contrast`:
`core` → `config` → **`memory`** → `prompts` → `capabilities` → `route` → `resilience` → `debate` → `executor` → `portable` → `ingest` → **`web`** → `devices` → `forensic` → `contrast` → `memgraph` → `re` → `fabrication` → `invention` → `conversation` → `mcp` → `gui`.

**Enmienda a T6 (dependencias externas).** Dos filas: **MAGI-WEB (`camofox-browser`)**, versión fijada en `externals.lock`, licencia a registrar al fijarla, instalación por NPM local o imagen OCI, ~300 MB de motor más 40 MB en reposo, opcional con camino de reserva; y **`pyahocorasick` 2.x** (MIT) para el autómata de sufijos del Área 18, obligatoria. La coherencia de licencias no cambia: ambas se ejecutan como proceso separado o son librerías permisivas.

**Enmienda a T7 (presupuesto).** El registro íntegro añade **25–60 kB comprimidos por deliberación** (despreciable). El **modo direccionado** añade 2–6 recuperaciones por turno, ≈ 300 ms y 1 500–6 000 tokens; el escenario «debate intensivo» pasa de ≈ 114 000 a **≈ 132 000 tokens** y de 4 min 10 s a **≈ 4 min 45 s**. La **prueba de recepción** añade ≈ 6 000 tokens y 9–20 s por cambio de modelo. MAGI-WEB **reduce** el consumo: el escenario de invención baja de ≈ 500 000 a **≈ 180 000 tokens** por ciclo gracias a las instantáneas de accesibilidad. Balance neto: la memoria íntegra cuesta cerca de un 16 % más de tokens en deliberación; la navegación gobernada ahorra alrededor de un 64 % en investigación.

**Enmienda a T8 (hoja de ruta).** El **Área 18 entra en F1**, y no es negociable: retroencajar un registro íntegro después de haber construido el sistema sobre resúmenes obliga a reescribir el acta, el compilador de prompts y el traspaso de proveedor. El **Área 19 entra en F2**, con su puerta de política **desde el primer día** — un navegador de este tipo sin puerta no debe existir ni en desarrollo.

**Enmienda a T9 (riesgos).** Dos riesgos nuevos:

| # | Riesgo | Prob. | Impacto | Mitigación | Señal temprana |
|---|---|---|---|---|---|
| 1-bis | **Reintroducción del resumen por presión de contexto** — alguien añade «sólo para lo antiguo» y la memoria vuelve a ser una paráfrasis | Alta | **Crítico** | `assert_verbatim` en el camino crítico con tolerancia cero; abortar es un fallo de programación, no una advertencia | Cualquier `SummaryDetected` en desarrollo, o un `PV-18.b.1` en rojo |
| 6-bis | **Uso del navegador para lo que el plan prohíbe** — la misma herramienta sirve para investigar y para evadir | Media | **Crítico** | CTL-5, CTL-6 y CTL-7 en código; el adaptador **no expone** parámetro de proxy; vigilante cada 10 min; lista negra no reducible; rechazo de configuración importada que los toque | Cualquier `web.blocked{reason:"policy"}` o cambio del perfil de huella |

**Enmienda a T11 (plan maestro).** Dos filas y dos puertas transversales:

| Orden | Paso | Puertas propias | Puerta de integración |
|---|---|---|---|
| 1-ter | P18.a–P18.e (memoria íntegra) | PV-18.a.1 … PV-18.e.1 | **PV-INT-21**: deliberación de 7 rondas con 3 cambios de modelo forzados: conjuntos de elementos idénticos, 3 pruebas de recepción superadas, 0 resúmenes, cuestionario de detalles ≥ 95 % |
| 11-bis | P19.a–P19.d (navegación) | PV-19.a.1 … PV-19.d.2 | **PV-INT-22**: 40 páginas capturadas con evidencia reproducible, ahorro ≥ 75 %, 20 bloqueos de lista negra, 0 telemetría, camino de reserva verificado |

| Puerta transversal | Qué comprueba | Criterio |
|---|---|---|
| **PV-X-MEM** (memoria) | Todo prompt y todo traspaso | 0 fragmentos de memoria que no existan literalmente en el registro; 0 traspasos con pérdida; 0 relevos sin prueba de recepción superada |
| **PV-X-WEB** (navegación) | Todo acceso web | 0 accesos sin propósito declarado; 0 rotaciones de identidad posibles; `robots.txt` respetado salvo excepción autorizada y registrada |

**Enmienda a T10 (glosario).** **Registro íntegro** — memoria literal, inmutable y encadenada por hash de todo lo dicho. · **Estado estructurado acumulado** — todos los elementos del registro, reorganizados por tipo y estado, con su texto literal. · **Direccionado** — modo en que el contexto no contiene todo pero todo es recuperable en el acto. · **`memory.fetch`** — herramienta con la que un nodo recupera literalmente cualquier elemento. · **Regla de lectura obligatoria** — no se puede afirmar nada sobre un elemento sin haberlo leído íntegro en ese turno. · **Traspaso** — cambio de modelo de un nodo, con paquete completo y prueba de recepción. · **Prueba de recepción** — cinco preguntas cuya respuesta está en el registro; sin superarlas no hay relevo. · **Inflación procedimental** — cuánto sube una puntuación por efecto del propio procedimiento. · **Ronda sombra** — control con críticas simuladas para detectar complacencia del juez. · **Regla de trinquete** — una versión no puntúa más alto sin resolver algo de forma comprobada. · **Instantánea de accesibilidad** — representación de una página pensada para agentes, mucho más barata que el HTML. · **Paquete de evidencia web** — congelación verificable de una página en un instante. · **CTL-5 / CTL-6 / CTL-7** — propósito declarado, rotación imposible y lista negra permanente.


## T17 Addenda de la inferencia en nube y de las Áreas 20 y 21

**Enmienda a T1 (árbol de directorios).**

```
modules/studio/            Área 20: especificación medible, generadores, medidores, bucle
modules/studio/rights.py   CTL-8: derechos e identidad, antes de generar
modules/shell/             Área 21: canal IPC, instancia única, emparejamiento de la extensión
modules/project/           carpeta de proyecto, repositorio, portabilidad, CTL-9
extension/                 extensión de navegador (manifiesto V3, mensajería nativa)
config/providers.yaml      registro de proveedores de nube, sin secretos, con ventanas de cuota
os/                        (sin cambios) recetas de sistemas portables
tests/studio/              encargos de referencia con criterios duros para el banco de autocorrección
tests/shell/portability/   proyectos de prueba para el clonado en contenedor limpio
```

**Enmienda a T2 (eventos).** Se añaden: `quota.reserved`, `quota.exhausted{provider, recovers_at}`, `quota.recovered`, `job.waiting_quota{eta}`, `provider.model_drift` (**crítico**), `studio.spec`, `studio.version`, `studio.measured`, `studio.converged`, `studio.blocked`, `app.started`, `app.ipc_ready`, `ext.paired`, `ext.page_sent`, `ext.blocked`, `project.created`, `repo.connected`, `repo.synced`, `repo.secret_blocked` (**crítico**), `project.portability`.

**Enmienda a T3 (base de datos).** Nueve tablas nuevas y una modificada:

```sql
-- La inferencia en nube sustituye la identidad por pesos con la del proveedor
ALTER TABLE model_identity ADD COLUMN provider_model_version TEXT;
ALTER TABLE model_identity ADD COLUMN quota_left_json TEXT;
-- weights_sha256 queda como NULL en todos los registros: no hay pesos locales

CREATE TABLE quota_ledger (
  provider_id TEXT NOT NULL, window_start TEXT NOT NULL,
  unit TEXT NOT NULL CHECK (unit IN ('requests','tokens')),
  limit_declared INTEGER, limit_observed INTEGER, consumed INTEGER NOT NULL DEFAULT 0,
  reserved INTEGER NOT NULL DEFAULT 0, exhausted_at TEXT, recovers_at TEXT,
  PRIMARY KEY (provider_id, window_start));

CREATE TABLE quota_reservation (
  reservation_id TEXT PRIMARY KEY, provider_id TEXT NOT NULL, unit TEXT NOT NULL,
  amount INTEGER NOT NULL, job_id TEXT, turn_id TEXT, state TEXT NOT NULL
    CHECK (state IN ('held','consumed','released')), ts TEXT NOT NULL);

CREATE TABLE canary_probe (
  probe_id INTEGER PRIMARY KEY AUTOINCREMENT, provider_id TEXT NOT NULL, model TEXT NOT NULL,
  window_start TEXT NOT NULL, expected_hash TEXT NOT NULL, got_hash TEXT NOT NULL,
  drift INTEGER NOT NULL, ts TEXT NOT NULL);

CREATE TABLE media_spec (
  spec_id TEXT PRIMARY KEY, project_id TEXT, kind TEXT NOT NULL
    CHECK (kind IN ('game','music','image','animation','comic','video')),
  brief TEXT NOT NULL, style_json TEXT NOT NULL, constraints_json TEXT NOT NULL,
  acceptance_json TEXT NOT NULL, rights_json TEXT NOT NULL, created_at TEXT NOT NULL);

CREATE TABLE media_version (
  spec_id TEXT NOT NULL REFERENCES media_spec(spec_id), version INTEGER NOT NULL,
  artifact_ref TEXT NOT NULL, rendered_ref TEXT, hard_passed INTEGER, hard_total INTEGER,
  verdict_score INTEGER, selected INTEGER NOT NULL DEFAULT 0, ts TEXT NOT NULL,
  PRIMARY KEY (spec_id, version));

CREATE TABLE media_measurement (
  spec_id TEXT NOT NULL, version INTEGER NOT NULL, metric TEXT NOT NULL,
  value REAL, unit TEXT, passed INTEGER, method TEXT NOT NULL,
  PRIMARY KEY (spec_id, version, metric));

CREATE TABLE playtest_run (
  run_id TEXT PRIMARY KEY, spec_id TEXT NOT NULL, version INTEGER NOT NULL, seed INTEGER NOT NULL,
  completed INTEGER NOT NULL, time_s REAL, deaths INTEGER, fps_p05 REAL,
  softlocks INTEGER, crashes INTEGER, video_ref TEXT, ts TEXT NOT NULL);

CREATE TABLE ext_pairing (
  pairing_id TEXT PRIMARY KEY, browser TEXT NOT NULL, extension_id TEXT NOT NULL,
  paired_at TEXT NOT NULL, revoked_at TEXT, UNIQUE(browser, extension_id));

CREATE TABLE project_repo (
  project_id TEXT PRIMARY KEY, folder_path TEXT NOT NULL, remote_url TEXT,
  auth_kind TEXT CHECK (auth_kind IN ('device_flow','os_credential_store',NULL)),
  last_push TEXT, last_pull TEXT, exclude_blobs INTEGER NOT NULL DEFAULT 1);

CREATE TABLE repo_sync_log (
  sync_id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL, direction TEXT NOT NULL,
  files INTEGER, bytes INTEGER, secrets_blocked INTEGER NOT NULL DEFAULT 0,
  confirmed_by TEXT NOT NULL, ts TEXT NOT NULL);
```

Consultas de control nuevas para `PV-X-SEG`:
`SELECT COUNT(*) FROM repo_sync_log WHERE confirmed_by IS NULL OR confirmed_by='system'` debe ser **0** — ninguna publicación sin confirmación humana.
`SELECT COUNT(*) FROM media_version WHERE selected=1 AND hard_passed < hard_total` debe ser **0** — nada se entrega como terminado sin cumplir sus criterios duros.
`SELECT COUNT(*) FROM model_identity WHERE provider_model_version IS NULL` debe ser **0** — no hay inferencia sin versión de proveedor registrada.

**Enmienda a T5 (orden topológico).** `shell` y `project` van inmediatamente después de `core` porque definen dónde vive todo lo demás; `studio` va al final, antes de la interfaz:
`core` → **`shell`** → **`project`** → `config` → `memory` → `prompts` → `capabilities` → `route` → `resilience` → `debate` → `executor` → `portable` → `ingest` → `web` → `devices` → `forensic` → `contrast` → `memgraph` → `re` → `fabrication` → `invention` → **`studio`** → `conversation` → `mcp` → `gui`.

**Enmienda a T6 (dependencias externas).** **Se eliminan**: `llama.cpp`, Ollama y los pesos GGUF (12–35 GB) — ya no hay inferencia local. **Se añaden**: Godot 4.x (MIT), `Pillow` 10.x (HPND), `cairosvg`/`resvg` (LGPL/MPL, proceso separado), `music21` 9.x (BSD), FluidSynth 2.3 (LGPL) con bancos de sonido de libre distribución, SuperCollider 3.13 (GPL, proceso separado), `pyloudnorm` (MIT), `scikit-image` (BSD). El **tamaño de instalación baja de 55–92 GB a 8–14 GB**, que es el efecto colateral más agradable de esta revisión.

**Enmienda a T7 (presupuesto de recursos).** Cambia por completo al desaparecer la inferencia local:

| Escenario | RAM | VRAM | Disco | Notas |
|---|---|---|---|---|
| Reposo | 0,7 GB | **0** | — | Sin modelos residentes |
| Deliberación de 5 rondas | 0,9 GB | **0** | — | El coste es de **cuota y latencia de red**, no de memoria |
| Análisis documental de 300 páginas | 2,1 GB | 0 | 4 GB | La visión ahora es de nube; el resto sigue siendo local |
| Decompilación larga | 8,5 GB | 0 | 25 GB + grafo | Sólo Ghidra; se puede hacer **sin conexión** |
| Creación de un juego con pruebas | 1,8 GB | 0 | 2 GB | Godot sin ventana |
| Sesión de fabricación | 1,2 GB | 0 | 3 GB | Sin conexión salvo la crítica |
| Todo instalado | — | — | **8–14 GB** | Frente a 55–92 GB de la revisión anterior |

**La GPU deja de ser necesaria y el requisito de 16 GB de RAM pasa a ser holgado.** A cambio, el sistema **no funciona sin conexión para nada que exija una inteligencia**, y su rendimiento depende de la latencia de red y de la cuota disponible.

**Enmienda a T8 (hoja de ruta).** El **Área 21 entra en F1** —el ejecutable, el canal sin puertos y el proyecto como carpeta son el cimiento de todo lo demás; la extensión llega en F2—. El **Área 20 entra en F3**, salvo el arte de píxeles y la música simbólica con su bucle, que se adelantan a F2 como banco de pruebas barato del mecanismo de autocorrección. La **columna de lienzo entra en F1** junto con la interfaz conversacional.

**Enmienda a T9 (riesgos).** Tres riesgos nuevos, dos de ellos en la cabecera de la lista:

| # | Riesgo | Prob. | Impacto | Mitigación | Señal temprana |
|---|---|---|---|---|---|
| 1-cuater | **Dependencia total de cuotas ajenas** — sin suelo local, un cambio de política de los proveedores deja el sistema sin deliberación | **Alta** | **Crítico** | Registro de proveedores con varios; libro de cuotas con suspensión y reanudación; **toda la mitad determinista del sistema sigue funcionando**; y la puerta de salida está documentada: si aparece la necesidad, reintroducir un proveedor local es añadir una fila al registro, no rehacer la arquitectura | Dos proveedores agotados a la vez de forma recurrente, o cualquier `provider.model_drift` |
| 2-quater | **Pérdida de la garantía de privacidad** — la clase `no_enviar` ya no puede analizarse con una inteligencia sin salir del equipo | **Alta** | **Crítico** | La clase no se envía **nunca** por defecto; análisis determinista local; permiso explícito por unidad de contenido con el proveedor nombrado; y declaración de qué quedó sin analizar | Cualquier petición de permiso rechazada que bloquee un análisis: indica que el usuario nota la pérdida |
| 7-bis | **Optimizar la métrica en vez de la obra** (Área 20) | Media | Medio | Crítica de BALTHASAR • 2 sobre lo que la medida no capta; el modo de fallo «cumple todo y es mala» está reconocido y se declara al usuario en vez de ocultarse | Rúbrica de estilo baja con medidas altas de forma repetida |

**Enmienda a T11 (plan maestro).** Tres filas y una puerta transversal:

| Orden | Paso | Puertas propias | Puerta de integración |
|---|---|---|---|
| 0-bis | P21.a–P21.d (aplicación y proyecto) | PV-21.a.1 … PV-21.d.2 | **PV-INT-23**: ejecutable sin puertos de interfaz, no abrible en navegador, proyecto clonado en contenedor limpio que **continúa la conversación** |
| 3-ter | Inferencia en nube (§I.3) | PV-I3.1 … PV-I3.4 | **PV-INT-24**: trabajo de 300 unidades que atraviesa **dos agotamientos de cuota**: se suspende, muestra el reloj, se reanuda solo y termina sin pérdida de memoria |
| 20-bis | P20.a–P20.e (estudio) | PV-20.a.1 … PV-20.e.2 | **PV-INT-25**: encargo de videojuego → especificación medible → 4 versiones con medidas crecientes → agente de prueba lo completa → se entrega la mejor versión, no la última |

| Puerta transversal | Qué comprueba | Criterio |
|---|---|---|
| **PV-X-CUOTA** | Todo trabajo largo | 0 trabajos fallidos por agotamiento de cuota; 100 % suspendidos con hora de reanudación visible y reanudados sin pérdida |
| **PV-X-EXE** | La aplicación | 0 puertos de interfaz; 0 direcciones abribles en un navegador; 0 publicaciones a repositorio sin confirmación humana |

**Enmienda a T10 (glosario).** **Ventana de cuota** — periodo tras el cual un proveedor gratuito repone su límite. · **Libro de cuotas** — registro por proveedor del límite declarado, el observado, lo consumido y la hora de recuperación. · **Suspensión por cuota** — estado en que un trabajo espera a que se reponga el límite, sin perder nada. · **Sonda canaria** — comprobación periódica de que el proveedor no ha cambiado el modelo por debajo. · **Clase `no_enviar`** — contenido que nunca sale del equipo sin permiso explícito por unidad. · **Lienzo** — columna derecha donde se ve el plan, el código, la imagen, el gráfico o la vista previa. · **Especificación medible** — descripción de una obra con criterios comprobables antes de generarla. · **Agente de prueba de juego** — programa que juega automáticamente para verificar que el juego es completable. · **Ficha de estilo** — datos que fijan paleta, línea y proporciones para que una serie sea coherente. · **Mensajería nativa** — canal por el que una extensión habla con un programa instalado sin abrir puertos. · **Carpeta de proyecto** — el proyecto entero como objeto portable en el disco. · **CTL-8 / CTL-9 / CTL-10** — derechos e identidad en la obra generada, barrido de secretos antes de publicar, y separación de caminos entre navegación e inferencia.


---

# Parte IV — Auto-verificación final

## 6.1 Tabla de cobertura

Veintidós áreas y diecisiete artefactos transversales. **≈ 120 300 palabras.** Ninguna casilla contiene «N».

| Área / Artefacto | ¿Doce subsecciones? | Decisiones | Casos con criterio numérico | Construibilidad | Palabras |
|---|---|---|---|---|---|
| Área 0 — Arquitectura global | **S** | 5 | 24 | 🟢 | 3 711 |
| Área 1 — Forense topográfico | **S** | 4 | 20 | 🟢 | 3 645 |
| Área 2 — Razonamiento contrastivo | **S** | 4 | 20 | 🟢 / 🟡 | 3 400 |
| Área 3 — Deliberación MAGI (rúbrica híbrida) | **S** | 8 | 26 | 🟢 / 🟡 (nube) | 5 383 |
| Área 4 — Telemetría de dispositivos | **S** | 3 | 23 | 🟡 / 🔴 | 3 586 |
| Área 5 — Ingeniería inversa y síntesis | **S** (13, §5.1 lo justifica) | 2 | 26 | 🟢 / 🟡 / 🔴 | 5 880 |
| Área 6 — Política de proveedores | **S** | 3 | 20 | 🟡 (nube) | 2 877 |
| Área 7 — Prompts (resumen derogado) | **S** | 4 | 18 | 🟢 | 4 710 |
| Área 8 — Ejecución autónoma | **S** | 3 | 22 | 🟢 | 3 139 |
| Área 9 — Fabricación y electrónica | **S** | 11 | 37 | 🟢 / 🟡 / 🔴 | 8 479 |
| **Área 10 — Interfaz horizontal con lienzo** | **S** | 8 | 33 | 🟢 | 7 400 |
| Área 11 — Invención | **S** | 3 | 22 | 🟢 / 🟡 / 🔴 | 3 582 |
| Área 12 — Capacidades C01–C39 | **S** | 2 | 53 | 🟢 / 🟡 | 5 885 |
| Área 13 — MAGI-MEM (grafo de código) | **S** | 3 | 26 | 🟢 | 3 697 |
| Área 14 — MAGI-ROUTE (pasarela) | **S** | 4 | 25 | 🟡 (nube) | 3 718 |
| Área 15 — Ingesta universal | **S** | 3 | 25 | 🟢 / 🟡 / 🔴 | 4 018 |
| Área 16 — Sistemas portables | **S** | 4 | 23 | 🟢 / 🟡 | 3 909 |
| Área 17 — Configuración y calibración | **S** | 2 | 25 | 🟢 / 🟡 | 3 597 |
| Área 18 — MAGI-KEEP (memoria íntegra) | **S** | 3 | 25 | 🟢 | 3 720 |
| Área 19 — MAGI-WEB (navegación gobernada) | **S** | 3 | 24 | 🟢 / 🟡 | 3 480 |
| **Área 20 — MAGI-STUDIO (obra con autocorrección) — nueva** | **S** | 3 | 23 | 🟢 / 🟡 | 3 415 |
| **Área 21 — MAGI-SHELL (aplicación, extensión, proyecto) — nueva** | **S** | 4 | 25 | 🟢 / 🟡 | 3 588 |
| T1–T11 (artefactos base, enmendados por T13–T17) | N/A | 1 | 24 puertas de integración + 16 transversales | 🟢 | 8 100 |
| T12 Sistema de diseño y lenguaje | N/A | 2 | 12 reglas con test | 🟢 | 940 |
| T13–T16 Addendas anteriores | N/A | — | 11 consultas de control + 7 puertas | 🟢 | 5 877 |
| **T17 Addenda nube, Áreas 20 y 21 (nuevo)** | N/A | — | 3 consultas de control + 2 puertas | 🟢 | 1 747 |

## 6.2 Trazabilidad de este encargo

| Requisito | Dónde queda resuelto |
|---|---|
| **Inteligencias de nube, sin clave de API, no locales, no instaladas** | **§I.3 reescrito por completo**: la jerarquía de tres niveles con `llama.cpp` local queda derogada. Tres formas de acceso admitidas, todas sin clave de servicio (cliente oficial con sesión del usuario, punto final público documentado, sesión propia del usuario donde el proveedor publique vía programática). `config` rechaza cualquier campo que parezca clave con `CredentialRefused`. La regla de diversidad pasa de «familias de pesos» a **«proveedores distintos»** |
| **Gratuitas, con límite temporal recuperable** | **§I.3.3**: la cuota deja de ser un accidente y pasa a ser recurso planificable — **libro de cuotas** con límite declarado y **observado**, reserva antes de gastar, **suspensión y reanudación por ventana** con la hora prevista visible («continúa a las 19:40»), planificación que no inicia una deliberación sin cuota para sus tres rondas mínimas, y reparto por prioridad entre nodos. Puerta `PV-X-CUOTA` y `PV-INT-24`: un trabajo de 300 unidades atraviesa **dos agotamientos** y termina sin pérdida |
| **Siempre en un ejecutable; nunca por HTML ni por la web de un navegador** | **§21.2 y §21.4.a**: aplicación de escritorio nativa; el canal entre interfaz y núcleo pasa de WebSocket sobre TCP a **tubería con nombre (Windows) o socket Unix (Linux)**. No hay servidor, no hay dirección, no hay pestaña. Verificado: `PV-21.a.2` exige **conjunto vacío** de puertos de interfaz —el arranque aborta si se fuerza uno— y `PV-21.a.3` comprueba en tres navegadores que **nada responde** |
| **Instalable como extensión en cualquier navegador, conectada al ejecutable** | **§21.4.b**: extensión con manifiesto V3 y **mensajería nativa** —no peticiones a `localhost`, que reintroducirían el puerto eliminado—, permisos mínimos sin `host_permissions` amplios, emparejamiento con confirmación y revocable, cuatro flujos (enviar página, enviar selección, capturar como evidencia, continuar aquí) y un indicador de estado. Una página web **no puede** alcanzar el ejecutable, y se verifica con página de prueba |
| **Columna a la derecha con código, plan de ejecución, imagen, gráfico…** | **§10.4, «la columna de lienzo»**: seis pestañas — **Plan** (el plan de ejecución de la instrucción, aprobable y ejecutable paso a paso), **Código** (con comparación y errores anclados), **Imagen** (con historial de versiones y la crítica de cada iteración), **Gráfico**, **Vista previa** (juego, animación, música o vídeo en ejecución) y **Documento** (informe con citas enlazadas). `Ctrl+L` abre y cierra; `Ctrl+Mayús+L` desprende a otra ventana; sigue al turno visible salvo que se fije |
| **Crear videojuegos, música, imagen (píxel, GIF, cómic, manga, fotorrealista, todo estilo) y vídeo** | **Área 20 completa**, con cuatro caminos de imagen, motor Godot 4.x más camino HTML5 para juegos, partitura simbólica y síntesis para música, y montaje por lista de decisiones para vídeo |
| **Autocorregirse para mejorar** | **§A20-1**: bucle con **especificación medible obligatoria antes de generar**, medición determinista sin modelo, crítica sobre las medidas, regla de trinquete, parada por meseta y **selección de la mejor versión de todo el historial, no la última**. Criterio de que el bucle funciona: `PV-20.b.2` exige mejora en ≥ 17 de 20 encargos. El **agente de prueba de juego** (§A20-2) hace objetivo lo que parecía subjetivo: un juego que el agente no puede terminar no está terminado |
| **Interfaz horizontal, nunca mayor que la pantalla, nunca vertical** | **§10.4, «regla de encuadre»**: la ventana se abre a `min(1440, ancho−80) × min(900, alto−80)` y nunca pide más; `overflow` del raíz en `hidden`; el CI comprueba a cuatro resoluciones y **falla si aparece una barra horizontal** o si el documento supera el alto de la ventana |
| **Conversación larga sin ensanchar; sólo rueda del ratón arriba y abajo** | **§10.4**: tres columnas, cada una región de desplazamiento independiente con `overflow-x: hidden` y `overscroll-behavior: contain`; la rueda actúa sobre la columna bajo el puntero sin encadenarse; las cadenas largas se cortan o se desplazan **dentro de su caja**; la barra de instrucción va anclada abajo y no se desplaza |
| **Proyecto = carpeta, conectable a un repositorio con autorización, usable en otro equipo** | **§21.4.c**: el proyecto es una carpeta real con estructura declarada y repositorio local desde el primer minuto; conexión al remoto con autorización explícita y **sin guardar claves** (flujo de dispositivo o gestor de credenciales del sistema); **nunca hay publicación automática**; `portability.json` responde a «¿esto se abre en otro equipo?» y `PV-21.d.2` lo prueba **clonando en un contenedor limpio y continuando la conversación en el turno siguiente** |
| Protección al publicar | **CTL-9** barrido de secretos previo al `push` (bloquea, no avisa), **CTL-1** vigente para volcados y firmware, blobs excluidos por defecto |
| **Corrección de la sección sobre el navegador** | §19.2, reescrita: se explica **por qué esta revisión agrava el problema** —al desaparecer el suelo local, el incentivo para usar el navegador contra un chat deja de ser abstracto— y se responde con una medida nueva, **CTL-10 · separación de caminos**: el módulo de navegación **no expone ninguna función que devuelva una respuesta de modelo**, y el registro de proveedores **rechaza por esquema** a cualquiera que no documente vía programática. No es una prohibición: es una ausencia. Y se admite que los controles son código que un *fork* puede quitar |
| **Corrección de la debilidad D5** | §A18-1b, **recuperación proactiva**, promovida de «debilidad declarada» a parte del diseño: cierre transitivo del grafo de referencias, elementos abiertos siempre presentes, reaparición, similitud, **aviso literal de lo no cargado con sus identificadores**, y métricas de precisión y cobertura con ajuste automático del tamaño de precarga |
| **Buscar y corregir más debilidades** | Tres corregidas en el sitio: la **deriva silenciosa del proveedor** (sonda canaria en §I.8, `provider.model_drift`), la **pérdida de privacidad** por falta de modelo local (clase `no_enviar` con permiso por unidad en §I.3.4) y el **incentivo perverso** creado por las cuotas (CTL-10). Las que quedan abiertas están en §6.4 |

## 6.3 Declaración de omisiones (revisada)

**Cerradas en esta revisión**

**C-10 — La debilidad D5 deja de ser una debilidad y pasa a ser un algoritmo.** La recuperación proactiva del §A18-1b no espera a que el modelo se dé cuenta: precarga por pertinencia y, cuando no puede, **le dice literalmente qué elementos existen y no están cargados**.

**C-11 — El sistema deja de ser abrible por la web.** No por configuración sino por ausencia de servidor: el canal es una tubería o un socket, y se verifica con análisis de puertos.

**C-12 — El proyecto deja de ser un silo.** Es una carpeta con repositorio, y la portabilidad se prueba clonando en limpio, no afirmando.

**Vigentes**

**V-1** Tape-out de ASIC fuera de todas las fases. · **V-2** PCB real y perfiles de consola exigen hardware. · **V-3** Los textos normativos los aporta el usuario. · **V-4** Los soportes físicos antiguos exigen la unidad. · **V-5** Los componentes de terceros (Áreas 13, 14, 19) siguen sin verificar por este equipo. · **V-6** No se ejecutan ni distribuyen sistemas propietarios modernos.

**Nuevas omisiones declaradas**

**N-6 — El sistema ya no funciona sin conexión para nada que exija una inteligencia.** Es la consecuencia directa e inevitable de que las inteligencias sean de nube, y no hay mitigación: se declara. Lo que sí funciona sin conexión es toda la mitad determinista —decompilación, grafo de código, ingesta de cualquier formato, CAD, rebanado, impresión, flasheo, HDL hasta GDSII, sistemas portables, arte de píxeles, música simbólica, montaje de vídeo y **todas las puertas de verificación**—, que no es poco pero tampoco es lo que el usuario suele venir a buscar.

**N-7 — La privacidad por construcción se ha perdido.** La clase `no_enviar` no se envía nunca por defecto, se analiza con herramientas deterministas locales y se pide permiso explícito por unidad de contenido con el proveedor nombrado. Pero **la garantía anterior —que el material sensible podía analizarse con una inteligencia sin salir del equipo— ya no existe**. Es la peor consecuencia de este encargo y no se disimula.

**N-8 — La reproducibilidad exacta desaparece.** Sin pesos locales no hay hash de modelo. La sonda canaria detecta la deriva del proveedor, pero **detectar no es evitar**: dos ejecuciones separadas por una actualización silenciosa del proveedor no son comparables, y el plan lo marca en el acta en vez de fingir que lo son.

## 6.4 Las cinco afirmaciones más débiles del plan (recalculadas)

**D1 (nueva y ahora la peor) — «El sistema es operable con inteligencias gratuitas de nube y cuota recuperable».**
*Refutación:* es la apuesta estructural de esta revisión y descansa en algo que **no controla nadie del proyecto**: que existan varios proveedores con nivel gratuito, acceso programático sin clave de servicio y cuota que se repone. Cualquiera de las tres condiciones puede desaparecer de un día para otro, y con las tres cae la mitad deliberativa del sistema. Peor: la deliberación de tres a siete rondas con tres nodos **multiplica por tres a veintiuno** el consumo de cuota respecto de una sola llamada, justo en el recurso más escaso. Es posible que el diseño de deliberación y el modelo de cuotas gratuitas sean, sencillamente, incompatibles en la práctica.
*Experimento barato que la resuelve primero:* **una semana de uso real registrando el libro de cuotas** — cuántas deliberaciones completas caben al día, cuánto tiempo se pasa en `WAITING_QUOTA`, y cuántas veces se degrada la diversidad por falta de proveedores sanos. Cero dinero, sólo esperar. Si el resultado es que caben menos de tres deliberaciones diarias o que el sistema pasa más tiempo esperando que trabajando, hay dos salidas y ninguna es cosmética: **bajar el mínimo de rondas a 3 y hacer la crítica de BALTHASAR • 2 diferida**, o **ampliar masivamente la lista de modelos de nube**. **Se ha eliminado por completo la opción de fallback a modelo local.** Si un modelo en la nube falla, se rotará a otro modelo de nube disponible; cuando la lista se reduzca al punto de fallar el antepenúltimo modelo (quedando solo 2 en reserva), el sistema **hará una pausa global** hasta que se restaure la disponibilidad de los modelos cloud. Esta reserva nunca se consume para continuar eternamente, sino para asegurar capacidad residual para culminaciones concretas.

**D2 — «El análisis forense distingue páginas alteradas con 2 % de falsos positivos y 85 % de detección».**
*Refutación:* los umbrales se calibran contra un corpus sintético que el propio sistema fabrica. Una falsificación competente —mismo escáner, misma fuente, documento reimpreso entero— no se parece a eso. Es, desde hace cuatro revisiones, la afirmación empírica peor sostenida y la única que no ha mejorado.
*Experimento barato:* 20 alteraciones adversarias hechas a mano, imprimiendo y reescaneando el documento completo. Unas horas y papel. Si la detección cae bajo el 40 %, la afirmación pasa a «detecta alteraciones que dejan huella de composición digital».

**D3 — «El bucle de autocorrección del Área 20 mejora la obra, y no sólo sus métricas».**
*Refutación:* es la ley de Goodhart aplicada a la creación. Todo lo que el bucle sabe medir —paleta, tamaño, tempo, fotogramas, completabilidad— es exactamente lo que un generador puede satisfacer sin producir nada bueno: un juego completable y aburrido cumple todos los criterios duros. El plan reconoce el modo de fallo («cumple todo y es mala») y responde declarándolo al usuario, pero **declarar no es corregir**, y la crítica estética recae en la mitad de juicio de la rúbrica, que es la parte que la D1 de la revisión anterior ya señalaba como frágil.
*Experimento barato:* **20 obras generadas y evaluadas a ciegas por cinco personas** que no sepan cuál es la versión 1 y cuál la final, puntuando sólo «¿cuál prefieres?». Si la versión final no gana en ≥ 14 de 20, el bucle está optimizando métricas y no obra, y la corrección es incorporar la preferencia humana como criterio: el sistema pediría al usuario elegir entre dos versiones en un punto del bucle, convirtiendo esa elección en una medida más. Coste: una tarde y cinco personas.

**D4 — «Ejecutar componentes de terceros, sistemas operativos y un navegador anti-detección no compromete la seguridad ni la integridad».**
*Refutación:* la superficie sigue creciendo — tres binarios de terceros, analizadores de formatos de treinta años, sistemas operativos completos, un motor de juegos que ejecuta código generado, y ahora una extensión de navegador. El vector nuevo de esta revisión es la **extensión**: vive en el navegador del usuario, y aunque la mensajería nativa impide que una página la suplante, una extensión comprometida en la tienda sería un canal directo al ejecutable. La mitigación —emparejamiento con confirmación, permisos mínimos, flujo de una sola dirección— es real pero no cubre el caso de la extensión legítima actualizada con código malicioso.
*Experimento barato:* corpus hostil por las Áreas 1, 5 y 15 con auditoría de ficheros y red; 20 sesiones del Área 16 con huésped hostil; auditoría de tráfico del Área 19; y, para la extensión, **revisar que el ejecutable valide cada mensaje contra su esquema y rechace todo campo no previsto**, con 50 mensajes malformados. Un día. Puertas `PV-X-SBX`, `PV-X-WEB` y `PV-21.b.3`, todas bloqueantes.

**D5 — «La memoria íntegra no degrada el funcionamiento» — mitigada por A18-1b, no cerrada.**
*Refutación restante:* la recuperación proactiva corrige el caso en que el modelo no sabe que algo existe, pero **no corrige el caso en que sabe y decide que no importa**. Y añade un riesgo nuevo: si la precarga se equivoca sistemáticamente, el contexto se llena de ruido pertinente-en-apariencia y desplaza a lo que sí importaba. Las métricas de precisión y cobertura existen precisamente para detectarlo, pero sus umbrales (0,40 y 0,70) **están puestos a ojo**, igual que el 92 % del Área 13 que llevo tres revisiones señalando.
*Experimento barato:* el cuestionario de `PV-18.c.2` con las tres condiciones —memoria resumida al 10 %, direccionada sin precarga, y direccionada con precarga— y **las curvas de precisión y cobertura frente al tamaño del bloque de precarga**, para fijar los umbrales con datos en vez de por intuición. Media jornada de cómputo.

---

*Fin del plan. Los commits fijados de los componentes externos, el resultado de cada puerta, la configuración efectiva de cada ejecución, el libro de cuotas, la cadena de hashes de cada registro de memoria y las capturas de referencia de la interfaz se registran en `config/externals.lock`, `reports/gates.json`, `config_history`, `quota_ledger`, `memory_record` y `tests/gui/visual/`. Cualquier afirmación de este documento que una puerta contradiga se corrige en el documento, no en la puerta.*
