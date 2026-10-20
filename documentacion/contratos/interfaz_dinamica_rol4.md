# Interfaz de dinámica poblacional — Rol 4

**Estado:** Día 1. Configuración, medición, elitismo y parada implementados;
cruce y mutación se conectarán cuando el Rol 3 publique sus firmas del Día 2.
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
            si rng.random() < probabilidad_mutacion:
                hijo <- mutacion_rol3(
                    hijo, generación, G_max, rng=rng
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

## Funciones disponibles desde el Día 1

```python
from src.algoritmo_genetico import (
    inicializar_poblacion,
    evaluar_poblacion,
    seleccionar_elites,
    calcular_estadisticas,
    detectar_estancamiento,
)
from src.configuracion import ConfiguracionAG
```

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

## Acuerdo pendiente para el Día 2

Antes de cerrar el ciclo deben fijarse con el Rol 3 las firmas y el número de
hijos devuelto por cada cruce, además de los parámetros de cada mutación. El
Rol 4 no duplica operadores temporales en `src/` porque eso produciría dos
implementaciones incompatibles y dificultaría atribuir las contribuciones.

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
El futuro runner debe contar llamadas reales y devolver E incluso con parada
anticipada. Si cambia a reutilizar aptitudes, cambia E: no usar N*G como atajo.
El baseline se ejecutará con el E observado, misma métrica, datos y semilla de
cada corrida. El runner todavía no existe: el conteo del AG no está verificado
experimentalmente. Consultar el plan detallado del Rol 5.

Las probabilidades 0.90/0.05 son valores del código; queda pendiente acordar
con Rol 3 si la mutación se aplica por hijo o por gen y evitar una segunda
aplicación de la probabilidad dentro del operador. Las llamadas de reproducción
son pseudocódigo, no firmas publicadas. No se añaden operadores ficticios.

Documento de entrega: [diseño conjunto](../diseno/diseno_completo_ag_dia1.md).
