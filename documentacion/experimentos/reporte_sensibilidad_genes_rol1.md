# Reporte de Sensibilidad 1D de Genes — Rol 1 al Rol 2 (Día 3)

**Autor:** `@🕷🕸Noctivagus🦇🩸` (Juan Manuel Soruco — Rol 1: Representación y Extracción)  
**Destinatario:** `@~Marcelo Navia` (Rol 2: Síntesis y Fitness) / Equipo AG  
**Fecha:** 2026-10-20  
**Archivos asociados:**
- Módulo: `src/sensibilidad.py`
- Tests: `tests/test_sensibilidad_rol1.py`
- Datos crudos: `resultados/sensibilidad/sensibilidad_1d_genes.csv`
- Ranking: `resultados/sensibilidad/ranking_sensibilidad_genes.csv`
- Gráficos: `resultados/sensibilidad/figura_sensibilidad_1d_todos_los_genes.png` y `figura_tornado_sensibilidad.png`

---

## 1. Objetivo y Metodología

El cronograma del **Día 3 (Experimentación)** asigna al **Rol 1** la tarea individual de:
> *"Fitness vs. variación de cada gen"* y el hito de integración *"Reportar genes sensibles al Rol 2"*.

### Metodología Experimental
1. **Punto base de referencia:** Cromosoma canónico de flauta traversa (`amp_arm1=0.90`, `amp_arm2=0.25`, `amp_arm3=0.08`, `ataque_s=0.05s`, `decaimiento_s=0.08s`, `sostenido_rel=0.80`, `relajacion_s=0.06s`, `ruido_soplo=0.04`).
2. **Barrido unidimensional (1D):** Para cada uno de los 8 genes, se barrieron $51$ valores equiespaciados en el hipercubo normalizado $[0.0, 1.0]$, manteniendo fijos los otros 7 genes en el valor de referencia.
3. **Evaluación acústica:** Cada variante generó un audio sintetizado con las 16 notas y duraciones reales de `melodia_01.csv`, contrastado contra `flauta_referencia_01.wav` mediante las métricas de `src/fitness.py`:
   - $\text{Fitness}_{\text{STFT}} = \frac{1}{1 + \text{error\_db} / 10} \in (0, 1]$
   - $\text{Fitness}_{\text{Croma}} \in [0, 1]$ (Similitud coseno de pitch classes)
4. **Métricas de sensibilidad:**
   - Rango de variación: $\Delta \text{Fitness} = \max(f) - \min(f)$
   - Dispersión: Desviación estándar $\sigma_f$
   - Gradiente máximo normalizado: $\max |\partial f / \partial g|$

---

## 2. Resultados y Ranking de Sensibilidad

Total de evaluaciones procesadas: **408 individuos**.

| Rank | Gen | $\Delta \text{Fitness}_{\text{STFT}}$ | $\sigma_{\text{STFT}}$ | $\max |\nabla_{\text{STFT}}|$ | $\Delta \text{Error (dB)}$ | $\Delta \text{Fitness}_{\text{Croma}}$ | Categoría STFT |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `ruido_soplo` | **0.2625** | 0.0870 | 0.5015 | 8.04 dB | 0.0004 | **Hipersensible** |
| **2** | `sostenido_rel` | **0.0400** | 0.0125 | 0.0812 | 0.90 dB | 0.0433 | **Sensibilidad Moderada** |
| **3** | `relajacion_s` | **0.0185** | 0.0061 | 0.0421 | 0.40 dB | 0.0641 | Robusto / Insensible |
| **4** | `decaimiento_s`| **0.0152** | 0.0044 | 0.0380 | 0.33 dB | 0.0012 | Robusto / Insensible |
| **5** | `ataque_s` | **0.0137** | 0.0028 | 0.0450 | 0.30 dB | 0.0574 | Robusto / Insensible |
| **6** | `amp_arm3` | **0.0093** | 0.0023 | 0.0189 | 0.20 dB | 0.0155 | Robusto / Insensible |
| **7** | `amp_arm2` | **0.0066** | 0.0015 | 0.0135 | 0.14 dB | 0.0007 | Robusto / Insensible |
| **8** | `amp_arm1` | **0.0028** | 0.0008 | 0.0062 | 0.06 dB | 0.0021 | Robusto / Insensible |

---

## 3. Hallazgos Acústicos Clave

1. **La asimetría del Ruido de Soplo (`ruido_soplo`):**
   - Es el parámetro más influyente en la métrica STFT por un orden de magnitud ($\Delta = 0.2625$, variación de error de $8.04\text{ dB}$).
   - Sin embargo, en **Croma es prácticamente plano ($\Delta = 0.0004$)**.
   - *Explicación acústica:* El ruido blanco inyecta energía no armónica en todas las bandas espectrales de la STFT elevando el piso de ruido global, pero las matrices de croma filtran las componentes no periódicas al acumular energía solo en los bins correspondientes a las 12 clases de altura (pitch classes).

2. **Sensibilidad de la Envolvente Temporal (ADSR):**
   - `sostenido_rel`, `relajacion_s` y `ataque_s` tienen un impacto balanceado tanto en STFT como en Croma.
   - En Croma, `relajacion_s` ($\Delta = 0.0641$) y `ataque_s` ($\Delta = 0.0574$) producen las mayores caídas cuando se prolongan excesivamente, debido a que el solapamiento o retraso temporal ensucia la energía de las notas contiguas en la melodía.

3. **Robustez de las Amplitudes Armónicas:**
   - La respuesta ante `amp_arm1`, `amp_arm2` y `amp_arm3` es suave y monótona, sin mínimos locales abruptos en este corte 1D. La normalización por ganancia máxima (`0.9 / MAXIMO_AMPLITUD`) amortigua fluctuaciones drásticas.

---

## 4. Recomendaciones Técnicas para el Rol 2

1. **Riesgo de convergencia prematura en `ruido_soplo`:**
   - Debido al gradiente tan pronunciado de `ruido_soplo` en STFT ($\max |\nabla| = 0.50$), el AG podría tender a colapsar rápidamente este gen hacia valores cercanos a cero antes de haber optimizado los armónicos tímbricos.
   - *Sugerencia:* Si se desea un timbre realista de flauta con aire, vigilar si el individuo evolucionado termina apagando el soplo.

2. **Justificación empírica de la combinación STFT + Croma:**
   - Los datos demuestran que STFT y Croma son ortogonales y complementarias:
     - STFT es ciega a la tonalidad pura pero hipersensible al ruido y timbre.
     - Croma es ciega al ruido pero detecta con precisión el seguimiento de las notas y las colas temporales del ADSR.
   - Esto respalda la decisión del Día 2 de disponer de ambas métricas para el análisis de robustez del AG.

3. **Insumo para Rol 5 (Meta-evaluación):**
   - Los archivos `sensibilidad_1d_genes.csv` y `ranking_sensibilidad_genes.csv` quedan disponibles para construir el gráfico de tornado consolidado del informe final.
