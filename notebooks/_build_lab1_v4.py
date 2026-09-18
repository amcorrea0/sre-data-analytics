"""Reescribe lab1_observabilidad con:
- Explicacion concreta de headroom (no asumir conocimiento)
- Heatmap arreglado (cada servicio ocupa su celda)
- Decisiones explicitas despues de cada grafico
- Duraciones en ms (latencia) - mantiene porque son milisegundos, no horas
"""
from pathlib import Path
import json
import sys

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
       "5 figuras + 1 tabla con recomendacion de capacidad por servicio."),

    py("import pandas as pd\nimport numpy as np\nfrom pathlib import Path\n"
       "import matplotlib.pyplot as plt\nimport seaborn as sns\n"
       "sns.set_theme(style='whitegrid', palette='muted')\n"
       "plt.rcParams['figure.figsize'] = (12, 5)\n\n"
       "DATA = Path('..') / 'data'\n"
       "metrics = pd.read_csv(DATA / 'metrics_timeseries.csv', parse_dates=['ts'])\n"
       "incidents = pd.read_csv(DATA / 'incidents.csv', parse_dates=['opened_at', 'resolved_at'])\n"
       "burn = pd.read_csv(DATA / 'slo_burn.csv', parse_dates=['ts'])\n"
       "print(f'Metricas: {len(metrics):,} filas, {metrics[\"service\"].nunique()} servicios')\n"
       "print(f'Incidentes: {len(incidents)}')\n"
       "print('Servicios:', metrics['service'].unique())"),

    md("## 1. Diagnostico de la calidad de los datos\n\n"
       "**Que buscamos:** ¿hay NaN o valores fisicamente imposibles que "
       "distorsionen nuestras conclusiones?\n\n"
       "**Por que importa:** si hay `latency_ms = -50` en el dataset, cualquier "
       "grafico de distribucion arrastra la media hacia abajo. El director "
       "recibe un numero falso y compra capacidad que no necesita."),

    py("fig, ax = plt.subplots(figsize=(12, 4))\n"
       "sns.heatmap(metrics.isnull(), cbar=False, yticklabels=False, cmap='viridis')\n"
       "ax.set_title('Mapa de NaN - cada columna amarilla es dato faltante')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab1_fig1_nan.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 2. Limpieza: que hacemos con NaN y errores\n\n"
       "**Reglas que aplicamos** (explicitas para nuevos SREs):\n"
       "- **`latency_ms < 0`**: error del exporter (reloj desincronizado) → **borrar**\n"
       "- **`latency_ms > 10 000`** (10s): bug o exporter colgado → **borrar**\n"
       "- **`cpu_pct > 100`**: imposible, CPU > 100% → **borrar**\n"
       "- **NaN en numericas**: imputar con la **mediana** del servicio (es robusta a outliers)."),

    py("def clean_numeric(df, col, lo, hi):\n"
       "    bad = (df[col] < lo) | (df[col] > hi)\n"
       "    print(f'{col}: {bad.sum()} valores imposibles')\n"
       "    df = df.loc[~bad].copy()\n"
       "    df[col] = df[col].fillna(df[col].median())\n"
       "    return df\n\n"
       "metrics_clean = clean_numeric(metrics, 'latency_ms', 0, 10_000)\n"
       "metrics_clean = clean_numeric(metrics_clean, 'cpu_pct', 0, 100)\n"
       "print(f'\\nShape limpio: {metrics_clean.shape}')"),

    md("## 3. Personalidad de cada servicio - ¿consumen distinto?\n\n"
       "**Que miramos:** agregamos CPU, latencia, memoria y error_rate por servicio "
       "con dos metricas clave:\n"
       "- **Media**: lo que consume **en promedio**\n"
       "- **p95**: lo que consume en el **peor 5% de los minutos**\n\n"
       "**Por que importa p95?** Porque las nubes cobran por picos, no por promedio. "
       "Si tu promedio es 30% pero tu p95 es 85%, necesitas capacidad para 85%, "
       "no para 30%.\n\n"
       "**Que es 'headroom'?** Es la **distancia hasta el 100%**. "
       "Si headroom = 15%, significa que el 5% del tiempo tu servicio esta "
       "al 85% de CPU (100% - 15%). Si headroom = 30%, tienes margen para crecer."),

    py("agg = metrics_clean.groupby('service').agg(\n"
       "    cpu_mean=('cpu_pct', 'mean'),\n"
       "    cpu_p95=('cpu_pct', lambda s: s.quantile(0.95)),\n"
       "    mem_mean=('mem_pct', 'mean'),\n"
       "    lat_p95=('latency_ms', lambda s: s.quantile(0.95)),\n"
       "    err_mean=('error_rate', 'mean'),\n"
       ").round(2)\nagg['cpu_headroom'] = (100 - agg['cpu_p95']).round(1)\nagg"),

    md("## 4. Decision visual - ¿quien necesita capacidad ya?\n\n"
       "**Reglas para leer este grafico**:\n"
       "- Barra **roja** (CPU p95): si supera 80%, el servicio **roza la saturacion**\n"
       "- Linea naranja: umbral critico (80%)\n"
       "- Si la barra de **latencia** (gris) esta alta junto con CPU alto = "
       "**señal de saturacion real** (los requests se quedan esperando CPU)\n"
       "- Si CPU es alto pero latencia es baja = probablemente **puede escalar** sin urgencia"),

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

    md("## 5. Heatmap dia x hora x servicio - ¿cuando hay alertas?\n\n"
       "**Que vemos:** el percentil 95 de CPU por servicio, por dia de la semana "
       "(eje Y) y hora del dia (eje X). Las celdas mas oscuras = mas CPU en el peor caso.\n\n"
       "**Para que sirve:**\n"
       "- Si un servicio tiene **picos claros lunes 9-11am** = oportunidad de "
       "auto-scaling programado (configura 2x capacidad solo en esa franja).\n"
       "- Si los picos son **uniformes** = necesitas capacidad constante (compra ya).\n"
       "- Si los fines de semana son **bajos** = oportunidad de apagarlo (ahorra dinero).\n\n"
       "**Por que p95 y no media:** la media esconde los picos. El p95 te dice el "
       "peor caso realista del 5% de los minutos."),

    py("metrics_clean['dow'] = metrics_clean['ts'].dt.day_name()\n"
       "metrics_clean['hour'] = metrics_clean['ts'].dt.hour\n"
       "dow_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']\n"
       "metrics_clean['dow'] = pd.Categorical(metrics_clean['dow'], categories=dow_order, ordered=True)\n\n"
       "# Heatmap en grilla 1 fila x 5 columnas (uno por servicio)\n"
       "fig, axes = plt.subplots(1, 5, figsize=(22, 5), sharey=True, sharex=True)\n"
       "services_sorted = metrics_clean['service'].value_counts().index.tolist()\n"
       "for ax, svc in zip(axes, services_sorted):\n"
       "    sub = metrics_clean[metrics_clean['service'] == svc]\n"
       "    pivot = sub.pivot_table(index='dow', columns='hour', values='cpu_pct', aggfunc=lambda s: s.quantile(0.95))\n"
       "    sns.heatmap(pivot, ax=ax, cmap='YlOrRd', vmin=0, vmax=100,\n"
       "                cbar=(svc == services_sorted[-1]),\n"
       "                cbar_kws={'label': 'CPU p95 (%)'} if svc == services_sorted[-1] else None)\n"
       "    ax.set_title(svc, fontsize=12, fontweight='bold')\n"
       "    ax.set_xlabel('Hora del dia')\n"
       "    ax.set_ylabel('Dia de la semana' if svc == services_sorted[0] else '')\n"
       "fig.suptitle('CPU p95 por dia x hora - cada panel es un servicio', fontsize=14, y=1.02)\n"
       "plt.tight_layout()\n"
       "plt.savefig('../html/lab1_fig3_heatmap_alerts.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 6. Boxplot por servicio - los outliers reales\n\n"
       "**Que es un boxplot?** Resume una distribucion en 5 numeros clave:\n"
       "- **Caja (Q1-Q3)**: el 50% tipico de tus runs\n"
       "- **Rayita central**: la mediana\n"
       "- **Bigotes**: rango normal (1.5x IQR)\n"
       "- **Puntos arriba**: outliers = runs anormales\n\n"
       "**Por que escala log en este caso?** La latencia varia de 60 ms "
       "(notifications) a 600+ ms (search-api). En escala lineal, los pequeños "
       "se aplastan contra cero y no ves nada. La escala log te deja comparar extremos.\n\n"
       "**Que decision tomamos?** Si los outliers arriba del bigote son picos "
       "recurrentes = incidente real (investigar). Si estan en ambos lados = bug."),

    py("fig, ax = plt.subplots(figsize=(12, 5))\n"
       "order = metrics_clean.groupby('service')['latency_ms'].median().sort_values().index\n"
       "sns.boxplot(data=metrics_clean, x='service', y='latency_ms', order=order, hue='service', legend=False, ax=ax)\n"
       "ax.set_yscale('log')\n"
       "ax.set_title('Latencia por servicio (eje log) - outliers arriba son incidentes')\n"
       "ax.set_ylabel('Latencia (ms, escala log)')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab1_fig4_boxplot.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 7. Tu decision como SRE\n\n"
       "Mirando los datos de la tabla de la seccion 3:\n\n"
       "1. **Compra de capacidad**: el servicio con **headroom < 15%** y **lat_p95 alta** "
       "esta saturado - compra 2 nodos ahora (30% descuento reserva anual).\n"
       "2. **Auto-scaling**: el servicio con **picos claros en horas especificas** "
       "(mira el heatmap de la seccion 5) - configura regla auto-scaling.\n"
       "3. **Bajar tier**: el servicio con **headroom > 40%** y **lat_p95 baja** "
       "- muevelo al plan basico del proveedor cloud.\n\n"
       "**Argumenta con datos, no con intuicion.** Muestra tu tabla y tu heatmap al facilitador."),

    md("## 8. Para presentar al director\n\n"
       "Tu headline ejecutiva (1 linea):\n\n"
       "> «El servicio **[NOMBRE]** tiene CPU p95 del **X%** con headroom del "
       "**Y%**; compramos 2 nodos con 30% de descuento = **$Z** ahorrados al año.»\n\n"
       "Usa los numeros de la tabla de la seccion 3."),
])

(NB_DIR / "lab1_observabilidad.ipynb").write_text(json.dumps(LAB_1, indent=1), encoding="utf-8")
print("wrote lab1 v4")