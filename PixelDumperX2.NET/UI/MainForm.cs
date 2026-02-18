using System.Drawing;
using System.Text.Encodings.Web;
using System.Text.Json;
using Dumper.NET.Capture;
using Dumper.NET.Core;
using Dumper.NET.Web;

namespace Dumper.NET.UI;

public sealed class MainForm : Form
{
    private readonly PixelDumpService _pixelDumpService;
    private readonly HttpApiServer _apiServer;

    private readonly ComboBox _monitorCombo = new();
    private readonly NumericUpDown _fpsInput = new();
    private readonly Button _refreshButton = new();
    private readonly Button _toggleButton = new();
    private readonly Button _pauseRefreshButton = new();
    private readonly Button _openApiButton = new();
    private readonly Button _iconLibraryButton = new();
    private readonly TextBox _apiText = new();
    private readonly TextBox _logBox = new();
    private readonly TextBox _dataBox = new();
    private readonly SplitContainer _splitContainer = new();
    private readonly System.Windows.Forms.Timer _uiTimer = new();

    private List<MonitorInfo> _monitors = new();
    private bool _running;
    private bool _dataRefreshEnabled = true;
    private IconLibraryForm? _iconLibraryForm;

    private static readonly JsonSerializerOptions UiJsonOptions = new()
    {
        WriteIndented = true,
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
    };

    public MainForm()
    {
        string baseDir = AppContext.BaseDirectory;
        string colorMapPath = Path.Combine(baseDir, "Assets", "ColorMap.json");
        string templatePath = Path.Combine(baseDir, "Assets", "mark8.png");
        string nodeDbPath = Path.Combine(baseDir, "Assets", "node_titles.db");

        _pixelDumpService = new PixelDumpService(colorMapPath, templatePath, nodeDbPath);
        _apiServer = new HttpApiServer(_pixelDumpService.GetPixelDump);

        InitializeLayout();

        _apiServer.Start();
        Log("HTTP API 已启动: http://127.0.0.1:65131");

        RefreshMonitors();

        _uiTimer.Interval = 300;
        _uiTimer.Tick += (_, _) =>
        {
            if (!_dataRefreshEnabled)
            {
                return;
            }

            Dictionary<string, object?> data = _pixelDumpService.GetPixelDump();
            _dataBox.Text = JsonSerializer.Serialize(data, UiJsonOptions);
        };
        _uiTimer.Start();
    }

    private void InitializeLayout()
    {
        Text = "PixelDumperX2.NET";
        Rectangle workingArea = Screen.PrimaryScreen?.WorkingArea ?? new Rectangle(0, 0, 1400, 900);
        Width = (int)(workingArea.Width * 0.8);
        Height = (int)(workingArea.Height * 0.8);
        MinimumSize = new Size(Width, Height);
        MaximumSize = new Size(Width, Height);
        StartPosition = FormStartPosition.CenterScreen;

        TableLayoutPanel root = new()
        {
            Dock = DockStyle.Fill,
            RowCount = 2,
            ColumnCount = 1,
        };
        root.RowStyles.Add(new RowStyle(SizeType.Absolute, 68));
        root.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        Controls.Add(root);

        TableLayoutPanel topBar = new()
        {
            Dock = DockStyle.Fill,
            ColumnCount = 2,
            RowCount = 1,
            Padding = new Padding(8, 16, 8, 8)
        };
        topBar.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        topBar.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        root.Controls.Add(topBar, 0, 0);

        FlowLayoutPanel leftTop = new()
        {
            Dock = DockStyle.Fill,
            FlowDirection = FlowDirection.LeftToRight,
            WrapContents = false,
            AutoSize = false,
            Margin = new Padding(0),
        };
        topBar.Controls.Add(leftTop, 0, 0);

        FlowLayoutPanel rightTop = new()
        {
            Dock = DockStyle.Right,
            FlowDirection = FlowDirection.LeftToRight,
            WrapContents = false,
            AutoSize = true,
            Margin = new Padding(0),
        };
        topBar.Controls.Add(rightTop, 1, 0);

        leftTop.Controls.Add(new Label { Text = "API地址：", AutoSize = true, Padding = new Padding(0, 7, 0, 0) });
        _apiText.Text = "http://127.0.0.1:65131";
        _apiText.Width = 216;
        _apiText.ReadOnly = true;
        _apiText.MouseClick += (_, _) => Clipboard.SetText(_apiText.Text);
        ConfigureTopControl(_apiText, 216);
        leftTop.Controls.Add(_apiText);

        _openApiButton.Text = "访问API";
        ConfigureTopButton(_openApiButton, 150);
        _openApiButton.Click += (_, _) =>
        {
            try
            {
                System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                {
                    FileName = _apiText.Text,
                    UseShellExecute = true,
                });
            }
            catch (Exception ex)
            {
                Log($"打开 API 失败: {ex.Message}");
            }
        };
        leftTop.Controls.Add(_openApiButton);

        leftTop.Controls.Add(new Label { Text = "选择显示器：", AutoSize = true, Padding = new Padding(8, 7, 0, 0) });
        _monitorCombo.Width = 504;
        ConfigureTopControl(_monitorCombo, 504);
        leftTop.Controls.Add(_monitorCombo);

        leftTop.Controls.Add(new Label { Text = "FPS：", AutoSize = true, Padding = new Padding(8, 7, 0, 0) });
        _fpsInput.Minimum = 1;
        _fpsInput.Maximum = 60;
        _fpsInput.Value = 10;
        _fpsInput.Width = 60;
        ConfigureTopControl(_fpsInput, 60);
        leftTop.Controls.Add(_fpsInput);

        _refreshButton.Text = "刷新显示器列表";
        ConfigureTopButton(_refreshButton, 198);
        _refreshButton.Click += (_, _) => RefreshMonitors();
        leftTop.Controls.Add(_refreshButton);

        _toggleButton.Text = "启动";
        ConfigureTopButton(_toggleButton, 120);
        _toggleButton.Click += (_, _) => ToggleCapture();
        leftTop.Controls.Add(_toggleButton);

        _iconLibraryButton.Text = "管理图标库";
        ConfigureTopButton(_iconLibraryButton, 162);
        _iconLibraryButton.Click += (_, _) => OpenIconLibrary();
        leftTop.Controls.Add(_iconLibraryButton);

        _pauseRefreshButton.Text = "暂停刷新日志";
        ConfigureTopButton(_pauseRefreshButton, 186);
        _pauseRefreshButton.Click += (_, _) => ToggleDataRefresh();
        leftTop.Controls.Add(_pauseRefreshButton);

        Button githubButton = new() { Text = "Github" };
        ConfigureTopButton(githubButton, 117);
        githubButton.Click += (_, _) =>
        {
            try
            {
                System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                {
                    FileName = "https://github.com/liantian-cn/PixelDumperX2",
                    UseShellExecute = true,
                });
            }
            catch (Exception ex)
            {
                Log($"打开 Github 失败: {ex.Message}");
            }
        };
        rightTop.Controls.Add(githubButton);

        Button discordButton = new() { Text = "Kook App" };
        ConfigureTopButton(discordButton, 117);
        discordButton.Click += (_, _) =>
        {
            try
            {
                System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                {
                    FileName = "https://kook.vip/P0KJnb",
                    UseShellExecute = true,
                });
            }
            catch (Exception ex)
            {
                Log($"打开 Discord 失败: {ex.Message}");
            }
        };
        rightTop.Controls.Add(discordButton);

        _splitContainer.Dock = DockStyle.Fill;
        _splitContainer.Orientation = Orientation.Vertical;
        _splitContainer.SplitterDistance = (int)(Width * 0.75);
        _splitContainer.Resize += (_, _) => UpdateSplitRatio();
        root.Controls.Add(_splitContainer, 0, 1);

        _dataBox.Multiline = true;
        _dataBox.ReadOnly = true;
        _dataBox.ScrollBars = ScrollBars.Both;
        _dataBox.Font = new Font("Consolas", 10);
        _dataBox.Dock = DockStyle.Fill;
        _splitContainer.Panel1.Controls.Add(_dataBox);

        _logBox.Multiline = true;
        _logBox.ReadOnly = true;
        _logBox.ScrollBars = ScrollBars.Both;
        _logBox.Font = new Font("Consolas", 9);
        _logBox.Dock = DockStyle.Fill;
        _splitContainer.Panel2.Controls.Add(_logBox);

        Shown += (_, _) => UpdateSplitRatio();
    }

    private void UpdateSplitRatio()
    {
        int usableWidth = _splitContainer.ClientSize.Width - _splitContainer.SplitterWidth;
        if (usableWidth <= 0)
        {
            return;
        }

        _splitContainer.SplitterDistance = (int)(usableWidth * 0.75);
    }

    private static void ConfigureTopButton(Button button, int width)
    {
        button.AutoSize = false;
        button.Width = width;
        button.Height = 32;
        button.Margin = new Padding(0, 0, 8, 0);
    }

    private static void ConfigureTopControl(Control control, int width)
    {
        control.Width = width;
        control.Height = 32;
        control.Margin = new Padding(0, 0, 8, 0);
    }

    private void OpenIconLibrary()
    {
        if (_iconLibraryForm is null || _iconLibraryForm.IsDisposed)
        {
            _iconLibraryForm = new IconLibraryForm(_pixelDumpService.GetTitleManager());
            _iconLibraryForm.Show(this);
            return;
        }

        _iconLibraryForm.Focus();
    }

    private void ToggleDataRefresh()
    {
        _dataRefreshEnabled = !_dataRefreshEnabled;
        _pauseRefreshButton.Text = _dataRefreshEnabled ? "暂停刷新日志" : "恢复刷新日志";
        if (_dataRefreshEnabled)
        {
            Dictionary<string, object?> data = _pixelDumpService.GetPixelDump();
            _dataBox.Text = JsonSerializer.Serialize(data, UiJsonOptions);
        }
    }

    private void RefreshMonitors()
    {
        _monitors = _pixelDumpService.GetMonitors();
        _monitorCombo.Items.Clear();

        foreach (MonitorInfo monitor in _monitors)
        {
            _monitorCombo.Items.Add(monitor.ToString());
        }

        if (_monitors.Count > 0)
        {
            int primaryIndex = _monitors.FindIndex(m => m.IsPrimary);
            _monitorCombo.SelectedIndex = primaryIndex >= 0 ? primaryIndex : 0;
        }

        Log($"显示器数量: {_monitors.Count}");
    }

    private void ToggleCapture()
    {
        if (_running)
        {
            _pixelDumpService.Stop();
            _running = false;
            _toggleButton.Text = "启动";
            _monitorCombo.Enabled = true;
            _fpsInput.Enabled = true;
            _refreshButton.Enabled = true;
            Log("采集已停止");
            return;
        }

        if (_monitorCombo.SelectedIndex < 0 || _monitorCombo.SelectedIndex >= _monitors.Count)
        {
            Log("请先选择显示器");
            return;
        }

        MonitorInfo monitor = _monitors[_monitorCombo.SelectedIndex];

        try
        {
            _pixelDumpService.Start(monitor.AdapterIndex, monitor.OutputIndex, (int)_fpsInput.Value, Log);
            _running = true;
            _toggleButton.Text = "停止";
            _monitorCombo.Enabled = false;
            _fpsInput.Enabled = false;
            _refreshButton.Enabled = false;
            Log($"采集已启动: Device[{monitor.AdapterIndex}] Output[{monitor.OutputIndex}] FPS={(int)_fpsInput.Value}");
        }
        catch (Exception ex)
        {
            Log($"启动失败: {ex.Message}");
        }
    }

    private void Log(string message)
    {
        string line = $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {message}{Environment.NewLine}";
        _logBox.AppendText(line);
    }

    protected override void OnFormClosing(FormClosingEventArgs e)
    {
        _uiTimer.Stop();
        _pixelDumpService.Dispose();
        _apiServer.Dispose();
        base.OnFormClosing(e);
    }
}

