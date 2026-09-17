"""Aisla las paginas del facilitador en /facilitator/.

- Reescribe rutas internas de las paginas facilitador/ para que sean relativas
  a su nueva ubicacion (ej: assets/style.css -> ../assets/style.css).
- En las paginas PUBLICAS (index, game, quiz), elimina los enlaces a
  STORY/FACILITATOR/PANEL y oculta cualquier link al panel desde la nav.
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACL = ROOT / "facilitator"

# ============================================================================
# Paginas del facilitador -> prefijo ../ a rutas que apunten al root
# ============================================================================
FACILITATOR_PAGES = [
    FACL / "STORY.html",
    FACL / "FACILITATOR.html",
    FACL / "panel.html",
]

# Reescrituras para que las paginas del facilitador vivan en su propio mundo
# (nav arriba siempre apunta a ../index.html, ../game.html, etc.)
FAC_REWRITES = [
    ('href="assets/style.css"', 'href="../assets/style.css"'),
    ('href="assets/registration.css"', 'href="../assets/registration.css"'),
    ('href="assets/registration.js"', 'href="../assets/registration.js"'),
    # boton registrar del banner usa ../assets via la propia API; mantenemos
    # la API ya carga desde window.__SETI__ que el propio root inyecta.
    # Estos rewrites catch-all
    ('href="index.html"', 'href="../index.html"'),
    ('href="game.html"', 'href="../game.html"'),
    ('href="quiz.html"', 'href="../quiz.html"'),
    # imagenes y demas: nada mas que cambiar
]

# ============================================================================
# Paginas publicas -> quitar enlaces a STORY/FACILITATOR/PANEL/panel.html
# ============================================================================
PUBLIC_PAGES = [ROOT / "index.html", ROOT / "game.html", ROOT / "quiz.html"]

# Patrones de enlaces que apuntan al facilitator
PUBLIC_BAD_PATTERNS = [
    r'<a [^>]*href="(panel\.html|STORY\.html|FACILITATOR\.html)"[^>]*>[^<]*</a>',
    r'<a [^>]*href="(facilitator/[^"]+)"[^>]*>[^<]*</a>',
]

PUBLIC_NAV_REMOVES = [
    # si hay un link a panel.html en la nav, eliminarlo
    '      <a href="panel.html">Panel</a>\n',
    '      <a href="STORY.html">Story</a>\n',
    '      <a href="FACILITATOR.html">Facilitador</a>\n',
    '      <a href="panel.html">Panel</a>\n',  # en game/quiz si existe
]


def rewrite_facilitator():
    for p in FACILITATOR_PAGES:
        if not p.exists():
            continue
        html = p.read_text(encoding="utf-8")
        new = html
        for old, repl in FAC_REWRITES:
            new = new.replace(old, repl)
        # cualquier referencia residua a href="facilitator/" se quita
        new = re.sub(r'<a [^>]*href="facilitator/[^"]+"[^>]*>[^<]*</a>', '', new)
        if new != html:
            p.write_text(new, encoding="utf-8")
            print(f"rewrote {p.relative_to(ROOT)}")


def clean_public():
    for p in PUBLIC_PAGES:
        if not p.exists():
            continue
        html = p.read_text(encoding="utf-8")
        new = html
        # 1) eliminar links directos a STORY/FACILITATOR/PANEL
        for pat in PUBLIC_BAD_PATTERNS:
            new = re.sub(pat, '', new, flags=re.IGNORECASE)
        # 2) eliminar lineas de nav que apunten a esos archivos
        for line in PUBLIC_NAV_REMOVES:
            new = new.replace(line, '')
        if new != html:
            p.write_text(new, encoding="utf-8")
            print(f"cleaned {p.relative_to(ROOT)}")


rewrite_facilitator()
clean_public()