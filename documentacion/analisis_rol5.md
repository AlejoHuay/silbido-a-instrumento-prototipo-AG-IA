# Rol 5 — Alcance del Día 1

## Entrega de esta rama

`notebooks/00_integracion.ipynb` documenta el objetivo, localiza el proyecto
desde la raíz, fija semillas para la comprobación y muestra el plan previsto.
La prueba usa `melodia_01.csv` ya procesada, valida un cromosoma, sintetiza
audio con semilla fija y compara sus métricas mediante las interfaces reales
de `src/representacion.py`, `src/extraccion.py`, `src/sintesis.py` y
`src/fitness.py`. La prueba no escribe resultados ni se presenta como
experimento.

`documentacion/diseno/dia1.md` se corrigió para concordar con el código actual
y los acuerdos comunicados por Rol 4. Allí se distinguen los parámetros
confirmados del diseño factorial codificado cuya ratificación sigue pendiente.

## Plan previsto, no ejecutado

- Configuración base del Rol 4: población 50, máximo 50 reemplazos tras
  generación 0, elitismo 2, torneo `k=3` y parada por mejora acumulada menor
  que `1e-4` en diez transiciones (ventana de once mejores globales).
- Tamaños considerados: 20, 50 y 100.
- Semillas previstas: 42, 101, 2024, 7 y 999.
- El código crea 12 configuraciones combinando población, elitismo y
  probabilidad de mutación. El equipo debe ratificar los niveles factoriales
  exactos antes de considerar esa matriz como el plan acordado definitivo.

No se ejecutaron corridas AG, búsqueda aleatoria comparativa ni análisis
estadísticos experimentales. El ciclo generacional sigue incompleto: el código
disponible aporta inicialización, evaluación, elitismo, estadísticas, parada y
selección por torneo; los contratos de cruce y mutación del Rol 3 y el runner
generacional completo todavía se necesitan.

## Contradicciones del diseño anterior

- La representación sí es un vector normalizado `float64` de ocho genes; los
  límites físicos y validaciones se documentan desde `GENES_SCHEMA` y
  `validar_individuo()`.
- El código de fitness usa STFT con `N_FFT=2048` y salto 256, no 1024.
- El croma implementado usa similitud coseno, no distancia euclídea.
- STFT y croma son métricas separadas seleccionables; no existe la fórmula
  compuesta que describía el diseño anterior.
- La regla de evaluación debe contar llamadas reales a fitness; el criterio
  de presupuesto para futuras comparaciones se detalla abajo.

## Próximas dependencias del equipo

1. El equipo ratifica los niveles concretos de los factores de las 12
   configuraciones y el criterio oficial de fitness.
2. Rol 3 publica las interfaces y parámetros acordados para cruce y mutación.
3. Rol 4 conecta esos operadores al ciclo completo y reporta el número real de
   evaluaciones, generaciones y motivo de parada.
4. Con esas decisiones disponibles, Rol 5 puede preparar etapas posteriores
   sin anticipar ni fabricar resultados.

## Plan único de comparación propuesto para ratificación

Documento de entrega y firmas: [diseño conjunto](diseno/diseno_completo_ag_dia1.md).
Esta sección detalla el plan; no registra experimentos ejecutados ni aprobación.

- Factorial completo del Rol 4: N={20,50,100} × élites={1,2} ×
  p_mutación={0.02,0.08}. Son 12 configuraciones distintas, no 12 réplicas.
  Constantes: G=50, torneo k=3, p_cruce=0.90, paciencia=10, tolerancia=1e-4.
- Réplicas: semillas 42,101,2024,7,999 para cada configuración. La matriz
  representa 60 corridas previstas por métrica, no ejecutadas.
- STFT es la propuesta base por ser el valor predeterminado del código;
  comparar con croma en bloques separados, mismas configuraciones, semillas,
  melodía, referencia y protocolo. No comparar sus valores absolutos como si
  tuvieran la misma escala ni promediar ambas métricas en una sola aptitud.
- Tres combinaciones propuestas para la comparación del Rol 3, en un bloque
  separado con configuración base y cinco semillas por combinación/métrica:
  A: torneo + BLX-0.5 + gaussiana (sigma=0.08);
  B: torneo + uniforme + gaussiana;
  C: SUS + BLX-0.5 + no uniforme decreciente.
  Se preservan las variantes previstas en el diseño histórico de Rol 1; esta
  elección de combinaciones es una propuesta explícita, NO un acuerdo firmado.
  Ratificar las firmas, tasas y si la mutación actúa por gen o individuo antes
  de ejecutar; no se implementan aquí. No se añaden configuraciones al factorial.
- Resumir por configuración (sin semilla), combinación, métrica y método:
  media, varianza muestral y desviación estándar muestral entre las cinco
  corridas (`ddof=1`). No ANOVA. `resumir_corridas()` ya entrega media y
  desviación; el cálculo de varianza queda previsto para la etapa de análisis.
  No agrupar configuraciones ni métricas distintas por el mero método.
- El runner del Rol 4 debe devolver `evaluaciones`, `generaciones_ejecutadas`
  y `motivo_parada`, contando cada llamada real a aptitud desde generación 0,
  incluidas reevaluaciones de élites y repeticiones efectivas. Las consultas
  adicionales que influyan en la búsqueda también cuentan. Una aptitud
  reutilizada desde caché no es una evaluación nueva.
- El pseudocódigo actual reevalúa toda la población: E=N*(g+1) si no hay
  llamadas extra y se ejecutan g reemplazos completos. El valor autoritativo
  será el contador real, incluido E con parada temprana, nunca N*G supuesto.
  `ejecutar_baselines_pareados()` usa el E de cada registro AG; la prueba
  unitaria verifica llamadas reales del baseline, no prueba un runner inexistente.
- Registrar configuración, combinación, métrica, semilla, E, generaciones,
  motivo de parada, tiempo y versión del código/datos; mismo conjunto de
  entradas para AG y baseline. No fabricar registros AG para afirmar resultados.
- Boxplot, sensibilidad/tornado, escucha y encuesta de 5–10 personas son
  tareas posteriores. No se ejecutan para completar el Día 1.

## Evidencia de pruebas recibidas

`test_dinamica_rol4.py` contiene 8 pruebas y `test_rol5.py` 6 en los commits
recibidos: 14 en conjunto, no 14 exclusivas del Rol 5. Las pruebas del runner
usan funciones de prueba explícitas para verificar inyección de semillas;
no son corridas AG. La revisión y sus regresiones se registran en
[revision_cierre_dia1.md](revision_cierre_dia1.md).
