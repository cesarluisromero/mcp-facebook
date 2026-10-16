using McpFacebook.Core;

namespace McpFacebook.Tests;

public class PublicationTests
{
    private static Publication Create() => new(Guid.NewGuid(), Guid.NewGuid(), "user", "Publicación de prueba");

    [Fact]
    public void TimeoutCannotCauseAutomaticDuplicateWrite()
    {
        var operation = Create();
        operation.Begin();
        operation.MarkUnknown();
        Assert.Throws<InvalidOperationException>(operation.Begin);
    }

    [Fact]
    public void ReceiptDoesNotProvePublicationWasVerified()
    {
        var operation = Create();
        operation.Begin();
        operation.Accept("123_456");
        Assert.Equal(PublicationState.Accepted, operation.State);
        Assert.Throws<InvalidOperationException>(() => operation.Verify("123_999"));
        operation.Verify("123_456");
        Assert.Equal(PublicationState.Verified, operation.State);
    }
}
