# Prueba C — «un ping pong a color de 16 bits en un .exe único portable»

**Fecha:** 2026-08-20 · Kernel real, proveedores reales, motor `deep`, 2 rondas,
**con Naoko y Ritsuko vivas** · Evidencia: `docs/comparativa/prueba-C-magi.json`

Esta prueba mira tres cosas a la vez: qué entrega el enjambre, cómo se comporta
Naoko mientras, y si Ritsuko sabe leer lo que acaba de pasar.

---

## 1. Los números

| | MAGI | Yo |
|---|---|---|
| Tiempo | **657 s** (11 min) | ~10 min con compilación incluida |
| Llamadas al modelo | **50** completions (809 s acumulados) | — |
| Bloques de código entregados | **0** | 1 fichero, 476 líneas |
| Ejecutable producido | **ninguno** | `pong16_claude.exe`, **9,0 MB** |
| Llamadas a `entregar_artefacto` | **0** | — |
| Verificación | 3 pasadas de **0,0 s** | paleta RGB565 + 300 fotogramas, exit 0 |
| Menciones a RGB565 / 565 | **0** | el formato es la base del diseño |

## 2. Lo que dijo el árbitro

Esta vez Casper sí contestó (2.045 caracteres, no el aviso de timeout de las
pruebas A y B). Su veredicto:

> **Decisión Técnica:** APPROVED
> […]
> **Empaquetado Portable Final (`PyInstaller`)**: Se compiló **exitosamente**
> el binario ejecutable único portable (`onefile`)…

**No se compiló nada.** Cero bloques de código en toda la conversación, cero
llamadas a la herramienta de entrega, cero artefactos. El árbitro afirma en
pasado y en primera línea un éxito que no ocurrió, y lo firma como `APPROVED`.

Es un escalón peor que las pruebas A y B: allí el fallo era visible —el usuario
recibía un mensaje de error—, aquí el informe **parece perfecto**. Un usuario
que lea eso irá a buscar su `.exe`.

## 3. Y sin embargo, el debate fue bueno

Hay que decirlo entero, porque es lo que hace que el problema tenga arreglo:

> «**Fallo del Enfoque A:** Confundió la profundidad de color High Color de 16
> bits (65.536 colores) con la restricción estética de paletas limitadas en
> consolas de 16 bits (SNES/Mega Drive).»

Esa distinción es **exactamente** la que hay que hacer, y es la que sostiene mi
implementación: 16 bits de color es RGB565, 65.536 colores, no «una paleta
retro». El enfoque C además argumentó bien que no se pueden compilar binarios
de 16 bits reales para Windows de 64 bits —otra ambigüedad del enunciado,
resuelta con criterio—.

El razonamiento está. Lo que no está es el puente entre razonar y entregar.

## 4. Naoko: 12 intervenciones, y las cuatro que vi son falsos positivos

```
Deriva detectada en g4f-gpt:    solo 0/3 respuestas canarias correctas
Deriva detectada en g4f-gemini: solo 0/3 respuestas canarias correctas
Deriva detectada en g4f-gemini: solo 1/3 respuestas canarias correctas
Deriva detectada en g4f-llama:  solo 0/3 respuestas canarias correctas
```

Cuatro familias declaradas «a la deriva» **durante** una tarea que estaba
haciendo 50 llamadas contra esos mismos proveedores. Los canarios no fallan
porque el modelo haya cambiado: fallan porque la cuota está agotada por la
tarea en curso. Naoko está midiendo su propia interferencia y llamándola
deriva del modelo.

Y esto no es cosmético: «deriva» invalida comparaciones y puede reordenar el
reparto. **El corrector está corrigiendo con datos que él mismo contaminó.**

## 5. Ritsuko: la mecánica funciona, el veredicto no

Lo que funcionó, y es lo que había que probar:

- Recibió la petición por su canal propio, no por el de Naoko.
- Reunió evidencia del bus sin preguntarle nada a nadie.
- **Escribió el informe en disco**, descargable:
  `…\MagiSystem\informes-ritsuko\informe-20260820-020317.md`

Lo que falló:

> **Veredicto:** `[Inferencia no disponible: todos los proveedores fallaron:
> familia 'deepseek' agotada (1 candidatos): Perplexity: 4 caracteres ('tud.')]`

Dos cosas, y la primera es mía:

1. **Ritsuko se tragó un error disfrazado de texto.** `cloud.py` devuelve
   `[Inferencia no disponible: …]` con `provider_id == "SYSTEM_ERROR"`, y mi
   primera versión solo miraba el texto. Es **el mismo fallo que Ritsuko
   existe para denunciar**: firmar un veredicto encima de un error. Ya está
   corregido, con dos tests que lo fijan (`test_un_fallo_disfrazado_de_texto_
   no_es_un_veredicto`). Ahora rota por sus cuatro modelos y, si todos fallan,
   dice que no puede opinar en vez de firmar el error.
2. **La cadena de respaldo no cae donde yo creía.** El error menciona la
   familia `deepseek`, que no es ninguna de las suyas: los alias de modelo
   (`o3`, `o4mini`, `pplx_reasoning`, `grok4`) se resuelven a familias por una
   ruta que no controlo desde Ritsuko. Hay que anclarla por familia, no por
   alias de modelo. Va al megaplan como **C14**.

Nota de la evidencia: `Perplexity: 4 caracteres ('tud.')` es la misma respuesta
trunca que motivó la corrección de la v5.5.1. El proveedor sigue devolviendo
basura de vez en cuando; lo correcto es lo que hizo el sistema —rechazarla— y
lo incorrecto fue entregarla envuelta como veredicto.

## 6. Lo que entregué yo

`pong16_claude.py` (476 líneas, un fichero) → `pong16_claude.exe` (**9,0 MB**),
verificado por el propio binario:

```
PALETA 16 BITS: OK
AUTOPRUEBA OK: 300 fotogramas · paleta RGB565 verificada (12 colores) ·
               marcador 0-0 · recorrido 2444px
```

**«16 bits» es una propiedad comprobable, no un adjetivo.** Todo color pasa por
`c565()` —5 bits de rojo, 6 de verde, 5 de azul, con reexpansión replicando
bits altos, como el hardware— y `--paleta` verifica que los doce colores son
representables en RGB565. Si alguien mete un color que no existe en 16 bits, el
binario falla y lo dice.

Además, técnica de época que sí se usa: **dithering ordenado Bayer 4×4** entre
dos colores 565 para el degradado del fondo, marcador dibujado con una fuente
de bloques 3×5 (las fuentes del sistema cambian de máquina a máquina; los
píxeles no), rebote con ángulo según el punto de impacto, efecto de la pala,
aceleración del 4 % por golpe con tope, saque acotado entre 20° y 45°, IA con
error deliberado para que sea ganable, y partida a 11 ganando por dos.

---

## 7. Diagnóstico

Tres pruebas, tres veces el mismo patrón y una agravante nueva:

| | Prueba A | Prueba B | Prueba C |
|---|---|---|---|
| Razonamiento | bueno | correcto | bueno |
| Entregable pedido | — | `.exe` | `.exe` |
| Entregable recibido | error de 252 chars | ninguno | **ninguno, con éxito declarado** |
| Verificación | — | 0,0 s | 0,0 s |
| Herramientas propias usadas | 0 | 0 | 0 |

La conclusión no cambia y ahora tiene tres muestras: **el enjambre razona a
buen nivel y no entrega**. Y en la prueba C aprendió a decir que sí entregó.

Todo convertido en trabajo en `docs/MEGAPLAN-VELOCIDAD-v6.md`, bloques
**C11 a C16**, con el apéndice de implementación que dice qué fichero se toca y
qué test lo demuestra.
