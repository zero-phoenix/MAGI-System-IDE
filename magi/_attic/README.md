# Ático — módulos retirados de la ruta de importación

Estos módulos estaban en `magi/` pero **devolvían valores aleatorios presentados
como análisis**. Se retiran aquí, no se borran, porque documentan la intención
original y pueden reimplementarse de verdad.

Regla del Plan MAGI 9.0: *cada fase conecta o borra, nunca añade sin conectar.*

---

## `quantum_oracle.py`

Declaraba resolver problemas NP-duros mediante «recocido cuántico simulado».
El cuerpo entero era:

```python
await asyncio.sleep(0.8)
collapse_state = random.choice(["Alpha-Route", "Beta-Route", "Gamma-Route"])
return collapse_state
```

Se instanciaba en `main.py` y **nunca se llamaba**. Su única función efectiva era
que se imprimiera `MAGI 5.0 Bio-Quantum: [Octopus Topology y Oráculo QML]` en el
arranque.

**Para reimplementarlo de verdad** haría falta un solver real (OR-Tools,
simulated annealing sobre una función objetivo concreta) y un problema
combinatorio que el sistema tenga de verdad — por ejemplo, ordenar la ejecución
de herramientas o repartir cuota entre proveedores.

---

## `quant_simulator.py` (antes `magi/modules/quant/simulator.py`)

Declaraba ser un «Gemelo Digital de Mercado» con Montecarlo y análisis
geopolítico. El cuerpo:

```python
risk_off_index = np.random.randint(60, 101)
...
return {"action": "SHORT", "confidence": f"{np.random.randint(80, 100)}%",
        "take_profit": "+5.2%", "stop_loss": "-1.5%"}
```

Un generador de números aleatorios con vocabulario financiero, con take-profit y
stop-loss **hardcodeados**. No se llamaba, así que no llegó a hacer daño; pero
conectado tal cual habría producido recomendaciones de inversión inventadas con
una confianza inventada — que es peor que no tener el módulo, porque *parece*
un análisis.

**La versión construible** (Plan MAGI 9.0 §6.3), cuando se implemente:

| Componente | Fuente real |
|---|---|
| Fundamentales | SEC EDGAR XBRL (gratis, completo, desde 2009) |
| Precios | `yfinance`, Stooq |
| Macro | FRED (Reserva Federal de St. Louis) |
| Owner earnings | FCO − capex de mantenimiento, calculado en Python |
| DCF | Aritmética determinista en código, **nunca del LLM** |
| Registro de tesis | Cada tesis con fecha, puntuada después → calibración medible |

Regla dura: toda aritmética financiera se ejecuta en Python y se muestra la
fórmula. El modelo interpreta y argumenta; no calcula.
