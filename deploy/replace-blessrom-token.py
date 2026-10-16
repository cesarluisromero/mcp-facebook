#!/usr/bin/env python3
"""Validate and replace only Blessrom's Page token, keeping a root-only backup."""
import getpass
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request

PAGE = "747862795080338"

def verify_token(token, version, opener=urllib.request.urlopen):
    if not token or len(token) > 16384 or any(c.isspace() for c in token):
        raise ValueError("Token vacío o inválido.")
    if not re.fullmatch(r"v\d+\.\d+", version):
        raise ValueError("Versión Graph inválida.")
    def graph(path):
        request = urllib.request.Request("https://graph.facebook.com/" + version + "/" + path,
            headers={"Authorization": "Bearer " + token})
        try:
            with opener(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            raise ValueError("Meta rechazó la verificación: HTTP " + str(error.code)) from None
    if graph("me?fields=id,name").get("id") != PAGE:
        raise ValueError("El token no pertenece a la página Blessrom. No se guardó.")
    if not isinstance(graph(PAGE + "/posts?fields=id&limit=1").get("data"), list):
        raise ValueError("No se pudo verificar la lectura de publicaciones.")

def main():
    if os.name != "posix" or os.geteuid() != 0:
        raise SystemExit("Ejecuta como root en el VPS Ubuntu.")
    root = Path(__file__).resolve().parent.parent
    config = json.loads((root / "secrets/appsettings.Production.json").read_text())
    page = config["Clients"]["blesroom"]["Pages"][PAGE]
    if page.get("TokenFile") != "/run/secrets/facebook-blessrom-token":
        raise SystemExit("La ruta configurada de Blessrom no coincide. No se modificó nada.")
    target = root / "secrets/facebook-blessrom-token"
    if not target.is_file() or target.is_symlink():
        raise SystemExit("Falta el archivo regular de token de Blessrom.")
    token = getpass.getpass("Token de PÁGINA Blessrom obtenido desde Blessrom Agency (entrada oculta): ").strip()
    try:
        verify_token(token, config["Meta"]["GraphVersion"])
    except (ValueError, urllib.error.URLError, TimeoutError):
        raise SystemExit("No se verificó la identidad o lectura de Blessrom. Se conservó el token anterior. Revisa el token en el Explorador.") from None
    backup = target.with_name(target.name + ".backup-" + str(time.time_ns()))
    fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(target.read_bytes())
        stream.flush()
        os.fsync(stream.fileno())
    # Keep the inode so the running container's bind mount observes the replacement.
    fd = os.open(target, os.O_WRONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "w") as stream:
        stream.write(token)
        stream.truncate()
        stream.flush()
        os.fsync(stream.fileno())
    os.chown(target, 0, 1654)
    os.chmod(target, 0o640)
    print("Identidad y lectura de Blessrom verificadas. Token actualizado sin mostrarlo.")
    print("Respaldo protegido: secrets/" + backup.name)
    print("Bucilar.com conserva su token. No requiere reiniciar ni reconstruir.")
    print("La app emisora y los permisos de escritura deben confirmarse en Meta; esta comprobación sólo valida identidad y lectura.")

if __name__ == "__main__":
    main()
