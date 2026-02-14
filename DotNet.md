# .NET 版本技术栈（`Dumper.NET\`）

## 运行平台与语言

- C# / .NET 8 (`net8.0-windows`)。
- Windows 桌面应用（WinForms）。

## UI 与交互

- `System.Windows.Forms`：主界面、图标库管理、编辑器窗体。

## 屏幕采集与图形底层

- `Vortice.DXGI` + `Vortice.Direct3D11`：DXGI Desktop Duplication 屏幕采集。
- 支持多种像素格式转换到统一 BGRA/RGB 流程。

## 数据服务与网络

- `HttpListener`：内置 HTTP API（替代 Flask）。
- `System.Text.Json`：JSON 序列化输出。

## 存储与匹配

- `Microsoft.Data.Sqlite`：本地图标标题库。
- `System.IO.Hashing`（XxHash3）：middle hash 计算。
- 余弦相似度匹配：自动标题补全。

## 并发与任务模型

- `Task` + `CancellationTokenSource`：采集循环后台执行与安全停止。
- `lock`：共享 `pixel_dump` 与缓存结构同步。

## 工程结构特征

- `Core`：像素模型、解析逻辑、标题库。
- `Capture`：采集驱动。
- `Web`：HTTP API。
- `UI`：WinForms 界面。

