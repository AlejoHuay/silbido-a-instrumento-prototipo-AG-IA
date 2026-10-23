# Operadores

| Etapa | Dos variantes implementadas |
|---|---|
| Selección | Torneo k=3 · SUS por lote |
| Cruce | BLX-alpha=0.5 · Uniforme (máscara 0.50) |
| Mutación | Gaussiana (sigma=0.08) · No uniforme (b=2) |

**Validez:** hijos en `[0,1]`, clipping y validación; copias independientes.
**Probabilidades:** cruce 0.90 por pareja; mutación 0.05 por gen, sin doble filtro.

| Combinación | STFT medio ↑ | Diversidad final |
|---|---:|---:|
| A: torneo / BLX / gaussiana | 0.726136 | 0.009409 |
| **B: torneo / uniforme / gaussiana** | **0.730850** | 0.009313 |
| C: SUS / BLX / no uniforme | 0.724787 | 0.125190 |

**Dos semillas: 42 y 101; 2550 evaluaciones por corrida. STFT provisional.**

BLX puede explorar fuera del intervalo parental; torneo favorece explotación.
C conserva más diversidad, sin mayor fitness; cambia selección y mutación a la vez.
**Recomendación preliminar: B por mayor media; dos réplicas no prueban superioridad general.**

[Gráfico existente de diversidad para insertar](../../resultados/operadores/dia3_2026-10-21_64617f8/diversidad.svg)
