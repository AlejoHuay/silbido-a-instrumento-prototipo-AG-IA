# Rol 4 — Día 4: configuración y convergencia

Fecha de cierre: 21 de octubre de 2026.

## Configuración final propuesta

La configuración operativa que el Rol 4 entrega para la integración conserva los acuerdos implementados en `ConfiguracionAG` e incorpora la recomendación preliminar del Rol 3 para los operadores.

| Elemento | Valor propuesto | Estado |
|---|---:|---|
| Tamaño de población | 50 | Implementado y acordado |
| Reemplazos máximos | 50 | Implementado y acordado |
| Elitismo | 2 | Implementado y acordado |
| Selección | Torneo, `k=3` | Implementado y acordado |
| Cruce | Uniforme, probabilidad 0.90 por pareja, máscara 0.50 | Recomendación preliminar de la comparación A/B/C |
| Mutación | Gaussiana, probabilidad 0.05 por gen, `sigma=0.08` | Implementado; operador recomendado preliminarmente |
| Parada por estancamiento | Paciencia 10, tolerancia `1e-4` | Valor operativo predeterminado del Rol 4 |
| Semilla | Una semilla explícita y un `rng` compartido por corrida | Implementado |
| Fitness | STFT primario; croma complementario | Propuesta provisional del Rol 2, pendiente de ratificación colectiva |

La combinación recomendada es **B: torneo + uniforme + gaussiana**. En las dos réplicas principales obtuvo el mayor fitness medio final, 0.730850220, frente a 0.726136022 de A y 0.724787225 de C. Es una recomendación limitada: A ganó con la semilla 42 y B con 101, por lo que dos réplicas no prueban superioridad general.

Las corridas comparativas usaron `tolerancia_mejora=0` para consumir el mismo presupuesto de 50 reemplazos y 2550 evaluaciones reales por corrida. Esa decisión experimental no sustituye la tolerancia operativa predeterminada de `1e-4`, y la configuración propuesta no fue reejecutada con dicha tolerancia durante este cierre.

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
    tam_poblacion=50,
    max_generaciones=50,
    elitismo=2,
    tam_torneo=3,
    probabilidad_cruce=0.90,
    probabilidad_mutacion=0.05,
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

Se reutilizaron representación y melodía del Rol 1; síntesis, referencia y fitness del Rol 2; operadores y comparación del Rol 3; y registro/resumen del Rol 5. La diapositiva `documentacion/presentacion/rol4_convergencia.pptx` contiene la evidencia visual para la presentación.

No se ejecutó el factorial de 12 configuraciones del Rol 4, el baseline aleatorio, una prueba de significación ni una validación perceptual. La comparación disponible tiene dos réplicas, una melodía y una referencia. El Rol 5 debe conservar estas limitaciones, ratificar la métrica oficial y ampliar la validación antes de formular conclusiones generales.

## Verificaciones ejecutadas

- `04_rol4_dinamica.ipynb` se ejecutó completo en un kernel Jupyter nuevo dentro de una copia temporal: 8/8 celdas de código, sin errores.
- El entorno verificado usó Python 3.10.0 y `pandas 2.3.3`; la dependencia local de pandas quedó disponible mediante `requirements-notebooks.txt` y el entorno `.venv` ya preparado.
- La suite `unittest` ejecutó 55 pruebas y todas pasaron.
- `validar_resultados()` comprobó las seis corridas principales sin llamar al fitness; `resumir_resultados()` mantuvo el orden B, A, C.
- `pip check` no reportó dependencias rotas y `git diff --check` no reportó errores de formato.
- La diapositiva fue validada estructuralmente, importada nuevamente y renderizada para revisión visual. Sus dos gráficos permanecen editables.

La ejecución limpia del notebook vuelve a producir la corrida pequeña del Día 2 que ya forma parte del propio notebook. La sección del Día 4 solo lee resultados guardados; no genera nuevas corridas comparativas ni reemplaza sus checkpoints.
