# Auditoría de cumplimiento — Rol 4

**Referencia base inspeccionada:** `origin/main`, commit `b122610`.

La contribución del Rol 4 ya aparece integrada en `main` mediante los commits
`e198f17` y `6e81ef1`. Esta auditoría distingue entregables existentes,
evidencia parcial y pendientes. No presenta las verificaciones documentales
como nuevas corridas experimentales.

## Cumplimiento por día

| Día | Requisito del Rol 4 | Estado | Archivos y evidencia |
|---|---|---|---|
| 1 | Pseudocódigo del ciclo completo | Existe | `documentacion/contratos/interfaz_dinamica_rol4.md`: inicialización, evaluación, reproducción, elitismo, registro, parada y retorno. |
| 1 | Acuerdo de operadores con Rol 3 | Existe | `documentacion/contratos/interfaz_dinamica_rol4.md` y `documentacion/contratos/interfaz_operadores_rol3.md`: firmas, probabilidades y conexión con operadores. |
| 1 | Configuración de población, elitismo y parada | Existe | `src/configuracion.py`: `ConfiguracionAG` valida población, elitismo, torneo, cruce, mutación, paciencia y tolerancia. |
| 2 | Implementación del ciclo completo | Existe | `src/algoritmo_genetico.py`: `ejecutar_ag()` implementa evaluación, reproducción, reemplazo, elitismo y parada. |
| 2 | Conexión con fitness y operadores | Existe | `src/algoritmo_genetico.py` y `notebooks/04_rol4_dinamica.ipynb`: fitness real, torneo o SUS, BLX o uniforme y mutaciones gaussiana o no uniforme. |
| 2 | Máximo, media y desviación del fitness | Existe | `calcular_estadisticas()` devuelve `fitness_maximo`, `fitness_medio` y `desviacion_fitness`. |
| 2 | Ejemplo con población pequeña | Existe | `notebooks/04_rol4_dinamica.ipynb`: población 5, elitismo 1 y tres reemplazos. |
| 2 | Primera corrida end-to-end documentada | Existe | `documentacion/rol4_dia2.md`: generaciones 0–3, 20 evaluaciones y fitness final 0.6493946951971431. |
| 3 | Diseño de 12 configuraciones | Existe | `src/configuracion.py`: población `{20,50,100}` × elitismo `{1,2}` × mutación `{0.02,0.08}`. |
| 3 | Ejecución del factorial | Existe | `resultados/rol5/dia3_factorial/ejecucion_20261021T184758Z_c5dc431/`: cinco semillas por configuración para STFT y croma, con baselines pareados. |
| 3 | Tabla experimental | Existe | `stft/resumen_por_configuracion.csv` y `croma/resumen_por_configuracion.csv`: parámetros, cinco réplicas, media y desviación. |
| 3 | Curvas de convergencia A/B/C | Existe | `resultados/operadores/dia3_2026-10-21_64617f8/fitness.svg` y `diversidad.svg`. |
| 3 | Curvas guardadas para las 12 configuraciones | Existe | `resultados/rol4/convergencia_factorial/`: láminas STFT y croma, cada una con 12 paneles y cinco semillas; se generan desde checkpoints mediante `scripts/graficar_convergencia_factorial.py` sin repetir experimentos. |
| 3 | Efecto de hiperparámetros | Parcial | El meta-análisis identifica efectos de población y mutación en croma. Ningún término STFT conservó significación después de Holm. Falta una respuesta del Rol 4 formulada expresamente como “el hiperparámetro que más importa”. |
| 3 | Convergencia prematura | Existe | `documentacion/rol4_dia4.md`, `documentacion/informe/informe_final_ag.md` y el notebook definen, detectan y proponen medidas preventivas. |
| 3 | Deriva genética | Parcial | Se analiza pérdida de diversidad y concentración poblacional, pero no existe una sección específica denominada “deriva genética”. |
| 3 | Entrega de resultados al Rol 5 | Parcial | El Rol 5 reutiliza configuración, ciclo y operadores, pero no existe un archivo denominado expresamente “entrega Rol 4 al Rol 5”. |
| 4 | Configuración final | Existe | `documentacion/rol4_dia4.md`: población 100, elitismo 2, combinación B, mutación 0.08, paciencia 10 y tolerancia 1e-4. |
| 4 | Respuesta teórica con evidencia | Existe | `documentacion/rol4_dia4.md` y la sección 4.3 del informe: definición, detección, prevención y diversidad observada. |
| 4 | Diapositiva “Convergencia” | Existe | `documentacion/presentacion/rol4_convergencia.pptx`: comparación A/B/C, fitness, diversidad y limitaciones. |
| 4 | Evidencia reproducible | Existe | `notebooks/04_rol4_dinamica.ipynb` lee resultados A/B/C y resúmenes factoriales sin ejecutar nuevas corridas. |
| Entorno | Dependencia local de pandas | Resuelta | `requirements-notebooks.txt` y `documentacion/verificacion_notebooks.md`: pandas 2.3.3 verificado. |
| Entorno | Kernels Jupyter limpios | Existe | `scripts/verificar_notebooks.py`: 5/5 notebooks ejecutados en kernels nuevos y copias temporales. |
| Pruebas | Suite unitaria | Existe | 55/55 pruebas pasadas. |

## Configuración final propuesta

- Población: 100.
- Elitismo: 2.
- Selección por torneo: k=3.
- Cruce uniforme con probabilidad 0.90 por pareja.
- Máscara uniforme: 0.50.
- Mutación gaussiana con probabilidad 0.08 por gen.
- Sigma: 0.08.
- Máximo: 50 generaciones o reemplazos.
- Paciencia de estancamiento: 10.
- Tolerancia de mejora: 1e-4.
- Una semilla explícita y un generador aleatorio compartido por corrida.

La combinación B, torneo + cruce uniforme + mutación gaussiana, continúa
como recomendación provisional.

## Resultados principales

### Comparación de operadores

| Combinación | Fitness STFT medio | Diversidad final media |
|---|---:|---:|
| A: torneo, BLX y gaussiana | 0.726136 | 0.009409 |
| **B: torneo, uniforme y gaussiana** | **0.730850** | 0.009313 |
| C: SUS, BLX y no uniforme | 0.724787 | **0.125190** |

B obtuvo el mayor fitness medio. A ganó con la semilla 42 y B con 101.
La comparación utiliza dos réplicas y no demuestra superioridad general. C
cambia selección y mutación simultáneamente, por lo que no aísla el efecto de
un solo operador.

### Factorial

La mejor media STFT fue 0.731952986 con población 100, elitismo 2 y mutación
0.08. La mejor media croma fue 0.959702027 con población 100, elitismo 1 y
mutación 0.08. La diferencia de elitismo muestra que la propuesta depende de
la métrica utilizada.

## Respuesta teórica

La convergencia prematura ocurre cuando la población pierde diversidad antes
de explorar adecuadamente y se concentra alrededor de una solución subóptima.
Debe detectarse combinando estancamiento del mejor fitness, estabilización de
la distribución del fitness y reducción sostenida de diversidad.

En A/B/C, la diversidad inicial media fue 0.285487. A terminó en 0.009409, B
en 0.009313 y C en 0.125190. A y B conservaron cerca de 3.3% de la diversidad
inicial y C cerca de 43.9%. Esto demuestra mayor concentración en A/B, pero no
confirma por sí solo convergencia prematura.

Para reducir el riesgo se propone ajustar presión selectiva, elitismo o
mutación. Inmigración y reinicios parciales permanecen como propuestas no
implementadas.

## Archivos principales

- `src/algoritmo_genetico.py`
- `src/configuracion.py`
- `notebooks/04_rol4_dinamica.ipynb`
- `documentacion/contratos/interfaz_dinamica_rol4.md`
- `documentacion/rol4_dia2.md`
- `documentacion/rol4_dia4.md`
- `documentacion/informe/informe_final_ag.md`
- `documentacion/presentacion/rol4_convergencia.pptx`
- `scripts/graficar_convergencia_factorial.py`
- `resultados/rol4/convergencia_factorial/`
- `scripts/verificar_notebooks.py`
- `requirements-notebooks.txt`
- `documentacion/verificacion_notebooks.md`

## Estado de la presentación grupal

Se encontraron contenidos de presentación para los cinco roles:

- Rol 1: `documentacion/presentacion/rol1_representacion.md`.
- Rol 2: `documentacion/presentacion/rol2_evaluacion.md`.
- Rol 3: `documentacion/presentacion/contenido-operadores-rol-3.md`.
- Rol 4: `documentacion/presentacion/rol4_convergencia.pptx`.
- Rol 5: `documentacion/presentacion/rol5_metaanalisis.md` y `rol5_metaanalisis.svg`.

No se localizó una presentación grupal única que reúna las cinco
contribuciones. La unión y maquetación final permanecen pendientes.

## Pendientes

- Formular explícitamente cuál hiperparámetro importa más para cada métrica.
- Agregar una sección específica sobre deriva genética.
- Crear una entrega identificada como “Rol 4 para Rol 5”.
- Ratificar STFT como métrica primaria y la combinación B.
- Realizar una evaluación auditiva ciega.
- Integrar las cinco contribuciones en una presentación grupal.
- Revisar que el informe cumpla la extensión solicitada.

## Conclusión

El Rol 4 cumple los requisitos principales de los Días 1, 2 y 4. El Día 3
incluye el factorial, los resultados compartidos con el Rol 5 y las curvas de
las 12 configuraciones para ambas métricas. Permanecen parciales la respuesta
sobre el hiperparámetro más importante, la sección de deriva genética y la
entrega formal al Rol 5.

La dependencia local de pandas está resuelta. Los cinco notebooks se ejecutaron
en kernels limpios y pasaron las 55 pruebas unitarias. La diapositiva de
convergencia existe. El pendiente principal es ensamblar la presentación grupal.
