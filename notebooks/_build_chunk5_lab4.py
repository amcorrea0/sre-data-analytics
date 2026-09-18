"""Chunk 5: lab4 - Dashboard ejecutivo."""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent))
from _build_chunk1 import cell, md, py, notebook, NB_DIR


LAB_4 = notebook([
    md("# Lab 4 - Dashboard ejecutivo: lo que cuenta la historia\n\n"
       "**Modalidad:** hands-on - **Duracion:** ~12 min\n\n"
       "## El caso de negocio\n\n"
       "El CFO nos pide en una sola pagina:\n\n"
       "> «¿Compramos capacidad o la reducimos? ¿Reescribimos jobs? "
       "¿Reforzamos equipos? ¿Cuanto nos cuesta la indisponibilidad?»\n\n"
       "Esta pagina es la respuesta. 4 secciones, 1 cifra cada una."),

    md("## 0. Carga + limpieza minima del dashboard"),

    py("import pandas as pd\nimport numpy as np\nfrom pathlib import Path\n"
       "import matplotlib.pyplot as plt\nimport seaborn as sns\n"
       "sns.set_theme(style='whitegrid', palette='muted')\n"
       "plt.rcParams['figure.figsize'] = (12, 5)\n\n"
       "DATA = Path('..') / 'data'\n"
       "metrics = pd.read_csv(DATA / 'metrics_timeseries.csv', parse_dates=['ts'])\n"
       "incidents = pd.read_csv(DATA / 'incidents.csv', parse_dates=['opened_at', 'resolved_at'])\n"
       "runs = pd.read_csv(DATA / 'automation_runs.csv', parse_dates=['started_at'])\n"
       "tickets = pd.read_csv(DATA / 'tickets.csv', parse_dates=['created_at'])\n\n"
       "# Limpieza minima\n"
       "for col, lo, hi in [('latency_ms', 0, 10_000), ('cpu_pct', 0, 100)]:\n"
       "    metrics = metrics.loc[~((metrics[col] < lo) | (metrics[col] > hi))].copy()\n"
       "    metrics[col] = metrics[col].fillna(metrics[col].median())\n"
       "runs = runs.loc[~((runs['duration_sec'] < 0) | (runs['duration_sec'] > 86400))].copy()\n"
       "tickets = tickets.loc[~((tickets['resolution_min'] <= 0) | (tickets['resolution_min'] > 100_000))].copy()\n"
       "tickets['priority'] = tickets['priority'].fillna(tickets['priority'].mode().iloc[0])\n"
       "tickets['team'] = tickets['team'].fillna(tickets['team'].mode().iloc[0])"),

    md("## 1) Disponibilidad y SLOs\n\n"
       "**Que decidimos:** si la disponibilidad observada esta por debajo del SLO "
       "(99.9%), hay que invertir en confiabilidad. Si esta por encima, podemos "
       "mover presupuesto a feature work."),

    py("avail = 1 - metrics['error_rate'].mean()\n"
       "burn_data = pd.read_csv(DATA / 'slo_burn.csv', parse_dates=['ts'])\n"
       "burn_max = burn_data.groupby('incident_id')['burn_5x'].max().mean()\n"
       "print(f'Disponibilidad observada: {avail:.4%}')\n"
       "print(f'Burn-rate 5x medio: {burn_max:.2f}x')\nprint()\n"
       "fig, ax = plt.subplots(figsize=(12, 5))\n"
       "top3 = incidents.nlargest(3, 'customers_affected')[['service', 'customers_affected', 'mttr_min']]\n"
       "top3.set_index('service')['customers_affected'].plot(kind='bar', color='#b30015', ax=ax)\n"
       "ax.set_title('Top 3 incidentes por clientes afectados')\n"
       "ax.set_ylabel('Clientes')\nplt.tight_layout()\n"
       "plt.savefig('../html/lab4_fig1_avail.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 2) Automatizacion - reescribimos o esperamos?\n\n"
       "**Que decidimos:** si el success rate global esta bajo 95%, hay que "
       "reescribir jobs prioritarios. Si esta sobre 99%, podemos recortar personal."),

    py("auto_ok = (runs['status'] == 'success').mean()\n"
       "failed = runs[runs['status'].isin(['failed','timeout'])]\n"
       "mttr_per_job = failed.groupby('job_name')['duration_sec'].median()\n"
       "worst_job = mttr_per_job.sort_values(ascending=False).head(1)\n"
       "print(f'Success rate global: {auto_ok:.2%}')\n"
       "print(f'Job con peor MTTR:\\n{worst_job}\\n')\n\n"
       "fig, ax = plt.subplots(figsize=(12, 5))\n"
       "agg = runs.groupby('job_name').agg(\n"
       "    runs=('run_id', 'count'),\n"
       "    success_rate=('status', lambda s: (s == 'success').mean()),\n"
       ")\n"
       "colors = ['#b30015' if x < 0.9 else '#3a3a3a' for x in agg['success_rate']]\n"
       "agg.sort_values('success_rate').plot(kind='barh', y='success_rate', color=colors, ax=ax)\n"
       "ax.axvline(x=0.9, color='orange', linestyle='--', label='Umbral 90%')\n"
       "ax.set_xlabel('Success rate')\n"
       "ax.set_title('Success rate por job (rojo = debajo del umbral)')\n"
       "ax.legend()\nplt.tight_layout()\n"
       "plt.savefig('../html/lab4_fig2_auto.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 3) Demanda operativa - donde reforzamos?\n\n"
       "**Que decidimos:** si un equipo lidera el breach + la carga, hay que "
       "reforzar. Si lidera el rollback, hay que mejorar el proceso de cambios."),

    py("tickets['date'] = tickets['created_at'].dt.date\n"
       "vol = tickets.groupby('date').size().mean()\n"
       "rollback_rate = tickets.loc[tickets['category']=='change', 'rollback'].mean()\n"
       "print(f'Tickets/dia promedio: {vol:.1f}')\n"
       "print(f'Rollback rate (changes): {rollback_rate:.2%}')\n\n"
       "fig, ax = plt.subplots(figsize=(12, 5))\n"
       "tickets.groupby('team')['sla_breached'].mean().sort_values(ascending=False).plot(kind='bar', color='#b30015', ax=ax)\n"
       "ax.axhline(y=tickets['sla_breached'].mean(), color='grey', linestyle='--', label='Promedio global')\n"
       "ax.set_ylabel('% breach SLA')\n"
       "ax.set_title('Breach SLA por equipo (rojo = arriba del promedio)')\n"
       "ax.legend()\nplt.tight_layout()\n"
       "plt.savefig('../html/lab4_fig3_ops.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 4) Recomendacion RICE\n\n"
       "**Que decidimos:** priorizamos las acciones donde RICE = (Reach x Impact) / "
       "Effort es mayor."),

    py("recos = pd.DataFrame([\n"
       "    {'accion': 'Comprar capacidad para checkout-api', 'reach': 9, 'impact': 4, 'effort': 3},\n"
       "    {'accion': 'Reescribir job con peor MTTR', 'reach': 6, 'impact': 3, 'effort': 2},\n"
       "    {'accion': 'Reforzar equipo con mas breach', 'reach': 7, 'impact': 3, 'effort': 2},\n"
       "    {'accion': 'Implementar auto-scaling lunes 9-11am', 'reach': 8, 'impact': 2, 'effort': 1},\n"
       "])\nrecos['rice'] = recos['reach'] * recos['impact'] / recos['effort']\nrecos.sort_values('rice', ascending=False)"),

    md("## Headline ejecutiva - tu version final\n\n"
       "Redacta en una linea por seccion (cifra + responsable + ventana + accion). "
       "Esta es la frase que leeras al CFO."),
])

(NB_DIR / "lab4_ejecutivo.ipynb").write_text(json.dumps(LAB_4, indent=1), encoding="utf-8")
print("wrote lab4")