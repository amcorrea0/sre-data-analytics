# Runbook: Publicar el SETI SRE training en GitLab interno de tu empresa

> **Audiencia:** Andrés (entrega) + equipo infra de la compañía (valida).
> **Tiempo total:** 30 min si Pages funciona, 1h si hay que configurar.

---

## 🎯 Qué vas a lograr

Servir el sitio SETI SRE training en:

```
http(s)://<gitlab-pages-url>/<grupo>/sre-data-analytics/
```

Accesible solo desde la red/VPN de tu empresa.

---

## PASO 1 — Validar que el GitLab interno existe y responde (5 min)

**Quién:** Andrés.

**Acción:**

```powershell
# En PowerShell, desde la raíz del proyecto:
& ".\.venv\Scripts\python.exe" notebooks\validate_gitlab.py https://gitlab.tu-empresa.com

# Si tu GitLab requiere token (recomendado si usas 2FA):
$env:GITLAB_TOKEN = "glpat-XXXXXXXXXXXX"
& ".\.venv\Scripts\python.exe" notebooks\validate_gitlab.py https://gitlab.tu-empresa.com $env:GITLAB_TOKEN
```

**Resultado esperado:**

```
Validando GitLab: https://gitlab.tu-empresa.com
============================================================

[1/3] Acceso al servidor GitLab
-----------------------------
  [OK]   GET /-/health                       -> 200 (15 bytes)
  [OK]   GET /users/sign_in                  -> 200 (12345 bytes)

[2/3] API de GitLab
-----------------------------
  [OK]   GET /api/v4/version                 -> 200 (...)
     Version GitLab: 17.5.1
     Revision: abc123

[3/3] Pages habilitado (puede requerir permisos admin)
```

Si ves [OK] arriba, el GitLab responde. **Pídele al equipo infra el paso 2** (validar Pages al nivel de la instancia).

---

## PASO 2 — Validar que Pages está habilitado (10 min)

**Quién:** Equipo de infra (con permisos admin en GitLab).

**Acción 1: verificar al nivel instancia**

Que el admin abra: `https://gitlab.tu-empresa.com/admin/pages`

- ✅ Si ve "Pages is enabled" con un dominio configurado → **Pages funciona**. Pasa al paso 3.
- ❌ Si ve "Pages is not enabled" o un error → el admin debe:

```bash
# En el servidor GitLab (omnibus)
sudo nano /etc/gitlab/gitlab.rb

# Agregar o descomentar:
external_url 'https://gitlab.tu-empresa.com'
pages_external_url 'https://pages.tu-empresa.com'  # o el subdominio que quieran

# (Opcional) configurar SSL wildcard con Let's Encrypt:
letsencrypt['enable'] = true

# Aplicar (tarda 1-3 min)
sudo gitlab-ctl reconfigure
sudo gitlab-ctl restart
```

**Acción 2: que el admin te confirme:**
1. ¿Cuál es el dominio de Pages? (ej: `https://pages.tu-empresa.com`)
2. ¿Los proyectos nuevos pueden activar Pages por defecto?

> Si el admin dice que Pages **no se puede** activar ahora mismo (no tiene tiempo, infra saturada, etc.), **sáltate al PLAN B** al final de este documento.

---

## PASO 3 — Crear el proyecto en GitLab (3 min)

**Quién:** Andrés.

**Acción:**

1. En GitLab → **New project** → **Create blank project**.
2. Configurar:
   - **Project name:** `sre-data-analytics`
   - **Visibility Level:** **Private** (Pages igual sirve aunque el proyecto sea privado)
   - **Initialize with a README:** NO
3. Click **Create project**.
4. Te muestra una pantalla con la URL del repo, ej: `git@gitlab.tu-empresa.com:andres-correa/sre-data-analytics.git`.

---

## PASO 4 — Subir el código al GitLab interno (5 min)

**Quién:** Andrés.

**Acción:**

```powershell
Set-Location "Documents\amc-builder\sre-data-analytics"

# Agregar GitLab como remote (mantenemos GitHub tambien si quieres)
git remote add gitlab https://gitlab.tu-empresa.com/andres-correa/sre-data-analytics.git

# Empujar
git push -u gitlab main
```

**Resultado esperado:**

```
Enumerating objects: 65, done.
Counting objects: 100% (65/65), done.
...
To https://gitlab.tu-empresa.com/andres-correa/sre-data-analytics.git
 * [new branch]      main -> main
branch 'main' set up to track 'gitlab/main'.
```

Si pide credenciales: usa **Personal Access Token** (Settings → Access Tokens → `write_repository`).

---

## PASO 5 — Esperar el deploy automático (1-3 min)

**Quién:** Andrés.

**Acción:**

1. En GitLab, ve a tu proyecto.
2. Menu lateral izquierdo → **Build → Pipelines** o **CI/CD → Pipelines**.
3. Verás un pipeline `pages` corriendo (amarillo) o terminado (verde).
4. Click en él para ver el log si quieres verificar.

---

## PASO 6 — Confirmar el sitio (2 min)

**Quién:** Andrés.

**Acción:**

En el menu lateral izquierdo del proyecto, busca **Deploy → Pages**.

Verás arriba la URL:

```
Your pages are served under: https://pages.tu-empresa.com/andres-correa/sre-data-analytics/
```

Abre:

> https://pages.tu-empresa.com/andres-correa/sre-data-analytics/index.html

Debería verse el sitio rojo/blanco/negro con el banner de registro.

**Una vez confirmado:**

| URL | Quién la usa |
|-----|--------------|
| `.../index.html` | Equipo |
| `.../game.html` | Equipo |
| `.../quiz.html` | Equipo |
| `.../html/lab1_observabilidad.html` | Equipo |
| `.../facilitator/panel.html` | Solo tú |
| `.../facilitator/STORY.html` | Solo tú |
| `.../facilitator/FACILITATOR.html` | Solo tú |

---

## PLAN B — Si tu infra interna no puede habilitar Pages pronto

Tu sitio es HTML estático puro. **No necesitas GitLab Pages.**

### Opción B1: Servidor Nginx estático en la intranet (1 día, pero sólido)

**Quién:** Infra.

El admin configura un Nginx que sirve la carpeta `html/` directamente:

```nginx
server {
    listen 80;
    server_name sre.tu-empresa.com;
    root /var/www/sre-data-analytics;
    index index.html;
}
```

Subes los archivos con `rsync` o `scp` en cada deploy. Sin CI/CD. Simple.

### Opción B2: GitLab CI + artifact (sin Pages)

La pipeline buildea el artifact pero **no** se publica vía Pages. Tú o el infra lo descarga y lo sirve con el servidor de su elección (Nginx, Apache, Tomcat). El `.gitlab-ci.yml` ya está listo.

### Opción B3: Push solo a GitHub Pages desde tu VPN

Algunos equipos publican desde VPN al GitHub público, sin pasar por la intranet de la empresa. Si tu empresa permite esto, **ya está funcionando** — solo falta activar Pages en el repo de GitHub que ya creaste.

---

## Checklist para el equipo infra

| Pregunta | Qué necesito saber |
|----------|---------------------|
| ¿Cuál es la URL del GitLab? | `https://gitlab.tu-empresa.com` |
| ¿Está habilitado Pages? | Sí / No |
| ¿En qué dominio sirve Pages? | `https://pages.tu-empresa.com` |
| ¿Puedo crear proyectos privados con Pages? | Sí / No |
| ¿Cómo me autentico? (token o SSH) | Instrucciones |

Cuando tenga eso, corro los pasos 3-6 y verifico.

---

## Si todo falla: alternativa segura

Mientras se valida GitLab, **puedes publicar temporalmente en GitHub Pages** (ya tienes el repo listo, solo falta activar el Source en Settings → Pages). El repo no es privado pero solo contiene material formativo público. Cuando GitLab esté confirmado, migras.

---

**Contacto:** Andrés Correa (@amcorrea0). Repo actual: https://github.com/amcorrea0/sre-data-analytics