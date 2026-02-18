namespace EZAssistedX2.NET
{
    public partial class MainForm : Form
    {
        private WorkerService? _worker;

        public MainForm()
        {
            InitializeComponent();

            btnRefresh.Click += BtnRefresh_Click;
            btnStart.Click += BtnStart_Click;
            btnStop.Click += BtnStop_Click;
            combo.SelectedIndexChanged += Combo_SelectedIndexChanged;

            RefreshWindows();
        }

        private void RefreshWindows()
        {
            combo.Items.Clear();
            combo.DisplayMember = "Text";
            combo.ValueMember = "Hwnd";

            var windows = NativeMethods.GetWindowsByTitle("魔兽世界");
            foreach (var (hwnd, title) in windows)
            {
                combo.Items.Add(new WindowItem(hwnd, $"魔兽世界{hwnd}"));
            }

            btnStart.Enabled = combo.Items.Count > 0;
            if (combo.Items.Count > 0)
                combo.SelectedIndex = 0;
        }

        private void BtnRefresh_Click(object? sender, EventArgs e)
        {
            RefreshWindows();
        }

        private void Combo_SelectedIndexChanged(object? sender, EventArgs e)
        {
            btnStart.Enabled = combo.SelectedIndex >= 0 && _worker == null;
        }

        private void BtnStart_Click(object? sender, EventArgs e)
        {
            if (combo.SelectedItem is not WindowItem item) return;

            _worker = new WorkerService(item.Hwnd);
            _worker.OnLog += msg => BeginInvoke(() => logLine.Text = msg);
            _worker.OnError += msg => BeginInvoke(() => logLine.Text = $"错误: {msg}");
            _worker.OnFinished += hasError => BeginInvoke(() => OnWorkerFinished(hasError));
            _worker.Start();

            btnStart.Enabled = false;
            btnStop.Enabled = true;
            btnRefresh.Enabled = false;
            combo.Enabled = false;
            logLine.Text = "已启动";
        }

        private void BtnStop_Click(object? sender, EventArgs e)
        {
            if (_worker != null)
            {
                _worker.Stop();
                btnStop.Enabled = false;
                logLine.Text = "正在停止...";
            }
        }

        private void OnWorkerFinished(bool hasError)
        {
            _worker = null;
            btnStart.Enabled = combo.Items.Count > 0;
            btnStop.Enabled = false;
            btnRefresh.Enabled = true;
            combo.Enabled = true;
            // 有错误时保留错误信息，不覆盖
            if (!hasError)
                logLine.Text = "已停止";
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            string input = ShowExitInputDialog();
            if (!string.Equals(input, "exit", StringComparison.OrdinalIgnoreCase))
            {
                e.Cancel = true;
                return;
            }

            if (_worker != null)
            {
                _worker.Stop();
                _worker.Wait();
            }
            base.OnFormClosing(e);
        }

        private static string ShowExitInputDialog()
        {
            using var form = new Form();
            form.Text = "确认退出";
            form.ClientSize = new Size(300, 120);
            form.FormBorderStyle = FormBorderStyle.FixedDialog;
            form.StartPosition = FormStartPosition.CenterParent;
            form.MaximizeBox = false;
            form.MinimizeBox = false;

            var label = new Label { Text = "请输入 exit 以退出程序：", Left = 20, Top = 15, AutoSize = true };
            var textBox = new TextBox { Left = 20, Top = 40, Width = 260 };
            var btnOk = new Button { Text = "确定", DialogResult = DialogResult.OK, Left = 120, Top = 75, Width = 75 };
            var btnCancel = new Button { Text = "取消", DialogResult = DialogResult.Cancel, Left = 205, Top = 75, Width = 75 };

            form.Controls.AddRange([label, textBox, btnOk, btnCancel]);
            form.AcceptButton = btnOk;
            form.CancelButton = btnCancel;

            return form.ShowDialog() == DialogResult.OK ? textBox.Text.Trim() : string.Empty;
        }
    }

    /// <summary>
    /// ComboBox 项，存储窗口句柄和显示文本。
    /// </summary>
    internal sealed class WindowItem
    {
        public IntPtr Hwnd { get; }
        public string Text { get; }

        public WindowItem(IntPtr hwnd, string text)
        {
            Hwnd = hwnd;
            Text = text;
        }

        public override string ToString() => Text;
    }
}
