"""Rol 3, Día 1: selección por torneo para cromosomas continuos."""

import numpy as np

from .representacion import num_genes, validar_individuo


def seleccion_torneo(poblacion, fitness, k=3, rng=None):
    """Devuelve una copia del participante con mayor aptitud.

    poblacion tiene forma (N, D), con D = num_genes(), y fitness (N,).
    Cada fitness[i] debe corresponder a poblacion[i]. Se sortean k índices
    sin reemplazo; en empates gana el primero en el orden sorteado.
    Un individuo puede volver a participar y ganar en llamadas posteriores.

    Se reutiliza el Generator recibido, o se crea uno sin semilla fija.
    No se modifican las entradas ni se calculan aptitudes. Las entradas
    inválidas producen ValueError; no se reparan genes ni se reduce k.
    La salida es un vector float64 de forma (D,) con memoria independiente.
    """
    poblacion = np.asarray(poblacion, dtype=np.float64)
    fitness = np.asarray(fitness, dtype=np.float64)

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

    cantidad = poblacion.shape[0]
    if fitness.ndim != 1 or fitness.size != cantidad:
        raise ValueError("fitness debe ser un vector con una aptitud por individuo.")
    if not np.all(np.isfinite(fitness)):
        raise ValueError("Las aptitudes deben ser finitas.")

    if isinstance(k, (bool, np.bool_)) or not isinstance(k, (int, np.integer)):
        raise ValueError("k debe ser un entero, no un booleano.")
    if not 1 <= k <= cantidad:
        raise ValueError("k debe cumplir 1 <= k <= N.")

    generador = rng if rng is not None else np.random.default_rng()
    participantes = generador.choice(cantidad, size=k, replace=False)
    # argmax conserva el primer máximo en el orden sorteado.
    ganador = participantes[np.argmax(fitness[participantes])]
    return poblacion[ganador].copy()
