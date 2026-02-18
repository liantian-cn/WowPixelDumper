namespace EZAssistedX2.NET
{
    partial class MainForm
    {
        private System.ComponentModel.IContainer components = null;

        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        private void InitializeComponent()
        {
            combo = new ComboBox();
            btnRefresh = new Button();
            btnStart = new Button();
            btnStop = new Button();
            logLine = new TextBox();
            topPanel = new FlowLayoutPanel();
            topPanel.SuspendLayout();
            SuspendLayout();

            // topPanel
            topPanel.AutoSize = true;
            topPanel.Dock = DockStyle.Top;
            topPanel.WrapContents = false;
            topPanel.Padding = new Padding(0);
            topPanel.Margin = new Padding(0);

            // combo
            combo.DropDownStyle = ComboBoxStyle.DropDownList;
            combo.MinimumSize = new Size(200, 0);
            combo.Margin = new Padding(3);

            // btnRefresh
            btnRefresh.Text = "刷新";
            btnRefresh.AutoSize = true;
            btnRefresh.Margin = new Padding(3);

            // btnStart
            btnStart.Text = "开始";
            btnStart.AutoSize = true;
            btnStart.Enabled = false;
            btnStart.Margin = new Padding(3);

            // btnStop
            btnStop.Text = "停止";
            btnStop.AutoSize = true;
            btnStop.Enabled = false;
            btnStop.Margin = new Padding(3);

            topPanel.Controls.Add(combo);
            topPanel.Controls.Add(btnRefresh);
            topPanel.Controls.Add(btnStart);
            topPanel.Controls.Add(btnStop);

            // logLine
            logLine.ReadOnly = true;
            logLine.PlaceholderText = "日志输出...";
            logLine.Dock = DockStyle.Fill;
            logLine.Margin = new Padding(3);

            // MainForm
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(460, 72);
            FormBorderStyle = FormBorderStyle.FixedSingle;
            MaximizeBox = false;
            MinimizeBox = false;
            Text = "EZAssistedX2";
            TopMost = true;
            Controls.Add(logLine);
            Controls.Add(topPanel);

            topPanel.ResumeLayout(false);
            topPanel.PerformLayout();
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private FlowLayoutPanel topPanel;
        private ComboBox combo;
        private Button btnRefresh;
        private Button btnStart;
        private Button btnStop;
        private TextBox logLine;
    }
}
