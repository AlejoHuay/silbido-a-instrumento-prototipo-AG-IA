"""Registro y resumen de evaluaciones del Rol 5."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


def _valor_finito(
    nombre: str,
    valor: Any,
    *,
    permitir_none: bool = False,
) -> float | None:
    if valor is None and permitir_none:
        return None
    if isinstance(valor, (bool, np.bool_)):
        raise ValueError(f"{nombre} debe ser un número finito.")
    try:
        resultado = float(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{nombre} debe ser un número finito.") from exc
    if not math.isfinite(resultado):
        raise ValueError(f"{nombre} debe ser un número finito.")
    return resultado


def _entero_no_negativo(nombre: str, valor: Any) -> int | None:
    if valor is None:
        return None
    if (
        isinstance(valor, (bool, np.bool_))
        or not isinstance(valor, (int, np.integer))
        or valor < 0
    ):
        raise ValueError(f"{nombre} debe ser un entero >= 0 o None.")
    return int(valor)


def construir_registro_corrida(
    *,
    metodo: str,
    semilla: int,
    configuracion: Any,
    resultado: Mapping[str, Any],
    tiempo_s: float,
    metrica: str | None = None,
) -> dict[str, Any]:
    """Normaliza la salida de una corrida para comparación y exportación."""

    if not isinstance(metodo, str) or not metodo.strip():
        raise ValueError("metodo debe ser una cadena no vacía.")
    if (
        isinstance(semilla, (bool, np.bool_))
        or not isinstance(semilla, (int, np.integer))
        or semilla < 0
    ):
        raise ValueError("semilla debe ser un entero >= 0.")
    if not isinstance(resultado, Mapping):
        raise ValueError("resultado debe ser un mapping.")
    if "mejor_fitness" not in resultado:
        raise ValueError("resultado debe contener mejor_fitness.")

    if is_dataclass(configuracion) and not isinstance(configuracion, type):
        configuracion_dict = asdict(configuracion)
    elif isinstance(configuracion, Mapping):
        configuracion_dict = dict(configuracion)
    else:
        raise ValueError("configuracion debe ser un dataclass o un mapping.")

    metrica_registro = (
        metrica
        if metrica is not None
        else resultado.get("metrica", configuracion_dict.get("metrica"))
    )
    if metrica_registro is not None and (
        not isinstance(metrica_registro, str) or not metrica_registro.strip()
    ):
        raise ValueError("metrica debe ser una cadena no vacía o None.")

    mejor_individuo = resultado.get("mejor_individuo")
    if mejor_individuo is None:
        mejor_individuo_json = None
    else:
        genes = np.asarray(mejor_individuo, dtype=np.float64)
        if genes.ndim != 1 or not np.all(np.isfinite(genes)):
            raise ValueError("mejor_individuo debe ser un vector finito.")
        mejor_individuo_json = json.dumps(genes.tolist())

    motivo = resultado.get("motivo_parada")
    if motivo is not None and not isinstance(motivo, str):
        raise ValueError("motivo_parada debe ser una cadena o None.")

    return {
        "metodo": metodo.strip(),
        "metrica": metrica_registro,
        "semilla": int(semilla),
        "mejor_fitness": _valor_finito(
            "mejor_fitness", resultado["mejor_fitness"]
        ),
        "error_stft_db": _valor_finito(
            "error_stft_db",
            resultado.get("error_stft_db"),
            permitir_none=True,
        ),
        "generaciones_ejecutadas": _entero_no_negativo(
            "generaciones_ejecutadas",
            resultado.get("generaciones_ejecutadas"),
        ),
        "evaluaciones": _entero_no_negativo(
            "evaluaciones", resultado.get("evaluaciones")
        ),
        "tiempo_s": _valor_finito("tiempo_s", tiempo_s),
        "motivo_parada": motivo,
        "mejor_individuo_json": mejor_individuo_json,
        "configuracion_json": json.dumps(
            configuracion_dict,
            sort_keys=True,
            ensure_ascii=False,
        ),
    }


def guardar_registros_csv(
    registros: Sequence[Mapping[str, Any]],
    ruta: str | Path,
    *,
    anexar: bool = False,
) -> Path:
    """Escribe registros sin sobrescribir; anexar debe solicitarse explícitamente."""

    if not registros:
        raise ValueError("Se requiere al menos un registro para crear un CSV.")

    campos = list(registros[0].keys())
    if not campos:
        raise ValueError("Los registros deben tener al menos un campo.")
    for indice, registro in enumerate(registros):
        if set(registro.keys()) != set(campos):
            raise ValueError(
                f"El registro {indice} no contiene los mismos campos que el primero."
            )

    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)

    if anexar and destino.exists():
        with destino.open("r", newline="", encoding="utf-8") as archivo:
            campos_existentes = next(csv.reader(archivo), [])
        if campos_existentes != campos:
            raise ValueError(
                "El encabezado existente no coincide con los campos del registro."
            )
        modo = "a"
        escribir_encabezado = False
    else:
        modo = "x"
        escribir_encabezado = True

    with destino.open(modo, newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=campos,
            extrasaction="raise",
        )
        if escribir_encabezado:
            escritor.writeheader()
        escritor.writerows(registros)

    return destino


def resumir_corridas(
    registros: Sequence[Mapping[str, Any]],
    *,
    agrupar_por: Sequence[str] = ("metodo",),
    metrica: str = "mejor_fitness",
) -> list[dict[str, Any]]:
    """Calcula media y desviación estándar muestral por grupo."""

    if not registros:
        raise ValueError("Se requiere al menos un registro.")
    if not agrupar_por:
        raise ValueError("agrupar_por no puede estar vacío.")

    grupos: dict[tuple[Any, ...], list[float]] = {}
    for indice, registro in enumerate(registros):
        faltantes = [
            campo
            for campo in (*agrupar_por, metrica)
            if campo not in registro
        ]
        if faltantes:
            raise ValueError(
                f"Al registro {indice} le faltan campos: {faltantes}."
            )
        clave = tuple(registro[campo] for campo in agrupar_por)
        try:
            hash(clave)
        except TypeError as exc:
            raise ValueError("Los campos de agrupación deben ser hashables.") from exc
        valor = _valor_finito(metrica, registro[metrica])
        grupos.setdefault(clave, []).append(float(valor))

    resumen: list[dict[str, Any]] = []
    for clave, valores in grupos.items():
        fila = dict(zip(agrupar_por, clave))
        fila.update(
            {
                "metrica": metrica,
                "n": len(valores),
                "media": float(np.mean(valores)),
                "desviacion_estandar": (
                    float(np.std(valores, ddof=1))
                    if len(valores) > 1
                    else None
                ),
            }
        )
        resumen.append(fila)
    return resumen
