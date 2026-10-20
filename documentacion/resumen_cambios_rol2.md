# Rol 2 — Cambios y comprobación del diseño del Día 1

## Estado del documento

Este resumen describe los cambios preparados para el notebook
del Rol 2 y las comprobaciones pendientes del diseño conjunto.

Su aplicación y ejecución final deben confirmarse en el proyecto.
No se verificaron nuevos commits, publicación ni integración en main.

## 1. Archivos involucrados

- notebooks/02_rol2_sintesis_fitness.ipynb
- documentacion/diseno/diseno_completo_ag_dia1.md

Los módulos src/sintesis.py y src/fitness.py mantienen sus
interfaces. No se requiere crear src/referencia.py.

## 2. Cambios preparados para el Rol 2

### Compatibilidad con el Rol 1

Se mantiene el contrato de ocho genes normalizados en [0, 1]:

1. amp_arm1
2. amp_arm2
3. amp_arm3
4. ataque_s
5. decaimiento_s
6. sostenido_rel
7. relajacion_s
8. ruido_soplo

Se reutilizan la validación y decodificación del Rol 1.

La carga del CSV mantiene la interfaz comprobada en el proyecto:
dos arreglos, notas MIDI y duraciones en segundos.
El valor -1 representa silencio.

El paso físico 0.001 corresponde al análisis teórico del espacio
de búsqueda. No implica redondear los genes durante la evolución.

### Referencia instrumental

La sección 12 prepara una referencia independiente con muestras
reales de flauta, utilizando las notas, duraciones y silencios
del CSV.

Se conservan las muestras originales, las fuentes y los ajustes.
Se comprueban formato WAV, frecuencia de muestreo, longitud,
finitud y silencios.

La referencia de trabajo permanece en datos/audio/referencias/.
Su articulación y las condiciones de uso requieren revisión.

### Comparación y superficie de fitness

Las secciones 13 y 14 comparan el cromosoma por defecto y cinco
candidatos aleatorios mediante STFT y croma.

Se realiza un barrido de 41 valores de amp_arm2, manteniendo
los otros genes y la semilla de síntesis constantes.

El barrido es un corte unidimensional de la superficie de fitness.
No demuestra el comportamiento de todo el espacio de búsqueda.

### Exportación y reproducibilidad

Las salidas utilizan la carpeta existente resultados/audios/.
No se crea resultados/rol2/.

Se exportan audios, tablas, figura, cromosoma seleccionado y
registro del entorno.

Se registran versiones, semillas y parámetros de evaluación.
El commit y la presencia de cambios locales se registran
cuando Git está disponible.

Las conclusiones numéricas se obtienen de los valores calculados
durante la ejecución, evitando copiar cifras antiguas.

Los candidatos comparados no representan una corrida completa
del AG ni un mejor individuo evolucionado.

## 3. Relación con el diseño de una página

Los cambios del notebook aportan información técnica para
actualizar el diseño del Día 1:

- Representación de ocho genes compartida con el Rol 1.
- Síntesis aditiva de tres armónicos, ADSR y ruido de soplo.
- Referencia instrumental independiente y alineada al CSV.
- STFT como propuesta principal y croma como alternativa.
- Maximización de la aptitud.
- Semilla del ruido independiente del generador del AG.

El diseño debe resumir estas decisiones. El código, las tablas
de resultados y los detalles extensos permanecen en el notebook
y en los contratos.

Las propuestas pendientes no deben presentarse como decisiones
ratificadas sin confirmación del equipo.

## 4. Comprobar que el diseño ocupa una página

Archivo de diseño vigente:

documentacion/diseno/diseno_completo_ag_dia1.md

El Markdown no tiene paginación fija. Para comprobar la extensión:

1. Actualizar el contenido del diseño conjunto.
2. Exportarlo a PDF con el formato definitivo de entrega.
3. Confirmar que el PDF tenga exactamente una página.
4. Revisar que el texto sea legible y no presente recortes.
5. Comprobar que los espacios de nombres, firmas y fecha
   estén incluidos en esa misma página.
6. Repetir la comprobación si se modifica el contenido o formato.

El Word elaborado anteriormente se comprobó en una página.
Esa comprobación corresponde únicamente a aquella versión;
no acredita la paginación del Markdown actual ni de futuras
exportaciones.

## 5. Completar nombres, firmas y fecha

El diseño vigente contempla cinco espacios de responsabilidad.
Completar los datos personales de quienes ejerzan cada rol:

- Rol 1 — Representación y extracción:
  Nombre: Juan Manuel Soruco.
  Firma: pendiente de completar por el responsable.

- Rol 2 — Síntesis y fitness:
  Nombre: pendiente.
  Firma: pendiente.

- Rol 3 — Operadores:
  Nombre: pendiente.
  Firma: pendiente.

- Rol 4 — Dinámica poblacional:
  Nombre: pendiente.
  Firma: pendiente.

- Rol 5 — Evaluación e integración:
  Nombre: pendiente.
  Firma: pendiente.

Si una persona ejerce dos roles, identificarla en ambos espacios
según el formato acordado por el equipo.

Fecha: completar con la fecha real de aprobación y firma.
No sustituirla automáticamente por la fecha de generación
del documento.

Las firmas deben incorporarlas los responsables. No se consideran
completadas por dejar líneas en blanco o escribir los nombres.

## 6. Lista de cierre

- [ ] Aplicar los cambios preparados al notebook.
- [ ] Ejecutarlo desde un kernel limpio y guardar sus salidas.
- [ ] Confirmar los archivos exportados en resultados/audios/.
- [ ] Actualizar el diseño conjunto con las decisiones vigentes.
- [ ] Resolver o identificar expresamente los acuerdos pendientes.
- [ ] Exportar el diseño y comprobar exactamente una página.
- [ ] Revisar legibilidad y ausencia de recortes.
- [ ] Completar los nombres de los responsables.
- [ ] Incorporar las firmas personales.
- [ ] Completar la fecha real de aprobación.
- [ ] Registrar rama, commit y estado real de la contribución.

## Punto de continuación

El cierre documental requiere comprobar la paginación de la
versión definitiva y completar nombres, firmas y fecha.

La ejecución correcta del notebook no sustituye esta comprobación,
y un diseño firmado no certifica por sí solo el funcionamiento
del ciclo completo del AG.