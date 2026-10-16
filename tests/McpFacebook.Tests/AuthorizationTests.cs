using McpFacebook.Core;

namespace McpFacebook.Tests;

public class AuthorizationTests
{
    [Fact]
    public void MembershipCannotAuthorizeAnotherClientsAsset()
    {
        var client = Guid.NewGuid();
        var other = Guid.NewGuid();
        var asset = new Asset(Guid.NewGuid(), other, "123", Permission.Publish);
        var memberships = new[] { new Membership("user", client, Permission.Publish) };
        Assert.Throws<UnauthorizedAccessException>(() => Authorization.Require("user", client, asset, memberships, Permission.Publish));
    }

    [Fact]
    public void ReadPermissionCannotAuthorizePublication()
    {
        var client = Guid.NewGuid();
        var asset = new Asset(Guid.NewGuid(), client, "123", Permission.Read | Permission.Publish);
        var memberships = new[] { new Membership("user", client, Permission.Read) };
        Assert.Throws<UnauthorizedAccessException>(() => Authorization.Require("user", client, asset, memberships, Permission.Publish));
    }

    [Fact]
    public void BothMembershipAndAssetMustPermitWrite()
    {
        var client = Guid.NewGuid();
        var asset = new Asset(Guid.NewGuid(), client, "123", Permission.Publish);
        Authorization.Require("user", client, asset, new[] { new Membership("user", client, Permission.Publish) }, Permission.Publish);
    }
}
