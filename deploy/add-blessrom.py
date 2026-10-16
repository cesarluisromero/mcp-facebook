#!/usr/bin/env python3
"""Register Blessrom on the existing VPS; never publishes content."""
import getpass
import json
import os
from pathlib import Path
import shutil
import time
import urllib.error
import urllib.request

PAGE = "747862795080338"

def main():
    if os.name != "posix" or os.geteuid() != 0:
        raise SystemExit("Ejecuta como root en el VPS Ubuntu.")
    root = Path(__file__).resolve().parent.parent
    config_file = root / "secrets/appsettings.Production.json"
    compose_file = root / "compose.yml"
    token_file = root / "secrets/facebook-blessrom-token"
    config = json.loads(config_file.read_text())
    client = config["Clients"]["blesroom"]
    writers = client["Pages"]["106657377566820"].get("WriteSubjects", [])
    if not writers or not set(writers).issubset(set(client["Subjects"])):
        raise SystemExit("No hay operadores de publicación válidos en la configuración existente.")
    compose = compose_file.read_text()
    anchor = "      - ./secrets/facebook-page-token:/run/secrets/facebook-page-token:ro"
    mount = "      - ./secrets/facebook-blessrom-token:/run/secrets/facebook-blessrom-token:ro"
    if mount not in compose and compose.count(anchor) != 1:
        raise SystemExit("El montaje de secretos no coincide. No se modificó la configuración.")
    if token_file.is_symlink():
        raise SystemExit("El archivo de token no puede ser un enlace simbólico.")
    token = getpass.getpass("Pega el access_token devuelto para Blessrom (entrada oculta): ").strip()
    if not token or len(token) > 16384 or any(c.isspace() for c in token):
        raise SystemExit("Token inválido; no se guardó.")
    version = config["Meta"]["GraphVersion"]
    if version != "v26.0":
        raise SystemExit("Revisar la versión Graph antes de continuar.")
    def graph(path):
        request = urllib.request.Request("https://graph.facebook.com/" + version + "/" + path,
            headers={"Authorization": "Bearer " + token})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            raise SystemExit("Meta rechazó la verificación: HTTP " + str(error.code) + ". No se cambió ningún secreto.") from None
    identity = graph("me?fields=id,name")
    if identity.get("id") != PAGE:
        raise SystemExit("El token no pertenece a Blessrom. No se guardó.")
    posts = graph(PAGE + "/posts?fields=id&limit=1")
    if not isinstance(posts.get("data"), list):
        raise SystemExit("Meta no devolvió una lista de publicaciones. No se guardó.")
    stamp = str(time.time_ns())
    for path in [config_file, compose_file]:
        backup = path.with_name(path.name + ".backup-" + stamp)
        shutil.copy2(path, backup)
        os.chmod(backup, 0o600)
    fd = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(token)
        stream.truncate()
        stream.flush()
        os.fsync(stream.fileno())
    os.chown(token_file, 0, 1654)
    os.chmod(token_file, 0o640)
    page_config = client["Pages"].setdefault(PAGE, {})
    page_config["TokenFile"] = "/run/secrets/facebook-blessrom-token"
    page_config.pop("Token", None)
    page_config["WriteSubjects"] = writers
    config_file.write_text(json.dumps(config, indent=2))
    if mount not in compose:
        compose_file.write_text(compose.replace(anchor, anchor + "\n" + mount))
    print("Identidad verificada: Blessrom, " + PAGE)
    print("Lectura verificada. Token independiente guardado sin mostrarlo.")
    print("Operadores autorizados para ambas páginas. Bucilar.com conserva su token.")
    print("Ejecuta: docker compose up -d --no-deps mcp")

if __name__ == "__main__":
    main()
