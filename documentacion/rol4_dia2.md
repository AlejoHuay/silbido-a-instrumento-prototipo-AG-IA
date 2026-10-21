# Rol 4 - Implementación y primera corrida del Día 2

**Fecha:** 20 de octubre de 2026
**Estado:** ciclo completo implementado y primera corrida end-to-end verificada.

## Alcance entregado

`ejecutar_ag()` conecta las capas publicadas por los demás roles:

1. Inicializa cromosomas normalizados con un único generador por corrida.
2. Evalúa la población en orden y maximiza el fitness del Rol 2.
3. Conserva copias independientes de los élites.
4. Selecciona mediante torneo o SUS.
5. Cruza mediante BLX-alpha o cruce uniforme.
6. Muta mediante gaussiana o no uniforme, con probabilidad por gen.
7. Conserva exactamente el tamaño poblacional, incluso cuando queda una plaza.
8. Registra máximo, media, desviación y diversidad en cada generación.
9. Detiene por máximo de generaciones o por estancamiento.
10. Devuelve el mejor individuo, historial y conteo real de evaluaciones.

El ciclo reevalúa la población completa después de cada reemplazo, incluidas
las élites. Por ello, si se ejecutan `g` reemplazos con población `N`, el conteo
observado es `N * (g + 1)`.

## Primera corrida end-to-end

La corrida de integración usó la melodía procesada, la referencia WAV y el
fitness STFT reales. Para mantenerla breve se configuró:

| Parámetro | Valor |
|---|---:|
| Población | 5 |
| Elitismo | 1 |
| Reemplazos máximos | 3 |
| Semilla | 42 |
| Selección | Torneo, k=3 |
| Cruce | BLX-alpha, alpha=0.5 |
| Probabilidad de cruce | 0.90 por pareja |
| Mutación | Gaussiana, sigma=0.08 |
| Probabilidad de mutación | 0.05 por gen |

Resultados reproducibles observados:

| Generación | Fitness máximo | Fitness medio | Diversidad genética |
|---:|---:|---:|---:|
| 0 | 0.645337 | 0.546423 | 0.246326 |
| 1 | 0.645337 | 0.624719 | 0.149449 |
| 2 | 0.645904 | 0.644938 | 0.008491 |
| 3 | 0.649395 | 0.645936 | 0.018477 |

- Motivo de parada: `max_generaciones`.
- Evaluaciones reales: 20.
- Mejor fitness STFT: 0.6493946951971431.
- El notebook genera `resultados/audios/rol4_dia2_mejor.wav` al ejecutarse.

Estos valores corresponden a una comprobación de integración con población
pequeña, no a la comparación experimental de 12 configuraciones del Día 3.

## Verificación

- Las 51 pruebas del repositorio pasan.
- Las ocho combinaciones de los dos selectores, dos cruces y dos mutaciones
  completan una generación y mantienen cromosomas válidos.
- Se verificaron reproducibilidad, presupuesto de evaluaciones, parada por
  estancamiento, rechazo de opciones inválidas y copias independientes.
- `04_rol4_dinamica.ipynb` ejecutó sus siete celdas de código en un kernel
  Jupyter nuevo y una copia temporal del repositorio.
