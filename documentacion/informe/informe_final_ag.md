# Del Silbido al Instrumento: Un Prototipo de Síntesis Mediante Algoritmos Genéticos Continuos (RCGA)
### Examen Práctico Grupal — Inteligencia Artificial
**Universidad Católica Boliviana "San Pablo"**  
**Fecha:** Octubre de 2026  

---

## Carátula y Equipo de Trabajo

| Rol | Responsabilidad Técnica | Integrante | Firma / Estado |
| :---: | :---| :---| :---: |
| **Rol 1** | **El Codificador:** Representación y Extracción Acústica | **Juan Mateo Soruco** | *Completado y validado* |
| **Rol 2** | **El Traductor:** Síntesis y Función de Fitness | *[Completar por Rol 2]* | *Pendiente* |
| **Rol 3** | **El Motor Evolutivo:** Operadores Genéticos Continuos | *[Completar por Rol 3]* | *Pendiente* |
| **Rol 4** | **El Estratega:** Dinámica Poblacional y Convergencia | *[Completar por Rol 4]* | *Día 4 completado; firma pendiente* |
| **Rol 5** | **El Analista:** Meta-evaluación, Baseline e Integración | *[Completar por Rol 5]* | *Pendiente* |

---

## Resumen Ejecutivo

El presente proyecto aborda la transducción bio-acústica de un silbido humano real en una melodía sintetizada con timbre de flauta traversa mediante un Algoritmo Genético de Codificación Real (RCGA) desarrollado desde cero (*from scratch*) sin bibliotecas externas de optimización ni modelos de aprendizaje profundo. El sistema procesa la señal de audio capturada, segmenta la trayectoria de tono fundamental ($f_0$) en eventos melódicos temperados y optimiza un vector continuo de 8 parámetros acústicos (armónicos, envolvente temporal ADSR y turbulencia de aire) guiado por funciones de aptitud espectrales en decibelios (STFT) y cromáticas. A continuación, se presenta el informe técnico formal que consolida la arquitectura del sistema, el marco experimental y las respuestas a las cinco preguntas teóricas del examen.

---

## 1. Capa 1: Representación del Cromosoma y Extracción Acústica (Rol 1 — Juan Mateo Soruco)

### 1.1 Captura y Acondicionamiento Acústico de la Señal
La señal de entrada corresponde a una grabación real de silbido humano (`sample.wav`) capturada originalmente a 48.0 kHz en estéreo con cuantización de 8 bits. Para cumplir las restricciones de procesamiento digital de señales del proyecto:
1. **Normalización de formato:** Se convirtió la señal a estándar WAV mono, $f_s = 22,050\text{ Hz}$, PCM de 16 bits (`silbido_01.wav`), optimizando el compromiso entre ancho de banda acústico (límite de Nyquist en $11,025\text{ Hz}$) y costo computacional.
2. **Seguimiento de tono fundamental ($f_0$):** Se aplicó el algoritmo probabilístico pYIN (*probabilistic YIN*) acotado al registro de silbido humano ($500 - 3000\text{ Hz}$), seguido de un filtro de mediana temporal (ventana de 5 cuadros) para suprimir fluctuaciones y *octave errors*.
3. **Segmentación y Detección de Silencios:** Se detectaron regiones de silencio con umbral de energía RMS en $-40\text{ dB}$, codificándolas con la convención estándar `-1`. La señal fue segmentada por codificación por longitud de racha (RLE), cuantizando las frecuencias a notas de la escala temperada occidental ($A_4 = 440\text{ Hz}$) y persistiendo la secuencia en `datos/procesados/melodia_01.csv`.
   * *Diagnóstico acústico:* La señal posee una relación señal-ruido ($\text{SNR}$) de $40.8\text{ dB}$ con $0.0\%$ de saturación digital (*clipping*). La melodía contiene 16 eventos (11 notas activas entre $E_6$ y $C_7$, MIDI 88 a 96, y 5 pausas) con una duración total de $2.705\text{ s}$ ($59,645\text{ muestras}$).

### 1.2 Esquema Canónico del Cromosoma y Biyección Genotipo-Fenotipo
Se optó por una **representación cromosómica en espacio continuo real** sobre el hipercubo unitario $[0.0, 1.0]^8$. Cada individuo se define como un vector $\vec{g} = [g_0, g_1, \dots, g_7] \in [0.0, 1.0]^8$, mapeado linealmente a parámetros físicos de síntesis mediante transformaciones afines invertibles:

$$x_i = \min_i + g_i \cdot (\max_i - \min_i) \quad \Longleftrightarrow \quad g_i = \frac{x_i - \min_i}{\max_i - \min_i}$$

#### Tabla Canónica de Genes
| Índice | Gen | Tipo | Unidad | Mínimo | Máximo | Flauta Default | Justificación Física / Acústica |
| :---: | :---| :---: | :---: | :---: | :---: | :---: | :---|
| `0` | `amp_arm1` | `float` | amp. rel. | $0.10$ | $1.00$ | $0.90$ | Amplitud del tono fundamental ($f_0$). Dominante en el timbre cuasi-senoidal de la flauta. |
| `1` | `amp_arm2` | `float` | amp. rel. | $0.00$ | $0.80$ | $0.25$ | Segundo armónico ($2f_0$). Proporciona cuerpo tímbrico y presencia espectral. |
| `2` | `amp_arm3` | `float` | amp. rel. | $0.00$ | $0.50$ | $0.08$ | Tercer armónico ($3f_0$). Brillo sutil de orden superior. |
| `3` | `ataque_s` | `float` | segundos | $0.005$ | $0.250$ | $0.050$ | Tiempo de ataque ADSR. Transitorio suave de la columna de aire en la embocadura. |
| `4` | `decaimiento_s` | `float` | segundos | $0.005$ | $0.300$ | $0.080$ | Tiempo de caída ADSR hasta alcanzar el régimen estacionario. |
| `5` | `sostenido_rel` | `float` | amp. rel. | $0.10$ | $1.00$ | $0.80$ | Nivel de sostenido mientras la columna de aire se mantiene activa. |
| `6` | `relajacion_s` | `float` | segundos | $0.005$ | $0.300$ | $0.060$ | Tiempo de extinción ADSR tras cortar la insuflación. |
| `7` | `ruido_soplo` | `float` | amp. rel. | $0.00$ | $0.25$ | $0.04$ | Ruido de turbulencia aerodinámica (*breath noise*) generado en el bisel. |

* **Invertibilidad Garantizada:** El mapeo genotipo-fenotipo es biunívoco y estrictamente invertible. La suite de pruebas unitarias (`tests/test_representacion_rol1.py`) certifica que $|\text{decodificar}(\text{codificar}(x)) - x| < 10^{-12}$ sobre un muestreo masivo de $1,000$ individuos aleatorios en el hipercubo.
* **Mecanismo Defensivo:** Se implementó `restringir_limites()` mediante *clipping* rígido ($\text{clip}(g, 0.0, 1.0)$), blindando la evaluación acústica frente a operadores genéticos desbordantes como el cruce BLX-$\alpha$.

### 1.3 Formalización del Espacio de Búsqueda
Bajo una discretización física de paso absoluto $\Delta = 0.001$ en las unidades reales de cada gen (con extremos incluidos, $N_i = \lfloor(\max_i - \min_i)/\Delta\rfloor + 1$):
* **Niveles por gen:** $N = [901, 801, 501, 246, 296, 901, 296, 251]$.
* **Tamaño del espacio combinatorio:**
  $$S = \prod_{i=0}^{7} N_i = 1,762,430,802,969,797,099,136 \approx \mathbf{1.76 \times 10^{21}} \text{ combinaciones}$$
* **Entropía de información:** $\log_2(S) \approx \mathbf{70.58\text{ bits}}$ equivalentes.
* **Justificación de la Metaheurística:** Evaluando $1,000$ candidatos por segundo en una CPU moderna, una búsqueda exhaustiva por fuerza bruta requeriría $\approx \mathbf{5.58 \times 10^{10}\text{ años}}$ (más de 4 veces la edad estimada del universo). Por consiguiente, la exploración determinista es intratable y se justifica plenamente el uso de un Algoritmo Genético con búsqueda dirigida.

### 1.4 Análisis de Sensibilidad Unidimensional (1D)
Se implementó un arnés de sensibilidad (`src/sensibilidad.py`) barriendo 51 valores en $[0.0, 1.0]$ para cada gen (408 evaluaciones totales) manteniendo constantes los restantes en el fenotipo de flauta por defecto, contrastando la síntesis contra `flauta_referencia_01.wav`.

| Ranking | Gen | $\Delta \text{Fitness}_{\text{STFT}}$ | $\sigma_{\text{STFT}}$ | $\max |\nabla_{\text{STFT}}|$ | $\Delta \text{Fitness}_{\text{Croma}}$ | Clasificación de Impacto |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **1** | `ruido_soplo` | **0.2625** | 0.0870 | 0.5015 | 0.0004 | **Hipersensible** (Impacto crítico en STFT) |
| **2** | `sostenido_rel` | **0.0400** | 0.0125 | 0.0812 | 0.0433 | **Sensibilidad Moderada** |
| **3** | `relajacion_s` | **0.0185** | 0.0061 | 0.0421 | 0.0641 | Robusto en STFT / Sensible en Croma |
| **4** | `decaimiento_s`| **0.0152** | 0.0044 | 0.0380 | 0.0012 | Robusto / Insensible |
| **5** | `ataque_s` | **0.0137** | 0.0028 | 0.0450 | 0.0574 | Robusto en STFT / Sensible en Croma |
| **6** | `amp_arm3` | **0.0093** | 0.0023 | 0.0189 | 0.0155 | Robusto / Insensible |
| **7** | `amp_arm2` | **0.0066** | 0.0015 | 0.0135 | 0.0007 | Robusto / Insensible |
| **8** | `amp_arm1` | **0.0028** | 0.0008 | 0.0062 | 0.0021 | Robusto / Insensible |

* **Hallazgo Acústico 1 (Asimetría del Ruido):** `ruido_soplo` genera una variación de error de $8.04\text{ dB}$ en STFT debido a que el ruido blanco eleva el piso espectral en todas las frecuencias; sin embargo, en Croma es plano ($\Delta = 0.0004$) porque las componentes no periódicas se disipan al proyectar la energía en los 12 bins de notas musicales.
* **Hallazgo Acústico 2 (Complementariedad STFT + Croma):** Las colas temporales del ADSR (`relajacion_s` y `ataque_s`) son detectadas con mayor severidad por Croma ($\Delta \approx 0.06$) al contaminar notas adyacentes, validando empíricamente la necesidad de combinar ambas métricas para una evaluación holística.

---

### 1.5 Pregunta Teórica 1 (Rol 1 — Juan Mateo Soruco)

> **Pregunta Oficial:** *¿Cómo influye la representación del cromosoma en la eficiencia del AG? Da un ejemplo de codificación mala y una buena para este problema.*

#### A. Fundamento Teórico: Preservación de la Topología y Localidad
En los Algoritmos Genéticos, la **representación del cromosoma** define el mapa topológico que vincula el espacio genotípico ($\mathcal{G}$) con el espacio fenotípico ($\mathcal{F}$) y, en última instancia, con la superficie de aptitud ($\mathcal{S}: \mathcal{F} \to \mathbb{R}$). 

La eficiencia de un AG depende directamente del principio de **fuerte causalidad o localidad**: perturbaciones pequeñas en el genotipo inducidas por los operadores genéticos (cruce y mutación) deben traducirse en variaciones proporcionalmente pequeñas y suaves en el fenotipo acústico. Si la codificación fragmenta este mapa, los operadores genéticos se comportan como saltos estocásticos desconectados, transformando la optimización evolutiva en una búsqueda ciega y errática.

#### B. Ejemplo de Mala Codificación para este Problema
* **Diseño:** Codificación en **cadena binaria estándar** cuantizando cada parámetro a $B = 8\text{ bits}$ (cromosoma de $64\text{ bits}$ concatenados).
* **Falla Crítica 1 — Acantilados de Hamming (Hamming Cliffs):**
  Considérese el tiempo de ataque $A$ con rango $[5, 250]\text{ ms}$. Dos fenotipos físicamente casi indistinguibles como $127$ y $128$ se representan en binario como:
  $$127_{10} = \mathbf{01111111}_2 \quad \longleftrightarrow \quad 128_{10} = \mathbf{10000000}_2$$
  La distancia de Hamming entre ambos estados adyacentes es de **8 bits** (la máxima posible). Para que el AG transite entre dos puntos contiguos en el espacio fenotípico, la mutación puntual tendría que invertir simultáneamente los 8 bits en una sola generación, un evento de probabilidad ínfima ($p_m^8 \approx 0.05^8 \approx 3.9 \times 10^{-11}$). Esto genera barreras artificiales y cañones de discontinuidad en la superficie de fitness, provocando el estancamiento prematuro de la población.
* **Falla Crítica 2 — Redundancia y Regiones Inválidas:**
  Si los límites físicos no coinciden con potencias exactas de 2 ($2^B$), la codificación binaria produce genotipos que decodifican fuera de rango, requiriendo operadores de reparación costosos o funciones de penalización que distorsionan el gradiente evolutivo.

#### C. Ejemplo de Buena Codificación (La Implementada en el Proyecto)
* **Diseño:** **Representación en Vector Real Continuo (RCGA)** acotado en el hipercubo normalizado $[0.0, 1.0]^8$ con decodificación lineal afín y operadores continuos especializados (cruce BLX-$\alpha$ y mutación gaussiana o no uniforme).
* **Ventajas que Maximizan la Eficiencia:**
  1. **Preservación Estricta de la Localidad:** La distancia euclídea en el genotipo $\|\vec{g}_A - \vec{g}_B\|_2$ es directamente proporcional a la diferencia en parámetros físicos, garantizando una superficie de fitness suave y continua.
  2. **Exploración y Explotación Ajustables:** Permite al cruce BLX-$\alpha$ recombinar intervalos de confianza alrededor de los progenitores y a la mutación gaussiana realizar ajustes finos mediante perturbaciones de paso continuo ($\sigma$), acelerando la sintonía acústica de los armónicos.
  3. **Desacoplamiento y Ausencia de Epistasis Artificial:** Normalizar cada gen de manera independiente previene que parámetros con órdenes de magnitud dispares (e.g. tiempos en milisegundos vs. amplitudes relativas adimensionales) dominen asimétricamente el operador de cruce.

---

## 2. Capa 2: Síntesis Acústica y Función de Aptitud (Rol 2)
*[Sección reservada para la redacción final de Rol 2]*

### 2.1 Síntesis Aditiva y Envolventes Instrumentales
*(Resumen técnico de la implementación en `src/sintesis.py`)*

### 2.2 Métricas de Aptitud: STFT en dB vs. Croma Armónico
*(Resumen técnico de la implementación en `src/fitness.py`)*

### 2.3 Pregunta Teórica 2 (Rol 2)
> **Pregunta Oficial:** *¿Qué es una superficie de fitness? ¿Por qué es importante que sea suave para un AG? Ilustra con un gráfico del proyecto.*
*[Desarrollo a completar por Rol 2]*

---

## 3. Capa 3: Operadores Genéticos Continuos (Rol 3)

### 3.1 Operadores implementados

En `src/operadores.py`, **torneo k=3** sortea participantes sin reemplazo y elige mayor aptitud; empata por orden sorteado. **SUS** selecciona un lote con un inicio aleatorio y punteros equidistantes proporcionales al fitness no negativo; puede repetir individuos y usa pesos iguales si todos son cero. Ambos maximizan.

**BLX-alpha**, con alpha=0.5, muestrea cada hijo por gen en `[mínimo-alpha*d, máximo+alpha*d]`, donde d es la distancia parental. **Uniforme** intercambia genes con máscara 0.50 y herencia complementaria. La **gaussiana** suma ruido normal de media cero y sigma=0.08 a los genes seleccionados; la **no uniforme** usa `delta=y*(1-r**((1-t/T)**b))`, con b=2, distancia y al límite elegido y desplazamiento cero en t=T.

El ciclo aplica cruce 0.90 **por pareja**; cada mutación aplica 0.05 **por gen**, sin filtro adicional por individuo. Los hijos se recortan a `[0,1]` con `restringir_limites()` y se validan; las entradas inválidas se rechazan. Se devuelven copias independientes, sin alterar padres ni discretizar genes, compartiendo el Generator de la corrida.

### 3.4 Pregunta Teórica 3 (Rol 3)
> **Pregunta Oficial:** *Explica el balance exploración vs. explotación. ¿Qué operador empuja más hacia la exploración y cuál hacia la explotación? Respalda con datos.*

**Explorar** introduce o visita valores diferentes; **explotar** concentra la búsqueda en soluciones prometedoras. BLX-alpha ofrece más exploración de valores nuevos que uniforme porque puede salir del intervalo parental; uniforme recombina valores existentes. El torneo favorece explotación al elegir al mejor participante. La gaussiana introduce perturbaciones; la no uniforme reduce sus desplazamientos con el tiempo, favoreciendo ajustes finales. Son tendencias de implementación, no garantías universales.

La comparación principal guardada usa únicamente semillas **42 y 101**, N=50, dos élites y 50 reemplazos: **2550 evaluaciones reales por corrida**, con tolerancia cero para igualar presupuesto. STFT se maximiza y sigue **provisional**, sin ratificación colectiva. Este bloque no se mezcla con el factorial del Rol 5.

| Combinación | Mejor STFT medio ± DE muestral | Diversidad final media |
|---|---:|---:|
| A: torneo / BLX / gaussiana | 0.726136 ± 0.008259 | 0.009409 |
| B: torneo / uniforme / gaussiana | **0.730850 ± 0.001608** | 0.009313 |
| C: SUS / BLX / no uniforme | 0.724787 ± 0.006706 | 0.125190 |

La diversidad —media de las desviaciones por gen normalizado— partió de 0.285487 en promedio. A/B concentraron más la población; C mantuvo mayor dispersión sin mejorar el fitness medio. Esto vincula explotación con concentración observada, pero **más diversidad no implica mejor rendimiento**. C cambia selección y mutación simultáneamente: no aísla el efecto de SUS ni de la mutación. A–B examina el cambio de cruce; A ganó con semilla 42 y B con 101. **B se recomienda preliminarmente por mayor media**, con solo dos réplicas, sin afirmar significación estadística, superioridad general ni óptimo universal.

Fuentes: [tabla principal](../../resultados/operadores/dia3_2026-10-21_64617f8/resumen.csv), [diversidad por generación](../../resultados/operadores/dia3_2026-10-21_64617f8/diversidad.svg) e [informe del experimento](../rol3_dia3.md).

---

## 4. Capa 4: Dinámica Poblacional y Convergencia (Rol 4)

### 4.1 Arquitectura del Ciclo Reproductivo (`ejecutar_ag`)

El ciclo recibe una función de aptitud escalar y una `ConfiguracionAG` validada. Inicializa una población normalizada, evalúa sus individuos en orden y, en cada reemplazo, conserva dos élites y completa la siguiente población con selección, cruce y mutación. Un único `numpy.random.Generator` explícito gobierna la aleatoriedad de la corrida; la síntesis mantiene una semilla independiente. El resultado incluye ganador, fitness, historial, generaciones, evaluaciones reales y motivo de parada.

### 4.2 Preservación de Élite y Criterios de Parada por Estancamiento

La configuración operativa propuesta usa población 50, máximo 50 reemplazos, elitismo 2, torneo de tamaño 3, cruce uniforme con probabilidad 0.90 y mutación gaussiana por gen con probabilidad 0.05 y `sigma=0.08`. La parada compara el mejor fitness dentro de una ventana de paciencia 10 y exige una mejora mayor que `1e-4`. La métrica STFT primaria y croma complementaria siguen pendientes de ratificación colectiva.

La combinación B —torneo, uniforme y gaussiana— es una recomendación preliminar: con semillas 42 y 101 alcanzó fitness medio final 0.730850220, frente a 0.726136022 de A y 0.724787225 de C. Las corridas comparativas consumieron 2550 evaluaciones cada una y usaron tolerancia cero para igualar el presupuesto; no prueban la parada operativa ni superioridad general.

### 4.3 Pregunta Teórica 4 (Rol 4)
> **Pregunta Oficial:** *¿Qué es la convergencia prematura? ¿Cómo se detecta y cómo se evita? Da evidencia concreta.*

La convergencia prematura ocurre cuando la población pierde diversidad antes de explorar adecuadamente y se concentra alrededor de una solución subóptima. Se detecta combinando estancamiento del mejor fitness, estabilización de la media y dispersión del fitness, y una caída sostenida de diversidad; una sola señal no basta.

En las seis corridas principales, la diversidad inicial media fue 0.285487. A y B terminaron en 0.009409 y 0.009313, conservando aproximadamente 3.3 %; C terminó en 0.125190 y conservó aproximadamente 43.9 %. Esto demuestra mayor concentración en A/B, pero no confirma convergencia prematura: B logró el mayor fitness medio y la parada por tolerancia se desactivó para el experimento. El riesgo puede reducirse moderando elitismo o presión selectiva, adaptando la mutación y, si persiste el estancamiento, usando inmigrantes o reinicios parciales. Estas dos últimas estrategias son propuestas no implementadas.

---

## 5. Capa 5: Meta-evaluación y Validación Experimental (Rol 5)
*[Sección reservada para la redacción final de Rol 5]*

### 5.1 Plan Experimental Factorial (12 Configuraciones x 5 Réplicas)
*(Resumen del análisis estadístico y de varianza en `notebooks/00_integracion.ipynb`)*

### 5.2 Comparativa Estadística: AG vs. Búsqueda Aleatoria (Baseline)
*(Tablas comparativas, boxplots y pruebas pareadas)*

### 5.3 Encuesta Subjetiva de Calidad Acústica
*(Resumen de la evaluación auditiva ciega)*

### 5.4 Pregunta Teórica 5 (Rol 5)
> **Pregunta Oficial:** *¿Cómo demuestras que tu AG es mejor que una búsqueda aleatoria? ¿Qué métricas usarías y qué resultados obtuviste?*
*[Desarrollo a completar por Rol 5]*

---

## 6. Conclusiones Generales del Proyecto
*[Sección consolidada de cierre grupal]*

---

## Referencias Bibliográficas
1. Goldberg, D. E. (1989). *Genetic Algorithms in Search, Optimization, and Machine Learning*. Addison-Wesley.
2. Herrera, F., Lozano, M., & Verdegay, J. L. (1998). *Tackling real-coded genetic algorithms: Operators and tools for behavioural analysis*. Artificial Intelligence Review, 12(4), 265-319.
3. Klapuri, A., & Davy, M. (Eds.). (2007). *Signal processing methods for music transcription*. Springer Science & Business Media.
4. Mauch, M., & Dixon, S. (2014). *pYIN: A fundamental frequency estimator using probabilistic threshold distributions*. In IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP) (pp. 659-663).
5. Michalewicz, Z. (1996). *Genetic Algorithms + Data Structures = Evolution Programs*. Springer-Verlag.
