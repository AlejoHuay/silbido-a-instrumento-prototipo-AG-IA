# Interfaz de dinámica poblacional — Rol 4

**Estado:** Día 2. Ciclo completo implementado y verificado con los operadores
del Rol 3, la síntesis y el fitness reales. Las 12 configuraciones y sus
réplicas corresponden al Día 3.
**Consumidores:** Roles 3 y 5, notebook de integración.

## Configuración base implementada y propuesta para ratificación

- El AG maximiza la aptitud provista por el Rol 2.
- Cromosoma: vector `float64` normalizado en `[0, 1]^8`.
- Población base: `N=50`; se experimentará con `N in {20, 50, 100}`.
- Selección: torneo `k=3` mediante `seleccion_torneo()` del Rol 3.
- Elitismo: dos copias independientes de los mejores individuos.
- Máximo: 50 reemplazos después de evaluar la generación 0.
- Parada anticipada: mejora global acumulada menor que `1e-4` en una ventana de 10 transiciones (11 registros).
- Una sola instancia de `np.random.Generator` por corrida, compartida con
  inicialización, selección, cruce y mutación.
- Registro por generación: fitness máximo, medio, desviación estándar y
  diversidad genética (media de la desviación estándar por gen).

Los valores viven en `ConfiguracionAG`; el notebook no define parámetros
ocultos. `crear_plan_experimental()` prepara exactamente 12 configuraciones:
3 tamaños de población x 2 niveles de elitismo x 2 tasas de mutación. Las
cinco semillas acordadas son réplicas posteriores, no configuraciones nuevas.

## Pseudocódigo del ciclo completo

```text
recibir configuración, función de fitness y operadores del Rol 3
crear rng una sola vez con la semilla de la corrida
P <- generar población inicial de N cromosomas usando rng
evaluaciones <- 0
mejor_global <- ninguno
historial_mejor <- vacío

para generación = 0, ..., G_max:
    F <- evaluar cada individuo de P, manteniendo el mismo orden
    incrementar evaluaciones por cada llamada real a fitness, incluidas élites
    registrar máximo, media, desviación y diversidad
    actualizar mejor_global e historial_mejor

    si generación == G_max:
        terminar por máximo de generaciones
    si detectar_estancamiento(historial_mejor, paciencia, tolerancia):
        terminar por estancamiento

    elites <- copias de los e individuos con mayor F
    nueva_P <- elites

    mientras tamaño(nueva_P) < N:
        padre_1 <- seleccion_torneo(P, F, k=configuracion.tam_torneo, rng=rng)
        padre_2 <- seleccion_torneo(P, F, k=configuracion.tam_torneo, rng=rng)

        si rng.random() < probabilidad_cruce:
            hijos <- cruce_rol3(padre_1, padre_2, rng=rng)
        si no:
            hijos <- copias(padre_1, padre_2)

        para cada hijo y mientras tamaño(nueva_P) < N:
            hijo <- mutacion_no_uniforme(
                hijo, generación, G_max, p_mut=probabilidad_mutacion, rng=rng
            )
            validar que hijo pertenece a [0, 1]^8
            añadir una copia de hijo a nueva_P

    P <- nueva_P

devolver copia de mejor_global, su fitness, historial, configuración,
         semilla, motivo de parada y evaluaciones reales
```

La población se evalúa antes de reproducirse. Por tanto, la generación 0 es la
población aleatoria inicial y la última población creada nunca queda sin
evaluar. El elitismo se copia antes de producir descendientes, lo que garantiza
que el mejor fitness no disminuya entre generaciones si la aptitud es determinista.
El ruido de síntesis usa su propia semilla fija (2026), independiente del Generator del AG.

## Interfaz ejecutable

```python
from src.algoritmo_genetico import (
    ejecutar_ag,
    inicializar_poblacion,
    evaluar_poblacion,
    seleccionar_elites,
    calcular_estadisticas,
    detectar_estancamiento,
)
from src.configuracion import ConfiguracionAG
```

La corrida completa se invoca así:

```python
resultado = ejecutar_ag(
    funcion_aptitud,
    ConfiguracionAG(tam_poblacion=5, max_generaciones=3, elitismo=1),
    seleccion="torneo",       # o "sus"
    cruce="blend",            # o "uniforme"
    mutacion="gaussiana",     # o "no_uniforme"
)
```

El resultado incluye `mejor_individuo`, `mejor_fitness`, `historial`,
`historial_mejor_fitness`, `generaciones_ejecutadas`, `evaluaciones`,
`motivo_parada`, copias de la población y fitness finales, configuración,
semilla y operadores elegidos. Es compatible con el runner inyectable de
`ejecutar_corridas_ag()` del Rol 5.

`evaluar_poblacion()` pasa una copia de cada cromosoma a la función de aptitud,
evitando que una evaluación modifique accidentalmente la población. El vector
de fitness mantiene exactamente el orden de las filas, como exige el contrato
de `seleccion_torneo()`.

## Conexión actual con el Rol 3

```python
import numpy as np

from src.algoritmo_genetico import inicializar_poblacion
from src.configuracion import ConfiguracionAG
from src.operadores import seleccion_torneo

config = ConfiguracionAG()
rng = np.random.default_rng(config.semilla)
poblacion = inicializar_poblacion(config, rng=rng)

# fitness debe provenir de evaluar_individuo() del Rol 2.
padre = seleccion_torneo(
    poblacion,
    fitness,
    k=config.tam_torneo,
    rng=rng,
)
```

## Firmas disponibles del Día 2

El [contrato del Rol 3](interfaz_operadores_rol3.md) publica las firmas de
BLX-alpha/uniforme (dos hijos), gaussiana/no uniforme y SUS por lote. El
marcador `cruce_rol3` del pseudocódigo corresponde a `cruce_blend` o
`cruce_uniforme`; no es una función ficticia implementada.
Para SUS se obtiene una sola vez por reproducción un lote de
`2*ceil((N-e)/2)` padres y se recorren parejas, en lugar de los dos torneos.
No llamar repetidamente a SUS con cantidad uno. Si falta una plaza, conservar
solo el primer hijo de la última pareja. La mutación recibe p_mut sin filtro
previo por individuo. Para la no uniforme, t=generación evaluada y T=G_max.
El notebook del Rol 3 demuestra un paso real. El ciclo que repite ese esquema,
controla la parada y registra la corrida está implementado en `ejecutar_ag()`.

## Definiciones precisas y presupuesto

Máximo y media se calculan sobre el fitness de la generación. Su desviación
es poblacional (`ddof=0`). Diversidad = `mean(std(P, axis=0, ddof=0))`, con
P normalizada. No confundir estas medidas con la variación entre corridas.

`detectar_estancamiento(H,p,tol)` usa los últimos p+1 mejores globales:
`max(ventana[1:]) - ventana[0] < tol`. Con menos registros devuelve False.
No existe contador de mejoras individuales ni reinicio; se desplaza la ventana.
Pequeñas mejoras acumuladas pueden impedir la parada. Con igualdad al umbral
no se para; tolerancia cero desactiva la parada para un historial no decreciente.
Se conserva esta semántica del código, sin reemplazarla por otra regla.

El pseudocódigo evalúa toda P en generación 0 y tras cada reemplazo, también
las élites. Sin evaluaciones extra: E=N*(g+1), donde g son reemplazos ejecutados.
El runner cuenta llamadas reales y devuelve E incluso con parada
anticipada. Si cambia a reutilizar aptitudes, cambia E: no usar N*G como atajo.
El baseline se ejecutará con el E observado, misma métrica, datos y semilla de
cada corrida. El conteo se verifica con pruebas de máximo de generaciones y de
parada anticipada. Consultar el plan detallado del Rol 5.

Acuerdo de granularidad de probabilidades (definido por Rol 1 con Roles 3 y 4):
- Cruce (p_cruce = 0.90): se aplica por pareja de padres seleccionados. En cruce
  uniforme, cada gen se intercambia con p_swap = 0.50 interno.
- Mutación (p_mutación base 0.05, factoriales 0.02 y 0.08): se aplica por gen de
  forma independiente dentro del operador de Rol 3. Rol 4 pasa el individuo y la
  tasa sin filtro previo por hijo, evitando atenuación cuadrática (p_m x p_m).
El ciclo implementado sigue este pseudocódigo y usa directamente las firmas
publicadas en el contrato del Rol 3.

Documento de entrega: [diseño conjunto](../diseno/diseno_completo_ag_dia1.md).
