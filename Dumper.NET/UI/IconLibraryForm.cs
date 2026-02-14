using System.Drawing;
using Dumper.NET.Core;

namespace Dumper.NET.UI;

public sealed class IconLibraryForm : Form
{
    private readonly NodeTitleManager _titleManager;
    private readonly Dictionary<string, string> _iconTypeMap;
    private readonly TabControl _tabControl = new();
    private readonly Label _statsLabel = new();
    private readonly List<CategoryTab> _categoryTabs = [];
    private readonly System.Windows.Forms.Timer _refreshTimer = new();

    private DataGridView _unmatchedGrid = new();
    private DataGridView _cosineGrid = new();
    private readonly Label _thresholdLabel = new();
    private readonly TrackBar _thresholdTrackBar = new();
    private readonly Label _dbInfoLabel = new();

    private readonly Dictionary<string, string> _unmatchedInputs = new(StringComparer.Ordinal);
    private readonly HashSet<string> _lastUnmatchedHashes = new(StringComparer.Ordinal);
    private Dictionary<string, NodeTitleManager.UnmatchedNode> _currentUnmatchedByHash = new(StringComparer.Ordinal);

    private readonly CategoryDef[] _categories =
    [
        new("敌人释放的减益", ["PLAYER_DEBUFF", "BLEED", "ENRAGE", "POISON", "DISEASE", "CURSE", "MAGIC"]),
        new("玩家施放的减益", ["ENEMY_DEBUFF"]),
        new("友方施放的增益", ["PLAYER_BUFF"]),
        new("友方施放的技能", ["PLAYER_SPELL"]),
        new("敌方释放的技能", ["ENEMY_SPELL_INTERRUPTIBLE", "ENEMY_SPELL_NOT_INTERRUPTIBLE"]),
        new("其他", ["NONE", "Unknown"]),
    ];

    public IconLibraryForm(NodeTitleManager titleManager)
    {
        _titleManager = titleManager;

        string colorMapPath = Path.Combine(AppContext.BaseDirectory, "Assets", "ColorMap.json");
        _iconTypeMap = ColorMap.Load(colorMapPath).IconType;
        Rectangle workingArea = Screen.PrimaryScreen?.WorkingArea ?? new Rectangle(0, 0, 1920, 1080);
        int formWidth = (int)(workingArea.Width * 0.6);
        int formHeight = (int)(workingArea.Height * 0.7);

        Text = "图标库管理";
        Width = formWidth;
        Height = formHeight;
        MinimumSize = new Size(formWidth, formHeight);
        MaximumSize = new Size(formWidth, formHeight);
        StartPosition = FormStartPosition.CenterParent;

        InitializeLayout();

        _refreshTimer.Interval = 1000;
        _refreshTimer.Tick += (_, _) => SmartRefreshUnmatched();
        _refreshTimer.Start();

        RefreshDatabaseTabs();
        RefreshUnmatchedTab();
        RefreshCosineTab();
        UpdateDbInfo();
        UpdateStats();
    }

    protected override void OnFormClosing(FormClosingEventArgs e)
    {
        _refreshTimer.Stop();
        base.OnFormClosing(e);
    }

    private void InitializeLayout()
    {
        TableLayoutPanel root = new()
        {
            Dock = DockStyle.Fill,
            RowCount = 2,
            ColumnCount = 1,
            Padding = new Padding(8),
        };
        root.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        root.RowStyles.Add(new RowStyle(SizeType.Absolute, 30));
        Controls.Add(root);

        _tabControl.Dock = DockStyle.Fill;
        root.Controls.Add(_tabControl, 0, 0);

        foreach (CategoryDef category in _categories)
        {
            CategoryTab categoryTab = CreateCategoryTab(category);
            _categoryTabs.Add(categoryTab);
            _tabControl.TabPages.Add(categoryTab.TabPage);
        }

        _tabControl.TabPages.Add(CreateUnmatchedTab());
        _tabControl.TabPages.Add(CreateCosineTab());
        _tabControl.TabPages.Add(CreateSettingsTab());

        _statsLabel.Dock = DockStyle.Fill;
        _statsLabel.TextAlign = ContentAlignment.MiddleLeft;
        root.Controls.Add(_statsLabel, 0, 1);
    }

    private CategoryTab CreateCategoryTab(CategoryDef category)
    {
        TabPage tab = new(category.Name);
        tab.BackColor = Color.White;
        TableLayoutPanel panel = new()
        {
            Dock = DockStyle.Fill,
            RowCount = 2,
            ColumnCount = 1,
            BackColor = Color.White,
        };
        panel.RowStyles.Add(new RowStyle(SizeType.Absolute, 48));
        panel.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        panel.RowStyles.Add(new RowStyle(SizeType.Absolute, 70));
        panel.RowCount = 3;
        tab.Controls.Add(panel);

        Label info = new()
        {
            Dock = DockStyle.Fill,
            Text = $"分类: {category.Name} | 包含Footnote类型: {string.Join(", ", category.Footnotes)}",
            AutoEllipsis = true,
            TextAlign = ContentAlignment.MiddleLeft,
        };
        panel.Controls.Add(info, 0, 0);

        DataGridView grid = CreateBaseGrid();
        grid.Columns.Add(CreateImageColumn("icon", "图标", 56));
        grid.Columns.Add(CreateTextColumn("title", "标题", 220));
        grid.Columns.Add(CreateTextColumn("hash", "Hash", 180));
        grid.Columns.Add(CreateTextColumn("footnote", "Footnote", 130));
        grid.Columns.Add(CreateTextColumn("type", "类型", 110));
        grid.Columns.Add(CreateButtonColumn("edit", "编辑", 80, "编辑"));
        grid.Columns.Add(CreateButtonColumn("delete", "删除", 80, "删除"));
        grid.CellContentClick += CategoryGridCellContentClick;
        panel.Controls.Add(grid, 0, 1);

        TableLayoutPanel bottom = new()
        {
            Dock = DockStyle.Fill,
            ColumnCount = 1,
            RowCount = 1,
            Padding = new Padding(0, 4, 0, 0),
        };
        bottom.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        Button refreshButton = new() { Text = "刷新列表", Dock = DockStyle.Fill, Height = 30 };
        refreshButton.Click += (_, _) => RefreshDatabaseTabs();
        bottom.Controls.Add(refreshButton, 0, 0);
        panel.Controls.Add(bottom, 0, 2);

        return new CategoryTab(tab, category, grid);
    }

    private TabPage CreateUnmatchedTab()
    {
        TabPage tab = new("未匹配图标");
        tab.BackColor = Color.White;
        TableLayoutPanel panel = new()
        {
            Dock = DockStyle.Fill,
            RowCount = 3,
            ColumnCount = 1,
            BackColor = Color.White,
        };
        panel.RowStyles.Add(new RowStyle(SizeType.Absolute, 48));
        panel.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        panel.RowStyles.Add(new RowStyle(SizeType.Absolute, 70));
        tab.Controls.Add(panel);

        Label info = new()
        {
            Dock = DockStyle.Fill,
            Text = "未匹配图标可在此输入标题并添加到数据库，最接近标题仅供参考。",
            TextAlign = ContentAlignment.MiddleLeft,
        };
        panel.Controls.Add(info, 0, 0);

        _unmatchedGrid = CreateBaseGrid();
        _unmatchedGrid.ReadOnly = false;
        _unmatchedGrid.Columns.Add(CreateImageColumn("icon", "图标", 56));
        _unmatchedGrid.Columns.Add(CreateTextColumn("hash", "Hash", 260));
        _unmatchedGrid.Columns.Add(CreateTextColumn("closest", "最接近的标题", 180));
        _unmatchedGrid.Columns.Add(CreateTextColumn("similarity", "相似度", 90));
        _unmatchedGrid.Columns.Add(CreateTextColumn("footnote", "Footnote", 120));
        _unmatchedGrid.Columns.Add(new DataGridViewTextBoxColumn
        {
            Name = "input",
            HeaderText = "输入标题",
            Width = 180,
            AutoSizeMode = DataGridViewAutoSizeColumnMode.None,
            ReadOnly = false,
        });
        _unmatchedGrid.Columns.Add(CreateButtonColumn("add", "添加", 80));
        _unmatchedGrid.CellContentClick += UnmatchedGridCellContentClick;
        _unmatchedGrid.CellFormatting += UnmatchedGridCellFormatting;
        _unmatchedGrid.CellEndEdit += (_, e) =>
        {
            if (e.RowIndex < 0 || e.ColumnIndex < 0 || !string.Equals(_unmatchedGrid.Columns[e.ColumnIndex].Name, "input", StringComparison.Ordinal))
            {
                return;
            }

            string hash = _unmatchedGrid.Rows[e.RowIndex].Tag?.ToString() ?? string.Empty;
            string text = _unmatchedGrid.Rows[e.RowIndex].Cells["input"].Value?.ToString() ?? string.Empty;
            _unmatchedInputs[hash] = text;
        };
        panel.Controls.Add(_unmatchedGrid, 0, 1);

        TableLayoutPanel bottom = new()
        {
            Dock = DockStyle.Fill,
            ColumnCount = 1,
            RowCount = 1,
            Padding = new Padding(0, 6, 0, 0),
        };
        bottom.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        Button clearButton = new() { Text = "清空缓存", Dock = DockStyle.Fill, Height = 30 };
        clearButton.Click += (_, _) =>
        {
            _titleManager.ClearUnmatchedCache();
            RefreshUnmatchedTab();
            UpdateDbInfo();
            UpdateStats();
        };
        bottom.Controls.Add(clearButton, 0, 0);
        panel.Controls.Add(bottom, 0, 2);

        return tab;
    }

    private TabPage CreateCosineTab()
    {
        TabPage tab = new("相似度匹配记录");
        tab.BackColor = Color.White;
        TableLayoutPanel panel = new()
        {
            Dock = DockStyle.Fill,
            RowCount = 3,
            ColumnCount = 1,
            BackColor = Color.White,
        };
        panel.RowStyles.Add(new RowStyle(SizeType.Absolute, 48));
        panel.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        panel.RowStyles.Add(new RowStyle(SizeType.Absolute, 70));
        tab.Controls.Add(panel);

        Label info = new()
        {
            Dock = DockStyle.Fill,
            Text = "以下是当前会话中自动余弦匹配并写入数据库的记录。",
            TextAlign = ContentAlignment.MiddleLeft,
        };
        panel.Controls.Add(info, 0, 0);

        _cosineGrid = CreateBaseGrid();
        _cosineGrid.Columns.Add(CreateImageColumn("icon", "图标", 56));
        _cosineGrid.Columns.Add(CreateTextColumn("title", "匹配到的标题", 180));
        _cosineGrid.Columns.Add(CreateTextColumn("similarity", "相似度", 100));
        _cosineGrid.Columns.Add(CreateTextColumn("time", "时间", 220));
        _cosineGrid.Columns.Add(CreateButtonColumn("detail", "查看", 80, "操作"));
        _cosineGrid.CellContentClick += CosineGridCellContentClick;
        _cosineGrid.CellFormatting += CosineGridCellFormatting;
        panel.Controls.Add(_cosineGrid, 0, 1);

        TableLayoutPanel bottom = new()
        {
            Dock = DockStyle.Fill,
            ColumnCount = 1,
            RowCount = 1,
            Padding = new Padding(0, 6, 0, 0),
        };
        bottom.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        Button clearButton = new() { Text = "清空会话记录", Dock = DockStyle.Fill, Height = 30 };
        clearButton.Click += (_, _) =>
        {
            _titleManager.ClearCosineMatchesCache();
            RefreshCosineTab();
            UpdateDbInfo();
            UpdateStats();
        };
        bottom.Controls.Add(clearButton, 0, 0);
        panel.Controls.Add(bottom, 0, 2);

        return tab;
    }

    private TabPage CreateSettingsTab()
    {
        TabPage tab = new("设置");
        tab.BackColor = Color.White;
        TableLayoutPanel panel = new()
        {
            Dock = DockStyle.Fill,
            RowCount = 4,
            ColumnCount = 1,
            Padding = new Padding(4),
            BackColor = Color.White,
        };
        panel.RowStyles.Add(new RowStyle(SizeType.Absolute, 180));
        panel.RowStyles.Add(new RowStyle(SizeType.Absolute, 200));
        panel.RowStyles.Add(new RowStyle(SizeType.Absolute, 120));
        panel.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        tab.Controls.Add(panel);

        GroupBox thresholdGroup = new() { Text = "余弦相似度阈值", Dock = DockStyle.Fill };
        TableLayoutPanel thresholdLayout = new() { Dock = DockStyle.Fill, RowCount = 2, ColumnCount = 1 };
        thresholdLayout.RowStyles.Add(new RowStyle(SizeType.Absolute, 52));
        thresholdLayout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        thresholdGroup.Controls.Add(thresholdLayout);

        TableLayoutPanel thresholdTop = new() { Dock = DockStyle.Fill, ColumnCount = 2, RowCount = 1, Margin = new Padding(0) };
        thresholdTop.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        thresholdTop.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 70));
        _thresholdTrackBar.Minimum = 980;
        _thresholdTrackBar.Maximum = 999;
        _thresholdTrackBar.TickStyle = TickStyle.None;
        _thresholdTrackBar.Dock = DockStyle.Fill;
        _thresholdTrackBar.Margin = new Padding(0, 0, 8, 0);
        _thresholdTrackBar.Value = Math.Clamp((int)Math.Round(_titleManager.SimilarityThreshold * 1000), 980, 999);
        _thresholdTrackBar.Scroll += (_, _) =>
        {
            double threshold = _thresholdTrackBar.Value / 1000.0;
            _titleManager.UpdateThreshold(threshold);
            _thresholdLabel.Text = threshold.ToString("0.000");
        };
        thresholdTop.Controls.Add(_thresholdTrackBar, 0, 0);
        _thresholdLabel.Text = (_thresholdTrackBar.Value / 1000.0).ToString("0.000");
        _thresholdLabel.Width = 64;
        _thresholdLabel.TextAlign = ContentAlignment.MiddleLeft;
        thresholdTop.Controls.Add(_thresholdLabel, 1, 0);
        thresholdLayout.Controls.Add(thresholdTop, 0, 0);

        Label thresholdHelp = new()
        {
            Dock = DockStyle.Fill,
            Text = "阈值说明:\n- 0.995 (推荐默认): 与原图标高度一致才会自动匹配\n- 范围 0.980 ~ 0.999: 值越高越严格，误匹配风险越低",
            TextAlign = ContentAlignment.TopLeft,
        };
        thresholdLayout.Controls.Add(thresholdHelp, 0, 1);
        panel.Controls.Add(thresholdGroup, 0, 0);

        GroupBox dbInfoGroup = new() { Text = "数据库信息", Dock = DockStyle.Fill };
        _dbInfoLabel.Dock = DockStyle.Fill;
        _dbInfoLabel.TextAlign = ContentAlignment.TopLeft;
        dbInfoGroup.Controls.Add(_dbInfoLabel);
        panel.Controls.Add(dbInfoGroup, 0, 1);

        GroupBox importExportGroup = new() { Text = "数据导入导出", Dock = DockStyle.Fill };
        TableLayoutPanel ioPanel = new() { Dock = DockStyle.Fill, RowCount = 2, ColumnCount = 1 };
        ioPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 50));
        ioPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 50));
        ioPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        Button exportButton = new() { Text = "导出JSON", Dock = DockStyle.Fill, Height = 30 };
        exportButton.Click += (_, _) => ExportJson();
        ioPanel.Controls.Add(exportButton, 0, 0);
        Button importButton = new() { Text = "导入JSON", Dock = DockStyle.Fill, Height = 30 };
        importButton.Click += (_, _) => ImportJson();
        ioPanel.Controls.Add(importButton, 0, 1);
        importExportGroup.Controls.Add(ioPanel);
        panel.Controls.Add(importExportGroup, 0, 2);

        return tab;
    }

    private static DataGridView CreateBaseGrid()
    {
        DataGridView grid = new()
        {
            Dock = DockStyle.Fill,
            AllowUserToAddRows = false,
            AllowUserToDeleteRows = false,
            AutoGenerateColumns = false,
            MultiSelect = false,
            SelectionMode = DataGridViewSelectionMode.FullRowSelect,
            RowHeadersVisible = false,
            ReadOnly = true,
            AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
            BackgroundColor = Color.White,
        };
        grid.DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleLeft;
        grid.RowTemplate.Height = 40;
        return grid;
    }

    private static DataGridViewImageColumn CreateImageColumn(string name, string header, int width)
    {
        return new DataGridViewImageColumn
        {
            Name = name,
            HeaderText = header,
            Width = width,
            ImageLayout = DataGridViewImageCellLayout.Zoom,
            AutoSizeMode = DataGridViewAutoSizeColumnMode.None,
        };
    }

    private static DataGridViewTextBoxColumn CreateTextColumn(string name, string header, int width)
    {
        return new DataGridViewTextBoxColumn
        {
            Name = name,
            HeaderText = header,
            Width = width,
            MinimumWidth = Math.Min(width, 120),
            FillWeight = Math.Max(width, 100),
            AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill,
            ReadOnly = true,
        };
    }

    private static DataGridViewButtonColumn CreateButtonColumn(string name, string text, int width, string headerText = "操作")
    {
        return new DataGridViewButtonColumn
        {
            Name = name,
            HeaderText = headerText,
            Text = text,
            UseColumnTextForButtonValue = true,
            Width = width,
            AutoSizeMode = DataGridViewAutoSizeColumnMode.None,
        };
    }

    private void CategoryGridCellContentClick(object? sender, DataGridViewCellEventArgs e)
    {
        if (sender is not DataGridView grid || e.RowIndex < 0 || e.ColumnIndex < 0)
        {
            return;
        }

        if (grid.Rows[e.RowIndex].Tag is not NodeTitleManager.TitleRecord record)
        {
            return;
        }

        string columnName = grid.Columns[e.ColumnIndex].Name;
        if (columnName == "edit")
        {
            string? newTitle = Prompt("编辑标题", "请输入新标题:", record.Title);
            if (string.IsNullOrWhiteSpace(newTitle) || string.Equals(newTitle, record.Title, StringComparison.Ordinal))
            {
                return;
            }

            if (_titleManager.UpdateTitle(record.Id, newTitle.Trim(), "manual"))
            {
                MessageBox.Show("标题已更新，类型已设为手动添加", "成功", MessageBoxButtons.OK, MessageBoxIcon.Information);
                RefreshDatabaseTabs();
                UpdateDbInfo();
                UpdateStats();
            }
            else
            {
                MessageBox.Show("更新失败", "失败", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }

            return;
        }

        if (columnName == "delete")
        {
            DialogResult dr = MessageBox.Show("确定要删除这条记录吗？", "确认删除", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
            if (dr != DialogResult.Yes)
            {
                return;
            }

            if (_titleManager.DeleteTitle(record.Id))
            {
                MessageBox.Show("记录已删除", "成功", MessageBoxButtons.OK, MessageBoxIcon.Information);
                RefreshDatabaseTabs();
                UpdateDbInfo();
                UpdateStats();
            }
            else
            {
                MessageBox.Show("删除失败", "失败", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }
    }

    private void UnmatchedGridCellContentClick(object? sender, DataGridViewCellEventArgs e)
    {
        if (sender is not DataGridView grid || e.RowIndex < 0 || e.ColumnIndex < 0)
        {
            return;
        }

        if (!string.Equals(grid.Columns[e.ColumnIndex].Name, "add", StringComparison.Ordinal))
        {
            return;
        }

        string hash = grid.Rows[e.RowIndex].Tag?.ToString() ?? string.Empty;
        if (string.IsNullOrWhiteSpace(hash) || !_currentUnmatchedByHash.TryGetValue(hash, out NodeTitleManager.UnmatchedNode? node))
        {
            MessageBox.Show("找不到对应的节点", "错误", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }

        string title = grid.Rows[e.RowIndex].Cells["input"].Value?.ToString()?.Trim() ?? string.Empty;
        if (string.IsNullOrWhiteSpace(title))
        {
            MessageBox.Show("请输入标题", "错误", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }

        _titleManager.AddTitle(node.FullArray, node.Hash, node.MiddleArray, title, "manual");
        MessageBox.Show($"已添加: {title}", "成功", MessageBoxButtons.OK, MessageBoxIcon.Information);

        _unmatchedInputs.Remove(hash);
        RefreshDatabaseTabs();
        RefreshUnmatchedTab();
        UpdateDbInfo();
        UpdateStats();
    }

    private void CosineGridCellContentClick(object? sender, DataGridViewCellEventArgs e)
    {
        if (sender is not DataGridView grid || e.RowIndex < 0 || e.ColumnIndex < 0)
        {
            return;
        }

        if (!string.Equals(grid.Columns[e.ColumnIndex].Name, "detail", StringComparison.Ordinal))
        {
            return;
        }

        if (grid.Rows[e.RowIndex].Tag is not NodeTitleManager.CosineMatch match)
        {
            return;
        }

        string message = $"Hash: {match.Hash}\n匹配标题: {match.Title}\n相似度: {match.Similarity:0.0000} ({match.Similarity * 100:0.00}%)\n时间: {match.Timestamp}";
        MessageBox.Show(message, "匹配详情", MessageBoxButtons.OK, MessageBoxIcon.Information);
    }

    private void UnmatchedGridCellFormatting(object? sender, DataGridViewCellFormattingEventArgs e)
    {
        if (sender is not DataGridView grid || e.RowIndex < 0 || e.ColumnIndex < 0)
        {
            return;
        }

        if (!string.Equals(grid.Columns[e.ColumnIndex].Name, "similarity", StringComparison.Ordinal))
        {
            return;
        }
        if (e.CellStyle is null)
        {
            return;
        }

        string text = e.Value?.ToString() ?? "0%";
        double value = 0.0;
        if (text.EndsWith('%'))
        {
            _ = double.TryParse(text.TrimEnd('%'), out value);
        }

        if (value >= 95)
        {
            e.CellStyle.ForeColor = Color.FromArgb(0, 150, 0);
        }
        else if (value >= 90)
        {
            e.CellStyle.ForeColor = Color.FromArgb(200, 150, 0);
        }
        else
        {
            e.CellStyle.ForeColor = Color.FromArgb(200, 0, 0);
        }
    }

    private void CosineGridCellFormatting(object? sender, DataGridViewCellFormattingEventArgs e)
    {
        if (sender is not DataGridView grid || e.RowIndex < 0 || e.ColumnIndex < 0)
        {
            return;
        }

        if (!string.Equals(grid.Columns[e.ColumnIndex].Name, "similarity", StringComparison.Ordinal))
        {
            return;
        }
        if (e.CellStyle is null)
        {
            return;
        }

        string text = e.Value?.ToString() ?? "0%";
        double value = 0.0;
        if (text.EndsWith('%'))
        {
            _ = double.TryParse(text.TrimEnd('%'), out value);
        }

        if (value >= 95)
        {
            e.CellStyle.ForeColor = Color.FromArgb(0, 150, 0);
        }
        else if (value >= 90)
        {
            e.CellStyle.ForeColor = Color.FromArgb(200, 150, 0);
        }
        else
        {
            e.CellStyle.ForeColor = Color.FromArgb(200, 0, 0);
        }
    }

    private void RefreshDatabaseTabs()
    {
        List<NodeTitleManager.TitleRecord> allRecords = _titleManager.GetAllTitles();

        foreach (CategoryTab categoryTab in _categoryTabs)
        {
            List<NodeTitleManager.TitleRecord> filtered = allRecords
                .Where(r => categoryTab.Category.FootnoteSet.Contains(r.FootnoteTitle))
                .ToList();
            PopulateCategoryGrid(categoryTab.Grid, filtered);
        }

        UpdateStats();
    }

    private static void PopulateCategoryGrid(DataGridView grid, List<NodeTitleManager.TitleRecord> records)
    {
        grid.Rows.Clear();

        foreach (NodeTitleManager.TitleRecord record in records)
        {
            int rowIndex = grid.Rows.Add(
                CreateIconBitmap(record.FullBlob),
                record.Title,
                record.MiddleHash,
                record.FootnoteTitle,
                record.MatchType == "manual" ? "手动添加" : "相似度匹配",
                "编辑",
                "删除");
            DataGridViewRow row = grid.Rows[rowIndex];
            row.Tag = record;
            row.Height = 40;
            row.Cells["hash"].ToolTipText = record.MiddleHash;
        }
    }

    private void RefreshUnmatchedTab()
    {
        List<NodeTitleManager.UnmatchedNode> nodes = _titleManager.GetUnmatchedNodes();
        _currentUnmatchedByHash = nodes.ToDictionary(v => v.Hash, v => v, StringComparer.Ordinal);

        _unmatchedGrid.Rows.Clear();
        foreach (NodeTitleManager.UnmatchedNode node in nodes)
        {
            string existingInput = _unmatchedInputs.TryGetValue(node.Hash, out string? value) ? value : string.Empty;
            string footnote = CalculateFootnoteTitle(node.FullArray);

            int rowIndex = _unmatchedGrid.Rows.Add(
                CreateIconBitmap(node.FullArray),
                node.Hash,
                string.IsNullOrWhiteSpace(node.ClosestTitle) ? "无" : node.ClosestTitle,
                $"{node.ClosestSimilarity * 100:0.00}%",
                footnote,
                existingInput,
                "添加");

            DataGridViewRow row = _unmatchedGrid.Rows[rowIndex];
            row.Tag = node.Hash;
            row.Height = 40;
            row.Cells["hash"].ToolTipText = node.Hash;
        }
    }

    private void SmartRefreshUnmatched()
    {
        string? focusedHash = null;
        string focusedText = string.Empty;
        DataGridViewCell? currentCell = _unmatchedGrid.CurrentCell;
        if (currentCell is not null && currentCell.RowIndex >= 0)
        {
            focusedHash = _unmatchedGrid.Rows[currentCell.RowIndex].Tag?.ToString();
            focusedText = _unmatchedGrid.Rows[currentCell.RowIndex].Cells["input"].Value?.ToString() ?? string.Empty;
        }

        List<NodeTitleManager.UnmatchedNode> nodes = _titleManager.GetUnmatchedNodes();
        HashSet<string> currentHashes = nodes.Select(v => v.Hash).ToHashSet(StringComparer.Ordinal);

        bool changed = currentHashes.Count != _lastUnmatchedHashes.Count || !currentHashes.SetEquals(_lastUnmatchedHashes);
        if (!changed)
        {
            return;
        }

        _lastUnmatchedHashes.Clear();
        foreach (string hash in currentHashes)
        {
            _lastUnmatchedHashes.Add(hash);
        }

        RefreshUnmatchedTab();
        if (!string.IsNullOrWhiteSpace(focusedHash))
        {
            for (int row = 0; row < _unmatchedGrid.Rows.Count; row++)
            {
                if (string.Equals(_unmatchedGrid.Rows[row].Tag?.ToString(), focusedHash, StringComparison.Ordinal))
                {
                    _unmatchedGrid.Rows[row].Cells["input"].Value = focusedText;
                    _unmatchedGrid.CurrentCell = _unmatchedGrid.Rows[row].Cells["input"];
                    break;
                }
            }
        }
        UpdateDbInfo();
        UpdateStats();
    }

    private void RefreshCosineTab()
    {
        List<NodeTitleManager.CosineMatch> matches = _titleManager.GetCosineMatches();
        _cosineGrid.Rows.Clear();

        foreach (NodeTitleManager.CosineMatch match in matches)
        {
            int rowIndex = _cosineGrid.Rows.Add(
                CreateIconBitmap(match.FullArray),
                match.Title,
                $"{match.Similarity * 100:0.00}%",
                match.Timestamp,
                "查看");
            DataGridViewRow row = _cosineGrid.Rows[rowIndex];
            row.Tag = match;
            row.Height = 40;
        }
    }

    private void UpdateDbInfo()
    {
        Dictionary<string, int> stats = _titleManager.GetStats();
        _dbInfoLabel.Text =
            $"数据库路径: {_titleManager.DbPath}\n" +
            $"总记录数: {stats["total"]}\n" +
            $"手动添加: {stats["manual"]}\n" +
            $"相似度匹配: {stats["cosine"]}\n" +
            $"Hash缓存: {stats["hash_cached"]}\n" +
            $"当前未匹配(内存): {stats["unmatched_memory"]}\n" +
            $"会话相似度匹配: {stats["cosine_matches_session"]}";
    }

    private void UpdateStats()
    {
        Dictionary<string, int> stats = _titleManager.GetStats();
        _statsLabel.Text =
            $"总记录: {stats["total"]} | 手动添加: {stats["manual"]} | 相似度匹配: {stats["cosine"]} | 当前未匹配: {stats["unmatched_memory"]}";
    }

    private void ExportJson()
    {
        using SaveFileDialog dialog = new()
        {
            Filter = "JSON文件 (*.json)|*.json",
            FileName = "node_titles.json",
            Title = "导出图标库",
        };

        if (dialog.ShowDialog(this) != DialogResult.OK)
        {
            return;
        }

        if (_titleManager.ExportToJson(dialog.FileName))
        {
            MessageBox.Show($"已导出到:\n{dialog.FileName}", "成功", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        else
        {
            MessageBox.Show("导出失败", "失败", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    private void ImportJson()
    {
        using OpenFileDialog dialog = new()
        {
            Filter = "JSON文件 (*.json)|*.json",
            Title = "导入图标库",
        };

        if (dialog.ShowDialog(this) != DialogResult.OK)
        {
            return;
        }

        DialogResult dr = MessageBox.Show(
            "选择导入方式:\nYes = 合并现有数据\nNo = 覆盖现有数据\nCancel = 取消",
            "导入方式",
            MessageBoxButtons.YesNoCancel,
            MessageBoxIcon.Question);

        if (dr == DialogResult.Cancel)
        {
            return;
        }

        bool merge = dr == DialogResult.Yes;
        if (_titleManager.ImportFromJson(dialog.FileName, merge))
        {
            MessageBox.Show("导入完成", "成功", MessageBoxButtons.OK, MessageBoxIcon.Information);
            RefreshDatabaseTabs();
            RefreshUnmatchedTab();
            RefreshCosineTab();
            UpdateDbInfo();
            UpdateStats();
        }
        else
        {
            MessageBox.Show("导入失败", "失败", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    private string CalculateFootnoteTitle(byte[] fullArray)
    {
        if (fullArray.Length != 8 * 8 * 3)
        {
            return "Unknown";
        }

        int[] positions =
        [
            ((6 * 8) + 6) * 3,
            ((6 * 8) + 7) * 3,
            ((7 * 8) + 6) * 3,
            ((7 * 8) + 7) * 3,
        ];

        byte r = fullArray[positions[0]];
        byte g = fullArray[positions[0] + 1];
        byte b = fullArray[positions[0] + 2];

        foreach (int idx in positions)
        {
            if (fullArray[idx] != r || fullArray[idx + 1] != g || fullArray[idx + 2] != b)
            {
                return "Unknown";
            }
        }

        string key = $"{r},{g},{b}";
        return _iconTypeMap.TryGetValue(key, out string? footnote) ? footnote : "Unknown";
    }

    private static Bitmap CreateIconBitmap(byte[] fullArray)
    {
        Bitmap source = new(8, 8);
        if (fullArray.Length == 8 * 8 * 3)
        {
            int idx = 0;
            for (int y = 0; y < 8; y++)
            {
                for (int x = 0; x < 8; x++)
                {
                    byte r = fullArray[idx++];
                    byte g = fullArray[idx++];
                    byte b = fullArray[idx++];
                    source.SetPixel(x, y, Color.FromArgb(r, g, b));
                }
            }
        }

        Bitmap scaled = new(32, 32);
        using Graphics graphics = Graphics.FromImage(scaled);
        graphics.InterpolationMode = System.Drawing.Drawing2D.InterpolationMode.NearestNeighbor;
        graphics.PixelOffsetMode = System.Drawing.Drawing2D.PixelOffsetMode.Half;
        graphics.DrawImage(source, new Rectangle(0, 0, 32, 32), new Rectangle(0, 0, 8, 8), GraphicsUnit.Pixel);
        source.Dispose();
        return scaled;
    }

    private static string ShortHash(string hash)
    {
        if (hash.Length <= 20)
        {
            return hash;
        }

        return $"{hash[..8]}...{hash[^8..]}";
    }

    private static string? Prompt(string title, string prompt, string defaultValue)
    {
        using Form dialog = new()
        {
            Text = title,
            Width = 480,
            Height = 160,
            StartPosition = FormStartPosition.CenterParent,
            FormBorderStyle = FormBorderStyle.FixedDialog,
            MaximizeBox = false,
            MinimizeBox = false,
        };

        Label label = new() { Left = 12, Top = 12, Width = 430, Text = prompt };
        TextBox input = new() { Left = 12, Top = 36, Width = 440, Text = defaultValue };
        Button ok = new() { Left = 296, Width = 75, Top = 70, Text = "确定", DialogResult = DialogResult.OK };
        Button cancel = new() { Left = 377, Width = 75, Top = 70, Text = "取消", DialogResult = DialogResult.Cancel };

        dialog.Controls.Add(label);
        dialog.Controls.Add(input);
        dialog.Controls.Add(ok);
        dialog.Controls.Add(cancel);
        dialog.AcceptButton = ok;
        dialog.CancelButton = cancel;

        return dialog.ShowDialog() == DialogResult.OK ? input.Text : null;
    }

    private sealed record CategoryDef(string Name, string[] Footnotes)
    {
        public HashSet<string> FootnoteSet { get; } = Footnotes.ToHashSet(StringComparer.Ordinal);
    }

    private sealed record CategoryTab(TabPage TabPage, CategoryDef Category, DataGridView Grid);
}
