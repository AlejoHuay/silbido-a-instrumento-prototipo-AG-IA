# Instrumento de escucha — Rol 5

## Estado

Instrumento y plantilla preparados para 5–10 participantes. **No se ha aplicado ni contiene respuestas.** La recopilación y cualquier conclusión quedan pendientes del equipo.

## Objetivo y alcance

Recoger una valoración subjetiva de un individuo de generación 0 y del mejor individuo evolucionado de **la misma corrida**, usando la referencia como ancla. El instrumento no compara el AG contra búsqueda aleatoria: no hay audios pareados de baseline guardados. Las valoraciones no sustituyen ni validan el fitness STFT/chroma.

## Preparación de la escucha

1. Reclutar entre 5 y 10 participantes voluntarios, explicar el propósito y solicitar su participación voluntaria. Asignar códigos P01–P10; no registrar nombres.
2. Usar estos tres WAV existentes, sin editarlos ni renombrarlos:
   - Referencia: `resultados/audios/referencia_flauta.wav`.
   - Candidato de generación 0: `resultados/audios/rol5_dia3_stft_N20_E1_pm0.02_seed42/generacion_0_individuo_0.wav`.
   - Mejor candidato evolucionado de esa misma corrida: `resultados/audios/rol5_dia3_stft_N20_E1_pm0.02_seed42/mejor_evolucionado_misma_corrida.wav`.
3. Presentar primero la referencia. La persona coordinadora asigna al azar las etiquetas A/B al audio de generación 0 y al evolucionado para cada participante, y conserva la clave aparte. No revelar las etiquetas reales antes de entregar la hoja.
4. Reproducir A y B en orden aleatorio con el mismo equipo y volumen, permitiendo una repetición. Registrar el equipo y las condiciones si difieren entre participantes.
5. No normalizar, recortar, remuestrear ni regenerar los WAV como parte de la encuesta. Si los archivos o el procedimiento cambian, documentarlo antes de recopilar respuestas.

## Preguntas para cada participante

Para similitud con la referencia: 1 = nada similar, 2 = poco similar, 3 = moderadamente similar, 4 = muy similar, 5 = extremadamente similar. Para calidad percibida: 1 = muy baja, 2 = baja, 3 = intermedia, 4 = alta, 5 = muy alta. Valorar A y B por separado; no hay una respuesta esperada.

| Código anónimo | Similitud A (1–5) | Calidad A (1–5) | Similitud B (1–5) | Calidad B (1–5) | ¿Cuál se acerca más a la referencia? (A / B / igual) | Comentarios opcionales |
|---|---:|---:|---:|---:|---|---|
| P01 |  |  |  |  |  |  |
| P02 |  |  |  |  |  |  |
| P03 |  |  |  |  |  |  |
| P04 |  |  |  |  |  |  |
| P05 |  |  |  |  |  |  |
| P06 |  |  |  |  |  |  |
| P07 |  |  |  |  |  |  |
| P08 |  |  |  |  |  |  |
| P09 |  |  |  |  |  |  |
| P10 |  |  |  |  |  |  |

## Registro de sesión y resumen posterior

- Fecha y lugar: ____________________
- Equipo de reproducción/auriculares: ____________________
- Corrida común: `ejecucion_20261021T184758Z_c5dc431`, STFT, N=20, elitismo=1, pm=0.02, semilla AG=42.
- Orden aleatorio aplicado y clave A/B custodiada por la persona coordinadora: ____________________
- Número de respuestas válidas (debe estar entre 5 y 10): ____________________
- Incidencias o condiciones distintas: ____________________

Dejar el resumen en blanco hasta completar la encuesta. Informar `n`, cantidad y proporción de preferencias A/B/igual, y media y mediana de similitud y calidad por candidato, además de respuestas omitidas e incidencias. Es una comparación exploratoria de una melodía, referencia, configuración y semilla; no compara contra baseline ni permite generalizar a otras melodías. No afirmar preferencia ni calidad perceptual antes de disponer de datos.
