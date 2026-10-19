# Día 1 — Diseño del Algoritmo Genético

**Proyecto:** Del Silbido a la Flauta — Síntesis Instrumental con Algoritmos Genéticos  
**Curso:** Inteligencia Artificial | **Entregable:** Diseño de Arquitectura (1 página)  
**Estado:** Definido y acordado por los 4 integrantes (Roles 1 al 5).

---

## 1. Objetivo y Melodía
Convertir un silbido humano en la misma melodía interpretada por una flauta sintetizada, optimizando sus parámetros tímbricos mediante un Algoritmo Genético continuo desde cero (sin Deep Learning ni frameworks externos de AG).
- **Melodía objetivo:** Sol5–La5–Si5–La5–Sol5 (Notas MIDI: 79–81–83–81–79).
- **Formato de datos:** Audio WAV mono, 22050 Hz, PCM 16-bit. Melodía en CSV: `nota_midi,duracion_s` (silencios con `-1`).
- **Archivos base:** `datos/audio/silbidos/silbido_01.wav`, `datos/audio/referencias/flauta_referencia_01.wav`, `datos/procesados/melodia_01.csv`.

---

## 2. Representación del Cromosoma (Rol 1)
Cromosoma continuo en $\mathbb{R}^8$ normalizado en el hipercubo $[0.0, 1.0]^8$, desacoplado mediante esquema modular extensible:
$$\vec{g} = [a_1, a_2, a_3, \text{Ataque}, \text{Decaimiento}, \text{Sostenido}, \text{Relajación}, \text{Soplo}]$$
- **Armónicos:** $a_1 \in [0.10, 1.00]$ (fundamental dominante), $a_2 \in [0.00, 0.80]$ (brillo), $a_3 \in [0.00, 0.50]$ (color tímbrico).
- **Envolvente ADSR:** Ataque $\in [0.005, 0.250]\text{ s}$, Decaimiento $\in [0.005, 0.300]\text{ s}$, Sostenido $\in [0.10, 1.00]$, Relajación $\in [0.005, 0.300]\text{ s}$.
- **Turbulencia:** Ruido de aliento $b_n \in [0.00, 0.25]$ (resonancia del bisel de la flauta).
- **Espacio de búsqueda:** $S \approx 1.76 \times 10^{21}$ estados a resolución $10^{-3}$ ($\approx 70.6$ bits). Inviable por fuerza bruta (>50 mil millones de años).

---

## 3. Síntesis y Función de Fitness (Rol 2)
- **Síntesis acústica:** $s(t) = \text{ADSR}(t) \cdot \sum_{k=1}^3 a_k \sin(2\pi k f_0 t) + b_n \cdot \eta(t)$, generada a 22050 Hz mono.
- **Fitness Principal ($F_{\text{STFT}}$):** Comparación de espectrogramas STFT en escala dB (ventana Hann 1024, hop 256). Se descarta el MSE temporal porque penaliza drásticamente los desfases de fase pese a ser inaudibles al oído humano (*Ley de Ohm acústica*).
- **Segunda Métrica ($F_{\text{Croma}}$):** Distancia euclídea media sobre vectores cromáticos (12 pitch classes) para asegurar afinación y pureza armónica.
- **Formulación del Fitness (Maximización acotada en $(0, 1]$):**
  $$\text{Fitness}(\vec{g}) = \frac{1}{1 + \mathcal{D}_{\text{STFT}}(\text{cand}, \text{ref}) + 0.5 \cdot \mathcal{D}_{\text{Croma}}(\text{cand}, \text{ref})}$$

---

## 4. Operadores Genéticos (Rol 3)
- **Selección:** Torneo determinista con $k=3$ (alta presión selectiva) y SUS (Stochastic Universal Sampling, preservación de diversidad).
- **Cruce:** Blend-$\alpha$ ($\text{BLX-}0.5$, exploración en espacio continuo) y Cruce Uniforme continuo ($p=0.5$).
- **Mutación:** Gaussiana con clipping ($\sigma = 0.08$) y No Uniforme adaptativa decreciente con la generación ($t/G_{\max}$).

---

## 5. Dinámica Poblacional y Meta-Evaluación (Roles 4 y 5)
- **Población y Ciclo:** $N \in \{20, 50, 100\}$, generaciones $G=50$, elitismo de 2 individuos ($k_e=2$). Parada por estancamiento ($\Delta F < 10^{-4}$ durante 10 generaciones) o generación máxima.
- **Plan Experimental:** Matriz de 12 configuraciones factoriales evaluadas en 5 semillas (`42, 101, 2024, 7, 999`).
- **Línea Base (Baseline):** Comparativa estadística contra Búsqueda Aleatoria pura (Random Search) con idéntico número de evaluaciones ($N \times G$).
- **Métricas:** Media, desviación estándar, varianza, curvas de convergencia y análisis de sensibilidad (diagrama tornado).

---

## 6. Firmas de Conformidad del Equipo

| Rol | Responsabilidad | Integrante | Firma |
|:---|:---|:---|:---|
| **Rol 1** | Codificador (Representación y Extracción) | ___________________________ | ___________________________ |
| **Rol 2** | Traductor (Síntesis y Fitness) | ___________________________ | ___________________________ |
| **Rol 3 y 5** | Motor Evolutivo, Meta-evaluación e Integración | ___________________________ | ___________________________ |
| **Rol 4** | Estratega (Dinámica Poblacional) | ___________________________ | ___________________________ |

**Fecha de Aprobación:** 19 de octubre de 2026
