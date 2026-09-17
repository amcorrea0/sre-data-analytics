"""Limpia referencias a slides.html y arregla rutas relativas en lab HTMLs.

- Quita todos los href a slides.html (deck eliminado).
- Arregla href a 'index.html' -> '../index.html' en lab HTMLs.
- Arregla href a 'labs/...' -> '../labs/...' en lab HTMLs.
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ROOT_FILES = ["index.html", "game.html", "quiz.html"]
LAB_FILES = [
    "html/lab1_observabilidad.html",
    "html/lab2_automatizacion.html",
    "html/lab3_requerimientos.html",
    "html/lab4_ejecutivo.html",
]


def strip_slides_refs(html: str) -> str:
    """Quita <a ... href='...slides.html...'>...</a> y referencias sueltas."""
    # borra anclas completas con slides.html
    html = re.sub(r'<a [^>]*href="[^"]*slides\.html[^"]*"[^>]*>[^<]*</a>', '', html, flags=re.DOTALL)
    # borra referencias sueltas a slides.html
    html = re.sub(r'href="[^"]*slides\.html[^"]*"', '#', html)
    return html


def fix_lab_paths(html: str) -> str:
    """En lab HTMLs, las rutas a root deben empezar con ../"""
    html = re.sub(r'(?<![\.\w])href="index\.html"', 'href="../index.html"', html)
    html = re.sub(r'(?<![\.\w])href="labs/', 'href="../labs/', html)
    return html


def fix_root_paths(html: str) -> str:
    """En root, lab HTMLs ya están bajo html/ pero los hrefs son html/lab?.html.
    Quitamos el prefijo html/ para que '../index.html' funcione bien.
    Las cards de index ya usan 'html/lab*.html' que es correcto.
    Solo nos aseguramos de que game.html y quiz.html usen rutas correctas."""
    return html


def main():
    for f in ROOT_FILES:
        p = ROOT / f
        html = p.read_text(encoding="utf-8")
        new = strip_slides_refs(html)
        if new != html:
            p.write_text(new, encoding="utf-8")
            print(f"stripped slides refs in {f}")

    for f in LAB_FILES:
        p = ROOT / f
        html = p.read_text(encoding="utf-8")
        html = strip_slides_refs(html)
        html = fix_lab_paths(html)
        # tambien limpiar las menciones textuales al "Deck" o "slides.html"
        html = html.replace('Deck (slides.html)', 'Index')
        p.write_text(html, encoding="utf-8")
        print(f"cleaned {f}")


if __name__ == "__main__":
    main()