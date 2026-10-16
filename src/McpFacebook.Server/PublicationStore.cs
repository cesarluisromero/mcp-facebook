using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

/// <summary>Durable single-VPS write ledger. Never resends an uncertain operation.</summary>
public sealed class PublicationStore(IConfiguration configuration)
{
    private sealed record Entry(string Fingerprint, string State, string? PostId);

    public async Task<string> Execute(Guid operationId, string client, string page, string subject,
        string message, Func<Task<string>> send)
    {
        var directory = configuration["Publications:Directory"] ?? Path.Combine(AppContext.BaseDirectory, "operations");
        Directory.CreateDirectory(directory);
        var file = Path.Combine(directory, operationId.ToString("N") + ".json");
        var fingerprint = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(
            JsonSerializer.Serialize(new[] { client, page, subject, message }))));
        FileStream stream;
        try { stream = new FileStream(file, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None); }
        catch (IOException) { throw new InvalidOperationException("La operación está ocupada o su registro no está disponible. No crees otro UUID."); }
        await using (stream)
        {
            if (stream.Length > 0)
            {
                var prior = await JsonSerializer.DeserializeAsync<Entry>(stream)
                    ?? throw new InvalidOperationException("Registro ilegible. Reconciliar antes de publicar.");
                if (prior.Fingerprint != fingerprint)
                    throw new InvalidOperationException("Ese UUID pertenece a otra publicación o usuario.");
                return JsonSerializer.Serialize(new { operationId, state = prior.State, postId = prior.PostId,
                    retryAllowed = false });
            }
            void Save(Entry entry)
            {
                var bytes = JsonSerializer.SerializeToUtf8Bytes(entry);
                stream.Position = 0;
                stream.Write(bytes);
                stream.SetLength(bytes.Length);
                stream.Flush(flushToDisk: true);
            }
            // Persist BEFORE the external write; crashes leave an uncertain operation, never a blind retry.
            Save(new Entry(fingerprint, "unknown", null));
            try
            {
                var postId = await send();
                Save(new Entry(fingerprint, "accepted", postId));
                return JsonSerializer.Serialize(new { operationId, state = "accepted", postId, retryAllowed = false });
            }
            catch
            {
                // The request may have reached Meta even when the response was lost.
                return JsonSerializer.Serialize(new { operationId, state = "unknown", postId = (string?)null,
                    retryAllowed = false, instruction = "Comprueba las publicaciones de la página antes de crear otra operación. No se reintentó el envío." });
            }
        }
    }
}
