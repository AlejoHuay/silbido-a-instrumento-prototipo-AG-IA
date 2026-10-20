# Revisión técnica para preparar el cierre del Día 1

**Estado:** cierre pendiente. No hay ratificación, firmas ni verificación de una
página impresa. No se implementó reproducción del Día 2 ni se ejecutaron
experimentos del AG. No se hicieron commits, push ni merge a main.

## Procedencia e integración

La revisión empezó con árbol limpio en `feature/rol3-torneo-dia1`.
No se encontró AGENTS.md en el repositorio ni en sus directorios ascendientes.
Se leyó el examen proporcionado, especialmente su cronograma por día y rol.
Después de `git fetch origin`, se creó `revision/cierre-dia1` desde
`89a089b09daaf4718b7e8ef90729a47356f907f9` (origin/main observado).

| Contribución revisada | Commit exacto | Situación comprobada |
|---|---|---|
| Rol 3 | `1660ce9201e6c58369f36f109eb367463f555e1b` | Integrado en main mediante b631dca. |
| Rol 4 | `f036e4184494a8072ff92e032673068ef4c1c771` | Integrado en main mediante 89a089b. |
| Rol 5 | `171b794ebf0a7666438d461819e4ae61624213dd` | Hijo directo de 89a089b; faltaba en main. Incorporado con cherry-pick --no-commit. |

No se duplicaron los cambios de Roles 3/4 ni hubo conflictos. El índice contiene
la contribución importada del Rol 5; las correcciones de esta revisión están
en el árbol de trabajo y deben revisarse junto con ella (`git diff HEAD`).

## Dictamen y evidencia por rol

| Rol | Dictamen para Día 1 | Evidencia y límite |
|---|---|---|
| 1 | Cumple con observaciones documentales | WAV, CSV, genes y validación disponibles. Espacio de búsqueda recalculado; no se repitió la extracción de pitch. |
| 2 | Cumple con observaciones de ratificación | Síntesis y ambas métricas ejecutadas contra referencia real; métrica oficial pendiente. |
| 3 | Cumple con observación de entorno | Firma y reglas conservadas; 5 celdas pasan en proceso nuevo. Kernel Jupyter pendiente. |
| 4 | Cumple con observaciones | Pseudocódigo completo y componentes compatibles; 8 pruebas originales pasan. Notebook local bloqueado por pandas; no se confirma su ejecución histórica en kernel limpio. |
| 5 | Cumple con observaciones | Integración real de 4 celdas pasa como script. Tiene 6 pruebas propias, no 14; 14 era el total junto al Rol 4. Plan ampliado y aún por ratificar. |

Confirmados del Rol 4: configuración base 50/50/2/k=3, máximo por reemplazos,
orden población–fitness, maximización, élites copiadas con desempate estable,
RNG compartido en demostración/pseudocódigo y semilla de síntesis independiente.
La configuración rechaza torneo mayor que N y élites >= N. Las estadísticas
usan desviación poblacional (`ddof=0`) y diversidad sobre genes normalizados.
El torneo mantiene su firma exacta y empata por orden sorteado.

La parada implementada compara mejora **acumulada en ventana**, no diez
incrementos pequeños contados individualmente. Se precisó sin cambiar la regla.
No existe runner del AG ni operadores ficticios: no se afirma AG completo.

Confirmados del Rol 5: registro/exportación sin sobrescritura por defecto,
resumen muestral, baseline con presupuesto explícito y emparejamiento por
registro. Su runner se inyecta; las pruebas usan funciones de prueba, no un AG.
Los módulos adelantados se conservaron sin ampliarlos con tareas del Día 2.

## Correcciones locales posteriores a los commits

1. `src/configuracion.py` y `src/algoritmo_genetico.py`: rechazar tolerancias
   NaN/infinito. Antes NaN impedía la parada y +infinito la activaba al completar
   la ventana. Documentar la semántica acumulada sin modificarla.
2. `src/experimentos.py`: rechazar baseline de métrica distinta o ausente en
   el registro AG antes de ejecutar evaluaciones. El llamador sigue siendo
   responsable de que el callable implemente esa métrica y use los mismos datos.
3. Tests: cuatro regresiones para tolerancias/configuración, ventana acumulada,
   métricas incompatibles y conteo efectivo de llamadas del baseline con dos
   presupuestos distintos. No se añadió framework.
4. `interfaz_dinamica_rol4.md`: generación 0, RNG, ventana, estadísticas,
   contador real, reevaluación de élites y retorno. `04_rol4_dinamica.ipynb`:
   únicamente texto explicativo de parada; no cambios de código ni salidas.
5. `analisis_rol5.md`: plan completo propuesto (12 configuraciones, réplicas,
   métricas, tres combinaciones, varianza/desviación sin ANOVA, baseline justo,
   tareas posteriores). El factorial existente se preserva: 3×2×2.
6. `contrato_cromosoma.md`: paso físico absoluto, niveles por gen, datos reales,
   límites de extensibilidad e interfaces usadas; se retira aprobación sin
   firmas verificables. No se modificó representación, síntesis ni fitness.
7. `diseno_completo_ag_dia1.md`: único diseño de entrega actualizado, cinco
   espacios individuales y fecha en blanco. `dia1.md` queda como anexo técnico.
   README e interfaz del Rol 3 apuntan a la entrega y distinguen las discrepancias
   históricas de la documentación actual.

## Verificación efectivamente ejecutada

Entorno: Python 3.13.15, NumPy 2.5.4, SciPy 1.18.1, SoundFile 0.14.0 en `.venv`.
No se instalaron paquetes en esta revisión ni se cambió requirements.txt.
Jupyter/nbclient/nbformat/ipykernel y pandas no están disponibles en ese entorno.

Comando: `.venv/Scripts/python.exe -m unittest discover -s tests -v`.
Primera ejecución aislada: 13 pasan, una falla por permisos del directorio
temporal. Repetida con permiso de ejecución fuera del sandbox: las **14 pruebas
originales pasan** (8 Rol 4 + 6 Rol 5). Tras correcciones: **18 pasan, 0 fallan**
(10 Rol 4 + 8 Rol 5). No se ocultó ni se corrigió el fallo ambiental como si
fuera un defecto del código.

Cobertura original: configuración, inicialización reproducible, orden de
evaluación, copia/desempate de élites, estadísticas y ventana; baseline,
semillas, validación de fitness, esquema de registros, CSV, resumen e inyección
de runner. No son pruebas limitadas a importaciones. Tampoco prueban el ciclo
generacional inexistente ni la calidad perceptual final.

| Notebook | Método de esta revisión | Resultado real |
|---|---|---|
| 03_rol3_operadores | Celdas en orden, proceso Python nuevo | 5 celdas completadas; 20 casos inválidos rechazados; integración real correcta. |
| 04_rol4_dinamica | Proceso nuevo, intento de ejecución | Se detiene en primera celda de código: falta pandas. 0 celdas completadas. |
| 00_integracion | Celdas en orden, proceso Python nuevo | 4 celdas completadas; síntesis reproducible e interfaces reales correctas. |

**Ninguna de esas ejecuciones fue un kernel Jupyter.** Se conservaron las
salidas históricas de los notebooks; no se presentaron como nuevas. Se revisó
su código antes de ejecutarlo: estas demostraciones no exportan archivos ni
ejecutan experimentos largos. Hashes SHA-256 de 32 archivos en datos/resultados
coinciden antes y después. No se escribieron WAV ni resultados experimentales.

Resultados de comprobación, no experimentos: Rol 3, semilla 2026,
fitness STFT `[0.67976701, 0.49070326, 0.70833249]`, gana índice 2.
Integración, semilla 42: `[0.51501230, 0.64533720, 0.52458545]`;
síntesis del cromosoma de prueba: STFT 0.5150123037 y croma 0.9064677389.

Se contrastaron CSV/JSON (notas y duraciones idénticas), WAV mono 22050 PCM16
de 59645 muestras, finitud y existencia de las siete muestras originales.
La referencia sigue siendo el montaje del Rol 2, sin normalización adicional.
El silbido procesado tiene 59424 muestras; el CSV dura 2.705 s, por lo que no
se confunde su duración con la grabación. La representación devuelve
1762430802969797099136 estados y 70.5780566078 bits con paso físico 0.001;
los niveles son 901,801,501,246,296,901,296,251.

## Presupuesto y decisiones aún pendientes

El plan fija llamadas efectivas: iniciales + todas las reevaluaciones realmente
ejecutadas, incluidas élites. En el pseudocódigo actual sin llamadas extra,
E=N*(g+1), con g reemplazos completos; no N*G. Una parada temprana conserva su E.
El baseline debe recibir ese E, misma métrica/datos y semilla. Sus pruebas
cuentan llamadas reales, pero no certifican el contador del futuro runner.

Pendientes del equipo: ratificar STFT base/croma alternativa, niveles factoriales,
tasas por gen/individuo y tres combinaciones propuestas. Mantener variantes
históricas SUS, BLX/uniforme, gaussiana/no uniforme sin inventar firmas finales.
El valor por defecto 0.05 no forma parte de los niveles factoriales 0.02/0.08;
son base y experimento diferentes. La documentación no los confunde.

El Rol 5 ya había eliminado duplicados y corregido 1024/2048, croma euclídeo y
fitness combinado en su anexo. Esta revisión completa la fórmula de síntesis,
reparto de cinco roles, cronología, aprobación y discretización. No se encontraron
firmas válidas ni evidencia suficiente para marcar aprobado el diseño conjunto.

## Paginación y entrega

Se entrega Markdown compacto en `diseno/diseno_completo_ag_dia1.md`.
No se encontró herramienta de exportación disponible (Pandoc/wkhtmltopdf,
ReportLab, navegador local en ubicaciones habituales) ni herramientas de
inspección PDF (Poppler/PyMuPDF/pypdf). No se instalaron herramientas. **No se
generó PDF ni se verificó una página impresa.** La paginación, legibilidad y
ausencia de recortes deben comprobarse antes de firmar; Markdown corto no
equivale a una página verificada.

Faltan ratificación, verificación de notebooks en kernels limpios, paginación,
cinco nombres y firmas personales y fecha de firma. El Día 1 no se declara cerrado.

Commit sugerido, sin ejecutar:
`docs(dia1): consolidar diseno y revisar integracion de roles 4 y 5`
