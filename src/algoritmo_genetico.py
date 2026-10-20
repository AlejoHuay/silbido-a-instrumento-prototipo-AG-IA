"""Rol 4: dinámica poblacional, elitismo y criterios de parada.

El ciclo reproductivo completo se conectará cuando el Rol 3 publique las
firmas de cruce y mutación del Día 2. Este módulo ya concentra las partes de
la dinámica que no dependen de esas firmas y evita duplicarlas en notebooks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .configuracion import ConfiguracionAG
from .representacion import (
    generar_poblacion_inicial,
    num_genes,
    validar_individuo,
)


@dataclass(frozen=True)
class EstadisticasGeneracion:
    """Resumen suficiente para estudiar convergencia y diversidad."""

    generacion: int
    fitness_maximo: float
    fitness_medio: float
    desviacion_fitness: float
    diversidad_genetica: float


def _validar_poblacion(poblacion) -> np.ndarray:
    poblacion = np.asarray(poblacion, dtype=np.float64)

    if (
        poblacion.ndim != 2
        or poblacion.shape[0] == 0
        or poblacion.shape[1] != num_genes()
    ):
        raise ValueError(
            f"La población debe tener forma (N, {num_genes()}) con N > 0."
        )

    for indice, individuo in enumerate(poblacion):
        valido, mensaje = validar_individuo(individuo)
        if not valido:
            raise ValueError(f"Individuo {indice} inválido: {mensaje}")

    return poblacion


def _validar_fitness(fitness, cantidad: int) -> np.ndarray:
    fitness = np.asarray(fitness, dtype=np.float64)

    if fitness.ndim != 1 or fitness.size != cantidad:
        raise ValueError("fitness debe contener una aptitud por individuo.")
    if not np.all(np.isfinite(fitness)):
        raise ValueError("Las aptitudes deben ser finitas.")

    return fitness


def inicializar_poblacion(
    configuracion: ConfiguracionAG,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Crea la población inicial usando el generador compartido de la corrida."""

    generador = rng if rng is not None else np.random.default_rng(
        configuracion.semilla
    )
    return generar_poblacion_inicial(
        configuracion.tam_poblacion,
        rng=generador,
    )


def evaluar_poblacion(
    poblacion,
    funcion_aptitud: Callable[[np.ndarray], float],
) -> np.ndarray:
    """Evalúa cada fila sin alterar la población y conserva su mismo orden."""

    poblacion = _validar_poblacion(poblacion)
    fitness = np.asarray(
        [funcion_aptitud(individuo.copy()) for individuo in poblacion],
        dtype=np.float64,
    )
    return _validar_fitness(fitness, len(poblacion))


def seleccionar_elites(poblacion, fitness, cantidad: int) -> np.ndarray:
    """Devuelve copias de los mejores individuos, ordenadas por aptitud.

    En empates se conserva el orden original de la población. El fitness se
    maximiza, igual que en ``seleccion_torneo`` del Rol 3.
    """

    poblacion = _validar_poblacion(poblacion)
    fitness = _validar_fitness(fitness, len(poblacion))

    if (
        isinstance(cantidad, (bool, np.bool_))
        or not isinstance(cantidad, (int, np.integer))
        or not 0 <= cantidad <= len(poblacion)
    ):
        raise ValueError("cantidad debe cumplir 0 <= cantidad <= N.")

    indices = np.argsort(-fitness, kind="stable")[:cantidad]
    return poblacion[indices].copy()


def calcular_estadisticas(
    poblacion,
    fitness,
    generacion: int,
) -> EstadisticasGeneracion:
    """Mide máximo, media, desviación y diversidad de una generación."""

    poblacion = _validar_poblacion(poblacion)
    fitness = _validar_fitness(fitness, len(poblacion))

    if (
        isinstance(generacion, (bool, np.bool_))
        or not isinstance(generacion, (int, np.integer))
        or generacion < 0
    ):
        raise ValueError("generacion debe ser un entero >= 0.")

    # Media de las desviaciones por gen en el espacio normalizado [0, 1].
    diversidad = float(np.mean(np.std(poblacion, axis=0)))

    return EstadisticasGeneracion(
        generacion=int(generacion),
        fitness_maximo=float(np.max(fitness)),
        fitness_medio=float(np.mean(fitness)),
        desviacion_fitness=float(np.std(fitness)),
        diversidad_genetica=diversidad,
    )


def detectar_estancamiento(
    historial_mejor_fitness,
    paciencia: int = 10,
    tolerancia: float = 1e-4,
) -> bool:
    """Compara la mejora acumulada en una ventana de ``paciencia`` pasos.

    El historial debe registrar el mejor fitness global tras cada generación,
    por lo que se espera una serie monótona no decreciente cuando hay elitismo.
    Con p = paciencia se comparan p+1 registros: max(ventana[1:]) - ventana[0].
    Se para si esa diferencia es estrictamente menor que tolerancia. No hay
    contador que se reinicie: la ventana avanza un registro por generación.
    """

    historial = np.asarray(historial_mejor_fitness, dtype=np.float64)

    if historial.ndim != 1 or not np.all(np.isfinite(historial)):
        raise ValueError("El historial debe ser un vector de valores finitos.")
    if (
        isinstance(paciencia, (bool, np.bool_))
        or not isinstance(paciencia, (int, np.integer))
        or paciencia < 1
    ):
        raise ValueError("paciencia debe ser un entero >= 1.")
    if (
        isinstance(tolerancia, bool)
        or not isinstance(tolerancia, (int, float))
        or not np.isfinite(tolerancia)
        or tolerancia < 0
    ):
        raise ValueError("tolerancia debe ser un número finito >= 0.")
    if historial.size < paciencia + 1:
        return False

    ventana = historial[-(paciencia + 1):]
    mejora = float(np.max(ventana[1:]) - ventana[0])
    return mejora < tolerancia
