# Curvas de convergencia del factorial — Rol 4

Estas figuras se generaron por posprocesamiento de los checkpoints existentes en
`resultados/rol5/dia3_factorial/ejecucion_20261021T184758Z_c5dc431/`. No se
repitieron corridas, síntesis de audio ni evaluaciones de fitness.

## Archivos

- `convergencia_stft_12_configuraciones.svg`: 12 configuraciones STFT.
- `convergencia_croma_12_configuraciones.svg`: 12 configuraciones croma.

Cada panel corresponde a una combinación de población `N={20,50,100}`,
elitismo `E={1,2}` y probabilidad de mutación `pm={0.02,0.08}`. Las cinco
líneas finas son las semillas `42, 101, 2024, 7, 999`. Cada línea termina en
la parada real de su corrida. La línea negra muestra la media únicamente en el
tramo común disponible para las cinco semillas; no prolonga resultados después
de la parada.

## Reproducción

Desde la raíz del repositorio:

```powershell
.\.venv\Scripts\python.exe scripts\graficar_convergencia_factorial.py --sobrescribir
```

El script valida 120 historiales AG, la matriz 12 × 5 de cada métrica, las
semillas, la secuencia de generaciones, valores finitos y monotonía del mejor
fitness.
