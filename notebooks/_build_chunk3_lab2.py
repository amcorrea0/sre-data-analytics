"""Chunk 3: lab2 - Automatizacion."""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent))
from _build_chunk1 import cell, md, py, notebook, NB_DIR


LAB_2 = notebook([
    md("# Lab 2 - Automatizacion: cada job cuenta su historia\n\n"
       "**Modalidad:** guiado - **Duracion:** ~12 min\n"
       "**Dataset:** automation_runs.csv\n\n"
       "## El caso de negocio\n\n"
       "El equipo DevOps nos pasa una lista de 8 jobs automatizados que se ejecutan "
       "a diario. El director pregunta:\n\n"
       "> «¿Cuanto tiempo perdemos al año por jobs que fallan o se demoran? "
       "¿Cual deberiamos reescribir primero?»\n\n"
       "## Entregable\n"
       "Tabla por job con: runs, success_rate, retries, MTTR, "
       "y decision asociada (mantener, optimizar, reescribir)."),

    py("import pandas as pd\nimport numpy as np\nfrom pathlib import Path\n"
       "import matplotlib.pyplot as plt\nimport seaborn as sns\n"
       "sns.set_theme(style='whitegrid', palette='muted')\n"
       "plt.rcParams['figure.figsize'] = (12, 5)\n\n"
       "DATA = Path('..') / 'data'\n"
       "runs = pd.read_csv(DATA / 'automation_runs.csv', parse_dates=['started_at'])\n"
       "runs.head()"),

    md("## 1. Limpieza - que datos faltantes / imposibles hay\n\n"
       "**Que decidimos:** si un job tiene duration_sec = -1, no es un job lento, "
       "es bug del exporter. Lo dropeamos antes de calcular MTTR."),

    py("fig, ax = plt.subplots(figsize=(12, 3))\n"
       "sns.heatmap(runs.isnull(), cbar=False, yticklabels=False, cmap='viridis', ax=ax)\n"
       "ax.set_title('Mapa de NaN - duracion_sec y job_name tienen huecos')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab2_fig1_nan.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    py("bad = (runs['duration_sec'] < 0) | (runs['duration_sec'] > 86400)\n"
       "print(f'duraciones imposibles: {bad.sum()}')\n"
       "runs = runs.loc[~bad].copy()\n"
       "med_by_job = runs.groupby('job_name')['duration_sec'].transform('median')\n"
       "runs['duration_sec'] = runs['duration_sec'].fillna(med_by_job)\n"
       "runs['job_name'] = runs['job_name'].fillna(runs['job_name'].mode().iloc[0])\n"
       "print('shape limpio:', runs.shape)"),

    md("## 2. Boxplot por job (log) - la distribucion natural\n\n"
       "**Que decidimos:** la mediana dice cual es el caso tipico; la caja dice "
       "el 50% comun; los puntos arriba del bigote son outliers reales (jobs lentos).\n\n"
       "**Por que log:** porque purge_cache corre en 2s y db_vacuum en 2min. "
       "Sin log, los pequenos se aplastan contra cero."),

    py("fig, ax = plt.subplots(figsize=(12, 5))\n"
       "order = runs.groupby('job_name')['duration_sec'].median().sort_values().index\n"
       "sns.boxplot(data=runs, x='job_name', y='duration_sec', order=order, hue='job_name', legend=False, ax=ax)\n"
       "ax.set_yscale('log')\n"
       "ax.set_title('Duracion por job (log) - outliers arriba = jobs lentos')\n"
       "plt.xticks(rotation=30, ha='right')\nplt.tight_layout()\n"
       "plt.savefig('../html/lab2_fig2_boxplot.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 3. ¿Cuanto tiempo del equipo se va en fallos?\n\n"
       "**Que decidimos:** el MTTR (mediana de duracion en fallos) multiplicado por "
       "numero de fallos al año = horas-hombre perdidas. Si supera X, reescribimos."),

    py("by_job = runs.groupby('job_name').agg(\n"
       "    runs=('run_id', 'count'),\n"
       "    success_rate=('status', lambda s: (s == 'success').mean()),\n"
       "    avg_retries=('retries', 'mean'),\n"
       "    p50_dur=('duration_sec', lambda s: s.quantile(0.5)),\n"
       "    p95_dur=('duration_sec', lambda s: s.quantile(0.95)),\n"
       "    failure_rate=('status', lambda s: (s != 'success').mean()),\n"
       ")\n"
       "failed = runs[runs['status'].isin(['failed', 'timeout'])]\n"
       "by_job['mttr_sec'] = failed.groupby('job_name')['duration_sec'].median()\n"
       "by_job = by_job.fillna(0).round(2)\nby_job.sort_values('success_rate')"),

    py("by_job['failures_per_year'] = (by_job['failure_rate'] * by_job['runs'] * 365 / 30).round(0)\n"
       "by_job['hours_lost_per_year'] = (by_job['failures_per_year'] * by_job['mttr_sec'] / 3600).round(1)\n"
       "by_job[['runs', 'success_rate', 'mttr_sec', 'failures_per_year', 'hours_lost_per_year']].sort_values('hours_lost_per_year', ascending=False)"),

    md("## 4. Visualizacion - que job duele mas al equipo\n\n"
       "**Que decidimos:** la barra de horas perdidas es nuestra recomendacion "
       "de prioridad para reescribir."),

    py("fig, ax = plt.subplots(figsize=(12, 5))\n"
       "top_loss = by_job.sort_values('hours_lost_per_year', ascending=True)\n"
       "colors = ['#b30015' if x > 5 else '#5a5a5a' for x in top_loss['hours_lost_per_year']]\n"
       "top_loss['hours_lost_per_year'].plot(kind='barh', color=colors, ax=ax)\n"
       "ax.set_xlabel('Horas-hombre perdidas estimadas por año')\n"
       "ax.set_title('Que job reescribimos primero? (top barras rojas = prioridad)')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab2_fig3_hours_lost.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 5. MTTR vs tasa de fallo - que reescribimos\n\n"
       "**Que decidimos:** un job con **baja tasa de fallo + alto MTTR** = reescribir "
       "(cuando falla, dura demasiado). **Alta tasa + bajo MTTR** = optimizar "
       "(falla mucho pero rapido, posiblemente script mal diseñado)."),

    py("fig, ax = plt.subplots(figsize=(10, 6))\n"
       "for _, row in by_job.iterrows():\n"
       "    ax.scatter(row['failure_rate'] * 100, row['mttr_sec'], s=row['runs']/5, alpha=0.6)\n"
       "    ax.annotate(row.name, (row['failure_rate'] * 100, row['mttr_sec']),\n"
       "                xytext=(5, 5), textcoords='offset points', fontsize=9)\n"
       "ax.axhline(y=by_job['mttr_sec'].median(), color='grey', linestyle='--', alpha=0.5)\n"
       "ax.axvline(x=by_job['failure_rate'].median() * 100, color='grey', linestyle='--', alpha=0.5)\n"
       "ax.set_xlabel('Tasa de fallo (%)')\n"
       "ax.set_ylabel('MTTR (segundos, escala log)')\n"
       "ax.set_yscale('log')\n"
       "ax.set_title('Jobs en cuadrantes - superior izq = reescribir, inferior der = ok')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab2_fig4_quadrant.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 6. Tu decision como SRE\n\n"
       "- ¿Cual job es el #1 candidato a reescribir? (alto MTTR + baja tasa de fallo)\n"
       "- ¿Cual job es el #1 candidato a optimizar? (alto fallo + bajo MTTR)\n"
       "- ¿Cual job podrias dar de baja por no usarse?"),

    py("runs['hour'] = runs['started_at'].dt.hour\n"
       "fig, ax = plt.subplots(figsize=(12, 4))\n"
       "runs.groupby('hour').size().plot(kind='bar', color='slategray', ax=ax)\n"
       "ax.set_title('Runs por hora del dia - picos nocturnos = batch')\n"
       "ax.set_xlabel('Hora del dia')\nax.set_ylabel('# runs')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab2_fig5_hourly.png', dpi=110, bbox_inches='tight')\nplt.show()"),
])

(NB_DIR / "lab2_automatizacion.ipynb").write_text(json.dumps(LAB_2, indent=1), encoding="utf-8")
print("wrote lab2")