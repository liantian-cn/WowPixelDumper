# Dumper.NET 运行与验证说明

## 构建

```powershell
dotnet build Dumper.NET\Dumper.NET.csproj
```

## 启动 GUI

```powershell
dotnet run --project Dumper.NET\Dumper.NET.csproj
```

默认 API 地址：`http://127.0.0.1:65131/`

## 无界面验证模式（推荐先跑）

```powershell
dotnet run --project Dumper.NET\Dumper.NET.csproj -- --validate --seconds 10
```

行为：
- 自动枚举并轮询所有显示器输出。
- 每个输出尝试 `截图 -> 模板定位 -> 数据提取`。
- 成功时生成 `validation_report.json`（`success=true`）并返回 0。
- 失败时同样生成报告并附带诊断截图 `diag_frame.bmp`。

输出文件路径：
- `Dumper.NET\bin\Debug\net8.0-windows\validation_report.json`
- `Dumper.NET\bin\Debug\net8.0-windows\diag_frame.bmp`

## 常见失败原因

1. 模板锚点未命中（`未找到模板锚点`）
- 先看 `diag_frame.bmp`，确认画面里是否确实有插件像素块和 `mark8` 图案。
- 确认 WoW 客户端没有被遮挡、缩放/色彩滤镜未影响像素。
- 确认插件已加载并正在输出像素块。

2. API 可用但返回 `相机尚未启动`
- 这是正常状态，说明程序与 HTTP 服务正常，仅采集尚未启动。

## 当前实现覆盖

- DXGI Desktop Duplication 截图（含 RowPitch 逐行读回与格式转换到 BGRA）。
- 模板定位、8x8 节点提取、JSON 输出。
- SQLite 标题库（hash 直匹配 + cosine 匹配 + 未匹配缓存）。
- 遮挡检测逻辑（对齐 Python 版本校验点）。

