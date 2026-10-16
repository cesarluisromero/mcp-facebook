#!/usr/bin/env python3
"""Replace only the known placeholder in this project's existing HTTPS site."""
from pathlib import Path
import shutil
import subprocess
import time

site = Path("/etc/nginx/sites-available/mifacebook-mcp.duckdns.org")
original = site.read_text()
old = '''    location / {
        default_type text/plain;
        return 200 "Servidor preparado. MCP pendiente de despliegue.\\n";
    }'''
new = '''    location ^~ /auth/admin/ { return 404; }
    location ^~ /auth/ {
        proxy_pass http://127.0.0.1:8180;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Port $server_port;
    }
    location / {
        proxy_pass http://127.0.0.1:5080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_buffering off;
        proxy_read_timeout 300s;
    }'''
if original.count(old) != 1:
    raise SystemExit("El bloque provisional no coincide. No se ha modificado Nginx.")
backup = site.with_name(site.name + ".backup-" + str(time.time_ns()))
shutil.copy2(site, backup)
site.write_text(original.replace(old, new))
try:
    subprocess.run(["nginx", "-t"], check=True)
    subprocess.run(["systemctl", "reload", "nginx"], check=True)
except subprocess.CalledProcessError:
    shutil.copy2(backup, site)
    raise SystemExit("La operación falló; se restauró el archivo anterior.")
print("Sitio MCP actualizado. Se conservaron los bloques TLS existentes.")
