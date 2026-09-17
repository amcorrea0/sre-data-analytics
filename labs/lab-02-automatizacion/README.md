# Lab 2 — Automatización: jobs, MTTR, outliers de duración (guiado)

## Datos faltantes y cómo arreglarlos

| Columna        | Problema                                | Tratamiento |
|----------------|-----------------------------------------|-------------|
| `duration_sec` | ~0.5% NaN + **1%** con valores `< 0` o `> 86400` | drop imposibles, NaN → **mediana del job** |
| `job_name`     | ~0.3% NaN                               | NaN → **moda** global |

> Truco: la imputación por grupo (mediana por `job_name`) preserva la forma del boxplot
> por job. Imputar con la mediana **global** mezclaría escalas.

## Figuras y cómo interpretarlas

1. **`fig1_nan.png`** — Heatmap de NaN. Si no hay bandas verticales, está limpio.
2. **`fig2_boxplot.png`** — Boxplot por job (eje log). Caja = Q1–Q3, rayita = mediana,
   bigotes = Tukey. Puntos fuera = jobs lentos.
3. **`fig3_success.png`** — Tasa de éxito. La barra corta == job problematico.
4. **`fig4_hourly.png`** — Runs por hora del dia. Picos nocturnos == batch.
5. **`fig5_trigger.png`** — Pie de triggers + barras de success-rate. Un trigger
   con alta participacion **y** baja tasa es candidato a automatizar mejor.

## Decisión rápida
- Outlier **arriba** del bigote: job lento real -> optimizar.
- Valor **negativo o > 24 h**: error técnico -> drop y abrir bug del exporter.