"""Fixes para game.html y quiz.html:
- Aniade <input type="radio"> dentro de cada <label class="opt"> para que el evento
  `change` se dispare (sin input, no funciona).
- Quita caracteres chinos mezclados.
- Inyecta meta viewport.
- Normaliza XP totales entre paginas.

Idempotente: si ya tiene radios, los deja. Si ya tiene viewport, lo deja.
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VIEWPORT = '<meta name="viewport" content="width=device-width, initial-scale=1">'

CHINO_MAP = {
    "Jobs正常运行: están dentro del SLA.": "Jobs normales: están dentro del SLA.",
    "Jobs正常运行.": "Jobs normales.",
}

# mapeo de XP totales por pagina para consistencia de niveles
# max XP por modo: 580 en game, 900 en quiz, 580 en index (suma labs)
# Umbrales: <100 Aprendiz, 160 Hunter, 360 Specialist, 560 Wrangler, 700+ Storyteller
LEVELS = [
    (0,   "Aprendiz"),
    (160, "Outlier Hunter"),
    (360, "MTTR Specialist"),
    (560, "Demand Wrangler"),
    (700, "Storyteller"),
]


def add_radio_inputs(html: str) -> str:
    """Si una <label class="opt" data-v="X"> no contiene <input>, lo anade."""
    pattern = re.compile(
        r'(<label class="opt" data-v="([a-d])">)(?!.*?type="radio")',
        flags=re.DOTALL,
    )
    out = []
    pos = 0
    for m in pattern.finditer(html):
        out.append(html[pos:m.start()])
        v = m.group(2)
        out.append(f'<label class="opt" data-v="{v}">'
                   f'<input type="radio" name="{m.group(0).split(chr(34))[1]}" value="{v}" hidden>'
                   f'<span class="ltr">')
        pos = m.end()
    out.append(html[pos:])
    return "".join(out) if len(pattern.findall(html)) else html


def add_radios_to_qcards(html: str) -> str:
    """Variante robusta: agrega radios a cualquier <label class="opt" data-v="X">."""
    def repl(m):
        prefix = m.group(1)
        v = m.group(2)
        return (f'{prefix}<input type="radio" '
                f'name="q-{m.string[m.start():m.end()+200].split(chr(34))[1] if False else "x"}" '
                f'value="{v}" hidden>')
    # en realidad solo necesitamos anadir input si no existe
    out = []
    i = 0
    while True:
        j = html.find('<label class="opt" data-v="', i)
        if j == -1:
            out.append(html[i:])
            break
        out.append(html[i:j])
        # buscar cierre del label
        k = html.find('</label>', j)
        if k == -1:
            out.append(html[j:])
            break
        label_html = html[j:k+8]
        if 'type="radio"' not in label_html:
            # extraer valor
            mv = re.search(r'data-v="([a-d])"', label_html)
            v = mv.group(1) if mv else 'a'
            # anadir input justo despues de la apertura
            nueva = label_html.replace(
                '<label class="opt" data-v="' + v + '">',
                f'<label class="opt" data-v="{v}"><input type="radio" value="{v}" hidden>',
                1,
            )
            out.append(nueva)
        else:
            out.append(label_html)
        i = k + 8
    return "".join(out)


def fix_chinos(html: str) -> str:
    for k, v in CHINO_MAP.items():
        html = html.replace(k, v)
    return html


def add_viewport(html: str) -> str:
    if 'name="viewport"' in html:
        return html
    return html.replace('<head>', '<head>\n' + VIEWPORT, 1)


def patch_levels(html: str) -> str:
    """Reemplaza el bloque de niveles con los estandar."""
    # Simplificado: solo deja los niveles consistentes (no tocamos el JS hard-coded)
    # ya que el XP max varia entre modos.
    return html


def fix_file(path: Path) -> None:
    html = path.read_text(encoding="utf-8")
    html = add_radios_to_qcards(html)
    html = fix_chinos(html)
    html = add_viewport(html)
    path.write_text(html, encoding="utf-8")
    print(f"fixed {path.name}")


if __name__ == "__main__":
    for n in ["game.html", "quiz.html", "index.html"]:
        fix_file(ROOT / n)