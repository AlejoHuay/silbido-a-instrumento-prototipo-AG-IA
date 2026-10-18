# Día 1 — Diseño del Algoritmo Genético

Estado: instrumento, melodía y formato de datos definidos.
Pendiente: completar el diseño del AG y las firmas del equipo.
La versión de entrega debe condensarse en una página.

## Objetivo

Convertir un silbido humano en la misma melodía interpretada
por una flauta sintetizada, evolucionando sus parámetros
mediante un Algoritmo Genético implementado desde cero.

## Instrumento y silbido

- Instrumento objetivo: flauta.
- Entrada: silbido humano grabado por un integrante del equipo.
- Melodía: Sol–La–Si–La–Sol.
- Registro previsto: Sol5–La5–Si5–La5–Sol5.
- Notas MIDI previstas: 79–81–83–81–79.
- Duración orientativa: 0,6 segundos por nota y separaciones
  de 0,1 segundos; aproximadamente 4 segundos en total.
- Grabación sin acompañamiento, ruido marcado ni saturación.
- El registro puede ajustarse a la comodidad del integrante.
- El Rol 1 extraerá las notas, duraciones y silencios reales.
  Los valores previstos no reemplazan la detección del audio.

Se elige flauta para comenzar con la síntesis aditiva básica
de tres armónicos solicitada para el Día 1 y posteriormente
ajustar sus parámetros. El timbre se verificará auditivamente.

## Referencia instrumental

El equipo no dispone de una flauta física. Se conseguirán
muestras reales de flauta sola, con permiso de uso y,
preferiblemente, de una misma colección e instrumento.

El Rol 2 preparará la referencia con las notas, octava,
duraciones y silencios detectados por el Rol 1.
Documentará la fuente, licencia y ajustes realizados.

La referencia será independiente del sintetizador optimizado.
Se conservarán las muestras originales.

Estado: muestras y referencia pendientes de obtener.

## Formato compartido de datos

| Dato | Formato acordado |
|---|---|
| Audio de trabajo y salida | WAV mono, 22050 Hz, PCM de 16 bits |
| Audio para cálculos | Arreglo NumPy unidimensional de flotantes |
| Notas | Arreglo unidimensional de enteros MIDI |
| Silencios | Valor -1 en el arreglo de notas |
| Duraciones | Arreglo de segundos, una duración por evento |
| Eventos guardados | CSV: nota_midi,duracion_s |
| Cromosoma | Parámetros del timbre, pendientes de definir |

Los arreglos de notas y duraciones tendrán igual longitud.
Cada evento representará una nota o un silencio.
La melodía extraída permanecerá fija durante la evolución.

Archivos de trabajo:

- datos/audio/silbidos/silbido_01.wav
- datos/audio/referencias/flauta_referencia_01.wav
- datos/procesados/melodia_01.csv

Se conservarán los originales cuando sea necesario convertir
los audios al formato requerido.

## Diseño del AG pendiente de completar

- Representación, genes, unidades y límites: Roles 1 y 2.
- Síntesis inicial: aditiva, con tres armónicos; Rol 2.
- Fitness principal: comparación de espectrogramas STFT en dB;
  escala y sentido de optimización pendientes del Rol 2.
- Segunda métrica: croma, conforme al cronograma.
- Selección inicial: torneo con k=3; Rol 3.
- Segunda selección: ruleta o SUS, pendiente de elegir.
- Cruces: blend-α y uniforme.
- Mutaciones: elegir dos entre gaussiana, uniforme y no uniforme,
  conforme a la aclaración del docente.
- Población inicial, elitismo y parada: pendientes del Rol 4.
- Interfaces, copias y manejo de semillas: acuerdo Roles 3 y 4.
- Plan experimental: Roles 4 y 5; tres combinaciones de operadores,
  al menos doce configuraciones, entre cinco y diez semillas
  y comparación con búsqueda aleatoria.
- Variabilidad: calcular varianza y desviación de las corridas,
  conforme a la aclaración del docente.

El contrato detallado se registrará en
documentacion/contratos/contrato_cromosoma.md.

## Responsabilidades del Día 1

- Rol 1: capturar el silbido, detectar pitch y esbozar los genes.
- Rol 2: preparar síntesis básica, conseguir muestras y acordar
  la relación entre genes y sonido con el Rol 1.
- Rol 3: preparar torneo y verificar compatibilidad del cromosoma.
- Rol 4: preparar pseudocódigo y acordar operadores con el Rol 3.
- Rol 5: configurar el notebook reproducible y acordar
  el plan experimental con el Rol 4.
- Los Roles 3 y 5 corresponden al mismo integrante.

## Firmas

- Rol 1 — Nombre y firma:
- Rol 2 — Nombre y firma:
- Roles 3 y 5 — Nombre y firma:
- Rol 4 — Nombre y firma:
- Fecha: