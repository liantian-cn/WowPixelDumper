using System.Text;
using System.Text.Json;
using Microsoft.Data.Sqlite;

namespace Dumper.NET.Core;

public sealed class NodeTitleManager : INodeTitleResolver, IDisposable
{
    public sealed record TitleRecord(
        int Id,
        byte[] FullBlob,
        string MiddleHash,
        string Title,
        string MatchType,
        string CreatedAt,
        string FootnoteTitle
    );

    public sealed record UnmatchedNode(
        string Hash,
        byte[] FullArray,
        byte[] MiddleArray,
        string ClosestTitle,
        double ClosestSimilarity,
        string Timestamp
    );

    public sealed record CosineMatch(
        string Hash,
        string Title,
        double Similarity,
        byte[] FullArray,
        string Timestamp
    );

    private readonly string _dbPath;
    private readonly ColorMap _colorMap;
    private readonly object _sync = new();

    private double _similarityThreshold;
    private readonly Dictionary<string, (string Title, int Id)> _hashMap = new();
    private readonly List<(int Id, byte[] MiddleArray, string Title)> _middleCache = [];

    private readonly HashSet<string> _unmatchedHashes = [];
    private readonly List<UnmatchedNode> _unmatchedNodes = [];
    private readonly List<CosineMatch> _cosineMatches = [];

    public NodeTitleManager(string dbPath, ColorMap colorMap, double similarityThreshold = 0.995)
    {
        _dbPath = dbPath;
        _colorMap = colorMap;
        _similarityThreshold = Math.Clamp(similarityThreshold, 0.0, 1.0);

        string? dir = Path.GetDirectoryName(_dbPath);
        if (!string.IsNullOrWhiteSpace(dir))
        {
            Directory.CreateDirectory(dir);
        }

        InitDatabase();
        LoadDataToMemory();
    }

    public string DbPath => _dbPath;

    public double SimilarityThreshold
    {
        get
        {
            lock (_sync)
            {
                return _similarityThreshold;
            }
        }
    }

    public string GetTitle(string middleHash, byte[] middleArray, byte[] fullArray)
    {
        lock (_sync)
        {
            if (_hashMap.TryGetValue(middleHash, out (string Title, int Id) hit))
            {
                return hit.Title;
            }

            if (_unmatchedHashes.Contains(middleHash))
            {
                return middleHash;
            }

            (int Id, string Title, double Similarity)? best = null;
            foreach ((int id, byte[] cachedMiddle, string title) in _middleCache)
            {
                double similarity = CosineSimilarity(middleArray, cachedMiddle);
                if (best is null || similarity > best.Value.Similarity)
                {
                    best = (id, title, similarity);
                }
            }

            if (best is not null && best.Value.Similarity >= _similarityThreshold)
            {
                AddTitle(fullArray, middleHash, middleArray, best.Value.Title, "cosine");

                _cosineMatches.Add(new CosineMatch(
                    middleHash,
                    best.Value.Title,
                    best.Value.Similarity,
                    fullArray.ToArray(),
                    DateTime.Now.ToString("O")));

                return best.Value.Title;
            }

            _unmatchedHashes.Add(middleHash);
            _unmatchedNodes.Add(new UnmatchedNode(
                middleHash,
                fullArray.ToArray(),
                middleArray.ToArray(),
                best?.Title ?? string.Empty,
                best?.Similarity ?? 0.0,
                DateTime.Now.ToString("O")));

            return middleHash;
        }
    }

    public int AddTitle(byte[] fullArray, string middleHash, byte[] middleArray, string title, string matchType = "manual")
    {
        lock (_sync)
        {
            byte[] fullData = Encoding.UTF8.GetBytes(Convert.ToBase64String(fullArray));
            string footnoteTitle = CalculateFootnoteTitle(fullArray);

            using SqliteConnection conn = new($"Data Source={_dbPath}");
            conn.Open();

            using SqliteCommand cmd = conn.CreateCommand();
            cmd.CommandText = @"
INSERT INTO node_titles (full_data, middle_hash, title, match_type, footnote_title)
VALUES ($full_data, $middle_hash, $title, $match_type, $footnote_title)
ON CONFLICT(middle_hash)
DO UPDATE SET
    full_data = excluded.full_data,
    title = excluded.title,
    match_type = excluded.match_type,
    footnote_title = excluded.footnote_title;";
            cmd.Parameters.AddWithValue("$full_data", fullData);
            cmd.Parameters.AddWithValue("$middle_hash", middleHash);
            cmd.Parameters.AddWithValue("$title", title);
            cmd.Parameters.AddWithValue("$match_type", matchType);
            cmd.Parameters.AddWithValue("$footnote_title", footnoteTitle);
            cmd.ExecuteNonQuery();

            int id;
            using SqliteCommand findId = conn.CreateCommand();
            findId.CommandText = "SELECT id FROM node_titles WHERE middle_hash = $middle_hash";
            findId.Parameters.AddWithValue("$middle_hash", middleHash);
            id = Convert.ToInt32(findId.ExecuteScalar());

            _hashMap[middleHash] = (title, id);

            int idx = _middleCache.FindIndex(v => v.Id == id);
            if (idx >= 0)
            {
                _middleCache[idx] = (id, middleArray.ToArray(), title);
            }
            else
            {
                _middleCache.Add((id, middleArray.ToArray(), title));
            }

            if (_unmatchedHashes.Remove(middleHash))
            {
                _unmatchedNodes.RemoveAll(v => string.Equals(v.Hash, middleHash, StringComparison.Ordinal));
            }

            return id;
        }
    }

    public bool ExportToJson(string path)
    {
        try
        {
            List<Dictionary<string, object?>> records = [];
            foreach (TitleRecord record in GetAllTitles())
            {
                if (record.FullBlob.Length != 8 * 8 * 3)
                {
                    continue;
                }

                records.Add(new Dictionary<string, object?>
                {
                    ["id"] = record.Id,
                    ["full"] = ToNestedArray(record.FullBlob, 8, 8),
                    ["middle"] = ToNestedArray(ExtractMiddle(record.FullBlob), 6, 6),
                    ["middle_hash"] = record.MiddleHash,
                    ["title"] = record.Title,
                    ["match_type"] = record.MatchType,
                    ["created_at"] = record.CreatedAt,
                });
            }

            string json = JsonSerializer.Serialize(records, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(path, json, Encoding.UTF8);
            return true;
        }
        catch
        {
            return false;
        }
    }

    public bool ImportFromJson(string path, bool merge = true)
    {
        try
        {
            string json = File.ReadAllText(path, Encoding.UTF8);
            JsonDocument doc = JsonDocument.Parse(json);

            lock (_sync)
            {
                if (!merge)
                {
                    using SqliteConnection clearConn = new($"Data Source={_dbPath}");
                    clearConn.Open();
                    using SqliteCommand clearCmd = clearConn.CreateCommand();
                    clearCmd.CommandText = "DELETE FROM node_titles";
                    clearCmd.ExecuteNonQuery();

                    _hashMap.Clear();
                    _middleCache.Clear();
                }

                foreach (JsonElement item in doc.RootElement.EnumerateArray())
                {
                    if (!item.TryGetProperty("middle_hash", out JsonElement hashProp) ||
                        !item.TryGetProperty("title", out JsonElement titleProp) ||
                        !item.TryGetProperty("full", out JsonElement fullProp))
                    {
                        continue;
                    }

                    string? middleHash = hashProp.GetString();
                    string? title = titleProp.GetString();
                    if (string.IsNullOrWhiteSpace(middleHash) || string.IsNullOrWhiteSpace(title))
                    {
                        continue;
                    }

                    if (_hashMap.ContainsKey(middleHash))
                    {
                        continue;
                    }

                    byte[] fullRaw = ParseNestedArray(fullProp);
                    if (fullRaw.Length != 8 * 8 * 3)
                    {
                        continue;
                    }

                    byte[] middle = ExtractMiddle(fullRaw);
                    string matchType = item.TryGetProperty("match_type", out JsonElement mt) && !mt.ValueKind.Equals(JsonValueKind.Null)
                        ? (mt.GetString() ?? "manual")
                        : "manual";

                    AddTitle(fullRaw, middleHash, middle, title, matchType);
                }
            }

            return true;
        }
        catch
        {
            return false;
        }
    }

    public void UpdateThreshold(double threshold)
    {
        lock (_sync)
        {
            _similarityThreshold = Math.Clamp(threshold, 0.0, 1.0);
        }
    }

    public List<TitleRecord> GetAllTitles()
    {
        lock (_sync)
        {
            List<TitleRecord> records = [];
            using SqliteConnection conn = new($"Data Source={_dbPath}");
            conn.Open();

            using SqliteCommand cmd = conn.CreateCommand();
            cmd.CommandText = @"
SELECT id, full_data, middle_hash, title, match_type, created_at, footnote_title
FROM node_titles
ORDER BY id DESC;";

            using SqliteDataReader reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                byte[] fullBlob = DecodeBase64Blob(ReadBlob(reader, 1));
                records.Add(new TitleRecord(
                    reader.GetInt32(0),
                    fullBlob,
                    reader.GetString(2),
                    reader.GetString(3),
                    reader.IsDBNull(4) ? "manual" : reader.GetString(4),
                    reader.IsDBNull(5) ? string.Empty : reader.GetString(5),
                    reader.IsDBNull(6) ? "Unknown" : reader.GetString(6)));
            }

            return records;
        }
    }

    public bool UpdateTitle(int id, string newTitle, string? matchType = null)
    {
        if (string.IsNullOrWhiteSpace(newTitle))
        {
            return false;
        }

        lock (_sync)
        {
            using SqliteConnection conn = new($"Data Source={_dbPath}");
            conn.Open();

            using SqliteCommand cmd = conn.CreateCommand();
            if (string.IsNullOrWhiteSpace(matchType))
            {
                cmd.CommandText = "UPDATE node_titles SET title = $title WHERE id = $id;";
            }
            else
            {
                cmd.CommandText = "UPDATE node_titles SET title = $title, match_type = $match_type WHERE id = $id;";
                cmd.Parameters.AddWithValue("$match_type", matchType);
            }

            cmd.Parameters.AddWithValue("$title", newTitle.Trim());
            cmd.Parameters.AddWithValue("$id", id);
            int rows = cmd.ExecuteNonQuery();
            if (rows <= 0)
            {
                return false;
            }

            for (int i = 0; i < _middleCache.Count; i++)
            {
                if (_middleCache[i].Id == id)
                {
                    _middleCache[i] = (_middleCache[i].Id, _middleCache[i].MiddleArray, newTitle.Trim());
                }
            }

            List<string> keys = _hashMap.Where(kv => kv.Value.Id == id).Select(kv => kv.Key).ToList();
            foreach (string key in keys)
            {
                _hashMap[key] = (newTitle.Trim(), id);
            }

            return true;
        }
    }

    public bool DeleteTitle(int id)
    {
        lock (_sync)
        {
            using SqliteConnection conn = new($"Data Source={_dbPath}");
            conn.Open();

            string? middleHash = null;
            using (SqliteCommand find = conn.CreateCommand())
            {
                find.CommandText = "SELECT middle_hash FROM node_titles WHERE id = $id;";
                find.Parameters.AddWithValue("$id", id);
                middleHash = find.ExecuteScalar()?.ToString();
            }

            using SqliteCommand cmd = conn.CreateCommand();
            cmd.CommandText = "DELETE FROM node_titles WHERE id = $id;";
            cmd.Parameters.AddWithValue("$id", id);
            int rows = cmd.ExecuteNonQuery();
            if (rows <= 0)
            {
                return false;
            }

            _middleCache.RemoveAll(v => v.Id == id);
            if (!string.IsNullOrEmpty(middleHash))
            {
                _hashMap.Remove(middleHash);
            }

            return true;
        }
    }

    public List<UnmatchedNode> GetUnmatchedNodes()
    {
        lock (_sync)
        {
            return _unmatchedNodes
                .Select(v => new UnmatchedNode(v.Hash, v.FullArray.ToArray(), v.MiddleArray.ToArray(), v.ClosestTitle, v.ClosestSimilarity, v.Timestamp))
                .ToList();
        }
    }

    public List<CosineMatch> GetCosineMatches()
    {
        lock (_sync)
        {
            return _cosineMatches
                .Select(v => new CosineMatch(v.Hash, v.Title, v.Similarity, v.FullArray.ToArray(), v.Timestamp))
                .ToList();
        }
    }

    public void ClearUnmatchedCache()
    {
        lock (_sync)
        {
            _unmatchedHashes.Clear();
            _unmatchedNodes.Clear();
        }
    }

    public void ClearCosineMatchesCache()
    {
        lock (_sync)
        {
            _cosineMatches.Clear();
        }
    }

    public Dictionary<string, int> GetStats()
    {
        lock (_sync)
        {
            using SqliteConnection conn = new($"Data Source={_dbPath}");
            conn.Open();

            int total = ExecuteCount(conn, "SELECT COUNT(*) FROM node_titles");
            int manual = ExecuteCount(conn, "SELECT COUNT(*) FROM node_titles WHERE match_type = 'manual'");
            int cosine = ExecuteCount(conn, "SELECT COUNT(*) FROM node_titles WHERE match_type = 'cosine'");

            return new Dictionary<string, int>
            {
                ["total"] = total,
                ["manual"] = manual,
                ["cosine"] = cosine,
                ["hash_cached"] = _hashMap.Count,
                ["unmatched_memory"] = _unmatchedHashes.Count,
                ["cosine_matches_session"] = _cosineMatches.Count,
            };
        }
    }

    private static int ExecuteCount(SqliteConnection conn, string sql)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = sql;
        object? value = cmd.ExecuteScalar();
        return value is null ? 0 : Convert.ToInt32(value);
    }

    private void InitDatabase()
    {
        using SqliteConnection conn = new($"Data Source={_dbPath}");
        conn.Open();

        using SqliteCommand create = conn.CreateCommand();
        create.CommandText = @"
CREATE TABLE IF NOT EXISTS node_titles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_data BLOB NOT NULL,
    middle_hash TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    match_type TEXT DEFAULT 'manual',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    footnote_title TEXT DEFAULT 'Unknown'
);
CREATE INDEX IF NOT EXISTS idx_hash ON node_titles(middle_hash);";
        create.ExecuteNonQuery();

        using SqliteCommand pragma = conn.CreateCommand();
        pragma.CommandText = "PRAGMA table_info(node_titles);";
        using SqliteDataReader reader = pragma.ExecuteReader();
        bool hasFootnote = false;
        while (reader.Read())
        {
            if (string.Equals(reader.GetString(1), "footnote_title", StringComparison.OrdinalIgnoreCase))
            {
                hasFootnote = true;
                break;
            }
        }

        if (!hasFootnote)
        {
            using SqliteCommand alter = conn.CreateCommand();
            alter.CommandText = "ALTER TABLE node_titles ADD COLUMN footnote_title TEXT DEFAULT 'Unknown';";
            alter.ExecuteNonQuery();
        }
    }

    private void LoadDataToMemory()
    {
        lock (_sync)
        {
            _hashMap.Clear();
            _middleCache.Clear();

            using SqliteConnection conn = new($"Data Source={_dbPath}");
            conn.Open();

            using SqliteCommand cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT id, full_data, middle_hash, title FROM node_titles";
            using SqliteDataReader reader = cmd.ExecuteReader();

            while (reader.Read())
            {
                int id = reader.GetInt32(0);
                byte[] fullBlob = ReadBlob(reader, 1);
                string middleHash = reader.GetString(2);
                string title = reader.GetString(3);

                byte[] fullRaw = DecodeBase64Blob(fullBlob);
                if (fullRaw.Length != 8 * 8 * 3)
                {
                    continue;
                }

                byte[] middle = ExtractMiddle(fullRaw);
                _hashMap[middleHash] = (title, id);
                _middleCache.Add((id, middle, title));
            }
        }
    }

    private string CalculateFootnoteTitle(byte[] fullArray)
    {
        if (fullArray.Length != 8 * 8 * 3)
        {
            return "Unknown";
        }

        int idx = ((6 * 8) + 6) * 3;
        byte r = fullArray[idx];
        byte g = fullArray[idx + 1];
        byte b = fullArray[idx + 2];

        int[] coords =
        [
            ((6 * 8) + 6) * 3,
            ((6 * 8) + 7) * 3,
            ((7 * 8) + 6) * 3,
            ((7 * 8) + 7) * 3,
        ];

        foreach (int c in coords)
        {
            if (fullArray[c] != r || fullArray[c + 1] != g || fullArray[c + 2] != b)
            {
                return "Unknown";
            }
        }

        string key = $"{r},{g},{b}";
        return _colorMap.IconType.TryGetValue(key, out string? value) ? value : "Unknown";
    }

    private static double CosineSimilarity(byte[] a, byte[] b)
    {
        if (a.Length != b.Length || a.Length == 0)
        {
            return 0.0;
        }

        double dot = 0.0;
        double normA = 0.0;
        double normB = 0.0;

        for (int i = 0; i < a.Length; i++)
        {
            double va = a[i];
            double vb = b[i];
            dot += va * vb;
            normA += va * va;
            normB += vb * vb;
        }

        if (normA <= 0 || normB <= 0)
        {
            return 0.0;
        }

        return dot / (Math.Sqrt(normA) * Math.Sqrt(normB));
    }

    private static byte[] ExtractMiddle(byte[] fullRaw)
    {
        byte[] middle = new byte[6 * 6 * 3];
        int di = 0;
        for (int y = 1; y < 7; y++)
        {
            for (int x = 1; x < 7; x++)
            {
                int si = ((y * 8) + x) * 3;
                middle[di++] = fullRaw[si];
                middle[di++] = fullRaw[si + 1];
                middle[di++] = fullRaw[si + 2];
            }
        }

        return middle;
    }

    private static byte[] DecodeBase64Blob(byte[] blob)
    {
        try
        {
            string text = Encoding.UTF8.GetString(blob);
            return Convert.FromBase64String(text);
        }
        catch
        {
            return blob;
        }
    }

    private static byte[] ReadBlob(SqliteDataReader reader, int ordinal)
    {
        if (reader.IsDBNull(ordinal))
        {
            return [];
        }

        long length = reader.GetBytes(ordinal, 0, null, 0, 0);
        byte[] buffer = new byte[length];
        reader.GetBytes(ordinal, 0, buffer, 0, buffer.Length);
        return buffer;
    }

    private static List<List<List<byte>>> ToNestedArray(byte[] data, int width, int height)
    {
        List<List<List<byte>>> result = [];
        int idx = 0;
        for (int y = 0; y < height; y++)
        {
            List<List<byte>> row = [];
            for (int x = 0; x < width; x++)
            {
                row.Add([data[idx], data[idx + 1], data[idx + 2]]);
                idx += 3;
            }

            result.Add(row);
        }

        return result;
    }

    private static byte[] ParseNestedArray(JsonElement element)
    {
        List<byte> bytes = [];
        foreach (JsonElement row in element.EnumerateArray())
        {
            foreach (JsonElement pixel in row.EnumerateArray())
            {
                int i = 0;
                foreach (JsonElement channel in pixel.EnumerateArray())
                {
                    if (i >= 3)
                    {
                        break;
                    }

                    bytes.Add((byte)channel.GetInt32());
                    i++;
                }
            }
        }

        return bytes.ToArray();
    }

    public void Dispose()
    {
    }
}
