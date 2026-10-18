"""Rol 2: fitness espectral y métrica alternativa."""

import numpy as np
from scipy.signal import stft

from .sintesis import (
    FRECUENCIA_MUESTREO,
    sintetizar_instrumento,
)


N_FFT = 2048
SALTO = 256
PISO_DB = -80.0
ESCALA_ERROR_DB = 10.0


def _validar_audio(audio, nombre):
    """Comprueba el formato del audio utilizado para los cálculos."""
    audio = np.asarray(audio, dtype=float)

    if audio.ndim != 1 or audio.size < N_FFT:
        raise ValueError(
            f"{nombre} debe ser mono y contener al menos "
            f"{N_FFT} muestras."
        )

    if not np.all(np.isfinite(audio)):
        raise ValueError(f"{nombre} contiene valores no finitos.")

    return audio


def _validar_par(audio, referencia):
    """Exige audios previamente alineados y de igual longitud."""
    audio = _validar_audio(audio, "El audio sintetizado")
    referencia = _validar_audio(referencia, "La referencia")

    if audio.size != referencia.size:
        raise ValueError(
            "Los audios deben tener igual cantidad de muestras. "
            "Prepara la referencia con las mismas notas, duraciones "
            "y silencios; no recortes automáticamente los audios."
        )

    if np.max(np.abs(referencia)) <= 1e-8:
        raise ValueError("La referencia no puede ser completamente silenciosa.")

    return audio, referencia


def _espectro(audio):
    """Calcula la magnitud de una STFT con ventana Hann."""
    frecuencias, _, transformada = stft(
        audio,
        fs=FRECUENCIA_MUESTREO,
        window="hann",
        nperseg=N_FFT,
        noverlap=N_FFT - SALTO,
        nfft=N_FFT,
        boundary="zeros",
        padded=True,
    )

    return frecuencias, np.abs(transformada)


def _a_db(magnitud):
    """
    Convierte amplitudes a dB con referencia fija de amplitud 1.

    Se utiliza la misma escala para todos los individuos.
    No se normaliza cada espectrograma por su propio máximo.
    """
    minimo = 10.0 ** (PISO_DB / 20.0)

    return 20.0 * np.log10(
        np.maximum(magnitud, minimo)
    )


def _calcular_croma(frecuencias, magnitud):
    """
    Agrupa la energía espectral en 12 clases de altura.

    Orden:
    Do, Do#, Re, Re#, Mi, Fa, Fa#, Sol, Sol#, La, La#, Si.

    Es una implementación básica de croma mediante bins de STFT.
    """
    mascara = (
        (frecuencias >= 50.0)
        & (frecuencias <= 5000.0)
    )

    frecuencias_validas = frecuencias[mascara]
    energia = magnitud[mascara] ** 2

    midi = np.rint(
        69.0 + 12.0 * np.log2(frecuencias_validas / 440.0)
    ).astype(int)

    clases = midi % 12
    croma = np.zeros((12, magnitud.shape[1]), dtype=float)

    for clase in range(12):
        croma[clase] = energia[clases == clase].sum(axis=0)

    return croma


def _similitud_croma(croma_audio, croma_referencia):
    """Promedia la similitud coseno entre cuadros temporales."""
    norma_audio = np.linalg.norm(croma_audio, axis=0)
    norma_referencia = np.linalg.norm(croma_referencia, axis=0)

    activo_audio = norma_audio > 1e-12
    activo_referencia = norma_referencia > 1e-12

    ambos_activos = activo_audio & activo_referencia
    ambos_silenciosos = ~activo_audio & ~activo_referencia

    similitudes = np.zeros(croma_audio.shape[1], dtype=float)

    # Un silencio coincidente se considera una coincidencia.
    similitudes[ambos_silenciosos] = 1.0

    producto = np.sum(
        croma_audio[:, ambos_activos]
        * croma_referencia[:, ambos_activos],
        axis=0,
    )

    denominador = (
        norma_audio[ambos_activos]
        * norma_referencia[ambos_activos]
    )

    similitudes[ambos_activos] = producto / denominador

    return float(np.mean(np.clip(similitudes, 0.0, 1.0)))


def evaluar_audio(audio, referencia):
    """
    Compara dos audios mono a 22050 Hz, alineados y de igual longitud.

    Retorna
    -------
    dict
        error_stft_db:
            Error absoluto medio entre espectrogramas en dB.
            Menor es mejor.
        fitness_stft:
            1 / (1 + error_stft_db / 10).
            Mayor es mejor; rango (0, 1].
        fitness_croma:
            Similitud coseno media del croma.
            Mayor es mejor; rango [0, 1].
    """
    audio, referencia = _validar_par(audio, referencia)

    frecuencias, magnitud_audio = _espectro(audio)
    _, magnitud_referencia = _espectro(referencia)

    db_audio = _a_db(magnitud_audio)
    db_referencia = _a_db(magnitud_referencia)

    error_db = float(
        np.mean(np.abs(db_audio - db_referencia))
    )

    fitness_stft = 1.0 / (
        1.0 + error_db / ESCALA_ERROR_DB
    )

    croma_audio = _calcular_croma(
        frecuencias, magnitud_audio
    )
    croma_referencia = _calcular_croma(
        frecuencias, magnitud_referencia
    )

    fitness_croma = _similitud_croma(
        croma_audio, croma_referencia
    )

    return {
        "error_stft_db": error_db,
        "fitness_stft": float(fitness_stft),
        "fitness_croma": fitness_croma,
    }


def evaluar_individuo(
    gen,
    notas,
    duraciones,
    referencia,
    metrica="stft",
):
    """
    Interfaz para el AG: recibe un cromosoma y devuelve su aptitud.

    metrica='stft': comparación de espectrogramas en dB.
    metrica='croma': comparación de clases de altura.

    Los cromosomas inválidos generan ValueError.
    Los operadores deben producir individuos válidos.
    """
    if metrica not in ("stft", "croma"):
        raise ValueError("La métrica debe ser 'stft' o 'croma'.")

    audio = sintetizar_instrumento(
        notas, duraciones, gen
    )

    resultados = evaluar_audio(audio, referencia)

    return resultados[f"fitness_{metrica}"]
