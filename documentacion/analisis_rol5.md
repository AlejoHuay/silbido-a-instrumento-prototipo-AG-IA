# Rol 5: cierre del Día 2

> **Vigencia:** este documento conserva la auditoría y el plan tal como estaban
> al cierre del Día 2. El factorial ejecutado del Día 3 está documentado en
> `rol5_dia3.md`; el análisis posterior y el estado de Día 4 están en
> `notebooks/05_rol5_metaevaluacion.ipynb` y en la sección 5 del informe final.
> Las propuestas pendientes que siguen abajo son antecedentes históricos, no
> el estado experimental actual.

## Estado de esta copia

`src/experimentos.py` ofrece el baseline de búsqueda aleatoria y el emparejamiento
por semilla, métrica y número observado de evaluaciones. `src/evaluacion.py`
normaliza registros de corrida, escribe CSV sin sobrescribir por defecto y
calcula resúmenes. Esas funciones preparan el análisis posterior; no son por sí
mismas resultados experimentales.

El ciclo completo está implementado en `src/algoritmo_genetico.py` y consume
las interfaces actuales de los Roles 2 y 3. `notebooks/00_integracion.ipynb`
ejecuta una corrida de demostración con la melodía y la referencia versionadas.
La corrida verifica repetibilidad, límites y finitud de genes y fitness, tamaño
de población, monotonía del mejor fitness, presupuesto de evaluaciones,
síntesis final y registro de configuración, operadores, métrica, semilla,
duración, commit y huellas SHA-256 de las entradas y del WAV. Genera el WAV
`resultados/audios/rol5_dia2_mejor.wav` si falta; si ya existe, comprueba que
coincida con la salida reproducida y lo conserva sin sobrescribirlo.

Esta ejecución individual sirve para cerrar la integración del Día 2. No mide
la calidad estadística del algoritmo y no sustituye las réplicas del Día 3.

## Verificación del entorno y pruebas

La copia se verificó en la rama `feature/rol5-cierre-dia2`, sin modificar
dependencias. El entorno disponible para la comprobación fue Python 3.14 con
NumPy, SciPy, SoundFile e IPython/Jupyter. No estaban instalados `pytest` ni
`pandas`; las pruebas existentes usan `unittest`, y el notebook integrado no
requiere pandas.

La suite completa pasó con:

```powershell
py -3.14 -B -m unittest discover -s tests -v
```

Se ejecutaron 51 pruebas. El entorno restringido bloqueó las pruebas que
escriben en `%TEMP%`; la misma suite se ejecutó fuera del sandbox con
autorización y terminó correctamente. No se cambiaron paquetes.

El notebook debe ejecutarse en un kernel limpio. Su corrida guarda un WAV
nuevo mediante una comprobación de existencia previa, así que el verificador
debe ejecutarlo en una copia temporal del repositorio.

## Análisis que queda para el Día 3

- **Factorial de dinámica:** la propuesta codificada es
  `N={20,50,100} × elitismo={1,2} × p_mutación={0.02,0.08}`: 12
  configuraciones. Mantiene `G=50`, torneo `k=3`, `p_cruce=0.90`,
  paciencia 10 y tolerancia `1e-4`. Las cinco semillas previstas son
  `42, 101, 2024, 7, 999`, es decir, 60 corridas por métrica. El equipo debe
  ratificar los niveles antes de ejecutar; ninguna de estas corridas se hizo
  en el cierre del Día 2.
- **Métricas:** STFT en dB es la propuesta principal por ser la aptitud
  predeterminada del código. Croma se debe medir en un bloque separado con las
  mismas entradas y semillas; sus valores no se deben mezclar ni promediar con
  STFT. La interfaz actual usa `N_FFT=2048`, salto 256 y similitud coseno para
  croma; no implementa una aptitud compuesta.
- **Operadores:** la propuesta pendiente de ratificación conserva tres
  combinaciones: A) torneo + BLX-alpha (`alpha=0.5`) + mutación gaussiana
  (`sigma=0.08`); B) torneo + cruce uniforme + mutación gaussiana; C) SUS +
  BLX-alpha + mutación no uniforme. Este bloque es independiente del factorial
  de dinámica. Hay que acordar combinaciones y granularidad de probabilidades
  antes de medirlas.
- **Resumen:** agrupar por configuración, combinación, métrica y método,
  excluyendo semilla; informar media, varianza muestral y desviación estándar
  muestral (`ddof=1`). No se propone ANOVA ni agrupar métricas de escalas
  distintas.
- **Baseline pareado:** emparejar cada corrida de búsqueda aleatoria con una
  corrida AG por semilla, métrica, entradas y presupuesto real de evaluaciones.
  El ciclo actual reevalúa toda la población, incluidas las élites; cuando
  ejecuta `g` reemplazos completos, `E=N*(g+1)`. Para el baseline se usa el
  contador devuelto por la corrida, incluidas paradas anticipadas, nunca un
  presupuesto supuesto `N*G`.
- La sensibilidad de genes y la sensibilidad de hiperparámetros del AG son
  análisis distintos. No hay mediciones ni gráficos de sensibilidad guardados
  en esta copia; por eso no se regenera el tornado previo.
- Antes del factorial, el equipo debe confirmar la métrica oficial y los
  niveles de factores del plan. STFT es la métrica predeterminada del código,
  pero la documentación previa deja su ratificación pendiente.

No se presentan valores históricos como resultados de esta rama ni se
atribuyen resultados a corridas que no se hayan ejecutado aquí.
