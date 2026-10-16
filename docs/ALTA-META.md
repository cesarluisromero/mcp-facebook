# Crear la aplicación de Meta

El propietario debe completar el alta en su propia cuenta:

1. Abrir https://developers.facebook.com/apps/ e iniciar sesión.
2. Si Meta solicita el registro como desarrollador, completarlo.
3. Crear una aplicación llamada `MCP RSF Blesroom` y asociarla al
   negocio correspondiente cuando se solicite.
4. Revisar los casos de uso que ofrece el asistente para páginas,
   Messenger y Marketing API. Los nombres pueden variar: compartir sólo
   una captura sin secretos si no aparece una opción compatible.
5. Guardar el ID de aplicación. Mantener el secreto de aplicación en un
   almacén protegido, fuera del chat y del repositorio.

No suponer que crear la app concede acceso a páginas de clientes: hay que
implementar su consentimiento OAuth y obtener los permisos aprobados.
Los primeros ensayos deben hacerse sobre activos de prueba o propios
autorizados, antes de conectar clientes.

El dominio previsto es `mifacebook-mcp.duckdns.org`. Las URLs de retorno,
webhook, privacidad y eliminación de datos se registrarán cuando estén
implementadas y verificadas; no registrar endpoints inexistentes.

Esta guía no confirma los nombres actuales de las opciones del asistente:
la consola de Meta exige acceso autenticado y no pudo inspeccionarse.
