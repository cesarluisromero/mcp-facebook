#!/usr/bin/env python3
"""Run on the Ubuntu VPS. Secrets are prompted invisibly and never printed."""
import getpass
import json
import os
from pathlib import Path
import secrets
import uuid

ROOT = Path(__file__).resolve().parent.parent
HOST = "https://mifacebook-mcp.duckdns.org"

def write(path, value, group=0, owner=0):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(value)
    os.chown(path, owner, group)
    os.chmod(path, 0o640 if group else 0o600)

def main():
    if os.name != "posix" or os.geteuid() != 0:
        raise SystemExit("Ejecuta este script como root en el VPS Ubuntu.")
    target = ROOT / "secrets"
    if (ROOT / ".env").exists() or target.exists():
        raise SystemExit("Ya hay configuración; no se ha sobrescrito ningún secreto.")
    callback = input("URI de retorno EXACTA mostrada por ChatGPT (Enter: configurar después): ").strip()
    if callback and not callback.startswith("https://chatgpt.com/"):
        raise SystemExit("La URI debe ser la de ChatGPT, sin comodines.")
    if any(c in callback for c in "*\r\n"):
        raise SystemExit("URI de retorno inválida.")
    password = getpass.getpass("Nueva contraseña del usuario operador del MCP (mínimo 16 caracteres): ")
    if len(password) < 16 or password != getpass.getpass("Repite la contraseña: "):
        raise SystemExit("Las contraseñas no coinciden o son demasiado cortas.")
    token = getpass.getpass("Token NUEVO de página Bucilar.com (Enter: guardar después): ").strip()
    if any(c.isspace() for c in token) or len(token) > 16384:
        raise SystemExit("Token inválido.")
    target.mkdir(mode=0o711)
    subject = str(uuid.uuid4())
    realm = {
        "realm": "facebook", "enabled": True, "registrationAllowed": False,
        "bruteForceProtected": True, "sslRequired": "external",
        "accessTokenLifespan": 300,
        "users": [{"id": subject, "username": "operador", "enabled": True,
                   "credentials": [{"type": "password", "value": password, "temporary": False}]}],
        "clientScopes": [{"name": "mcp:read", "protocol": "openid-connect",
            "attributes": {"include.in.token.scope": "true", "display.on.consent.screen": "true"},
            "protocolMappers": [{"name": "mcp-audience", "protocol": "openid-connect",
                "protocolMapper": "oidc-audience-mapper", "consentRequired": False,
                "config": {"included.custom.audience": HOST + "/mcp", "access.token.claim": "true", "id.token.claim": "false"}}]}],
        "clients": [{"clientId": "chatgpt-mcp", "protocol": "openid-connect", "enabled": True,
            "publicClient": True, "standardFlowEnabled": True,
            "directAccessGrantsEnabled": False, "serviceAccountsEnabled": False,
            "implicitFlowEnabled": False, "consentRequired": True,
            "redirectUris": [callback] if callback else [],
            "defaultClientScopes": ["basic", "mcp:read"],
            "optionalClientScopes": ["offline_access"],
            "attributes": {"pkce.code.challenge.method": "S256"}}]
    }
    realm["clientScopes"].append({"name": "basic", "protocol": "openid-connect",
        "attributes": {"include.in.token.scope": "false", "display.on.consent.screen": "false"},
        "protocolMappers": [{"name": "Subject (sub)", "protocol": "openid-connect",
            "protocolMapper": "oidc-sub-mapper", "consentRequired": False,
            "config": {"access.token.claim": "true", "introspection.token.claim": "true"}}]})
    config = {"Auth": {"Authority": HOST + "/auth/realms/facebook", "Audience": HOST + "/mcp"},
        "Meta": {"GraphVersion": "v26.0"},
        "Clients": {"blesroom": {"Subjects": [subject], "Pages": {
            "106657377566820": {"TokenFile": "/run/secrets/facebook-page-token"}}}}}
    write(target / "facebook-realm.json", json.dumps(realm, indent=2), owner=1000)
    write(target / "appsettings.Production.json", json.dumps(config, indent=2), 1654)
    write(target / "facebook-page-token", token, 1654)
    write(ROOT / ".env", "IDENTITY_DB_PASSWORD=" + secrets.token_urlsafe(32) +
          "\nIDENTITY_ADMIN_PASSWORD=" + secrets.token_urlsafe(32) + "\n")
    print("Configuración guardada. Usuario: operador. Ningún secreto se ha mostrado.")
    if not callback:
        print("El cliente OAuth permanece sin URI de retorno: aún no puede conectarse ChatGPT.")
    if not token:
        print("Falta introducir el token de página antes de consultar Facebook.")

if __name__ == "__main__":
    main()
