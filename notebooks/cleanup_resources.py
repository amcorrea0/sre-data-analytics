import re
from pathlib import Path

p = Path("index.html")
t = p.read_text(encoding="utf-8")

# Quitar las cards de Story y Facilitador del bloque Recursos
# Patron: cada card esta entre </div>\n      </div> y empieza con <div class="learn-card">\n        <h3>Story</h3>
t = re.sub(
    r'\s*<div class="learn-card">\s*<h3>Story</h3>.*?</div>\s*</div>\s*</div>',
    '\n      </div>',
    t,
    flags=re.DOTALL,
)
t = re.sub(
    r'\s*<div class="learn-card">\s*<h3>Facilitador</h3>.*?</div>\s*</div>\s*</div>',
    '\n      </div>',
    t,
    flags=re.DOTALL,
)

# Si quedo solo Game dentro de lab-grid, no tiene sentido la seccion entera
# (sera una grid con un solo card). Mejor cambiar titulo y contenido.
t = re.sub(
    r'<h2 class="section-title">Recursos para el equipo</h2>',
    '<h2 class="section-title">Siguiente paso</h2>',
    t,
)
# Reemplazar el card de Game restante por un texto de aliento
t = re.sub(
    r'<div class="lab-grid">\s*<div class="learn-card">\s*<h3>Game</h3>.*?</p>\s*</div>\s*</div>',
    '<p style="max-width:720px; color:var(--grey-2);">Ya tienes todo para empezar: <a href="game.html">Game</a> para jugar, <a href="quiz.html">Quiz</a> para medir aprendizaje. Si tienes dudas, habla con tu facilitador.</p>',
    t,
    flags=re.DOTALL,
)

p.write_text(t, encoding="utf-8")
print("cleaned index.html")