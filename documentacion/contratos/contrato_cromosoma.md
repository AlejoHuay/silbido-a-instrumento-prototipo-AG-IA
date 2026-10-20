# Contrato del Cromosoma y Especificación de Interfaces (Rol 1)

**Estado:** contrato implementado; ratificación y firmas del equipo pendientes.
Documento de entrega: [diseño conjunto](../diseno/diseno_completo_ag_dia1.md).
**Responsables Directos:** Rol 1 (Representación y Extracción) y Rol 2 (Síntesis y Fitness)  
**Consumidores:** Rol 3 (Operadores), Rol 4 (Dinámica Poblacional) y Rol 5 (Meta-evaluación)  

---

## 1. Representación del Individuo

- **Instrumento objetivo:** Flauta traversa / dulce.
- **Tipo de estructura:** Vector unidimensional continuo NumPy `float64` de longitud fija ($D = 8$).
- **Espacio genotípico:** Hipercubo unitario normalizado $[0.0, 1.0]^8$.
- **Espacio fenotípico:** Espacio físico acústico en unidades SI (segundos, amplitudes relativas).
- **Flexibilidad arquitectónica:** Esquema en `GENES_SCHEMA`; los consumidores obtienen D con `num_genes()`. Añadir o retirar genes requiere revisar la validación y la síntesis, que usan nombres concretos.

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
  $$\left| \text{decodificar}(\text{codificar}(x)) - x \right| < 10^{-15} \quad \forall x \in \text{Rango}$$
- **Tratamiento de valores fuera de rango:**
  - `restringir_limites(cromosoma)` aplica recorte rígido (*clipping*) mediante `np.clip(g, 0.0, 1.0)` tras cualquier operador genético (cruce o mutación).

---

## 3. Análisis del Espacio de Búsqueda (Justificación de Metaheurística)

- Con paso absoluto de $10^{-3}$ en las unidades físicas de cada gen, no 1000 niveles por gen normalizado:
  - Número de genes: $D = 8$.
  - Niveles en orden del esquema: 901, 801, 501, 246, 296, 901, 296, 251.
  - Producto verificado con `calcular_tamano_espacio_busqueda()`: 1762430802969797099136.
  - Combinatoria total: $S \approx 1.76 \times 10^{21}$ estados posibles.
  - Bits de información equivalentes: $\approx 70.6$ bits.
- **Intratabilidad por fuerza bruta:**
  - Evaluando 1,000 individuos por segundo en una CPU moderna, una búsqueda exhaustiva requeriría más de **55 mil millones de años**.
  - Esto descarta la búsqueda exhaustiva a esa resolución, pero no demuestra superioridad del AG frente a otras estrategias.

---

## 4. Contrato de Datos de la Melodía y Audio Real

- **Formato compartido:**
  - Audio de trabajo procesado: WAV mono, $22050\text{ Hz}$, PCM 16-bit. El original `sample.wav` conserva estéreo, 48000 Hz y PCM de 8 bits.
  - Representación en memoria: `notas_midi` (`int32[N]`) y `duraciones_s` (`float64[N]`).
  - Silencios: representados estrictamente con el valor `-1`.
  - Persistencia: archivo CSV en `datos/procesados/melodia_01.csv` con cabecera `nota_midi,duracion_s`.
- **Registro Real Extraído:**
  - Audio origen: `datos/audio/silbidos/sample.wav` (convertido a `datos/audio/silbidos/silbido_01.wav`).
  - Eventos vigentes del CSV: 11 notas entre MIDI 88 y 96 (Mi6–Do7) y 5 silencios; no la secuencia sintética Sol5–La5–Si5.
  - Silbido procesado: 2.694966 s; CSV: 2.705 s. Referencia y síntesis: 59645 muestras (2.704989 s).
  - Relación Señal/Ruido: $40.8\text{ dB}$ (señal limpia y apta).
- **Archivos de Trabajo:**
  - Silbido de entrada: `datos/audio/silbidos/silbido_01.wav`.
  - Referencia de flauta: `datos/audio/referencias/flauta_referencia_01.wav` (o precursora en `datos/audio/referencias/pre1.wav`).
  - Eventos procesados: `datos/procesados/melodia_01.csv`.

---

## 5. Compatibilidad técnica; aprobación pendiente

- **Rol 1 (Representación y Extracción):** Implementado con audio real procesado; no se encontraron firmas que acrediten aprobación colectiva.
- **Rol 2 (Síntesis y Fitness):** La síntesis usa `decodificar()` y consume los eventos de `datos/procesados/melodia_01.csv`.
- **Rol 3 (Operadores):** Torneo compatible con individuos normalizados $[0.0, 1.0]^8$ y `validar_individuo()`; rechaza inválidos sin recortarlos.
- **Rol 4 (Dinámica Poblacional):** Compatible con `generar_poblacion_inicial(tam_poblacion)`.
