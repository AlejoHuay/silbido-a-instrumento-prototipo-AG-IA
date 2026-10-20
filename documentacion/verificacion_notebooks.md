# Verificación de notebooks en kernels Jupyter limpios

**Fecha:** 20 de octubre de 2026
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
| `00_integracion.ipynb` | 4 | 17.99 s | Correcto |
| `01_rol1_representacion.ipynb` | 8 | 25.28 s | Correcto |
| `02_rol2_sintesis_fitness.ipynb` | 15 | 21.38 s | Correcto |
| `03_rol3_operadores.ipynb` | 5 | 17.57 s | Correcto |
| `04_rol4_dinamica.ipynb` | 6 | 18.37 s | Correcto |

Todas las celdas de código recibieron contador de ejecución y no produjeron
salidas de error. También pasaron las 18 pruebas unitarias del proyecto.

Los tiempos son evidencia de esta corrida y pueden variar entre equipos. Una
advertencia de compatibilidad de `nbformat` indicó que algunas celdas antiguas
no tienen identificador; Jupyter las normalizó en memoria y la advertencia no
afectó ningún resultado.
