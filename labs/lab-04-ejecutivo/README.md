# Lab 4 — Dashboard ejecutivo (hands-on)

## Limpieza mínima del dashboard
Aplica las mismas reglas que los labs anteriores, en una sola pasada al inicio:
- `metrics`: drop latencia<0, cpu>100; NaN → mediana por columna.
- `runs`: drop duraciones imposibles.
- `tickets`: drop resolution<=0 o >100 000; NaN en `priority`/`team` → moda.

## 4 figuras listas para personalizar

1. **`fig1_avail.png`** — Disponibilidad observada + top 3 incidentes por clientes afectados.
2. **`fig2_auto.png`** — Volumen vs success-rate por job (eje secundario).
3. **`fig3_ops.png`** — % breach por equipo.
4. **(fig4)** — Tabla RICE con las 3 acciones priorizadas.

## Cómo escribir una headline ejecutiva

> "Disponibilidad del **99.92%** en el período; el servicio **checkout-api** explica el
> **60%** del error budget consumido en los últimos 30 días."

Reglas:
- 1 cifra grande + 1 responsable + 1 ventana de tiempo.
- Sin acrónimos sin definir.
- Cuantifica el siguiente paso (no "investigar", sino "reducir p95 a < 200 ms en 2 sprints").