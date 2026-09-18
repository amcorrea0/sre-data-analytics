# Validador rapido del entorno GitLab antes de publicar.
#
# Que valida:
#   1) Acceso de red a tu GitLab (DNS + HTTPS)
#   2) Si Pages esta habilitado (es un setting del admin, no del project)
#   3) Si el usuario tiene permisos para crear proyectos
#
# NO sube nada, solo consulta.
#
# Uso:
#   python notebooks/validate_gitlab.py <GITLAB_URL> <TOKEN_O_DEJAR_VACIO>
#
# Ejemplo:
#   python notebooks/validate_gitlab.py https://gitlab.tu-empresa.com

import sys
import urllib.request, urllib.error
import ssl, json, os
from pathlib import Path

if len(sys.argv) < 2:
    print("Uso: python notebooks/validate_gitlab.py <GITLAB_URL>")
    sys.exit(1)

GITLAB = sys.argv[1].rstrip("/")
TOKEN = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("GITLAB_TOKEN", "")

print(f"\nValidando GitLab: {GITLAB}\n" + "=" * 60)

def get(path, label):
    url = f"{GITLAB}{path}"
    headers = {"PRIVATE-TOKEN": TOKEN} if TOKEN else {}
    try:
        req = urllib.request.Request(url, headers=headers)
        ctx = ssl.create_default_context()
        # Si tu GitLab usa certificado self-signed, comentar la linea de abajo
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            body = r.read().decode("utf-8", errors="replace")
            print(f"  [OK]   {label:35} -> {r.status} ({len(body)} bytes)")
            return r.status, body
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  [404]  {label:35} -> no encontrado")
        elif e.code == 401:
            print(f"  [401]  {label:35} -> token invalido o falta")
        elif e.code == 403:
            print(f"  [403]  {label:35} -> acceso denegado (sin permisos)")
        else:
            print(f"  [ERR]  {label:35} -> HTTP {e.code}")
        return e.code, None
    except urllib.error.URLError as e:
        print(f"  [NET]  {label:35} -> {e.reason}")
        return None, None
    except Exception as e:
        print(f"  [ERR]  {label:35} -> {type(e).__name__}: {e}")
        return None, None

# 1. Resolucion DNS + HTTPS
print("\n[1/3] Acceso al servidor GitLab")
print("-" * 60)
status, _ = get("/-/health", "GET /-/health")
status, _ = get("/users/sign_in", "GET /users/sign_in")

if status is None:
    print("\n[x] No se puede conectar al GitLab. Verifica red/VPN/DNS.")
    sys.exit(1)

# 2. Version API
print("\n[2/3] API de GitLab")
print("-" * 60)
status, body = get("/api/v4/version", "GET /api/v4/version")
if status == 200 and body:
    try:
        info = json.loads(body)
        print(f"     Version GitLab: {info.get('version')}")
        print(f"     Revision:       {info.get('revision')}")
    except Exception:
        print(f"     Respuesta: {body[:200]}")

# 3. Detectar Pages
print("\n[3/3] Pages habilitado (puede requerir permisos admin)")
print("-" * 60)
print("     Para verificar Pages habilitado al nivel de instancia:")
print(f"     => {GITLAB}/admin/pages  (requiere ser admin)")
print()
print("     Si tu GitLab usa omnibus y Pages esta apagado, el admin debe:")
print("       1. Editar /etc/gitlab/gitlab.rb")
print("       2. Agregar: pages_external_url 'http(s)://<tu-dominio-pages>'")
print("       3. (Opcional) configurar cert SSL")
print("       4. Ejecutar: sudo gitlab-ctl reconfigure && sudo gitlab-ctl restart")
print()
print("     Para verificar Pages habilitado al nivel de proyecto:")
print("     - Crea proyecto de prueba y mira si en el menu lateral aparece")
print("       'Deploy > Pages' o similar.")

print("\n" + "=" * 60)
print("Resumen:")
print("-" * 60)
print("Si los [OK] aparecen en [1] y [2], el GitLab responde.")
print("Para Pages, necesitas que el admin confirme que esta habilitado.")
print("Si tu instancia no tiene Pages, alternativas:")
print("  - GitLab CI/CD + artifact bajado + Nginx (mas control)")
print("  - Servidor web estatico simple en intranet (mas simple)")
print("=" * 60)