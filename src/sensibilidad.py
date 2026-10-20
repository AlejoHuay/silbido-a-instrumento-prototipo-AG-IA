"""Rol 1 — Día 3: Análisis de sensibilidad unidimensional (1D).

Mide la respuesta de las funciones de aptitud (STFT y Croma) ante la variación
individual de cada uno de los 8 genes del cromosoma, manteniendo los restantes
constantes en los valores de referencia acordados para la flauta traversa.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import soundfile as sf

from .extraccion import cargar_melodia_csv
from .fitness import evaluar_audio
from .representacion import (
    decodificar,
    num_genes,
    obtener_limites_fisicos,
    obtener_nombres_genes,
    obtener_valores_default,
    validar_individuo,
)
from .sintesis import sintetizar_instrumento


def barrido_sensibilidad_gen(
    indice_gen: int,
    notas: Sequence[int] | np.ndarray,
    duraciones: Sequence[float] | np.ndarray,
    referencia_audio: np.ndarray,
    gen_base: np.ndarray | None = None,
    num_puntos: int = 51,
) -> pd.DataFrame:
    """Realiza un barrido 1D para un gen específico en el rango normalizado [0, 1].

    Parámetros
    ----------
    indice_gen : int
        Índice del gen a variar (0 a 7).
    notas : Sequence[int] | np.ndarray
        Secuencia de notas MIDI de la melodía.
    duraciones : Sequence[float] | np.ndarray
        Secuencia de duraciones en segundos.
    referencia_audio : np.ndarray
        Arreglo 1D del audio de flauta de referencia.
    gen_base : np.ndarray | None
        Cromosoma normalizado base. Si es None, usa el valor default de flauta.
    num_puntos : int
        Cantidad de puntos equiespaciados en [0.0, 1.0].

    Retorna
    -------
    pd.DataFrame
        Tabla con valores normalizados, físicos, error STFT, fitness STFT y Croma.
    """
    if not (0 <= indice_gen < num_genes()):
        raise ValueError(f"indice_gen debe estar en el rango [0, {num_genes() - 1}].")
    if num_puntos < 2:
        raise ValueError("num_puntos debe ser al menos 2.")

    if gen_base is None:
        base = np.asarray(obtener_valores_default(normalizado=True), dtype=np.float64)
    else:
        base = np.asarray(gen_base, dtype=np.float64).copy()
        valido, msg = validar_individuo(base)
        if not valido:
            raise ValueError(f"gen_base inválido: {msg}")

    nombres = obtener_nombres_genes()
    nombre_gen = nombres[indice_gen]
    valores_norm = np.linspace(0.0, 1.0, num_puntos)

    registros = []
    for val_norm in valores_norm:
        cromosoma = base.copy()
        cromosoma[indice_gen] = float(val_norm)

        fenotipo = decodificar(cromosoma)
        val_fisico = fenotipo[nombre_gen]

        audio = sintetizar_instrumento(notas, duraciones, cromosoma)
        metricas = evaluar_audio(audio, referencia_audio)

        registros.append({
            "gen_indice": indice_gen,
            "gen_nombre": nombre_gen,
            "valor_normalizado": float(val_norm),
            "valor_fisico": float(val_fisico),
            "error_stft_db": float(metricas["error_stft_db"]),
            "fitness_stft": float(metricas["fitness_stft"]),
            "fitness_croma": float(metricas["fitness_croma"]),
        })

    return pd.DataFrame(registros)


def barrido_sensibilidad_todos(
    notas: Sequence[int] | np.ndarray,
    duraciones: Sequence[float] | np.ndarray,
    referencia_audio: np.ndarray,
    gen_base: np.ndarray | None = None,
    num_puntos: int = 51,
) -> pd.DataFrame:
    """Ejecuta el barrido 1D para los 8 genes del cromosoma."""
    dfs = []
    for i in range(num_genes()):
        df_gen = barrido_sensibilidad_gen(
            indice_gen=i,
            notas=notas,
            duraciones=duraciones,
            referencia_audio=referencia_audio,
            gen_base=gen_base,
            num_puntos=num_puntos,
        )
        dfs.append(df_gen)

    return pd.concat(dfs, ignore_index=True)


def calcular_ranking_sensibilidad(df_sensibilidad: pd.DataFrame) -> pd.DataFrame:
    """Calcula métricas resumen de sensibilidad (rango, desviación y gradiente) por gen."""
    filas = []
    for nombre, grupo in df_sensibilidad.groupby("gen_nombre", sort=False):
        idx = int(grupo["gen_indice"].iloc[0])

        f_stft = grupo["fitness_stft"].to_numpy()
        f_croma = grupo["fitness_croma"].to_numpy()
        err_db = grupo["error_stft_db"].to_numpy()
        x_norm = grupo["valor_normalizado"].to_numpy()

        delta_stft = float(np.ptp(f_stft))
        std_stft = float(np.std(f_stft))
        delta_croma = float(np.ptp(f_croma))
        std_croma = float(np.std(f_croma))
        delta_err_db = float(np.ptp(err_db))

        # Gradiente numérico máximo respecto al espacio normalizado
        grad_stft_max = float(np.max(np.abs(np.gradient(f_stft, x_norm))))
        grad_croma_max = float(np.max(np.abs(np.gradient(f_croma, x_norm))))

        # Clasificación heurística de sensibilidad STFT
        if delta_stft >= 0.10:
            categoria_stft = "Hipersensible"
        elif delta_stft >= 0.02:
            categoria_stft = "Sensibilidad Moderada"
        else:
            categoria_stft = "Robusto / Insensible"

        filas.append({
            "gen_indice": idx,
            "gen_nombre": nombre,
            "delta_fitness_stft": delta_stft,
            "std_fitness_stft": std_stft,
            "max_grad_stft": grad_stft_max,
            "delta_error_db": delta_err_db,
            "delta_fitness_croma": delta_croma,
            "std_fitness_croma": std_croma,
            "max_grad_croma": grad_croma_max,
            "categoria_stft": categoria_stft,
        })

    df_rank = pd.DataFrame(filas)
    df_rank.sort_values(by="delta_fitness_stft", ascending=False, inplace=True)
    df_rank.reset_index(drop=True, inplace=True)
    df_rank["ranking_stft"] = np.arange(1, len(df_rank) + 1)
    return df_rank


def generar_figura_curvas_1d(
    df_sensibilidad: pd.DataFrame,
    ruta_guardado: str | Path | None = None,
) -> plt.Figure:
    """Genera una grilla 2x4 con las curvas de respuesta de fitness de cada gen."""
    nombres = obtener_nombres_genes()
    fig, axes = plt.subplots(2, 4, figsize=(16, 8), sharey=False)
    axes = axes.flatten()

    for i, nombre in enumerate(nombres):
        ax = axes[i]
        sub = df_sensibilidad[df_sensibilidad["gen_nombre"] == nombre]

        ax.plot(
            sub["valor_normalizado"],
            sub["fitness_stft"],
            label="Fitness STFT (dB)",
            color="#1f77b4",
            linewidth=2,
        )
        ax.plot(
            sub["valor_normalizado"],
            sub["fitness_croma"],
            label="Fitness Croma",
            color="#ff7f0e",
            linestyle="--",
            linewidth=1.8,
        )

        ax.set_title(f"Gen {i}: {nombre}", fontsize=11, fontweight="bold")
        ax.set_xlabel("Valor Normalizado [0, 1]", fontsize=9)
        ax.set_ylabel("Fitness", fontsize=9)
        ax.grid(True, linestyle=":", alpha=0.6)
        if i == 0:
            ax.legend(fontsize=8, loc="best")

    plt.tight_layout()
    if ruta_guardado:
        Path(ruta_guardado).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(ruta_guardado, dpi=300)
    return fig


def generar_figura_tornado(
    df_ranking: pd.DataFrame,
    ruta_guardado: str | Path | None = None,
) -> plt.Figure:
    """Genera un gráfico de barras horizontales (tipo tornado/impacto) ordenado por sensibilidad."""
    df_sorted = df_ranking.sort_values(by="delta_fitness_stft", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    barras = ax.barh(
        df_sorted["gen_nombre"],
        df_sorted["delta_fitness_stft"],
        color="#2ca02c",
        alpha=0.85,
        edgecolor="#1b611b",
    )

    ax.set_xlabel(r"Impacto en Fitness ($\Delta \text{Fitness}_{\text{STFT}} = \max - \min$)", fontsize=10)
    ax.set_title("Ranking de Sensibilidad de Genes (Impacto en Fitness Espectral)", fontsize=12, fontweight="bold")
    ax.grid(True, axis="x", linestyle="--", alpha=0.7)

    for barra in barras:
        ancho = barra.get_width()
        ax.text(
            ancho + 0.003,
            barra.get_y() + barra.get_height() / 2,
            f"{ancho:.4f}",
            va="center",
            ha="left",
            fontsize=9,
            fontweight="bold",
        )

    ax.set_xlim(0, max(df_sorted["delta_fitness_stft"]) * 1.15)
    plt.tight_layout()
    if ruta_guardado:
        Path(ruta_guardado).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(ruta_guardado, dpi=300)
    return fig
