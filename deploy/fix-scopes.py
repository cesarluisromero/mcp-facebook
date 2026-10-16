#!/usr/bin/env python3
"""Repair scopes for the existing desktop client without changing passwords."""
import json
from pathlib import Path
import urllib.parse
import urllib.request

root = Path(__file__).resolve().parent.parent
env = dict(line.split("=", 1) for line in (root / ".env").read_text().splitlines() if "=" in line)
base = "http://127.0.0.1:8180/auth"
form = urllib.parse.urlencode({"client_id": "admin-cli", "grant_type": "password",
    "username": "bootstrap-admin", "password": env["IDENTITY_ADMIN_PASSWORD"]}).encode()
with urllib.request.urlopen(urllib.request.Request(base + "/realms/master/protocol/openid-connect/token", data=form), timeout=30) as response:
    token = json.load(response)["access_token"]
headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
admin = base + "/admin/realms/facebook"

def api(path, method="GET", data=None):
    body = json.dumps(data).encode() if data is not None else (b"" if method == "PUT" else None)
    request = urllib.request.Request(admin + path, headers=headers, method=method, data=body)
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read()
        return json.loads(raw) if raw else None

clients = api("/clients?clientId=chatgpt-mcp")
if len(clients) != 1:
    raise SystemExit("No se encontró un único cliente chatgpt-mcp.")
client_id = clients[0]["id"]
scopes = {scope["name"]: scope["id"] for scope in api("/client-scopes")}
if "basic" not in scopes:
    api("/client-scopes", "POST", {
        "name": "basic", "protocol": "openid-connect",
        "attributes": {"include.in.token.scope": "false", "display.on.consent.screen": "false"}
    })
    scopes = {scope["name"]: scope["id"] for scope in api("/client-scopes")}
mapper_path = "/client-scopes/" + scopes["basic"] + "/protocol-mappers/models"
mappers = api(mapper_path)
subject_mapper = next((m for m in mappers if m.get("protocolMapper") == "oidc-sub-mapper"), None)
if subject_mapper is None:
    api(mapper_path, "POST", {
        "name": "Subject (sub)", "protocol": "openid-connect",
        "protocolMapper": "oidc-sub-mapper", "consentRequired": False,
        "config": {"access.token.claim": "true", "introspection.token.claim": "true"}
    })
else:
    subject_mapper.setdefault("config", {})["access.token.claim"] = "true"
    api(mapper_path + "/" + subject_mapper["id"], "PUT", subject_mapper)
for name, category in [("basic", "default"), ("mcp:read", "default"), ("offline_access", "optional")]:
    if name not in scopes:
        raise SystemExit("Falta el alcance en el realm: " + name)
    api("/clients/" + client_id + "/" + category + "-client-scopes/" + scopes[name], "PUT")
users = api("/users?username=operador&exact=true")
if len(users) != 1:
    raise SystemExit("No se encontró un único usuario operador.")
role = api("/roles/offline_access")
api("/users/" + users[0]["id"] + "/role-mappings/realm", "POST", [{"id": role["id"], "name": role["name"]}])
print("Cliente chatgpt-mcp: basic y mcp:read habilitados; offline_access opcional.")
print("Mapeo de sub configurado para incluir el identificador del usuario en el token.")
print("Usuario operador autorizado para offline_access. Vuelve a iniciar la autenticación.")
