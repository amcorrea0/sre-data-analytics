/* =========================================================================
   SETI · Registration helper
   ---------------------------------------------------------------------------
   API expuesta en window.__SETI__:
     .showBanner()           - muestra el banner si no esta registrado
     .openModal()            - abre el modal manualmente (botón "Registrarse")
     .closeModal()           - cierra el modal
     .submitRegistration(formData)  - persiste y notifica al endpoint
     .getSnapshot()          - snapshot del progreso actual (XP, badges, respuestas)
     .getRegistration()      - el registro persistido (o null)

   ENDPOINT ABSTRACTO
   Hoy: loguea a consola + guarda en localStorage. Cuando el facilitador publique
   en GitHub Pages, basta reemplazar SETI.endpoint por una llamada real a:

     POST https://api.github.com/repos/{owner}/{repo}/issues
     Authorization: Bearer {PAT}
     Body: { title: "[REG] <nombre> (<equipo>)", labels: ["registration"],
             body: <JSON con snapshot> }

   Ver README.md -> "Activar el registro en GitHub Issues".
   ========================================================================= */
(function () {
  'use strict';

  var STORAGE_REG = 'seti-sre-registration';
  var STORAGE_PROGRESS = 'seti-sre-progress';

  function loadRegistration() {
    try { return JSON.parse(localStorage.getItem(STORAGE_REG)) || null; }
    catch (e) { return null; }
  }
  function saveRegistration(reg) {
    localStorage.setItem(STORAGE_REG, JSON.stringify(reg));
  }
  function loadProgress() {
    try { return JSON.parse(localStorage.getItem(STORAGE_PROGRESS)) || {}; }
    catch (e) { return {}; }
  }
  function loadXP() {
    try { return JSON.parse(localStorage.getItem('seti-sre-game')) || {}; }
    catch (e) { return {}; }
  }

  /**
   * Snapshot del progreso actual para enviar al endpoint.
   * Combina: XP de game, badges desbloqueados en labs, respuestas de quiz.
   */
  function getSnapshot() {
    var labs = loadProgress();
    var x = loadXP();
    var quizzes = (function () {
      try {
        var all = {};
        for (var i = 0; i < localStorage.length; i++) {
          var k = localStorage.key(i);
          if (k && k.indexOf('seti-sre-quiz-') === 0) all[k] = JSON.parse(localStorage.getItem(k));
        }
        return all;
      } catch (e) { return {}; }
    })();
    return {
      labs_completed: Object.keys(labs).filter(function (k) { return labs[k]; }),
      badges_earned: Object.keys(labs).filter(function (k) { return labs[k]; }).length,
      missions_unlocked: Object.keys(x).filter(function (k) { return x[k]; }),
      quizzes: quizzes,
      captured_at: new Date().toISOString(),
    };
  }

  /**
   * Hook de envío. Hoy: log. Mañana: GitHub Issues.
   * Devuelve Promise<{ok, message}>.
   */
  function submitRegistration(payload) {
    payload = payload || {};
    var enriched = {
      name: payload.name,
      email: payload.email,
      team: payload.team || null,
      consent: !!payload.consent,
      source: payload.source || 'unknown',
      snapshot: payload.snapshot || getSnapshot(),
    };

    // persistir local siempre (no esperamos el server)
    enriched.registered_at = new Date().toISOString();
    saveRegistration(enriched);

    return new Promise(function (resolve) {
      // Enviar al Worker de Cloudflare (KV store)
      fetch('https://seti-registros.amcorrea0.workers.dev/registro', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(enriched),
        keepalive: true,
      })
        .then(function (r) { return r.json().then(function (j) {
          resolve({ ok: r.ok, message: r.ok ? ('Registro guardado (#' + (j.id || '') + ')') : ('Error del servidor: ' + (j.error || '')) });
        }); })
        .catch(function (e) {
          // Fallo de red: el registro queda local, lo informamos
          resolve({ ok: true, message: 'Guardado localmente (sin red: ' + String(e) + ')' });
        });
    });
  }

  // === UI ============================================================
  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === 'class') node.className = attrs[k];
      else if (k === 'html') node.innerHTML = attrs[k];
      else if (k.indexOf('on') === 0) node.addEventListener(k.slice(2), attrs[k]);
      else node.setAttribute(k, attrs[k]);
    }
    if (children) {
      (Array.isArray(children) ? children : [children]).forEach(function (c) {
        if (c == null) return;
        node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
      });
    }
    return node;
  }

  function ensureUI() {
    // banner
    if (!document.getElementById('reg-banner')) {
      var banner = el('div', { id: 'reg-banner', class: 'reg-banner', role: 'region' }, [
        el('span', { class: 'pill' }, 'Team'),
        el('span', { class: 'text' }, el('strong', null, [
          document.createTextNode('\u00bfNuevo en el programa? '),
        ]).appendChild ? null : null),
        el('button', { class: 'reg-cta', type: 'button', onclick: openModal }, 'Registrarme'),
        el('button', { class: 'reg-close', type: 'button', 'aria-label': 'Cerrar', onclick: hideBanner }, '\u00d7'),
      ]);
      // fix the text node construction
      var text = el('span', { class: 'text' });
      text.innerHTML = 'Hola equipo, por favor <strong>registren su asistencia</strong> para hacer seguimiento.';
      // easier: rebuild banner cleanly
      banner = el('div', { id: 'reg-banner', class: 'reg-banner', role: 'region' }, [
        el('span', { class: 'pill' }, 'Team'),
        text,
        el('button', { class: 'reg-cta', type: 'button', onclick: openModal }, 'Registrarme'),
        el('button', { class: 'reg-close', type: 'button', 'aria-label': 'Cerrar', onclick: hideBanner }, '\u00d7'),
      ]);
      document.body.insertBefore(banner, document.body.firstChild);
      document.body.classList.add('has-reg-banner');
    }

    // modal
    if (!document.getElementById('reg-overlay')) {
      var overlay = el('div', { id: 'reg-overlay', class: 'reg-overlay', role: 'dialog', 'aria-modal': 'true' });
      var modal = el('div', { class: 'reg-modal' });
      // head
      var head = el('div', { class: 'reg-modal-head' }, [
        el('button', { class: 'close', type: 'button', 'aria-label': 'Cerrar', onclick: closeModal }, '\u00d7'),
        el('h2', null, 'Bienvenido al programa'),
        el('p', null, 'Reg\u00edstrate para que podamos dar seguimiento a tu progreso.'),
      ]);
      // body
      var body = el('div', { class: 'reg-modal-body' });
      body.appendChild(buildField('name', 'Nombre', 'text', true, 'Tu nombre completo.'));
      body.appendChild(buildField('email', 'Email corporativo', 'email', true, 'Lo usamos solo para enviarte el reporte del entrenamiento.'));
      body.appendChild(buildField('team', 'Equipo (opcional)', 'text', false, 'payments, identity, platform, frontend, etc.'));
      var consentLabel = el('label', { class: 'reg-check' });
      var consentCb = el('input', { type: 'checkbox', id: 'reg-consent', required: 'required' });
      consentLabel.appendChild(consentCb);
      consentLabel.appendChild(el('span', { html: 'Acepto enviar mi progreso (XP, badges, respuestas) al repositorio para an\u00e1lisis del equipo.' }));
      var checks = el('div', { class: 'reg-checks' }, [consentLabel]);
      body.appendChild(checks);

      var status = el('div', { id: 'reg-status', class: 'reg-status' });

      var actions = el('div', { class: 'reg-actions' }, [
        el('button', { type: 'button', class: 'ghost', onclick: closeModal }, 'Cancelar'),
        el('button', { type: 'button', id: 'reg-submit', class: 'primary', onclick: onSubmit }, 'Registrarme'),
      ]);
      modal.appendChild(head);
      modal.appendChild(body);
      modal.appendChild(status);
      modal.appendChild(actions);
      overlay.appendChild(modal);
      overlay.addEventListener('click', function (e) { if (e.target === overlay) closeModal(); });
      document.body.appendChild(overlay);
    }
  }

  function buildField(id, label, type, required, hint) {
    var wrap = el('div', { class: 'reg-field' });
    var lbl = el('label', { for: 'reg-' + id });
    lbl.appendChild(document.createTextNode(label));
    if (required) lbl.appendChild(el('span', { class: 'req' }, ' *'));
    wrap.appendChild(lbl);
    var input = el('input', { id: 'reg-' + id, name: id, type: type, required: required ? 'required' : null });
    wrap.appendChild(input);
    if (hint) wrap.appendChild(el('div', { class: 'hint' }, hint));
    return wrap;
  }

  function openModal() {
    ensureUI();
    var overlay = document.getElementById('reg-overlay');
    overlay.classList.add('open');
    setTimeout(function () {
      var f = document.getElementById('reg-name');
      if (f) f.focus();
    }, 50);
  }
  function closeModal() {
    var overlay = document.getElementById('reg-overlay');
    if (overlay) overlay.classList.remove('open');
    var s = document.getElementById('reg-status');
    if (s) { s.className = 'reg-status'; s.textContent = ''; }
    document.querySelectorAll('.reg-field.invalid').forEach(function (n) { n.classList.remove('invalid'); });
  }
  function hideBanner() {
    var banner = document.getElementById('reg-banner');
    if (banner) banner.style.display = 'none';
    document.body.classList.remove('has-reg-banner');
    // recordar que se cerro (no que se registro)
    try { sessionStorage.setItem('seti-sre-banner-dismissed', '1'); } catch (e) {}
  }

  function onSubmit() {
    var name = (document.getElementById('reg-name').value || '').trim();
    var email = (document.getElementById('reg-email').value || '').trim();
    var team = (document.getElementById('reg-team').value || '').trim();
    var consent = document.getElementById('reg-consent').checked;
    var statusEl = document.getElementById('reg-status');
    var submitBtn = document.getElementById('reg-submit');

    // reset
    document.querySelectorAll('.reg-field.invalid').forEach(function (n) { n.classList.remove('invalid'); });

    var ok = true;
    if (!name) { document.getElementById('reg-name').parentElement.classList.add('invalid'); ok = false; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      document.getElementById('reg-email').parentElement.classList.add('invalid'); ok = false;
    }
    if (!consent) ok = false;

    if (!ok) {
      statusEl.className = 'reg-status err';
      statusEl.textContent = 'Revisa los campos y marca la casilla de consentimiento.';
      return;
    }

    submitBtn.disabled = true;
    statusEl.className = 'reg-status';
    statusEl.textContent = 'Enviando...';

    var source = (location.pathname.split('/').pop() || 'index.html');
    submitRegistration({
      name: name, email: email, team: team, consent: consent, source: source,
      snapshot: getSnapshot(),
    }).then(function (res) {
      submitBtn.disabled = false;
      if (res.ok) {
        statusEl.className = 'reg-status ok';
        statusEl.textContent = res.message || '\u00a1Listo! Gracias por registrarte.';
        hideBanner();
        setTimeout(closeModal, 1200);
      } else {
        statusEl.className = 'reg-status err';
        statusEl.textContent = res.message || 'No se pudo enviar el registro.';
      }
    });
  }

  function showBanner() {
    ensureUI();
    if (loadRegistration()) return; // ya registrado: no banner
    try { if (sessionStorage.getItem('seti-sre-banner-dismissed')) return; } catch (e) {}
    var banner = document.getElementById('reg-banner');
    if (banner) banner.style.display = '';
  }

  // API publica
  window.__SETI__ = {
    showBanner: showBanner,
    openModal: openModal,
    closeModal: closeModal,
    hideBanner: hideBanner,
    submitRegistration: submitRegistration,
    getSnapshot: getSnapshot,
    getRegistration: loadRegistration,
  };

  // auto-init
  document.addEventListener('DOMContentLoaded', function () {
    ensureUI();
    // si ya hay registro, ocultar banner
    if (loadRegistration()) hideBanner();
  });
})();
