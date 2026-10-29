# Encuesta auditiva — Rol 5

## Estado y procedencia

Se dispone de **diez respuestas reales (P1–P10)**, según la aclaración del equipo del 29 de octubre de 2026. La identificación previa de P2–P10 como simuladas fue un error de documentación. Esta corrección conserva los valores registrados y no representa una nueva aplicación de la encuesta. La fecha de la aclaración no se presenta como fecha de aplicación.

## Objetivo y estímulos

La encuesta recoge la percepción de conservación melódica, semejanza con la referencia de flauta y preferencia entre el individuo de generación 0 y el mejor individuo evolucionado de una misma corrida.

- Referencia: `resultados/audios/referencia_flauta.wav`.
- Generación 0: `resultados/audios/rol5_dia3_stft_N20_E1_pm0.02_seed42/generacion_0_individuo_0.wav`.
- Evolucionado: `resultados/audios/rol5_dia3_stft_N20_E1_pm0.02_seed42/mejor_evolucionado_misma_corrida.wav`.

La corrida corresponde a STFT, población 20, elitismo 1, probabilidad de mutación 0.02 y semilla AG 42. Generación 0 es el individuo inicial de índice 0, reconstruido determinísticamente; no es el mejor individuo inicial ni el audio del Día 2.

## Procedimiento previsto

Reclutar entre 5 y 10 participantes voluntarios, explicar el propósito, asignar códigos anónimos y no registrar nombres. Presentar primero la referencia y luego los dos candidatos en orden aleatorio, manteniendo el mismo equipo y volumen. Puede permitirse una repetición. No normalizar, recortar ni remuestrear los archivos; registrar fecha, equipo, orden e incidencias.

Este es el protocolo propuesto. Las respuestas están registradas, pero el documento no detalla las condiciones efectivas de escucha, el orden aplicado ni el cegamiento; por ello, no se certifica que esos controles se hayan realizado.

## Preguntas

1. ¿El audio evolucionado conserva la melodía del silbido? **Sí / Parcialmente / No.**
2. ¿Cuánto se parece el audio evolucionado a la referencia de flauta? **Escala de 1 a 5** (1 = nada; 5 = muchísimo).
3. Entre generación 0 y evolucionado, ¿cuál se parece más a la referencia? **Generación 0 / Evolucionado / Sin diferencia.**

## Respuestas registradas

| Código | Conserva la melodía | Similitud con flauta (1–5) | Más parecido a la referencia |
|---|---|---:|---|
| P1 | Sí, casi idénticas | 4 | Evolucionado |
| P2 | Parcialmente | 3 | Evolucionado |
| P3 | Sí | 4 | Evolucionado |
| P4 | Parcialmente | 4 | Sin diferencia |
| P5 | Sí | 4 | Evolucionado |
| P6 | Parcialmente | 3 | Generación 0 |
| P7 | Sí | 5 | Evolucionado |
| P8 | Parcialmente | 4 | Evolucionado |
| P9 | Sí | 3 | Sin diferencia |
| P10 | Parcialmente | 4 | Evolucionado |

## Resultados (n=10)

Se utiliza como denominador a los diez participantes. La respuesta textual de P1, “Sí, casi idénticas”, se cuenta en la categoría “Sí”.

- **Conservación de la melodía:** Sí, 5/10 (50%); Parcialmente, 5/10 (50%); No, 0/10 (0%).
- **Similitud media con la referencia:** 38/10 = **3.8/5**.
- **Más parecido a la referencia:** generación 0, 1/10 (10%); evolucionado, **7/10 (70%)**; sin diferencia, 2/10 (20%).

## Conclusión

La mayoría de los participantes consideró el audio evolucionado más parecido a la referencia que el individuo inicial. La conservación melódica recibió respuestas divididas entre “Sí” y “Parcialmente”. Estos resultados aportan evidencia subjetiva favorable al evolucionado en esta comparación concreta, sin demostrar superioridad perceptual general ni equivaler a una puntuación de fitness STFT o croma.

## Limitaciones y registro de aplicación

La muestra informal incluye diez personas, una melodía, una referencia y una corrida. No compara con un audio de búsqueda aleatoria y no permite atribuir la preferencia a un operador específico. Faltan en el registro la fecha y lugar de aplicación, equipo y volumen, orden efectivo de reproducción e incidencias. No se inventan esos datos ni se afirma una evaluación ciega o controlada.

El resumen se incorpora en la sección 5.3 del [informe final](informe/informe_final_ag.md).
