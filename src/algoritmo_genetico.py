"""Rol 4: ciclo completo, dinámica poblacional y criterios de parada."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
from typing import Callable

import numpy as np

from .configuracion import ConfiguracionAG
from .operadores import (
    cruce_blend,
    cruce_uniforme,
    mutacion_gaussiana,
    mutacion_no_uniforme,
    seleccion_sus,
    seleccion_torneo,
)
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


def _validar_opcion(nombre: str, valor: str, permitidas: tuple[str, ...]) -> str:
    if valor not in permitidas:
        opciones = ", ".join(repr(opcion) for opcion in permitidas)
        raise ValueError(f"{nombre} debe ser una de: {opciones}.")
    return valor


def _validar_parametro_operador(
    nombre: str,
    valor: float,
    *,
    positivo: bool = False,
) -> None:
    if (
        isinstance(valor, (bool, np.bool_))
        or not isinstance(valor, Real)
        or not np.isfinite(valor)
    ):
        comparacion = "> 0" if positivo else ">= 0"
        raise ValueError(f"{nombre} debe ser un número finito {comparacion}.")
    limite_invalido = valor <= 0 if positivo else valor < 0
    if limite_invalido:
        comparacion = "> 0" if positivo else ">= 0"
        raise ValueError(f"{nombre} debe ser un número finito {comparacion}.")


def _seleccionar_padres(
    poblacion: np.ndarray,
    fitness: np.ndarray,
    cantidad: int,
    seleccion: str,
    configuracion: ConfiguracionAG,
    rng: np.random.Generator,
) -> np.ndarray:
    """Obtiene un lote par de padres sin compartir memoria con la población."""

    if seleccion == "sus":
        return seleccion_sus(
            poblacion,
            fitness,
            cantidad=cantidad,
            rng=rng,
        )

    return np.stack([
        seleccion_torneo(
            poblacion,
            fitness,
            k=configuracion.tam_torneo,
            rng=rng,
        )
        for _ in range(cantidad)
    ])


def ejecutar_ag(
    funcion_aptitud: Callable[[np.ndarray], float],
    configuracion: ConfiguracionAG | None = None,
    *,
    seleccion: str = "torneo",
    cruce: str = "blend",
    mutacion: str = "gaussiana",
    alpha: float = 0.5,
    sigma: float = 0.08,
    b: float = 2.0,
) -> dict:
    """Ejecuta el algoritmo genético completo y maximiza ``funcion_aptitud``.

    La población inicial es la generación 0. Cada reemplazo crea la generación
    siguiente y vuelve a evaluar todos sus individuos, incluidas las élites.
    El generador de la corrida se comparte con todos los operadores; la función
    de aptitud debe ser determinista si se quiere garantizar monotonía por
    elitismo. Los parámetros ``alpha``, ``sigma`` y ``b`` se validan antes de
    iniciar la corrida y vuelven a respetar los contratos del Rol 3 al usarse.

    Retorna un diccionario compatible con ``ejecutar_corridas_ag`` del Rol 5,
    además del historial y de copias de la población y el fitness finales.
    """

    if not callable(funcion_aptitud):
        raise ValueError("funcion_aptitud debe ser invocable.")
    if configuracion is None:
        configuracion = ConfiguracionAG()
    if not isinstance(configuracion, ConfiguracionAG):
        raise ValueError("configuracion debe ser una instancia de ConfiguracionAG.")

    seleccion = _validar_opcion(
        "seleccion", seleccion, ("torneo", "sus")
    )
    cruce = _validar_opcion("cruce", cruce, ("blend", "uniforme"))
    mutacion = _validar_opcion(
        "mutacion", mutacion, ("gaussiana", "no_uniforme")
    )
    _validar_parametro_operador("alpha", alpha)
    _validar_parametro_operador("sigma", sigma)
    _validar_parametro_operador("b", b, positivo=True)

    rng = np.random.default_rng(configuracion.semilla)
    poblacion = inicializar_poblacion(configuracion, rng=rng)
    historial: list[EstadisticasGeneracion] = []
    historial_mejor: list[float] = []
    mejor_individuo: np.ndarray | None = None
    mejor_fitness = -np.inf
    evaluaciones = 0
    motivo_parada = "max_generaciones"

    for generacion in range(configuracion.max_generaciones + 1):
        fitness = evaluar_poblacion(poblacion, funcion_aptitud)
        evaluaciones += len(poblacion)
        historial.append(
            calcular_estadisticas(poblacion, fitness, generacion)
        )

        indice_mejor = int(np.argmax(fitness))
        if fitness[indice_mejor] > mejor_fitness:
            mejor_fitness = float(fitness[indice_mejor])
            mejor_individuo = poblacion[indice_mejor].copy()
        historial_mejor.append(float(mejor_fitness))

        if generacion == configuracion.max_generaciones:
            motivo_parada = "max_generaciones"
            break
        if detectar_estancamiento(
            historial_mejor,
            paciencia=configuracion.paciencia_estancamiento,
            tolerancia=configuracion.tolerancia_mejora,
        ):
            motivo_parada = "estancamiento"
            break

        elites = seleccionar_elites(
            poblacion,
            fitness,
            configuracion.elitismo,
        )
        plazas_descendencia = configuracion.tam_poblacion - len(elites)
        cantidad_padres = 2 * ((plazas_descendencia + 1) // 2)
        padres = _seleccionar_padres(
            poblacion,
            fitness,
            cantidad_padres,
            seleccion,
            configuracion,
            rng,
        )

        nueva_poblacion = [elite.copy() for elite in elites]
        for indice in range(0, cantidad_padres, 2):
            padre_1, padre_2 = padres[indice], padres[indice + 1]
            if rng.random() < configuracion.probabilidad_cruce:
                if cruce == "blend":
                    hijos = cruce_blend(
                        padre_1,
                        padre_2,
                        alpha=alpha,
                        rng=rng,
                    )
                else:
                    hijos = cruce_uniforme(padre_1, padre_2, rng=rng)
            else:
                hijos = (padre_1.copy(), padre_2.copy())

            for hijo in hijos:
                if mutacion == "gaussiana":
                    hijo_mutado = mutacion_gaussiana(
                        hijo,
                        p_mut=configuracion.probabilidad_mutacion,
                        sigma=sigma,
                        rng=rng,
                    )
                else:
                    hijo_mutado = mutacion_no_uniforme(
                        hijo,
                        generacion=generacion,
                        max_generaciones=configuracion.max_generaciones,
                        p_mut=configuracion.probabilidad_mutacion,
                        b=b,
                        rng=rng,
                    )
                nueva_poblacion.append(hijo_mutado.copy())
                if len(nueva_poblacion) == configuracion.tam_poblacion:
                    break
            if len(nueva_poblacion) == configuracion.tam_poblacion:
                break

        poblacion = _validar_poblacion(np.stack(nueva_poblacion))

    if mejor_individuo is None:  # pragma: no cover - defensa interna
        raise RuntimeError("La corrida terminó sin evaluar individuos.")

    return {
        "mejor_individuo": mejor_individuo.copy(),
        "mejor_fitness": float(mejor_fitness),
        "historial": tuple(historial),
        "historial_mejor_fitness": tuple(historial_mejor),
        "configuracion": configuracion,
        "semilla": configuracion.semilla,
        "motivo_parada": motivo_parada,
        "generaciones_ejecutadas": generacion,
        "evaluaciones": evaluaciones,
        "poblacion_final": poblacion.copy(),
        "fitness_final": fitness.copy(),
        "operadores": {
            "seleccion": seleccion,
            "cruce": cruce,
            "mutacion": mutacion,
            "alpha": alpha,
            "sigma": sigma,
            "b": b,
        },
    }
