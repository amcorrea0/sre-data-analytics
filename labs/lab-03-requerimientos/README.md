# Lab 3 — Requerimientos operación: tickets y outliers (hands-on)

## Datos faltantes y cómo arreglarlos

| Columna         | Problema                              | Tratamiento |
|-----------------|---------------------------------------|-------------|
| `priority`      | ~2% NaN                               | NaN → **moda** (categorica, no se inventa) |
| `team`          | ~1.5% NaN                             | NaN → **moda** |
| `resolution_min`| ~1% con valores `<= 0` o `> 100 000`  | drop errores técnicos antes de boxplot |

> Importante: imputar la moda no cambia el conteo de breach global (un NaN en `priority`
> **sí** lo cambiaria si se filtra con `breach=(resolution>sla)`. Por eso conviene
> recuperar prioridad primero.

## Figuras (6)

1. **`fig1_nan.png`** — mapa de NaN.
2. **`fig2_daily.png`** — Tickets por día (lineplot). Picos en lunes = incidentes batch.
3. **`fig3_heatmap.png`** — pivote team × category, escala `YlGnBu` con números encima.
4. **`fig4_boxplot.png`** — `resolution_min` por equipo en escala **log**. La escala log es
   clave: sin ella, 1 ticket de 24 h aplasta toda la distribución.
5. **`fig5_breach.png`** — % breach de SLA por equipo.
6. **`fig6_rollback.png`** — % rollback entre cambios (solo `category=='change'`).

## Cómo leer un boxplot (recordatorio)
- Caja = percentiles 25–75 (IQR).
- Rayita dentro = mediana.
- Bigotes = Tukey (1.5 × IQR).
- **Puntos fuera** = outliers. **Si son solo arriba**, suelen ser incidentes reales.

## Plantilla de insight ejecutivo (1 línea por seccion)
- **Carga:** "el equipo **___** concentra el **__%** de tickets del período."
- **Breach:** "el equipo **___** lidera el breach con **__%**; el promedio es __%."
- **Outlier:** "los tickets outliers se concentran los **lunes 9–11 a.m.**"
- **Accion:** "la accion priorizada es ___, RICE = ___."