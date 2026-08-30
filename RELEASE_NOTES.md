# v5.11.0 — corridas con ojos

**Qué cambia:** una corrida de emulador sin capturas de pantalla con veredicto
de imagen y movimiento ya no se acepta como evidencia. El origen es una
medición real: YabauseVita reportó 59,9 FPS estables durante media hora con la
pantalla negra — el contador contaba vueltas de bucle, no juego.

**Lo concreto:**

- **Bitácora inyectada al prompt** (`magi/modules/swarm/bitacora.py`, ya
  existía) — ahora alimenta al enjambre con los hallazgos A1-A18 y las reglas
  R1-R11 de las rondas de optimización del emulador: lo ya medido y lo que no
  hay que volver a intentar.
- **Nuevo `ronda_verificada`** (`magi/modules/swarm/ronda_verificada.py`) —
  inyecta el protocolo R9 cuando el encargo es una corrida de emulador:
  capturas continuas de la ventana del juego (no la del GUI), veredicto
  `has_image`/`has_motion`, los DOS contadores de FPS citados por separado
  (app anfitriona vs ROM) y el formato de veredicto de cuatro campos. Conecta
  con las tres filosofías ortogonales de la bitácora (hacer menos → composite,
  mover menos → upload, repartir mejor → dropped): cada propuesta declara su
  métrica y la corrida verificada es la que adjudica.
- **Nuevo `scripts/ronda_emulador.py`** — la Ronda 2 de YabauseVita como
  procedimiento ejecutable: NiGHTS con espera larga, verificación de input,
  sonda del dynarec y perfil SH2 por juego, con veredicto JSON en formato R9.
- **Tests:** 1472 en Python (32 nuevos fijan pertinencia, contenido del
  protocolo y localización del harness). Sin tests verdes no hay release.

**Compatibilidad:** sin cambios de configuración ni de interfaz. El protocolo
se inyecta solo cuando el encargo lo amerita; el resto de peticiones no notan
diferencia.

**Caso piloto verificado con esta versión:** la ronda 1 de YabauseVita
encontró cinco bloqueos que el log daba por buenos (CI rota, flags agresivos,
núcleos SH2 que reportaban FPS fantasma, cadena de vídeo incompatible, BIOS de
región equivocada). Resultado: Panzer Dragoon a velocidad completa (59,8 FPS)
y Sonic R jugable (46,3), confirmados con capturas y movimiento, no con log.
