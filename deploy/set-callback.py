#!/usr/bin/env python3
"""Update a pre-registered OAuth client over the VPS loopback interface."""
import json
from pathlib import Path
import urllib.parse
import urllib.request

root = Path(__file__).resolve().parent.parent
callback = input("URI de retorno EXACTA mostrada por ChatGPT: ").strip()
desktop_callback = "http://127.0.0.1:4321/callback"
if (not callback.startswith("https://chatgpt.com/") and callback != desktop_callback) or any(c in callback for c in "*\r\n"):
    raise SystemExit("Usa la URI exacta de ChatGPT o el callback local configurado del escritorio, sin comodines.")
env = dict(line.split("=", 1) for line in (root / ".env").read_text().splitlines() if "=" in line)
base = "http://127.0.0.1:8180/auth"
body = urllib.parse.urlencode({"client_id": "admin-cli", "grant_type": "password",
    "username": "bootstrap-admin", "password": env["IDENTITY_ADMIN_PASSWORD"]}).encode()
with urllib.request.urlopen(urllib.request.Request(base + "/realms/master/protocol/openid-connect/token", data=body), timeout=30) as response:
    token = json.load(response)["access_token"]
headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
url = base + "/admin/realms/facebook/clients"
with urllib.request.urlopen(urllib.request.Request(url + "?clientId=chatgpt-mcp", headers=headers), timeout=30) as response:
    clients = json.load(response)
if len(clients) != 1:
    raise SystemExit("No se encontró un único cliente OAuth esperado.")
client = clients[0]
client["redirectUris"] = [callback]
with urllib.request.urlopen(urllib.request.Request(url + "/" + client["id"], headers=headers,
    data=json.dumps(client).encode(), method="PUT"), timeout=30):
    pass
print("URI exacta guardada para chatgpt-mcp.")
realm_file = root / "secrets/facebook-realm.json"
realm = json.loads(realm_file.read_text())
for user in realm.get("users", []):
    user.pop("credentials", None)
realm_file.write_text(json.dumps(realm, indent=2))
print("Contraseñas iniciales retiradas del archivo de importación; los usuarios permanecen en PostgreSQL.")
