# Estado de ejecución del MEGAPLAN v6

**Fecha:** 2026-08-20 · Suite completa en verde tras cada bloque.

Este fichero existe para que «el megaplan está hecho» sea una afirmación
comprobable y no un recuerdo. Cada bloque dice qué se tocó y qué test lo
sostiene; los que quedan fuera dicen por qué, que es la parte que normalmente
se omite.

## Hecho

| Bloque | Qué se hizo | Dónde | Test |
|---|---|---|---|
| **C11** | `es_degradada(texto, provider_id)` en un solo sitio; `_ask_with_tools` deja de tirar `AgentTurn.degraded` en la frontera | `providers/base.py`, `swarm/agents.py` | `test_arbitro_no_aprueba_a_ciegas.py`, `test_ritsuko.py` |
| **C1** | `_leer_decision` devuelve `SIN_ARBITRAJE` ante un turno degradado. Se acabó el `APPROVED` por defecto | `swarm/agents.py` | `test_una_respuesta_degradada_nunca_produce_aprobacion` |
| **C2** | Sin árbitro se entrega la tesis y la crítica con cabecera honesta, en vez de tirarlas | `swarm/agents.py`, `orchestrator.py` | mismo fichero |
| **C3** | El techo por iteración sale del presupuesto restante (`_techo_de_iteracion`), no de la constante 150 s | `swarm/agents.py`, `orchestrator.py` | suite de presupuesto |
| **C4** | Contrato de entregable: `pide_artefacto()` + `_contrato_de_entregable()`; sin código, sin verificación o sin artefacto la entrega sale marcada `[INCOMPLETO]` | `swarm/intencion.py`, `orchestrator.py` | `test_contrato_de_entregable.py` |
| **C5** | El prompt de Melchior nombra el catálogo y prohíbe responder de memoria teniendo herramienta | `swarm/agents.py` | revisión del prompt |
| **C7** | `verificado` ≠ `ok`: cero bloques ya no cuentan como verificado; el estado se persiste en la tarea | `core/verification.py`, `orchestrator.py` | `test_phase2.py` + contrato |
| **C8** | La auditoría mide entregado/producido, bloques de código, artefacto y `[INCOMPLETO]` | `scripts/auditar_sistema.py` | el propio informe |
| **C10** | Presupuesto de dependencias en el prompt, con la medida de tkinter (9 MB) frente a pygame (30-40) | `swarm/agents.py` | revisión del prompt |
| **C12** | `_contraste_con_el_registro`: si la síntesis dice «se compiló» y no consta artefacto, sale aviso | `orchestrator.py` | `test_declarar_una_compilacion_que_no_consta_sale_avisado` |
| **C13** | Naoko no sondea con tareas vivas; 0/N canarios es «no concluyente», no deriva | `infrastructure/naoko.py` | `test_medir_no_envenena.py` |
| **C14** | Ritsuko pide por **familia**, no por alias de modelo | `infrastructure/ritsuko.py` | `test_ritsuko.py` |
| **C15** | Casper empieza diciendo cómo entendió el encargo y qué decidió en lo ambiguo | `swarm/agents.py` | revisión del prompt |
| **C16** | El artefacto debe traer autoprueba (`--autotest`) y comprobar las propiedades pedidas | `swarm/agents.py` | revisión del prompt |
| **B1** | Los bloques Python se verifican **unidos** primero; solo si falla el conjunto se cae al modo por bloque | `core/verification.py` | `test_phase2.py` |
| **B2** | `max_iters` = 4 en motor `fast` (era 10) | `swarm/agents.py` | suite del enjambre |
| **B4** | Hedge también en la puerta de las herramientas (`run_agent` propaga `hedge`) | `core/agent_loop.py`, `swarm/agents.py` | `test_hedge_selectivo.py` |
| **B8** | La sonda espera a que el enjambre esté quieto | `core/kernel.py` | `test_medir_no_envenena.py` |
| **B9** | Una tarea reanudada con las rondas agotadas amplía margen y **lo dice**, en vez de callarse | `orchestrator.py` | — (reproducido a mano) |
| **B10** | `AASLoader` deja de gritar en cada arranque por un repositorio opcional | `modules/skills/loader.py` | arranque limpio |

## No hecho, y por qué

| Bloque | Por qué se queda fuera |
|---|---|
| **C6** | El `TypeError: argument of type 'NoneType' is not iterable` de HuggingSpace no se reproduce sin llamar al proveedor real, y arreglar a ciegas un adaptador de terceros es cómo se meten fallos peores. Queda con la evidencia guardada (`docs/comparativa/prueba-A-magi.json`) para atacarlo cuando se pueda reproducir. Lo que **sí** está hecho es que un proveedor roto ya no se confunde con uno agotado en el camino del árbitro (C11). |
| **B3** | Caché de propuesta por (tarea, ronda, rama). Es la mejora con más riesgo de todas: una caché mal invalidada devuelve la propuesta anterior y el usuario ve un sistema que ignora sus correcciones. Se hace después de B4, con las medidas de B4 delante. |
| **B5** | Una sola política de selección consultada desde las dos puertas. Requiere tocar `ProviderRegistry` en su camino más caliente; con B4 recién metido, hacerlo a la vez impediría saber cuál de los dos cambios movió los números. |
| **B7** | Subir el factor de solape de 1,4× a 2,5×. Aquí no hay diagnóstico todavía: sé que hay 294 s de espera en 206 s de pared, pero no dónde se serializa. Reducir el candado «por si acaso» es exactamente el tipo de cambio que introduce carreras. Primero medir, después tocar. |

## Cómo se comprueba que esto funcionó

`python scripts/auditar_sistema.py --con-ritsuko` sobre la misma tarea de
referencia, antes y después. Los números que tienen que moverse:

| Métrica | Antes (medido 20-ago) | Objetivo |
|---|---|---|
| `APPROVED` sobre un turno degradado | 3 de 3 pruebas | 0 |
| Caracteres entregados / producidos | 0,8 % y 1,9 % | ≥ 60 % |
| Encargo de `.exe` cerrado sin artefacto ni aviso | 2 de 2 | 0 (sale `[INCOMPLETO]`) |
| Derivas declaradas durante una tarea viva | 4 | 0 |
| Rebuild por bloques verificados sueltos | 1 en la tarea trivial | 0 |
