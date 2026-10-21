# Interfaz de operadores — Rol 3, Días 2 y 3

**Estado:** seis operadores disponibles. El torneo conserva su interfaz y comportamiento. El Rol 4 ya los conecta mediante `ejecutar_ag()`; este notebook conserva su demostración acotada a un paso de reproducción.

## Firmas definitivas

```python
seleccion_torneo(poblacion, fitness, k=3, rng=None)
seleccion_sus(poblacion, fitness, cantidad, rng=None)
cruce_blend(padre1, padre2, alpha=0.5, rng=None)
cruce_uniforme(padre1, padre2, rng=None)
mutacion_gaussiana(individuo, p_mut=0.05, sigma=0.08, rng=None)
mutacion_no_uniforme(individuo, generacion, max_generaciones,
                    p_mut=0.05, b=2.0, rng=None)
```

## Representación y salidas

Población no vacía `(N,D)`, con `D=num_genes()` (actualmente ocho). Individuos `(D,)`, convertidos a `float64`, finitos y normalizados en `[0,1]`. Se reutiliza `validar_individuo()`. Las entradas inválidas se rechazan con `ValueError`, sin repararlas. Fitness debe tener forma `(N,)`, valores finitos y conservar el orden de las filas; una permutación semántica con longitud correcta no es detectable automáticamente.

Todas las salidas son copias independientes. No se modifican padres, población ni aptitudes. Cruces y mutaciones recortan sus resultados con `restringir_limites()` y validan; no redondean ni discretizan genes. Los cruces retornan una tupla de dos vectores; las mutaciones, un vector. Ningún operador calcula fitness ni sintetiza audio. STFT y croma se maximizan; `error_stft_db` es un error y no debe usarse directamente como aptitud.

## Selección

**Torneo:** sortea k índices sin reemplazo y devuelve solamente el cromosoma ganador. Gana el máximo; en empates, el primero en el orden sorteado. Acepta aptitudes negativas. k debe ser entero Python/NumPy, excluyendo booleanos, con `1<=k<=N`; N menor que tres falla con el valor predeterminado. No se reduce k. Se puede volver a seleccionar al mismo individuo en llamadas posteriores.

**SUS:** retorna matriz `(cantidad,D)`, con posibles repeticiones y sin compartir memoria con la entrada. cantidad debe ser entero positivo, excluyendo booleanos; puede superar N. Requiere aptitudes no negativas y no las desplaza silenciosamente. Escala por el máximo antes de sumar para evitar desbordamientos; con todas cero utiliza pesos iguales. Sobre pesos normalizados, sortea un único inicio en `[0,1/cantidad)` y emplea punteros equidistantes sobre la acumulada. Omite intervalos de masa cero. No equivale a ruletas independientes ni a llamadas repetidas con cantidad uno.

## Cruces y mutaciones

| Operador | Regla |
|---|---|
| BLX-alpha | Cada hijo se muestrea por gen en `[min-alpha*d,max+alpha*d]`, con `d=abs(p1-p2)`. alpha finito no negativo. |
| Uniforme | Máscara por gen de probabilidad 0.50, herencia complementaria. |
| Gaussiana | Selección independiente por gen con p_mut; suma ruido normal de media cero y desviación sigma. sigma finito no negativo. |
| No uniforme | Selección por gen; dirección hacia 0 o 1, distancia y a ese límite y `delta=y*(1-r**((1-t/T)**b))`, r uniforme en `[0,1)`. |

p_mut debe ser finito en `[0,1]`. Los parámetros numéricos rechazan booleanos. La no uniforme exige t=generacion y T=max_generaciones enteros, `T>0`, `0<=t<=T` y b finito positivo. En t=T devuelve una copia sin cambios y sin consumir sorteos. Seleccionar un gen no garantiza cambiar su valor: clipping, sigma cero o desplazamiento cero pueden conservarlo.

## Probabilidades y generador

**Decisiones indicadas por el usuario:** torneo/SUS, BLX/uniforme, gaussiana/no uniforme; p_cruce=0.90 una sola vez por pareja en el ciclo, sin filtro interno en el cruce; máscara uniforme 0.50; p_mut base=0.05 por gen dentro de la mutación, variantes experimentales 0.02 y 0.08. El ciclo llama a la mutación de cada hijo conservado sin filtro previo por individuo. Sin cruce se copian los padres.

**Convenciones de implementación entregadas al Rol 4:** dirección equiprobable hacia ambos límites; con una plaza impar se conserva el primer hijo de la última pareja; al reproducir la población evaluada g para crear g+1 se usa t=g y T=G_max. Se reproduce con g=0,...,G_max-1; t=T es el extremo de desplazamiento cero, no una generación adicional.

Crear un Generator por corrida y compartirlo con inicialización y operadores. Los operadores avanzan su estado; con rng=None crean default_rng() sin semilla fija. No se modifica la semilla independiente 2026 del ruido de síntesis.

## Ejemplos exactos para el Rol 4

Con P y F ya evaluados y alineados, dos padres por torneo:

```python
from src.operadores import seleccion_torneo
p1 = seleccion_torneo(P, F, k=3, rng=rng)
p2 = seleccion_torneo(P, F, k=3, rng=rng)
```

Alternativa SUS: un lote para todas las plazas. Este fragmento realiza solamente reproducción, sin implementar el ciclo completo:

```python
import numpy as np
from src.algoritmo_genetico import seleccionar_elites
from src.operadores import seleccion_sus, cruce_blend, mutacion_no_uniforme

# config: ConfiguracionAG; rng compartido; g: generación evaluada.
elites = seleccionar_elites(P, F, config.elitismo)
nueva = [elite.copy() for elite in elites]
plazas = len(P) - len(elites)
cantidad = 2 * ((plazas + 1) // 2)
padres = seleccion_sus(P, F, cantidad=cantidad, rng=rng)
for i in range(0, cantidad, 2):
    p1, p2 = padres[i:i+2]
    if rng.random() < config.probabilidad_cruce:
        hijos = cruce_blend(p1, p2, alpha=0.5, rng=rng)
    else:
        hijos = (p1.copy(), p2.copy())
    for hijo in hijos:
        if len(nueva) == len(P):
            break
        nueva.append(mutacion_no_uniforme(
            hijo, g, config.max_generaciones,
            p_mut=config.probabilidad_mutacion, b=2.0, rng=rng,
        ))
P_nueva = np.array(nueva, dtype=np.float64)
```

Alternativas: `cruce_uniforme(p1,p2,rng=rng)` y `mutacion_gaussiana(hijo,p_mut=config.probabilidad_mutacion,sigma=0.08,rng=rng)`. Evaluar la nueva población en orden y contar cada llamada real, incluidas las élites si se reevalúan. No usar automáticamente N*G como presupuesto.

## Referencias y comprobación

Se consultaron el examen y ag_ejemplo_reinas.ipynb proporcionados fuera del repositorio. Se conserva el estilo de funciones independientes y la lógica de torneo del docente (random.sample y máximo), adaptados a NumPy y aptitudes precalculadas. OX y swap de permutaciones se sustituyen por operadores para genes continuos.

`tests/test_operadores_rol3.py` comprueba propiedades, validaciones, reproducibilidad y evaluación real de hijos. `notebooks/03_rol3_operadores.ipynb` carga el CSV con cargar_melodia_csv() y el WAV del Rol 2 con sf.read(...,dtype="float32"). Demuestra reproducción con N=5, dos élites, tres plazas y cuatro padres SUS, contando diez evaluaciones (cinco iniciales y cinco de nueva población). No escribe WAV ni sustituye referencias por resultados guardados.

La documentación del cierre del Día 1 conserva su carácter histórico. Esta entrega no ratifica ni firma el diseño conjunto.

## Comparación del Día 3

Las firmas anteriores se conservan. El experimento se orquesta en
`src/comparacion_operadores.py`, reutilizando `ejecutar_ag()` del Rol 4,
sin duplicar operadores ni cambiar valores predeterminados. Compara A:
torneo/BLX/gaussiana, B: torneo/uniforme/gaussiana y C: SUS/BLX/no uniforme.
El protocolo usa N=50, dos élites, 50 reemplazos y STFT provisional;
tolerancia cero desactiva estancamiento para igualar presupuesto. El usuario
redujo la comparación principal a las semillas 42 y 101: seis corridas.
Se conservan cinco corridas adicionales por separado. El lote está detenido.
Las llamadas reales a fitness se cuentan independientemente y las poblaciones
iniciales observadas se comparan por semilla.

Recomendación preliminar: B (torneo + uniforme + gaussiana), con media STFT
0.730850220 y solo dos réplicas. Resultados y límites:
[informe del Día 3](../rol3_dia3.md).
El notebook conserva el Día 2 y separa ejecución costosa de lectura de resultados
guardados. No confundir la visualización con corridas nuevas. El examen pide
tres combinaciones y análisis; N, generaciones y réplicas son el protocolo de
esta tarea, no requisitos atribuidos al examen.
