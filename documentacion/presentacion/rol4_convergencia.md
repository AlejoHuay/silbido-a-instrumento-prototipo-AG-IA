# Convergencia

**Dinámica poblacional:** `ejecutar_ag()` inicializa, evalúa y reemplaza la población por generaciones. Conserva los mejores individuos mediante elitismo y registra máximo global, media, desviación de fitness y diversidad genotípica. Un único `rng` controla la aleatoriedad de cada corrida.

## Configuración propuesta para la demostración STFT

| Elemento | Valor propuesto |
|---|---:|
| Población y límite | N=100, máximo 50 reemplazos |
| Elitismo y selección | 2 élites, torneo k=3 |
| Cruce | Uniforme, probabilidad 0.90 por pareja |
| Mutación | Gaussiana, probabilidad 0.08 por gen, sigma=0.08 |
| Parada | Paciencia 10, tolerancia `1e-4` |

La propuesta usa la combinación **B: torneo + uniforme + gaussiana**. Los valores predeterminados de `ConfiguracionAG` permanecen en N=50 y mutación 0.05. La demostración crea una configuración explícita para no alterar contratos ni resultados anteriores.

## Evidencia de convergencia y diversidad

| Combinación | STFT medio final ↑ | Diversidad final | Diversidad inicial media |
|---|---:|---:|---:|
| A: torneo / BLX / gaussiana | 0.726136 | 0.009409 | 0.285487 |
| **B: torneo / uniforme / gaussiana** | **0.730850** | 0.009313 | 0.285487 |
| C: SUS / BLX / no uniforme | 0.724787 | **0.125190** | 0.285487 |

**Dos semillas, 42 y 101. 2550 evaluaciones por corrida. STFT provisional.** A y B conservaron cerca de 3.3 % de la diversidad inicial. C conservó cerca de 43.9 %, pero no logró mayor fitness medio. Más diversidad no garantiza mejor aptitud.

## Convergencia prematura

Ocurre cuando la población pierde diversidad antes de explorar suficientemente y se concentra alrededor de una solución subóptima. Se detecta combinando:

- estancamiento del mejor fitness durante una ventana de paciencia.
- estabilización de la media y de la dispersión del fitness.
- caída sostenida de la diversidad genotípica.

La baja diversidad de A y B indica **concentración**, pero no demuestra por sí sola convergencia prematura. B obtuvo el mayor fitness medio y estas corridas usaron tolerancia cero para igualar el presupuesto, por lo que no probaron la parada operativa.

El factorial integrado evaluó 12 configuraciones × cinco semillas por métrica con la parada operativa. La mayor media STFT alcanzó **0.731953** con N=100, elitismo=2 y mutación=0.08. Croma favoreció N=100, elitismo=1 y mutación=0.08, por lo que la recomendación depende de la métrica y no constituye un óptimo universal.

**Cómo reducir el riesgo:** moderar elitismo o presión selectiva y adaptar la mutación cuando caiga la diversidad. El equipo podría incorporar inmigrantes o reinicios parciales, pero todavía no implementó ni probó esas estrategias.

[Curvas de mejor fitness para insertar](../../resultados/operadores/dia3_2026-10-21_64617f8/fitness.svg)

[Curvas de diversidad para insertar](../../resultados/operadores/dia3_2026-10-21_64617f8/diversidad.svg)

**Código:** `src/configuracion.py` y `src/algoritmo_genetico.py`.

**Fuentes:** `resultados/operadores/dia3_2026-10-21_64617f8/resumen.csv` y `documentacion/rol4_dia4.md`. La lámina reutiliza resultados guardados y no ejecuta corridas nuevas.
