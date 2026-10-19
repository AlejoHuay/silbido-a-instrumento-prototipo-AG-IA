# Contrato del Cromosoma y Especificación de Interfaces (Rol 1)

**Estado:** APROBADO (Versión 1.0 - Día 1)  
**Responsables Directos:** Rol 1 (Representación y Extracción) y Rol 2 (Síntesis y Fitness)  
**Consumidores:** Rol 3 (Operadores), Rol 4 (Dinámica Poblacional) y Rol 5 (Meta-evaluación)  

---

## 1. Representación del Individuo

- **Instrumento objetivo:** Flauta traversa / dulce.
- **Tipo de estructura:** Vector unidimensional continuo NumPy `float64` de longitud fija ($D = 8$).
- **Espacio genotípico:** Hipercubo unitario normalizado $[0.0, 1.0]^8$.
- **Espacio fenotípico:** Espacio físico acústico en unidades SI (segundos, amplitudes relativas).
- **Flexibilidad arquitectónica:** Esquema desacoplado mediante `GENES_SCHEMA` en `src/representacion.py`. Si se añaden o remueven genes (e.g. vibrato, modulación FM), la interfaz se preserva automáticamente sin alterar el código de los Roles 3 y 4.

### Tabla Oficial de Genes

| Índice | Identificador | Tipo | Unidad | Mínimo | Máximo | Default (Flauta) | Justificación Física / Acústica |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---|
| `0` | `amp_arm1` | `float` | amp. rel. | `0.10` | `1.00` | `0.90` | Amplitud del tono fundamental ($f_0$). Dominante en el timbre cuasi-senoidal de la flauta. |
| `1` | `amp_arm2` | `float` | amp. rel. | `0.00` | `0.80` | `0.25` | Segundo armónico ($2f_0$). Aporta presencia tímbrica y brillo moderado. |
| `2` | `amp_arm3` | `float` | amp. rel. | `0.00` | `0.50` | `0.08` | Tercer armónico ($3f_0$). Sutil en el registro medio y agudo. |
| `3` | `ataque_s` | `float` | segundos | `0.005` | `0.250` | `0.050` | Tiempo de ataque ADSR. Transitorio suave de la columna de aire en la embocadura. |
| `4` | `decaimiento_s` | `float` | segundos | `0.005` | `0.300` | `0.080` | Tiempo de decaimiento ADSR hasta el régimen estacionario. |
| `5` | `sostenido_rel` | `float` | amp. rel. | `0.10` | `1.00` | `0.80` | Nivel relativo de sostenido mientras se sopla la nota. |
| `6` | `relajacion_s` | `float` | segundos | `0.005` | `0.300` | `0.060` | Tiempo de relajación ADSR tras cortar la columna de aire. |
| `7` | `ruido_soplo` | `float` | amp. rel. | `0.00` | `0.25` | `0.04` | Ruido de turbulencia de aire (*breath noise*) generado en el bisel de la flauta. |

---

## 2. Codificación y Decodificación

- **`codificar(fenotipo: dict | Sequence) -> np.ndarray`**:
  - Mapeo lineal: $g_i = \frac{x_i - \min_i}{\max_i - \min_i}$.
  - Retorna un arreglo `float64` acotado estrictamente en $[0.0, 1.0]$.
- **`decodificar(cromosoma: np.ndarray) -> dict[str, float]`**:
  - Mapeo inverso: $x_i = \min_i + g_i \cdot (\max_i - \min_i)$.
  - Retorna un diccionario con los nombres de los genes y valores en unidades físicas.
- **`decodificar_a_array(cromosoma: np.ndarray) -> np.ndarray`**:
  - Mapeo inverso a arreglo NumPy directo para cálculos vectorizados de alta velocidad en el Rol 2.
- **Garantía de Invertibilidad:**
  $$\left| \text{decodificar}(\text{codificar}(x)) - x \right| < 10^{-5} \quad \forall x \in \text{Rango}$$
- **Tratamiento de valores fuera de rango:**
  - `restringir_limites(cromosoma)` aplica recorte rígido (*clipping*) mediante `np.clip(g, 0.0, 1.0)` tras cualquier operador genético (cruce o mutación).

---

## 3. Análisis del Espacio de Búsqueda (Justificación de Metaheurística)

- Con una discretización estándar de $10^{-3}$ ($1000$ niveles de resolución por gen):
  - Número de genes: $D = 8$.
  - Combinatoria total: $S \approx 1.76 \times 10^{21}$ estados posibles.
  - Bits de información equivalentes: $\approx 70.6$ bits.
- **Intratabilidad por fuerza bruta:**
  - Evaluando 1,000 individuos por segundo en una CPU moderna, una búsqueda exhaustiva requeriría más de **55 mil millones de años**.
  - Esto justifica formalmente la necesidad de metaheurísticas poblacionales guiadas como el Algoritmo Genético.

---

## 4. Contrato de Datos de la Melodía

- **Formato compartido:**
  - Audio original y procesado: WAV mono, $22050\text{ Hz}$, PCM 16-bit.
  - Representación en memoria: `notas_midi` (`int32[N]`) y `duraciones_s` (`float64[N]`).
  - Silencios: representados estrictamente con el valor `-1`.
  - Persistencia: archivo CSV en `datos/procesados/melodia_01.csv` con cabecera `nota_midi,duracion_s`.
- **Melodía base prevista:** Sol5–La5–Si5–La5–Sol5 (MIDI: 79, 81, 83, 81, 79).
- **Archivos acordados:**
  - Silbido de entrada: `datos/audio/silbidos/silbido_01.wav`.
  - Referencia de flauta: `datos/audio/referencias/flauta_referencia_01.wav`.
  - Eventos procesados: `datos/procesados/melodia_01.csv`.

---

## 5. Protocolo de Calibración para la Grabación Definitiva (Checkpoints)

Cuando el integrante del equipo grabe el silbido humano real, se ejecutará `diagnosticar_audio_silbido()` para validar:
1. **Ausencia de Clipping:** $\le 0.1\%$ de muestras al límite de saturación.
2. **Relación Señal/Ruido (SNR):** $\ge 15\text{ dB}$.
3. **Estabilidad de Tono:** Ausencia de transiciones violentas que falseen la escala diatónica.
4. **Respeto a los silencios:** Claridad de corte entre notas sucesivas ($\ge 0.05\text{ s}$).

---

## 6. Firmas y Aprobación de Interfaces

- **Rol 1 (Representación y Extracción):** Aprobado e Implementado.
- **Rol 2 (Síntesis y Fitness):** Compatible con `decodificar_a_array` y `datos/procesados/melodia_01.csv`.
- **Rol 3 (Operadores):** Compatible con individuos normalizados $[0.0, 1.0]^8$ y `restringir_limites`.
- **Rol 4 (Dinámica Poblacional):** Compatible con `generar_poblacion_inicial(tam_poblacion)`.
