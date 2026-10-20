# Día 1 — Diseño e integración del algoritmo genético

**Proyecto:** Del silbido a la flauta — síntesis instrumental con algoritmos
genéticos.
**Documento de entrega:** [diseño conjunto](diseno_completo_ag_dia1.md), pendiente
de decisiones, paginación y firmas. Este archivo es el anexo técnico.
**Alcance:** diseño y contratos disponibles para revisar el Día 1.
No afirma que exista un ciclo generacional completo ni que se hayan
ejecutado experimentos. Las firmas de conformidad deben completarse por el
equipo.

## Objetivo y datos

Usar las notas y duraciones extraídas del silbido para sintetizar una flauta y
optimizar sus parámetros tímbricos. La melodía procesada se lee de
`datos/procesados/melodia_01.csv`; el audio de referencia utilizado por la
prueba de integración es `datos/audio/referencias/flauta_referencia_01.wav`.
La lectura del CSV no vuelve a ejecutar la extracción desde el WAV original.

La síntesis y el fitness requieren audio mono a 22050 Hz, alineado y con igual
número de muestras. El fitness rechaza longitudes incompatibles; no recorta ni
remuestrea automáticamente. Los silencios de la melodía se representan como
nota MIDI `-1`.

## Cromosoma — Rol 1

El genotipo es un vector continuo de ocho `float64` normalizados en
`[0, 1]^8`. En orden:

| Índice | Gen | Rango físico |
|---:|---|---:|
| 0 | `amp_arm1` | 0.10–1.00 |
| 1 | `amp_arm2` | 0.00–0.80 |
| 2 | `amp_arm3` | 0.00–0.50 |
| 3 | `ataque_s` | 0.005–0.250 s |
| 4 | `decaimiento_s` | 0.005–0.300 s |
| 5 | `sostenido_rel` | 0.10–1.00 |
| 6 | `relajacion_s` | 0.005–0.300 s |
| 7 | `ruido_soplo` | 0.00–0.25 |

`codificar()` transforma valores físicos a la escala normalizada y los recorta
a `[0,1]`; `decodificar()` realiza la transformación inversa. `validar_individuo()`
comprueba forma, finitud, límites y que ataque + decaimiento + relajación no
supere 1 s. La síntesis acepta el cromosoma normalizado, valida sus ocho genes
y genera ruido reproducible si se proporciona la misma semilla.

## Síntesis y fitness — Rol 2

`sintetizar_instrumento()` genera audio mono `float32` a 22050 Hz mediante
síntesis aditiva de tres armónicos, envolvente ADSR y ruido de soplo. Recibe
notas MIDI, duraciones, cromosoma y una semilla opcional para la síntesis.
La fórmula efectiva es `(0.9/2.55) * ADSR * (armónicos + ruido)`: el ruido
también recibe la envolvente. Se omiten armónicos sobre Nyquist y se comprimen
los tiempos ADSR proporcionalmente si no caben en la duración del evento.

`evaluar_individuo()` sintetiza el candidato y devuelve **una métrica elegida**:

- `metrica="stft"`: la magnitud STFT usa ventana Hann, `N_FFT=2048`,
  `SALTO=256`, conversión a dB con piso de `-80 dB` y referencia fija de
  amplitud 1. El error es la media del error absoluto en dB y el fitness a
  maximizar es `1 / (1 + error_stft_db / 10)`.
- `metrica="croma"`: similitud coseno media por cuadro entre cromas de 12
  clases de altura, en `[0,1]`, a maximizar.

`evaluar_audio()` devuelve ambas métricas por separado
(`error_stft_db`, `fitness_stft`, `fitness_croma`). El código no combina STFT y
croma en un fitness compuesto. La referencia y el candidato deben ser mono,
finitos, tener al menos 2048 muestras y ser de igual longitud.

## Parámetros de dinámica — Rol 4, Día 1

Parámetros base implementados por el Rol 4:

- Población base: 50 individuos; tamaños previstos: 20, 50 y 100.
- Máximo: 50 reemplazos después de evaluar la generación 0.
- Elitismo base: 2 individuos, copiados independientemente.
- Selección: torneo con `k=3`, reutilizando `seleccion_torneo()` del Rol 3.
- Aptitud: maximización; se conserva la correspondencia entre orden de
  población y vector de fitness.
- Parada: mejora acumulada menor que `1e-4` en ventana de 10 transiciones
  (11 mejores globales); no hay contador reiniciable de mejoras individuales.
- Un `numpy.random.Generator` compartido por corrida.
- Estadísticas disponibles: fitness máximo, media, desviación estándar y
  diversidad genética (media de desviaciones estándar por gen).

`src/configuracion.py` prepara 12 configuraciones y declara las semillas
previstas `42, 101, 2024, 7, 999` como réplicas. Según la implementación
actual, la matriz factorial completa es N={20,50,100} × élites={1,2} ×
p_mutación={0.02,0.08}. Son 12 configuraciones y cinco réplicas por configuración,
no resultados obtenidos. Niveles y tasas deben ratificarse. El plan detallado,
las tres combinaciones propuestas y la comparación de métricas están en
[el plan del Rol 5](../analisis_rol5.md).

## Estado real de integración y pendientes

Hay funciones de inicialización, evaluación de población, elitismo,
estadísticas y detección de estancamiento, además de selección por torneo.
Todavía no hay un ciclo completo de generaciones integrado. Las interfaces de
cruce y mutación, así como sus decisiones de parámetros, permanecen a cargo
del Rol 3 y pendientes de confirmación. Por tanto, no se declara operativo el
algoritmo genético completo.

El notebook `notebooks/00_integracion.ipynb` comprueba con datos reales la
conexión entre la melodía procesada, el cromosoma, la síntesis y el fitness.
No ejecuta el AG ni el plan factorial.

## Decisiones a confirmar

1. Ratificar los factores que forman las 12 configuraciones, en particular
   elitismo alternativo y probabilidades de mutación.
2. Definir los contratos de cruce/mutación y el ciclo generacional del AG.
3. Ratificar STFT como propuesta base y croma como comparación separada. El diseño
   anterior describía STFT con `N_FFT=1024`, distancia euclídea de croma y una
   combinación de ambas; esas definiciones contradicen `src/fitness.py`.
4. Instrumentar en el Día 2 el contador de llamadas reales del pseudocódigo
   del Rol 4: incluye población inicial y reevaluaciones efectivas. El baseline
   igualará ese contador por corrida, también con parada temprana.
