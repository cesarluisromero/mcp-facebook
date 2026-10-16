using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.Configuration;
using Microsoft.AspNetCore.Hosting;
using System.Net;

namespace McpFacebook.Tests;

public class HttpTests
{
    private sealed class Factory : WebApplicationFactory<Program>
    {
        protected override void ConfigureWebHost(IWebHostBuilder builder)
        {
            builder.ConfigureAppConfiguration((_, config) => config.AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["Auth:Authority"] = "https://identity.example.invalid/realms/facebook",
                ["Auth:Audience"] = "https://mifacebook-mcp.duckdns.org/mcp"
            }));
        }
    }

    [Fact]
    public async Task AnonymousRequestsCannotReachMcpTools()
    {
        await using var factory = new Factory();
        using var client = factory.CreateClient();
        using var response = await client.PostAsync("/mcp", new StringContent("{}", System.Text.Encoding.UTF8, "application/json"));
        Assert.Equal(HttpStatusCode.Unauthorized, response.StatusCode);
    }

    [Fact]
    public async Task HealthEndpointDoesNotRequireMetaCredentials()
    {
        await using var factory = new Factory();
        using var client = factory.CreateClient();
        using var response = await client.GetAsync("/health");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }
}
