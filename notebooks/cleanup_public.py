"""Limpia elementos de branding interno en las paginas PUBLICAS.

Problemas:
1. index.html: 4 botones 'Guia' en las cards de lab (links a guide.html, redundante con
   el CTA primario 'Abrir lab').
2. index.html, game.html, quiz.html: footer muestra texto interno
   'SETI SRE Data Analytics blanco + grises + rojos' (eso es branding de
   pizarra, no del usuario).
3. index.html: el link 'Inspirado en lab10' en el footer es meta-info interna.

El branding permanece en el CSS, en el titulo del head, en el <title>, y
en la 'brand' de la nav. Solo limpiamos las paginas del SRE.
"""
import re
from pathlib import Path

ROOT = Path(".")

# Reescrituras exactas (idempotente: si ya esta limpio no cambia nada)
REWRITES = [
    # 1) Quitar botones "Guia" de las cards de lab en index.html
    # El patron exacto de cada card
    (
        '<a href="labs/lab-01-observabilidad/guide.html">Gu\u00eda</a>\n',
        '',
    ),
    (
        '<a href="labs/lab-02-automatizacion/guide.html">Gu\u00eda</a>\n',
        '',
    ),
    (
        '<a href="labs/lab-03-requerimientos/guide.html">Gu\u00eda</a>\n',
        '',
    ),
    (
        '<a href="labs/lab-04-ejecutivo/guide.html">Gu\u00eda</a>\n',
        '',
    ),
]

# Reescritura del footer publico (mas limpio, sin info interna)
PUBLIC_FOOTER = """<footer class="site">
  <div class="wrap">
    <div>&copy; 2026 &middot; SETI &middot; SRE Data Analytics</div>
    <div><a href="index.html">Inicio</a></div>
  </div>
</footer>"""

# Reescritura del footer del index (sin 'Inspirado en lab10', sin paleta de colores)
INDEX_FOOTER = """<footer class="site">
  <div class="wrap">
    <div>&copy; 2026 &middot; SETI &middot; SRE Data Analytics</div>
    <div><a href="index.html">Inicio</a></div>
  </div>
</footer>"""


def clean(path: Path, footer_html: str):
    t = path.read_text(encoding='utf-8')
    new = t
    # 1) Botones Guia (solo en index)
    for old, repl in REWRITES:
        if old in new:
            new = new.replace(old, repl)
    # 2) Footer completo
    new = re.sub(
        r'<footer class="site">.*?</footer>',
        footer_html,
        new,
        flags=re.DOTALL,
    )
    if new != t:
        path.write_text(new, encoding='utf-8')
        print(f"cleaned {path.name}")


# index.html: limpiar botones Guia + footer simple
clean(ROOT / "index.html", INDEX_FOOTER)
# game.html y quiz.html: solo footer
for f in ["game.html", "quiz.html"]:
    clean(ROOT / f, PUBLIC_FOOTER)

print("done")