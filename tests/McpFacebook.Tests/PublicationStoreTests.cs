using Microsoft.Extensions.Configuration;

namespace McpFacebook.Tests;

public class PublicationStoreTests
{
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task DuplicateOperationNeverResendsAfterSuccessOrLostResponse(bool timeout)
    {
        var directory = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"));
        try
        {
            var config = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?>
                { ["Publications:Directory"] = directory }).Build();
            var id = Guid.NewGuid();
            var calls = 0;
            Task<string> Send() { calls++; return timeout ? Task.FromException<string>(new HttpRequestException("Lost response")) : Task.FromResult("page_post"); }
            await new PublicationStore(config).Execute(id, "client", "page", "user", "text", Send);
            // Recreate the store to simulate a process restart with the same persistent volume.
            var store = new PublicationStore(config);
            var result = await store.Execute(id, "client", "page", "user", "text", Send);
            Assert.Equal(1, calls);
            Assert.Contains(timeout ? "unknown" : "accepted", result);
            await Assert.ThrowsAsync<InvalidOperationException>(() => store.Execute(id, "other-client", "page", "user", "text", Send));
        }
        finally { if (Directory.Exists(directory)) Directory.Delete(directory, true); }
    }
}
