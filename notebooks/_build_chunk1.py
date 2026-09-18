"""Construye los 4 notebooks (.ipynb) v3 - chunk 1: helpers + header comun.

Cada celda de markdown explica QUE BUSCAMOS y POR QUE.
Graficos cuentan decisiones ejecutivas concretas (comprar capacidad,
reescribir job, reforzar equipo).
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / "notebooks"
NB_DIR.mkdir(parents=True, exist_ok=True)


def cell(code: str, cell_type: str = "code") -> dict:
    # nbformat valido: code cells usan execution_count + outputs,
    # markdown cells NO llevan esos campos.
    if cell_type == "markdown":
        return {
            "cell_type": "markdown",
            "metadata": {},
            "source": code.splitlines(keepends=True),
        }
    return {
        "cell_type": "code",
        "execution_count": 0,
        "metadata": {},
        "outputs": [],
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
