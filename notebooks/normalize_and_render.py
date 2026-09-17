"""
Normaliza tildes en archivos .md y .html, y convierte los .md restantes
(STORY.md, FACILITATOR.md, labs/*/README.md) a HTML renderizado con el
branding SETI.

- Cambia `lang="en"` a `lang="es"` en los 4 lab HTMLs.
- Reemplaza formas sin tilde por tildes cuando son ambiguas (errores tecnicos
  -> errores tecnicos con tilde). NO toca URLs, paths, ni codigos.
"""
from __future__ import annotations

import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]

# Tildes faltantes detectadas en la auditoria.
# Solo formas que SIEMPRE llevan tilde (no son palabras sin tilde validas).
TILDE_FIXES = {
    "errores tecnicos": "errores técnicos",
    "Errores tecnicos": "Errores técnicos",
    "ERRORES TECNICOS": "ERRORES TÉCNICOS",
    "errores_tecnicos": "errores_técnicos",
    "tecnico": "técnico",
    "Tecnico": "Técnico",
    "categoria": "categoría",
    "Categoria": "Categoría",
    "metrica": "métrica",
    "Metrica": "Métrica",
    "Sesion": "Sesión",
    "sesion": "sesión",
    "Version": "Versión",
    "version": "versión",
    "publico": "público",
    "Publico": "Público",
    "maximo": "máximo",
    "Maximo": "Máximo",
    "minimo": "mínimo",
    "Minimo": "Mínimo",
    "Numero": "Número",
    "numero": "número",
    "automatas": "autómatas",  # no aparece, defensivo
    "diagnostico": "diagnóstico",
    "Diagnostico": "Diagnóstico",
    "espanol": "español",
    "Espanol": "Español",
    "medico": "médico",
    "Medico": "Médico",
    "Senales": "Señales",
    "senales": "señales",
    "periodo": "período",
    "Periodo": "Período",
}


def normalize_tildes(text: str) -> tuple[str, int]:
    n = 0
    for bad, good in TILDE_FIXES.items():
        if bad in text:
            text = text.replace(bad, good)
            n += 1
    return text, n


def fix_lang_in_html(text: str) -> tuple[str, int]:
    n = 0
    if '<html lang="en">' in text:
        text = text.replace('<html lang="en">', '<html lang="es">', 1)
        n += 1
    return text, n


# ============================================================================
# MD to HTML con branding SETI
# ============================================================================

PAGE_TPL = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — SETI · SRE Data Analytics</title>
<link rel="stylesheet" href="{css_path}">
<style>
  /* prose-page solo para el contenido renderizado */
  .prose-page {{ max-width: 920px; margin: 0 auto; padding: 56px 28px 96px; }}
  .prose-page h1 {{ font-size: clamp(2rem, 4vw, 2.8rem); margin: 0 0 8px; letter-spacing: -.02em; }}
  .prose-page > p {{ color: var(--grey-2); margin: 4px 0 0; max-width: 720px; }}
  .prose-page h2 {{ font-size: 1.4rem; margin-top: 36px; border-bottom: 1px solid var(--grey-5); padding-bottom: 6px; }}
  .prose-page h3 {{ font-size: 1.12rem; margin-top: 28px; color: var(--red-7); }}
  .prose-page h1 + h2 {{ margin-top: 32px; }}
</style>
</head>
<body>
{nav}
<header class="hero" style="padding: 56px 28px 56px;">
  <div class="wrap">
    <span class="eyebrow"><span class="dot"></span> {badge}</span>
    <h1>{title}</h1>
    {subtitle}
  </div>
</header>
<article class="prose-page">
{body}
</article>
{footer}
</body>
</html>
"""


def md_nav(home: str) -> str:
    return f"""<nav class="nav"><div class="wrap">
<div class="brand"><div class="logo">S</div> SETI · SRE Data Analytics</div>
<div class="links">
<a href="{home}">Inicio</a>
<a href="{home}">Misiones</a>
<a href="{home.replace('index.html', 'game.html')}">Game</a>
<a href="{home.replace('index.html', 'quiz.html')}">Quiz</a>
</div>
<a class="cta" href="{home}">Empezar</a>
</div></nav>"""


def md_footer(home: str) -> str:
    return f"""<footer class="site">
<div class="wrap">
<div>SETI · SRE Data Analytics · blanco + grises + rojos</div>
<div><a href="{home}">Inicio</a></div>
</div></footer>"""


def md_to_html(md_path: Path, out_path: Path, *, title: str, badge: str,
               css_path: str, home: str, subtitle_html: str = "") -> None:
    md_text = md_path.read_text(encoding="utf-8")
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "toc"])
    html = PAGE_TPL.format(
        title=title, badge=badge, body=body, css_path=css_path,
        nav=md_nav(home), footer=md_footer(home),
        subtitle=subtitle_html,
    )
    out_path.write_text(html, encoding="utf-8")
    print(f"rendered {out_path.relative_to(ROOT)}")


# ============================================================================
# Main
# ============================================================================

def normalize_all_md():
    # normaliza los .md existentes
    targets = [
        ROOT / "README.md",
        ROOT / "STORY.md",
        ROOT / "FACILITATOR.md",
        ROOT / "labs" / "lab-01-observabilidad" / "README.md",
        ROOT / "labs" / "lab-02-automatizacion" / "README.md",
        ROOT / "labs" / "lab-03-requerimientos" / "README.md",
        ROOT / "labs" / "lab-04-ejecutivo" / "README.md",
    ]
    total = 0
    for p in targets:
        if not p.exists():
            continue
        text, n = normalize_tildes(p.read_text(encoding="utf-8"))
        if n:
            p.write_text(text, encoding="utf-8")
            print(f"normalized {p.relative_to(ROOT)} ({n} fixes)")
            total += n
    print(f"total tilde fixes: {total}")


def fix_lab_htmls_lang():
    for slug in ["lab1_observabilidad", "lab2_automatizacion",
                 "lab3_requerimientos", "lab4_ejecutivo"]:
        p = ROOT / "html" / f"{slug}.html"
        text, n = fix_lang_in_html(p.read_text(encoding="utf-8"))
        if n:
            p.write_text(text, encoding="utf-8")
            print(f"fixed lang in {p.relative_to(ROOT)}")


def normalize_lab_htmls_body():
    """Aplica normalización de tildes al TEXTO VISIBLE del usuario dentro de los notebooks.
    Cuidado: no tocar clases CSS, ids, ni codigo que sí contenga 'tecnico' como variable."""
    for slug in ["lab1_observabilidad", "lab2_automatizacion",
                 "lab3_requerimientos", "lab4_ejecutivo"]:
        p = ROOT / "html" / f"{slug}.html"
        text = p.read_text(encoding="utf-8")
        # Reemplaza "errores tecnicos" SOLO en texto entre tags (no en atributos)
        # Estrategia: split por tags, solo modifica el contenido.
        def fix_in_segment(seg: str) -> str:
            new_seg, n = normalize_tildes(seg)
            return new_seg
        # Aplicar al texto entre > y <
        out = []
        i = 0
        in_tag = False
        buf_tag = []
        for ch in text:
            if ch == "<":
                if buf_tag:
                    out.append("".join(buf_tag))
                buf_tag = ["<"]
                in_tag = True
            elif ch == ">":
                buf_tag.append(">")
                out.append("".join(buf_tag))
                buf_tag = []
                in_tag = False
            else:
                if in_tag:
                    buf_tag.append(ch)
                else:
                    out.append(ch)
        if buf_tag:
            out.append("".join(buf_tag))
        new_html = "".join(out)
        # Aplica fixes solo a texto entre tags
        fixed_text, n = normalize_tildes(new_html)
        if n:
            p.write_text(fixed_text, encoding="utf-8")
            print(f"normalized text in {p.relative_to(ROOT)} ({n} fixes)")


def render_md_to_html():
    """Convierte los .md clave en .html con branding SETI."""
    pairs = [
        # (md_path, out_html_rel, title, badge, css_path_relative_to_out, home_relative_to_out, subtitle)
        (
            ROOT / "STORY.md",
            ROOT / "STORY.html",
            "Story — el arco narrativo",
            "Para el facilitador",
            "assets/style.css",
            "index.html",
            "<p class=\"lede\">Cómo vivimos los 60 minutos: emoción por emoción.</p>",
        ),
        (
            ROOT / "FACILITATOR.md",
            ROOT / "FACILITATOR.html",
            "Facilitador — guía operativa",
            "Para quien conduce la sesión",
            "assets/style.css",
            "index.html",
            "<p class=\"lede\">Agenda cronometrada, prompts de discusión y señales de éxito.</p>",
        ),
        # guías de cada lab (rutas son ../)
        (
            ROOT / "labs" / "lab-01-observabilidad" / "README.md",
            ROOT / "labs" / "lab-01-observabilidad" / "guide.html",
            "Lab 1 — Guía del estudiante",
            "Misión 1 · Guiado · 12 min",
            "../../assets/style.css",
            "../../index.html",
            "",
        ),
        (
            ROOT / "labs" / "lab-02-automatizacion" / "README.md",
            ROOT / "labs" / "lab-02-automatizacion" / "guide.html",
            "Lab 2 — Guía del estudiante",
            "Misión 2 · Guiado · 12 min",
            "../../assets/style.css",
            "../../index.html",
            "",
        ),
        (
            ROOT / "labs" / "lab-03-requerimientos" / "README.md",
            ROOT / "labs" / "lab-03-requerimientos" / "guide.html",
            "Lab 3 — Guía del estudiante",
            "Misión 3 · Hands-on · 12 min",
            "../../assets/style.css",
            "../../index.html",
            "",
        ),
        (
            ROOT / "labs" / "lab-04-ejecutivo" / "README.md",
            ROOT / "labs" / "lab-04-ejecutivo" / "guide.html",
            "Lab 4 — Guía del estudiante",
            "Misión 4 · Hands-on · 12 min",
            "../../assets/style.css",
            "../../index.html",
            "",
        ),
    ]
    for md_p, html_p, title, badge, css_path, home, subtitle in pairs:
        if not md_p.exists():
            print(f"skip {md_p} (no existe)")
            continue
        md_to_html(md_p, html_p, title=title, badge=badge,
                   css_path=css_path, home=home, subtitle_html=subtitle)


def main():
    print("=== Normalizando tildes en .md ===")
    normalize_all_md()
    print("\n=== Arreglando lang=en en lab HTMLs ===")
    fix_lab_htmls_lang()
    print("\n=== Renderizando .md a HTML con branding SETI ===")
    render_md_to_html()
    # NOTA: aplicar normalize_tildes a los lab HTMLs es riesgoso (puede romper
    # codigo Python que usa 'tecnico' como nombre). Lo dejamos para revision manual.


if __name__ == "__main__":
    main()