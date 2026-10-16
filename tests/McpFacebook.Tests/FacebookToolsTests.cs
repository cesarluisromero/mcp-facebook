using System.Net;
using System.Security.Claims;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace McpFacebook.Tests;

public class FacebookToolsTests
{
    private sealed class GraphHandler : HttpMessageHandler
    {
        public int Calls { get; private set; }
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            Calls++;
            Assert.Equal("https", request.RequestUri!.Scheme);
            Assert.Equal("graph.facebook.com", request.RequestUri.Host);
            Assert.Equal("/v26.0/106657377566820/posts", request.RequestUri.AbsolutePath);
            Assert.Equal("Bearer", request.Headers.Authorization!.Scheme);
            Assert.Equal("test-token", request.Headers.Authorization.Parameter);
            Assert.DoesNotContain("test-token", request.RequestUri.ToString());
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent("{\"data\":[{\"id\":\"post1\"}],\"paging\":{\"next\":\"https://example.invalid/?access_token=secret\"}}")
            });
        }
    }

    [Theory]
    [InlineData("operator", true)]
    [InlineData("another-client-user", false)]
    public async Task McpActivationUsesConfiguredGraphClientAndEnforcesMembership(string subject, bool authorized)
    {
        var handler = new GraphHandler();
        var services = new ServiceCollection();
        services.AddSingleton<IConfiguration>(new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?>
        {
            ["Meta:GraphVersion"] = "v26.0",
            ["Clients:blesroom:Subjects:0"] = "operator",
            ["Clients:blesroom:Pages:106657377566820:Token"] = "test-token"
        }).Build());
        FacebookHttp.Register(services);
        services.AddSingleton<PublicationStore>();
        services.AddHttpClient(FacebookHttp.ClientName).ConfigurePrimaryHttpMessageHandler(() => handler);
        await using var provider = services.BuildServiceProvider();
        // MCP constructs tool classes through DI rather than the typed HttpClient factory.
        var tool = ActivatorUtilities.CreateInstance<FacebookTools>(provider);
        var principal = new ClaimsPrincipal(new ClaimsIdentity(new[] { new Claim("sub", subject), new Claim("scope", "mcp:read") }, "test"));
        if (authorized)
        {
            var result = await tool.ListPosts("blesroom", "106657377566820", principal, CancellationToken.None);
            Assert.Contains("post1", result);
            Assert.DoesNotContain("secret", result);
            Assert.DoesNotContain("paging", result);
            Assert.Equal(1, handler.Calls);
        }
        else
        {
            await Assert.ThrowsAsync<UnauthorizedAccessException>(() => tool.ListPosts("blesroom", "106657377566820", principal, CancellationToken.None));
            Assert.Equal(0, handler.Calls);
        }
    }
}
