# Evaluación

**Síntesis:** ocho genes controlan tres armónicos, envolvente ADSR
y ruido de soplo. Se conservan las notas y duraciones del silbido.
Audio mono a 22050 Hz; semilla de síntesis 2026.

| Métrica | Qué compara | Aptitud |
|---|---|---|
| STFT en dB | Magnitudes espectrales y evolución temporal | `1 / (1 + error_db / 10)`, rango `(0, 1]` |
| Croma | Energía en doce clases de altura | Similitud coseno media, rango `[0, 1]` |

**Mayor aptitud es mejor.** STFT utiliza ventana Hann, FFT 2048,
salto 256 y piso −80 dB, con referencia fija de amplitud 1.

Se evita MSE sobre la onda cruda porque pequeñas diferencias
de fase pueden producir errores grandes entre sonidos similares.

## Comparación de métricas

| Candidato | Error STFT, dB ↓ | Fitness STFT ↑ | Fitness croma ↑ |
|---|---:|---:|---:|
| `default` | **4.714410** | **0.679606** | 0.914508 |
| `aleatorio_2` | 5.495775 | 0.645337 | **0.920207** |

**Seis candidatos: default y cinco aleatorios con semilla 42.**
STFT y croma seleccionan candidatos diferentes.
Esta comparación no ejecuta evolución.

## Superficie de fitness

Relaciona cada cromosoma con su aptitud. Una respuesta relativamente
suave facilita ajustes pequeños mediante mutación, aunque el AG
no necesita derivadas ni garantiza encontrar el óptimo global.

**Ocho barridos × 51 puntos = 408 evaluaciones**, reutilizando
`src/sensibilidad.py` del Rol 1.

| Gen | Rango de fitness STFT | Rango de fitness croma |
|---|---:|---:|
| `ruido_soplo` | **0.262472** | 0.000379 |
| `ataque_s` | 0.013708 | 0.057390 |
| `relajacion_s` | 0.018473 | **0.064137** |

STFT responde más al soplo; croma muestra mayor variación ante
ataque y relajación en estos cortes. Son respuestas distintas,
sin demostrar superioridad perceptual de una métrica.

[Gráfico de superficie para insertar](../../resultados/audios/rol2_dia4_superficie_fitness.png)

[Comparación STFT y croma en los ocho genes](../../resultados/audios/rol2_dia4_complementariedad.png)

**Recomendación provisional:** STFT como aptitud principal
y croma como evaluación complementaria, pendientes de ratificación.

**Límites:** los cortes modifican un gen a la vez; no prueban
suavidad global, interacciones ni convergencia prematura.
La sensibilidad al soplo requiere interpretación y escucha.

**Fuentes:** `resultados/audios/comparacion_metricas.csv`
y `resultados/audios/rol2_dia3_ranking_metricas.csv`.
Resultados guardados del proyecto; no corresponden a nuevas corridas.