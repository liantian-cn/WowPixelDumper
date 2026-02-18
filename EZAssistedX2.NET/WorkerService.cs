namespace EZAssistedX2.NET;

/// <summary>
/// 后台工作服务：截屏 → 查找模板 → 颜色识别 → 发送按键。
/// </summary>
internal sealed class WorkerService
{
    public event Action<string>? OnLog;
    public event Action<string>? OnError;
    /// <summary>
    /// hasError 为 true 时表示因错误而结束，UI 不应覆盖错误信息。
    /// </summary>
    public event Action<bool>? OnFinished;

    private readonly IntPtr _hwnd;
    private CancellationTokenSource? _cts;
    private Task? _task;

    public WorkerService(IntPtr hwnd)
    {
        _hwnd = hwnd;
    }

    public void Start()
    {
        _cts = new CancellationTokenSource();
        var token = _cts.Token;
        _task = Task.Run(() => Run(token), token);
    }

    public void Stop()
    {
        _cts?.Cancel();
    }

    public void Wait()
    {
        try { _task?.Wait(); } catch { /* ignored */ }
    }

    private void Run(CancellationToken token)
    {
        ScreenCapture? capture = null;
        bool hasError = false;
        try
        {
            capture = new ScreenCapture();

            OnLog?.Invoke($"屏幕: {capture.Width}x{capture.Height}, 格式: {capture.FormatName}");

            // 第一步：全屏截图，查找模板（带重试，DXGI 首帧可能为空）
            byte[]? frame = null;
            for (int attempt = 0; attempt < 10; attempt++)
            {
                frame = capture.GrabFrame();
                if (frame != null)
                {
                    // 检查帧是否全黑（DXGI 首帧可能为空白）
                    bool allBlack = true;
                    for (int i = 0; i < Math.Min(frame.Length, 4000); i += 4)
                    {
                        if (frame[i] != 0 || frame[i + 1] != 0 || frame[i + 2] != 0)
                        {
                            allBlack = false;
                            break;
                        }
                    }
                    if (!allBlack) break;
                    OnLog?.Invoke($"帧全黑，重试... ({attempt + 1}/10)");
                    frame = null;
                }
                else
                {
                    OnLog?.Invoke($"等待屏幕帧... ({attempt + 1}/10)");
                }
                Thread.Sleep(500);
            }

            if (frame == null)
            {
                hasError = true;
                OnError?.Invoke($"无法抓取有效屏幕帧（重试 10 次后仍失败，格式: {capture.FormatName}）");
                return;
            }

            var bounds = FindTemplateBounds(frame, capture.Width, capture.Height);
            if (bounds == null)
            {
                hasError = true;
                // 诊断：保存截图帧到文件，方便排查
                var diagPath = Path.Combine(AppContext.BaseDirectory, "diag_frame.bmp");
                try
                {
                    SaveFrameAsBmp(frame, capture.Width, capture.Height, diagPath);
                    OnLog?.Invoke($"诊断帧已保存: {diagPath}");
                }
                catch { /* ignored */ }

                // 诊断：扫描近似红色像素
                var redPixels = ScanApproxColor(frame, capture.Width, capture.Height, 200, 0, 0, 55);
                var info = $"未找到模板 (帧大小: {capture.Width}x{capture.Height}, 近似红色像素数: {redPixels.Count})";
                if (redPixels.Count > 0)
                {
                    var (px, py, pr, pg, pb) = redPixels[0];
                    info += $", 首个红色像素: ({px},{py}) RGB=({pr},{pg},{pb})";
                }
                OnError?.Invoke(info);
                return;
            }

            var (left, top, right, bottom) = bounds.Value;
            if (right - left != 12 || bottom - top != 4)
            {
                hasError = true;
                OnError?.Invoke($"模板大小不正确: {right - left}x{bottom - top}，期望 12x4");
                return;
            }

            // 中间 4 像素区域
            int regionLeft = left + 4;
            int regionTop = top;
            int regionRight = right - 4;
            int regionBottom = bottom;
            int regionW = regionRight - regionLeft;

            OnLog?.Invoke($"模板已定位: ({regionLeft},{regionTop})-({regionRight},{regionBottom})");

            var rng = new Random();

            // 第二步：循环截取区域，识别颜色，发送按键
            while (!token.IsCancellationRequested)
            {
                int sleepMs = rng.Next(100, 200);
                Thread.Sleep(sleepMs);

                if (token.IsCancellationRequested) break;

                var fullFrame = capture.GrabFrame();
                if (fullFrame == null) continue;

                var cropped = ScreenCapture.CropRegion(fullFrame, capture.Width,
                    regionLeft, regionTop, regionRight, regionBottom);

                if (IsUniformColor(cropped, regionW, out var r, out var g, out var b))
                {
                    if (r == 255 && g == 255 && b == 255)
                    {
                        OnLog?.Invoke("纯白");
                    }
                    else if (r == 0 && g == 0 && b == 0)
                    {
                        OnLog?.Invoke("纯黑");
                    }
                    else if (KeyMapping.KeyColorMap.TryGetValue((r, g, b), out var hotKey))
                    {
                        KeyMapping.SendHotKey(_hwnd, hotKey);
                        OnLog?.Invoke($"发送按键: {hotKey}");
                    }
                    else
                    {
                        OnLog?.Invoke($"未知颜色: {r}, {g}, {b}");
                    }
                }
                else
                {
                    OnLog?.Invoke("不是纯色");
                }
            }
        }
        catch (OperationCanceledException)
        {
            // 正常取消
        }
        catch (Exception ex)
        {
            hasError = true;
            OnError?.Invoke(ex.Message);
        }
        finally
        {
            capture?.Dispose();
            OnFinished?.Invoke(hasError);
        }
    }

    /// <summary>
    /// 检查裁剪区域是否为纯色（所有像素相同）。
    /// </summary>
    private static bool IsUniformColor(byte[] data, int width, out byte r, out byte g, out byte b)
    {
        var (r0, g0, b0) = ScreenCapture.GetPixel(data, width, 0, 0);
        r = r0; g = g0; b = b0;

        int pixelCount = data.Length / 4;
        for (int i = 1; i < pixelCount; i++)
        {
            int offset = i * 4;
            if (data[offset] != data[0] || data[offset + 1] != data[1] || data[offset + 2] != data[2])
                return false;
        }
        return true;
    }

    /// <summary>
    /// 在全屏截图中查找 4×4 模板（红/绿/黑/蓝 2×2 块），返回两个匹配点的外接矩形。
    /// 模板像素布局 (RGB):
    ///   [255,0,0] [255,0,0] [0,255,0] [0,255,0]
    ///   [255,0,0] [255,0,0] [0,255,0] [0,255,0]
    ///   [0,0,0]   [0,0,0]   [0,0,255] [0,0,255]
    ///   [0,0,0]   [0,0,0]   [0,0,255] [0,0,255]
    /// 注意：截图数据为 BGRA 格式。允许 ±tolerance 的颜色容差。
    /// </summary>
    private static (int Left, int Top, int Right, int Bottom)? FindTemplateBounds(
        byte[] frame, int frameWidth, int frameHeight, int tolerance = 3)
    {
        // 模板 4×4 (RGB 值)
        // Row 0-1: Red Red Green Green
        // Row 2-3: Black Black Blue Blue
        byte[,] templateR = { { 255, 255, 0, 0 }, { 255, 255, 0, 0 }, { 0, 0, 0, 0 }, { 0, 0, 0, 0 } };
        byte[,] templateG = { { 0, 0, 255, 255 }, { 0, 0, 255, 255 }, { 0, 0, 0, 0 }, { 0, 0, 0, 0 } };
        byte[,] templateB = { { 0, 0, 0, 0 }, { 0, 0, 0, 0 }, { 0, 0, 255, 255 }, { 0, 0, 255, 255 } };

        var matches = new List<(int X, int Y)>();

        for (int y = 0; y <= frameHeight - 4; y++)
        {
            for (int x = 0; x <= frameWidth - 4; x++)
            {
                if (MatchTemplate(frame, frameWidth, x, y, templateR, templateG, templateB, tolerance))
                {
                    matches.Add((x, y));
                    // 跳过已匹配区域，避免重叠匹配
                    x += 3;
                }
            }
        }

        if (matches.Count < 2)
            return null;

        // 取前两个匹配
        int left = Math.Min(matches[0].X, matches[1].X);
        int top = Math.Min(matches[0].Y, matches[1].Y);
        int right = Math.Max(matches[0].X + 4, matches[1].X + 4);
        int bottom = Math.Max(matches[0].Y + 4, matches[1].Y + 4);

        int w = right - left;
        int h = bottom - top;
        if (w % 4 != 0 || h % 4 != 0)
            return null;

        return (left, top, right, bottom);
    }

    private static bool MatchTemplate(byte[] frame, int frameWidth,
        int startX, int startY,
        byte[,] tR, byte[,] tG, byte[,] tB, int tolerance)
    {
        for (int dy = 0; dy < 4; dy++)
        {
            for (int dx = 0; dx < 4; dx++)
            {
                int offset = ((startY + dy) * frameWidth + (startX + dx)) * 4;
                byte b = frame[offset];
                byte g = frame[offset + 1];
                byte r = frame[offset + 2];

                if (Math.Abs(r - tR[dy, dx]) > tolerance ||
                    Math.Abs(g - tG[dy, dx]) > tolerance ||
                    Math.Abs(b - tB[dy, dx]) > tolerance)
                    return false;
            }
        }
        return true;
    }

    /// <summary>
    /// 扫描帧中近似指定颜色的像素（RGB），返回前 10 个匹配位置。
    /// </summary>
    private static List<(int X, int Y, byte R, byte G, byte B)> ScanApproxColor(
        byte[] frame, int width, int height, byte targetR, byte targetG, byte targetB, int tolerance)
    {
        var results = new List<(int, int, byte, byte, byte)>();
        for (int y = 0; y < height && results.Count < 10; y++)
        {
            for (int x = 0; x < width && results.Count < 10; x++)
            {
                int offset = (y * width + x) * 4;
                byte r = frame[offset + 2];
                byte g = frame[offset + 1];
                byte b = frame[offset];
                if (Math.Abs(r - targetR) <= tolerance &&
                    Math.Abs(g - targetG) <= tolerance &&
                    Math.Abs(b - targetB) <= tolerance)
                {
                    results.Add((x, y, r, g, b));
                }
            }
        }
        return results;
    }

    /// <summary>
    /// 将 BGRA 帧数据保存为 BMP 文件，用于诊断。
    /// </summary>
    private static void SaveFrameAsBmp(byte[] frame, int width, int height, string path)
    {
        // BMP 文件头 (14 bytes) + DIB 头 (40 bytes) = 54 bytes
        int rowSize = width * 3;
        int padding = (4 - rowSize % 4) % 4;
        int paddedRowSize = rowSize + padding;
        int imageSize = paddedRowSize * height;
        int fileSize = 54 + imageSize;

        using var fs = new FileStream(path, FileMode.Create);
        using var bw = new BinaryWriter(fs);

        // BMP 文件头
        bw.Write((byte)'B'); bw.Write((byte)'M');
        bw.Write(fileSize);
        bw.Write(0); // reserved
        bw.Write(54); // pixel data offset

        // DIB 头 (BITMAPINFOHEADER)
        bw.Write(40); // header size
        bw.Write(width);
        bw.Write(height); // positive = bottom-up
        bw.Write((short)1); // planes
        bw.Write((short)24); // bits per pixel
        bw.Write(0); // compression
        bw.Write(imageSize);
        bw.Write(2835); // horizontal resolution
        bw.Write(2835); // vertical resolution
        bw.Write(0); // colors in palette
        bw.Write(0); // important colors

        // 像素数据 (BMP 是 bottom-up，BGR 格式)
        var padBytes = new byte[padding];
        for (int y = height - 1; y >= 0; y--)
        {
            for (int x = 0; x < width; x++)
            {
                int offset = (y * width + x) * 4;
                bw.Write(frame[offset]);     // B
                bw.Write(frame[offset + 1]); // G
                bw.Write(frame[offset + 2]); // R
            }
            if (padding > 0) bw.Write(padBytes);
        }
    }
}
