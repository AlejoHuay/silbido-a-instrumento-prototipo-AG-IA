"""Configuración reproducible del algoritmo genético del Rol 4."""

from __future__ import annotations

from dataclasses import dataclass, replace


SEMILLAS_EXPERIMENTALES = (42, 101, 2024, 7, 999)
TAMANOS_POBLACION_EXPERIMENTALES = (20, 50, 100)


def _validar_entero(nombre: str, valor: int, minimo: int) -> None:
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < minimo:
        raise ValueError(f"{nombre} debe ser un entero >= {minimo}.")


def _validar_probabilidad(nombre: str, valor: float) -> None:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError(f"{nombre} debe ser un número entre 0 y 1.")
    if not 0.0 <= float(valor) <= 1.0:
        raise ValueError(f"{nombre} debe estar entre 0 y 1.")


@dataclass(frozen=True)
class ConfiguracionAG:
    """Hiperparámetros de una corrida del AG.

    Los valores por defecto corresponden al acuerdo del Día 1. Las tasas
    quedan declaradas desde ahora para que el Rol 3 pueda conectarlas a sus
    operadores del Día 2 sin introducir variables globales ocultas.
    """

    tam_poblacion: int = 50
    max_generaciones: int = 50
    elitismo: int = 2
    tam_torneo: int = 3
    probabilidad_cruce: float = 0.90
    probabilidad_mutacion: float = 0.05
    paciencia_estancamiento: int = 10
    tolerancia_mejora: float = 1e-4
    semilla: int = 42

    def __post_init__(self) -> None:
        _validar_entero("tam_poblacion", self.tam_poblacion, 3)
        _validar_entero("max_generaciones", self.max_generaciones, 1)
        _validar_entero("elitismo", self.elitismo, 0)
        _validar_entero("tam_torneo", self.tam_torneo, 1)
        _validar_entero(
            "paciencia_estancamiento",
            self.paciencia_estancamiento,
            1,
        )
        _validar_entero("semilla", self.semilla, 0)
        _validar_probabilidad(
            "probabilidad_cruce", self.probabilidad_cruce
        )
        _validar_probabilidad(
            "probabilidad_mutacion", self.probabilidad_mutacion
        )

        if self.elitismo >= self.tam_poblacion:
            raise ValueError("elitismo debe ser menor que tam_poblacion.")
        if self.tam_torneo > self.tam_poblacion:
            raise ValueError("tam_torneo no puede superar tam_poblacion.")
        if (
            isinstance(self.tolerancia_mejora, bool)
            or not isinstance(self.tolerancia_mejora, (int, float))
            or self.tolerancia_mejora < 0
        ):
            raise ValueError("tolerancia_mejora debe ser un número >= 0.")


def crear_plan_experimental() -> list[ConfiguracionAG]:
    """Construye las 12 configuraciones factoriales acordadas para el Día 3.

    Factores: tamaño de población (20, 50, 100), elitismo (1, 2) y
    probabilidad de mutación (0.02, 0.08). Cada configuración conserva los
    demás valores del contrato. Las cinco semillas se aplicarán como réplicas,
    no como configuraciones adicionales.
    """

    base = ConfiguracionAG()
    return [
        replace(
            base,
            tam_poblacion=tam_poblacion,
            elitismo=elitismo,
            probabilidad_mutacion=probabilidad_mutacion,
        )
        for tam_poblacion in TAMANOS_POBLACION_EXPERIMENTALES
        for elitismo in (1, 2)
        for probabilidad_mutacion in (0.02, 0.08)
    ]
