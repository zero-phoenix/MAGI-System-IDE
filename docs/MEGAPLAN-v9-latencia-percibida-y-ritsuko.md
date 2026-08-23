# MEGAPLAN v9 — la latencia que se ve, y qué hacer con Ritsuko

**Fecha:** 2026-08-23 · **Partida:** v5.8.0 · **Salida:** v5.9.0

---

## 0. Lo que se reportó

> «analiza porque demora tanto mi pedido, ademas porque no se registra mi
> comentario a naoko, yo le dije "hola naoko" y no aparece mi mensaje a
> diferencia de cuando le escribo a ritsuko»

Dos observaciones. Las dos son **ciertas**, las dos tienen causa medida, y
—esto es lo importante— **son el mismo fallo visto por dos sitios**.

---

## 1. La medición que lo resuelve todo

Sonda externa contra la aplicación que el usuario tenía abierta, por el mismo
socket que usa la interfaz. Sin filtros: se registró todo lo que salía.

```
[   6,1 s]  RPC {'status': 'ok'}                    <- el kernel ya publicó
[  14,0 s]  naoko.user_message                      <- el bus lo entrega 7,9 s DESPUÉS
[  16,7 s]  naoko.log [USER] hola naoko             <- el eco, 10,6 s tarde
[  19,2 s]  naoko.status Pensando (claude45sonnet)  <- 13,1 s
[  63,8 s]  naoko.log [NAOKO] Hola. El sistema...   <- 57,7 s en total

[ 104,4 s]  RPC {'status': 'ok'}
[ 104,4 s]  ritsuko.user_message                    <- INSTANTÁNEO
[ 104,4 s]  ritsuko.log [USER] hola ritsuko         <- INSTANTÁNEO
```

**El mensaje a Naoko sí se registraba. Tardaba 10,6 segundos en aparecer.**

El usuario escribió, no vio nada durante diez segundos, hizo la captura y
concluyó —razonablemente— que su mensaje se había perdido. Con Ritsuko, unos
segundos más tarde y en el mismo sistema, el eco fue instantáneo. Esa
diferencia es real y es exactamente lo que él describió.

La diferencia no era Naoko. Era **el reparto de eventos**, que iba atascado en
ese momento y no en el otro.

---

## 2. Causa A — el reparto a la interfaz es un embudo sin tiempo límite

`ws_server` se suscribe a `"*"`. **Todo** lo que ocurre en MAGI pasa por una
única cola con un único worker, porque `MagiBus._worker` espera a que el
handler termine antes de coger el siguiente evento. Y el handler hacía:

```python
await asyncio.gather(*[self._send_safe(c, msg) for c in self.clients])
```

con un `_send_safe` **sin `timeout`**.

Un socket medio abierto —lo normal cuando el webview se recarga y deja la
conexión anterior colgando; el registro del usuario muestra literalmente dos
`Cliente GUI conectado` seguidos— no lanza `ConnectionClosed`: se queda
esperando. Con un solo worker, eso deja sin eventos a **todos** los clientes
mientras el kernel sigue contestando por RPC como si nada, porque las
respuestas RPC van por otro camino.

De ahí la sensación desconcertante: **responde a todo menos a lo que se ve**.

### Arreglo (§G1)

- Techo de 2 s por envío. Un cliente que no traga en 2 s se da por muerto y se
  saca de la lista — si no, cada evento siguiente vuelve a pagar el timeout.
- La serialización JSON se hace una vez, no una por cliente.
- El retraso se **mide y se registra**: un reparto de siete segundos ya no es
  indistinguible de «Naoko no responde».

### Arreglo (§G2) — qué se tira cuando no cabe todo

La política de desbordamiento era «fuera el más viejo», y era ciega. La cola de
la interfaz se llena de `TERMINAL_OUT` —cada línea de log de cada proveedor;
con cobertura x3 son cientos en segundos—. Al llenarse, lo primero que salía
podía ser perfectamente la respuesta de Naoko esperando turno detrás de
trescientas líneas de registro.

Ahora: si lo que **entra** es prescindible, se queda fuera lo que entra. Solo
se desaloja a un veterano cuando lo nuevo es algo que el usuario necesita ver.

> Perder una línea de terminal es un inconveniente. Perder la respuesta que la
> persona está esperando delante de la pantalla no lo es.

---

## 3. Causa B — la medición le quitaba el turno al usuario

Registro del usuario, en orden:

```
root@system:~# crea un juego de tetris en un unico ejecutable exe portable
[g4f-razonamiento] Perplexity devolvió una respuesta inservible ('tud.')
[registry] familia 'razonamiento' agotada (3 candidatos)
[sonda] 32 candidatos medidos, 0 saltados por tope diario
[sonda] 32 mediciones (la última medición fue hace 84.1 h)
[g4f-gpt] respondió Perplexity/gpt4o en 12734ms (cubierto x3)
[g4f-gpt] respondió Perplexity/gpt5  en 15109ms (cubierto x3)
[naoko] g4f-gpt: 0/3 canarios
[g4f-gemini] ... (cubierto x3) ×3
[g4f-command] ... (cubierto x3) ×3
```

Contando: **32 mediciones de sonda + tres familias de canarios con cobertura
x3** ≈ sesenta y pico llamadas HTTP a proveedores gratuitos, limitados por
cuota, **antes** de atender lo que la persona acababa de pedir. Mientras tanto,
en el panel central: «Esperando flujos del Enjambre».

El resultado se ve en el propio log: la familia `razonamiento` acabó agotada
devolviendo cuatro caracteres, y los canarios salieron `0/3` — no porque nada
funcionara, sino porque la sonda se había comido la cuota.

### Por qué B8 no bastó

B8 ya comprobaba si el enjambre estaba ocupado. Pero comprueba **una vez** y
luego se va a medir durante un minuto: un comprobar-y-actuar con una ventana
enorme en medio. Y esa ventana se abre en el peor momento posible —el
arranque—, porque el freno de 24 h **garantiza** que la primera sesión del día
dispare el sondeo justo mientras la persona escribe su primera petición.

### Arreglo (§G4)

1. **Tregua de arranque de 120 s.** La sonda no gasta un solo token hasta que
   pasen dos minutos. No cuesta nada: MAGI ya arranca con la última medida
   conocida.
2. **`_enjambre_ocupado()` cuenta también lo encolado y lo que espera en
   admisión** — el instante entre «el usuario pulsa Ejecutar» y «el orquestador
   marca la tarea en curso», que es justo donde caía el sondeo.
3. **Se vuelve a comprobar pegado al gasto**, no solo al entrar en el bucle.

---

## 4. Causa C — dos alarmas falsas sobre proveedores intactos

En los mismos 200 segundos de sonda, con el sistema **parado**:

```
Deriva detectada en g4f-gpt:    solo 1/3 respuestas canarias correctas
Deriva detectada en g4f-gemini: solo 1/3 respuestas canarias correctas
```

C13 ya cubría el `0 de N`. El caso intermedio quedaba fuera. Con proveedores
gratuitos que devuelven basura de vez en cuando —«tud.», cuatro caracteres,
tres veces seguidas ese mismo día—, **acertar 1 de 3 es ruido normal**.

Y «deriva» no es una nota al margen: se publica como crítica e invalida las
comparaciones del sistema.

### Arreglo (§G3)

`deriva_es_concluyente(acertados, total)`: se exige **mayoría estricta** de
canarios correctos. Deriva significa que el proveedor responde *bien y
distinto*; si la mayoría no llega a responder bien, lo que se mide es la salud
del proveedor, no la identidad del modelo.

---

## 5. Ritsuko: de documentación a control de calidad

> «evalúa qué rol mayor le puedes dar a ritsuko para que el sistema magi y
> naoko funcione mejor»

### El diagnóstico honesto de su situación actual

Ritsuko funciona: contesta, audita, escribe informes correctos. Pero en esta
sesión encontré tres fallos —el embudo del reparto, la sonda pisando al
usuario, las derivas falsas— y **Ritsuko tenía delante la evidencia de los
tres** y no sirvió de nada. Porque no podía servir: nada de lo que concluye
toca jamás una decisión.

**Un auditor cuyas conclusiones no cambian nada no es un auditor: es
documentación.**

El encargo original fue: *«que verifique que Naoko corrige adecuadamente a las
3 IA … y redireccione su funcionamiento»*. La primera mitad estaba hecha. La
segunda —*redireccionar*— no se había implementado nunca.

### R1 — Veto sobre los diagnósticos de Naoko · **IMPLEMENTADO**

Ritsuko se suscribe a `provider.model_drift`. Cada vez que Naoko declara
deriva, Ritsuko la revisa contra su ventana de eventos:

| Situación | Qué hace |
|---|---|
| La mayoría de canarios no contestó bien | **Anula** — «para afirmar que un modelo responde distinto, hace falta antes que responda» |
| Hubo trabajo del enjambre en los 2 min previos | **Anula** — se midió la cuota gastada, no el modelo |
| Muestra suficiente y sistema en reposo | **Confirma**, y deja constancia de que se revisó |

Sigue sin arreglar nada, sin tocar el reparto y sin hablar con los tres nodos.
La anulación viaja como `ritsuko.veto_de_deriva`: un hecho auditable más, no
una orden. Pero ahora **llega a tiempo de que se tenga en cuenta**.

Que confirme también importa: «nadie lo miró» y «lo miré y está bien» son
cosas distintas, y el informe debe poder distinguirlas.

### R2 — Guardiana del reloj percibido · *propuesto*

Ritsuko ya pone marca de tiempo a cada evento que ve. Puede medir sola lo que
en esta sesión tuve que medir desde fuera: el retraso entre que el usuario
manda algo y que aparece en pantalla. Si pasa de 2 s, es un hallazgo.

Nadie mide eso hoy. Por eso el usuario tuvo que ser el detector.

### R3 — Portera de la sonda · *propuesto*

§G4 arregla la colisión con reglas fijas (tregua de 120 s, comprobar dos
veces). Ritsuko es quien tiene la vista global de «¿hay alguien esperando
algo?» y podría decidirlo mejor que un temporizador. Conviene hacerlo **después**
de que §G4 esté rodado: una regla simple que funciona vale más que una decisión
inteligente sin verificar.

### R4 — Segunda firma en las entregas · *propuesto*

Ritsuko ya calcula `entrega.artefactos_listos` y `entrega.marcada_incompleta`.
Cuando Casper cierre un encargo de producto con `APPROVED`, que Ritsuko
compruebe la evidencia de entrega **antes** de que se le diga al usuario que
está hecho. Es el mismo control que C12/D3, con un segundo par de ojos que no
tiene nada que defender.

### Lo que NO se le va a dar, y por qué

Ni escritura de código, ni cambiar el reparto, ni hablar con los tres nodos.
Su valor entero está en ser independiente de lo que juzga. Un auditor que
también ejecuta acaba auditándose a sí mismo, que es precisamente el agujero
que ella vino a tapar.

---

## 6. Ejecución

| # | Acción | Estado |
|---|---|---|
| G1 | Techo por envío + descarte de clientes muertos + medición del retraso | ✅ |
| G2 | El ruido no desaloja lo que el usuario necesita ver | ✅ |
| G3 | La deriva exige mayoría de canarios correctos | ✅ |
| G4 | Tregua de arranque + `_enjambre_ocupado()` + doble comprobación | ✅ |
| R1 | Ritsuko revisa y puede anular las derivas de Naoko | ✅ |
| — | `ConnectionClosed` importado explícito (fallo latente encontrado por un test) | ✅ |
| R2 | Ritsuko mide el retraso percibido | ⏳ siguiente |
| R3 | Ritsuko decide cuándo puede medir la sonda | ⏳ tras rodar G4 |
| R4 | Segunda firma de Ritsuko en las entregas | ⏳ siguiente |

### Pruebas nuevas (26)

| Fichero | n | La que importa |
|---|---:|---|
| `test_reparto_no_se_atasca.py` | 5 | que el reparto normal **siga siendo inmediato** |
| `test_sonda_no_pisa_al_usuario.py` | 6 | que un sistema de verdad parado **sí** deje medir |
| `test_deriva_necesita_muestra.py` | 10 | que con mayoría **sí** se detecte deriva real |
| `test_ritsuko_revisa_a_naoko.py` | 5 | que Ritsuko **confirme** cuando el diagnóstico se sostiene |

En los cuatro casos la prueba decisiva no es la del fallo que se arregla, sino
la que impide que el arreglo se convierta en un daño nuevo. Un revisor que
anula siempre es tan inútil como uno que no revisa nunca.

---

## 7. Criterio de aceptación

1. El eco de Naoko aparece en **< 1 s**, igual que el de Ritsuko (partida:
   10,6 s).
2. Tras abrir MAGI y pedir algo de inmediato, **no hay sondeo** compitiendo con
   la petición.
3. Cero «deriva detectada» con el sistema en reposo (partida: 2 en 200 s).
4. Suite completa en verde.
