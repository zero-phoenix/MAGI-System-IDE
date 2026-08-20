# Estado de ejecución del MEGAPLAN v7

**Fecha:** 2026-08-20 · Suite completa en verde · **Verificado en caliente
contra el sistema real**, no solo con tests.

## La prueba que importa

Encargo: *«Crea un juego de ping pong de 32 bits a todo color en un único
ejecutable exe portable»*. Con el workspace vaciado antes, para que no valiera
un artefacto viejo.

```
[CONTRATO] Así he entendido lo que pides, y así lo voy a comprobar:
  · que sea jugable — se comprueba: autoprueba que avanza la partida y sale con codigo 0
  · el formato de color pedido — se comprueba: el artefacto lo verifica solo
  ...
[FÁBRICA] Construyendo «ping» desde la propuesta verificada...
[fábrica] ping.exe entregado en Escritorio: C:\Users\D\Desktop\ping.exe
          (14370685 bytes, sha256 03d515a99b72fd2e…)
[FÁBRICA] Listo: C:\Users\D\Desktop\ping.exe
```

Comprobado a mano después: el fichero existe (13,7 MB), arranca y sale con
código 0.

| Métrica | v5.5.2 | v5.6.0 | **v5.7.0** | Objetivo v7 |
|---|---|---|---|---|
| Ratio entregado/producido | 0,8 % | 12-25 % | **49,9 %** | ≥ 50 % |
| Artefacto en encargo de producto | no | no | **sí** | sí |
| `APPROVED` sobre degradado | 3/3 | 0/2 | **0** | 0 |
| `[SIN CONTESTAR]` cuando falta algo | — | — | **sí** | sí |

## Hecho

| Bloque | Qué se hizo | Test |
|---|---|---|
| **D1** | El encargo se lee como contrato: compromisos con su forma de comprobarse, enseñados al usuario y enviados al prompt | `test_contrato_del_encargo.py` |
| **D2** | `APPROVED` no sobrevive a un contrato incumplido: la decisión baja a `INCOMPLETO` | `test_cerrar_el_lazo.py` |
| **D3** | El orquestador construye y entrega el artefacto en vez de esperar a que el modelo se acuerde | `test_cerrar_el_lazo.py` |
| **D4** | `analyze_port` se **ejecuta** y su resultado entra en el prompt como evidencia obtenida | — (verificado en caliente) |
| **D5** | Cobertura del enunciado: lo que no se contesta se dice | `test_contrato_del_encargo.py` |
| **D6** | Dos enfoques en vez de tres o cuatro | `test_fase2_velocidad.py` |
| **D7** | Ritsuko ve las métricas de entrega y no puede decir «sin datos» con un incumplimiento delante | `test_ritsuko.py` |
| **D10** | Se reconocen los artefactos que construye el agente, comprobando la ruta contra el disco | `test_artefacto_del_agente.py` |
| **D11** | El prompt dice que la fábrica construye Python: proponer C/mingw es proponer no entregar | — (prompt) |
| extra | Un bloque de Python sin etiqueta sigue siendo Python (11 de 18 venían así) | `test_bloques_sin_etiqueta.py` |

## Tres fallos que encontró la ejecución real, y no los tests

Vale la pena listarlos porque son la mejor prueba de por qué hay que ejecutar
contra el sistema y no solo correr la suite:

1. **`coroutine 'fabricar_y_entregar' was never awaited`.** Envolví una
   corrutina en `asyncio.to_thread`, que es para funciones síncronas. La
   fábrica no corría. **Los tests pasaban en verde** porque mi doble de prueba
   era síncrono y no se parecía a la función real.
2. **La guarda de `test_cancel` me cazó** tirando el handle de un
   `create_task`. Tenía razón: una tarea sin handle es una tarea que el botón
   de parada no puede parar.
3. **El artefacto existía y el sistema decía que no.** Melchior había
   construido dos ejecutables que funcionan; el estado de la tarea no se
   enteraba. De ahí sale D10.

## No hecho, y por qué

| Bloque | Motivo |
|---|---|
| **D8** (elegir candidato por latencia en la puerta de herramientas) | El reparto por mérito ya existe y lo alimenta la sonda; lo que falta es medirlo dentro del bucle de herramientas antes de tocarlo. Cambiar la selección a ciegas es cómo se empeora sin enterarse. |
| **D9** (caducidad de tareas atascadas) | Ritsuko ya las detecta y las reporta —8 en `WAITING_USER_APPROVAL`—. Borrar tareas por tiempo toca datos del usuario, y eso se decide antes de implementarse, no después. |
| **C6** (el `TypeError` de HuggingSpace) | Sigue sin reproducirse sin llamar al proveedor real. |
| **B3, B5, B7** | Igual que en el megaplan anterior: caché con riesgo de servir respuestas viejas, y solape que requiere medir dónde se serializa antes de tocar el candado. |

## Lo que sigue siendo mejor en una entrega externa

Honestidad sobre el resultado: el `.exe` que produjo MAGI **funciona** y se
autoverifica, pero pesa 13,7 MB porque eligió pygame; la versión de referencia
pesa 9,0 MB con tkinter y su `--formato` **calcula** la matemática del alfa en
vez de imprimir una cadena. La regla de presupuesto de dependencias (C10) está
en el prompt y esta vez no ganó. Ahí queda el siguiente escalón.
