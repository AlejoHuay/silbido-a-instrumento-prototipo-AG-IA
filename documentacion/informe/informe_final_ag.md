# Del silbido al instrumento: prototipo de síntesis mediante un algoritmo genético continuo

**Examen práctico grupal — Inteligencia Artificial, Universidad Católica Boliviana “San Pablo”**
**Octubre de 2026**

> **Estado editorial:** versión compacta para revisión del equipo. El README del proyecto indica una entrega de 3–4 páginas, pero no se encontró la guía oficial ni un formato paginado institucional. No se afirma que esta versión cumpla esa extensión al exportarse.

| Rol | Integrante | Aporte documentado |
|---|---|---|
| 1 — Representación y extracción | Juan Mateo Soruco | Codificación, extracción melódica y análisis 1D de genes. |
| 2 — Síntesis y fitness | Marcelo David Navia Rocabado | Síntesis aditiva, métricas espectrales y sensibilidad. |
| 3 — Operadores genéticos | Alejandro Alvarez Huayhua | Selección, cruce y mutación; comparación exploratoria. |
| 4 — Dinámica poblacional | César Cádiz Rivero | Ciclo AG, élites, criterios de parada y convergencia. |
| 5 — Meta-evaluación | Tairin Andrea Muñoz Claros | Factorial, baseline pareado, análisis y reproducibilidad. |

Los nombres reflejan la tabla del proyecto. La revisión de firmas y ratificación colectiva permanece pendiente.

## Sistema y resultados técnicos

El prototipo convierte una melodía extraída de un silbido en una síntesis aditiva de flauta. Rol 1 entrega notas, duraciones y una representación de ocho genes normalizados en [0,1]^8: amplitudes de tres armónicos, ataque, decaimiento, sostenido, relajación y ruido de soplo. La transformación lineal a parámetros físicos facilita aplicar operadores continuos; el recorte mantiene los genes dentro de sus límites. Detalles: [diseño técnico](../diseno/dia1.md) y [contrato del cromosoma](../contratos/contrato_cromosoma.md).

Rol 2 implementa síntesis aditiva con envolvente ADSR y una semilla de síntesis reproducible. La función de fitness compara audios mono, finitos, alineados, a 22050 Hz y de igual longitud. STFT usa Hann, FFT de 2048, salto 256, piso −80 dB y amplitud de referencia 1; transforma el error absoluto medio en dB mediante 1/(1+E_dB/10), que se maximiza. Croma agrupa energía en 12 clases y usa similitud coseno media por cuadro, también maximizada. Ninguna mide directamente calidad perceptual. Véase [src/fitness.py](../../src/fitness.py).

### Pregunta teórica 1 — Rol 1: representación

Una representación adecuada mantiene una relación interpretable entre cambios del genotipo y cambios de los parámetros. Una cadena binaria puede producir “acantilados de Hamming”: dos valores físicos contiguos, como 127 y 128 en una cuantización de 8 bits, difieren en todos sus bits y una mutación puntual no los conecta fácilmente. El proyecto usa números reales normalizados y decodificación lineal, evitando esa discontinuidad artificial y permitiendo mutación continua. Esto preserva localidad en el mapeo de parámetros, pero no demuestra que toda la función de fitness sea suave; la síntesis, la envolvente y el piso espectral pueden cambiar pendientes.

### Pregunta teórica 2 — Rol 2: superficie de fitness

La superficie asigna aptitud a cada combinación de genes; aquí es una función de ocho dimensiones. Cortes unidimensionales, que cambian un gen mientras fijan los otros siete, ayudan a observar sensibilidad local, pero no muestran interacciones ni prueban suavidad global. La implementación de sensibilidad reutilizada por Rol 2 evalúa 51 puntos por cada uno de los ocho genes (408 evaluaciones). El gráfico [superficie STFT](../../resultados/audios/rol2_dia4_superficie_fitness.png) presenta cortes; sus escalas verticales difieren. El soplo tuvo rango STFT 0.262472 y croma 0.000379; la relajación tuvo rango croma 0.064137. Esto muestra respuestas distintas según gen y métrica, no calidad auditiva ni convergencia garantizada. La interpretación debe ser validada por Rol 2.

### Pregunta teórica 3 — Rol 3: exploración y explotación

Exploración visita regiones nuevas; explotación concentra la búsqueda en soluciones prometedoras. BLX-alpha (alpha=0.5) puede producir valores fuera del intervalo parental antes del recorte y favorece exploración respecto del cruce uniforme, que intercambia genes parentales. Torneo k=3 aumenta la presión de selección; la mutación gaussiana usa sigma=0.08 y la no uniforme reduce desplazamientos al acercarse al límite temporal. Son mecanismos, no garantías universales.

En seis corridas comparativas (N=50, 50 reemplazos, dos semillas y 2550 evaluaciones reales por corrida), las medias STFT fueron A=torneo/BLX/gaussiana 0.726136 (DE 0.008259), B=torneo/uniforme/gaussiana 0.730850 (DE 0.001608) y C=SUS/BLX/no uniforme 0.724787 (DE 0.006706). A ganó con semilla 42 y B con 101. C conservó más diversidad final (0.125190 frente a 0.009409 y 0.009313), pero no obtuvo mayor fitness. B es recomendación preliminar basada en dos réplicas, no resultado concluyente. Más detalles: [comparación de Rol 3](../rol3_dia3.md).

### Pregunta teórica 4 — Rol 4: convergencia prematura

Es la pérdida temprana de diversidad alrededor de una solución potencialmente subóptima. Se diagnostica combinando descenso sostenido de diversidad, estabilización de fitness y estancamiento; diversidad baja por sí sola no basta. En las seis corridas anteriores, A/B acabaron con diversidad mucho menor que C, pero eso no prueba convergencia prematura: B obtuvo la media más alta y aquella comparación desactivó la parada por estancamiento para igualar presupuestos. Reducir presión selectiva, ajustar mutación o introducir inmigrantes son medidas posibles; inmigración y reinicios no están implementados. Evidencia: [Día 4 de Rol 4](../rol4_dia4.md).

## Experimento del Rol 5

Se reutilizaron los CSV y checkpoints guardados del factorial, sin repetir corridas: población {20, 50, 100}, elitismo {1, 2}, mutación {0.02, 0.08}, cinco semillas (42, 101, 2024, 7, 999), 12 configuraciones y 60 corridas por métrica. Se fijó B (torneo, uniforme, gaussiana, sigma=0.08) como opción experimental provisional. Se mantuvieron los demás parámetros y la parada por estancamiento existentes. Chroma y STFT se procesaron por separado. STFT como métrica primaria y B siguen pendientes de ratificación colectiva.

### Pregunta teórica 5 — Rol 5: AG frente a búsqueda aleatoria

Cada corrida AG se emparejó con búsqueda aleatoria por configuración, semilla y métrica, usando el presupuesto real de evaluaciones de esa corrida:

| Métrica | Media AG (DE) | Media baseline (DE) | Diferencia pareada media (DE) | Mediana diferencia | AG mayor |
|---|---:|---:|---:|---:|---:|
| STFT | 0.729882 (0.003367) | 0.717397 (0.001472) | 0.012485 (0.003424) | 0.013607 | 60/60 |
| Chroma | 0.958681 (0.001454) | 0.954582 (0.000978) | 0.004099 (0.001224) | 0.004168 | 60/60 |

Las varianzas muestrales (ddof=1) sobre los 60 mejores fitness agrupados por método/métrica son: STFT, AG 1.13349×10⁻⁵ y baseline 2.16822×10⁻⁶; chroma, AG 2.11307×10⁻⁶ y baseline 9.56984×10⁻⁷. Agrupan factores y semillas; no estiman variabilidad dentro de una configuración.

El ANOVA factorial usó semilla como bloque y ajuste Holm conjunto para 14 contrastes. En chroma quedaron efectos ajustados de población (p=1.87×10⁻⁸) y mutación (p=0.00587); ningún término STFT conservó p ajustada <0.05. El ANOVA evalúa hiperparámetros, no AG contra baseline. No se comprobaron normalidad ni homogeneidad de residuos. No se hizo prueba inferencial AG–baseline ni se demuestra superioridad general: hay una melodía/referencia, cinco semillas por configuración y ninguna encuesta auditiva aplicada.

Los [boxplots STFT](../../resultados/rol5/dia4_metaevaluacion/boxplot_corridas_stft.svg) y [chroma](../../resultados/rol5/dia4_metaevaluacion/boxplot_corridas_croma.svg) muestran por separado 60 resultados agrupados entre configuraciones. El [tornado](../../resultados/rol5/dia4_metaevaluacion/tornado_hiperparametros.svg) representa efectos marginales de población, elitismo y mutación, no sensibilidad de genes del Rol 1. Protocolo: [Día 3 de Rol 5](../rol5_dia3.md).

## Audios y escucha

Los cuatro audios requeridos existen y se verificaron como WAV PCM16, mono, 22050 Hz y finitos:

| Papel | Ruta | Duración y procedencia |
|---|---|---|
| Silbido original | datos/audio/silbidos/silbido_01.wav | 2.694966 s. |
| Generación 0 | resultados/audios/rol5_dia3_stft_N20_E1_pm0.02_seed42/generacion_0_individuo_0.wav | 2.704989 s; individuo índice 0 reconstruido con inicializador determinista y semilla AG 42. |
| Referencia | resultados/audios/referencia_flauta.wav | 2.704989 s; SHA-256 coincide con la referencia fuente. |
| Mejor evolucionado | resultados/audios/rol5_dia3_stft_N20_E1_pm0.02_seed42/mejor_evolucionado_misma_corrida.wav | 2.704989 s; mejor cromosoma final del mismo checkpoint que generación 0. |

El checkpoint y los módulos fuente coinciden con las huellas del manifiesto; la diversidad de la población reconstruida coincide con el registro de generación 0. El checkpoint no guardó la población completa: el WAV es el primer individuo, no el mejor inicial. No se presenta el audio del Día 2 como generación 0. Procedencia y hashes: [manifiesto de audios](../../resultados/audios/rol5_dia3_stft_N20_E1_pm0.02_seed42/manifiesto_audios.json).

La [encuesta](../encuesta_auditiva_rol5.md) está preparada con referencia, candidatos inicial/final de una corrida, preguntas neutrales y plantilla para 5–10 personas. No tiene participantes ni respuestas; no hay conclusiones perceptuales. No se encontró un deck grupal editable: la lámina individual de Rol 5 está en [SVG](../presentacion/rol5_metaanalisis.svg); el equipo debe proporcionar el deck maestro. El notebook integrado y los WAV pueden apoyar una demo, aún pendiente de coordinación.

## Conclusión

El proyecto integra extracción, representación continua, síntesis, fitness, operadores, ciclo poblacional y análisis experimental. En estas condiciones el AG tuvo fitness mayor que el baseline en 60/60 pares por métrica, pero la comparación es descriptiva y limitada: no demuestra significación, superioridad general ni calidad perceptual. STFT como métrica primaria y B siguen provisionales. Pendientes del equipo: ratificación, encuesta real, deck grupal, demo y verificación de la paginación oficial.

## Referencias y documentación

- Goldberg, D. E. (1989). *Genetic Algorithms in Search, Optimization, and Machine Learning*. Addison-Wesley.
- [Implementación de fitness](../../src/fitness.py); [diseño](../diseno/dia1.md).
- [Operadores](../rol3_dia3.md); [convergencia](../rol4_dia4.md); [factorial y baseline](../rol5_dia3.md).
- [Auditoría de entregables](../auditoria_entregables_rol5_dia4.md); [verificaciones](../verificacion_notebooks.md).
