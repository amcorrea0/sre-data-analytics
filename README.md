# SETI · SRE Data Analytics — Programa (60 min)

Hands-on labs para SREs junior con datos de **observabilidad, automatización y tickets**.
**Branding SETI** (blanco · grises · rojos), XP, badges, niveles y rúbrica.
**Registro no bloqueante** del equipo + **panel paso a paso** con control de errores.
Inspirado en el formato de [lab10](https://app.lab10.ai/aprende).

## Páginas principales

| Página | Para quién | Descripción |
|--------|-----------|-------------|
| [**index.html**](index.html) | SRE | Inicio, galería de misiones, progreso XP propio |
| [**game.html**](game.html) | SRE | Preguntas en línea *gated* por lab (recomendado durante la sesión) |
| [**quiz.html**](quiz.html) | SRE | Quiz final libre con XP y rúbrica |
| [STORY.html](STORY.html) | Facilitador | Arco narrativo de los 60 min |
| [FACILITATOR.html](FACILITATOR.html) | Facilitador | Agenda cronometrada + prompts de discusión |
| [**panel.html**](panel.html) | Facilitador | **Panel paso a paso con control de errores** |
| [labs/lab-0X-*/guide.html](labs/) | SRE | Guías del estudiante (HTML renderizado, mismo branding SETI) |

## 🎯 Panel del facilitador (lo nuevo)

[`panel.html`](panel.html) está pensado para abrirlo **antes de la sesión y tenerlo en una pestaña** mientras conduces:

- **10 pasos numerados** (0..9).
- Cada paso tiene 4 bloques: **qué hago**, **qué digo al equipo**, **dónde mirar**, **qué hago si falla (Plan B)**.
- El progreso se guarda en tu navegador, así que puedes cerrar y volver y sigue ahí.
- El paso 9 reúne todos los planes B en un solo lugar (Jupyter falla, sitio caído, sin registro, sin tiempo).

### Cómo usarlo
1. Abre `panel.html` en una pestaña del presentador.
2. Sigue los pasos en orden. Marca cada checkbox cuando lo completes.
3. Si algo falla, lee el cuadro rojo del paso o salta al paso 9.

## 🕹️ XP y niveles

| Nivel | XP | Título |
|-------|----|--------|
| 0 | 0 | Aprendiz |
| 1 | 100 | Outlier Hunter |
| 2 | 220 | MTTR Specialist |
| 3 | 380 | Demand Wrangler |
| 4 | 580+ | Storyteller (producción) |

XP y badges se guardan en `localStorage` (no se envían a ningún servidor todavía — ver abajo).

## 📝 Registro del equipo

Cada visitante ve un **banner rojo pegajoso** en la parte superior con un botón "Registrarme".
El banner:

- **No es bloqueante** — si el SRE no quiere dejar email, lo cierra con la X y sigue.
- Captura **nombre, email, equipo (opcional)** y un consentimiento explícito.
- Persiste en `localStorage` (`seti-sre-registration`).
- Recolecta en cada submit un **snapshot del progreso** (XP, badges, misiones desbloqueadas, respuestas por pregunta con timestamp).

### Hoja de ruta para activar el envío a GitHub Issues

El endpoint real está **deshabilitado** (placeholder que loguea a consola) para que puedas publicar el repo sin secretos. Cuando estés listo:

1. Edita `assets/registration.js`, función `submitRegistration` (busca el comentario `=== HOOK PARA FUTURO ===`).
2. Reemplaza el bloque placeholder por una llamada a `fetch` con un PAT y el endpoint `https://api.github.com/repos/{owner}/{repo}/issues`.
3. Body sugerido del Issue:

   ```
   title:  "[REG] <nombre> (<equipo>)"
   labels: ["registration"]
   body:   ```json
           { "name": "...", "email": "...", "team": "...",
             "snapshot": { ... capturado por getSnapshot() ... } }
           ```
   ```

4. Filtra los registros con `is:issue label:registration` en GitHub.

> **Importante:** el PAT vive en el navegador del facilitador, no se commitea. Para sesiones donde muchos facilitadores registran SREs, despliega un proxy serverless (Cloudflare Worker, Vercel Function) que reciba el payload y cree el Issue desde el servidor. Es trivial de implementar.

## 🧪 Cómo extraer los registros manualmente (modo actual)

En la consola del navegador del facilitador (F12):
```js
JSON.stringify(window.__SETI__.getRegistration(), null, 2);
JSON.stringify(window.__SETI__.getSnapshot(), null, 2);
```
Copia el JSON al portapapeles y pégalo en tu hoja de seguimiento.

## 🚀 Sincronizar con tu GitHub personal — paso a paso

### 1 · Crear el repo en GitHub

1. Entra a **https://github.com/new** autenticado con tu cuenta personal.
2. **Repository name**: `sre-data-analytics` (o el que prefieras).
3. **Visibilidad**: `Public` (para que GitHub Pages sirva gratuito).
4. **NO** inicialices con README/LICENSE/.gitignore — este repo ya los trae.
5. Click en **Create repository**.
6. Copia la URL que aparece: `https://github.com/<tu-usuario>/sre-data-analytics.git`.

### 2 · Conectar y subir desde tu laptop

Abre **PowerShell** en la raíz del proyecto y ejecuta (sustituye `<tu-usuario>`):

```powershell
cd "Documents\amc-builder\sre-data-analytics"

# 1. Inicializar git (solo la primera vez)
git init

# 2. Conectar con tu repo remoto
git remote add origin https://github.com/<tu-usuario>/sre-data-analytics.git

# 3. Identidad git (la primera vez, una sola)
git config user.name "Tu Nombre"
git config user.email "tu@email.com"

# 4. Ver qué se va a subir (debe incluir data/*.csv y html/*)
git status

# 5. Primer commit
git add .
git commit -m "SETI · SRE Data Analytics — v1.0"

# 6. Subir a GitHub (te pedira login)
git push -u origin main
```

> **GitHub ya no acepta contraseña en `git push`.** Si te la pide,
> abre **https://github.com/settings/tokens** → **Generate new token (classic)**
> → marca `repo` → copia el token → pégalo cuando lo pida. Guárdalo, no lo
> podrás ver de nuevo.
>
> **Alternativa sin token:** GitHub Desktop
> (https://desktop.github.com) — añade el repo con un click y maneja la auth.

### 3 · Activar GitHub Pages

1. En tu repo en GitHub: **Settings → Pages** (menú izquierdo).
2. **Source**: `Deploy from a branch`.
3. **Branch**: `main`, carpeta `/ (root)`.
4. Click **Save**.
5. Espera 1–2 min. Verás: `✅ Your site is live at https://<tu-usuario>.github.io/sre-data-analytics/`.

### 4 · Compartir al equipo

Comparte esta única URL:
```
https://<tu-usuario>.github.io/sre-data-analytics/index.html
```

El equipo verá: index con hero, game con misiones, quiz, 4 labs, 18 figuras, banner de registro. **Nada** de `/facilitator/` es accesible desde el index.

### 5 · Tu flujo local (lo que no subes pero sí usas)

En tu laptop, abre 3 pestañas:

| Para qué | URL local |
|----------|-----------|
| Sesión paso a paso | `panel.html` |
| Arco narrativo | `STORY.html` |
| Agenda cronometrada | `FACILITATOR.html` |

Sirve el directorio completo y abre `http://localhost:8000/facilitator/panel.html`:
```powershell
& ".\.venv\Scripts\python.exe" -m http.server 8000
```

### Lo que se commitea

- ✅ `data/*.csv` — los 5 datasets (≈76 MB)
- ✅ `html/lab*.html` + 18 figuras PNG
- ✅ `assets/*` (CSS + JS)
- ✅ `notebooks/*.py` + los 4 `.ipynb`
- ✅ `facilitator/*.html` + `.md` (publicados pero NO enlazados desde el index)
- ✅ `labs/*/guide.html` (guías renderizadas)
- ❌ `.venv/` (regenerable)
- ❌ `__pycache__/`, `*.pyc`
- ❌ `data/_generate.log`

## ✅ Validación

Corre en la raíz del proyecto:
```bash
python notebooks/final_check.py
```
Verifica: 0 referencias rotas, radios correctos, lang=es, tildes, guías HTML renderizadas, CSS cubre nbconvert.

## 📋 Estructura

```
sre-data-analytics/
├── index.html, game.html, quiz.html
├── panel.html                # <- nuevo: panel paso a paso para el facilitador
├── STORY.html, FACILITATOR.html
├── assets/
│   ├── style.css             # branding SETI + reglas nbconvert
│   ├── registration.css      # banner + modal
│   └── registration.js       # API + tracking + hook para GitHub Issues
├── html/lab{1..4}_*.html     # 4 notebooks renderizados con header SETI
├── html/lab{1..4}_fig*.png   # 18 figuras
├── labs/lab-0X-*/guide.html  # guías del estudiante
├── notebooks/
│   ├── generate_data.py
│   ├── build_notebooks.py
│   ├── decorate_lab_html.py
│   ├── normalize_and_render.py
│   ├── inject_registration.py
│   └── final_check.py        # <- nuevo: valida todo end-to-end
└── *.md                      # README, STORY, FACILITATOR (md originales)