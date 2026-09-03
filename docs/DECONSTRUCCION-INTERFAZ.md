# Deconstrucción de la interfaz — del IDE de tres columnas a la conversación como columna vertebral

**Fecha:** 3-sep-2026 · **Encargo:** ingeniería inversa de la interfaz del
agente que supervisa (ZCode Desktop) y réplica de su paradigma en MAGI,
manteniendo colores e icono del `.exe`.

---

## 1. Los diez principios operativos de la interfaz de origen

Observados usándola durante toda la sesión de supervisión:

| # | Principio | Qué significa en la práctica |
|---|---|---|
| 1 | **La conversación es la única columna vertebral** | No hay «paneles de resultados»: todo lo que ocurre —texto, herramientas, planes, archivos, veredictos— aparece EN el flujo, en orden cronológico, en el mismo sitio donde escribes |
| 2 | **Una sola caja de entrada, siempre en el mismo sitio** | Abajo, fija, con foco. Nunca se mueve ni se esconde tras pestañas |
| 3 | **Las herramientas se muestran como tarjetas plegadas en el flujo** | «leyendo vidgpu.c:338…» — plegadas por defecto, desplegables, sin saltar de contexto |
| 4 | **El plan vive con la conversación** | La lista de tareas con estados (pendiente/haciendo/hecha) es parte del mismo hilo: se VE mientras trabaja |
| 5 | **Los paneles auxiliares son cajones, no columnas fijas** | Nada ocupa pantalla si no lo estás mirando; se abren a demanda y se cierran solos |
| 6 | **Una línea de estado honesta abajo** | Versión, conexión, motor, tarea activa: lo mínimo, siempre visible, sin adornos |
| 7 | **Cada artefacto es una referencia clicable en el flujo** | El archivo que se creó se nombra con su ruta y se puede abrir desde el propio mensaje |
| 8 | **Aprobaciones y paradas son botones inline, no modales** | Donde está la pregunta está la respuesta |
| 9 | **La paleta de comandos (Ctrl+K) es la puerta a TODO** | Cualquier acción alcanzable sin recordar dónde vive |
| 10 | **El estado del agente se cuenta, no se actúa** | La persona ve QUÉ está pasando; no hay que interpretar silencios |

## 2. Qué tenía MAGI y qué quedaba corto

- **Tres columnas fijas** donde la conversación central era la más estrecha:
  el protagonista tenía la menos pantalla, y los nodos del enjambre
  (decorativos en reposo) ocupaban un tercio del ancho.
- **Un panel de pestañas fijo a la derecha** (Plan, Código, Vista previa,
  Terminal, Naoko, Ritsuko, Configuración, Mejoras): ocho funciones
  compitiendo por un tercio de pantalla SIEMPRE visible, aunque no se
  mirara ninguna.
- **Pie con datos falsos** (el «v3.0» ya corregido) y sin línea de estado
  operativa real.

Lo que ya cumplía y se conserva: trazas de herramientas bajo cada mensaje
(#3), aprobaciones inline (#8), paleta Ctrl+K (#9), streaming, columna de
conversaciones izquierda.

## 3. La reconstrucción (v1)

1. **Dos columnas + cajón**: izquierda (conversaciones + GitHub, igual),
   centro = LA conversación a pleno ancho con los nodos compactos arriba;
   las nueve funciones del panel derecho pasan a un **cajón lateral
   plegable** que se abre con un botón y recuerda la última pestaña.
2. **Línea de estado operativa** bajo la entrada: versión real (del kernel),
   EN LÍNEA/FUERA, motor seleccionado, tarea activa y su estado — siempre
   visible, siempre cierto (#6, #10).
3. **Trazas, planes y aprobaciones ya inline** — ahora con espacio para
   respirar (#1, #3, #8).
4. **Colores e icono intactos**: no se toca el CSS de tema ni ningún asset;
  el cambio es de ARQUITECTURA de la información, no de identidad.

### Pendiente para v2 (anotado, no construido)

- Artefactos como tarjetas clicables DENTRO del flujo (#7) — hoy el cajón
  de Vista previa sigue siendo el destino.
- El plan de la tarea como tarjeta viva en el flujo (#4) — depende de la
  Fase 3 del megaplan v6 (plan.md por tarea), que el backend aún no emite.
- Naoko y Ritsuko como hilos propios seleccionables en la izquierda, no
  como pestañas del cajón.
