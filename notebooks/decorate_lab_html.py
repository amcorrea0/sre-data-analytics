"""
Post-procesa los HTML de nbconvert para inyectar el header SETI, TOC,
sección de aprendizaje y footer con CTA.

Uso:
    python notebooks/decorate_lab_html.py

Lee html/lab{1,2,3,4}_*.html y escribe html/lab{1,2,3,4}_*.html (in-place).
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "html"

LAB_META = {
    "lab1_observabilidad": {
        "num": 1, "title": "Observabilidad: ETL + outliers",
        "mod": "guiado", "xp": 100, "badge": "Outlier Hunter",
        "duration": "12 min",
        "lab_md": "labs/lab-01-observabilidad/README.md",
        "next": ("html/lab2_automatizacion.html", "Misión 2 · Automatización →"),
        "back": "index.html",
        "learn": [
            "Diagnosticar NaN con heatmap y decidir imputación (mediana vs media).",
            "Detectar errores técnicos vs outliers reales.",
            "Aplicar la regla de Tukey (IQR × 1.5) por grupo.",
            "Comparar distribución cruda vs limpia con media/mediana.",
        ],
    },
    "lab2_automatizacion": {
        "num": 2, "title": "Automatización: jobs, MTTR, outliers",
        "mod": "guiado", "xp": 120, "badge": "MTTR Specialist",
        "duration": "12 min",
        "lab_md": "labs/lab-02-automatizacion/README.md",
        "next": ("html/lab3_requerimientos.html", "Misión 3 · Tickets →"),
        "back": "index.html",
        "learn": [
            "Imputar `duration_sec` por grupo (mediana del job).",
            "Leer un boxplot en escala log y separar jobs lentos vs rápidos.",
            "Calcular MTTR como mediana en runs fallidos/timeout.",
            "Identificar el trigger ruidoso para automatizar mejor.",
        ],
    },
    "lab3_requerimientos": {
        "num": 3, "title": "Tickets y requerimientos de operación",
        "mod": "hands-on", "xp": 160, "badge": "Demand Wrangler",
        "duration": "12 min",
        "lab_md": "labs/lab-03-requerimientos/README.md",
        "next": ("html/lab4_ejecutivo.html", "Misión 4 · Dashboard ejecutivo →"),
        "back": "index.html",
        "learn": [
            "Pivotar team × category en heatmap.",
            "Boxplot log de `resolution_min` por equipo.",
            "Calcular % breach SLA global y por equipo.",
            "Reportar rollback rate entre cambios.",
        ],
    },
    "lab4_ejecutivo": {
        "num": 4, "title": "Dashboard ejecutivo: de datos a historia",
        "mod": "hands-on", "xp": 200, "badge": "Storyteller",
        "duration": "12 min",
        "lab_md": "labs/lab-04-ejecutivo/README.md",
        "next": ("game.html", "Modo game →"),
        "back": "index.html",
        "learn": [
            "Consolidar 5 datasets en 4 secciones listas para presentar.",
            "Calcular disponibilidad observada y burn-rate medio.",
            "Priorizar acciones con score RICE.",
            "Redactar una headline ejecutiva de 1 línea.",
        ],
    },
}

NAV_TPL = """<nav class="nav"><div class="wrap">
<div class="brand"><div class="logo">S</div> SETI · SRE Data Analytics</div>
<div class="links">
<a href="../{back}">Inicio</a>
<a href="../game.html">Game</a>
<a href="../quiz.html">Quiz</a>
<a href="../{lab_md}">Guía</a>
</div>
<a class="cta" href="../{next_path}">{next_label}</a>
</div></nav>"""

HEADER_TPL = """<header class="hero" style="padding: 48px 28px 56px;">
<div class="wrap">
<span class="eyebrow"><span class="dot"></span> Misión {num} · {mod} · {duration} · +{xp} XP</span>
<h1>{title}</h1>
<p class="lede">Notebook ejecutable + figuras listas para presentar. Completa el lab,
luego juega las preguntas en <a href="../game.html" style="color:#ff6b61;text-decoration:underline;">game.html</a>
para ganar XP y el badge <strong>{badge}</strong>.</p>
<div class="cta-row">
<a class="btn btn-primary" href="../game.html">🎮 Jugar Misión {num}</a>
<a class="btn btn-ghost" href="../{next_path}">{next_label}</a>
</div>
</div></header>"""

LEARN_TPL = """<section class="block" style="padding-top: 32px;">
<div class="wrap"><div class="learn-card">
<h3>🎯 Lo que aprendes en este lab</h3>
<ul>{items}</ul>
</div></div></section>"""

FOOTER_TPL = """<footer class="site">
<div class="wrap">
<div>&copy; 2026 &middot; SETI &middot; SRE Data Analytics</div>
<div><a href="../index.html">Inicio</a></div>
</div></footer>"""

CSS_LINK = '<link rel="stylesheet" href="../assets/style.css">'


def build_toc(body: str) -> str:
    """Extrae los encabezados y genera anchors consistentes (h1, h2, ...)."""
    items = []
    for m in re.finditer(r'<h([1-3])[^>]*id="h(\d+)"[^>]*>(.*?)</h\1>', body, flags=re.DOTALL):
        lvl = int(m.group(1))
        idx = int(m.group(2))
        text = re.sub(r'<[^>]+>', '', m.group(3)).strip()
        if not text:
            continue
        if lvl == 1:
            continue
        items.append((lvl, idx, text))
    if not items:
        return ""
    ol = "".join(
        f'<li style="margin-left:{(lvl - 2) * 14}px;"><a href="#h{idx}">{t}</a></li>'
        for lvl, idx, t in items
    )
    return f'<section class="block" style="padding-top:24px;"><div class="wrap"><div class="toc"><h3>Tabla de contenidos</h3><ol>{ol}</ol></div></div></section>'


def anchor_headings(body: str) -> str:
    """Pone id limpio 'hN' en cada h2/h3 para que el TOC navegue.

    nbconvert produce <h2 id="Titulo-Encoded">Titulo</h2>. El id del heading sale
    duplicado como texto visible. Aqui eliminamos el id viejo y lo reescribimos.
    """
    counter = [0]

    def repl(m):
        lvl = int(m.group(1))
        attrs = m.group(2)
        text = m.group(3)
        if lvl == 1:
            # El h1 = titulo del notebook: limpiamos su id largo si existe
            attrs_clean = re.sub(r'\s*id="[^"]*"', '', attrs)
            return f'<h{lvl}{attrs_clean}>{text}</h{lvl}>'
        counter[0] = counter[0] + 1
        # Si el contenido empieza con id="X" suelto (el bug nbconvert), lo quitamos
        text_clean = re.sub(r'^\s*id="[^"]*"\s*', '', text)
        # Quitamos cualquier atributo id viejo del nbconvert
        attrs_clean = re.sub(r'\s*id="[^"]*"', '', attrs)
        return f'<h{lvl} id="h{counter[0]}" data-toc{attrs_clean}>{text_clean}</h{lvl}>'

    return re.sub(r'<h([1-3])([^>]*)>(.*?)</h\1>', repl, body, flags=re.DOTALL)


def decorate(slug: str) -> Path:
    meta = LAB_META[slug]
    path = HTML / f"{slug}.html"
    html = path.read_text(encoding="utf-8")

    # Quita cualquier inyección previa (idempotencia)
    html = re.sub(r'<nav class="nav">.*?</nav>', '', html, flags=re.DOTALL)
    html = re.sub(r'<header class="hero"[^>]*>.*?</header>', '', html, flags=re.DOTALL)
    html = re.sub(r'<footer class="site">.*?</footer>', '', html, flags=re.DOTALL)
    html = re.sub(r'<section class="block"[^>]*>\s*<div class="wrap">\s*<div class="learn-card">.*?</div>\s*</div>\s*</section>', '', html, flags=re.DOTALL)
    html = re.sub(r'<section class="block"[^>]*>\s*<div class="wrap">\s*<div class="toc">.*?</div>\s*</div>\s*</section>', '', html, flags=re.DOTALL)

    # Inyecta CSS en <head>
    if 'assets/style.css' not in html:
        html = html.replace('</head>', CSS_LINK + '</head>', 1)

    # nbconvert pone todo en un <body><div>... contenido ...</div></body>
    # localizamos el contenedor principal
    body_match = re.search(r'(<body[^>]*>)(.*?)(</body>)', html, flags=re.DOTALL)
    if not body_match:
        raise RuntimeError(f"no body in {path}")
    open_b, body, close_b = body_match.groups()

    # Quita padding/margin default del notebook para que el hero ocupe todo el ancho
    body = re.sub(r'<div[^>]*class="[^"]*container[^"]*"[^>]*>', '<div class="lab-shell">', body, count=1)
    if 'lab-shell' not in body:
        body = '<div class="lab-shell">' + body
    if '</body>' in body and body.count('</div>') >= 1:
        # cerramos el wrapper al final
        body = body.replace('</body>', '</div></body>')

    # Anchor en h2/h3
    body = anchor_headings(body)

    # Extrae TOC del body ANTES de inyectar header
    toc = build_toc(body)

    # Header, learn, footer
    header = HEADER_TPL.format(
        num=meta["num"], mod=meta["mod"].upper(), duration=meta["duration"],
        xp=meta["xp"], title=meta["title"], badge=meta["badge"],
        next_path=meta["next"][0], next_label=meta["next"][1],
    )
    nav = NAV_TPL.format(
        back=meta["back"], next_path=meta["next"][0], next_label=meta["next"][1],
        lab_md=meta["lab_md"],
    )
    learn = LEARN_TPL.format(items="".join(f"<li>{x}</li>" for x in meta["learn"]))
    footer = FOOTER_TPL

    new_body = nav + header + toc + learn + body + footer
    html = html[:body_match.start()] + open_b + new_body + close_b + html[body_match.end():]

    # suprime el <h1> interno del notebook (queda redundante con el hero)
    html = re.sub(r'<h1[^>]*>.*?</h1>', '', html, count=1, flags=re.DOTALL)

    path.write_text(html, encoding="utf-8")
    return path


if __name__ == "__main__":
    for slug in LAB_META:
        p = decorate(slug)
        print(f"decorated {p.name} ({p.stat().st_size:,} bytes)")