# Interfaz de operadores — Rol 3

**Estado:** Día 1. Selección por torneo implementada; cruces y mutaciones pendientes del Día 2.
**Equipo:** cinco integrantes; Rol 3 y Rol 5 separados.
**Consumidor:** Rol 4, responsable del ciclo del AG.

## Firma acordada

```python
seleccion_torneo(poblacion, fitness, k=3, rng=None)
```

| Elemento | Contrato |
|---|---|
| `poblacion` | Matriz NumPy `(N, D)`, N > 0, D = `num_genes()`; actualmente D = 8. Individuos normalizados en `[0, 1]`. |
| `fitness` | Vector `(N,)` de aptitudes finitas. `fitness[i]` corresponde a `poblacion[i]`. |
| `k` | Entero Python o NumPy, excluyendo booleanos; `1 <= k <= N`. Por defecto 3. |
| `rng` | `np.random.Generator` compartido por la corrida, o `None`. |
| Retorno | Únicamente un cromosoma `np.ndarray`, `float64`, de forma `(D,)`, con memoria independiente. |

Las entradas se convierten a arreglos `float64`. Se comprueba la forma y se
reutiliza `validar_individuo()` para cada fila. No se recortan ni reparan genes.
Una población inválida, aptitudes de forma incorrecta o no finitas, o un k
inválido producen `ValueError`. Con N < 3, el k predeterminado falla.
El llamador conserva la correspondencia semántica entre filas y aptitudes:
el operador no puede detectar aptitudes permutadas si tienen la misma longitud.

## Regla del torneo

1. Sortear k índices sin reemplazo dentro de cada torneo.
2. Elegir el participante con mayor fitness: **maximización**.
3. En empates, conservar el primero entre los participantes sorteados,
   no necesariamente el de menor índice en la población.
4. Devolver una copia del cromosoma ganador, sin modificar población ni fitness.

Un individuo puede participar y ganar en llamadas posteriores. No se reduce k
automáticamente ni se cambia a muestreo con reemplazo. Se aceptan aptitudes
negativas, cero y positivas; no se impone una escala de fitness.

El torneo no calcula fitness, sintetiza audio ni llama directamente a la
decodificación. La validación compartida del Rol 1 sí realiza internamente
sus comprobaciones físicas. `fitness_stft` y `fitness_croma` se maximizan;
`error_stft_db` se minimiza y **no debe pasarse directamente como aptitud**.

## Generador y ejemplo para el Rol 4

Crear el generador una sola vez por corrida y compartirlo. El operador avanza
su estado sin reinicializarlo. Si se omite, crea `np.random.default_rng()` sin
semilla fija; para reproducibilidad hay que proporcionarlo.

```python
import numpy as np
from src.representacion import generar_poblacion_inicial
from src.fitness import evaluar_individuo
from src.operadores import seleccion_torneo

# notas, duraciones y referencia ya cargadas y alineadas como en el Rol 2.
rng = np.random.default_rng(42)
poblacion = generar_poblacion_inicial(3, rng=rng)
fitness = np.array([
    evaluar_individuo(gen, notas, duraciones, referencia, metrica="stft")
    for gen in poblacion
])
padre = seleccion_torneo(poblacion, fitness, k=3, rng=rng)
```

## Referencias y verificación

El examen `examen2_practicoA-grupal.md`, cronograma del Día 1, pide al Rol 3
selección por torneo y compatibilidad con la tabla de genes. El notebook
del docente `ag_ejemplo_reinas.ipynb`, sección 4, usa `random.sample()` y
`max(..., key=fitness)`. Se conserva esa lógica, adaptada a cromosomas
continuos, aptitudes precalculadas, Generator y copia independiente.

`notebooks/03_rol3_operadores.ipynb` importa el operador y comprueba selección
del máximo, copia, entradas intactas, reproducibilidad, empates, validaciones
y compatibilidad con la población del Rol 1. La integración carga el CSV con
`cargar_melodia_csv()` y el WAV preparado por el Rol 2 con
`sf.read(..., dtype="float32")`, verifica sus metadatos y evalúa tres
individuos nuevos mediante `evaluar_individuo(..., metrica="stft")`.
No regenera la referencia ni consume los resultados experimentales del Rol 2.
Ante archivos o dependencias ausentes, informa el error sin sustituirlos.

## Inconsistencias pendientes de coordinación

Confirmadas en la base `81b09dd`. El Rol 5 corrigió varias en `171b794`;
la revisión de cierre alinea las restantes. La lista siguiente describe esa
base histórica, no el estado vigente. Entrega y decisiones pendientes:
[diseño conjunto](../diseno/diseno_completo_ag_dia1.md).

- `documentacion/diseno/dia1.md` indica STFT de 1024 muestras; `src/fitness.py`
  usa `N_FFT = 2048`.
- El diseño describe distancia euclídea de croma y fitness combinado; el código
  usa similitud coseno y permite elegir STFT o croma por separado.
- La fórmula escrita aplica ADSR solo a los armónicos y suma el ruido después.
  `src/sintesis.py` aplica ADSR a armónicos y ruido, además de una ganancia fija
  `0.9 / MAXIMO_AMPLITUD`.
- El diseño contiene secciones duplicadas, menciona cuatro integrantes y
  mantiene los Roles 3 y 5 agrupados; el equipo actual tiene cinco integrantes.
- El contrato del cromosoma menciona 1000 niveles por gen, pero el cálculo
  de `1.76e21` estados utiliza pasos absolutos de 0.001 en unidades físicas,
  con diferente cantidad de niveles por gen. Son discretizaciones distintas.

No se implementan SUS/ruleta, cruces, mutaciones, dinámica poblacional,
experimentos ni tareas del Rol 5 en esta entrega.
