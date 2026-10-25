"""Rol 5 — análisis reproducible de resultados guardados del Día 3.

Este módulo no ejecuta el AG ni vuelve a evaluar individuos. Lee únicamente
los CSV ya guardados del factorial y sus comparaciones pareadas.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import f as distribucion_f


RAIZ_REPOSITORIO = Path(__file__).resolve().parents[1]
RUTA_FACTORIAL = (
    RAIZ_REPOSITORIO
    / "resultados/rol5/dia3_factorial/ejecucion_20261021T184758Z_c5dc431"
)
METRICAS = ("stft", "croma")
SEMILLAS = (42, 101, 2024, 7, 999)


def _leer_csv(ruta: Path) -> list[dict[str, str]]:
    with ruta.open("r", newline="", encoding="utf-8") as archivo:
        return list(csv.DictReader(archivo))


def _numero(fila: dict[str, str], campo: str) -> float:
    valor = float(fila[campo])
    if not np.isfinite(valor):
        raise ValueError(f"{campo} contiene un valor no finito: {valor}")
    return valor


def _configuracion(fila: dict[str, str]) -> dict:
    return json.loads(fila["configuracion_json"])


def _identidad(fila: dict[str, str]) -> tuple[int, int, float, int]:
    config = _configuracion(fila)
    return (
        int(config["tam_poblacion"]),
        int(config["elitismo"]),
        float(config["probabilidad_mutacion"]),
        int(fila["semilla"]),
    )


def cargar_y_validar(ruta_factorial: Path = RUTA_FACTORIAL) -> dict[str, dict]:
    """Carga los resultados existentes y comprueba estructura y emparejamiento."""
    datos: dict[str, dict] = {}
    identidades_esperadas = {
        (n, elite, pm, semilla)
        for n in (20, 50, 100)
        for elite in (1, 2)
        for pm in (0.02, 0.08)
        for semilla in SEMILLAS
    }

    for metrica in METRICAS:
        carpeta = ruta_factorial / metrica
        ag = _leer_csv(carpeta / "corridas_ag.csv")
        baseline = _leer_csv(carpeta / "corridas_baseline.csv")
        pareadas = _leer_csv(carpeta / "comparacion_pareada.csv")
        if not (len(ag) == len(baseline) == len(pareadas) == 60):
            raise ValueError(f"{metrica}: se esperaban 60 registros de cada tipo.")

        mapas = []
        for nombre, filas in (("AG", ag), ("baseline", baseline)):
            ids = [_identidad(fila) for fila in filas]
            if len(set(ids)) != 60 or set(ids) != identidades_esperadas:
                raise ValueError(f"{metrica}: matriz de identidades inválida en {nombre}.")
            for fila in filas:
                if fila["metrica"] != metrica:
                    raise ValueError(f"{metrica}: métrica mezclada en {nombre}.")
                _numero(fila, "mejor_fitness")
                _numero(fila, "tiempo_s")
                if fila["combinacion_operadores"] != "B":
                    raise ValueError(f"{metrica}: operador inesperado.")
            mapas.append({_identidad(fila): fila for fila in filas})

        ag_por_id, baseline_por_id = mapas
        if len(pareadas) != 60 or len({_identidad(f) for f in pareadas}) != 60:
            raise ValueError(f"{metrica}: pares duplicados o incompletos.")
        for par in pareadas:
            identidad = _identidad(par)
            corrida_ag = ag_por_id[identidad]
            corrida_baseline = baseline_por_id[identidad]
            if int(par["evaluaciones_ag"]) != int(corrida_ag["evaluaciones"]):
                raise ValueError(f"{metrica}: evaluaciones AG inconsistentes.")
            if int(par["evaluaciones_baseline"]) != int(corrida_baseline["evaluaciones"]):
                raise ValueError(f"{metrica}: evaluaciones baseline inconsistentes.")
            if int(corrida_ag["evaluaciones"]) != int(corrida_baseline["evaluaciones"]):
                raise ValueError(f"{metrica}: presupuesto pareado distinto.")
            if corrida_ag["configuracion_json"] != corrida_baseline["configuracion_json"]:
                raise ValueError(f"{metrica}: configuración AG/baseline distinta.")
            if not np.isclose(_numero(par, "fitness_ag"), _numero(corrida_ag, "mejor_fitness")):
                raise ValueError(f"{metrica}: fitness AG del par no coincide con su CSV.")
            if not np.isclose(
                _numero(par, "fitness_baseline"),
                _numero(corrida_baseline, "mejor_fitness"),
            ):
                raise ValueError(f"{metrica}: fitness baseline del par no coincide con su CSV.")
            if par["metrica"] != metrica:
                raise ValueError(f"{metrica}: métrica incorrecta en la comparación pareada.")
            if not np.isclose(_numero(par, "diferencia_ag_menos_baseline"),
                              _numero(par, "fitness_ag") - _numero(par, "fitness_baseline")):
                raise ValueError(f"{metrica}: diferencia pareada inconsistente.")

        datos[metrica] = {"ag": ag, "baseline": baseline, "pareadas": pareadas}
    return datos


def _matriz_diseno(filas: list[dict[str, str]]) -> tuple[np.ndarray, dict[str, slice]]:
    """Diseño factorial completo con contrastes de tratamiento e interacciones."""
    valores = [_identidad(fila) for fila in filas]
    niveles = [sorted({fila[i] for fila in valores}) for i in range(3)]
    codigos = []
    for factor, factor_niveles in enumerate(niveles):
        codigos.append(np.array([factor_niveles.index(fila[factor]) for fila in valores]))

    terminos = {
        "poblacion": (0,),
        "elitismo": (1,),
        "probabilidad_mutacion": (2,),
        "poblacion:elitismo": (0, 1),
        "poblacion:probabilidad_mutacion": (0, 2),
        "elitismo:probabilidad_mutacion": (1, 2),
        "poblacion:elitismo:probabilidad_mutacion": (0, 1, 2),
    }
    columnas = [np.ones((len(filas), 1))]
    # Las mismas cinco semillas se repiten en cada configuración; se incluyen
    # como bloque para no atribuir al tratamiento diferencias basales por semilla.
    niveles_semilla = sorted({int(fila["semilla"]) for fila in filas})
    codigos_semilla = np.array(
        [niveles_semilla.index(int(fila["semilla"])) for fila in filas]
    )
    bloque_semilla = np.column_stack(
        [codigos_semilla == nivel for nivel in range(1, len(niveles_semilla))]
    ).astype(float)
    columnas.append(bloque_semilla)
    rangos: dict[str, slice] = {}
    inicio = 1 + bloque_semilla.shape[1]
    for nombre, factores in terminos.items():
        bloques = []
        for factor in factores:
            n_niveles = len(niveles[factor])
            dummy = np.column_stack(
                [codigos[factor] == nivel for nivel in range(1, n_niveles)]
            ).astype(float)
            bloques.append(dummy)
        bloque = bloques[0]
        for siguiente in bloques[1:]:
            bloque = np.einsum("ni,nj->nij", bloque, siguiente).reshape(len(filas), -1)
        columnas.append(bloque)
        rangos[nombre] = slice(inicio, inicio + bloque.shape[1])
        inicio += bloque.shape[1]
    return np.column_stack(columnas), rangos


def _sse(x: np.ndarray, y: np.ndarray) -> tuple[float, int]:
    beta, _, rango, _ = np.linalg.lstsq(x, y, rcond=None)
    residuo = y - x @ beta
    return float(residuo @ residuo), int(rango)


def anova_factorial(filas: list[dict[str, str]]) -> list[dict[str, float | str]]:
    """ANOVA factorial fija 3 factores, con todas las interacciones y semillas replicadas."""
    x, rangos = _matriz_diseno(filas)
    y = np.array([_numero(fila, "mejor_fitness") for fila in filas])
    sse_completo, rango_completo = _sse(x, y)
    gl_residuo = len(y) - rango_completo
    if gl_residuo <= 0:
        raise ValueError("No quedan grados de libertad residuales para el ANOVA.")

    resultados = []
    for termino, columnas in rangos.items():
        reducida = np.delete(x, np.s_[columnas.start:columnas.stop], axis=1)
        sse_reducido, rango_reducido = _sse(reducida, y)
        gl_efecto = rango_completo - rango_reducido
        ss_efecto = max(sse_reducido - sse_completo, 0.0)
        f_obs = (ss_efecto / gl_efecto) / (sse_completo / gl_residuo)
        resultados.append({
            "termino": termino,
            "gl": gl_efecto,
            "F": f_obs,
            "p": float(distribucion_f.sf(f_obs, gl_efecto, gl_residuo)),
            "eta2_parcial": ss_efecto / (ss_efecto + sse_completo)
            if ss_efecto + sse_completo > 0 else 0.0,
        })
    return resultados


def ajustar_holm(resultados_por_metrica: dict[str, list[dict]]) -> None:
    """Añade p ajustada de Holm a la familia conjunta de 14 pruebas factoriales."""
    pruebas = [
        (metrica, fila)
        for metrica, resultados in resultados_por_metrica.items()
        for fila in resultados
    ]
    orden = sorted(range(len(pruebas)), key=lambda i: float(pruebas[i][1]["p"]))
    ajustadas = [0.0] * len(pruebas)
    anterior = 0.0
    total = len(pruebas)
    for posicion, indice in enumerate(orden):
        p = float(pruebas[indice][1]["p"])
        ajuste = min(1.0, (total - posicion) * p)
        anterior = max(anterior, ajuste)
        ajustadas[indice] = anterior
    for indice, (metrica, fila) in enumerate(pruebas):
        fila["p_holm_14"] = ajustadas[indice]


def efectos_marginales(filas: list[dict[str, str]]) -> dict[str, float]:
    """Contrastes descriptivos entre niveles extremos de cada hiperparámetro."""
    niveles = {"poblacion": {}, "elitismo": {}, "probabilidad_mutacion": {}}
    for fila in filas:
        n, elite, pm, _ = _identidad(fila)
        for nombre, nivel in (("poblacion", n), ("elitismo", elite),
                              ("probabilidad_mutacion", pm)):
            niveles[nombre].setdefault(nivel, []).append(_numero(fila, "mejor_fitness"))
    return {
        "población: 100 − 20": float(np.mean(niveles["poblacion"][100]) - np.mean(niveles["poblacion"][20])),
        "elitismo: 2 − 1": float(np.mean(niveles["elitismo"][2]) - np.mean(niveles["elitismo"][1])),
        "mutación: 0.08 − 0.02": float(np.mean(niveles["probabilidad_mutacion"][0.08]) - np.mean(niveles["probabilidad_mutacion"][0.02])),
    }


def resumen_pareado(filas: list[dict[str, str]]) -> dict[str, float | int]:
    diferencias = np.array([_numero(fila, "diferencia_ag_menos_baseline") for fila in filas])
    return {
        "n": int(diferencias.size),
        "media_ag": float(np.mean([_numero(fila, "fitness_ag") for fila in filas])),
        "de_ag": float(np.std([_numero(fila, "fitness_ag") for fila in filas], ddof=1)),
        "media_baseline": float(np.mean([_numero(fila, "fitness_baseline") for fila in filas])),
        "de_baseline": float(np.std([_numero(fila, "fitness_baseline") for fila in filas], ddof=1)),
        "diferencia_media": float(np.mean(diferencias)),
        "diferencia_de": float(np.std(diferencias, ddof=1)),
        "diferencia_mediana": float(np.median(diferencias)),
        "pares_ag_mayor": int(np.sum(diferencias > 0)),
        "pares_empatados": int(np.sum(diferencias == 0)),
        "pares_baseline_mayor": int(np.sum(diferencias < 0)),
    }


def graficar_efectos(datos: dict[str, dict]):
    fig, ejes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    colores = {"stft": "#3569a8", "croma": "#b56542"}
    for eje, metrica in zip(ejes, METRICAS):
        efectos = efectos_marginales(datos[metrica]["ag"])
        nombres = list(efectos)
        valores = [efectos[nombre] for nombre in nombres]
        eje.barh(nombres, valores, color=colores[metrica])
        eje.axvline(0, color="#333333", linewidth=0.8)
        eje.set_title(metrica.upper())
        eje.set_xlabel("Cambio medio de fitness (nivel alto − bajo)")
        eje.grid(axis="x", alpha=0.22)
    fig.suptitle("Sensibilidad factorial descriptiva — resultados guardados del Día 3")
    fig.tight_layout()
    return fig


def graficar_boxplot(datos: dict[str, dict], metrica: str):
    """Compara AG y baseline en una métrica, con las 60 observaciones guardadas."""
    if metrica not in METRICAS:
        raise ValueError(f"Métrica no reconocida: {metrica}")
    filas_ag = datos[metrica]["ag"]
    filas_baseline = datos[metrica]["baseline"]
    valores = [
        [_numero(fila, "mejor_fitness") for fila in filas_ag],
        [_numero(fila, "mejor_fitness") for fila in filas_baseline],
    ]
    figura, eje = plt.subplots(figsize=(7.4, 5.2))
    cajas = eje.boxplot(valores, patch_artist=True, widths=0.55)
    for caja, color in zip(cajas["boxes"], ("#3569a8", "#b56542")):
        caja.set_facecolor(color)
        caja.set_alpha(0.72)
    eje.set_xticks((1, 2), ("Algoritmo genético", "Búsqueda aleatoria"))
    eje.set_ylabel("Mejor fitness (mayor es mejor)")
    eje.set_title(f"{metrica.upper()}: distribución de 60 corridas por método")
    eje.grid(axis="y", alpha=0.24)
    figura.text(
        0.5, 0.015,
        "Datos agrupados de 12 configuraciones × 5 semillas; no representa una sola configuración.",
        ha="center", fontsize=8.5, color="#4b5563",
    )
    figura.tight_layout(rect=(0, 0.055, 1, 1))
    return figura


def graficar_tornado_hiperparametros(datos: dict[str, dict]):
    """Muestra efectos marginales alto−bajo de hiperparámetros, separados por métrica."""
    figura, ejes = plt.subplots(1, 2, figsize=(11.5, 5.2))
    colores = {"stft": "#3569a8", "croma": "#b56542"}
    for eje, metrica in zip(ejes, METRICAS):
        efectos = efectos_marginales(datos[metrica]["ag"])
        ordenados = sorted(efectos.items(), key=lambda par: abs(par[1]))
        nombres = [par[0] for par in ordenados]
        valores = [par[1] for par in ordenados]
        eje.barh(nombres, valores, color=colores[metrica], alpha=0.82)
        maximo = max((abs(valor) for valor in valores), default=0.0)
        limite = maximo * 1.18 if maximo else 1.0
        eje.set_xlim(-limite, limite)
        eje.axvline(0, color="#333333", linewidth=0.9)
        eje.set_title(metrica.upper())
        eje.set_xlabel("Cambio medio de fitness (nivel alto − bajo)")
        eje.grid(axis="x", alpha=0.22)
        eje.set_axisbelow(True)
    figura.suptitle("Tornado de sensibilidad de hiperparámetros — datos del factorial guardado")
    figura.text(
        0.5, 0.015,
        "Población (100−20), elitismo (2−1) y mutación (0.08−0.02); no son genes del Rol 1.",
        ha="center", fontsize=8.5, color="#4b5563",
    )
    figura.tight_layout(rect=(0, 0.06, 1, 0.94))
    return figura


def guardar_svg_exclusivo(figura, ruta: Path) -> None:
    """Guarda un SVG nuevo y cierra la figura, sin reemplazar evidencia previa."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    try:
        with ruta.open("x", encoding="utf-8") as archivo:
            figura.savefig(archivo, format="svg", bbox_inches="tight")
    finally:
        plt.close(figura)


def graficar_lamina(datos: dict[str, dict]):
    """Crea una lámina SVG 16:9 lista para insertar en la presentación grupal."""
    figura = plt.figure(figsize=(13.333, 7.5), facecolor="#f7f8fa")
    figura.text(0.055, 0.93, "Meta-evaluación del algoritmo genético",
                fontsize=24, fontweight="bold", color="#182433")
    figura.text(0.057, 0.885,
                "Factorial del Día 3 · 12 configuraciones × 5 semillas · B provisional",
                fontsize=12, color="#536273")

    colores = {"stft": "#3569a8", "croma": "#b56542"}
    for metrica, rect in (("stft", [0.06, 0.31, 0.25, 0.47]),
                          ("croma", [0.34, 0.31, 0.25, 0.47])):
        eje = figura.add_axes(rect)
        efecto = efectos_marginales(datos[metrica]["ag"])
        nombres = ["Población 100 − 20", "Elitismo 2 − 1", "Mutación .08 − .02"]
        valores = list(efecto.values())
        eje.barh(nombres, valores, color=colores[metrica])
        eje.axvline(0, color="#4b5563", linewidth=0.8)
        eje.set_title(metrica.upper(), loc="left", fontweight="bold")
        eje.set_xlabel("Cambio medio de fitness")
        eje.tick_params(axis="y", labelsize=9)
        eje.grid(axis="x", alpha=0.2)
        eje.set_axisbelow(True)

    stft = resumen_pareado(datos["stft"]["pareadas"])
    croma = resumen_pareado(datos["croma"]["pareadas"])
    figura.text(0.64, 0.77, "AG vs búsqueda aleatoria", fontsize=15,
                fontweight="bold", color="#182433")
    figura.text(0.64, 0.69,
                f"STFT: {stft['media_ag']:.4f} vs {stft['media_baseline']:.4f}\n"
                f"Δ pareada media: +{stft['diferencia_media']:.5f} · AG mayor {stft['pares_ag_mayor']}/60",
                fontsize=11, color="#263544", linespacing=1.5)
    figura.text(0.64, 0.56,
                f"Chroma: {croma['media_ag']:.4f} vs {croma['media_baseline']:.4f}\n"
                f"Δ pareada media: +{croma['diferencia_media']:.5f} · AG mayor {croma['pares_ag_mayor']}/60",
                fontsize=11, color="#263544", linespacing=1.5)
    figura.text(0.64, 0.41,
                "ANOVA factorial exploratorio + Holm (14 contrastes):\n"
                "efectos de población y mutación en chroma;\n"
                "ningún término de STFT conserva p ajustada < 0.05.",
                fontsize=10.5, color="#263544", linespacing=1.45)
    figura.text(0.055, 0.19,
                "Lectura: comparación pareada descriptiva; baseline igualó evaluaciones reales de cada AG.",
                fontsize=11, fontweight="bold", color="#263544")
    figura.text(0.055, 0.12,
                "Una melodía/referencia · cinco semillas por configuración · sin encuesta auditiva ni validación perceptual.",
                fontsize=10, color="#536273")
    figura.text(0.055, 0.07,
                "STFT primaria y operadores B siguen pendientes de ratificación colectiva; no se concluye superioridad general.",
                fontsize=10, color="#8a4b18")
    return figura


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--guardar-svg", type=Path,
                        help="Ruta nueva para guardar el gráfico, sin sobrescritura.")
    parser.add_argument("--guardar-lamina", type=Path,
                        help="Ruta nueva para exportar la lámina SVG 16:9, sin sobrescritura.")
    parser.add_argument("--guardar-boxplot-stft", type=Path,
                        help="Ruta nueva para el boxplot STFT, sin sobrescritura.")
    parser.add_argument("--guardar-boxplot-croma", type=Path,
                        help="Ruta nueva para el boxplot chroma, sin sobrescritura.")
    parser.add_argument("--guardar-tornado-hiperparametros", type=Path,
                        help="Ruta nueva para el tornado de hiperparámetros, sin sobrescritura.")
    args = parser.parse_args()

    datos = cargar_y_validar()
    anovas = {
        metrica: anova_factorial(datos[metrica]["ag"])
        for metrica in METRICAS
    }
    ajustar_holm(anovas)
    for metrica in METRICAS:
        print(f"\n[{metrica.upper()}] descriptivos pareados")
        print(json.dumps(resumen_pareado(datos[metrica]["pareadas"]), indent=2))
        print(f"[{metrica.upper()}] efectos marginales (fitness)")
        print(json.dumps(efectos_marginales(datos[metrica]["ag"]), indent=2))
        print(f"[{metrica.upper()}] ANOVA factorial")
        print(json.dumps(anovas[metrica], indent=2))

    if args.guardar_svg:
        figura = graficar_efectos(datos)
        args.guardar_svg.parent.mkdir(parents=True, exist_ok=True)
        with args.guardar_svg.open("x", encoding="utf-8") as archivo:
            figura.savefig(archivo, format="svg", bbox_inches="tight")
        plt.close(figura)
        print(f"Gráfico nuevo guardado en: {args.guardar_svg}")
    if args.guardar_lamina:
        figura = graficar_lamina(datos)
        guardar_svg_exclusivo(figura, args.guardar_lamina)
        print(f"Lámina nueva guardada en: {args.guardar_lamina}")
    if args.guardar_boxplot_stft:
        guardar_svg_exclusivo(
            graficar_boxplot(datos, "stft"), args.guardar_boxplot_stft
        )
        print(f"Boxplot STFT nuevo guardado en: {args.guardar_boxplot_stft}")
    if args.guardar_boxplot_croma:
        guardar_svg_exclusivo(
            graficar_boxplot(datos, "croma"), args.guardar_boxplot_croma
        )
        print(f"Boxplot chroma nuevo guardado en: {args.guardar_boxplot_croma}")
    if args.guardar_tornado_hiperparametros:
        guardar_svg_exclusivo(
            graficar_tornado_hiperparametros(datos),
            args.guardar_tornado_hiperparametros,
        )
        print(
            "Tornado de hiperparámetros nuevo guardado en: "
            f"{args.guardar_tornado_hiperparametros}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
