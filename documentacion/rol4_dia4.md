# Rol 4 — Día 4: configuración y convergencia

Fecha de cierre inicial: 21 de octubre de 2026. Actualización de integración: 22 de octubre de 2026.

## Configuración final propuesta

La configuración operativa que el Rol 4 entrega para la integración conserva los acuerdos implementados en `ConfiguracionAG` e incorpora la recomendación preliminar del Rol 3 para los operadores.

| Elemento | Valor propuesto | Estado |
|---|---:|---|
| Tamaño de población | 100 | Propuesta final para STFT basada en el factorial integrado |
| Reemplazos máximos | 50 | Implementado y acordado |
| Elitismo | 2 | Mejor media STFT; croma favoreció marginalmente elitismo 1 |
| Selección | Torneo, `k=3` | Implementado y acordado |
| Cruce | Uniforme, probabilidad 0.90 por pareja, máscara 0.50 | Recomendación preliminar de la comparación A/B/C |
| Mutación | Gaussiana, probabilidad 0.08 por gen, `sigma=0.08` | Nivel con mejor media en STFT y croma dentro del factorial |
| Parada por estancamiento | Paciencia 10, tolerancia `1e-4` | Valor operativo predeterminado del Rol 4 |
| Semilla | Una semilla explícita y un `rng` compartido por corrida | Implementado |
| Fitness | STFT primario; croma complementario | Propuesta provisional del Rol 2, pendiente de ratificación colectiva |

La combinación recomendada es **B: torneo + uniforme + gaussiana**. En las dos réplicas principales obtuvo el mayor fitness medio final, 0.730850220, frente a 0.726136022 de A y 0.724787225 de C. Es una recomendación limitada: A ganó con la semilla 42 y B con 101, por lo que dos réplicas no prueban superioridad general.

Las corridas comparativas del Rol 3 usaron `tolerancia_mejora=0` para consumir el mismo presupuesto de 50 reemplazos y 2550 evaluaciones reales por corrida. Esa decisión experimental no sustituye la tolerancia operativa predeterminada de `1e-4`.

Después del cierre inicial se integró el factorial del Rol 5: 12 configuraciones × cinco semillas, por separado para STFT y croma, todas con la combinación B y con paciencia 10/tolerancia `1e-4`. La mayor media STFT fue **0.731952986** para N=100, elitismo=2 y mutación=0.08; la mayor media croma fue **0.959702027** para N=100, elitismo=1 y mutación=0.08. Como STFT continúa como métrica primaria provisional, se propone N=100, elitismo=2 y mutación=0.08 para la demostración final. La diferencia de elitismo entre métricas debe conservarse como sensibilidad pendiente de ratificación, no como contradicción ni superioridad universal.

### Curvas de convergencia del factorial

Las curvas se generaron por posprocesamiento de los 120 historiales AG ya
guardados; no se repitieron experimentos, síntesis ni evaluaciones de fitness.
Cada lámina contiene las 12 configuraciones y sus cinco semillas. Las líneas
individuales terminan en la generación de parada real y la media gruesa se
limita al tramo común presente en las cinco réplicas, evitando inventar
generaciones posteriores:

- `resultados/rol4/convergencia_factorial/convergencia_stft_12_configuraciones.svg`
- `resultados/rol4/convergencia_factorial/convergencia_croma_12_configuraciones.svg`

Se regeneran desde la raíz con
`python scripts/graficar_convergencia_factorial.py --sobrescribir`. El script
valida la matriz 12 × 5, las semillas, la secuencia de generaciones, la finitud
de las estadísticas y que el mejor fitness no disminuya.

## Pregunta teórica: convergencia prematura

La **convergencia prematura** ocurre cuando la población pierde diversidad demasiado pronto y se concentra alrededor de una solución subóptima. El algoritmo deja de explorar regiones prometedoras aunque todavía pueda mostrar pequeñas mejoras locales.

Se detecta combinando tres señales a lo largo de las generaciones:

1. el mejor fitness deja de mejorar durante una ventana de paciencia;
2. la media y la desviación del fitness se estabilizan;
3. la diversidad genotípica cae y permanece baja.

La diversidad baja, por sí sola, no confirma convergencia prematura. Debe relacionarse con el estancamiento y con la calidad lograda.

### Evidencia concreta disponible

Las seis corridas principales comenzaron con diversidad media 0.285487. A terminó en 0.009409 y B en 0.009313: conservaron cerca de 3.3 % de la diversidad inicial. C terminó en 0.125190 y conservó cerca de 43.9 %. A y B, por tanto, concentraron la población con mucha mayor intensidad.

No se afirma que A o B hayan convergido prematuramente: B obtuvo el mayor fitness medio final y las corridas desactivaron de forma deliberada la tolerancia de estancamiento para igualar presupuestos. Los datos permiten advertir un riesgo de pérdida de diversidad, no diagnosticar por sí solos un óptimo local.

Como análisis contrafactual sobre los historiales guardados —sin nuevas llamadas al fitness—, la regla operativa de paciencia 10 y tolerancia `1e-4` habría detenido A/42 en la generación 32, A/101 en la 26, B/42 en la 46, B/101 en la 33 y C/101 en la 43; C/42 habría llegado a 50. Este cálculo orienta la integración, pero no reemplaza corridas ejecutadas con esa configuración.

### Cómo reducir el riesgo

- Reducir elitismo o presión selectiva cuando la diversidad caiga demasiado rápido.
- Aumentar o adaptar la mutación para recuperar exploración.
- Introducir inmigrantes o reinicios parciales si persiste el estancamiento.
- Comparar varias semillas y mantener curvas de fitness y diversidad.

Las dos primeras medidas pueden estudiarse con las interfaces actuales. Inmigración y reinicios son propuestas pendientes: no están implementados ni probados.

## Interfaces entregadas

```python
from src.algoritmo_genetico import ejecutar_ag
from src.configuracion import ConfiguracionAG

config = ConfiguracionAG(
    tam_poblacion=100,
    max_generaciones=50,
    elitismo=2,
    tam_torneo=3,
    probabilidad_cruce=0.90,
    probabilidad_mutacion=0.08,
    paciencia_estancamiento=10,
    tolerancia_mejora=1e-4,
    semilla=42,
)

resultado = ejecutar_ag(
    aptitud,
    config,
    seleccion="torneo",
    cruce="uniforme",
    mutacion="gaussiana",
    sigma=0.08,
)
```

`aptitud` recibe un cromosoma normalizado de forma `(8,)` y devuelve un escalar finito a maximizar. `ejecutar_ag` devuelve, entre otros campos, el mejor individuo, su fitness, historial, generaciones ejecutadas, evaluaciones reales y motivo de parada.

Para reutilizar la evidencia sin recalcular fitness:

```python
from src.comparacion_operadores import validar_resultados, resumir_resultados

corridas = validar_resultados(
    "resultados/operadores/dia3_2026-10-21_64617f8"
)
resumen = resumir_resultados(corridas)
```

## Alcance y pendientes

Se reutilizaron representación y melodía del Rol 1; síntesis, referencia y fitness del Rol 2; operadores, comparación y documentación del Rol 3; y factorial, baseline, registro y resumen del Rol 5. La diapositiva `documentacion/presentacion/rol4_convergencia.pptx` conserva la evidencia visual de la comparación de operadores; no presenta el factorial como si fuera parte de esas seis corridas.

El factorial y el baseline sí están ahora integrados: 60 corridas AG y 60 baselines por métrica. El AG superó descriptivamente al baseline en 60/60 pares STFT y 60/60 pares croma. No se ejecutó una prueba de significación ni una validación perceptual; los datos siguen limitados a una melodía, una referencia y cinco semillas por configuración. El equipo debe ratificar la métrica oficial antes de formular conclusiones generales.

## Verificaciones ejecutadas

- `04_rol4_dinamica.ipynb` se ejecutó completo en un kernel Jupyter nuevo dentro de una copia temporal: 9/9 celdas de código, sin errores y con código de salida 0.
- El entorno verificado usó Python 3.10.0 y `pandas 2.3.3`; la dependencia local de pandas quedó disponible mediante `requirements-notebooks.txt` y el entorno `.venv` ya preparado.
- La suite `unittest` ejecutó 55 pruebas y todas pasaron.
- La verificación conjunta ejecutó 5/5 notebooks, cada uno en un kernel nuevo y una copia independiente del repositorio.
- `validar_resultados()` comprobó las seis corridas principales sin llamar al fitness; `resumir_resultados()` mantuvo el orden B, A, C.
- `--validar-guardado` comprobó los factoriales STFT y croma, incluidos los checkpoints AG y baseline, sin nuevas evaluaciones.
- `graficar_convergencia_factorial.py` validó y representó 120 historiales existentes en dos SVG; no ejecutó el AG ni el fitness.
- `pip check` no reportó dependencias rotas y `git diff --check` no reportó errores de formato.
- La diapositiva fue validada estructuralmente, importada nuevamente y renderizada para revisión visual. Sus dos gráficos permanecen editables.

La ejecución limpia del notebook vuelve a producir la corrida pequeña del Día 2 que ya forma parte del propio notebook. La sección del Día 4 solo lee resultados guardados; no genera nuevas corridas comparativas ni reemplaza sus checkpoints.

En Windows se ajustó `scripts/verificar_notebooks.py` para usar el bucle `WindowsSelectorEventLoopPolicy`, evitando un fallo de cierre de pyzmq que ocurría después de ejecutar correctamente todas las celdas. Este cambio afecta al verificador, no al algoritmo genético ni a sus resultados.
