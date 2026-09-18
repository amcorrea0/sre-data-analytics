"""Append Lab 3."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / "notebooks"


def cell(code, cell_type="code"):
    return {
        "cell_type": cell_type,
        "execution_count": None if cell_type == "markdown" else 0,
        "metadata": {},
        "outputs": [] if cell_type == "code" else None,
        "source": code.splitlines(keepends=True),
    }


def md(t): return cell(t, "markdown")
def py(t): return cell(t, "code")


def notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.13"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


LAB_3 = notebook([
    md("# Lab 3 - Tickets y demanda operativa\n\n"
       "**Modalidad:** hands-on - **Duracion:** ~12 min\n"
       "**Dataset:** tickets.csv\n\n"
       "## El caso de negocio\n\n"
       "El equipo de ingenieria reporta que esta saturado. El director nos pregunta:\n\n"
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
       "fig, ax = plt.subplots(figsize=(12, 3))\n"
       "sns.heatmap(tickets.isnull(), cbar=False, yticklabels=False, cmap='viridis', ax=ax)\n"
       "ax.set_title('NaN - priority y team tienen huecos')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab3_fig1_nan.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    py("# Limpiar errores tecnicos: resolution <= 0 o > 100 000\n"
       "t = tickets[(tickets['resolution_min'] > 0) & (tickets['resolution_min'] < 100_000)].copy()\n"
       "t['priority'] = t['priority'].fillna(t['priority'].mode().iloc[0])\n"
       "t['team'] = t['team'].fillna(t['team'].mode().iloc[0])\n"
       "print(f'limpiados: {len(tickets) - len(t)} filas con errores tecnicos')"),

    md("## 2. Heatmap de demanda por equipo x categoria\n\n"
       "**Que decidimos:** el equipo con mas volumen total + la categoria dominante "
       "define donde reforzar personal."),

    py("pivot = t.pivot_table(index='team', columns='category', values='ticket_id', aggfunc='count', fill_value=0)\n"
       "fig, ax = plt.subplots(figsize=(8, 4))\n"
       "sns.heatmap(pivot, annot=True, fmt='d', cmap='YlGnBu', ax=ax)\n"
       "ax.set_title('Volumen por equipo x categoria (cuanto mas oscuro, mas carga)')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab3_fig2_heatmap.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 3. Heatmap dia x hora x equipo - cuando hay tickets?\n\n"
       "**Que decidimos:** si la mayoria de tickets llegan lunes 9-11am, podemos "
       "absorber la carga con rotacion de turnos. Si es uniforme, no."),

    py("t['dow'] = t['created_at'].dt.day_name()\n"
       "t['hour'] = t['created_at'].dt.hour\n"
       "dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']\n"
       "t['dow'] = pd.Categorical(t['dow'], categories=dow_order, ordered=True)\n\n"
       "fig, axes = plt.subplots(1, 5, figsize=(20, 4), sharey=True, sharex=True)\n"
       "teams = sorted(t['team'].unique())\n"
       "for ax, team in zip(axes, teams):\n"
       "    sub = t[t['team'] == team]\n"
       "    pivot = sub.pivot_table(index='dow', columns='hour', values='ticket_id', aggfunc='count', fill_value=0)\n"
       "    sns.heatmap(pivot, ax=ax, cmap='YlOrRd', cbar=(team == teams[-1]))\n"
       "    ax.set_title(team, fontsize=11)\nax.set_xlabel('')\nax.set_ylabel('')\n"
       "    if team != teams[0]:\nax.set_yticklabels([])\n"
       "fig.suptitle('Demanda por dia x hora x equipo - patron visible = oportunidad de rotacion', fontsize=13, y=1.05)\n"
       "plt.tight_layout()\nplt.savefig('../html/lab3_fig3_heatmap_demand.png', dpi=110, bbox_inches='tight')\nplt.show()"),

    md("## 4. Boxplot de tiempo de resolucion (log)\n\n"
       "**Que decidimos:** la mediana dice cuanto tarda el caso tipico. Los "
       "outliers arriba son incidentes graves."),

    py("fig, ax = plt.subplots(figsize=(12, 5))\n"
       "order = t.groupby('team')['resolution_min'].median().sort_values().index\n"
       "sns.boxplot(data=t, x='team', y='resolution_min', order=order, hue='team', legend=False, ax=ax)\n"
       "ax.set_yscale('log')\n"
       "ax.set_title('Tiempo de resolucion por equipo (log) - outliers = incidentes')\n"
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
       "- ¿Cual equipo necesita mas gente?\n"
       "- ¿Cual equipo tiene un patron horario claro que permita rotar turnos?\n"
       "- ¿La brecha de SLA se concentra en pocos equipos o esta dispersa?"),

    py("# Rollback en cambios por equipo\n"
       "changes = t[t['category'] == 'change']\n"
       "fig, ax = plt.subplots(figsize=(10, 4))\n"
       "changes.groupby('team')['rollback'].mean().sort_values(ascending=False).plot(kind='bar', color='goldenrod', ax=ax)\n"
       "ax.set_ylabel('% rollback')\n"
       "ax.set_title('Rollback rate por equipo (solo cambios)')\n"
       "plt.tight_layout()\nplt.savefig('../html/lab3_fig6_rollback.png', dpi=110, bbox_inches='tight')\nplt.show()"),
])

(NB_DIR / "lab3_requerimientos.ipynb").write_text(json.dumps(LAB_3, indent=1), encoding="utf-8")
print("wrote lab3")