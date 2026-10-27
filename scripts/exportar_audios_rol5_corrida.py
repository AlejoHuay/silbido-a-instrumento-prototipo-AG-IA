"""Exporta audios inicial y final desde una corrida Rol 5 ya guardada.

Reconstruye de forma determinista la población de generación 0 a partir del
código versionado y la semilla registrada. No ejecuta el AG ni evalúa fitness.
La carpeta de destino se crea en modo exclusivo para preservar archivos previos.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.algoritmo_genetico import inicializar_poblacion
from src.configuracion import ConfiguracionAG
from src.extraccion import cargar_melodia_csv
from src.sintesis import FRECUENCIA_MUESTREO, sintetizar_instrumento


CORRIDA = (
    RAIZ
    / "resultados/rol5/dia3_factorial/ejecucion_20261021T184758Z_c5dc431"
)
METRICA = "stft"
NOMBRE_CHECKPOINT = "ag_N20_E1_pm0.02_seed42.json"
RUTA_CHECKPOINT = CORRIDA / METRICA / NOMBRE_CHECKPOINT
RUTA_MANIFIESTO = CORRIDA / "manifiesto.json"
RUTA_MELODIA = RAIZ / "datos/procesados/melodia_01.csv"
RUTA_REFERENCIA = RAIZ / "datos/audio/referencias/flauta_referencia_01.wav"
CARPETA_SALIDA = (
    RAIZ / "resultados/audios/rol5_dia3_stft_N20_E1_pm0.02_seed42"
)
SEMILLA_SINTESIS = 2026
INDICE_INDIVIDUO_GENERACION_0 = 0


def _sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def _exportar_wav_exclusivo(ruta: Path, audio: np.ndarray) -> None:
    if audio.ndim != 1 or not np.all(np.isfinite(audio)):
        raise ValueError(f"Audio inválido (mono/finito requerido): {ruta}")
    if audio.size == 0 or np.max(np.abs(audio)) > 1.0:
        raise ValueError(f"Audio fuera de rango o vacío: {ruta}")
    with ruta.open("xb") as archivo:
        sf.write(
            archivo,
            audio,
            FRECUENCIA_MUESTREO,
            format="WAV",
            subtype="PCM_16",
        )


def main() -> int:
    manifiesto = json.loads(RUTA_MANIFIESTO.read_text(encoding="utf-8"))
    checkpoint = json.loads(RUTA_CHECKPOINT.read_text(encoding="utf-8"))

    if checkpoint["metodo"] != "algoritmo_genetico" or checkpoint["metrica"] != METRICA:
        raise ValueError("El checkpoint no corresponde a AG/STFT.")
    if checkpoint["operadores"].get("cruce") != "uniforme":
        raise ValueError("El checkpoint no registra la combinación B esperada.")

    # El estado inicial depende de estos módulos; exigir las huellas del registro.
    hashes_codigo = manifiesto["sha256_codigo"]
    for nombre, esperado in hashes_codigo.items():
        if nombre.startswith("src/"):
            actual = _sha256(RAIZ / nombre)
            if actual != esperado:
                raise ValueError(f"El código cambió respecto al experimento: {nombre}")

    for ruta in (RUTA_MELODIA, RUTA_REFERENCIA):
        relativo = ruta.relative_to(RAIZ).as_posix()
        if _sha256(ruta) != manifiesto["datos"][relativo]:
            raise ValueError(f"El dato de entrada cambió respecto al experimento: {relativo}")

    configuracion = ConfiguracionAG(**checkpoint["configuracion"])
    rng = np.random.default_rng(configuracion.semilla)
    poblacion_inicial = inicializar_poblacion(configuracion, rng=rng)
    if (
        poblacion_inicial.shape != (configuracion.tam_poblacion, 8)
        or not np.all(np.isfinite(poblacion_inicial))
        or np.any((poblacion_inicial < 0.0) | (poblacion_inicial > 1.0))
    ):
        raise ValueError("La población inicial reconstruida no es válida.")

    diversidad_reconstruida = float(np.mean(np.std(poblacion_inicial, axis=0)))
    historial_0 = next(
        fila for fila in checkpoint["historial"] if fila["generacion"] == 0
    )
    if not np.isclose(
        diversidad_reconstruida,
        float(historial_0["diversidad_genetica"]),
        rtol=0.0,
        atol=1e-15,
    ):
        raise ValueError("La población no coincide con la diversidad guardada en generación 0.")

    notas, duraciones = cargar_melodia_csv(RUTA_MELODIA)
    gen0 = poblacion_inicial[INDICE_INDIVIDUO_GENERACION_0].copy()
    mejor_final = np.asarray(
        checkpoint["resultado_completo"]["mejor_individuo"], dtype=np.float64
    )
    audio_gen0 = sintetizar_instrumento(
        notas, duraciones, gen0, semilla=SEMILLA_SINTESIS
    )
    audio_final = sintetizar_instrumento(
        notas, duraciones, mejor_final, semilla=SEMILLA_SINTESIS
    )

    # La carpeta completa es una unidad nueva; no se mezcla con WAV históricos.
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=False)
    ruta_gen0 = CARPETA_SALIDA / "generacion_0_individuo_0.wav"
    ruta_final = CARPETA_SALIDA / "mejor_evolucionado_misma_corrida.wav"
    _exportar_wav_exclusivo(ruta_gen0, audio_gen0)
    _exportar_wav_exclusivo(ruta_final, audio_final)

    salidas = {}
    for nombre, ruta in (("generacion_0", ruta_gen0), ("mejor_evolucionado", ruta_final)):
        info = sf.info(ruta)
        if info.format != "WAV" or info.subtype != "PCM_16" or info.channels != 1:
            raise ValueError(f"El WAV exportado no cumple el formato esperado: {ruta}")
        salidas[nombre] = {
            "ruta": ruta.relative_to(RAIZ).as_posix(),
            "sha256": _sha256(ruta),
            "formato": info.format,
            "subtipo": info.subtype,
            "canales": info.channels,
            "frecuencia_muestreo": info.samplerate,
            "muestras": info.frames,
            "duracion_s": info.duration,
        }

    evidencia = {
        "proposito": "Exportar audio sin repetir AG ni evaluar fitness.",
        "corrida": {
            "id": CORRIDA.name,
            "checkpoint": RUTA_CHECKPOINT.relative_to(RAIZ).as_posix(),
            "metrica": checkpoint["metrica"],
            "semilla_ag": checkpoint["semilla"],
            "configuracion": checkpoint["configuracion"],
            "operadores": checkpoint["operadores"],
            "fitness_mejor_final_guardado": checkpoint["resultado_completo"]["mejor_fitness"],
        },
        "generacion_0": {
            "poblacion_reconstruida_deterministicamente": True,
            "fuente_inicializacion": "src/algoritmo_genetico.inicializar_poblacion + src/representacion.generar_poblacion_inicial",
            "indice_individuo": INDICE_INDIVIDUO_GENERACION_0,
            "cromosoma": gen0.tolist(),
            "diversidad_guardada": historial_0["diversidad_genetica"],
            "diversidad_reconstruida": diversidad_reconstruida,
        },
        "mejor_evolucionado": {
            "cromosoma": mejor_final.tolist(),
            "origen": "resultado_completo.mejor_individuo del checkpoint",
        },
        "sintesis": {
            "funcion": "src.sintesis.sintetizar_instrumento",
            "melodia": RUTA_MELODIA.relative_to(RAIZ).as_posix(),
            "melodia_sha256": _sha256(RUTA_MELODIA),
            "referencia_sha256": _sha256(RUTA_REFERENCIA),
            "semilla_ruido_sintesis": SEMILLA_SINTESIS,
        },
        "salidas": salidas,
    }
    ruta_evidencia = CARPETA_SALIDA / "manifiesto_audios.json"
    with ruta_evidencia.open("x", encoding="utf-8") as archivo:
        json.dump(evidencia, archivo, indent=2, ensure_ascii=False)
        archivo.write("\n")

    print(json.dumps(evidencia, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
