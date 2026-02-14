using Dumper.NET.Core;

namespace Dumper.NET.UI;

public sealed class TitleEditorForm : Form
{
    private readonly NodeTitleManager _titleManager;
    private readonly DataGridView _grid = new();
    private readonly Button _refreshButton = new();
    private readonly Button _saveButton = new();
    private readonly Button _deleteButton = new();

    public TitleEditorForm(NodeTitleManager titleManager)
    {
        _titleManager = titleManager;
        InitializeLayout();
        LoadRecords();
    }

    private void InitializeLayout()
    {
        Text = "标题编辑器";
        Width = 1100;
        Height = 700;
        StartPosition = FormStartPosition.CenterParent;

        TableLayoutPanel root = new()
        {
            Dock = DockStyle.Fill,
            RowCount = 2,
            ColumnCount = 1,
            Padding = new Padding(8),
        };
        root.RowStyles.Add(new RowStyle(SizeType.Absolute, 44));
        root.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        Controls.Add(root);

        FlowLayoutPanel top = new()
        {
            Dock = DockStyle.Fill,
            FlowDirection = FlowDirection.LeftToRight,
            WrapContents = false,
        };
        root.Controls.Add(top, 0, 0);

        ConfigureButton(_refreshButton, "刷新", (_, _) => LoadRecords());
        ConfigureButton(_saveButton, "保存标题", (_, _) => SaveSelectedTitle());
        ConfigureButton(_deleteButton, "删除记录", (_, _) => DeleteSelectedRecord());

        top.Controls.Add(_refreshButton);
        top.Controls.Add(_saveButton);
        top.Controls.Add(_deleteButton);

        _grid.Dock = DockStyle.Fill;
        _grid.ReadOnly = false;
        _grid.AllowUserToAddRows = false;
        _grid.AllowUserToDeleteRows = false;
        _grid.SelectionMode = DataGridViewSelectionMode.FullRowSelect;
        _grid.MultiSelect = false;
        _grid.RowHeadersVisible = false;
        _grid.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill;
        _grid.ColumnHeadersHeight = 34;
        _grid.RowTemplate.Height = 30;

        _grid.Columns.Add(new DataGridViewTextBoxColumn { Name = "id", HeaderText = "ID", ReadOnly = true, FillWeight = 10 });
        _grid.Columns.Add(new DataGridViewTextBoxColumn { Name = "hash", HeaderText = "Hash", ReadOnly = true, FillWeight = 30 });
        _grid.Columns.Add(new DataGridViewTextBoxColumn { Name = "title", HeaderText = "Title", ReadOnly = false, FillWeight = 30 });
        _grid.Columns.Add(new DataGridViewTextBoxColumn { Name = "matchType", HeaderText = "Match Type", ReadOnly = true, FillWeight = 12 });
        _grid.Columns.Add(new DataGridViewTextBoxColumn { Name = "footnote", HeaderText = "Footnote", ReadOnly = true, FillWeight = 12 });
        _grid.Columns.Add(new DataGridViewTextBoxColumn { Name = "createdAt", HeaderText = "Created At", ReadOnly = true, FillWeight = 20 });

        root.Controls.Add(_grid, 0, 1);
    }

    private static void ConfigureButton(Button button, string text, EventHandler click)
    {
        button.Text = text;
        button.AutoSize = false;
        button.Size = new Size(96, 30);
        button.Margin = new Padding(0, 6, 8, 0);
        button.Click += click;
    }

    private void LoadRecords()
    {
        List<NodeTitleManager.TitleRecord> records = _titleManager.GetAllTitles();

        _grid.Rows.Clear();
        foreach (NodeTitleManager.TitleRecord r in records)
        {
            _grid.Rows.Add(r.Id, r.MiddleHash, r.Title, r.MatchType, r.FootnoteTitle, r.CreatedAt);
        }
    }

    private void SaveSelectedTitle()
    {
        if (_grid.SelectedRows.Count == 0)
        {
            MessageBox.Show("请先选中一条记录。", "提示", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        DataGridViewRow row = _grid.SelectedRows[0];
        int id = Convert.ToInt32(row.Cells["id"].Value);
        string newTitle = row.Cells["title"].Value?.ToString() ?? string.Empty;

        if (!_titleManager.UpdateTitle(id, newTitle))
        {
            MessageBox.Show("保存失败，标题不能为空或记录不存在。", "错误", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }

        LoadRecords();
    }

    private void DeleteSelectedRecord()
    {
        if (_grid.SelectedRows.Count == 0)
        {
            MessageBox.Show("请先选中一条记录。", "提示", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        DataGridViewRow row = _grid.SelectedRows[0];
        int id = Convert.ToInt32(row.Cells["id"].Value);

        DialogResult dr = MessageBox.Show($"确认删除记录 ID={id} ?", "确认", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
        if (dr != DialogResult.Yes)
        {
            return;
        }

        if (!_titleManager.DeleteTitle(id))
        {
            MessageBox.Show("删除失败，记录可能已不存在。", "错误", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }

        LoadRecords();
    }
}
