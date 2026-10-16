# Publicación de texto: piloto

Herramienta `publish_post(client, page, message, operationId)`. Publica el
texto exacto de una petición explícita del usuario. No se ha realizado
ninguna publicación real durante las pruebas de implementación.

Requiere JWT válido, alcance `mcp:write`, pertenencia al cliente y sujeto
incluido en `Pages:<id>:WriteSubjects`. El alcance de ChatGPT no sustituye
el permiso `pages_manage_posts` del token de página de Meta.

Cada operación tiene un UUID y huella de cliente, página, usuario y texto.
El registro se escribe y sincroniza a disco antes de enviar a Meta.
Repetir el UUID no repite el POST; cambiar el contenido con ese UUID se
rechaza. Un UUID distinto representa una operación distinta: no generarlo
automáticamente cuando no se conoce el resultado de un envío previo.

La respuesta `accepted` incluye el ID devuelto por Meta, pero no demuestra
una verificación posterior de lectura. La respuesta `unknown` requiere
reconciliar con las publicaciones de la página; no reintentar ciegamente.
También se conserva como incierto un rechazo HTTP: el piloto prioriza no
repetir envíos y no dispone aún de clasificación completa de errores.

Compose monta el volumen `publications` en `/app/operations`. No borrar el
volumen ni ejecutar `down -v`: se perdería la protección entre reinicios.
Esta implementación está limitada a un VPS con almacenamiento local; no
es una cola distribuida ni implementa planificación, fotos o aprobación
por un segundo usuario. La autorización es la petición explícita del
usuario y los controles de acceso indicados.

## Habilitar en el VPS

1. Transferir y extraer `mcp-facebook-publish.tar.gz` en `/opt/mcp-facebook`.
2. Ejecutar `python3 deploy/enable-publication.py`. Habilita únicamente el
   usuario operador y la página Bucilar.com en la configuración existente.
3. Ejecutar `docker compose up -d --build --no-deps mcp` y comprobar salud.
4. En Meta, autorizar `pages_manage_posts` además de los permisos de lectura.
   En el Explorador generar la autorización de usuario actualizada, luego
   seleccionar Bucilar.com para obtener el token de página. Guardarlo con
   `deploy/store-token.py`. Añadir un permiso a revisión no significa que
   Meta lo haya aprobado para activos de clientes.
5. Renovar la autenticación del MCP aceptando `mcp:write`. Comprobar primero
   la lectura y después realizar una publicación explícitamente solicitada.

El permiso de Meta lo concede el titular mediante la interfaz de Meta;
los scripts de este proyecto no pueden concederlo por sí solos.
