"""Rol 1: Representación del cromosoma, codificación y análisis del espacio."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np


@dataclass(frozen=True)
class GenSpec:
    nombre: str
    unidad: str
    min_val: float
    max_val: float
    default: float
    descripcion: str


GENES_SCHEMA: list[GenSpec] = [
    GenSpec(
        nombre="amp_arm1",
        unidad="amplitud rel.",
        min_val=0.10,
        max_val=1.00,
        default=0.90,
        descripcion="Amplitud de la frecuencia fundamental (f0). En la flauta es dominante.",
    ),
    GenSpec(
        nombre="amp_arm2",
        unidad="amplitud rel.",
        min_val=0.00,
        max_val=0.80,
        default=0.25,
        descripcion="Amplitud del segundo armónico (2*f0). Aporta brillo moderado.",
    ),
    GenSpec(
        nombre="amp_arm3",
        unidad="amplitud rel.",
        min_val=0.00,
        max_val=0.50,
        default=0.08,
        descripcion="Amplitud del tercer armónico (3*f0). Sutil en registro medio/agudo.",
    ),
    GenSpec(
        nombre="ataque_s",
        unidad="segundos",
        min_val=0.005,
        max_val=0.250,
        default=0.050,
        descripcion="Tiempo de ataque ADSR. La flauta tiene un transitorio suave de embocadura.",
    ),
    GenSpec(
        nombre="decaimiento_s",
        unidad="segundos",
        min_val=0.005,
        max_val=0.300,
        default=0.080,
        descripcion="Tiempo de decaimiento ADSR hasta el nivel de sostenido.",
    ),
    GenSpec(
        nombre="sostenido_rel",
        unidad="amplitud rel.",
        min_val=0.10,
        max_val=1.00,
        default=0.80,
        descripcion="Nivel de sostenido ADSR mientras se mantiene la columna de aire.",
    ),
    GenSpec(
        nombre="relajacion_s",
        unidad="segundos",
        min_val=0.005,
        max_val=0.300,
        default=0.060,
        descripcion="Tiempo de relajación ADSR tras cortar la columna de aire.",
    ),
    GenSpec(
        nombre="ruido_soplo",
        unidad="amplitud rel.",
        min_val=0.00,
        max_val=0.25,
        default=0.04,
        descripcion="Amplitud de turbulencia de aire (breath noise) en la embocadura.",
    ),
]


def num_genes() -> int:
    return len(GENES_SCHEMA)


def obtener_nombres_genes() -> list[str]:
    return [g.nombre for g in GENES_SCHEMA]


def obtener_limites_fisicos() -> tuple[np.ndarray, np.ndarray]:
    mins = np.array([g.min_val for g in GENES_SCHEMA], dtype=np.float64)
    maxs = np.array([g.max_val for g in GENES_SCHEMA], dtype=np.float64)
    return mins, maxs


def obtener_valores_default(normalizado: bool = False) -> np.ndarray | dict[str, float]:
    if normalizado:
        mins, maxs = obtener_limites_fisicos()
        defs = np.array([g.default for g in GENES_SCHEMA], dtype=np.float64)
        return (defs - mins) / (maxs - mins)
    return {g.nombre: g.default for g in GENES_SCHEMA}


def generar_individuo_aleatorio(normalizado: bool = True, rng: np.random.Generator | None = None) -> np.ndarray:
    gen = rng if rng is not None else np.random.default_rng()
    n = num_genes()
    valores_norm = gen.uniform(0.0, 1.0, size=n)
    if normalizado:
        return valores_norm
    mins, maxs = obtener_limites_fisicos()
    return mins + valores_norm * (maxs - mins)


def generar_poblacion_inicial(tam_poblacion: int, normalizado: bool = True, rng: np.random.Generator | None = None) -> np.ndarray:
    gen = rng if rng is not None else np.random.default_rng()
    n = num_genes()
    matriz_norm = gen.uniform(0.0, 1.0, size=(tam_poblacion, n))
    if normalizado:
        return matriz_norm
    mins, maxs = obtener_limites_fisicos()
    return mins + matriz_norm * (maxs - mins)


def codificar(fenotipo: dict[str, float] | Sequence[float]) -> np.ndarray:
    mins, maxs = obtener_limites_fisicos()
    nombres = obtener_nombres_genes()

    if isinstance(fenotipo, dict):
        valores_fisicos = np.array([fenotipo[nombre] for nombre in nombres], dtype=np.float64)
    else:
        valores_fisicos = np.asarray(fenotipo, dtype=np.float64)
        if len(valores_fisicos) != len(nombres):
            raise ValueError(f"Longitud incorrecta: esperado {len(nombres)}, recibido {len(valores_fisicos)}")

    genotipo = (valores_fisicos - mins) / (maxs - mins)
    return np.clip(genotipo, 0.0, 1.0)


def decodificar(cromosoma: np.ndarray | Sequence[float]) -> dict[str, float]:
    crom_arr = restringir_limites(np.asarray(cromosoma, dtype=np.float64), normalizado=True)
    mins, maxs = obtener_limites_fisicos()
    valores_fisicos = mins + crom_arr * (maxs - mins)
    return {g.nombre: float(val) for g, val in zip(GENES_SCHEMA, valores_fisicos)}


def decodificar_a_array(cromosoma: np.ndarray | Sequence[float]) -> np.ndarray:
    crom_arr = restringir_limites(np.asarray(cromosoma, dtype=np.float64), normalizado=True)
    mins, maxs = obtener_limites_fisicos()
    return mins + crom_arr * (maxs - mins)


def restringir_limites(cromosoma: np.ndarray, normalizado: bool = True) -> np.ndarray:
    if normalizado:
        return np.clip(cromosoma, 0.0, 1.0)
    mins, maxs = obtener_limites_fisicos()
    return np.clip(cromosoma, mins, maxs)


def validar_individuo(cromosoma: np.ndarray, normalizado: bool = True) -> tuple[bool, str]:
    crom = np.asarray(cromosoma, dtype=np.float64)
    if crom.ndim != 1 or len(crom) != num_genes():
        return False, f"Forma inválida: esperado ({num_genes()},), recibido {crom.shape}"

    if normalizado:
        if np.any(np.isnan(crom)) or np.any(np.isinf(crom)):
            return False, "Cromosoma contiene NaN o Infinitos"
        if np.any(crom < 0.0) or np.any(crom > 1.0):
            return False, f"Genes normalizados fuera del intervalo [0, 1]: min={crom.min()}, max={crom.max()}"
        valores = decodificar(crom)
    else:
        mins, maxs = obtener_limites_fisicos()
        if np.any(crom < mins) or np.any(crom > maxs):
            return False, "Genes físicos fuera de los límites especificados"
        valores = {g.nombre: float(v) for g, v in zip(GENES_SCHEMA, crom)}

    duracion_minima_envolvente = valores["ataque_s"] + valores["decaimiento_s"] + valores["relajacion_s"]
    if duracion_minima_envolvente > 1.0:
        return False, f"Envolvente ADSR excede la duración física razonable de una nota individual ({duracion_minima_envolvente:.3f} s > 1.0 s)"

    return True, "Válido"


def calcular_tamano_espacio_busqueda(resolucion: float = 1e-3) -> dict[str, Any]:
    mins, maxs = obtener_limites_fisicos()
    estados_por_gen: list[int] = []

    for min_v, max_v in zip(mins, maxs):
        rango = max_v - min_v
        estados = int(math.floor(rango / resolucion)) + 1
        estados_por_gen.append(estados)

    espacio_total = 1
    for e in estados_por_gen:
        espacio_total *= e

    bits_necesarios = sum(math.log2(e) for e in estados_por_gen)
    
    return {
        "num_genes": num_genes(),
        "resolucion_utilizada": resolucion,
        "estados_por_gen": dict(zip(obtener_nombres_genes(), estados_por_gen)),
        "estados_totales": espacio_total,
        "estados_totales_notacion_cientifica": f"{espacio_total:.2e}",
        "bits_equivalentes": bits_necesarios,
        "tiempo_estimado_fuerza_bruta_segundos_a_1000_evals_por_seg": espacio_total / 1000.0,
        "tiempo_estimado_anos": (espacio_total / 1000.0) / (3600 * 24 * 365.25),
    }


def probar_inversion_codificacion(tolerancia: float = 1e-5) -> bool:
    valores_originales = {g.nombre: g.default for g in GENES_SCHEMA}
    crom_norm = codificar(valores_originales)
    valores_recuperados = decodificar(crom_norm)

    for nombre, val_orig in valores_originales.items():
        val_rec = valores_recuperados[nombre]
        if abs(val_orig - val_rec) > tolerancia:
            return False
    return True
