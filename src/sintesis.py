"""Rol 2: síntesis aditiva de una flauta con tres armónicos."""

from pathlib import Path

import numpy as np
import soundfile as sf


FRECUENCIA_MUESTREO = 22050

# Propuesta de interfaz compartida con el Rol 1.
# Cada gen está normalizado al intervalo [0, 1].
NOMBRES_GENES = (
    "amplitud_1",
    "amplitud_2",
    "amplitud_3",
    "ataque_s",
    "liberacion_s",
)

LIMITES_FISICOS = np.array(
    [
        [0.50, 1.00],
        [0.00, 0.50],
        [0.00, 0.30],
        [0.005, 0.150],
        [0.010, 0.200],
    ],
    dtype=float,
)


def _parametros_sintesis(gen):
    """Valida el cromosoma y convierte sus genes a unidades físicas."""
    genes = np.asarray(gen, dtype=float)

    if genes.shape != (len(NOMBRES_GENES),):
        raise ValueError("El cromosoma debe contener exactamente 5 genes.")

    if not np.all(np.isfinite(genes)):
        raise ValueError("Los genes deben ser números finitos.")

    if np.any((genes < 0.0) | (genes > 1.0)):
        raise ValueError("Todos los genes deben estar entre 0 y 1.")

    minimos = LIMITES_FISICOS[:, 0]
    maximos = LIMITES_FISICOS[:, 1]

    return minimos + genes * (maximos - minimos)


def _crear_envolvente(n_muestras, ataque_s, liberacion_s):
    """Construye ataque, sostenimiento y liberación dentro del evento."""
    ataque = max(2, round(ataque_s * FRECUENCIA_MUESTREO))
    liberacion = max(2, round(liberacion_s * FRECUENCIA_MUESTREO))

    # Para notas cortas, ajusta ambos tiempos proporcionalmente.
    if ataque + liberacion > n_muestras:
        proporcion = ataque / (ataque + liberacion)
        ataque = int(round(n_muestras * proporcion))
        ataque = max(2, min(ataque, n_muestras - 2))
        liberacion = n_muestras - ataque

    envolvente = np.ones(n_muestras, dtype=float)

    # Rampas suaves para reducir clics en los extremos.
    envolvente[:ataque] = np.sin(
        np.linspace(0.0, np.pi / 2.0, ataque)
    ) ** 2

    envolvente[-liberacion:] = np.cos(
        np.linspace(0.0, np.pi / 2.0, liberacion)
    ) ** 2

    return envolvente


def sintetizar_instrumento(notas, duraciones, gen):
    """
    Genera audio mono a 22050 Hz.

    Parámetros
    ----------
    notas : secuencia de enteros
        Notas MIDI entre 0 y 127. El valor -1 representa silencio.
    duraciones : secuencia de números
        Segundos por evento, incluyendo ataque y liberación.
    gen : secuencia de 5 números
        Cromosoma normalizado al intervalo [0, 1].

    Retorno
    -------
    np.ndarray
        Audio unidimensional de tipo float32.
    """
    notas = np.asarray(notas, dtype=float)
    duraciones = np.asarray(duraciones, dtype=float)

    if notas.ndim != 1 or duraciones.ndim != 1:
        raise ValueError("Notas y duraciones deben ser unidimensionales.")

    if notas.size == 0 or notas.size != duraciones.size:
        raise ValueError(
            "Debe existir al menos un evento y una duración por evento."
        )

    if not np.all(np.isfinite(notas)):
        raise ValueError("Las notas deben ser números finitos.")

    notas_validas = (
        (notas == np.floor(notas))
        & ((notas == -1) | ((notas >= 0) & (notas <= 127)))
    )

    if not np.all(notas_validas):
        raise ValueError("Usa notas MIDI enteras de 0 a 127 o -1.")

    if (
        not np.all(np.isfinite(duraciones))
        or np.any(duraciones <= 0)
    ):
        raise ValueError("Las duraciones deben ser positivas y finitas.")

    a1, a2, a3, ataque_s, liberacion_s = _parametros_sintesis(gen)
    amplitudes = (a1, a2, a3)

    # Redondear fronteras acumuladas evita acumular errores por evento.
    fronteras = np.rint(
        np.concatenate(([0.0], np.cumsum(duraciones)))
        * FRECUENCIA_MUESTREO
    ).astype(np.int64)

    longitudes = np.diff(fronteras)

    if np.any(longitudes < 4):
        raise ValueError("Cada evento debe durar al menos 4 muestras.")

    audio = np.zeros(int(fronteras[-1]), dtype=float)
    nyquist = FRECUENCIA_MUESTREO / 2.0

    for indice, (nota, n_muestras) in enumerate(zip(notas, longitudes)):
        if nota == -1:
            continue

        frecuencia = 440.0 * 2.0 ** ((nota - 69.0) / 12.0)

        if frecuencia >= nyquist:
            raise ValueError("La nota supera el límite de frecuencia.")

        tiempo = np.arange(n_muestras) / FRECUENCIA_MUESTREO
        evento = np.zeros(n_muestras, dtype=float)

        for armonico, amplitud in enumerate(amplitudes, start=1):
            frecuencia_armonico = armonico * frecuencia

            # Omite armónicos que producirían aliasing.
            if frecuencia_armonico < nyquist:
                evento += amplitud * np.sin(
                    2.0 * np.pi * frecuencia_armonico * tiempo
                )

        evento *= _crear_envolvente(
            n_muestras, ataque_s, liberacion_s
        )

        # Ganancia fija: la suma máxima de amplitudes es 1,8.
        # No normalizar cada individuo por su propio pico.
        evento *= 0.9 / 1.8

        inicio = fronteras[indice]
        fin = fronteras[indice + 1]
        audio[inicio:fin] = evento

    return audio.astype(np.float32)


def guardar_wav(ruta, audio):
    """Guarda audio mono como WAV PCM de 16 bits a 22050 Hz."""
    audio = np.asarray(audio, dtype=float)

    if audio.ndim != 1 or audio.size == 0:
        raise ValueError("El audio debe ser un arreglo mono no vacío.")

    if not np.all(np.isfinite(audio)):
        raise ValueError("El audio contiene valores no finitos.")

    if np.max(np.abs(audio)) > 1.0:
        raise ValueError("El audio supera el rango permitido [-1, 1].")

    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    sf.write(
        str(ruta),
        audio,
        FRECUENCIA_MUESTREO,
        format="WAV",
        subtype="PCM_16",
    )

    return ruta