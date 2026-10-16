namespace McpFacebook.Core;

public enum PublicationState { Prepared, Executing, Accepted, Verified, Rejected, Unknown }

/// <summary>Tracks one immutable write. Ambiguous outcomes must be reconciled, never retried blindly.</summary>
public sealed class Publication
{
    public Guid Id { get; } = Guid.NewGuid();
    public Guid ClientId { get; }
    public Guid AssetId { get; }
    public string RequestedBy { get; }
    public string Text { get; }
    public PublicationState State { get; private set; } = PublicationState.Prepared;
    public string? ExternalId { get; private set; }

    public Publication(Guid clientId, Guid assetId, string requestedBy, string text)
    {
        if (clientId == Guid.Empty || assetId == Guid.Empty || string.IsNullOrWhiteSpace(requestedBy))
            throw new ArgumentException("Falta identificar al cliente, activo o usuario.");
        if (string.IsNullOrWhiteSpace(text) || text.Length > 63206)
            throw new ArgumentException("El texto debe contener entre 1 y 63206 caracteres.");
        ClientId = clientId;
        AssetId = assetId;
        RequestedBy = requestedBy;
        Text = text;
    }

    public void Begin()
    {
        RequireState(PublicationState.Prepared);
        State = PublicationState.Executing;
    }

    public void Accept(string externalId)
    {
        RequireState(PublicationState.Executing);
        if (string.IsNullOrWhiteSpace(externalId)) throw new ArgumentException("Falta el identificador de Meta.");
        ExternalId = externalId;
        State = PublicationState.Accepted;
    }

    public void Verify(string externalId)
    {
        RequireState(PublicationState.Accepted);
        if (ExternalId != externalId) throw new InvalidOperationException("La publicación comprobada no coincide.");
        State = PublicationState.Verified;
    }

    public void Reject() { RequireState(PublicationState.Executing); State = PublicationState.Rejected; }
    public void MarkUnknown() { RequireState(PublicationState.Executing); State = PublicationState.Unknown; }

    private void RequireState(PublicationState expected)
    {
        if (State != expected) throw new InvalidOperationException($"Estado incompatible: {State}.");
    }
}
