# Lab 1 — Observabilidad: ETL + estadística + outliers (guiado)

## Datos faltantes y cómo arreglarlos

| Columna       | Problema                                | Tratamiento aplicado |
|---------------|-----------------------------------------|----------------------|
| `latency_ms`  | ~0.3% NaN + **0.5%** con valores `< 0`  | drop errores técnicos (físicamente imposibles), imputar NaN con **mediana** del servicio |
| `cpu_pct`     | ~0.2% NaN + **0.2%** con valores `> 100` | drop errores técnicos, imputar NaN con **mediana** |
| `error_rate`  | OK, ya acotado [0, 1]                   | sin cambios |
| `ts`, `service`, `region`, `env` | OK | sin cambios |

> Por qué mediana y no media: la mediana es **robusta a outliers**. En `latency_ms` hay picos
> de incidentes reales (~600 ms) y valores negativos basura. La mediana no se mueve con
> ninguno de los dos extremos.

## Figuras y cómo interpretarlas

1. **`fig1_nan.png`** — Heatmap amarillo/verde de NaN. Bandas horizontales delatan inyector.
2. **`fig2_latency_dist.png`** — Histograma+KDE crudo vs limpio + líneas media/mediana.
   En "crudo" la cola izquierda negativa revela errores técnicos; en "limpio" la media se
   acerca a la mediana.
3. **`fig3_boxplot.png`** — Latencia por servicio (eje log). **Puntos arriba del bigote
   = outliers Tukey** (Q3 + 1.5 × IQR). Outliers simétricos arriba y abajo suelen ser
   dato malo; outliers **solo arriba** suelen ser **incidentes**.
4. **`fig4_outliers_per_service.png`** — Conteo de outliers Tukey por servicio. Nos dice
   **dónde duele**.

## Regla de Tukey (IQR)

Para una métrica numérica:
- Q1 = percentil 25, Q3 = percentil 75, IQR = Q3 − Q1.
- **Outlier alto** si valor > Q3 + 1.5·IQR.
- **Outlier bajo** si valor < Q1 − 1.5·IQR.

Se aplica **por grupo** (servicio), no sobre todo el dataset, porque cada servicio tiene su
propia escala.

## Discusión
- ¿Por qué p95 > media para alertar latencia?
- ¿Cómo se traduce `error_rate` promedio mensual a disponibilidad?
- Outlier = incidente real o sensor roto? Cómo decidir.