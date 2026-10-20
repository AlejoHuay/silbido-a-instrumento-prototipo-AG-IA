"""Baselines y planificación reproducible de experimentos del Rol 5.

Este módulo no implementa el ciclo reproductivo del algoritmo genético.
Para ejecutar corridas AG se inyecta un callable cuando Rol 3/4 publiquen
una interfaz completa.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import replace
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from .configuracion import ConfiguracionAG
from .evaluacion import construir_registro_corrida
from .representacion import generar_individuo_aleatorio


FuncionAptitud = Callable[[np.ndarray], float]
RunnerAG = Callable[[ConfiguracionAG], Mapping[str, Any]]


def _validar_cantidad(nombre: str, valor: int) -> None:
    if (
        isinstance(valor, (bool, np.bool_))
        or not isinstance(valor, (int, np.integer))
        or valor < 1
    ):
        raise ValueError(f"{nombre} debe ser un entero >= 1.")


def ejecutar_busqueda_aleatoria(
    funcion_aptitud: FuncionAptitud,
    *,
    num_evaluaciones: int,
    semilla: int,
) -> dict[str, Any]:
    """Busca cromosomas uniformemente en [0, 1]^D con presupuesto explícito."""

    _validar_cantidad("num_evaluaciones", num_evaluaciones)
    if not callable(funcion_aptitud):
        raise ValueError("funcion_aptitud debe ser invocable.")
    if (
        isinstance(semilla, (bool, np.bool_))
        or not isinstance(semilla, (int, np.integer))
        or semilla < 0
    ):
        raise ValueError("semilla debe ser un entero >= 0.")

    rng = np.random.default_rng(int(semilla))
    mejor_fitness = -math.inf
    mejor_individuo: np.ndarray | None = None
    inicio = time.perf_counter()

    for _ in range(int(num_evaluaciones)):
        individuo = generar_individuo_aleatorio(rng=rng)
        fitness = funcion_aptitud(individuo.copy())
        if isinstance(fitness, (bool, np.bool_)):
            raise ValueError("La función de aptitud debe devolver un número finito.")
        try:
            fitness_float = float(fitness)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "La función de aptitud debe devolver un número finito."
            ) from exc
        if not math.isfinite(fitness_float):
            raise ValueError("La función de aptitud debe devolver un número finito.")
        if fitness_float > mejor_fitness:
            mejor_fitness = fitness_float
            mejor_individuo = individuo.copy()

    return {
        "mejor_fitness": float(mejor_fitness),
        "mejor_individuo": mejor_individuo,
        "error_stft_db": None,
        "generaciones_ejecutadas": None,
        "evaluaciones": int(num_evaluaciones),
        "tiempo_s": time.perf_counter() - inicio,
        "motivo_parada": "presupuesto_de_evaluaciones",
    }


def ejecutar_corridas_busqueda_aleatoria(
    funcion_aptitud: FuncionAptitud,
    *,
    num_evaluaciones: int,
    semillas: Sequence[int],
    metrica: str = "fitness",
) -> list[dict[str, Any]]:
    """Ejecuta el baseline por semilla y devuelve registros compatibles con AG."""

    _validar_cantidad("num_evaluaciones", num_evaluaciones)
    if not callable(funcion_aptitud):
        raise ValueError("funcion_aptitud debe ser invocable.")
    if not isinstance(metrica, str) or not metrica.strip():
        raise ValueError("metrica debe ser una cadena no vacía.")
    semillas = list(semillas)
    if not semillas:
        raise ValueError("Se requiere al menos una semilla.")
    if any(
        isinstance(semilla, (bool, np.bool_))
        or not isinstance(semilla, (int, np.integer))
        or semilla < 0
        for semilla in semillas
    ):
        raise ValueError("Cada semilla debe ser un entero >= 0.")

    registros = []
    configuracion = {
        "presupuesto_evaluaciones": int(num_evaluaciones),
        "metrica": metrica,
    }
    for semilla in semillas:
        resultado = ejecutar_busqueda_aleatoria(
            funcion_aptitud,
            num_evaluaciones=num_evaluaciones,
            semilla=int(semilla),
        )
        registros.append(
            construir_registro_corrida(
                metodo="busqueda_aleatoria",
                semilla=int(semilla),
                configuracion=configuracion,
                resultado=resultado,
                tiempo_s=resultado["tiempo_s"],
                metrica=metrica,
            )
        )
    return registros


def ejecutar_baselines_pareados(
    funcion_aptitud: FuncionAptitud,
    registros_ag: Sequence[Mapping[str, Any]],
    *,
    metrica: str,
) -> list[dict[str, Any]]:
    """Repite búsqueda aleatoria con semilla y evaluaciones de cada corrida AG."""

    registros_ag = list(registros_ag)
    if not registros_ag:
        raise ValueError("Se requiere al menos una corrida AG para emparejar.")
    if not callable(funcion_aptitud):
        raise ValueError("funcion_aptitud debe ser invocable.")
    if not isinstance(metrica, str) or not metrica.strip():
        raise ValueError("metrica debe ser una cadena no vacía.")

    pares: list[tuple[int, int, Mapping[str, Any]]] = []
    for indice, fila in enumerate(registros_ag):
        if fila.get("metodo") != "algoritmo_genetico":
            raise ValueError(f"El registro {indice} no corresponde a una corrida AG.")
        if fila.get("metrica") != metrica:
            raise ValueError(
                f"El registro {indice} no usa la misma métrica que el baseline."
            )
        semilla = fila.get("semilla")
        presupuesto = fila.get("evaluaciones")
        _validar_cantidad("evaluaciones del AG", presupuesto)
        if (
            isinstance(semilla, (bool, np.bool_))
            or not isinstance(semilla, (int, np.integer))
            or semilla < 0
        ):
            raise ValueError(f"El registro {indice} tiene una semilla inválida.")
        configuracion_json = fila.get("configuracion_json")
        if not isinstance(configuracion_json, str):
            raise ValueError(
                f"El registro {indice} no contiene configuracion_json."
            )
        try:
            configuracion = json.loads(configuracion_json)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"El registro {indice} tiene configuracion_json inválida."
            ) from exc
        if not isinstance(configuracion, Mapping):
            raise ValueError(
                f"El registro {indice} no serializa una configuración mapping."
            )
        pares.append((int(semilla), int(presupuesto), configuracion))

    registros: list[dict[str, Any]] = []
    for semilla, presupuesto, configuracion in pares:
        resultado = ejecutar_busqueda_aleatoria(
            funcion_aptitud,
            num_evaluaciones=presupuesto,
            semilla=semilla,
        )
        registros.append(
            construir_registro_corrida(
                metodo="busqueda_aleatoria",
                semilla=semilla,
                configuracion=configuracion,
                resultado=resultado,
                tiempo_s=resultado["tiempo_s"],
                metrica=metrica,
            )
        )
    return registros


def ejecutar_corridas_ag(
    runner: RunnerAG,
    configuraciones: Sequence[ConfiguracionAG],
    semillas: Sequence[int],
    *,
    metrica: str,
) -> list[dict[str, Any]]:
    """Ejecuta un runner AG externo para cada par configuración/semilla."""

    if not callable(runner):
        raise ValueError("runner debe ser una función de corrida AG.")
    if not isinstance(metrica, str) or not metrica.strip():
        raise ValueError("metrica debe ser una cadena no vacía.")
    configuraciones = list(configuraciones)
    semillas = list(semillas)
    if not configuraciones:
        raise ValueError("Se requiere al menos una configuración.")
    if not semillas:
        raise ValueError("Se requiere al menos una semilla.")

    if any(
        not isinstance(configuracion, ConfiguracionAG)
        for configuracion in configuraciones
    ):
        raise ValueError("Cada configuración debe ser ConfiguracionAG.")
    if any(
        isinstance(semilla, (bool, np.bool_))
        or not isinstance(semilla, (int, np.integer))
        or semilla < 0
        for semilla in semillas
    ):
        raise ValueError("Cada semilla debe ser un entero >= 0.")

    registros: list[dict[str, Any]] = []
    for configuracion in configuraciones:
        for semilla in semillas:
            config_corrida = replace(configuracion, semilla=int(semilla))
            inicio = time.perf_counter()
            resultado = runner(config_corrida)
            tiempo_s = time.perf_counter() - inicio
            registros.append(
                construir_registro_corrida(
                    metodo="algoritmo_genetico",
                    semilla=int(semilla),
                    configuracion=config_corrida,
                    resultado=resultado,
                    tiempo_s=tiempo_s,
                    metrica=metrica,
                )
            )
    return registros
