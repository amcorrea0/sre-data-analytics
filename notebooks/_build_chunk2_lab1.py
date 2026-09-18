"""Chunk 2: lab1 - Observabilidad con caso de negocio y heatmap dia x hora."""
from pathlib import Path
import json
import sys

# Importar helpers del chunk 1
sys.path.insert(0, str(Path(__file__).parent))
from _build_chunk1 import cell, md, py, notebook, NB_DIR


LAB_1 = notebook([
    md("# Lab 1 - Observabilidad: ETL + outliers + alertas\n\n"
       "**Modalidad:** guiado - **Duracion:** ~12 min\n"
       "**Datasets:** metrics_timeseries.csv, incidents.csv, slo_burn.csv\n\n"
       "## El caso de negocio\n\n"
       "Somos SREs de una plataforma de pagos. El director nos pregunta:\n\n"
       "> «Nuestros proveedores cloud nos ofrecen reservar capacidad por 1 año con "
       "30% de descuento. ¿Cual servicio necesita mas capacidad ya, y cual podria "
       "moverse a otro mas barato?»\n\n"
       "Para responder necesitamos ver: (1) cual servicio consume **mas CPU** "
       "consistentemente, (2) cual tiene **picos recurrentes** en horarios "
       "especificos, (3) cual esta **saturado** permanentemente.\n\n"
       "## Entregable\n"
       "4 figuras + 1 tabla con recomendacion de capacidad por servicio."),

    py("import pandas as pd\nimport numpy as np\nfrom pathlib import Path\n"
       "import matplotlib.pyplot as plt\nimport seaborn as sns\n"
       "sns.set_theme(style='whitegrid', palette='muted')\n"
       "plt.rcParams['figure.figsize'] = (12, 5)\n\n"
       "DATA = Path('..') / 'data'\n"
       "metrics = pd.read_csv(DATA / 'metrics_timeseries.csv', parse_dates=['ts'])\n"
       "incidents = pd.read_csv(DATA / 'incidents.csv', parse_dates=['opened_at', 'resolved_at'])\n"
       "burn = pd.read_csv(DATA / 'slo_burn.csv', parse_dates=['ts'])\n"
       "metrics.shape, incidents.shape, burn.shape"),

    md("## 1. Diagnostico de la calidad de los datos\n\n"
       "**Que buscamos:** ¿hay NaN o valores fisicamente imposibles que "
       "distorsionen nuestras conclusiones?\n\n"
       "**Por que importa:** si hay latency_ms = -50 en el dataset, cualquier "
       "grafico de distribucion arrastra la media hacia abajo. El director "
       "recibe un numero falso y compra capacidad que no necesita."),

    py("fig, ax = plt.subplots(figsize=(12, 4))\n"
       "sns.heatmap(metrics.isnull(), cbar=False, yticklabels=False, cmap='viridis')\n"
       "ax.set_title('Mapa de NaN - cada columna amarilla es dato faltante')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab1_fig1_nan.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    py("def clean_numeric(df, col, lo, hi):\n"
       "    bad = (df[col] < lo) | (df[col] > hi)\n"
       "    print(f'{col}: {bad.sum()} valores imposibles')\n"
       "    df = df.loc[~bad].copy()\n"
       "    df[col] = df[col].fillna(df[col].median())\n"
       "    return df\n\n"
       "metrics_clean = clean_numeric(metrics, 'latency_ms', 0, 10_000)\n"
       "metrics_clean = clean_numeric(metrics_clean, 'cpu_pct', 0, 100)\n"
       "print('shape limpio:', metrics_clean.shape)"),

    md("## 2. Personalidad de cada servicio - ¿consumen distinto?\n\n"
       "**Que decidimos con este grafico:** que servicio tiene la media mas alta "
       "(candidato a compra de capacidad) y cual es estable (candidato a reducir).\n\n"
       "**Cuando NO usar:** si los servicios tienen escalas radicalmente distintas, "
       "mejor normalizar a p95 o % de su propio baseline."),

    py("agg = metrics_clean.groupby('service').agg(\n"
       "    cpu_mean=('cpu_pct', 'mean'),\n"
       "    cpu_p95=('cpu_pct', lambda s: s.quantile(0.95)),\n"
       "    mem_mean=('mem_pct', 'mean'),\n"
       "    lat_p95=('latency_ms', lambda s: s.quantile(0.95)),\n"
       "    err_mean=('error_rate', 'mean'),\n"
       ").round(2)\nagg['cpu_headroom'] = (100 - agg['cpu_p95']).round(1)\nagg"),

    md("## 3. Decision visual - ¿quien necesita capacidad ya?\n\n"
       "**Que decidimos:** si el headroom (margen hasta 100%) es bajo y la "
       "latencia p95 es alta, hay que comprar capacidad. Si todo es bajo, podemos "
       "bajar el tier."),

    py("fig, ax = plt.subplots(figsize=(12, 5))\n"
       "services = agg.index.tolist()\nx = np.arange(len(services))\nwidth = 0.35\n"
       "ax.bar(x - width/2, agg['cpu_p95'], width, label='CPU p95 (%)', color='#b30015')\n"
       "ax.bar(x + width/2, agg['lat_p95'], width, label='Latencia p95 (ms)', color='#3a3a3a')\n"
       "ax.axhline(y=80, color='orange', linestyle='--', label='Umbral CPU critico (80%)')\n"
       "ax.set_xticks(x)\nax.set_xticklabels(services, rotation=20, ha='right')\n"
       "ax.set_ylabel('CPU p95 (%)  /  Latencia p95 (ms)')\n"
       "ax.set_title('¿Quien necesita capacidad ya? CPU p95 + latencia p95 por servicio')\n"
       "ax.legend(loc='upper left')\nplt.tight_layout()\n"
       "plt.savefig('../html/lab1_fig2_capacity.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 4. Heatmap dia x hora x servicio - ¿cuando hay alertas?\n\n"
       "**Que decidimos:** si hay un patron claro (ej: picos lunes 9-11am), "
       "podemos anticipar la capacidad con auto-scaling programado.\n\n"
       "**Por que la escala es percentil 95:** porque la media esconde los picos. "
       "El p95 nos dice cual es el peor caso realista."),

    py("metrics_clean['dow'] = metrics_clean['ts'].dt.day_name()\n"
       "metrics_clean['hour'] = metrics_clean['ts'].dt.hour\n"
       "dow_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']\n"
       "metrics_clean['dow'] = pd.Categorical(metrics_clean['dow'], categories=dow_order, ordered=True)\n\n"
       "fig, axes = plt.subplots(2, 3, figsize=(18, 9), sharey=True, sharex=True)\n"
       "services_sorted = metrics_clean['service'].value_counts().index.tolist()\n"
       "for ax, svc in zip(axes.flatten(), services_sorted):\n"
       "    sub = metrics_clean[metrics_clean['service'] == svc]\n"
       "    pivot = sub.pivot_table(index='dow', columns='hour', values='cpu_pct', aggfunc=lambda s: s.quantile(0.95))\n"
       "    sns.heatmap(pivot, ax=ax, cmap='YlOrRd', vmin=0, vmax=100, cbar=(svc == services_sorted[-1]))\n"
       "    ax.set_title(svc, fontsize=11)\n"
       "    ax.set_xlabel('')\n"
       "    ax.set_ylabel('')\n"
       "    if svc != services_sorted[0]:\n"
       "        ax.set_yticklabels([])\n"
       "fig.suptitle('CPU p95 por dia x hora - cada panel es un servicio', fontsize=14, y=1.02)\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab1_fig3_heatmap_alerts.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 5. Boxplot por servicio en escala log - los outliers reales\n\n"
       "**Que decidimos:** el boxplot muestra la distribucion natural + outliers. "
       "Si los outliers son picos arriba del bigote = incidente. Si estan en ambos "
       "lados = bug del exporter.\n\n"
       "**Por que escala log:** la mediana de purge_cache es 2 s y la de "
       "db_vacuum 120 s; sin log, los pequenos desaparecen."),

    py("fig, ax = plt.subplots(figsize=(12, 5))\n"
       "order = metrics_clean.groupby('service')['latency_ms'].median().sort_values().index\n"
       "sns.boxplot(data=metrics_clean, x='service', y='latency_ms', order=order, hue='service', legend=False, ax=ax)\n"
       "ax.set_yscale('log')\n"
       "ax.set_title('Latencia por servicio (eje log) - outliers arriba son incidentes')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab1_fig4_boxplot.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 6. Tu decision como SRE\n\n"
       "Mirando los datos:\n"
       "1. ¿Que servicio tiene el CPU p95 mas alto? (candidato a compra de capacidad)\n"
       "2. ¿Que servicio muestra picos claros lunes-viernes 9-11am? (candidato a auto-scaling)\n"
       "3. ¿Cual podrias bajar de tier por su consumo bajo estable?\n\n"
       "**Argumenta con datos, no con intuicion.**"),
])

(NB_DIR / "lab1_observabilidad.ipynb").write_text(json.dumps(LAB_1, indent=1), encoding="utf-8")
print("wrote lab1")