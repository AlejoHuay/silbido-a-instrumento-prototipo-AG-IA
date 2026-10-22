# Rol 5 — Día 3: factorial y baseline pareado

## Estado y protocolo

Se ejecutó el factorial de 12 configuraciones con cinco semillas (`42, 101,
2024, 7, 999`), para 60 corridas por métrica. Factores: población `{20, 50,
100}`, elitismo `{1, 2}` y probabilidad de mutación `{0.02, 0.08}`. Se
conservaron los demás valores de `ConfiguracionAG`: 50 generaciones máximas,
torneo de tamaño 3, probabilidad de cruce 0.90, paciencia 10 y tolerancia de
mejora `1e-4`.

El operador fijo fue B: torneo, cruce uniforme y mutación gaussiana, con
`sigma=0.08`; `alpha=0.5` y `b=2.0` quedan registrados aunque no son usados por
esta combinación. Es una elección experimental provisional basada en la
recomendación preliminar del Rol 4; no está ratificada colectivamente. STFT se
usó como métrica inicial por ser la predeterminada en el código, pero su
ratificación colectiva también sigue pendiente. Chroma se ejecutó como bloque
separado y no se mezcló con STFT.

La parada existente se mantuvo sin cambios. Cada generación reevaluó la
población completa, incluidas las élites; por eso el conteo satisface
`evaluaciones = tam_poblacion × (generaciones_ejecutadas + 1)`. Las paradas por
estancamiento explican presupuestos inferiores al máximo. Cada baseline usó
exactamente las evaluaciones reales de su AG, y se emparejó por configuración,
semilla y métrica.

## Datos y reproducibilidad

La melodía tiene 16 notas/duraciones. La referencia es WAV mono PCM16, 22,050
Hz y 59,645 muestras; dimensiones, canales, metadatos, frecuencia y valores
finitos se validaron antes de ejecutar. Se registraron SHA-256 de las entradas,
versión del intérprete y dependencias científicas en el manifiesto.

Las ejecuciones se hicieron en procesos Python 3.14.5 sobre Windows, no en
kernels Jupyter. No se instalaron paquetes, no se regeneraron evidencias de
Roles 2 o 3 y no se cambiaron contratos de `src/`.

Desde la raíz del repositorio, `python scripts/ejecutar_rol5_factorial.py
--ejecutar --metricas stft croma` inicia una ejecución nueva. El script crea
una carpeta con identificador UTC y falla si ya existe. Para una interrupción,
`--reanudar RUTA_DE_EJECUCION --metricas stft croma` consume checkpoints y
ejecuta únicamente las corridas que falten. `--validar-guardado
RUTA_DE_EJECUCION --metricas stft croma` vuelve a comprobar resultados sin
llamar al fitness.

## Resultados descriptivos

| Métrica | AG n | Baseline n | Media fitness AG (DE muestral) | Media fitness baseline (DE muestral) | Diferencia pareada media AG−baseline (DE) | Mediana diferencia | Pares con AG mayor |
|---|---:|---:|---:|---:|---:|---:|---:|
| STFT | 60 | 60 | 0.729882 (0.003367) | 0.717397 (0.001472) | 0.012485 (0.003424) | 0.013607 | 60/60 |
| Chroma | 60 | 60 | 0.958681 (0.001454) | 0.954582 (0.000978) | 0.004099 (0.001224) | 0.004168 | 60/60 |

Estas cifras son descriptivas para una melodía, una referencia, estos factores y
estas semillas. No se ejecutó una prueba de significación ni validación
perceptual; no se concluye superioridad general. Los resúmenes por configuración
contienen cinco réplicas por grupo y están separados por métrica.

| Métrica | Evaluaciones AG totales | Rango de evaluaciones por AG | Parada máxima | Parada por estancamiento |
|---|---:|---:|---:|---:|
| STFT | 133,300 | 760–5,100 | 24 | 36 |
| Chroma | 152,680 | 480–5,100 | 28 | 32 |

Los baselines igualaron esos conteos corrida por corrida. El total fue 285,980
evaluaciones AG y 285,980 evaluaciones de búsqueda aleatoria entre ambas
métricas.

## Artefactos

La ejecución está en
`resultados/rol5/dia3_factorial/ejecucion_20261021T184758Z_c5dc431/`.
Contiene manifiesto y cierre, checkpoints JSON de cada corrida AG con resultado
completo e historial, checkpoints de baseline, CSV separados de AG, baseline y
comparación pareada, resúmenes y validaciones por métrica. El resumen
`resumen_pareado_por_configuracion.csv` tiene 12 grupos y cinco pares por grupo;
`resumen_por_configuracion.csv` informa AG y baseline por separado.

El primer cierre de STFT encontró un defecto local del runner: al validar la
matriz, una clave de configuración conservaba la semilla base en vez de la
semilla inyectada. Las 60 corridas STFT ya tenían checkpoints y no se
repitieron. Se corrigió el acceso a la semilla, se validaron los 60 checkpoints
sin volver a llamar al fitness y se reanudó desde ellos. Las corridas chroma y
los baselines se realizaron con el runner corregido. Los módulos de AG,
configuración, aptitud, evaluación, datos y síntesis conservaron las huellas
del manifiesto inicial. El hash del script de orquestación actual difiere del
registrado al lanzamiento porque se añadieron soporte de reanudación,
validación en disco y resúmenes etiquetados; el manifiesto inicial se conserva
sin sobrescribirlo. `auditoria_orquestacion.json` registra los hashes
disponibles y declara que no se conservó el hash intermedio del runner corregido.

El archivo `resumen_metodos.csv`, generado antes de detectar el defecto de
etiquetado, conserva medias y desviaciones correctas, pero su campo `metrica`
indica `mejor_fitness` en vez de STFT/chroma. La tabla corregida es
`resumen_metodos_etiquetado.csv`, con el campo adicional
`metrica_evaluacion`. Se preservó el archivo anterior y no se sobrescribió.

## Verificación y limitaciones

El runner valida 12 configuraciones × cinco semillas, unicidad, finitud,
historiales, monotonía del mejor fitness, relación entre generaciones y
evaluaciones, motivo de parada, operadores y presupuesto pareado. Después de
guardar, `--validar-guardado` vuelve a comparar los CSV con los 120 checkpoints
por métrica sin ejecutar aptitud.

Compilación del runner y validación guardada: correctas para ambas métricas.
Pasaron 22 pruebas existentes de Rol 4 y Rol 5. La suite completa previamente
reportó 51 pruebas pasadas y una importación fallida porque falta pandas; no se
instaló. Ninguna prueba unitaria se presenta como experimento. Las corridas
fueron procesos Python, no kernels Jupyter.

Los CSV son de creación exclusiva; el reanudador lee checkpoints existentes y
no repite corridas ya completas. Para crear una nueva ejecución se requiere un
identificador de carpeta nuevo. No se hizo commit, push ni merge. La métrica y
los operadores mantienen estado provisional pendiente de ratificación del
equipo.
