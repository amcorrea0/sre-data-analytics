"""Reescribe lab3_requerimientos con:
- Columna de resolucion en horas (mejor lectura humana que minutos cuando son muchas)
- Heatmap dia x hora explicito correctamente
- Tablas con respuestas concretas
"""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent))
from _build_chunk1 import cell, md, py, notebook, NB_DIR


LAB_3 = notebook([
    md("# Lab 3 - Tickets y demanda operativa\n\n"
       "**Modalidad:** hands-on - **Duracion:** ~12 min (en parejas)\n"
       "**Dataset:** tickets.csv (~900 tickets del equipo)\n\n"
       "## El caso de negocio\n\n"
       "El equipo de ingenieria reporta que esta saturado. El director pregunta:\n\n"
       "> «¿Cual equipo necesita refuerzo de personal? ¿Donde estamos perdiendo "
       "dinero en SLA breached? ¿La carga es uniforme o tiene picos que podamos "
       "absorber con rotacion?»\n\n"
       "## Entregable\n"
       "Mapa de carga por equipo + heatmap temporal + ranking de breach + decision."),

    md("## 1. Carga + diagnostico\n\n"
       "**Que buscamos:** saber si hay NaN antes de calcular breach (cambian el resultado)."),

    py("import pandas as pd\nimport numpy as np\nfrom pathlib import Path\n"
       "import matplotlib.pyplot as plt\nimport seaborn as sns\n"
       "sns.set_theme(style='whitegrid', palette='muted')\n"
       "plt.rcParams['figure.figsize'] = (12, 5)\n\n"
       "DATA = Path('..') / 'data'\n"
       "tickets = pd.read_csv(DATA / 'tickets.csv', parse_dates=['created_at'])\n"
       "# Columna humana: resolucion en horas\n"
       "tickets['resolution_h'] = tickets['resolution_min'] / 60\n"
       "fig, ax = plt.subplots(figsize=(12, 3))\n"
       "sns.heatmap(tickets.isnull(), cbar=False, yticklabels=False, cmap='viridis', ax=ax)\n"
       "ax.set_title('NaN - priority y team tienen huecos')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab3_fig1_nan.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    py("# Limpiar errores tecnicos: resolution <= 0 o > 100 000 (mas de 2 meses)\n"
       "t = tickets[(tickets['resolution_min'] > 0) & (tickets['resolution_min'] < 100_000)].copy()\n"
       "t['priority'] = t['priority'].fillna(t['priority'].mode().iloc[0])\n"
       "t['team'] = t['team'].fillna(t['team'].mode().iloc[0])\n"
       "print(f'limpiados: {len(tickets) - len(t)} filas con errores tecnicos')\n"
       "print(f'Tickets validos: {len(t)}')\n"
       "print('\\nPor equipo:')\nprint(t['team'].value_counts())"),

    md("## 2. Heatmap de demanda por equipo x categoria\n\n"
       "**Que decidimos:** el equipo con mas volumen total + la categoria dominante "
       "define donde reforzar personal."),

    py("pivot = t.pivot_table(index='team', columns='category', values='ticket_id', aggfunc='count', fill_value=0)\n"
       "fig, ax = plt.subplots(figsize=(8, 4))\n"
       "sns.heatmap(pivot, annot=True, fmt='d', cmap='YlGnBu', ax=ax)\n"
       "ax.set_title('Volumen por equipo x categoria (cuanto mas oscuro, mas carga)')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab3_fig2_heatmap.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 3. Heatmap dia x hora x equipo - cuando hay tickets?\n\n"
       "**Que vemos:** la densidad de tickets por equipo, por dia de la semana "
       "(eje Y) y hora del dia (eje X).\n\n"
       "**Para que sirve:**\n"
       "- **Picos claros en horas especificas** = oportunidad de rotacion de turnos\n"
       "- **Distribucion uniforme** = no rotacion, sino contratar mas\n"
       "- **Caida fuerte en finde** = oportunidad de automatizar tickets no urgentes"),

    py("t['dow'] = t['created_at'].dt.day_name()\n"
       "t['hour'] = t['created_at'].dt.hour\n"
       "dow_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']\n"
       "t['dow'] = pd.Categorical(t['dow'], categories=dow_order, ordered=True)\n\n"
       "fig, axes = plt.subplots(1, 5, figsize=(22, 5), sharey=True, sharex=True)\n"
       "teams = sorted(t['team'].unique())\n"
       "for ax, team in zip(axes, teams):\n"
       "    sub = t[t['team'] == team]\n"
       "    pivot = sub.pivot_table(index='dow', columns='hour', values='ticket_id', aggfunc='count', fill_value=0)\n"
       "    sns.heatmap(pivot, ax=ax, cmap='YlOrRd',\n"
       "                cbar=(team == teams[-1]),\n"
       "                cbar_kws={'label': '# tickets'} if team == teams[-1] else None)\n"
       "    ax.set_title(team, fontsize=12, fontweight='bold')\n"
       "    ax.set_xlabel('Hora del dia')\n"
       "    ax.set_ylabel('Dia de la semana' if team == teams[0] else '')\n"
       "fig.suptitle('Demanda por dia x hora x equipo - patron visible = oportunidad de rotacion', fontsize=13, y=1.05)\n"
       "plt.tight_layout()\nplt.savefig('../html/lab3_fig3_heatmap_demand.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 4. Boxplot de tiempo de resolucion (horas)\n\n"
       "**Que vemos:** la mediana dice cuanto tarda el caso tipico (horas). "
       "Los outliers arriba son incidentes graves."),

    py("fig, ax = plt.subplots(figsize=(12, 5))\n"
       "order = t.groupby('team')['resolution_h'].median().sort_values().index\n"
       "sns.boxplot(data=t, x='team', y='resolution_h', order=order, hue='team', legend=False, ax=ax)\n"
       "ax.set_yscale('log')\n"
       "ax.set_title('Tiempo de resolucion por equipo (horas, log) - outliers = incidentes')\n"
       "ax.set_ylabel('Horas (escala log)')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab3_fig4_boxplot.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 5. Breach SLA - ¿donde perdemos dinero?\n\n"
       "**Que decidimos:** cada breach SLA puede tener penalizacion contractual. "
       "El equipo con mayor breach rate es candidato a refuerzo."),

    py("breach = t.groupby('team')['sla_breached'].mean().sort_values(ascending=False)\n"
       "fig, ax = plt.subplots(figsize=(10, 4))\n"
       "breach.plot(kind='bar', color='indianred', ax=ax)\n"
       "ax.set_ylabel('% breach SLA')\n"
       "ax.set_title('Breach por equipo (ordenado de mayor a menor)')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab3_fig5_breach.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 6. Tu decision como SRE\n\n"
       "Mirando los datos:\n"
       "- **Refuerzo de personal**: equipo con **mayor volumen total** en el heatmap "
       "team x categoria **y** alto % breach = candidato #1.\n"
       "- **Rotacion de turnos**: equipo con **patron horario claro** en el heatmap "
       "dia x hora (ej: picos lunes 9-11am) = candidato a rotacion.\n"
       "- **Dispersión de breach**: si breach esta en todos los equipos, el problema "
       "es global (proceso). Si esta en 1-2, el problema es local (equipo)."),

    py("# Tabla resumen para tu decision\n"
       "summary = t.groupby('team').agg(\n"
       "    total_tickets=('ticket_id', 'count'),\n"
       "    pct_breach=('sla_breached', lambda s: s.mean() * 100),\n"
       "    avg_resolution_h=('resolution_h', 'mean'),\n"
       "    pct_rollback=('rollback', lambda s: s.sum() / max((t['category']=='change').sum(), 1) * 100),\n"
       ").round(2).sort_values('pct_breach', ascending=False)\n"
       "summary\n\n"
       "print('\\nLectura:')\n"
       "print('- Equipo con >30% breach: necesita refuerzo')\n"
       "print('- Equipo con patron horario claro (heatmap sec 3): rotacion')\n"
       "print('- Equipo con >20% rollback: proceso de cambios roto')"),

    md("## 7. Rollback en cambios por equipo\n\n"
       "**Que decidimos:** un rollback rate alto = cambios mal probados o sin revision "
       "suficiente; candidato a postmortem del proceso de cambios."),

    py("changes = t[t['category'] == 'change']\n"
       "fig, ax = plt.subplots(figsize=(10, 4))\n"
       "changes.groupby('team')['rollback'].mean().sort_values(ascending=False).plot(kind='bar', color='goldenrod', ax=ax)\n"
       "ax.set_ylabel('% rollback')\n"
       "ax.set_title('Rollback rate por equipo (solo cambios)')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab3_fig6_rollback.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 8. Para presentar al director\n\n"
       "Tu headline (1 linea):\n\n"
       "> «El equipo **[NOMBRE]** maneja el **X%** de los tickets con un **Y%** de "
       "breach SLA; rotamos turnos lunes-viernes 9-11am = **$Z** ahorrados en "
       "penalizaciones.»"),
])

(NB_DIR / "lab3_requerimientos.ipynb").write_text(json.dumps(LAB_3, indent=1), encoding="utf-8")
print("wrote lab3 v4")