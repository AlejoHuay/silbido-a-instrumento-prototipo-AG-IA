"""Rol 3: selección, cruces y mutaciones para cromosomas continuos."""

from numbers import Real
import numpy as np

from .representacion import num_genes, validar_individuo, restringir_limites


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


def _validar_cromosoma(individuo):
    """Convierte a float64 y rechaza entradas inválidas sin repararlas."""
    genes = np.asarray(individuo, dtype=np.float64)
    valido, mensaje = validar_individuo(genes)
    if not valido:
        raise ValueError(f"Cromosoma inválido: {mensaje}")
    return genes


def _validar_real(nombre, valor, minimo=0.0, maximo=None):
    if (
        isinstance(valor, (bool, np.bool_))
        or not isinstance(valor, Real)
        or not np.isfinite(valor)
        or valor < minimo
        or (maximo is not None and valor > maximo)
    ):
        raise ValueError(f"{nombre} debe ser real finito en el rango permitido.")


def _recortar_y_validar(hijo):
    hijo = restringir_limites(hijo)
    return _validar_cromosoma(hijo).copy()


def seleccion_sus(poblacion, fitness, cantidad, rng=None):
    """Selecciona un lote (cantidad, D) con un único inicio y punteros equidistantes.

    Maximiza aptitudes no negativas. Escala por el máximo antes de sumar;
    si todas son cero, usa pesos iguales. Puede repetir filas, sin compartir
    memoria con la entrada ni entre cromosomas devueltos. No desplaza negativos.
    """
    poblacion = np.asarray(poblacion, dtype=np.float64)
    fitness = np.asarray(fitness, dtype=np.float64)
    if (
        poblacion.ndim != 2 or poblacion.shape[0] == 0
        or poblacion.shape[1] != num_genes()
    ):
        raise ValueError(f"La población debe tener forma (N, {num_genes()}) con N > 0.")
    for individuo in poblacion:
        _validar_cromosoma(individuo)
    if fitness.ndim != 1 or fitness.size != len(poblacion):
        raise ValueError("fitness debe contener una aptitud por individuo.")
    if not np.all(np.isfinite(fitness)) or np.any(fitness < 0):
        raise ValueError("SUS requiere aptitudes finitas no negativas.")
    if (
        isinstance(cantidad, (bool, np.bool_))
        or not isinstance(cantidad, (int, np.integer)) or cantidad < 1
    ):
        raise ValueError("cantidad debe ser un entero positivo.")

    generador = rng if rng is not None else np.random.default_rng()
    maximo = fitness.max()
    pesos = fitness / maximo if maximo > 0 else np.ones(len(fitness))
    acumulada = np.cumsum(pesos / pesos.sum())
    acumulada[-1] = 1.0
    inicio = generador.random() / cantidad
    punteros = inicio + np.arange(cantidad) / cantidad
    # Evitar que el redondeo del último puntero alcance exactamente 1.
    punteros = np.minimum(punteros, np.nextafter(1.0, 0.0))
    indices = np.searchsorted(acumulada, punteros, side="right")
    return poblacion[indices].copy()


def cruce_blend(padre1, padre2, alpha=0.5, rng=None):
    """BLX-alpha por gen; devuelve dos copias válidas. p_cruce pertenece al ciclo."""
    padre1 = _validar_cromosoma(padre1)
    padre2 = _validar_cromosoma(padre2)
    _validar_real("alpha", alpha)
    generador = rng if rng is not None else np.random.default_rng()
    distancia = np.abs(padre1 - padre2)
    inferior = np.minimum(padre1, padre2) - alpha * distancia
    superior = np.maximum(padre1, padre2) + alpha * distancia
    hijo1 = generador.uniform(inferior, superior)
    hijo2 = generador.uniform(inferior, superior)
    return _recortar_y_validar(hijo1), _recortar_y_validar(hijo2)


def cruce_uniforme(padre1, padre2, rng=None):
    """Intercambia genes con p_swap=0.50 y herencia complementaria, sin p_cruce."""
    padre1 = _validar_cromosoma(padre1)
    padre2 = _validar_cromosoma(padre2)
    generador = rng if rng is not None else np.random.default_rng()
    intercambiar = generador.random(num_genes()) < 0.5
    hijo1 = np.where(intercambiar, padre2, padre1)
    hijo2 = np.where(intercambiar, padre1, padre2)
    return _recortar_y_validar(hijo1), _recortar_y_validar(hijo2)


def mutacion_gaussiana(individuo, p_mut=0.05, sigma=0.08, rng=None):
    """Selecciona cada gen con p_mut y suma N(0, sigma) antes del clipping."""
    hijo = _validar_cromosoma(individuo).copy()
    _validar_real("p_mut", p_mut, maximo=1.0)
    _validar_real("sigma", sigma)
    generador = rng if rng is not None else np.random.default_rng()
    seleccionados = generador.random(num_genes()) < p_mut
    hijo[seleccionados] += generador.normal(0.0, sigma, size=seleccionados.sum())
    return _recortar_y_validar(hijo)


def mutacion_no_uniforme(
    individuo, generacion, max_generaciones, p_mut=0.05, b=2.0, rng=None,
):
    """Muta por gen hacia un límite con delta=y*(1-r**((1-t/T)**b)).

    t y T son enteros, T>0 y 0<=t<=T. El ejemplo del ciclo usa t=g al
    reproducir la población evaluada g para crear g+1 (g=0,...,T-1).
    En t=T devuelve una copia sin desplazamiento ni consumo de aleatoriedad.
    No debe aplicarse otro filtro de probabilidad por individuo en el ciclo.
    """
    hijo = _validar_cromosoma(individuo).copy()
    _validar_real("p_mut", p_mut, maximo=1.0)
    _validar_real("b", b)
    if b == 0:
        raise ValueError("b debe ser positivo.")
    for nombre, valor in (("generacion", generacion), ("max_generaciones", max_generaciones)):
        if isinstance(valor, (bool, np.bool_)) or not isinstance(valor, (int, np.integer)):
            raise ValueError(f"{nombre} debe ser entero.")
    if max_generaciones <= 0 or not 0 <= generacion <= max_generaciones:
        raise ValueError("Se requiere T > 0 y 0 <= t <= T.")
    if generacion == max_generaciones:
        return hijo

    generador = rng if rng is not None else np.random.default_rng()
    seleccionados = generador.random(num_genes()) < p_mut
    cantidad = seleccionados.sum()
    hacia_uno = generador.random(cantidad) < 0.5
    r = generador.random(cantidad)
    valores = hijo[seleccionados]
    distancia = np.where(hacia_uno, 1.0 - valores, valores)
    exponente = (1.0 - generacion / max_generaciones) ** b
    delta = distancia * (1.0 - r ** exponente)
    hijo[seleccionados] += np.where(hacia_uno, delta, -delta)
    return _recortar_y_validar(hijo)
