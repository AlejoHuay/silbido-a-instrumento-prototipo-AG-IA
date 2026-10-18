# Del silbido al instrumento

Prototipo académico de síntesis instrumental mediante un
Algoritmo Genético implementado desde cero.

## Equipo

| Integrante | Responsabilidad |
|---|---|
| Por completar | Rol 1: representación y extracción |
| Por completar | Rol 2: síntesis y fitness |
| Por completar | Roles 3 + 5: operadores, evaluación e integración |
| Por completar | Rol 4: dinámica poblacional |

## Objetivo

Extraer una melodía de un silbido WAV y reproducirla con
un instrumento cuyos parámetros evolucionan mediante un AG.

## Entorno

- Python 3.10+.
- Google Colab o Jupyter.
- Audio: WAV mono, 22050 Hz, PCM de 16 bits.
- Prohibidos frameworks de AG y modelos preentrenados.
- No utilizar deep learning.

## Dependencias

Las dependencias externas están en requirements.txt.
No se necesitan todas en cada módulo.

Instalación:

    python -m pip install -r requirements.txt

## Organización

- notebooks/: trabajo por rol y notebook de integración.
- src/: funciones compartidas; evitar duplicarlas en notebooks.
- datos/audio/silbidos/: entradas originales.
- datos/audio/referencias/: referencias instrumentales.
- datos/procesados/: notas, duraciones y datos derivados.
- resultados/: mediciones, tablas, figuras y audios.
- documentacion/: contratos, diseño, informe y presentación.

## Acuerdos pendientes

Consultar documentacion/contratos/contrato_cromosoma.md
y documentacion/diseno/dia1.md.

## Reproducibilidad

- Usar rutas relativas a la raíz del repositorio.
- Registrar semillas y configuraciones.
- Identificar la versión del código usada en cada experimento.
- Conservar entradas y resultados necesarios para reproducirlo.
- Verificar el notebook integrado desde un entorno limpio.
- Registrar las versiones de dependencias realmente verificadas.
- No publicar resultados de ejemplo como mediciones reales.

## Trabajo en equipo

- Una rama de trabajo por rol o tarea.
- Compartir cambios mediante commits y revisión.
- Coordinar modificaciones de interfaces antes de integrarlas.
- No sobrescribir el trabajo de otros integrantes.
- Coordinar la edición de 00_integracion.ipynb con Roles 3 + 5.

## Entregables

- Día 1: diseño del AG de una página, firmado por todos.
- Día 2: notebook que ejecute el proceso completo.
- Día 3: tablas, gráficos y conclusiones preliminares.
- Día 4: notebook, audios, informe y presentación.

Entrega final:
- Notebook reproducible.
- WAV: silbido, generación 0, referencia y mejor evolucionado.
- Informe de 3–4 páginas con cinco respuestas teóricas.
- Presentación de 10 minutos con demo.

## Estado

Estructura inicial. Todavía no hay implementación funcional.