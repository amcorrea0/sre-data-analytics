"""Reescribe los radios en game.html y quiz.html.

- Cada <label class='opt' data-v='x'> dentro de una .qcard[data-q='QN']
  recibe un <input type='radio' name='QN' value='x'> para que el form funcione.
- JS actualizado: lee el value del input checked dentro de la qcard.
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rewrite_card_radio_block(html: str) -> str:
    """Para cada .qcard[data-q="QN"], asigna name='QN' a todos los radios internos."""
    # Matchea todo el bloque de una qcard
    card_re = re.compile(
        r'(<div class="qcard" data-q="([^"]+)"[^>]*>)(.*?)(</div>\s*</div>)',
        re.DOTALL,
    )

    def fix_card(m):
        open_tag, qid, body, close_tag = m.group(1), m.group(2), m.group(3), m.group(4)
        # Cambia todos los inputs sin name o con name="x" por name=qid
        body = re.sub(
            r'<input type="radio" value="([a-d])" hidden>',
            lambda mm: f'<input type="radio" name="{qid}" value="{mm.group(1)}" hidden>',
            body,
        )
        return open_tag + body + close_tag

    return card_re.sub(fix_card, html)


def rewrite_js_check(html: str) -> str:
    """Actualiza el JS para leer el input checked en lugar de buscar data-v del label."""
    # Varios archivos tienen patrones similares; hacemos match por bloques de script
    # y sustituimos la heurística de "sel.closest('.opt').dataset.v" por
    # "input[name=QN]:checked".value"
    script_re = re.compile(r'(<script[^>]*>)(.*?)(</script>)', re.DOTALL)

    def fix_script(m):
        open_tag, body, close_tag = m.group(1), m.group(2), m.group(3)
        # Reemplazo 1: en el handler 'change', leer el valor del input
        body = re.sub(
            r"const sel = e\.target\.closest\('\.opt'\); if \(!sel\) return;",
            "const qid = card.dataset.q;"
            " const selInput = card.querySelector(`input[name=\"${qid}\"]:checked`);"
            " if (!selInput) return;",
            body,
        )
        # Reemplazo 2: chosen = sel.dataset.v  -> chosen = selInput.value
        body = body.replace(
            "const chosen = sel.dataset.v;",
            "const chosen = selInput.value;",
        )
        # Reemplazo 3: sel.classList.add('sel'); -> selInput.parentElement.classList.add('sel');
        body = body.replace(
            "sel.classList.add('sel');",
            "selInput.parentElement.classList.add('sel');",
        )
        return open_tag + body + close_tag

    return script_re.sub(fix_script, html)


def fix_viewport(html: str) -> str:
    if 'name="viewport"' in html:
        return html
    return html.replace("<head>", '<head>\n<meta name="viewport" content="width=device-width, initial-scale=1">', 1)


def fix_chinos(html: str) -> str:
    return (html
            .replace("Jobs正常运行: están dentro del SLA.", "Jobs normales: están dentro del SLA.")
            .replace("Jobs正常运行.", "Jobs normales."))


def main():
    for slug in ["game.html", "quiz.html"]:
        p = ROOT / slug
        html = p.read_text(encoding="utf-8")
        html = fix_chinos(html)
        html = fix_viewport(html)
        html = rewrite_card_radio_block(html)
        html = rewrite_js_check(html)
        p.write_text(html, encoding="utf-8")
        print(f"rewrote {slug}")


if __name__ == "__main__":
    main()