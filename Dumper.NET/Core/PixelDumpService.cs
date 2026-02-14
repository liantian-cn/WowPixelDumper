using System.Drawing;
using System.Drawing.Imaging;
using Dumper.NET.Capture;

namespace Dumper.NET.Core;

public sealed class PixelDumpService : IDisposable
{
    private readonly object _sync = new();
    private readonly ColorMap _colorMap;
    private readonly TemplateImage _template;
    private readonly NodeTitleManager _titleManager;

    private DesktopDuplicatorCapture? _capture;
    private CancellationTokenSource? _cts;
    private Task? _loopTask;
    private (int Left, int Top, int Right, int Bottom)? _bounds;

    private Dictionary<string, object?> _pixelDump = new()
    {
        ["error"] = "相机尚未启动",
    };

    public PixelDumpService(string colorMapPath, string templatePath, string nodeDbPath)
    {
        _colorMap = ColorMap.Load(colorMapPath);
        _template = TemplateImage.Load(templatePath);
        _titleManager = new NodeTitleManager(nodeDbPath, _colorMap, 0.995);
    }

    public Dictionary<string, object?> GetPixelDump()
    {
        lock (_sync)
        {
            return new Dictionary<string, object?>(_pixelDump);
        }
    }

    public List<MonitorInfo> GetMonitors()
    {
        return DesktopDuplicatorCapture.EnumerateMonitors();
    }

    public NodeTitleManager GetTitleManager()
    {
        return _titleManager;
    }

    public void Start(int adapterIndex, int outputIndex, int fps, Action<string>? log = null)
    {
        Stop();

        _capture = new DesktopDuplicatorCapture(adapterIndex, outputIndex);

        PixelFrame? initialFrame = null;
        for (int i = 0; i < 10; i++)
        {
            initialFrame = _capture.GrabFrame(300);
            if (initialFrame is not null && !initialFrame.Value.IsAllBlack())
            {
                break;
            }

            Thread.Sleep(50);
        }

        if (initialFrame is null || initialFrame.Value.IsAllBlack())
        {
            throw new InvalidOperationException("首次截图失败或全黑");
        }

        _bounds = TemplateMatcher.FindTemplateBounds(initialFrame.Value, _template, 0);
        if (_bounds is null)
        {
            string diag = Path.Combine(AppContext.BaseDirectory, "diag_frame.bmp");
            SaveFrameAsBmp(initialFrame.Value, diag);
            throw new InvalidOperationException($"未找到模板锚点，无法定位数据区域。诊断截图: {diag}");
        }

        log?.Invoke($"模板定位成功: ({_bounds.Value.Left}, {_bounds.Value.Top}, {_bounds.Value.Right}, {_bounds.Value.Bottom})");

        _cts = new CancellationTokenSource();
        int delayMs = Math.Max(1, 1000 / Math.Max(1, fps));

        _loopTask = Task.Run(async () =>
        {
            while (!_cts.IsCancellationRequested)
            {
                try
                {
                    PixelFrame? frame = _capture.GrabFrame(100);
                    if (frame is null || frame.Value.IsAllBlack())
                    {
                        await Task.Delay(5, _cts.Token);
                        continue;
                    }

                    PixelFrame cropped = frame.Value.Crop(_bounds.Value);
                    NodeExtractor extractor = new(cropped, _colorMap, _titleManager);

                    List<string> occlusionErrors = ValidateOcclusion(extractor);
                    if (occlusionErrors.Count > 0)
                    {
                        lock (_sync)
                        {
                            _pixelDump = new Dictionary<string, object?>
                            {
                                ["error"] = "游戏窗口被遮挡或插件未加载，请检查游戏窗口是否可见",
                                ["details"] = occlusionErrors,
                            };
                        }
                    }
                    else
                    {
                        Dictionary<string, object?> data = NodeDataExtractor.ExtractAllData(extractor, _colorMap);
                        lock (_sync)
                        {
                            _pixelDump = data;
                        }
                    }
                }
                catch (OperationCanceledException)
                {
                    break;
                }
                catch (Exception ex)
                {
                    lock (_sync)
                    {
                        _pixelDump = new Dictionary<string, object?> { ["error"] = ex.Message };
                    }

                    log?.Invoke($"采集错误: {ex.Message}");
                }

                await Task.Delay(delayMs, _cts.Token);
            }
        }, _cts.Token);
    }

    public void Stop()
    {
        if (_cts is not null)
        {
            _cts.Cancel();
            try
            {
                _loopTask?.Wait(1000);
            }
            catch
            {
                // ignore
            }

            _cts.Dispose();
            _cts = null;
            _loopTask = null;
        }

        _capture?.Dispose();
        _capture = null;

        lock (_sync)
        {
            _pixelDump = new Dictionary<string, object?>
            {
                ["error"] = "已停止",
            };
        }
    }

    private static List<string> ValidateOcclusion(NodeExtractor extractor)
    {
        List<string> errors = [];

        Node node116 = extractor.Node(1, 16);
        Node node501 = extractor.Node(50, 1);
        Node node11 = extractor.Node(1, 1);
        Node node5016 = extractor.Node(50, 16);
        Node node514 = extractor.Node(51, 4);

        if (!node116.IsBlack)
        {
            errors.Add("(1,16)应为黑色");
        }

        if (!node501.IsBlack)
        {
            errors.Add("(50,1)应为黑色");
        }

        if (!node11.IsPure)
        {
            errors.Add("(1,1)应为纯色(参考色)");
        }

        if (!node5016.IsPure)
        {
            errors.Add("(50,16)应为纯色(参考色)");
        }

        if (node11.IsPure && node5016.IsPure && !string.Equals(node11.ColorString, node5016.ColorString, StringComparison.Ordinal))
        {
            errors.Add($"(1,1)和(50,16)颜色不匹配: {node11.ColorString} != {node5016.ColorString}");
        }

        if (node514.IsPure)
        {
            errors.Add("(51,4)应为非纯色(数据区)");
        }

        return errors;
    }

    private static void SaveFrameAsBmp(PixelFrame frame, string outputPath)
    {
        using Bitmap bitmap = new(frame.Width, frame.Height, PixelFormat.Format32bppArgb);
        BitmapData data = bitmap.LockBits(new Rectangle(0, 0, frame.Width, frame.Height), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);

        try
        {
            for (int y = 0; y < frame.Height; y++)
            {
                IntPtr dst = data.Scan0 + (y * data.Stride);
                int src = y * frame.Width * 4;
                System.Runtime.InteropServices.Marshal.Copy(frame.Bgra, src, dst, frame.Width * 4);
            }
        }
        finally
        {
            bitmap.UnlockBits(data);
        }

        bitmap.Save(outputPath, ImageFormat.Bmp);
    }

    public void Dispose()
    {
        Stop();
        _titleManager.Dispose();
    }
}
