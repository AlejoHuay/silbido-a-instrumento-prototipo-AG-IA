# Diapositiva 2: Representación del Cromosoma y Extracción Acústica
### Presentación Final — Rol 1: El Codificador
**Expositor:** Juan Mateo Soruco (`@🕷🕸Noctivagus🦇🩸`)  
**Tiempo estimado:** 2 minutos (de los 10 min totales del equipo)

---

## 1. Diseño Visual de la Diapositiva

```
+---------------------------------------------------------------------------------------------------+
|  CAPA 1: EXTRACCIÓN ACÚSTICA Y REPRESENTACIÓN CONTINUA DEL CROMOSOMA                               |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  [PIPELINE ACÚSTICO]                     [CROMOSOMA CONTINUO: RCGA]                               |
|  Silbido Real (22 kHz, 16-bit)           Espacio Normalizado: g in [0.0, 1.0]^8                   |
|  SNR: 40.8 dB | 0% clipping               Transformación afín biunívoca | Error < 10^-12         |
|  pYIN + Mediana (5 cuadros)                                                                       |
|  16 eventos (11 notas E6-C7, 5 pausas)    [TABLA DE 8 GENES]                                      |
|                                           - Armónicos: amp_arm1 (f0), amp_arm2 (2f0), amp_arm3    |
|  [ESPACIO DE BÚSQUEDA]                    - Envolvente ADSR: ataque, decaimiento, sost., relaj.   |
|  Paso físico Delta = 0.001                - Aire / Turbulencia: ruido_soplo                       |
|  1.76 x 10^21 combinaciones                                                                       |
|  70.58 bits de información                [SENSIBILIDAD 1D (ROL 1 -> ROL 2)]                      |
|  > 55 mil millones de años por fuerza b.  - ruido_soplo: Hipersensible en STFT (Delta=0.2625)     |
|                                           - ADSR: Balanceado en STFT y Croma                      |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Contenido Clave para Mostrar (Bullets)
* **De la Voz al Algoritmo:**
  - Conversión del silbido precario a audio maestro ($22,050\text{ Hz}$, mono, 16-bit PCM).
  - Estimación robusta de $f_0$ mediante pYIN y filtro de mediana temporal.
  - Melodía cuantizada a notas MIDI occidentales: 16 eventos reales en `melodia_01.csv`.
* **Codificación Real vs. Acantilados de Hamming:**
  - Cromosoma continuo en $[0.0, 1.0]^8$ con decodificación afín a unidades físicas.
  - Evita acantilados de Hamming binarios ($127_{10} \leftrightarrow 128_{10}$ distan a 8 bits).
  - Preserva la localidad del espacio acústico: perturbaciones genotípicas suaves producen variaciones fenotípicas suaves.
* **Espacio Combinatorio:**
  - $1.76 \times 10^{21}$ estados posibles ($70.58\text{ bits}$).
  - Justifica matemáticamente la necesidad de la metaheurística frente a la fuerza bruta ($> 5.58 \times 10^{10}\text{ años}$).
* **Análisis de Sensibilidad 1D:**
  - Barrido de 408 evaluaciones: el ruido de soplo es hipersensible en STFT ($\Delta = 0.2625$) pero plano en Croma, demostrando la complementariedad de las funciones de evaluación.

---

## 3. Guion de Exposición Verbal (Oral Script — Juan Mateo Soruco)

> *"Buenas tardes a todos. Mi nombre es **Juan Mateo Soruco**, responsable del **Rol 1: El Codificador**.*
>
> *Nuestra misión en esta primera capa fue construir el puente entre la señal bioacústica del silbido y la estructura genética que optimiza el algoritmo.*
>
> *Primero, procesamos la grabación del silbido original convirtiéndola al estándar de audio del proyecto: $22050\text{ Hz}$ mono en 16 bits. Implementamos el estimador probabilístico pYIN con un filtro de mediana para extraer con precisión la melodía, detectando 16 eventos —11 notas de octava alta entre Mi6 y Do7 y 5 silencios reales— con una relación señal-ruido de $40.8\text{ dB}$.*
>
> *En segundo lugar, diseñamos la representación del cromosoma. En lugar de usar una cadena binaria clásica —que en nuestro dominio causaría acantilados de Hamming donde dos sonidos casi idénticos distan a 8 mutaciones de bits—, implementamos un **Algoritmo Genético de Codificación Real en el hipercubo continuo $[0, 1]^8$**. Este vector modela 3 armónicos, la envolvente temporal ADSR y el ruido de soplo de la flauta, garantizando una biyección invertible probada con error numérico inferior a $10^{-12}$.*
>
> *Al discretizar este espacio con una resolución física de $0.001$, demostramos que existen **$1.76 \times 10^{21}$ combinaciones**, lo que tomaría más de **55 mil millones de años** por fuerza bruta, justificando plenamente el uso del Algoritmo Genético.*
>
> *Finalmente, ejecutamos el análisis de sensibilidad 1D con 408 evaluaciones, reportando a Rol 2 que el ruido de soplo es el gen con mayor impacto en el error espectral STFT ($\Delta = 0.26$), mientras que el croma es sensible a las colas temporales del ADSR, validando la complementariedad de ambas métricas.*
>
> *Le cedo la palabra a mi compañero del Rol 2 para explicar la función de fitness."*
