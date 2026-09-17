"""Inyecta el banner + modal de registro en los root files y persiste
respuestas individuales en quiz/game.

- Anade <link rel="stylesheet" href="assets/registration.css"> + <script
  src="assets/registration.js"> a: index.html, game.html, quiz.html,
  STORY.html, FACILITATOR.html.
- Inyecta un boton 'Registrarse' en la nav.
- Parchea quiz.html y game.html para guardar cada respuesta (correcta/incorrecta)
  en localStorage con key 'seti-sre-quiz-{source}-{qid}', de modo que
  getSnapshot() en registration.js los recoja.
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CSS = '<link rel="stylesheet" href="assets/registration.css">'
JS = '<script src="assets/registration.js" defer></script>'

ROOT_FILES = ["index.html", "game.html", "quiz.html", "STORY.html", "FACILITATOR.html"]


def add_assets(html: str) -> str:
    if "registration.css" not in html:
        # anadir css y js antes de </head>
        html = html.replace("</head>", f"  {CSS}\n</head>", 1)
    if "registration.js" not in html:
        # anadir el script antes de </body>
        html = html.replace("</body>", f"  {JS}\n</body>", 1)
    return html


def add_nav_button(html: str) -> str:
    """Anade 'Registrarse' al final del bloque .links de la nav (si existe)."""
    if "__SETI_OPEN_REG__" in html:
        return html
    # busca el ultimo </a> antes de </div></nav>
    btns = (
        '    <a class="cta reg-nav-btn" href="#" '
        'onclick="event.preventDefault();window.__SETI__.openModal();" '
        'id="__SETI_OPEN_REG__">\u00b7 Registrarme</a>\n'
    )
    # Insertar antes del cierre del .nav (</div></nav>)
    if "</nav>" in html:
        idx = html.rfind("</nav>")
        # Encontrar el cierre del wrap (</div>) dentro de nav
        # Estrategia simple: insertar antes del </nav> a nivel del </div> previo
        # Localizar el wrap de nav (ultimo </div></nav> tras un .links)
        # Simplificamos: pondremos el boton justo antes de </nav>
        html = html[:idx] + btns + html[idx:]
    return html


for f in ROOT_FILES:
    p = ROOT / f
    if not p.exists():
        print(f"skip {f} (no existe)")
        continue
    html = p.read_text(encoding="utf-8")
    new_html = add_assets(html)
    new_html = add_nav_button(new_html)
    if new_html != html:
        p.write_text(new_html, encoding="utf-8")
        print(f"updated {f}")


# ===========================================================================
# Persistir respuestas individuales en quiz.html
# ===========================================================================
QUIZ_PATCH = """
<script>
(function(){
  if (!window.__SETI__) return;
  var KEY = 'seti-sre-quiz-quiz';
  var ans = {};
  try { ans = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch(e){}
  function save(){
    try { localStorage.setItem(KEY, JSON.stringify(ans)); } catch(e){}
  }
  document.querySelectorAll('.qcard[data-q]').forEach(function(card){
    card.addEventListener('change', function(e){
      var qid = card.dataset.q;
      var inp = card.querySelector('input[name="'+qid+'"]:checked');
      if (!inp) return;
      ans[qid] = {
        chosen: inp.value,
        correct: card.dataset.correct,
        correct_chosen: inp.value === card.dataset.correct,
        at: new Date().toISOString()
      };
      save();
    });
  });
  // re-pintar respuestas previas al cargar
  document.querySelectorAll('.qcard[data-q]').forEach(function(card){
    var qid = card.dataset.q; var a = ans[qid]; if (!a) return;
    var inp = card.querySelector('input[name="'+qid+'"][value="'+a.chosen+'"]');
    if (inp) { inp.checked = true; inp.parentElement.classList.add(a.correct_chosen ? 'right' : 'wrong'); }
    var corr = card.querySelector('.opt[data-v="'+a.correct+'"]');
    if (corr) corr.classList.add('right');
  });
})();
</script>
"""

GAME_PATCH = """
<script>
(function(){
  if (!window.__SETI__) return;
  var KEY = 'seti-sre-quiz-game';
  var ans = {};
  try { ans = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch(e){}
  function save(){
    try { localStorage.setItem(KEY, JSON.stringify(ans)); } catch(e){}
  }
  document.querySelectorAll('.qcard[data-q]').forEach(function(card){
    card.addEventListener('change', function(e){
      var qid = card.dataset.q;
      var inp = card.querySelector('input[name="'+qid+'"]:checked');
      if (!inp) return;
      ans[qid] = {
        chosen: inp.value,
        correct: card.dataset.correct,
        correct_chosen: inp.value === card.dataset.correct,
        at: new Date().toISOString()
      };
      save();
    });
  });
  document.querySelectorAll('.qcard[data-q]').forEach(function(card){
    var qid = card.dataset.q; var a = ans[qid]; if (!a) return;
    var inp = card.querySelector('input[name="'+qid+'"][value="'+a.chosen+'"]');
    if (inp) { inp.checked = true; inp.parentElement.classList.add(a.correct_chosen ? 'right' : 'wrong'); }
    var corr = card.querySelector('.opt[data-v="'+a.correct+'"]');
    if (corr) corr.classList.add('right');
  });
  // tambien guardar misiones desbloqueadas
  var MK = 'seti-sre-game-persistent';
  try {
    var s = JSON.parse(localStorage.getItem(MK) || '{}');
    document.querySelectorAll('[data-toggle]').forEach(function(b){
      var id = b.dataset.toggle;
      if (s[id]) {
        var gate = document.getElementById('gate-'+id);
        if (gate) { gate.classList.add('unlocked'); gate.innerHTML = '<p><strong>✓ Lab completado.</strong> Responde para ganar XP.</p>'; }
        var qs = document.getElementById('qs-'+id);
        if (qs) qs.hidden = false;
        var st = document.getElementById(id+'-status');
        if (st) { st.textContent = 'Desbloqueado'; st.classList.remove('ghost'); st.classList.add('red'); }
      }
    });
  } catch(e){}
})();
</script>
"""

for slug, patch, key in [
    ("quiz.html", QUIZ_PATCH, "seti-sre-quiz-quiz"),
    ("game.html", GAME_PATCH, "seti-sre-quiz-game"),
]:
    p = ROOT / slug
    html = p.read_text(encoding="utf-8")
    if key in html:
        print(f"{slug}: ya tiene persistencia")
        continue
    # inyectar antes de </body>
    html = html.replace("</body>", patch + "\n</body>", 1)
    p.write_text(html, encoding="utf-8")
    print(f"patched {slug}")

print("done")