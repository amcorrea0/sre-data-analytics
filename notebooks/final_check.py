"""Validacion post-fix bug del h2.

Checklist:
- 0 headings con id="..." literal en los 4 lab HTMLs
- Headings tienen texto legible (no solo 'id="X"')
- TOC anchors apuntan a IDs validos
- 0 broken refs
- Caracteres con tilde presentes
"""
import re
from pathlib import Path
import sys

ROOT = Path(".")
problems = []
ok = []

LABS = ["lab1_observabilidad", "lab2_automatizacion",
        "lab3_requerimientos", "lab4_ejecutivo"]

for slug in LABS:
    p = ROOT / "html" / f"{slug}.html"
    t = p.read_text(encoding="utf-8")

    # 1. Bug: id="..." como texto literal dentro del h
    bad = re.findall(r'<h[1-3][^>]*>[^<]*id="[^"]+"', t)
    if bad:
        problems.append(f"{slug}: {len(bad)} headings con id='X' literal")
    else:
        ok.append(f"{slug}: sin id='X' literal en headings")

    # 2. Tildes y caracteres no-ASCII presentes
    tildes = re.findall(r'[áéíóúñÁÉÍÓÚÑ—¿¡]', t)
    if len(tildes) < 20:
        problems.append(f"{slug}: solo {len(tildes)} tildes/acento")
    else:
        ok.append(f"{slug}: {len(tildes)} tildes/acento preservadas")

    # 3. Todos los h2/h3 tienen id limpio 'hN'
    h_ids = re.findall(r'<h[1-3][^>]*\bid="(h\d+)"', t)
    if len(h_ids) < 5:
        problems.append(f"{slug}: solo {len(h_ids)} anchors hN")
    else:
        ok.append(f"{slug}: {len(h_ids)} anchors hN")

    # 4. TOC apunta a anchors validos
    toc_hrefs = re.findall(r'<div class="toc">.*?</div>', t, re.DOTALL)
    if toc_hrefs:
        toc = toc_hrefs[0]
        toc_links = re.findall(r'href="(#h\d+)"', toc)
        missing = [l for l in toc_links if l not in [f'#{i}' for i in h_ids]]
        if missing:
            problems.append(f"{slug}: TOC apunta a {missing} que no existen")
        else:
            ok.append(f"{slug}: TOC con {len(toc_links)} enlaces, todos validos")

# 5. 0 broken refs (las paginas publicas)
problems2 = []
all_public = (["index.html", "game.html", "quiz.html"]
              + [f"html/lab{n}_{s}.html" for n, s in [(1,"observabilidad"),(2,"automatizacion"),(3,"requerimientos"),(4,"ejecutivo")]])
for f in all_public:
    p = ROOT / f
    if not p.exists(): continue
    t = p.read_text(encoding="utf-8")
    base = p.parent
    for m in re.finditer(r'(?:href|src)="([^"]+)"', t):
        href = m.group(1)
        if href.startswith(("http", "#", "mailto:", "data:")):
            continue
        parts = Path(href).parts
        cur = base
        for x in parts:
            if x == "..": cur = cur.parent
            elif x in (".", ""): pass
            else: cur = cur / x
        if not cur.exists():
            problems2.append((f, href))
if problems2:
    problems.append(f"{len(problems2)} broken refs")
else:
    ok.append(f"0 broken refs en {len(all_public)} paginas publicas")

print("=" * 70)
print("CHECKS OK")
print("=" * 70)
for c in ok:
    print(f"  [OK] {c}")
print()
if problems:
    print(f"ERRORES ({len(problems)}):")
    for p in problems:
        print(f"  [ERR] {p}")
    sys.exit(1)
else:
    print("SIN ERRORES. Bug de tildes resuelto.")
    sys.exit(0)