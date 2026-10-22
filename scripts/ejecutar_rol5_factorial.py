"""Factorial Día 3 de Rol 5 y baseline aleatorio pareado.

Sin ``--ejecutar`` solo muestra el protocolo. Cada ejecución se escribe en
un directorio nuevo; checkpoints y CSV se crean en modo exclusivo.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import platform
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import soundfile as sf

from src.algoritmo_genetico import ejecutar_ag
from src.configuracion import (
    SEMILLAS_EXPERIMENTALES,
    ConfiguracionAG,
    crear_plan_experimental,
)
from src.evaluacion import (
    construir_registro_corrida,
    guardar_registros_csv,
    resumir_corridas,
)
from src.experimentos import ejecutar_baselines_pareados, ejecutar_corridas_ag
from src.extraccion import cargar_melodia_csv
from src.fitness import (
    ESCALA_ERROR_DB,
    N_FFT,
    PISO_DB,
    SALTO,
    evaluar_individuo,
)
from src.sintesis import FRECUENCIA_MUESTREO


METRICAS = ("stft", "croma")
OPERADORES_B = {
    "seleccion": "torneo",
    "cruce": "uniforme",
    "mutacion": "gaussiana",
    "alpha": 0.5,
    "sigma": 0.08,
    "b": 2.0,
}
SEMILLAS = tuple(SEMILLAS_EXPERIMENTALES)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _has_package(name: str) -> bool:
    try:
        version(name)
    except PackageNotFoundError:
        return False
    return True


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, tuple):
        return list(value)
    raise TypeError(f"No se puede serializar {type(value).__name__} a JSON.")


def _write_json_exclusive(path: Path, content: Any) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(content, stream, ensure_ascii=False, indent=2,
                  allow_nan=False, default=_json_default)
        stream.write("\n")


def _cargar_datos() -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, str]]:
    melody_path = ROOT / "datos/procesados/melodia_01.csv"
    reference_path = ROOT / "datos/audio/referencias/flauta_referencia_01.wav"
    notes, durations = cargar_melodia_csv(melody_path)
    reference, sample_rate = sf.read(reference_path, dtype="float32")
    info = sf.info(reference_path)
    metadata = json.loads(reference_path.with_suffix(".json").read_text(encoding="utf-8"))

    if sample_rate != FRECUENCIA_MUESTREO:
        raise ValueError(f"Frecuencia inesperada: {sample_rate} Hz.")
    if reference.ndim != 1 or info.channels != 1:
        raise ValueError("La referencia debe ser mono.")
    if reference.size < N_FFT or not np.all(np.isfinite(reference)):
        raise ValueError("Referencia vacía, corta o con valores no finitos.")
    if notes.ndim != 1 or durations.ndim != 1 or notes.size != durations.size:
        raise ValueError("Notas y duraciones deben ser vectores del mismo tamaño.")
    if not np.array_equal(notes, np.asarray(metadata["notas"])):
        raise ValueError("La melodía no coincide con los metadatos de referencia.")
    if not np.array_equal(durations, np.asarray(metadata["duraciones_s"])):
        raise ValueError("Las duraciones no coinciden con los metadatos de referencia.")
    if metadata["frecuencia_muestreo"] != sample_rate:
        raise ValueError("La frecuencia de muestreo no coincide con los metadatos.")
    expected_frames = int(round(float(np.sum(durations)) * sample_rate))
    if reference.size != expected_frames or info.frames != expected_frames:
        raise ValueError("La referencia no cubre la duración completa de la melodía.")
    if np.max(np.abs(reference)) <= 1e-8:
        raise ValueError("La referencia no puede ser silenciosa.")
    if not np.all(np.isfinite(durations)) or np.any(durations <= 0):
        raise ValueError("Las duraciones deben ser positivas y finitas.")

    hashes = {
        path.relative_to(ROOT).as_posix(): _sha256(path)
        for path in (melody_path, reference_path)
    }
    return notes, durations, reference, {
        **hashes,
        "sample_rate": str(sample_rate),
        "channels": str(info.channels),
        "frames": str(info.frames),
        "subtype": str(info.subtype),
    }


def _crear_aptitud(notes, durations, reference, metric: str):
    if metric not in METRICAS:
        raise ValueError(f"Métrica desconocida: {metric}.")

    def aptitud(individuo: np.ndarray) -> float:
        return float(evaluar_individuo(
            individuo, notes, durations, reference, metrica=metric
        ))

    return aptitud


def _nombre_checkpoint(config: ConfiguracionAG, seed: int) -> str:
    return (
        f"ag_N{config.tam_poblacion}_E{config.elitismo}_"
        f"pm{config.probabilidad_mutacion:g}_seed{seed}.json"
    )


def _crear_runner(aptitud, metric: str, metric_dir: Path, captured: dict):
    def runner(config: ConfiguracionAG) -> dict[str, Any]:
        started = time.perf_counter()
        result = ejecutar_ag(aptitud, config, **OPERADORES_B)
        runner_time = time.perf_counter() - started
        checkpoint = metric_dir / _nombre_checkpoint(config, config.semilla)
        _write_json_exclusive(checkpoint, {
            "metodo": "algoritmo_genetico",
            "metrica": metric,
            "semilla": config.semilla,
            "configuracion": asdict(config),
            "operadores": dict(OPERADORES_B),
            "tiempo_runner_s": runner_time,
            "resultado_completo": result,
            "historial": result["historial"],
        })
        captured[(json.dumps(asdict(config), sort_keys=True), config.semilla)] = result
        print(
            f"AG {metric}: N={config.tam_poblacion}, E={config.elitismo}, "
            f"pm={config.probabilidad_mutacion}, semilla={config.semilla}, "
            f"fitness={result['mejor_fitness']:.8f}, "
            f"evaluaciones={result['evaluaciones']}, "
            f"parada={result['motivo_parada']}",
            flush=True,
        )
        return result

    return runner


def _configuracion_registro(row: dict[str, Any]) -> None:
    config = json.loads(row["configuracion_json"])
    config["operadores"] = dict(OPERADORES_B)
    row["configuracion_json"] = json.dumps(
        config, sort_keys=True, ensure_ascii=False
    )
    row["combinacion_operadores"] = "B"


def _json_corrida(result: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    return {
        "registro": row,
        "resultado_completo": result,
        "historial": result["historial"],
        "operadores": dict(OPERADORES_B),
    }


def _identidad(row: dict[str, Any]) -> tuple[str, int, str]:
    return row["configuracion_json"], int(row["semilla"]), row["metrica"]


def validar_bloque(
    registros_ag: list[dict[str, Any]],
    registros_baseline: list[dict[str, Any]],
    expected_metric: str,
    captured_ag: dict,
) -> None:
    configs = crear_plan_experimental()
    expected = {
        (json.dumps({**asdict(replace(config, semilla=seed)), "operadores": OPERADORES_B},
                    sort_keys=True, ensure_ascii=False), seed, expected_metric)
        for config in configs
        for seed in SEMILLAS
    }
    ag_keys = [_identidad(row) for row in registros_ag]
    baseline_keys = [_identidad(row) for row in registros_baseline]
    if len(ag_keys) != 60 or len(set(ag_keys)) != 60 or set(ag_keys) != expected:
        raise ValueError("El bloque AG no contiene exactamente las 60 corridas esperadas.")
    if len(baseline_keys) != 60 or len(set(baseline_keys)) != 60 or set(baseline_keys) != expected:
        raise ValueError("El baseline no contiene los 60 pares AG esperados.")

    baselines = {_identidad(row): row for row in registros_baseline}
    for row in registros_ag:
        config = json.loads(row["configuracion_json"])
        generations = row["generaciones_ejecutadas"]
        evaluations = row["evaluaciones"]
        if (
            not np.all(np.isfinite([row["mejor_fitness"], row["tiempo_s"]]))
            or evaluations is None or evaluations < 1
            or generations is None or generations < 0
            or generations > config["max_generaciones"]
            or evaluations != config["tam_poblacion"] * (generations + 1)
        ):
            raise ValueError("Registro AG no finito o sin evaluaciones reales.")
        if row["metrica"] != expected_metric or row["combinacion_operadores"] != "B":
            raise ValueError("Métrica u operadores incorrectos en AG.")
        raw = captured_ag[(json.dumps(
            {key: value for key, value in config.items() if key != "operadores"},
            sort_keys=True,
        ), int(row["semilla"]))]
        history = raw["historial"]
        if len(history) != generations + 1:
            raise ValueError("La longitud del historial no coincide con generaciones.")
        def stat_value(item, key):
            return item[key] if isinstance(item, dict) else getattr(item, key)
        history_values = np.asarray([
            [stat_value(item, "generacion"), stat_value(item, "fitness_maximo"),
             stat_value(item, "fitness_medio"), stat_value(item, "desviacion_fitness"),
             stat_value(item, "diversidad_genetica")]
            for item in history
        ], dtype=np.float64)
        if not np.all(np.isfinite(history_values)):
            raise ValueError("El historial contiene valores no finitos.")
        best_history = np.asarray(raw["historial_mejor_fitness"], dtype=np.float64)
        if (
            best_history.size != generations + 1
            or not np.all(np.isfinite(best_history))
            or np.any(np.diff(best_history) < 0)
            or best_history[-1] != row["mejor_fitness"]
        ):
            raise ValueError("Historial de mejor fitness inconsistente.")
        if row["motivo_parada"] not in ("max_generaciones", "estancamiento"):
            raise ValueError("Motivo de parada AG desconocido.")
        baseline = baselines[_identidad(row)]
        if baseline["evaluaciones"] != row["evaluaciones"]:
            raise ValueError("El baseline no iguala el presupuesto real del AG.")
        if baseline["motivo_parada"] != "presupuesto_de_evaluaciones":
            raise ValueError("Motivo de parada del baseline inesperado.")
        if not np.isfinite(baseline["mejor_fitness"]) or not np.isfinite(baseline["tiempo_s"]):
            raise ValueError("Registro baseline no finito.")


def _paired_rows(ag_rows: list[dict[str, Any]], baseline_rows: list[dict[str, Any]]):
    baseline_index = {_identidad(row): row for row in baseline_rows}
    pairs = []
    for ag in ag_rows:
        baseline = baseline_index[_identidad(ag)]
        pairs.append({
            "configuracion_json": ag["configuracion_json"],
            "combinacion_operadores": "B",
            "semilla": ag["semilla"],
            "metrica": ag["metrica"],
            "fitness_ag": ag["mejor_fitness"],
            "fitness_baseline": baseline["mejor_fitness"],
            "diferencia_ag_menos_baseline": ag["mejor_fitness"] - baseline["mejor_fitness"],
            "evaluaciones_ag": ag["evaluaciones"],
            "evaluaciones_baseline": baseline["evaluaciones"],
            "tiempo_ag_s": ag["tiempo_s"],
            "tiempo_baseline_s": baseline["tiempo_s"],
            "motivo_parada_ag": ag["motivo_parada"],
        })
    return pairs


def _summary_rows(ag_rows, baseline_rows, pairs):
    method_rows = []
    for rows in (ag_rows, baseline_rows):
        summaries = resumir_corridas(
            rows,
            agrupar_por=("metodo",),
            metrica="mejor_fitness",
        )
        for summary in summaries:
            summary["metrica_evaluacion"] = rows[0]["metrica"]
            summary["estadistico"] = "mejor_fitness"
        method_rows.extend(summaries)

    by_config = []
    for rows in (ag_rows, baseline_rows):
        enriched = []
        for row in rows:
            item = dict(row)
            config = json.loads(row["configuracion_json"])
            for factor in ("tam_poblacion", "elitismo", "probabilidad_mutacion"):
                item[factor] = config[factor]
            enriched.append(item)
        summaries = resumir_corridas(
            enriched,
            agrupar_por=("tam_poblacion", "elitismo", "probabilidad_mutacion", "metodo"),
            metrica="mejor_fitness",
        )
        for summary in summaries:
            summary["metrica_evaluacion"] = rows[0]["metrica"]
            summary["combinacion_operadores"] = "B"
        by_config.extend(summaries)

    deltas = np.asarray([row["diferencia_ag_menos_baseline"] for row in pairs])
    pair_summary = [{
        "metrica": pairs[0]["metrica"],
        "n_pares": int(deltas.size),
        "diferencia_media_ag_menos_baseline": float(np.mean(deltas)),
        "diferencia_de_muestral": float(np.std(deltas, ddof=1)),
        "diferencia_mediana": float(np.median(deltas)),
        "pares_con_ag_mayor_fitness": int(np.count_nonzero(deltas > 0)),
        "pares_empatados": int(np.count_nonzero(deltas == 0)),
        "pares_con_baseline_mayor_fitness": int(np.count_nonzero(deltas < 0)),
    }]
    paired_by_config = []
    grouped: dict[tuple[int, int, float], list[dict[str, Any]]] = {}
    for pair in pairs:
        config = json.loads(pair["configuracion_json"])
        key = (config["tam_poblacion"], config["elitismo"], config["probabilidad_mutacion"])
        grouped.setdefault(key, []).append(pair)
    for (population, elitism, p_mut), group in grouped.items():
        values = np.asarray([row["diferencia_ag_menos_baseline"] for row in group], dtype=float)
        paired_by_config.append({
            "metrica_evaluacion": group[0]["metrica"],
            "tam_poblacion": population,
            "elitismo": elitism,
            "probabilidad_mutacion": p_mut,
            "combinacion_operadores": "B",
            "n_pares": int(values.size),
            "diferencia_media_ag_menos_baseline": float(np.mean(values)),
            "diferencia_de_muestral": float(np.std(values, ddof=1)),
            "diferencia_mediana": float(np.median(values)),
            "pares_con_ag_mayor_fitness": int(np.count_nonzero(values > 0)),
            "pares_empatados": int(np.count_nonzero(values == 0)),
            "pares_con_baseline_mayor_fitness": int(np.count_nonzero(values < 0)),
        })
    return method_rows, pair_summary, by_config, paired_by_config


def resumir_guardado(run_dir: Path, metrics: tuple[str, ...]) -> None:
    numeric_fields = {
        "semilla": int,
        "mejor_fitness": float,
        "tiempo_s": float,
        "evaluaciones": int,
        "generaciones_ejecutadas": int,
        "error_stft_db": float,
        "fitness_ag": float,
        "fitness_baseline": float,
        "diferencia_ag_menos_baseline": float,
        "evaluaciones_ag": int,
        "evaluaciones_baseline": int,
        "tiempo_ag_s": float,
        "tiempo_baseline_s": float,
    }

    def read_rows(path: Path) -> list[dict[str, Any]]:
        with path.open("r", newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            for field, conversion in numeric_fields.items():
                if row.get(field) not in (None, ""):
                    row[field] = conversion(row[field])
        return rows

    for metric in metrics:
        metric_dir = run_dir / metric
        ag_rows = read_rows(metric_dir / "corridas_ag.csv")
        baseline_rows = read_rows(metric_dir / "corridas_baseline.csv")
        pairs = read_rows(metric_dir / "comparacion_pareada.csv")
        method_rows, _, config_rows, paired_config_rows = _summary_rows(
            ag_rows, baseline_rows, pairs
        )
        guardar_registros_csv(
            method_rows, metric_dir / "resumen_metodos_etiquetado.csv"
        )
        guardar_registros_csv(
            config_rows, metric_dir / "resumen_por_configuracion.csv"
        )
        guardar_registros_csv(
            paired_config_rows,
            metric_dir / "resumen_pareado_por_configuracion.csv",
        )


def validar_guardado(run_dir: Path, metrics: tuple[str, ...]) -> None:
    def read_csv(path: Path) -> list[dict[str, str]]:
        with path.open("r", newline="", encoding="utf-8") as stream:
            return list(csv.DictReader(stream))

    for metric in metrics:
        metric_dir = run_dir / metric
        ag_rows = read_csv(metric_dir / "corridas_ag.csv")
        baseline_rows = read_csv(metric_dir / "corridas_baseline.csv")
        pair_rows = read_csv(metric_dir / "comparacion_pareada.csv")
        if not (len(ag_rows) == len(baseline_rows) == len(pair_rows) == 60):
            raise ValueError(f"{metric}: se esperaban exactamente 60 registros por CSV.")
        baseline_checkpoints = list(metric_dir.glob("baseline_*.json"))
        if len(baseline_checkpoints) != 60:
            raise ValueError(f"{metric}: se esperaban 60 checkpoints de baseline.")
        identities = [
            (row["configuracion_json"], int(row["semilla"]), row["metrica"])
            for row in ag_rows
        ]
        if len(set(identities)) != 60 or any(row["metrica"] != metric for row in ag_rows + baseline_rows):
            raise ValueError(f"{metric}: identidades duplicadas o métrica cruzada.")
        ag_index = {key: row for key, row in zip(identities, ag_rows)}
        baseline_index = {
            (row["configuracion_json"], int(row["semilla"]), row["metrica"]): row
            for row in baseline_rows
        }
        if set(ag_index) != set(baseline_index):
            raise ValueError(f"{metric}: las identidades AG y baseline no coinciden.")
        pair_index = {
            (row["configuracion_json"], int(row["semilla"]), row["metrica"]): row
            for row in pair_rows
        }
        if len(pair_index) != 60 or set(pair_index) != set(ag_index):
            raise ValueError(f"{metric}: identidades de comparación pareada inválidas.")
        for identity, row in ag_index.items():
            config = json.loads(row["configuracion_json"])
            if config.get("operadores") != OPERADORES_B:
                raise ValueError(f"{metric}: combinación de operadores incorrecta.")
            checkpoint_path = metric_dir / _nombre_checkpoint(
                ConfiguracionAG(**{k: v for k, v in config.items() if k != "operadores"}),
                int(row["semilla"]),
            )
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            raw = checkpoint["resultado_completo"]
            n_evals = int(row["evaluaciones"])
            generations = int(row["generaciones_ejecutadas"])
            if (
                checkpoint["metrica"] != metric
                or checkpoint["semilla"] != int(row["semilla"])
                or raw["mejor_fitness"] != float(row["mejor_fitness"])
                or n_evals != int(config["tam_poblacion"]) * (generations + 1)
                or len(checkpoint["historial"]) != generations + 1
            ):
                raise ValueError(f"{metric}: checkpoint AG inconsistente.")
            history_best = np.asarray(raw["historial_mejor_fitness"], dtype=float)
            if not np.all(np.isfinite(history_best)) or np.any(np.diff(history_best) < 0):
                raise ValueError(f"{metric}: historial AG no finito o no monótono.")
            baseline = baseline_index[identity]
            if int(baseline["evaluaciones"]) != n_evals:
                raise ValueError(f"{metric}: baseline no iguala el presupuesto AG.")
            pair = pair_index[identity]
            if not np.isclose(
                float(row["mejor_fitness"]) - float(baseline["mejor_fitness"]),
                float(pair["diferencia_ag_menos_baseline"]),
                rtol=0.0, atol=1e-14,
            ):
                raise ValueError(f"{metric}: diferencia pareada incorrecta.")
        for index, baseline_row in enumerate(baseline_rows, start=1):
            baseline_path = metric_dir / (
                f"baseline_seed{baseline_row['semilla']}_pair{index:02d}.json"
            )
            checkpoint_row = json.loads(
                baseline_path.read_text(encoding="utf-8")
            )["registro"]
            identity = (
                baseline_row["configuracion_json"],
                int(baseline_row["semilla"]),
                baseline_row["metrica"],
            )
            if (
                identity not in ag_index
                or checkpoint_row["metrica"] != metric
                or checkpoint_row["semilla"] != identity[1]
                or checkpoint_row["evaluaciones"] != int(baseline_row["evaluaciones"])
                or checkpoint_row["configuracion_json"] != baseline_row["configuracion_json"]
                or not np.isclose(
                    checkpoint_row["mejor_fitness"],
                    float(baseline_row["mejor_fitness"]),
                    rtol=0.0, atol=1e-14,
                )
            ):
                raise ValueError(f"{metric}: checkpoint baseline inconsistente.")
        if len(read_csv(metric_dir / "resumen_por_configuracion.csv")) != 24:
            raise ValueError(f"{metric}: el resumen factorial debe contener 24 filas.")
        paired_summary = read_csv(metric_dir / "resumen_pareado_por_configuracion.csv")
        if len(paired_summary) != 12 or any(int(row["n_pares"]) != 5 for row in paired_summary):
            raise ValueError(f"{metric}: resumen pareado por configuración inválido.")


def _ag_row_from_checkpoint(path: Path, metric: str) -> tuple[dict, dict]:
    checkpoint = json.loads(path.read_text(encoding="utf-8"))
    if checkpoint.get("metodo") != "algoritmo_genetico" or checkpoint.get("metrica") != metric:
        raise ValueError(f"Checkpoint incompatible: {path}")
    config = checkpoint["configuracion"]
    result = checkpoint["resultado_completo"]
    row = construir_registro_corrida(
        metodo="algoritmo_genetico",
        semilla=int(checkpoint["semilla"]),
        configuracion=config,
        resultado=result,
        tiempo_s=checkpoint["tiempo_runner_s"],
        metrica=metric,
    )
    _configuracion_registro(row)
    return row, result


def ejecutar(
    output_root: Path,
    metrics: tuple[str, ...],
    resume_dir: Path | None = None,
) -> Path:
    notes, durations, reference, data_info = _cargar_datos()
    configs = crear_plan_experimental()
    if len(configs) != 12 or len({asdict(config).__repr__() for config in configs}) != 12:
        raise ValueError("El plan factorial no tiene 12 configuraciones únicas.")
    if len(SEMILLAS) != 5 or len(set(SEMILLAS)) != 5:
        raise ValueError("El plan requiere cinco semillas únicas.")
    if not metrics or len(set(metrics)) != len(metrics):
        raise ValueError("Indica una o más métricas distintas.")
    if any(metric not in METRICAS for metric in metrics):
        raise ValueError("Métrica no soportada.")

    is_resume = resume_dir is not None
    if is_resume:
        run_dir = resume_dir.resolve()
        manifest_path = run_dir / "manifiesto.json"
        if not manifest_path.is_file():
            raise FileNotFoundError(f"No existe el manifiesto para reanudar: {manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("commit_base") != "c5dc431612bbc3ef3dec85d31bf8ce2ad3488c71":
            raise ValueError("El checkpoint no corresponde al commit base esperado.")
        if any(metric not in manifest.get("metricas", []) for metric in metrics):
            raise ValueError("La métrica no está declarada en el manifiesto original.")
    else:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + "c5dc431"
        run_dir = output_root / f"ejecucion_{run_id}"
        run_dir.mkdir(parents=True, exist_ok=False)
        manifest = {
        "estado": "en ejecución",
        "creado_utc": datetime.now(timezone.utc).isoformat(),
        "commit_base": "c5dc431612bbc3ef3dec85d31bf8ce2ad3488c71",
        "rama_esperada": "feature/rol5-experimentos-dia3",
        "python": sys.version,
        "plataforma": platform.platform(),
        "paquetes": {
            package: (version(package) if _has_package(package) else None)
            for package in ("numpy", "scipy", "soundfile")
        },
        "configuraciones": [asdict(config) for config in configs],
        "semillas": list(SEMILLAS),
        "operadores_provisionales_no_ratificados": OPERADORES_B,
        "metricas": list(metrics),
        "metricas_separadas": True,
        "stft_ratificacion_colectiva_pendiente": True,
        "datos": data_info,
        "sha256_codigo": {
            path.relative_to(ROOT).as_posix(): _sha256(path)
            for path in (
                ROOT / "scripts/ejecutar_rol5_factorial.py",
                ROOT / "src/algoritmo_genetico.py",
                ROOT / "src/configuracion.py",
                ROOT / "src/evaluacion.py",
                ROOT / "src/experimentos.py",
                ROOT / "src/extraccion.py",
                ROOT / "src/fitness.py",
                ROOT / "src/representacion.py",
                ROOT / "src/sintesis.py",
            )
        },
        "fitness": {
            "n_fft": N_FFT, "salto": SALTO, "piso_db": PISO_DB,
            "escala_error_db": ESCALA_ERROR_DB,
            "frecuencia_muestreo": FRECUENCIA_MUESTREO,
        },
        "parada": "ConfiguracionAG existente; parada por max_generaciones o estancamiento.",
        }
        _write_json_exclusive(run_dir / "manifiesto.json", manifest)

    for metric in metrics:
        metric_dir = run_dir / metric
        metric_dir.mkdir(exist_ok=is_resume)
        aptitud = _crear_aptitud(notes, durations, reference, metric)
        captured_results = {}
        runner = _crear_runner(aptitud, metric, metric_dir, captured_results)
        start = time.perf_counter()
        ag_rows = []
        for config in configs:
            missing_seeds = []
            for seed in SEMILLAS:
                config_seeded = replace(config, semilla=seed)
                checkpoint = metric_dir / _nombre_checkpoint(config_seeded, seed)
                if checkpoint.exists():
                    row, raw_result = _ag_row_from_checkpoint(checkpoint, metric)
                    ag_rows.append(row)
                    captured_results[(json.dumps(asdict(config_seeded), sort_keys=True), seed)] = raw_result
                else:
                    missing_seeds.append(seed)
            if missing_seeds:
                ag_rows.extend(ejecutar_corridas_ag(
                    runner, [config], missing_seeds, metrica=metric
                ))
        ag_elapsed = time.perf_counter() - start

        by_identity = {}
        for row in ag_rows:
            _configuracion_registro(row)
            key = _identidad(row)
            by_identity[key] = row
        for config in configs:
            for seed in SEMILLAS:
                key = (
                    json.dumps({**asdict(replace(config, semilla=seed)), "operadores": OPERADORES_B},
                               sort_keys=True, ensure_ascii=False),
                    seed,
                    metric,
                )
                row = by_identity[key]
                raw_result = captured_results[
                    (json.dumps(asdict(replace(config, semilla=seed)), sort_keys=True), seed)
                ]
                if row["mejor_fitness"] != raw_result["mejor_fitness"]:
                    raise ValueError("Fitness del registro y checkpoint no coinciden.")

        baseline_rows = []
        for index, ag_row in enumerate(ag_rows, start=1):
            baseline_path = metric_dir / f"baseline_seed{ag_row['semilla']}_pair{index:02d}.json"
            if baseline_path.exists():
                baseline_row = json.loads(baseline_path.read_text(encoding="utf-8"))["registro"]
            else:
                baseline_row = ejecutar_baselines_pareados(
                    aptitud, [ag_row], metrica=metric
                )[0]
                baseline_row["combinacion_operadores"] = "B"
                _write_json_exclusive(baseline_path, {"registro": baseline_row})
            baseline_rows.append(baseline_row)
            print(
                f"Baseline {metric}: par {index}/60, "
                f"semilla={ag_row['semilla']}, "
                f"evaluaciones={baseline_row['evaluaciones']}",
                flush=True,
            )
        validar_bloque(ag_rows, baseline_rows, metric, captured_results)
        pairs = _paired_rows(ag_rows, baseline_rows)
        method_summary, pair_summary, config_summary, paired_config_summary = _summary_rows(
            ag_rows, baseline_rows, pairs
        )

        guardar_registros_csv(ag_rows, metric_dir / "corridas_ag.csv")
        guardar_registros_csv(baseline_rows, metric_dir / "corridas_baseline.csv")
        guardar_registros_csv(pairs, metric_dir / "comparacion_pareada.csv")
        guardar_registros_csv(method_summary, metric_dir / "resumen_metodos_etiquetado.csv")
        guardar_registros_csv(pair_summary, metric_dir / "resumen_pareado.csv")
        guardar_registros_csv(config_summary, metric_dir / "resumen_por_configuracion.csv")
        guardar_registros_csv(
            paired_config_summary,
            metric_dir / "resumen_pareado_por_configuracion.csv",
        )
        _write_json_exclusive(metric_dir / "validacion.json", {
            "estado": "válido",
            "n_corridas_ag": len(ag_rows),
            "n_corridas_baseline": len(baseline_rows),
            "tiempo_bloque_ag_s": ag_elapsed,
            "metricas_separadas": True,
        })

    manifest["estado"] = "completado"
    manifest["completado_utc"] = datetime.now(timezone.utc).isoformat()
    # The initial manifest is immutable; a separate exclusive completion record
    # avoids overwriting it.
    _write_json_exclusive(
        run_dir / ("cierre_" + "_".join(metrics) + ".json"), manifest
    )
    return run_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ejecutar", action="store_true",
                        help="ejecuta las métricas listadas; sin esto solo muestra el plan")
    parser.add_argument("--metricas", nargs="+", choices=METRICAS, default=["stft", "croma"])
    parser.add_argument("--directorio-resultados", type=Path,
                        default=ROOT / "resultados/rol5/dia3_factorial")
    parser.add_argument("--reanudar", type=Path,
                        help="reanuda desde los checkpoints de una carpeta de ejecución existente")
    parser.add_argument("--resumir", type=Path,
                        help="crea tablas descriptivas nuevas desde CSV ya guardados; no ejecuta corridas")
    parser.add_argument("--validar-guardado", type=Path,
                        help="revalida CSV y checkpoints existentes sin ejecutar corridas")
    args = parser.parse_args()

    if args.resumir is not None:
        resumir_guardado(args.resumir, tuple(args.metricas))
        print(args.resumir)
        return 0
    if args.validar_guardado is not None:
        validar_guardado(args.validar_guardado, tuple(args.metricas))
        print("validación guardada correcta:", args.validar_guardado)
        return 0

    if not args.ejecutar:
        print(json.dumps({
            "configuraciones": [asdict(config) for config in crear_plan_experimental()],
            "semillas": SEMILLAS,
            "operadores_provisionales": OPERADORES_B,
            "metricas": args.metricas,
            "corridas_por_metrica": 60,
            "destino_base": str(args.directorio_resultados),
        }, ensure_ascii=False, indent=2))
        return 0

    path = ejecutar(args.directorio_resultados, tuple(args.metricas), args.reanudar)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
