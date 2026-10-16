# Dirección pública del MCP en Hostinger

## Datos de este despliegue

- Proveedor: Hostinger.
- Sistema operativo: Ubuntu 24.04 LTS.
- IPv4 pública indicada por el propietario: `77.37.43.158`.
- Dominio creado por el propietario: `mifacebook-mcp.duckdns.org`.
- Estado: subdominio reservado y registro A verificado. MCP no desplegado.
- Comprobación DNS del 11 de octubre de 2026: el registro A devuelve
  `77.37.43.158`, que coincide con la IPv4 indicada para el VPS.
- Registro AAAA observado: `2a02:4780:14:147c::1`. Pendiente de confirmar
  que pertenece al mismo VPS y que permite alcanzar el servicio HTTPS.

La extensión `.face` no figura en la lista de TLD delegados de IANA
comprobada el 11 de octubre de 2026:
https://data.iana.org/TLD/tlds-alpha-by-domain.txt.
Por tanto, el nombre solicitado no sirve como dominio público convencional.
El propietario creó posteriormente `mifacebook-mcp.duckdns.org`, que es
el nombre adoptado para este despliegue.

En la fila `mifacebook-mcp` de DuckDNS, cambiar el campo de IPv4 a
`77.37.43.158` y pulsar `update ip`. La actualización DNS no instala el MCP
ni configura por sí sola el certificado HTTPS.

El VPS ejecuta el servidor C#. El DNS traduce un nombre, como
`mifacebook-mcp.duckdns.org`, a la IP pública del VPS. HTTPS cifra la conexión
y permite comprobar la identidad del servidor mediante un certificado.

La dirección se utilizará para el endpoint MCP de ChatGPT, los retornos OAuth
y los webhooks de Meta. Comprar un dominio no es necesario para el piloto.
Un nombre tampoco concede permisos sobre Facebook: cada cliente deberá
autorizar sus activos y Meta deberá aprobar los permisos que lo requieran.

## Subdominio gratuito

1. Identificar en hPanel la IP pública y el sistema operativo del VPS.
2. Abrir https://www.duckdns.org/ e iniciar sesión con una cuenta propia.
3. Elegir un subdominio disponible y asignarle la IP pública del VPS.
4. Guardar el token de DuckDNS como secreto; no compartirlo en el chat,
   subirlo a Git ni incluirlo en capturas o enlaces públicos.
5. Comprobar que el nombre resuelve a la IP correcta. En Windows:
   `Resolve-DnsName mifacebook-mcp.duckdns.org`.
6. Preparar el servidor y el proxy HTTPS. Permitir TCP 80 y 443 en los
   cortafuegos necesarios, manteniendo PostgreSQL sin exposición pública.
7. Configurar el certificado HTTPS antes de registrar las URLs de OAuth
   y el endpoint MCP. El certificado debe renovarse automáticamente.

El subdominio del ejemplo no está reservado. El alta requiere acceder a la
cuenta de DuckDNS. El despliegue requiere acceso autorizado al VPS.

## Límites pendientes de verificar

El piloto debe comprobar el alta de las URLs exactas en ChatGPT y Meta.
Los requisitos de revisión comercial o verificación de dominio de Meta
pueden exigir una configuración adicional o un dominio propio: un
subdominio gratuito no garantiza superar esos procesos.

Fuentes: https://www.duckdns.org/ y https://www.duckdns.org/spec.jsp.
