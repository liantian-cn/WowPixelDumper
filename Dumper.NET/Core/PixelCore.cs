using System.Drawing;
using System.IO.Hashing;
using System.Text.Json;

namespace Dumper.NET.Core;

public sealed class ColorMap
{
    public Dictionary<string, string> IconType { get; init; } = new();
    public Dictionary<string, string> Class { get; init; } = new();
    public Dictionary<string, string> Role { get; init; } = new();

    public static ColorMap Load(string path)
    {
        string json = File.ReadAllText(path);
        ColorMap? map = JsonSerializer.Deserialize<ColorMap>(json);
        return map ?? new ColorMap();
    }
}

public readonly record struct PixelFrame(int Width, int Height, byte[] Bgra)
{
    public bool IsAllBlack()
    {
        for (int i = 0; i < Bgra.Length; i += 4)
        {
            if (Bgra[i] != 0 || Bgra[i + 1] != 0 || Bgra[i + 2] != 0)
            {
                return false;
            }
        }

        return true;
    }

    public PixelFrame Crop((int Left, int Top, int Right, int Bottom) bounds)
    {
        int width = bounds.Right - bounds.Left;
        int height = bounds.Bottom - bounds.Top;
        byte[] data = new byte[width * height * 4];

        for (int y = 0; y < height; y++)
        {
            int srcOffset = ((bounds.Top + y) * Width + bounds.Left) * 4;
            int dstOffset = y * width * 4;
            Buffer.BlockCopy(Bgra, srcOffset, data, dstOffset, width * 4);
        }

        return new PixelFrame(width, height, data);
    }
}

public sealed class TemplateImage
{
    public int Width { get; }
    public int Height { get; }
    public byte[] Bgr { get; }

    public TemplateImage(int width, int height, byte[] bgr)
    {
        Width = width;
        Height = height;
        Bgr = bgr;
    }

    public static TemplateImage Load(string path)
    {
        using Bitmap bmp = new(path);
        byte[] bgr = new byte[bmp.Width * bmp.Height * 3];

        for (int y = 0; y < bmp.Height; y++)
        {
            for (int x = 0; x < bmp.Width; x++)
            {
                Color color = bmp.GetPixel(x, y);
                int idx = (y * bmp.Width + x) * 3;
                bgr[idx] = color.B;
                bgr[idx + 1] = color.G;
                bgr[idx + 2] = color.R;
            }
        }

        return new TemplateImage(bmp.Width, bmp.Height, bgr);
    }
}

public static class TemplateMatcher
{
    public static List<(int X, int Y)> FindAllMatches(PixelFrame frame, TemplateImage template, int tolerance = 0)
    {
        List<(int X, int Y)> matches = new();

        if (template.Width > frame.Width || template.Height > frame.Height)
        {
            return matches;
        }

        int maxX = frame.Width - template.Width;
        int maxY = frame.Height - template.Height;

        for (int y = 0; y <= maxY; y++)
        {
            for (int x = 0; x <= maxX; x++)
            {
                if (IsMatch(frame, template, x, y, tolerance))
                {
                    matches.Add((x, y));
                }
            }
        }

        matches.Sort((a, b) => a.X != b.X ? a.X.CompareTo(b.X) : a.Y.CompareTo(b.Y));
        return matches;
    }

    public static (int Left, int Top, int Right, int Bottom)? FindTemplateBounds(PixelFrame frame, TemplateImage template, int tolerance = 0)
    {
        List<(int X, int Y)> matches = FindAllMatches(frame, template, tolerance);
        if (matches.Count != 2)
        {
            return null;
        }

        (int x1, int y1) = matches[0];
        (int x2, int y2) = matches[1];

        int right1 = x1 + template.Width;
        int bottom1 = y1 + template.Height;
        int right2 = x2 + template.Width;
        int bottom2 = y2 + template.Height;

        int left = Math.Min(x1, x2);
        int top = Math.Min(y1, y2);
        int right = Math.Max(right1, right2);
        int bottom = Math.Max(bottom1, bottom2);

        int width = right - left;
        int height = bottom - top;
        if (width % 8 != 0 || height % 8 != 0)
        {
            return null;
        }

        return (left, top, right, bottom);
    }

    private static bool IsMatch(PixelFrame frame, TemplateImage template, int originX, int originY, int tolerance)
    {
        for (int ty = 0; ty < template.Height; ty++)
        {
            for (int tx = 0; tx < template.Width; tx++)
            {
                int templateIdx = (ty * template.Width + tx) * 3;
                int frameIdx = ((originY + ty) * frame.Width + (originX + tx)) * 4;

                int db = Math.Abs(frame.Bgra[frameIdx] - template.Bgr[templateIdx]);
                int dg = Math.Abs(frame.Bgra[frameIdx + 1] - template.Bgr[templateIdx + 1]);
                int dr = Math.Abs(frame.Bgra[frameIdx + 2] - template.Bgr[templateIdx + 2]);

                if (db > tolerance || dg > tolerance || dr > tolerance)
                {
                    return false;
                }
            }
        }

        return true;
    }
}

public interface INodeTitleResolver
{
    string GetTitle(string middleHash, byte[] middleArray, byte[] fullArray);
}

public sealed class HashTitleResolver : INodeTitleResolver
{
    public string GetTitle(string middleHash, byte[] middleArray, byte[] fullArray)
    {
        return middleHash;
    }
}

public sealed class PixelBlock
{
    private readonly byte[] _data;
    private string? _hash;

    public PixelBlock(byte[] data)
    {
        _data = data;
    }

    public byte[] Data => _data;

    public string Hash
    {
        get
        {
            if (_hash is null)
            {
                ulong hash = XxHash3.HashToUInt64(_data);
                _hash = hash.ToString("x16");
            }

            return _hash;
        }
    }

    public double Mean => _data.Length == 0 ? 0.0 : _data.Average(v => (double)v);

    public double Percent => Mean / 255.0 * 100.0;

    public double Decimal => Mean / 255.0;

    public bool IsPure
    {
        get
        {
            if (_data.Length < 3)
            {
                return true;
            }

            byte r = _data[0];
            byte g = _data[1];
            byte b = _data[2];

            for (int i = 3; i < _data.Length; i += 3)
            {
                if (_data[i] != r || _data[i + 1] != g || _data[i + 2] != b)
                {
                    return false;
                }
            }

            return true;
        }
    }

    public bool IsNotPure => !IsPure;

    public (byte R, byte G, byte B) Color => (_data[0], _data[1], _data[2]);

    public string ColorString => $"{_data[0]},{_data[1]},{_data[2]}";

    public bool IsBlack => IsPure && _data[0] == 0 && _data[1] == 0 && _data[2] == 0;

    public bool IsWhite => IsPure && _data[0] == 255 && _data[1] == 255 && _data[2] == 255;

    public int WhiteCount
    {
        get
        {
            int count = 0;
            for (int i = 0; i < _data.Length; i += 3)
            {
                if (_data[i] == 255 && _data[i + 1] == 255 && _data[i + 2] == 255)
                {
                    count++;
                }
            }

            return count;
        }
    }

    public double Remaining
    {
        get
        {
            int y = (int)Mean;
            List<(double Time, int Bright)> points =
            [
                (0.0, 0),
                (5.0, 100),
                (30.0, 150),
                (155.0, 200),
                (375.0, 255),
            ];

            if (y <= points[0].Bright)
            {
                return points[0].Time;
            }

            if (y >= points[^1].Bright)
            {
                return points[^1].Time;
            }

            for (int i = 0; i < points.Count - 1; i++)
            {
                (double x1, int y1) = points[i];
                (double x2, int y2) = points[i + 1];

                if (y >= y1 && y <= y2)
                {
                    return x1 + ((x2 - x1) * (y - y1) / (y2 - y1));
                }
            }

            return 0.0;
        }
    }
}

public sealed class Node
{
    private readonly byte[] _full;
    private readonly ColorMap _colorMap;
    private readonly INodeTitleResolver _resolver;

    private PixelBlock? _fullBlock;
    private PixelBlock? _middle;
    private PixelBlock? _inner;
    private PixelBlock? _footnote;
    private (PixelBlock, PixelBlock, PixelBlock, PixelBlock)? _sub;

    public Node(byte[] full, ColorMap colorMap, INodeTitleResolver resolver)
    {
        _full = full;
        _colorMap = colorMap;
        _resolver = resolver;
    }

    public PixelBlock Full => _fullBlock ??= new PixelBlock(_full);

    public PixelBlock Middle => _middle ??= new PixelBlock(ExtractRegion(_full, 8, 8, 1, 1, 6, 6));

    public PixelBlock Inner => _inner ??= new PixelBlock(ExtractRegion(_full, 8, 8, 2, 2, 4, 4));

    public PixelBlock Footnote => _footnote ??= new PixelBlock(ExtractRegion(_full, 8, 8, 6, 6, 2, 2));

    public (PixelBlock, PixelBlock, PixelBlock, PixelBlock) MixNode
    {
        get
        {
            if (_sub is null)
            {
                _sub = (
                    new PixelBlock(ExtractRegion(_full, 8, 8, 1, 1, 2, 2)),
                    new PixelBlock(ExtractRegion(_full, 8, 8, 5, 1, 2, 2)),
                    new PixelBlock(ExtractRegion(_full, 8, 8, 1, 5, 2, 2)),
                    new PixelBlock(ExtractRegion(_full, 8, 8, 5, 5, 2, 2))
                );
            }

            return _sub.Value;
        }
    }

    public double Mean => Inner.Mean;
    public double Percent => Inner.Percent;
    public double Decimal => Inner.Decimal;
    public bool IsPure => Inner.IsPure;
    public bool IsNotPure => Inner.IsNotPure;
    public bool IsBlack => Inner.IsBlack;
    public bool IsWhite => Inner.IsWhite;
    public string ColorString => Inner.ColorString;
    public double Remaining => Inner.Remaining;
    public string Hash => Middle.Hash;

    public int WhiteCount
    {
        get
        {
            if (Inner.IsPure)
            {
                return 0;
            }

            int whiteCount = Middle.WhiteCount;
            if (whiteCount <= 9)
            {
                return whiteCount;
            }

            if (whiteCount == 10)
            {
                return 0;
            }

            return 20;
        }
    }

    public string Title => _resolver.GetTitle(Middle.Hash, Middle.Data, Full.Data);

    public string FootnoteTitle
    {
        get
        {
            if (!Footnote.IsPure)
            {
                return "Unknown";
            }

            return _colorMap.IconType.TryGetValue(Footnote.ColorString, out string? value)
                ? value
                : "Unknown";
        }
    }

    private static byte[] ExtractRegion(byte[] source, int width, int height, int x, int y, int regionWidth, int regionHeight)
    {
        byte[] result = new byte[regionWidth * regionHeight * 3];

        for (int row = 0; row < regionHeight; row++)
        {
            int srcRow = y + row;
            for (int col = 0; col < regionWidth; col++)
            {
                int srcCol = x + col;
                int srcIdx = (srcRow * width + srcCol) * 3;
                int dstIdx = (row * regionWidth + col) * 3;
                result[dstIdx] = source[srcIdx];
                result[dstIdx + 1] = source[srcIdx + 1];
                result[dstIdx + 2] = source[srcIdx + 2];
            }
        }

        return result;
    }
}

public sealed class NodeExtractor
{
    private readonly byte[] _rgb;
    private readonly int _width;
    private readonly int _height;
    private readonly ColorMap _colorMap;
    private readonly INodeTitleResolver _resolver;

    public NodeExtractor(PixelFrame frame, ColorMap colorMap, INodeTitleResolver resolver)
    {
        _width = frame.Width;
        _height = frame.Height;
        _rgb = BgraToRgb(frame.Bgra);
        _colorMap = colorMap;
        _resolver = resolver;
    }

    public Node Node(int x, int y)
    {
        int maxX = _width / 8;
        int maxY = _height / 8;
        if (x >= maxX || y >= maxY)
        {
            throw new ArgumentOutOfRangeException(nameof(x), $"节点坐标({x},{y})超出范围({maxX},{maxY})");
        }

        int startX = x * 8;
        int startY = y * 8;
        byte[] full = new byte[8 * 8 * 3];

        for (int row = 0; row < 8; row++)
        {
            int srcOffset = ((startY + row) * _width + startX) * 3;
            int dstOffset = row * 8 * 3;
            Buffer.BlockCopy(_rgb, srcOffset, full, dstOffset, 8 * 3);
        }

        return new Node(full, _colorMap, _resolver);
    }

    public double ReadHealthBar(int left, int top, int length)
    {
        int whiteCount = 0;
        int totalCount = 0;

        for (int x = left; x < left + length; x++)
        {
            Node node = Node(x, top);
            byte[] data = node.Full.Data;
            for (int row = 3; row <= 4; row++)
            {
                for (int col = 0; col < 8; col++)
                {
                    int idx = (row * 8 + col) * 3;
                    if (data[idx] == 255 && data[idx + 1] == 255 && data[idx + 2] == 255)
                    {
                        whiteCount++;
                    }

                    totalCount++;
                }
            }
        }

        return totalCount == 0 ? 0.0 : (double)whiteCount / totalCount;
    }

    public (List<Dictionary<string, object?>>, Dictionary<string, Dictionary<string, object?>>) ReadSpellSequence(int left, int top, int length)
    {
        List<Dictionary<string, object?>> sequence = new();
        Dictionary<string, Dictionary<string, object?>> dict = new();

        for (int x = left; x < left + length; x++)
        {
            Node iconNode = Node(x, top);
            if (iconNode.IsPure && iconNode.IsBlack)
            {
                continue;
            }

            Node mixNode = Node(x, top + 1);
            Node chargeNode = Node(x, top + 2);
            (PixelBlock cooldownBlock, PixelBlock usableBlock, PixelBlock heightBlock, PixelBlock knownBlock) = mixNode.MixNode;

            Dictionary<string, object?> spell = new()
            {
                ["title"] = iconNode.Title,
                ["remaining"] = cooldownBlock.Remaining,
                ["height"] = heightBlock.IsWhite,
                ["charge"] = (chargeNode.IsPure && chargeNode.IsBlack) ? 0 : chargeNode.WhiteCount,
                ["known"] = knownBlock.IsWhite,
                ["usable"] = usableBlock.IsWhite,
            };

            sequence.Add(spell);
            dict[iconNode.Title] = spell;
        }

        return (sequence, dict);
    }

    public (List<Dictionary<string, object?>>, Dictionary<string, Dictionary<string, object?>>) ReadAuraSequence(int left, int top, int length)
    {
        List<Dictionary<string, object?>> sequence = new();
        Dictionary<string, Dictionary<string, object?>> dict = new();

        for (int x = left; x < left + length; x++)
        {
            Node iconNode = Node(x, top);
            if (iconNode.IsPure && iconNode.IsBlack)
            {
                continue;
            }

            Node mixNode = Node(x, top + 1);
            Node countNode = Node(x, top + 2);
            (PixelBlock remainBlock, PixelBlock typeBlock, PixelBlock foreverBlock, PixelBlock _) = mixNode.MixNode;

            string auraType = _colorMap.IconType.TryGetValue(typeBlock.ColorString, out string? auraTypeValue)
                ? auraTypeValue
                : "Unknown";

            Dictionary<string, object?> aura = new()
            {
                ["title"] = iconNode.Title,
                ["remaining"] = remainBlock.IsBlack ? 0.0 : remainBlock.Remaining,
                ["type"] = auraType,
                ["count"] = countNode.WhiteCount,
                ["forever"] = foreverBlock.IsWhite,
            };

            sequence.Add(aura);
            dict[iconNode.Title] = aura;
        }

        return (sequence, dict);
    }

    private static byte[] BgraToRgb(byte[] bgra)
    {
        byte[] rgb = new byte[(bgra.Length / 4) * 3];
        int j = 0;
        for (int i = 0; i < bgra.Length; i += 4)
        {
            rgb[j++] = bgra[i + 2];
            rgb[j++] = bgra[i + 1];
            rgb[j++] = bgra[i];
        }

        return rgb;
    }
}

public static class NodeDataExtractor
{
    public static Dictionary<string, object?> ExtractAllData(NodeExtractor extractor, ColorMap colorMap)
    {
        Dictionary<string, object?> data = new()
        {
            ["timestamp"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
            ["misc"] = new Dictionary<string, object?>(),
            ["spec"] = new Dictionary<string, object?>(),
            ["player"] = new Dictionary<string, object?> { ["unitToken"] = "player" },
            ["target"] = new Dictionary<string, object?> { ["unitToken"] = "target" },
            ["focus"] = new Dictionary<string, object?> { ["unitToken"] = "focus" },
            ["party"] = new Dictionary<string, object?>(),
            ["signal"] = new Dictionary<string, object?>(),
        };

        try
        {
            Dictionary<string, object?> misc = (Dictionary<string, object?>)data["misc"]!;
            misc["ac"] = extractor.Node(34, 5).Title;
            misc["on_chat"] = extractor.Node(35, 5).IsWhite;
            misc["is_targeting"] = extractor.Node(36, 5).IsWhite;

            Dictionary<string, object?> player = (Dictionary<string, object?>)data["player"]!;
            Dictionary<string, object?> playerAura = new()
            {
                ["buff_sequence"] = new List<Dictionary<string, object?>>(),
                ["buff"] = new Dictionary<string, Dictionary<string, object?>>(),
                ["debuff_sequence"] = new List<Dictionary<string, object?>>(),
                ["debuff"] = new Dictionary<string, Dictionary<string, object?>>(),
            };
            player["aura"] = playerAura;

            (List<Dictionary<string, object?>> buffSeq, Dictionary<string, Dictionary<string, object?>> buffDict) = extractor.ReadAuraSequence(2, 5, 32);
            (List<Dictionary<string, object?>> debuffSeq, Dictionary<string, Dictionary<string, object?>> debuffDict) = extractor.ReadAuraSequence(2, 8, 8);
            playerAura["buff_sequence"] = buffSeq;
            playerAura["buff"] = buffDict;
            playerAura["debuff_sequence"] = debuffSeq;
            playerAura["debuff"] = debuffDict;

            (List<Dictionary<string, object?>> spellSeq, Dictionary<string, Dictionary<string, object?>> spellDict) = extractor.ReadSpellSequence(2, 2, 36);
            player["spell_sequence"] = spellSeq;
            player["spell"] = spellDict;

            Dictionary<string, object?> playerStatus = new()
            {
                ["unit_damage_absorbs"] = extractor.ReadHealthBar(38, 2, 8) * 100,
                ["unit_heal_absorbs"] = extractor.ReadHealthBar(38, 3, 8) * 100,
                ["unit_health"] = extractor.Node(45, 4).Percent,
                ["unit_power"] = extractor.Node(45, 5).Percent,
                ["unit_in_combat"] = extractor.Node(38, 4).IsWhite,
                ["unit_in_movement"] = extractor.Node(39, 4).IsWhite,
                ["unit_in_vehicle"] = extractor.Node(40, 4).IsWhite,
                ["unit_is_empowering"] = extractor.Node(41, 4).IsWhite,
                ["unit_cast_icon"] = null,
                ["unit_cast_duration"] = null,
                ["unit_channel_icon"] = null,
                ["unit_channel_duration"] = null,
                ["unit_class"] = "NONE",
                ["unit_role"] = "NONE",
                ["unit_is_dead_or_ghost"] = extractor.Node(40, 5).IsWhite,
                ["unit_in_range"] = true,
            };
            player["status"] = playerStatus;

            Node castIcon = extractor.Node(42, 4);
            if (castIcon.IsNotPure)
            {
                playerStatus["unit_cast_icon"] = castIcon.Title;
                playerStatus["unit_cast_duration"] = extractor.Node(43, 4).Percent;
            }

            Node channelIcon = extractor.Node(42, 5);
            if (channelIcon.IsNotPure)
            {
                playerStatus["unit_channel_icon"] = channelIcon.Title;
                playerStatus["unit_channel_duration"] = extractor.Node(43, 5).Percent;
            }

            Node classNode = extractor.Node(38, 5);
            if (classNode.IsPure)
            {
                playerStatus["unit_class"] = colorMap.Class.TryGetValue(classNode.ColorString, out string? cls) ? cls : "NONE";
            }

            Node roleNode = extractor.Node(39, 5);
            if (roleNode.IsPure)
            {
                playerStatus["unit_role"] = colorMap.Role.TryGetValue(roleNode.ColorString, out string? role) ? role : "NONE";
            }

            Dictionary<string, object?> target = (Dictionary<string, object?>)data["target"]!;
            Dictionary<string, object?> targetAura = new()
            {
                ["debuff_sequence"] = new List<Dictionary<string, object?>>(),
                ["debuff"] = new Dictionary<string, Dictionary<string, object?>>(),
            };
            target["aura"] = targetAura;

            Dictionary<string, object?> targetStatus = new() { ["exists"] = extractor.Node(38, 6).IsWhite };
            target["status"] = targetStatus;

            if ((bool)targetStatus["exists"]!)
            {
                (List<Dictionary<string, object?>> tDebuffSeq, Dictionary<string, Dictionary<string, object?>> tDebuffDict) = extractor.ReadAuraSequence(10, 8, 16);
                targetAura["debuff_sequence"] = tDebuffSeq;
                targetAura["debuff"] = tDebuffDict;

                targetStatus["unit_can_attack"] = extractor.Node(39, 6).IsWhite;
                targetStatus["unit_is_self"] = extractor.Node(40, 6).IsWhite;
                targetStatus["unit_is_alive"] = extractor.Node(41, 6).IsWhite;
                targetStatus["unit_in_combat"] = extractor.Node(42, 6).IsWhite;
                targetStatus["unit_in_range"] = extractor.Node(43, 6).IsWhite;
                targetStatus["unit_health"] = extractor.Node(45, 6).Percent;
                targetStatus["unit_cast_icon"] = null;
                targetStatus["unit_cast_duration"] = null;
                targetStatus["unit_cast_interruptible"] = null;
                targetStatus["unit_channel_icon"] = null;
                targetStatus["unit_channel_duration"] = null;
                targetStatus["unit_channel_interruptible"] = null;

                Node targetCast = extractor.Node(38, 7);
                if (targetCast.IsNotPure)
                {
                    targetStatus["unit_cast_icon"] = targetCast.Title;
                    targetStatus["unit_cast_duration"] = extractor.Node(39, 7).Percent;
                    targetStatus["unit_cast_interruptible"] = extractor.Node(40, 7).IsWhite;
                }

                Node targetChannel = extractor.Node(41, 7);
                if (targetChannel.IsNotPure)
                {
                    targetStatus["channel_icon"] = targetChannel.Title;
                    targetStatus["channel_duration"] = extractor.Node(42, 7).Percent;
                    targetStatus["unit_channel_interruptible"] = extractor.Node(43, 7).IsWhite;
                }
            }

            Dictionary<string, object?> focus = (Dictionary<string, object?>)data["focus"]!;
            Dictionary<string, object?> focusAura = new()
            {
                ["debuff_sequence"] = new List<Dictionary<string, object?>>(),
                ["debuff"] = new Dictionary<string, Dictionary<string, object?>>(),
            };
            focus["aura"] = focusAura;

            Dictionary<string, object?> focusStatus = new() { ["exists"] = extractor.Node(38, 8).IsWhite };
            focus["status"] = focusStatus;

            if ((bool)focusStatus["exists"]!)
            {
                (List<Dictionary<string, object?>> fDebuffSeq, Dictionary<string, Dictionary<string, object?>> fDebuffDict) = extractor.ReadAuraSequence(26, 8, 8);
                focusAura["debuff_sequence"] = fDebuffSeq;
                focusAura["debuff"] = fDebuffDict;

                focusStatus["unit_can_attack"] = extractor.Node(39, 8).IsWhite;
                focusStatus["unit_is_self"] = extractor.Node(40, 8).IsWhite;
                focusStatus["unit_is_alive"] = extractor.Node(41, 8).IsWhite;
                focusStatus["unit_in_combat"] = extractor.Node(42, 8).IsWhite;
                focusStatus["unit_in_range"] = extractor.Node(43, 8).IsWhite;
                focusStatus["unit_health"] = extractor.Node(45, 8).Percent;
                focusStatus["unit_cast_icon"] = null;
                focusStatus["unit_cast_duration"] = null;
                focusStatus["unit_cast_interruptible"] = null;
                focusStatus["unit_channel_icon"] = null;
                focusStatus["unit_channel_duration"] = null;
                focusStatus["unit_channel_interruptible"] = null;

                Node focusCast = extractor.Node(38, 9);
                if (focusCast.IsNotPure)
                {
                    focusStatus["unit_cast_icon"] = focusCast.Title;
                    focusStatus["unit_cast_duration"] = extractor.Node(39, 9).Percent;
                    focusStatus["unit_cast_interruptible"] = extractor.Node(40, 9).IsWhite;
                }

                Node focusChannel = extractor.Node(41, 9);
                if (focusChannel.IsNotPure)
                {
                    focusStatus["unit_channel_icon"] = focusChannel.Title;
                    focusStatus["unit_channel_duration"] = extractor.Node(42, 9).Percent;
                    focusStatus["unit_channel_interruptible"] = extractor.Node(43, 9).IsWhite;
                }
            }

            Dictionary<string, object?> party = (Dictionary<string, object?>)data["party"]!;
            for (int i = 1; i <= 4; i++)
            {
                string key = $"party{i}";
                Dictionary<string, object?> partyItem = new()
                {
                    ["exists"] = false,
                    ["unitToken"] = key,
                    ["status"] = new Dictionary<string, object?>(),
                    ["aura"] = new Dictionary<string, object?>(),
                };

                bool exists = extractor.Node((12 * i) - 2, 14).IsWhite;
                partyItem["exists"] = exists;

                if (exists)
                {
                    Dictionary<string, object?> status = new()
                    {
                        ["unit_in_range"] = extractor.Node((12 * i) - 1, 14).IsWhite,
                        ["unit_health"] = extractor.Node(12 * i, 14).Percent,
                        ["selectd"] = extractor.Node(12 * i, 15).IsWhite,
                        ["unit_damage_absorbs"] = extractor.ReadHealthBar((12 * i) - 10, 14, 8) * 100,
                        ["unit_heal_absorbs"] = extractor.ReadHealthBar((12 * i) - 10, 15, 8) * 100,
                    };

                    Node partyClass = extractor.Node((12 * i) - 2, 15);
                    status["unit_class"] = partyClass.IsPure && colorMap.Class.TryGetValue(partyClass.ColorString, out string? c) ? c : "NONE";

                    Node partyRole = extractor.Node((12 * i) - 1, 15);
                    status["unit_role"] = partyRole.IsPure && colorMap.Role.TryGetValue(partyRole.ColorString, out string? r) ? r : "NONE";

                    partyItem["status"] = status;

                    Dictionary<string, object?> aura = new();
                    (List<Dictionary<string, object?>> pbSeq, Dictionary<string, Dictionary<string, object?>> pbDict) = extractor.ReadAuraSequence((12 * i) - 4, 11, 6);
                    (List<Dictionary<string, object?>> pdSeq, Dictionary<string, Dictionary<string, object?>> pdDict) = extractor.ReadAuraSequence((12 * i) - 10, 11, 6);
                    aura["buff_sequence"] = pbSeq;
                    aura["buff"] = pbDict;
                    aura["debuff_sequence"] = pdSeq;
                    aura["debuff"] = pdDict;
                    partyItem["aura"] = aura;
                }

                party[key] = partyItem;
            }

            Dictionary<string, object?> signal = new();
            int signalIndex = 1;
            for (int x = 38; x <= 45; x++)
            {
                signal[signalIndex.ToString()] = ReadStdNode(extractor.Node(x, 10));
                signalIndex++;
            }

            data["signal"] = signal;

            Dictionary<string, object?> spec = new();
            int specIndex = 1;
            for (int x = 34; x <= 37; x++)
            {
                for (int y = 8; y <= 10; y++)
                {
                    spec[specIndex.ToString()] = ReadStdNode(extractor.Node(x, y));
                    specIndex++;
                }
            }

            data["spec"] = spec;
        }
        catch (Exception ex)
        {
            data["error"] = $"数据提取失败: {ex.Message}";
        }

        return data;
    }

    private static Dictionary<string, object?> ReadStdNode(Node node)
    {
        if (node.IsPure)
        {
            return new Dictionary<string, object?>
            {
                ["is_pure"] = true,
                ["title"] = null,
                ["color_string"] = node.ColorString,
                ["is_white"] = node.IsWhite,
                ["percent"] = node.Percent,
                ["mean"] = node.Mean,
                ["decimal"] = node.Decimal,
            };
        }

        return new Dictionary<string, object?>
        {
            ["is_pure"] = false,
            ["title"] = node.Title,
            ["hash"] = node.Hash,
        };
    }
}




