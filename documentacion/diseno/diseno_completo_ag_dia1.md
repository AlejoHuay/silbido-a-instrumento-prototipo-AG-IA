# Del silbido a la flauta — Diseño del AG, Día 1

**Estado: BORRADOR revisado técnicamente; pendiente de decisiones, ratificación y cinco firmas.**

**Objetivo y entradas.** Reproducir la melodía de `datos/audio/silbidos/silbido_01.wav`
con timbre de flauta. Se usan `datos/procesados/melodia_01.csv` (16 eventos, 11 notas,
5 silencios; 2.705 s, MIDI 88–96) y `datos/audio/referencias/flauta_referencia_01.wav`
(montaje de muestras instrumentales; JSON con notas y duraciones). WAV de trabajo:
mono, 22050 Hz, PCM16; referencia de 59645 muestras, alineada al CSV.

**Representación y síntesis.** Población `(N,D)`, `D=num_genes()=8`; cada individuo
es `float64` en `[0,1]^8`: tres amplitudes armónicas, ataque, decaimiento, sostenido,
relajación y soplo. Validación del Rol 1. Síntesis: ganancia fija `0.9/2.55` por
`ADSR * (suma de tres armónicos + ruido uniforme de soplo)`; se omiten armónicos
sobre Nyquist y se comprime el ADSR si no cabe. Semilla del ruido independiente del AG.

**Aptitud propuesta.** Maximizar STFT: `1/(1+MAE_dB/10)`, Hann 2048, salto 256,
piso -80 dB y referencia de amplitud 1. Comparación alternativa: similitud coseno
media del croma, también a maximizar. Sin fitness combinado. Ratificación pendiente.

**Operadores y dinámica.** Torneo disponible: `seleccion_torneo(P,F,k=3,rng=rng)`;
sin reemplazo, gana el mayor, empate por orden sorteado y salida copiada.
Previsiones del Día 2: SUS, cruces BLX-0.5/uniforme y mutaciones gaussiana
(sigma 0.08)/no uniforme. Firmas y aplicación de probabilidades aún por acordar.
Base implementada: N=50, elitismo=2, G=50 reemplazos tras generación 0,
p_cruce=0.90 y p_mutación=0.05 (tasas provisionales). Un Generator por corrida.
Parar cuando `max(H[-10:]) - H[-11] < 1e-4`: mejora global acumulada en diez
transiciones; requiere once registros. Es ventana móvil, no contador reiniciable.

**Ciclo completo previsto (reproducción pendiente del Día 2).**
Crear RNG y población → evaluar en orden y contar llamadas → copiar mejor global,
registrar máximo/media/desviación poblacional y diversidad (media de desviaciones
por gen normalizado) → comprobar G o estancamiento → copiar élites → seleccionar
padres, cruzar/mutar según contratos, validar y completar N con copias → reemplazar
→ repetir evaluación. Retornar mejor cromosoma/aptitud, historial, configuración,
semilla, motivo de parada y evaluaciones reales, incluida la población inicial.

**Plan posterior, sin resultados.** Factorial completo 3×2×2: N={20,50,100},
elitismo={1,2}, p_mutación={0.02,0.08}; 12 configuraciones y cinco réplicas
{42,101,2024,7,999}, por métrica. Comparar STFT/croma por separado. Tres combinaciones
propuestas: torneo–BLX–gaussiana; torneo–uniforme–gaussiana; SUS–BLX–no uniforme.
Ratificar niveles, combinaciones y tasas con Roles 3/4. Comparar media, varianza y
desviación muestrales entre semillas, sin ANOVA. Baseline aleatorio con exactamente
las llamadas reales del AG por corrida, incluidas reevaluaciones y parada temprana;
no N*G. En el pseudocódigo actual se reevalúan élites: N*(g+1) si g reemplazos
completos, pero manda el contador. Boxplot, sensibilidad y encuesta a 5–10 personas: posteriores.

**Estado y cierre.** Roles 1/2: datos, genes, síntesis y fitness disponibles;
Rol 3: torneo; Rol 4: componentes y pseudocódigo; Rol 5: demostración y plan.
No existe ciclo reproductivo completo ni corridas experimentales del AG.
Pendientes: ratificar métrica, plan y propuestas de operadores; verificar kernels
limpios y paginación impresa; completar nombres, firmas y fecha personalmente.

| Rol | Nombre | Firma |
|---|---|---|
| 1 — Representación | ____________________ | ____________________ |
| 2 — Síntesis/fitness | ____________________ | ____________________ |
| 3 — Operadores | ____________________ | ____________________ |
| 4 — Dinámica | ____________________ | ____________________ |
| 5 — Análisis/integración | ____________________ | ____________________ |

**Fecha de firma:** ____________________
