# Representación

**Extracción:** silbido real acondicionado a WAV mono, 22050 Hz, 16-bit PCM
(`datos/audio/silbidos/silbido_01.wav`). Relación señal-ruido: 40.8 dB; 0.0% de clipping.
Tracking de $f_0$ con pYIN + filtro de mediana (5 cuadros) acotado a 500–3000 Hz.
Detección de silencios por energía RMS (< −40 dB codificado como −1).
Segmentación RLE a escala temperada occidental ($A_4 = 440\text{ Hz}$): 16 eventos melódicos
(11 notas activas entre Mi6 y Do7, MIDI 88–96, y 5 silencios) con duración total de 2.705 s
(`datos/procesados/melodia_01.csv`).

## Esquema canónico del cromosoma

Cromosoma en espacio continuo real sobre el hipercubo normalizado $[0.0, 1.0]^8$.
Transformación afín biunívoca e invertible entre genotipo normalizado y fenotipo físico:

| Índice | Gen | Tipo | Unidad | Rango físico | Default (Flauta) | Función acústica en síntesis |
|:---:|:---|:---:|:---:|:---:|:---:|:---|
| `0` | `amp_arm1` | `float` | amp. rel. | `[0.10, 1.00]` | `0.90` | Amplitud de frecuencia fundamental ($f_0$); timbre cuasi-senoidal |
| `1` | `amp_arm2` | `float` | amp. rel. | `[0.00, 0.80]` | `0.25` | Segundo armónico ($2f_0$); presencia espectral y cuerpo |
| `2` | `amp_arm3` | `float` | amp. rel. | `[0.00, 0.50]` | `0.08` | Tercer armónico ($3f_0$); brillo tímbrico superior |
| `3` | `ataque_s` | `float` | segundos | `[0.005, 0.250]` | `0.050` | Transitorio de ataque ADSR en la columna de aire |
| `4` | `decaimiento_s` | `float` | segundos | `[0.005, 0.300]` | `0.080` | Caída ADSR hasta régimen estacionario |
| `5` | `sostenido_rel` | `float` | amp. rel. | `[0.10, 1.00]` | `0.80` | Nivel relativo de sostenido mientras dura el soplido |
| `6` | `relajacion_s` | `float` | segundos | `[0.005, 0.300]` | `0.060` | Extinción ADSR tras corte de insuflación |
| `7` | `ruido_soplo` | `float` | amp. rel. | `[0.00, 0.25]` | `0.04` | Turbulencia aerodinámica de aire en el bisel |

**Invertibilidad comprobada:** $\left|\text{decodificar}(\text{codificar}(x)) - x\right| < 10^{-12}$ en 1000 muestras aleatorias y en el default.
**Protección defensiva:** `restringir_limites()` aplica clipping rígido a $[0, 1]$ ante operadores continuos desbordantes (e.g. BLX-$\alpha$). `validar_individuo()` comprueba forma $(8,)$, finitud y rango.

## Espacio de búsqueda y metaheurística

- **Discretización física:** resolución $\Delta = 0.001$ en unidades físicas por gen con extremos incluidos: $\lfloor(\max - \min)/\Delta\rfloor + 1$.
- **Niveles por gen:** `[901, 801, 501, 246, 296, 901, 296, 251]`.
- **Combinatoria total:** $1,762,430,802,969,797,099,136 \approx 1.76 \times 10^{21}$ estados posibles.
- **Entropía de información:** $70.58\text{ bits}$ equivalentes.
- **Intratabilidad por fuerza bruta:** a 1000 evaluaciones/s requeriría $> 5.58 \times 10^{10}\text{ años}$, descartando búsqueda exhaustiva.

## Codificación continua vs. acantilados de Hamming

- **Representación binaria tradicional:** cuantizar parámetros a 8 bits genera acantilados de Hamming (e.g., $127_{10} = 01111111_2$ y $128_{10} = 10000000_2$ distan a 8 mutaciones simultáneas; $p_m^8 \approx 3.9 \times 10^{-11}$).
- **Representación continua en $[0, 1]^8$ (RCGA):** preserva la causalidad y localidad topológica; perturbaciones genotípicas suaves producen variaciones acústicas suaves.

## Sensibilidad 1D (Reporte de Rol 1 a Rol 2)

Barrido unidimensional de 8 genes $\times$ 51 puntos = 408 evaluaciones reales contra `flauta_referencia_01.wav`.

| Gen | Rango fitness STFT | Rango fitness croma | Categoría |
|---|---:|---:|---|
| `ruido_soplo` | **0.262472** | 0.000379 | Hipersensible en STFT ($\Delta \text{error} = 8.04\text{ dB}$, $\max |\nabla| = 0.50$) |
| `sostenido_rel` | 0.040001 | 0.043348 | Sensibilidad moderada |
| `relajacion_s` | 0.018473 | **0.064137** | Sensible en Croma (solapamiento temporal) |
| `ataque_s` | 0.013708 | 0.057390 | Sensible en Croma |
| Armónicos 1–3 | 0.0028 – 0.0093 | 0.0007 – 0.0155 | Respuesta suave / amortiguada |

[Curvas de sensibilidad 1D para insertar](../../resultados/sensibilidad/figura_sensibilidad_1d_todos_los_genes.png)

[Ranking tornado de impacto para insertar](../../resultados/sensibilidad/figura_tornado_sensibilidad.png)

**Hallazgo clave:** STFT y Croma son ortogonales y complementarias: STFT captura timbre y ruido blanco pero es sorda a la tonalidad pura; Croma evalúa afinación y solapamiento de notas pero es insensible al ruido de fondo.
