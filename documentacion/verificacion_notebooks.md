# Verificación de notebooks en kernels Jupyter limpios

**Fecha de última verificación:** 22 de octubre de 2026
**Estado:** 5 de 5 notebooks ejecutados correctamente.

## Entorno local reproducible

La verificación se realizó en un entorno virtual `.venv` creado con Python
3.10.0. La dependencia local que faltaba quedó instalada mediante
`requirements-notebooks.txt`, que incluye las dependencias del proyecto por
medio de `requirements.txt` y agrega el ejecutor de Jupyter.

Versiones observadas durante la ejecución:

| Componente | Versión |
|---|---:|
| Python | 3.10.0 |
| NumPy | 2.2.6 |
| SciPy | 1.15.3 |
| pandas | 2.3.3 |
| Matplotlib | 3.10.9 |
| SoundFile | 0.14.0 |
| IPython | 8.39.0 |
| nbformat | 5.11.1 |

## Procedimiento

Se ejecutó:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-notebooks.txt
.\.venv\Scripts\python scripts\verificar_notebooks.py --timeout 300
```

El verificador inicia un kernel nuevo para cada notebook. Además, ejecuta cada
uno en su propia copia temporal del repositorio. De esta forma, no se comparte
estado de Python ni archivos generados entre notebooks y tampoco se modifican
los WAV, CSV, figuras o resultados versionados.

## Resultados

| Notebook | Celdas de código | Tiempo | Resultado |
|---|---:|---:|---|
| `00_integracion.ipynb` | 5 | 26.58 s | Correcto |
| `01_rol1_representacion.ipynb` | 8 | 35.74 s | Correcto |
| `02_rol2_sintesis_fitness.ipynb` | 18 | 39.94 s | Correcto |
| `03_rol3_operadores.ipynb` | 10 | 22.97 s | Correcto |
| `04_rol4_dinamica.ipynb` | 9 | 27.29 s | Correcto |

Todas las celdas de código recibieron contador de ejecución y no produjeron
salidas de error. También pasaron las 55 pruebas unitarias del proyecto.

Los tiempos son evidencia de esta corrida y pueden variar entre equipos. Una
advertencia de compatibilidad de `nbformat` indicó que algunas celdas antiguas
no tienen identificador; Jupyter las normalizó en memoria y la advertencia no
afectó ningún resultado.

En Windows, el verificador configura `WindowsSelectorEventLoopPolicy` antes de
iniciar los kernels. Esto evita que pyzmq falle durante el cierre del proceso
después de haber ejecutado correctamente las celdas. La advertencia de que los
kernels locales usan TCP sin cifrado corresponde al transporte interno de esta
verificación y no alteró los resultados.

## Verificación posterior del notebook de Rol 5

**Fecha:** 25 de octubre de 2026. Se ejecutó `notebooks/05_rol5_metaevaluacion.ipynb`
con `nbclient` en un kernel Jupyter `python3` nuevo. Las cuatro celdas de código
terminaron sin errores. Se inspeccionaron sus fuentes y la ejecución usa la
carga/validación de CSV existentes, estadísticas descriptivas, ANOVA y gráficos;
no llama al AG, al baseline ni a funciones de fitness. No se ejecutaron corridas
experimentales ni se reescribió el notebook o los CSV; las salidas de esta
verificación quedaron en memoria.

Entorno del proceso verificador: Python 3.14.5, `nbclient` 0.11.0,
`nbformat` 5.11.1, NumPy 2.5.2, Matplotlib 3.11.1 y SciPy 1.18.1. El kernel
terminó correctamente con advertencias informativas de Windows Proactor/zmq
(se creó un hilo selector auxiliar) y de transporte TCP local sin cifrado.
Estas advertencias no interrumpieron las celdas ni modificaron los resultados.

## Auditoría de cierre — 26 de octubre de 2026

- `python -B scripts/analizar_rol5_dia4.py`: terminó con código 0. Leyó los CSV existentes, validó 60 pares por métrica y calculó descriptivos/ANOVA; no ejecutó AG, baseline ni fitness.
- `python -B scripts/exportar_audios_rol5_corrida.py`: después de corregir la carga local de `src`, terminó con código 0. Reconstruyó la generación 0 y exportó dos WAV desde cromosomas guardados/reproducidos determinísticamente, sin ejecutar AG ni fitness.
- `notebooks/05_rol5_metaevaluacion.ipynb`: hay una ejecución limpia exitosa previa, fechada el 25-oct-2026, documentada arriba. En la revisión actual se intentó ejecutar con el kernel Jupyter `python3` registrado; ese kernel usa Python 3.12 y falló en la primera celda con `ModuleNotFoundError: scipy`. Python 3.14 del proceso sí tiene scipy, pero un intento de crear un kernelspec temporal para esa versión quedó bloqueado por `WinError 5` al asignar permisos al archivo de conexión. No se instaló nada. El notebook y los CSV no se reescribieron.
- `python -B -m unittest discover -s tests -p test_rol5.py -v`: 8/8 pruebas pasaron al ejecutar fuera del sandbox. Dentro del sandbox, una prueba que escribe en `%TEMP%` falló con `PermissionError`; al elevar el mismo comando pasó.
- Los cuatro SVG de boxplots/sensibilidad/tornado parsearon como XML válido. Los enlaces internos del informe compacto se comprobaron y todos existen.
- Se regeneraron boxplots STFT/chroma y tornado desde los CSV en una carpeta temporal exclusiva; los tres SVG nuevos parsearon como XML y la carpeta temporal se retiró después. No se tocaron los gráficos guardados. Matplotlib avisó que no podía escribir su caché de fuentes en el perfil del usuario; no impidió la exportación.
- Se validaron los cuatro WAV con SoundFile/NumPy: PCM16, mono, 22050 Hz, finitos; los hashes del manifiesto coinciden y la referencia conserva el hash de su fuente.
- `documentacion/informe/informe_final_ag.md` se compactó a 1438 palabras. Todos sus enlaces locales existen; el conteo de páginas no se verificó por ausencia del formato oficial.
- `python -B -m unittest discover -s tests -v`: 52 pruebas ejecutables; 51 pasaron y una prueba no pudo importarse porque falta `pandas` (`tests/test_sensibilidad_rol1.py`). No se instalaron paquetes. El primer intento dentro del sandbox añadió errores `WinError 5` al escribir en `%TEMP%`; al repetir fuera del sandbox, esas dos pruebas pasaron y quedó únicamente la importación faltante.
- `python -B -m unittest discover -v` no descubrió pruebas desde la raíz (0 tests); se usó la forma explícita con `-s tests`.

La rama no ejecutó experimentos factoriales ni regeneró fitness. Los tests unitarios del proyecto sí incluyen evaluaciones acotadas propias de sus casos de prueba. El Jupyter actualmente registrado no ofrece scipy; la ejecución limpia histórica exitosa corresponde a otro kernel/entorno y no se debe atribuir al kernel actual.
