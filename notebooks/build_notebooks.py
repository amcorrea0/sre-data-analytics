"""Construye los 4 notebooks (.ipynb) del programa v3.

Cambios vs v2:
- Cada seccion inicia con markdown explicando QUE BUSCAMOS y POR QUE.
- Bloques de texto (markdown cells) usan tildes correctas.
- Codigo Python sigue siendo ASCII (sin tildes en variables/strings).
- Salida sigue exportando PNG al directorio html/.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / "notebooks"
NB_DIR.mkdir(parents=True, exist_ok=True)


def cell(code: str, cell_type: str = "code") -> dict:
    return {
        "cell_type": cell_type,
        "execution_count": None if cell_type == "markdown" else 0,
        "metadata": {},
        "outputs": [] if cell_type == "code" else None,
        "source": code.splitlines(keepends=True),
    }


def md(text: str) -> dict:
    return cell(text, cell_type="markdown")


def py(code: str) -> dict:
    return cell(code, cell_type="code")


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.13"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


# ============================================================================
# Contexto precomputado (se imprime como markdown entre celdas)
# ============================================================================
CTX_LIMPIEZA = """
**Qué buscamos:** aislar los datos físicamente imposibles (latencias negativas,
CPU > 100 %) y los NaN, para que el análisis posterior refleje el servicio real.

**Por qué:** la media y los percentiles se distorsionan con valores basura
y reportan disponibilidad falsa. Un solo `latency_ms = -50` basta para
arrastrar la media hacia abajo.

**Reglas que aplicamos:**
- `latency_ms < 0` → drop (error del exporter).
- `latency_ms > 10 000` → drop.
- `cpu_pct < 0 | > 100` → drop.
- `NaN` en numéricas → imputar con la **mediana** del servicio (es robusta a outliers).
"""

CTX_TUKEY = """
**Qué buscamos:** saber qué servicios están sufriendo incidentes reales.

**Por qué importa Tukey (IQR × 1.5):**
- Media y p50 esconden los picos.
- La mediana es robusta, pero necesitamos un criterio operativo para etiquetar
  un valor como "anómalo" y actuar.

**Lectura del boxplot:**
- Caja = percentiles 25–75 (IQR).
- Rayita dentro = mediana.
- Bigotes = `Q3 + 1.5·IQR` (arriba) y `Q1 - 1.5·IQR` (abajo).
- Puntos fuera del bigote = outliers. Solo arriba = incidente unilateral.
"""


def plot_setup() -> str:
    return (
        "import matplotlib.pyplot as plt\n"
        "import seaborn as sns\n"
        "sns.set_theme(style='whitegrid', palette='muted')\n"
        "plt.rcParams['figure.figsize'] = (10, 4)\n"
    )


# ============================================================================
# Lab 1 — Observabilidad
# ============================================================================
LAB_1 = notebook([
    md("# Lab 1 — Observabilidad: ETL + estadística + outliers\n"
       "\n"
       "**Modalidad:** guiado · **Duración:** ~12 min\n"
       "**Datasets:** `metrics_timeseries.csv`, `incidents.csv`, `slo_burn.csv`\n"
       "\n"
       "## Objetivo general\n"
       "Aprender el ciclo ETL con pandas y las primeras medidas de **estadística "
       "descriptiva** sobre series temporales de observabilidad: media, mediana, "
       "percentiles y **dispersión**. Detectar NaN y errores del exporter.\n"
       "\n"
       "## Entregable\n"
       "Un mini-reporte con 3 KPIs por servicio y un gráfico por KPI, en este notebook."),
    py("import pandas as pd\n"
       "import numpy as np\n"
       "from pathlib import Path\n"
       "import matplotlib.pyplot as plt\n"
       "import seaborn as sns\n"
       "sns.set_theme(style='whitegrid', palette='muted')\n"
       "plt.rcParams['figure.figsize'] = (10, 4)\n"
       "\n"
       "DATA = Path('..') / 'data'\n"
       "metrics = pd.read_csv(DATA / 'metrics_timeseries.csv', parse_dates=['ts'])\n"
       "incidents = pd.read_csv(DATA / 'incidents.csv', parse_dates=['opened_at', 'resolved_at'])\n"
       "burn = pd.read_csv(DATA / 'slo_burn.csv', parse_dates=['ts'])\n"
       "metrics.shape, incidents.shape, burn.shape"),
    md("## 1. Diagnóstico — mapa de calor de faltantes\n"
       "\n" + CTX_LIMPIEZA + "\n"),
    py("fig, ax = plt.subplots(figsize=(10, 4))\n"
       "sns.heatmap(metrics.isnull(), cbar=False, yticklabels=False, cmap='viridis')\n"
       "ax.set_title('Mapa de NaN en metrics_timeseries.csv (amarillo = faltante)')\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab1_fig1_nan.png', dpi=110, bbox_inches='tight')\n"
       "plt.show()"),
    md("## 2. Limpieza — qué datos faltan y cómo arreglarlos\n"
       "\n"
       "| Columna       | Qué falta                                | Cómo arreglar                                |\n"
       "|---------------|------------------------------------------|----------------------------------------------|\n"
       "| `latency_ms`  | ~0.3 % NaN + 0.5 % con valores < 0       | Drop errores + imputar con la **mediana**     |\n"
       "| `cpu_pct`     | ~0.2 % NaN + 0.2 % con valores > 100     | Drop errores + imputar con la **mediana**     |\n"
       "| `error_rate`  | OK (ya acotado 0–1)                       | Sin cambios                                   |"),
    py("def clean_numeric(df, col, lo, hi):\n"
       "    bad = (df[col] < lo) | (df[col] > hi)\n"
       "    print(f'{col}: {bad.sum()} valores imposibles borrados')\n"
       "    df = df.loc[~bad].copy()\n"
       "    med = df[col].median()\n"
       "    df[col] = df[col].fillna(med)\n"
       "    return df\n"
       "\n"
       "metrics = clean_numeric(metrics, 'latency_ms', 0, 10_000)\n"
       "metrics = clean_numeric(metrics, 'cpu_pct', 0, 100)\n"
       "print('shape limpio:', metrics.shape)"),
    md("## 3. Distribución — histograma + KDE + líneas de media / mediana\n"
       "\n"
       "**Qué comparamos:** cómo cambia la distribución de latencia al limpiar outliers.\n\n"
       "**Por qué:** en el histograma crudo verás la cola izquierda negativa revelando "
       "los errores del exporter. En el limpio, media y mediana se acercan."),
    py("fig, ax = plt.subplots(1, 2, figsize=(14, 4))\n"
       "for i, (label, lo, hi) in enumerate([('crudo', 0, 1500), ('limpio', 0, 600)]):\n"
       "    ax[i].set_title(f'latency_ms — {label}')\n"
       "    if label == 'crudo':\n"
       "        s = pd.read_csv(DATA / 'metrics_timeseries.csv', parse_dates=['ts'])['latency_ms'].dropna()\n"
       "    else:\n"
       "        s = metrics['latency_ms']\n"
       "    s = s[(s >= lo) & (s <= hi)]\n"
       "    sns.histplot(s, kde=True, bins=40, color='steelblue', ax=ax[i])\n"
       "    ax[i].axvline(s.mean(), color='red', linestyle='--', label=f'media={s.mean():.1f}')\n"
       "    ax[i].axvline(s.median(), color='green', linestyle='--', label=f'mediana={s.median():.1f}')\n"
       "    ax[i].legend()\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab1_fig2_latency_dist.png', dpi=110, bbox_inches='tight')\n"
       "plt.show()"),
    md("## 4. Boxplot por servicio (outliers visuales)\n"
       "\n" + CTX_TUKEY),
    py("fig, ax = plt.subplots(figsize=(12, 5))\n"
       "sns.boxplot(data=metrics, x='service', y='latency_ms', hue='service', legend=False, ax=ax)\n"
       "ax.set_yscale('log')\n"
       "ax.set_title('Latencia por servicio (eje log) — los puntos arriba del bigote son outliers Tukey')\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab1_fig3_boxplot.png', dpi=110, bbox_inches='tight')\n"
       "plt.show()"),
    md("## 5. Regla de Tukey — explicita para `latency_ms`\n"
       "\n"
       "**Qué buscamos:** traducir la visualización del boxplot a una métrica operable.\n\n"
       "**Por qué:** un operador necesita saber *cuántos* outliers por servicio, no solo *verlos*."),
    py("def iqr_outliers(df, col, by):\n"
       "    q1 = df.groupby(by)[col].quantile(0.25)\n"
       "    q3 = df.groupby(by)[col].quantile(0.75)\n"
       "    iqr = q3 - q1\n"
       "    low = (q1 - 1.5 * iqr).rename('low')\n"
       "    high = (q3 + 1.5 * iqr).rename('high')\n"
       "    return pd.concat([q1.rename('q1'), q3.rename('q3'), iqr.rename('iqr'), low, high], axis=1).round(2)\n"
       "\n"
       "bounds = iqr_outliers(metrics, 'latency_ms', 'service')\n"
       "bounds"),
    py("def flag_outliers(df, col, by):\n"
       "    q1 = df.groupby(by)[col].quantile(0.25)\n"
       "    q3 = df.groupby(by)[col].quantile(0.75)\n"
       "    iqr = q3 - q1\n"
       "    low = q1 - 1.5 * iqr\n"
       "    high = q3 + 1.5 * iqr\n"
       "    return ((df[col] < df[by].map(low)) | (df[col] > df[by].map(high)))\n"
       "\n"
       "metrics['is_outlier'] = flag_outliers(metrics, 'latency_ms', 'service')\n"
       "print(f\"Outliers Tukey en latency_ms: {metrics['is_outlier'].sum():,} \"\n"
       "      f\"({metrics['is_outlier'].mean():.2%})\")\n"
       "metrics.groupby('service')['is_outlier'].mean().round(4).sort_values(ascending=False)"),
    md("## 6. Insight ejecutivo — cabeza de línea por carga\n"
       "\n"
       "**Qué comunicamos:** el SLO del servicio top con más outliers y por qué.\n\n"
       "**Por qué:** el boxplot y los números sirven al equipo, pero el director necesita "
       "una sola cifra. Cerramos con **p95** y **burn-rate 5x**."),
    py("agg = metrics.groupby('service').agg(\n"
       "    cpu_mean=('cpu_pct', 'mean'),\n"
       "    cpu_p95=('cpu_pct', lambda s: s.quantile(0.95)),\n"
       "    lat_mean=('latency_ms', 'mean'),\n"
       "    p95_lat=('latency_ms', lambda s: s.quantile(0.95)),\n"
       "    err_rate=('error_rate', 'mean'),\n"
       "    rps_total=('rps', 'sum'),\n"
       "    outliers=('is_outlier', 'sum'),\n"
       ")\n"
       "agg.round(3)"),
    py("fig, ax = plt.subplots(figsize=(10, 4))\n"
       "agg['outliers'].sort_values().plot(kind='barh', color='salmon', ax=ax)\n"
       "ax.set_title('Outliers Tukey en latency_ms por servicio (suma en el periodo)')\n"
       "ax.set_xlabel('# outliers')\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab1_fig4_outliers_per_service.png', dpi=110, bbox_inches='tight')\n"
       "plt.show()"),
    md("## Para discutir\n"
       "- ¿Por qué p95 > media para alertar latencia?\n"
       "- ¿Cómo se traduce `error_rate` promedio mensual a disponibilidad?\n"
       "- Outliers = incidente real o sensor roto? Cómo decidir."),
])


# ============================================================================
# Lab 2 — Automatización
# ============================================================================
LAB_2 = notebook([
    md("# Lab 2 — Automatización: jobs, MTTR y outliers de duración\n"
       "\n"
       "**Modalidad:** guiado · **Duración:** ~12 min\n"
       "**Dataset:** `automation_runs.csv`\n"
       "\n"
       "## Objetivo general\n"
       "Medir la **confiabilidad de la automatización**: tasa de éxito, MTTR de jobs, "
       "distribución de retries y costo operativo por job.\n"
       "\n"
       "## Entregable\n"
       "Tabla por `job_name` con: runs, success_rate, retries promedio, MTTR (mediana y "
       "p95 de `duration_sec` agrupado por `status`)."),
    py("import pandas as pd\n"
       "import numpy as np\n"
       "from pathlib import Path\n"
       "import matplotlib.pyplot as plt\n"
       "import seaborn as sns\n"
       "sns.set_theme(style='whitegrid', palette='muted')\n"
       "plt.rcParams['figure.figsize'] = (10, 4)\n"
       "\n"
       "DATA = Path('..') / 'data'\n"
       "runs = pd.read_csv(DATA / 'automation_runs.csv', parse_dates=['started_at'])\n"
       "runs.head()"),
    md("## 1. Diagnóstico de faltantes y errores técnicos\n"
       "\n"
       "**Qué buscamos:** tres tipos de datos problemáticos — NaN en `duration_sec`, "
       "NaN en `job_name`, y duraciones físicamente imposibles.\n\n"
       "**Por qué:** la imputación por grupo (mediana del job) preserva la forma del "
       "boxplot. Imputar con la global mezclaría escalas entre jobs."),
    py("fig, ax = plt.subplots(figsize=(10, 4))\n"
       "sns.heatmap(runs.isnull(), cbar=False, yticklabels=False, cmap='viridis')\n"
       "ax.set_title('Mapa de NaN — automation_runs.csv')\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab2_fig1_nan.png', dpi=110, bbox_inches='tight')\n"
       "plt.show()"),
    py("bad = (runs['duration_sec'] < 0) | (runs['duration_sec'] > 86400)\n"
       "print(f'duraciones imposibles: {bad.sum()}')\n"
       "runs = runs.loc[~bad].copy()\n"
       "med_by_job = runs.groupby('job_name')['duration_sec'].transform('median')\n"
       "runs['duration_sec'] = runs['duration_sec'].fillna(med_by_job)\n"
       "jobs_mode = runs['job_name'].mode().iloc[0]\n"
       "runs['job_name'] = runs['job_name'].fillna(jobs_mode)\n"
       "print('shape limpio:', runs.shape)"),
    md("## 2. Distribución — boxplot por job (escala log)\n"
       "\n"
       "**Qué buscamos:** separar jobs lentos reales (outliers arriba) de jobs normales.\n\n"
       "**Por qué la escala log:** la mediana de `purge_cache` puede ser 2 s y la de "
       "`db_vacuum` 200 s. Sin log, los pequeños desaparecen.\n\n" + CTX_TUKEY),
    py("fig, ax = plt.subplots(figsize=(12, 5))\n"
       "order = runs.groupby('job_name')['duration_sec'].median().sort_values().index\n"
       "sns.boxplot(data=runs, x='job_name', y='duration_sec', order=order, hue='job_name', legend=False, ax=ax)\n"
       "ax.set_yscale('log')\n"
       "ax.set_title('Duración por job (log) — outliers = jobs muy lentos')\n"
       "ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha='right')\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab2_fig2_boxplot.png', dpi=110, bbox_inches='tight')\n"
       "plt.show()"),
    md("## 3. Métricas por job\n"
       "\n"
       "**Qué buscamos:** ranking operativo de jobs por confiabilidad.\n\n"
       "**Por qué importa:** con la success_rate y los retries vemos dónde la "
       "automatización está fallando más — candidato a ser reemplazada o tuneada."),
    py("by_job = runs.groupby('job_name').agg(\n"
       "    runs=('run_id', 'count'),\n"
       "    success_rate=('status', lambda s: (s == 'success').mean()),\n"
       "    avg_retries=('retries', 'mean'),\n"
       "    p50_dur=('duration_sec', lambda s: s.quantile(0.5)),\n"
       "    p95_dur=('duration_sec', lambda s: s.quantile(0.95)),\n"
       ")\n"
       "by_job.sort_values('success_rate')"),
    py("fig, ax = plt.subplots(figsize=(10, 4))\n"
       "by_job['success_rate'].sort_values().plot(kind='barh', color='teal', ax=ax)\n"
       "ax.set_title('Tasa de éxito por job')\n"
       "ax.set_xlabel('success rate')\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab2_fig3_success.png', dpi=110, bbox_inches='tight')\n"
       "plt.show()"),
    md("## 4. MTTR — mediana de duración en fallos\n"
       "\n"
       "**Qué entendemos por MTTR:** tiempo que tarda el job en *fallar* o hacer timeout. "
       "No la duración de runs exitosos.\n\n"
       "**Por qué la mediana y no la media:** porque en fallos suele haber valores extremos."),
    py("failed = runs[runs['status'].isin(['failed', 'timeout'])]\n"
       "mttr = failed.groupby('job_name')['duration_sec'].median().rename('mttr_sec')\n"
       "by_job_full = by_job.join(mttr).fillna(0)\n"
       "by_job_full.sort_values('mttr_sec', ascending=False)"),
    py("# Conteo de ejecuciones por hora del dia (ciclo)\n"
       "runs['hour'] = runs['started_at'].dt.hour\n"
       "fig, ax = plt.subplots(figsize=(10, 4))\n"
       "runs.groupby('hour').size().plot(kind='bar', color='slategray', ax=ax)\n"
       "ax.set_title('Runs por hora del día — picos = batch nocturno')\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab2_fig4_hourly.png', dpi=110, bbox_inches='tight')\n"
       "plt.show()"),
    md("## 5. Distribución por trigger\n"
       "\n"
       "**Qué buscamos:** qué origen dispara más automatización y cuál falla más.\n\n"
       "**Por qué importa:** un trigger ruidoso es candidato a mejor runbook o a "
       "alertas que no deberían terminar en un job automático."),
    py("fig, ax = plt.subplots(1, 2, figsize=(14, 4))\n"
       "runs['triggered_by'].value_counts().plot(kind='pie', ax=ax[0], autopct='%1.0f%%')\n"
       "ax[0].set_ylabel('')\n"
       "ax[0].set_title('Trigger')\n"
       "success_by_trigger = runs.groupby('triggered_by').apply(lambda g: (g['status']=='success').mean())\n"
       "success_by_trigger.sort_values().plot(kind='barh', color='mediumseagreen', ax=ax[1])\n"
       "ax[1].set_title('Success-rate por trigger')\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab2_fig5_trigger.png', dpi=110, bbox_inches='tight')\n"
       "plt.show()"),
    md("## Para discutir\n"
       "- ¿Qué job explica más del 50 % del `mttr` total?\n"
       "- ¿Cuál trigger es el más ruidoso (más fallos)?\n"
       "- Cómo decidir si un outlier es **saturación** o **bug**."),
])


# ============================================================================
# Lab 3 — Tickets (hands-on)
# ============================================================================
LAB_3 = notebook([
    md("# Lab 3 — Requerimientos de la operación (hands-on)\n"
       "\n"
       "**Modalidad:** hands-on · **Duración:** ~12 min\n"
       "**Dataset:** `tickets.csv`\n"
       "\n"
       "## Objetivo general\n"
       "Caracterizar la **demanda operativa**: volumen por equipo, categoría y prioridad; "
       "cumplimiento de SLA y tasa de rollback de cambios.\n"
       "\n"
       "## Buenas prácticas\n"
       "- **NaN ≠ 0.** Si imputas, declara cómo (mediana, moda, drop).\n"
       "- Outliers en tiempo de resolución suelen ser **incidentes** (lunes a las 9 a.m.).\n"
       "- Un boxplot por equipo/prioridad te lo muestra en una sola imagen.\n"
       "\n"
       "## Entregable\n"
       "Un mini-reporte con 5 celdas: volumen, pivot, breach global, top-3 breach, rollback."),
    md("## 1. Carga + diagnóstico de NaN\n"
       "\n"
       "**Qué buscamos:** saber si hay columnas con datos faltantes y dónde están.\n\n"
       "**Por qué:** un NaN en `priority` cambia el cálculo de breach. Hay que "
       "recuperarlo antes."),
    py("import pandas as pd\n"
       "import numpy as np\n"
       "from pathlib import Path\n"
       "import matplotlib.pyplot as plt\n"
       "import seaborn as sns\n"
       "sns.set_theme(style='whitegrid', palette='muted')\n"
       "plt.rcParams['figure.figsize'] = (10, 4)\n"
       "\n"
       "DATA = Path('..') / 'data'\n"
       "tickets = pd.read_csv(DATA / 'tickets.csv', parse_dates=['created_at'])\n"
       "tickets.shape\n"
       "fig, ax = plt.subplots(figsize=(10, 3))\n"
       "sns.heatmap(tickets.isnull(), cbar=False, yticklabels=False, cmap='viridis', ax=ax)\n"
       "ax.set_title('NaN — tickets.csv (cuanto más amarillo, más faltante)')\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab3_fig1_nan.png', dpi=110, bbox_inches='tight')\n"
       "plt.show()"),
    md("## 2. Volumen diario\n"
       "\n"
       "**Qué vemos:** la serie temporal de tickets creados cada día.\n\n"
       "**Qué buscar:** picos recurrentes (¿siempre los lunes a las 9?) y mesetas "
       "(¿estamos saturando al equipo?)."),
    py("vol = tickets.set_index('created_at').resample('D').size()\n"
       "fig, ax = plt.subplots(figsize=(10, 4))\n"
       "vol.plot(ax=ax, color='steelblue')\n"
       "ax.set_title('Tickets por día')\n"
       "ax.set_ylabel('# tickets')\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab3_fig2_daily.png', dpi=110, bbox_inches='tight')\n"
       "plt.show()"),
    md("## 3. Heatmap team × categoría\n"
       "\n"
       "**Qué buscamos:** dónde se concentra la carga operativa.\n\n"
       "**Por qué:** con un solo vistazo sabemos a qué equipo pedirle soporte y en qué "
       "tipo de tickets."),
    py("pivot = tickets.pivot_table(index='team', columns='category', values='ticket_id', aggfunc='count', fill_value=0)\n"
       "fig, ax = plt.subplots(figsize=(8, 4))\n"
       "sns.heatmap(pivot, annot=True, fmt='d', cmap='YlGnBu', ax=ax)\n"
       "ax.set_title('Volumen por equipo × categoría (cuanto más oscuro, más carga)')\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab3_fig3_heatmap.png', dpi=110, bbox_inches='tight')\n"
       "plt.show()"),
    md("## 4. Boxplot de tiempo de resolución por equipo (escala log)\n"
       "\n"
       "**Qué vemos:** cada equipo como un boxplot distinto.\n\n"
       "**Por qué la escala log:** porque la mezcla de minutos y días hace que la "
       "distribución sea muy asimétrica; sin log, los outliers aplastan todo.\n\n" + CTX_TUKEY),
    py("t = tickets[(tickets['resolution_min'] > 0) & (tickets['resolution_min'] < 100_000)].copy()\n"
       "fig, ax = plt.subplots(figsize=(10, 4))\n"
       "order = t.groupby('team')['resolution_min'].median().sort_values().index\n"
       "sns.boxplot(data=t, x='team', y='resolution_min', order=order, hue='team', legend=False, ax=ax)\n"
       "ax.set_yscale('log')\n"
       "ax.set_title('Tiempo de resolución por equipo (log) — outliers = incidentes')\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab3_fig4_boxplot.png', dpi=110, bbox_inches='tight')\n"
       "plt.show()"),
    md("## 5. Breach SLA — global y por equipo\n"
       "\n"
       "**Qué entendemos por breach:** un ticket cuyo `resolution_min` supera el SLA "
       "definido en `sla_min`.\n\n"
       "**Por qué importa:** breach alto en un equipo = cuello de capacidad o necesidad "
       "de automatizar."),
    py("tickets['priority'] = tickets['priority'].fillna(tickets['priority'].mode().iloc[0])\n"
       "print(f'Breach global: {tickets[\"sla_breached\"].mean():.2%}')\n"
       "fig, ax = plt.subplots(figsize=(8, 4))\n"
       "tickets.groupby('team')['sla_breached'].mean().sort_values(ascending=False).plot(kind='bar', color='indianred', ax=ax)\n"
       "ax.set_ylabel('% breach SLA')\n"
       "ax.set_title('Breach por equipo (de mayor a menor, datos del periodo)')\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab3_fig5_breach.png', dpi=110, bbox_inches='tight')\n"
       "plt.show()"),
    md("## 6. Rollback en cambios\n"
       "\n"
       "**Qué buscamos:** de los cambios (`category == 'change'`), cuántos terminaron en rollback.\n\n"
       "**Por qué:** un rollback rate alto = cambios mal probados o sin revisión "
       "suficiente; candidato a postmortem."),
    py("changes = tickets[tickets['category'] == 'change']\n"
       "fig, ax = plt.subplots(figsize=(8, 4))\n"
       "changes.groupby('team')['rollback'].mean().sort_values(ascending=False).plot(kind='bar', color='goldenrod', ax=ax)\n"
       "ax.set_ylabel('% rollback')\n"
       "ax.set_title('Rollback rate por equipo (solo cambios)')\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab3_fig6_rollback.png', dpi=110, bbox_inches='tight')\n"
       "plt.show()"),
    md("## Insights a compartir\n"
       "- Equipo top en carga y equipo top en breach **¿son el mismo**?\n"
       "- ¿Los outliers de resolución se concentran los **lunes 9 a.m.**?\n"
       "- ¿Qué patrón de rollback merece un postmortem?"),
])


# ============================================================================
# Lab 4 — Dashboard ejecutivo (hands-on)
# ============================================================================
LAB_4 = notebook([
    md("# Lab 4 — Dashboard ejecutivo: de datos a historia (hands-on)\n"
       "\n"
       "**Modalidad:** hands-on · **Duración:** ~12 min\n"
       "\n"
       "## Objetivo\n"
       "Construir una tabla resumen (1 página, 4 secciones) que un director pueda "
       "leer en 60 segundos. Practicar el principio **\"una cifra, una historia\"**.\n"
       "\n"
       "## Estructura del reporte\n"
       "1. **Disponibilidad y SLOs** — error budget consumido, top 3 incidentes.\n"
       "2. **Automatización** — success rate global, job con peor MTTR, retries.\n"
       "3. **Demanda operativa** — tickets/día, breach SLA por equipo, rollback.\n"
       "4. **Recomendaciones** — 3 acciones priorizadas (RICE simple).\n"
       "\n"
       "## Plantilla\n"
       "Las celdas ya están armadas — solo tienes que conectar los datos correctos."),
    md("## 0. Carga + limpieza mínima\n"
       "\n"
       "**Qué hacemos:** una sola pasada de limpieza para que las 4 secciones siguientes "
       "trabajen sobre datos coherentes.\n\n"
       "**Por qué centralizada:** aplicamos el mismo criterio que aprendimos en los "
       "labs anteriores."),
    py("import pandas as pd\n"
       "import numpy as np\n"
       "from pathlib import Path\n"
       "import matplotlib.pyplot as plt\n"
       "import seaborn as sns\n"
       "sns.set_theme(style='whitegrid', palette='muted')\n"
       "plt.rcParams['figure.figsize'] = (10, 4)\n"
       "\n"
       "DATA = Path('..') / 'data'\n"
       "metrics = pd.read_csv(DATA / 'metrics_timeseries.csv', parse_dates=['ts'])\n"
       "incidents = pd.read_csv(DATA / 'incidents.csv', parse_dates=['opened_at', 'resolved_at'])\n"
       "burn = pd.read_csv(DATA / 'slo_burn.csv', parse_dates=['ts'])\n"
       "runs = pd.read_csv(DATA / 'automation_runs.csv', parse_dates=['started_at'])\n"
       "tickets = pd.read_csv(DATA / 'tickets.csv', parse_dates=['created_at'])"),
    py("# ==== Limpieza minima necesaria para el dashboard ====\n"
       "# metrics: drop errores tecnicos + imputar mediana en numericas\n"
       "for col, lo, hi in [('latency_ms', 0, 10_000), ('cpu_pct', 0, 100)]:\n"
       "    metrics = metrics.loc[~((metrics[col] < lo) | (metrics[col] > hi))].copy()\n"
       "    metrics[col] = metrics[col].fillna(metrics[col].median())\n"
       "# runs: drop duraciones imposibles\n"
       "runs = runs.loc[~((runs['duration_sec'] < 0) | (runs['duration_sec'] > 86400))].copy()\n"
       "# tickets: drop errores tecnicos y rellenar priority/team NaN\n"
       "tickets = tickets.loc[~((tickets['resolution_min'] <= 0) | (tickets['resolution_min'] > 100_000))].copy()\n"
       "tickets['priority'] = tickets['priority'].fillna(tickets['priority'].mode().iloc[0])\n"
       "tickets['team'] = tickets['team'].fillna(tickets['team'].mode().iloc[0])\n"
       "print('Listo: shapes ->', metrics.shape, runs.shape, tickets.shape)"),
    md("## 1) Disponibilidad y SLOs\n"
       "\n"
       "**Qué reportamos al director:** disponibilidad observada en el periodo + top 3 "
       "incidentes por clientes afectados + burn-rate medio."),
    py("avail = 1 - metrics['error_rate'].mean()\n"
       "burn_max = burn.groupby('incident_id')['burn_5x'].max().mean()\n"
       "print(f'Disponibilidad observada: {avail:.4%}')\n"
       "print(f'Burn-rate 5x medio en incidentes: {burn_max:.2f}x')\n"
       "fig, ax = plt.subplots(figsize=(10, 4))\n"
       "top3 = incidents.nlargest(3, 'customers_affected')[['service', 'customers_affected', 'mttr_min']]\n"
       "top3.set_index('service')['customers_affected'].plot(kind='bar', color='coral', ax=ax)\n"
       "ax.set_title('Top 3 incidentes por clientes afectados')\n"
       "ax.set_ylabel('clientes')\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab4_fig1_avail.png', dpi=110, bbox_inches='tight')\n"
       "plt.show()"),
    md("## 2) Automatización\n"
       "\n"
       "**Qué reportamos:** success rate global + job con peor MTTR en fallos."),
    py("auto_ok = (runs['status'] == 'success').mean()\n"
       "failed = runs[runs['status'].isin(['failed','timeout'])]\n"
       "worst_job = failed.groupby('job_name')['duration_sec'].median().sort_values(ascending=False).head(1)\n"
       "print(f'Success rate global: {auto_ok:.2%}')\n"
       "print(f'Job con peor MTTR:\\n{worst_job}\\n')\n"
       "fig, ax = plt.subplots(figsize=(10, 4))\n"
       "agg = runs.groupby('job_name').agg(\n"
       "    runs=('run_id', 'count'),\n"
       "    success=('status', lambda s: (s == 'success').mean()),\n"
       ")\n"
       "agg.plot(kind='bar', secondary_y='success', ax=ax)\n"
       "ax.set_title('Volumen vs tasa de éxito por job')\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab4_fig2_auto.png', dpi=110, bbox_inches='tight')\n"
       "plt.show()"),
    md("## 3) Demanda operativa\n"
       "\n"
       "**Qué reportamos:** tickets por día en promedio + equipo líder en breach + "
       "rollback rate."),
    py("tickets['date'] = tickets['created_at'].dt.date\n"
       "vol = tickets.groupby('date').size().mean()\n"
       "rollback_rate = tickets.loc[tickets['category']=='change', 'rollback'].mean()\n"
       "fig, ax = plt.subplots(figsize=(10, 4))\n"
       "tickets.groupby('team')['sla_breached'].mean().sort_values(ascending=False).plot(kind='bar', color='indianred', ax=ax)\n"
       "ax.set_ylabel('% breach SLA')\n"
       "ax.set_title('Breach SLA por equipo')\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab4_fig3_ops.png', dpi=110, bbox_inches='tight')\n"
       "plt.show()\n"
       "print(f'Tickets/día promedio: {vol:.1f}')\n"
       "print(f'Rollback rate (changes): {rollback_rate:.2%}')"),
    md("## 4) Recomendaciones (RICE simplificado)\n"
       "\n"
       "**Qué es RICE:** Reach × Impact / Effort. Prioriza donde el beneficio "
       "(alcance × impacto) supera el esfuerzo.\n\n"
       "**Por qué importa:** convierte hallazgos en acciones comparables."),
    py("# Cambia las 3 acciones según los hallazgos de tu dupla\n"
       "recos = pd.DataFrame([\n"
       "    {'accion': 'Reducir p95 de checkout-api', 'reach': 8, 'impact': 3, 'effort': 2},\n"
       "    {'accion': 'Automatizar retry de db_vacuum', 'reach': 6, 'impact': 2, 'effort': 1},\n"
       "    {'accion': 'Repriorizar P1 del equipo payments', 'reach': 5, 'impact': 3, 'effort': 1},\n"
       "])\n"
       "recos['rice'] = recos['reach'] * recos['impact'] / recos['effort']\n"
       "recos.sort_values('rice', ascending=False)"),
    md("## Headline — escribe 1 línea por sección\n"
       "\n"
       "**Regla:** 1 cifra grande + 1 responsable + 1 ventana de tiempo + 1 acción priorizada.\n\n"
       "**Ejemplo:**\n"
       "> \"Disponibilidad del 99.92 %; el servicio checkout-api explica el 60 % del "
       "error budget consumido en los últimos 30 días.\""),
])


def write(name: str, nb: dict) -> Path:
    p = NB_DIR / name
    p.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    return p


if __name__ == "__main__":
    files = [
        ("lab1_observabilidad.ipynb", LAB_1),
        ("lab2_automatizacion.ipynb", LAB_2),
        ("lab3_requerimientos.ipynb", LAB_3),
        ("lab4_ejecutivo.ipynb", LAB_4),
    ]
    for name, nb in files:
        p = write(name, nb)
        print(f"wrote {p}")