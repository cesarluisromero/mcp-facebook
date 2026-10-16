#!/usr/bin/env python3
import getpass
import os
from pathlib import Path

path = Path(__file__).resolve().parent.parent / "secrets/facebook-page-token"
token = getpass.getpass("Token NUEVO de página Bucilar.com (entrada oculta): ").strip()
if not token or len(token) > 16384 or any(c.isspace() for c in token):
    raise SystemExit("Token inválido; no se guardó.")
if not path.is_file() or path.is_symlink():
    raise SystemExit("Primero configura los secretos del proyecto.")
# Update the existing inode so the read-only Docker bind mount sees rotation.
with path.open("w") as stream:
    stream.write(token)
os.chown(path, 0, 1654)
os.chmod(path, 0o640)
print("Token guardado sin mostrarlo. No requiere reconstruir la imagen.")
