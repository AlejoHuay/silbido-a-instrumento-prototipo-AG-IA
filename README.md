# Del silbido al instrumento

Prototipo académico de síntesis instrumental mediante un
Algoritmo Genético implementado desde cero.

## Equipo

| Integrante | Responsabilidad |
|---|---|
| JMjuanma | Rol 1: representación y extracción |
| Por completar | Rol 2: síntesis y fitness |
| Por completar | Rol 3: operadores genéticos |
| Por completar | Rol 4: dinámica poblacional |
| Por completar | Rol 5: integración reproducible y análisis experimental |

## Objetivo

Extraer una melodía de un silbido WAV y reproducirla con
un instrumento cuyos parámetros evolucionan mediante un AG.

## Entorno

- Python 3.10+.
- Google Colab o Jupyter.
- Audio: WAV mono, 22050 Hz, PCM de 16 bits.
- Prohibidos frameworks de AG y modelos preentrenados.
- No utilizar deep learning.

## Dependencias

Las dependencias externas están en requirements.txt.
No se necesitan todas en cada módulo.

Instalación:

    python -m pip install -r requirements.txt

Para ejecutar y verificar los notebooks en un entorno local limpio:

    py -3.10 -m venv .venv
    .\.venv\Scripts\python -m pip install -r requirements-notebooks.txt
    .\.venv\Scripts\python scripts\verificar_notebooks.py

`requirements-notebooks.txt` incluye las dependencias del proyecto (también
`pandas`) y añade el kernel y el ejecutor automatizado de Jupyter. El verificador
usa un kernel nuevo por notebook y una copia temporal del repositorio, por lo
que las celdas que generan WAV, CSV o figuras no alteran el árbol de trabajo.
La evidencia de la última corrida está en
[`documentacion/verificacion_notebooks.md`](documentacion/verificacion_notebooks.md).

## Organización

- notebooks/: trabajo por rol y notebook de integración.
- src/: funciones compartidas; evitar duplicarlas en notebooks.
- datos/audio/silbidos/: entradas originales.
- datos/audio/referencias/: referencias instrumentales.
- datos/procesados/: notas, duraciones y datos derivados.
- resultados/: mediciones, tablas, figuras y audios.
- documentacion/: contratos, diseño, informe y presentación.

## Estado de Avance por Rol

### Rol 1 — Representación y Extracción (JMjuanma)
- **Audio de entrada:** Grabación real calibrada y convertida a WAV mono 22050 Hz 16-bit (`datos/audio/silbidos/silbido_01.wav`), con SNR de 40.8 dB y 0% clipping.
- **Extracción de notas:** Detección de F0 tramo a tramo (pYIN/autocorrelación), filtrado de mediana y segmentación temporal registrada en `datos/procesados/melodia_01.csv`.
- **Representación cromosómica:** Vector continuo $\mathbb{R}^8$ acotado en $[0.0, 1.0]^8$ mediante esquema desacoplado `GENES_SCHEMA` (3 armónicos, ADSR y ruido de soplo).
- **Validación:** Inversión formal `decodificar(codificar(x)) == x` verificada con error de precisión máquina ($< 10^{-15}$).
- **Espacio de búsqueda:** Cuantificado en $1.76 \times 10^{21}$ estados posibles ($70.6$ bits), justificando la intratabilidad de fuerza bruta.
- **Entregables:** `src/representacion.py`, `src/extraccion.py`, `notebooks/01_rol1_representacion.ipynb`, `documentacion/contratos/contrato_cromosoma.md` y `documentacion/diseno/dia1.md`.

### Rol 4 — Dinámica poblacional (Días 1, 2 y 4)
- **Configuración reproducible:** parámetros validados en `ConfiguracionAG`, con una semilla y un generador compartidos por corrida.
- **Dinámica implementada:** ciclo generacional completo, inicialización, evaluación ordenada, elitismo por maximización, estadísticas de convergencia y detección de estancamiento.
- **Plan experimental:** matriz factorial de 12 configuraciones preparada para el Día 3, con cinco semillas como réplicas.
- **Integración Día 2:** `ejecutar_ag()` conecta torneo o SUS, BLX-alpha o cruce uniforme y mutación gaussiana o no uniforme; la primera corrida end-to-end usa síntesis y fitness reales con una población pequeña.
- **Cierre Día 4:** configuración operativa documentada, respuesta teórica sobre convergencia prematura y diapositiva basada en las seis corridas principales del Rol 3. Tras integrar el factorial del Rol 5, la propuesta STFT quedó en N=100, elitismo=2 y mutación=0.08, manteniendo B como combinación provisional.
- **Curvas del factorial:** `scripts/graficar_convergencia_factorial.py` reconstruye, sin ejecutar el AG ni el fitness, las 12 configuraciones y cinco semillas de STFT y croma desde los checkpoints guardados.
- **Entregables:** `src/configuracion.py`, `src/algoritmo_genetico.py`, `notebooks/04_rol4_dinamica.ipynb`, `scripts/graficar_convergencia_factorial.py`, `resultados/rol4/convergencia_factorial/`, `documentacion/rol4_dia2.md`, `documentacion/rol4_dia4.md`, `documentacion/contratos/interfaz_dinamica_rol4.md` y `documentacion/presentacion/rol4_convergencia.pptx`.

### Rol 5 — Análisis experimental (Día 2 cerrado; Día 3 ejecutado; Día 4 en revisión local)
- **Integración end-to-end:** `notebooks/00_integracion.ipynb` ejecuta el AG con la melodía y referencia reales, verifica repetibilidad, límites, finitud, población y presupuesto de evaluaciones. Genera `resultados/audios/rol5_dia2_mejor.wav` cuando falta o comprueba que el existente coincide, sin sobrescribirlo.
- **Evidencia de demostración:** semilla 2026, población 10, cinco generaciones, torneo, cruce BLX y mutación gaussiana; 60 evaluaciones reales y fitness STFT 0.7152406. Esta corrida valida la integración y no es parte del análisis estadístico del Día 3.
- **Día 3:** factorial de 12 configuraciones y cinco semillas ejecutado para STFT y chroma, con 60 corridas AG y 60 baselines pareados por métrica. Los resultados y checkpoints están en `resultados/rol5/dia3_factorial/`; el protocolo y los resultados descriptivos están en `documentacion/rol5_dia3.md`.
- **Decisiones provisionales:** STFT se usó como métrica inicial y B (torneo + cruce uniforme + mutación gaussiana, sigma 0.08) como operadores del factorial. Ambas decisiones siguen pendientes de ratificación del equipo; STFT y chroma tienen resultados separados.
- **Limitaciones:** comparación AG–baseline descriptiva para una melodía/referencia y cinco semillas por configuración, sin afirmar superioridad general. El ANOVA factorial exploratorio evalúa hiperparámetros, no la diferencia AG–baseline. No hay evaluación auditiva ciega. La suite completa requiere pandas para importar la prueba de sensibilidad de Rol 1.
- **Día 4:** `notebooks/05_rol5_metaevaluacion.ipynb` y `scripts/analizar_rol5_dia4.py` analizan los CSV guardados sin repetir corridas. El informe final contiene la comparación, ANOVA factorial exploratorio con ajuste Holm y las limitaciones; la encuesta auditiva sigue pendiente. La lámina Meta-análisis está en SVG y su fuente/resumen en `documentacion/presentacion/rol5_metaanalisis.md`.
- **Entregables:** `notebooks/00_integracion.ipynb`, `notebooks/05_rol5_metaevaluacion.ipynb`, `scripts/ejecutar_rol5_factorial.py`, `scripts/analizar_rol5_dia4.py`, `documentacion/analisis_rol5.md`, `documentacion/rol5_dia3.md` y `documentacion/informe/informe_final_ag.md`.

## Acuerdos y Diseño

Documento de entrega del Día 1: [diseño conjunto](documentacion/diseno/diseno_completo_ag_dia1.md).
Estado: borrador revisado; decisiones, paginación y firmas pendientes.
`documentacion/diseno/dia1.md` es el anexo técnico; los contratos detallan
las interfaces. Evidencia de revisión: [revisión de cierre](documentacion/revision_cierre_dia1.md).

## Reproducibilidad

- Usar rutas relativas a la raíz del repositorio.
- Registrar semillas y configuraciones.
- Identificar la versión del código usada en cada experimento.
- Conservar entradas y resultados necesarios para reproducirlo.
- Verificar el notebook integrado desde un entorno limpio.
- Registrar las versiones de dependencias realmente verificadas.
- No publicar resultados de ejemplo como mediciones reales.

## Trabajo en equipo

- Una rama de trabajo por rol o tarea.
- Compartir cambios mediante commits y revisión.
- Coordinar modificaciones de interfaces antes de integrarlas.
- No sobrescribir el trabajo de otros integrantes.
- Coordinar la edición de 00_integracion.ipynb con el Rol 5 y los responsables de las interfaces afectadas.

## Entregables

- Día 1: diseño del AG de una página, firmado por todos.
- Día 2: notebook que ejecute el proceso completo.
- Día 3: tablas, gráficos y conclusiones preliminares.
- Día 4: notebook, audios, informe y presentación.

Entrega final:
- Notebook reproducible.
- WAV: silbido, generación 0, referencia y mejor evolucionado.
- Informe de 3–4 páginas con cinco respuestas teóricas.
- Presentación de 10 minutos con demo.
