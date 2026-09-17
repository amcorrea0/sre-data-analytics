# Guía del facilitador — Sesión de 60 minutos

## Agenda (cronometrada)

| Min  | Bloque                                | Quien conduce | Material                                     |
|------|---------------------------------------|---------------|----------------------------------------------|
| 0–5  | Bienvenida + setup                    | Facilitador   | `README.md` (venv + generate_data)            |
| 5–17 | **Lab 1** Observabilidad (guiado)     | Facilitador   | `lab1_observabilidad.ipynb` (4 figuras)      |
| 17–29| **Lab 2** Automatización (guiado)     | Facilitador   | `lab2_automatizacion.ipynb` (5 figuras)      |
| 29–41| **Lab 3** Tickets (hands-on)          | SREs          | `lab3_requerimientos.ipynb` (6 figuras)      |
| 41–53| **Lab 4** Dashboard ejecutivo         | SREs          | `lab4_ejecutivo.ipynb` (3 + RICE)            |
| 53–60| Cierre + insights compartidos         | Grupo         | —                                            |

## Antes de la sesión (T-24h)
- [ ] Regenerar datos si la fecha cambió: `python notebooks\generate_data.py`.
- [ ] Renderizar HTML (las figuras PNG se exportan a `html/`).
- [ ] Compartir a los SREs: `README.md` + los 4 READMEs en `labs/lab-0X-*/README.md`.
- [ ] Confirmar `.venv` activado y notebooks abiertos (los PNGs ya están en pantalla).
- [ ] Si la red esta lenta, copiar `pip install` a un script local pre-descargado.

## Cómo correr los labs **guiados**
1. Proyectar tu pantalla en Jupyter (zoom 125%). Las figuras se ven bien en pantalla completa.
2. Hacer cada celda en vivo y **explicar el por que** antes del como:
   - Por que **mediana** y no media para imputar.
   - Por que **escala log** en boxplots de latencia / duracion.
   - Por que **IQR por grupo** y no global.
3. Antes de pasar al siguiente lab, pedir a 2 SREs que repitan la ultima celda en su notebook.

## Cómo correr los labs **hands-on**
1. Enunciar el objetivo y dar 60 s de lectura del README del lab.
2. Los SREs trabajan en parejas (pair-programming) y comparten insights al final.
3. El facilitador circula y resuelve bloqueos (`groupby`, `resample`, `fillna`, `boxplot`).
4. **Pit-stop a los 8 minutos**: cada dupla dice 1 hallazgo en 15 s.

## Prompts de discusión por lab

### Lab 1 (figuras: nan, dist, boxplot, outliers)
- Por que p95 > media para alertar latencia?
- Como se traduce `error_rate_mean` a disponibilidad mensual?
- Outlier = incidente real o sensor roto? Como decidir.

### Lab 2 (figuras: nan, boxplot, success, hourly, trigger)
- Cual es el job con peor `success_rate` y por que preocupa?
- Que trigger tiene el success-rate mas bajo?
- Outliers arriba del bigote: optimizar. Negativos: abrir bug del exporter.

### Lab 3 (figuras: nan, daily, heatmap, boxplot, breach, rollback)
- Que equipo concentra la mayor carga?
- La tasa de breach correlaciona con la prioridad?
- Los outliers de resolucion se concentran en lunes 9–11 a.m.?

### Lab 4 (figuras: avail, auto, ops + RICE)
- Una cifra por seccion o un parrafo? Justificar.
- Que accion (RICE mas alto) priorizaran esta semana?

## Cierre (últimos 7 min)
- Cada dupla comparte su **frase ejecutiva** del lab 4.
- Mural y voto: la headline mas clara.
- Tarea post-sesión: aplicar el mismo ejercicio a **1 semana real** de su servicio.

## Señales de que la sesión va bien
- Al menos 1 insight inesperado por dupla al final de cada lab.
- Preguntas sobre **interpretacion** de figuras, no solo sintaxis.
- Algun SRE propone una métrica que **no** esta en los datasets.

## Señales de riesgo
- Errores de instalacion al inicio -> tener `requirements.txt` + Python 3.11 portable como plan B.
- Grupo silencioso en hands-on -> asignar duplicas explicitas en chat antes de empezar.
- Notebooks lentos al cargar figuras -> exportar PNGs pre-renderizados de `html/`.