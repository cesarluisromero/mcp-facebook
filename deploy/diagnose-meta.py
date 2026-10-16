#!/usr/bin/env python3
"""Read-only Graph diagnostics. Never print tokens, response bodies or paging URLs."""
import json
from pathlib import Path
import re
import urllib.error
import urllib.request

root = Path(__file__).resolve().parent.parent
token = (root / "secrets/facebook-page-token").read_text().strip()
if not token:
    raise SystemExit("El archivo de token está vacío.")

for path in ["me?fields=id", "106657377566820/posts?fields=id,message,created_time,permalink_url&limit=10"]:
    request = urllib.request.Request("https://graph.facebook.com/v26.0/" + path,
        headers={"Authorization": "Bearer " + token})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.load(response)
        if path.startswith("me?"):
            print("Identidad del token:", data.get("id"), "(página esperada: 106657377566820)")
        else:
            print("Lectura de publicaciones: OK; cantidad:", len(data.get("data", [])))
    except urllib.error.HTTPError as error:
        try:
            details = json.load(error).get("error", {})
        except (ValueError, AttributeError):
            details = {}
        message = str(details.get("message", "Sin mensaje JSON de Meta")).replace(token, "[TOKEN OCULTO]")
        message = re.sub(r"(?i)(access_token[= :]+)[^\s&\"']+", r"\1[OCULTO]", message)
        print("HTTP:", error.code, "Código Meta:", details.get("code"), "Subcódigo:", details.get("error_subcode"))
        print("Motivo:", message[:1500])
