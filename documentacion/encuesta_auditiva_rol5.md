# Encuesta auditiva — Rol 5

## Estado y procedencia de las respuestas

Hay **una respuesta real**, P1, proporcionada para este registro. P2–P10 son **simulaciones ficticias** creadas únicamente para mostrar una tabla completa y ejemplificar los cálculos. No se han recopilado respuestas reales de P2–P10; la encuesta real tiene n=1 y su aplicación a 5–10 personas sigue pendiente. No atribuir los datos simulados a participantes.

## Objetivo y alcance

Valorar si el audio evolucionado conserva la melodía del silbido, cuánto se parece a la referencia de flauta y cuál de dos candidatos —generación 0 o evolucionado— se acerca más a la referencia. Se usan la generación 0 y el mejor individuo evolucionado de la misma corrida, con la referencia como ancla. Esto no compara AG con búsqueda aleatoria y no sustituye las métricas STFT/chroma ni demuestra calidad perceptual general.

## Estímulos y procedimiento

Usar los tres WAV, sin modificarlos:

- Referencia: `resultados/audios/referencia_flauta.wav`.
- Generación 0: `resultados/audios/rol5_dia3_stft_N20_E1_pm0.02_seed42/generacion_0_individuo_0.wav`.
- Evolucionado: `resultados/audios/rol5_dia3_stft_N20_E1_pm0.02_seed42/mejor_evolucionado_misma_corrida.wav`.

La corrida es `ejecucion_20261021T184758Z_c5dc431`, STFT, población 20, elitismo 1, probabilidad de mutación 0.02, semilla AG 42. El audio de generación 0 es el individuo inicial índice 0, reconstruido determinísticamente; no es el mejor individuo inicial ni el audio de la demostración del Día 2.

Para una aplicación real, reclutar voluntarios, explicar el propósito, asignar códigos anónimos (P1–P10) y no recoger nombres. Presentar primero la referencia. Luego reproducir generación 0 y evolucionado en orden aleatorio, con igual equipo y volumen. Si se oculta la identidad de los candidatos, la persona coordinadora conserva la clave hasta recoger respuestas. Permitir una repetición. No normalizar, recortar ni remuestrear. Registrar fecha, condiciones e incidencias.

## Preguntas

1. ¿El audio evolucionado conserva la melodía del silbido? **Sí / Parcialmente / No.**
2. ¿Cuánto se parece el audio evolucionado a la referencia de flauta? **Escala de 1 a 5** (1 = nada; 5 = muchísimo).
3. Entre generación 0 y evolucionado, ¿cuál se parece más a la referencia? **Generación 0 / Evolucionado / Sin diferencia.**

## Registro de respuestas

P1 es la respuesta real comunicada. Cada fila P2–P10 se identifica como **SIMULADA** y no corresponde a una persona encuestada.

| Código | Estado | Conserva melodía (P1) | Similitud con flauta (P2, 1–5) | Más parecido a referencia (P3) |
|---|---|---|---:|---|
| P1 | REAL | Sí, casi idénticas | 4 | Evolucionado |
| P2 | **SIMULADA** | Parcialmente | 3 | Evolucionado |
| P3 | **SIMULADA** | Sí | 4 | Evolucionado |
| P4 | **SIMULADA** | Parcialmente | 4 | Sin diferencia |
| P5 | **SIMULADA** | Sí | 4 | Evolucionado |
| P6 | **SIMULADA** | Parcialmente | 3 | Generación 0 |
| P7 | **SIMULADA** | Sí | 5 | Evolucionado |
| P8 | **SIMULADA** | Parcialmente | 4 | Evolucionado |
| P9 | **SIMULADA** | Sí | 3 | Sin diferencia |
| P10 | **SIMULADA** | Parcialmente | 4 | Evolucionado |

## Resumen del resultado real — solo P1

Denominador: una respuesta real válida.

- Conservación de melodía: Sí (respuesta textual: “Sí, casi idénticas”) **1/1 = 100%**; Parcialmente **0/1 = 0%**; No **0/1 = 0%**.
- Similitud media con la referencia: **4/5** (n=1).
- Preferencia: generación 0 **0/1 = 0%**; evolucionado **1/1 = 100%**; sin diferencia **0/1 = 0%**.

Es una observación individual. No permite generalizar ni estimar variabilidad entre oyentes.

## Ejemplo simulado — P1 real más P2–P10 simuladas

Este ejemplo combina P1 con nueve filas ficticias para ilustrar el resumen de una tabla de diez personas. No es un resultado experimental.

- Conservación de melodía: Sí **5/10 = 50%**; Parcialmente **5/10 = 50%**; No **0/10 = 0%**. La respuesta “Sí, casi idénticas” de P1 se cuenta en Sí.
- Similitud media con la referencia: **38/10 = 3.8/5**.
- Preferencia: generación 0 **1/10 = 10%**; evolucionado **7/10 = 70%**; sin diferencia **2/10 = 20%**.

Los porcentajes y el promedio anteriores describen la mezcla real/simulada diseñada para el ejemplo. No describen diez participantes reales, no son una conclusión perceptual y no demuestran resultados del AG.

## Registro para una aplicación real futura

- Fecha y lugar: ____________________
- Equipo/auriculares y volumen: ____________________
- Orden de reproducción: ____________________
- Número de respuestas reales válidas: ____________________
- Incidencias: ____________________

Al sustituir las filas simuladas por respuestas reales, conservar separadamente los registros originales, indicar el denominador de cada cálculo y resumir frecuencias/porcentajes, promedio de P2 y preferencias de P3. No completar respuestas faltantes ni mezclar datos simulados con los resultados reales.
