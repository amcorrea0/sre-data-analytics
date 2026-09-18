"""Reescribe lab2_automatizacion con:
- Columnas adicionales de duracion en minutos y horas
- Explicar que son 'datos imposibles' con ejemplos concretos
- Explicar que es un boxplot, que son outliers, como interpretarlos
- Tablas con respuestas concretas en la seccion 'Tu decision como SRE'
- Quitar el grafico 'runs por hora' que no aporta (lo movemos a la seccion 3)
"""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent))
from _build_chunk1 import cell, md, py, notebook, NB_DIR


LAB_2 = notebook([
    md("# Lab 2 - Automatizacion: cada job cuenta su historia\n\n"
       "**Modalidad:** guiado - **Duracion:** ~12 min\n"
       "**Dataset:** automation_runs.csv (~1500 ejecuciones de 8 jobs)\n\n"
       "## El caso de negocio\n\n"
       "El equipo DevOps ejecuta 8 jobs automatizados al dia (restart_pod, "
       "db_vacuum, scale_deployment, etc.). El director pregunta:\n\n"
       "> «¿Cuanto tiempo perdemos al año por jobs que fallan o se demoran? "
       "¿Cual deberiamos reescribir primero?»\n\n"
       "## Entregable\n"
       "Tabla por job con runs, success_rate, retries, MTTR, "
       "horas-hombre perdidas y decision (mantener, optimizar, reescribir)."),

    md("## 1. Carga y limpieza - entendiendo los datos imposibles\n\n"
       "**Antes de tocar nada**, entendamos los datos. Un job se ve asi:\n\n"
       "| campo          | ejemplo       | que significa                          |\n"
       "|----------------|---------------|---------------------------------------|\n"
       "| `run_id`       | R-00123       | ID unico de la ejecucion              |\n"
       "| `job_name`     | restart_pod   | que job automatizado se ejecuto       |\n"
       "| `started_at`   | 2026-08-15 03 | cuando empezo                         |\n"
       "| `duration_sec` | 12            | cuanto duro en **segundos**            |\n"
       "| `status`       | success       | success, failed o timeout             |\n"
       "| `retries`      | 0             | cuantos reintentos tuvo                |\n\n"
       "**Que es un 'dato imposible'?** El exporter puede corromperse y reportar:\n"
       "- `duration_sec = -1` o `-10` (negativo): el reloj del exporter se desincronizo\n"
       "- `duration_sec = 86401` (> 24 horas): bug del exporter o el job quedo colgado dias\n\n"
       "**Que hacemos con ellos?** Los **borramos** (no los imputamos). Si "
       "imputamos con la mediana, contaminamos el MTTR real."),

    py("import pandas as pd\nimport numpy as np\nfrom pathlib import Path\n"
       "import matplotlib.pyplot as plt\nimport seaborn as sns\n"
       "sns.set_theme(style='whitegrid', palette='muted')\n"
       "plt.rcParams['figure.figsize'] = (12, 5)\n\n"
       "DATA = Path('..') / 'data'\n"
       "runs = pd.read_csv(DATA / 'automation_runs.csv', parse_dates=['started_at'])\n"
       "# Crear columnas en minutos y horas para que el humano no lea segundos\n"
       "runs['duration_min'] = runs['duration_sec'] / 60\n"
       "runs['duration_h'] = runs['duration_sec'] / 3600\n"
       "print('Ejemplo de una ejecucion normal:')\n"
       "print(runs[['job_name', 'duration_sec', 'duration_min', 'duration_h', 'status']].head(3))\n"
       "print(f'\\nTotal runs: {len(runs)}')\n"
       "print(f'Servicios unicos: {runs[\"job_name\"].nunique()}')"),

    md("## 2. Mapa de NaN + duraciones imposibles\n\n"
       "Antes de cualquier analisis, identificamos:\n"
       "- **NaN** en `duration_sec` o `job_name`\n"
       "- **Duraciones imposibles**: negativas o > 24 horas\n\n"
       "**Regla**: borrar las imposibles, imputar los NaN con la mediana **del job** "
       "(no la global) - porque cada job tiene su escala."),

    py("# Detectar NaN\n"
       "fig, ax = plt.subplots(figsize=(12, 3))\n"
       "sns.heatmap(runs.isnull(), cbar=False, yticklabels=False, cmap='viridis', ax=ax)\n"
       "ax.set_title('Mapa de NaN (amarillo = faltante). Se ve poco - ~0.5%')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab2_fig1_nan.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    py("# Detectar y mostrar duraciones imposibles\n"
       "impossible = (runs['duration_sec'] < 0) | (runs['duration_sec'] > 86400)\n"
       "print(f'Duraciones imposibles: {impossible.sum()} de {len(runs)}')\n"
       "print('Ejemplos de datos imposibles (los borraremos):')\n"
       "print(runs[impossible][['run_id','job_name','duration_sec','status']].head())\n\n"
       "# Limpiar\n"
       "runs = runs.loc[~impossible].copy()\n"
       "med_by_job = runs.groupby('job_name')['duration_sec'].transform('median')\n"
       "runs['duration_sec'] = runs['duration_sec'].fillna(med_by_job)\n"
       "runs['job_name'] = runs['job_name'].fillna(runs['job_name'].mode().iloc[0])\n"
       "# Regenerar columnas humanas\n"
       "runs['duration_min'] = runs['duration_sec'] / 60\n"
       "runs['duration_h'] = runs['duration_sec'] / 3600\n"
       "print(f'\\nDespues de limpieza: {len(runs)} runs validos')"),

    md("## 3. Distribucion horaria - cuando corren los jobs?\n\n"
       "Antes de mirar rendimiento, veamos el ritmo. Esto te dice si tienes "
       "picos de carga (batch nocturno) o distribucion uniforme."),

    py("runs['hour'] = runs['started_at'].dt.hour\n"
       "fig, ax = plt.subplots(figsize=(12, 4))\n"
       "runs.groupby('hour').size().plot(kind='bar', color='slategray', ax=ax)\n"
       "ax.set_title('Runs por hora del dia - picos nocturnos = batch')\n"
       "ax.set_xlabel('Hora del dia')\nax.set_ylabel('# runs')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab2_fig2_hourly.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 4. Boxplot por job - entendiendo los outliers\n\n"
       "**Por que usamos boxplot?** Resume una distribucion en 5 numeros clave:\n"
       "- **Min / Max** (los bigotes): lo normal, sin outliers\n"
       "- **Caja (Q1-Q3)**: el 50% tipico de tus runs\n"
       "- **Rayita central**: la mediana\n"
       "- **Puntos arriba del bigote**: outliers = runs anormales (lentos)\n\n"
       "**Por que escala log?** Hay jobs de 3 segundos (purge_cache) y de 30 minutos "
       "(db_vacuum). En escala lineal, los pequeños se aplastan contra cero y "
       "no ves nada. La escala log te deja comparar extremos sin perder detalle.\n\n"
       "**Que decision tomamos?** Si los outliers arriba son picos recurrentes = "
       "incidente real (investigar). Si son anomalías raras = bug del exporter "
       "(filtrar). En este lab los outliers son jobs lentos legítimos (5% del "
       "data artificialmente pesado)."),

    py("fig, ax = plt.subplots(figsize=(12, 5))\n"
       "order = runs.groupby('job_name')['duration_min'].median().sort_values().index\n"
       "sns.boxplot(data=runs, x='job_name', y='duration_min', order=order, hue='job_name', legend=False, ax=ax)\n"
       "ax.set_yscale('log')\n"
       "ax.set_title('Duracion por job (minutos, log) - outliers arriba son jobs lentos')\n"
       "ax.set_ylabel('Duracion (min, escala log)')\n"
       "plt.xticks(rotation=30, ha='right')\nplt.tight_layout()\n"
       "plt.savefig('../html/lab2_fig3_boxplot.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 5. Tabla por job - horas-hombre perdidas y decision\n\n"
       "**Como se calcula el costo humano**:\n"
       "1. `failure_rate` = proporcion de runs que fallan\n"
       "2. `failures_per_year` = failure_rate * runs_dia * 365\n"
       "3. `hours_lost_per_year` = failures_per_year * MTTR_seg / 3600\n\n"
       "**Tu recomendacion**:\n"
       "- **Alta falla + alto MTTR** = reescribir (causa dolores repetidos y largos)\n"
       "- **Alta falla + bajo MTTR** = optimizar script (falla rapido, posiblemente "
       "logica mal)\n"
       "- **Baja falla + alto MTTR** = reescribir solo cuando falla (es lento al fallar)\n"
       "- **Baja falla + bajo MTTR** = mantener (esta bien)"),

    py("by_job = runs.groupby('job_name').agg(\n"
       "    runs=('run_id', 'count'),\n"
       "    success_rate=('status', lambda s: (s == 'success').mean()),\n"
       "    avg_retries=('retries', 'mean'),\n"
       "    p50_dur_min=('duration_min', lambda s: s.quantile(0.5)),\n"
       "    p95_dur_min=('duration_min', lambda s: s.quantile(0.95)),\n"
       "    failure_rate=('status', lambda s: (s != 'success').mean()),\n"
       ")\n"
       "failed = runs[runs['status'].isin(['failed', 'timeout'])]\n"
       "by_job['mttr_min'] = failed.groupby('job_name')['duration_min'].median()\n"
       "by_job = by_job.fillna(0).round(3)\n"
       "# Estimaciones anuales (asumimos ~30 dias de datos)\n"
       "by_job['failures_per_year'] = (by_job['failure_rate'] * by_job['runs'] * 365 / 30).round(0)\n"
       "by_job['hours_lost_per_year'] = (by_job['failures_per_year'] * by_job['mttr_min'] / 60).round(1)\n"
       "# Decision sugerida\n"
       "def suggestion(r):\n"
       "    if r['failure_rate'] >= 0.10 and r['mttr_min'] >= 5:\n"
       "        return 'REESCRIBIR'\n"
       "    if r['failure_rate'] >= 0.07 and r['mttr_min'] < 5:\n"
       "        return 'OPTIMIZAR'\n"
       "    if r['failure_rate'] < 0.07 and r['mttr_min'] >= 5:\n"
       "        return 'REESCRIBIR SI FALLA'\n"
       "    return 'MANTENER'\n"
       "by_job['decision'] = by_job.apply(suggestion, axis=1)\n"
       "by_job.sort_values('hours_lost_per_year', ascending=False)"),

    md("## 6. Visualizacion - que job duele mas al equipo\n\n"
       "Las barras **rojas** son los jobs prioritarios para reescribir "
       "(>5 horas-hombre perdidas al año)."),

    py("fig, ax = plt.subplots(figsize=(12, 5))\n"
       "top_loss = by_job.sort_values('hours_lost_per_year', ascending=True)\n"
       "colors = ['#b30015' if x > 5 else '#5a5a5a' for x in top_loss['hours_lost_per_year']]\n"
       "top_loss['hours_lost_per_year'].plot(kind='barh', color=colors, ax=ax)\n"
       "ax.set_xlabel('Horas-hombre perdidas estimadas por año')\n"
       "ax.set_title('Que job reescribimos primero? (top barras rojas = prioridad)')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab2_fig4_hours_lost.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 7. Cuadrante MTTR vs tasa de fallo - decision visual\n\n"
       "Mirando el scatter: el cuadrante **superior-izquierdo** (baja falla + alto "
       "MTTR) es el **peor**: falla poco pero cuando falla, tarda mucho. Eso es un job "
       "mal diseñado. El cuadrante **inferior-derecho** (alta falla + bajo MTTR) "
       "falla mucho pero rapido: posiblemente script con logica mala que tira excepcion."),

    py("fig, ax = plt.subplots(figsize=(10, 6))\n"
       "for _, row in by_job.iterrows():\n"
       "    ax.scatter(row['failure_rate'] * 100, row['mttr_min'], s=row['runs']/5, alpha=0.6, color='#b30015')\n"
       "    ax.annotate(row.name, (row['failure_rate'] * 100, row['mttr_min']),\n"
       "                xytext=(5, 5), textcoords='offset points', fontsize=9)\n"
       "ax.axhline(y=by_job['mttr_min'].median(), color='grey', linestyle='--', alpha=0.5)\n"
       "ax.axvline(x=by_job['failure_rate'].median() * 100, color='grey', linestyle='--', alpha=0.5)\n"
       "ax.set_xlabel('Tasa de fallo (%)')\n"
       "ax.set_ylabel('MTTR (minutos)')\n"
       "ax.set_title('Jobs en cuadrantes - superior izq = reescribir, inferior der = ok')\n"
       "ax.text(0.5, 0.95, 'Reescribir urgente\\n(falla poco, pero tarda mucho)',\n"
       "        transform=ax.transAxes, ha='center', color='#b30015', fontweight='bold')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab2_fig5_quadrant.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 8. Tu decision como SRE\n\n"
       "Con los datos de la tabla anterior:\n\n"
       "- **#1 candidato a reescribir**: el job con la **mayor `hours_lost_per_year`** y "
       "decision sugerida **REESCRIBIR**. Reescribirlo elimina el mayor dolor humano.\n"
       "- **#1 candidato a optimizar**: el job con `failure_rate >= 7%` y `decision = OPTIMIZAR`. "
       "Suele ser un script con logica fragil.\n"
       "- **#1 candidato a dar de baja**: el job con menos `runs` y `failure_rate = 0`. "
       "Si nadie lo corre, se puede eliminar.\n\n"
       "Muestra tu tabla al facilitador y argumenta tu eleccion con estos 3 numeros.\n\n"
       "---\n\n"
       "**Frase ejecutiva para tu reporte** (1 linea):\n"
       "> «Reescribir [JOB] ahorra ~X horas/año a [EQUIPO]; el script se reescribe "
       "en ~Y sprints; dejamos de gastar Z retries/semana.»"),
])

(NB_DIR / "lab2_automatizacion.ipynb").write_text(json.dumps(LAB_2, indent=1), encoding="utf-8")
print("wrote lab2 v4")