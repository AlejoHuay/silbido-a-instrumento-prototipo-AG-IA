"""Genera curvas de convergencia desde los checkpoints del factorial.

Este script es exclusivamente de posprocesamiento: lee los historiales JSON
existentes y no ejecuta el algoritmo genetico, el fitness ni el baseline.
Cada lamina contiene las 12 configuraciones de una metrica y las cinco
semillas registradas por configuracion.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from io import StringIO
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


RAIZ_REPOSITORIO = Path(__file__).resolve().parents[1]
RUTA_FACTORIAL = (
    RAIZ_REPOSITORIO
    / "resultados/rol5/dia3_factorial/ejecucion_20261021T184758Z_c5dc431"
)
RUTA_SALIDA = RAIZ_REPOSITORIO / "resultados/rol4/convergencia_factorial"
METRICAS = ("stft", "croma")
POBLACIONES = (20, 50, 100)
COLUMNAS = ((1, 0.02), (1, 0.08), (2, 0.02), (2, 0.08))
SEMILLAS = (42, 101, 2024, 7, 999)


def _finito(valor: object, campo: str, ruta: Path) -> float:
    numero = float(valor)
    if not np.isfinite(numero):
        raise ValueError(f"{ruta.name}: {campo} no es finito: {numero}")
    return numero


def cargar_historiales(
    ruta_factorial: Path = RUTA_FACTORIAL,
) -> dict[str, dict[tuple[int, int, float], dict[int, list[dict]]]]:
    """Carga y valida las 120 trayectorias AG ya guardadas."""
    datos: dict[str, dict[tuple[int, int, float], dict[int, list[dict]]]] = {}
    configuraciones_esperadas = {
        (poblacion, elitismo, mutacion)
        for poblacion in POBLACIONES
        for elitismo, mutacion in COLUMNAS
    }

    for metrica in METRICAS:
        agrupados: dict[tuple[int, int, float], dict[int, list[dict]]] = defaultdict(dict)
        rutas = sorted((ruta_factorial / metrica).glob("ag_*.json"))
        if len(rutas) != 60:
            raise ValueError(
                f"{metrica}: se esperaban 60 checkpoints AG y se encontraron {len(rutas)}."
            )

        for ruta in rutas:
            with ruta.open("r", encoding="utf-8") as archivo:
                registro = json.load(archivo)
            if registro.get("metodo") != "algoritmo_genetico":
                raise ValueError(f"{ruta.name}: metodo inesperado.")
            if registro.get("metrica") != metrica:
                raise ValueError(f"{ruta.name}: metrica mezclada.")

            config = registro["configuracion"]
            identidad = (
                int(config["tam_poblacion"]),
                int(config["elitismo"]),
                float(config["probabilidad_mutacion"]),
            )
            semilla = int(registro["semilla"])
            historial = registro["resultado_completo"]["historial"]
            if not historial:
                raise ValueError(f"{ruta.name}: historial vacio.")
            generaciones = [int(fila["generacion"]) for fila in historial]
            if generaciones != list(range(len(historial))):
                raise ValueError(f"{ruta.name}: generaciones incompletas o desordenadas.")
            maximos = [
                _finito(fila["fitness_maximo"], "fitness_maximo", ruta)
                for fila in historial
            ]
            if np.any(np.diff(maximos) < -1e-12):
                raise ValueError(f"{ruta.name}: el mejor fitness disminuye.")
            for fila in historial:
                _finito(fila["fitness_medio"], "fitness_medio", ruta)
                _finito(fila["desviacion_fitness"], "desviacion_fitness", ruta)
                _finito(fila["diversidad_genetica"], "diversidad_genetica", ruta)
            if semilla in agrupados[identidad]:
                raise ValueError(f"{metrica}: semilla duplicada para {identidad}.")
            agrupados[identidad][semilla] = historial

        if set(agrupados) != configuraciones_esperadas:
            raise ValueError(f"{metrica}: matriz de configuraciones incompleta.")
        for identidad, replicas in agrupados.items():
            if set(replicas) != set(SEMILLAS):
                raise ValueError(f"{metrica}: semillas incompletas para {identidad}.")
        datos[metrica] = dict(agrupados)
    return datos


def graficar_metrica(
    metrica: str,
    configuraciones: dict[tuple[int, int, float], dict[int, list[dict]]],
):
    """Crea una lamina 3x4 sin prolongar artificialmente las corridas."""
    figura, ejes = plt.subplots(
        len(POBLACIONES), len(COLUMNAS), figsize=(15.4, 10.2),
        sharex=True, sharey=True,
    )
    colores = plt.get_cmap("tab10").colors
    manejadores = []
    etiquetas = []

    for fila, poblacion in enumerate(POBLACIONES):
        for columna, (elitismo, mutacion) in enumerate(COLUMNAS):
            eje = ejes[fila, columna]
            replicas = configuraciones[(poblacion, elitismo, mutacion)]
            for indice, semilla in enumerate(SEMILLAS):
                historial = replicas[semilla]
                generaciones = [int(punto["generacion"]) for punto in historial]
                maximos = [float(punto["fitness_maximo"]) for punto in historial]
                linea, = eje.plot(
                    generaciones, maximos, color=colores[indice], alpha=0.58,
                    linewidth=1.15,
                )
                if fila == 0 and columna == 0:
                    manejadores.append(linea)
                    etiquetas.append(f"Semilla {semilla}")

            ultima_comun = min(len(historial) for historial in replicas.values())
            matriz_comun = np.array([
                [
                    float(punto["fitness_maximo"])
                    for punto in replicas[semilla][:ultima_comun]
                ]
                for semilla in SEMILLAS
            ])
            media, = eje.plot(
                range(ultima_comun), matriz_comun.mean(axis=0), color="#111827",
                linewidth=2.6, zorder=5,
            )
            if fila == 0 and columna == 0:
                manejadores.append(media)
                etiquetas.append("Media (tramo comun 5/5)")

            eje.set_title(
                f"N={poblacion} · E={elitismo} · pm={mutacion:.2f}", fontsize=10
            )
            eje.grid(alpha=0.2)
            eje.set_axisbelow(True)
            if fila == len(POBLACIONES) - 1:
                eje.set_xlabel("Generacion")
            if columna == 0:
                eje.set_ylabel("Mejor fitness")

    figura.suptitle(
        f"Convergencia factorial — {metrica.upper()}",
        fontsize=20, fontweight="bold", y=0.985,
    )
    figura.text(
        0.5, 0.946,
        "12 configuraciones × 5 semillas · lineas terminan en la parada real de cada corrida",
        ha="center", fontsize=11, color="#4b5563",
    )
    figura.legend(
        manejadores, etiquetas, loc="lower center", ncol=6, frameon=False,
        bbox_to_anchor=(0.5, 0.014), fontsize=9,
    )
    figura.text(
        0.5, 0.004,
        "Posprocesamiento de checkpoints guardados; no se repitieron experimentos ni evaluaciones de fitness.",
        ha="center", fontsize=8.5, color="#6b7280",
    )
    figura.tight_layout(rect=(0.03, 0.065, 0.99, 0.925))
    return figura


def guardar_svg(figura, ruta: Path, sobrescribir: bool = False) -> None:
    """Guarda una figura; evita reemplazos salvo autorizacion explicita."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    modo = "w" if sobrescribir else "x"
    buffer = StringIO()
    try:
        figura.savefig(buffer, format="svg", bbox_inches="tight")
        contenido = "\n".join(linea.rstrip() for linea in buffer.getvalue().splitlines())
        with ruta.open(modo, encoding="utf-8") as archivo:
            archivo.write(contenido + "\n")
    finally:
        plt.close(figura)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--factorial", type=Path, default=RUTA_FACTORIAL,
        help="Carpeta de la ejecucion factorial ya guardada.",
    )
    parser.add_argument(
        "--salida", type=Path, default=RUTA_SALIDA,
        help="Carpeta donde se guardaran las dos laminas SVG.",
    )
    parser.add_argument(
        "--sobrescribir", action="store_true",
        help="Permite reemplazar figuras existentes.",
    )
    args = parser.parse_args()

    datos = cargar_historiales(args.factorial)
    for metrica in METRICAS:
        destino = args.salida / f"convergencia_{metrica}_12_configuraciones.svg"
        guardar_svg(
            graficar_metrica(metrica, datos[metrica]),
            destino,
            sobrescribir=args.sobrescribir,
        )
        print(f"[{metrica.upper()}] curva guardada en: {destino}")
    print("Se leyeron 120 historiales guardados; no se ejecutaron corridas ni fitness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
