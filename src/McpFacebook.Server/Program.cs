using Microsoft.AspNetCore.Authentication.JwtBearer;
using ModelContextProtocol.Server;
using System.ComponentModel;
using System.Security.Claims;
using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme).AddJwtBearer(o =>
{
    o.Authority = builder.Configuration["Auth:Authority"];
    o.Audience = builder.Configuration["Auth:Audience"];
    if (string.IsNullOrWhiteSpace(o.Authority) || string.IsNullOrWhiteSpace(o.Audience))
        throw new InvalidOperationException("Configura Auth:Authority y Auth:Audience antes de iniciar.");
    if (!Uri.TryCreate(o.Authority, UriKind.Absolute, out var issuer) || issuer.Scheme != "https" ||
        !Uri.TryCreate(o.Audience, UriKind.Absolute, out var resource) || resource.Scheme != "https")
        throw new InvalidOperationException("El emisor y la audiencia deben usar URLs HTTPS.");
    o.MapInboundClaims = false;
    o.RequireHttpsMetadata = true;
    o.Events = new JwtBearerEvents
    {
        OnChallenge = context =>
        {
            context.HandleResponse();
            context.Response.StatusCode = 401;
            var metadataResource = new Uri(builder.Configuration["Auth:Audience"]!);
            context.Response.Headers.WWWAuthenticate = $"Bearer resource_metadata=\"{metadataResource.GetLeftPart(UriPartial.Authority)}/.well-known/oauth-protected-resource\"";
            return Task.CompletedTask;
        }
    };
});
builder.Services.AddAuthorization();
FacebookHttp.Register(builder.Services);
builder.Services.AddSingleton<PublicationStore>();
builder.Services.AddMcpServer().WithHttpTransport(o => o.Stateless = true).WithTools<FacebookTools>();
var app = builder.Build();
_ = app.Services.GetRequiredService<Microsoft.Extensions.Options.IOptionsMonitor<JwtBearerOptions>>().Get(JwtBearerDefaults.AuthenticationScheme);
app.UseAuthentication();
app.UseAuthorization();
app.MapGet("/health", () => Results.Ok(new { status = "ok" }));
app.MapGet("/.well-known/oauth-protected-resource", () => Results.Json(new
{
    resource = app.Configuration["Auth:Audience"],
    authorization_servers = new[] { app.Configuration["Auth:Authority"] },
    scopes_supported = new[] { "mcp:read", "mcp:write" }
}));
app.MapMcp("/mcp").RequireAuthorization();
app.Run();

[McpServerToolType]
public sealed class FacebookTools(IHttpClientFactory httpClients, IConfiguration configuration, PublicationStore publications)
{
    [McpServerTool(ReadOnly = false, Destructive = false, Idempotent = true, OpenWorld = true),
        Description("Publica inmediatamente un texto en Facebook. Requiere una petición explícita del usuario, mcp:write y permiso de escritura sobre la página. Usa un operationId UUID nuevo por publicación y conserva el mismo para consultar/reintentar esa operación; nunca cambies el UUID si el resultado es incierto.")]
    public async Task<string> PublishPost(string client, string page, string message, string operationId,
        ClaimsPrincipal user, CancellationToken cancellationToken)
    {
        if (!System.Text.RegularExpressions.Regex.IsMatch(page, @"^\d+$") ||
            !System.Text.RegularExpressions.Regex.IsMatch(client, @"^[a-zA-Z0-9_-]{1,64}$") || !Guid.TryParse(operationId, out var id))
            throw new ArgumentException("Cliente, página o UUID de operación inválidos.");
        if (string.IsNullOrWhiteSpace(message) || message.Length > 63206)
            throw new ArgumentException("El texto debe contener entre 1 y 63206 caracteres.");
        var subject = user.FindFirstValue("sub") ?? throw new UnauthorizedAccessException();
        var members = configuration.GetSection($"Clients:{client}:Subjects").Get<string[]>() ?? [];
        var writers = configuration.GetSection($"Clients:{client}:Pages:{page}:WriteSubjects").Get<string[]>() ?? [];
        if (!members.Contains(subject, StringComparer.Ordinal) || !writers.Contains(subject, StringComparer.Ordinal) ||
            !user.FindAll("scope").SelectMany(c => c.Value.Split(' ')).Contains("mcp:write"))
            throw new UnauthorizedAccessException("No tienes permiso de publicación sobre esta página.");
        var version = configuration["Meta:GraphVersion"] ?? "";
        if (!System.Text.RegularExpressions.Regex.IsMatch(version, @"^v\d+\.\d+$"))
            throw new InvalidOperationException("Versión Graph inválida.");
        var pageConfig = configuration.GetSection($"Clients:{client}:Pages:{page}");
        var token = pageConfig["TokenFile"] is { Length: > 0 } tokenFile
            ? (await File.ReadAllTextAsync(tokenFile, cancellationToken)).Trim() : pageConfig["Token"];
        if (string.IsNullOrWhiteSpace(token) || token.Length > 16384 || token.Contains('\n') || token.Contains('\r'))
            throw new InvalidOperationException("Falta un token de página válido.");
        return await publications.Execute(id, client, page, subject, message, async () =>
        {
            using var http = httpClients.CreateClient(FacebookHttp.ClientName);
            using var request = new HttpRequestMessage(HttpMethod.Post, $"{version}/{page}/feed");
            request.Headers.Authorization = new("Bearer", token);
            request.Content = new FormUrlEncodedContent(new Dictionary<string, string> { ["message"] = message });
            using var response = await http.SendAsync(request, cancellationToken);
            if (!response.IsSuccessStatusCode)
                throw new InvalidOperationException($"Meta respondió HTTP {(int)response.StatusCode}. Revisa la operación antes de volver a publicar.");
            using var json = JsonDocument.Parse(await response.Content.ReadAsStringAsync(cancellationToken));
            return json.RootElement.GetProperty("id").GetString() ?? throw new InvalidOperationException("Meta no devolvió el ID.");
        });
    }

    [McpServerTool, Description("Lee diez publicaciones de una página autorizada del cliente.")]
    public async Task<string> ListPosts(string client, string page, ClaimsPrincipal user, CancellationToken cancellationToken)
    {
        if (!System.Text.RegularExpressions.Regex.IsMatch(page, @"^\d+$") ||
            !System.Text.RegularExpressions.Regex.IsMatch(client, @"^[a-zA-Z0-9_-]{1,64}$"))
            throw new ArgumentException("Identificadores inválidos.");
        var subject = user.FindFirstValue("sub") ?? throw new UnauthorizedAccessException();
        var pageConfig = configuration.GetSection($"Clients:{client}:Pages:{page}");
        var allowed = configuration.GetSection($"Clients:{client}:Subjects").Get<string[]>() ?? [];
        if (!allowed.Contains(subject, StringComparer.Ordinal) ||
            (pageConfig["Token"] is not { Length: > 0 } && pageConfig["TokenFile"] is not { Length: > 0 }))
            throw new UnauthorizedAccessException("Cliente o página no autorizados.");
        if (!user.FindAll("scope").SelectMany(c => c.Value.Split(' ')).Contains("mcp:read"))
            throw new UnauthorizedAccessException("Falta el alcance mcp:read.");
        var version = configuration["Meta:GraphVersion"] ?? throw new InvalidOperationException("Configura la versión Graph de tu app Meta.");
        if (!System.Text.RegularExpressions.Regex.IsMatch(version, @"^v\d+\.\d+$")) throw new InvalidOperationException("Versión Graph inválida.");
        using var request = new HttpRequestMessage(HttpMethod.Get, $"{version}/{page}/posts?fields=id,message,created_time,permalink_url&limit=10");
        var token = pageConfig["TokenFile"] is { Length: > 0 } tokenFile
            ? (await File.ReadAllTextAsync(tokenFile, cancellationToken)).Trim()
            : pageConfig["Token"]!;
        if (string.IsNullOrWhiteSpace(token) || token.Length > 16384 || token.Contains('\n') || token.Contains('\r'))
            throw new InvalidOperationException("El secreto de Meta no contiene un token válido.");
        request.Headers.Authorization = new("Bearer", token);
        using var http = httpClients.CreateClient(FacebookHttp.ClientName);
        using var response = await http.SendAsync(request, cancellationToken);
        if (!response.IsSuccessStatusCode) throw new InvalidOperationException($"Meta rechazó la consulta: HTTP {(int)response.StatusCode}.");
        using var json = JsonDocument.Parse(await response.Content.ReadAsStringAsync(cancellationToken));
        return json.RootElement.GetProperty("data").GetRawText();
    }
}

public partial class Program { }

public static class FacebookHttp
{
    public const string ClientName = "MetaGraph";

    public static void Register(IServiceCollection services) => services
        .AddHttpClient(ClientName, c => c.BaseAddress = new Uri("https://graph.facebook.com/"))
        .ConfigurePrimaryHttpMessageHandler(() => new HttpClientHandler { AllowAutoRedirect = false })
        .RemoveAllLoggers();
}
