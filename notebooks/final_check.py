import re
from pathlib import Path

# final_check
ROOT = Path(".")
problems = []
checks = []

LABS = ["lab1_observabilidad", "lab2_automatizacion",
        "lab3_requerimientos", "lab4_ejecutivo"]

for slug in LABS:
    p = ROOT / "html" / f"{slug}.html"
    t = p.read_text(encoding="utf-8")
    bad = re.findall(r'<h[1-3][^>]*>[^<]*id="[^"]+"', t)
    if bad:
        problems.append(f"{slug}: {len(bad)} headings con id='X' literal")
    else:
        checks.append(f"{slug}: sin id='X' literal en headings")
    tildes = re.findall(r'[áéíóúñÁÉÍÓÚÑ—¿¡]', t)
    if len(tildes) < 20:
        problems.append(f"{slug}: solo {len(tildes)} tildes/acento")
    else:
        checks.append(f"{slug}: {len(tildes)} tildes/acento preservadas")
    h_ids = re.findall(r'<h[1-3][^>]*\bid="(h\d+)"', t)
    if len(h_ids) < 5:
        problems.append(f"{slug}: solo {len(h_ids)} anchors hN")
    else:
        checks.append(f"{slug}: {len(h_ids)} anchors hN")

# 0 broken refs
all_public = (
    ["index.html", "game.html", "quiz.html"]
    + [f"html/lab{n}_{s}.html" for n, s in [
        (1, "observabilidad"), (2, "automatizacion"),
        (3, "requerimientos"), (4, "ejecutivo")]]
)
problems2 = []
for f in all_public:
    p = ROOT / f
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    base = p.parent
    for m in re.finditer(r'(?:href|src)="([^"]+)"', t):
        href = m.group(1)
        if href.startswith(("http", "#", "mailto:", "data:")):
            continue
        parts = Path(href).parts
        cur = base
        for x in parts:
            if x == "..":
                cur = cur.parent
            elif x in (".", ""):
                pass
            else:
                cur = cur / x
        if not cur.exists():
            problems2.append((f, href))
if problems2:
    problems.append(f"{len(problems2)} broken refs")
    for f, h in problems2[:10]:
        problems.append(f"  {f}: {h}")
else:
    checks.append(f"0 broken refs en {len(all_public)} paginas publicas")

# Quiz radios
t = (ROOT / "quiz.html").read_text(encoding="utf-8")
names = re.findall(r'<input type="radio" name="([^"]+)"', t)
if len(names) == 36 and len(set(names)) == 9:
    checks.append(f"quiz.html: 36 radios, 9 names unicos (9 preguntas)")
else:
    problems.append(f"quiz.html: {len(names)} radios, {len(set(names))} names unicos")

print("=== CHECKS OK ===")
for c in checks:
    print(f"  [OK] {c}")
print()
if problems:
    print(f"ERRORES ({len(problems)}):")
    for p in problems:
        print(f"  [ERR] {p}")
else:
    print("SIN ERRORES.")
import sys
sys.exit(0 if not problems else 1)