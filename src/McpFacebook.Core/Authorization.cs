namespace McpFacebook.Core;

[Flags]
public enum Permission { Read = 1, Publish = 2, Messaging = 4, Ads = 8, Admin = 16 }

public sealed record Membership(string Subject, Guid ClientId, Permission Permissions);
public sealed record Asset(Guid Id, Guid ClientId, string ExternalId, Permission Capabilities);

public static class Authorization
{
    public static void Require(string subject, Guid clientId, Asset asset,
        IEnumerable<Membership> memberships, Permission permission)
    {
        if (string.IsNullOrWhiteSpace(subject) || permission == 0 || asset.ClientId != clientId ||
            (asset.Capabilities & permission) != permission ||
            !memberships.Any(m => m.Subject == subject && m.ClientId == clientId &&
                (m.Permissions & permission) == permission))
            throw new UnauthorizedAccessException("No tienes permiso para operar sobre este activo del cliente.");
    }
}
