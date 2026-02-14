# Dumper / Dumper.NET 文件用途说明

## `Dumper\`（Python / PySide6）

- `Dumper/DumperGUI.py`：程序入口，创建 Qt 应用与主窗口，使用 Windows 互斥锁保证单实例。
- `Dumper/MainWindow.py`：主界面与主流程编排；负责显示器选择、采集启停、日志显示、数据展示、API 启动、遮挡校验触发。
- `Dumper/Worker.py`：后台线程。
  - `CameraWorker`：持续拉取 DXCam 帧并发信号给主线程。
  - `WebServerWorker`：启动 Flask HTTP 服务，输出最新 JSON。
- `Dumper/Node.py`：像素模型与提取引擎。
  - `PixelBlock`：纯色、亮度、hash、剩余时间等基础计算。
  - `Node`：8x8 节点的 full/middle/inner/sub/footnote 访问。
  - `NodeExtractor`：按坐标读取节点、读取技能序列、光环序列、血条。
- `Dumper/NodeExtractorData.py`：`extract_all_data`，按约定坐标输出完整业务 JSON。
- `Dumper/Database.py`：`NodeTitleManager`，管理 SQLite 标题库、hash 匹配、余弦匹配、缓存、导入导出。
- `Dumper/IconLibraryDialog.py`：图标库管理 UI（分类浏览、未匹配补录、相似度记录、阈值配置、导入导出）。
- `Dumper/Utils.py`：工具函数与配置加载（`ColorMap.json`、模板匹配、边界查找、路径工具）。
- `Dumper/ColorMap.json`：颜色到业务语义映射（IconType/Class/Role）。
- `Dumper/mark8.png`：模板锚点图，用于定位数据区域。
- `Dumper/icon.ico`：Windows 图标资源（打包使用）。
- `Dumper/deploy.py`：Nuitka 打包脚本，构建 EXE 并拷贝资源文件。
- `Dumper/DumperGUI.cmd`：便捷启动脚本（`uvw run .\DumperGUI.py`）。
- `Dumper/test_script.py`：模块级测试脚本（Utils/Database/Node/comment_deleter）。
- `Dumper/comment_deleter.py`：辅助工具，去除 Python 注释/docstring（AST 方式）。

## `Dumper.NET\`（C# / WinForms）

- `Dumper.NET/Program.cs`：应用入口；单实例互斥；GUI 模式与 `--validate` 验证模式切换。
- `Dumper.NET/Dumper.NET.csproj`：项目配置与依赖（WinForms、net8、Vortice、Sqlite），并链接 Python 侧资源到 `Assets\`。
- `Dumper.NET/Dumper.NET.slnx`：解决方案文件。
- `Dumper.NET/Dumper.NET.csproj.user`：本地 IDE 用户配置（与 Form 设计器关联）。
- `Dumper.NET/Core/PixelCore.cs`：核心像素与解析基础能力。
  - `ColorMap`、`PixelFrame`、`TemplateMatcher`
  - `PixelBlock`、`Node`、`NodeExtractor`
  - `NodeDataExtractor.ExtractAllData`
- `Dumper.NET/Core/PixelDumpService.cs`：采集业务服务编排（启动/停止/循环处理/遮挡校验/最新 JSON 缓存）。
- `Dumper.NET/Core/NodeTitleManager.cs`：C# 版标题库管理（SQLite + hash/cosine 匹配 + 未匹配缓存 + 导入导出）。
- `Dumper.NET/Capture/DesktopDuplicatorCapture.cs`：基于 DXGI Desktop Duplication 的高性能屏幕采集。
- `Dumper.NET/Web/HttpApiServer.cs`：HTTP API 服务（返回当前 JSON，含 CORS 头）。
- `Dumper.NET/UI/MainForm.cs`：主界面（显示器/FPS/启动停止/API/日志/JSON 显示/图标库入口）。
- `Dumper.NET/UI/IconLibraryForm.cs`：图标库管理界面（与 Python 版本功能对应）。
- `Dumper.NET/UI/TitleEditorForm.cs`：标题记录编辑器（简化 CRUD 工具窗）。
- `Dumper.NET/README.NET.md`：.NET 侧构建、运行、验证说明。
- `Dumper.NET/ColorMap.json`：颜色映射（与 Python 侧同源）。
- `Dumper.NET/mark8.png`：模板锚点图（与 Python 侧同源）。
- `Dumper.NET/Form1.cs`：历史默认窗体代码（当前主流程未使用）。
- `Dumper.NET/Form1.Designer.cs`：`Form1` 设计器代码（历史遗留）。
- `Dumper.NET/Form1.resx`：`Form1` 资源文件（历史遗留）。

