# Despliegue del piloto de lectura

Los archivos preparan OAuth con Keycloak 26.8.0 y PostgreSQL 17, sin
exponer sus puertos fuera de localhost. No confundir el usuario `operador`
con el usuario de Facebook: el primero autoriza ChatGPT ante el MCP y
el token de página permite al MCP consultar Meta.

## Transferencia desde Windows

Desde PowerShell, dentro del proyecto:

```powershell
scp .\mcp-facebook-pilot.tar.gz root@77.37.43.158:/root/
```

La conexión requiere acceso SSH del propietario. Verificar la huella del
servidor mediante Hostinger antes de aceptarla. No compartir contraseñas.

## En el VPS, como root

```bash
mkdir -p /opt/mcp-facebook
cd /opt/mcp-facebook
tar -xzf /root/mcp-facebook-pilot.tar.gz
python3 deploy/configure.py
docker compose up -d --build
```

El configurador pide una contraseña nueva para `operador` y el token de
página mediante entrada oculta. Permite dejar pendiente el token y la URI
exacta de retorno de ChatGPT. No admite sobrescribir secretos existentes.
Conservar la contraseña del operador en un gestor de contraseñas.

Si aún no se dispone del callback, pulsar Enter; después se configurará
con `python3 deploy/set-callback.py`. El cliente permanece bloqueado hasta
registrar esa URI exacta.

Comprobar los servicios antes de cambiar el sitio Nginx:

```bash
docker compose ps
curl -fsS http://127.0.0.1:5080/health
curl -fsS http://127.0.0.1:8180/auth/realms/facebook/.well-known/openid-configuration
python3 deploy/nginx.py
curl -fsS https://mifacebook-mcp.duckdns.org/health
curl -fsS https://mifacebook-mcp.duckdns.org/auth/realms/facebook/.well-known/openid-configuration
```

La importación inicial del realm contiene la contraseña inicial del
operador. Después de confirmar que Keycloak arrancó y el usuario puede
entrar, ejecutar `deploy/set-callback.py`: además de guardar el callback,
quita `credentials` de los usuarios del archivo de importación
para que no quede esa contraseña en disco. Keycloak guarda sus usuarios
en PostgreSQL; importar al iniciar no sobrescribe un realm existente.

## Conectar ChatGPT

Registrar el servidor HTTPS `https://mifacebook-mcp.duckdns.org/mcp` con
OAuth y un cliente prerregistrado: ID `chatgpt-mcp`, cliente público,
sin secreto, PKCE S256. Copiar la URI exacta mostrada por ChatGPT y
ejecutar `python3 deploy/set-callback.py` en el VPS.

Emisor: `https://mifacebook-mcp.duckdns.org/auth/realms/facebook`.
Alcance solicitado: `mcp:read`. Audiencia: URL completa del endpoint MCP.
Si la pantalla del producto no ofrece cliente prerregistrado, inspeccionar
esa pantalla y adaptar CIMD/DCR antes de continuar; no inventar una URI ni
activar comodines en las redirecciones.

Entrar como `operador`. La autorización de Facebook ya comprobada en el
Explorador no autoriza automáticamente esta conexión de ChatGPT.
Consulta inicial: cliente `blesroom`, página `106657377566820`.

Para guardar o rotar el token: `python3 deploy/store-token.py`.
El secreto sólo se monta en el contenedor MCP, con lectura para UID 1654.
Los archivos se protegen por permisos; esto no equivale a cifrado en reposo.
Antes de conectar clientes, completar el almacén cifrado y la conexión OAuth
de Meta, y la revisión de permisos correspondiente.

## Verificación y límites

Una petición anónima a `/mcp` debe obtener HTTP 401 con `WWW-Authenticate`.
La identidad debe firmar tokens con audiencia y alcance correctos; comprobar
con la sesión real de ChatGPT. El piloto sólo proporciona `ListPosts`.
La configuración Compose se verifica localmente; arranque e importación
de Keycloak deben verificarse en el VPS. No ejecutar `down -v`: elimina
datos persistentes de identidad.

Referencias: https://developers.openai.com/plugins/build/auth y
https://www.keycloak.org/securing-apps/mcp-authz-server.
