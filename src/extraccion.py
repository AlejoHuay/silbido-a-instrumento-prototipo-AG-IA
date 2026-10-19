"""Rol 1: Extracción de melodía, detección de pitch y procesamiento de silbidos.

Este módulo implementa el pipeline de procesamiento de audio:
1. Carga y normalización a WAV 22050 Hz mono.
2. Detección de F0 (pitch tracking) con pYIN / autocorrelación.
3. Conversión continua Hz -> notas MIDI discretas.
4. Detección de silencios y segmentación temporal en notas y duraciones.
5. Persistencia en CSV estandarizado (nota_midi, duracion_s).
6. Generador de silbido sintético de referencia para pruebas desacopladas.
7. Diagnóstico de calidad acústica para calibrar grabaciones reales.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import scipy.signal
import soundfile as sf

try:
    import librosa
    TIENE_LIBROSA = True
except ImportError:
    librosa = None  # type: ignore
    TIENE_LIBROSA = False


# Frecuencia de muestreo estándar acordada por el equipo
FRECUENCIA_MUESTREO_DEFAULT = 22050

# Rango típico de frecuencias del silbido humano (C5 ~ 523 Hz a C7 ~ 2093 Hz)
F0_MIN_SILBIDO_HZ = 500.0
F0_MAX_SILBIDO_HZ = 2200.0

# Nombres de notas musicales para visualización y depuración
NOMBRES_NOTAS = ["Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]


def hz_a_midi(f0_hz: float | np.ndarray) -> int | np.ndarray:
    """Convierte frecuencia continua en Hz al entero MIDI más cercano.
    
    Formula estándar: MIDI = round(69 + 12 * log2(f0 / 440))
    Si la frecuencia es <= 0 o NaN, devuelve -1 (silencio).
    """
    if np.isscalar(f0_hz):
        if f0_hz is None or np.isnan(f0_hz) or f0_hz <= 0:
            return -1
        val = 69.0 + 12.0 * math.log2(float(f0_hz) / 440.0)
        return int(round(val))

    arr = np.asarray(f0_hz, dtype=np.float64)
    mascara_valida = (arr > 0) & (~np.isnan(arr))
    resultado = np.full(arr.shape, -1, dtype=np.int32)
    resultado[mascara_valida] = np.round(69.0 + 12.0 * np.log2(arr[mascara_valida] / 440.0)).astype(np.int32)
    return resultado


def midi_a_hz(nota_midi: int | np.ndarray) -> float | np.ndarray:
    """Convierte número MIDI a frecuencia fundamental en Hz.
    
    Formula estándar: f0 = 440 * 2^((MIDI - 69) / 12)
    Si la nota es -1 (silencio), devuelve 0.0 Hz.
    """
    if np.isscalar(nota_midi):
        if int(nota_midi) <= 0:
            return 0.0
        return 440.0 * (2.0 ** ((float(nota_midi) - 69.0) / 12.0))

    arr = np.asarray(nota_midi, dtype=np.int32)
    resultado = np.zeros(arr.shape, dtype=np.float64)
    mascara = arr > 0
    resultado[mascara] = 440.0 * (2.0 ** ((arr[mascara].astype(np.float64) - 69.0) / 12.0))
    return resultado


def nombre_nota_midi(nota_midi: int) -> str:
    """Retorna el nombre musical legible (e.g. 79 -> 'Sol5 (79)')."""
    if nota_midi <= 0:
        return "Silencio (-1)"
    octava = (nota_midi // 12) - 1
    nombre = NOMBRES_NOTAS[nota_midi % 12]
    return f"{nombre}{octava} ({nota_midi})"


def cargar_audio(ruta_wav: str | Path, sr_objetivo: int = FRECUENCIA_MUESTREO_DEFAULT) -> tuple[np.ndarray, int]:
    """Carga un archivo WAV, asegurando formato mono a sr_objetivo en flotantes [-1.0, 1.0]."""
    ruta = Path(ruta_wav)
    if not ruta.is_file():
        raise FileNotFoundError(f"No se encontró el archivo de audio: {ruta}")

    audio, sr = sf.read(str(ruta), dtype="float32")

    # Si es estéreo, promediar a mono
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    # Re-muestreo si es necesario
    if sr != sr_objetivo:
        if TIENE_LIBROSA:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=sr_objetivo)
        else:
            num_muestras_nuevas = int(round(len(audio) * float(sr_objetivo) / sr))
            audio = scipy.signal.resample(audio, num_muestras_nuevas)
        sr = sr_objetivo

    # Normalización de pico para evitar distorsión sin alterar dinámica
    max_pico = np.max(np.abs(audio))
    if max_pico > 0:
        audio = audio / max_pico

    return np.asarray(audio, dtype=np.float32), sr


def guardar_audio(ruta_wav: str | Path, audio: np.ndarray, sr: int = FRECUENCIA_MUESTREO_DEFAULT) -> None:
    """Guarda un arreglo de audio como WAV PCM de 16 bits normalizado."""
    ruta = Path(ruta_wav)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    audio_clip = np.clip(audio, -1.0, 1.0)
    sf.write(str(ruta), audio_clip, sr, subtype="PCM_16")


def detectar_f0(
    audio: np.ndarray,
    sr: int = FRECUENCIA_MUESTREO_DEFAULT,
    fmin: float = F0_MIN_SILBIDO_HZ,
    fmax: float = F0_MAX_SILBIDO_HZ,
    hop_length: int = 256,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Detecta la frecuencia fundamental F0 tramo a tramo.
    
    Retorna:
        f0: Frecuencia en Hz por trama (0 o NaN en tramas no expresadas).
        tiempos: Tiempo en segundos para cada trama.
        sonoridad: Probabilidad o confianza de que la trama contenga voz/silbido.
    """
    if TIENE_LIBROSA:
        # Algoritmo probabilístico YIN (pYIN): estándar de oro para pitch tracking monofónico
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio,
            fmin=fmin,
            fmax=fmax,
            sr=sr,
            hop_length=hop_length,
            fill_na=0.0,
        )
        tiempos = librosa.times_like(f0, sr=sr, hop_length=hop_length)
        return np.asarray(f0), np.asarray(tiempos), np.asarray(voiced_probs)

    # Fallback sin librosa: Autocorrelación normalizada por ventanas
    frame_size = int(sr * 0.04)  # Ventana de 40 ms
    num_frames = (len(audio) - frame_size) // hop_length + 1
    tiempos = np.arange(num_frames) * (hop_length / sr)
    f0 = np.zeros(num_frames, dtype=np.float64)
    sonoridad = np.zeros(num_frames, dtype=np.float64)

    min_lag = int(sr / fmax)
    max_lag = int(sr / fmin)

    for i in range(num_frames):
        inicio = i * hop_length
        trama = audio[inicio : inicio + frame_size] * np.hanning(frame_size)
        energia = np.sum(trama ** 2)
        if energia < 1e-4:
            continue
        
        # Autocorrelación
        corr = np.correlate(trama, trama, mode="full")[frame_size - 1 :]
        corr_valida = corr[min_lag : max_lag]
        if len(corr_valida) == 0:
            continue
        
        pico_idx = np.argmax(corr_valida) + min_lag
        if corr[0] > 0 and (corr[pico_idx] / corr[0]) > 0.4:
            f0[i] = sr / pico_idx
            sonoridad[i] = corr[pico_idx] / corr[0]

    return f0, tiempos, sonoridad


def segmentar_melodia(
    f0: np.ndarray,
    tiempos: np.ndarray,
    sonoridad: np.ndarray,
    umbral_sonoridad: float = 0.5,
    min_duracion_nota_s: float = 0.08,
) -> tuple[np.ndarray, np.ndarray]:
    """Segmenta la curva continua de F0 en una secuencia de notas MIDI y duraciones.
    
    Filtra ruidos espurios y silencios, agrupando tramas contiguas con igual altura.
    
    Retorna:
        notas_midi: Arreglo 1D de enteros con las notas (o -1 para silencios).
        duraciones_s: Arreglo 1D de flotantes con la duración en segundos de cada evento.
    """
    if len(f0) == 0:
        return np.array([], dtype=np.int32), np.array([], dtype=np.float64)

    dt = tiempos[1] - tiempos[0] if len(tiempos) > 1 else 0.01

    # Convertir cada trama a MIDI (o -1 si no tiene suficiente sonoridad)
    midi_tramas = np.full(len(f0), -1, dtype=np.int32)
    mascara_sonora = (sonoridad >= umbral_sonoridad) & (f0 > 0)
    midi_tramas[mascara_sonora] = hz_a_midi(f0[mascara_sonora])

    # Suavizado de mediana móvil de 3 puntos para eliminar saltos aislados de una trama
    if len(midi_tramas) >= 5:
        midi_suave = midi_tramas.copy()
        for i in range(1, len(midi_tramas) - 1):
            if midi_tramas[i - 1] == midi_tramas[i + 1] and midi_tramas[i] != midi_tramas[i - 1]:
                midi_suave[i] = midi_tramas[i - 1]
        midi_tramas = midi_suave

    # Agrupación RLE (Run-Length Encoding)
    eventos_crudos: list[tuple[int, float]] = []
    nota_actual = midi_tramas[0]
    conteo_tramas = 1

    for nota in midi_tramas[1:]:
        if nota == nota_actual:
            conteo_tramas += 1
        else:
            duracion = conteo_tramas * dt
            eventos_crudos.append((int(nota_actual), duracion))
            nota_actual = nota
            conteo_tramas = 1
    eventos_crudos.append((int(nota_actual), conteo_tramas * dt))

    # Filtrar notas transitorias demasiado cortas (glitches)
    eventos_filtrados: list[tuple[int, float]] = []
    for nota, dur in eventos_crudos:
        if nota != -1 and dur < min_duracion_nota_s:
            # Nota espuria: tratar como silencio
            nota = -1
        if eventos_filtrados and eventos_filtrados[-1][0] == nota:
            prev_nota, prev_dur = eventos_filtrados.pop()
            eventos_filtrados.append((prev_nota, prev_dur + dur))
        else:
            eventos_filtrados.append((nota, dur))

    notas = np.array([e[0] for e in eventos_filtrados], dtype=np.int32)
    duraciones = np.array([round(e[1], 3) for e in eventos_filtrados], dtype=np.float64)

    return notas, duraciones


def guardar_melodia_csv(notas_midi: Sequence[int], duraciones_s: Sequence[float], ruta_csv: str | Path) -> None:
    """Guarda la secuencia de eventos melódicos en formato CSV estandarizado."""
    ruta = Path(ruta_csv)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["nota_midi", "duracion_s"])
        for n, d in zip(notas_midi, duraciones_s):
            writer.writerow([int(n), float(round(d, 3))])


def cargar_melodia_csv(ruta_csv: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """Carga la melodía desde CSV retornando (notas_midi, duraciones_s)."""
    ruta = Path(ruta_csv)
    if not ruta.is_file():
        raise FileNotFoundError(f"Archivo de melodía CSV no encontrado: {ruta}")

    notas: list[int] = []
    duraciones: list[float] = []
    with open(ruta, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            notas.append(int(row["nota_midi"]))
            duraciones.append(float(row["duracion_s"]))

    return np.array(notas, dtype=np.int32), np.array(duraciones, dtype=np.float64)


def generar_silbido_sintetico(
    melodia_eventos: Sequence[tuple[int, float]] | None = None,
    sr: int = FRECUENCIA_MUESTREO_DEFAULT,
    con_vibrato: bool = True,
    con_ruido_turbulencia: bool = True,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Genera un audio de silbido sintético realista para pruebas desacopladas.
    
    Emula las propiedades acústicas del silbido humano:
    - Casi una onda senoidal pura en fundamental (f0).
    - Presencia de vibrato natural suave (~5 Hz).
    - Ligero deslizamiento de frecuencia (portamento) y ataque gradual.
    - Soplo / turbulencia suave de aire.
    """
    gen = rng if rng is not None else np.random.default_rng(42)

    # Si no se pasa melodía, usar la acordada: Sol5-La5-Si5-La5-Sol5 con silencios
    if melodia_eventos is None:
        melodia_eventos = [
            (79, 0.60), (-1, 0.10),
            (81, 0.60), (-1, 0.10),
            (83, 0.60), (-1, 0.10),
            (81, 0.60), (-1, 0.10),
            (79, 0.60),
        ]

    partes_audio: list[np.ndarray] = []

    for nota, dur in melodia_eventos:
        num_muestras = int(round(dur * sr))
        if num_muestras <= 0:
            continue

        if nota <= 0:
            # Silencio con leve ruido de fondo ambiente (-60 dB)
            ruido_fondo = gen.normal(0, 0.001, size=num_muestras).astype(np.float32)
            partes_audio.append(ruido_fondo)
            continue

        f0 = float(midi_a_hz(nota))
        t = np.linspace(0.0, dur, num_muestras, endpoint=False, dtype=np.float64)

        # Modulación de frecuencia (vibrato de ~5.5 Hz con profundidad de ~1.5%)
        if con_vibrato and dur > 0.2:
            modulacion_f0 = f0 * (1.0 + 0.015 * np.sin(2.0 * np.pi * 5.5 * t))
        else:
            modulacion_f0 = np.full_like(t, f0)

        fase = 2.0 * np.pi * np.cumsum(modulacion_f0) / sr
        onda_pura = np.sin(fase)

        # Envolvente suave de silbido (ataque senoidal suave y decaimiento natural)
        t_ataque = min(0.06, dur * 0.3)
        t_relajacion = min(0.05, dur * 0.3)
        n_ataque = int(round(t_ataque * sr))
        n_rel = int(round(t_relajacion * sr))
        n_sost = num_muestras - n_ataque - n_rel

        env_ataque = 0.5 * (1.0 - np.cos(np.linspace(0, np.pi, n_ataque)))
        env_sost = np.ones(max(0, n_sost))
        env_rel = 0.5 * (1.0 + np.cos(np.linspace(0, np.pi, n_rel)))
        envolvente = np.concatenate([env_ataque, env_sost, env_rel])[:num_muestras]

        audio_nota = onda_pura * envolvente

        # Turbulencia de aire (ruido blanco filtrado paso-alto)
        if con_ruido_turbulencia:
            ruido = gen.normal(0, 0.03, size=num_muestras)
            audio_nota += ruido * envolvente

        partes_audio.append(audio_nota.astype(np.float32))

    audio_completo = np.concatenate(partes_audio)
    # Normalizar a 0.95 de pico
    max_val = np.max(np.abs(audio_completo))
    if max_val > 0:
        audio_completo = (audio_completo / max_val) * 0.95

    return audio_completo.astype(np.float32)


def diagnosticar_audio_silbido(audio: np.ndarray, sr: int = FRECUENCIA_MUESTREO_DEFAULT) -> dict[str, Any]:
    """Inspecciona la calidad de una grabación de silbido para verificación y calibración.
    
    Proporciona feedback diagnóstico sobre saturación, relación señal/ruido y consistencia.
    """
    pico = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(audio ** 2)))
    duracion = len(audio) / sr

    # Detección de clipping (muestras pegadas a +-1.0)
    muestras_clipeadas = int(np.sum(np.abs(audio) >= 0.999))
    porcentaje_clipping = (muestras_clipeadas / len(audio)) * 100.0

    # Estimación de piso de ruido en segmentos de mínima energía
    tam_trama = int(sr * 0.05)
    num_tramas = len(audio) // tam_trama
    if num_tramas > 0:
        energias = [np.mean(audio[i * tam_trama : (i + 1) * tam_trama] ** 2) for i in range(num_tramas)]
        piso_ruido_rms = float(np.sqrt(min(energias)))
        snr_estimado_db = 20.0 * math.log10((rms + 1e-9) / (piso_ruido_rms + 1e-9))
    else:
        piso_ruido_rms = 0.0
        snr_estimado_db = 0.0

    es_apto = pico > 0.1 and porcentaje_clipping < 0.5 and snr_estimado_db > 15.0

    alertas: list[str] = []
    if pico < 0.2:
        alertas.append("Volumen muy bajo: se recomienda aumentar ganancia del micrófono.")
    if porcentaje_clipping > 0.1:
        alertas.append("Saturación detectada: bajar el volumen de entrada para evitar distorsión armónica.")
    if snr_estimado_db < 15.0:
        alertas.append("Ruido ambiental alto: se recomienda grabar en una habitación más silenciosa.")

    return {
        "duracion_segundos": round(duracion, 2),
        "frecuencia_muestreo": sr,
        "amplitud_pico": round(pico, 3),
        "rms": round(rms, 4),
        "porcentaje_clipping": round(porcentaje_clipping, 2),
        "snr_estimado_db": round(snr_estimado_db, 1),
        "es_apto_para_ag": es_apto,
        "alertas": alertas,
    }
