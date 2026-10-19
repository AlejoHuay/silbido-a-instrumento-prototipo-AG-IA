"""Rol 2: síntesis aditiva de una flauta con tres armónicos."""

from pathlib import Path

import numpy as np
import soundfile as sf

from .representacion import (
    GENES_SCHEMA,
    decodificar,
    validar_individuo,
)


FRECUENCIA_MUESTREO = 22050

# Ganancia fija basada en los límites del contrato compartido.
MAXIMO_AMPLITUD = sum(
    especificacion.max_val
    for especificacion in GENES_SCHEMA
    if especificacion.nombre in (
        "amp_arm1",
        "amp_arm2",
        "amp_arm3",
        "ruido_soplo",
    )
)


def _parametros_sintesis(gen):
    """Valida los ocho genes y devuelve sus valores físicos."""
    genes = np.asarray(gen, dtype=float)

    valido, mensaje = validar_individuo(genes)

    if not valido:
        raise ValueError(f"Cromosoma inválido: {mensaje}")

    return decodificar(genes)


def _crear_envolvente(n_muestras, parametros):
    """
    Construye una envolvente ADSR dentro de la duración del evento.

    Si ataque, decaimiento y relajación no caben, sus tiempos
    se reducen proporcionalmente sin extender la nota.
    """
    duracion = (n_muestras - 1) / FRECUENCIA_MUESTREO

    etapas = np.array([
        parametros["ataque_s"],
        parametros["decaimiento_s"],
        parametros["relajacion_s"],
    ], dtype=float)

    if etapas.sum() > duracion:
        etapas *= duracion / etapas.sum()

    ataque, decaimiento, relajacion = etapas
    sostenido = parametros["sostenido_rel"]

    puntos_tiempo = [
        0.0,
        ataque,
        ataque + decaimiento,
        max(ataque + decaimiento, duracion - relajacion),
        duracion,
    ]

    puntos_amplitud = [
        0.0,
        1.0,
        sostenido,
        sostenido,
        0.0,
    ]

    tiempo = np.arange(n_muestras) / FRECUENCIA_MUESTREO

    return np.interp(
        tiempo,
        puntos_tiempo,
        puntos_amplitud,
    )


def sintetizar_instrumento(
    notas,
    duraciones,
    gen,
    *,
    semilla=2026,
):
    """
    Genera audio mono float32 a 22050 Hz.

    notas:
        Notas MIDI enteras entre 0 y 127.
        El valor -1 representa silencio.
    duraciones:
        Segundos por evento, incluyendo toda la envolvente ADSR.
    gen:
        Cromosoma normalizado de ocho genes definido por el Rol 1.
    semilla:
        Semilla fija para que el ruido de soplo sea reproducible.
    """
    parametros = _parametros_sintesis(gen)

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

    fronteras = np.rint(
        np.concatenate(([0.0], np.cumsum(duraciones)))
        * FRECUENCIA_MUESTREO
    ).astype(np.int64)

    longitudes = np.diff(fronteras)

    if np.any(longitudes < 4):
        raise ValueError("Cada evento debe durar al menos 4 muestras.")

    audio = np.zeros(int(fronteras[-1]), dtype=float)
    rng = np.random.default_rng(semilla)
    nyquist = FRECUENCIA_MUESTREO / 2.0

    amplitudes = (
        parametros["amp_arm1"],
        parametros["amp_arm2"],
        parametros["amp_arm3"],
    )

    for indice, (nota, n_muestras) in enumerate(
        zip(notas, longitudes)
    ):
        if nota == -1:
            continue

        frecuencia = 440.0 * 2.0 ** ((nota - 69.0) / 12.0)

        if frecuencia >= nyquist:
            raise ValueError("La nota supera el límite de frecuencia.")

        tiempo = np.arange(n_muestras) / FRECUENCIA_MUESTREO
        evento = np.zeros(n_muestras, dtype=float)

        for armonico, amplitud in enumerate(amplitudes, start=1):
            frecuencia_armonico = armonico * frecuencia

            if frecuencia_armonico < nyquist:
                evento += amplitud * np.sin(
                    2.0 * np.pi * frecuencia_armonico * tiempo
                )

        # Modelo inicial de ruido de soplo, acotado entre -1 y 1.
        evento += parametros["ruido_soplo"] * rng.uniform(
            -1.0,
            1.0,
            n_muestras,
        )

        evento *= _crear_envolvente(n_muestras, parametros)

        # Misma ganancia para todos los individuos.
        evento *= 0.9 / MAXIMO_AMPLITUD

        inicio = fronteras[indice]
        fin = fronteras[indice + 1]

        audio[inicio:fin] = evento

    return audio.astype(np.float32)


def guardar_wav(ruta, audio):
    """Guarda WAV mono a 22050 Hz, PCM de 16 bits."""
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