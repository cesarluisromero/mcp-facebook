#!/usr/bin/env python3
"""Enable one existing operator and page for text publication. Does not call Meta."""
import json
from pathlib import Path
import runpy

root = Path(__file__).resolve().parent.parent
context = runpy.run_path(str(root / "deploy/fix-scopes.py"))
api = context["api"]
client_id = context["client_id"]
scopes = {s["name"]: s["id"] for s in api("/client-scopes")}
if "mcp:write" not in scopes:
    api("/client-scopes", "POST", {"name": "mcp:write", "protocol": "openid-connect",
        "attributes": {"include.in.token.scope": "true", "display.on.consent.screen": "true"}})
    scopes = {s["name"]: s["id"] for s in api("/client-scopes")}
api("/clients/" + client_id + "/optional-client-scopes/" + scopes["mcp:write"], "PUT")
users = api("/users?username=operador&exact=true")
if len(users) != 1:
    raise SystemExit("No hay un único operador.")
path = root / "secrets/appsettings.Production.json"
config = json.loads(path.read_text())
client = config["Clients"]["blesroom"]
subject = users[0]["id"]
if subject not in client["Subjects"]:
    raise SystemExit("El operador no es miembro autorizado de blesroom.")
page = client["Pages"]["106657377566820"]
page["WriteSubjects"] = sorted(set(page.get("WriteSubjects", []) + [subject]))
path.write_text(json.dumps(config, indent=2))
print("Publicación habilitada únicamente para operador y Bucilar.com. No se publicó contenido.")
print("Falta autorizar pages_manage_posts en Meta, actualizar el token y renovar OAuth con mcp:write.")
