using System.Text;
using System.Text.Json;
using System.Threading;
using Dumper.NET.Core;
using Dumper.NET.UI;

namespace Dumper.NET;

internal static class Program
{
    [STAThread]
    private static void Main(string[] args)
    {
        bool validateMode = args.Any(a => string.Equals(a, "--validate", StringComparison.OrdinalIgnoreCase));

        if (validateMode)
        {
            int code = RunValidation(args);
            Environment.ExitCode = code;
            return;
        }

        using Mutex mutex = new(false, "DumperGUI.NET", out bool createdNew);
        if (!createdNew)
        {
            MessageBox.Show("DumperGUI.NET 已经在运行。", "提示", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        ApplicationConfiguration.Initialize();
        Application.Run(new MainForm());
    }

    private static int RunValidation(string[] args)
    {
        int seconds = 8;
        for (int i = 0; i < args.Length - 1; i++)
        {
            if (string.Equals(args[i], "--seconds", StringComparison.OrdinalIgnoreCase) && int.TryParse(args[i + 1], out int parsed))
            {
                seconds = Math.Clamp(parsed, 3, 30);
                break;
            }
        }

        string baseDir = AppContext.BaseDirectory;
        string colorMapPath = Path.Combine(baseDir, "Assets", "ColorMap.json");
        string templatePath = Path.Combine(baseDir, "Assets", "mark8.png");
        string nodeDbPath = Path.Combine(baseDir, "Assets", "node_titles.db");
        string reportPath = Path.Combine(baseDir, "validation_report.json");

        List<string> logs = [];

        using PixelDumpService service = new(colorMapPath, templatePath, nodeDbPath);

        try
        {
            var monitors = service.GetMonitors();
            if (monitors.Count == 0)
            {
                WriteReport(reportPath, false, "未枚举到显示器", logs, service.GetPixelDump());
                return 2;
            }

            List<(bool Success, string Message, Dictionary<string, object?> Data)> attempts = [];
            foreach (var monitor in monitors.OrderByDescending(m => m.IsPrimary))
            {
                logs.Add($"Trying monitor: {monitor}");
                Dictionary<string, object?> latest = new();

                try
                {
                    service.Start(monitor.AdapterIndex, monitor.OutputIndex, 10, m => logs.Add(m));
                    DateTime deadline = DateTime.Now.AddSeconds(seconds);
                    latest = service.GetPixelDump();

                    while (DateTime.Now < deadline)
                    {
                        Thread.Sleep(300);
                        latest = service.GetPixelDump();

                        if (!latest.TryGetValue("error", out object? errorObj))
                        {
                            WriteReport(reportPath, true, $"采集成功，显示器: {monitor}", logs, latest);
                            return 0;
                        }

                        string err = errorObj?.ToString() ?? string.Empty;
                        if (!string.Equals(err, "相机尚未启动", StringComparison.Ordinal) &&
                            !string.Equals(err, "已停止", StringComparison.Ordinal))
                        {
                            logs.Add($"Current error: {err}");
                        }
                    }

                    string reason = latest.TryGetValue("error", out object? e) ? e?.ToString() ?? "未知错误" : "超时未取到错误字段";
                    attempts.Add((false, $"显示器 {monitor} 失败: {reason}", latest));
                }
                catch (Exception ex)
                {
                    attempts.Add((false, $"显示器 {monitor} 异常: {ex.Message}", service.GetPixelDump()));
                    logs.Add($"Exception on {monitor}: {ex.Message}");
                }
                finally
                {
                    service.Stop();
                }
            }

            var final = attempts.LastOrDefault();
            string message = attempts.Count == 0 ? "未执行任何显示器尝试" : string.Join(" | ", attempts.Select(a => a.Message));
            WriteReport(reportPath, false, message, logs, final.Data ?? service.GetPixelDump());
            return 1;
        }
        catch (Exception ex)
        {
            logs.Add($"Exception: {ex}");
            WriteReport(reportPath, false, ex.Message, logs, service.GetPixelDump());
            return 3;
        }
        finally
        {
            service.Stop();
        }
    }

    private static void WriteReport(string path, bool success, string message, List<string> logs, Dictionary<string, object?> pixelDump)
    {
        Dictionary<string, object?> report = new()
        {
            ["timestamp"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
            ["success"] = success,
            ["message"] = message,
            ["logs"] = logs,
            ["pixel_dump"] = pixelDump,
        };

        string json = JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(path, json, Encoding.UTF8);
    }
}
