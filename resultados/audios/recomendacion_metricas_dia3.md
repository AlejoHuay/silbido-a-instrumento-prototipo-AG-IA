# Rol 2 — Recomendación de métrica del Día 3

## Condiciones de comparación

- Candidatos evaluados: 6.
- Semilla de candidatos: 42.
- Semilla de síntesis: 2026.
- Genes analizados: 8.
- Puntos por gen: 51.
- Evaluaciones de sensibilidad: 408.
- Se utilizó la misma melodía y referencia para ambas métricas.

## Selección de candidatos

STFT seleccionó **default**:

- Fitness STFT: 0.679606.
- Error espectral medio: 4.714410 dB.

Croma seleccionó **aleatorio_2**:

- Fitness croma: 0.920207.

Las métricas seleccionaron candidatos diferentes.

Las puntuaciones STFT y croma no se comparan directamente
entre sí porque sus escalas y criterios son distintos.

## Respuesta a los genes

El mayor rango de variación STFT correspondió a
**ruido_soplo**:
0.262472.

El mayor rango de variación de croma correspondió a
**relajacion_s**:
0.064137.

Son resultados de barridos individuales alrededor del
cromosoma por defecto. No describen sensibilidad global.

## Recomendación al Rol 4

Se propone usar `metrica="stft"` como aptitud principal
a maximizar y registrar croma como evaluación complementaria.

STFT permite evaluar diferencias espectrales relevantes
para el timbre. Croma aporta una comparación de alturas.

La recomendación es provisional hasta contrastarla con
la escucha y acordarla con el equipo. No se propone
un fitness combinado ni cambios de escala en esta etapa.

## Alcance

Esta comparación no ejecuta el AG y no demuestra convergencia
ni superioridad perceptual. El proyecto ya dispone de
`ejecutar_ag()` para realizar las corridas correspondientes.
