## MAGI System IDE v5.1.0

Reconstrucción completa sobre v5.0.28. **571 tests en Python y 66 en la
interfaz**, todos en verde: sin tests verdes no hay release.

**Descarga:** `MAGI-IDE-v5.zip` más abajo contiene el ejecutable de Windows,
compilado por GitHub Actions tras pasar la suite completa.

---

### El hallazgo que motivó todo

El «debate popperiano» de v5.0.28 era ficticio: los tres nodos llamaban a
`gpt-4o-mini`. Un modelo hablando solo, con tres nombres distintos. Ahora cada
nodo está anclado a una familia de modelo real y la interfaz muestra la familia
que **de verdad** respondió, no la que tenía asignada.

### Los agentes ahora actúan, no solo hablan

`run_agent` existía, tenía tests y solo lo usaba Naoko: los tres nodos del
enjambre no podían abrir un fichero. Melchior escribía planes para analizar
código sin poder leerlo y Balthasar «criticaba» sin poder ejecutar nada. Ya
están conectados, con **44 herramientas** repartidas por rol y acotadas por
dominio para que quepan en el prompt de un proveedor gratuito.

### Naoko: repara sola, mejora contigo

Dos vías separadas a propósito. **Reparar** devuelve el sistema a donde ya debía
estar, es verificable con tests y va sin consultar. **Mejorar** cambia hacia
dónde va el sistema, y ese criterio es del usuario: va con compuertas.

Naoko tiene ahora rol creativo de desarrollo. Cuando detecta un método más
eficiente o más rápido —citando fichero y línea—, el plan da **dos vueltas
completas** al enjambre antes de volver a ti: Melchior analiza y mejora,
Balthasar examina el plan *y lo de Melchior* con crítica popperiana, y Casper
evalúa las tres cosas por separado y añade temas nuevos. Solo entonces te llega
el plan hiperperfeccionado. Tus propias propuestas recorren lo mismo.

Publicar es siempre tuyo, aunque el cambio sea una reparación.

### Controles que decían funcionar y no funcionaban

- **La parada de emergencia no paraba nada.** El handler escribía una línea de
  log y devolvía `"EMERGENCY_STOP_TRIGGERED"`. Además el botón ni siquiera
  llegaba ahí: se enviaba como si fuera una petición del usuario, así que
  lanzaba un debate del enjambre sobre la cadena «KILL_ALL_PROCESSES». Ahora
  cancela de verdad, con `SIGTERM` antes que `SIGKILL`, e informa de lo que paró
  **realmente**, incluidos los procesos que no murieron. Hay `PARAR ESTA` además
  de `PARAR TODO`.
- **El visor de diffs recibía el original vacío** y pintaba todo en verde: no
  era un diff, era el texto nuevo con fondo de color. El estado de aprobación se
  deducía raspando el terminal en busca de una frase. Ahora llega un evento con
  los ficheros, su contenido antes y después, las órdenes que se ejecutarán y si
  los tests pasaron.
- **La contabilidad de tokens se calculaba y se tiraba.** El esquema existía,
  los métodos existían, y nadie los llamaba: la tabla llevaba vacía desde que se
  creó.
- **Un fallo en cualquier handler cerraba la conexión** con la interfaz.

### Capacidades nuevas

- **Ingeniería inversa y emuladores:** Capstone, Unicorn, prueba diferencial,
  matriz de portabilidad entre consolas, indexado del código real de un emulador
  y **entropía de Shannon** para distinguir un binario cifrado de código roto.
- **Fábrica de artefactos que se mira a sí misma:** juegos, programas,
  documentos, imágenes, **vídeo** (detecta el vídeo en negro y el congelado) y
  **datos** (detecta el CSV con cabecera y cero filas).
- **Vídeo programático** con FFmpeg: animática Ken Burns y manga → vídeo.
- **Manga:** composición con orden de lectura derecha-a-izquierda y validación
  de solapes antes de gastar generaciones.
- **Mundo real:** macro y geopolítica desde FRED, BCE y Banco Mundial;
  fundamentales desde SEC EDGAR; aritmética financiera determinista que muestra
  su fórmula; y un registro de tesis con calibración medible por regla de Brier.
  Todas las fuentes gratuitas y **sin clave de API**.

### Interfaz

Paleta de comandos con **Ctrl+K**, panel de coste, panel de sistema (salud,
banco de evaluación, auto-mejora), panel de mejoras, y historiales acotados
—el terminal crecía sin límite y se recorría entero dos veces por repintado—.

### Reversibilidad

Antes de tocar un fichero se copia. `undo` lo devuelve, por operación o por
tarea entera. No añade permisos: añade reversibilidad. Y esa misma copia es la
que alimenta el panel de aprobación.

---

**Requisitos opcionales**, detectados si están: `capstone` y `unicorn`,
`pygame` y `pillow`, `ffmpeg`, y ComfyUI en `127.0.0.1:8188`. Sin ellos el
sistema funciona y avisa de lo que no puede hacer, en vez de fingir.
