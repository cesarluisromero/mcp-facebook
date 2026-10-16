using System.Net;
using System.Security.Claims;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace McpFacebook.Tests;

public class PublishPostTests
{
    private sealed class Handler : HttpMessageHandler
    {
        public int Calls;
        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            Calls++;
            Assert.Equal(HttpMethod.Post, request.Method);
            Assert.Equal("https://graph.facebook.com/v26.0/106657377566820/feed", request.RequestUri!.ToString());
            Assert.Equal("test-token", request.Headers.Authorization!.Parameter);
            Assert.Equal("message=Texto+de+prueba", await request.Content!.ReadAsStringAsync(cancellationToken));
            return new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent("{\"id\":\"106657377566820_123\"}") };
        }
    }

    [Theory]
    [InlineData("operator", "mcp:read mcp:write", true, true)]
    [InlineData("operator", "mcp:read", true, false)]
    [InlineData("operator", "mcp:write", false, false)]
    [InlineData("other", "mcp:read mcp:write", true, false)]
    public async Task PublicationRequiresScopeAndPageWriterAndIsDeduplicated(string subject, string scopes, bool writer, bool accepted)
    {
        var directory = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"));
        try
        {
            var config = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["Meta:GraphVersion"] = "v26.0",
                ["Clients:blesroom:Subjects:0"] = "operator",
                ["Clients:blesroom:Pages:106657377566820:WriteSubjects:0"] = writer ? "operator" : "nobody",
                ["Clients:blesroom:Pages:106657377566820:Token"] = "test-token",
                ["Publications:Directory"] = directory
            }).Build();
            var handler = new Handler();
            var services = new ServiceCollection();
            services.AddSingleton<IConfiguration>(config);
            services.AddSingleton<PublicationStore>();
            FacebookHttp.Register(services);
            services.AddHttpClient(FacebookHttp.ClientName).ConfigurePrimaryHttpMessageHandler(() => handler);
            await using var provider = services.BuildServiceProvider();
            var tool = ActivatorUtilities.CreateInstance<FacebookTools>(provider);
            var user = new ClaimsPrincipal(new ClaimsIdentity(new[] { new Claim("sub", subject), new Claim("scope", scopes) }, "test"));
            var id = Guid.NewGuid().ToString();
            Task<string> Publish() => tool.PublishPost("blesroom", "106657377566820", "Texto de prueba", id, user, CancellationToken.None);
            if (accepted)
            {
                Assert.Contains("106657377566820_123", await Publish());
                await Publish();
                Assert.Equal(1, handler.Calls);
            }
            else
            {
                await Assert.ThrowsAsync<UnauthorizedAccessException>(Publish);
                Assert.Equal(0, handler.Calls);
            }
        }
        finally { if (Directory.Exists(directory)) Directory.Delete(directory, true); }
    }
}
