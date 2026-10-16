# Estado de implementación

## Implementado y verificado localmente

- Servidor ASP.NET Core .NET 10 y SDK MCP oficial, transporte HTTP en `/mcp`.
- Autenticación JWT con emisor y audiencia configurables; sin modo anónimo.
- Herramienta `ListPosts`: lectura de diez publicaciones; validación de
  identificadores, usuario, cliente, página y alcance `mcp:read`.
- Tokens de Meta enviados por cabecera, sin registradores del cliente HTTP.
  La respuesta excluye los enlaces de paginación que podrían contener tokens.
- Modelo inicial de permisos y estados de publicación con pruebas unitarias.
  Todavía no hay ejecutor ni persistencia de estas operaciones.
- Dockerfile y Compose para el servidor en `127.0.0.1:5080` detrás de Nginx.

## Pendiente antes del uso real

Crear la app Meta y obtener permisos y tokens mediante su autorización;
configurar el proveedor de identidad OAuth de ChatGPT y sus clientes;
integrar almacenamiento cifrado, base de datos, persistencia e idempotencia;
implementar publicaciones, mensajes, anuncios, webhooks y aprobaciones;
construir y probar la imagen Docker en Linux, cargarla al VPS y verificar
el protocolo MCP con autenticación real. Las pruebas locales no demuestran
compatibilidad con una cuenta real de Meta o ChatGPT.

El propietario creó la app `MCP RSF Blesroom` con páginas, Messenger y
Marketing API. La lectura de publicaciones de `Bucilar.com.`, ID
`106657377566820`, funcionó en el Explorador de Graph con v26.0.
El VPS sirve una respuesta provisional por HTTPS.

Se añadió una configuración de Keycloak 26.8.0 y PostgreSQL 17, un cliente
OAuth público con PKCE S256 y un alcance con audiencia fija para este MCP.
Los scripts de `deploy/` preparan las credenciales directamente en el VPS,
rotan el token con entrada oculta y actualizan sólo el sitio Nginx propio.
Compose y la sintaxis Python se verificaron localmente; el arranque del
proveedor de identidad, el almacenamiento de secretos reales y la conexión
OAuth completa todavía deben verificarse en el VPS.

Consulta [las instrucciones de despliegue](../deploy/README.md).

## Configuración del contenedor

Crear `secrets/appsettings.Production.json` fuera de Git y protegerlo con
permisos que permitan lectura exclusivamente al administrador y al UID
del contenedor. No incluir secretos en imágenes, capturas ni el chat.

Estructura orientativa (todos los valores son marcadores):

```json
{
  "Auth": {
    "Authority": "https://EMISOR-OAUTH/realms/facebook",
    "Audience": "https://mifacebook-mcp.duckdns.org/mcp"
  },
  "Meta": { "GraphVersion": "VERSION-DE-LA-APP-META" },
  "Clients": {
    "cliente1": {
      "Subjects": ["SUB-DEL-USUARIO-AUTORIZADO"],
      "Pages": { "ID-PAGINA": { "Token": "TOKEN-DE-PAGINA" } }
    }
  }
}
```

Este archivo es un mecanismo inicial de configuración; no sustituye la
conexión OAuth de clientes ni un almacén de secretos para producción.
No iniciar el servicio con emisores inventados o tokens ficticios.

Una vez resueltos los requisitos: `docker compose up -d --build`.
Comprobar `curl -fsS http://127.0.0.1:5080/health` antes de cambiar Nginx.
El bloque `location /` del sitio propio del MCP deberá usar:

```nginx
proxy_pass http://127.0.0.1:5080;
proxy_http_version 1.1;
proxy_set_header Host $host;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_buffering off;
proxy_read_timeout 300s;
```

Respaldar el archivo propio, ejecutar `nginx -t` y recargar sólo si pasa.
No sustituir bloques TLS ni configuraciones de otros sitios.
